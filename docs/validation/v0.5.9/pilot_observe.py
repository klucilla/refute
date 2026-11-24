"""v0.5.9 pilot: the independent measure (the maintainer's decision of 2026-11-24, received at 05:07
local, #218, comment 7125778250, item 2).

**Exploratory.** A separate process, started before ``pilot_run.py`` and stopped after it, that
measures what the supervisor charges without using any of its numbers:

- **CPU, by Windows:** every half second it reads the attempt journal; for each dispatch with a
  PID it opens its own handle to that process (checking the creation time the journal records, so
  a reused PID is refused) and holds it; at the end it reads ``GetProcessTimes`` (user plus kernel)
  by that handle, after the process has exited. The pilot driver's own process is measured the same
  way, from ``.cache/v059/pilot/driver.json``.
- **Bytes, by the files written:** every half second it lists every file under
  ``.cache/v059/data/lightkurve`` (where the downloads land) and keeps the largest size seen of
  every file absent when it started, so a pixel file deleted later still counts.

``compare`` then sets the supervisor's account (the journal's settled charges and the ledger's
controller CPU, the fetch attempts' charged bytes) against these measures, with the criterion
posted on #218 before the pilot ran, and writes ``pilot-comparison.json``.

Usage (from the project root, pinned): ``pilot_observe.py watch`` (until
``.cache/v059/pilot/observer.stop`` exists), then ``pilot_observe.py compare``.
"""

from __future__ import annotations

import ctypes
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import pilot_run  # noqa: E402
import prototype_run as pr  # noqa: E402 - read only

OBSERVED = pilot_run.PILOT_DIR / "observed.json"
STOP_FILE = pilot_run.PILOT_DIR / "observer.stop"
COMPARISON = HERE / "pilot-comparison.json"
POLL_SECONDS = 0.5
TOLERANCE = 0.10  # the decision: a difference of at most 10 %

_QUERY = 0x1000 | 0x00100000  # PROCESS_QUERY_LIMITED_INFORMATION | SYNCHRONIZE


def _k32():
    k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    k32.OpenProcess.restype = ctypes.c_void_p
    k32.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
    k32.GetProcessTimes.argtypes = [ctypes.c_void_p] + [ctypes.c_void_p] * 4
    k32.CloseHandle.argtypes = [ctypes.c_void_p]
    return k32


def _times(k32, handle) -> tuple[int, float] | None:
    t = [ctypes.c_ulonglong() for _ in range(4)]
    if not k32.GetProcessTimes(handle, *(ctypes.byref(x) for x in t)):
        return None
    return int(t[0].value), (t[2].value + t[3].value) / 1e7


def _open(k32, pid: int, created: int | None):
    """A handle to the process with this PID and creation time, or None (gone or reused)."""
    h = k32.OpenProcess(_QUERY, False, int(pid))
    if not h:
        return None
    got = _times(k32, h)
    if got is None or created is None or got[0] != int(created):
        k32.CloseHandle(h)
        return None
    return h


def _journal() -> list[dict]:
    out = []
    for p in sorted(pr.ATTEMPTS.glob("*.json")) if pr.ATTEMPTS.exists() else []:
        try:
            out.append(json.loads(p.read_text("utf-8")))
        except (OSError, ValueError):
            continue  # being replaced; read on the next poll
    return out


def _files(root: Path) -> dict[str, int]:
    out = {}
    if root.exists():
        for p in root.rglob("*"):
            try:
                if p.is_file():
                    out[p.relative_to(pr.ROOT).as_posix()] = p.stat().st_size
            except (FileNotFoundError, PermissionError):
                continue
    return out


def watch() -> None:
    k32 = _k32()
    pilot_run.PILOT_DIR.mkdir(parents=True, exist_ok=True)
    if STOP_FILE.exists():
        raise SystemExit("refused: a stop file is already there")
    started = pr.sr.utc()
    baseline = _files(pr.LIGHTKURVE)
    held: dict[str, int] = {}  # attempt id (or "driver") -> handle
    seen_attempts: dict[str, dict] = {}
    missed: dict[str, str] = {}
    sizes: dict[str, int] = {}
    polls = 0
    while True:
        stopping = STOP_FILE.exists()
        for a in _journal():
            aid = a["attempt_id"]
            seen_attempts[aid] = {k: a.get(k) for k in ("key", "target_key", "kind", "pid")}
            if aid in held or aid in missed or "pid" not in a:
                continue
            h = _open(k32, int(a["pid"]), a.get("created"))
            if h:
                held[aid] = h
            elif a.get("state") == "settled":
                missed[aid] = "the process was gone before the observer opened it"
        if "driver" not in held and pilot_run.DRIVER.exists():
            try:
                d = json.loads(pilot_run.DRIVER.read_text("utf-8"))
                h = _open(k32, int(d["pid"]), d.get("created"))
                if h:
                    held["driver"] = h
            except (OSError, ValueError):
                pass
        for path, size in _files(pr.LIGHTKURVE).items():
            if path not in baseline:
                sizes[path] = max(size, sizes.get(path, 0))
        polls += 1
        if stopping:
            break
        time.sleep(POLL_SECONDS)
    cpu = {}
    for aid, h in held.items():
        got = _times(k32, h)
        cpu[aid] = None if got is None else got[1]
        k32.CloseHandle(h)
    for aid in seen_attempts:
        if aid not in held and aid not in missed:
            missed[aid] = "never opened (no PID or no matching process)"
    pr.write_json(OBSERVED, {
        "schema": "refute-v059-pilot-observed-1", "mode": "exploratory",
        "started_utc": started, "ended_utc": pr.sr.utc(), "polls": polls,
        "poll_seconds": POLL_SECONDS, "process_cpu_seconds": cpu, "missed": missed,
        "attempts": seen_attempts, "baseline_files": len(baseline), "file_max_bytes": sizes,
    })  # fmt: skip
    print(f"observed {len(cpu)} processes, {len(missed)} missed, {len(sizes)} files", flush=True)


def _rel(s: float, i: float) -> float | None:
    return None if i <= 0 else abs(s - i) / i


def compare_numbers(obs: dict, journal: list[dict], ledger: dict, keys: set[str],
                    charged: dict) -> dict:  # fmt: skip
    """The supervisor's account against the independent measure (pure: the tests call it)."""
    pilot_attempts = [a for a in journal if a.get("target_key") in keys]
    unsettled = [a["attempt_id"] for a in pilot_attempts if a.get("state") != "settled"]
    s_workers = sum(float(a.get("cpu_seconds_charged") or 0.0) for a in pilot_attempts)
    i_workers, missing = 0.0, []
    for a in pilot_attempts:
        v = obs["process_cpu_seconds"].get(a["attempt_id"])
        if v is None:
            missing.append(a["attempt_id"])
        else:
            i_workers += v
    batches = [b for b in ledger.get("batches", []) if b.get("label") == "pilot"]
    s_ctrl = 3600.0 * sum(float(b.get("controller_cpu_hours") or 0.0) for b in batches)
    i_ctrl = obs["process_cpu_seconds"].get("driver")
    s_bytes = sum(int(a.get("bytes_charged") or 0) for a in pilot_attempts if a["kind"] == "fetch")
    i_bytes = sum(obs["file_max_bytes"].values())
    disk_peak = int(ledger.get("disk_peak_bytes") or 0)
    caps = {
        "cpu_hours_charged": charged["cpu_hours"], "cpu_cap": pr.CAP_CPU_HOURS,
        "download_bytes_charged": charged["download_bytes"],
        "download_cap": pr.CAP_DOWNLOAD_BYTES, "disk_peak_bytes": disk_peak,
        "disk_cap": pr.CAP_DISK_BYTES,
    }  # fmt: skip
    passed_cap = (charged["cpu_hours"] > pr.CAP_CPU_HOURS
                  or charged["download_bytes"] > pr.CAP_DOWNLOAD_BYTES
                  or disk_peak > pr.CAP_DISK_BYTES)  # fmt: skip
    rel = {
        "cpu_workers": _rel(s_workers, i_workers),
        "cpu_total": None if i_ctrl is None else _rel(s_workers + s_ctrl, i_workers + i_ctrl),
        "bytes": _rel(s_bytes, i_bytes),
    }
    reasons = []
    if missing or obs.get("missed"):
        reasons.append("an attempt's process was not measured independently")
    if unsettled:
        reasons.append("an attempt is not settled")
    if i_ctrl is None:
        reasons.append("the driver's process was not measured")
    for name, v in rel.items():
        if v is None or v > TOLERANCE:
            reasons.append(f"{name}: the difference is not within {TOLERANCE:.0%}")
    if passed_cap:
        reasons.append("a cap was passed")
    if ledger.get("state") == "stopped":
        reasons.append(f"the run stopped: {ledger.get('state_reason')}")
    return {
        "attempts": len(pilot_attempts),
        "unsettled": unsettled,
        "missing_measure": missing,
        "cpu_seconds": {"supervisor_workers": s_workers, "independent_workers": i_workers,
                        "supervisor_controller": s_ctrl, "independent_driver_process": i_ctrl},
        "bytes": {"supervisor_charged": s_bytes, "independent_files": i_bytes,
                  "files": len(obs["file_max_bytes"])},
        "relative_difference": rel,
        "caps": caps,
        "passed": not reasons,
        "reasons": reasons,
    }  # fmt: skip


def compare() -> None:
    obs = json.loads(OBSERVED.read_text("utf-8"))
    keys = {t["key"] for t in pilot_run.pilot_targets(pr.targets())}
    out = compare_numbers(obs, pr.attempts(), pr.sr._ledger(), keys, pr.charged())
    doc = {
        "schema": "refute-v059-pilot-comparison-1", "mode": "exploratory",
        "limits_label": pr.LABEL, "method_status": "not_validated", "written_utc": pr.sr.utc(),
        "decision": "#218, comment 7125778250, item 2", "pilot_tois": list(pilot_run.PILOT_TOIS),
        "tolerance": TOLERANCE, "observer": {k: obs[k] for k in
                                             ("started_utc", "ended_utc", "polls", "poll_seconds")},
        **out,
    }  # fmt: skip
    pr.write_json(COMPARISON, doc)
    print(json.dumps({k: doc[k] for k in ("relative_difference", "passed", "reasons")}))


def main(argv: list[str]) -> None:
    pr.point_runner()
    if argv == ["watch"]:
        watch()
    elif argv == ["compare"]:
        compare()
    else:
        raise SystemExit("usage: pilot_observe.py watch|compare")


if __name__ == "__main__":
    main(sys.argv[1:])
