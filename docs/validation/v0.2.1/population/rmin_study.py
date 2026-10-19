"""The ``R_min`` study (docs/validation/v0.2.1/reopen/m4-implementation-map.md, Amendment 19; its
implementation, Amendment 26): the evaluator's side of the scenarios.

The study's light curves are the population harness's (``population_v2.build_case``, the frozen
version 2, loaded through version 3, which captures the M4 configuration). This module holds the
pure functions of the scenarios, computed from a case's **recorded final parameters** only (no
random generator is run again):

- ``deficit_and_trend``: the generator's transit deficit ``D(t)`` (``1 - signal_model``) and its
  multiplicative trend (``1`` for ``pure_noise``), as ``build_case`` builds them;
- ``alter_last_year``: the disappearing (``s = 0``) and weakened (``s = 0.3``) scenarios,
  ``flux + (1 - s) D(t) trend(t)`` on the cadences of the last observing year, the noise untouched;
- ``noiseless_model``: the scenario's complete model without noise (the signal times the trend,
  plus the variability, with the alteration where it applies), the twin's input.

The evaluator keeps the parameters and the scenario; the analysis receives only the light curve
and the metadata.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import population_v3 as v3  # noqa: E402

pv2 = v3.pv2

SCENARIOS = {"constant": 1.0, "disappearing": 0.0, "weakened": 0.3}
STUDY_MECHANISMS = ("two_years", "three_years", "few_train", "variability_some_years")


def _check(case: dict) -> None:
    if case["class"] != "planet" or case["mechanism"] not in STUDY_MECHANISMS:
        raise ValueError(f"{case['id']}: not a planet of the study's mechanisms")


def deficit_and_trend(case: dict, p: dict, time: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """The generator's ``D(t)`` and trend at ``time`` (``build_case``, the model before the
    noise)."""
    from refute.packs.tess import synthetic

    _check(case)
    t = np.asarray(time, dtype=float)
    deficit = 1.0 - synthetic.signal_model(t, pv2._signal_spec(synthetic, case, p, p["depth"]))
    if case["mechanism"] == "pure_noise":
        trend = np.ones_like(t)
    else:
        trend = 1.0 + pv2.TREND_AMPLITUDE * np.sin(2 * np.pi * t / pv2.TREND_PERIOD_DAYS)
    return deficit, trend


def _last_year_mask(year: np.ndarray) -> np.ndarray:
    year = np.asarray(year)
    return year == year.max()


def alter_last_year(
    case: dict, p: dict, time: np.ndarray, year: np.ndarray, flux: np.ndarray, s: float
) -> np.ndarray:
    """``flux + (1 - s) D(t) trend(t)`` on the last observing year's cadences; the other cadences
    and the noise unchanged. ``s = 1`` returns the flux as it is."""
    flux = np.asarray(flux, dtype=float)
    if s == 1.0:
        return flux.copy()
    deficit, trend = deficit_and_trend(case, p, time)
    last = _last_year_mask(year)
    return np.where(last, flux + (1.0 - s) * deficit * trend, flux)


def noiseless_model(
    case: dict, p: dict, time: np.ndarray, year: np.ndarray, s: float = 1.0
) -> np.ndarray:
    """The scenario's model without noise: ``(signal + (1 - s_y) D) trend + variability``, with
    ``s_y = s`` in the last observing year and 1 elsewhere (``build_case``'s model, altered as the
    scenario is; with ``s = 1`` the very products of ``build_case``)."""
    from refute.packs.tess import synthetic

    t = np.asarray(time, dtype=float)
    year = np.asarray(year)
    deficit, trend = deficit_and_trend(case, p, t)
    signal = synthetic.signal_model(t, pv2._signal_spec(synthetic, case, p, p["depth"]))
    factor = np.where(_last_year_mask(year), s, 1.0)
    model = (signal + (1.0 - factor) * deficit) * trend
    if "var_amplitude" in p:
        present = year != p.get("var_absent_year")
        model = model + np.where(
            present,
            p["var_amplitude"] * np.sin(2 * np.pi * (t - p["var_phase"]) / p["var_period"]),
            0.0,
        )
    return model


# --- the study's timing lot (Amendment 26, 6) ------------------------------------------------

TIMING_PREFIX = "refute-v0.2.1-rmin-timing"
# The rule fixed by Amendment 26, 6: per noise model, without variability 10 near and 10
# measurable (two_years, three_years, few_train in the proportion 2 : 1 : 1); with variability the
# indexes 200 to 209 of each band.
TIMING_INDEXES = {
    "near": (0, 1, 2, 3, 4, 100, 101, 102, 150, 151, *range(200, 210)),
    "measurable": (0, 1, 2, 3, 4, 100, 101, 150, 151, 152, *range(200, 210)),
}
R_VALUES = (8, 10, 12, 15, 20)
THREAD_ENV = {
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}


def group_of(case: dict) -> str:
    noise = "white" if case["noise"] == "white" else "AR(1)"
    variability = (
        "variability" if case["mechanism"] == "variability_some_years" else "no variability"
    )
    return f"{noise}, {variability}"


def timing_cases() -> list[dict]:
    """The 80 targets of the timing lot, in the order of the population harness."""
    out = []
    for case in pv2.population_cases("confirm:" + TIMING_PREFIX):
        if case["class"] != "planet" or case["band"] not in TIMING_INDEXES:
            continue
        if case["index"] in TIMING_INDEXES[case["band"]]:
            out.append(case)
    return out


# The timing lot's own configuration (Amendment 26, 6), checked before any generation (added after
# the Codex review of the stage: any loaded configuration was accepted).
TIMING_CONFIGURATION = {
    "name": "M4-rmin-timing",
    "path": "docs/validation/v0.2.1/population/m4-configurations/rmin-timing.json",
}
TIMING_SETTINGS = {"r_min": 8, "capacity_b": 0.0, "capacity_s": 0.0}
TIMING_WORKERS = 6
TIMING_AFFINITY = "0xff"  # logical processors 0 to 7


def calibration_identity() -> dict:
    ident = v3.STATE["identity"]
    return {k: ident[k] for k in ("path", "sha256", "block_sha256")}


def timing_configuration_problems(identity: dict | None, plan) -> list[str]:
    """Why the loaded configuration is not the timing lot's (empty when it is)."""
    if identity is None:
        return ["no configuration identity"]
    problems = [
        f"{key} {identity.get(key)!r} is not {value!r}"
        for key, value in TIMING_CONFIGURATION.items()
        if identity.get(key) != value
    ]
    c = plan.gauntlet.corrections
    problems += [
        f"{key} {getattr(c, key)!r} is not {value!r}"
        for key, value in TIMING_SETTINGS.items()
        if getattr(c, key) != value
    ]
    return problems


def aggregate(outcomes: list[dict]) -> str:
    """``run_holdout``'s aggregation of a target's rounds: any FAIL gives FAIL; otherwise any PASS
    gives PASS; otherwise INCONCLUSIVE."""
    statuses = [o["status"] for o in outcomes]
    if "FAIL" in statuses:
        return "FAIL"
    if "PASS" in statuses:
        return "PASS"
    return "INCONCLUSIVE"


def time_target(case: dict, expected: dict | None = None) -> dict:
    """One target of the timing lot: the generation, then each scenario's rounds (with the twin)
    and its derivation and aggregation over the five R. Only times are returned: no record, count
    or outcome leaves this function (Amendment 26, 6). ``expected`` is the main process's
    configuration identity; this worker's must be the same and the timing lot's."""
    import os
    import time

    from refute.packs.tess.holdout import calibration_measurement, derive_round
    from refute.packs.tess.types import LightCurveData

    if v3.STATE["problem"] is not None:
        raise RuntimeError(f"the M4 configuration is not loaded: {v3.STATE['problem']}")
    plan = v3._plan()
    problems = timing_configuration_problems(v3.STATE["identity"], plan)
    if problems:
        raise RuntimeError("the configuration is not the timing lot's: " + "; ".join(problems))
    if expected is None or v3.STATE["identity"] != expected:
        raise RuntimeError("this worker's configuration has another identity than the main one")
    identity = calibration_identity()
    c = plan.gauntlet.corrections
    min_snr = plan.gauntlet.holdout_by_year.min_snr
    start = time.perf_counter()
    blob, _ = pv2.build_case(case)
    meta, arrays = pv2.deserialize(blob)
    data = pv2.parts_to_data(meta, arrays)
    generation = time.perf_counter() - start
    p, lc = meta["parameters"], data.lc
    times = {}
    for scenario, s in SCENARIOS.items():
        t0 = time.perf_counter()
        flux = alter_last_year(case, p, lc.time, lc.year, lc.flux, s)
        raw = LightCurveData(lc.time, flux, lc.flux_err, lc.sector, lc.year)
        model = noiseless_model(case, p, lc.time, lc.year, s)
        records = [
            calibration_measurement(
                raw, data.sectors, year, plan, identity=identity, twin_model=model
            )
            for year in raw.years
        ]
        t1 = time.perf_counter()
        for r_min in R_VALUES:
            outcomes = [
                derive_round(rec, r_min, c.capacity_b, c.capacity_s, min_snr) for rec in records
            ]
            _ = (aggregate(outcomes), any(o["eligible"] for o in outcomes))
        t2 = time.perf_counter()
        times[scenario] = {"rounds": t1 - t0, "aggregation": t2 - t1, "total": t2 - t0}
        del records, outcomes
    return {
        "target": f"{TIMING_PREFIX}/{case['id']}",
        "group": group_of(case),
        "generation_seconds": generation,
        "scenarios": times,
        "pid": os.getpid(),
        "identity_block_sha256": identity["block_sha256"],
        "affinity": pv2.affinity_mask(),
    }


def run_timing_lot(out: Path, workers: int = 6) -> dict:
    """Run the timing lot on 6 spawned workers (the caller's affinity, logical processors 0 to 7,
    is inherited) and write its dated record to ``out`` (never replaced)."""
    import json
    import multiprocessing
    import os
    import statistics
    import subprocess
    import time
    from concurrent.futures import ProcessPoolExecutor
    from datetime import UTC, datetime
    from functools import partial

    if out.exists():
        raise SystemExit(f"{out} exists; not replaced")
    if v3.STATE["problem"] is not None:
        raise SystemExit(f"the M4 configuration is not loaded: {v3.STATE['problem']}")
    problems = timing_configuration_problems(v3.STATE["identity"], v3._plan())
    if problems:
        raise SystemExit("the configuration is not the timing lot's: " + "; ".join(problems))
    if workers != TIMING_WORKERS:
        raise SystemExit(f"the timing lot runs on {TIMING_WORKERS} workers, not {workers}")
    affinity = pv2.affinity_mask()
    if affinity != TIMING_AFFINITY:
        raise SystemExit(f"the affinity is {affinity}, not {TIMING_AFFINITY} (processors 0 to 7)")
    os.environ.update(THREAD_ENV)
    cases = timing_cases()
    head = subprocess.run(
        ["git", "-C", str(v3.CHECKOUT_ROOT), "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "-C", str(v3.CHECKOUT_ROOT), "status", "--porcelain", "--untracked-files=no"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    if dirty:
        raise SystemExit("the checkout has uncommitted changes: the record names a commit")
    started = datetime.now(UTC).isoformat(timespec="seconds")
    wall = time.perf_counter()
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(max_workers=workers, mp_context=ctx) as pool:
        results = list(pool.map(partial(time_target, expected=v3.STATE["identity"]), cases))
    wall = time.perf_counter() - wall
    expected = calibration_identity()["block_sha256"]
    if any(r["identity_block_sha256"] != expected for r in results):
        raise SystemExit("a worker measured another corrections block")
    worker_affinities = sorted({str(r["affinity"]) for r in results})
    if worker_affinities != [TIMING_AFFINITY]:
        raise SystemExit(f"a worker ran with another affinity: {worker_affinities}")
    summary: dict = {}
    for group in sorted({r["group"] for r in results}):
        rows = [r for r in results if r["group"] == group]
        entry = {
            "targets": len(rows),
            "generation": {
                "median": statistics.median(r["generation_seconds"] for r in rows),
                "max": max(r["generation_seconds"] for r in rows),
            },
        }
        for scenario in SCENARIOS:
            values = [r["scenarios"][scenario]["total"] for r in rows]
            entry[scenario] = {"median": statistics.median(values), "max": max(values)}
        summary[group] = entry
    ident = v3.STATE["identity"]
    record = {
        "format": "refute-v0.2.1-rmin-timing/1",
        "note": "times only (map Amendment 26, 6): no outcome, pull, rate or count is recorded",
        "started_utc": started,
        "code_commit": head,
        "configuration": {k: ident[k] for k in ("name", "path", "sha256", "block_sha256")},
        "workers": workers,
        "affinity": affinity,
        "worker_affinities": worker_affinities,
        "thread_env": THREAD_ENV,
        "wall_seconds": wall,
        "targets": len(results),
        "light_curves": len(results) * len(SCENARIOS),
        "per_target": [{k: v for k, v in r.items() if k != "pid"} for r in results],
        "summary": summary,
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8", newline="\n")
    return record


# --- the lots of bs-choice and of the study (Amendments 19, 26 and 27) ------------------------

BS_CHOICE_PREFIX = "refute-v0.2.1-bs-choice"
STUDY_PREFIX = "refute-v0.2.1-rmin-study"
# Amendment 26, reading 1 (approved on 2026-10-19): each group takes its cases of each prefix
# whole, in order of k, until 6400: 16 prefixes of 400 without variability, 64 of 100 with.
STUDY_PREFIXES = {"no variability": 16, "variability": 64}
STUDY_CONFIGURATION = {
    "name": "M4-rmin-study",
    "path": "docs/validation/v0.2.1/population/m4-configurations/rmin-study.json",
}
STUDY_SETTINGS = {"r_min": 8, "capacity_b": 0.0, "capacity_s": 0.0}


def _planets(prefix: str) -> list[dict]:
    return [
        c
        for c in pv2.population_cases("confirm:" + prefix)
        if c["class"] == "planet" and c["band"] in ("near", "measurable")
    ]


def bs_choice_cases() -> list[dict]:
    """Amendment 9: the planets of the bands near and measurable, every tenth index."""
    return [c for c in _planets(BS_CHOICE_PREFIX) if c["index"] % 10 == 0]


def study_cases() -> list[tuple[str, dict]]:
    """``(prefix, case)`` of the study, every group in whole blocks of its prefixes in order."""
    out = []
    for k in range(1, max(STUDY_PREFIXES.values()) + 1):
        prefix = f"{STUDY_PREFIX}-{k}"
        for case in _planets(prefix):
            kind = group_of(case).split(", ")[1]
            if k <= STUDY_PREFIXES[kind]:
                out.append((prefix, case))
    return out


def _lot(lot: str) -> tuple[list[tuple[str, dict]], tuple[str, ...]]:
    if lot == "bs-choice":
        return [(BS_CHOICE_PREFIX, c) for c in bs_choice_cases()], ("constant",)
    if lot == "study":
        return study_cases(), tuple(SCENARIOS)
    raise ValueError(f"unknown lot {lot!r}")


def lot_manifest(lot: str) -> list[tuple[str, str]]:
    """The expected ``(target, scenario)`` pairs of a lot (Amendment 27, 3)."""
    targets, scenarios = _lot(lot)
    return [(f"{prefix}/{case['id']}", sc) for prefix, case in targets for sc in scenarios]


def study_configuration_problems(identity: dict | None, plan) -> list[str]:
    """Why the loaded configuration is not the study's and bs-choice's (Amendment 27, 2)."""
    if identity is None:
        return ["no configuration identity"]
    problems = [
        f"{key} {identity.get(key)!r} is not {value!r}"
        for key, value in STUDY_CONFIGURATION.items()
        if identity.get(key) != value
    ]
    c = plan.gauntlet.corrections
    problems += [
        f"{key} {getattr(c, key)!r} is not {value!r}"
        for key, value in STUDY_SETTINGS.items()
        if getattr(c, key) != value
    ]
    return problems


def record_target(case: dict, prefix: str, scenarios, expected: dict | None) -> list[dict]:
    """One record per scenario of a target: the measurement's records, one per observing year of
    the light curve's metadata, with the scenario's twin (Amendment 27, 3). Refuses another
    configuration than the study's, and a worker whose identity is not the main process's."""
    from refute.packs.tess.holdout import calibration_measurement
    from refute.packs.tess.types import LightCurveData

    if v3.STATE["problem"] is not None:
        raise RuntimeError(f"the M4 configuration is not loaded: {v3.STATE['problem']}")
    plan = v3._plan()
    problems = study_configuration_problems(v3.STATE["identity"], plan)
    if problems:
        raise RuntimeError("the configuration is not the study's: " + "; ".join(problems))
    if expected is None or v3.STATE["identity"] != expected:
        raise RuntimeError("this worker's configuration has another identity than the main one")
    identity = calibration_identity()
    blob, _ = pv2.build_case(case)
    meta, arrays = pv2.deserialize(blob)
    data = pv2.parts_to_data(meta, arrays)
    p, lc = meta["parameters"], data.lc
    years = sorted({int(s.year) for s in data.sectors})
    out = []
    for scenario in scenarios:
        s = SCENARIOS[scenario]
        flux = alter_last_year(case, p, lc.time, lc.year, lc.flux, s)
        raw = LightCurveData(lc.time, flux, lc.flux_err, lc.sector, lc.year)
        model = noiseless_model(case, p, lc.time, lc.year, s)
        rounds = [
            calibration_measurement(raw, data.sectors, y, plan, identity=identity, twin_model=model)
            for y in years
        ]
        out.append(
            {
                "target": f"{prefix}/{case['id']}",
                "group": group_of(case),
                "scenario": scenario,
                "years": years,
                "configuration": v3.STATE["identity"],
                "rounds": rounds,
            }
        )
    return out


def record_path(run_dir: Path, target: str, scenario: str) -> Path:
    prefix, case_id = target.split("/", 1)
    return Path(run_dir) / "records" / prefix / f"{case_id}.{scenario}.json"


def write_record(run_dir: Path, record: dict) -> Path:
    """Write one record file; an existing file is never replaced (``FileExistsError``)."""
    from refute.core.io import dumps_json, to_jsonable

    path = record_path(run_dir, record["target"], record["scenario"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(dumps_json(to_jsonable(record)))
    return path


def _record_task(task: tuple[str, dict, tuple[str, ...], dict]) -> list[dict]:
    prefix, case, scenarios, expected = task
    return record_target(case, prefix, scenarios, expected)


LOT_FORMAT = "refute-v0.2.1-rmin-lot/1"


def _canonical(obj):
    """The value as JSON reads it back (tuples become lists), for comparisons with a file."""
    import json

    return json.loads(json.dumps(obj))


def manifest_payload(lot: str, configuration: dict) -> dict:
    return _canonical(
        {
            "format": LOT_FORMAT,
            "lot": lot,
            "configuration": configuration,
            "expected": lot_manifest(lot),
        }
    )


class _InlineExecutor:
    """Runs the tasks in this process (tests only)."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def submit(self, fn, *args):
        from concurrent.futures import Future

        fut = Future()
        try:
            fut.set_result(fn(*args))
        except Exception as exc:  # noqa: BLE001 - delivered to the caller as the pool would
            fut.set_exception(exc)
        return fut


def _spawn_pool(workers: int):
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor

    return ProcessPoolExecutor(max_workers=workers, mp_context=multiprocessing.get_context("spawn"))


def run_lot(lot: str, run_dir: Path, workers: int = TIMING_WORKERS, executor=None) -> dict:
    """Generate and record a lot (bs-choice, or the study) on 6 spawned workers on logical
    processors 0 to 7 (Amendment 27, 3). The manifest is written first; targets whose records all
    exist are not run again (a record is never replaced); a failed target is reported, never
    retried here; the run ends with the lot's integrity check and a dated run report (never
    replaced). Resuming an interrupted lot is a rerun: its approval is recorded first
    (CLAUDE.md)."""
    import json
    import os
    from concurrent.futures import as_completed
    from datetime import UTC, datetime

    if v3.STATE["problem"] is not None:
        raise SystemExit(f"the M4 configuration is not loaded: {v3.STATE['problem']}")
    problems = study_configuration_problems(v3.STATE["identity"], v3._plan())
    if problems:
        raise SystemExit("the configuration is not the study's: " + "; ".join(problems))
    if workers != TIMING_WORKERS:
        raise SystemExit(f"the lots run on {TIMING_WORKERS} workers, not {workers}")
    affinity = pv2.affinity_mask()
    if affinity != TIMING_AFFINITY:
        raise SystemExit(f"the affinity is {affinity}, not {TIMING_AFFINITY} (processors 0 to 7)")
    os.environ.update(THREAD_ENV)
    run_dir = Path(run_dir)
    configuration = v3.STATE["identity"]
    targets, scenarios = _lot(lot)
    payload = manifest_payload(lot, configuration)
    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        if json.loads(manifest_path.read_text(encoding="utf-8")) != payload:
            raise SystemExit("the run folder holds another lot's or configuration's manifest")
    else:
        run_dir.mkdir(parents=True, exist_ok=True)
        with open(manifest_path, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(payload, indent=1) + "\n")
    todo = [
        (prefix, case, scenarios, configuration)
        for prefix, case in targets
        if not all(record_path(run_dir, f"{prefix}/{case['id']}", sc).exists() for sc in scenarios)
    ]
    started = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    failures = []
    pool = _spawn_pool(workers) if executor is None else executor
    with pool:
        futures = {pool.submit(_record_task, task): task for task in todo}
        for fut in as_completed(futures):
            prefix, case = futures[fut][0], futures[fut][1]
            try:
                records = fut.result()
            except Exception as exc:  # noqa: BLE001 - every failure is reported, none retried
                failures.append({"target": f"{prefix}/{case['id']}", "error": repr(exc)})
                continue
            for rec in records:
                if not record_path(run_dir, rec["target"], rec["scenario"]).exists():
                    write_record(run_dir, rec)
    integrity = lot_problems(run_dir, lot, configuration)
    report = {
        "lot": lot,
        "run": str(run_dir),
        "started_utc": started,
        "dispatched": len(todo),
        "failures": failures,
        "integrity_problems": integrity,
        "complete": not failures and not integrity,
    }
    with open(run_dir / f"run-report-{started}.json", "x", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(report, indent=1) + "\n")
    return report


def load_lot(run_dir: Path) -> dict:
    """The manifest, the records and the SHA-256 of every record file of a run folder."""
    import hashlib
    import json

    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    files = sorted((run_dir / "records").rglob("*.json")) if (run_dir / "records").exists() else []
    records, digests = [], {}
    for p in files:
        data = p.read_bytes()
        digests[p.relative_to(run_dir).as_posix()] = hashlib.sha256(data).hexdigest()
        records.append(json.loads(data.decode("utf-8")))
    return {"manifest": manifest, "records": records, "files": digests}


def lot_problems(run_dir: Path, lot: str, configuration: dict, loaded: dict | None = None) -> list:
    """The integrity of a lot (Amendment 27, 1 and 3): the manifest's format, lot and
    configuration; every record's configuration that of the manifest; the completeness."""
    import rmin_evaluate as ev

    data = load_lot(run_dir) if loaded is None else loaded
    manifest = data["manifest"]
    problems = []
    if manifest.get("format") != LOT_FORMAT:
        problems.append(f"manifest format {manifest.get('format')!r}")
    if manifest.get("lot") != lot:
        problems.append(f"the manifest's lot is {manifest.get('lot')!r}, not {lot!r}")
    if _canonical(manifest.get("configuration")) != _canonical(configuration):
        problems.append("the manifest names another configuration")
    for rec in data["records"]:
        if _canonical(rec.get("configuration")) != _canonical(manifest.get("configuration")):
            problems.append(f"{rec.get('target')} {rec.get('scenario')}: another configuration")
    expected = [tuple(m) for m in manifest.get("expected", [])]
    problems += ev.completeness_problems(expected, data["records"])
    return problems


def _source(lot: str, data: dict) -> dict:
    import hashlib
    import json

    manifest_bytes = json.dumps(data["manifest"], sort_keys=True).encode("utf-8")
    files = json.dumps(data["files"], sort_keys=True).encode("utf-8")
    return {
        "lot": lot,
        "configuration": data["manifest"].get("configuration"),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "records_sha256": hashlib.sha256(files).hexdigest(),
        "records": len(data["files"]),
    }


def evaluate_bs_choice(run_dir: Path, min_snr: float, configuration: dict) -> dict:
    """``k`` and the pairs ``b_R``, ``s_R`` from the records of ``bs-choice`` (Amendment 27, 4 and
    5), with their source; an incomplete or foreign lot is not evaluated, an empty set of a ``k``
    stops the study."""
    import rmin_evaluate as ev

    data = load_lot(run_dir)
    problems = lot_problems(run_dir, "bs-choice", configuration, data)
    source = _source("bs-choice", data)
    if problems:
        return {"complete": False, "problems": problems, "source": source}
    try:
        k = ev.choose_k(data["records"], min_snr)
    except ev.StudyStoppedError as exc:
        return {"complete": True, "stopped": str(exc), "source": source}
    pairs = {str(r): ev.pair_for_r(data["records"], k["k"], r, min_snr) for r in ev.R_VALUES}
    return {"complete": True, "k": k, "pairs": pairs, "min_snr": min_snr, "source": source}


def evaluate_study(run_dir: Path, bs: dict, min_snr: float, configuration: dict) -> dict:
    """Criteria 1 to 5 per ``R`` and group with the pairs of ``bs-choice`` and the choice (Amendment
    27, 6 to 10). The pairs must come from a complete bs-choice of the same configuration and
    ``min_snr``; an incomplete or foreign study lot is not evaluated."""
    import rmin_evaluate as ev

    src = bs.get("source") or {}
    refusals = []
    if src.get("lot") != "bs-choice" or not bs.get("complete") or "pairs" not in bs:
        refusals.append("the pairs do not come from a complete evaluation of bs-choice")
    if _canonical(src.get("configuration")) != _canonical(configuration):
        refusals.append("the pairs come from another configuration")
    if bs.get("min_snr") != min_snr:
        refusals.append("the pairs were computed with another min_snr")
    data = load_lot(run_dir)
    source = _source("study", data)
    if refusals:
        return {"complete": False, "problems": refusals, "source": source}
    problems = lot_problems(run_dir, "study", configuration, data)
    if problems:
        return {"complete": False, "problems": problems, "source": source}
    pairs = bs["pairs"]
    results = {
        r: (
            None
            if pairs[str(r)] is None
            else ev.criteria(data["records"], r, pairs[str(r)], min_snr)
        )
        for r in ev.R_VALUES
    }
    return {
        "complete": True,
        "results": {str(r): v for r, v in results.items()},
        "chosen_r_min": ev.choose_r_min(results),
        "source": source,
        "pairs_source": src,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    t = sub.add_parser("timing", help="run the study's timing lot (Amendment 26, 6)")
    t.add_argument("--out", required=True)
    t.add_argument("--workers", type=int, default=6)
    lo = sub.add_parser("lot", help="generate and record bs-choice or the study (Amendment 27)")
    lo.add_argument("--lot", choices=("bs-choice", "study"), required=True)
    lo.add_argument("--run", required=True)
    lo.add_argument("--workers", type=int, default=6)
    eb = sub.add_parser("evaluate-bs-choice", help="k and the pairs from bs-choice")
    eb.add_argument("--run", required=True)
    eb.add_argument("--out", required=True)
    es = sub.add_parser("evaluate-study", help="the criteria and the choice of R_min")
    es.add_argument("--run", required=True)
    es.add_argument("--pairs", required=True, help="the output of evaluate-bs-choice")
    es.add_argument("--out", required=True)
    args = parser.parse_args()
    if args.mode == "timing":
        run_timing_lot(Path(args.out), args.workers)
    elif args.mode == "lot":
        print(run_lot(args.lot, Path(args.run), args.workers))
    else:
        import json

        from refute.core.io import dumps_json, to_jsonable

        out = Path(args.out)
        if out.exists():
            raise SystemExit(f"{out} exists; not replaced")
        if v3.STATE["problem"] is not None:
            raise SystemExit(f"the M4 configuration is not loaded: {v3.STATE['problem']}")
        plan = v3._plan()
        problems = study_configuration_problems(v3.STATE["identity"], plan)
        if problems:
            raise SystemExit("the configuration is not the study's: " + "; ".join(problems))
        min_snr = plan.gauntlet.holdout_by_year.min_snr
        configuration = v3.STATE["identity"]
        if args.mode == "evaluate-bs-choice":
            result = evaluate_bs_choice(Path(args.run), min_snr, configuration)
        else:
            bs = json.loads(Path(args.pairs).read_text(encoding="utf-8"))
            result = evaluate_study(Path(args.run), bs, min_snr, configuration)
        out.parent.mkdir(parents=True, exist_ok=True)
        with open(out, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(dumps_json(to_jsonable(result)))
