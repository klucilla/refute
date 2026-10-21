"""The R_min study's diagnosis (option B), exactly as declared in
docs/validation/v0.2.1/reopen/rmin-study/diagnosis/DECLARATION.md (revision 3, commit 254f447):
Q1 gates, Q2 interruptions, Q3 capacity, Q5 b and s, Q8 safety and utility, from the recorded
fields only, with the study's code (2e4ff99). No light curve is built and the engine is not run.

Run with run-with-study-code.ps1. Usage:
  python diagnosis.py <study run folder> <record-digests.json> <bs-choice folder>
                      <bs-choice-evaluation.json> <out folder (new)>
"""

import hashlib
import json
import math
import re
import statistics
import sys
from collections import Counter, defaultdict
from pathlib import Path
from statistics import NormalDist

import numpy as np
from scipy.stats import beta, pearsonr, spearmanr

WT = Path("C:/Projetos/refute/.cache/wt-v021")
sys.path.insert(0, str(WT / "docs/validation/v0.2.1/population"))
import rmin_evaluate as ev  # noqa: E402
import rmin_study as rs  # noqa: E402

from refute.packs.tess.holdout import capacity_threshold  # noqa: E402

pv2 = rs.pv2
MIN_SNR = 5.0
LEVEL = 1.0 - 0.05 / 5
SCENARIOS = ("constant", "disappearing", "weakened")
TIMING = "train-only timing uncertainty in the hidden year"
KIND = re.compile(r"^[A-Za-z_\- ]+")
TIMING_TEXT = re.compile(r"\(([0-9.]+) h\) exceeds 1 transit duration\(s\) \(([0-9.]+) h\)")
GATES = ("G0", "G1", "G2", "G3", "G4", "G5", "G6")
SNR_BINS = ((0, 5), (5, 10), (10, 20), (20, 40), (40, math.inf))
RATIO_BINS = ((1, 1.5), (1.5, 2), (2, 3), (3, 5), (5, 10), (10, math.inf))
QS = (0.05, 0.25, 0.5, 0.75, 0.95)


def kind(reason) -> str:
    """The reason kind of ../study/scripts/summarize.py (one reason, not a combination)."""
    text = str(reason)
    m = KIND.match(text.strip())
    return ((m.group(0) if m else text).strip().rstrip("-_ ")) or text


def finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def labels(target: str) -> dict:
    case_id = target.split("/", 1)[1]
    cls, band, noise, index = case_id.split("-")
    index = int(index)
    mechanism = pv2._planet_mechanism(index)
    out = {"band": band, "noise": noise, "index": index, "mechanism": mechanism}
    if mechanism == "few_train":
        extra = pv2._few_train_extra(index - 150, 50)
        out["few_train"] = (
            f"train_transits={extra['train_transits']},distance={extra['distance_years']}"
        )
    return out


def gate_of(d: dict, rec_round: dict) -> tuple[int, str]:
    """(gate index, subcategory) of a derived round, in derive_round's order (declaration, 3)."""
    reason = d["reason"]
    if rec_round["stage"] == "before_capacity":
        return 0, kind(reason)
    if reason == "train_replicas_below_r_min":
        return 1, "train_replicas_below_r_min"
    if reason == "insufficient_capacity_train":
        return 2, "insufficient_capacity_train"
    if reason == "hidden_noise_undetermined" and d["decision_2"] is None:
        if rec_round["stage"] == "hidden_noise":
            return 3, "hidden_noise_stage"
        if rec_round["hidden_noise_undetermined"]:
            return 3, "hidden_noise_undetermined_flag"
        return 3, "hidden_replicas_below_r"
    if reason == "insufficient_capacity_hidden_noise":
        return 4, "insufficient_capacity_hidden_noise"
    if d["decision_1"] == "pass" and d["decision_2"] == "pass":
        if d["status"] == "INCONCLUSIVE" and reason not in (
            "not_detected_not_inconsistent",
            "non_finite_statistic",
        ):
            return 5, str(reason)
        if d["status"] == "PASS":
            return 6, "PASS"
        if d["status"] == "FAIL":
            return 6, "FAIL"
        return 6, f"INCONCLUSIVE {reason}"
    return -1, f"unclassified {reason}"


def frac(x: int, n: int):
    return {"x": x, "n": n, "fraction": (x / n) if n else None}


def cp_upper(x: int, n: int):
    if n == 0:
        return None
    return 1.0 if x >= n else float(beta.ppf(LEVEL, x + 1, n - x))


def cp_lower(x: int, n: int):
    if n == 0:
        return None
    return 0.0 if x <= 0 else float(beta.ppf(1.0 - LEVEL, x, n - x + 1))


def quantiles(values) -> dict:
    v = [x for x in values if finite(x)]
    out = {"valid": len(v), "undefined": len(values) - len(v)}
    if v:
        out.update({f"q{int(q * 100)}": float(np.quantile(v, q)) for q in QS})
    return out


def bin_of(x, bins) -> str:
    for lo, hi in bins:
        if lo < x <= hi:
            return f"({lo}, {hi}]"
    return "outside"


def check_digests(run_dir: Path, digests_file: Path, data: dict) -> None:
    committed = json.loads(digests_file.read_text(encoding="utf-8"))
    if committed != data["files"]:
        raise SystemExit("the records differ from the committed digests: the analysis stops")


# --- Q1, Q2, Q3, Q8 on the study lot -----------------------------------------------------------


def study_tables(records: list[dict], pairs: dict) -> dict:
    out = {"Q1": {}, "Q2": {}, "Q3": {}, "Q8": {}}
    for r_min in ev.R_VALUES:
        pair = pairs[str(r_min)]
        b, s = pair["b"], pair["s"]
        q1 = defaultdict(
            lambda: {
                "rounds": 0,
                "reach": Counter(),
                "stopped": Counter(),
                "sub": defaultdict(Counter),
                "targets_stopped_at": Counter(),
                "furthest": Counter(),
                "last_round_gate": Counter(),
                "g3_cross": Counter(),
                "targets": 0,
            }
        )
        q2_rounds = defaultdict(Counter)  # cut -> "Gk:kind" counts of INCONCLUSIVE rounds
        q2_round_totals = Counter()
        q2_targets = defaultdict(Counter)  # target-level cut -> T-a combination counts
        q2_target_totals = Counter()
        q2_snr = defaultdict(Counter)  # group|scenario -> train-SNR bin (INCONCLUSIVE rounds)
        q2_timing = defaultdict(Counter)  # group|scenario -> ratio bin
        q3 = defaultdict(lambda: {"G2": [], "G4": []})
        q3_per_target = defaultdict(Counter)
        q8 = defaultdict(Counter)
        q8_qualified = defaultdict(Counter)
        for rec in records:
            lab = labels(rec["target"])
            g, sc = rec["group"], rec["scenario"]
            cell = f"{g}|{sc}"
            n_years = len(rec["years"])
            tcut = f"{g}|{sc}|{lab['band']}|{lab['mechanism']}|years={n_years}"
            if "few_train" in lab:
                tcut += f"|{lab['few_train']}"
            o = ev.target_outcomes(rec, r_min, b, s, MIN_SNR)
            t = q1[cell]
            t["targets"] += 1
            furthest = -1
            stopped_here = set()
            inconclusive_kinds = set()
            g2g4 = Counter()
            for d in o["rounds"]:
                rr = d["record"]
                gi, sub = gate_of(d, rr)
                t["rounds"] += 1
                for k in range(0, gi + 1):
                    t["reach"][GATES[k]] += 1
                gname = GATES[gi] if gi >= 0 else "unclassified"
                t["stopped"][gname] += 1
                t["sub"][gname][sub] += 1
                stopped_here.add(gname)
                furthest = max(furthest, gi)
                if gi == 3:
                    reps = rr.get("hidden_n_rep") or []
                    below = not ev.replicas_enough(reps, r_min) if reps else True
                    t["g3_cross"][
                        f"flag={rr.get('hidden_noise_undetermined')}|below_r={below}"
                    ] += 1
                if d["status"] == "INCONCLUSIVE":
                    key = f"{gname}:{sub}"
                    q2_rounds[tcut][key] += 1
                    inconclusive_kinds.add(kind(d["reason"]))
                    dt, et = rr.get("d_train"), rr.get("e_train")
                    if finite(dt) and finite(et) and et > 0:
                        q2_snr[cell][bin_of(dt / et, SNR_BINS)] += 1
                    else:
                        q2_snr[cell][f"not recorded ({gname})"] += 1
                    if gi == 0 and kind(d["reason"]) == TIMING:
                        m = TIMING_TEXT.search(str(d["reason"]))
                        if not m:
                            q2_timing[cell]["unparsed"] += 1
                        else:
                            sig, t14 = float(m.group(1)), float(m.group(2))
                            if t14 == 0:
                                q2_timing[cell]["T14 printed 0"] += 1
                            elif sig / t14 <= 1:
                                q2_timing[cell]["<= 1 (rounding)"] += 1
                            else:
                                q2_timing[cell][bin_of(sig / t14, RATIO_BINS)] += 1
                q2_round_totals[tcut] += 1
                if gi in (2, 4):
                    s_pred = rr.get("s_pred_1" if gi == 2 else "s_pred_2")
                    thr = capacity_threshold(MIN_SNR, b, s, rr["n_years"])
                    # per scenario, as the declaration's default (R x group x scenario); the
                    # first run pooled the scenarios here (Codex's opinion on the delivery)
                    q3[f"{g}|{sc}|{lab['band']}|{lab['mechanism']}"][GATES[gi]].append(
                        {
                            "s_pred": s_pred,
                            "threshold": thr,
                            "d_train": rr.get("d_train"),
                            "e_train": rr.get("e_train"),
                            "n_years": rr["n_years"],
                        }
                    )
                    g2g4[GATES[gi]] += 1
            for gname in stopped_here:
                t["targets_stopped_at"][gname] += 1
            t["furthest"][GATES[furthest] if furthest >= 0 else "unclassified"] += 1
            last = o["last_round"]
            if last is not None:
                lgi, lsub = gate_of(last, last["record"])
                t["last_round_gate"][f"{GATES[lgi] if lgi >= 0 else 'unclassified'}:{lsub}"] += 1
            if o["status"] == "INCONCLUSIVE":
                q2_targets[tcut]["+".join(sorted(inconclusive_kinds))] += 1
            q2_target_totals[tcut] += 1
            q3_per_target[cell][f"G2={g2g4['G2']},G4={g2g4['G4']}"] += 1
            # Q8
            c8 = q8[cell]
            c8["total"] += 1
            c8["eligible"] += o["eligible"]
            decided = o["status"] in ("PASS", "FAIL")
            c8["decided"] += decided
            c8[o["status"]] += 1
            if o["eligible"]:
                c8[f"eligible_{o['status']}"] += 1
            if sc == "disappearing" and ev._passes_decisions(last):
                q8_qualified[cell]["n"] += 1
                q8_qualified[cell][last["status"] if last else "none"] += 1
                q8_qualified[cell][f"target_{o['status']}"] += 1
        # assemble Q1
        out["Q1"][str(r_min)] = {
            cell: {
                "targets": t["targets"],
                "rounds": t["rounds"],
                "gates": {
                    gname: {
                        "reach": frac(t["reach"][gname], t["rounds"]),
                        "stopped_of_population": frac(t["stopped"][gname], t["rounds"]),
                        "stopped_of_reach": frac(t["stopped"][gname], t["reach"][gname]),
                        "subcategories": dict(t["sub"][gname].most_common()),
                        "targets_with_a_round_stopped_here_T_b": frac(
                            t["targets_stopped_at"][gname], t["targets"]
                        ),
                    }
                    for gname in GATES
                },
                "unclassified_rounds": t["stopped"]["unclassified"],
                "furthest_gate_per_target": dict(t["furthest"]),
                "last_round_gate": dict(t["last_round_gate"].most_common()),
                "g3_cross_table": dict(t["g3_cross"]),
            }
            for cell, t in sorted(q1.items())
        }
        out["Q2"][str(r_min)] = {
            "inconclusive_rounds_by_cut": {
                cut: {"rounds": q2_round_totals[cut], "by_gate_kind": dict(c.most_common())}
                for cut, c in sorted(q2_rounds.items())
            },
            "inconclusive_targets_T_a_by_cut": {
                cut: {"targets": q2_target_totals[cut], "by_combination": dict(c.most_common())}
                for cut, c in sorted(q2_targets.items())
            },
            "inconclusive_rounds_by_train_snr": {k: dict(v) for k, v in sorted(q2_snr.items())},
            "timing_rounds_by_rounded_ratio": {k: dict(v) for k, v in sorted(q2_timing.items())},
        }
        q3_out = {}
        for cut, gates in sorted(q3.items()):
            entry = {}
            for gname, rows in gates.items():
                undefined = [r for r in rows if not finite(r["s_pred"])]
                below = [r for r in rows if finite(r["s_pred"]) and r["s_pred"] < MIN_SNR]
                margin = [
                    r
                    for r in rows
                    if finite(r["s_pred"]) and MIN_SNR <= r["s_pred"] < r["threshold"]
                ]
                other = len(rows) - len(undefined) - len(below) - len(margin)
                valid_ratio = [
                    r
                    for r in rows
                    if finite(r["d_train"])
                    and finite(r["e_train"])
                    and r["e_train"] > 0
                    and finite(r["s_pred"])
                    and r["s_pred"] > 0
                ]
                dc_ratio = [
                    (r["d_train"] - r["e_train"]) / r["d_train"]
                    for r in valid_ratio
                    if r["d_train"] != 0
                ]
                ep_ratio = [
                    ((r["d_train"] - r["e_train"]) / r["s_pred"]) / r["e_train"]
                    for r in valid_ratio
                ]
                entry[gname] = {
                    "rounds": len(rows),
                    "undefined": len(undefined),
                    "below_min_snr": len(below),
                    "in_margin_min_snr_to_threshold": len(margin),
                    "not_in_any_category": other,
                    "s_pred_quantiles": quantiles([r["s_pred"] for r in rows]),
                    "ratio_valid": len(valid_ratio),
                    "ratio_invalid": len(rows) - len(valid_ratio),
                    "d_c_over_d_train": quantiles(dc_ratio),
                    "e_pred_over_e_train": quantiles(ep_ratio),
                }
            q3_out[cut] = entry
        years_seen = sorted(
            {rr["n_years"] for rec in records for rr in rec["rounds"] if rr.get("n_years")}
        )
        out["Q3"][str(r_min)] = {
            "pair": pair,
            "threshold_parts": {
                str(n): {
                    "min_snr": MIN_SNR,
                    "minus_b": -b,
                    "z_s": NormalDist().inv_cdf(1.0 - 0.005 / n) * s,
                    "threshold": capacity_threshold(MIN_SNR, b, s, n),
                }
                for n in (years_seen or [2, 3, 4])
            },
            "by_group_scenario_band_mechanism": q3_out,
            "per_target_counts_of_rounds_at_G2_G4": {
                k: dict(v) for k, v in sorted(q3_per_target.items())
            },
        }
        q8_out = {}
        for cell, c in sorted(q8.items()):
            sc = cell.split("|")[1]
            entry = {
                "total": c["total"],
                "eligible": c["eligible"],
                "decided": c["decided"],
                "PASS": c["PASS"],
                "FAIL": c["FAIL"],
                "INCONCLUSIVE": c["INCONCLUSIVE"],
                "decided_over_total": frac(c["decided"], c["total"]),
                "eligible_over_total": frac(c["eligible"], c["total"]),
            }
            if sc in ("constant", "disappearing"):
                err = c["FAIL"] if sc == "constant" else c["PASS"]
                err_el = c["eligible_FAIL"] if sc == "constant" else c["eligible_PASS"]
                entry["error_label"] = (
                    "FAIL (false FAIL)" if sc == "constant" else "PASS (false PASS)"
                )
                entry["error_over_eligible"] = frac(err_el, c["eligible"])
                entry["error_over_decided"] = frac(err, c["decided"])
                entry["error_over_total"] = frac(err, c["total"])
                entry["error_upper_over_eligible"] = cp_upper(err_el, c["eligible"])
                entry["error_upper_over_decided"] = cp_upper(err, c["decided"])
                entry["error_upper_over_total"] = cp_upper(err, c["total"])
            if sc == "disappearing":
                entry["fail_correct_over_eligible"] = frac(c["eligible_FAIL"], c["eligible"])
                entry["fail_correct_over_decided"] = frac(c["FAIL"], c["decided"])
                entry["fail_correct_over_total"] = frac(c["FAIL"], c["total"])
                entry["fail_lower_over_decided"] = cp_lower(c["FAIL"], c["decided"])
                entry["evaluation_qualified_set"] = dict(q8_qualified[cell])
            if sc == "weakened":
                entry["note"] = "PASS and FAIL fractions without an error label (Q6)"
                entry["pass_over_decided"] = frac(c["PASS"], c["decided"])
                entry["fail_over_decided"] = frac(c["FAIL"], c["decided"])
            q8_out[cell] = entry
        out["Q8"][str(r_min)] = q8_out
    return out


# --- Q5 on bs-choice ---------------------------------------------------------------------------


def anova_icc(groups: list[list[float]]) -> dict:
    groups = [g for g in groups if g]
    a = len(groups)
    n_total = sum(len(g) for g in groups)
    if a < 2 or n_total <= a:
        return {"clusters": a, "rounds": n_total, "icc": None, "note": "not computable"}
    grand = sum(sum(g) for g in groups) / n_total
    ssb = sum(len(g) * (statistics.fmean(g) - grand) ** 2 for g in groups)
    ssw = sum(sum((x - statistics.fmean(g)) ** 2 for x in g) for g in groups)
    msb, msw = ssb / (a - 1), ssw / (n_total - a)
    n0 = (n_total - sum(len(g) ** 2 for g in groups) / n_total) / (a - 1)
    var_between = (msb - msw) / n0
    icc = var_between / (var_between + msw) if (var_between + msw) != 0 else None
    return {
        "clusters": a,
        "rounds": n_total,
        "n0": n0,
        "ms_between": msb,
        "ms_within": msw,
        "var_between": var_between,
        "var_within": msw,
        "icc": icc,
        "negative_icc": icc is not None and icc < 0,
    }


def residuals_of(records, r_min) -> list[tuple[dict, dict, float]]:
    rows = [(rec, r) for rec, r in ev._k_set(records, 2, MIN_SNR) if ev.meets_r(r, r_min)]
    return [(rec, r, r["s_meas"] - r["s_pred_2"]) for rec, r in rows]


def mad_s(values) -> float:
    v = np.asarray(values, dtype=float)
    return float(1.4826 * np.median(np.abs(v - np.median(v))))


def bs_tables(bs_records: list[dict], pairs: dict) -> tuple[dict, dict]:
    rng = np.random.default_rng(20261021)  # consumed in order: for each R, B1 then B2
    z2 = NormalDist().inv_cdf(1.0 - 0.005 / 2)
    out, resid_out = {}, {}
    for r_min in ev.R_VALUES:
        rows = residuals_of(bs_records, r_min)
        by_target = defaultdict(list)
        for rec, r, x in rows:
            by_target[rec["target"]].append((r["hidden_year"], x, rec))
        res = [x for _, _, x in rows]
        b, s = float(np.median(res)), mad_s(res)
        if pairs[str(r_min)] and (
            abs(b - pairs[str(r_min)]["b"]) > 1e-12 or abs(s - pairs[str(r_min)]["s"]) > 1e-12
        ):
            raise SystemExit(f"R {r_min}: the residuals do not give the committed pair")
        two = {t: sorted(v) for t, v in by_target.items() if len(v) == 2}
        earlier = [v[0][1] for v in two.values()]
        later = [v[1][1] for v in two.values()]
        regimes = defaultdict(list)
        table = []
        for t, v in sorted(by_target.items()):
            rec = v[0][2]
            lab = labels(t)
            regime = {
                "group": rec["group"],
                "band": lab["band"],
                "mechanism": lab["mechanism"],
                "years": len(rec["years"]),
            }
            for key, value in regime.items():
                regimes[f"{key}={value}"].extend(x for _, x, _ in v)
            table.append(
                {
                    "target": t,
                    **regime,
                    "residuals": {str(y): x for y, x, _ in sorted(v)},
                    "two_round_difference": (sorted(v)[1][1] - sorted(v)[0][1])
                    if len(v) == 2
                    else None,
                }
            )
        all_regimes = {}
        for rec in bs_records:
            lab = labels(rec["target"])
            for key, value in (
                ("group", rec["group"]),
                ("band", lab["band"]),
                ("mechanism", lab["mechanism"]),
                ("years", len(rec["years"])),
            ):
                all_regimes.setdefault(f"{key}={value}", None)
        regime_out = {
            name: (
                {
                    "rounds": len(regimes[name]),
                    "median": float(np.median(regimes[name])),
                    "s": mad_s(regimes[name]),
                }
                if regimes.get(name)
                else {"rounds": 0}
            )
            for name in sorted(all_regimes)
        }

        def boot_b1():
            # called at once, in the same iteration of the loop over R (lint comments only)
            keys = sorted(by_target)  # noqa: B023
            draws = []
            for _ in range(2000):
                pick = rng.integers(0, len(keys), size=len(keys))
                xs = [x for i in pick for _, x, _ in by_target[keys[i]]]  # noqa: B023
                bb, ss = float(np.median(xs)), mad_s(xs)
                draws.append((bb, ss, MIN_SNR - bb + z2 * ss))
            return draws

        def boot_b2():
            draws, empty = [], 0
            n = len(bs_records)
            for _ in range(2000):
                pick = rng.integers(0, n, size=n)
                sample = [bs_records[i] for i in pick]
                xs = [x for _, _, x in residuals_of(sample, r_min)]  # noqa: B023
                if not xs:
                    empty += 1
                    continue
                bb, ss = float(np.median(xs)), mad_s(xs)
                draws.append((bb, ss, MIN_SNR - bb + z2 * ss))
            return draws, empty

        def pts(draws):
            arr = np.asarray(draws)
            return {
                name: {
                    "p2_5": float(np.quantile(arr[:, i], 0.025)),
                    "p97_5": float(np.quantile(arr[:, i], 0.975)),
                }
                for i, name in enumerate(("b", "s", "threshold_2_years"))
            }

        b1 = boot_b1()
        b2, b2_empty = boot_b2()
        corr = {}
        if len(two) >= 3:
            corr = {
                "pearson": float(pearsonr(earlier, later)[0]),
                "spearman": float(spearmanr(earlier, later)[0]),
            }
        out[str(r_min)] = {
            "rounds": len(rows),
            "targets": len(by_target),
            "targets_with_one_round": sum(len(v) == 1 for v in by_target.values()),
            "targets_with_two_rounds": len(two),
            "median_b": b,
            "s": s,
            "sd": float(np.std(res, ddof=1)) if len(res) > 1 else None,
            "iqr": float(np.quantile(res, 0.75) - np.quantile(res, 0.25)),
            "quantiles": {f"q{int(q * 100)}": float(np.quantile(res, q)) for q in QS},
            "beyond_3s": int(sum(abs(x - b) > 3 * s for x in res)),
            "anova": anova_icc([[x for _, x, _ in v] for v in by_target.values()]),
            "two_round_correlation": corr,
            "regimes": regime_out,
            "bootstrap_B1_selected_targets": {"draws": len(b1), **pts(b1)},
            "bootstrap_B2_all_targets": {"draws": len(b2), "empty_draws": b2_empty, **pts(b2)},
        }
        resid_out[str(r_min)] = {
            "per_target": table,
            "sorted_residuals": sorted(res),
            "sorted_residuals_per_regime": {k: sorted(v) for k, v in sorted(regimes.items())},
        }
    return out, resid_out


def main() -> int:
    run_dir, digests, bs_dir, bs_eval, out = (Path(a) for a in sys.argv[1:6])
    out.mkdir(parents=True, exist_ok=False)
    data = rs.load_lot(run_dir)
    check_digests(run_dir, digests, data)
    plan = rs.v3._plan()
    configuration = rs.v3.STATE["identity"]
    committed = json.loads(bs_eval.read_text(encoding="utf-8"))
    again = rs.evaluate_bs_choice(bs_dir, plan.gauntlet.holdout_by_year.min_snr, configuration)
    if rs._canonical(again) != rs._canonical(committed):
        raise SystemExit("bs-choice does not give its committed evaluation again")
    if plan.gauntlet.holdout_by_year.min_snr != MIN_SNR:
        raise SystemExit("min_snr is not 5")
    pairs = committed["pairs"]
    tables = study_tables(data["records"], pairs)
    bs_records = rs.load_lot(bs_dir)["records"]
    q5, q5_resid = bs_tables(bs_records, pairs)
    files = {
        "gates.json": tables["Q1"],
        "interruptions.json": tables["Q2"],
        "capacity.json": tables["Q3"],
        "safety-utility.json": tables["Q8"],
        "bs.json": q5,
        "bs-residuals.json": q5_resid,
    }
    for name, content in files.items():
        (out / name).write_text(
            json.dumps(content, indent=1) + "\n", encoding="utf-8", newline="\n"
        )
        print(name, hashlib.sha256((out / name).read_bytes()).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
