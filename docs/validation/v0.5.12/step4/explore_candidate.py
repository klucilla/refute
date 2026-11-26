"""v0.5.12 step 4, an exploratory check of the candidate noise estimator (the maintainer's decision
of #218 comment 7193864189, item 3). EXPLORATORY and POST HOC (after M1): it generates hypotheses
only, decides nothing, and is never in ``src/``.

    launch_v3 unit explore-candidate:
        {python} -I -B docs/validation/v0.5.12/step4/explore_candidate.py

**The candidate (the correction's draft [choice]),** computed here by its own code from the draft's
text, on the same frozen geometry as M1 (``step1/m1_common.py``):
- w = 1/sigma^2; the baseline is d(t, 0) > T (the specification's).
- **Scale:** s^2 = sum_b w (f - m_b)^2 / (n_b - 1), the baseline's reduced chi-square about its
  weighted mean m_b.
- **Red noise (K25 Eq. 3 form):** bins of width T over the baseline from the first valid time,
  n >= 2 per bin, at least 3 bins; each bin's weighted mean mu_k and total weight W_k;
  sigma_bin^2 = the UNWEIGHTED variance (ddof 1) of the mu_k; sigma_bin,xpt^2 = mean of s^2 / W_k;
  sigma_r^2 = max(0, sigma_bin^2 - sigma_bin,xpt^2).
- **Per parity (K25 Eq. 2 form):** sigma_par^2 = s^2 / W_par + sigma_r^2 / N_par, with W_par the
  total weight of that parity's in-transit points and N_par its number of epochs.
- **OE_box** = |delta_odd - delta_even| / sqrt(sigma_odd^2 + sigma_even^2), delta_par = m_b minus
  the parity's in-transit weighted mean (K25 Eq. 11); fail if OE_box > 3.

**The cases, all NEW** (outside 1..3000, 100001..103000 and 200001..200300, never M1's, M2's or the
control's inputs):
- null: the seven families, seeds 500001 to 501000 (1,000 per family);
- sensitivity: the seven families, seeds 600001 to 600300, the odd box depth increased by
  5 * sqrt(1/sum(w_odd) + 1/sum(w_even)) over each parity's in-transit cadences.

It reports per family the fail counts (and OE_box > 2) of the candidate. It writes
``explore-candidate.json`` (copied to ``step4/``). Labels: exploratory, post hoc,
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

NULL_SEEDS = range(500001, 501001)
SENS_SEEDS = range(600001, 600301)


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
    sig_bin2 = float(np.var(np.array(mus), ddof=1))
    xpt2 = float(np.mean(s2 / np.array(ws)))
    sig_r2 = max(0.0, sig_bin2 - xpt2)
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
            summary[label] = {
                "n": len(vals),
                "not_computed": len(vals) - len(ok),
                "fail": sum(v > 3 for v in ok),
                "oe_box_over_2": sum(v > 2 for v in ok),
            }
        summary["odd_depth_extra"] = extra
        result[fam] = summary
    doc = {
        "schema": "refute-v0512-explore-candidate-1",
        "labels": ["exploratory", "post hoc", "method_status: not_validated"],
        "decision": "#218 comment 7193864189, item 3",
        "seeds": {"null": [500001, 501000], "sensitivity": [600001, 600300]},
        "families": result,
    }
    out = Path(os.environ["REFUTE_RUN_OUT"]) / "explore-candidate.json"
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    brief = {f: (v["null"]["fail"], v["sensitivity"]["fail"]) for f, v in result.items()}
    print(json.dumps({"null_fail_of_1000__sensitivity_fail_of_300": brief}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
