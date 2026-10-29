"""The per-curve measurements of the v0.4 pilot: the stage-1 chain on injected curves, and the
chain on transformed curves (protocol sections 9 and 10), with their cost.

The chain is the analysis without the holdout: detrending, search, the gauntlet and the battery
(with the catalog test when the claim attaches catalogs), then the deferral of the tests of a
later stage. It returns two outcomes apart: the verdict over every decisive test (INCONCLUSIVE at
stage 1, since the pixel tests are deferred), and the outcome over the decisive tests **of that
stage** (``survived_stage_tests``), which is what the transformed-curve counts use. A funnel star
runs it at stage 1; a promoted star or a control runs its transformed curves at stage 2 (the full
battery). Each worker applies the stage's plan before it reads anything, so a stage-1 measurement
never reads a pixel file.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from refute.core.verdict import TestStatus, aggregate, defer_tests, enforce_coverage
from refute.packs.tess.detrend import detrend
from refute.packs.tess.discover import injection as inj
from refute.packs.tess.discover.transforms import Transform, transforms_for
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import attack_candidate, expected_by_role, global_prewhitening
from refute.packs.tess.search import search_period
from refute.packs.tess.types import TessData

SURVIVING = ("SURVIVED", "WEAKENED")


def chain(
    data: TessData,
    plan: TessTestPlan,
    stage: int,
    catalogs: list | None = None,
    catalog_scan: dict | None = None,
) -> dict[str, Any]:
    """The analysis without the holdout, at ``stage``."""
    discovery = plan.discovery
    if discovery is None:
        raise ValueError("the measurement chain needs a discover plan")
    flat = detrend(data.lc, plan.detrend)
    pw, searched = global_prewhitening(data, plan, flat)
    search = search_period(searched, plan.search)
    gauntlet = attack_candidate(data, search.candidate, plan, catalogs, catalog_scan, pw)
    tests = enforce_coverage(gauntlet.tests)
    tests, deferred = defer_tests(tests, dict(discovery.stages), stage)
    decisive, _ = expected_by_role(plan, catalogs is not None)
    verdict, reason = aggregate([t for t in tests if t.name in decisive], expected=decisive)
    staged = [n for n in decisive if n not in deferred]
    stage_verdict, stage_reason = aggregate([t for t in tests if t.name in staged], expected=staged)
    gate = next((t for t in tests if t.name == "snr"), None)
    candidate = gauntlet.candidate
    return {
        "candidate": None
        if candidate is None
        else {"period_days": candidate.period, "t0_btjd": candidate.t0, "snr": candidate.snr},
        "tests": {t.name: {"status": t.status.value, "severity": t.severity.value} for t in tests},
        "deferred": deferred,
        "catalog_test": catalogs is not None,
        "verdict": verdict.value,
        "verdict_reason": reason,
        "stage_tests": staged,
        "stage_verdict": stage_verdict.value,
        "stage_verdict_reason": stage_reason,
        "gate_passed": gate is not None and gate.status is TestStatus.PASS,
        "survived_stage_tests": stage_verdict.value in SURVIVING,
    }


def stage_plan(test_plan: dict[str, Any], stage: int) -> dict[str, Any]:
    """The plan of ``stage`` (stage 1 reads no pixel file), as ``refute discover`` uses it."""
    from refute.packs.tess.schema import TessClaimSchema

    return TessClaimSchema().plan_for_stage(test_plan, stage)


def load_catalogs(paths: tuple[str, ...], scan: str | None, cache_dir: Path):
    """The claim's eclipsing-binary catalogs and scan, as the analyzer loads them (None when
    the claim attaches none)."""
    if not paths:
        return None, None
    from refute.packs.tess.ebcatalog import load_catalogs as load
    from refute.packs.tess.ebcatalog import load_scan, resolve_references

    catalog_scan = load_scan(Path(scan)) if scan else None
    catalogs = resolve_references(load([Path(p) for p in paths]), catalog_scan, cache_dir)
    return catalogs, catalog_scan


@dataclass(frozen=True)
class InjectionTask:
    """One injection of one star (picklable)."""

    target: dict[str, Any]
    test_plan: dict[str, Any]
    cache_dir: str
    seed: int
    index: int
    k: int
    stage: int = 1
    catalog_paths: tuple[str, ...] = field(default_factory=tuple)
    scan_path: str | None = None


def run_injection(task: InjectionTask) -> dict[str, Any]:
    """One injection. ``cpu_seconds`` is the whole task, from reading the data to the verdict,
    also when the task fails (its record then has ``status`` ERROR)."""
    from refute.packs.tess.adapter import TessAdapter

    started = time.process_time()
    record: dict[str, Any] = {"target_key": task.target["key"], "stage": task.stage}
    record["index"] = task.index
    try:
        test_plan = stage_plan(task.test_plan, task.stage)
        plan = TessTestPlan.model_validate(test_plan)
        cache = Path(task.cache_dir)
        data = TessAdapter().load(task.target, test_plan, cache)
        catalogs, scan = load_catalogs(task.catalog_paths, task.scan_path, cache)
        star = data.star
        drawn = inj.draw_injections(
            task.seed,
            task.k,
            inj.first_time(data),
            star.radius_rsun if star else None,
            star.logg_cgs if star else None,
        )[task.index]
        result = chain(inj.inject(data, drawn), plan, task.stage, catalogs, scan)
        record.update(
            {
                "status": "OK",
                "injection": drawn.to_dict(),
                "chain": result,
                "recovery": inj.recovery(drawn, result["candidate"], result["gate_passed"]),
            }
        )
    except Exception as exc:  # noqa: BLE001 - recorded; the injection stays in the denominator
        record.update({"status": "ERROR", "reason": f"{type(exc).__name__}: {exc}"})
        record["recovery"] = {"recovered": False, "alias": None, "gate_passed": False}
    record["cpu_seconds"] = time.process_time() - started
    return record


@dataclass(frozen=True)
class TransformTask:
    """One transformed curve of one star (picklable)."""

    target: dict[str, Any]
    test_plan: dict[str, Any]
    cache_dir: str
    seed: int
    position: int  # 0 inverted, 1 and 2 the rotations
    stage: int
    catalog_paths: tuple[str, ...] = field(default_factory=tuple)
    scan_path: str | None = None


def transforms_of(target: dict[str, Any], cache_dir: Path, seed: int, plan: TessTestPlan):
    """The three transformations of a star's curve and the rotation record, from the raw
    lengths of the sectors the plan reads (up to its ``max_sector``)."""
    from refute.core.io import read_json
    from refute.packs.tess.adapter import manifest_path, raw_lengths

    manifest = read_json(manifest_path(cache_dir, int(target["tic_id"])))
    limit = plan.discovery.max_sector if plan.discovery is not None else None
    if limit is not None:
        manifest = {**manifest, "files": [f for f in manifest["files"] if f["sector"] <= limit]}
    return transforms_for(seed, raw_lengths(manifest, cache_dir))


def run_transform(task: TransformTask) -> dict[str, Any]:
    """One transformed curve. ``cpu_seconds`` is the whole task, also when it fails."""
    from refute.packs.tess.adapter import TessAdapter

    started = time.process_time()
    record: dict[str, Any] = {
        "target_key": task.target["key"],
        "position": task.position,
        "stage": task.stage,
    }
    try:
        test_plan = stage_plan(task.test_plan, task.stage)
        plan = TessTestPlan.model_validate(test_plan)
        cache = Path(task.cache_dir)
        transforms, rotations = transforms_of(task.target, cache, task.seed, plan)
        transform: Transform = transforms[task.position]
        record.update({"transform": transform.to_dict(), "rotations": rotations.to_dict()})
        if transform.kind == "rotate" and (task.position - 1) in rotations.inconclusive:
            record.update(
                {"chain": None, "status": "INCONCLUSIVE", "reason": "no distinct offsets drawn"}
            )
        else:
            data = TessAdapter().load(task.target, test_plan, cache, transform=transform)
            catalogs, scan = load_catalogs(task.catalog_paths, task.scan_path, cache)
            record.update({"chain": chain(data, plan, task.stage, catalogs, scan), "status": "OK"})
    except Exception as exc:  # noqa: BLE001 - recorded: the transformed curve is INCONCLUSIVE
        record.update({"chain": None, "status": "INCONCLUSIVE", "reason": f"{exc}"})
    record["cpu_seconds"] = time.process_time() - started
    return record


def summarize_transforms(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Per curve: transformed curves run, detections that pass the gate, and detections that
    survive the declared tests of their stage, counted apart. Not a false-alarm rate."""
    ok = [r for r in records if r.get("status") == "OK"]
    return {
        "name": "detections on transformed curves (not a false-alarm rate)",
        "transformed_curves": len(records),
        "inconclusive": len(records) - len(ok),
        "gate_passed": sum(1 for r in ok if r["chain"]["gate_passed"]),
        "survived_stage_tests": sum(1 for r in ok if r["chain"]["survived_stage_tests"]),
    }
