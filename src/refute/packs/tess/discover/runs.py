"""Orchestration of the v0.4 measurements and of the stage-1 bookkeeping (protocol sections 4.4,
6, 7, 9 and 10).

- ``measurement_tasks``: the injection and transformed-curve tasks of one star, with the seeds of
  R_inj; ``run_measurements`` runs them over worker processes and writes one JSON line per task
  and one ``cost.jsonl`` line per task (logical-processor seconds), as input for v0.7.
- ``stage1_entries``: after a stage-1 run, the deduplication, the eligibility and the light
  ledger entry of every funnel star, from its ``verdict.json`` (with its SHA-256).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from refute.core.runner import default_workers, run_processes
from refute.packs.tess.discover import case, dedup, funnel
from refute.packs.tess.discover import injection as inj
from refute.packs.tess.discover.measure import (
    InjectionTask,
    TransformTask,
    run_injection,
    run_transform,
    summarize_transforms,
)
from refute.packs.tess.discover.transforms import stream_seed


def measurement_tasks(
    target: dict[str, Any],
    test_plan: dict[str, Any],
    cache_dir: Path,
    randomness_inj: str,
    k: int,
    transform_stage: int,
    catalog_paths: tuple[str, ...] = (),
    scan_path: str | None = None,
    first_injection: int = 0,
    transforms: bool = True,
) -> tuple[list[InjectionTask], list[TransformTask]]:
    """Injections ``first_injection`` to ``k - 1`` (at stage 1) and, with ``transforms``, the
    three transformed curves (at ``transform_stage``) of one star. The continuation of a
    control's measurement prefix is ``first_injection=5, transforms=False``: its transformed
    curves were part of the prefix and are never run twice."""
    tic = int(target["tic_id"])
    inj_seed = inj.stage1_chain_seed(randomness_inj, tic)
    tr_seed = stream_seed(randomness_inj, "v0.4", "transform", tic)
    common = {"catalog_paths": tuple(catalog_paths), "scan_path": scan_path}
    injections = [
        InjectionTask(target, test_plan, str(cache_dir), inj_seed, i, k, 1, **common)
        for i in range(first_injection, k)
    ]
    curves = [
        TransformTask(
            target, test_plan, str(cache_dir), tr_seed, position, transform_stage, **common
        )
        for position in range(3)
    ]
    return injections, curves if transforms else []


def _run_task(task: InjectionTask | TransformTask) -> dict[str, Any]:
    if isinstance(task, InjectionTask):
        return {"kind": "injection", **run_injection(task)}
    return {"kind": "transform", **run_transform(task)}


def task_identity(record: dict[str, Any]) -> tuple:
    """What makes two measurement records the same task: the star, the kind, the injection
    index or the transformed-curve position, and the stage."""
    slot = record.get("index") if record["kind"] == "injection" else record.get("position")
    return (record["target_key"], record["kind"], slot, record.get("stage"))


def run_measurements(
    tasks: list[InjectionTask | TransformTask], out_dir: Path, workers: int | None = None
) -> dict[str, Any]:
    """Run every task and return the per-star summaries. ``out_dir`` must not exist: it is
    created exclusively before any task is dispatched, so a repeated call never repeats the
    work. The tasks run in chunks of ``workers``; after each chunk its records are appended to
    ``measurements.jsonl`` and ``cost.jsonl`` (the whole task's logical-processor seconds), so
    what finished is kept. A task's own failure is a record (status ERROR or INCONCLUSIVE),
    never a lost chunk."""
    out_dir = Path(out_dir)
    out_dir.parent.mkdir(parents=True, exist_ok=True)
    out_dir.mkdir(exist_ok=False)
    n = workers or default_workers()
    results: list[dict[str, Any]] = []
    for start in range(0, len(tasks), n):
        chunk = tasks[start : start + n]
        done = run_processes(_run_task, chunk, n)
        with open(out_dir / "measurements.jsonl", "a", encoding="utf-8", newline=LF) as out:
            for result in done:
                out.write(json.dumps(result, sort_keys=True, default=str) + LF)
        with open(out_dir / "cost.jsonl", "a", encoding="utf-8", newline=LF) as cost:
            for task, result in zip(chunk, done, strict=True):
                line = {
                    "kind": result["kind"],
                    "target_key": task.target["key"],
                    "task": {k: v for k, v in asdict(task).items() if k != "test_plan"},
                    "cpu_seconds": result.get("cpu_seconds"),
                    "status": result.get("status"),
                }
                cost.write(json.dumps(line, sort_keys=True, default=str) + LF)
        results.extend(done)
    return summarize_records(results)


LF = "\n"


def read_records(path: Path) -> list[dict[str, Any]]:
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line]


def summarize_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-star summaries over every record given (for a control, the prefix and its
    continuation together). The same task twice is refused, never counted twice."""
    seen: dict[tuple, dict[str, Any]] = {}
    for record in records:
        identity = task_identity(record)
        if identity in seen:
            raise ValueError(f"the task {identity} is recorded twice")
        seen[identity] = record
    summaries: dict[str, Any] = {}
    for key in sorted({r["target_key"] for r in records}):
        mine = [r for r in records if r["target_key"] == key]
        summaries[key] = {
            "injections": inj.summarize([r for r in mine if r["kind"] == "injection"]),
            "transformed_curves": summarize_transforms(
                [r for r in mine if r["kind"] == "transform"]
            ),
            "cpu_seconds": sum(float(r.get("cpu_seconds") or 0.0) for r in mine),
        }
    return summaries


def verdict_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dossier_problems(
    verdict: dict[str, Any], key: str, target: dict[str, Any], identity: dict[str, str]
) -> list[str]:
    """Why a stage-1 ``verdict.json`` is not this claim's dossier of ``key``: its target key
    and TIC, its stage, and its provenance (claim id, locked claim hash, locked code hash)."""
    problems = []
    if verdict.get("target_key") != key:
        problems.append(f"target_key {verdict.get('target_key')!r}")
    if int(verdict.get("tic_id") or -1) != int(target.get("tic_id") or -2):
        problems.append(f"tic_id {verdict.get('tic_id')!r}")
    if (verdict.get("discovery") or {}).get("stage") != 1:
        problems.append("not a stage-1 run")
    provenance = verdict.get("provenance") or {}
    for field in ("claim_id", "claim_sha256", "code_sha256"):
        if provenance.get(field) != identity.get(field):
            problems.append(f"{field} {provenance.get(field)!r}")
    return problems


def stage1_entries(
    run_dir: Path,
    run_set: list[str],
    indexes: dict[str, Any],
    targets: dict[str, dict[str, Any]],
    identity: dict[str, str],
) -> list[dict]:
    """For each funnel star of the run set (in order), from its stage-1 dossier: the SHA-256 of
    ``verdict.json``, the deduplication of its signal (only when the gate passed), the
    eligibility, and the light ledger entry. ``targets`` are the locked claim's targets by key,
    and ``identity`` its ``claim_id``, ``claim_sha256`` and ``code_sha256``: a dossier of another
    claim, code, star or stage is never used (the star is then not eligible, with the reason),
    and the position for the deduplication is the locked target's (from the selection walk),
    never the dossier's. A star without a dossier is recorded, never skipped."""
    out = []
    for key in run_set:
        path = Path(run_dir) / key / "verdict.json"
        if not path.is_file():
            entry = {"target_key": key, "verdict_sha256": None}
            entry["eligibility"] = {"eligible": False, "reason": "no stage-1 dossier"}
            out.append(entry)
            continue
        verdict = json.loads(path.read_text(encoding="utf-8"))
        target = targets.get(key) or {}
        foreign = dossier_problems(verdict, key, target, identity)
        if foreign:
            out.append(
                {
                    "target_key": key,
                    "verdict_sha256": verdict_sha256(path),
                    "eligibility": {
                        "eligible": False,
                        "reason": "the stage-1 dossier is not this claim's: " + "; ".join(foreign),
                    },
                }
            )
            continue
        candidate = verdict.get("candidate") or {}
        gate = next((t for t in verdict.get("tests", []) if t["name"] == "snr"), None)
        found = None
        if gate is not None and gate["status"] == "PASS" and candidate.get("period"):
            evidence = target.get("mast") or {}
            found = dedup.deduplicate(
                indexes,
                int(target["tic_id"]),
                evidence.get("tic_ra"),
                evidence.get("tic_dec"),
                float(candidate["period"]),
            )
        eligibility = funnel.stage1_eligibility(verdict, found)
        out.append(
            {
                "target_key": key,
                "verdict_sha256": verdict_sha256(path),
                "deduplication": found,
                "eligibility": eligibility,
                "ledger": case.light_entry(verdict, eligibility, found),
            }
        )
    return out
