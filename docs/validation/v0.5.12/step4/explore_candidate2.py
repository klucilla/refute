"""v0.5.12 step 4, the second exploratory check: correction 2's estimator WITH the red term weighted
by each bin's variance (the maintainer's decision of #218 comment 7196269069, item 2). EXPLORATORY
and POST HOC: it decides nothing, is never in ``src/``, and the estimator is NOT adjusted after it.

    launch_v3 unit explore-candidate2:
        {python} -I -B docs/validation/v0.5.12/step4/explore_candidate2.py

**The estimator** is the text of ``docs/plans/v0.5.12-spec-correction-2.md`` section 4 (commit
``be14460``), computed by this script's own code on M1's frozen geometry (``step1/m1_common.py``):
- w = 1/sigma^2; the baseline is d(t, 0) > T, at least 10 points; m_b is its weighted mean;
- s^2 = sum_b w (f - m_b)^2 / (n_b - 1);
- bins of width T over the baseline from the first valid time, at least 2 points each, at least 3
  bins; mu_k is a bin's weighted mean, W_k its total weight, v_k = s^2 / W_k and u_k = 1 / v_k;
  mu_bar = sum u mu / sum u; Q = sum u (mu - mu_bar)^2; c = sum u - sum u^2 / sum u;
  sigma_r^2 = max(0, (Q - (M - 1)) / c);
- sigma_par^2 = s^2 / W_par + sigma_r^2 / N_par; OE_box per K25 Eq. (11); fail if OE_box > 3.

**The cases, NEW seeds** (different from 1..3000, 100001..103000, 200001..200300 and the first
check's 500001..501000 and 600001..600300):
- null: the seven families, seeds 700001 to 701000 (1,000 per family);
- sensitivity: the seven families, seeds 800001 to 800300, the odd box depth increased by
  5 * sqrt(1/sum(w_odd) + 1/sum(w_even)) over each parity's in-transit cadences (the control's
  rule).

**Pre-registered flags** (reported, never acted on before the Codex round):
- sensitivity below 281 of 300 in a family;
- null "above nominal": the 95 % Wilson lower bound of the null fail rate above the nominal
  erfc(3/sqrt(2)) = 0.0026998.

It writes ``explore-candidate2.json`` (copied to ``step4/``). Labels: exploratory, post hoc,
``method_status: not_validated``.
"""

from __future__ import annotations

import json
import math
import os
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "step1"))
import m1_common as mc  # noqa: E402

NULL_SEEDS = range(700001, 701001)
SENS_SEEDS = range(800001, 800301)
Z = 1.959963984540054
NOMINAL = math.erfc(3 / math.sqrt(2))


def wilson(k: int, n: int) -> tuple[float, float]:
    p = k / n
    den = 1 + Z * Z / n
    centre = p + Z * Z / (2 * n)
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))
    return (centre - half) / den, (centre + half) / den


def candidate_oe(t, f, s) -> float | None:
    w = 1.0 / s**2
    k = np.floor((t - mc.T0) / mc.P + 0.5)
    intr = np.abs(t - (mc.T0 + k * mc.P)) <= mc.T / 2.0
    d0 = np.abs(np.mod(t - mc.T0 + mc.P / 2.0, mc.P) - mc.P / 2.0)
    base = d0 > mc.T
    fb, wb, tb = f[base], w[base], t[base]
    nb = fb.size
    if nb < 10:
        return None
    mb = float(np.sum(wb * fb) / np.sum(wb))
    s2 = float(np.sum(wb * (fb - mb) ** 2) / (nb - 1))
    if not (math.isfinite(s2) and s2 > 0):
        return None
    idx = np.floor((tb - t.min()) / mc.T)
    mus, ws = [], []
    for m in np.unique(idx):
        sel = idx == m
        if sel.sum() < 2:
            continue
        mus.append(float(np.sum(wb[sel] * fb[sel]) / np.sum(wb[sel])))
        ws.append(float(np.sum(wb[sel])))
    if len(mus) < 3:
        return None
    mu, u = np.array(mus), np.array(ws) / s2
    mu_bar = float(np.sum(u * mu) / np.sum(u))
    q = float(np.sum(u * (mu - mu_bar) ** 2))
    c = float(np.sum(u) - np.sum(u**2) / np.sum(u))
    if not (math.isfinite(q) and math.isfinite(c) and c > 0):
        return None
    sig_r2 = max(0.0, (q - (mu.size - 1)) / c)
    out = {}
    for name, par in (("odd", 1), ("even", 0)):
        sel = intr & (np.mod(k, 2) == par)
        if sel.sum() < 3:
            return None
        wp = float(np.sum(w[sel]))
        m_in = float(np.sum(w[sel] * f[sel]) / wp)
        n_ep = int(np.unique(k[sel]).size)
        out[name] = (mb - m_in, s2 / wp + sig_r2 / n_ep)
    denom = math.sqrt(out["odd"][1] + out["even"][1])
    if not math.isfinite(denom) or denom <= 0:
        return None
    return abs(out["odd"][0] - out["even"][0]) / denom


def main() -> int:
    g = mc.geometry()
    k = np.floor((g["t"] - mc.T0) / mc.P + 0.5)
    odd_in = g["intr"] & (np.mod(k, 2) == 1)
    even_in = g["intr"] & (np.mod(k, 2) == 0)
    result = {}
    for fam in mc.FAMILIES:
        sig = mc.sigmas(g, fam)
        w = 1.0 / sig**2
        extra = 5.0 * math.sqrt(1.0 / w[odd_in].sum() + 1.0 / w[even_in].sum())
        rows = {"null": [], "sensitivity": []}
        plan = (("null", NULL_SEEDS, None), ("sensitivity", SENS_SEEDS, extra))
        for label, seeds, depth in plan:
            for seed in seeds:
                t, f, s = mc.curve(g, fam, seed, depth_odd_extra=depth)
                rows[label].append(candidate_oe(t, f, s))
        summary = {}
        for label, vals in rows.items():
            ok = [v for v in vals if v is not None]
            fails = sum(v > 3 for v in ok)
            lo, hi = wilson(fails, len(vals))
            summary[label] = {
                "n": len(vals),
                "not_computed": len(vals) - len(ok),
                "fail": fails,
                "oe_box_over_2": sum(v > 2 for v in ok),
                "wilson_95": [lo, hi],
            }
        summary["odd_depth_extra"] = extra
        summary["flags"] = {
            "sensitivity_below_281": summary["sensitivity"]["fail"] < 281,
            "null_above_nominal": summary["null"]["wilson_95"][0] > NOMINAL,
        }
        result[fam] = summary
    doc = {
        "schema": "refute-v0512-explore-candidate-2",
        "labels": ["exploratory", "post hoc", "method_status: not_validated"],
        "decision": "#218 comment 7196269069, item 2",
        "estimator": "docs/plans/v0.5.12-spec-correction-2.md section 4 at be14460",
        "seeds": {"null": [700001, 701000], "sensitivity": [800001, 800300]},
        "nominal": NOMINAL,
        "families": result,
    }
    out = Path(os.environ["REFUTE_RUN_OUT"]) / "explore-candidate2.json"
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    brief = {f: (v["null"]["fail"], v["sensitivity"]["fail"]) for f, v in result.items()}
    print(json.dumps({"null_fail_of_1000__sensitivity_fail_of_300": brief}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
