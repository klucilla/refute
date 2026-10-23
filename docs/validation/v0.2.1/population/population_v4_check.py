"""The acceptance checks of population_v4 (criteria 1 to 4 and 6 to 9).

Acceptance record: ``population-v4-acceptance.md`` next to this file, sections 3 and 4.
Criterion 5 is ``band_check_v4.py`` (independent of this file and of the generator). Every
check reports its coverage; zero coverage is a failure. Nothing here runs the engine.

Modes:

- ``run --generation G --workers N --order index|reverse|interleaved --out-dir DIR``: every
  case of the acceptance population laid out, built in memory, checked (criteria 1, 4, 5, 6),
  hashed and discarded; the population's checks (criteria 2, 3, 4's counts, 8). Writes
  ``population-G.json`` and ``manifest-G.json`` (the per-case SHA-256).
- ``compare --out-dir DIR``: the three manifests byte-identical (criterion 7); writes
  ``determinism.json``.
- ``order --out FILE``: the git history's order (criterion 9).
"""

from __future__ import annotations

import argparse
import ast
import concurrent.futures as cf
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import band_check_v4 as band  # noqa: E402
import population_v4 as v4  # noqa: E402

pv2 = v4.pv2
domain = v4.domain
REPO = HERE.parents[3]
RESIDUAL_BINS = 1000

# The record's declarations (sections 2.2 and 3), held here and never read from the generator,
# so that a change of the generator cannot move what it is checked against.
DT = 120.0 / 86400.0
GENERATOR = "refute-population-v4/1"
PLANET_REGIMES = ("three_years", "variability_some_years")
PLANETS_PER_REGIME = 180
FIRST_START = (1325.0, 1325.0 + 365.25)
SHORT_SEPARATION = (345.0, 385.0)
LONG_SEPARATION = (710.0, 750.0)
ORBIT_DAYS = (12.5, 14.0)
ORBIT_GAP_DAYS = (0.5, 2.0)
MAX_BLOCKS = 4
BLOCK_SECONDS = (600.0, 21600.0)
LOSS_RATE = (0.0, 0.05)
JITTER_S = 0.25
CASE_KEYS = (
    "id", "class", "band", "noise", "index", "mechanism", "catalog_variant", "seed", "extra",
)  # fmt: skip
WORKER_COUNTS_REQUIRED = 3
ORDERS = ("index", "reverse", "interleaved")
REDRAW_REASONS = frozenset(
    {f"layout:D{i}" for i in range(1, 6)}
    | {"band", "depth_limit", "no_transit_in_a_year", "commensurate_periods"}
)

# Criterion 6 (c): what population_v4.py may read from population_v2 and from synthetic.
PV2_ATTRIBUTES = frozenset(
    {
        "draw_parameters", "_place_in_band", "_mechanism_condition", "_noise", "sub_seed",
        "BANDS", "DEPTH_LIMITS", "MAX_ATTEMPTS", "_case", "CATALOG_VARIANTS", "_fp_mechanism",
        "_notransit_mechanism", "TARGET_TIC", "_signal_spec", "TREND_AMPLITUDE",
        "TREND_PERIOD_DAYS", "NOISE_PPM", "_scene", "NEIGHBOR_TIC", "_catalog", "data_to_parts",
        "SERIALIZATION", "serialize", "plain",
    }
)  # fmt: skip
SYNTHETIC_ATTRIBUTES = frozenset(
    {
        "make_star", "signal_model", "scene_aperture", "crowding", "SignalSpec", "render_pixels",
        "PIXEL_SCALE_ARCSEC", "make_sector_aux", "make_aux", "make_data",
    }
)  # fmt: skip
DOMAIN_ATTRIBUTES = frozenset({"check_domain"})
REFUTE_MODULES = frozenset(
    f"refute.packs.tess.{m}" for m in ("synthetic", "params", "types", "domain")
)

RECORD_FILES = ("docs/validation/v0.2.1/population/population-v4-acceptance.md",)
TEST_FILES = ("tests/test_domain.py", "tests/test_population_v4.py")
CODE_FILES = (
    "src/refute/packs/tess/domain.py",
    "docs/validation/v0.2.1/population/population_v4.py",
    "docs/validation/v0.2.1/population/population_v4_check.py",
    "docs/validation/v0.2.1/population/band_check_v4.py",
    "docs/validation/v0.2.1/population/population_v4_sabotage.py",
)
FIRST_RUN = "docs/validation/v0.2.1/population/v4-acceptance/first-run.json"
SABOTAGES = "docs/validation/v0.2.1/population/v4-acceptance/sabotages.json"


# --- criterion 4: the composition, and criterion 3: the allocation -----------------------------


def _expected_composition() -> Counter:
    want: Counter = Counter()
    for noise in ("white", "correlated"):
        for b in ("below", "near", "measurable"):
            for regime in PLANET_REGIMES:
                want[("planet", noise, b, regime)] = PLANETS_PER_REGIME
        for b, n in (("below", 100), ("near", 100), ("measurable", 250)):
            for i in range(n):
                want[("false_positive", noise, b, pv2._fp_mechanism(i, n))] += 1
        n = 2200 if noise == "white" else 600
        for i in range(n):
            want[("no_transit", noise, None, pv2._notransit_mechanism(i, n))] += 1
    return want


def composition_problems(cases: list[dict]) -> list[str]:
    if not cases:
        return ["no case"]
    got = Counter((c["class"], c["noise"], c["band"], c["mechanism"]) for c in cases)
    want = _expected_composition()
    problems = [
        f"{key}: {got.get(key, 0)} cases, {n} declared"
        for key, n in sorted(want.items(), key=str)
        if got.get(key, 0) != n
    ]
    problems += [f"{key}: undeclared group" for key in got if key not in want]
    if len({c["id"] for c in cases}) != len(cases):
        problems.append("duplicate case ids")
    return problems


def _groups(cases: list[dict]) -> dict[tuple, list[dict]]:
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for c in cases:
        groups[(c["class"], c["noise"], c["band"], c["mechanism"])].append(c)
    for rows in groups.values():
        rows.sort(key=lambda c: c["index"])
    return groups


def allocation_problems(cases: list[dict]) -> list[str]:
    """Within each group, the counts of G-a, G-b short-long and G-b long-short equal the declared
    allocation (G-a ceil(n/2), short-long ceil(floor(n/2)/2)), and each case its position's."""
    if not cases:
        return ["no case"]
    problems = []
    for key, rows in _groups(cases).items():
        n = len(rows)
        got = Counter((c["extra"].get("geometry"), c["extra"].get("order")) for c in rows)
        want = Counter({("G-a", None): (n + 1) // 2, ("G-b", "short-long"): (n + 2) // 4})
        want[("G-b", "long-short")] = n // 4
        if +got != +want:
            problems.append(f"{key}: allocation {dict(got)}, declared {dict(+want)}")
        for j, c in enumerate(rows):
            declared = (
                {"geometry": "G-a"}
                if j % 2 == 0
                else {"geometry": "G-b", "order": "short-long" if j % 4 == 1 else "long-short"}
            )
            if c["extra"] != declared:
                problems.append(f"{c['id']}: geometry {c['extra']} at position {j}")
                break
    return problems


# --- criteria 1, 2 and 3 on the layouts ---------------------------------------------------------


def _residual_histogram(times) -> list[int]:
    hist = np.zeros(RESIDUAL_BINS, dtype=np.int64)
    for t in times:
        dt = np.diff(t) * 86400.0
        steps = dt[dt <= domain.INTERNAL_GAP_S]
        residual = steps - np.rint(steps / domain.CADENCE_S) * domain.CADENCE_S
        h, _ = np.histogram(residual, bins=RESIDUAL_BINS, range=(-0.5, 0.5))
        hist += h
    return [int(x) for x in hist]


def layout_record(case: dict, lay: dict) -> dict:
    """The plain summary of a case's accepted layout (criteria 1 to 3)."""
    jitter = np.concatenate(lay["jitter_s"])
    edges = (-JITTER_S + 2 * JITTER_S / 3, -JITTER_S + 4 * JITTER_S / 3)
    return {
        "id": case["id"],
        "class": case["class"],
        "noise": case["noise"],
        "band": case["band"],
        "mechanism": case["mechanism"],
        "geometry": case["extra"]["geometry"],
        "order": case["extra"].get("order"),
        "attempt": lay["attempt"],
        "redraws": dict(lay["redraws"]),
        "draws": json.loads(json.dumps(lay["draws"])),
        "domain": lay["domain"].summary(),
        "jitter": {
            "min": float(jitter.min()),
            "max": float(jitter.max()),
            "thirds": [
                int(np.count_nonzero(jitter < edges[0])),
                int(np.count_nonzero((jitter >= edges[0]) & (jitter < edges[1]))),
                int(np.count_nonzero(jitter >= edges[1])),
            ],
        },
        "residual_histogram": _residual_histogram(lay["times"]),
    }


def domain_problems(records: list[dict]) -> list[str]:
    if not records:
        return ["no case checked by the domain function"]
    return [f"{r['id']}: {r['domain']['reason']}" for r in records if not r["domain"]["inside"]]


def geometry_problems(records: list[dict]) -> list[str]:
    if not records:
        return ["no case"]
    problems = []
    for r in records:
        seps = r["domain"]["separations_days"]
        long_ = [domain.TWO_YEARS_DAYS[0] <= s <= domain.TWO_YEARS_DAYS[1] for s in seps]
        want = (
            [False, False]
            if r["geometry"] == "G-a"
            else [False, True]
            if r["order"] == "short-long"
            else [True, False]
        )
        if long_ != want:
            problems.append(f"{r['id']}: separations {seps} for {r['geometry']} {r['order']}")
    return problems


def _thirds(values, lo: float, hi: float) -> list[int]:
    e1, e2 = lo + (hi - lo) / 3.0, lo + 2.0 * (hi - lo) / 3.0
    v = np.asarray(values, dtype=float)
    return [
        int(np.count_nonzero((v >= lo) & (v < e1))),
        int(np.count_nonzero((v >= e1) & (v < e2))),
        int(np.count_nonzero((v >= e2) & (v <= hi))),
    ]


def _declared(name: str, values, lo: float, hi: float) -> tuple[dict, list[str]]:
    counts = _thirds(values, lo, hi)
    outside = int(np.count_nonzero((np.asarray(values) < lo) | (np.asarray(values) >= hi)))
    out = {"interval": [lo, hi], "thirds": counts, "n": len(values), "outside": outside}
    problems = [f"{name}: thirds {counts} of [{lo}, {hi})"] if min(counts) == 0 else []
    if outside:
        problems.append(f"{name}: {outside} values outside [{lo}, {hi})")
    return out, problems


def _realized(name: str, values) -> tuple[dict, list[str]]:
    if len(values) == 0:
        return {"n": 0}, [f"{name}: nothing realized"]
    lo, hi = float(min(values)), float(max(values))
    if hi <= lo:
        return {"n": len(values), "range": [lo, hi]}, [f"{name}: a single realized value {lo}"]
    counts = _thirds(values, lo, hi)
    out = {"n": len(values), "range": [lo, hi], "thirds": counts}
    return out, ([f"{name}: thirds {counts} of its realized range"] if min(counts) == 0 else [])


def _residual_thirds(hist: np.ndarray) -> tuple[dict, list[str]]:
    """The residuals' thirds of their realized range, counting only the bins wholly inside a
    third (conservative: a boundary bin never makes a third populated)."""
    width = 1.0 / RESIDUAL_BINS
    nonzero = np.flatnonzero(hist)
    if nonzero.size == 0:
        return {"n": 0}, ["residuals: none"]
    lo, hi = -0.5 + nonzero[0] * width, -0.5 + (nonzero[-1] + 1) * width
    e = [lo, lo + (hi - lo) / 3, lo + 2 * (hi - lo) / 3, hi]
    starts = -0.5 + np.arange(RESIDUAL_BINS) * width
    counts = [int(hist[(starts >= e[i]) & (starts + width <= e[i + 1])].sum()) for i in range(3)]
    out = {"range": [lo, hi], "thirds": counts, "n": int(hist.sum())}
    return out, ([f"residuals: thirds {counts}"] if min(counts) == 0 else [])


def coverage_problems(records: list[dict], report: dict | None = None) -> list[str]:
    """Criterion 2, per class and noise model: the declared intervals' thirds, then (apart) the
    realized quantities' thirds."""
    if not records:
        return ["no case"]
    problems = []
    by_group: dict[tuple, list[dict]] = defaultdict(list)
    for r in records:
        by_group[(r["class"], r["noise"])].append(r)
    for (cls, noise), rows in sorted(by_group.items()):
        tag = f"{cls}/{noise}"
        sectors = [s for r in rows for s in r["draws"]["sectors"]]
        blocks = [b for s in sectors for b in s["blocks"]]
        seps = [x for r in rows for x in r["draws"]["separations"]]
        declared = {
            "first_start": ([r["draws"]["first_start"] for r in rows], *FIRST_START),
            "separation_one_year": ([x for x in seps if x < 500.0], *SHORT_SEPARATION),
            "separation_two_years": ([x for x in seps if x >= 500.0], *LONG_SEPARATION),
            "orbit_days": ([x for s in sectors for x in s["orbit_days"]], *ORBIT_DAYS),
            "orbit_gap_days": ([s["orbit_gap_days"] for s in sectors], *ORBIT_GAP_DAYS),
            "block_seconds": ([b["seconds"] for b in blocks], *BLOCK_SECONDS),
            "block_place": ([b["place"] for b in blocks], 0.0, 1.0),
            "loss_rate": ([s["loss_rate"] for s in sectors], *LOSS_RATE),
        }  # fmt: skip
        out: dict = {}
        for name, (values, lo, hi) in declared.items():
            out[name], found = _declared(f"{tag} {name}", values, lo, hi)
            problems += found
        counts = Counter(len(s["blocks"]) for s in sectors)
        out["block_count"] = {str(k): counts.get(k, 0) for k in range(MAX_BLOCKS + 1)}
        if any(counts.get(k, 0) == 0 for k in range(MAX_BLOCKS + 1)):
            problems.append(f"{tag} block_count: values {dict(counts)}, 0 to 4 required")
        jit = [sum(r["jitter"]["thirds"][i] for r in rows) for i in range(3)]
        out["jitter"] = {"thirds": jit, "min": min(r["jitter"]["min"] for r in rows),
                         "max": max(r["jitter"]["max"] for r in rows)}  # fmt: skip
        if min(jit) == 0:
            problems.append(f"{tag} jitter: thirds {jit}")
        if out["jitter"]["min"] < -JITTER_S or out["jitter"]["max"] >= JITTER_S:
            problems.append(f"{tag} jitter outside [-0.25, 0.25)")
        realized_sectors = [s for r in rows for s in r["domain"]["sectors"]]
        realized = {
            f"k{k}_count": [s["k_counts"][str(k)] for s in realized_sectors] for k in range(1, 5)
        }
        realized["orbit_days"] = [x for s in realized_sectors for x in (s["orbit_days"] or [])]
        realized["orbit_gap_days"] = [s["orbit_gap_days"] for s in realized_sectors]
        realized["other_gap_seconds"] = [
            x for s in realized_sectors for x in s["other_gaps_seconds"]
        ]
        realized["other_gap_count"] = [len(s["other_gaps_seconds"]) for s in realized_sectors]
        realized["coverage"] = [s["coverage"] for s in realized_sectors]
        for name, values in realized.items():
            out[f"realized_{name}"], found = _realized(f"{tag} realized {name}", values)
            problems += found
            if name.endswith("_count") and name.startswith("k") and sum(values) == 0:
                problems.append(f"{tag} realized {name}: never realized")
        hist = np.sum([r["residual_histogram"] for r in rows], axis=0)
        out["realized_residuals"], found = _residual_thirds(hist)
        problems += [f"{tag} {p}" for p in found]
        if report is not None:
            report[tag] = out
    return problems


# --- criterion 8: X2f ---------------------------------------------------------------------------


def x2f_report() -> dict:
    from refute.packs.tess import synthetic

    problems: list[str] = []
    out: dict = {}
    for mech in ("three_years", "variability_some_years"):
        times = [t for _, t in pv2._sector_cadences(synthetic, pv2._layout(mech, {}))]
        result = domain.check_domain(times)
        if not result.inside:
            problems.append(f"{mech}: {result.reason}")
        seps = list(result.separations_days)
        if not all(domain.ONE_YEAR_DAYS[0] <= s <= domain.ONE_YEAR_DAYS[1] for s in seps):
            problems.append(f"{mech}: separations {seps} not G-a")
        if not np.allclose(seps, [375.0, 361.0], rtol=0, atol=1e-9):
            problems.append(f"{mech}: separations {seps}, 375 and 361 d expected")
        for s in result.sectors:
            if s.other_gaps_seconds:
                problems.append(f"{mech}: other gaps {s.other_gaps_seconds}")
            if s.orbit_days is None or not np.allclose(s.orbit_days, 13.0, atol=1e-6):
                problems.append(f"{mech}: orbits {s.orbit_days}")
            if s.orbit_gap_days is None or not 1.0 - 1e-9 <= s.orbit_gap_days <= 1.0 + DT + 1e-9:
                problems.append(f"{mech}: orbit gap {s.orbit_gap_days}")
        out = {
            "geometry": "G-a" if len(seps) == 2 and not problems else None,
            "separations_days": seps,
            "coverage": [s.coverage for s in result.sectors],
            "orbit_days": [list(s.orbit_days or ()) for s in result.sectors],
            "orbit_gap_days": [s.orbit_gap_days for s in result.sectors],
            "labels": [s.label for s in result.sectors],
        }
    out["problems"] = problems
    return out


# --- criteria 1, 4 and 6 on a built case --------------------------------------------------------


def _replay_layout(case: dict) -> tuple[dict, dict[str, int], int]:
    seed = int(case["seed"])
    counts: dict[str, int] = {}
    for attempt in range(v4.MAX_ATTEMPTS):
        lay = v4._draw(case, np.random.default_rng(pv2.sub_seed(seed, v4.LAYOUT_STREAM, attempt)))
        result = domain.check_domain(lay["times"])
        if result.inside:
            return (
                {**lay, "attempt": attempt, "redraws": dict(counts), "domain": result},
                counts,
                attempt + 1,
            )
        counts[f"layout:{result.failed}"] = counts.get(f"layout:{result.failed}", 0) + 1
    raise RuntimeError(f"{case['id']}: the layout replay found no attempt inside")


def _map_absent(p: dict, labels: list[int]) -> None:
    """The record's rule (section 2.2), written here: the drawn year's position in (2018, 2019,
    2020) names the curve's label at that position."""
    if "var_absent_year" in p:
        position = (2018, 2019, 2020).index(p["var_absent_year"])
        p["var_absent_position"] = position
        p["var_absent_year"] = int(labels[position])


def _replay_parameters(case: dict, time, years, cadences, labels):
    from refute.packs.tess import synthetic
    from refute.packs.tess.params import HoldoutParams, SnrParams

    gate, hidden_min = SnrParams().min_snr, HoldoutParams().min_snr
    seed = int(case["seed"])
    counts: dict[str, int] = {}
    for attempt in range(v4.MAX_ATTEMPTS):
        seed_k = seed if attempt == 0 else pv2.sub_seed(seed, "redraw", attempt)
        p = pv2.draw_parameters(case, np.random.default_rng(seed_k), float(time.min()))
        _map_absent(p, labels)
        reason, profile = None, {}
        if case["class"] != "no_transit":
            reason = pv2._mechanism_condition(case, p, cadences)
            if reason is None:
                reason, profile = pv2._place_in_band(
                    synthetic, case, p, time, years, gate, hidden_min
                )
        if reason is None:
            if case["class"] != "no_transit" and "var_amplitude_factor" in p:
                p["var_amplitude"] = p["var_amplitude_factor"] * p["depth"]
            return seed_k, p, profile, counts, attempt + 1
        counts[reason] = counts.get(reason, 0) + 1
    raise RuntimeError(f"{case['id']}: the parameter replay found no valid attempt")


def _plain_json(value) -> str:
    return json.dumps(pv2.plain(value), sort_keys=True)


def built_report(case: dict, blob: bytes, layout: dict | None = None) -> dict:
    """Criteria 1, 4 and 6 on one built case (the replay of its attempts); each problem starts
    with its criterion, ``[1]``, ``[4]`` or ``[6]``."""
    problems: list[str] = []

    def add(criterion: int, text: str) -> None:
        problems.append(f"[{criterion}] {text}")

    meta, arrays = pv2.deserialize(blob)
    declared = {k: case[k] for k in CASE_KEYS}
    if _plain_json(meta.get("case")) != _plain_json(declared):
        add(4, f"the serialized case {meta.get('case')} is not the declared case {declared}")
    lay, layout_counts, n_layout = _replay_layout(case) if layout is None else layout
    sector, t_all, years_all = arrays["lc/sector"], arrays["lc/time"], arrays["lc/year"]
    numbers = sorted(set(sector.tolist()))
    built_times = [t_all[sector == k] for k in numbers]
    built = domain.check_domain(built_times)
    cadences = int(t_all.size)
    # criterion 1
    if not built.inside:
        add(1, f"the built curve is outside the domain: {built.reason}")
    if numbers != [1, 2, 3]:
        add(1, f"sectors {numbers}")
    for k, t in enumerate(lay["times"]):
        if k >= len(built_times) or not np.array_equal(built_times[k], t):
            add(1, f"sector {k + 1}: the built time stamps are not the layout's")
    labels = [s.label for s in built.sectors]
    for k, number in enumerate(numbers):
        if not np.all(years_all[sector == number] == labels[k]):
            add(1, f"sector {number}: year labels are not the first cadence's year")
    if meta.get("generator") != GENERATOR:
        add(1, f"generator {meta.get('generator')}")
    if _plain_json(meta["domain"]) != _plain_json(built.summary()):
        add(1, "the recorded domain summary is not the built curve's")
    if _plain_json(meta["layout"]) != _plain_json({"attempt": lay["attempt"], **lay["draws"]}):
        add(1, "the recorded layout is not the replayed one")
    # criterion 6 (b): the replay of every attempt
    cad = [(k + 1, t) for k, t in enumerate(built_times)]
    time = np.concatenate(built_times)
    years = np.concatenate([np.full(t.size, y) for t, y in zip(built_times, labels, strict=True)])
    seed_k, p, profile, param_counts, n_param = _replay_parameters(case, time, years, cad, labels)
    replayed = {**layout_counts}
    for key, n in param_counts.items():
        replayed[key] = replayed.get(key, 0) + n
    if meta["redraws"] != replayed:
        add(6, f"redraws {meta['redraws']}, replayed {replayed}")
    unknown = set(meta["redraws"]) - REDRAW_REASONS
    if unknown:
        add(6, f"undeclared redraw reasons {sorted(unknown)}")
    if meta["attempt_seed"] != str(seed_k):
        add(6, f"attempt seed {meta['attempt_seed']}, replayed {seed_k}")
    if _plain_json(meta["parameters"]) != _plain_json(p):
        add(6, "the recorded parameters are not the replayed ones")
    if _plain_json(meta["expected_snr"]) != _plain_json(profile):
        add(6, "the recorded expected SNR is not the replayed one")
    # criterion 6 (a): the primitive fields are draw_parameters'
    q = pv2.draw_parameters(
        case, np.random.default_rng(int(meta["attempt_seed"])), float(time.min())
    )
    _map_absent(q, labels)
    for key, value in q.items():
        if _plain_json(meta["parameters"].get(key)) != _plain_json(value):
            add(6, f"primitive {key}: recorded {meta['parameters'].get(key)}, drawn {value}")
    # criterion 4: the variability-free year
    rec = meta["parameters"]
    if case["mechanism"] == "variability_some_years":
        pos = rec.get("var_absent_position")
        if pos not in (0, 1, 2) or rec.get("var_absent_year") != labels[pos]:
            add(4, f"var_absent_year {rec.get('var_absent_year')} at {pos}, labels {labels}")
    elif "var_absent_year" in rec:
        add(4, "a variability-free year outside variability_some_years")
    return {
        "id": case["id"],
        "problems": problems,
        "replayed_attempts": n_layout + n_param,
        "cadences": cadences,
        "redraws": dict(meta["redraws"]),
    }


# --- criterion 6 (c): the source's boundaries ---------------------------------------------------


def source_problems(path: Path | None = None) -> list[str]:
    path = path or HERE / "population_v4.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    problems, seen = [], 0
    allowed = {
        "pv2": PV2_ATTRIBUTES,
        "synthetic": SYNTHETIC_ATTRIBUTES,
        "domain": DOMAIN_ATTRIBUTES,
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("refute"):
            for a in node.names:
                name = f"{node.module}.{a.name}"
                if name not in REFUTE_MODULES and node.module not in REFUTE_MODULES:
                    problems.append(f"imports {name}")
        elif isinstance(node, ast.Import):
            problems += [f"imports {a.name}" for a in node.names if a.name.startswith("refute")]
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            owner = node.value.id
            if owner in allowed:
                seen += 1
                if node.attr not in allowed[owner]:
                    problems.append(f"reads {owner}.{node.attr}")
        if isinstance(node, ast.Name) and "analy" in node.id.lower():
            problems.append(f"names {node.id}")
    if seen == 0:
        problems.append("no attribute read found (nothing checked)")
    return problems


# --- criterion 9: the order ---------------------------------------------------------------------


def order_problems(history: list[tuple[str, list[str]]]) -> list[str]:
    """``history``: (commit, paths) from the oldest. The record's first commit, then the tests'
    first commit, then the code's first commit, each strictly after the one before."""
    stages = (("record", RECORD_FILES), ("tests", TEST_FILES), ("code", CODE_FILES))
    first: dict[str, int] = {}
    for i, (_, paths) in enumerate(history):
        for name, files in stages:
            if name not in first and any(p in files for p in paths):
                first[name] = i
    problems = [f"no commit of the {name}" for name, _ in stages if name not in first]
    if not problems:
        if not first["record"] < first["tests"] < first["code"]:
            problems.append(f"order {first}: the record, the tests and the code must follow")
    return problems


RUN_CHECKS = (
    "1_domain", "2_coverage", "3_allocation", "4_composition", "5_band", "6_replay", "6_source",
    "8_x2f",
)  # fmt: skip
SABOTAGE_IDS = ("S1", "S2", "S3", "S4", "S5a", "S5b", "S6", "S7", "S8", "S9")


def first_run_problems(text: str | None) -> list[str]:
    """The tests' first run: recorded, with tests, none passing, every test failing or erring."""
    if not text:
        return ["the first run's record cannot be read"]
    record = json.loads(text)
    problems = []
    runs = record.get("runs", [])
    if not runs:
        problems.append("the first run's record holds no run")
    for run in runs:
        counts = run.get("counts", {})
        if run.get("tests", 0) < 1:
            problems.append(f"first run {run.get('label')}: no test")
        if counts.get("passed", 0) or counts.get("skipped", 0):
            problems.append(f"first run {run.get('label')}: a test passed or was skipped")
        if counts.get("failure", 0) + counts.get("error", 0) != run.get("tests"):
            problems.append(f"first run {run.get('label')}: not every test failed")
    return problems


def sabotage_output_problems(text: str | None) -> list[str]:
    if not text:
        return ["the sabotages' output cannot be read"]
    out = json.loads(text)
    got = {s.get("id"): s for s in out.get("sabotages", [])}
    problems = [f"sabotage {sid} missing" for sid in SABOTAGE_IDS if sid not in got]
    problems += [
        f"sabotage {sid} not caught"
        for sid in SABOTAGE_IDS
        if sid in got and not (got[sid].get("caught") and got[sid].get("control", {}).get("passed"))
    ]
    problems += [
        f"sabotage {sid}: its control has no positive coverage"
        for sid in SABOTAGE_IDS
        if sid in got and not (got[sid].get("control", {}).get("coverage") or 0) > 0
    ]
    if not out.get("all_caught"):
        problems.append("the sabotages' output does not record all caught")
    return problems


def _git_show(commit: str, path: str) -> str | None:
    done = subprocess.run(
        ["git", "show", f"{commit}:{path}"], cwd=REPO, capture_output=True, text=True
    )
    return done.stdout if done.returncode == 0 else None


def git_history(since: str = "c27a965") -> list[tuple[str, list[str]]]:
    text = subprocess.run(
        ["git", "log", "--reverse", "--name-only", "--format=commit %H", f"{since}..HEAD"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    history: list[tuple[str, list[str]]] = []
    for line in text.splitlines():
        if line.startswith("commit "):
            history.append((line.split()[1], []))
        elif line.strip() and history:
            history[-1][1].append(line.strip())
    return history


# --- the acceptance population ------------------------------------------------------------------


def check_case(case: dict) -> dict:
    """One case: its layout, its curve built in memory, criteria 1, 4, 5 and 6, its digest."""
    lay, counts, n_layout = _replay_layout(case)
    blob, _ = v4.build_case(case)
    report = built_report(case, blob, (lay, counts, n_layout))
    b = band.check(blob)
    return {
        "id": case["id"],
        "sha256": hashlib.sha256(blob).hexdigest(),
        "bytes": len(blob),
        "layout": layout_record(case, lay),
        "built": report,
        "band": b,
    }


def _ordered(cases: list[dict], order: str) -> list[dict]:
    if order == "index":
        return list(cases)
    if order == "reverse":
        return list(reversed(cases))
    if order == "interleaved":
        return cases[0::2] + cases[1::2][::-1]
    raise SystemExit(f"unknown order {order}")


def _worker_init():
    for name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[name] = "1"


def mode_run(args) -> int:
    cases = v4.population_cases(args.population)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict] = {}
    with cf.ProcessPoolExecutor(max_workers=args.workers, initializer=_worker_init) as pool:
        for r in pool.map(check_case, _ordered(cases, args.order), chunksize=4):
            results[r["id"]] = r
    rows = [results[c["id"]] for c in cases]
    records = [r["layout"] for r in rows]
    population: dict = {"coverage": {}}

    def built(criterion: int) -> list[str]:
        tag = f"[{criterion}] "
        return [
            f"{r['id']}: {p}" for r in rows for p in r["built"]["problems"] if p.startswith(tag)
        ]

    n = len(rows)
    with_transit = [r for r in rows if r["layout"]["class"] != "no_transit"]
    not_blend = [r for r in rows if r["layout"]["mechanism"] != "blend"]
    coverage = {
        "1_domain": sum(r["built"]["cadences"] > 0 for r in rows),
        "2_coverage": len(records),
        "3_allocation": len(cases),
        "4_composition": len(cases),
        "5_band": sum(r["band"]["snr_checked"] > 0 for r in with_transit)
        + sum(r["band"]["flux_checked"] > 0 for r in not_blend),
        "6_replay": sum(r["built"]["replayed_attempts"] >= 2 for r in rows),
        "6_source": 1,
        "8_x2f": 3,
    }
    required = {
        "1_domain": n,
        "2_coverage": n,
        "3_allocation": n,
        "4_composition": n,
        "5_band": len(with_transit) + len(not_blend),
        "6_replay": n,
        "6_source": 1,
        "8_x2f": 3,
    }
    checks = {
        "1_domain": domain_problems(records) + built(1),
        "2_coverage": coverage_problems(records, population["coverage"]),
        "3_allocation": allocation_problems(cases) + geometry_problems(records),
        "4_composition": composition_problems(cases) + built(4),
        "5_band": [f"{r['id']}: {p}" for r in rows for p in r["band"]["problems"]],
        "6_replay": built(6),
        "6_source": source_problems(),
        "8_x2f": x2f_report()["problems"],
    }
    for key in checks:
        if n == 0 or coverage[key] < required[key] or required[key] == 0:
            checks[key].append(
                f"coverage {coverage[key]} of the {required[key]} required (cases {n})"
            )
    redraws: Counter = Counter()
    for r in rows:
        for reason, n in r["built"]["redraws"].items():
            lay = r["layout"]
            redraws[(lay["class"], lay["band"], lay["mechanism"], reason)] += n
    population.update(
        {
            "format": "refute-population-v4-acceptance/1",
            "population": args.population,
            "generation": args.generation,
            "workers": args.workers,
            "order": args.order,
            "cases": len(rows),
            "cadences": int(sum(r["built"]["cadences"] for r in rows)),
            "snr_checked": int(sum(r["band"]["snr_checked"] for r in rows)),
            "flux_checked": int(sum(r["band"]["flux_checked"] for r in rows)),
            "replayed_attempts": int(sum(r["built"]["replayed_attempts"] for r in rows)),
            "redraws": {" | ".join(map(str, k)): n for k, n in sorted(redraws.items(), key=str)},
            "redraws_by_reason": {
                reason: sum(n for k, n in redraws.items() if k[3] == reason)
                for reason in sorted({k[3] for k in redraws})
            },
            "cases_with_layout_redraws": sum(r["layout"]["attempt"] > 0 for r in rows),
            "checks": {
                k: {
                    "passed": not v,
                    "problems": v[:50],
                    "n_problems": len(v),
                    "coverage": coverage[k],
                    "required": required[k],
                }
                for k, v in checks.items()
            },
            "x2f": x2f_report(),
        }
    )
    manifest = {
        "format": "refute-population-v4-manifest/1",
        "population": args.population,
        "cases": {r["id"]: r["sha256"] for r in rows},
    }
    manifest_bytes = (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode("utf-8")
    population["manifest_sha256"] = hashlib.sha256(manifest_bytes).hexdigest()
    (out_dir / f"population-{args.generation}.json").write_text(
        json.dumps(population, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    (out_dir / f"manifest-{args.generation}.json").write_bytes(manifest_bytes)
    failed = [k for k, v in checks.items() if v]
    print(json.dumps({"cases": len(rows), "failed": failed}))
    return 1 if failed else 0


def determinism_problems(out_dir: Path, population: str = "acceptance") -> tuple[dict, list[str]]:
    """Criterion 7: generations 1, 2 and 3, each a passing run over the whole population with its
    own worker count and order, and their manifests (bound to their runs) byte-identical."""
    expected = [c["id"] for c in v4.population_cases(population)]
    problems: list[str] = []
    runs = []
    for g in ("1", "2", "3"):
        man, pop = out_dir / f"manifest-{g}.json", out_dir / f"population-{g}.json"
        if not man.is_file() or not pop.is_file():
            problems.append(f"generation {g}: its manifest or its run record is missing")
            continue
        blob = man.read_bytes()
        manifest, run = json.loads(blob), json.loads(pop.read_text(encoding="utf-8"))
        digest = hashlib.sha256(blob).hexdigest()
        if run.get("manifest_sha256") != digest:
            problems.append(f"generation {g}: the run record does not name this manifest")
        if run.get("population") != population or manifest.get("population") != population:
            problems.append(f"generation {g}: not the {population} population")
        checks = run.get("checks", {})
        if set(checks) != set(RUN_CHECKS):
            problems.append(f"generation {g}: checks {sorted(checks)}, {list(RUN_CHECKS)} required")
        for name, c in checks.items():
            req = c.get("required") or 0
            if not c.get("passed") or req <= 0 or (c.get("coverage") or 0) < req:
                problems.append(f"generation {g}: check {name} did not pass with its coverage")
        ids = list(manifest.get("cases", {}))
        if sorted(ids) != sorted(expected) or run.get("cases") != len(expected):
            problems.append(f"generation {g}: {len(ids)} cases, the {len(expected)} expected")
        bad = [k for k, v in manifest.get("cases", {}).items() if not _is_sha256(v)]
        if bad:
            problems.append(f"generation {g}: {len(bad)} digests are not SHA-256")
        runs.append({"generation": g, "manifest_sha256": digest, "workers": run.get("workers"),
                     "order": run.get("order")})  # fmt: skip
    if len(runs) == 3:
        if len({r["manifest_sha256"] for r in runs}) != 1:
            problems.append("the manifests differ")
        if len({r["workers"] for r in runs}) != WORKER_COUNTS_REQUIRED:
            problems.append(f"worker counts {[r['workers'] for r in runs]}, three different")
        if sorted(r["order"] for r in runs) != sorted(ORDERS):
            problems.append(f"orders {[r['order'] for r in runs]}, the three declared")
    return {"runs": runs, "cases": len(expected)}, problems


def _is_sha256(value) -> bool:
    return (
        isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)
    )


def mode_compare(args) -> int:
    out_dir = Path(args.out_dir)
    summary, problems = determinism_problems(out_dir)
    out = {
        "format": "refute-population-v4-determinism/1",
        **summary,
        "passed": not problems,
        "problems": problems,
    }
    (out_dir / "determinism.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(out))
    return 1 if problems else 0


def mode_order(args) -> int:
    history = git_history(args.since)
    problems = order_problems(history)
    tests_commit = next((c for c, paths in history if any(p in TEST_FILES for p in paths)), None)
    if tests_commit is None or FIRST_RUN not in dict(history)[tests_commit]:
        problems.append("the first run's record is not in the tests' commit")
    else:
        problems += first_run_problems(_git_show(tests_commit, FIRST_RUN))
    code_index = next(
        (i for i, (_, p) in enumerate(history) if any(x in CODE_FILES for x in p)), None
    )
    sab_index = next((i for i, (_, p) in enumerate(history) if SABOTAGES in p), None)
    if sab_index is None:
        problems.append("pending: the sabotages' output is not committed")
    elif code_index is not None and sab_index < code_index:
        problems.append("the sabotages' output before the code")
    else:
        problems += sabotage_output_problems(_git_show(history[-1][0], SABOTAGES))
    out = {
        "format": "refute-population-v4-order/1",
        "history": [
            {"commit": c, "paths": [p for p in paths if "v4" in p or "domain" in p]}
            for c, paths in history
        ],
        "passed": not problems,
        "problems": problems,
    }
    Path(args.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"passed": out["passed"], "problems": problems}))
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    run = sub.add_parser("run")
    run.add_argument("--population", default="acceptance")
    run.add_argument("--generation", required=True)
    run.add_argument("--workers", type=int, required=True)
    run.add_argument("--order", default="index")
    run.add_argument("--out-dir", required=True)
    cmp_ = sub.add_parser("compare")
    cmp_.add_argument("--out-dir", required=True)
    order = sub.add_parser("order")
    order.add_argument("--out", required=True)
    order.add_argument("--since", default="c27a965")
    args = parser.parse_args(argv)
    return {"run": mode_run, "compare": mode_compare, "order": mode_order}[args.mode](args)


if __name__ == "__main__":
    raise SystemExit(main())
