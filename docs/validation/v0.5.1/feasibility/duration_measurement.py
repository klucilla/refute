"""v0.5.1 amendment 3, item 2 (b): what the `duration_excess` warning would do, on development data.

Development data only (never confirmation data): planets of the frozen C1 generator (families P and
PG, seeds ``refute-v051-dev:dur-<family>:<i>``, 200 each) and binaries folded at half their period
in the C1 EB1 geometry (the generator's own star, sectors, noise and trapezoid; the depth ratio of
the secondary fixed at 1.0, 0.9 or 0.7 and the target SNR at 10, 20 or 30; impact parameter
uniform in [0, 0.8]; seeds ``refute-v051-dev:dur-EB-<ratio>-<snr>:<i>``, 100 per case).

The candidate is the truth's ephemeris at the period a search finds for each (the true period for
planets, half the true period for the binaries; no search is run: the measurement is about the
warning, not the search). The rule measured is the acceptance text's (`duration_excess` in
docs/plans/v0.5.1-acceptance.md), with the parts not yet fixed there chosen as stated here:

- the curve detrended by the frozen v0.4 plan's detrending, the candidate's transits masked;
- ``T`` from a least-squares trapezoid on the folded curve (depth, total duration, ingress
  fraction and epoch shift free);
- ``sigma_T``: the standard deviation of ``T`` over 20 injection-recoveries of the fitted trapezoid
  at phases 0.20 to 0.40 and 0.60 to 0.80 of the period (the transits masked), the same fit (a
  development choice; A0's final mechanism is not adopted yet);
- ``T_max(P)`` for a central transit around the TIC star of the generator (radius 1.0 +- 0.05,
  mass 1.0 +- 0.05), ``sigma_Tmax`` from 2000 seeded draws of radius, mass and ``k``;
- warning when ``T - T_max(P) >= 3 sqrt(sigma_T^2 + sigma_Tmax^2)``; detectable when
  ``(T_max(2P) - T_max(P)) / sqrt(sigma_T^2 + sigma_Tmax^2) >= 3 + 1.645``. As a decisive warning
  test, a PASS that is not detectable is INCONCLUSIVE.

It reports, per family and case: the fraction not detectable (the INCONCLUSIVE the warning adds,
for planets a planet otherwise kept would lose), the warning rate, and the warning rate among the
detectable. It decides nothing.

Usage:
  scripts/launch_affinity.ps1 -Script docs/validation/v0.5.1/feasibility/duration_measurement.py
      -Arguments 'run' -Log .cache/v051/duration/run
  .venv/Scripts/python.exe docs/validation/v0.5.1/feasibility/duration_measurement.py summarize
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / ".cache/v051/duration"
RECORDS = OUT / "records.jsonl"
HERE = Path(__file__).resolve().parent
Z = 3.0 + 1.645
RATIOS = (1.0, 0.9, 0.7)
SNRS = (10.0, 20.0, 30.0)


def seed(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def t_max(period, k, radius, mass):
    from refute.packs.tess.calib05.c1 import a_over_rstar

    a = a_over_rstar(period) * mass ** (1.0 / 3.0) / radius
    return period / math.pi * math.asin(min(1.0, (1.0 + k) / a))


def fit_trapezoid(t, y, period, t0, depth0, dur0):
    """Least-squares trapezoid on the folded curve near the events; returns (depth, T, f, shift)."""
    from scipy.optimize import least_squares

    from refute.packs.tess import synthetic as syn

    dt = np.mod(t - t0 + 0.5 * period, period) - 0.5 * period
    near = np.abs(dt) <= 1.5 * dur0
    tn, yn = t[near], y[near]

    def resid(x):
        depth, dur, f, shift = x
        return (1.0 - syn.trapezoid(tn, period, t0 + shift, depth, dur, f)) - yn

    best = None
    for f0 in (0.05, 0.2):
        fit = least_squares(
            resid,
            [depth0, dur0, f0, 0.0],
            bounds=(
                [0.0, 0.3 * dur0, 0.01, -0.3 * dur0],
                [10 * depth0, 3.0 * dur0, 0.5, 0.3 * dur0],
            ),
            x_scale=[depth0, 0.1 * dur0, 0.05, 0.05 * dur0],
            max_nfev=300,
        )
        if best is None or fit.cost < best.cost:
            best = fit
    return tuple(float(v) for v in best.x)


def measure(data, period, t0, depth, duration, rng_seed):
    from refute.packs.tess import synthetic as syn
    from refute.packs.tess.calib05.plans import pair
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.events import transit_mask

    p04, _ = pair(v04_test_plan(ROOT))
    mask = transit_mask(data.lc.time, period, t0, duration)
    flat = detrend(data.lc, p04.detrend, mask=mask)
    t, y = flat.time, flat.flux
    d_fit, dur_t, f, shift = fit_trapezoid(t, y, period, t0, depth, duration)
    model = syn.trapezoid(t, period, t0 + shift, d_fit, dur_t, f)
    clean = y + model  # the real transits removed (their fitted model added back)
    recovered = []
    for phi in np.concatenate([np.linspace(0.20, 0.40, 10), np.linspace(0.60, 0.80, 10)]):
        tj = t0 + shift + phi * period
        yj = clean - syn.trapezoid(t, period, tj, d_fit, dur_t, f)
        recovered.append(fit_trapezoid(t, yj, period, tj, d_fit, dur_t)[1])
    sigma_t = float(np.std(recovered, ddof=1))
    rng = np.random.default_rng(rng_seed)
    k = math.sqrt(max(d_fit, 1e-9))
    radius = np.clip(rng.normal(1.0, 0.05, 2000), 0.1, None)
    mass = np.clip(rng.normal(1.0, 0.05, 2000), 0.1, None)
    tmax_p = np.array([t_max(period, k, r, m) for r, m in zip(radius, mass, strict=True)])
    tmax_2p = np.array([t_max(2 * period, k, r, m) for r, m in zip(radius, mass, strict=True)])
    sigma_tmax = float(np.std(tmax_p, ddof=1))
    nominal_p, nominal_2p = t_max(period, k, 1.0, 1.0), t_max(2 * period, k, 1.0, 1.0)
    sigma = math.hypot(sigma_t, sigma_tmax)
    return {
        "T": dur_t,
        "sigma_T": sigma_t,
        "T_max_P": nominal_p,
        "T_max_2P": nominal_2p,
        "sigma_Tmax": sigma_tmax,
        "sigma_Tmax_2P": float(np.std(tmax_2p, ddof=1)),
        "warning": bool(dur_t - nominal_p >= 3.0 * sigma),
        "detectable": bool((nominal_2p - nominal_p) / sigma >= Z),
    }


def run_planet(family: str, i: int) -> dict:
    from refute.packs.tess.calib05 import c1

    started = time.process_time()
    s = seed(f"refute-v051-dev:dur-{family}:{i}")
    rec = {"case": family, "index": i}
    try:
        data, truth = c1.generate(family, s)
    except c1.GenerationFailedError as exc:
        return {**rec, "status": "GENERATION_FAILURE", "reason": str(exc)}
    m = measure(data, truth["period_days"], truth["t0_btjd"], truth["depth"],
                truth["duration_days"], s)  # fmt: skip
    rec.update(status="OK", target_snr=truth["target_snr"], **m)
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def run_binary(ratio: float, snr: float, i: int) -> dict:
    """A C1 EB1-geometry binary with the secondary ratio and target SNR fixed, folded at half."""
    from refute.packs.tess import synthetic as syn
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.types import LightCurveData

    started = time.process_time()
    label = f"EB-{ratio}-{int(snr)}"
    s = seed(f"refute-v051-dev:dur-{label}:{i}")
    rec = {"case": label, "index": i}
    rng = np.random.default_rng(s)
    star = c1._draw_star("EB1", s, rng)
    t, sector = c1._times(star)
    try:
        tr = c1._transit_truth(rng, star, t, (snr, snr), (0.0, 0.8), "EB1")
    except c1.GenerationFailedError as exc:
        return {**rec, "status": "GENERATION_FAILURE", "reason": str(exc)}
    p, t0, d = tr["period_days"], tr["t0_btjd"], tr["depth"]
    model = 1.0 - syn.trapezoid(t, p, t0, d, tr["duration_days"], tr["ingress_fraction"])
    model -= syn.trapezoid(t, p, t0, ratio * d, tr["duration_days"], tr["ingress_fraction"], 0.5)
    flux = c1._noisy(model, t, sector, star)
    lc = LightCurveData(t, flux, np.full(t.size, star.sigma_w), sector, c1._years(t, sector))
    data = syn.make_data(lc, c1._sector_infos(lc, star), syn.make_star(), 1, None)
    m = measure(data, p / 2.0, t0, d * (1 + ratio) / 2.0, tr["duration_days"], s)
    rec.update(status="OK", target_snr=snr, ratio=ratio, impact=tr["impact"], **m)
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def _done():
    if not RECORDS.exists():
        return set()
    return {
        (r["case"], r["index"])
        for r in (json.loads(x) for x in RECORDS.read_text(encoding="utf-8").splitlines() if x)
    }


def run() -> None:
    from refute.core.runner import default_workers

    OUT.mkdir(parents=True, exist_ok=True)
    done = _done()
    jobs = [("P", i) for i in range(200)] + [("PG", i) for i in range(200)]
    jobs += [(f"EB-{r}-{int(q)}", i) for r in RATIOS for q in SNRS for i in range(100)]
    with ProcessPoolExecutor(max_workers=default_workers()) as pool:
        futures = {}
        for case, i in jobs:
            if (case, i) in done:
                continue
            if case in ("P", "PG"):
                futures[pool.submit(run_planet, case, i)] = (case, i)
            else:
                _, r, q = case.split("-")
                futures[pool.submit(run_binary, float(r), float(q), i)] = (case, i)
        for fut in as_completed(futures):
            case, i = futures[fut]
            try:
                rec = fut.result()
            except Exception as exc:  # noqa: BLE001 - recorded, kept in the denominators
                rec = {"case": case, "index": i, "status": "ERROR", "reason": repr(exc)}
            with RECORDS.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")


def summarize() -> dict:
    recs = [json.loads(x) for x in RECORDS.read_text(encoding="utf-8").splitlines() if x.strip()]
    out = {"label": "development measurement (amendment 3, item 2 (b)); it decides nothing"}
    cases = sorted({r["case"] for r in recs})
    for case in cases:
        rows = [r for r in recs if r["case"] == case and r["status"] == "OK"]
        n = len(rows)
        det = [r for r in rows if r["detectable"]]
        out[case] = {
            "n": n,
            "statuses": {
                s: sum(r["status"] == s for r in recs if r["case"] == case)
                for s in ("OK", "GENERATION_FAILURE", "ERROR")
            },  # fmt: skip
            "not_detectable_fraction": (n - len(det)) / n if n else None,
            "warning_fraction": sum(r["warning"] for r in rows) / n if n else None,
            "warning_fraction_among_detectable": (
                sum(r["warning"] for r in det) / len(det) if det else None
            ),
            "median_sigma_T_over_Tmax": float(
                np.median([r["sigma_T"] / r["T_max_P"] for r in rows])
            )
            if rows
            else None,  # fmt: skip
            "median_sigma_Tmax_over_Tmax": float(
                np.median([r["sigma_Tmax"] / r["T_max_P"] for r in rows])
            )
            if rows
            else None,
        }
        if case in ("P", "PG") and rows:
            hi = [r for r in rows if r["target_snr"] >= 15]
            out[case]["not_detectable_fraction_snr15"] = (
                sum(not r["detectable"] for r in hi) / len(hi) if hi else None
            )
        if rows:
            out[case]["counts"] = _counts(rows)
        if case.startswith("EB") and rows:
            out[case]["by_impact"] = _by_impact(rows)
            out[case]["per_geometry_effect"] = _per_geometry(rows)
    out["cpu_hours"] = round(sum(r.get("cpu_seconds", 0) for r in recs) / 3600.0, 2)
    return out


def wilson(k, n, z=1.959964):
    if not n:
        return None
    p = k / n
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(c - h, 4), round(c + h, 4)]


def _counts(rows):
    """Counts and Wilson 95 % intervals (Codex's round 2 under amendment 3)."""
    n = len(rows)
    det = sum(r["detectable"] for r in rows)
    warn = sum(r["warning"] for r in rows)
    return {
        "n": n,
        "not_detectable": n - det,
        "not_detectable_wilson": wilson(n - det, n),
        "warnings": warn,
        "warnings_wilson": wilson(warn, n),
    }


def _by_impact(rows):
    """Detectable fraction and warning rates (all and among detectable) by impact parameter."""
    out = {}
    for lo, hi in ((0.0, 0.3), (0.3, 0.6), (0.6, 0.8)):
        g = [r for r in rows if lo <= r["impact"] < hi or (hi == 0.8 and r["impact"] == 0.8)]
        det = [r for r in g if r["detectable"]]
        out[f"{lo}-{hi}"] = {
            "n": len(g),
            "detectable_fraction": len(det) / len(g) if g else None,
            "warning_fraction": sum(r["warning"] for r in g) / len(g) if g else None,
            "warning_fraction_among_detectable": (
                sum(r["warning"] for r in det) / len(det) if det else None
            ),
        }
    return out


def _per_geometry(rows):
    """For reporting only (Codex's round 1 under amendment 3; never used to retune): the effect of
    each binary's own geometry, its generated duration minus T_max(P), against the same total
    uncertainty; the generated duration is rebuilt from the binary's seed."""
    from refute.packs.tess.calib05 import c1

    detectable = 0
    effects = []
    for r in rows:
        ratio, snr = r["ratio"], r["target_snr"]
        s = seed(f"refute-v051-dev:dur-EB-{ratio}-{int(snr)}:{r['index']}")
        rng = np.random.default_rng(s)
        star = c1._draw_star("EB1", s, rng)
        t, _ = c1._times(star)
        tr = c1._transit_truth(rng, star, t, (snr, snr), (0.0, 0.8), "EB1")
        effect = tr["duration_days"] - r["T_max_P"]
        sigma = math.hypot(r["sigma_T"], r["sigma_Tmax"])
        effects.append(effect / r["T_max_P"])
        detectable += effect / sigma >= Z
    return {
        "detectable_fraction": detectable / len(rows),
        "median_effect_over_Tmax": float(np.median(effects)),
        "fraction_negative_effect": float(np.mean(np.asarray(effects) < 0)),
    }


if __name__ == "__main__":
    if sys.argv[1:] == ["run"]:
        run()
    elif sys.argv[1:] == ["summarize"]:
        doc = summarize()
        (HERE / "duration-measurement.json").write_text(
            json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(doc, indent=1, sort_keys=True))
    else:
        raise SystemExit("usage: duration_measurement.py run|summarize")
