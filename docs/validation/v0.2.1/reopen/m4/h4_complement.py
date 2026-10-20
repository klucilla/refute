"""The complement of the integrated H4 case (map Amendment 18; the maintainer's items 2 and 3 of
2026-10-18), for the record; the decision is the test's. Writes ``h4-complement.json`` next to
this file.

1. **The injected planet on the same curve** (the second construction: seed 3510, white 600 ppm
   plus AR(1) 400 ppm, a 270 ppm planet of ``synthetic.PLANET``'s ephemeris, the two-by-two
   layout, the round with 2020 hidden): the train search's candidates, whether the planet is among
   them, and the planet measured by the same computation as the H4 gate of ``plan_round`` (mask,
   re-detrending, per-point sigma, ``finalize_candidate``, ``event_noise``, ``_bls_gate``) at the
   planet's own period and duration instead of the search's candidate.
2. **The mechanism of the first construction's incompatibility** (seed 3509, AR(1) 800 ppm, a
   300 ppm planet): ``β`` per sector at the candidate's ``n_T`` on the detrended, masked train
   curve (what the gate reads) and on the raw normalized train curve (no detrending), with the
   robust and the plain per-cadence standard deviations, and the a priori estimate of the
   amendment evaluated with the measured white noise.

Run from the worktree root with the virtual environment's Python.
"""

import json
import math
from pathlib import Path

import numpy as np

from refute.packs.tess import rednoise, synthetic
from refute.packs.tess.detrend import detrend
from refute.packs.tess.events import per_point_sigma, transit_mask
from refute.packs.tess.holdout import train_validity
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import _bls_gate
from refute.packs.tess.rednoise import event_noise
from refute.packs.tess.search import finalize_candidate, search_period

HERE = Path(__file__).resolve().parent
PLANET = synthetic.PLANET
TWO_BY_TWO = (1325.0, 1353.0, 2061.0, 2089.0)
HIDDEN = 2020
GATE = 7.1


def _plan():
    plan = synthetic.fast_plan_dict()
    plan["gauntlet"] = {"corrections": {"version": 2, "enabled": True}}
    return TessTestPlan.model_validate(plan)


def _curve(depth, seed, red):
    spec = synthetic.SignalSpec(
        period=PLANET.period, t0=PLANET.t0, depth=depth, duration=PLANET.duration
    )
    lc, _ = synthetic.make_lightcurve(spec, sector_starts=TWO_BY_TWO, seed=seed, red_noise_ppm=red)
    return lc.select(lc.year != HIDDEN)


def _gate(train_raw, period, t0, duration, sde, plan):
    """The H4 gate of ``plan_round`` at a given ephemeris (the same calls, in the same order)."""
    half = plan.detrend.transit_mask_half_width_durations * duration
    flat = detrend(train_raw, plan.detrend, mask=transit_mask(train_raw.time, period, t0, half))
    sigma = per_point_sigma(flat, transit_mask(flat.time, period, t0, half))
    refit = finalize_candidate(flat, period, duration, plan.search, sde, sigma)
    noise = event_noise(flat, None, refit.period, refit.t0, refit.duration, plan)
    corrected, gate = _bls_gate(refit, flat, sigma, noise, None, plan.gauntlet)
    validity = train_validity(corrected, plan)
    return {
        "period": refit.period,
        "t0": refit.t0,
        "duration_hours": refit.duration * 24.0,
        "depth_ppm": refit.depth * 1e6,
        "bls_snr": refit.snr,
        "corrected_snr": corrected.snr,
        "beta_d": gate.metrics.get("beta_d"),
        "sector_betas": {k: v["beta"] for k, v in (gate.metrics.get("sectors") or {}).items()},
        "gate_status": gate.status.value,
        "passes_7_1": bool(math.isfinite(corrected.snr) and corrected.snr >= GATE),
        "validity_reasons": validity["reasons"],
    }, flat


def _near(period, target, tol=0.01):
    return any(abs(period / (target * k) - 1.0) <= tol for k in (0.5, 1.0, 2.0))


def planet_on_the_same_curve():
    plan = _plan()
    train_raw = _curve(270e-6, 3510, 400.0)
    search = search_period(detrend(train_raw, plan.detrend), plan.search)
    found = search.candidate
    candidate, _ = _gate(train_raw, found.period, found.t0, found.duration, found.sde, plan)
    planet, _ = _gate(train_raw, PLANET.period, PLANET.t0, PLANET.duration, float("nan"), plan)
    refined = [
        {"period": float(r["period"]), **{k: r[k] for k in r if k in ("power", "sde", "snr")}}
        for r in search.diagnostics.get("refined", [])
        if isinstance(r, dict) and "period" in r
    ]
    return {
        "search_candidate": {
            "period": found.period,
            "duration_hours": found.duration * 24.0,
            "depth_ppm": found.depth * 1e6,
            "sde": found.sde,
            "is_the_planet_or_an_alias": _near(found.period, PLANET.period),
        },
        "search_candidate_gate": candidate,
        "refined_candidates": refined,
        "planet_among_refined": any(_near(r["period"], PLANET.period) for r in refined),
        "planet_at_its_ephemeris": planet,
        "injected": {
            "period": PLANET.period,
            "t0": PLANET.t0,
            "duration_hours": PLANET.duration * 24.0,
            "depth_ppm": 270.0,
        },
    }


def first_construction_mechanism():
    plan = _plan()
    train_raw = _curve(300e-6, 3509, 800.0)
    found = search_period(detrend(train_raw, plan.detrend), plan.search).candidate
    gate, flat = _gate(train_raw, found.period, found.t0, found.duration, found.sde, plan)
    out = {"candidate": {"period": found.period, "duration_hours": found.duration * 24.0}}
    out["gate"] = gate
    cadence = plan.data.exptime_seconds / 86400.0
    n_t = max(1, int(round(gate["duration_hours"] / 24.0 / cadence)))
    duration = gate["duration_hours"] / 24.0
    half = plan.detrend.transit_mask_half_width_durations * duration
    for name, lc in (("detrended_masked", flat), ("raw_normalized", train_raw)):
        noise = event_noise(lc, None, gate["period"], gate["t0"], duration, plan)
        # the same estimate with the plain standard deviation in place of the robust one, for
        # sigma_w and for the spread of the bin means alike, on the same kept cadences (the
        # Codex stage review: the first version compared samples that differed)
        robust = rednoise.robust_sigma
        rednoise.robust_sigma = lambda x: float(np.std(np.asarray(x, dtype=float)))
        try:
            plain = event_noise(lc, None, gate["period"], gate["t0"], duration, plan)
        finally:
            rednoise.robust_sigma = robust
        keep = ~transit_mask(lc.time, gate["period"], gate["t0"], half)
        sectors = {}
        for s, v in sorted(noise.box.sectors.items()):
            resid = lc.flux[(lc.sector == s) & keep] - 1.0
            sectors[str(s)] = {
                "beta": v.beta,
                "beta_plain_std": plain.box.sectors[s].beta,
                "sigma_w_robust_ppm": v.sigma_w * 1e6,
                "sigma_w_plain_std_ppm": plain.box.sectors[s].sigma_w * 1e6,
                "std_kept_ppm": float(np.std(resid)) * 1e6,
                "n_bins": v.n_bins,
            }
        out[name] = {"n_t": noise.box.n, "sectors": sectors}
    # the a priori estimate of Amendment 18, beta^2 = 1 + n_T 0.49 A^2 / (sigma_white^2 + A^2),
    # at the n_T it assumed (75, a 2.5 h planet) and at the candidate's measured n_T
    a, sw = 800e-6, 600e-6
    out["a_priori"] = {
        f"n_t_{n}": math.sqrt(1.0 + n * 0.49 * a**2 / (sw**2 + a**2)) for n in (75, n_t)
    }
    return out


def main():
    out = {
        "note": "for the record; the decision is the test's (map Amendment 18)",
        "planet_on_the_same_curve": planet_on_the_same_curve(),
        "first_construction_mechanism": first_construction_mechanism(),
    }
    path = HERE / "h4-complement.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
