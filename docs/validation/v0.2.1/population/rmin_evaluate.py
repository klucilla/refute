"""The evaluation of the ``R_min`` study and of its lot ``bs-choice``
(docs/validation/v0.2.1/reopen/m4-implementation-map.md, Amendment 19; the readings of Amendment
26, 1 and 2, approved on 2026-10-19; the evaluation rules of Amendment 27). Pure functions over
the records: no lot is generated or read from disk here.

A target record is ``{"target", "group", "scenario", "years", "rounds"}``: its identity
(``<prefix>/<case id>``), its group (noise model and variability), its scenario, the observing
years of its light curve's metadata and one ``calibration_measurement`` record per observing year
(with the scenario's twin).
"""

from __future__ import annotations

import math
from collections import Counter

import numpy as np
from scipy.stats import beta

from refute.packs.tess.holdout import derive_round, replicas_enough

R_VALUES = (8, 10, 12, 15, 20)
LEVEL = 1.0 - 0.05 / len(R_VALUES)  # one-sided Clopper-Pearson, per bound (Amendment 19)
MAD_SCALE = 1.4826
TIE = 0.05  # Amendment 9: a tie within 5 % of the larger goes to k = 2
MINIMA = {"false_fail": 866, "disappearance": 83, "weakening": 101}  # Amendment 26, reading 2
FALSE_FAIL_MAX = 0.02
DISAPPEARANCE_MIN = 0.80
WEAKENING_MIN = 0.50
WEAKENING_FILTER = 3.0  # 0.3 * S_pred,2 <= 3
WEAKENED_S = 0.3
COVERAGE_1 = (0.60, 0.76)
COVERAGE_2 = (0.92, 0.98)
COVERAGE_MEDIAN = 0.2
GROUPS = (
    "white, no variability",
    "white, variability",
    "AR(1), no variability",
    "AR(1), variability",
)


class StudyStoppedError(RuntimeError):
    """The study cannot go on (Amendment 27, 4): it goes to the maintainer."""


def _finite(x) -> bool:
    return x is not None and isinstance(x, (int, float)) and math.isfinite(x)


def _mad(values) -> float:
    v = np.asarray(values, dtype=float)
    return float(np.median(np.abs(v - np.median(v))))


def _rounds(records):
    for rec in records:
        for r in rec["rounds"]:
            yield rec, r


def _k_set(records, k: int, min_snr: float) -> list[tuple[dict, dict]]:
    key = f"s_pred_{k}"
    return [
        (rec, r)
        for rec, r in _rounds(records)
        if _finite(r.get("s_meas")) and _finite(r.get(key)) and r[key] >= min_snr
    ]


def choose_k(records: list[dict], min_snr: float) -> dict:
    """Amendment 9's rule on the constant rounds of ``bs-choice`` (Amendment 27, 4). The tie is read
    on the unscaled MADs (the factor 1.4826 is positive and cancels)."""
    sets = {k: _k_set(records, k, min_snr) for k in (1, 2)}
    empty = [k for k, s in sets.items() if not s]
    if empty:
        raise StudyStoppedError(
            f"no round for k = {empty}: Amendment 9's comparison does not exist"
        )
    mad = {k: _mad([r["s_meas"] - r[f"s_pred_{k}"] for _, r in s]) for k, s in sets.items()}
    if abs(mad[1] - mad[2]) <= TIE * max(mad[1], mad[2]):
        k = 2
    else:
        k = 1 if mad[1] < mad[2] else 2
    return {
        "k": k,
        "a": {k_: MAD_SCALE * m for k_, m in mad.items()},
        "n": {k_: len(s) for k_, s in sets.items()},
    }


def meets_r(r: dict, r_min: int) -> bool:
    """The round meets ``R``: the train and the hidden replica counts at least ``R`` at every dP of
    the grid and the hidden noise determined (Amendment 27, 5)."""
    return (
        bool(r.get("train_n_rep"))
        and replicas_enough(r["train_n_rep"], r_min)
        and bool(r.get("hidden_n_rep"))
        and replicas_enough(r["hidden_n_rep"], r_min)
        and r.get("hidden_noise_undetermined") is False
    )


def pair_for_r(records: list[dict], k: int, r_min: int, min_snr: float) -> dict | None:
    """``b_R``, ``s_R``: the median and 1.4826 MAD of ``S_meas - S_pred,k`` over item 4's set that
    meets ``R``; ``None`` without any residual (that R is not evaluable)."""
    rows = [(rec, r) for rec, r in _k_set(records, k, min_snr) if meets_r(r, r_min)]
    if not rows:
        return None
    residuals = [r["s_meas"] - r[f"s_pred_{k}"] for _, r in rows]
    return {
        "b": float(np.median(residuals)),
        "s": MAD_SCALE * _mad(residuals),
        "rounds": len(rows),
        "targets": len({rec["target"] for rec, _ in rows}),
    }


def completeness_problems(manifest: list[tuple[str, str]], records: list[dict]) -> list[str]:
    """Amendment 27, 3: every expected target and scenario has one record, with one round per
    observing year of its metadata and no other."""
    problems = []
    seen = Counter((rec["target"], rec["scenario"]) for rec in records)
    expected = Counter(tuple(m) for m in manifest)
    for key, n in expected.items():
        if n > 1:
            problems.append(f"{key}: listed {n} times in the manifest")
        if seen[key] == 0:
            problems.append(f"{key}: no record")
    for key, n in seen.items():
        if key not in expected:
            problems.append(f"{key}: a record not in the manifest")
        elif n > 1:
            problems.append(f"{key}: {n} records")
    for rec in records:
        years = Counter(r["hidden_year"] for r in rec["rounds"])
        if sorted(years) != sorted(set(rec["years"])) or any(n != 1 for n in years.values()):
            problems.append(
                f"{(rec['target'], rec['scenario'])}: rounds {dict(years)} for years {rec['years']}"
            )
    return problems


def aggregate(statuses: list[str]) -> str:
    if "FAIL" in statuses:
        return "FAIL"
    if "PASS" in statuses:
        return "PASS"
    return "INCONCLUSIVE"


def target_outcomes(rec: dict, r_min: int, b: float, s: float, min_snr: float) -> dict:
    """The target at ``R`` and the pair: each round derived, the aggregated status, its
    eligibility, its first eligible round (in increasing year) and the round hiding its last
    observing year (the largest year of the metadata)."""
    derived = {
        r["hidden_year"]: {**derive_round(r, r_min, b, s, min_snr), "record": r}
        for r in rec["rounds"]
    }
    ordered = [derived[y] for y in sorted(derived)]
    last_year = max(rec["years"])
    first = next((d for d in ordered if d["eligible"]), None)
    return {
        "status": aggregate([d["status"] for d in ordered]),
        "eligible": first is not None,
        "first_eligible": (
            None if first is None else {**first, "hidden_year": first["record"]["hidden_year"]}
        ),
        "last_year": last_year,
        "last_round": derived.get(last_year),
        "rounds": ordered,
    }


def _cp_upper(x: int, n: int) -> float:
    return 1.0 if x >= n else float(beta.ppf(LEVEL, x + 1, n - x))


def _cp_lower(x: int, n: int) -> float:
    return 0.0 if x <= 0 else float(beta.ppf(1.0 - LEVEL, x, n - x + 1))


def _passes_decisions(last: dict | None) -> bool:
    return last is not None and last["decision_1"] == "pass" and last["decision_2"] == "pass"


def _fraction(x: int, n: int) -> float | None:
    """A reported fraction; ``None`` (not evaluable) with a zero denominator."""
    return x / n if n else None


def _inconclusive(outcomes: list[dict]) -> dict:
    """Criterion 6 (reported, not a criterion): the INCONCLUSIVE fractions per target and per
    round, with every reason. A target is counted once, under the combination of the distinct
    reasons of its INCONCLUSIVE rounds (``+``-joined, sorted), so the target counts sum to the
    INCONCLUSIVE targets (added after the Codex review of the round)."""
    n_targets = len(outcomes)
    n_rounds = sum(len(o["rounds"]) for o in outcomes)
    inconclusive = [o for o in outcomes if o["status"] == "INCONCLUSIVE"]
    combos = Counter(
        "+".join(sorted({str(d["reason"]) for d in o["rounds"] if d["status"] == "INCONCLUSIVE"}))
        for o in inconclusive
    )
    rounds = Counter(
        str(d["reason"]) for o in outcomes for d in o["rounds"] if d["status"] == "INCONCLUSIVE"
    )
    return {
        "targets": n_targets,
        "inconclusive_targets": len(inconclusive),
        "inconclusive_target_fraction": _fraction(len(inconclusive), n_targets),
        "targets_by_reasons": {
            k: {"count": v, "fraction": _fraction(v, n_targets)} for k, v in sorted(combos.items())
        },
        "rounds": n_rounds,
        "inconclusive_rounds": sum(rounds.values()),
        "inconclusive_round_fraction": _fraction(sum(rounds.values()), n_rounds),
        "rounds_by_reason": {
            k: {"count": v, "fraction": _fraction(v, n_rounds)} for k, v in sorted(rounds.items())
        },
    }


def criteria(records: list[dict], r_min: int, pair: dict, min_snr: float) -> dict:
    """Criteria 1 to 5 of Amendment 19 at ``R`` with its pair, per group (Amendment 27, 6 to 9), and
    the INCONCLUSIVE fractions (criterion 6, reported)."""
    out = {}
    for group in GROUPS:
        rows = [rec for rec in records if rec["group"] == group]
        by = {
            sc: [
                target_outcomes(rec, r_min, pair["b"], pair["s"], min_snr)
                for rec in rows
                if rec["scenario"] == sc
            ]
            for sc in ("constant", "disappearing", "weakened")
        }
        eligible = [o for o in by["constant"] if o["eligible"]]
        n1 = len(eligible)
        fails = sum(o["status"] == "FAIL" for o in eligible)
        upper = _cp_upper(fails, n1) if n1 else 1.0
        false_fail = {
            "n": n1,
            "fails": fails,
            "upper": upper,
            "passed": n1 >= MINIMA["false_fail"] and upper <= FALSE_FAIL_MAX,
        }
        pulls, missing = [], 0
        for o in eligible:
            r = o["first_eligible"]["record"]
            if (
                _finite(r.get("d_twin"))
                and _finite(r.get("d_hidden"))
                and _finite(r.get("e_hidden"))
            ):
                pulls.append((r["d_hidden"] - r["d_twin"]) / r["e_hidden"])
            else:
                missing += 1
        coverage: dict = {"n": n1, "missing_twin": missing, "evaluable": n1 > 0 and missing == 0}
        if coverage["evaluable"]:
            p = np.asarray(pulls)
            within_1 = float(np.mean(np.abs(p) <= 1.0))
            within_2 = float(np.mean(np.abs(p) <= 2.0))
            median = float(np.median(p))
            coverage.update(
                within_1=within_1,
                within_2=within_2,
                median=median,
                passed=(
                    COVERAGE_1[0] <= within_1 <= COVERAGE_1[1]
                    and COVERAGE_2[0] <= within_2 <= COVERAGE_2[1]
                    and abs(median) <= COVERAGE_MEDIAN
                ),
            )
        else:
            coverage["passed"] = False
        power = {}
        for name, sc, minimum, threshold in (
            ("disappearance", "disappearing", MINIMA["disappearance"], DISAPPEARANCE_MIN),
            ("weakening", "weakened", MINIMA["weakening"], WEAKENING_MIN),
        ):
            qualified = []
            for o in by[sc]:
                last = o["last_round"]
                if not _passes_decisions(last):
                    continue
                if name == "weakening":
                    s2 = last["record"].get("s_pred_2")
                    if not (_finite(s2) and WEAKENED_S * s2 <= WEAKENING_FILTER):
                        continue
                qualified.append(o)
            n = len(qualified)
            x = sum(o["status"] == "FAIL" for o in qualified)
            lower = _cp_lower(x, n) if n else 0.0
            power[name] = {
                "n": n,
                "fails": x,
                "lower": lower,
                "passed": n >= minimum and lower >= threshold,
                "last_round_statuses": dict(Counter(o["last_round"]["status"] for o in qualified)),
            }
        result = {
            "false_fail": false_fail,
            "coverage": coverage,
            **power,
            "inconclusive": {sc: _inconclusive(v) for sc, v in by.items()},
        }
        result["all_passed"] = all(
            result[c]["passed"] for c in ("false_fail", "coverage", "disappearance", "weakening")
        )
        out[group] = result
    return out


def choose_r_min(results: dict) -> int | None:
    """The smallest ``R`` whose pair exists (its result is not ``None``) and that meets criteria 1
    to 5 in all four groups; ``None`` is option (c)."""
    for r_min in sorted(results):
        res = results[r_min]
        if res is not None and all(res[g]["all_passed"] for g in GROUPS):
            return r_min
    return None
