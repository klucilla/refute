"""Item 3 (a) and (d, power) of the maintainer's decision of 2026-11-08 (#208): reading of the
recorded result of A0's second run. It runs nothing and uses no seed; it decides nothing.

**(a) The acceptance's rule** (docs/plans/v0.5.1-acceptance.md, section A0: a pull row failing in
a stratum makes the errors of that stratum not accepted; the decisive test relying on them is
INCONCLUSIVE). At run time only the coverage stratum and the sector count are known; the noise
model is not. So a run-time cell is accepted only if it holds under every noise model:

- ``strict``: no row of the cell is FAIL or NOT DECIDABLE;
- ``ignoring_nd``: no row of the cell is FAIL (the favourable reading: a NOT DECIDABLE row, which
  has no evidence either way, does not count against it).

The rows of a cell: per-event errors, A0.1 and A0.8's event rows; group statistics, A0.2, A0.4,
A0.5, A0.8's group rows (each where the statistic exists) and A0.7 (partial coverage).

**(d) The power of the limits.** For a perfectly calibrated Gaussian pull with the n of each
recorded row, the exact probability of each row passing its band is
``P(|m| <= 0.1) P(0.81 <= s^2 <= 1.21)`` (mean and variance independent); the expected count of
failing rows and the probability that every row passes (independence: an approximation, rows
sharing a curve are correlated) are compared with what was recorded. Each sabotage's rows are
compared with the same rows of the unsabotaged section.

Usage (from the project root): ``.venv/Scripts/python.exe <this file>``; writes
``strata.json`` next to it.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

from scipy import stats as st

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
RESULT = ROOT / "docs/validation/v0.5.1/acceptance/a0r2-result.json"
NOISES = ("white", "correlated", "long", "trend", "correlated_trend")
COVERAGE = ("full", "partial", "minimal")
SECTORS = ("2", "3", "4")
TESTS = {
    "single_event, event_consistency": ("per_event",),
    "odd_even (decisive statistic)": ("matched_diff",),
    "odd_even (the three statistics it reports)": (
        "matched_diff",
        "matched_odd",
        "matched_even",
    ),
    "aperture_depth": ("large_minus_core",),
    "systematics": ("sap_minus_expected",),
}


def flatten(node, path, out):
    if isinstance(node, dict):
        if "result" in node and ("sd" in node or "mean" in node):
            out.append(("/".join(path), node))
            return
        for k, v in node.items():
            flatten(v, [*path, str(k)], out)


def cell_rows(bands):
    """{(statistic, coverage, sectors or None, noise): [(row name, band), ...]}."""
    cells: dict = {}

    def add(stat, cov, sec, noise, name, band):
        cells.setdefault((stat, cov, sec, noise), []).append((name, band))

    for path, band in bands:
        p = path.split("/")
        sec_name, kind = p[0], p[1]
        if sec_name == "a01" and kind == "bands":
            add("per_event", p[3], None, p[2], path, band)
        elif sec_name == "a08" and kind == "event_bands":
            add("per_event", p[3], None, p[2], path, band)
        elif sec_name in ("a02", "a04") and kind == "bands":
            add(p[5], p[3], p[4], p[2], path, band)
        elif sec_name == "a05" and kind == "bands":
            add(p[8], p[6], p[7], p[5], path, band)
        elif sec_name == "a08" and kind == "group_bands":
            add(p[8], p[4], p[5], p[3], path, band)
    return cells


def accepted(rows, strict):
    results = [b["result"] for _, b in rows]
    if not results or "FAIL" in results:
        return False
    return not (strict and "NOT DECIDABLE" in results)


def runtime_table(cells, a07):
    out = {}
    stats = sorted({k[0] for k in cells})
    for stat in stats:
        per_event = stat == "per_event"
        for cov in COVERAGE:
            for sec in (None,) if per_event else SECTORS:
                rows_by_noise = {n: cells.get((stat, cov, sec, n), []) for n in NOISES}
                extra = []
                if not per_event and cov == "partial":
                    extra = [
                        (f"a07/{sec}/{stat}", a07[f"{sec}/partial/{stat}"])
                        for _ in [0]
                        if f"{sec}/partial/{stat}" in a07
                    ]
                key = f"{stat}|{cov}|{sec or '-'}"
                per_noise = {}
                for n, rows in rows_by_noise.items():
                    fails = sum(b["result"] == "FAIL" for _, b in rows)
                    nd = sum(b["result"] == "NOT DECIDABLE" for _, b in rows)
                    per_noise[n] = {"rows": len(rows), "fail": fails, "not_decidable": nd}
                all_rows = [r for rows in rows_by_noise.values() for r in rows] + extra
                decidable = [
                    b
                    for _, b in all_rows
                    if b["result"] in ("PASS", "FAIL") and (b.get("n") or 0) > 2
                ]
                base_prefix = "a01/" if per_event else "a02/"
                base = [b for name, b in all_rows if name.startswith(base_prefix)]
                out[key] = {
                    "probability_accepted_if_perfectly_calibrated": math.exp(
                        sum(math.log(pass_probability(int(b["n"]))[0]) for b in decidable)
                    ),
                    "base_row_only_ignoring_nd": bool(base)
                    and all(b["result"] != "FAIL" for b in base),
                    "strict": all(accepted(r + extra, True) for r in rows_by_noise.values()),
                    "ignoring_nd": all(accepted(r + extra, False) for r in rows_by_noise.values()),
                    "white_only_ignoring_nd": accepted(rows_by_noise["white"] + extra, False),
                    "per_noise": per_noise,
                    "a07_result": extra[0][1]["result"] if extra else None,
                    "rows": len(all_rows),
                }
    return out


def decisive_map(table):
    out = {}
    for test, stats in TESTS.items():
        keys = {}
        for key, cell in table.items():
            stat, cov, sec = key.split("|")
            if stat in stats:
                keys.setdefault(f"{cov}|{sec}", []).append(cell)
        out[test] = {
            k: {
                "strict": all(c["strict"] for c in v),
                "ignoring_nd": all(c["ignoring_nd"] for c in v),
                "white_only_ignoring_nd": all(c["white_only_ignoring_nd"] for c in v),
            }
            for k, v in sorted(keys.items())
        }
        for reading in ("strict", "ignoring_nd", "white_only_ignoring_nd"):
            out[test][f"accepted_cells_{reading}"] = sum(
                v[reading] for k, v in out[test].items() if "|" in k
            )
        out[test]["cells"] = sum("|" in k for k in out[test])
    return out


def pass_probability(n):
    """Exact probability that a perfectly calibrated Gaussian pull passes both bands, n draws."""
    mean = 2.0 * st.norm.cdf(0.1 * math.sqrt(n)) - 1.0
    dof = n - 1
    sd = st.chi2.cdf(1.21 * dof, dof) - st.chi2.cdf(0.81 * dof, dof)
    return mean * sd, mean, sd


def power(bands):
    out = {}
    rows = [
        (p, b)
        for p, b in bands
        if b["result"] in ("PASS", "FAIL") and not p.startswith(("sabotage", "a07/forced"))
    ]
    for sec in ("a01", "a02", "a04", "a05", "a07", "a08", "all"):
        chosen = [(p, b) for p, b in rows if sec == "all" or p.startswith(sec + "/")]
        probs = [pass_probability(int(b["n"]))[0] for _, b in chosen if b.get("n") and b["n"] > 2]
        log_all = sum(math.log(q) for q in probs)
        out[sec] = {
            "decidable_rows": len(chosen),
            "recorded_fail": sum(b["result"] == "FAIL" for _, b in chosen),
            "expected_fail_if_perfectly_calibrated": round(sum(1 - q for q in probs), 2),
            "probability_every_row_passes_if_perfectly_calibrated": math.exp(log_all),
        }
    out["per_row_at_n"] = {
        str(n): {
            "pass": round(pass_probability(n)[0], 4),
            "mean_band": round(pass_probability(n)[1], 4),
            "sd_band": round(pass_probability(n)[2], 4),
        }
        for n in (100, 200, 310, 400, 800, 1600)
    }
    return out


def sabotage_vs_baseline(bands):
    by = dict(bands)
    out = {}
    for path, band in bands:
        if not path.startswith("sabotage-"):
            continue
        sab, _, rest = path.split("/", 2)
        name = sab.removeprefix("sabotage-")
        base_path = {
            "model_errors_alone": f"a01/bands/{rest}",
            "neff_equals_n": f"a01/bands/{rest}",
            "rho_zero": f"a02/bands/{rest}",
            "pool_sectors": f"a04/bands/{rest}",
        }.get(name)
        if name == "force_phase_half":
            parts = rest.split("/")
            base_path = f"a08/event_bands/{parts[0]}/{parts[1]}/4/{parts[2]}"
        base = by.get(base_path)
        out.setdefault(name, []).append(
            {
                "row": rest,
                "sabotaged": {k: band.get(k) for k in ("mean", "sd", "n", "result")},
                "baseline": {k: base.get(k) for k in ("mean", "sd", "n", "result")}
                if base
                else None,
            }
        )
    for name, rows in list(out.items()):
        paired = [
            r
            for r in rows
            if r["baseline"] and r["baseline"].get("sd") is not None and r["sabotaged"].get("sd")
        ]
        diffs = [r["sabotaged"]["sd"] - r["baseline"]["sd"] for r in paired]
        n = len(diffs)
        mean = sum(diffs) / n if n else None
        se = math.sqrt(sum((d - mean) ** 2 for d in diffs) / (n - 1) / n) if n > 1 else None
        out[name] = {
            "rows": rows,
            "paired_rows": n,
            "mean_sd_sabotaged_minus_baseline": mean,
            "se_of_that_mean_over_rows": se,
            "rows_failing_sabotaged": sum(r["sabotaged"]["result"] == "FAIL" for r in paired),
            "rows_failing_baseline": sum(r["baseline"]["result"] == "FAIL" for r in paired),
        }
    return out


def main():
    data = json.loads(RESULT.read_text("utf-8"))
    bands = []
    flatten(data["sections"], [], bands)
    a07 = {
        k.split("rule_bands/")[1]: v
        for k, v in ((p, b) for p, b in bands)
        if k.startswith("a07/rule_bands/")
    }
    cells = cell_rows(bands)
    table = runtime_table(cells, a07)
    doc = {
        "label": "development reading of the recorded A0 second run; it decides nothing",
        "method_status": "not_validated",
        "source": "docs/validation/v0.5.1/acceptance/a0r2-result.json",
        "runtime_cells": table,
        "tests": decisive_map(table),
        "power": power(bands),
        "sabotage_vs_baseline": sabotage_vs_baseline(bands),
        "sabotage_detected": data["sabotage_detected"],
    }
    (HERE / "strata.json").write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8")
    print(json.dumps({"tests": doc["tests"], "power": doc["power"]}, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
