"""The readings, the viability rule and the investigation step of the C/D viability package
(docs/validation/v0.2.1/reopen/stage-1/viability-cd/README.md, sections 3 to 6 and 9; the
acceptance record ``viability-cd-acceptance.md``, E1 to E9). It reads records only; it runs no
engine call and generates nothing.

- ``row_of``: every derived (status, reason) to its row of the declaration's section 4 (an
  unmapped one raises);
- ``target_rounds`` and ``spec_b``: ``derive_round`` at R = 8 with the committed pair, then
  specification B over every observing year;
- ``readings``: R1, R2 (the three sets of rows), R3 (the oracle), the identity flags, per
  alternative, noise model and regime;
- ``outcome``: OPERATIONAL CLOSURE, PASS, FAIL or INDETERMINATE (section 6), with the one-sided 95%
  Clopper-Pearson bounds and the missing planets assigned the worst way;
- ``newcombe``: C against D (section 5);
- ``e_pred``, ``derive_with``, ``step``: section 9's step over specification C's twelve pairs;
- ``destination``: section 9's table.
"""

from __future__ import annotations

import hashlib
import math
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import viability_cd as vc  # noqa: E402

pv2, rs = vc.pv2, vc.rs

R_MIN = 8
# The R_min study's committed pair (docs/validation/v0.2.1/reopen/stage-1/viability/README.md,
# section 3).
PAIR_B, PAIR_S = 0.585, 2.883
BENCHMARK = 275.0 / 360.0
FAIL_LIMIT = 0.10
MISSING_LIMIT = 0.05
OUTCOMES = ("PASS", "FAIL", "INDETERMINATE", "OPERATIONAL CLOSURE")
CLOSURE = "OPERATIONAL CLOSURE"

# --- the rows (the declaration's section 4) ----------------------------------------------------

ROW_EXACT = {
    "no training data": 1,
    "the train-only search found no candidate": 2,
    "train_noise_undetermined": 3,
    "train_snr_below_gate": 4,
    "duration_period_ratio_above_max": 5,
    "hidden_window_fraction_above_max": 8,
    "no_predicted_window": 9,
    "train_replicas_below_r_min": 10,
    "insufficient_capacity_train": 11,
    "hidden_noise_undetermined": 12,
    "insufficient_capacity_hidden_noise": 13,
    "too_few_windows": 14,
    "non_finite_statistic": 15,
    "not_detected_not_inconsistent": 16,
}
ROW6 = re.compile(r"only \d+ train transit times \(< \d+\)")
ROW7_PREFIX = "train-only timing uncertainty in the hidden year ("
BARRIERS = {
    1: "X", 2: "S", 3: "G", 4: "S", 5: "S", 6: "K", 7: "T", 8: "W", 9: "W",
    10: "K", 11: "K", 12: "N", 13: "N", 14: "M", 15: "M", 16: "decided", 17: "decided",
}  # fmt: skip
R2_SETS = {
    "R2-K": frozenset({6, 10, 11}),
    "R2-KT": frozenset({6, 7, 10, 11}),
    "R2-KTN": frozenset({6, 7, 10, 11, 12, 13}),
}
STEP_ROWS = frozenset({11, 13})

# The reason-producing functions of holdout.py (E2), pinned by the SHA-256 of their source: a
# change fails a test, so that section 4's table is reviewed again before any reading.
PINNED = {
    "plan_round": "5122b97bbc37f568f31fa16bfc1cce5502319edd5e09c2f14fbbca2bad74a2a3",
    "train_validity": "966ed3842c0d584756c5294276f6fc222f2197cfee64c7aa866b386e69677306",
    "_round_corrected": "5cbe75d2a17038ea6fa47957b979c39c11b1a37c52cc0a063ff11d6fc2988835",
    "replica_stats": "e38e39bdfda771d84e5eab2827f3df179a8ffa2f03a641e815d52aa24efd9e6f",
    "measure_windows": "b50a3cec3cecc3e16260b824f55d3ab58b9246b73d93c8e6c59be241e401e141",
    "measure_with_replicas": "ed9164242bc912e2b8394a98ca762293e843fb08e2fede784ecc194c6758be0d",
    "calibration_measurement": "dd93b5374d10b176ceffad9bed4ef659d6e24c72b53bceab4f46dd1dee42c52c",
    "derive_round": "4b801107653c3578712a123ed3e3ce2cfcd2cac31cf19ca50058dabb14d81dfb",
    "fail_rule": "f21643a1853afa2e1a9d250cc0f4648d3e957bdfce7df5e5ff196e47f9d32f86",
}


class UnmappedReasonError(ValueError):
    """A derived reason not in the declaration's table: a defect, never a silent class."""


def source_digests() -> dict[str, str]:
    """The SHA-256 of each pinned function's source as ``holdout.py`` holds it on disk (read from
    the file, so a function replaced at run time does not change it)."""
    import ast

    from refute.packs.tess import holdout

    text = Path(holdout.__file__).read_text(encoding="utf-8")
    found = {
        node.name: ast.get_source_segment(text, node)
        for node in ast.parse(text).body
        if isinstance(node, ast.FunctionDef) and node.name in PINNED
    }
    return {name: hashlib.sha256(found[name].encode()).hexdigest() for name in PINNED}


def row_of(status: str, reason) -> int:
    if status == "PASS" and reason is None:
        return 17
    if status == "FAIL" and reason == "inconsistent_with_train":
        return 17
    if status == "INCONCLUSIVE" and isinstance(reason, str):
        if reason in ROW_EXACT:
            return ROW_EXACT[reason]
        if ROW6.fullmatch(reason):
            return 6
        if reason.startswith(ROW7_PREFIX):
            return 7
    raise UnmappedReasonError(f"status {status!r} with reason {reason!r} is not in the table")


# --- the derivation and specification B (E1) ---------------------------------------------------


def _min_snr(min_snr: float | None) -> float:
    if min_snr is not None:
        return float(min_snr)
    from refute.packs.tess.params import HoldoutParams

    return float(HoldoutParams().min_snr)


def target_rounds(record: dict, min_snr: float | None = None, derive=None) -> list[dict]:
    """Each round of a target derived (``derive_round`` at R = 8 with the committed pair, or
    ``derive(round)``), with its row."""
    from refute.packs.tess.holdout import derive_round

    m = _min_snr(min_snr)
    out = []
    for rnd in record["rounds"]:
        d = derive(rnd) if derive else derive_round(rnd, R_MIN, PAIR_B, PAIR_S, m)
        out.append(
            {
                "year": int(rnd["hidden_year"]),
                "status": d["status"],
                "reason": d["reason"],
                "row": row_of(d["status"], d["reason"]),
            }
        )
    return out


def spec_b(rounds: list[dict], years: list[int], released: frozenset = frozenset()) -> str:
    """Specification B over every observing year; an INCONCLUSIVE round of a released row counts
    PASS (R2)."""
    from refute.packs.tess.holdout import spec_b_outcome

    triples = [
        (
            r["year"],
            "PASS" if r["status"] == "INCONCLUSIVE" and r["row"] in released else r["status"],
            r["reason"],
        )
        for r in rounds
    ]
    return spec_b_outcome(triples, years)["status"]


# --- the readings (R1 to R3) -------------------------------------------------------------------


def target_reading(record: dict, min_snr: float | None = None) -> dict:
    rounds = target_rounds(record, min_snr)
    years = [int(y) for y in record["years"]]
    oracle = record["oracle"]
    return {
        "case_id": record["case_id"],
        "alternative": record["alternative"],
        "noise": record["noise"],
        "regime": record["regime"],
        "n_years": len(years),
        "geometry": record["geometry"]["position"],
        "rounds": rounds,
        "R1": spec_b(rounds, years),
        "legacy": rs.aggregate(rounds),
        **{name: spec_b(rounds, years, rows) for name, rows in R2_SETS.items()},
        "R3": "PASS" if all(oracle[str(y)]["detectable"] for y in years) else "not PASS",
        "identity_flags": sum(bool(v["flag"]) for v in record["identity"].values()),
        "not_identifiable": sum(not v["identifiable"] for v in record["identity"].values()),
    }


def counts(readings: list[dict], key: str) -> Counter:
    return Counter(r[key] for r in readings)


def bounds(k: int, n: int) -> dict:
    return {
        "k": int(k),
        "n": int(n),
        "L": pv2.cp_lower(int(k), int(n)),
        "U": pv2.cp_upper(int(k), int(n)),
    }


# --- the rule (E5, E6) -------------------------------------------------------------------------


def pass_rule(n: int, n_pass: int, n_fail: int, missing: int) -> bool:
    """Section 6's PASS condition in one noise model, the missing planets counted not PASS and
    FAIL."""
    return pv2.cp_lower(n_pass, n) >= BENCHMARK and pv2.cp_upper(n_fail + missing, n) <= FAIL_LIMIT


def fail_rule_met(n: int, n_pass_r2ktn: int, n_fail: int, missing: int) -> bool:
    """Section 6's FAIL condition in one noise model, the missing planets counted PASS and not
    FAIL."""
    return (
        pv2.cp_upper(n_pass_r2ktn + missing, n) < BENCHMARK or pv2.cp_lower(n_fail, n) > FAIL_LIMIT
    )


def outcome(per_noise: dict[str, dict], operational: list[str]) -> dict:
    """``per_noise[noise]``: ``n`` declared, ``missing``, R1's ``pass`` and ``fail``, R2-KTN's
    ``pass_r2ktn``. ``operational``: the integrity errors and the cost check's stop (each a cause
    of OPERATIONAL CLOSURE)."""
    causes = list(operational)
    for noise, x in per_noise.items():
        if x["missing"] > MISSING_LIMIT * x["n"]:
            causes.append(f"{noise}: {x['missing']} of {x['n']} planets without a record")
    if causes:
        return {"outcome": CLOSURE, "causes": causes}
    if all(pass_rule(x["n"], x["pass"], x["fail"], x["missing"]) for x in per_noise.values()):
        return {"outcome": "PASS", "causes": []}
    if any(
        fail_rule_met(x["n"], x["pass_r2ktn"], x["fail"], x["missing"]) for x in per_noise.values()
    ):
        return {"outcome": "FAIL", "causes": []}
    return {"outcome": "INDETERMINATE", "causes": []}


# --- C against D (E7) --------------------------------------------------------------------------


def wilson(k: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    p = k / n
    centre = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return centre - half, centre + half


def newcombe(k1: int, n1: int, k2: int, n2: int) -> dict:
    """The difference ``k1/n1 - k2/n2`` with Newcombe's hybrid score (Wilson) two-sided 95%
    interval (his method 10)."""
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1)
    l2, u2 = wilson(k2, n2)
    d = p1 - p2
    return {
        "difference": d,
        "lo": d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2),
        "hi": d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2),
    }


# --- section 9's step (E8) ---------------------------------------------------------------------

MODELS_1 = ("E1.0", "E1.nomargin", "E1.dp0", "E1.dp0.nomargin")
MODELS_2 = ("E2.0", "E2.dp0", "E2.median")
PAIRS = tuple((a, b) for a in MODELS_1 for b in MODELS_2)


def e_pred(model: str, record: dict) -> float:
    """Specification C's C2 from the record's fields; ``nan`` unless every grid value is finite
    and not negative and ``n_pred`` positive (``predicted_error``'s rule)."""
    first = model.startswith("E1")
    values = record["train_var_rep"] if first else record["hidden_var_rep"]
    n_pred = record["n_pred"]
    if values is None or n_pred is None:
        return float("nan")
    v = np.asarray([np.nan if x is None else x for x in values], dtype=float)
    if v.size == 0 or not n_pred > 0 or not np.all(np.isfinite(v)) or np.any(v < 0):
        return float("nan")
    margin = float(record["m_beta"]) if first and not model.endswith("nomargin") else 1.0
    if model in ("E1.0", "E1.nomargin", "E2.0"):
        var = float(np.max(v))
    elif model == "E2.median":
        var = float(np.median(v))
    else:  # the dP_0 = 0 point of the grid
        grid = [float(x) for x in record["grid_dp"]]
        if 0.0 not in grid:
            return float("nan")
        var = float(v[grid.index(0.0)])
    return float(margin * math.sqrt(var / n_pred))


def s_pred(record: dict, e: float) -> float:
    d_c = record.get("d_c")
    if d_c is None or not (e > 0):
        return float("nan")
    return float(d_c) / e


def derive_with(record: dict, s1, s2, min_snr: float | None = None) -> dict:
    """``derive_round``'s order with only ``s_pred,1`` and ``s_pred,2`` given (section 9)."""
    from refute.packs.tess.holdout import capacity_threshold, fail_rule, replicas_enough

    def out(status, reason):
        return {"status": status, "reason": reason}

    m = _min_snr(min_snr)
    if record["stage"] == "before_capacity":
        return out("INCONCLUSIVE", record["reason"])
    if not replicas_enough(record["train_n_rep"], R_MIN):
        return out("INCONCLUSIVE", "train_replicas_below_r_min")
    threshold = capacity_threshold(m, PAIR_B, PAIR_S, record["n_years"])
    if not (s1 is not None and math.isfinite(s1) and s1 >= threshold):
        return out("INCONCLUSIVE", "insufficient_capacity_train")
    if (
        record["stage"] == "hidden_noise"
        or record["hidden_noise_undetermined"]
        or not replicas_enough(record["hidden_n_rep"] or [], R_MIN)
    ):
        return out("INCONCLUSIVE", "hidden_noise_undetermined")
    if not (s2 is not None and math.isfinite(s2) and s2 >= threshold):
        return out("INCONCLUSIVE", "insufficient_capacity_hidden_noise")
    if record["measurement_status"] != "ok":
        return out("INCONCLUSIVE", record["measurement_status"])
    status, reason, _ = fail_rule(
        record["s_meas"],
        m,
        record["d_train"],
        record["e_train"],
        record["d_hidden"],
        record["e_hidden"],
    )
    return out(status, reason)


def _pair_derive(e1: str, e2: str, min_snr: float | None):
    def derive(rnd):
        return derive_with(rnd, s_pred(rnd, e_pred(e1, rnd)), s_pred(rnd, e_pred(e2, rnd)), min_snr)

    return derive


def _envelope_derive(min_snr: float | None):
    def best(rnd, models):
        values = [s_pred(rnd, e_pred(m, rnd)) for m in models]
        finite = [v for v in values if math.isfinite(v)]
        return max(finite) if finite else float("nan")

    def derive(rnd):
        return derive_with(rnd, best(rnd, MODELS_1), best(rnd, MODELS_2), min_snr)

    return derive


def _tally(records: list[dict], derive, min_snr) -> Counter:
    c: Counter = Counter()
    for rec in records:
        rounds = target_rounds(rec, min_snr, derive)
        c[spec_b(rounds, [int(y) for y in rec["years"]])] += 1
    return c


def step_applies(alt_outcome: str, per_noise: dict, readings_by_noise: dict) -> bool:
    """Section 9: INDETERMINATE and, in a noise model where R1 misses the PASS rule, a non-PASS
    target with an undecided year of row 11 or 13."""
    if alt_outcome != "INDETERMINATE":
        return False
    for noise, x in per_noise.items():
        if pass_rule(x["n"], x["pass"], x["fail"], x["missing"]):
            continue
        for r in readings_by_noise[noise]:
            if r["R1"] != "PASS" and any(
                rd["status"] == "INCONCLUSIVE" and rd["row"] in STEP_ROWS for rd in r["rounds"]
            ):
                return True
    return False


# Section 9's ceiling: 1 LP-h (this one process's CPU time) and 0.5 h of wall time, shared by the
# step's alternatives, checked after each pair and after the envelope.
STEP_CPU_SECONDS = 3600.0
STEP_WALL_SECONDS = 1800.0


def both_ways(k: int, missing: int, n: int) -> dict:
    """The bounds with the missing planets counted not and counted (section 6)."""
    return {"without_missing": bounds(k, n), "with_missing": bounds(k + missing, n)}


def step(
    records_by_noise: dict,
    declared: dict,
    min_snr: float | None = None,
    cpu_seconds: float = STEP_CPU_SECONDS,
    clock=None,
    wall_seconds: float = STEP_WALL_SECONDS,
    wall_clock=None,
) -> dict:
    """The twelve pairs and the envelope over the records of one alternative; ``declared[noise]``
    the declared planets. Succeeds only if a single pair meets the PASS rule in both noise
    models. Past ``cpu_seconds`` of this process's CPU time or ``wall_seconds`` of wall time the
    step stops: OPERATIONAL CLOSURE of the step, never a result."""
    import time

    clock = time.process_time if clock is None else clock
    wall_clock = time.monotonic if wall_clock is None else wall_clock
    start, wall_start = clock(), wall_clock()

    def spent() -> dict:
        return {"cpu_seconds": clock() - start, "wall_seconds": wall_clock() - wall_start}

    def over(used: dict) -> bool:
        return used["cpu_seconds"] > cpu_seconds or used["wall_seconds"] > wall_seconds

    pairs = {}
    for e1, e2 in PAIRS:
        derive = _pair_derive(e1, e2, min_snr)
        per = {}
        for noise, records in records_by_noise.items():
            t = _tally(records, derive, min_snr)
            n, missing = declared[noise], declared[noise] - len(records)
            per[noise] = {
                "pass": t["PASS"],
                "fail": t["FAIL"],
                "missing": missing,
                "pass_bounds": both_ways(t["PASS"], missing, n),
                "fail_bounds": both_ways(t["FAIL"], missing, n),
                "meets": pass_rule(n, t["PASS"], t["FAIL"], missing),
            }
        pairs[f"{e1}+{e2}"] = {"noise": per, "meets_both": all(v["meets"] for v in per.values())}
        used = spent()
        if over(used):
            return {"closure": True, **used, "pairs": pairs}
    envelope = {}
    derive = _envelope_derive(min_snr)
    for noise, records in records_by_noise.items():
        t = _tally(records, derive, min_snr)
        envelope[noise] = {"pass_upper": t["PASS"], "fail_upper": t["FAIL"]}
    used = spent()
    if over(used):  # the envelope counts against the ceiling too
        return {"closure": True, **used, "pairs": pairs}
    meeting = [name for name, v in pairs.items() if v["meets_both"]]
    return {
        "closure": False,
        **used,
        "pairs": pairs,
        "envelope_descriptive": envelope,
        "pairs_meeting_the_rule": meeting,
        "succeeds": bool(meeting),
    }


# --- the destination (E9) ----------------------------------------------------------------------


def destination(c: str, d: str) -> dict:
    """Section 9's table: the proposals that may be presented, the alternatives whose records the
    step reads, the closures, the alternatives abandoned, and whether the investment ends."""
    if c not in OUTCOMES or d not in OUTCOMES:
        raise ValueError(f"unknown outcomes {c!r}, {d!r}")
    out = {"proposals": [], "step_over": [], "closures": [], "abandoned": [], "ends": False}
    for name, x in (("C", c), ("D", d)):
        if x == CLOSURE:
            out["closures"].append(name)
    if c == CLOSURE and d == CLOSURE:
        return out
    if c == CLOSURE:
        if d == "PASS":
            out["proposals"].append("D sizing proposal")
        elif d == "FAIL":
            out["abandoned"].append("D")
        else:
            out["step_over"].append("D")
        return out
    if d == CLOSURE:
        if c == "PASS":
            out["proposals"].append("C executable plan")
        elif c == "FAIL":
            out["abandoned"].append("C")
        else:
            out["step_over"].append("C")
        return out
    if c == "PASS":
        out["proposals"].append("C executable plan")
        return out
    if c == "FAIL" and d == "FAIL":
        out["abandoned"] += ["C", "D"]
        out["ends"] = True
        return out
    if d == "PASS":
        out["proposals"].append("D sizing proposal")
        if c == "INDETERMINATE":
            out["step_over"].append("C")
        else:
            out["abandoned"].append("C")
        return out
    if c == "FAIL":  # D INDETERMINATE
        out["abandoned"].append("C")
        out["step_over"].append("D")
        return out
    out["step_over"].append("C")  # C INDETERMINATE, D FAIL or INDETERMINATE
    if d == "INDETERMINATE":
        out["step_over"].append("D")
    else:
        out["abandoned"].append("D")
    return out


# --- the evaluation of the two sub-lots --------------------------------------------------------


def declared_planets(alternative: str) -> dict[str, int]:
    return {noise: sum(n for _, n in vc.REGIMES[alternative]) for noise in vc.NOISES}


def alternative_summary(
    records: list[dict], alternative: str, operational: list[str], min_snr=None
):
    """Every reading and the outcome of one alternative from its records (present ones). A record
    that cannot be derived (an unmapped reason, specification B's completeness) is an integrity
    error: OPERATIONAL CLOSURE, never an exception before the outcome."""
    operational = list(operational)
    readings = []
    for r in records:
        try:
            readings.append(target_reading(r, min_snr))
        except Exception as exc:  # noqa: BLE001 - every such error is a cause, reported
            operational.append(f"{r.get('case_id')}: not derivable ({type(exc).__name__}: {exc})")
    declared = declared_planets(alternative)
    per_noise, by_noise = {}, {}
    for noise in vc.NOISES:
        rows = [r for r in readings if r["noise"] == noise]
        by_noise[noise] = rows
        c1, c2 = counts(rows, "R1"), counts(rows, "R2-KTN")
        n, missing = declared[noise], declared[noise] - len(rows)
        per_noise[noise] = {
            "n": n,
            "missing": missing,
            "pass": c1["PASS"],
            "fail": c1["FAIL"],
            "pass_r2ktn": c2["PASS"],
            "R1_pass_bounds_worst": bounds(c1["PASS"], n),
            "R1_pass_bounds_best": bounds(c1["PASS"] + missing, n),
            "R1_fail_bounds_worst": bounds(c1["FAIL"] + missing, n),
            "R1_fail_bounds_best": bounds(c1["FAIL"], n),
            **{
                f"{name}_pass": counts(rows, name)["PASS"]
                for name in ("legacy", "R2-K", "R2-KT", "R2-KTN", "R3")
            },
            # the binding barriers (section 6): each R2 set's PASS and FAIL bounds both ways, and
            # whether its PASS reaches L >= 275/360 with the missing planets counted not PASS
            "R2": {
                name: {
                    "pass_bounds": both_ways(counts(rows, name)["PASS"], missing, n),
                    "fail_bounds": both_ways(counts(rows, name)["FAIL"], missing, n),
                    "reaches_benchmark": pv2.cp_lower(counts(rows, name)["PASS"], n) >= BENCHMARK,
                }
                for name in R2_SETS
            },
            "R3_pass_bounds": both_ways(counts(rows, "R3")["PASS"], missing, n),
        }
    result = outcome(per_noise, operational)
    out = {
        "alternative": alternative,
        "per_noise": per_noise,
        "outcome": result,
        "barriers": dict(Counter(BARRIERS[rd["row"]] for r in readings for rd in r["rounds"])),
        "rows": dict(Counter(rd["row"] for r in readings for rd in r["rounds"])),
        "by_regime": {
            f"{noise}/{regime}": dict(
                counts([r for r in by_noise[noise] if r["regime"] == regime], "R1")
            )
            for noise in vc.NOISES
            for regime, _ in vc.REGIMES[alternative]
        },
        "by_years": {
            str(k): dict(counts([r for r in readings if r["n_years"] == k], "R1"))
            for k in sorted({r["n_years"] for r in readings})
        },
        "by_geometry": {
            str(g): dict(counts([r for r in readings if r["geometry"] == g], "R1"))
            for g in sorted({r["geometry"] for r in readings})
        },
        "rounds_pass_by_years": {
            str(k): {
                "rounds": sum(len(r["rounds"]) for r in readings if r["n_years"] == k),
                "pass": sum(
                    rd["status"] == "PASS"
                    for r in readings
                    if r["n_years"] == k
                    for rd in r["rounds"]
                ),
            }
            for k in sorted({r["n_years"] for r in readings})
        },
        "identity_flags": sum(r["identity_flags"] for r in readings),
        "not_identifiable_rounds": sum(r["not_identifiable"] for r in readings),
    }
    out["readings"] = readings
    out["by_noise"] = by_noise
    out["records"] = records
    return out


def _read_json(path: Path):
    import json

    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def sublot_state(
    run_dir: Path, spec, geometries: list[dict], geometry_sha256: str, tasks=None
) -> dict:
    """A sub-lot's present valid records, its operational causes and its notes (never raises).

    Causes (OPERATIONAL CLOSURE): an unreadable manifest, or one that is not this sub-lot's (its
    lot, alternative, prefix, seed root, ceilings, task list, geometry list's SHA-256), or whose
    code, plan, configuration or environment differs from the evaluation's; a record file that
    does not parse, is not at a task's path or fails its check; the 10% cost check's stop; a
    generation defect. Notes (the completeness rule decides, section 6 and section 7: "what ran is
    evaluated as section 6 says"): the submission ceiling reached, an invocation interrupted,
    failed tasks, each leaving records missing."""
    from refute.core.canonical import canonical_sha256

    run_dir = Path(run_dir)
    manifest = _read_json(run_dir / "manifest.json")
    if not isinstance(manifest, dict):
        return {
            "records": [],
            "causes": [f"{spec.name}: no readable manifest (not run)"],
            "notes": [],
        }
    causes, notes = [], []
    want = {
        "format": vc.LOT_FORMAT,
        "lot": spec.name,
        "alternative": spec.alternative,
        "prefix": spec.prefix,
        "seed_root": spec.seed_root,
        "deadline_hours": spec.deadline_hours,
        "lp_hours": spec.lp_hours,
        "geometry_sha256": geometry_sha256,
        "configuration": rs._canonical(vc.v3.STATE["identity"]),
        "plan_sha256": canonical_sha256(vc.v3._plan().model_dump(mode="json")),
        "code_sha256": vc.code_digest(),
        "environment": rs._canonical(vc.x2.environment()),
    }
    causes += [
        f"{spec.name}: the manifest's {k} is not the evaluation's"
        for k, v in want.items()
        if manifest.get(k) != v
    ]
    problems = vc.lot_problems(run_dir, spec, geometries, tasks, full=True)
    missing = [p for p in problems if p.endswith(": no record")]
    causes += [p for p in problems if not p.endswith(": no record")]
    if (run_dir / "defect.json").exists():
        causes.append(f"{spec.name}: a generation defect stopped the sub-lot (defect.json)")
    check = _read_json(run_dir / "cost-check.json")
    if (run_dir / "cost-check.json").exists() and not isinstance(check, dict):
        causes.append(f"{spec.name}: the cost check's record is not readable")
    elif isinstance(check, dict) and check.get("stop") is True:
        causes.append(f"{spec.name}: the 10% cost check stopped the sub-lot")
    reports = [_read_json(p) for p in sorted(run_dir.glob("run-report-*.json"))]
    if any(not isinstance(r, dict) for r in reports):
        causes.append(f"{spec.name}: a run report is not readable")
    reports = [r for r in reports if isinstance(r, dict)]
    if any(r.get("deadline_reached") for r in reports):
        notes.append("the submission ceiling was reached")
    for path in sorted((run_dir / "consumption").glob("*.json")):
        c = _read_json(path)
        if not isinstance(c, dict) or c.get("closed") is not True:
            notes.append(f"the invocation {path.stem} did not close (interrupted)")
    if any(r.get("failures") or r.get("terminal_failures") for r in reports):
        notes.append("failed tasks")
    if missing:
        notes.append(f"{len(missing)} records missing")
    records, bad = vc.load_records(run_dir)
    causes += [f"{rel}: not a record" for rel in bad]
    records = [r for r in records if r.get("alternative") == spec.alternative]
    return {"records": records, "causes": causes, "notes": notes}


def final_reading(destination_: dict, steps: dict) -> dict:
    """What may follow, after the step (section 9): the proposals the table allows, the proposal of
    specification C's validation if a step succeeded, the INDETERMINATE alternatives ended, and
    whether the current effort ends as not approved."""
    proposals = list(destination_["proposals"])
    ended = list(destination_["abandoned"])
    closures = list(destination_["closures"])
    for alt, s in steps.items():
        if s is None:
            ended.append(alt)  # the step does not apply: the INDETERMINATE ends the alternative
        elif s.get("closure"):
            closures.append(f"the step over {alt}")
        elif s["succeeds"]:
            if "specification C validation proposal" not in proposals:
                proposals.append("specification C validation proposal")
        else:
            ended.append(alt)
    return {
        "proposals": proposals,
        "ended": sorted(set(ended)),
        "closures": closures,
        "effort_ends_not_approved": not proposals and not closures,
    }


def evaluate(run_dirs: dict[str, Path], listing_path: Path, min_snr: float | None = None) -> dict:
    """Both sub-lots, in this order: each alternative's readings and outcome; their joint
    destination (section 9's table); then the one investigation step, over the alternatives the
    destination names and only where it applies, within its ceiling; then the final reading."""
    import json

    data = Path(listing_path).read_bytes()
    geometry_sha256 = hashlib.sha256(data).hexdigest()
    listing = json.loads(data)
    summaries, states = {}, {}
    for name in vc.SUBLOT_ORDER:
        spec = vc.SUBLOTS[name]
        geometries = vc.selected_geometries(spec.alternative, listing)
        if not geometries:  # the declaration, section 1: no geometry, INDETERMINATE
            summaries[spec.alternative] = {
                "alternative": spec.alternative,
                "outcome": {"outcome": "INDETERMINATE", "causes": ["no geometry"]},
                "readings": [],
                "by_noise": {},
                "per_noise": {},
                "records": [],
            }
            states[spec.alternative] = {"causes": [], "notes": ["no geometry"]}
            continue
        state = sublot_state(run_dirs[name], spec, geometries, geometry_sha256)
        states[spec.alternative] = {k: state[k] for k in ("causes", "notes")}
        summaries[spec.alternative] = alternative_summary(
            state["records"], spec.alternative, state["causes"], min_snr
        )
    c, d = summaries["C"], summaries["D"]
    dest = destination(c["outcome"]["outcome"], d["outcome"]["outcome"])
    steps: dict = {}
    budget, wall_budget = STEP_CPU_SECONDS, STEP_WALL_SECONDS  # shared by the alternatives
    for alt in dest["step_over"]:
        s = summaries[alt]
        if not s["per_noise"] or not step_applies(
            s["outcome"]["outcome"], s["per_noise"], s["by_noise"]
        ):
            steps[alt] = None
            continue
        records = {noise: [r for r in s["records"] if r["noise"] == noise] for noise in vc.NOISES}
        steps[alt] = step(
            records,
            declared_planets(alt),
            min_snr,
            cpu_seconds=budget,
            wall_seconds=wall_budget,
        )
        budget -= steps[alt]["cpu_seconds"]
        wall_budget -= steps[alt]["wall_seconds"]
    return {
        "geometry_sha256": geometry_sha256,
        "states": states,
        "alternatives": {
            k: {x: v for x, v in s.items() if x not in ("readings", "by_noise", "records")}
            for k, s in summaries.items()
        },
        "c_against_d": compare(c["readings"], d["readings"]),
        "destination": dest,
        "steps": steps,
        "final": final_reading(dest, steps),
        "readings": {k: s["readings"] for k, s in summaries.items()},
    }


def compare(c_readings: list[dict], d_readings: list[dict]) -> dict:
    """E7: on the planets without variability, C's spec-B PASS fraction minus D's, per noise model,
    for R1 and R2-KTN."""
    out = {}
    for noise in vc.NOISES:
        a = [r for r in c_readings if r["noise"] == noise and r["regime"] == "three_years"]
        b = [r for r in d_readings if r["noise"] == noise and r["regime"] == "three_years"]
        if not a or not b:
            out[noise] = None
            continue
        out[noise] = {
            key: newcombe(
                sum(r[key] == "PASS" for r in a), len(a), sum(r[key] == "PASS" for r in b), len(b)
            )
            for key in ("R1", "R2-KTN")
        }
    return out
