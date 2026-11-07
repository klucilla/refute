"""v0.5.1 amendment 10, item 3: the search for a D1 route for the folded binaries.

**Development data only** (the WP1 forecast's records and seeds, and new development seeds
``refute-v051-dev:route-<family>:<i>``); it decides nothing and writes no acceptance. At most 10
processor-hours (the maintainer's approval).

- ``decompose`` (item 3 (a)): the WP1 forecast's oracle (``forecast.nearest_planet``: the planet
  at the found period nearest to each eligible EB1 and EB2 binary, its depth, impact parameter,
  epoch shift and the star's radius free, the Mahalanobis distance under the generator's noise)
  repeated with the radius free within ``1 +- 3 sigma_R`` for ``sigma_R`` 0 (the radius known),
  0.025, 0.05 (the forecast's, the generator's TIC error) and 0.10; for each, the optimistic
  survival summed over the binaries and scaled to C1' (about half the forecast's eligible counts),
  and how many nearest planets sit at the radius bound. It shows how much of the separation the
  TIC's radius error removes.
- ``route`` (item 3 (c)): a candidate catalog-assisted route measured with a real estimator on
  noisy curves: the **transit-geometry consistency** (the stellar density implied by the transit's
  duration, ingress and depth against the TIC star; Seager and Mallen-Ornelas 2003,
  https://arxiv.org/abs/astro-ph/0206228, read 2026-11-07). For each development curve (EB1, EB2,
  P, PG; 150 each), the frozen v0.4 candidate generation (detrending, prewhitening, search) gives
  the found ephemeris; on the curve flattened with the candidate's transits masked, two fits near
  the events: a free trapezoid (``battery_v51._fit_shape_status``) and a physical planet at the
  found period (``forecast.planet_model``: depth, impact parameter, epoch shift, the star's radius
  and mass free under Gaussian priors from the TIC star's values and errors). The statistic is
  ``dchi2 = chi2_planet + prior penalty - chi2_trapezoid`` in white weights (the curve's median
  error). Reported per family and noise type (white, correlated): the quantiles of ``dchi2``; at a
  nominal threshold of 9 and at the 99.73 % quantile of the planets' own ``dchi2`` (the false-flag
  rate 0.0027 estimated on development planets), the fraction of eligible binaries flagged (the
  effect on D1) and of eligible planets flagged (the effect on D2).

Usage (heavy, resumable):
  scripts/launch_affinity.ps1 -Script docs/validation/v0.5.1/feasibility/d1_routes.py
      -Arguments 'decompose' -Log .cache/v051/d1routes/decompose
  scripts/launch_affinity.ps1 -Script docs/validation/v0.5.1/feasibility/d1_routes.py
      -Arguments 'route' -Log .cache/v051/d1routes/route
  .venv/Scripts/python.exe docs/validation/v0.5.1/feasibility/d1_routes.py summarize
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from statistics import NormalDist

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OUT = ROOT / ".cache/v051/d1routes"
FORECAST = ROOT / ".cache/v051/feasibility/records.jsonl"
SIGMAS = (0.0, 0.025, 0.05, 0.10)
ROUTE_FAMILIES = ("EB1", "EB2", "P", "PG")
ROUTE_SIZE = 150
C1_PRIME_SCALE = 0.5  # C1' has 200 per family, the forecast 400


def seed(text: str) -> int:
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def _forecast():
    sys.path.insert(0, str(HERE))
    import forecast

    return forecast


# --- (a) the decomposition ------------------------------------------------------------------


# (sigma_R, sigma_M) for the joint decomposition (Codex's round 1: the mass too): the planet
# model's a / R* depends on the star through R / M^(1/3), so the fit's free "radius" is that
# effective radius, bounded by the 3-sigma extremes of the radius and the mass together
JOINT = ((0.0, 0.05), (0.025, 0.025), (0.05, 0.05), (0.10, 0.10))


def effective_bounds(sigma_r: float, sigma_m: float) -> tuple[float, float]:
    lo = (1.0 - 3 * sigma_r) / (1.0 + 3 * sigma_m) ** (1.0 / 3.0)
    hi = (1.0 + 3 * sigma_r) / max(1.0 - 3 * sigma_m, 1e-3) ** (1.0 / 3.0)
    return (lo, hi) if hi - lo > 2e-9 else (1.0 - 1e-9, 1.0 + 1e-9)


def nearest_with_bounds(fc, t, truth, found, sigma_r, bounds=None):
    """``forecast.nearest_planet`` with the radius free within 1 +- 3 sigma_r (or ``bounds``)."""
    from scipy.optimize import least_squares

    if bounds is not None:
        lo, hi = bounds
    else:
        lo, hi = (1.0 - 3 * sigma_r, 1.0 + 3 * sigma_r) if sigma_r > 0 else (1.0 - 1e-9, 1.0 + 1e-9)
    pf, t0f = found["period_days"], found["t0_btjd"]
    target = fc.binary_model(t, truth)
    dt = np.mod(t - t0f + 0.5 * pf, pf) - 0.5 * pf
    near = np.abs(dt) <= 2.0 * truth["duration_days"]
    tn, yn = t[near], target[near]
    mean_depth = truth["depth"] * (1.0 + truth["secondary_ratio"]) / 2.0

    def resid(x):
        depth, b, shift, radius = x
        return fc.planet_model(tn, pf, t0f + shift, depth, b, radius) - yn

    best = None
    for b0 in (0.0, 0.3, 0.6, 0.85):
        for r0 in (lo + 0.25 * (hi - lo), lo + 0.75 * (hi - lo)):
            for depth0 in (mean_depth, truth["depth"]):
                try:
                    fit = least_squares(
                        resid,
                        [depth0, b0, 0.0, r0],
                        bounds=([1e-7, 0.0, -0.1, lo], [0.5, 1.2, 0.1, hi]),
                        x_scale=[mean_depth, 0.1, 0.005, 0.05],
                        max_nfev=400,
                    )
                except ValueError:
                    continue
                if best is None or fit.cost < best.cost:
                    best = fit
    depth, b, shift, radius = best.x
    r = fc.planet_model(t, pf, t0f + shift, depth, b, radius) - target
    return float(radius), r, (hi - radius) < 1e-3 * max(hi - 1.0, 1e-9) or radius >= hi - 1e-6


def decompose_one(family: str, i: int, seed_str: str, found: dict) -> dict:
    from refute.packs.tess.calib05 import c1

    fc = _forecast()
    started = time.process_time()
    data, truth = c1.generate(family, int(seed_str))
    t, sector = data.lc.time, data.lc.sector
    sigma_w = truth["sigma_white_ppm"] * 1e-6
    sigma_r_noise = sigma_w / 2.0 if truth["correlated"] else 0.0
    out = {"family": family, "index": i, "secondary_ratio": truth["secondary_ratio"]}
    for s in SIGMAS:
        radius, r, at_bound = nearest_with_bounds(fc, t, truth, found, s)
        d = math.sqrt(fc.mahalanobis2(t, sector, r, sigma_w, sigma_r_noise))
        out[str(s)] = {
            "radius": radius,
            "distance": d,
            "survival": 1.0 - NormalDist().cdf(d - 1.645),
            "at_bound": bool(at_bound),
        }
    out["cpu_seconds"] = time.process_time() - started
    return out


def decompose_joint_one(family: str, i: int, seed_str: str, found: dict) -> dict:
    """The decomposition with the radius and the mass free together (``JOINT``)."""
    from refute.packs.tess.calib05 import c1

    fc = _forecast()
    started = time.process_time()
    data, truth = c1.generate(family, int(seed_str))
    t, sector = data.lc.time, data.lc.sector
    sigma_w = truth["sigma_white_ppm"] * 1e-6
    sigma_r_noise = sigma_w / 2.0 if truth["correlated"] else 0.0
    out = {"family": family, "index": i, "secondary_ratio": truth["secondary_ratio"]}
    for sr, sm in JOINT:
        bounds = effective_bounds(sr, sm)
        radius, r, at_bound = nearest_with_bounds(fc, t, truth, found, sr, bounds)
        d = math.sqrt(fc.mahalanobis2(t, sector, r, sigma_w, sigma_r_noise))
        out[f"R{sr}_M{sm}"] = {
            "effective_radius": radius,
            "bounds": list(bounds),
            "distance": d,
            "survival": 1.0 - NormalDist().cdf(d - 1.645),
            "at_bound": bool(at_bound),
        }
    out["cpu_seconds"] = time.process_time() - started
    return out


# --- (c) the transit-geometry consistency on noisy curves -----------------------------------


def _priors(star):
    r = float(star.radius_rsun or 1.0)
    m = float(star.mass_msun or 1.0)
    return r, float(star.radius_err_rsun or 0.05 * r), m, float(star.mass_err_msun or 0.05 * m)


def planet_model_rm(t, period, t0, depth, b, radius, mass):
    """``forecast.planet_model`` with a / R* from the radius and the mass (Kepler)."""
    from refute.packs.tess import synthetic as syn
    from refute.packs.tess.calib05.c1 import a_over_rstar

    if depth <= 0 or radius <= 0 or mass <= 0:
        return np.zeros_like(t)
    k = math.sqrt(depth)
    a = a_over_rstar(period) * mass ** (1.0 / 3.0) / radius
    if (1 + k) ** 2 - b**2 <= 0:
        return np.zeros_like(t)
    total = period / math.pi * math.asin(min(1.0, math.sqrt((1 + k) ** 2 - b**2) / a))
    flat_arg = max(0.0, (1 - k) ** 2 - b**2)
    flat = period / math.pi * math.asin(min(1.0, math.sqrt(flat_arg) / a))
    ingress = (total - flat) / (2.0 * total)
    return syn.trapezoid(t, period, t0, depth, total, ingress)


def geometry_dchi2(flat, cand, star, noise=None):
    """``noise`` = (sigma_w, sigma_r): the generator's white and AR(1) levels; when given, the
    same two fits' residuals are also scored under the full covariance (``dchi2_cov``,
    ``forecast.mahalanobis2``; the fits themselves stay in white weights; Codex's round 1)."""
    from scipy.optimize import least_squares

    from refute.packs.tess import battery_v51 as v51

    t, y = flat.time, flat.flux
    sigma = float(np.nanmedian(flat.flux_err))
    p, t0, dur = cand.period, cand.t0, cand.duration
    dt = np.mod(t - t0 + 0.5 * p, p) - 0.5 * p
    near = np.abs(dt) <= 2.0 * dur
    tn, yn = t[near], y[near]
    (d_t, dur_t, f_t, s_t), ok, _ = v51._fit_shape_status(t, y, cand)
    from refute.packs.tess import synthetic as syn

    chi2_trap = float(np.sum(((1.0 - syn.trapezoid(tn, p, t0 + s_t, d_t, dur_t, f_t)) - yn) ** 2))
    chi2_trap /= sigma**2
    r0, sr, m0, sm = _priors(star)
    depth0 = max(cand.depth, 1e-6)

    def resid(x):
        depth, b, shift, radius, mass = x
        model = 1.0 - planet_model_rm(tn, p, t0 + shift, depth, b, radius, mass)
        return np.concatenate([(model - yn) / sigma, [(radius - r0) / sr, (mass - m0) / sm]])

    best = None
    for b0 in (0.0, 0.4, 0.8):
        for d0 in (depth0, 1.3 * depth0):
            try:
                fit = least_squares(
                    resid,
                    [d0, b0, 0.0, r0, m0],
                    bounds=([1e-7, 0.0, -0.3 * dur, 0.2, 0.1], [0.5, 1.2, 0.3 * dur, 5.0, 5.0]),
                    x_scale=[depth0, 0.1, 0.05 * dur, 0.05, 0.05],
                    max_nfev=400,
                )
            except ValueError:
                continue
            if best is None or fit.cost < best.cost:
                best = fit
    chi2_planet = 2.0 * float(best.cost)
    depth, b, shift, radius, mass = (float(v) for v in best.x)
    out = {
        "dchi2": chi2_planet - chi2_trap,
        "trapezoid_ok": bool(ok),
        "planet_fit": {"depth": depth, "b": b, "radius": radius, "mass": mass},
        "trapezoid_duration_hours": dur_t * 24.0,
    }
    if noise is not None:
        fc = _forecast()
        sector = flat.sector[near]
        r_trap = (1.0 - syn.trapezoid(tn, p, t0 + s_t, d_t, dur_t, f_t)) - yn
        r_planet = (1.0 - planet_model_rm(tn, p, t0 + shift, depth, b, radius, mass)) - yn
        penalty = ((radius - r0) / sr) ** 2 + ((mass - m0) / sm) ** 2
        out["dchi2_cov"] = (
            fc.mahalanobis2(tn, sector, r_planet, *noise)
            + penalty
            - fc.mahalanobis2(tn, sector, r_trap, *noise)
        )
    return out


def route_one(family: str, i: int) -> dict:
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.calib05.plans import pair
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.events import transit_mask
    from refute.packs.tess.pipeline import global_prewhitening
    from refute.packs.tess.search import search_period

    started = time.process_time()
    s = seed(f"refute-v051-dev:route-{family}:{i}")
    rec: dict = {"family": family, "index": i}
    try:
        data, truth = c1.generate(family, s)
    except c1.GenerationFailedError as exc:
        return {**rec, "status": "GENERATION_FAILURE", "reason": str(exc)}
    p04, _ = pair(v04_test_plan(ROOT))
    flat0 = detrend(data.lc, p04.detrend)
    _, searched = global_prewhitening(data, p04, flat0)
    cand = search_period(searched, p04.search).candidate
    snr = None if cand is None else float(cand.snr)
    eligible = snr is not None and snr >= p04.gauntlet.snr.min_snr
    found = None if cand is None else {"period_days": cand.period, "t0_btjd": cand.t0}
    if family in ("P", "PG"):
        eligible = eligible and c1.identity(truth, found)
    rec.update(
        status="OK",
        eligible=bool(eligible),
        correlated=bool(truth["correlated"]),
        secondary_ratio=truth.get("secondary_ratio"),
        target_snr=truth.get("target_snr"),
    )
    if eligible:
        mask = transit_mask(data.lc.time, cand.period, cand.t0, cand.duration)
        flat = detrend(data.lc, p04.detrend, mask=mask)
        sigma_w = truth["sigma_white_ppm"] * 1e-6
        noise = (sigma_w, sigma_w / 2.0 if truth["correlated"] else 0.0)
        rec.update(geometry_dchi2(flat, cand, data.star, noise))
        rec["candidate"] = {"period_days": cand.period, "t0_btjd": cand.t0, "snr": snr}
        if family == "EB1":
            rec["folded"] = abs(cand.period - truth["period_days"] / 2.0) < 0.01 * cand.period
    rec["cpu_seconds"] = time.process_time() - started
    return rec


# --- running and summarizing ------------------------------------------------------------------


def _append(path: Path, rec: dict) -> None:
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, sort_keys=True) + "\n")


def _done(path: Path) -> set:
    if not path.exists():
        return set()
    rows = [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    return {(r["family"], r["index"]) for r in rows}


def run(part: str) -> None:
    from refute.core.runner import default_workers

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{part}.jsonl"
    done = _done(path)
    with ProcessPoolExecutor(max_workers=default_workers()) as pool:
        futures = {}
        if part in ("decompose", "decompose_joint"):
            fn = decompose_one if part == "decompose" else decompose_joint_one
            rows = [json.loads(x) for x in FORECAST.read_text(encoding="utf-8").splitlines() if x]
            for r in rows:
                if r.get("family") in ("EB1", "EB2") and r.get("eligible"):
                    key = (r["family"], r["index"])
                    if key not in done:
                        fut = pool.submit(fn, r["family"], r["index"], r["seed"], r["found"])
                        futures[fut] = key
        else:
            for fam in ROUTE_FAMILIES:
                for i in range(ROUTE_SIZE):
                    if (fam, i) not in done:
                        futures[pool.submit(route_one, fam, i)] = (fam, i)
        for fut in as_completed(futures):
            fam, i = futures[fut]
            try:
                rec = fut.result()
            except Exception as exc:  # noqa: BLE001 - recorded
                rec = {"family": fam, "index": i, "status": "ERROR", "reason": repr(exc)}
            _append(path, rec)


def summarize() -> dict:
    out: dict = {"label": "development data only (amendment 10, item 3); it decides nothing"}
    dec = [json.loads(x) for x in (OUT / "decompose.jsonl").read_text("utf-8").splitlines() if x]
    out["decompose"] = {}
    for fam in ("EB1", "EB2"):
        rows = [r for r in dec if r["family"] == fam and "0.05" in r]
        out["decompose"][fam] = {"eligible": len(rows)}
        for s in SIGMAS:
            k = str(s)
            surv = sum(r[k]["survival"] for r in rows)
            out["decompose"][fam][f"sigma_R={s}"] = {
                "expected_survivors_at_c1_prime": round(surv * C1_PRIME_SCALE, 2),
                "nearest_at_radius_bound": sum(r[k]["at_bound"] for r in rows),
            }
    joint_path = OUT / "decompose_joint.jsonl"
    joint = []
    if joint_path.exists():
        joint = [json.loads(x) for x in joint_path.read_text("utf-8").splitlines() if x]
        out["decompose_joint"] = {}
        for fam in ("EB1", "EB2"):
            rows = [r for r in joint if r["family"] == fam and "R0.05_M0.05" in r]
            out["decompose_joint"][fam] = {"eligible": len(rows)}
            for sr, sm in JOINT:
                k = f"R{sr}_M{sm}"
                surv = sum(r[k]["survival"] for r in rows)
                out["decompose_joint"][fam][k] = {
                    "expected_survivors_at_c1_prime": round(surv * C1_PRIME_SCALE, 2),
                    "nearest_at_bound": sum(r[k]["at_bound"] for r in rows),
                }
    rte = [json.loads(x) for x in (OUT / "route.jsonl").read_text("utf-8").splitlines() if x]
    ok = [r for r in rte if r.get("status") == "OK" and r.get("eligible") and "dchi2" in r]
    out["route"] = {
        "note": "thresholds exploratory (Codex's round 1): 9 has no calibrated false-flag "
        "meaning; the planets' 99.73 % quantile rests on about one tail observation",
        "families": {},
    }
    for stat in ("dchi2", "dchi2_cov"):
        planets = np.array([r[stat] for r in ok if r["family"] in ("P", "PG") and stat in r])
        q = float(np.quantile(planets, 0.9973)) if planets.size else None
        out["route"][f"{stat}_planet_q9973"] = q
        for fam in ROUTE_FAMILIES:
            for noise in (False, True):
                g = [r for r in ok if r["family"] == fam and r["correlated"] == noise and stat in r]
                vals = np.array([r[stat] for r in g])
                key = f"{stat} {fam} {'correlated' if noise else 'white'}"
                out["route"]["families"][key] = {
                    "eligible": len(g),
                    "quantiles_10_50_90": [float(np.quantile(vals, x)) for x in (0.1, 0.5, 0.9)]
                    if vals.size
                    else None,
                    "flagged_at_9": float(np.mean(vals >= 9.0)) if vals.size else None,
                    "flagged_at_planet_q": float(np.mean(vals >= q)) if vals.size and q else None,
                }
    eb1 = [r for r in ok if r["family"] == "EB1"]
    out["route"]["EB1_folded"] = sum(bool(r.get("folded")) for r in eb1)
    out["cpu_hours"] = round(sum(r.get("cpu_seconds", 0) for r in dec + rte + joint) / 3600.0, 2)
    return out


if __name__ == "__main__":
    if sys.argv[1:] in (["decompose"], ["route"], ["decompose_joint"]):
        run(sys.argv[1])
    elif sys.argv[1:] == ["summarize"]:
        doc = summarize()
        with open(HERE / "d1-routes.json", "x", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(doc, indent=1, sort_keys=True) + "\n")
        print(json.dumps(doc, indent=1, sort_keys=True))
    else:
        raise SystemExit("usage: d1_routes.py decompose|route|summarize")
