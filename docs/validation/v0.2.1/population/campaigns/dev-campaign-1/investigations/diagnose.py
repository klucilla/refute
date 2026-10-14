"""Read-only diagnosis of development campaign 1 (M0 and M3, slot 1; the two slots are
identical). It reads the frozen manifest and the result records already written, changes
nothing, and writes diagnosis.md and the compact extraction it used (extract-<point>.json,
about 22 MB each, in the work folder).

This is the script that wrote ../diagnosis.md. It was copied here at the closure of the
study (2026-10-14) with the analysis and every output string unchanged; only the plumbing
changed (repository root found by walking up, the paths as arguments, the observations text
embedded), and a rerun reproduces diagnosis.md byte for byte (see README.md). diagnosis.md
says its script was not published because it was written before this copy existed.

Inputs: ../../../manifest-dev.json and the M0 and M3 slot 1 result records, kept out of git
and listed in ../asset-SHA256SUMS (default: .cache/population/campaign-dev-1/runs).

Steps: extraction in parallel (ProcessPoolExecutor, os.cpu_count() - 2 workers under the
inherited affinity), then aggregation. No causal conclusion is drawn; hypotheses are marked.

Usage: python diagnose.py [--records DIR] [--work DIR] [--out FILE]
"""

from __future__ import annotations

import collections
import argparse
import hashlib
import json
import math
import os
import re
from concurrent.futures import ProcessPoolExecutor
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
DEFAULT_WORK = REPO / ".cache" / "population" / "dev-campaign-1-diagnosis"
DEFAULT_OUT = HERE.parent / "diagnosis.md"
POINTS = ("M0", "M3")
SNR_GATE, HIDDEN_MIN = 7.1, 5.0
NUM = re.compile(r"-?\d+(?:\.\d+)?(?:e[-+]?\d+)?")


def f(v):
    """A typed float back to a Python float (other values unchanged)."""
    if isinstance(v, dict) and "dec" in v and "f64" in v:
        return float(v["dec"]) if v["dec"] not in ("nan", "inf", "-inf") else float(v["dec"])
    return v


def norm(msg: str | None) -> str:
    return NUM.sub("#", msg or "").strip()


def compact_condition(cond: dict) -> dict:
    sci = cond.get("scientific") or {}
    ho = cond.get("harness_outcomes") or {}
    cand = sci.get("candidate") or {}
    tests = []
    for t in sci.get("tests") or []:
        tests.append(
            {
                "name": t.get("name"),
                "status": t.get("status"),
                "severity": t.get("severity"),
                "message": t.get("message"),
                "metrics": {k: f(v) for k, v in (t.get("metrics") or {}).items()
                            if not isinstance(v, (dict, list))},
            }
        )
    rounds = [
        {"hidden_year": r.get("hidden_year"), "status": r.get("status"), "message": r.get("message")}
        for r in sci.get("holdout_rounds") or []
    ]
    return {
        "verdict": sci.get("verdict"),
        "verdict_reason": sci.get("verdict_reason"),
        "candidate": {k: f(cand.get(k)) for k in ("period", "depth_ppm", "snr", "t0", "duration_hours", "sde", "n_transits")} if cand else None,
        "signal_identity": ho.get("signal_identity"),
        "identity_factor": f(ho.get("identity_factor")),
        "verdict_without_eb_catalog": ho.get("signal_verdict_without_eb_catalog"),
        "tests": tests,
        "holdout_rounds": rounds,
    }


def extract(task: tuple[str, str, str]) -> tuple[str, dict]:
    runs, point, case = task
    path = Path(runs) / f"{point}-slot1" / "cases" / f"{case}.json"
    data = path.read_bytes()
    rec = json.loads(data)
    out = {"status": rec.get("status"), "sha256": hashlib.sha256(data).hexdigest()}
    for c, cond in (rec.get("conditions") or {}).items():
        out[c] = compact_condition(cond)
    return case, out


def load_extract(point: str, ids: list[str], runs: Path, work: Path) -> dict:
    target = work / f"extract-{point}.json"
    if target.exists():
        return json.loads(target.read_bytes())
    workers = max(1, (os.cpu_count() or 4) - 2)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        res = dict(pool.map(extract, [(str(runs), point, i) for i in ids], chunksize=40))
    work.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(res), encoding="utf-8")
    return res


def family(e: dict) -> str:
    return e["mechanism"]


def flagged(cond: dict) -> bool:
    return cond.get("verdict_without_eb_catalog") == "REFUTED" and bool(cond.get("signal_identity"))


def fatal_fails(cond: dict) -> list[dict]:
    return [t for t in cond["tests"] if t["status"] == "FAIL" and t["severity"] == "fatal"]


def md_table(header: list[str], rows: list[list]) -> list[str]:
    out = ["| " + " | ".join(header) + " |", "|" + "---|" * len(header)]
    out += ["| " + " | ".join(str(x) for x in r) + " |" for r in rows]
    return out


def fmt(v, nd=4):
    if isinstance(v, float):
        if math.isnan(v):
            return "nan"
        return f"{v:.{nd}g}"
    return str(v)


OBSERVATIONS = [
    '## Observations (not causal conclusions)',
    '',
    'The tables above are the basis. What follows summarizes what they show; every causal reading',
    'is marked **Hypothesis** and was not tested.',
    '',
    '1. **The population agrees with its generation parameters (item f).** In all 1500 planets,',
    '   `r` recomputed from `expected_snr` and the depth equals the recorded `r_actual` and falls',
    "   in the declared band. When Refute's candidate is the injected signal (factor 1), period,",
    '   ephemeris, depth and duration agree: |P/P_inj - 1| < 0.001 in every case, median phase',
    '   offset of t0 from 0.009 to 0.017 durations, median depth 0.98 to 1.05 times the injected',
    '   depth, median duration 0.94 to 0.95 times. No defect of the population appears in these',
    '   quantities.',
    "2. **Refute's SNR agrees with the expected SNR in white noise and not in correlated noise.**",
    "   With the right signal, Refute's SNR divided by the expected global SNR: median 1.00 to 1.07",
    '   in white noise; 4.6 to 4.8 in correlated noise, in the three bands. The expected SNR of',
    "   section 3 includes the AR(1) covariance. **Hypothesis:** Refute's SNR treats the noise as",
    '   white and overstates the significance in correlated noise. Observed consequence: 83.8% of',
    '   the "below" planets pass Refute\'s own SNR gate.',
    '3. **The "below" band is always set by a single year.** In the 500 "below" planets, the ratio',
    '   that sets the band is the train ratio (403) or the hidden-year ratio (97), never the global',
    '   one; 299 of the 500 have an expected global SNR of 7.1 or more (table of item f). This is',
    '   the design of section 3, not a generation error.',
    '4. **Half of the "below" planets do not have the injected signal as their candidate.** Only',
    '   53.2% (266 of 500) have signal identity; in "near", 82.4%; in "measurable", 91.2%. Among the',
    '   REFUTED planets of M3, below band, 132 of the 183 `period_alias` failures are of candidates',
    '   that are not the injected signal (the candidate is another signal: variability, trend or',
    '   noise; see the examples, with periods of 0.5 to 1 d). C1 counts these cases as refuted',
    "   planets, because the criterion counts the target's verdict.",
    '5. **`period_alias` is the main fatal test in the below and near planets** ("a sinusoid at the',
    '   found period explains the dip", BIC gain < 10): 183 below and 123 near planets at M0 and at',
    '   M3 (the test did not change between the points). It also fails with the right signal: 51',
    '   below and 38 near planets with signal identity. **Hypothesis:** at low SNR, the BIC gain of',
    '   a box over a sinusoid does not reach 10 even for a real transit, and the test records a lack',
    '   of evidence as a fatal FAIL instead of INCONCLUSIVE.',
    '6. **`holdout_by_year` with the right signal remains the main cause in near and measurable at',
    '   M3:** 92 near and 58 measurable planets with signal identity ("prediction failed for hidden',
    '   year(s)"). In near, the holdout failures concentrate in `three_years` (32 in correlated',
    '   noise, 28 in white) and in correlated `variability_some_years` (28); in measurable, in',
    '   `variability_some_years` (36 correlated, 22 white). From M0 to M3 (the effect of H4, at M2),',
    '   holdout failures fall sharply for candidates that are not the signal (126 to 25 in below),',
    '   but little with the right signal (105 to 92 in near). **Hypotheses, not tested:** in',
    '   `three_years`, the prediction of a hidden year from the other two fails for a reason not',
    '   examined here; in `variability_some_years`, the variability present in the hidden year',
    '   distorts the measurement of the transit times; in correlated noise, the underestimated error',
    '   (item 2) may make the prediction too narrow. (A complementary read-only investigation of',
    '   these failures was made afterwards; it is not part of this translation.)',
    '7. **`variability_some_years` (300 planets):** in 228 the candidate is not the planet; the ratio',
    '   of the found period to the variability period is 1 or 2 (sample in item c). The',
    "   `period_alias` test correctly identifies that candidate as a sinusoid, and the target's",
    '   verdict is REFUTED. At M0 all 300 are REFUTED; at M3, 275 (12 INCONCLUSIVE and 13 SURVIVED),',
    '   through the fall of the holdout failures. **Hypothesis:** the search finds the variability,',
    '   stronger than the transit (amplitude 2 to 4 times the depth), and the variability is not',
    '   removed before the search.',
    '8. **C2 white, `variability_masked` (0 of 62 flagged):** 60 of 62 are REFUTED without',
    '   `eb_catalog`, but none has signal identity: the period found is that of the variability',
    '   (ratio 1 or 2), not that of the eclipse (ratio 0.11 to 0.51). The false positive is refuted',
    '   for the wrong reason (the candidate is the sinusoid), and the identity rule of H7 does not',
    '   count it. The same pattern in correlated noise (0 of 62). **Hypothesis:** the same as item 7',
    '   (the search finds the variability).',
    '9. **C3 of the white measurable planets (`two_years` 42 of 100, `few_train` 15 of 50',
    '   INCONCLUSIVE):** in all of them, `holdout_by_year` is INCONCLUSIVE because, in both rounds,',
    '   "the train-only timing uncertainty in the hidden year exceeds 1 transit duration"; no hidden',
    '   year could be tested. The candidate is the right signal in the examples. In correlated noise',
    '   the same mechanism has only 3 INCONCLUSIVE. **Hypothesis:** with two years two years apart',
    '   (or few train transits), propagating the ephemeris from a single year exceeds the limit of',
    '   1 duration in white noise; in correlated noise the underestimated error (item 2) keeps the',
    '   uncertainty below the limit and the test runs (and fails, item 6).',
    '',
    '**Tool versus population (the request of item f).** None of the quantities checked points to',
    'a defect of the synthetic population: bands, parameters, periods, ephemerides, depths and',
    'durations agree. The patterns behind C1, C2 and C3 lie in how the tool treats the data: the',
    'candidate chosen (items 4, 7, 8), the `period_alias` rule at low SNR (item 5) and the holdout',
    '(items 6 and 9), with the SNR in correlated noise (item 2) as a possible common factor.',
    '',
    '## Conclusion',
    '',
    'No defect of the population appeared in the checks performed. The diagnosis points to',
    'limitations of the tool, whose causes and corrections still need to be tested.',
]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--records", type=Path, default=DEFAULT_RUNS)
    ap.add_argument("--work", type=Path, default=DEFAULT_WORK)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()
    OUT = args.out
    if OUT.exists():
        raise SystemExit(f"{OUT.name} exists; not replaced")
    manifest = json.loads(MANIFEST.read_bytes())
    cases = manifest["cases"]
    by_id = {c["id"]: c for c in cases}
    ids = [c["id"] for c in cases]
    X = {p: load_extract(p, ids, args.records, args.work) for p in POINTS}
    L: list[str] = []
    L += [
        "# Diagnosis of development campaign 1 (M0 and M3)",
        "",
        "Read only: the frozen manifest (`../../manifest-dev.json`) and the result records of slot 1 "
        "(the two slots are identical: 208 recorded comparisons). Nothing was changed; no new "
        "analysis ran. Made by a local read-only script (not published); the result records are "
        "listed in `asset-SHA256SUMS`. What follows are counts and values read from the records; "
        "**hypotheses are marked as hypotheses**. The result of the campaign is FAILS and is not "
        "reinterpreted here. Translated from the maintainer's Portuguese diagnostic record.",
        "",
        "Verdicts found in the records: "
        + ", ".join(
            f"{p}: " + str(dict(collections.Counter(X[p][i]["i"]["verdict"] for i in ids)))
            for p in POINTS
        ),
        "",
        "Record statuses: "
        + ", ".join(f"{p}: {dict(collections.Counter(X[p][i]['status'] for i in ids))}" for p in POINTS),
        "",
    ]

    # (a) verdict counts per point x noise x band x family.
    L += ["## a) Verdicts by point, noise, band and family (condition i)", ""]
    L += [
        "`flagged` = the verdict recomputed without `eb_catalog` is REFUTED **and** there is signal "
        "identity (the definition of C2), counted for every class as information.",
        "",
    ]
    verdicts = ["REFUTED", "WEAKENED", "INCONCLUSIVE", "SURVIVED"]
    for p in POINTS:
        rows = []
        groups = collections.defaultdict(list)
        for e in cases:
            groups[(e["class"], e["noise"], e["band"], family(e))].append(e["id"])
        for key in sorted(groups, key=lambda k: (k[0], k[1], str(k[2]), k[3])):
            vs = collections.Counter(X[p][i]["i"]["verdict"] for i in groups[key])
            other = sum(n for v, n in vs.items() if v not in verdicts)
            fl = sum(flagged(X[p][i]["i"]) for i in groups[key])
            rows.append([*key, len(groups[key]), *[vs.get(v, 0) for v in verdicts], other, fl])
        L += [f"### {p}", ""]
        L += md_table(
            ["class", "noise", "band", "family", "n", *verdicts, "other", "flagged"], rows
        )
        L += [""]

    # (b) refuted planets: failing fatal tests, ranked, per band.
    L += ["## b) REFUTED planets: fatal tests that failed (ranked by frequency)", ""]
    L += [
        "Each REFUTED planet counts once for each fatal test with status FAIL; the column "
        "\"combination\" counts the exact set of fatal tests that failed.",
        "",
    ]
    for p in POINTS:
        for band in ("below", "near", "measurable"):
            refuted = [e["id"] for e in cases if e["class"] == "planet" and e["band"] == band
                       and X[p][e["id"]]["i"]["verdict"] == "REFUTED"]
            tests = collections.Counter()
            combos = collections.Counter()
            msgs = collections.Counter()
            for i in refuted:
                ff = fatal_fails(X[p][i]["i"])
                combos[" + ".join(sorted(t["name"] for t in ff)) or "(no fatal test FAIL)"] += 1
                for t in ff:
                    tests[t["name"]] += 1
                    msgs[(t["name"], norm(t["message"]))] += 1
            L += [f"### {p}, band {band}: {len(refuted)} REFUTED planets (of 500, both noise models)", ""]
            L += md_table(["fatal test FAIL", "planets"], [[k, v] for k, v in tests.most_common()])
            L += [""]
            L += md_table(["combination", "planets"], [[k, v] for k, v in combos.most_common(8)])
            L += [""]
            L += md_table(["test", "message (numbers as #)", "n"],
                          [[k[0], k[1], v] for k, v in msgs.most_common(8)])
            L += [""]
            ident = collections.Counter()
            for i in refuted:
                c = X[p][i]["i"]
                key = "candidate = injected signal" if c["signal_identity"] else "candidate = another signal"
                for t in fatal_fails(c) or [{"name": "(none)"}]:
                    ident[(key, t["name"])] += 1
            L += md_table(["signal identity", "fatal test FAIL", "planets"],
                          [[*k, v] for k, v in sorted(ident.items())])
            L += [""]
            by_noise_mech = collections.Counter()
            for i in refuted:
                for t in fatal_fails(X[p][i]["i"]):
                    by_noise_mech[(by_id[i]["noise"], by_id[i]["mechanism"], t["name"])] += 1
            L += md_table(["noise", "mechanism", "fatal test FAIL", "n"],
                          [[*k, v] for k, v in sorted(by_noise_mech.items())])
            L += [""]

    # (c) variability_some_years.
    L += ["## c) `variability_some_years` planets", ""]
    for p in POINTS:
        fam = [e["id"] for e in cases if e["class"] == "planet" and e["mechanism"] == "variability_some_years"]
        vs = collections.Counter(X[p][i]["i"]["verdict"] for i in fam)
        tests = collections.Counter()
        msgs = collections.Counter()
        period_match = collections.Counter()
        to_planet, to_var = [], []
        for i in fam:
            c = X[p][i]["i"]
            for t in fatal_fails(c):
                tests[t["name"]] += 1
                msgs[(t["name"], norm(t["message"]))] += 1
            cand = c["candidate"] or {}
            pr = by_id[i]["parameters"]
            if cand.get("period"):
                to_planet.append(cand["period"] / pr["period"])
                to_var.append(cand["period"] / pr["var_period"])
            period_match["signal identity" if c["signal_identity"] else "no signal identity"] += 1
        L += [f"### {p}: {len(fam)} cases, verdicts {dict(vs)}; {dict(period_match)}", ""]
        L += [
            "- ratio of the found period to the planet period (sorted sample): "
            + ", ".join(fmt(x, 4) for x in sorted(to_planet)[:: max(1, len(to_planet) // 12)]),
            "- ratio of the found period to the variability period (sorted sample): "
            + ", ".join(fmt(x, 4) for x in sorted(to_var)[:: max(1, len(to_var) // 12)]),
            "",
        ]
        L += md_table(["fatal test FAIL", "cases"], [[k, v] for k, v in tests.most_common()])
        L += [""]
        L += md_table(["test", "message (numbers as #)", "n"], [[k[0], k[1], v] for k, v in msgs.most_common(10)])
        L += [""]

    # (d) C2 white variability_masked and C3 planets white two_years / few_train.
    L += ["## d) C2 white (`variability_masked`) and C3 of white planets (`two_years`, `few_train`)", ""]
    for p in POINTS:
        fam = [e["id"] for e in cases if e["class"] == "false_positive" and e["mechanism"] == "variability_masked"
               and e["noise"] == "white" and e["band"] == "measurable"]
        vno = collections.Counter(X[p][i]["i"]["verdict_without_eb_catalog"] for i in fam)
        ident = collections.Counter(bool(X[p][i]["i"]["signal_identity"]) for i in fam)
        ratios = []
        for i in fam:
            cand = X[p][i]["i"]["candidate"] or {}
            if cand.get("period"):
                ratios.append(cand["period"] / by_id[i]["parameters"]["period"])
        var_ratio = []
        for i in fam:
            cand = X[p][i]["i"]["candidate"] or {}
            vp = by_id[i]["parameters"].get("var_period")
            if cand.get("period") and vp:
                var_ratio.append(cand["period"] / vp)
        tests = collections.Counter()
        for i in fam:
            for t in fatal_fails(X[p][i]["i"]):
                tests[t["name"]] += 1
        L += [f"### {p}, `variability_masked` false positives, measurable, white ({len(fam)} cases)", ""]
        L += [
            f"- verdict without `eb_catalog`: {dict(vno)}",
            f"- signal identity (found period = f x eclipse period, f in 1, 2, 1/2, tolerance 0.001): {dict(ident)}",
            "- ratio of the found period to the injected eclipse period: "
            + (", ".join(fmt(x, 3) for x in sorted(ratios)[:: max(1, len(ratios) // 12)]) if ratios else "no candidate"),
            "- ratio of the found period to the injected variability period: "
            + (", ".join(fmt(x, 3) for x in sorted(var_ratio)[:: max(1, len(var_ratio) // 12)]) if var_ratio else "the variability period is not in the manifest parameters"),
            f"- fatal tests FAIL (condition i): {dict(tests.most_common())}",
            "",
        ]
        for mech in ("two_years", "few_train"):
            fam = [e["id"] for e in cases if e["class"] == "planet" and e["mechanism"] == mech
                   and e["noise"] == "white" and e["band"] == "measurable"]
            inc = [i for i in fam if X[p][i]["i"]["verdict"] == "INCONCLUSIVE"]
            tests = collections.Counter()
            msgs = collections.Counter()
            for i in inc:
                for t in X[p][i]["i"]["tests"]:
                    if t["status"] == "INCONCLUSIVE":
                        tests[t["name"]] += 1
                        msgs[(t["name"], norm(t["message"]))] += 1
                for r in X[p][i]["i"]["holdout_rounds"]:
                    if r["status"] == "INCONCLUSIVE":
                        msgs[("holdout round", norm(r["message"]))] += 1
            L += [f"### {p}, `{mech}` planets, measurable, white: {len(inc)} of {len(fam)} INCONCLUSIVE", ""]
            L += md_table(["test INCONCLUSIVE", "cases"], [[k, v] for k, v in tests.most_common()])
            L += [""]
            L += md_table(["source", "message (numbers as #)", "n"], [[k[0], k[1], v] for k, v in msgs.most_common(10)])
            L += [""]

    # (e) examples.
    L += ["## e) Example cases (3 per pattern, M3, condition i)", ""]

    def show(i: str, names: list[str] | None = None) -> list[str]:
        e = by_id[i]
        c = X["M3"][i]["i"]
        pr = e["parameters"]
        cand = c["candidate"] or {}
        out = [
            f"- `{i}` ({e['class']}, {e['band']}, {e['noise']}, {e['mechanism']}): verdict {c['verdict']}; "
            f"injected P={fmt(pr.get('period'), 7)} d, depth={fmt(pr.get('depth'), 4)}, t0={fmt(pr.get('t0'), 8)}; "
            f"candidate P={fmt(cand.get('period'), 7)}, depth={fmt(cand.get('depth_ppm'), 4)} ppm, SNR={fmt(cand.get('snr'), 3)}; "
            f"identity={c['signal_identity']}, without eb_catalog={c['verdict_without_eb_catalog']}"
        ]
        for t in c["tests"]:
            if (names and t["name"] in names) or (not names and t["status"] in ("FAIL", "INCONCLUSIVE")):
                m = ", ".join(f"{k}={fmt(v, 4)}" for k, v in list(t["metrics"].items())[:8])
                out.append(f"  - {t['name']} {t['status']} ({t['severity']}): {t['message']} [{m}]")
        return out

    patterns = []
    for band in ("below", "near", "measurable"):
        ref = [e["id"] for e in cases if e["class"] == "planet" and e["band"] == band
               and e["mechanism"] != "variability_some_years" and X["M3"][e["id"]]["i"]["verdict"] == "REFUTED"]
        top = collections.Counter(t["name"] for i in ref for t in fatal_fails(X["M3"][i]["i"])).most_common(1)
        if top:
            name = top[0][0]
            ex = [i for i in ref if any(t["name"] == name for t in fatal_fails(X["M3"][i]["i"]))][:3]
            patterns.append((f"{band} planets REFUTED by `{name}` (outside variability_some_years)", ex))
    vsy = [e["id"] for e in cases if e["class"] == "planet" and e["mechanism"] == "variability_some_years"][:3]
    patterns.append(("`variability_some_years` planets", vsy))
    vm = [e["id"] for e in cases if e["class"] == "false_positive" and e["mechanism"] == "variability_masked"
          and e["noise"] == "white" and e["band"] == "measurable"][:3]
    patterns.append(("`variability_masked` false positives, white, measurable", vm))
    for mech in ("two_years", "few_train"):
        inc = [e["id"] for e in cases if e["class"] == "planet" and e["mechanism"] == mech and e["noise"] == "white"
               and e["band"] == "measurable" and X["M3"][e["id"]]["i"]["verdict"] == "INCONCLUSIVE"][:3]
        patterns.append((f"`{mech}` planets, measurable, white, INCONCLUSIVE", inc))
    for title, ex in patterns:
        L += [f"### {title}", ""]
        for i in ex:
            L += show(i)
        L += [""]

    # (f) sanity of the synthetic population: below planets (and the other bands for reference).
    L += ["## f) Sanity of the synthetic population (planets)", ""]
    L += [
        "In the manifest, `expected_snr` holds the expected SNR **per unit depth** (c_k of "
        "section 3): SNR_k = depth x c_k. Recomputed here: r = min(global/7.1, train(y)/7.1, "
        "hidden(y)/5.0) x depth, compared with the recorded `r_actual` and with the band. The "
        "recovery uses the M3 candidate and only the cases in which it is the injected signal with "
        "factor 1 (rows `[f=1]`): the period (ratio - 1), the depth (candidate / depth of the "
        "injected trapezoid, which is not the mean box depth), Refute's SNR / expected global SNR "
        "(different definitions: the ratio only describes), the ephemeris (phase distance of the "
        "candidate t0 from the injected t0, in durations) and the duration.",
        "",
    ]
    for band in ("below", "near", "measurable"):
        rows_stat = collections.defaultdict(list)
        bad_band, bad_r, n = [], [], 0
        for e in cases:
            if e["class"] != "planet" or e["band"] != band:
                continue
            n += 1
            pr, es = e["parameters"], e["expected_snr"]
            d = pr["depth"]
            ratios = [es["global"] * d / SNR_GATE]
            ratios += [v * d / SNR_GATE for v in (es.get("train") or {}).values()]
            ratios += [v * d / HIDDEN_MIN for v in (es.get("hidden") or {}).values()]
            r = min(ratios)
            if abs(r - pr["r_actual"]) > 1e-9 * max(1.0, r):
                bad_r.append(e["id"])
            in_band = (r < 1.0) if band == "below" else (1.0 <= r < 1.5) if band == "near" else (r >= 1.5)
            if not in_band:
                bad_band.append(e["id"])
            rows_stat["r"].append(r)
            rows_stat["expected_global_snr"].append(es["global"] * d)
            c = X["M3"][e["id"]]["i"]
            cand = c["candidate"] or {}
            rows_stat["signal identity (fraction, all)"].append(1.0 if c["signal_identity"] else 0.0)
            gate = next((t for t in c["tests"] if t["name"] == "snr"), None)
            rows_stat["Refute snr gate PASS (fraction, all)"].append(
                1.0 if gate and gate["status"] == "PASS" else 0.0
            )
            if cand.get("period") and c["signal_identity"] and abs(c["identity_factor"] - 1.0) < 1e-12:
                P = cand["period"]
                rows_stat["[f=1] P_found/P_injected - 1"].append(P / pr["period"] - 1)
                rows_stat["[f=1] depth_found/depth_injected"].append(cand["depth_ppm"] * 1e-6 / d)
                rows_stat[f"[f=1] measured_SNR/expected_global_SNR, {e['noise']}"].append(
                    cand["snr"] / (es["global"] * d)
                )
                dur = pr["duration"]
                ph = ((cand["t0"] - pr["t0"]) / pr["period"]) % 1.0
                ph = min(ph, 1 - ph)
                rows_stat["[f=1] |dt0| in durations (phase)"].append(ph * pr["period"] / dur)
                rows_stat["[f=1] duration_found/injected"].append(cand["duration_hours"] / 24 / dur)
        L += [f"### band {band}: {n} planets", ""]
        L += [
            f"- r recomputed equal to the recorded `r_actual`: {n - len(bad_r)} of {n}"
            + (f" (differ: {bad_r[:5]})" if bad_r else ""),
            f"- r inside the declared band: {n - len(bad_band)} of {n}" + (f" (outside: {bad_band[:5]})" if bad_band else ""),
        ]
        rows = []
        for k in [k for k in rows_stat if "fraction" in k]:
            vals = rows_stat.pop(k)
            L.append(f"- {k}: {sum(vals) / len(vals):.3f} ({int(sum(vals))} of {len(vals)})")
        for k, vals in rows_stat.items():
            v = sorted(vals)
            q = lambda x: v[min(len(v) - 1, int(x * (len(v) - 1)))]  # noqa: E731
            rows.append([k, len(v), fmt(v[0]), fmt(q(0.1)), fmt(q(0.5)), fmt(q(0.9)), fmt(v[-1])])
        L += [""] + md_table(["quantity", "n", "min", "p10", "median", "p90", "max"], rows) + [""]
        if band == "below":
            which = collections.Counter()
            for e in cases:
                if e["class"] != "planet" or e["band"] != "below":
                    continue
                pr, es = e["parameters"], e["expected_snr"]
                d = pr["depth"]
                opts = {"global": es["global"] * d / SNR_GATE}
                opts.update({f"train {y}": v * d / SNR_GATE for y, v in (es.get("train") or {}).items()})
                opts.update({f"hidden {y}": v * d / HIDDEN_MIN for y, v in (es.get("hidden") or {}).items()})
                kind = min(opts, key=opts.get).split()[0]
                which[(e["mechanism"], kind, opts["global"] < 1.0)] += 1
            L += ["Which ratio sets the \"below\" band (the smallest), by mechanism, and whether the expected global SNR is also below 7.1:", ""]
            L += md_table(["mechanism", "smallest ratio", "global SNR < 7.1", "planets"],
                          [[*k, v] for k, v in sorted(which.items())])
            L += [""]
    L += OBSERVATIONS
    if OUT.exists():
        raise SystemExit(f"{OUT.name} exists; not replaced")
    OUT.write_text("\n".join(L) + "\n", encoding="utf-8", newline="\n")
    print(OUT, hashlib.sha256(OUT.read_bytes()).hexdigest(), OUT.stat().st_size)


if __name__ == "__main__":
    main()
