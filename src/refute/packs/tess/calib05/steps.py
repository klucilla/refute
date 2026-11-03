"""The steps of the v0.5 calibration (calibration/v0.5/PROTOCOL.md, section 8), so that every line
they execute is inside the lock's code hash; ``calibration/v0.5/run_calibration.py`` only parses
its arguments and calls these. Each step that runs tasks writes into a new folder (refused if it
exists) and its report exclusively.

C1: ``c1_prefix`` (the development prefix and the cost rule), ``c1_confirmation`` (after R_c1,
once). C2: ``c2_fetch`` (a new download and the input check), ``c2_prefix`` (3 stars, the
compatibility and the cost), ``c2_run``. C3: ``c3_claim``, ``c3_run``. ``r_c1`` reads the round
fixed by the CI push run of the lock's commit B.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from refute.packs.tess.calib05 import c1, c2, c3run, runner
from refute.packs.tess.calib05.values import BUDGET, C1, C2, STEP_DIR

RUNS = Path(".cache/v05/calibration")
V04_STEP = Path("calibration/v0.4")


def _write_once(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, indent=2, sort_keys=True, default=str) + "\n")


def v04_test_plan(root: Path) -> dict[str, Any]:
    import yaml

    claim = yaml.safe_load((Path(root) / V04_STEP / "claim.yaml").read_text(encoding="utf-8"))
    return claim["test_plan"]


# --- C1 ---------------------------------------------------------------------------------


def c1_sizes(projected_hours: float) -> dict[str, int]:
    """The sizes of the confirmation set: the protocol's, each halved (by this rule, before the
    run) when the projection exceeds ``C1.max_processor_hours``."""
    if projected_hours > C1.max_processor_hours:
        return {f: n // 2 for f, n in C1.sizes.items()}
    return dict(C1.sizes)


def c1_prefix(root: Path, workers: int | None = None) -> dict[str, Any]:
    """The development prefix: the first ``C1.development_prefix`` development seeds of each
    family; the projection of the full set's processor-hours and the sizes it gives."""
    plan = v04_test_plan(root)
    tasks = [
        c1.C1Task(f, i, c1.development_seed(f, i), plan)
        for f in c1.FAMILIES
        for i in range(C1.development_prefix)
    ]
    out_dir = Path(root) / RUNS / "c1-prefix"
    records = runner.run_tasks(c1.run_task, tasks, _c1_id, out_dir, workers)
    hours = runner.projected_hours(records, C1.sizes, "family")
    report = {
        "projected_processor_hours": hours,
        "cap": C1.max_processor_hours,
        "sizes": c1_sizes(hours),
        "prefix_tasks": len(records),
        "prefix_processor_hours": sum(float(r["cpu_seconds"]) for r in records) / 3600.0,
        "metrics_development": c1.metrics(records),
    }
    _write_once(out_dir / "report.json", report)
    return report


def _c1_id(task: c1.C1Task) -> str:
    return f"{task.family}/{task.index}"


def r_c1(root: Path, commit_b: str) -> tuple[int, dict[str, Any], str]:
    """The round R_c1: the first drand round at least one hour after the creation of the CI push
    run of the lock's commit B; its beacon, signature verified."""
    from refute.drand import drand_seed, round_after
    from refute.packs.tess.discover import pilot

    created = pilot.push_run_created_at(commit_b)
    number = round_after(created)
    _seed, beacon = drand_seed(number)
    return number, beacon, created


def c1_confirmation(
    root: Path, commit_b: str, prefix_report: Path, workers: int | None = None
) -> dict[str, Any]:
    """The confirmation set, once, on the locked code: the sizes of the prefix's report, the
    seeds of R_c1; the metrics and the decision rules D1 to D5."""
    prefix = json.loads(Path(prefix_report).read_text(encoding="utf-8"))
    number, beacon, created = r_c1(root, commit_b)
    plan = v04_test_plan(root)
    tasks = [
        c1.C1Task(f, i, c1.confirmation_seed(beacon["randomness"], f, i), plan)
        for f, n in prefix["sizes"].items()
        for i in range(n)
    ]
    out_dir = Path(root) / RUNS / "c1-confirmation"
    runner.run_tasks(c1.run_task, tasks, _c1_id, out_dir, workers)
    records = runner.all_records(out_dir, [_c1_id(t) for t in tasks])
    report = {
        "round": number,
        "beacon": beacon,
        "push_run_created_at": created,
        "lock_commit_b": commit_b,
        "sizes": prefix["sizes"],
        "processor_hours": sum(float(r["cpu_seconds"]) for r in records) / 3600.0,
        **c1.metrics(records),
    }
    _write_once(out_dir / "report.json", report)
    return report


# --- C2 ---------------------------------------------------------------------------------


def c2_targets(root: Path) -> list[dict[str, Any]]:
    """The v0.4 funnel's 100 stars, in the run set's order."""
    import yaml

    doc = yaml.safe_load(
        (Path(root) / V04_STEP / "selection" / "targets.yaml").read_text(encoding="utf-8")
    )
    by_key = {t["key"]: t for t in doc["targets"]}
    run_set = json.loads(
        (Path(root) / V04_STEP / "runs" / "funnel_run_set.json").read_text(encoding="utf-8")
    )
    keys = run_set["run_set"] if isinstance(run_set, dict) else run_set
    return [by_key[k] for k in keys]


def development_stars(root: Path) -> set[str]:
    """The three promoted stars of v0.4 (the development cases of v0.5)."""
    record = json.loads(
        (Path(root) / V04_STEP / "runs" / "promotion.json").read_text(encoding="utf-8")
    )
    return {str(k) for k in record["promoted"]}


def c2_cache(root: Path) -> Path:
    return Path(root) / ".cache" / "v05" / "c2" / "cache"


def c2_fetch(root: Path) -> dict[str, Any]:
    """A new download of every star's light curves (stage 1: no pixel file) into a new cache,
    and the input check against each v0.4 dossier's manifest. The TESS-EB static edition is
    placed where the v0.4 claim's catalog scan expects it, checked against its content SHA-256."""
    from refute.core.io import read_json
    from refute.packs.tess.adapter import TessAdapter, manifest_path
    from refute.packs.tess.discover.claim import TESS_EB_CACHE_PATH
    from refute.packs.tess.discover.measure import stage_plan
    from refute.packs.tess.discover.pilot import TESS_EB_STATIC, static_tess_eb

    cache = c2_cache(root)
    cache.mkdir(parents=True, exist_ok=False)
    eb = cache / TESS_EB_CACHE_PATH
    eb.parent.mkdir(parents=True)
    with open(eb, "xb") as handle:
        handle.write(static_tess_eb(Path(root) / TESS_EB_STATIC["path"], TESS_EB_STATIC))
    plan = stage_plan(v04_test_plan(root), 1)
    dossiers, _ = c2.references(root)
    changed: dict[str, list[str]] = {}
    for target in c2_targets(root):
        TessAdapter().fetch(target, plan, cache)
        new = read_json(manifest_path(cache, int(target["tic_id"])))
        problems = c2.input_problems(new, dossiers[target["key"]]["manifest"])
        if problems:
            changed[target["key"]] = problems
    report = {"cache": cache.as_posix(), "stars": C2.stars, "input_changed": changed}
    _write_once(Path(root) / RUNS / "c2-fetch.json", report)
    return report


def c2_tasks(root: Path, keys: list[str] | None, k: int) -> list[c2.C2Task]:
    fetch = json.loads((Path(root) / RUNS / "c2-fetch.json").read_text(encoding="utf-8"))
    r_inj = json.loads((Path(root) / V04_STEP / "runs" / "r_inj.json").read_text("utf-8"))
    randomness = r_inj["beacon"]["randomness"]
    step = Path(root) / V04_STEP
    catalog = ((step / "eb_catalog.csv").as_posix(),)
    scan = (step / "eb_catalog_scan.json").as_posix()
    plan = v04_test_plan(root)
    tasks = []
    for target in c2_targets(root):
        if target["key"] in fetch["input_changed"]:
            continue
        if keys is not None and target["key"] not in keys:
            continue
        tasks += c2.tasks_for(target, plan, Path(fetch["cache"]), randomness, catalog, scan, k)
    return tasks


def _compat(root: Path, records: list[dict[str, Any]]) -> dict[str, list[str]]:
    dossiers, measurements = c2.references(root)
    out = {}
    for r in records:
        if r["kind"] == "original":
            ref = dossiers[r["target_key"]]["reference"]
        else:
            ref = measurements.get(r["task"])
            if ref is None:
                out[r["task"]] = ["no v0.4 record of this curve"]
                continue
        out[r["task"]] = c2.compat_problems(r, ref)
    return out


def c2_prefix(root: Path, workers: int | None = None) -> dict[str, Any]:
    """The first 3 authenticated stars of the run set: every curve, the compatibility check and
    the cost per task kind (for the projection of section 8)."""
    keys = [
        t["key"]
        for t in c2_targets(root)
        if t["key"]
        not in json.loads((Path(root) / RUNS / "c2-fetch.json").read_text("utf-8"))["input_changed"]
    ][:3]
    tasks = c2_tasks(root, keys, C2.injections_per_curve)
    out_dir = Path(root) / RUNS / "c2-prefix"
    records = runner.run_tasks(c2.run_task, tasks, c2.task_id, out_dir, workers)
    compat = _compat(root, records)
    report = {
        "stars": keys,
        "compatibility": {k: v for k, v in compat.items() if v},
        "cpu_seconds_by_kind": {
            kind: [float(r["cpu_seconds"]) for r in records if r["kind"] == kind]
            for kind in c2.KINDS
        },
    }
    _write_once(out_dir / "report.json", report)
    return report


def c2_run(root: Path, k: int, workers: int | None = None) -> dict[str, Any]:
    """Every authenticated star (``k`` injections per curve: 20, or 10 by the budget rule of
    section 8, decided before the run); then the compatibility and the summary."""
    if k not in (C2.injections_per_curve, C2.injections_fallback):
        raise ValueError("k is 20 or, by the budget rule, 10")
    tasks = c2_tasks(root, None, k)
    out_dir = Path(root) / RUNS / "c2"
    runner.run_tasks(c2.run_task, tasks, c2.task_id, out_dir, workers)
    records = runner.all_records(out_dir, [c2.task_id(t) for t in tasks])
    fetch = json.loads((Path(root) / RUNS / "c2-fetch.json").read_text(encoding="utf-8"))
    report = c2.summarize(
        records, fetch["input_changed"], development_stars(root), _compat(root, records)
    )
    report["processor_hours"] = sum(float(r["cpu_seconds"]) for r in records) / 3600.0
    report["injections_per_curve"] = k
    _write_once(out_dir / "report.json", report)
    return report


# --- C3 ---------------------------------------------------------------------------------


def c3_claim(root: Path) -> dict[str, Any]:
    """The C3 claim from the committed protocol, inputs and selection."""
    from refute.packs.tess.calib05.c3select import cache_dir
    from refute.packs.tess.discover import pilot

    inputs = json.loads((Path(root) / STEP_DIR / "inputs.json").read_text(encoding="utf-8"))
    return c3run.write_claim(root, cache_dir(root, inputs), pilot.utc_now()[:10])


def c3_run(root: Path, cache: Path, workers: int | None = None) -> dict[str, Any]:
    """Every C3 control and reserve (the data fetched by ``refute fetch --stage 2`` into
    ``cache``), the assignment by the replacement rule and the targets T3a and T3b."""
    import yaml

    step = Path(root) / STEP_DIR
    claim = yaml.safe_load((step / "claim.yaml").read_text(encoding="utf-8"))
    targets = yaml.safe_load((step / "selection" / "targets.yaml").read_text("utf-8"))["targets"]
    from refute.packs.tess.params import TessTestPlan

    v05 = TessTestPlan.model_validate(claim["test_plan"])
    if not v05.v05:
        raise ValueError("the C3 claim is not a v0.5 claim")
    inputs = json.loads((step / "inputs.json").read_text(encoding="utf-8"))
    plan_v04 = c3run.v04_plan_for(root, inputs, step)
    catalog = ((step / c3run.EB_CATALOG).as_posix(),)
    scan = (step / c3run.EB_SCAN).as_posix()
    tasks = [c3run.C3Task(t, plan_v04, str(cache), catalog, scan) for t in targets]
    out_dir = Path(root) / RUNS / "c3"
    runner.run_tasks(c3run.run_task, tasks, c3run.task_id, out_dir, workers)
    records = runner.all_records(out_dir, [c3run.task_id(t) for t in tasks])
    by_key = {r["target_key"]: r for r in records}
    assigned = c3run.assign(targets, by_key)
    report = {
        "assignment": assigned,
        "targets": c3run.targets(assigned, by_key),
        "processor_hours": sum(float(r["cpu_seconds"]) for r in records) / 3600.0,
        "budget_reserve_processor_hours": BUDGET.reserve_processor_hours,
    }
    _write_once(out_dir / "report.json", report)
    return report
