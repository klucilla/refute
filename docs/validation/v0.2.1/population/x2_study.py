"""X2 (docs/validation/v0.2.1/reopen/stage-1/x2-declaration.md): its cases, seeds, noise
realizations, records and resumable lot runner. Nothing here runs a lot by itself; the lot runs
only with the maintainer's authorization (x2-execution-package.md).

- ``x2_cases``: per group, the planets of the bands near and measurable of the prefix
  ``refute-v0.2.1-x2-1`` in the order (band near then measurable, index), every ``n // 20``-th, the
  first 20 (80 cases);
- ``realization_seed``: the first 8 bytes (big-endian) of the SHA-256 of
  ``refute/v0.2.1/stage-1/X2/<group>/<case id>/<j>``;
- ``realization``: the case as ``population_v2.build_case`` makes it (its parameters, sampling,
  model and auxiliary data), its noise drawn again, sector by sector in time order exactly as
  ``build_case`` draws it, from the realization's seed (``population_v2.py`` is frozen and is not
  edited); with the case's own noise seed it is the case byte for byte (tested);
- ``record_realization``: every round by ``calibration_measurement`` (the capacity decisions
  recorded, not enforced) on the study's M4 configuration, with the noiseless twin; the evaluator's
  truth made before the engine calls and attached after them (``rmin_study.EvaluatorTruth``);
- ``run_x2_lot``: the lot, resumable: a manifest first; a task whose record exists is not run
  again; each record is written to a temporary file and linked to its name, so a record file is
  complete or absent and is never replaced; an interrupted lot relaunched gives the same record
  bytes as a continuous run (tested, and checked on the real configuration before the lot).
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rmin_study as rs  # noqa: E402

v3, pv2 = rs.v3, rs.pv2

PREFIX = "refute-v0.2.1-x2-1"
N_CASES = 20
N_REALIZATIONS = 100
GROUPS = (
    "white, no variability",
    "white, variability",
    "AR(1), no variability",
    "AR(1), variability",
)
BAND_ORDER = ("near", "measurable")
SEED_ROOT = "refute/v0.2.1/stage-1/X2"
RECORD_FORMAT = "refute-v0.2.1-x2-record/1"
LOT_FORMAT = "refute-v0.2.1-x2-lot/1"
LOT_AFFINITY = "0xffffff00"  # logical processors 8 to 31


@dataclass(frozen=True)
class LotSpec:
    """A lot of this module: X2 itself (the default, unchanged), its extension X2e
    (stage-1/x2e-declaration.md), or a sub-lot of spec C's choice lot X2f
    (stage-1/after-x2e/x2f-declaration.md): the prefix, the groups, the cases per
    group, the realizations, the seeds' root (X2e's and X2f's seeds also carry the prefix, since
    case ids repeat across prefixes), the record's and the lot's formats; and, for X2f, the regime
    ``selection``: ``(group, mechanisms, cases)`` entries that replace ``n_cases`` per group."""

    name: str
    prefix: str
    groups: tuple[str, ...]
    n_cases: int
    n_realizations: int
    seed_root: str
    seed_with_prefix: bool
    record_format: str
    lot_format: str
    selection: tuple[tuple[str, tuple[str, ...], int], ...] = ()


X2 = LotSpec(
    "x2", PREFIX, GROUPS, N_CASES, N_REALIZATIONS, SEED_ROOT, False, RECORD_FORMAT, LOT_FORMAT
)
X2E = LotSpec(
    "x2e",
    "refute-v0.2.1-x2-2",
    ("white, no variability", "AR(1), no variability"),
    20,
    100,
    "refute/v0.2.1/stage-1/X2e",
    True,
    "refute-v0.2.1-x2e-record/1",
    "refute-v0.2.1-x2e-lot/1",
)
X2F_PREFIX = "refute-v0.2.1-x2-3"


def _x2f(part: str, groups: tuple[str, ...], selection: tuple) -> LotSpec:
    return LotSpec(
        f"x2f-{part}",
        X2F_PREFIX,
        groups,
        0,  # the selection gives the cases
        100,
        "refute/v0.2.1/stage-1/X2f",
        True,
        f"refute-v0.2.1-x2f-{part}-record/1",
        f"refute-v0.2.1-x2f-{part}-lot/1",
        selection,
    )


NO_VARIABILITY = ("white, no variability", "AR(1), no variability")
VARIABILITY = ("white, variability", "AR(1), variability")
# the sizes of stage-1/after-x2e/x2f-declaration.md (its sizing rule, scripts/sizing_a.py)
X2F_S1 = _x2f("s1", NO_VARIABILITY, tuple((g, ("three_years",), 47) for g in NO_VARIABILITY))
X2F_S2 = _x2f("s2", VARIABILITY, tuple((g, ("variability_some_years",), 45) for g in VARIABILITY))
# X2f is S1 + S2 (plan B, section 6; the declaration's revision of 2026-10-26): S3 removed
X2F_SEQUENCE = ("x2f-s1", "x2f-s2")  # the order fixed before any result
LOTS = {s.name: s for s in (X2, X2E, X2F_S1, X2F_S2)}


def _every_kth(rows: list[dict], n: int, what: str) -> list[dict]:
    """X2's rule: in (band, index) order, every ``len // n``-th row, the first ``n``."""
    rows = sorted(rows, key=lambda c: (BAND_ORDER.index(c["band"]), c["index"]))
    step = max(1, len(rows) // n)
    chosen = rows[::step][:n]
    if len(chosen) != n:
        raise ValueError(f"{what}: {len(chosen)} cases, not {n}")
    return chosen


def x2_cases(spec: LotSpec = X2) -> list[dict]:
    """The lot's cases, ``n_cases`` per group, in group order then (band, index) order (X2: 80); for
    a lot with a regime ``selection``, each entry's cases among its group's planets of its
    mechanisms, by the same rule, in the selection's order."""
    planets = rs._planets(spec.prefix)
    if spec.selection:
        parts = [
            _every_kth(
                [c for c in planets if rs.group_of(c) == g and c["mechanism"] in mechanisms],
                n,
                f"{g} {mechanisms}",
            )
            for g, mechanisms, n in spec.selection
        ]
    else:
        parts = [
            _every_kth([c for c in planets if rs.group_of(c) == g], spec.n_cases, g)
            for g in spec.groups
        ]
    out = []
    for chosen in parts:
        for c in chosen:
            rs._check(c)
        out += chosen
    return out


def realization_seed(group: str, case_id: str, j: int, spec: LotSpec = X2) -> int:
    middle = f"{spec.prefix}/{group}" if spec.seed_with_prefix else group
    digest = hashlib.sha256(f"{spec.seed_root}/{middle}/{case_id}/{int(j)}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def case_noise_seed(meta: dict) -> int:
    """The seed ``build_case`` used for the case's own noise."""
    return pv2.sub_seed(int(meta["attempt_seed"]), "noise")


def realization(case: dict, noise_seed: int):
    """``(data, parameters, model, meta)``: the case's data with the flux ``model + noise``, the
    noise drawn from ``noise_seed`` as ``build_case`` draws it; the twin's model is ``model``."""
    from dataclasses import replace

    from refute.packs.tess.types import LightCurveData

    blob, _ = pv2.build_case(case)
    meta, arrays = pv2.deserialize(blob)
    data = pv2.parts_to_data(meta, arrays)
    p, lc = meta["parameters"], data.lc
    model = rs.noiseless_model(case, p, lc.time, lc.year, 1.0)
    rng = np.random.default_rng(int(noise_seed))
    noise = np.empty(len(lc))
    for info in sorted(data.sectors, key=lambda s: s.t_start):  # build_case's order: time
        sel = lc.sector == info.sector
        noise[sel] = pv2._noise(rng, lc.time[sel], case["noise"])
    raw = LightCurveData(lc.time, model + noise, lc.flux_err, lc.sector, lc.year)
    return replace(data, lc=raw), p, model, meta


def record_realization(case: dict, j: int, expected: dict | None, spec: LotSpec = X2) -> dict:
    """One realization's record (the declaration, section 4)."""
    from refute.packs.tess.holdout import calibration_measurement

    if v3.STATE["problem"] is not None:
        raise RuntimeError(f"the M4 configuration is not loaded: {v3.STATE['problem']}")
    plan = v3._plan()
    problems = rs.study_configuration_problems(v3.STATE["identity"], plan)
    if problems:
        raise RuntimeError("the configuration is not the study's: " + "; ".join(problems))
    if expected is None or v3.STATE["identity"] != expected:
        raise RuntimeError("this worker's configuration has another identity than the main one")
    group = rs.group_of(case)
    seed = realization_seed(group, case["id"], j, spec)
    data, p, model, _ = realization(case, seed)
    years = sorted({int(s.year) for s in data.sectors})
    truth = rs.EvaluatorTruth(rs.truth_of(case, p, 1.0))  # made before, read only after the calls
    with rs.engine_call():
        rounds = [
            calibration_measurement(
                data.lc,
                data.sectors,
                y,
                plan,
                identity=rs.calibration_identity(),
                twin_model=model,
            )
            for y in years
        ]
    windows = {
        str(y): registered_windows(data, y, plan, rnd) for y, rnd in zip(years, rounds, strict=True)
    }
    return {
        "format": spec.record_format,
        "target": f"{spec.prefix}/{case['id']}",
        "group": group,
        "case_id": case["id"],
        "mechanism": case["mechanism"],
        "band": case["band"],
        "realization": int(j),
        "noise_seed": str(seed),
        "years": years,
        "sectors": [
            {"sector": int(s.sector), "year": int(s.year), "t_start": s.t_start, "t_end": s.t_end}
            for s in sorted(data.sectors, key=lambda s: s.t_start)
        ],
        "configuration": v3.STATE["identity"],
        "rounds": rounds,
        "registered_windows": windows,
        "truth": {k: truth[k] for k in truth},
    }


def registered_windows(data, year: int, plan, rnd: dict) -> list[dict] | None:
    """The windows the engine registers for ``year``'s round (its transit and control windows and
    their replicas: the hidden year's masks, bands and boxes), recomputed on the evaluator's side
    after the engine's calls with the engine's own functions from the train data and the hidden
    sectors' spans only (no truth, no hidden datum). The round's recorded train ephemeris must be
    the recomputed one exactly (else the record is refused). ``None`` when the round stops before
    its windows exist."""
    from refute.packs.tess.holdout import plan_round, register_replicas

    spans = [(s.t_start, s.t_end) for s in data.sectors if s.year == year]
    prepared = plan_round(data.lc.select(data.lc.year != year), spans, year, plan)
    if prepared.decided is not None or prepared.ephemeris is None:
        return None
    if prepared.diagnostics.get("train_ephemeris") != rnd.get("train_ephemeris"):
        raise RuntimeError(f"{year}: the recomputed train ephemeris is not the round's")
    replicas = register_replicas(prepared.ephemeris, prepared.windows, spans)
    return [
        {
            "kind": w.kind,
            "epoch": int(w.epoch),
            "t_pred": float(w.t_pred),
            "half_width": float(w.half_width),
            "baseline_inner": float(w.baseline_inner),
            "baseline_outer": float(w.baseline_outer),
        }
        for w in [*prepared.windows, *replicas]
    ]


# --- the lot ---------------------------------------------------------------------------------

CODE_FILES = (
    "pyproject.toml",
    "uv.lock",
    "docs/validation/v0.2.1/population/x2_study.py",
    "docs/validation/v0.2.1/population/x2_evaluate.py",
    "docs/validation/v0.2.1/population/rmin_study.py",
    "docs/validation/v0.2.1/population/population_v3.py",
    "docs/validation/v0.2.1/population/population_v2.py",
)
REPO = Path(__file__).resolve().parents[4]


def code_digest() -> str:
    """SHA-256 over the engine (``src/refute/**/*.py``), the lock files and the lot's modules: each
    file's repository path and bytes, in path order."""
    files = sorted(
        [p.relative_to(REPO).as_posix() for p in (REPO / "src" / "refute").rglob("*.py")]
        + list(CODE_FILES)
    )
    h = hashlib.sha256()
    for rel in files:
        h.update(rel.encode() + b"\0" + (REPO / rel).read_bytes() + b"\0")
    return h.hexdigest()


def environment() -> dict:
    import platform

    import astropy
    import scipy

    return {
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "astropy": astropy.__version__,
        "machine": platform.machine(),
        "system": platform.system(),
    }


def all_tasks(spec: LotSpec = X2) -> list[tuple[dict, int]]:
    return [(case, j) for case in x2_cases(spec) for j in range(spec.n_realizations)]


def record_path(run_dir: Path, case_id: str, j: int) -> Path:
    return Path(run_dir) / "records" / case_id / f"{int(j):03d}.json"


def record_text(record: dict) -> str:
    from refute.core.io import dumps_json, to_jsonable

    return dumps_json(to_jsonable(record))


def write_record_atomic(path: Path, text: str) -> Path:
    """Write ``text`` to a temporary file beside ``path``, then link it to ``path`` (which fails if
    ``path`` exists: a record is never replaced) and remove the temporary name. A process stopped at
    any point leaves ``path`` complete or absent; a leftover temporary file starts with a dot and
    is never read as a record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with open(tmp, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
        fh.flush()
        os.fsync(fh.fileno())
    try:
        os.link(tmp, path)
    finally:
        tmp.unlink()
    return path


def manifest_payload(
    tasks: list[tuple[dict, int]], configuration: dict, spec: LotSpec = X2
) -> dict:
    """The lot's identity: its tasks, the configuration, the resolved plan's SHA-256, the code's
    digest and the numeric environment; a relaunch with any of them changed is refused. X2's payload
    is unchanged; another lot names itself (``lot``)."""
    from refute.core.canonical import canonical_sha256

    payload = {
        "format": spec.lot_format,
        "configuration": configuration,
        "plan_sha256": canonical_sha256(v3._plan().model_dump(mode="json")),
        "code_sha256": code_digest(),
        "environment": environment(),
        "expected": [
            [c["id"], int(j), str(realization_seed(rs.group_of(c), c["id"], j, spec))]
            for c, j in tasks
        ],
    }
    if spec is not X2:
        payload = {"lot": spec.name, **payload}
    return rs._canonical(payload)


def spec_of(manifest: dict) -> LotSpec:
    """The lot a manifest is of (X2's manifest names none)."""
    return LOTS[manifest.get("lot", "x2")]


def _x2_task(task: tuple) -> dict:
    case, j, expected = task[:3]
    spec = LOTS[task[3]] if len(task) > 3 else X2
    return record_realization(case, j, expected, spec)


def load_x2_lot(run_dir: Path) -> dict:
    """The manifest, the records and the SHA-256 of every record file; leftover temporary files
    are listed, never read."""
    run_dir = Path(run_dir)
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    root = run_dir / "records"
    files = (
        sorted(p for p in root.rglob("*.json") if not p.name.startswith("."))
        if root.exists()
        else []
    )
    records, digests = [], {}
    for path in files:
        data = path.read_bytes()
        digests[path.relative_to(run_dir).as_posix()] = hashlib.sha256(data).hexdigest()
        records.append(json.loads(data))
    leftovers = (
        sorted(p.relative_to(run_dir).as_posix() for p in root.rglob(".*.tmp"))
        if root.exists()
        else []
    )
    return {"manifest": manifest, "records": records, "files": digests, "leftovers": leftovers}


TRUTH_FIELDS = (*rs.TRUTH_KEYS, "s")


def _round_fields() -> tuple[str, ...]:
    """The keys every calibration record has, whatever its stopping point (holdout.py)."""
    from refute.packs.tess.holdout import INSTRUMENT_FIELDS, _empty_derivation_fields

    base = (
        "calibration_only",
        "hidden_year",
        "decision_1",
        "decision_2",
        "s_pred_1",
        "s_pred_2",
        "s_meas",
        "reason",
        "d_twin",
        "twin_status",
        "capacity_b",
        "capacity_s",
        "configuration",
    )
    return tuple(sorted({*base, *_empty_derivation_fields(), *INSTRUMENT_FIELDS}))


ROUND_FIELDS = _round_fields()


def expected_sectors(case: dict) -> list[dict]:
    """The case's sectors as the harness lays them out (number, year, start, end), in time order."""
    from refute.packs.tess import synthetic
    from refute.packs.tess.types import btjd_to_year

    out = [
        {
            "sector": int(n),
            "year": int(btjd_to_year(float(t.min()))),
            "t_start": float(t.min()),
            "t_end": float(t.max()),
        }
        for n, t in pv2._sector_cadences(synthetic, pv2._layout(case["mechanism"], case["extra"]))
    ]
    return sorted(out, key=lambda s: s["t_start"])


def record_problems(
    rec, case: dict, j: int, seed: str, configuration: dict, spec: LotSpec = X2
) -> list[str]:
    """Why a record file (at the path of ``case``, ``j``) is not a complete record of that task: its
    format, its task and seed, the configuration, its sectors (exactly the case's layout) and years,
    one round per year with every calibration record field, one entry of registered windows per
    year, and its truth."""
    case_id = case["id"]
    key = f"{case_id}/{int(j):03d}"
    if not isinstance(rec, dict):
        return [f"{key}: not a record"]
    out = []
    if rec.get("format") != spec.record_format:
        out.append(f"{key}: format {rec.get('format')!r}")
    if spec is not X2 and rec.get("target") != f"{spec.prefix}/{case_id}":
        out.append(f"{key}: target {rec.get('target')!r}")  # exact, absent included
    if rec.get("case_id") != case_id or rec.get("realization") != int(j):
        out.append(f"{key}: names {rec.get('case_id')}/{rec.get('realization')}")
    for field, value in (
        ("group", rs.group_of(case)),
        ("mechanism", case["mechanism"]),
        ("band", case["band"]),
    ):
        if rec.get(field) != value:  # the evaluator groups by these (Codex's review)
            out.append(f"{key}: {field} {rec.get(field)!r} is not the case's {value!r}")
    if rec.get("noise_seed") != seed:
        out.append(f"{key}: seed {rec.get('noise_seed')} is not {seed}")
    if rec.get("configuration") != configuration:
        out.append(f"{key}: another configuration")
    layout = expected_sectors(case)
    if rec.get("sectors") != layout:
        out.append(f"{key}: sectors are not the case's layout")
    years = rec.get("years")
    layout_years = sorted({s["year"] for s in layout})
    if years != layout_years:
        out.append(f"{key}: years {years} are not the layout's {layout_years}")
    rounds = rec.get("rounds")
    hidden = (
        sorted(r.get("hidden_year") for r in rounds if isinstance(r, dict))
        if isinstance(rounds, list)
        else None
    )
    if hidden != layout_years or len(rounds or []) != len(layout_years):
        out.append(f"{key}: rounds {hidden} for years {layout_years}")
    for r in rounds if isinstance(rounds, list) else []:
        missing = [k for k in ROUND_FIELDS if not isinstance(r, dict) or k not in r]
        if missing:
            out.append(f"{key}: a round lacks {missing[:4]}")
            break
    years = layout_years
    windows = rec.get("registered_windows")
    if not isinstance(windows, dict) or sorted(windows) != sorted(str(y) for y in years or []):
        out.append(f"{key}: registered windows not one entry per year")
    truth = rec.get("truth")
    if not isinstance(truth, dict) or set(truth) != set(TRUTH_FIELDS):
        out.append(f"{key}: truth {sorted(truth) if isinstance(truth, dict) else truth}")
    return out


def x2_lot_problems(run_dir: Path, full: bool = False) -> list[str]:
    """Every expected task has exactly one record file, at its own path, complete
    (``record_problems``); no record file outside the manifest's tasks. With ``full`` (the
    evaluation's check), the manifest's tasks must also be exactly the declared lot's, each once:
    a diagnostic subset is not a lot."""
    run_dir = Path(run_dir)
    data = load_x2_lot(run_dir)
    manifest = data["manifest"]
    spec = spec_of(manifest)
    expected = {(c, int(j)): s for c, j, s in manifest["expected"]}
    cases = {c["id"]: c for c in x2_cases(spec)}
    canonical = {f"records/{c}/{j:03d}.json" for c, j in expected}
    problems = [
        f"{rel}: a record file not at a task's own path"
        for rel in data["files"]
        if rel not in canonical
    ]
    if full:
        declared = sorted(
            [c["id"], int(j), str(realization_seed(rs.group_of(c), c["id"], j, spec))]
            for c, j in all_tasks(spec)
        )
        listed = sorted([c, int(j), str(s)] for c, j, s in manifest["expected"])
        if listed != declared:
            problems.append(
                f"the manifest's {len(listed)} tasks are not the declared lot's {len(declared)}"
            )
    for (case_id, j), seed in sorted(expected.items()):
        path = record_path(run_dir, case_id, j)
        if not path.exists():
            problems.append(f"{case_id}/{j:03d}: no record")
            continue
        try:
            rec = json.loads(path.read_bytes())
        except ValueError:
            problems.append(f"{case_id}/{j:03d}: not JSON")
            continue
        if case_id not in cases:
            problems.append(f"{case_id}: not one of the lot's cases")
            continue
        problems += record_problems(rec, cases[case_id], j, seed, manifest["configuration"], spec)
    return problems


def failure_path(run_dir: Path, case_id: str, j: int, started: str) -> Path:
    """The marker of a failed task, written by the run (``started``) in which it failed."""
    return Path(run_dir) / "failed" / case_id / f"{int(j):03d}-{started}.json"


def attempt_path(run_dir: Path, case_id: str, j: int, started: str) -> Path:
    """The marker of a task's submission, written by the run (``started``) right before it."""
    return Path(run_dir) / "attempts" / case_id / f"{int(j):03d}-{started}.json"


def not_submitted_path(run_dir: Path, case_id: str, j: int, started: str) -> Path:
    """The marker of a recorded submission that the ceiling stopped before it ran."""
    return Path(run_dir) / "not-submitted" / case_id / f"{int(j):03d}-{started}.json"


def _finite_hours(value) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    value = float(value)
    return value if math.isfinite(value) and value >= 0.0 else None


def decisions(run_dir: Path) -> tuple[set[str], dict[str, float]]:
    """The maintainer's recorded decisions on a run folder (audit of 2026-10-26, R2 and R3):
    files ``retry-decisions/*.json``, each with a non-empty ``decision`` text, and ``covers``
    (the failure or attempt markers, relative to the run folder, it lets run again) and/or
    ``consumption`` (``{started: hours}``, the reconciled time of an interrupted invocation, a
    finite number of hours, not negative). A file that is not such a decision decides nothing."""
    covered: set[str] = set()
    reconciled: dict[str, float] = {}
    folder = Path(run_dir) / "retry-decisions"
    for path in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        try:
            decision = json.loads(path.read_text(encoding="utf-8"))
        except ValueError:
            continue  # not a decision
        if not isinstance(decision, dict):
            continue
        text = decision.get("decision")
        if not isinstance(text, str) or not text.strip():
            continue
        covers = decision.get("covers")
        if isinstance(covers, list):
            covered |= {str(c) for c in covers}
        consumption = decision.get("consumption")
        if isinstance(consumption, dict):
            for started, hours in consumption.items():
                if _finite_hours(hours) is not None:
                    reconciled[str(started)] = float(hours)
    return covered, reconciled


def _markers(run_dir: Path, kind: str) -> dict[tuple[str, int], dict[str, str]]:
    """``{(case, j): {started: marker path}}`` of ``failed/`` or ``attempts/``."""
    out: dict[tuple[str, int], dict[str, str]] = {}
    root = Path(run_dir) / kind
    for path in sorted(root.rglob("*.json")) if root.exists() else []:
        if path.name.startswith("."):
            continue
        number, _, started = path.stem.partition("-")
        key = (path.parent.name, int(number))
        out.setdefault(key, {})[started] = path.relative_to(run_dir).as_posix()
    return out


def task_states(run_dir: Path) -> tuple[dict[tuple[str, int], str], set[tuple[str, int]]]:
    """For the tasks without a record: ``(blocked, retry)``. A task is blocked (never submitted
    again) when it has a failure marker, or a submission marker with no outcome (its run was
    interrupted before the failure could be recorded), that no decision covers; it is retried
    when every such marker is covered (R2)."""
    covered, _ = decisions(run_dir)
    failed = _markers(run_dir, "failed")
    attempts = _markers(run_dir, "attempts")
    not_submitted = _markers(run_dir, "not-submitted")
    blocked: dict[tuple[str, int], str] = {}
    retry: set[tuple[str, int]] = set()
    for key in set(failed) | set(attempts):
        open_markers = [("failed", m) for m in failed.get(key, {}).values()]
        open_markers += [
            ("outcome unknown", m)
            for started, m in attempts.get(key, {}).items()
            if started not in failed.get(key, {}) and started not in not_submitted.get(key, {})
        ]
        left = [state for state, m in open_markers if m not in covered]
        if left:
            blocked[key] = left[0]
        elif open_markers:
            retry.add(key)
    return blocked, retry


def consumed_hours(run_dir: Path) -> float:
    """The time already used by the lot's earlier invocations (R3): the sum of their consumption
    records (``consumption/<started>.json``, updated at every check, after every task and at the
    end). An invocation that did not close its record (it was interrupted) counts only through a
    recorded decision giving its time; without one, the lot does not run. A time that is not a
    finite, non-negative number of hours is refused."""
    _, reconciled = decisions(run_dir)
    root = Path(run_dir) / "consumption"
    total, open_runs = 0.0, []
    for path in sorted(root.glob("*.json")) if root.exists() else []:
        if path.name.startswith("."):
            continue
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
            hours = _finite_hours(record["elapsed_hours"])
        except (ValueError, KeyError, TypeError):
            hours, record = None, {}
        if hours is None:
            raise SystemExit(f"the consumption record {path.name} is not a finite, positive time")
        started = path.stem
        if record.get("closed") is True:
            total += hours
        elif started in reconciled:
            if reconciled[started] < hours:  # a decision never gives back time already measured
                raise SystemExit(
                    f"the reconciled time of {started} ({reconciled[started]} h) is below the "
                    f"time it recorded ({hours} h)"
                )
            total += reconciled[started]
        else:
            open_runs.append(started)
    if open_runs:
        raise SystemExit(
            f"the invocation(s) {open_runs} did not close their consumption record (interrupted): "
            "record a decision with their time (retry-decisions/, consumption) before a relaunch"
        )
    return total


def _write_consumption(run_dir: Path, started: str, elapsed_hours: float, closed: bool) -> None:
    path = Path(run_dir) / "consumption" / f"{started}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(
        json.dumps({"started_utc": started, "elapsed_hours": elapsed_hours, "closed": closed})
        + "\n",
        encoding="utf-8",
    )
    os.replace(temporary, path)


def run_x2_lot(
    run_dir: Path,
    tasks: list[tuple[dict, int]] | None = None,
    workers: int = 22,
    executor=None,
    deadline_hours: float | None = None,
    clock=None,
    spec: LotSpec = X2,
) -> dict:
    """Generate and record X2's lot, or another of this module's lots (``spec``; or the subset
    ``tasks``), on ``workers`` spawned workers on
    logical processors 8 to 31 (22 as authorized; never read from the environment). The manifest is
    published first (atomically, never replaced) and must match on a relaunch; a task whose record
    exists and is complete is not run again, and an existing incomplete record stops the run (it is
    never replaced). A failed task is recorded at once as a terminal state (``failed/``) and is not
    submitted again on a relaunch, unless a decision recorded in ``retry-decisions/`` names its
    failure (R2). ``deadline_hours`` is the lot's ceiling, counted across its invocations (the
    time of the earlier ones is read from ``consumption/``, R3) and checked right before every
    submission (none after it, those in flight end). A dated run report is written (never
    replaced). Relaunching an interrupted lot resumes it."""
    import time
    from concurrent.futures import FIRST_COMPLETED, wait
    from datetime import UTC, datetime

    if v3.STATE["problem"] is not None:
        raise SystemExit(f"the M4 configuration is not loaded: {v3.STATE['problem']}")
    problems = rs.study_configuration_problems(v3.STATE["identity"], v3._plan())
    if problems:
        raise SystemExit("the configuration is not the study's: " + "; ".join(problems))
    affinity = pv2.affinity_mask()
    if executor is None and affinity != LOT_AFFINITY:
        raise SystemExit(f"the affinity is {affinity}, not {LOT_AFFINITY} (processors 8 to 31)")
    workers = int(workers)
    if workers < 1:
        raise SystemExit(f"workers must be positive, got {workers}")
    os.environ.update(rs.THREAD_ENV)
    run_dir = Path(run_dir)
    configuration = v3.STATE["identity"]
    tasks = all_tasks(spec) if tasks is None else list(tasks)
    payload = manifest_payload(tasks, configuration, spec)
    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        try:
            stored = json.loads(manifest_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise SystemExit(f"the run folder's manifest is not readable: {exc}") from exc
        if stored != payload:
            raise SystemExit(
                "the run folder's manifest is another lot's, configuration's, plan's, code's or "
                "environment's"
            )
    else:
        write_record_atomic(manifest_path, json.dumps(payload, indent=1) + "\n")
    consumed_before = consumed_hours(run_dir)  # the earlier invocations of this lot (R3)
    todo = []
    blocked_keys, retry_keys = task_states(run_dir)
    terminal_failures: list[dict] = []
    retried: list[dict] = []
    for c, j in tasks:
        path = record_path(run_dir, c["id"], j)
        if not path.exists():
            key = (c["id"], int(j))
            if key in blocked_keys:  # terminal without a recorded decision (R2)
                terminal_failures.append(
                    {"case_id": c["id"], "realization": int(j), "state": blocked_keys[key]}
                )
                continue
            if key in retry_keys:
                retried.append({"case_id": c["id"], "realization": int(j)})
            todo.append((c, j, configuration) if spec is X2 else (c, j, configuration, spec.name))
            continue
        seed = str(realization_seed(rs.group_of(c), c["id"], j, spec))
        try:
            existing = json.loads(path.read_bytes())
        except ValueError:
            existing = None
        bad = record_problems(existing, c, j, seed, configuration, spec)
        if bad:
            raise SystemExit("an existing record is incomplete (never replaced): " + "; ".join(bad))
    started = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    failures: list[dict] = []
    dispatch_error = None
    submitted = 0
    clock = time.monotonic if clock is None else clock
    t0 = clock()
    _write_consumption(run_dir, started, 0.0, closed=False)
    deadline_reached = False
    futures: dict = {}

    def collect(done) -> None:
        for fut in done:
            case, j = futures.pop(fut)[:2]
            try:
                record = fut.result()
            except Exception as exc:  # noqa: BLE001 - every failure is reported, none retried
                failure = {"case_id": case["id"], "realization": j, "error": repr(exc)}
                failures.append(failure)
                # recorded at once, as a terminal state (R2)
                write_record_atomic(
                    failure_path(run_dir, case["id"], j, started),
                    json.dumps({**failure, "run_started_utc": started}, indent=1) + "\n",
                )
            else:
                path = record_path(run_dir, case["id"], j)
                if not path.exists():
                    write_record_atomic(path, record_text(record))
            _write_consumption(run_dir, started, (clock() - t0) / 3600.0, closed=False)

    try:
        pool = rs._spawn_pool(workers) if executor is None else executor
        with pool:
            try:
                for task in todo:
                    while len(futures) >= 4 * workers:
                        done, _ = wait(futures, return_when=FIRST_COMPLETED)
                        collect(done)
                    # the submission is recorded first: a run cut short leaves its outcome
                    # unknown, never a task silently free to run again (R2)
                    write_record_atomic(
                        attempt_path(run_dir, task[0]["id"], task[1], started),
                        json.dumps({"run_started_utc": started}) + "\n",
                    )
                    # the ceiling, read last, right before the submission (after any wait and
                    # any write), on the time of the whole lot: the earlier invocations' and
                    # this one's (R3); a task stopped here is recorded as not submitted
                    if deadline_hours is not None:
                        elapsed = (clock() - t0) / 3600.0
                        if consumed_before + elapsed >= deadline_hours:
                            write_record_atomic(
                                not_submitted_path(run_dir, task[0]["id"], task[1], started),
                                json.dumps({"run_started_utc": started}) + "\n",
                            )
                            deadline_reached = True
                            break
                    futures[pool.submit(_x2_task, task)] = task
                    submitted += 1
                    if deadline_hours is not None:
                        _write_consumption(run_dir, started, elapsed, closed=False)
            except Exception as exc:  # noqa: BLE001 - the dispatch stops, reported, not retried
                dispatch_error = f"submission: {exc!r}"
            while futures:
                done, _ = wait(futures, return_when=FIRST_COMPLETED)
                collect(done)
    except Exception as exc:  # noqa: BLE001 - the pool itself failed: reported, not retried
        dispatch_error = (dispatch_error or "") + f" pool: {exc!r}"
    elapsed_hours = (clock() - t0) / 3600.0
    _write_consumption(run_dir, started, elapsed_hours, closed=True)
    integrity = x2_lot_problems(run_dir)
    report = {
        "format": spec.lot_format,
        "run": str(run_dir),
        "started_utc": started,
        "workers": workers,
        "affinity": affinity,
        "tasks": len(tasks),
        "dispatched": len(todo),
        "submitted": submitted,
        "dispatch_error": dispatch_error,
        "deadline_hours": deadline_hours,
        "deadline_reached": deadline_reached,
        "elapsed_hours": elapsed_hours,
        "consumed_before_hours": consumed_before,
        "consumed_total_hours": consumed_before + elapsed_hours,
        "failures": failures,
        "terminal_failures": terminal_failures,
        "retried": retried,
        "leftover_temporary_files": load_x2_lot(run_dir)["leftovers"],
        "integrity_problems": integrity,
        "complete": (
            dispatch_error is None
            and not deadline_reached
            and not failures
            and not terminal_failures
            and not integrity
        ),
    }
    with open(run_dir / f"run-report-{started}.json", "x", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(report, indent=1) + "\n")
    return report


def hidden_times_of(spec: LotSpec = X2):
    """``f(case_id, year)``: the case's cadences in that observing year, from its layout (no noise,
    no flux), for X2-A's overlaps."""
    from refute.packs.tess import synthetic
    from refute.packs.tess.types import btjd_to_year

    cases = {c["id"]: c for c in x2_cases(spec)}
    cache: dict = {}

    def times(case_id: str, year: int) -> np.ndarray:
        if case_id not in cache:
            c = cases[case_id]
            per_year: dict[int, list] = {}
            for _, t in pv2._sector_cadences(synthetic, pv2._layout(c["mechanism"], c["extra"])):
                per_year.setdefault(btjd_to_year(float(t.min())), []).append(t)
            cache[case_id] = {y: np.concatenate(v) for y, v in per_year.items()}
        return cache[case_id].get(int(year), np.empty(0))

    return times


def lot_rows(run_dir: Path) -> tuple[list[dict], dict, object]:
    """``(rows, manifest, plan)``: every round's row (``x2_evaluate.round_rows``) of a complete lot,
    with the very code, plan, configuration and environment the lot was made with (else refused)."""
    import x2_evaluate as ev

    from refute.core.canonical import canonical_sha256

    problems = x2_lot_problems(run_dir, full=True)
    if problems:
        raise SystemExit("the lot is not complete: " + "; ".join(problems[:5]))
    data = load_x2_lot(run_dir)
    manifest = data["manifest"]
    spec = spec_of(manifest)
    plan = v3._plan()
    now = rs._canonical(
        {
            "configuration": v3.STATE["identity"],
            "plan_sha256": canonical_sha256(plan.model_dump(mode="json")),
            "code_sha256": code_digest(),
            "environment": environment(),
        }
    )
    changed = [k for k, v in now.items() if manifest.get(k) != v]
    if changed:
        raise SystemExit(f"the evaluation's {changed} differ from the lot's manifest")
    times = hidden_times_of(spec)
    rows = [
        row
        for rec in data["records"]
        for row in ev.round_rows(rec, times, plan.gauntlet.holdout_by_year.min_snr)
    ]
    return rows, manifest, plan


def evaluate_lot(run_dir: Path) -> dict:
    """X2-A and X2-B on a complete lot, exactly as declared (``x2_evaluate``)."""
    import x2_evaluate as ev

    rows, manifest, plan = lot_rows(run_dir)
    out = ev.evaluate(rows, float(plan.gauntlet.corrections.m_beta))
    return {"manifest_code_sha256": manifest["code_sha256"], "rounds": len(rows), **out}


def pooled_rows(x2_rows: list[dict], x2e_rows: list[dict]) -> list[dict]:
    """X2e's pooled analysis (stage-1/x2e-declaration.md): X2's committed rows of X2e's cells and
    X2e's rows, each case named by its prefix (case ids repeat across prefixes)."""
    out = []
    for prefix, rows in ((X2.prefix, x2_rows), (X2E.prefix, x2e_rows)):
        for r in rows:
            if r["group"] in X2E.groups:
                out.append({**r, "case_id": f"{prefix}/{r['case_id']}"})
    return out


def evaluate_pooled(x2_evaluation: Path, x2e_run_dir: Path) -> dict:
    """X2-A and X2-B on X2e's cells, over X2's committed rows (``x2-evaluation.json``, read as
    stored, never recomputed) and X2e's lot (its own identity checked)."""
    import x2_evaluate as ev

    stored = json.loads(Path(x2_evaluation).read_text(encoding="utf-8"))
    rows_e, manifest, plan = lot_rows(x2e_run_dir)
    if spec_of(manifest) is not X2E:
        raise SystemExit("the run folder is not X2e's lot")
    rows = pooled_rows(stored["rows"], rows_e)
    out = ev.evaluate(rows, float(plan.gauntlet.corrections.m_beta))
    return {
        "x2_evaluation_code_sha256": stored["manifest_code_sha256"],
        "x2e_manifest_code_sha256": manifest["code_sha256"],
        "rounds": len(rows),
        **out,
    }


def subset_tasks(n_cases: int, n_realizations: int, spec: LotSpec = X2) -> list[tuple[dict, int]]:
    """The first ``n_cases`` cases of each group and their first ``n_realizations`` realizations
    (the resumption check before the lot; never the lot)."""
    cases = x2_cases(spec)
    chosen = [c for g in spec.groups for c in [x for x in cases if rs.group_of(x) == g][:n_cases]]
    return [(c, j) for c in chosen for j in range(n_realizations)]


def main(argv: list[str]) -> int:
    """``run <run_dir> --workers <n> [--lot x2|x2e|x2f-s1|x2f-s2|x2f-s3]
    [--subset <cases per group> <realizations>]
    [--deadline-hours <h>]``, ``check <run_dir> [--full]``, ``evaluate <run_dir> <out>`` or
    ``evaluate-pooled <x2-evaluation.json> <x2e run_dir> <out>``."""
    command = argv[0]
    if command == "evaluate-pooled":
        out = Path(argv[3])
        result = evaluate_pooled(Path(argv[1]), Path(argv[2]))
        with open(out, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(rs._canonical(result), indent=1) + "\n")
        print(json.dumps(result["findings"], indent=1))
        return 0
    run_dir = Path(argv[1])
    if command == "check":
        problems = x2_lot_problems(run_dir, full="--full" in argv[2:])
        print(json.dumps({"problems": problems}, indent=1))
        return 1 if problems else 0
    if command == "evaluate":
        out = Path(argv[2])
        result = evaluate_lot(run_dir)
        with open(out, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(rs._canonical(result), indent=1) + "\n")
        print(json.dumps(result["findings"], indent=1))
        return 0
    if command != "run":
        raise SystemExit(f"unknown command {command!r}")
    tasks, deadline, workers, spec, subset = None, None, None, X2, None
    rest = argv[2:]
    while rest:
        if rest[0] == "--lot":
            if rest[1] not in LOTS:
                raise SystemExit(f"unknown lot {rest[1]!r}; the lots are {sorted(LOTS)}")
            spec = LOTS[rest[1]]
            rest = rest[2:]
        elif rest[0] == "--subset":
            subset = (int(rest[1]), int(rest[2]))
            rest = rest[3:]
        elif rest[0] == "--deadline-hours":
            deadline = float(rest[1])
            rest = rest[2:]
        elif rest[0] == "--workers":
            workers = int(rest[1])
            rest = rest[2:]
        else:
            raise SystemExit(f"unknown argument {rest[0]!r}")
    if workers is None:
        raise SystemExit("--workers is required (22 as authorized)")
    if subset is not None:
        tasks = subset_tasks(*subset, spec)
    report = run_x2_lot(run_dir, tasks=tasks, workers=workers, deadline_hours=deadline, spec=spec)
    print(json.dumps({k: report[k] for k in ("tasks", "dispatched", "complete")}))
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
