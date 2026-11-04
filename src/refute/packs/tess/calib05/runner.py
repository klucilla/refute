"""Task runs of the v0.5 calibration (calibration/v0.5/PROTOCOL.md, section 7, frozen before any
run).

- A run folder is created exclusively before any task is dispatched, with its **manifest**
  (``manifest.json``: the task function, the ordered task identities, the SHA-256 of the tasks'
  content, and the provenance: the code hash and the step's inputs) and a lock (``running.lock``,
  the process id). A second run into the folder is refused.
- The tasks run over worker processes in chunks of ``workers``; after each chunk its records are
  appended to ``records.jsonl``, then one line per task to ``cost.jsonl``. A task is **complete**
  when its record is appended; a task that raises, times out or fails its validation is complete as
  an error record, kept in the denominators and never rerun. A cost line missing after an
  interruption is restored from its record (which holds the same ``cpu_seconds``).
- ``resume`` (only after an interruption, with its approval recorded in an issue first) needs the
  same function, the same tasks and the same provenance as the manifest, refuses a complete run
  and a run whose process is still alive, and runs only the tasks without a record; a task already
  recorded is refused, never counted twice.
- ``all_records`` returns the records only when they are exactly the manifest's tasks, each once,
  each with its cost line.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
from collections.abc import Callable, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from refute.core.runner import default_workers, run_processes

LF = "\n"
RECORDS = "records.jsonl"
COST = "cost.jsonl"
MANIFEST = "manifest.json"
LOCK = "running.lock"


def provenance(root: Path, **extra: Any) -> dict[str, Any]:
    """The code hash of the tree that runs (``refute-code-1``) and the step's own inputs."""
    from refute.core.codehash import compute_code_hash

    return {"code_sha256": compute_code_hash(Path(root)).sha256, **extra}


def _content(task: Any) -> Any:
    return dataclasses.asdict(task) if dataclasses.is_dataclass(task) else task


def tasks_sha256(tasks: Sequence[Any]) -> str:
    text = json.dumps([_content(t) for t in tasks], sort_keys=True, default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _manifest(fn, tasks, task_id, prov) -> dict[str, Any]:
    ids = [task_id(t) for t in tasks]
    if len(set(ids)) != len(ids):
        raise ValueError("two tasks have the same identity")
    return {
        "schema": "refute-calib05-run-1",
        "function": f"{fn.__module__}.{fn.__qualname__}",
        "tasks": ids,
        "tasks_sha256": tasks_sha256(tasks),
        "provenance": prov,
    }


def read_records(out_dir: Path) -> list[dict[str, Any]]:
    path = Path(out_dir) / RECORDS
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _cost_ids(out_dir: Path) -> set[str]:
    path = Path(out_dir) / COST
    if not path.is_file():
        return set()
    return {
        json.loads(line)["task"] for line in path.read_text(encoding="utf-8").splitlines() if line
    }


def _cost_line(record: dict[str, Any]) -> str:
    line = {
        "task": record["task"],
        "cpu_seconds": record.get("cpu_seconds"),
        "status": record.get("status"),
    }
    return json.dumps(line, sort_keys=True) + LF


def _append(out_dir: Path, done: list[dict[str, Any]]) -> None:
    with open(Path(out_dir) / RECORDS, "a", encoding="utf-8", newline=LF) as out:
        for record in done:
            out.write(json.dumps(record, sort_keys=True, default=str) + LF)
    with open(Path(out_dir) / COST, "a", encoding="utf-8", newline=LF) as cost:
        for record in done:
            cost.write(_cost_line(record))


def _restore_costs(out_dir: Path) -> int:
    """Cost lines of recorded tasks that lack one (an interruption between the two writes)."""
    have = _cost_ids(out_dir)
    missing = [r for r in read_records(out_dir) if r["task"] not in have]
    if missing:
        with open(Path(out_dir) / COST, "a", encoding="utf-8", newline=LF) as cost:
            for record in missing:
                cost.write(_cost_line(record))
    return len(missing)


def _pid_alive(pid: int) -> bool:
    """Whether a process with this id runs (a query only; nothing is signalled)."""
    if os.name == "nt":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
        if not handle:
            return False
        code = ctypes.c_ulong()
        ok = kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        kernel32.CloseHandle(handle)
        return bool(ok) and code.value == 259  # STILL_ACTIVE
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _dispatch(fn, tasks, task_id, out_dir: Path, workers: int, seen: set[str]) -> list[dict]:
    ids = [task_id(t) for t in tasks]
    repeated = sorted(set(ids) & seen)
    if repeated:
        raise ValueError(f"tasks already recorded, never counted twice: {repeated[:5]}")
    results: list[dict[str, Any]] = []
    for start in range(0, len(tasks), workers):
        chunk = list(tasks[start : start + workers])
        done = run_processes(fn, chunk, workers)
        for key, record in zip(ids[start : start + workers], done, strict=True):
            record["task"] = key
        _append(out_dir, done)
        results.extend(done)
    return results


def _lock(out_dir: Path, mode: str) -> None:
    with open(Path(out_dir) / LOCK, mode, encoding="utf-8") as handle:
        handle.write(json.dumps({"pid": os.getpid(), "utc": _now()}))


def _now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_tasks(
    fn: Callable[[Any], dict[str, Any]],
    tasks: Sequence[Any],
    task_id: Callable[[Any], str],
    out_dir: Path,
    workers: int | None = None,
    prov: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Run every task once into a new folder ``out_dir`` (refused if it exists)."""
    out_dir = Path(out_dir)
    manifest = _manifest(fn, tasks, task_id, prov or {})
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(exist_ok=False)
    with open(out_dir / MANIFEST, "x", encoding="utf-8", newline=LF) as handle:
        handle.write(json.dumps({**manifest, "created_utc": _now()}, indent=1) + LF)
    _lock(out_dir, "x")
    records = _dispatch(fn, tasks, task_id, out_dir, workers or default_workers(), set())
    (out_dir / LOCK).unlink()
    return records


def resume(
    fn: Callable[[Any], dict[str, Any]],
    tasks: Sequence[Any],
    task_id: Callable[[Any], str],
    out_dir: Path,
    approval_url: str,
    workers: int | None = None,
    prov: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """After an interruption: the manifest's tasks without a record, under the same function,
    tasks and provenance. Needs the URL of the approval recorded in an issue first."""
    from refute.packs.tess.discover.steps import APPROVAL_URL

    if not APPROVAL_URL.fullmatch(approval_url):
        raise ValueError("a resumption needs the issue comment URL of its approval")
    out_dir = Path(out_dir)
    path = out_dir / MANIFEST
    if not path.is_file():
        raise ValueError(f"{out_dir} has no run manifest")
    stored = json.loads(path.read_text(encoding="utf-8"))
    current = _manifest(fn, tasks, task_id, prov or {})
    for key in ("function", "tasks", "tasks_sha256", "provenance"):
        if stored.get(key) != current[key]:
            raise ValueError(f"the resumption differs from the run's manifest in `{key}`")
    lock = out_dir / LOCK
    if lock.is_file() and _pid_alive(json.loads(lock.read_text(encoding="utf-8"))["pid"]):
        raise ValueError("the run's process is still alive")
    restored = _restore_costs(out_dir)
    recorded = {r["task"] for r in read_records(out_dir)}
    missing = [t for t in tasks if task_id(t) not in recorded]
    if not missing:
        raise ValueError("the run is complete; nothing to resume")
    with open(out_dir / "resumptions.jsonl", "a", encoding="utf-8", newline=LF) as log:
        entry = {
            "approval": approval_url,
            "tasks": len(missing),
            "costs_restored": restored,
            "utc": _now(),
        }
        log.write(json.dumps(entry) + LF)
    _lock(out_dir, "w")
    done = _dispatch(fn, missing, task_id, out_dir, workers or default_workers(), recorded)
    lock.unlink()
    return done


def all_records(out_dir: Path) -> list[dict[str, Any]]:
    """The run's records, refused unless they are exactly the manifest's tasks, each once, each
    with its cost line, and the run is not still marked as running."""
    out_dir = Path(out_dir)
    manifest = json.loads((out_dir / MANIFEST).read_text(encoding="utf-8"))
    if (out_dir / LOCK).exists():
        raise ValueError("the run is marked as running or interrupted")
    records = read_records(out_dir)
    ids = [r["task"] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError("a task is recorded twice")
    expected = set(manifest["tasks"])
    missing, extra = sorted(expected - set(ids)), sorted(set(ids) - expected)
    if missing:
        raise ValueError(f"{len(missing)} scheduled tasks have no record (first: {missing[:3]})")
    if extra:
        raise ValueError(f"records of unscheduled tasks: {extra[:3]}")
    if set(ids) - _cost_ids(out_dir):
        raise ValueError("a recorded task has no cost line")
    return records


def read_manifest(out_dir: Path) -> dict[str, Any]:
    return json.loads((Path(out_dir) / MANIFEST).read_text(encoding="utf-8"))


def projected_hours(prefix: list[dict[str, Any]], counts: dict[str, int], key: str) -> float:
    """The projected processor-hours: per group (``key`` of each record), the mean CPU seconds of
    the prefix's records times the group's scheduled count."""
    total = 0.0
    for group, n in counts.items():
        cpu = [float(r.get("cpu_seconds") or 0.0) for r in prefix if r.get(key) == group]
        if not cpu:
            raise ValueError(f"the prefix has no record of {group}")
        total += n * sum(cpu) / len(cpu)
    return total / 3600.0
