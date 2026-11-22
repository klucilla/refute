"""v0.5.6 part A (exploratory): the labelled v0.5 battery on the drawn TOIs, the pilot first
(docs/plans/v0.5.6-plan.md; the maintainer's decisions of 2026-11-21, 22:30, item 3, and of
2026-11-22, 09:00, item 1; #218).

**What runs:** for each drawn TIC, the TESS adapter's download (SPOC 120-s light curves and pixel
files up to sector 107, into ``.cache/v056/data``), then the v0.5 battery unchanged: the C3
claim's test plan (``calibration/v0.5/claim.yaml``, its SHA-256 checked), stage 2, **without the
catalog test**, by the same calls as ``refute.packs.tess.discover.measure.chain`` (detrending,
prewhitening, search, ``attack_candidate``, coverage, the sensitivity rule, deferral, the
decisive aggregate). The chain is reproduced here, not changed, so that each test's message,
coverage and sensitivity are kept (``measure.chain`` keeps only status and severity). No code in
``src/`` changes.

**Every record** carries ``mode: exploratory`` and the limits label; outputs are never verdicts on
any TOI, never candidates in a public claim. ``method_status: not_validated``. Zero coverage stays
INCONCLUSIVE (``enforce_coverage``).

**Signal identity** (recorded, never a replacement): the found period against the TOI's at the
factors 1, 2 and 0.5 within 0.1 % (C3's tolerance), and the found epoch's offset from the TOI's
predicted transit, in hours.

**Caps** (the decisions): 50 CPU-h for everything of part A, the pilot, attempts and reruns
included, in ``part-a-ledger.json``. The pilot is the first 5 TICs of each arm in draw order. Its
projection stopped the run on disk (144 GB against 20 GB); the decision of 2026-11-22 (09:00)
turned the disk cap into a **peak** (what is on disk at any moment) and keeps the battery. After
Codex's round ``partarest`` (REFUTED for running with the first version; its five blocking items
are applied here):

- **Pixel files are deleted per target** after its record is written and read back. Before the
  deletion, the record carries each TPF's manifest (MAST product name, observation id, data URI,
  sector, size, SHA-256), so the target can be reproduced by downloading again. The 10 pilot
  records are anchored by SHA-256 in ``part-a-pilot.json`` and do not change; every target's
  deletion manifest is also written, and read back, before any file is removed, to a new record in
  ``.cache/v056/run/tpf-deletions``. A resumed deletion keeps every entry of that manifest.
- **What is deleted** is the file found on disk by the target's TIC in its name, by its literal
  path, inside ``.cache/v056/data/lightkurve`` only: the name must carry the TIC (16 digits) and
  end in ``_tp.fits``, no component from ``.cache`` down may be a link or a junction, the resolved
  path must equal the literal one, and the file's SHA-256 is computed just before the deletion and
  must equal the manifest's. Light curves stay. (Residual: the check and the deletion are two
  calls, so a change made between them by another program is not excluded.)
- **The peak stays under the cap by admission:** a target starts only if the measured size of
  ``.cache/v056``, plus a reserve for every target in flight, plus its own reserve stays at or
  under 18 GB. A reserve is the target's listed sectors times the pilot's largest per-sector size
  (101 220 480 bytes of TPF plus 4 164 480 of light curve; about twice the pilot's typical size),
  and the measured size already counts what in-flight targets have written, so their files are
  counted twice. The first target in draw order that fits is admitted. The size is sampled every 2
  seconds; a sample over 20 GB stops admission and the run STOPS (what is in flight finishes and
  is recorded). This is a margin, not a proof: the adapter downloads what MAST lists up to sector
  107, and each record compares the sectors downloaded with the listed ones.
- **Network and workers:** Monday to Friday, 08:00 to 18:00, at most 10 workers and 2
  simultaneous downloads; otherwise up to 20 workers and 6 simultaneous downloads. A batch takes
  the smaller of the limits now and 30 minutes later. The parent admits a target only while fewer
  downloads than the limit are in progress (each worker reports the end of its fetch), and a
  semaphore shared by the workers holds the same limit around the adapter's fetch.
- **Batches:** a target is admitted only if the batch's elapsed time plus its estimated duration
  (65 s plus 25 s per listed sector, the pilot's largest per-sector wall time) stays within 28
  minutes; the batch then drains. Its CPU estimate (40 s plus 20 s per sector) must also fit under
  the 50 CPU-h cap with what is charged and in flight. BelowNormal priority and CPUs 8 to 31
  (``pinrun``).
- **Resumable:** every target is one record file, and a recorded target never runs again. A marker
  with a heartbeat lists the targets in flight; after an unclean end, the next start charges their
  lost CPU by an upper bound (their wall time up to the last heartbeat plus two intervals) in the
  ledger's interruptions. A worker or record failure stops admission, and every other finished
  result is still recorded. The parent's own CPU (sampling, hashing, deletion) is charged too.
- **Downloaded volume** per target: the bytes of the files that the fetch wrote and that were not
  on disk before it (``downloaded_bytes``); files reused from the cache are counted apart
  (``reused_bytes``). Partial transfers of failed attempts are not counted (the adapter removes
  them), so the total is a lower bound. The pilot's records carry their bytes on disk.

Usage: ``part_a_run.py pilot`` (done) then ``part_a_run.py rest``.
"""

from __future__ import annotations

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

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CLAIM = ROOT / "calibration/v0.5/claim.yaml"
DRAW = HERE / "part-a-draw.json"
LEDGER = HERE / "part-a-ledger.json"
CACHE = ROOT / ".cache"
WORK = CACHE / "v056"
DATA = WORK / "data"
LIGHTKURVE = DATA / "lightkurve"
RECORDS = WORK / "run/records"
TPF_LOGS = WORK / "run/tpf-deletions"
MARKER = WORK / "run/in-flight.json"
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"
CAP_CPU_HOURS = 50.0
CAP_DISK_BYTES = 20e9
ADMIT_DISK_BYTES = 18e9
RESERVE_PER_SECTOR = 101_220_480 + 4_164_480
PILOT_PER_ARM = 5
BATCH_SECONDS = 28 * 60
SAMPLE_SECONDS = 2.0
WALL_BASE, WALL_PER_SECTOR = 65.0, 25.0
CPU_BASE, CPU_PER_SECTOR = 40.0, 20.0
BTJD = 2457000.0
IDENTITY_TOLERANCE = 0.001
FACTORS = (1.0, 2.0, 0.5)

_DOWNLOADS = None  # the workers' shared download semaphore (set by _init)
_FETCHED = None  # the queue on which a worker reports the end of its fetch


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
    """The smaller limits of now and of the batch's longest end (30 minutes later)."""
    now = dt.datetime.now()
    a, b = limits(now), limits(now + dt.timedelta(minutes=30))
    return min(a[0], b[0]), min(a[1], b[1])


def targets() -> list[dict]:
    draw = json.loads(DRAW.read_text("utf-8"))
    if draw.get("status") != "complete":
        raise SystemExit("the draw is not complete")
    out = []
    for arm in ("planet", "open"):
        for rank, c in enumerate(draw["arms"][arm]["chosen"]):
            out.append({**c, "arm": arm, "rank": rank, "key": f"TIC-{c['tic_id']}"})
    return out


def pilot_set(all_targets: list[dict]) -> list[dict]:
    return [t for t in all_targets if t["rank"] < PILOT_PER_ARM]


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


def run_one(target: dict, test_plan: dict) -> dict:
    """One TIC: download, the battery, the identity. Any failure is recorded, never hidden."""
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
    from refute.packs.tess.search import search_period

    started, wall = time.process_time(), time.time()
    rec = {
        "target_key": target["key"],
        "tic_id": target["tic_id"],
        "toi": target["toi"],
        "arm": target["arm"],
        "rank": target["rank"],
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
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
        search = search_period(searched, plan.search)
        gauntlet = attack_candidate(data, search.candidate, plan, None, None, pw)
        tests = enforce_coverage(gauntlet.tests)
        tests = enforce_sensitivity(tests, registry_for(plan))
        tests, deferred = defer_tests(tests, dict(plan.discovery.stages), 2)
        decisive, _ = expected_by_role(plan, False)
        verdict, reason = aggregate([t for t in tests if t.name in decisive], expected=decisive)
        cand = gauntlet.candidate
        found = None if cand is None else float(cand.period)
        published = float(target["period_days"])
        factor = matching_factor(published, found, FACTORS, IDENTITY_TOLERANCE)
        offset_hours = None
        if cand is not None:
            epoch = float(target["epoch_bjd"]) - BTJD
            phase = ((float(cand.t0) - epoch) / published) % 1.0
            offset_hours = (min(phase, 1.0 - phase)) * published * 24.0
        rec.update(
            {
                "status": "OK",
                "candidate": None
                if cand is None
                else {"period_days": found, "t0_btjd": float(cand.t0), "snr": float(cand.snr)},
                "tests": {t.name: _test(t) for t in tests},
                "decisive": list(decisive),
                "deferred": deferred,
                "outcome": verdict.value,
                "outcome_reason": reason,
                "identity": {
                    "toi_period_days": published,
                    "found_period_days": found,
                    "factor": factor,
                    "epoch_offset_hours": offset_hours,
                    "toi_duration_hours": float(target["duration_hours"]),
                    "matched": factor == 1.0
                    and offset_hours is not None
                    and offset_hours <= float(target["duration_hours"]) / 2.0,
                },
            }
        )
    except Exception as exc:  # noqa: BLE001 - recorded, never hidden
        rec.update({"status": "ERROR", "reason": f"{type(exc).__name__}: {exc}",
                    "trace": traceback.format_exc()[-1500:]})  # fmt: skip
    finally:
        rec["cpu_seconds"] = time.process_time() - started
        rec["wall_seconds"] = time.time() - wall
    return rec


def _plain(value):
    """numpy scalars and other objects in a JSON record."""
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


# --- disk ----------------------------------------------------------------------------


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
    ``.cache/v056/data/lightkurve`` only, after its SHA-256 is checked."""
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
    """Write the target's TPF manifest to a new record, read it back, then delete its pixel files.

    The files are the ones found on disk with the TIC in their name; an entry takes the
    adapter's metadata only when the adapter lists that file at that path with that size, and its
    SHA-256 is checked again before the deletion. A resumed deletion keeps every entry already
    written and adds any file found since. Returns the deletion record."""
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
    log.update(
        {
            "status": "deleted",
            "deleted_utc": utc(),
            "bytes_deleted": freed,
            "absent_at_deletion": absent,
        }
    )
    _write_json(log_path, log)
    return log


# --- ledger --------------------------------------------------------------------------


def _ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text("utf-8"))
    return {"cap_cpu_hours": CAP_CPU_HOURS, "cap_disk_bytes": CAP_DISK_BYTES, "batches": []}


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
    """CPU-h measured in the records, plus the parent's CPU (sampling, hashing, deletion) in the
    batches and sweeps, plus the upper bounds charged for interruptions."""
    ledger = _ledger()
    extra = sum(i.get("cpu_hours_upper_bound", 0.0) for i in ledger.get("interruptions", []))
    extra += sum(b.get("parent_cpu_hours", 0.0) for b in ledger.get("batches", []))
    extra += sum(s.get("parent_cpu_hours", 0.0) for s in ledger.get("sweeps", []))
    return _spent()[0] + extra


def _totals() -> dict:
    recs = _records()
    logs = [json.loads(f.read_text("utf-8")) for f in sorted(TPF_LOGS.glob("*.json"))]
    pilot = [r for r in recs if "downloaded_bytes" not in r]
    return {
        "records": len(recs),
        "downloaded_bytes_recorded": sum(r.get("downloaded_bytes", 0) for r in recs),
        "reused_bytes_recorded": sum(r.get("reused_bytes", 0) for r in recs),
        "records_with_bytes_on_disk_only": sorted(r["target_key"] for r in pilot),
        "bytes_on_disk_of_those": sum(r.get("bytes", 0) for r in pilot),
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
    """Write a target's record, read it back, then release its pixel files; a failure is
    returned as a STOP reason."""
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
    """Release the pixel files of every recorded target that still has them (the pilot's, or a
    target recorded just before an interruption)."""
    done = []
    for f in sorted(RECORDS.glob("*.json")):
        r = json.loads(f.read_text("utf-8"))
        log = TPF_LOGS / f"{r['target_key']}.json"
        if log.exists() and json.loads(log.read_text("utf-8")).get("status") == "deleted":
            continue
        release_tpfs(r["target_key"], int(r["tic_id"]))
        done.append(r["target_key"])
    return done


# --- batches -------------------------------------------------------------------------


def _pick(todo: list[dict], in_flight: dict, elapsed: float) -> int | None | str:
    """The index of the first target in draw order that fits, None if none fits now, or a STOP
    reason if nothing fits even with nothing in flight."""
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


def run_batch(selection: list[dict], label: str) -> str | None:
    """One batch; returns a STOP reason, or None."""
    claim_text = CLAIM.read_bytes()
    import yaml

    test_plan = yaml.safe_load(claim_text.decode("utf-8"))["test_plan"]
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
                    in_flight_key = fetched.get_nowait()
                except queue.Empty:
                    break
                for v in in_flight.values():
                    if v["key"] == in_flight_key:
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
                fut = pool.submit(run_one, t, test_plan)
                in_flight[fut] = {
                    "key": t["key"],
                    "reserve": reserve(t),
                    "cpu": est_cpu_hours(t),
                    "fetching": True,
                }
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
                spent = _charged()
                cpu = round(rec["cpu_seconds"])
                print(rec["target_key"], rec["status"], rec.get("outcome"), cpu,
                      f"charged {spent:.2f} CPU-h", f"peak {monitor.peak / 1e9:.2f} GB",
                      flush=True)  # fmt: skip
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
            "claim_sha256": sha256(claim_text),
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


def projection(total: int) -> dict:
    recs = _records()
    cpu = sum(r.get("cpu_seconds", 0.0) for r in recs) / 3600.0
    nbytes = sum(r.get("bytes", 0) for r in recs)
    k = len(recs)
    per_cpu, per_bytes = (cpu / k, nbytes / k) if k else (math.nan, math.nan)
    return {
        "records": k,
        "cpu_hours": cpu,
        "bytes": nbytes,
        "cpu_hours_per_target": per_cpu,
        "bytes_per_target": per_bytes,
        "projected_cpu_hours": per_cpu * total,
        "projected_bytes": per_bytes * total,
        "stop": per_cpu * total > CAP_CPU_HOURS or per_bytes * total > CAP_DISK_BYTES,
    }


def main(step: str) -> None:
    all_targets = targets()
    if step == "pilot":
        run_batch(pilot_set(all_targets), "pilot")
        p = projection(len(all_targets))
        ledger = _ledger()
        ledger["pilot_projection"] = p
        _save_ledger(ledger)
        print(json.dumps(p, indent=1))
    elif step == "rest":
        p = _ledger().get("pilot_projection")
        # The decision of 2026-11-22 (09:00): the projected total no longer stops the run on
        # disk (the cap is a peak now); the CPU projection still must fit.
        if p is None or p["projected_cpu_hours"] > CAP_CPU_HOURS:
            raise SystemExit("no pilot projection, or its CPU projection is over the cap")
        charged = charge_interruption()
        if charged:
            print("interruption charged:", json.dumps(charged), flush=True)
        parent_cpu = time.process_time()
        released = sweep()
        ledger = _ledger()
        ledger.setdefault("sweeps", []).append(
            {
                "utc": utc(),
                "released": released,
                "parent_cpu_hours": round((time.process_time() - parent_cpu) / 3600.0, 6),
            }
        )
        _save_ledger(ledger)
        print("pixel files released before the batches:", released, flush=True)
        while any(not (RECORDS / f"{t['key']}.json").exists() for t in all_targets):
            stop = run_batch(all_targets, "rest")
            if stop:
                print("STOP:", stop, flush=True)
                raise SystemExit(2)
        print("all targets recorded", json.dumps(_totals()), flush=True)
    else:
        raise SystemExit("usage: part_a_run.py pilot|rest")


if __name__ == "__main__":
    main(sys.argv[1])
