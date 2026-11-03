"""Task runs of the v0.5 calibration (calibration/v0.5/PROTOCOL.md, section 7, frozen before any
run).

- A run folder is created exclusively before any task is dispatched; a second call on it is
  refused, so a run is never repeated by accident.
- The tasks run over worker processes in chunks of ``workers``; after each chunk its records are
  appended to ``records.jsonl`` and one line per task to ``cost.jsonl`` (the task's
  logical-processor seconds). A task is **complete** when its record is appended; a task that
  raises, times out or fails its validation is complete as an error record, kept in the
  denominators and never rerun.
- ``resume`` (only after an interruption, with its approval recorded in an issue first) runs the
  tasks without a record, under the identical code and the same seeds; a task already recorded
  is refused, never counted twice.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from refute.core.runner import default_workers, run_processes

LF = "\n"
RECORDS = "records.jsonl"
COST = "cost.jsonl"


def read_records(out_dir: Path) -> list[dict[str, Any]]:
    path = Path(out_dir) / RECORDS
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def _append(out_dir: Path, done: list[dict[str, Any]], ids: list[str]) -> None:
    with open(Path(out_dir) / RECORDS, "a", encoding="utf-8", newline=LF) as out:
        for record in done:
            out.write(json.dumps(record, sort_keys=True, default=str) + LF)
    with open(Path(out_dir) / COST, "a", encoding="utf-8", newline=LF) as cost:
        for task_id, record in zip(ids, done, strict=True):
            line = {
                "task": task_id,
                "cpu_seconds": record.get("cpu_seconds"),
                "status": record.get("status"),
            }
            cost.write(json.dumps(line, sort_keys=True) + LF)


def _run(
    fn: Callable[[Any], dict[str, Any]],
    tasks: Sequence[Any],
    task_id: Callable[[Any], str],
    out_dir: Path,
    workers: int,
    seen: set[str],
) -> list[dict[str, Any]]:
    ids = [task_id(t) for t in tasks]
    if len(set(ids)) != len(ids):
        raise ValueError("two tasks have the same identity")
    repeated = sorted(set(ids) & seen)
    if repeated:
        raise ValueError(f"tasks already recorded, never counted twice: {repeated[:5]}")
    results: list[dict[str, Any]] = []
    for start in range(0, len(tasks), workers):
        chunk = list(tasks[start : start + workers])
        done = run_processes(fn, chunk, workers)
        for task_key, record in zip(ids[start : start + workers], done, strict=True):
            record["task"] = task_key
        _append(out_dir, done, ids[start : start + workers])
        results.extend(done)
    return results


def run_tasks(
    fn: Callable[[Any], dict[str, Any]],
    tasks: Sequence[Any],
    task_id: Callable[[Any], str],
    out_dir: Path,
    workers: int | None = None,
) -> list[dict[str, Any]]:
    """Run every task once into a new folder ``out_dir`` (refused if it exists)."""
    out_dir = Path(out_dir)
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(exist_ok=False)
    return _run(fn, tasks, task_id, out_dir, workers or default_workers(), set())


def resume(
    fn: Callable[[Any], dict[str, Any]],
    tasks: Sequence[Any],
    task_id: Callable[[Any], str],
    out_dir: Path,
    approval_url: str,
    workers: int | None = None,
) -> list[dict[str, Any]]:
    """After an interruption: the tasks of ``tasks`` without a record in ``out_dir``. Needs the
    URL of the approval recorded in an issue first (protocol section 7)."""
    from refute.packs.tess.discover.steps import APPROVAL_URL

    if not APPROVAL_URL.fullmatch(approval_url):
        raise ValueError("a resumption needs the issue comment URL of its approval")
    out_dir = Path(out_dir)
    if not out_dir.is_dir():
        raise ValueError(f"{out_dir} is not a run folder")
    recorded = {r["task"] for r in read_records(out_dir)}
    missing = [t for t in tasks if task_id(t) not in recorded]
    with open(out_dir / "resumptions.jsonl", "a", encoding="utf-8", newline=LF) as log:
        log.write(json.dumps({"approval": approval_url, "tasks": len(missing)}) + LF)
    return _run(fn, missing, task_id, out_dir, workers or default_workers(), recorded)


def all_records(out_dir: Path, expected: Sequence[str]) -> list[dict[str, Any]]:
    """The run's records, refused unless every expected task has exactly one."""
    records = read_records(out_dir)
    ids = [r["task"] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError("a task is recorded twice")
    missing = sorted(set(expected) - set(ids))
    if missing:
        raise ValueError(f"{len(missing)} scheduled tasks have no record (first: {missing[:3]})")
    return records


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
