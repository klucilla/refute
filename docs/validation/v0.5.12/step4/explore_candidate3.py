"""v0.5.12 step 4, the third exploratory check: correction 2's revision 1 (the effective epoch
count of the blind review's B1, alternative A) under red noise (the maintainer's decision of #218
comment 7197099779, item 4). EXPLORATORY and POST HOC: it decides nothing, is never in ``src/``,
and the estimator is NOT adjusted after it; its result goes to Codex's round 3 as a fact.

    launch_v3 unit explore-candidate3:
        {python} -I -B docs/validation/v0.5.12/step4/explore_candidate3.py

**The estimator** is the text of ``docs/plans/v0.5.12-spec-correction-2-r1.md`` section 4,
computed by this script's own code on M1's frozen geometry (``step1/m1_common.py``):
- w = 1/sigma^2; the baseline is d(t, 0) > T, at least 10 points; m_b is its weighted mean;
- s^2 = sum_b w (f - m_b)^2 / (n_b - 1); not computed unless finite and > 0;
- bins of width T over the baseline from the first valid time, at least 2 points each, at least 3
  bins; W_k a bin's total weight, mu_k its weighted mean; B = sum W_k;
  mu_bar = sum W_k mu_k / B; Q0 = sum W_k (mu_k - mu_bar)^2;
  C = 2 sum_k W_k (sum_{j<k} W_j) / B (the positive prefix sum); not computed unless C > 0;
  sigma_r^2 = max(0, (Q0 - s^2 (M - 1)) / C);
- per parity (at least 3 in-transit points): W_par,e the in-transit weight of epoch e,
  W_par = sum_e W_par,e, N_eff,par = W_par^2 / sum_e W_par,e^2;
  sigma_par^2 = s^2 / W_par + sigma_r^2 / N_eff,par;
- OE_box = |m_in,odd - m_in,even| / sqrt(sigma_odd^2 + sigma_even^2); fail if OE_box > 3.
For comparison only, the same curves are also scored with the reviewed form,
sigma_r^2 / N_par (``npar_form``); revision 1's counts are the check's result.

**The cells:** eight families x three red levels.
- The families: M1's seven (U, S9.5, P2.4, P9.5, T2, T6, B6) and the noisy-sector family
  ``S3-9.5``: sigma x 9.5 on every cadence later than one third of the time span, the M1-geometry
  form of the blind reviewer's "S3", the family with its highest null rate.
- **The red noise:** one Gaussian offset per block, added to the flux (``flux_err`` unchanged):
  each transit epoch's in-transit window (|t - (t0 + kP)| <= T/2) is one block, one offset per
  transit epoch; every other cadence is in the block of its width-T bin from the first time (the
  estimator's bins). sigma_r = 0, 3e-4 and 1e-3, that is 0, 0.5 and 5/3 of sigma0 = 6e-4. The
  offsets come from ``default_rng([seed, 222, 2])``, a stream apart from M1's white noise
  ``default_rng([seed, 222])``.
- **The curves, NEW seeds** (none used before, the blind reviewer's 20261126-20261130,
  20261426-20261430 and 20262126-20262130 included): for red level j = 0, 1, 2, null seeds
  20263001 + 10000 j to 20264000 + 10000 j (1,000 per cell) and sensitivity seeds
  20268001 + 10000 j to 20268300 + 10000 j (300 per cell). The families share the seeds, as in M1.
- **Sensitivity, under the control's rule:** the odd box depth increased by
  5 * sqrt(1/sum(w_odd) + 1/sum(w_even)) over each parity's in-transit cadences (white weights
  only, the control's rule unchanged).

**Pre-registered flags** (reported, never acted on):
- sensitivity below 281 of 300 in a cell;
- null "above nominal": the 95 % Wilson lower bound of the null fail rate above the nominal
  erfc(3/sqrt(2)) = 0.0026998.

It writes ``explore-candidate3.json`` (copied to ``step4/``). Labels: exploratory, post hoc,
``method_status: not_validated``. Its limits: one geometry; red blocks aligned with the
estimator's bins and the transit windows; synthetic boxes only.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "step1"))
import m1_common as mc  # noqa: E402

ROOT = HERE.parents[3]
SPEC = "docs/plans/v0.5.12-spec-correction-2-r1.md"
FAMILIES = (*mc.FAMILIES, "S3-9.5")
RED = (0.0, 3e-4, 1e-3)
Z = 1.959963984540054
NOMINAL = math.erfc(3 / math.sqrt(2))
WORKERS = 8


def null_seeds(j: int) -> range:
    return range(20263001 + 10000 * j, 20264001 + 10000 * j)


def sens_seeds(j: int) -> range:
    return range(20268001 + 10000 * j, 20268301 + 10000 * j)


def wilson(k: int, n: int) -> tuple[float, float]:
    p = k / n
    den = 1 + Z * Z / n
    centre = p + Z * Z / (2 * n)
    half = Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n))
    return (centre - half) / den, (centre + half) / den


def sigmas(g: dict, family: str) -> np.ndarray:
    if family != "S3-9.5":
        return mc.sigmas(g, family)
    t = g["t"]
    s = np.full(t.size, mc.SIGMA0)
    s[t > t.min() + (t.max() - t.min()) / 3.0] = 9.5 * mc.SIGMA0
    return s


def blocks(g: dict) -> np.ndarray:
    """One integer label per cadence: its transit epoch's window, else its width-T bin."""
    t = g["t"]
    k = np.floor((t - mc.T0) / mc.P + 0.5).astype(np.int64)
    b = np.floor((t - t.min()) / mc.T).astype(np.int64)
    key = np.where(g["intr"], k - k.min(), (k.max() - k.min() + 1) + b)
    return np.unique(key, return_inverse=True)[1].ravel()


def curve(g, labels, family, seed, red, depth_odd_extra=None):
    """M1's recipe (``m1_common.curve``, the same lines) with this check's families, plus red."""
    t = g["t"]
    box = np.where(g["intr"], 1.0 - mc.DEPTH, 1.0)
    if depth_odd_extra is not None:
        box = box - np.where(g["intr"] & g["odd"], depth_odd_extra, 0.0)
    s = sigmas(g, family)
    z = np.random.default_rng([seed, mc.STREAM]).standard_normal(t.size)
    f = box + s * z
    if red > 0:
        r = np.random.default_rng([seed, mc.STREAM, 2]).standard_normal(int(labels.max()) + 1)
        f = f + red * r[labels]
    return t, f, s


def score(t, f, s):
    """(OE_box of revision 1, OE_box of the N_par form, sigma_r) or None when not computed."""
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
    mu, wk = np.array(mus), np.array(ws)
    big_b = float(np.sum(wk))
    mu_bar = float(np.sum(wk * mu) / big_b)
    q0 = float(np.sum(wk * (mu - mu_bar) ** 2))
    prefix = np.concatenate(([0.0], np.cumsum(wk)[:-1]))
    c = float(2.0 * np.sum(wk * (prefix / big_b)))
    if not (math.isfinite(q0) and math.isfinite(c) and c > 0):
        return None
    sig_r2 = max(0.0, (q0 - s2 * (mu.size - 1)) / c)
    out = {}
    for name, par in (("odd", 1), ("even", 0)):
        sel = intr & (np.mod(k, 2) == par)
        if sel.sum() < 3:
            return None
        wp = float(np.sum(w[sel]))
        m_in = float(np.sum(w[sel] * f[sel]) / wp)
        eps, inv = np.unique(k[sel], return_inverse=True)
        we = np.bincount(inv.ravel(), weights=w[sel])
        n_eff = wp**2 / float(np.sum(we**2))
        out[name] = (mb - m_in, s2 / wp + sig_r2 / n_eff, s2 / wp + sig_r2 / eps.size)
    res = []
    for col in (1, 2):
        denom = math.sqrt(out["odd"][col] + out["even"][col])
        if not math.isfinite(denom) or denom <= 0:
            return None
        res.append(abs(out["odd"][0] - out["even"][0]) / denom)
    return res[0], res[1], math.sqrt(sig_r2)


def cell(args) -> dict:
    family, j = args
    red = RED[j]
    g = mc.geometry()
    labels = blocks(g)
    k = np.floor((g["t"] - mc.T0) / mc.P + 0.5)
    odd_in = g["intr"] & (np.mod(k, 2) == 1)
    even_in = g["intr"] & (np.mod(k, 2) == 0)
    w = 1.0 / sigmas(g, family) ** 2
    extra = 5.0 * math.sqrt(1.0 / w[odd_in].sum() + 1.0 / w[even_in].sum())
    summary = {"family": family, "sigma_r": red, "sigma_r_over_sigma0": red / mc.SIGMA0}
    plan = (("null", null_seeds(j), None), ("sensitivity", sens_seeds(j), extra))
    for label, seeds, depth in plan:
        vals = [score(*curve(g, labels, family, s, red, depth)) for s in seeds]
        ok = [v for v in vals if v is not None]
        fails = sum(v[0] > 3 for v in ok)
        lo, hi = wilson(fails, len(vals))
        summary[label] = {
            "seeds": [seeds.start, seeds.stop - 1],
            "n": len(vals),
            "not_computed": len(vals) - len(ok),
            "fail": fails,
            "oe_box_over_2": sum(v[0] > 2 for v in ok),
            "wilson_95": [lo, hi],
            "npar_form_fail": sum(v[1] > 3 for v in ok),
            "median_sigma_r_hat": float(np.median([v[2] for v in ok])) if ok else None,
        }
    summary["odd_depth_extra"] = extra
    summary["flags"] = {
        "sensitivity_below_281": summary["sensitivity"]["fail"] < 281,
        "null_above_nominal": summary["null"]["wilson_95"][0] > NOMINAL,
    }
    return summary


def main() -> int:
    spec_sha = hashlib.sha256((ROOT / SPEC).read_bytes()).hexdigest()
    g = mc.geometry()
    labels = blocks(g)
    base = np.abs(np.mod(g["t"] - mc.T0 + mc.P / 2.0, mc.P) - mc.P / 2.0) > mc.T
    per_bin = np.bincount(np.floor((g["t"][base] - g["t"].min()) / mc.T).astype(np.int64))
    k = np.floor((g["t"] - mc.T0) / mc.P + 0.5)
    jobs = [(fam, j) for j in range(len(RED)) for fam in FAMILIES]
    with ProcessPoolExecutor(max_workers=WORKERS) as pool:
        cells = list(pool.map(cell, jobs))
    doc = {
        "schema": "refute-v0512-explore-candidate-3",
        "labels": ["exploratory", "post hoc", "method_status: not_validated"],
        "decision": "#218 comment 7197099779, item 4",
        "estimator": f"{SPEC} section 4",
        "estimator_file_sha256": spec_sha,
        "geometry": {
            "cadences": int(g["t"].size),
            "red_blocks": int(labels.max()) + 1,
            "transit_epochs": int(np.unique(k[g["intr"]]).size),
            "median_cadences_per_baseline_bin": float(np.median(per_bin[per_bin > 0])),
            "sigma0": mc.SIGMA0,
        },
        "nominal": NOMINAL,
        "workers": WORKERS,
        "cells": cells,
    }
    out = Path(os.environ["REFUTE_RUN_OUT"]) / "explore-candidate3.json"
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    brief = {
        f"{c['family']}@{c['sigma_r']:g}": (
            c["null"]["fail"],
            c["sensitivity"]["fail"],
            c["null"]["npar_form_fail"],
        )
        for c in cells
    }
    print(json.dumps({"null_fail__sens_fail__npar_null_fail": brief}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
