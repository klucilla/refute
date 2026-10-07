"""Gauntlet v0.1: deterministic falsification tests for a transit candidate.

Each function returns a :class:`~refute.core.verdict.TestResult` carrying the
thresholds it used and the provenance of its inputs. The blind holdout (test e)
lives in :mod:`refute.packs.tess.holdout` because it must never see the candidate.
See ``docs/gauntlet-tess-v0.1.md``.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
from astropy import constants

from refute.core.verdict import Severity, TestResult, TestStatus
from refute.packs.tess.events import EventDepths, group_mean
from refute.packs.tess.params import (
    OddEvenParams,
    PlausibilityParams,
    SecondaryParams,
    SnrParams,
)
from refute.packs.tess.types import Candidate, StarInfo

G_SI = constants.G.value
M_SUN_KG = constants.M_sun.value
R_SUN_M = constants.R_sun.value
R_JUP_M = constants.R_jup.value
G_CGS = constants.G.cgs.value
M_SUN_G = constants.M_sun.cgs.value
R_SUN_CM = constants.R_sun.cgs.value


def check_snr(candidate: Candidate | None, params: SnrParams) -> TestResult:
    """(a) Gate: the box depth must be at least ``min_snr`` times its uncertainty."""
    thresholds = {"min_snr": params.min_snr}
    if candidate is None:
        return TestResult(
            "snr",
            TestStatus.FAIL,
            Severity.GATE,
            "the period search found no candidate signal",
            thresholds=thresholds,
        )
    metrics = {
        "snr": candidate.snr,
        "depth_ppm": candidate.depth * 1e6,
        "depth_err_ppm": candidate.depth_err * 1e6,
        "sde_stage1": candidate.sde,
        "n_transits_with_data": candidate.n_transits,
    }
    passed = math.isfinite(candidate.snr) and candidate.snr >= params.min_snr
    return TestResult(
        "snr",
        TestStatus.PASS if passed else TestStatus.FAIL,
        Severity.GATE,
        f"SNR {candidate.snr:.1f} {'>=' if passed else '<'} {params.min_snr}",
        metrics=metrics,
        thresholds=thresholds,
    )


def check_odd_even(events: EventDepths, params: OddEvenParams) -> TestResult:
    """(b) Odd and even transit depths must agree within ``max_sigma``."""
    thresholds = {"max_sigma": params.max_sigma, "min_transits_each": params.min_transits_each}
    even = events.subset(events.epochs % 2 == 0)
    odd = events.subset(events.epochs % 2 != 0)
    if len(even) < params.min_transits_each or len(odd) < params.min_transits_each:
        return TestResult(
            "odd_even",
            TestStatus.INCONCLUSIVE,
            Severity.FATAL,
            f"not enough transits: {len(even)} even, {len(odd)} odd",
            metrics={"n_even": len(even), "n_odd": len(odd)},
            thresholds=thresholds,
        )
    g_even = group_mean(even.depths, even.errors)
    g_odd = group_mean(odd.depths, odd.errors)
    sigma = abs(g_even.mean - g_odd.mean) / math.hypot(g_even.error, g_odd.error)
    passed = sigma <= params.max_sigma
    metrics = {
        "depth_even_ppm": g_even.mean * 1e6,
        "depth_even_err_ppm": g_even.error * 1e6,
        "depth_odd_ppm": g_odd.mean * 1e6,
        "depth_odd_err_ppm": g_odd.error * 1e6,
        "n_even": g_even.n,
        "n_odd": g_odd.n,
        "difference_sigma": sigma,
    }
    return TestResult(
        "odd_even",
        TestStatus.PASS if passed else TestStatus.FAIL,
        Severity.FATAL,
        f"odd/even depth difference {sigma:.2f} sigma "
        f"({'<=' if passed else '>'} {params.max_sigma})",
        metrics=metrics,
        thresholds=thresholds,
    )


def check_secondary_eclipse(
    primary: EventDepths, secondary: EventDepths, params: SecondaryParams
) -> TestResult:
    """(c) No significant eclipse at phase 0.5; a deep one is fatal, a shallow one a warning."""
    thresholds = {"max_sigma": params.max_sigma, "fatal_depth_ratio": params.fatal_depth_ratio}
    if len(secondary) == 0 or len(primary) == 0:
        return TestResult(
            "secondary_eclipse",
            TestStatus.INCONCLUSIVE,
            Severity.FATAL,
            "no data covers phase 0.5" if len(secondary) == 0 else "no primary events measured",
            metrics={"n_secondary_events": len(secondary), "n_primary_events": len(primary)},
            thresholds=thresholds,
        )
    g_sec = group_mean(secondary.depths, secondary.errors)
    g_pri = group_mean(primary.depths, primary.errors)
    significance = g_sec.mean / g_sec.error
    ratio = g_sec.mean / g_pri.mean if g_pri.mean > 0 else float("inf")
    metrics = {
        "secondary_depth_ppm": g_sec.mean * 1e6,
        "secondary_depth_err_ppm": g_sec.error * 1e6,
        "secondary_sigma": significance,
        "primary_depth_ppm": g_pri.mean * 1e6,
        "depth_ratio": ratio,
        "n_secondary_events": g_sec.n,
    }
    if significance < params.max_sigma:
        return TestResult(
            "secondary_eclipse",
            TestStatus.PASS,
            Severity.FATAL,
            f"no significant eclipse at phase 0.5 ({significance:.2f} sigma)",
            metrics=metrics,
            thresholds=thresholds,
        )
    severity = Severity.FATAL if ratio >= params.fatal_depth_ratio else Severity.WARNING
    return TestResult(
        "secondary_eclipse",
        TestStatus.FAIL,
        severity,
        f"eclipse at phase 0.5: {significance:.1f} sigma, depth ratio {ratio:.3f} "
        f"({'>=' if severity is Severity.FATAL else '<'} {params.fatal_depth_ratio})",
        metrics=metrics,
        thresholds=thresholds,
    )


def _valid(value: float | None) -> bool:
    return value is not None and math.isfinite(value) and value > 0


def star_inputs(star: StarInfo | None) -> dict[str, Any]:
    if star is None:
        return {"stellar_parameters": None}
    return {
        "stellar_parameters_source": star.source,
        "tic_version": star.tic_version,
        "retrieved_utc": star.retrieved_utc,
        "radius_rsun": star.radius_rsun,
        "radius_err_rsun": star.radius_err_rsun,
        "mass_msun": star.mass_msun,
        "logg_cgs": star.logg_cgs,
    }


def stellar_mass_msun(star: StarInfo) -> tuple[float | None, str]:
    if _valid(star.mass_msun):
        return float(star.mass_msun), "TIC mass"
    if star.logg_cgs is not None and math.isfinite(star.logg_cgs) and _valid(star.radius_rsun):
        grav = 10.0**star.logg_cgs
        mass = grav * (star.radius_rsun * R_SUN_CM) ** 2 / G_CGS / M_SUN_G
        return float(mass), "TIC logg and radius"
    return None, "unavailable"


def max_transit_duration(period: float, mass_msun: float, radius_rsun: float, k: float) -> float:
    """Longest central-transit duration (days) of a circular orbit: P/pi * asin((1+k) R*/a)."""
    period_s = period * 86400.0
    a = (G_SI * mass_msun * M_SUN_KG * period_s**2 / (4.0 * math.pi**2)) ** (1.0 / 3.0)
    ratio = (1.0 + k) * radius_rsun * R_SUN_M / a
    return period / math.pi * math.asin(min(1.0, ratio))


def check_plausibility(
    candidate: Candidate, star: StarInfo | None, params: PlausibilityParams
) -> TestResult:
    """(d) Companion radius from depth and stellar radius; duration vs the circular-orbit maximum.

    Needs a reliable TIC stellar radius. If it is missing or its relative error
    exceeds ``max_stellar_radius_rel_err``, the test is INCONCLUSIVE, never PASS.
    """
    thresholds = {
        "max_companion_radius_rjup": params.max_companion_radius_rjup,
        "max_duration_ratio": params.max_duration_ratio,
        "max_stellar_radius_rel_err": params.max_stellar_radius_rel_err,
    }
    inputs = star_inputs(star)
    if star is None or not _valid(star.radius_rsun):
        return TestResult(
            "plausibility",
            TestStatus.INCONCLUSIVE,
            Severity.FATAL,
            "no TIC stellar radius available",
            thresholds=thresholds,
            inputs=inputs,
        )
    if not _valid(star.radius_err_rsun):
        return TestResult(
            "plausibility",
            TestStatus.INCONCLUSIVE,
            Severity.FATAL,
            "TIC stellar radius has no uncertainty; reliability cannot be assessed",
            thresholds=thresholds,
            inputs=inputs,
        )
    rel_err = star.radius_err_rsun / star.radius_rsun
    if rel_err > params.max_stellar_radius_rel_err:
        return TestResult(
            "plausibility",
            TestStatus.INCONCLUSIVE,
            Severity.FATAL,
            f"TIC stellar radius too uncertain ({rel_err:.2f} > "
            f"{params.max_stellar_radius_rel_err})",
            metrics={"stellar_radius_rel_err": rel_err},
            thresholds=thresholds,
            inputs=inputs,
        )

    k = math.sqrt(max(candidate.depth, 0.0))
    companion_rjup = k * star.radius_rsun * R_SUN_M / R_JUP_M
    metrics: dict[str, Any] = {
        "radius_ratio": k,
        "companion_radius_rjup": companion_rjup,
        "stellar_radius_rel_err": rel_err,
    }
    if companion_rjup > params.max_companion_radius_rjup:
        return TestResult(
            "plausibility",
            TestStatus.FAIL,
            Severity.FATAL,
            f"implied companion radius {companion_rjup:.2f} R_Jup > "
            f"{params.max_companion_radius_rjup} R_Jup: too large for a planet",
            metrics=metrics,
            thresholds=thresholds,
            inputs=inputs,
        )

    mass, mass_source = stellar_mass_msun(star)
    metrics["stellar_mass_msun"] = mass
    metrics["stellar_mass_source"] = mass_source
    if mass is None:
        return TestResult(
            "plausibility",
            TestStatus.INCONCLUSIVE,
            Severity.WARNING,
            "companion radius is plausible, but no stellar mass to check the duration",
            metrics=metrics,
            thresholds=thresholds,
            inputs=inputs,
        )
    t_max = max_transit_duration(candidate.period, mass, star.radius_rsun, k)
    ratio = candidate.duration / t_max if t_max > 0 else float(np.inf)
    metrics["duration_hours"] = candidate.duration * 24.0
    metrics["max_duration_hours"] = t_max * 24.0
    metrics["duration_ratio"] = ratio
    if ratio > params.max_duration_ratio:
        return TestResult(
            "plausibility",
            TestStatus.FAIL,
            Severity.WARNING,
            f"duration {candidate.duration * 24:.2f} h is {ratio:.2f} times the circular-orbit "
            f"maximum ({t_max * 24:.2f} h)",
            metrics=metrics,
            thresholds=thresholds,
            inputs=inputs,
        )
    return TestResult(
        "plausibility",
        TestStatus.PASS,
        Severity.FATAL,
        f"companion radius {companion_rjup:.2f} R_Jup and duration ratio {ratio:.2f} are plausible",
        metrics=metrics,
        thresholds=thresholds,
        inputs=inputs,
    )
