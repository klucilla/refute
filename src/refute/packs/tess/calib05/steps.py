"""The steps of the v0.5 calibration (calibration/v0.5/PROTOCOL.md, section 8), so that every line
they execute is inside the lock's code hash; ``calibration/v0.5/run_calibration.py`` only parses
its arguments and calls these. Each step that runs tasks writes into a new run folder with its
manifest (``runner.py``) and its report exclusively.

Every step after the freeze first checks the freeze (``frozen_code``): the tree's code hash must be
the one recorded in ``inputs.json`` by the freeze. C1: ``c1_prefix`` (the development prefix),
``c1_confirmation`` (after R_c1, once; commit B authenticated as the commit that added the lock,
whose code hash is the frozen one; the sizes recomputed from the authenticated prefix). C2:
``c2_fetch`` (a new download and the input check), ``c2_prefix`` (3 stars, 10 injections each:
the compatibility and the cost; reused by ``c2_run``), ``budget`` (the decision of section 8),
``c2_run``. C3: ``c3_claim``, ``c3_fetch`` (stage 2, the product state of every control),
``c3_run``.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

from refute.packs.tess.calib05 import c1, c2, c3run, runner
from refute.packs.tess.calib05.values import BUDGET, C1, C2, C3, STEP_DIR

RUNS = Path(".cache/v05/calibration")
V04_STEP = Path("calibration/v0.4")
LOCK_FILE = f"{STEP_DIR}/claim.lock.json"


def _write_once(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, indent=2, sort_keys=True, default=str) + "\n")


def _read(path: Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def v04_test_plan(root: Path) -> dict[str, Any]:
    import yaml

    claim = yaml.safe_load((Path(root) / V04_STEP / "claim.yaml").read_text(encoding="utf-8"))
    return claim["test_plan"]


def frozen_code(root: Path) -> str:
    """The freeze, checked: the designated freeze commit, every bound path (the code, the
    protocol, the inputs and the v0.4 records the calibration reads) its bytes, and the tree's
    code hash the one its ``inputs.json`` records. Returns that code hash."""
    from refute.packs.tess.calib05.c3select import bound_problems, code_record, freeze_commit

    root = Path(root)
    commit = freeze_commit(root)
    problems = bound_problems(root, commit)
    if problems:
        raise ValueError("the freeze is not intact: " + "; ".join(problems))
    frozen = json.loads(_git(root, "show", f"{commit}:{STEP_DIR}/inputs.json"))["code"]["sha256"]
    if code_record(root)["sha256"] != frozen:
        raise ValueError("the tree's code hash is not the one frozen in inputs.json")
    return frozen


def _authenticated(root: Path, out_dir: Path, fn, tasks, task_id, step: str) -> list[dict]:
    """A run folder's records, refused unless its manifest names this step and the frozen code,
    and its function, task identities and tasks' SHA-256 are those of ``tasks`` rebuilt now."""
    manifest = runner.read_manifest(out_dir)
    if manifest["provenance"].get("code_sha256") != frozen_code(root):
        raise ValueError(f"{out_dir.name}: not run by the frozen code")
    if manifest["provenance"].get("step") != step:
        raise ValueError(f"{out_dir.name}: not a {step} run")
    rebuilt = runner.manifest_of(fn, tasks, task_id, {})
    for key in ("function", "tasks", "tasks_sha256"):
        if manifest[key] != rebuilt[key]:
            raise ValueError(f"{out_dir.name}: its `{key}` is not that of the scheduled tasks")
    return runner.all_records(out_dir)


def _budget_decision(root: Path) -> int:
    """The written budget decision (20 or 10 injections per curve); a stop, or no decision,
    refuses every run that reads it."""
    path = Path(root) / RUNS / "budget.json"
    if not path.is_file():
        raise ValueError("no budget decision: run the budget step first")
    decision = _read(path)["injections_per_curve"]
    if decision not in (C2.injections_per_curve, C2.injections_fallback):
        raise ValueError(f"the budget decision is {decision!r}: nothing runs")
    return decision


# --- C1 ---------------------------------------------------------------------------------


def _c1_id(task: c1.C1Task) -> str:
    return f"{task.family}/{task.index}"


def c1_sizes(projected_hours: float) -> dict[str, int]:
    """The sizes of the confirmation set: the protocol's, each halved (by this rule, before the
    run) when the projection exceeds ``C1.max_processor_hours``."""
    if projected_hours > C1.max_processor_hours:
        return {f: n // 2 for f, n in C1.sizes.items()}
    return dict(C1.sizes)


def _c1_prefix_tasks(root: Path) -> list[c1.C1Task]:
    plan = v04_test_plan(root)
    return [
        c1.C1Task(f, i, c1.development_seed(f, i), plan)
        for f in c1.FAMILIES
        for i in range(C1.development_prefix)
    ]


def c1_prefix(root: Path, workers: int | None = None) -> dict[str, Any]:
    """The development prefix: the first ``C1.development_prefix`` development seeds of each
    family; the projection of the full set's processor-hours and the sizes it gives."""
    frozen_code(root)
    tasks = _c1_prefix_tasks(root)
    out_dir = Path(root) / RUNS / "c1-prefix"
    prov = runner.provenance(root, step="c1-prefix")
    runner.run_tasks(c1.run_task, tasks, _c1_id, out_dir, workers, prov)
    return c1_prefix_report(root, write=True)


def c1_prefix_report(root: Path, write: bool = False) -> dict[str, Any]:
    """The prefix's projection, from its authenticated records (never from a report file)."""
    tasks = _c1_prefix_tasks(root)
    out_dir = Path(root) / RUNS / "c1-prefix"
    records = _authenticated(root, out_dir, c1.run_task, tasks, _c1_id, "c1-prefix")
    hours = runner.projected_hours(records, C1.sizes, "family")
    sizes = c1_sizes(hours)
    report = {
        "projected_processor_hours": hours,
        "cap": C1.max_processor_hours,
        "sizes": sizes,
        "projected_confirmation_hours": runner.projected_hours(records, sizes, "family"),
        "prefix_tasks": len(records),
        "prefix_processor_hours": sum(float(r["cpu_seconds"]) for r in records) / 3600.0,
        "mean_cpu_seconds": sum(float(r["cpu_seconds"]) for r in records) / len(records),
    }
    if write:
        _write_once(out_dir / "report.json", {**report, "development": c1.metrics(records)})
    return report


def _git(root: Path, *args: str) -> str:
    done = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise ValueError(f"git {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout.strip()


def lock_commit_b(root: Path) -> str:
    """Commit B: the one commit that added the C3 lock file; its first parent must be the commit
    the lock records (commit A), the lock's code hash must be the frozen one, and the lock must
    verify against the claim and its attachments as they are now (``refute verify``)."""
    from refute.core.lock import VerifyStatus, verify_claim

    added = _git(root, "log", "--diff-filter=A", "--format=%H", "--", LOCK_FILE).split()
    if len(added) != 1:
        raise ValueError(f"{len(added)} commits added {LOCK_FILE}; the maintainer decides")
    commit_b = added[0]
    lock = json.loads(_git(root, "show", f"{commit_b}:{LOCK_FILE}"))
    parent = _git(root, "rev-parse", f"{commit_b}^1")
    if lock.get("git_commit") != parent:
        raise ValueError("the lock does not record the parent of commit B as its commit A")
    if lock["code"]["sha256"] != frozen_code(root):
        raise ValueError("the lock's code hash is not the one frozen in inputs.json")
    if _git(root, "diff", "--name-only", commit_b, "--", LOCK_FILE):
        raise ValueError("the lock file differs from commit B's")
    verified = verify_claim(Path(root) / STEP_DIR / "claim.yaml", code_root=Path(root))
    if verified.status is not VerifyStatus.PASS:
        raise ValueError(f"the C3 claim does not verify against its lock: {verified.status}")
    return commit_b


def r_c1(commit_b: str) -> tuple[int, dict[str, Any], str]:
    """The round R_c1: the first drand round at least one hour after the creation of the CI push
    run of commit B; its beacon, signature verified."""
    from refute.drand import drand_seed, round_after
    from refute.packs.tess.discover import pilot

    created = pilot.push_run_created_at(commit_b)
    number = round_after(created)
    _seed, beacon = drand_seed(number)
    return number, beacon, created


def c1_confirmation(
    root: Path, commit_b: str, workers: int | None = None, approval_url: str | None = None
) -> dict[str, Any]:
    """The confirmation set, once, on the locked code. Before any network access: commit B
    authenticated and equal to ``commit_b``, the budget decision read, the sizes recomputed from
    the authenticated prefix, and an attempt reserved (any later attempt needs its approval URL);
    then the round, every family and index with the seeds of R_c1; the metrics and D1 to D5."""
    out_dir = Path(root) / RUNS / "c1-confirmation"
    if out_dir.exists():
        raise FileExistsError(f"{out_dir} exists: the confirmation runs once")
    found_b = lock_commit_b(root)
    if commit_b != found_b:
        raise ValueError(f"commit B is {found_b}, not {commit_b}")
    _budget_decision(root)
    sizes = c1_prefix_report(root)["sizes"]
    attempt = runner.reserve_attempt(
        Path(root) / RUNS / "c1-confirmation-attempts", approval_url, "R_c1"
    )
    number, beacon, created = r_c1(commit_b)
    with open(attempt / "round.json", "x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps({"round": number, "beacon": beacon}, default=str) + "\n")
    plan = v04_test_plan(root)
    tasks = [
        c1.C1Task(f, i, c1.confirmation_seed(beacon["randomness"], f, i), plan)
        for f in c1.FAMILIES
        for i in range(sizes[f])
    ]
    prov = runner.provenance(
        root, step="c1-confirmation", round=number, commit_b=commit_b, attempt=attempt.name
    )
    runner.run_tasks(c1.run_task, tasks, _c1_id, out_dir, workers, prov)
    records = runner.all_records(out_dir)
    report = {
        "round": number,
        "beacon": beacon,
        "push_run_created_at": created,
        "lock_commit_b": commit_b,
        "sizes": sizes,
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
    run_set = _read(Path(root) / V04_STEP / "runs" / "funnel_run_set.json")
    keys = run_set["run_set"] if isinstance(run_set, dict) else run_set
    return [by_key[k] for k in keys]


def development_stars(root: Path) -> set[str]:
    """The three promoted stars of v0.4 (the development cases of v0.5)."""
    record = _read(Path(root) / V04_STEP / "runs" / "promotion.json")
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

    frozen_code(root)
    cache = c2_cache(root)
    cache.mkdir(parents=True, exist_ok=False)
    eb = cache / TESS_EB_CACHE_PATH
    eb.parent.mkdir(parents=True)
    with open(eb, "xb") as handle:
        handle.write(static_tess_eb(Path(root) / TESS_EB_STATIC["path"], TESS_EB_STATIC))
    plan = stage_plan(v04_test_plan(root), 1)
    dossiers, _ = c2.references(root)
    changed: dict[str, list[str]] = {}
    files: dict[str, list[dict[str, Any]]] = {}
    for target in c2_targets(root):
        TessAdapter().fetch(target, plan, cache)
        new = read_json(manifest_path(cache, int(target["tic_id"])))
        files[target["key"]] = [
            {k: f.get(k) for k in ("name", "url", "bytes", "sha256")} for f in new["files"]
        ]
        problems = c2.input_problems(new, dossiers[target["key"]]["manifest"])
        if problems:
            changed[target["key"]] = problems
    report = {
        "cache": cache.as_posix(),
        "stars": C2.stars,
        "input_changed": changed,
        "files": files,
    }
    _write_once(Path(root) / RUNS / "c2-fetch.json", report)
    return report


def _c2_fetch(root: Path) -> dict[str, Any]:
    return _read(Path(root) / RUNS / "c2-fetch.json")


def c2_tasks(root: Path, keys: list[str] | None, k: int) -> list[c2.C2Task]:
    fetch = _c2_fetch(root)
    r_inj = _read(Path(root) / V04_STEP / "runs" / "r_inj.json")
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


def _c2_prefix_stars(root: Path) -> list[str]:
    changed = _c2_fetch(root)["input_changed"]
    return [t["key"] for t in c2_targets(root) if t["key"] not in changed][:3]


def _c2_prefix_tasks(root: Path) -> list[c2.C2Task]:
    # 10 injections: their draws are the first 10 of each star's stream for any K, so the
    # prefix is part of the full run whether the budget gives 20 or 10
    return c2_tasks(root, _c2_prefix_stars(root), C2.injections_fallback)


def c2_prefix(root: Path, workers: int | None = None) -> dict[str, Any]:
    """The first 3 authenticated stars of the run set (the original, 3 transformed and 10
    injected curves each): the compatibility and the cost per task kind. Its records are part of
    the full C2 run (``c2_run`` schedules only the remaining curves)."""
    frozen_code(root)
    tasks = _c2_prefix_tasks(root)
    out_dir = Path(root) / RUNS / "c2-prefix"
    prov = runner.provenance(root, step="c2-prefix")
    runner.run_tasks(c2.run_task, tasks, c2.task_id, out_dir, workers, prov)
    records = runner.all_records(out_dir)
    compat = _compat(root, records)
    report = {
        "stars": _c2_prefix_stars(root),
        "compatibility": {k: v for k, v in compat.items() if v},
        "cpu_seconds_by_kind": {
            kind: [float(r["cpu_seconds"]) for r in records if r["kind"] == kind]
            for kind in c2.KINDS
        },
    }
    _write_once(out_dir / "report.json", report)
    return report


def _c2_prefix_records(root: Path) -> list[dict[str, Any]]:
    tasks = _c2_prefix_tasks(root)
    return _authenticated(
        root, Path(root) / RUNS / "c2-prefix", c2.run_task, tasks, c2.task_id, "c2-prefix"
    )


def budget(root: Path) -> dict[str, Any]:
    """The decision of section 8, before C1's confirmation and before C2 and C3 run, from the
    authenticated prefixes: the projected processor-hours of C1 (its sizes), of C2 with 20 and with
    10 injections per curve (the remaining curves, at the prefix's mean CPU per task kind) and of
    C3 (every control and reserve, two paired runs each, at the larger of C1's and C2's mean CPU
    per curve, times two for the pixel tests of stage 2); against the reserve minus the hours the
    calibration's runs have used. 20 when everything fits, else 10, else ``stop`` (the maintainer
    decides). Written once."""
    c1_report = c1_prefix_report(root)
    prefix = _c2_prefix_records(root)
    if any(_compat(root, prefix).values()):
        raise ValueError("the C2 prefix's compatibility is not established")
    mean = {
        kind: sum(float(r["cpu_seconds"]) for r in prefix if r["kind"] == kind)
        / max(1, sum(r["kind"] == kind for r in prefix))
        for kind in c2.KINDS
    }
    authenticated = C2.stars - len(_c2_fetch(root)["input_changed"])
    rest = authenticated - len(_c2_prefix_stars(root))
    prefix_stars = len(_c2_prefix_stars(root))

    def c2_hours(k: int) -> float:
        per_star = mean["original"] + 3 * mean["transform"] + k * mean["injection"]
        extra = (k - C2.injections_fallback) * mean["injection"] * prefix_stars
        return (rest * per_star + extra) / 3600.0

    sizes = c1_report["sizes"]
    c1_hours = c1_report["projected_confirmation_hours"]
    per_curve = max(c1_report["mean_cpu_seconds"], mean["original"])
    c3_hours = (C3.planets + C3.false_positives + 2 * C3.reserves) * 2 * 2 * per_curve / 3600.0
    used = (
        c1_report["prefix_processor_hours"] + sum(float(r["cpu_seconds"]) for r in prefix) / 3600.0
    )
    remaining = BUDGET.reserve_processor_hours - used
    decision = "stop"
    for k in (C2.injections_per_curve, C2.injections_fallback):
        if c1_hours + c2_hours(k) + c3_hours <= remaining:
            decision = k
            break
    record = {
        "c1_projected_hours": c1_hours,
        "c1_sizes": sizes,
        "c2_projected_hours": {
            str(k): c2_hours(k) for k in (C2.injections_per_curve, C2.injections_fallback)
        },
        "c3_projected_hours": c3_hours,
        "used_hours": used,
        "remaining_hours": remaining,
        "reserve_hours": BUDGET.reserve_processor_hours,
        "injections_per_curve": decision,
        "rule": "PROTOCOL.md section 8: 20 when C1 + C2 + C3 fit the remaining reserve, else 10, "
        "else stop",
    }
    _write_once(Path(root) / RUNS / "budget.json", record)
    return record


def c2_run(root: Path, workers: int | None = None) -> dict[str, Any]:
    """Every authenticated star with the budget's injections per curve; the prefix's records are
    reused (its compatibility must be established before any dispatch) and only the remaining
    curves run; then the compatibility over every curve and the summary."""
    frozen_code(root)
    decision = _budget_decision(root)
    prefix = _c2_prefix_records(root)
    if any(_compat(root, prefix).values()):
        raise ValueError("the C2 prefix's compatibility is not established")
    expected = c2_tasks(root, None, decision)
    done = {r["task"] for r in prefix}
    tasks = [t for t in expected if c2.task_id(t) not in done]
    out_dir = Path(root) / RUNS / "c2"
    prov = runner.provenance(root, step="c2", injections_per_curve=decision)
    runner.run_tasks(c2.run_task, tasks, c2.task_id, out_dir, workers, prov)
    records = runner.all_records(out_dir)
    expected_ids = {c2.task_id(t) for t in expected}
    union = [r for r in prefix if r["task"] in expected_ids] + records
    if sorted(r["task"] for r in union) != sorted(expected_ids):
        raise ValueError("the prefix and the run are not exactly the scheduled curves")
    report = c2.summarize(
        union, _c2_fetch(root)["input_changed"], development_stars(root), _compat(root, union)
    )
    report["processor_hours"] = sum(float(r["cpu_seconds"]) for r in union) / 3600.0
    report["injections_per_curve"] = decision
    _write_once(out_dir / "report.json", report)
    return report


# --- C3 ---------------------------------------------------------------------------------


def c3_claim(root: Path) -> dict[str, Any]:
    """The C3 claim from the committed protocol, inputs and selection."""
    from refute.packs.tess.calib05.c3select import cache_dir
    from refute.packs.tess.discover import pilot

    frozen_code(root)
    inputs = _read(Path(root) / STEP_DIR / "inputs.json")
    return c3run.write_claim(root, cache_dir(root, inputs), pilot.utc_now()[:10])


def _c3_targets(root: Path) -> list[dict[str, Any]]:
    import yaml

    path = Path(root) / STEP_DIR / "selection" / "targets.yaml"
    return yaml.safe_load(path.read_text("utf-8"))["targets"]


def c3_fetch(root: Path, cache: Path) -> dict[str, Any]:
    """Stage 2 (light curves and pixel files) of every control and reserve into ``cache``, and
    each one's product state (``c3run.product_state``). Written once."""
    import yaml

    frozen_code(root)
    _budget_decision(root)
    step = Path(root) / STEP_DIR
    claim = yaml.safe_load((step / "claim.yaml").read_text(encoding="utf-8"))
    states = {
        t["key"]: c3run.fetch_products(t, claim["test_plan"], Path(cache))
        for t in _c3_targets(root)
    }
    report = {"cache": Path(cache).as_posix(), "states": states}
    _write_once(Path(root) / RUNS / "c3-fetch.json", report)
    return report


def c3_run(root: Path, workers: int | None = None) -> dict[str, Any]:
    """Every C3 control and reserve with its product state, the assignment by the replacement
    rule and the targets T3a and T3b."""
    import yaml

    from refute.packs.tess.params import TessTestPlan

    frozen_code(root)
    _budget_decision(root)
    step = Path(root) / STEP_DIR
    claim = yaml.safe_load((step / "claim.yaml").read_text(encoding="utf-8"))
    targets = _c3_targets(root)
    if not TessTestPlan.model_validate(claim["test_plan"]).v05:
        raise ValueError("the C3 claim is not a v0.5 claim")
    fetch = _read(Path(root) / RUNS / "c3-fetch.json")
    inputs = _read(step / "inputs.json")
    plan_v04 = c3run.v04_plan_for(root, inputs, step)
    catalog = ((step / c3run.EB_CATALOG).as_posix(),)
    scan = (step / c3run.EB_SCAN).as_posix()
    tasks = [
        c3run.C3Task(t, plan_v04, fetch["cache"], fetch["states"][t["key"]], catalog, scan)
        for t in targets
    ]
    out_dir = Path(root) / RUNS / "c3"
    prov = runner.provenance(root, step="c3")
    runner.run_tasks(c3run.run_task, tasks, c3run.task_id, out_dir, workers, prov)
    records = runner.all_records(out_dir)
    by_key = {r["target_key"]: r for r in records}
    assigned = c3run.assign(targets, by_key)
    report = {
        "assignment": assigned,
        "targets": c3run.targets(assigned, by_key),
        "processor_hours": sum(float(r["cpu_seconds"]) for r in records) / 3600.0,
    }
    _write_once(out_dir / "report.json", report)
    return report
