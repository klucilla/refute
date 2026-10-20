"""Diagnosis of the holdout's timing rule (the maintainer's decision of 2026-10-19, item 3a), from
records already examined only: the geometric lot of map Amendment 10
(``calc/option-a-geometry.json``: for each round, the measured ``sigma_T / T14`` of the rounds that
reached the geometry, or the rule's message with ``sigma_T`` and the duration), the decomposition of
Amendment 16 (``calc/interruptions-decomposition.json``) and H4 complement 2.

For each round the geometry is recomputed from the case's metadata (its layout, period, epoch and
duration, rebuilt deterministically by ``population_v2.build_case`` from the lot's prefix; no
analysis is run): the train transits ``N`` with data, their epochs, the farthest hidden epoch ``m``
from the train epochs' mean, and the geometric factor of a linear fit with equal errors,
``g = sqrt(1/N + m^2 / sum (x - mean)^2)``, so that ``sigma_T = sigma_t * g``. With the train SNR
``S`` (the manifest's expected SNR at the case's depth) and ``sigma_t / T14 = kappa sqrt(N) / S``:

    sigma_T / T14 = kappa * (g sqrt(N)) / S

``g sqrt(N)`` is the geometry (about ``sqrt(12) * dt / L`` when the hidden year is far from a
train baseline ``L``), ``S`` the train SNR, ``kappa`` what the timing measurement adds (the
transit's shape, the template, the noise beyond white). The rule's own factor is the threshold 1
(``max_timing_sigma_durations``). Read-only; writes timing-diagnosis.json next to this file.
"""

from __future__ import annotations

import json
import math
import re
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]  # the checkout (docs/validation/v0.2.1/reopen/calc)
CALC = ROOT / "docs" / "validation" / "v0.2.1" / "reopen" / "calc"
sys.path.insert(0, str(ROOT / "docs" / "validation" / "v0.2.1" / "population"))
OUT = HERE / "timing-diagnosis.json"
MESSAGE = re.compile(r"\(([0-9.]+) h\) exceeds ([0-9.]+) transit duration\(s\) \(([0-9.]+) h\)")


def geometry(entry: dict, data, hidden_year: int) -> dict:
    p = entry["parameters"]
    period, t0, dur = p["period"], p["t0"], p["duration"]
    time = data.lc.time
    years = data.lc.year
    train_t = time[years != hidden_year]
    epochs_train = []
    for n in range(
        math.floor((train_t.min() - t0) / period), math.ceil((train_t.max() - t0) / period) + 1
    ):
        tc = t0 + n * period
        inside = np.abs(train_t - tc) <= dur / 2
        if inside.sum() >= 0.5 * dur / (120 / 86400):
            epochs_train.append(n)
    spans = [(s.t_start, s.t_end) for s in data.sectors if s.year == hidden_year]
    epochs_hidden = [
        n
        for lo, hi in spans
        for n in range(math.ceil((lo - t0) / period), math.floor((hi - t0) / period) + 1)
    ]
    x = np.asarray(epochs_train, float)
    mean = float(x.mean()) if x.size else float("nan")
    sxx = float(((x - mean) ** 2).sum()) if x.size else float("nan")
    m = max((abs(n - mean) for n in epochs_hidden), default=float("nan"))
    n_train = len(epochs_train)
    g = math.sqrt(1.0 / n_train + m * m / sxx) if n_train >= 2 and sxx > 0 else float("nan")
    train_span = float(train_t.max() - train_t.min())
    far = max((abs(t0 + n * period - (t0 + mean * period)) for n in epochs_hidden), default=0.0)
    return {
        "n_train": n_train,
        "train_span_days": train_span,
        "distance_days": far,
        "lever": far / train_span if train_span > 0 else float("nan"),
        "g": g,
        "g_sqrt_n": g * math.sqrt(n_train) if n_train else float("nan"),
        "period_share": (m * m / sxx) / (1.0 / n_train + m * m / sxx) if n_train >= 2 else None,
        "duration_h": dur * 24,
    }


def main() -> None:
    import population_v3 as v3

    pv2 = v3.pv2
    lot = json.loads((CALC / "option-a-geometry.json").read_text(encoding="utf-8"))
    cases = {c["id"]: c for c in pv2.population_cases("confirm:" + lot["prefix"])}
    rows = []
    for c in lot["cases"]:
        case = cases[c["id"]]
        blob, entry = pv2.build_case(case)
        meta, arrays = pv2.deserialize(blob)
        data = pv2.parts_to_data(meta, arrays)
        for r in c["rounds"]:
            year = r["year"]
            ratio, source = None, None
            if r.get("max_sigma_t_over_t14") is not None:
                ratio, source = float(r["max_sigma_t_over_t14"]), "measured, passed"
            elif r.get("decided_before") and "timing uncertainty" in r["decided_before"]:
                mt = MESSAGE.search(r["decided_before"])
                ratio, source = float(mt.group(1)) / float(mt.group(3)), "measured, failed"
            geo = geometry(entry, data, year)
            snr = entry["parameters"]["depth"] * entry["expected_snr"]["train"][str(year)]
            row = {
                "case": c["id"],
                "mechanism": c["mechanism"],
                "noise": c["noise"],
                "band": case["band"],
                "hidden_year": year,
                "train_snr_expected": snr,
                "ratio": ratio,
                "ratio_source": source,
                "decided_before": r.get("decided_before"),
                **geo,
            }
            if ratio is not None and geo["g_sqrt_n"] == geo["g_sqrt_n"]:
                row["kappa"] = ratio * snr / geo["g_sqrt_n"]
            rows.append(row)

    def summary(sel):
        out = {"rounds": len(sel)}
        known = [r for r in sel if r["ratio"] is not None]
        out["with_ratio"] = len(known)
        out["failed_timing"] = sum(r["ratio_source"] == "measured, failed" for r in sel)
        for key in (
            "lever",
            "n_train",
            "g_sqrt_n",
            "train_snr_expected",
            "ratio",
            "kappa",
            "period_share",
        ):
            vals = [r[key] for r in known if r.get(key) is not None and r[key] == r[key]]
            out[f"median_{key}"] = statistics.median(vals) if vals else None
        return out

    groups = defaultdict(list)
    for r in rows:
        groups["all"].append(r)
        groups[f"mechanism={r['mechanism']}"].append(r)
        groups[f"noise={r['noise']}"].append(r)
        groups[f"band={r['band']}"].append(r)
        groups[f"mechanism={r['mechanism']},hidden={r['hidden_year']}"].append(r)
    known = [r for r in rows if r["ratio"] is not None and r.get("kappa")]
    # the share of the spread of log(ratio) carried by each term (variances and covariances)
    lr = np.log([r["ratio"] for r in known])
    terms = {
        "geometry log(g sqrt N)": np.log([r["g_sqrt_n"] for r in known]),
        "train SNR -log(S)": -np.log([r["train_snr_expected"] for r in known]),
        "timing measurement log(kappa)": np.log([r["kappa"] for r in known]),
    }
    total = float(np.var(lr))
    shares = {k: float(np.cov(v, lr, bias=True)[0, 1] / total) for k, v in terms.items()}
    # counterfactuals on the measured ratios (the rule's factor; a doubled train SNR)
    failed = [r for r in known if r["ratio_source"] == "measured, failed"]
    counter = {
        f"threshold {t:g} durations": sum(r["ratio"] <= t for r in failed) for t in (1.5, 2, 3, 5)
    }
    counter["train SNR doubled (threshold 1)"] = sum(r["ratio"] / 2 <= 1 for r in failed)
    out = {
        "note": "from records already examined; the geometry recomputed from the cases' metadata",
        "rounds": len(rows),
        "rounds_with_ratio": len(known),
        "failed_timing_rounds": len(failed),
        "log_ratio_variance": total,
        "log_ratio_variance_shares": shares,
        "failed_rounds_passing_under": counter,
        "groups": {k: summary(v) for k, v in sorted(groups.items())},
        "rows": rows,
    }
    OUT.write_text(json.dumps(out, indent=1, default=str) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1, default=str))


if __name__ == "__main__":
    main()
