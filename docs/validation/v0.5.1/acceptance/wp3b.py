"""v0.5.1 acceptance run of WP3 (b), the per-harmonic sinusoid (docs/plans/v0.5.1-acceptance.md).

**Status: a draft, not run.** It is reviewed by Codex before its single run on frozen code.

Acceptance seeds ``refute-v051-accept:wp3b-<row>:<i>`` (unseen while building), 200 trials per
case, run **once** on frozen code; counts and binomial bands as the acceptance conventions say. The
curves: two sectors (``synthetic.sector_times`` at 2000.0 and 2027.4 BTJD), two-minute cadence,
white noise of 1000 ppm, or the AR(1) of ``synthetic.ar1_series`` (half the white level, tau one
hour) added, or a C1-like stellar trend (amplitude uniform in [0, 2000] ppm, period uniform in
[3, 10] d, random phase), or both; a box-like trapezoid (ingress fraction 0.1) at period 3.3 d,
duration 0.12 d, its depth set for the case's SNR from the white level; the candidate is the
truth (the test, not the search, is under test).

Rows: 3.1 (v0.5 3.3: a sinusoid at P of semi-amplitude 2 x the apparent depth: FAIL at least at
rate 0.95; v0.5 3.8: box only: false-failure at most 0.0027); 3.2 (planets at SNR 12 and 20 with
a trend: false-failure at most 0.0027; every applicable sub-check detectable in at least 0.95 at
SNR 20); 3.3 (v0.5 3.4 and 3.5: never fatal); 3.4 (three close frequencies: FAIL at least at the
v0.5 code's rate on the same curves); 3.5 (P 12 and 15 d: P/2 and P applicable, 2P not, never
INCONCLUSIVE by the domain); 3.6 (a sinusoid at 14 d found as a box: FAIL at least 0.95 when
detectable); 3.7 (variability within 1 / T_span of P: never an extra frequency); 3.8 (1.8 (a), (b),
(c) per sub-check).

Usage: scripts/launch_affinity.ps1 -Script docs/validation/v0.5.1/acceptance/wp3b.py
       -Arguments 'run' -Log .cache/v051/accept/wp3b
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
N = 200
NOISES = ("white", "correlated", "trend", "correlated_trend")


def seed(row: str, i: int) -> int:
    return int(hashlib.sha256(f"refute-v051-accept:wp3b-{row}:{i}".encode()).hexdigest()[:16], 16)


def curve(s, noise, period=3.3, depth=0.0, duration=0.12, sinus=None, extra=None):
    from refute.packs.tess import synthetic as syn
    from refute.packs.tess.types import LightCurveData

    rng = np.random.default_rng(s)
    starts = (2000.0, 2027.4)
    t = np.concatenate([syn.sector_times(x) for x in starts])
    sector = np.concatenate(
        [np.full(syn.sector_times(x).size, i + 1) for i, x in enumerate(starts)]
    )
    sigma = 1000e-6
    flux = np.ones_like(t)
    t0 = 2000.5 + rng.uniform(0.0, period)
    if depth:
        flux -= syn.trapezoid(t, period, t0, depth, duration, 0.1)
    for p, amp in [sinus] if sinus else []:
        flux += amp * np.sin(2 * math.pi * t / p + rng.uniform(0, 2 * math.pi))
    for p, amp in extra or []:
        flux += amp * np.sin(2 * math.pi * t / p + rng.uniform(0, 2 * math.pi))
    if noise in ("trend", "correlated_trend"):
        amp, p = rng.uniform(0, 2000e-6), rng.uniform(3.0, 10.0)
        flux *= 1.0 + amp * np.sin(2 * math.pi * t / p + rng.uniform(0, 2 * math.pi))
    flux += sigma * rng.standard_normal(t.size)
    if noise in ("correlated", "correlated_trend"):
        rr = np.random.default_rng([s, 3])
        for n in (1, 2):
            sel = sector == n
            flux[sel] += syn.ar1_series(t[sel], sigma / 2.0, 1.0 / 24.0, rr)
    lc = LightCurveData(t, flux, np.full(t.size, sigma), sector, np.full(t.size, 2020))
    return lc, t0


def depth_for(snr, period, duration, n_points):
    n_in = n_points * duration / period
    return snr * 1000e-6 / math.sqrt(n_in)


def candidate(period, t0, depth, duration):
    from refute.packs.tess.types import Candidate

    return Candidate(period=period, t0=t0, duration=duration, depth=depth, depth_err=depth / 10,
                     snr=20.0, log_likelihood=0.0, sde=10.0, n_transits=10)  # fmt: skip


def one(task):
    from refute.core.sensitivity import enforce_sensitivity
    from refute.packs.tess import battery_v5 as v5
    from refute.packs.tess import battery_v51 as v51
    from refute.packs.tess.params import StrongerParams, V051Params
    from refute.packs.tess.power import TESS_REGISTRY_V3

    row, case, i, noise = task
    sp, cp = StrongerParams(), V051Params()
    s = seed(f"{row}-{case}-{noise}", i)
    period, duration, n_points = 3.3, 0.12, 2 * 2 * 13 * 720
    out = {"row": row, "case": case, "noise": noise, "i": i}
    if row in ("3.1a", "3.6"):
        p = 3.3 if row == "3.1a" else 14.0
        dur = duration if row == "3.1a" else 0.3
        apparent = depth_for(20, p, dur, n_points)
        lc, t0 = curve(s, noise, period=p, sinus=(p, 2 * apparent))
        cand = candidate(p, t0, apparent, dur)
    elif row in ("3.1b", "3.2", "3.8c"):
        snr = {"3.1b": 20, "3.8c": 20, "3.2": int(case)}[row]
        d = depth_for(snr, period, duration, n_points)
        lc, t0 = curve(s, "trend" if row == "3.2" else noise, depth=d)
        cand = candidate(period, t0, d, duration)
    elif row == "3.3":
        d = depth_for(15, period, duration, n_points)
        ratio = {"unrelated": 2.37, "rotation": 1.0}[case]
        amp = (3.0 if case == "unrelated" else 1.0) * d
        lc, t0 = curve(s, noise, depth=d, extra=[(period * ratio, amp)])
        cand = candidate(period, t0, d, duration)
    elif row == "3.4":
        d = depth_for(15, period, duration, n_points)
        f0 = 1.0 / period
        extra = [(1.0 / f, d) for f in (f0, f0 * 1.02, f0 * 1.04)]
        lc, t0 = curve(s, noise, extra=extra)
        cand = candidate(period, t0, d, duration)
    elif row == "3.5":
        p = float(case)
        d = depth_for(15, p, 0.2, n_points)
        lc, t0 = curve(s, noise, period=p, depth=d, duration=0.2)
        cand = candidate(p, t0, d, 0.2)
    elif row == "3.7":
        d = depth_for(15, period, duration, n_points)
        lc, t0 = curve(s, noise, depth=d, extra=[(period * 1.002, 2 * d)])
        cand = candidate(period, t0, d, duration)
    elif row == "3.8a":
        d = depth_for(20, period, duration, n_points)
        lc, t0 = curve(s, noise, sinus=(period, d))
        cand = candidate(period, t0, d, duration)
    else:  # 3.8b: below the rule (errors too large)
        d = depth_for(20, period, duration, n_points)
        lc, t0 = curve(s, noise, sinus=(period, d))
        lc = type(lc)(lc.time, 1 + 25 * (lc.flux - 1), lc.flux_err * 25, lc.sector, lc.year)
        cand = candidate(period, t0, d, duration)
    r = v51.check_sinusoid(lc, cand, sp, cp, seed=s % 100000)
    e = enforce_sensitivity([r], TESS_REGISTRY_V3)[0]
    blocks = [b for b in (r.sensitivity or {}).values() if "detectable" in b]
    out.update(
        status=r.status.value,
        enforced=e.status.value,
        detectable=bool(blocks) and all(b["detectable"] for b in blocks),
        applicable=sorted(k for k, b in (r.sensitivity or {}).items() if "detectable" in b),
        extra=[x["frequency_per_day"] for x in r.metrics.get("extra_frequencies", [])],
        domain_inconclusive=r.metrics.get("inconclusive_class") == "outside_domain",
    )
    if row == "3.4":
        out["v05_status"] = v5.check_sinusoid(lc, cand, sp, seed=s % 100000).status.value
    return out


def tasks():
    rows = []
    for noise in NOISES:
        for i in range(N):
            rows += [("3.1a", "-", i, noise), ("3.1b", "-", i, noise), ("3.4", "-", i, noise)]
            rows += [("3.3", c, i, noise) for c in ("unrelated", "rotation")]
            rows += [("3.5", c, i, noise) for c in ("12", "15")]
            rows += [("3.6", "-", i, noise), ("3.7", "-", i, noise)]
            rows += [("3.8a", "-", i, noise), ("3.8b", "-", i, noise), ("3.8c", "-", i, noise)]
    rows += [("3.2", c, i, "trend") for c in ("12", "20") for i in range(N)]
    return rows


def band_low(n, p):
    from scipy.stats import binom

    return int(binom.ppf(0.025, n, p))


def band_high(n, a):
    from scipy.stats import binom

    return int(binom.ppf(0.975, n, a))


def judge(recs):
    out = {}
    groups = {}
    for r in recs:
        groups.setdefault((r["row"], r["case"], r["noise"]), []).append(r)
    for (row, case, noise), g in sorted(groups.items()):
        n = len(g)
        fails = sum(r["status"] == "FAIL" for r in g)
        key = f"{row}|{case}|{noise}"
        if row in ("3.1a", "3.6", "3.8a"):
            det = [r for r in g if r["detectable"] or r["status"] == "FAIL"]
            k = sum(r["status"] == "FAIL" for r in det)
            ok = k >= band_low(len(det), 0.95) if det else False
            out[key] = {"n": n, "fails": fails, "detectable_or_fail": len(det), "pass": ok}
        elif row in ("3.1b", "3.8c", "3.2"):
            ok = fails <= band_high(n, 0.0027)
            entry = {"n": n, "fails": fails, "pass": ok}
            if row == "3.2" and case == "20":
                det = sum(r["detectable"] for r in g)
                entry["detectable"] = det
                entry["pass"] = ok and det >= band_low(n, 0.95)
            out[key] = entry
        elif row == "3.3":
            out[key] = {"n": n, "fails": fails, "pass": True, "note": "warning only: never fatal"}
        elif row == "3.4":
            v05 = sum(r["v05_status"] == "FAIL" for r in g)
            out[key] = {"n": n, "fails": fails, "v05_fails": v05, "pass": fails >= v05}
        elif row == "3.5":
            bad = sum(r["domain_inconclusive"] or r["applicable"] != ["P", "P/2"] for r in g)
            out[key] = {"n": n, "violations": bad, "pass": bad == 0}
        elif row == "3.7":
            f0 = 1.0 / 3.3
            span = 2027.4 + 27.0 - 2000.0
            bad = sum(any(abs(f - f0) <= 1.0 / span for f in r["extra"]) for r in g)
            out[key] = {"n": n, "violations": bad, "pass": bad == 0}
        elif row == "3.8b":
            bad = sum(r["enforced"] == "PASS" for r in g)
            out[key] = {"n": n, "passes_after_rule": bad, "pass": bad == 0}
    return out


def main():
    from refute.core.runner import default_workers

    with ProcessPoolExecutor(max_workers=default_workers()) as pool:
        recs = list(pool.map(one, tasks(), chunksize=8))
    out_dir = ROOT / ".cache/v051/accept"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "wp3b-records.jsonl").write_text(
        "".join(json.dumps(r, sort_keys=True) + "\n" for r in recs), encoding="utf-8"
    )
    verdicts = judge(recs)
    doc = {
        "label": "v0.5.1 WP3 (b) acceptance run (acceptance seeds, once, frozen code)",
        "rows": verdicts,
        "all_pass": all(v["pass"] for v in verdicts.values()),
    }
    (HERE / "wp3b.json").write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8")
    print(json.dumps({"all_pass": doc["all_pass"]}))


if __name__ == "__main__":
    if sys.argv[1:] == ["run"]:
        main()
    else:
        raise SystemExit("usage: wp3b.py run")
