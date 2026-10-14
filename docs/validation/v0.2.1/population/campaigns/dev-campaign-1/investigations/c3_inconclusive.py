"""Read-only investigation of the C3 white INCONCLUSIVE planets (M3, slot 1).

English version of the script behind the maintainer's Portuguese record
dev1-c3-inconclusive.md, version 2 (2026-10-14): the same selection, the same calculation, the
same formatting of the numbers; the text is that of version 2, translated, plus a dated errata.
The measurable white planets of mechanisms two_years and few_train whose verdict is
INCONCLUSIVE.

Inputs: ../../../manifest-dev.json and the M3 slot 1 result records, kept out of git and
listed in ../asset-SHA256SUMS (default: .cache/population/campaign-dev-1/runs). Outputs:
c3-inconclusive-investigation.md (default: the campaign folder) and c3-rounds.json (default:
this folder). Never replaces an existing file.

Per holdout round (one hidden year), from the record:
- the tool's train-only timing uncertainty at the farthest hidden transit (max_timing_sigma),
  its ratio to the train duration (the rule: INCONCLUSIVE above 1), the train ephemeris
  (t_ref error, period error, reduced chi-square, number of transit times N) and the lever
  arm m (epochs from the reference epoch to the farthest hidden transit), approximated from
  sigma_max^2 = t_ref_err^2 + m^2 period_err^2 (reported only; see the errata);
- the per-transit precision the tool's ephemeris implies: sigma_tc_tool = t_ref_err * sqrt(N)
  (equal weights; includes the tool's chi-square inflation).

Carter approximation of the per-transit precision, Carter, Yee, Eastman, Gaudi and Winn 2008
(arXiv:0805.0238, DOI 10.1086/592321, eq. 43; uniform source, white noise, uniform sampling):
  Q = sqrt(Gamma T) delta / sigma,  theta = tau / T,  sigma_tc = Q^-1 T sqrt(theta / 2),
with T the duration between the midpoints of ingress and egress, tau the ingress duration,
Gamma the sampling rate and sigma the per-point noise. Two versions:
- "train": delta, T14 and sigma from the tool's train candidate (sigma from its depth error
  and in-transit cadences); tau = injected ingress fraction x T14 (the box model has no
  ingress: diagnosis only); T = T14 - tau;
- "truth": the injected depth, duration and ingress, sigma = 600 ppm (diagnosis only).
The prediction scales the tool's: sigma_pred_approx = sigma_pred_tool * sigma_tc_approx /
sigma_tc_tool (same epochs and lever arm; chi-square 1). The counts use this scaled
prediction, not the lever arm. The generation parameters are used for the diagnosis only,
never as a proposed input to the tool.

Usage: python c3_inconclusive.py [--records DIR] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import collections
import json
import math
from pathlib import Path

from scipy.stats import beta

HERE = Path(__file__).resolve().parent


def repo_root() -> Path:
    for p in HERE.parents:
        if (p / "pyproject.toml").is_file() and (p / "ROADMAP.md").is_file():
            return p
    raise SystemExit("repository root not found")


REPO = repo_root()
MANIFEST = REPO / "docs" / "validation" / "v0.2.1" / "population" / "manifest-dev.json"
DEFAULT_RUNS = REPO / ".cache" / "population" / "campaign-dev-1" / "runs"
MD_NAME = "c3-inconclusive-investigation.md"
JSON_NAME = "c3-rounds.json"
PT_RECORD = "dev1-c3-inconclusive.md"
PT_SHA256 = "3c1b2732775cdbe0b7c655af6f55521fa75362a00dbaa15f734ab77bf00dda5b"
PT_V1_SHA256 = "38372427b10c7c36802f24ce9607ac7979345993fefb0a93378d36c74503899e"
CADENCE = 2.0 / 1440.0
SIGMA_WHITE = 600e-6
GOOD_EPOCH = 0.1  # diagnostic threshold: train epoch precision below 0.1 duration
KIND_I = "(i) uncertainty below one duration by the Carter approximation"
KIND_III = "(iii) above one duration by the approximation, train epoch below 0.1 duration"
KIND_II = "(ii) above one duration by the approximation, train epoch at 0.1 duration or more"
# Text added in translation (not in the Portuguese record) sits between these markers, so that
# check_numbers.py can compare the numbers of the two versions; the markers do not render.
ADD, END = "<!-- translation-note -->", "<!-- /translation-note -->"


def f(v):
    if isinstance(v, dict) and "dec" in v and "f64" in v:
        return float(v["dec"])
    return v


def carter(delta: float, t14: float, tau: float, sigma: float) -> float:
    t = t14 - tau
    q = math.sqrt(t / CADENCE) * delta / sigma
    return t * math.sqrt((tau / t) / 2.0) / q


def cp_upper(k: int, n: int) -> float:
    return 1.0 if k >= n else float(beta.ppf(0.95, k + 1, n - k))


def fmt(v, nd=3):
    return "-" if v is None else (f"{v:.{nd}g}" if isinstance(v, float) else str(v))


def med(vals):
    vals = sorted(v for v in vals if v is not None)
    return vals[len(vals) // 2] if vals else None


ERRATA = [
    ADD,
    "",
    "## Errata (2026-10-14)",
    "",
    "Version 2 is translated below without changes; this section corrects it and does not "
    "rewrite it, in four separate items, each with its source. The sources are Codex review 3, "
    "section 5, and section 4 of Claude's critique, both in "
    "`../../corrections-plan/codex-review-3.md`; the code lines are those of the Portuguese "
    "script that the review read (`dev1/c3_inconclusive.py`, in the archive of the study). The "
    "Portuguese record keeps the same errata, item for item, in "
    "`dev1-c3-inconclusive-errata-v2.md`.",
    "",
    "1. **C01 (method (a)).** The omission affects the reported lever arm, not directly the "
    "counts 21 and 38. The counts compare the `max_timing_sigma` recorded by the tool, scaled "
    "by sigma_tc,approx / sigma_tc,tool (method (b)), with one duration "
    "(`dev1/c3_inconclusive.py:103-104`); the lever arm m of method (a) "
    "(`dev1/c3_inconclusive.py:96`), which leaves out C01 and the integer reference epoch, is "
    "only reported. The sentence of method (a) that gives the counts \"an uncertainty of a few "
    "cases\" because of these two approximations is therefore wrong. The approximation that "
    "does weigh on the counts is the scaling by err(t_ref) x sqrt(N) of method (b). *Source:* "
    "Codex review 3, section 5, correction 1; Claude's critique, section 4, item 1.",
    "2. **Uncertainty of the counts.** The effect of that scaling on the counts is an "
    "unquantified sensitivity, not \"a few cases\" (method (a) and the caveats of section "
    "(d)). *Source:* Codex review 3, section 5, correction 2; Claude's critique, section 4, "
    "item 2.",
    "3. **\"Do not change\".** In the last caveat of section (d), the other paths to "
    "INCONCLUSIVE (4 of the 61) do not change only inside the conditional scenario of (d); "
    "the M4 package could change candidates, capacity and other paths to INCONCLUSIVE "
    "(corrections plan, revision 3, section 6). *Source:* Codex review 3, section 5, "
    "correction 3; Claude's critique, section 4, item 3.",
    "4. **Medians.** With an even number of values the medians take the upper central value "
    "(`vals[len(vals) // 2]`, `dev1/c3_inconclusive.py:152-154`), not the mean of the two "
    "central values; this does not change the counts 21 and 38. *Source:* Codex review 3, "
    "section 5, correction 4; Claude's critique, section 4, item 4.",
    "",
    END,
    "",
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--records", type=Path, default=DEFAULT_RUNS)
    ap.add_argument("--out-dir", type=Path, default=None)
    args = ap.parse_args()
    md = (args.out_dir or HERE.parent) / MD_NAME
    js = (args.out_dir or HERE) / JSON_NAME
    for p in (md, js):
        if p.exists():
            raise SystemExit(f"{p.name} exists; not replaced")
    manifest = json.loads(MANIFEST.read_bytes())
    cases = [
        e
        for e in manifest["cases"]
        if e["class"] == "planet"
        and e["noise"] == "white"
        and e["band"] == "measurable"
        and e["mechanism"] in ("two_years", "few_train")
    ]
    rows, per_case = [], {}
    for e in cases:
        rec = json.loads((args.records / "M3-slot1" / "cases" / f"{e['id']}.json").read_bytes())
        sci = rec["conditions"]["i"]["scientific"]
        if sci["verdict"] != "INCONCLUSIVE":
            continue
        pr = e["parameters"]
        case_rows = []
        for r in sci.get("holdout_rounds") or []:
            m = {k: f(v) for k, v in (r.get("metrics") or {}).items()}
            tc = (
                {k: f(v) for k, v in m["train_candidate"].items()}
                if isinstance(m.get("train_candidate"), dict)
                else {}
            )
            eph = {k: f(v) for k, v in (r.get("train_ephemeris") or {}).items()}
            row = {
                "case": e["id"],
                "mechanism": e["mechanism"],
                "hidden_year": r["hidden_year"],
                "status": r["status"],
                "message": r["message"],
            }
            smax = m.get("max_timing_sigma_days")
            if smax is None or not tc or not eph:
                row["kind"] = "no timing data"
                case_rows.append(row)
                continue
            n_times = int(m.get("n_transit_times") or eph.get("n_transits") or 0)
            t_dur = tc["duration"]
            lever = (
                math.sqrt(max(smax**2 - eph["t_ref_err"] ** 2, 0.0)) / eph["period_err"]
                if eph["period_err"] > 0
                else None
            )
            sig_tool = eph["t_ref_err"] * math.sqrt(n_times)
            n_in = tc["n_transits"] * tc["duration"] / CADENCE
            sigma_est = tc["depth_err"] * math.sqrt(n_in)
            tau_train = pr["ingress_fraction"] * tc["duration"]
            opt_train = carter(tc["depth"], tc["duration"], tau_train, sigma_est)
            opt_truth = carter(
                pr["depth"], pr["duration"], pr["ingress_fraction"] * pr["duration"], SIGMA_WHITE
            )
            pred_train = smax * opt_train / sig_tool
            pred_truth = smax * opt_truth / sig_tool
            epoch_opt = opt_train / math.sqrt(n_times)
            row.update(
                {
                    "ratio_tool": smax / t_dur,
                    "max_timing_sigma_h": smax * 24,
                    "train_duration_h": t_dur * 24,
                    "n_transit_times": n_times,
                    "chi2_reduced": eph.get("chi2_reduced"),
                    "lever_epochs": lever,
                    "sigma_tc_tool_min": sig_tool * 1440,
                    "sigma_noise_est_ppm": sigma_est * 1e6,
                    "ingress_fraction": pr["ingress_fraction"],
                    "sigma_tc_opt_train_min": opt_train * 1440,
                    "sigma_tc_opt_truth_min": opt_truth * 1440,
                    "ratio_opt_train": pred_train / t_dur,
                    "ratio_opt_truth": pred_truth / t_dur,
                    "epoch_opt_over_duration": epoch_opt / t_dur,
                    "train_snr": tc.get("snr"),
                }
            )
            if row["ratio_opt_train"] <= 1.0:
                row["kind"] = KIND_I
            elif row["epoch_opt_over_duration"] < GOOD_EPOCH:
                row["kind"] = KIND_III
            else:
                row["kind"] = KIND_II
            case_rows.append(row)
        rows += case_rows
        timed = [r for r in case_rows if "ratio_opt_train" in r]
        if any(r["ratio_opt_train"] <= 1.0 for r in timed):
            kind = KIND_I
        elif any(r["kind"].startswith("(iii)") for r in timed):
            kind = KIND_III
        elif timed:
            kind = KIND_II
        else:
            kind = "no timing data"
        per_case[e["id"]] = {
            "mechanism": e["mechanism"],
            "kind": kind,
            "best_ratio_tool": min((r["ratio_tool"] for r in timed), default=None),
            "best_ratio_opt_train": min((r["ratio_opt_train"] for r in timed), default=None),
            "best_ratio_opt_truth": min((r["ratio_opt_truth"] for r in timed), default=None),
        }

    n_case = len(per_case)
    by_kind = collections.Counter((v["mechanism"], v["kind"]) for v in per_case.values())
    resolved_train = sum(
        1
        for v in per_case.values()
        if v["best_ratio_opt_train"] is not None and v["best_ratio_opt_train"] <= 1.0
    )
    resolved_truth = sum(
        1
        for v in per_case.values()
        if v["best_ratio_opt_truth"] is not None and v["best_ratio_opt_truth"] <= 1.0
    )
    kmax = max(k for k in range(251) if cp_upper(k, 250) <= 0.20)
    L = [
        "# The C3 white INCONCLUSIVE planets: train timing precision (M3, slot 1)",
        "",
        "Version 2 (2026-10-14). The version reviewed in `codex-m4-plan-review-2.md` is preserved "
        "unchanged in `dev1-c3-inconclusive-v1.md` (SHA-256",
        f"`{PT_V1_SHA256}`). This version changes only the text",
        "(the class names, the caveats of the method and the presentation of the 40 of 250); the "
        "numbers are the same, from the same script and the same records.",
        "",
        ADD,
        "",
        f"Translated by script from the maintainer's Portuguese record `{PT_RECORD}`, "
        f"version 2 (SHA-256 `{PT_SHA256}`), with the same numbers "
        "(`investigations/check_numbers.py`), plus the dated errata below. The Portuguese "
        "records and the review files named here are kept in the archive of the study. File and "
        "line references are to commit `605fac1`.",
        "",
        END,
        "",
        *ERRATA,
        "Read only: the result records and the frozen manifest. Script: "
        "`investigations/c3_inconclusive.py`. Cases: white measurable planets of `two_years` and "
        f"`few_train` with verdict INCONCLUSIVE at M3: **{n_case}**. The generation parameters "
        "(injected ingress, depth and duration) enter **only the diagnosis**, never as a proposed "
        "input to the tool.",
        "",
        "## Method",
        "",
        "- **(a) The tool:** in each round, `max_timing_sigma` is the train-only timing "
        "uncertainty at the farthest hidden transit; the rule declares the round INCONCLUSIVE "
        "when it exceeds 1 duration of the train candidate (`holdout.py:513-537`). The lever arm "
        "m (epochs between the reference epoch and the farthest hidden transit) is "
        "**approximated** by sigma_max² = err(t_ref)² + m² err(P)². The tool's actual prediction "
        "is sigma_pred² = C00 + 2·m·C01 + m²·C11 (`ephemeris.py:103`), with the reference epoch "
        "**rounded to an integer** (`ephemeris.py:124`); the cross term C01 was left out here "
        "because `Ephemeris.to_dict` does not export it. The effect of these two approximations "
        "**was not quantified**; at least two cases lie close to the limit of 1 (ratios 1.0116 "
        "in `planet-measurable-white-0062` and 1.0304 in `planet-measurable-white-0044`), so the "
        f"counts below have an uncertainty of a few cases {ADD}(see the errata, item 1){END}. The "
        "per-transit precision that the ephemeris implies is sigma_tc,tool = err(t_ref) × √N "
        "(equal weights; includes the chi-square inflation).",
        "- **(b) The Carter approximation:** Carter, Yee, Eastman, Gaudi and Winn 2008 "
        "(arXiv:0805.0238, DOI 10.1086/592321, eq. 43; reference and formula checked on arXiv on "
        "2026-10-14): Q = √(ΓT)·δ/σ, θ = τ/T, σ_tc = Q⁻¹·T·√(θ/2), with T the duration between "
        "the midpoints of ingress and egress, τ the ingress duration, Γ the sampling rate (1 per "
        "2 min) and σ the per-point noise. **Eq. 43 holds for a uniform source, white noise and "
        "uniform sampling**; with limb darkening it underestimates the uncertainties (the "
        "abstract of the paper). Two versions: **approximation with train numbers** (δ, T14 and "
        "σ of the train candidate, σ taken from the depth error and the in-transit cadences, "
        "neglecting the baseline term and counting partial transits; δ and the duration are "
        "those of the BLS box, not the δ and T14 of the trapezoid; τ = **injected** ingress "
        "fraction × T14, because the box has no ingress) and **approximation with the truth** "
        "(injected δ, T14 and τ, σ = 600 ppm). Neither is an optimal estimator computed only "
        "from information that can be estimated from the train. The prediction scales the "
        "tool's: σ_pred,approx = σ_pred,tool × σ_tc,approx / σ_tc,tool, which is exact only if "
        "the new covariance is proportional to the old one (same epochs, equal weights, "
        "chi-square 1). The direct calculation, σ_pred² = σ_tc² [1/N + (n_hidden − mean(n))² / "
        "Σ(n_i − mean(n))²], would need the epochs of the train times, which are not in the "
        "records.",
        "- **(c) Classification per round (a description of the calculation, a hypothesis; it "
        "does not show that the case is recoverable):**",
        "  - **(i) uncertainty below one duration by the Carter approximation** (train version);",
        "  - **(iii) above one duration by the approximation, with the train epoch below 0.1 "
        "duration** (σ_tc,approx/√N < 0.1 duration): by the approximation, the shortfall comes "
        "from the extrapolation over many periods;",
        "  - **(ii) above one duration by the approximation, with the train epoch at 0.1 "
        "duration or more.**",
        "  A case counts as (i) if some round is (i); otherwise (iii) if some round is (iii); "
        "otherwise (ii). The threshold of 0.1 duration is a choice of this diagnosis "
        "(`GOOD_EPOCH` in the script), not a physical boundary. The file `dev1/c3-rounds.json` "
        "of the Portuguese record, written by the run of its script, keeps the old class names, "
        "in Portuguese: \"current estimator overestimates\" corresponds to (i) above, and "
        "\"measurable SNR, but the extrapolation exceeds one duration\" corresponds to (iii)"
        f"{ADD}; `investigations/c3-rounds.json` is written with the class names of version 2, "
        f"in English{END}.",
        "",
        "## Result",
        "",
        "| mechanism | classification | cases |",
        "|---|---|---|",
    ]
    L += [f"| {k[0]} | {k[1]} | {v} |" for k, v in sorted(by_kind.items())]
    timed = [r for r in rows if "ratio_opt_train" in r]
    for mech in ("two_years", "few_train"):
        sub = [r for r in timed if r["mechanism"] == mech]
        L += [
            "",
            f"**{mech}** ({len(sub)} rounds with timing data), medians: tool ratio "
            f"{fmt(med(r['ratio_tool'] for r in sub))}; tool σ_tc "
            f"{fmt(med(r['sigma_tc_tool_min'] for r in sub))} min; σ_tc by the approximation "
            f"(train) {fmt(med(r['sigma_tc_opt_train_min'] for r in sub))} min; σ_tc by the "
            f"approximation (truth) {fmt(med(r['sigma_tc_opt_truth_min'] for r in sub))} min; "
            f"ratio by the approximation (train) {fmt(med(r['ratio_opt_train'] for r in sub))}; "
            f"ratio by the approximation (truth) {fmt(med(r['ratio_opt_truth'] for r in sub))}; "
            f"lever arm {fmt(med(r['lever_epochs'] for r in sub))} periods; N times "
            f"{fmt(med(r['n_transit_times'] for r in sub))}; reduced chi-square "
            f"{fmt(med(r['chi2_reduced'] for r in sub))}; estimated noise "
            f"{fmt(med(r['sigma_noise_est_ppm'] for r in sub))} ppm.",
        ]
    L += [
        "",
        "## Examples (3 per mechanism, the round with the smallest ratio by the approximation)",
        "",
    ]
    for mech in ("two_years", "few_train"):
        ids = [c for c, v in per_case.items() if v["mechanism"] == mech][:3]
        for c in ids:
            r = min(
                (x for x in timed if x["case"] == c),
                key=lambda x: x["ratio_opt_train"],
                default=None,
            )
            if r is None:
                continue
            L.append(
                f"- `{c}`, hidden year {r['hidden_year']}: tool σ_max "
                f"{fmt(r['max_timing_sigma_h'])} h against duration {fmt(r['train_duration_h'])} h "
                f"(ratio {fmt(r['ratio_tool'])}); N = {r['n_transit_times']}, chi-square "
                f"{fmt(r['chi2_reduced'])}, lever arm {fmt(r['lever_epochs'])} periods; tool σ_tc "
                f"{fmt(r['sigma_tc_tool_min'])} min, train approximation "
                f"{fmt(r['sigma_tc_opt_train_min'])} min, truth approximation "
                f"{fmt(r['sigma_tc_opt_truth_min'])} min (ingress fraction "
                f"{fmt(r['ingress_fraction'])}); ratio by the approximation, train "
                f"{fmt(r['ratio_opt_train'])}, truth {fmt(r['ratio_opt_truth'])}; class "
                f"{r['kind'].split(' ')[0]}"
            )
    rt, rtr = resolved_train, resolved_truth
    L += [
        "",
        "## Observations (hypotheses marked)",
        "",
        "1. **No case fell into (ii).** By the approximation, in every round the train epoch "
        "would be fixed to well under 0.1 duration; what exceeds 1 duration is the extrapolation "
        "over ~240 periods to the hidden year (two years away). The boundary between (ii) and "
        "(iii) is the diagnostic threshold of 0.1 duration, chosen here; with another threshold "
        "the partition changes.",
        "2. **The tool's ephemeris fit has a reduced chi-square far above 1** (median 53.6 in "
        "`two_years`, 12.3 in `few_train`): the individual times measured with the box scatter "
        "much more than the errors the tool assigns to them, and the √chi-square inflation "
        "(`ephemeris.py:133`) recovers the scatter. The effective per-transit precision (median "
        "9.6 min in `two_years`) is about twice that of the approximation (4.9 min). "
        "**Hypothesis:** the per-transit error of the box scan (half-width of Δchi² = 1, with the "
        "floor of half a cadence, `ephemeris.py:64-78`) is optimistic, and the box measurement, "
        "without ingress, is less efficient than a model with ingress. **The chi-square of 53.6 "
        "does not by itself identify the cause**, and **does not guarantee that the trapezoidal "
        "model corrects it**: the scatter may also come from other sources (the residual "
        "variability, the trend, the selection of the train candidate); the model with ingress "
        "is what the ROADMAP asks for (`ROADMAP.md:132-133`), and its effect has to be measured "
        f"on the calibration population{ADD} (the planned noise-calibration population of the "
        "corrections plan, never generated nor analyzed; distinct from `calibration/v0.2/` and "
        f"from the tag `v0.2.0-calibration-lock`){END}.",
        "3. **In all these planets the ingress fraction is 0.05**, the floor of the generator "
        "(section 4.3): a short ingress, the most favorable case for timing precision according "
        "to eq. 43.",
        "4. **The two years of distance dominate.** Even by the approximation with train numbers, "
        "the median ratio stays at 1.21 (`two_years`) and 2.04 (`few_train`): most of these "
        "cases still cannot test the hidden year by timing. **Hypothesis:** it is a consequence "
        "of the declared geometry of the mechanisms (section 4.3), which the definition of "
        "\"measurable\" by SNR does not consider; it is not a defect of the population.",
        "",
        "## (d) What this implies for C3 (without changing the criterion)",
        "",
        f"- Cases of the {n_case} with some round below 1 duration by the Carter approximation: "
        f"**{rt}** (train version) and **{rtr}** (truth version).",
        "- The C3 white of planets at M3 is 61 of 250; the one-sided 95% upper limit "
        f"(Clopper-Pearson) stays ≤ 0.20 with at most **{kmax}** of 250 (computed here; it agrees "
        "with `population-study.md:72`).",
        f"- **Sensitivity, not a bound:** if the {rt} cases of the train version stopped being "
        f"INCONCLUSIVE and nothing else changed, the C3 white would be 61 − {rt} = {61 - rt} of "
        f"250; with the truth version, 61 − {rtr} = {61 - rtr}. It is a conditional scenario "
        f"(same candidates, same epochs, a valid proportional scaling, all {rt} conclusive and "
        "no other transition).",
        "  **The approximation puts C3 near the approval threshold. There is a relevant risk of "
        "it staying FAILS; the probability of approval has not been estimated yet.**",
        "- Caveats: a round that becomes conclusive can give PASS or FAIL (a FAIL would increase "
        "the C1 measurable white, now 58 of 250), or stay INCONCLUSIVE because of capacity, "
        "coverage or `period_alias`; the new model may recover discarded times and change the "
        "geometry of the fit; the approximations of (a) and (b) change the counts in a few "
        "cases; other paths to INCONCLUSIVE (4 of the 61 are outside these mechanisms) do not "
        f"change{ADD} (see the errata, items 2 and 3){END}.",
        "",
    ]
    js.parent.mkdir(parents=True, exist_ok=True)
    js.write_text(
        json.dumps({"rounds": rows, "cases": per_case}, indent=1) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    md.write_text("\n".join(L), encoding="utf-8", newline="\n")
    print(md.name, js.name, n_case, "cases", len(rows), "rounds", "resolved", rt, rtr, "kmax", kmax)


if __name__ == "__main__":
    main()
