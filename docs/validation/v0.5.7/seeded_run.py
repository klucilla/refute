"""v0.5.7 (exploratory): the labelled v0.5 battery, unchanged, seeded by the TOI's ephemeris, for
the 540 TOIs of v0.5.6 parts A and B (docs/plans/v0.5.7-plan.md).

The decisions behind it (#218): the opening of 2026-11-23, received at 10:41 local (comment
7102888515), and the design decision received at 11:01 local (comment 7103371874). The second
chose mode A: TOI-seeded, the battery unchanged.

**What runs:** for each TOI, the TESS adapter's download (SPOC 120-s light curves and pixel files,
into ``.cache/v057/data``), then the v0.5 battery **unchanged**, with the test plan the TOI's
v0.5.6 run used (part A: ``calibration/v0.5/claim.yaml``; part B:
``calibration/v0.5.6/claim.yaml``), stage 2, with no catalog test. The steps are the same calls
as v0.5.6's runners:
- detrending and prewhitening;
- ``attack_candidate``;
- the coverage and sensitivity rules;
- deferral and the decisive aggregate.

The only difference is the seed handed to ``attack_candidate``: no search is run. Nothing in
``src/`` changes, and nothing holds the period or the epoch inside the battery.

**The TOI-seeded candidate:**
- **The seed:** the TOI's period and duration, and the TOI's epoch moved to the best offset in a
  window of ± one TOI duration.
  - The window is a weighted box of the TOI's duration, on a grid centred on the propagated
    epoch, in two-minute steps that never pass the window's edge.
  - An offset is kept only if its depth SNR is at least 3.0, a heuristic for the start, not a
    significance. Otherwise the propagated epoch is used, and the record says so.
- **What the seed sets:** the battery's detrending mask, and the start of its fit.
- **What the battery refits**, by its own ``finalize_candidate``: the period (within one
  refinement step), the epoch (over the whole phase), the duration, the depth and the SNR. Every
  test sees that fit.

**Every record keeps** (the design decision, item 2):
- **The ephemeris:**
  - the TOI's period and the battery's final period, their factor and their difference;
  - the largest epoch residual across the data, in units of the TOI's duration;
  - the TOI transits covered by data;
  - ``stayed_on_toi_ephemeris``, by v0.5.6's matching rule: factor 1 within 0.001, and the final
    epoch within half a TOI duration of the propagated one.
- **The window and the provenance of the inputs** against the TOI's v0.5.6 record.
- **The record's own fields:** a machine ``started_utc``, ``mode: exploratory``, the limits label,
  ``method_status: not_validated``, and ``coverage_state`` (``measured`` from the tests, or
  ``unavailable``).

Zero coverage stays INCONCLUSIVE (``enforce_coverage``). Outputs are never verdicts on a TOI,
never candidates and never a disposition.

**Inputs bound to v0.5.6** (Codex's design round, blocking item 3):
- After the download, the target's light-curve and pixel-file sectors must equal those of its
  v0.5.6 record. Otherwise the target is **not analyzed** (``status: INPUTS_DIFFER``, with the
  differences).
- With the same sectors, the SHA-256 of every pixel file (both parts) and of every light curve
  (part B; part A stored none) is compared.
- The record's provenance is ``same``, ``different`` (the same sectors, other bytes) or ``unknown``
  (part A's light curves).

**Caps and machine** (the opening, item 3; Codex's design round, blocking item 5):
- **CPU:** 20 CPU-h for everything of the phase. Charged as:
  - the larger of the records' CPU and the workers' measured process CPU (Windows
    ``GetProcessTimes``, which includes failed attempts);
  - plus the controller's own CPU;
  - plus an upper bound for any unclean end.
- **Disk:** a peak of 20 GB over everything under ``.cache/v057``.
  - Admission is held at 18 GB, sampled every 2 s.
  - Every cache (XDG, Astropy, Matplotlib, TEMP and TMP) is set inside ``.cache/v057`` before any
    import, so it is measured too.
  - A sample over 20 GB stops admission.
- **Pixel files** are deleted per target, after a manifest is written and read back to
  ``.cache/v057/run/tpf-deletions``.
- **Light curves** are deleted at the end by ``clean``. It deletes only the light curves the
  adapter's manifests list, by literal path with SHA-256, with a log. It runs only after a
  terminal state, with no lock held, and with every pixel file released.
- **Workers and downloads:** Monday to Friday, 08:00 to 18:00, at most 10 workers and 2
  simultaneous downloads; otherwise up to 20 and 6. The smaller of the limits now and 30 minutes
  later applies to a batch.
- **Batches:** admission stops after 28 minutes, and then the batch drains. BelowNormal priority,
  CPUs 8 to 31 (``pinrun``).
- **The deadline:** no target is admitted after 2026-12-03 23:59 local.
- **The lock:** one exclusive run lock for ``pilot``, ``rest`` and ``clean``. A lock whose process
  no longer exists is reported and removed only by the next start.
- **Resumable:** one record per target; a recorded target never runs again. The in-flight marker
  is written before each dispatch, and an unclean end is charged by an upper bound before any
  step runs again.

**The pilot** (the plan, "The pilot and the stop"):
- **The set:** the first 3 matched planet records and the first 2 matched others of each part, in
  draw order, from the v0.5.6 records stored in git.
- **Reproduced** means the same outcome and the same status for every test as the v0.5.6 record.
  Each row also carries its provenance.
- **``rest`` runs only if:**
  - the pilot has ten terminal rows and at least nine are reproduced;
  - the pilot's batch did not stop;
  - the runner, the plans, the draws and the v0.5.6 bundles still have the SHA-256 the pilot
    recorded.

Usage (from the project root, pinned):
- ``seeded_run.py pilot``
- ``seeded_run.py rest``
- ``seeded_run.py clean``
"""

from __future__ import annotations

import ctypes
import datetime as dt
import hashlib
import json
import math
import multiprocessing
import os
import queue
import sys
import threading
import time
import traceback
from concurrent.futures import FIRST_COMPLETED, ProcessPoolExecutor, wait
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CACHE = ROOT / ".cache"
WORK = CACHE / "v057"

# Every cache inside .cache/v057: set by ``isolate_caches`` when the runner starts, before any
# scientific package is imported; spawned workers inherit the environment.
ENV_DIRS = {
    "XDG_CACHE_HOME": "env/xdg-cache",
    "XDG_CONFIG_HOME": "env/xdg-config",
    "ASTROPY_CACHE_DIR": "env/astropy-cache",
    "ASTROPY_CONFIG_DIR": "env/astropy-config",
    "MPLCONFIGDIR": "env/matplotlib",
    "TEMP": "env/tmp",
    "TMP": "env/tmp",
}


def isolate_caches() -> dict[str, str]:
    for name, rel in ENV_DIRS.items():
        (WORK / rel).mkdir(parents=True, exist_ok=True)
        os.environ[name] = str(WORK / rel)
    return {name: os.environ[name] for name in ENV_DIRS}


V056 = ROOT / "docs/validation/v0.5.6"
PLANS = {"A": ROOT / "calibration/v0.5/claim.yaml", "B": ROOT / "calibration/v0.5.6/claim.yaml"}
DRAWS = {"A": V056 / "part-a-draw.json", "B": ROOT / "calibration/v0.5.6/part-b-draw.json"}
BUNDLES = {"A": V056 / "part-a-records.json", "B": V056 / "part-b-records.json"}
LEDGER = HERE / "seeded-ledger.json"
PILOT_RESULT = HERE / "seeded-pilot.json"
DATA = WORK / "data"
LIGHTKURVE = DATA / "lightkurve"
RECORDS = WORK / "run/records"
TPF_LOGS = WORK / "run/tpf-deletions"
LC_LOG = WORK / "run/lc-deletions.json"
MARKER = WORK / "run/in-flight.json"
LOCK = WORK / "run/run.lock"
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"
CAP_CPU_HOURS = 20.0
CAP_DISK_BYTES = 20e9
ADMIT_DISK_BYTES = 18e9
RESERVE_PER_SECTOR = 101_220_480 + 4_164_480  # v0.5.6 part A's largest per-sector size
BATCH_SECONDS = 28 * 60
SAMPLE_SECONDS = 2.0
WALL_BASE, WALL_PER_SECTOR = 65.0, 25.0
CPU_BASE, CPU_PER_SECTOR = 40.0, 20.0
DEADLINE = dt.datetime(2026, 12, 3, 23, 59)
BTJD = 2457000.0
IDENTITY_TOLERANCE = 0.001
FACTORS = (1.0, 2.0, 0.5)
WINDOW_DURATIONS = 1.0  # the seed's epoch window: +- this many TOI durations
STEP_DAYS = 2.0 / 1440.0  # two minutes
MIN_WINDOW_SNR = 3.0  # a heuristic to choose the seed, not a significance
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
    """(workers, simultaneous downloads) at a local moment."""
    now = now or dt.datetime.now()
    business = now.weekday() < 5 and 8 <= now.hour < 18
    return (10, 2) if business else (20, 6)


def batch_limits() -> tuple[int, int]:
    now = dt.datetime.now()
    a, b = limits(now), limits(now + dt.timedelta(minutes=30))
    return min(a[0], b[0]), min(a[1], b[1])


def fingerprints() -> dict[str, str]:
    """The SHA-256 of the runner, the report script, the plans, the draws and the v0.5.6 bundles."""
    files = {
        "runner": Path(__file__),
        "report": HERE / "seeded_report.py",
        **{f"plan_{p}": v for p, v in PLANS.items()},
        **{f"draw_{p}": v for p, v in DRAWS.items()},
        **{f"bundle_{p}": v for p, v in BUNDLES.items()},
    }
    return {k: sha256(v.read_bytes()) for k, v in files.items()}


# --- process facts (Windows) -------------------------------------------------------------

_PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
_STILL_ACTIVE = 259


def _handle(pid: int):
    return ctypes.windll.kernel32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))


def process_alive(pid: int) -> bool:
    h = _handle(pid)
    if not h:
        return False
    try:
        code = ctypes.c_ulong()
        ok = ctypes.windll.kernel32.GetExitCodeProcess(h, ctypes.byref(code))
        return bool(ok) and code.value == _STILL_ACTIVE
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


def process_cpu_seconds(pid: int) -> float | None:
    """User plus kernel CPU of a process (100-ns units), or None if it cannot be read."""
    h = _handle(pid)
    if not h:
        return None
    try:
        t = [ctypes.c_ulonglong() for _ in range(4)]
        if not ctypes.windll.kernel32.GetProcessTimes(h, *(ctypes.byref(x) for x in t)):
            return None
        return (t[2].value + t[3].value) / 1e7
    finally:
        ctypes.windll.kernel32.CloseHandle(h)


class RunLock:
    """One exclusive lock for pilot, rest and clean: a file created exclusively with this PID."""

    def __enter__(self):
        LOCK.parent.mkdir(parents=True, exist_ok=True)
        if LOCK.exists():
            held = json.loads(LOCK.read_text("utf-8"))
            if process_alive(held["pid"]):
                raise SystemExit(f"refused: the run lock is held by PID {held['pid']}")
            print(f"a stale run lock (PID {held['pid']}, {held['utc']}) is removed", flush=True)
            LOCK.unlink()
        fd = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, json.dumps({"pid": os.getpid(), "utc": utc()}).encode())
        os.close(fd)
        return self

    def __exit__(self, *exc):
        LOCK.unlink(missing_ok=True)


# --- targets and the v0.5.6 records ----------------------------------------------------------


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
    if len(set(keys)) != len(keys) or len(keys) != 540:
        raise SystemExit("the cohort is not 540 unique TICs")
    return out


def search_records() -> dict[str, dict]:
    """The v0.5.6 records (search mode), from the bundles in git, by target key."""
    out = {}
    for part, path in BUNDLES.items():
        for item in json.loads(path.read_text("utf-8"))["records"]:
            content = item["content"]
            out[content["target_key"]] = {**content, "_part": part}
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


def _file_entry(f: dict) -> dict:
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


# --- the seed and the ephemeris record (pure functions: the tests call them) -------------------


def window_offsets(period: float, duration: float) -> tuple[np.ndarray, bool]:
    """The centred grid of offsets (days), never past the window's edge; if the window spans the
    whole phase, only offsets in [-P/2, P/2) are used and the second value is True."""
    if not (math.isfinite(period) and math.isfinite(duration) and 0 < duration < period):
        raise ValueError("the seed needs finite values with 0 < duration < period")
    half = WINDOW_DURATIONS * duration
    full = 2.0 * half >= period
    limit = 0.5 * period if full else half
    steps = int(np.floor(limit / STEP_DAYS))
    offsets = np.arange(-steps, steps + 1, dtype=float) * STEP_DAYS
    offsets = offsets[np.abs(offsets) <= limit]
    if full:
        offsets = offsets[offsets < 0.5 * period]
    return offsets, full


def refine_epoch(
    time_: np.ndarray, flux: np.ndarray, sigma: np.ndarray, period: float, epoch: float,
    duration: float,
) -> dict:  # fmt: skip
    """The seed's epoch: the best offset in the window, at the TOI's period and duration.

    For each offset, a weighted box: depth = weighted mean outside the box minus weighted mean
    inside; its error from the weights; SNR = depth / error. The offset with the largest positive
    SNR is kept if that SNR is at least MIN_WINDOW_SNR (a heuristic for the start, not a
    significance); otherwise the propagated epoch is used and ``found`` is False."""
    offsets, full = window_offsets(period, duration)
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
        "window_half_width_hours": WINDOW_DURATIONS * duration * 24.0,
        "spans_full_phase": full,
        "step_minutes": STEP_DAYS * 1440.0,
        "offsets_evaluated": evaluated,
        "found": found,
        "offset_hours": best["offset_days"] * 24.0 if found else 0.0,
        "best_snr": None if not np.isfinite(best["snr"]) else best["snr"],
        "best_offset_hours": None if not np.isfinite(best["snr"]) else best["offset_days"] * 24.0,
        "seed_depth": best["depth"] if found else None,
        "seed_depth_err": best["depth_err"] if found else None,
        "min_snr": MIN_WINDOW_SNR,
        "note": "the window's depth and SNR choose the seed only; the battery refits them",
    }


def epoch_offset_hours(t0: float, epoch: float, period: float) -> float:
    """The signed distance of ``t0`` from the nearest propagated transit of ``epoch``, in hours,
    in [-P/2, P/2)."""
    return float(((t0 - epoch + 0.5 * period) % period - 0.5 * period) * 24.0)


def ephemeris_record(
    toi_period: float, toi_epoch: float, toi_duration: float, final_period: float | None,
    final_t0: float | None, factor: float | None, t_first: float, t_last: float,
    toi_events_covered: int,
) -> dict:  # fmt: skip
    """The design decision's item 2. The largest epoch residual across the data: the fitted epoch
    is aligned to the nearest TOI cycle; both ephemerides are propagated over the same cycle
    indices to the first and last observed cycles; the residual is the larger difference there,
    in units of the TOI's duration (the difference is linear in the cycle index, so the extremes
    are at the ends)."""
    rec = {
        "toi_period_days": toi_period,
        "final_period_days": final_period,
        "factor": factor,
        "period_difference_days": None if final_period is None else final_period - toi_period,
        "toi_duration_hours": toi_duration * 24.0,
        "toi_events_covered": int(toi_events_covered),
        "any_toi_event_covered": toi_events_covered > 0,
        "final_epoch_offset_hours": None,
        "max_epoch_residual_durations": None,
        "stayed_on_toi_ephemeris": False,
        "rule": "stayed: factor 1 within 0.001 and the final epoch within half a TOI duration of "
        "the propagated one (v0.5.6's matching rule)",
    }
    if final_period is None or final_t0 is None:
        return rec
    offset = epoch_offset_hours(final_t0, toi_epoch, toi_period)
    n0 = round((final_t0 - toi_epoch) / toi_period)
    residuals = []
    for t_edge in (t_first, t_last):
        n = round((t_edge - toi_epoch) / toi_period)
        toi_time = toi_epoch + n * toi_period
        fit_time = final_t0 + (n - n0) * final_period
        residuals.append(abs(fit_time - toi_time))
    rec.update(
        {
            "final_epoch_offset_hours": offset,
            "max_epoch_residual_durations": max(residuals) / toi_duration,
            "stayed_on_toi_ephemeris": factor == 1.0 and abs(offset) <= toi_duration * 24.0 / 2.0,
        }
    )
    return rec


def provenance(now_lc: list[dict], now_tpf: list[dict], hist: dict | None) -> dict:
    """The inputs against the TOI's v0.5.6 record: the sectors must be equal (otherwise
    ``refuse``); with equal sectors, the SHA-256 of each file is compared where the history has
    it."""
    out = {"refuse": False, "sector_differences": {}, "light_curves": "unknown",
           "pixel_files": "unknown"}  # fmt: skip
    if hist is None or "light_curve_sectors" not in hist or "pixel_file_sectors" not in hist:
        out["overall"] = "unknown"
        out["note"] = "the v0.5.6 record has no sector lists (it ended before its download)"
        return out
    lc_now = sorted({int(f["sector"]) for f in now_lc})
    tpf_now = sorted({int(f["sector"]) for f in now_tpf})
    for kind, now, then in (("light_curves", lc_now, hist["light_curve_sectors"]),
                            ("pixel_files", tpf_now, hist["pixel_file_sectors"])):  # fmt: skip
        if list(now) != list(then):
            out["sector_differences"][kind] = {"now": now, "v056": list(then)}
    if out["sector_differences"]:
        out.update({"refuse": True, "overall": "different"})
        return out

    def compare(now: list[dict], then: list[dict] | None) -> str:
        if then is None:
            return "unknown"
        a = {f["name"]: f["sha256"] for f in now}
        b = {f["name"]: f["sha256"] for f in then}
        return "same" if a == b else "different"

    out["light_curves"] = compare(now_lc, hist.get("light_curve_manifest"))
    out["pixel_files"] = compare(now_tpf, hist.get("tpf_manifest"))
    kinds = (out["light_curves"], out["pixel_files"])
    out["overall"] = (
        "different" if "different" in kinds else "unknown" if "unknown" in kinds else "same"
    )
    return out


def seed_candidate(searched, target: dict):
    """The seed handed to ``attack_candidate``: the TOI's period and duration, the epoch from the
    window. Its depth and SNR are the window's; the battery refits everything."""
    from refute.packs.tess.events import per_point_sigma
    from refute.packs.tess.search import count_transits
    from refute.packs.tess.types import Candidate

    period = float(target["period_days"])
    duration = float(target["duration_hours"]) / 24.0
    epoch = float(target["epoch_bjd"]) - BTJD
    sigma = per_point_sigma(searched)
    window = refine_epoch(searched.time, searched.flux, sigma, period, epoch, duration)
    t0 = epoch + window["offset_hours"] / 24.0
    snr = window["best_snr"] if window["found"] else 0.0
    cand = Candidate(
        period=period,
        t0=t0,
        duration=duration,
        depth=float(window["seed_depth"] or 0.0),
        depth_err=float(window["seed_depth_err"] or float("nan")),
        snr=float(snr),
        log_likelihood=0.5 * float(snr) ** 2,
        sde=0.0,  # not searched: shown as unavailable in the record
        n_transits=count_transits(searched, period, t0, duration),
    )
    return cand, window


def run_one(target: dict, test_plan: dict, hist: dict | None) -> dict:
    """One TIC, TOI-seeded: download, the provenance check, the seed, the unchanged battery, the
    ephemeris record. Any failure is recorded, never hidden."""
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
    from refute.packs.tess.search import count_transits

    started, wall = time.process_time(), time.time()
    rec = {
        "target_key": target["key"],
        "tic_id": target["tic_id"],
        "toi": target["toi"],
        "part": target["part"],
        "arm": target["arm"],
        "rank": target["rank"],
        "mode": "exploratory",
        "candidate_mode": "TOI-seeded (the battery unchanged refits the seed)",
        "limits_label": LABEL,
        "method_status": "not_validated",
        "started_utc": utc(wall),
        "worker_pid": os.getpid(),
        "test_plan_source": PLANS[target["part"]].relative_to(ROOT).as_posix(),
        "coverage_state": "unavailable",
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
        rec["light_curve_manifest"] = [_file_entry(f) for f in manifest["files"]]
        rec["tpf_manifest"] = [_file_entry(f) for f in manifest["pixel_files"]]
        rec["light_curve_sectors"] = sorted({int(f["sector"]) for f in manifest["files"]})
        rec["pixel_file_sectors"] = sorted({int(f["sector"]) for f in manifest["pixel_files"]})
        rec["listed_sectors"] = target["sectors"]
        prov = provenance(manifest["files"], manifest["pixel_files"], hist)
        rec["provenance"] = prov
        if prov["refuse"]:
            reason = "the downloaded sectors differ from the v0.5.6 record"
            rec.update({"status": "INPUTS_DIFFER", "reason": reason})
            return rec
        data = TessAdapter().load(tgt, plan_dict, DATA)
        flat = detrend(data.lc, plan.detrend)
        pw, searched = global_prewhitening(data, plan, flat)
        seed, window = seed_candidate(searched, target)
        gauntlet = attack_candidate(data, seed, plan, None, None, pw)
        tests = enforce_coverage(gauntlet.tests)
        tests = enforce_sensitivity(tests, registry_for(plan))
        tests, deferred = defer_tests(tests, dict(plan.discovery.stages), 2)
        decisive, _ = expected_by_role(plan, False)
        verdict, reason = aggregate([t for t in tests if t.name in decisive], expected=decisive)
        cand = gauntlet.candidate
        toi_period = float(target["period_days"])
        toi_epoch = float(target["epoch_bjd"]) - BTJD
        toi_duration = float(target["duration_hours"]) / 24.0
        found = None if cand is None else float(cand.period)
        factor = matching_factor(toi_period, found, FACTORS, IDENTITY_TOLERANCE)
        covered = count_transits(data.lc, toi_period, toi_epoch, toi_duration)
        eph = ephemeris_record(
            toi_period, toi_epoch, toi_duration, found, None if cand is None else float(cand.t0),
            factor, float(np.nanmin(data.lc.time)), float(np.nanmax(data.lc.time)), covered,
        )  # fmt: skip
        rec.update(
            {
                "status": "OK",
                "coverage_state": "measured",
                "seed": {
                    "period_days": seed.period,
                    "t0_btjd": seed.t0,
                    "duration_hours": seed.duration * 24.0,
                    "n_transits": seed.n_transits,
                    "sde": None,
                },  # fmt: skip
                "window": window,
                "candidate": None
                if cand is None
                else {
                    "period_days": found,
                    "t0_btjd": float(cand.t0),
                    "duration_hours": float(cand.duration) * 24.0,
                    "depth": float(cand.depth),
                    "depth_err": float(cand.depth_err),
                    "snr": float(cand.snr),
                },  # fmt: skip
                "tests": {t.name: _test(t) for t in tests},
                "decisive": list(decisive),
                "deferred": deferred,
                "outcome": verdict.value,
                "outcome_reason": reason,
                "ephemeris": eph,
                "identity": {
                    "matched": eph["stayed_on_toi_ephemeris"],
                    "rule": "v0.5.6's matching rule, on the battery's final fit",
                },  # fmt: skip
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


# --- records, disk, deletion ----------------------------------------------------------------


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


def delete_literal(path: Path, tic_id: int, expected_sha256: str, suffix: str) -> int:
    """Delete one file of ``tic_id`` ending in ``suffix`` by its literal path, inside
    ``.cache/v057/data/lightkurve`` only, after its SHA-256 is checked."""
    path = Path(os.path.abspath(path))
    base = Path(os.path.abspath(LIGHTKURVE))
    if base not in path.parents or not path.name.endswith(suffix):
        raise RuntimeError(f"refused: {path.name} is not a {suffix} file inside the cache")
    if f"-{int(tic_id):016d}-" not in path.name:
        raise RuntimeError(f"refused: {path.name} is not a file of TIC {tic_id}")
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
            listed[f["path"]] = _file_entry(f)
    entries = list(log["tpf_manifest"]) if log is not None else []
    known = {e["path"] for e in entries}
    for f in _tic_files(tic_id, "_tp.fits"):
        rel = f.relative_to(DATA).as_posix()
        if rel in known:
            continue
        size = f.stat().st_size
        entry = listed.get(rel)
        if entry is None or entry["bytes"] != size:
            entry = {"name": f.name, "path": rel, "sector": int(f.name.split("-s")[1][:4]),
                     "bytes": size, "sha256": sha256_path(f), "obs_id": None, "data_uri": None,
                     "url": None, "source": "the file (not in the adapter's manifest)"}  # fmt: skip
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
        freed += delete_literal(path, tic_id, e["sha256"], "_tp.fits")
    log.update({"status": "deleted", "deleted_utc": utc(), "bytes_deleted": freed,
                "absent_at_deletion": absent})  # fmt: skip
    _write_json(log_path, log)
    return log


# --- ledger -----------------------------------------------------------------------------------


def _ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text("utf-8"))
    return {
        "mode": "exploratory",
        "limits_label": LABEL,
        "cap_cpu_hours": CAP_CPU_HOURS,
        "cap_disk_bytes": CAP_DISK_BYTES,
        "deadline_local": DEADLINE.isoformat(),
        "batches": [],
        "state": "open",
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
    """The larger of the records' CPU and the workers' measured process CPU, plus the controller's
    CPU and the upper bounds of interruptions."""
    ledger = _ledger()
    measured = sum(b.get("worker_process_cpu_hours") or 0.0 for b in ledger.get("batches", []))
    extra = sum(i.get("cpu_hours_upper_bound", 0.0) for i in ledger.get("interruptions", []))
    extra += sum(b.get("parent_cpu_hours", 0.0) for b in ledger.get("batches", []))
    extra += sum(s.get("parent_cpu_hours", 0.0) for s in ledger.get("sweeps", []))
    return max(_spent()[0], measured) + extra


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


# --- batches ----------------------------------------------------------------------------------


def _pick(todo: list[dict], in_flight: dict, elapsed: float) -> int | None | str:
    if dt.datetime.now() > DEADLINE:
        return f"the phase's deadline ({DEADLINE.isoformat()} local) has passed"
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


def _worker_cpu(pool) -> float | None:
    """The process CPU of the pool's live workers, in seconds (None if any cannot be read)."""
    total = 0.0
    for p in list(getattr(pool, "_processes", {}).values()):
        value = process_cpu_seconds(p.pid)
        if value is None:
            return None
        total += value
    return total


def run_batch(selection: list[dict], label: str) -> str | None:
    """One batch; returns a STOP reason, or None."""
    plans, plan_shas = _plans()
    history = search_records()
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
    worker_cpu = None
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
                with monitor.lock:  # the reservation is journaled before the dispatch
                    monitor.flight[t["key"]] = time.time()
                monitor.beat()
                fut = pool.submit(run_one, t, plans[t["part"]], history.get(t["key"]))
                in_flight[fut] = {"key": t["key"], "reserve": reserve(t),
                                  "cpu": est_cpu_hours(t), "fetching": True}  # fmt: skip
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
        worker_cpu = _worker_cpu(pool)  # the workers are still alive here
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
            "fingerprints": fingerprints(),
            "recorded_in_batch": recorded,
            "records": done,
            "cpu_hours_spent_records": round(spent, 4),
            "worker_process_cpu_hours": None if worker_cpu is None else round(worker_cpu / 3600, 4),
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


# --- the pilot's comparison and the end ---------------------------------------------------------


def compare(seeded: dict, searched: dict) -> dict:
    """Is the TOI-seeded record the search-mode record, test by test?"""
    names = sorted(set(seeded.get("tests", {})) | set(searched.get("tests", {})))
    differ = {
        n: {
            "search": (searched.get("tests", {}).get(n) or {}).get("status"),
            "seeded": (seeded.get("tests", {}).get(n) or {}).get("status"),
        }  # fmt: skip
        for n in names
        if (seeded.get("tests", {}).get(n) or {}).get("status")
        != (searched.get("tests", {}).get(n) or {}).get("status")
    }
    same_outcome = seeded.get("outcome") == searched.get("outcome")
    return {
        "target_key": seeded["target_key"],
        "seeded_status": seeded.get("status"),
        "provenance": (seeded.get("provenance") or {}).get("overall"),
        "outcome_search": searched.get("outcome"),
        "outcome_seeded": seeded.get("outcome"),
        "stayed_on_toi_ephemeris": (seeded.get("ephemeris") or {}).get("stayed_on_toi_ephemeris"),
        "tests_differing": differ,
        "reproduced": seeded.get("status") == "OK" and same_outcome and not differ,
    }


def pilot_comparison(pilot: list[dict], batch_stop: str | None) -> dict:
    searched = search_records()
    rows = []
    for t in pilot:
        path = RECORDS / f"{t['key']}.json"
        if not path.exists():
            rows.append({"target_key": t["key"], "seeded_status": "NO RECORD",
                         "reproduced": False})  # fmt: skip
            continue
        rows.append(compare(json.loads(path.read_text("utf-8")), searched[t["key"]]))
    n = sum(r["reproduced"] for r in rows)
    terminal = sum(r["seeded_status"] != "NO RECORD" for r in rows)
    return {
        "mode": "exploratory",
        "limits_label": LABEL,
        "rule": f"reproduced = same outcome and the same status for every test; the run goes on "
        f"only if all {len(pilot)} rows are terminal, at least {PILOT_MIN_REPRODUCED} are "
        f"reproduced and the batch did not stop",
        "fingerprints": fingerprints(),
        "written_utc": utc(),
        "rows": rows,
        "terminal_rows": terminal,
        "reproduced": n,
        "batch_stop": batch_stop,
        "stop": n < PILOT_MIN_REPRODUCED or terminal != len(pilot) or batch_stop is not None,
    }


def clean() -> None:
    """Delete the light curves at the end: only after a terminal state, with every pixel file
    released; only the files the adapter's manifests list, by literal path and SHA-256, with a
    log."""
    from refute.packs.tess.adapter import manifest_path

    ledger = _ledger()
    if ledger.get("state") not in ("complete", "stopped"):
        raise SystemExit(f"refused: the ledger's state is {ledger.get('state')!r}, not terminal")
    if MARKER.exists():
        raise SystemExit("refused: a target is still marked in flight")
    for r in _records():
        log = TPF_LOGS / f"{r['target_key']}.json"
        if not log.exists() or json.loads(log.read_text("utf-8")).get("status") != "deleted":
            raise SystemExit(f"refused: {r['target_key']}'s pixel files are not released")
    entries, freed = [], 0
    for r in _records():
        mpath = manifest_path(DATA, int(r["tic_id"]))
        if not mpath.exists():
            continue
        for f in json.loads(mpath.read_text("utf-8")).get("files", []):
            path = DATA / f["path"]
            if not path.exists():
                entries.append({"path": f["path"], "status": "absent"})
                continue
            freed += delete_literal(path, int(r["tic_id"]), f["sha256"], "_lc.fits")
            entries.append({"path": f["path"], "sha256": f["sha256"], "status": "deleted"})
    _write_json(LC_LOG, {"utc": utc(), "bytes_deleted": freed, "files": entries})
    print(f"light curves deleted: {sum(e['status'] == 'deleted' for e in entries)} files, "
          f"{freed} bytes; log {LC_LOG.relative_to(ROOT).as_posix()}")  # fmt: skip


def _terminal(state: str, reason: str | None = None) -> None:
    ledger = _ledger()
    ledger["state"] = state
    ledger["state_reason"] = reason
    ledger["state_utc"] = utc()
    _save_ledger(ledger)


def main(step: str) -> None:
    all_targets = targets()
    with RunLock():
        if step in ("pilot", "rest"):
            charged = charge_interruption()
            if charged:
                print("interruption charged:", json.dumps(charged), flush=True)
        if step == "pilot":
            pilot = pilot_set(all_targets)
            if len(pilot) != 2 * sum(PILOT_PICK.values()):
                raise SystemExit(f"the pilot set has {len(pilot)} TOIs, not 10")
            stop = run_batch(pilot, "pilot")
            result = pilot_comparison(pilot, stop)
            _write_json(PILOT_RESULT, result)
            if result["stop"]:
                _terminal("stopped", "the pilot did not pass")
            print(json.dumps({k: result[k] for k in ("terminal_rows", "reproduced", "stop")}))
        elif step == "rest":
            if not PILOT_RESULT.exists():
                raise SystemExit("no pilot result")
            pilot = json.loads(PILOT_RESULT.read_text("utf-8"))
            if pilot["stop"] or pilot["reproduced"] < PILOT_MIN_REPRODUCED:
                raise SystemExit("the pilot did not pass: STOP")
            if pilot["fingerprints"] != fingerprints():
                raise SystemExit("the runner, plans, draws or bundles changed since the pilot")
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
                    _terminal("stopped", stop)
                    print("STOP:", stop, flush=True)
                    raise SystemExit(2)
            _terminal("complete")
            print("all targets recorded", json.dumps(_totals()), flush=True)
        elif step == "clean":
            clean()
        else:
            raise SystemExit("usage: seeded_run.py pilot|rest|clean")


if __name__ == "__main__":
    isolate_caches()
    main(sys.argv[1])
