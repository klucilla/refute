"""The sensitivity rule in the TESS pack (v0.5 WP1, issue #185; docs/plans/v0.5-acceptance.md).

``TESS_REGISTRY`` says, for every test of a v0.5 claim and each of its sub-checks, whether it is
a statistical rule (with its required probability) or an applicability category. The functions
below compute the sensitivity blocks of the tests the v0.4 battery already had, from each
result's own measurements, against its full rejection region and the declared alternative.
The v0.4 check functions are not changed: in a v0.5 plan the pipeline attaches these blocks to
their results; the tests whose rule changes in v0.5 live in ``refute.packs.tess.battery_v5``.
"""

from __future__ import annotations

import math
from dataclasses import replace
from typing import TYPE_CHECKING, Any

import numpy as np

from refute.core.sensitivity import (
    category_block,
    gaussian_probability,
    not_applicable_block,
    rule_block,
    seed_for,
    simulated_probability,
)
from refute.core.verdict import TestResult, TestStatus

if TYPE_CHECKING:
    from refute.packs.tess.params import StrongerParams, TessTestPlan
    from refute.packs.tess.types import Candidate, LightCurveData, SectorAux

TESS_REGISTRY: dict[str, dict[str, str]] = {
    "odd_even": {"main": "rule"},
    "secondary_eclipse": {"dip": "rule", "brightening": "rule"},
    "plausibility": {"radius": "deterministic-bound", "duration": "deterministic-bound"},
    "centroid_shift": {"main": "rule"},
    "aperture_depth": {"main": "rule"},
    "nearby_contamination": {"main": "catalog-lookup"},
    # detectable iff at least 45 of 50 simulated sinusoids fail the test (acceptance WP1)
    "period_alias": {"main": "rule@0.9"},
    "systematics": {"dumps": "fraction", "sap": "rule", "background": "rule"},
    "eb_catalog": {"main": "catalog-lookup"},
    "single_event": {"main": "rule"},
    "event_consistency": {"main": "rule"},
    "edge_events": {"proximity": "fraction", "comparison": "rule?"},
    "sinusoid": {"main": "rule"},
    "duty_cycle": {"main": "deterministic-bound"},
    "transit_shape": {"main": "rule"},
    "depth_stability": {"main": "rule"},
}


# v0.5.1 (discovery version 3, docs/plans/v0.5.1-acceptance.md): the registry of the corrected
# battery. `sinusoid` has one sub-check per harmonic: P/2 required (always inside its domain for
# the searched periods), P and 2P conditional (not applicable outside their domain; WP3 (b)).
TESS_REGISTRY_V3: dict[str, dict[str, str]] = {
    **TESS_REGISTRY,
    "sinusoid": {"P/2": "rule", "P": "rule?", "2P": "rule?"},
}


def registry_for(plan: TessTestPlan) -> dict[str, dict[str, str]]:
    """The registry of a plan's battery: v0.5.1's for discovery version 3, v0.5's otherwise."""
    return TESS_REGISTRY_V3 if plan.is_v051 else TESS_REGISTRY


def attach(result: TestResult, blocks: dict[str, dict[str, Any]] | None) -> TestResult:
    """The result with its sensitivity blocks (an empty set means "none computed")."""
    return replace(result, sensitivity=blocks or None)


def _ppm(metrics: dict[str, Any], key: str) -> float | None:
    value = metrics.get(key)
    if value is None or not math.isfinite(float(value)):
        return None
    return float(value) / 1e6


# --- odd_even -----------------------------------------------------------------------------


def odd_even_blocks(result: TestResult, depth: float, sp: StrongerParams) -> dict | None:
    """Gaussian closed form: the odd/even difference, alternative = the depth (#185)."""
    m = result.metrics
    e_even, e_odd = _ppm(m, "depth_even_err_ppm"), _ppm(m, "depth_odd_err_ppm")
    if e_even is None or e_odd is None:
        return None
    alternative = sp.odd_even_alternative_depth_fraction * depth
    sigma = math.hypot(e_even, e_odd)
    probability = gaussian_probability(alternative, sigma, result.thresholds["max_sigma"])
    block = rule_block(
        "odd/even depth difference", alternative * 1e6, "ppm", "gaussian-1", probability
    )
    return {"main": block}


# --- aperture_depth -----------------------------------------------------------------------


def aperture_blocks(result: TestResult, sp: StrongerParams, seed: int) -> dict | None:
    """Sufficient-statistic simulation over the compound region (difference at max_sigma and
    ratio at least min_depth_ratio), alternative ratio = min_depth_ratio + 0.3."""
    m = result.metrics
    core, e_core = _ppm(m, "depth_core_ppm"), _ppm(m, "depth_core_err_ppm")
    e_large = _ppm(m, "depth_large_err_ppm")
    if core is None or e_core is None or e_large is None:
        return None
    max_sigma = float(result.thresholds["max_sigma"])
    min_ratio = float(result.thresholds["min_depth_ratio"])
    ratio_alt = min_ratio + sp.aperture_alternative_ratio_increment
    if not (core > 0):
        probability = 0.0
    else:

        def draw(rng: np.random.Generator, n: int):
            c = core + e_core * rng.standard_normal(n)
            big = core * ratio_alt + e_large * rng.standard_normal(n)
            return c, big

        def reject(stats):
            c, big = stats
            diff = (big - c) / math.hypot(e_large, e_core)
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = np.where(c > 0, big / c, np.inf)
            return (diff >= max_sigma) & (ratio >= min_ratio)

        probability = simulated_probability(draw, reject, seed)
    block = rule_block(
        "large-to-core depth ratio", ratio_alt, "ratio", "compound-sim-1", probability
    )
    return {"main": block}


# --- systematics --------------------------------------------------------------------------


def systematics_blocks(
    result: TestResult,
    aux: list[SectorAux],
    candidate: Candidate,
    plan: TessTestPlan,
    seed: int,
) -> dict | None:
    """Three sub-checks: dumps (category ``fraction``), SAP versus PDCSAP and the background
    rise (sufficient-statistic simulations over their compound regions). The group means are
    measured again with the calls of ``check_systematics`` (``event_shift``), which is not
    changed."""
    from refute.packs.tess.battery import event_shift

    if not aux:
        return None
    sp = plan.stronger
    params = plan.gauntlet.systematics
    time = np.concatenate([a.time for a in aux])
    sector = np.concatenate([np.full(a.time.size, a.sector) for a in aux])
    g_pdc = event_shift(time, np.concatenate([a.pdcsap_flux for a in aux]), sector, candidate, plan)
    g_sap = event_shift(time, np.concatenate([a.sap_flux for a in aux]), sector, candidate, plan)
    g_bkg = event_shift(time, np.concatenate([a.sap_bkg for a in aux]), sector, candidate, plan)
    crowds = [a.crowdsap for a in aux if a.crowdsap is not None]
    blocks: dict[str, dict] = {
        "dumps": category_block(
            "fraction",
            f"fraction of the transits near momentum dumps, against {params.max_dump_fraction}",
        )
    }
    if crowds and g_pdc is not None and g_sap is not None and g_pdc.mean > 0:
        crowd = float(np.median(crowds))
        pdc, e_pdc, e_sap = g_pdc.mean, g_pdc.error, g_sap.error
        rel_alt = params.max_sap_rel_diff + sp.sap_alternative_increment

        # the SAP and PDCSAP depths drawn jointly (Codex's review of round 2): the expected SAP
        # depth in the rule is the measured PDCSAP depth times CROWDSAP, not a fixed value
        def draw_sap(rng, n):
            p_hat = pdc + e_pdc * rng.standard_normal(n)
            s_hat = crowd * pdc * (1.0 + rel_alt) + e_sap * rng.standard_normal(n)
            return p_hat, s_hat

        def reject_sap(stats):
            p_hat, s_hat = stats
            expected = crowd * p_hat
            diff = np.abs(s_hat - expected)
            with np.errstate(divide="ignore", invalid="ignore"):
                rel = np.where(expected > 0, diff / expected, 0.0)
            sigma = math.hypot(e_sap, crowd * e_pdc)
            return (
                (p_hat > 0)
                & (diff / sigma >= params.max_sap_sigma)
                & (rel >= params.max_sap_rel_diff)
            )

        ok = e_sap > 0 or e_pdc > 0
        p = simulated_probability(draw_sap, reject_sap, seed) if ok else 0.0
        blocks["sap"] = rule_block(
            "SAP relative depth difference", rel_alt, "fraction", "compound-sim-1", p
        )
    if g_bkg is not None and g_sap is not None and g_sap.mean > 0 and g_bkg.error > 0:
        frac_alt = params.max_background_fraction + sp.background_alternative_increment
        e_bkg, sap_depth, e_sap = g_bkg.error, g_sap.mean, g_sap.error

        # the background rise and the SAP depth drawn jointly, with the positivity branch
        def draw_bkg(rng, n):
            s_hat = sap_depth + e_sap * rng.standard_normal(n)
            rise = frac_alt * sap_depth + e_bkg * rng.standard_normal(n)
            return s_hat, rise

        def reject_bkg(stats):
            s_hat, rise = stats
            with np.errstate(divide="ignore", invalid="ignore"):
                frac = np.where(s_hat > 0, rise / s_hat, 0.0)
            return (
                (s_hat > 0)
                & (rise / e_bkg >= params.max_background_sigma)
                & (frac >= params.max_background_fraction)
            )

        p = simulated_probability(draw_bkg, reject_bkg, seed + 1)
        blocks["background"] = rule_block(
            "background rise in transit", frac_alt, "fraction of the depth", "compound-sim-1", p
        )
    return blocks


# --- period_alias -------------------------------------------------------------------------


def period_alias_blocks(
    lc: LightCurveData, candidate: Candidate, plan: TessTestPlan, check, seed: int
) -> dict:
    """Full-data simulation: ``period_alias_realizations`` seeded realizations of a sinusoid at
    the candidate's period, peak to trough equal to the depth, on the candidate's own times and
    errors; detectable iff at least ``period_alias_required_failures`` of them FAIL the test."""
    sp = plan.stronger
    n = sp.period_alias_realizations
    rng = np.random.default_rng(seed)
    amplitude = candidate.depth / 2.0
    errors = np.where(
        np.isfinite(lc.flux_err) & (lc.flux_err > 0), lc.flux_err, np.nanmedian(lc.flux_err)
    )
    failures = 0
    for _ in range(n):
        phase = rng.uniform(0.0, 2.0 * math.pi)
        model = 1.0 + amplitude * np.cos(
            2.0 * math.pi * (lc.time - candidate.t0) / candidate.period + phase
        )
        flux = model + errors * rng.standard_normal(lc.time.size)
        trial = replace(lc, flux=flux)
        if check(trial, candidate, plan).status is TestStatus.FAIL:
            failures += 1
    required = sp.period_alias_required_failures / n
    block = rule_block(
        "sinusoid at the candidate's period, peak to trough = depth",
        candidate.depth * 1e6,
        "ppm",
        "alias-sim-1",
        failures / n,
        required=required,
    )
    block["failures"], block["realizations"] = failures, n
    return {"main": block}


# --- categories ---------------------------------------------------------------------------


def plausibility_blocks(result: TestResult) -> dict | None:
    if result.status is not TestStatus.PASS:
        return None
    return {
        "radius": category_block(
            "deterministic-bound", "companion radius from the depth and the TIC radius"
        ),
        "duration": category_block(
            "deterministic-bound", "duration against the circular-orbit maximum for the TIC star"
        ),
    }


def catalog_blocks(result: TestResult, what: str) -> dict:
    return {
        "main": category_block(
            "catalog-lookup", f"{what}; coverage = {result.coverage} {result.coverage_unit}"
        )
    }


def conditional_not_applicable(reason: str) -> dict[str, Any]:
    return not_applicable_block(reason)


def candidate_seed(name: str, candidate: Candidate) -> int:
    return seed_for(
        name, round(candidate.period, 9), round(candidate.t0, 7), round(candidate.depth, 9)
    )


def period_alias_plan(plan: TessTestPlan) -> TessTestPlan:
    """A version-3 plan's period_alias with ``v051.period_alias_harmonics`` harmonics (WP3 (c));
    the v0.4 and v0.5 plans keep theirs."""
    alias = plan.gauntlet.period_alias.model_copy(
        update={"sine_harmonics": plan.v051.period_alias_harmonics}
    )
    gauntlet = plan.gauntlet.model_copy(update={"period_alias": alias})
    return plan.model_copy(update={"gauntlet": gauntlet})


def period_alias_blocks_v51(
    lc: LightCurveData, candidate: Candidate, plan: TessTestPlan, check, seed: int
) -> dict:
    """WP3 (c), version 3: ``v051.period_alias_realizations`` seeded sinusoids at the candidate's
    period (peak to trough = the depth) on the candidate's own times and errors; detectable when
    the exact one-sided 95 % lower bound (Clopper-Pearson) of the failure fraction is at least
    ``v051.period_alias_required_lower_bound``. ``probability`` is that lower bound."""
    from scipy.stats import beta

    cp = plan.v051
    n = cp.period_alias_realizations
    rng = np.random.default_rng(seed)
    amplitude = candidate.depth / 2.0
    errors = np.where(
        np.isfinite(lc.flux_err) & (lc.flux_err > 0), lc.flux_err, np.nanmedian(lc.flux_err)
    )
    failures = 0
    for _ in range(n):
        phase = rng.uniform(0.0, 2.0 * math.pi)
        model = 1.0 + amplitude * np.cos(
            2.0 * math.pi * (lc.time - candidate.t0) / candidate.period + phase
        )
        flux = model + errors * rng.standard_normal(lc.time.size)
        if check(replace(lc, flux=flux), candidate, plan).status is TestStatus.FAIL:
            failures += 1
    lower = float(beta.ppf(0.05, failures, n - failures + 1)) if failures > 0 else 0.0
    block = rule_block(
        "sinusoid at the candidate's period, peak to trough = depth",
        candidate.depth * 1e6,
        "ppm",
        "alias-sim-2",
        lower,
        required=cp.period_alias_required_lower_bound,
    )
    block["failures"], block["realizations"] = failures, n
    block["failure_fraction"] = failures / n
    return {"main": block}
