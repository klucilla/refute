"""v0.5.7 (exploratory): the labelled v0.5 battery on the TOI's own ephemeris, for the 540 TOIs of
v0.5.6 parts A and B (docs/plans/v0.5.7-plan.md; the maintainer's decision of 2026-11-23,
received at 10:41 local, #218, comment 7102888515).

**What runs:** for each TOI, the TESS adapter's download (SPOC 120-s light curves and pixel files,
into ``.cache/v057/data``), then the v0.5 battery unchanged, with the test plan the TOI's v0.5.6
run used (part A: ``calibration/v0.5/claim.yaml``; part B: ``calibration/v0.5.6/claim.yaml``),
stage 2, with no catalog test. The steps are the same calls as v0.5.6's runners:
- detrending and prewhitening;
- ``attack_candidate``;
- the coverage and sensitivity rules;
- deferral and the decisive aggregate.

The only difference is the candidate handed to ``attack_candidate``: no search is run. No code in
``src/`` changes, and no rule, threshold, refusal or aggregation changes.

**Fixed mode** (the plan, "Fixed mode"):
- **The period** is the TOI's.
- **The epoch** is the TOI's, refined only inside ± one TOI duration. A box of the TOI's duration
  is slid in two-minute steps over the detrended (and prewhitened, if any) curve, with the
  battery's own per-point noise (``per_point_sigma``).
- **The offset kept** has the largest positive depth SNR, if that SNR is at least 3.0. If none
  qualifies, the TOI is attacked at its propagated epoch, and the record says so.
- **The candidate** handed to the battery carries the TOI's period and duration and the refined
  epoch.
- **The battery's own** ``attack_candidate`` then does everything else, unchanged: its masked
  detrending, its own finalization (depth, SNR, final epoch) and every test.
- **The record keeps:** the window, the refined offset, the final ephemeris, whether the final
  epoch left the window, and the identity by v0.5.6's rule.

**Every record** carries a machine ``started_utc``, ``mode: exploratory``, the limits label and
``method_status: not_validated``, and its tests' coverage. Zero coverage stays INCONCLUSIVE
(``enforce_coverage``). Outputs are never verdicts on a TOI, never candidates and never a
disposition.

**Caps and machine** (the decision, item 3):
- 20 CPU-h for everything of the phase, the pilot included.
- A disk peak of 20 GB, by admission at 18 GB, as v0.5.6 part A did.
- Pixel files are deleted per target, after a manifest (MAST name, observation id, data URI,
  sector, size, SHA-256) is written and read back to ``.cache/v057/run/tpf-deletions``.
- Light curves stay until the end; they are deleted then, as regenerable files.
- Monday to Friday, 08:00 to 18:00: at most 10 workers and 2 simultaneous downloads; otherwise up
  to 20 workers and 6.
- Batches of up to 28 minutes of admission, then drain. BelowNormal priority and CPUs 8 to 31
  (``pinrun``).
- Resumable: one record per target, and a recorded target never runs again. An unclean end is
  charged by an upper bound.

**The pilot** (the plan, "The pilot and the stop"):
- **The set:** the first 3 matched planet records and the first 2 matched others of each part, in
  draw order, from the v0.5.6 records stored in git.
- **The comparison:** after the pilot, the step compares each fixed-mode record with its v0.5.6
  record. A TOI is reproduced when the outcome is the same and every test has the same status.
- **The stop:** fewer than 9 reproduced writes ``fixed-pilot.json`` with ``stop: true``, and
  ``rest`` refuses to run.

Usage (from the project root, pinned):
- ``fixed_run.py pilot``
- ``fixed_run.py rest``
- ``fixed_run.py clean`` (deletes the light curves at the end)
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import multiprocessing
import os
import queue
import shutil
import sys
import threading
import time
import traceback
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
V056 = ROOT / "docs/validation/v0.5.6"
PLANS = {
    "A": ROOT / "calibration/v0.5/claim.yaml",
    "B": ROOT / "calibration/v0.5.6/claim.yaml",
}
DRAWS = {"A": V056 / "part-a-draw.json", "B": ROOT / "calibration/v0.5.6/part-b-draw.json"}
BUNDLES = {"A": V056 / "part-a-records.json", "B": V056 / "part-b-records.json"}
LEDGER = HERE / "fixed-ledger.json"
PILOT_RESULT = HERE / "fixed-pilot.json"
CACHE = ROOT / ".cache"
WORK = CACHE / "v057"
DATA = WORK / "data"
LIGHTKURVE = DATA / "lightkurve"
RECORDS = WORK / "run/records"
TPF_LOGS = WORK / "run/tpf-deletions"
MARKER = WORK / "run/in-flight.json"
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"
CAP_CPU_HOURS = 20.0
CAP_DISK_BYTES = 20e9
ADMIT_DISK_BYTES = 18e9
RESERVE_PER_SECTOR = 101_220_480 + 4_164_480  # v0.5.6 part A's largest per-sector size
BATCH_SECONDS = 28 * 60
SAMPLE_SECONDS = 2.0
WALL_BASE, WALL_PER_SECTOR = 65.0, 25.0
CPU_BASE, CPU_PER_SECTOR = 40.0, 20.0
BTJD = 2457000.0
IDENTITY_TOLERANCE = 0.001
FACTORS = (1.0, 2.0, 0.5)
WINDOW_DURATIONS = 1.0  # the epoch window: +- this many TOI durations
STEP_DAYS = 2.0 / 1440.0  # the refinement step: two minutes
MIN_WINDOW_SNR = 3.0  # an offset is kept only if its depth SNR is at least this
PILOT_PICK = {"planet": 3, "other": 2}  # per part, in draw order, among matched records
PILOT_MIN_REPRODUCED = 9

_DOWNLOADS = None
_FETCHED = None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_path(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def utc(t: float | None = None) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def limits(now: dt.datetime | None = None) -> tuple[int, int]:
    """(workers, simultaneous downloads) at a moment."""
    now = now or dt.datetime.now()
    business = now.weekday() < 5 and 8 <= now.hour < 18
    return (10, 2) if business else (20, 6)


def batch_limits() -> tuple[int, int]:
    now = dt.datetime.now()
    a, b = limits(now), limits(now + dt.timedelta(minutes=30))
    return min(a[0], b[0]), min(a[1], b[1])


# --- targets and the v0.5.6 records ---------------------------------------------------


def targets() -> list[dict]:
    """The 540 TOIs, in draw order: part A (planet, open), then part B (planet, fp)."""
    out = []
    for part, arms in (("A", ("planet", "open")), ("B", ("planet", "fp"))):
        draw = json.loads(DRAWS[part].read_text("utf-8"))
        if draw.get("status") != "complete":
            raise SystemExit(f"part {part}'s draw is not complete")
        for arm in arms:
            for rank, c in enumerate(draw["arms"][arm]["chosen"]):
                out.append(
                    {**c, "part": part, "arm": arm, "rank": rank, "key": f"TIC-{c['tic_id']}"}
                )
    keys = [t["key"] for t in out]
    if len(set(keys)) != len(keys):
        raise SystemExit("a TIC appears twice across parts A and B")
    return out


def search_records() -> dict[str, dict]:
    """The v0.5.6 records (search mode), from the bundles in git, by target key."""
    out = {}
    for part, path in BUNDLES.items():
        doc = json.loads(path.read_text("utf-8"))
        for item in doc["records"]:
            content = item["content"]
            text = json.dumps(content, sort_keys=True)
            out[content["target_key"]] = {**content, "_part": part, "_bundle_sha": item["sha256"],
                                          "_len": len(text)}  # fmt: skip
    return out


def pilot_set(all_targets: list[dict]) -> list[dict]:
    """The plan's pilot: per part, the first 3 matched planet records and the first 2 matched
    others (open or FP), in draw order, among the v0.5.6 records with status OK."""
    searched = search_records()
    picked = []
    for part in ("A", "B"):
        counts = {"planet": 0, "other": 0}
        for t in all_targets:
            if t["part"] != part:
                continue
            r = searched.get(t["key"])
            if r is None or r.get("status") != "OK" or not (r.get("identity") or {}).get("matched"):
                continue
            kind = "planet" if t["arm"] == "planet" else "other"
            if counts[kind] < PILOT_PICK[kind]:
                counts[kind] += 1
                picked.append(t)
    return picked


def reserve(target: dict) -> int:
    return len(target["sectors"]) * RESERVE_PER_SECTOR


def est_wall(target: dict) -> float:
    return WALL_BASE + WALL_PER_SECTOR * len(target["sectors"])


def est_cpu_hours(target: dict) -> float:
    return (CPU_BASE + CPU_PER_SECTOR * len(target["sectors"])) / 3600.0


def _bytes(manifest: dict) -> int:
    total = 0
    for rec in [*manifest.get("files", []), *manifest.get("pixel_files", [])]:
        path = DATA / rec["path"]
        if path.exists():
            total += path.stat().st_size
    return total


def _tic_files(tic_id: int, suffix: str = ".fits") -> list[Path]:
    if not LIGHTKURVE.exists():
        return []
    return sorted(LIGHTKURVE.rglob(f"*-{int(tic_id):016d}-*{suffix}"))


def _tpf_entry(f: dict) -> dict:
    return {
        "name": f["name"],
        "path": f["path"],
        "sector": int(f["sector"]),
        "bytes": int(f["bytes"]),
        "sha256": f["sha256"],
        "obs_id": f.get("obs_id"),
        "data_uri": f.get("data_uri"),
        "url": f.get("url"),
    }


def _test(t) -> dict:
    return {
        "status": t.status.value,
        "severity": t.severity.value,
        "message": (t.message or "")[:400],
        "coverage": t.coverage,
        "coverage_unit": t.coverage_unit,
        "sensitivity": t.sensitivity,
    }


def _init(semaphore, fetched) -> None:
    global _DOWNLOADS, _FETCHED
    _DOWNLOADS, _FETCHED = semaphore, fetched


# --- fixed mode ------------------------------------------------------------------------


def refine_epoch(
    time_: np.ndarray, flux: np.ndarray, sigma: np.ndarray, period: float, epoch: float,
    duration: float,
) -> dict:  # fmt: skip
    """The epoch refined inside +- WINDOW_DURATIONS durations of the propagated epoch, at a fixed
    period and the TOI's duration. For each offset, a weighted box: depth = weighted mean outside
    the box minus weighted mean inside, its error from the weights, SNR = depth / error. The
    offset with the largest positive SNR is kept if that SNR is at least MIN_WINDOW_SNR; otherwise
    the propagated epoch is used and ``found`` is False. Pure function: the tests call it."""
    half = WINDOW_DURATIONS * duration
    offsets = np.arange(-half, half + STEP_DAYS / 2.0, STEP_DAYS)
    ok = np.isfinite(time_) & np.isfinite(flux) & np.isfinite(sigma) & (sigma > 0)
    t, f, w = time_[ok], flux[ok], 1.0 / sigma[ok] ** 2
    best = {"snr": -np.inf, "offset_days": 0.0, "depth": float("nan"), "depth_err": float("nan")}
    evaluated = 0
    for d in offsets:
        phase = (t - (epoch + d) + 0.5 * period) % period - 0.5 * period
        inside = np.abs(phase) < duration / 2.0
        if inside.sum() < 3 or (~inside).sum() < 3:
            continue
        evaluated += 1
        w_in, w_out = w[inside].sum(), w[~inside].sum()
        depth = (w[~inside] * f[~inside]).sum() / w_out - (w[inside] * f[inside]).sum() / w_in
        err = float(np.sqrt(1.0 / w_in + 1.0 / w_out))
        snr = depth / err
        if depth > 0 and snr > best["snr"]:
            best = {"snr": float(snr), "offset_days": float(d), "depth": float(depth),
                    "depth_err": err}  # fmt: skip
    found = bool(np.isfinite(best["snr"]) and best["snr"] >= MIN_WINDOW_SNR)
    return {
        "window_half_width_hours": half * 24.0,
        "step_minutes": STEP_DAYS * 1440.0,
        "offsets_evaluated": evaluated,
        "found": found,
        "offset_hours": best["offset_days"] * 24.0 if found else 0.0,
        "best_snr": None if not np.isfinite(best["snr"]) else best["snr"],
        "best_offset_hours": None if not np.isfinite(best["snr"]) else best["offset_days"] * 24.0,
        "depth": best["depth"] if found else None,
        "depth_err": best["depth_err"] if found else None,
        "min_snr": MIN_WINDOW_SNR,
    }


def epoch_offset_hours(t0: float, epoch: float, period: float) -> float:
    """The distance of ``t0`` from the nearest propagated transit of ``epoch``, in hours (signed,
    in [-P/2, P/2))."""
    return float(((t0 - epoch + 0.5 * period) % period - 0.5 * period) * 24.0)


def fixed_candidate(searched, target: dict):
    """The candidate handed to ``attack_candidate``: the TOI's period and duration, the refined
    epoch. Its depth and SNR are the window's; the battery's own finalization replaces them."""
    from refute.packs.tess.events import per_point_sigma
    from refute.packs.tess.search import count_transits
    from refute.packs.tess.types import Candidate

    period = float(target["period_days"])
    duration = float(target["duration_hours"]) / 24.0
    epoch = float(target["epoch_bjd"]) - BTJD
    sigma = per_point_sigma(searched)
    window = refine_epoch(searched.time, searched.flux, sigma, period, epoch, duration)
    t0 = epoch + window["offset_hours"] / 24.0
    depth = window["depth"] if window["found"] else 0.0
    depth_err = window["depth_err"] if window["found"] else float("nan")
    snr = window["best_snr"] if window["found"] else 0.0
    cand = Candidate(
        period=period,
        t0=t0,
        duration=duration,
        depth=float(depth),
        depth_err=float(depth_err),
        snr=float(snr),
        log_likelihood=0.5 * float(snr) ** 2,
        sde=0.0,
        n_transits=count_transits(searched, period, t0, duration),
    )
    return cand, window


def run_one(target: dict, test_plan: dict) -> dict:
    """One TIC in fixed mode: download, the fixed candidate, the battery, the identity. Any
    failure is recorded, never hidden."""
    from refute.core.io import read_json
    from refute.core.sensitivity import enforce_sensitivity
    from refute.core.verdict import aggregate, defer_tests, enforce_coverage
    from refute.packs.tess.adapter import NoProductsError, TessAdapter, manifest_path
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.discover.measure import stage_plan
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.pipeline import (
        attack_candidate,
        expected_by_role,
        global_prewhitening,
        matching_factor,
    )
    from refute.packs.tess.power import registry_for

    started, wall = time.process_time(), time.time()
    rec = {
        "target_key": target["key"],
        "tic_id": target["tic_id"],
        "toi": target["toi"],
        "part": target["part"],
        "arm": target["arm"],
        "rank": target["rank"],
        "mode": "exploratory",
        "candidate_mode": "fixed (the TOI's ephemeris)",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "started_utc": utc(wall),
        "test_plan_source": PLANS[target["part"]].relative_to(ROOT).as_posix(),
    }
    try:
        plan_dict = stage_plan(test_plan, 2)
        plan = TessTestPlan.model_validate(plan_dict)
        tgt = {"key": target["key"], "tic_id": int(target["tic_id"])}
        before = {p.name for p in _tic_files(int(target["tic_id"]))}
        fetch_started = time.time()
        try:
            if _DOWNLOADS is None:
                TessAdapter().fetch(tgt, plan_dict, DATA)
            else:
                with _DOWNLOADS:
                    TessAdapter().fetch(tgt, plan_dict, DATA)
        except NoProductsError as exc:
            rec.update({"status": "MISSING_PRODUCTS", "reason": str(exc)})
            return rec
        finally:
            rec["fetch_wall_seconds"] = time.time() - fetch_started
            if _FETCHED is not None:
                _FETCHED.put(target["key"])
        manifest = read_json(manifest_path(DATA, int(target["tic_id"])))
        every = [*manifest["files"], *manifest["pixel_files"]]
        rec["bytes"] = _bytes(manifest)
        rec["light_curve_bytes"] = sum(int(f["bytes"]) for f in manifest["files"])
        rec["pixel_file_bytes"] = sum(int(f["bytes"]) for f in manifest["pixel_files"])
        rec["downloaded_bytes"] = sum(int(f["bytes"]) for f in every if f["name"] not in before)
        rec["reused_bytes"] = sum(int(f["bytes"]) for f in every if f["name"] in before)
        rec["tpf_manifest"] = [_tpf_entry(f) for f in manifest["pixel_files"]]
        rec["light_curve_sectors"] = sorted({int(f["sector"]) for f in manifest["files"]})
        rec["pixel_file_sectors"] = sorted({int(f["sector"]) for f in manifest["pixel_files"]})
        rec["listed_sectors"] = target["sectors"]
        downloaded = set(rec["light_curve_sectors"]) | set(rec["pixel_file_sectors"])
        rec["sectors_beyond_listed"] = sorted(downloaded - set(target["sectors"]))
        data = TessAdapter().load(tgt, plan_dict, DATA)
        flat = detrend(data.lc, plan.detrend)
        pw, searched = global_prewhitening(data, plan, flat)
        given, window = fixed_candidate(searched, target)
        gauntlet = attack_candidate(data, given, plan, None, None, pw)
        tests = enforce_coverage(gauntlet.tests)
        tests = enforce_sensitivity(tests, registry_for(plan))
        tests, deferred = defer_tests(tests, dict(plan.discovery.stages), 2)
        decisive, _ = expected_by_role(plan, False)
        verdict, reason = aggregate([t for t in tests if t.name in decisive], expected=decisive)
        cand = gauntlet.candidate
        published = float(target["period_days"])
        epoch = float(target["epoch_bjd"]) - BTJD
        duration_h = float(target["duration_hours"])
        found = None if cand is None else float(cand.period)
        factor = matching_factor(published, found, FACTORS, IDENTITY_TOLERANCE)
        final_offset = None if cand is None else epoch_offset_hours(float(cand.t0), epoch,
                                                                    published)  # fmt: skip
        rec.update(
            {
                "status": "OK",
                "given": {
                    "period_days": given.period,
                    "t0_btjd": given.t0,
                    "duration_hours": given.duration * 24.0,
                    "snr": given.snr,
                    "n_transits": given.n_transits,
                },  # fmt: skip
                "window": window,
                "candidate": None
                if cand is None
                else {
                    "period_days": found,
                    "t0_btjd": float(cand.t0),
                    "snr": float(cand.snr),
                    "duration_hours": float(cand.duration) * 24.0,
                },  # fmt: skip
                "tests": {t.name: _test(t) for t in tests},
                "decisive": list(decisive),
                "deferred": deferred,
                "outcome": verdict.value,
                "outcome_reason": reason,
                "identity": {
                    "toi_period_days": published,
                    "found_period_days": found,
                    "factor": factor,
                    "epoch_offset_hours": None if final_offset is None else abs(final_offset),
                    "signed_epoch_offset_hours": final_offset,
                    "toi_duration_hours": duration_h,
                    "left_window": final_offset is not None
                    and abs(final_offset) > window["window_half_width_hours"],
                    "matched": factor == 1.0
                    and final_offset is not None
                    and abs(final_offset) <= duration_h / 2.0,
                },
            }
        )
    except Exception as exc:  # noqa: BLE001 - recorded, never hidden
        rec.update({"status": "ERROR", "reason": f"{type(exc).__name__}: {exc}",
                    "trace": traceback.format_exc()[-1500:]})  # fmt: skip
    finally:
        rec["cpu_seconds"] = time.process_time() - started
        rec["wall_seconds"] = time.time() - wall
        rec["ended_utc"] = utc()
    return rec


# --- records, disk, deletion ------------------------------------------------------------


def _plain(value):
    return value.item() if hasattr(value, "item") else str(value)


def _write_json(path: Path, obj: dict) -> str:
    """Atomic write, then read back and compared; returns the text written."""
    text = json.dumps(obj, indent=1, default=_plain)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(text, "utf-8")
    os.replace(tmp, path)
    if path.read_text("utf-8") != text:
        raise RuntimeError(f"{path.name} did not read back as written")
    return text


def disk_bytes(root: Path = WORK) -> int:
    """Bytes of every regular file under ``root``; links and junctions are not followed."""
    total, stack = 0, [str(root)]
    while stack:
        try:
            entries = list(os.scandir(stack.pop()))
        except FileNotFoundError:
            continue
        for e in entries:
            try:
                if e.is_symlink() or e.is_junction():
                    continue
                if e.is_dir(follow_symlinks=False):
                    stack.append(e.path)
                elif e.is_file(follow_symlinks=False):
                    total += e.stat(follow_symlinks=False).st_size
            except FileNotFoundError:
                continue
    return total


class Monitor(threading.Thread):
    """Samples the disk and keeps the in-flight marker's heartbeat."""

    def __init__(self) -> None:
        super().__init__(daemon=True)
        self.peak = disk_bytes()
        self.samples = 1
        self.flight: dict[str, float] = {}
        self.lock = threading.Lock()
        self._halt = threading.Event()
        self.beat()

    def beat(self) -> None:
        with self.lock:
            flight = dict(self.flight)
        MARKER.parent.mkdir(parents=True, exist_ok=True)
        _write_json(
            MARKER,
            {"heartbeat": time.time(), "interval_seconds": SAMPLE_SECONDS, "in_flight": flight},
        )

    def run(self) -> None:
        while not self._halt.wait(SAMPLE_SECONDS):
            self.peak = max(self.peak, disk_bytes())
            self.samples += 1
            self.beat()

    def stop(self) -> None:
        self._halt.set()
        self.join()
        self.peak = max(self.peak, disk_bytes())
        MARKER.unlink()


def _no_link(path: Path) -> bool:
    """No component from ``.cache`` down to ``path`` is a link or a junction."""
    p = path
    while True:
        if p.is_symlink() or p.is_junction():
            return False
        if p == CACHE or p.parent == p:
            return p == CACHE
        p = p.parent


def delete_literal(path: Path, tic_id: int, expected_sha256: str) -> int:
    """Delete one pixel file of ``tic_id`` by its literal path, inside
    ``.cache/v057/data/lightkurve`` only, after its SHA-256 is checked."""
    path = Path(os.path.abspath(path))
    base = Path(os.path.abspath(LIGHTKURVE))
    if base not in path.parents or not path.name.endswith("_tp.fits"):
        raise RuntimeError(f"refused: {path.name} is not a pixel file inside the cache")
    if f"-{int(tic_id):016d}-" not in path.name:
        raise RuntimeError(f"refused: {path.name} is not a pixel file of TIC {tic_id}")
    if not _no_link(path) or os.path.normcase(str(path.resolve())) != os.path.normcase(str(path)):
        raise RuntimeError(f"refused: a link or junction on the path of {path.name}")
    if not path.is_file():
        raise RuntimeError(f"refused: {path.name} is not a regular file")
    if sha256_path(path) != expected_sha256:
        raise RuntimeError(f"refused: {path.name}'s SHA-256 differs from its manifest")
    size = path.stat().st_size
    path.unlink()
    return size


def release_tpfs(target_key: str, tic_id: int) -> dict:
    """Write the target's TPF manifest to a new record, read it back, then delete its pixel files
    (as v0.5.6 part A's runner does)."""
    from refute.packs.tess.adapter import manifest_path

    log_path = TPF_LOGS / f"{target_key}.json"
    log = json.loads(log_path.read_text("utf-8")) if log_path.exists() else None
    if log is not None and log.get("status") == "deleted":
        return log
    listed = {}
    mpath = manifest_path(DATA, tic_id)
    if mpath.exists():
        for f in json.loads(mpath.read_text("utf-8")).get("pixel_files", []):
            listed[f["path"]] = _tpf_entry(f)
    entries = list(log["tpf_manifest"]) if log is not None else []
    known = {e["path"] for e in entries}
    for f in _tic_files(tic_id, "_tp.fits"):
        rel = f.relative_to(DATA).as_posix()
        if rel in known:
            continue
        size = f.stat().st_size
        entry = listed.get(rel)
        if entry is None or entry["bytes"] != size:
            entry = {
                "name": f.name,
                "path": rel,
                "sector": int(f.name.split("-s")[1][:4]),
                "bytes": size,
                "sha256": sha256_path(f),
                "obs_id": None,
                "data_uri": None,
                "url": None,
                "source": "the file (not in the adapter's manifest at this path and size)",
            }
        if log is not None:
            entry = {**entry, "added_on_resume": True}
        entries.append(entry)
    log = {
        "target_key": target_key,
        "tic_id": tic_id,
        "mode": "exploratory",
        "limits_label": LABEL,
        "status": "manifest-written",
        "written_utc": (log or {}).get("written_utc", utc()),
        "tpf_manifest": entries,
        "listed_by_adapter_not_on_disk": sorted(
            listed[p]["name"] for p in set(listed) - {e["path"] for e in entries}
        ),
    }
    TPF_LOGS.mkdir(parents=True, exist_ok=True)
    _write_json(log_path, log)
    freed, absent = 0, []
    for e in entries:
        path = DATA / e["path"]
        if not path.exists():
            absent.append(e["name"])
            continue
        freed += delete_literal(path, tic_id, e["sha256"])
    log.update({"status": "deleted", "deleted_utc": utc(), "bytes_deleted": freed,
                "absent_at_deletion": absent})  # fmt: skip
    _write_json(log_path, log)
    return log


# --- ledger ------------------------------------------------------------------------------


def _ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text("utf-8"))
    return {
        "mode": "exploratory",
        "limits_label": LABEL,
        "cap_cpu_hours": CAP_CPU_HOURS,
        "cap_disk_bytes": CAP_DISK_BYTES,
        "batches": [],
    }


def _save_ledger(ledger: dict) -> None:
    tmp = LEDGER.with_name(LEDGER.name + ".tmp")
    tmp.write_text(json.dumps(ledger, indent=1) + "\n", "utf-8", newline="\n")
    os.replace(tmp, LEDGER)


def _records() -> list[dict]:
    return [json.loads(f.read_text("utf-8")) for f in sorted(RECORDS.glob("*.json"))]


def _spent() -> tuple[float, int, int]:
    recs = _records()
    cpu = sum(r.get("cpu_seconds", 0.0) for r in recs)
    return cpu / 3600.0, sum(r.get("bytes", 0) for r in recs), len(recs)


def _charged() -> float:
    ledger = _ledger()
    extra = sum(i.get("cpu_hours_upper_bound", 0.0) for i in ledger.get("interruptions", []))
    extra += sum(b.get("parent_cpu_hours", 0.0) for b in ledger.get("batches", []))
    extra += sum(s.get("parent_cpu_hours", 0.0) for s in ledger.get("sweeps", []))
    return _spent()[0] + extra


def _totals() -> dict:
    recs = _records()
    logs = [json.loads(f.read_text("utf-8")) for f in sorted(TPF_LOGS.glob("*.json"))]
    return {
        "records": len(recs),
        "downloaded_bytes_recorded": sum(r.get("downloaded_bytes", 0) for r in recs),
        "reused_bytes_recorded": sum(r.get("reused_bytes", 0) for r in recs),
        "tpf_bytes_deleted": sum(g.get("bytes_deleted", 0) for g in logs),
        "tpf_deletion_records": len(logs),
    }


def charge_interruption() -> dict | None:
    """After an unclean end, charge the lost CPU of the targets that were in flight."""
    if not MARKER.exists():
        return None
    m = json.loads(MARKER.read_text("utf-8"))
    end = m["heartbeat"] + 2 * m["interval_seconds"]
    lost = {
        k: max(0.0, end - s)
        for k, s in m["in_flight"].items()
        if not (RECORDS / f"{k}.json").exists()
    }
    entry = {
        "detected_utc": utc(),
        "last_heartbeat_utc": utc(m["heartbeat"]),
        "targets_in_flight_without_record": sorted(lost),
        "cpu_hours_upper_bound": round(sum(lost.values()) / 3600.0, 4),
        "rule": "wall time of each unrecorded in-flight target up to the last heartbeat plus two "
        "intervals (one process each, so CPU time cannot exceed it)",
    }
    ledger = _ledger()
    ledger.setdefault("interruptions", []).append(entry)
    _save_ledger(ledger)
    MARKER.unlink()
    return entry


def _finish(rec: dict) -> str | None:
    RECORDS.mkdir(parents=True, exist_ok=True)
    try:
        _write_json(RECORDS / f"{rec['target_key']}.json", rec)
    except Exception as exc:  # noqa: BLE001 - stops the run
        return f"{rec['target_key']}'s record could not be written: {exc}"
    try:
        release_tpfs(rec["target_key"], int(rec["tic_id"]))
    except Exception as exc:  # noqa: BLE001 - stops the run
        return f"{rec['target_key']}'s pixel files were not released: {exc}"
    return None


def sweep() -> list[str]:
    done = []
    for f in sorted(RECORDS.glob("*.json")):
        r = json.loads(f.read_text("utf-8"))
        log = TPF_LOGS / f"{r['target_key']}.json"
        if log.exists() and json.loads(log.read_text("utf-8")).get("status") == "deleted":
            continue
        release_tpfs(r["target_key"], int(r["tic_id"]))
        done.append(r["target_key"])
    return done


# --- batches ----------------------------------------------------------------------------


def _pick(todo: list[dict], in_flight: dict, elapsed: float) -> int | None | str:
    measured = disk_bytes()
    held = sum(v["reserve"] for v in in_flight.values())
    cpu = _charged() + sum(v["cpu"] for v in in_flight.values())
    for i, t in enumerate(todo):
        if elapsed + est_wall(t) > BATCH_SECONDS:
            continue
        if measured + held + reserve(t) > ADMIT_DISK_BYTES:
            continue
        if cpu + est_cpu_hours(t) > CAP_CPU_HOURS:
            continue
        return i
    if not in_flight and elapsed == 0.0:
        return f"no remaining target fits (disk {measured / 1e9:.2f} GB measured)"
    return None


def _plans() -> tuple[dict, dict]:
    import yaml

    texts = {part: path.read_bytes() for part, path in PLANS.items()}
    plans = {part: yaml.safe_load(t.decode("utf-8"))["test_plan"] for part, t in texts.items()}
    return plans, {part: sha256(t) for part, t in texts.items()}


def run_batch(selection: list[dict], label: str) -> str | None:
    """One batch; returns a STOP reason, or None."""
    plans, plan_shas = _plans()
    RECORDS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    todo = [t for t in selection if not (RECORDS / f"{t['key']}.json").exists()]
    if _charged() >= CAP_CPU_HOURS:
        return f"the cap of {CAP_CPU_HOURS} CPU-h is reached"
    n, k = batch_limits()
    parent_cpu = time.process_time()
    ctx = multiprocessing.get_context("spawn")
    semaphore, fetched = ctx.Semaphore(k), ctx.Queue()
    monitor = Monitor()
    monitor.start()
    start, stop, in_flight, recorded, failures = time.time(), None, {}, 0, []
    with ProcessPoolExecutor(
        max_workers=n, mp_context=ctx, initializer=_init, initargs=(semaphore, fetched)
    ) as pool:
        while True:
            while True:
                try:
                    done_key = fetched.get_nowait()
                except queue.Empty:
                    break
                for v in in_flight.values():
                    if v["key"] == done_key:
                        v["fetching"] = False
            while todo and stop is None and len(in_flight) < n:
                if sum(v["fetching"] for v in in_flight.values()) >= k:
                    break
                elapsed = 0.0 if not in_flight and recorded == 0 else time.time() - start
                i = _pick(todo, in_flight, elapsed)
                if isinstance(i, str):
                    stop = i
                    break
                if i is None:
                    break
                t = todo.pop(i)
                fut = pool.submit(run_one, t, plans[t["part"]])
                in_flight[fut] = {"key": t["key"], "reserve": reserve(t),
                                  "cpu": est_cpu_hours(t), "fetching": True}  # fmt: skip
                with monitor.lock:
                    monitor.flight[t["key"]] = time.time()
            if not in_flight:
                break
            finished, _ = wait(list(in_flight), timeout=SAMPLE_SECONDS, return_when=FIRST_COMPLETED)
            for fut in finished:
                v = in_flight.pop(fut)
                try:
                    rec = fut.result()
                except Exception as exc:  # noqa: BLE001 - a worker failure stops admission
                    with monitor.lock:
                        monitor.flight.pop(v["key"], None)
                    failures.append(f"{v['key']}: {type(exc).__name__}: {exc}")
                    stop = stop or f"a worker failed on {v['key']}"
                    continue
                problem = _finish(rec)
                with monitor.lock:
                    monitor.flight.pop(v["key"], None)
                if problem:
                    failures.append(problem)
                    stop = stop or problem
                    continue
                recorded += 1
                print(rec["target_key"], rec["status"], rec.get("outcome"),
                      round(rec["cpu_seconds"]), f"charged {_charged():.2f} CPU-h",
                      f"peak {monitor.peak / 1e9:.2f} GB", flush=True)  # fmt: skip
            if monitor.peak > CAP_DISK_BYTES and stop is None:
                stop = f"the disk peak passed {CAP_DISK_BYTES / 1e9:.0f} GB"
    monitor.stop()
    if monitor.peak > CAP_DISK_BYTES and stop is None:
        stop = f"the disk peak passed {CAP_DISK_BYTES / 1e9:.0f} GB"
    spent, nbytes, done = _spent()
    ledger = _ledger()
    ledger["batches"].append(
        {
            "label": label,
            "started_utc": utc(start),
            "ended_utc": utc(),
            "wall_seconds": round(time.time() - start, 1),
            "workers": n,
            "simultaneous_downloads": k,
            "test_plan_sha256": plan_shas,
            "code_sha256": sha256(Path(__file__).read_bytes()),
            "recorded_in_batch": recorded,
            "records": done,
            "cpu_hours_spent": round(spent, 4),
            "parent_cpu_hours": round((time.process_time() - parent_cpu) / 3600.0, 6),
            "bytes": nbytes,
            "disk_peak_bytes": monitor.peak,
            "disk_samples": monitor.samples,
            **_totals(),
            "failures": failures,
            "stop": stop,
        }
    )
    ledger["disk_peak_bytes"] = max(ledger.get("disk_peak_bytes", 0), monitor.peak)
    _save_ledger(ledger)
    ledger["batches"][-1]["cpu_hours_charged"] = round(_charged(), 4)
    _save_ledger(ledger)
    return stop


# --- the pilot's comparison ----------------------------------------------------------------


def compare(fixed: dict, searched: dict) -> dict:
    """Is the fixed-mode record the search-mode record, test by test?"""
    names = sorted(set(fixed.get("tests", {})) | set(searched.get("tests", {})))
    differ = [
        n
        for n in names
        if (fixed.get("tests", {}).get(n) or {}).get("status")
        != (searched.get("tests", {}).get(n) or {}).get("status")
    ]
    same_outcome = fixed.get("outcome") == searched.get("outcome")
    return {
        "target_key": fixed["target_key"],
        "fixed_status": fixed.get("status"),
        "outcome_search": searched.get("outcome"),
        "outcome_fixed": fixed.get("outcome"),
        "tests_differing": differ,
        "reproduced": fixed.get("status") == "OK" and same_outcome and not differ,
    }


def pilot_comparison(pilot: list[dict]) -> dict:
    searched = search_records()
    rows = []
    for t in pilot:
        path = RECORDS / f"{t['key']}.json"
        if not path.exists():
            rows.append({"target_key": t["key"], "fixed_status": "NO RECORD", "reproduced": False})
            continue
        rows.append(compare(json.loads(path.read_text("utf-8")), searched[t["key"]]))
    n = sum(r["reproduced"] for r in rows)
    return {
        "mode": "exploratory",
        "limits_label": LABEL,
        "rule": f"reproduced = same outcome and the same status for every test; the run goes on "
        f"only if at least {PILOT_MIN_REPRODUCED} of {len(pilot)} are reproduced",
        "code_sha256": sha256(Path(__file__).read_bytes()),
        "written_utc": utc(),
        "rows": rows,
        "reproduced": n,
        "stop": n < PILOT_MIN_REPRODUCED,
    }


def clean() -> None:
    """Delete the light curves at the end (regenerable), by literal path, refusing links."""
    if not LIGHTKURVE.exists():
        print("nothing to clean")
        return
    if not _no_link(LIGHTKURVE):
        raise SystemExit("refused: a link or junction on the path")
    for dirpath, dirnames, filenames in os.walk(LIGHTKURVE, followlinks=False):
        for name in dirnames + filenames:
            p = Path(dirpath) / name
            if p.is_symlink() or p.is_junction():
                raise SystemExit(f"refused: a link or junction inside: {p}")
    size = disk_bytes(LIGHTKURVE)
    shutil.rmtree(LIGHTKURVE)
    print(f"removed {LIGHTKURVE} ({size} bytes)")


def main(step: str) -> None:
    all_targets = targets()
    if step == "pilot":
        pilot = pilot_set(all_targets)
        if len(pilot) != sum(PILOT_PICK.values()) * 2:
            raise SystemExit(f"the pilot set has {len(pilot)} TOIs, not 10")
        stop = run_batch(pilot, "pilot")
        result = pilot_comparison(pilot)
        result["batch_stop"] = stop
        _write_json(PILOT_RESULT, result)
        print(json.dumps({k: result[k] for k in ("reproduced", "stop")}), flush=True)
    elif step == "rest":
        if not PILOT_RESULT.exists():
            raise SystemExit("no pilot result")
        pilot = json.loads(PILOT_RESULT.read_text("utf-8"))
        if pilot["stop"] or pilot["reproduced"] < PILOT_MIN_REPRODUCED:
            raise SystemExit("the pilot did not reproduce at least 9 of 10: STOP")
        charged = charge_interruption()
        if charged:
            print("interruption charged:", json.dumps(charged), flush=True)
        parent_cpu = time.process_time()
        released = sweep()
        ledger = _ledger()
        ledger.setdefault("sweeps", []).append(
            {"utc": utc(), "released": released,
             "parent_cpu_hours": round((time.process_time() - parent_cpu) / 3600.0, 6)}
        )  # fmt: skip
        _save_ledger(ledger)
        while any(not (RECORDS / f"{t['key']}.json").exists() for t in all_targets):
            stop = run_batch(all_targets, "rest")
            if stop:
                print("STOP:", stop, flush=True)
                raise SystemExit(2)
        print("all targets recorded", json.dumps(_totals()), flush=True)
    elif step == "clean":
        clean()
    else:
        raise SystemExit("usage: fixed_run.py pilot|rest|clean")


if __name__ == "__main__":
    main(sys.argv[1])
