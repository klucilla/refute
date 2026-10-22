"""X2's evaluation (docs/validation/v0.2.1/reopen/stage-1/x2-declaration.md, revision 2): X2-A
(geometry and identity, section 5) and X2-B (the calibration of the uncertainties, section 6), as
pure functions over the records, the evaluator's truth and the cases' noiseless cadences. The
engine never sees any of this; nothing here reads a light curve's flux.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter, defaultdict

import numpy as np

ALIASES = ((2.0, "alias x2"), (3.0, "alias x3"), (0.5, "alias /2"), (1.0 / 3.0, "alias /3"))
REDUCTION = 0.8  # a factor reduces d_twin / d_train when it is below 0.8 (I above 1.25)
MIN_REALIZATIONS = 30
MIN_CASES = 15
TAU = 0.10
N_BOOT = 2000
BOOT_SEED_TEXT = "refute/v0.2.1/stage-1/X2/bootstrap"
MAD_SCALE = 1.4826


def _finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


# --- X2-A (section 5) ------------------------------------------------------------------------


def identity_class(period: float, true_period: float, true_duration: float, span: float) -> str:
    """5.1: ``same``, ``alias ...`` or ``other``, with ``eps = D* / (2 span)``."""
    eps = true_duration / (2.0 * span)
    q = period / true_period
    if abs(q - 1.0) <= eps:
        return "same"
    for k, name in ALIASES:
        if abs(q / k - 1.0) <= eps:
            return name
    return "other"


def predicted_centers(eph: dict, dp: float, spans: list[tuple[float, float]]) -> list[float]:
    """5.2: the measurement's centers ``t_ref + m (P + dP)`` for the epochs ``m`` whose
    ``t_ref + m P`` falls inside a hidden span (the engine's ``_predict_windows``, transit kind)."""
    t_ref, period = float(eph["t_ref"]), float(eph["period"])
    out = []
    for start, end in spans:
        first = math.ceil((start - t_ref) / period)
        last = math.floor((end - t_ref) / period)
        out += [t_ref + m * (period + dp) for m in range(first, last + 1)]
    return out


def injected_centers(t0: float, period: float, spans: list[tuple[float, float]]) -> list[float]:
    out = []
    for start, end in spans:
        first = math.ceil((start - t0) / period)
        last = math.floor((end - t0) / period)
        out += [t0 + n * period for n in range(first, last + 1)]
    return out


def _near(t: np.ndarray, centers: list[float], half: float) -> np.ndarray:
    mask = np.zeros(t.size, bool)
    for c in centers:
        mask |= np.abs(t - c) <= half
    return mask


def _band(t: np.ndarray, centers: list[float], inner: float, outer: float) -> np.ndarray:
    mask = np.zeros(t.size, bool)
    for c in centers:
        d = np.abs(t - c)
        mask |= (d > inner) & (d <= outer)
    return mask


def _windows_mask(t: np.ndarray, windows: list[dict], key: str) -> np.ndarray:
    """Cadences within ``window[key]`` of a window's predicted time, for any of ``windows``."""
    mask = np.zeros(t.size, bool)
    for w in windows:
        mask |= np.abs(t - w["t_pred"]) <= w[key]
    return mask


def _windows_band(t: np.ndarray, windows: list[dict]) -> np.ndarray:
    mask = np.zeros(t.size, bool)
    for w in windows:
        d = np.abs(t - w["t_pred"])
        mask |= (d > w["baseline_inner"]) & (d <= w["baseline_outer"])
    return mask


def round_geometry(
    rnd: dict,
    truth: dict,
    hidden_times: np.ndarray,
    spans,
    span: float,
    deficit,
    registered: list[dict] | None,
) -> dict:
    """5.1 to 5.5 for one round. ``deficit(t)`` is ``1 - signal_model`` of the injected signal
    (no noise, trend or variability); ``registered`` the windows the engine registered for the
    round (transit, control, replica; ``x2_study.registered_windows``), or ``None`` when the round
    stopped before they existed. Every round gets a ``cause`` (5.6)."""
    eph = rnd.get("train_ephemeris")
    if not eph:
        return {"has_ephemeris": False, "twin_ok": False, "cause": "twin unavailable"}
    d_star, p_star, t0_star = truth["duration"], truth["period"], truth["t0"]
    depth_star = truth["depth"]
    duration = rnd.get("train_duration_days")
    measured = rnd.get("measurement_status") == "ok"
    dp = float(rnd.get("dp") or 0.0) if measured else 0.0
    n_ref = int(eph["n_ref"])
    out: dict = {
        "has_ephemeris": True,
        "identity": identity_class(float(eph["period"]), p_star, d_star, span),
        "period_ratio": float(eph["period"]) / p_star,
        "measured": measured,
        "windows_registered": registered is not None,
    }
    if registered is not None:
        transit = [w for w in registered if w["kind"] == "transit"]
        centers = [w["t_pred"] + (w["epoch"] - n_ref) * dp for w in transit]
    else:
        transit = []
        centers = predicted_centers(eph, dp, spans)
    truth_c = injected_centers(t0_star, p_star, spans)
    sigma_t = rnd.get("max_timing_sigma_days")
    if centers and truth_c:
        offsets = [min((c - t for t in truth_c), key=abs) for c in centers]
        largest = max(offsets, key=abs)
        out["offset_max_durations"] = abs(largest) / d_star
        out["offset_mean_durations"] = float(np.mean(offsets)) / d_star
        out["offset_mean_days"] = float(np.mean(offsets))
        if _finite(sigma_t) and sigma_t > 0:
            out["offset_max_sigma_t"] = abs(largest) / sigma_t
            out["offset_mean_sigma_t"] = float(np.mean(offsets)) / sigma_t
    if duration and centers and truth_c and hidden_times.size:
        t = np.asarray(hidden_times, float)
        in_true = _near(t, truth_c, d_star / 2.0)
        half_box = duration / 2.0
        n_true = int(in_true.sum())
        if n_true and registered is not None:
            # the engine's own windows: boxes at the measured centers, the transit windows'
            # baseline bands, and the masks of every registered window (transit, control and
            # replica) out to the inner edge of its band
            out["overlap_box"] = float((in_true & _near(t, centers, half_box)).sum() / n_true)
            out["overlap_baseline"] = float((in_true & _windows_band(t, transit)).sum() / n_true)
            masked = _windows_mask(t, registered, "baseline_inner")
            out["outside_masks"] = float((in_true & ~masked).sum() / n_true)
        dfc = deficit(t)
        box_true = _near(t, truth_c, half_box)
        box_pred = _near(t, centers, half_box)
        out["b_true"] = float(dfc[box_true].mean()) if box_true.any() else None
        out["b_pred"] = float(dfc[box_pred].mean()) if box_pred.any() else 0.0
    for key in ("d_train", "d_twin", "d_hidden"):
        v = rnd.get(key)
        out[f"{key}_over_depth"] = v / depth_star if _finite(v) else None
    d_train, d_twin = rnd.get("d_train"), rnd.get("d_twin")
    b_true, b_pred = out.get("b_true"), out.get("b_pred")
    if _finite(d_train) and _finite(b_true) and b_true > 0:
        out["I"] = d_train / b_true
    if _finite(b_true) and b_true > 0 and _finite(b_pred):
        out["L"] = b_pred / b_true
    if _finite(d_twin) and _finite(b_pred) and b_pred > 0:
        out["A"] = d_twin / b_pred
    e_train, e_hidden = rnd.get("e_train"), rnd.get("e_hidden")
    if all(_finite(x) for x in (d_train, d_twin, e_train, e_hidden)):
        out["z_train"] = (d_train - d_twin) / math.sqrt(e_train**2 + e_hidden**2)
    out["twin_ok"] = measured and rnd.get("twin_status") == "ok" and _finite(d_twin)
    out["fail"] = measurement_fail(rnd)
    out["cause"] = cause(out)
    return out


MIN_SNR = 5.0  # the plan's holdout_by_year.min_snr in the study's configuration (checked there)


def measurement_fail(rnd: dict, min_snr: float = MIN_SNR) -> bool:
    """5.7's FAIL: the FAIL rule (``holdout.fail_rule``) on the round's measurement, the capacity
    decisions not enforced (as ``calibration_measurement`` records them)."""
    from refute.packs.tess.holdout import fail_rule

    if rnd.get("measurement_status") != "ok":
        return False
    values = [rnd.get(k) for k in ("s_meas", "d_train", "e_train", "d_hidden", "e_hidden")]
    if not all(_finite(v) for v in values):
        return False
    s_meas, d_train, e_train, d_hidden, e_hidden = values
    return fail_rule(s_meas, min_snr, d_train, e_train, d_hidden, e_hidden)[0] == "FAIL"


def injected_deficit(truth: dict):
    """``1 - signal_model`` of the injected planet (no noise, trend or variability)."""
    from refute.packs.tess import synthetic

    spec = synthetic.SignalSpec(
        period=truth["period"],
        t0=truth["t0"],
        depth=truth["depth"],
        duration=truth["duration"],
        ingress_fraction=truth["ingress_fraction"],
    )
    return lambda t: 1.0 - synthetic.signal_model(np.asarray(t, float), spec)


def cause(g: dict) -> str:
    """5.6, in order: twin unavailable; wrong candidate; the factor of largest reduction; none."""
    if not g.get("has_ephemeris") or not g.get("twin_ok"):
        return "twin unavailable"
    if g["identity"] != "same":
        return "wrong candidate"
    reductions = {}
    i, lo, a = g.get("I"), g.get("L"), g.get("A")
    if _finite(i) and i > 1.0 / REDUCTION:
        reductions["inflated train depth"] = math.log(i)
    if _finite(lo):
        if lo <= 0:
            reductions["imprecise extrapolation"] = math.inf
        elif lo < REDUCTION:
            reductions["imprecise extrapolation"] = -math.log(lo)
    if _finite(a):  # A exists only with b_pred > 0, so never beside a complete loss of placement
        if a <= 0:
            reductions["attenuation in the processing"] = math.inf
        elif a < REDUCTION:
            reductions["attenuation in the processing"] = -math.log(a)
    if not reductions:
        return "none"
    # a tie goes to the first in this order: inflated, extrapolation, processing
    return max(reductions.items(), key=lambda kv: kv[1])[0]


# --- X2-B (section 6) ------------------------------------------------------------------------


def _sd(values) -> float:
    v = np.asarray(values, float)
    return float(np.std(v, ddof=1)) if v.size >= 2 else math.nan


def _mad(values) -> float:
    v = np.asarray(values, float)
    return float(MAD_SCALE * np.median(np.abs(v - np.median(v)))) if v.size else math.nan


def case_year_stats(rows: list[dict]) -> dict:
    """``rows``: one per realization of a case-year, ``{d_hidden, d_twin, e_hidden, e_pred_1,
    e_pred_2, measured, twin_ok}``. Every measured realization with its twin counts."""
    use = [
        r
        for r in rows
        if r.get("measured")
        and r.get("twin_ok")
        and all(_finite(r.get(k)) for k in ("d_hidden", "d_twin"))
    ]
    out = {"realizations": len(rows), "measured": len(use)}
    if len(use) < MIN_REALIZATIONS:
        out["excluded"] = True
        return out
    resid = [r["d_hidden"] - r["d_twin"] for r in use]
    out.update(
        excluded=False,
        sigma_meas_sd=_sd(resid),
        sigma_meas_mad=_mad(resid),
        sigma_tot=_sd([r["d_hidden"] for r in use]),
        sigma_sig=_sd([r["d_twin"] for r in use]),
    )
    for name, key in (("rho_1", "e_pred_1"), ("rho_2", "e_pred_2"), ("rho_h", "e_hidden")):
        vals = [r[key] for r in use if _finite(r.get(key))]
        med = float(np.median(vals)) if vals else math.nan
        out[f"{name}_sd"] = med / out["sigma_meas_sd"] if out["sigma_meas_sd"] > 0 else math.nan
        out[f"{name}_mad"] = med / out["sigma_meas_mad"] if out["sigma_meas_mad"] > 0 else math.nan
    return out


def boot_seed() -> int:
    return int.from_bytes(hashlib.sha256(BOOT_SEED_TEXT.encode()).digest()[:8], "big")


def cell_interval(per_case: dict[str, list[float]], n_boot: int = N_BOOT, seed: int | None = None):
    """The median over the case-years and its 95% interval by a cluster bootstrap over the cases
    (all of a case's years together). ``per_case``: case -> its case-years' finite values."""
    cases = [c for c, v in per_case.items() if v]
    if len(cases) < MIN_CASES:
        return {"cases": len(cases), "value": None, "lo": None, "hi": None}
    values = [x for c in cases for x in per_case[c]]
    rng = np.random.default_rng(boot_seed() if seed is None else seed)
    meds = []
    for _ in range(n_boot):
        pick = rng.integers(0, len(cases), len(cases))
        meds.append(float(np.median([x for k in pick for x in per_case[cases[k]]])))
    lo, hi = np.quantile(meds, [0.025, 0.975])
    return {
        "cases": len(cases),
        "value": float(np.median(values)),
        "lo": float(lo),
        "hi": float(hi),
    }


def verdict(lo, hi, design: float) -> str:
    """6: with ``tau``: calibrated or conservative as designed, overestimated, underestimated, not
    determined."""
    if lo is None or hi is None:
        return "not determined"
    if lo >= 1.0 - TAU and hi <= (1.0 + TAU) * design:
        return "calibrated or conservative as designed"
    if lo > (1.0 + TAU) * design:
        return "overestimated"
    if hi < 1.0 - TAU:
        return "underestimated"
    return "not determined"


def cell_verdict(sd_interval: dict, mad_interval: dict, design: float) -> dict:
    """The SD decides; the MAD checks; a disagreement makes the verdict not determined."""
    v_sd = verdict(sd_interval["lo"], sd_interval["hi"], design)
    v_mad = verdict(mad_interval["lo"], mad_interval["hi"], design)
    return {
        "sd": v_sd,
        "mad": v_mad,
        "verdict": v_sd if v_sd == v_mad else "not determined",
    }


def class_counts(geoms: list[dict]) -> dict:
    """Counts of the causes over all rounds, over those with ``Z_train >= 3`` and over the FAIL
    rounds, each with its denominator (5.7)."""
    all_c = Counter(g["cause"] for g in geoms)
    z3 = Counter(g["cause"] for g in geoms if _finite(g.get("z_train")) and g["z_train"] >= 3.0)
    fail = Counter(g["cause"] for g in geoms if g.get("fail"))
    return {
        "all": {"n": sum(all_c.values()), "counts": dict(sorted(all_c.items()))},
        "z_train_ge_3": {"n": sum(z3.values()), "counts": dict(sorted(z3.items()))},
        "fail": {"n": sum(fail.values()), "counts": dict(sorted(fail.items()))},
    }


def identity_stability(geoms_by_realization: list[dict]) -> dict:
    """Per case-year (5.7): how often the identity differs from the most frequent one, and the
    scatter of the mean offset."""
    ids = [g.get("identity") for g in geoms_by_realization if g.get("has_ephemeris")]
    offs = [
        g["offset_mean_days"] for g in geoms_by_realization if _finite(g.get("offset_mean_days"))
    ]
    if not ids:
        return {"with_ephemeris": 0}
    mode, n_mode = Counter(ids).most_common(1)[0]
    return {
        "with_ephemeris": len(ids),
        "modal_identity": mode,
        "differs_from_modal": len(ids) - n_mode,
        "offset_mean_sd_days": _sd(offs) if len(offs) >= 2 else None,
        "causes": dict(Counter(g["cause"] for g in geoms_by_realization)),
    }


def group_by(rows, key):
    out = defaultdict(list)
    for r in rows:
        out[key(r)].append(r)
    return out


RATIOS = (("rho_1", "e_pred_1"), ("rho_2", "e_pred_2"), ("rho_h", "e_hidden"))
CAPACITY_REFUSALS = {
    "decision_1": "insufficient_capacity_train",
    "decision_2": "insufficient_capacity_hidden_noise",
}
# the calibration record's fields kept in each row (X2-B and section 7 read them)
ROW_FIELDS = (
    "d_hidden",
    "d_twin",
    "e_hidden",
    "e_pred_1",
    "e_pred_2",
    "d_c",
    "n_pred",
    "threshold",
    "decision_1",
    "decision_2",
    "d_train",
    "e_train",
    "s_meas",
    "measurement_status",
)


def round_rows(record: dict, hidden_times, min_snr: float = MIN_SNR) -> list[dict]:
    """One row per round of a realization's record: its X2-A geometry and cause, and the fields
    X2-B reads. ``hidden_times(case_id, year)``: the case's cadences in that year (no noise)."""
    truth = record["truth"]
    deficit = injected_deficit(truth)
    sectors = record["sectors"]
    span = max(s["t_end"] for s in sectors) - min(s["t_start"] for s in sectors)
    out = []
    for rnd in record["rounds"]:
        y = rnd["hidden_year"]
        spans = [(s["t_start"], s["t_end"]) for s in sectors if s["year"] == y]
        g = round_geometry(
            rnd,
            truth,
            hidden_times(record["case_id"], y),
            spans,
            span,
            deficit,
            record["registered_windows"].get(str(y)),
        )
        g["fail"] = measurement_fail(rnd, min_snr)
        out.append(
            {
                **g,
                "group": record["group"],
                "mechanism": record["mechanism"],
                "n_years": len(record["years"]),
                "case_id": record["case_id"],
                "realization": record["realization"],
                "year": y,
                **{k: rnd.get(k) for k in ROW_FIELDS},
                "m_beta": rnd.get("m_beta"),
            }
        )
    return out


def evaluate(rows: list[dict], m_beta: float) -> dict:
    """Sections 5.7, 6 and the findings' order, from ``round_rows`` over the whole lot. Every row
    counts in X2-A's denominators; X2-B reads every measured realization with its twin, and reports
    the subset ``same`` with ``L >= 0.8`` apart (not deciding)."""
    cells = sorted({r["group"] for r in rows})
    a = {
        "by_cell": {g: class_counts([r for r in rows if r["group"] == g]) for g in cells},
        "by_cell_and_mechanism": {
            f"{g} | {m}": class_counts(rs_)
            for (g, m), rs_ in sorted(
                group_by(rows, lambda r: (r["group"], r["mechanism"])).items()
            )
        },
        "by_cell_and_years": {
            f"{g} | {n} years": class_counts(rs_)
            for (g, n), rs_ in sorted(group_by(rows, lambda r: (r["group"], r["n_years"])).items())
        },
        "case_years": {
            f"{c} | {y}": identity_stability(rs_)
            for (c, y), rs_ in sorted(group_by(rows, lambda r: (r["case_id"], r["year"])).items())
        },
    }
    b, findings = {}, []
    for g in cells:
        cell_rows = [r for r in rows if r["group"] == g]
        by_cy = group_by(cell_rows, lambda r: (r["case_id"], r["year"]))
        stats = {k: case_year_stats(v) for k, v in by_cy.items()}
        subset = {
            k: case_year_stats(
                [
                    r
                    for r in v
                    if r.get("identity") == "same" and _finite(r.get("L")) and r["L"] >= REDUCTION
                ]
            )
            for k, v in by_cy.items()
        }
        entry = {
            "case_years": len(stats),
            "excluded": sum(1 for s in stats.values() if s.get("excluded")),
            "ratios": {},
            "subset_same_and_placed": {},
        }
        for name, _ in RATIOS:
            design = m_beta if name == "rho_1" else 1.0
            ivs = {}
            for scale in ("sd", "mad"):
                per_case = defaultdict(list)
                for (case, _y), s in stats.items():
                    v = s.get(f"{name}_{scale}")
                    if not s.get("excluded") and _finite(v):
                        per_case[case].append(v)
                ivs[scale] = cell_interval(dict(per_case))
            # the intervals and the verdicts under separate keys (X2's results: spreading the
            # verdict over the intervals overwrote them, its keys being `sd` and `mad` too)
            v = cell_verdict(ivs["sd"], ivs["mad"], design)
            entry["ratios"][name] = {
                "design": design,
                "sd_interval": ivs["sd"],
                "mad_interval": ivs["mad"],
                "sd_verdict": v["sd"],
                "mad_verdict": v["mad"],
                "verdict": v["verdict"],
            }
            findings.append((g, name, entry["ratios"][name]["verdict"]))
            sub = defaultdict(list)
            for (case, _y), s in subset.items():
                v = s.get(f"{name}_sd")
                if not s.get("excluded") and _finite(v):
                    sub[case].append(v)
            entry["subset_same_and_placed"][name] = cell_interval(dict(sub))
        entry["case_year_stats"] = {f"{c} | {y}": s for (c, y), s in sorted(stats.items())}
        entry["subset_case_year_stats"] = {f"{c} | {y}": s for (c, y), s in sorted(subset.items())}
        b[g] = entry
    order = {"underestimated": 0, "overestimated": 1, "not determined": 2}
    findings.sort(key=lambda f: (order.get(f[2], 3), f[0], f[1]))
    return {
        "x2a": a,
        "x2b": b,
        "descriptive": descriptive(rows, b),
        "findings": [{"cell": c, "ratio": n, "verdict": v} for c, n, v in findings],
        "rows": rows,
    }


def descriptive(rows: list[dict], x2b: dict) -> dict:
    """Section 7, descriptive only: per cell, the rounds stopped by decision 1 or 2 that would pass
    with the case-year's ``sigma_meas`` (SD) in place of ``e_pred`` (``d_c / sigma_meas`` at least
    the round's threshold), with no claim that this would be better; the case-years' ``rho`` (SD) by
    mechanism and by ``n_pred`` (the case-year's median); the fraction of rounds measured."""
    out = {}
    for g, entry in sorted(x2b.items()):
        stats = entry["case_year_stats"]
        cell_rows = [r for r in rows if r["group"] == g]
        # only the capacity refusals can change with the error; the structural impediments (no
        # predicted window, train replicas below r_min) are counted apart (Codex's third review)
        stopped = {"decision_1": [0, 0], "decision_2": [0, 0]}  # [refused, would pass]
        structural: Counter = Counter()
        for r in cell_rows:
            s = stats.get(f"{r['case_id']} | {r['year']}", {})
            sigma = s.get("sigma_meas_sd")
            for d in stopped:
                value = r.get(d)
                if value is None or value == "pass":
                    continue
                if value != CAPACITY_REFUSALS[d]:
                    structural[f"{d}: {value}"] += 1
                    continue
                stopped[d][0] += 1
                if (
                    not s.get("excluded")
                    and _finite(sigma)
                    and sigma > 0
                    and _finite(r.get("d_c"))
                    and _finite(r.get("threshold"))
                    and r["d_c"] / sigma >= r["threshold"]
                ):
                    stopped[d][1] += 1
        by_mech, by_npred = (
            defaultdict(lambda: defaultdict(list)),
            defaultdict(lambda: defaultdict(list)),
        )
        for (case, year), rs_ in group_by(cell_rows, lambda r: (r["case_id"], r["year"])).items():
            s = stats.get(f"{case} | {year}", {})
            if s.get("excluded"):
                continue
            npred = [r["n_pred"] for r in rs_ if _finite(r.get("n_pred"))]
            for name, _ in RATIOS:
                v = s.get(f"{name}_sd")
                if _finite(v):
                    by_mech[rs_[0]["mechanism"]][name].append(v)
                    if npred:
                        by_npred[int(np.median(npred))][name].append(v)
        measured = sum(1 for r in cell_rows if r.get("measured"))
        out[g] = {
            "stopped_that_would_pass": {
                d: {"refused_by_capacity": v[0], "would_pass_with_sigma_meas": v[1]}
                for d, v in stopped.items()
            },
            "structural_impediments": dict(sorted(structural.items())),
            "rho_by_mechanism": {
                m: {n: float(np.median(v)) for n, v in d.items()}
                for m, d in sorted(by_mech.items())
            },
            "rho_by_n_pred": {
                str(k): {n: float(np.median(v)) for n, v in d.items()}
                for k, d in sorted(by_npred.items())
            },
            "measured": {"x": measured, "n": len(cell_rows)},
        }
    return out
