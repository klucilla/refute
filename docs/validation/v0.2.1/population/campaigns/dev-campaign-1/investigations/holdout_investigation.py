"""Read-only investigation of the holdout_by_year failures with the right signal (M3, slot 1).

English version of the script behind the maintainer's Portuguese record dev1-holdout.md
(2026-10-14): the same selection, the same quantities, the same formatting of the numbers;
only the text is translated. Planets three_years (near band) and variability_some_years
(measurable band) whose candidate has signal identity and whose holdout test FAILS.

Inputs: ../../../manifest-dev.json and the M3 slot 1 result records, kept out of git and
listed in ../asset-SHA256SUMS (default: .cache/population/campaign-dev-1/runs). Outputs:
holdout-investigation.md (default: the campaign folder) and holdout-rounds.json (default: this
folder, every round examined, with the values used). Never replaces an existing file.

Per round (one hidden year):
- train-only quantities, as the tool had them before reading the hidden year: the train
  candidate (period, depth, depth error, SNR, number of transits), the timing uncertainty,
  the number of predicted transit windows; and a train-only prediction of the hidden SNR,
  SNR_pred = (train depth / train depth error) * sqrt(n_predicted / n_train_transits)
  (the depth error scales as 1/sqrt(number of transits); diagnosis only, not the tool's);
- what the hidden year gave: windows with data, stacked SNR, white and scatter errors, the
  phase-0.5 control;
- the truth (diagnosis only, never available to the tool): the expected hidden-year SNR of
  the manifest (c_hidden(y) * injected depth, under the case's noise model), and the offset
  of each predicted window from the true transit time, in units of its half-width;
- for variability_some_years, whether the hidden year is the year without variability.

Usage: python holdout_investigation.py [--records DIR] [--out-dir DIR]
"""

from __future__ import annotations

import argparse
import collections
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent


def repo_root() -> Path:
    for p in HERE.parents:
        if (p / "pyproject.toml").is_file() and (p / "ROADMAP.md").is_file():
            return p
    raise SystemExit("repository root not found")


REPO = repo_root()
MANIFEST = REPO / "docs" / "validation" / "v0.2.1" / "population" / "manifest-dev.json"
DEFAULT_RUNS = REPO / ".cache" / "population" / "campaign-dev-1" / "runs"
MD_NAME = "holdout-investigation.md"
JSON_NAME = "holdout-rounds.json"
PT_RECORD = "dev1-holdout.md"
PT_SHA256 = "feeb5313361d64258c09245e3035fcc57481c7cbe68f1acc6a669a4a5fd37dfe"
MIN_SNR = 5.0
# Text added in translation (not in the Portuguese record) sits between these markers, so that
# check_numbers.py can compare the numbers of the two versions; the markers do not render.
ADD, END = "<!-- translation-note -->", "<!-- /translation-note -->"
WINDOWS_OUT = "FAIL: windows outside the true transit"


def f(v):
    if isinstance(v, dict) and "dec" in v and "f64" in v:
        return float(v["dec"])
    return v


def rounds_of(runs: Path, case: str) -> tuple[dict, list[dict]]:
    rec = json.loads((runs / "M3-slot1" / "cases" / f"{case}.json").read_bytes())
    cond = rec["conditions"]["i"]
    return cond, cond["scientific"].get("holdout_rounds") or []


def examine(runs: Path, e: dict) -> list[dict]:
    cond, rounds = rounds_of(runs, e["id"])
    pr, es = e["parameters"], e["expected_snr"]
    P, t0, depth = pr["period"], pr["t0"], pr["depth"]
    out = []
    for r in rounds:
        m = {k: f(v) for k, v in (r.get("metrics") or {}).items()}
        tc = (
            {k: f(v) for k, v in m["train_candidate"].items()}
            if isinstance(m.get("train_candidate"), dict)
            else {}
        )
        y = r["hidden_year"]
        n_pred = m.get("n_predicted_transits")
        n_train = tc.get("n_transits")
        pred = None
        if tc.get("depth") and tc.get("depth_err") and n_pred and n_train:
            pred = (tc["depth"] / tc["depth_err"]) * math.sqrt(n_pred / n_train)
        offsets = []
        for w in r.get("windows") or []:
            tp, hw = f(w["t_pred"]), f(w["half_width"])
            true = t0 + round((tp - t0) / P) * P
            offsets.append(abs(tp - true) / hw)
        truth_hidden = (es.get("hidden") or {}).get(str(y))
        timing = m.get("max_timing_sigma_days")
        row = {
            "case": e["id"],
            "noise": e["noise"],
            "mechanism": e["mechanism"],
            "hidden_year": y,
            "status": r["status"],
            "message": r["message"],
            "train_period_over_true": (tc.get("period") / P) if tc.get("period") else None,
            "train_snr": tc.get("snr"),
            "train_depth_ppm": (tc.get("depth") or 0) * 1e6 if tc.get("depth") else None,
            "train_n_transits": n_train,
            "injected_depth_ppm": depth * 1e6,
            "max_timing_sigma_over_duration": (timing / tc["duration"])
            if timing is not None and tc.get("duration")
            else None,
            "n_predicted_transits": n_pred,
            "n_windows_with_data": m.get("n_windows_with_data"),
            "snr_pred_train_only": pred,
            "hidden_snr": m.get("hidden_snr"),
            "hidden_depth_ppm": m.get("hidden_depth_ppm"),
            "hidden_white_err_ppm": m.get("hidden_white_err_ppm"),
            "hidden_scatter_err_ppm": m.get("hidden_scatter_err_ppm"),
            "control_phase05_snr": m.get("control_phase05_snr"),
            "depth_consistency_sigma": m.get("depth_consistency_sigma"),
            "truth_hidden_snr": truth_hidden * depth if truth_hidden else None,
            "max_window_offset_over_half_width": max(offsets) if offsets else None,
            "windows_containing_true_transit": sum(o <= 1.0 for o in offsets) if offsets else None,
            "var_absent_year": pr.get("var_absent_year"),
        }
        out.append(row)
    return out


def classify(r: dict) -> str:
    if r["status"] != "FAIL":
        return r["status"]
    off = r["max_window_offset_over_half_width"]
    if off is not None and off > 1.0:
        return WINDOWS_OUT
    pred = r["snr_pred_train_only"]
    if pred is None:
        return "FAIL: no prediction"
    truth = r["truth_hidden_snr"]
    if pred < MIN_SNR:
        return "FAIL: the train did not allow a prediction (predicted SNR < 5)"
    if truth is not None and truth < MIN_SNR:
        return "FAIL: the train predicted a detectable signal, but the true hidden-year SNR is < 5"
    return "FAIL: the train predicted a detectable signal, the true SNR is >= 5, and it did not appear"


def fmt(v, nd=3):
    if v is None:
        return "-"
    if isinstance(v, float):
        return f"{v:.{nd}g}"
    return str(v)


def observations(fails: dict[str, list[dict]]) -> list[str]:
    three, var = fails["three_years, near"], fails["variability_some_years, measurable"]
    out3 = sum(classify(r) == WINDOWS_OUT for r in three)
    outv = sum(classify(r) == WINDOWS_OUT for r in var)
    n_fail = len(three) + len(var)
    return [
        "## Observations (causal readings are marked as hypotheses)",
        "",
        f"1. **The windows are almost always in the right place.** In {n_fail - out3 - outv} of "
        f"the {n_fail} FAIL rounds ({len(three)} in `three_years`, {len(var)} in "
        "`variability_some_years`) the windows contain the center of the true transit (median "
        f"offset 0.1 to 0.5 half-width); {out3 + outv} rounds have some window displaced "
        f"({out3} in `three_years`, {outv} in `variability_some_years`). For these cases, the "
        "failure is not in the train ephemeris.",
        "2. **`three_years`, near: the signal is in the hidden year, but near the threshold.** "
        "The depth measured in the hidden year stays close to the injected one (median 145 "
        "against 165 ppm in white, 761 against 877 in correlated) and the measured SNR stays just "
        "below the threshold (median 4.2 against 5.0). The true hidden-year SNR is low (median "
        "6.1 to 6.3): a fatal test with a 5.0 threshold on a signal with a true SNR of ~6 fails "
        "often from fluctuation alone. In this reading, the round had **little capacity to "
        "test** and the FAIL is not evidence that the signal disappeared. **Hypothesis** (not "
        "tested): a rule that requires, before the hidden year is read, a predicted SNR with a "
        "margin above the threshold would turn most of these FAILs into INCONCLUSIVE, without "
        "touching the cases in which the predicted signal is strong.",
        "3. **In correlated noise the train overestimates the capacity to test.** The train-only "
        "prediction gives a median SNR of 23.8 for `three_years` near, against a true SNR of "
        "6.3; in the hidden year the scatter error (188 ppm) is five times the white one (37 "
        "ppm), and it is the scatter error that sets the measured SNR. It is the same pattern as "
        f"item 2 of the diagnosis {ADD}(the observations of `diagnosis.md`){END} (SNR with a "
        "white-noise error). **Hypothesis:** a capacity rule only works here if the train error "
        "also accounts for the correlated noise.",
        f"4. **`variability_some_years`, measurable: all {len(var)} FAIL rounds are hidden years "
        "with variability;** the 43 hidden years without variability gave INCONCLUSIVE (no "
        "FAIL). In the hidden year with variability, the scatter error is about 10 times the "
        "white one (547 against 55 ppm in white; 1740 against 168 in correlated), and the "
        "measured SNR falls to ~0.9, although the measured depth stays close to the injected one "
        "(515 against 616 ppm in white). **Hypothesis:** the local straight line of each window "
        "does not remove a sinusoid of 0.3 to 1 d with 2 to 4 times the transit depth; the "
        "scatter between windows dominates the error and the test declares that the signal did "
        "not appear. The \"true SNR\" of the manifest does not include the variability, so it "
        "overestimates the detectability in those years.",
        "5. **Answer to the maintainer's question.** In both families, the train predicted (by "
        "the approximate rule above) a detectable signal and the measured SNR did not reach 5. "
        "But the records show that the signal is present (measured depth close to the injected "
        "one, correct windows): the FAIL comes from **little real capacity to test** (a true "
        "signal near the threshold in `three_years` near) or from **an error that the "
        "hidden-year measurement does not control** (variability in `variability_some_years`), "
        "not from a signal that disappeared. The case \"the train did not allow a prediction\" "
        "hardly appears **because the train prediction is optimistic** (item 3), not because the "
        "capacity was good.",
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
    runs = args.records
    manifest = json.loads(MANIFEST.read_bytes())
    planets = [e for e in manifest["cases"] if e["class"] == "planet"]
    groups = {
        "three_years, near": [
            e for e in planets if e["mechanism"] == "three_years" and e["band"] == "near"
        ],
        "variability_some_years, measurable": [
            e
            for e in planets
            if e["mechanism"] == "variability_some_years" and e["band"] == "measurable"
        ],
    }
    L = [
        "# Holdout with the right signal: what the train predicted and what the hidden year gave "
        "(M3, slot 1)",
        "",
        "Read only: the result records already written and the frozen manifest. Script: "
        "`investigations/holdout_investigation.py`. Cases: planets whose candidate has signal "
        "identity with the injected period and whose `holdout_by_year` is FAIL. Each round is one "
        "hidden year.",
        "",
        ADD,
        "",
        f"Translated by that script from the maintainer's Portuguese record `{PT_RECORD}` "
        f"(2026-10-14, SHA-256 `{PT_SHA256}`), with the same numbers "
        "(`investigations/check_numbers.py`); the Portuguese record is kept in the archive of the "
        "study. File and line references are to commit `605fac1`.",
        "",
        END,
        "",
        "Quantities:",
        "",
        "- **Predicted SNR (train only)** = (train depth / train depth error) x sqrt(predicted "
        "windows / train transits). It uses only what the tool had before reading the hidden "
        "year (the train candidate and the windows, which come from the metadata). It is an "
        "approximation of this diagnosis, not a rule of the tool.",
        "- **True hidden-year SNR** = c_hidden(y) x injected depth, from the manifest, under the "
        "noise model of the case (including the AR(1) covariance). **The tool never has this "
        "value**; it only serves to separate the categories.",
        "- **Window offset** = |predicted t - t of the nearest true transit| / half-width of the "
        "window; above 1, the window does not contain the center of the transit.",
        "- The tool's FAIL: stacked SNR in the windows < 5.0 (`holdout_by_year.min_snr`).",
        "",
    ]
    all_rows: list[dict] = []
    fails_by_group: dict[str, list[dict]] = {}
    for title, cases in groups.items():
        failing = []
        for e in cases:
            cond, _ = rounds_of(runs, e["id"])
            hb = next(
                (t for t in cond["scientific"]["tests"] if t["name"] == "holdout_by_year"), None
            )
            if cond["harness_outcomes"].get("signal_identity") and hb and hb["status"] == "FAIL":
                failing.append(e)
        rows = [r for e in failing for r in examine(runs, e)]
        all_rows += rows
        L += [
            f"## {title}: {len(failing)} of {len(cases)} planets with the right signal and "
            "holdout FAIL",
            "",
        ]
        cats = collections.Counter((r["noise"], classify(r)) for r in rows)
        L += ["| noise | round | n |", "|---|---|---|"]
        L += [f"| {k[0]} | {k[1]} | {v} |" for k, v in sorted(cats.items())]
        L += [""]
        fails = [r for r in rows if r["status"] == "FAIL"]
        fails_by_group[title] = fails
        for noise in ("white", "correlated"):
            sub = [r for r in fails if r["noise"] == noise]
            if not sub:
                continue

            def med(key, sub=sub):
                vals = sorted(r[key] for r in sub if r[key] is not None)
                return vals[len(vals) // 2] if vals else None

            L += [
                f"FAIL rounds in {noise} noise ({len(sub)}), medians: train SNR "
                f"{fmt(med('train_snr'))}; SNR predicted from the train only "
                f"{fmt(med('snr_pred_train_only'))}; SNR measured in the hidden year "
                f"{fmt(med('hidden_snr'))}; true hidden-year SNR {fmt(med('truth_hidden_snr'))}; "
                f"white error {fmt(med('hidden_white_err_ppm'))} ppm, scatter error "
                f"{fmt(med('hidden_scatter_err_ppm'))} ppm; depth measured in the hidden year "
                f"{fmt(med('hidden_depth_ppm'))} ppm against {fmt(med('injected_depth_ppm'))} "
                f"injected; windows with data {fmt(med('n_windows_with_data'))} of "
                f"{fmt(med('n_predicted_transits'))}; largest window offset "
                f"{fmt(med('max_window_offset_over_half_width'))} half-width; timing "
                f"uncertainty {fmt(med('max_timing_sigma_over_duration'))} duration.",
                "",
            ]
        if title.startswith("variability"):
            var = collections.Counter(
                (
                    "hidden year without variability"
                    if r["hidden_year"] == r["var_absent_year"]
                    else "hidden year with variability",
                    r["status"],
                )
                for r in rows
            )
            L += ["| hidden year | round | n |", "|---|---|---|"]
            L += [f"| {k[0]} | {k[1]} | {v} |" for k, v in sorted(var.items())]
            L += [""]
        L += ["Examples (3 FAIL rounds):", ""]
        for r in fails[:3]:
            L.append(
                f"- `{r['case']}`, hidden year {r['hidden_year']} ({r['noise']}): {r['message']}; "
                f"train SNR {fmt(r['train_snr'])}, {fmt(r['train_n_transits'])} transits, depth "
                f"{fmt(r['train_depth_ppm'])} ppm (injected {fmt(r['injected_depth_ppm'])}); "
                f"predicted SNR {fmt(r['snr_pred_train_only'])}; hidden year: SNR "
                f"{fmt(r['hidden_snr'])}, depth {fmt(r['hidden_depth_ppm'])} ppm, white error "
                f"{fmt(r['hidden_white_err_ppm'])}, scatter {fmt(r['hidden_scatter_err_ppm'])}, "
                f"windows {fmt(r['n_windows_with_data'])}/{fmt(r['n_predicted_transits'])}, "
                f"phase-0.5 control SNR {fmt(r['control_phase05_snr'])}; truth: hidden-year SNR "
                f"{fmt(r['truth_hidden_snr'])}, largest offset "
                f"{fmt(r['max_window_offset_over_half_width'])}"
            )
        L += [""]
    L += observations(fails_by_group)
    js.parent.mkdir(parents=True, exist_ok=True)
    js.write_text(json.dumps(all_rows, indent=1) + "\n", encoding="utf-8", newline="\n")
    md.write_text("\n".join(L), encoding="utf-8", newline="\n")
    print(md.name, js.name, len(all_rows), "rounds")


if __name__ == "__main__":
    main()
