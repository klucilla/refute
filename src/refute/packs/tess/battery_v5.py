"""The v0.5 tests (docs/plans/v0.5-acceptance.md, WP2 and WP3), each with its sensitivity block.

They run only in a v0.5 claim (discovery version 2). Their thresholds are in the plan's
``stronger`` section (``refute.packs.tess.params.StrongerParams``); the provenance of each
number is in the acceptance documents. A test outside its domain (too few events, a period
beyond the sinusoid test's reach) is INCONCLUSIVE, never PASS.

- ``secondary_eclipse`` (two-sided, warning only): a dip or a brightening at phase 0.5.
- ``single_event`` (fatal): the largest single-event SNR over the total SNR.
- ``event_consistency`` (fatal): the per-event depths against a common depth.
- ``edge_events`` (warning): events next to a segment edge or a gap.
- ``sinusoid`` (warning): a sinusoid at P/2, P or 2P in the undetrended flux.
- ``duty_cycle`` (fatal): duration over period above the bound.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

from refute.core.chi2 import chi2_isf, chi2_sf, ncx2_sf
from refute.core.sensitivity import (
    category_block,
    gaussian_probability,
    not_applicable_block,
    rule_block,
    simulated_probability,
)
from refute.core.verdict import Severity, TestResult, TestStatus
from refute.packs.tess.events import EventDepths, group_mean

if TYPE_CHECKING:
    from refute.packs.tess.params import SecondaryParams, StrongerParams
    from refute.packs.tess.types import Candidate, LightCurveData

EVENTS = "measured events"


def _inconclusive(name: str, severity: Severity, why: str, **metrics) -> TestResult:
    return TestResult(name, TestStatus.INCONCLUSIVE, severity, why, metrics=metrics)


# --- secondary_eclipse, two-sided (WP3) ---------------------------------------------------


def check_secondary_two_sided(
    primary: EventDepths,
    secondary: EventDepths,
    params: SecondaryParams,
    sp: StrongerParams,
    seed: int,
) -> TestResult:
    """A dip or a brightening at phase 0.5, each a warning (never fatal in v0.5). Not covered:
    eccentric secondaries away from phase 0.5; a secondary alone does not classify an
    eclipsing binary; a planet's occultation is not modelled (#181)."""
    name, severity = "secondary_eclipse", Severity.WARNING
    thresholds = {
        "max_sigma": params.max_sigma,
        "brightening_min_depth_ratio": sp.brightening_min_depth_ratio,
    }
    if len(secondary) == 0 or len(primary) == 0:
        why = "no data covers phase 0.5" if len(secondary) == 0 else "no primary events measured"
        return _inconclusive(name, severity, why)
    g_sec = group_mean(secondary.depths, secondary.errors)
    g_pri = group_mean(primary.depths, primary.errors)
    sig = g_sec.mean / g_sec.error
    ratio = g_sec.mean / g_pri.mean if g_pri.mean > 0 else float("inf")
    metrics = {
        "secondary_depth_ppm": g_sec.mean * 1e6,
        "secondary_depth_err_ppm": g_sec.error * 1e6,
        "secondary_sigma": sig,
        "primary_depth_ppm": g_pri.mean * 1e6,
        "depth_ratio": ratio,
        "n_secondary_events": g_sec.n,
    }
    alternative = sp.secondary_alternative_depth_fraction * max(g_pri.mean, 0.0)
    dip = gaussian_probability(alternative, g_sec.error, params.max_sigma)
    floor = sp.brightening_min_depth_ratio * max(g_pri.mean, 0.0)
    e_sec = g_sec.error

    def draw(rng, n):
        return alternative + e_sec * rng.standard_normal(n)

    def reject(b):
        return (b / e_sec >= params.max_sigma) & (b >= floor)

    bright = simulated_probability(draw, reject, seed) if alternative > 0 else 0.0
    blocks = {
        "dip": rule_block("secondary dip", alternative * 1e6, "ppm", "gaussian-1", dip),
        "brightening": rule_block(
            "brightening at phase 0.5", alternative * 1e6, "ppm", "compound-sim-1", bright
        ),
    }
    common = dict(metrics=metrics, thresholds=thresholds, coverage=g_sec.n)
    common["coverage_unit"] = "phase-0.5 windows measured"
    if sig >= params.max_sigma:
        message = f"dip at phase 0.5: {sig:.1f} sigma, depth ratio {ratio:.3f}"
        return TestResult(name, TestStatus.FAIL, severity, message, sensitivity=blocks, **common)
    if -sig >= params.max_sigma and -g_sec.mean >= floor:
        message = (
            f"brightening at phase 0.5: {-sig:.1f} sigma, {-g_sec.mean * 1e6:.0f} ppm: "
            "possible variability"
        )
        return TestResult(name, TestStatus.FAIL, severity, message, sensitivity=blocks, **common)
    message = f"no significant dip or brightening at phase 0.5 ({sig:.2f} sigma)"
    return TestResult(name, TestStatus.PASS, severity, message, sensitivity=blocks, **common)


# --- single_event and event_consistency (WP2) ---------------------------------------------


def _total_snr(depths: np.ndarray, errors: np.ndarray) -> np.ndarray:
    """The inverse-variance total SNR, along the last axis."""
    w = 1.0 / np.square(errors)
    return np.sum(depths * w, axis=-1) / np.sqrt(np.sum(w, axis=-1))


def check_single_event(events: EventDepths, sp: StrongerParams, seed: int) -> TestResult:
    """Fatal when one event carries the signal: the largest single-event SNR over the total
    SNR above ``single_event_max_ratio`` (Kunimoto et al. 2025, III.11; beyond 10 events a
    Refute adaptation). At least ``min_measured_events`` measured events, else INCONCLUSIVE."""
    name, severity = "single_event", Severity.FATAL
    thresholds = {"max_ratio": sp.single_event_max_ratio, "min_events": sp.min_measured_events}
    n = len(events)
    if n < sp.min_measured_events:
        return _inconclusive(name, severity, f"only {n} measured event(s)", n_events=n)
    d, e = events.depths, events.errors
    total = float(_total_snr(d, e))
    if not total > 0:
        return _inconclusive(name, severity, "the total SNR is not positive", n_events=n)
    snr = d / e
    ratio = float(np.max(snr) / total)
    w_sum = float(np.sum(1.0 / np.square(e)))
    limit = sp.single_event_max_ratio

    probabilities = []
    for k in range(n):
        # the alternative: event k alone holds a signal of the observed total SNR
        truth = np.zeros(n)
        truth[k] = total * e[k] ** 2 * math.sqrt(w_sum)

        def draw(rng, m, truth=truth):
            return truth + e * rng.standard_normal((m, n))

        def reject(x):
            tot = _total_snr(x, e)
            with np.errstate(divide="ignore", invalid="ignore"):
                r = np.max(x / e, axis=1) / tot
            return (tot > 0) & (r > limit)

        probabilities.append(simulated_probability(draw, reject, seed + k))
    worst = int(np.argmin(probabilities))
    block = rule_block(
        "one event holds the whole signal",
        total,
        "total SNR",
        "single-event-sim-1",
        probabilities[worst],
    )
    block["worst_event"] = int(events.epochs[worst])
    metrics = {
        "max_event_snr": float(np.max(snr)),
        "total_snr": total,
        "ratio": ratio,
        "n_events": n,
    }
    passed = ratio <= limit
    message = (
        f"largest single-event SNR {ratio:.2f} of the total ({'<=' if passed else '>'} {limit})"
    )
    return TestResult(
        name,
        TestStatus.PASS if passed else TestStatus.FAIL,
        severity,
        message,
        metrics=metrics,
        thresholds=thresholds,
        coverage=n,
        coverage_unit=EVENTS,
        sensitivity={"main": block},
    )


def check_event_consistency(events: EventDepths, sp: StrongerParams) -> TestResult:
    """Fatal when the per-event depths disagree with one common depth: chi-square about the
    weighted mean, p below ``chi2_alpha``. Sensitivity: the non-central chi-square power for
    one event off the common depth by a full depth, at the worst eligible event."""
    name, severity = "event_consistency", Severity.FATAL
    thresholds = {"alpha": sp.chi2_alpha, "min_events": sp.min_measured_events}
    n = len(events)
    if n < sp.min_measured_events:
        return _inconclusive(name, severity, f"only {n} measured event(s)", n_events=n)
    d, e = events.depths, events.errors
    w = 1.0 / np.square(e)
    w_sum = float(np.sum(w))
    mean = float(np.sum(w * d) / w_sum)
    chi2 = float(np.sum(w * np.square(d - mean)))
    dof = n - 1
    p = chi2_sf(chi2, dof)
    critical = chi2_isf(sp.chi2_alpha, dof)
    delta = max(mean, 0.0)
    lams = delta**2 * w * (1.0 - w / w_sum)
    powers = [ncx2_sf(critical, dof, float(lam)) for lam in lams]
    worst = int(np.argmin(powers))
    block = rule_block(
        "one event off the common depth by a full depth",
        delta * 1e6,
        "ppm",
        "ncx2-1",
        powers[worst],
    )
    block["worst_event"] = int(events.epochs[worst])
    metrics = {"chi2": chi2, "dof": dof, "p_value": p, "common_depth_ppm": mean * 1e6}
    passed = p >= sp.chi2_alpha
    message = f"per-event depths: chi2 {chi2:.1f} for {dof} dof, p = {p:.2g}"
    return TestResult(
        name,
        TestStatus.PASS if passed else TestStatus.FAIL,
        severity,
        message,
        metrics=metrics,
        thresholds=thresholds,
        coverage=n,
        coverage_unit=EVENTS,
        sensitivity={"main": block},
    )


# --- edge_events (WP2) --------------------------------------------------------------------


def segment_edges(time: np.ndarray, gap_days: float) -> np.ndarray:
    """The start and end times of the data segments split by gaps of at least ``gap_days``."""
    if time.size == 0:
        return np.zeros(0)
    t = np.sort(time)
    breaks = np.flatnonzero(np.diff(t) >= gap_days)
    starts = np.concatenate([[t[0]], t[breaks + 1]])
    ends = np.concatenate([t[breaks], [t[-1]]])
    return np.sort(np.concatenate([starts, ends]))


def check_edge_events(
    time: np.ndarray,
    events: EventDepths,
    duration: float,
    min_snr: float,
    sp: StrongerParams,
) -> TestResult:
    """Warning when half or more of the measured events lie next to a segment edge (an event's
    mid-center within ``edge_reach_durations`` durations of an edge of a gap of at least
    ``edge_gap_days``; Kunimoto et al. 2025, III.12) and the depth of those events differs, at
    3 sigma, from the depth of the others. INCONCLUSIVE if the others give an SNR below
    ``min_snr``."""
    name, severity = "edge_events", Severity.WARNING
    thresholds = {
        "gap_days": sp.edge_gap_days,
        "reach_durations": sp.edge_reach_durations,
        "min_fraction": sp.edge_min_fraction,
        "max_sigma": 3.0,
    }
    n = len(events)
    if n == 0:
        return _inconclusive(name, severity, "no measured event")
    edges = segment_edges(time, sp.edge_gap_days)
    reach = sp.edge_reach_durations * duration
    near = np.array(
        [bool(edges.size and np.min(np.abs(edges - c)) <= reach) for c in events.centers]
    )
    fraction = float(near.mean())
    proximity = category_block(
        "fraction", f"fraction of events near an edge, against {sp.edge_min_fraction}"
    )
    metrics = {"n_events": n, "n_near_edges": int(near.sum()), "fraction_near_edges": fraction}
    common = dict(metrics=metrics, thresholds=thresholds, coverage=n, coverage_unit=EVENTS)
    if fraction < sp.edge_min_fraction:
        blocks = {
            "proximity": proximity,
            "comparison": not_applicable_block(
                "fewer than the minimum fraction of events near an edge"
            ),
        }
        message = f"{int(near.sum())} of {n} events near a segment edge ({fraction:.0%})"
        return TestResult(name, TestStatus.PASS, severity, message, sensitivity=blocks, **common)
    others = events.subset(~near)
    edge = events.subset(near)
    if len(others) == 0:
        return _inconclusive(
            name, severity, "every measured event is near a segment edge", **metrics
        )
    g_other = group_mean(others.depths, others.errors)
    g_edge = group_mean(edge.depths, edge.errors)
    if not g_other.mean / g_other.error >= min_snr:
        why = f"the events away from edges give SNR {g_other.mean / g_other.error:.1f} < {min_snr}"
        return _inconclusive(name, severity, why, **metrics)
    sigma = math.hypot(g_edge.error, g_other.error)
    diff_sigma = (g_edge.mean - g_other.mean) / sigma
    metrics.update(
        {
            "depth_edge_ppm": g_edge.mean * 1e6,
            "depth_other_ppm": g_other.mean * 1e6,
            "difference_sigma": diff_sigma,
        }
    )
    alternative = sp.edge_alternative_depth_fraction * g_other.mean
    probability = gaussian_probability(alternative, sigma, 3.0)
    blocks = {
        "proximity": proximity,
        "comparison": rule_block(
            "edge-event depth change", alternative * 1e6, "ppm", "gaussian-1", probability
        ),
    }
    passed = abs(diff_sigma) < 3.0
    message = (
        f"{int(near.sum())} of {n} events near a segment edge; their depth differs from the "
        f"others by {diff_sigma:.1f} sigma"
    )
    return TestResult(
        name,
        TestStatus.PASS if passed else TestStatus.FAIL,
        severity,
        message,
        sensitivity=blocks,
        **common,
    )


# --- sinusoid (WP3) -----------------------------------------------------------------------


def _beta(residuals: np.ndarray, time: np.ndarray, bin_days: float) -> float:
    """The red-noise factor of the residuals at the time scale ``bin_days`` (the binned scatter
    over the white expectation; at least 1)."""
    if residuals.size < 10 or not bin_days > 0:
        return 1.0
    bins = np.floor((time - time.min()) / bin_days).astype(int)
    counts = np.bincount(bins)
    sums = np.bincount(bins, weights=residuals)
    full = counts >= max(2, int(np.median(counts[counts > 0])) // 2)
    if full.sum() < 3:
        return 1.0
    means = sums[full] / counts[full]
    expected = np.std(residuals) / math.sqrt(float(np.mean(counts[full])))
    if not expected > 0:
        return 1.0
    return max(1.0, float(np.std(means) / expected))


def _sinusoid_fit(time, flux, err, sector, period):
    """Weighted least squares: one offset per sector plus a cos and a sin at ``period``.
    Returns (a, b, cov_ab, residuals)."""
    sectors = np.unique(sector)
    phase = 2.0 * math.pi * time / period
    columns = [(sector == s).astype(float) for s in sectors]
    columns += [np.cos(phase), np.sin(phase)]
    x = np.column_stack(columns)
    w = 1.0 / np.square(err)
    xtw = x.T * w
    cov = np.linalg.inv(xtw @ x)
    coef = cov @ (xtw @ flux)
    residuals = flux - x @ coef
    return float(coef[-2]), float(coef[-1]), cov[-2:, -2:], residuals


def check_sinusoid(
    raw: LightCurveData, candidate: Candidate, sp: StrongerParams, seed: int
) -> TestResult:
    """Warning when the undetrended flux, with the transits masked, holds a sinusoid at P/2, P
    or 2P with amplitude significance above ``sinusoid_min_significance`` and semi-amplitude at
    least ``sinusoid_min_amplitude_ratio`` of the depth (Kunimoto et al. 2025, III.3; the
    amplitude floor and the mask are Refute adaptations). Only for P below
    ``sinusoid_max_period_days``: beyond it the test is INCONCLUSIVE (outside its domain). Never
    fatal in v0.5: a box not detected after subtracting the sinusoid is a non-detection, not
    evidence that the variability explains the signal; that box depth is reported."""
    name, severity = "sinusoid", Severity.WARNING
    thresholds = {
        "min_significance": sp.sinusoid_min_significance,
        "max_period_days": sp.sinusoid_max_period_days,
        "min_amplitude_ratio": sp.sinusoid_min_amplitude_ratio,
        "mask_durations": sp.sinusoid_mask_durations,
    }
    if candidate.period >= sp.sinusoid_max_period_days:
        limit = sp.sinusoid_max_period_days
        why = f"period {candidate.period:.2f} d is outside the test's domain (< {limit} d)"
        return _inconclusive(name, severity, why)
    good = np.isfinite(raw.flux) & np.isfinite(raw.flux_err) & (raw.flux_err > 0)
    lc = raw.select(good)
    flux = lc.flux.copy()
    err = lc.flux_err.copy()
    for s in np.unique(lc.sector):
        sel = lc.sector == s
        med = float(np.median(flux[sel]))
        flux[sel] /= med
        err[sel] /= med
    half = candidate.duration / 2.0 + sp.sinusoid_mask_durations * candidate.duration
    dt = np.abs(
        np.mod(lc.time - candidate.t0 + 0.5 * candidate.period, candidate.period)
        - 0.5 * candidate.period
    )
    keep = dt > half
    if keep.sum() < 100:
        return _inconclusive(name, severity, "too few out-of-transit cadences for the fit")
    t, f, e, sec = lc.time[keep], flux[keep], err[keep], lc.sector[keep]
    depth = candidate.depth
    alt = depth  # the alternative: semi-amplitude equal to the depth
    rows = {}
    probabilities = []
    for label, factor in (("P/2", 0.5), ("P", 1.0), ("2P", 2.0)):
        period = candidate.period * factor
        a, b, cov, residuals = _sinusoid_fit(t, f, e, sec, period)
        beta = _beta(residuals, t, candidate.duration)
        cov = cov * beta**2
        amp = math.hypot(a, b)
        var = (
            (a * a * cov[0, 0] + b * b * cov[1, 1] + 2 * a * b * cov[0, 1]) / amp**2
            if amp > 0
            else float(cov[0, 0])
        )
        sigma = math.sqrt(max(var, 0.0))
        significance = amp / sigma if sigma > 0 else 0.0
        rows[label] = {
            "semi_amplitude_ppm": amp * 1e6,
            "semi_amplitude_err_ppm": sigma * 1e6,
            "significance": significance,
            "beta": beta,
        }
        probabilities.append(_sinusoid_power(cov, alt, depth, sp, seed + int(factor * 4)))
    worst = int(np.argmin(probabilities))
    block = rule_block(
        "sinusoid semi-amplitude", depth * 1e6, "ppm", "compound-sim-1", probabilities[worst]
    )
    block["worst_period"] = ("P/2", "P", "2P")[worst]
    flagged = [
        label
        for label, row in rows.items()
        if row["significance"] > sp.sinusoid_min_significance
        and row["semi_amplitude_ppm"] / 1e6 >= sp.sinusoid_min_amplitude_ratio * depth
    ]
    metrics = {"fits": rows, "n_cadences": int(keep.sum())}
    if flagged:
        metrics["box_depth_after_sinusoid_ppm"] = (
            _box_after(lc.time, flux, candidate, flagged[0]) * 1e6
        )
    status = TestStatus.FAIL if flagged else TestStatus.PASS
    message = (
        f"significant sinusoid at {', '.join(flagged)}: possible stellar variability"
        if flagged
        else "no significant sinusoid at P/2, P or 2P"
    )
    return TestResult(
        name,
        status,
        severity,
        message,
        metrics=metrics,
        thresholds=thresholds,
        coverage=int(keep.sum()),
        coverage_unit="out-of-transit cadences",
        sensitivity={"main": block},
    )


def _sinusoid_power(
    cov: np.ndarray, alternative: float, depth: float, sp: StrongerParams, seed: int
) -> float:
    """The probability that the test's own rule rejects a sinusoid of semi-amplitude
    ``alternative``: the (cos, sin) coefficients drawn jointly with their full covariance, the
    amplitude and its uncertainty recomputed in each draw as the test computes them, at the
    worst of eight phases of the alternative (Codex's review of round 2)."""
    try:
        chol = np.linalg.cholesky(cov)
    except np.linalg.LinAlgError:
        return 0.0
    probabilities = []
    for k in range(8):
        angle = 2.0 * math.pi * k / 8.0
        truth = alternative * np.array([math.cos(angle), math.sin(angle)])

        def draw(rng, n, truth=truth):
            return truth + rng.standard_normal((n, 2)) @ chol.T

        def reject(ab):
            a, b = ab[:, 0], ab[:, 1]
            amp = np.hypot(a, b)
            with np.errstate(divide="ignore", invalid="ignore"):
                var = (a * a * cov[0, 0] + b * b * cov[1, 1] + 2 * a * b * cov[0, 1]) / amp**2
                sig = np.where(var > 0, amp / np.sqrt(np.abs(var)), 0.0)
            return (sig > sp.sinusoid_min_significance) & (
                amp >= sp.sinusoid_min_amplitude_ratio * depth
            )

        probabilities.append(simulated_probability(draw, reject, seed + k))
    return min(probabilities)


def _box_after(time: np.ndarray, flux: np.ndarray, candidate: Candidate, label: str) -> float:
    """The box depth at the candidate's ephemeris after subtracting the sinusoid at ``label``
    fitted on all the data (reported only; never a decision)."""
    factor = {"P/2": 0.5, "P": 1.0, "2P": 2.0}[label]
    phase = 2.0 * math.pi * time / (candidate.period * factor)
    x = np.column_stack([np.ones_like(time), np.cos(phase), np.sin(phase)])
    coef, *_ = np.linalg.lstsq(x, flux, rcond=None)
    clean = flux - x[:, 1:] @ coef[1:]
    dt = np.abs(
        np.mod(time - candidate.t0 + 0.5 * candidate.period, candidate.period)
        - 0.5 * candidate.period
    )
    inside = dt <= candidate.duration / 2.0
    if not inside.any() or inside.all():
        return float("nan")
    return float(np.mean(clean[~inside]) - np.mean(clean[inside]))


# --- duty_cycle (WP3) ---------------------------------------------------------------------


def check_duty_cycle(candidate: Candidate, sp: StrongerParams) -> TestResult:
    """Fatal when duration over period exceeds ``max_duty_cycle`` (Kunimoto et al. 2025, III.4):
    a geometry no transit has. Category ``deterministic-bound``."""
    q = candidate.duration / candidate.period
    passed = q <= sp.max_duty_cycle
    return TestResult(
        "duty_cycle",
        TestStatus.PASS if passed else TestStatus.FAIL,
        Severity.FATAL,
        f"duration over period {q:.3f} ({'<=' if passed else '>'} {sp.max_duty_cycle})",
        metrics={"duty_cycle": q},
        thresholds={"max_duty_cycle": sp.max_duty_cycle},
        coverage=1,
        coverage_unit="candidate duration",
        sensitivity={
            "main": category_block(
                "deterministic-bound", "duration over period against a fixed bound"
            )
        },
    )
