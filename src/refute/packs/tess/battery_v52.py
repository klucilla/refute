"""The tests of battery version 4 (v0.5.2; docs/plans/v0.5.2-stage2-design.md). Versions 3 and
earlier never import this module.

- ``choose_sectors`` (section 2): at most four sectors for the event-based tests that use A0's
  errors, chosen from the cadences and the ephemeris alone, before any event is measured.
- ``check_odd_even`` (guideline 2): the odd/even difference of the box depths, with A0's errors.
- ``check_sinusoid`` (section 5): a flagged harmonic FAILs only on positive evidence that the
  variability removes at least half of the dip; a flagged harmonic without it is INCONCLUSIVE.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from refute.core.sensitivity import gaussian_probability, not_applicable_block, rule_block
from refute.core.verdict import Severity, TestResult, TestStatus
from refute.packs.tess import a0
from refute.packs.tess.battery_v5 import _beta, _inconclusive, _sinusoid_power
from refute.packs.tess.battery_v51 import (
    EXTRA_MAX_FREQUENCY,
    HARMONICS,
    OUTSIDE_DOMAIN,
    _design,
    _ls_peak,
    _wls,
)

GRID_SECTORS = (2, 3, 4)
MAX_SELECTED_SECTORS = 4
MAX_ORIGINAL_SECTORS = 20
AMBIGUOUS_SINUSOID = "ambiguous_sinusoid_with_transit"
ATTENUATION_FRACTION = 0.5
ATTENUATION_SIGMAS = 3.0


@dataclass(frozen=True)
class SectorChoice:
    """The sectors chosen for the A0-dependent tests, with the reason when none may be used."""

    original: tuple[int, ...]
    events: dict[int, int]
    cadences: dict[int, int]
    chosen: tuple[int, ...]
    refused: str | None


def _eligible_events(time: np.ndarray, candidate, ev, cadence_days: float) -> tuple[int, int]:
    """(events with enough in-event and baseline cadences on both sides, their window cadences)."""
    duration, period, t0 = candidate.duration, candidate.period, candidate.t0
    half = duration / 2.0
    inner = half + ev.baseline_gap_durations * duration
    outer = half + ev.baseline_outer_durations * duration
    need_in = ev.min_coverage * duration / cadence_days
    need_band = ev.min_coverage * (outer - inner) / cadence_days
    events, cadences = 0, 0
    first = int(math.floor((time.min() - outer - t0) / period))
    last = int(math.ceil((time.max() + outer - t0) / period))
    for epoch in range(first, last + 1):
        centre = t0 + epoch * period
        n_in = int(np.count_nonzero(np.abs(time - centre) <= half))
        before = int(np.count_nonzero((time >= centre - outer) & (time < centre - inner)))
        after = int(np.count_nonzero((time > centre + inner) & (time <= centre + outer)))
        if n_in >= need_in and before >= need_band and after >= need_band:
            events += 1
            cadences += n_in + before + after
    return events, cadences


def choose_sectors(time, sector, candidate, ev, cadence_days, selector_certified) -> SectorChoice:
    """Section 2's rule: the four eligible sectors with the most eligible events, ties by the
    cadences in those windows, then by the lower sector number. Flux-blind, conditional on the
    ephemeris and the cadences. ``refused`` holds why the A0-dependent tests may not run."""
    original = tuple(int(s) for s in np.unique(sector))
    events, cadences = {}, {}
    for s in original:
        events[s], cadences[s] = _eligible_events(time[sector == s], candidate, ev, cadence_days)
    eligible = [s for s in original if events[s] > 0]
    order = sorted(eligible, key=lambda s: (-events[s], -cadences[s], s))
    chosen = tuple(sorted(order[:MAX_SELECTED_SECTORS]))
    refused = None
    if len(original) > MAX_ORIGINAL_SECTORS:
        refused = f"{len(original)} sectors: above the supported {MAX_ORIGINAL_SECTORS}"
    elif len(original) > MAX_SELECTED_SECTORS and not selector_certified:
        refused = f"{len(original)} sectors: the sector selection is not certified"
    return SectorChoice(original, events, cadences, chosen, refused)


def odd_even_inconclusive(message, cls, thresholds, **metrics):
    return TestResult(
        "odd_even",
        TestStatus.INCONCLUSIVE,
        Severity.FATAL,
        message,
        metrics={**metrics, "inconclusive_class": cls},
        thresholds=thresholds,
    )


def check_odd_even(flat, measured, windows, candidate, gp, sp, cadence_days, exclude, seed):
    """The odd/even difference of the box depths of the events A0 measured, each group the
    inverse-variance mean, the error by A0's group rule; v0.4's rejection region and #185's
    alternative."""
    params, ev = gp.odd_even, gp.events
    thresholds = {"max_sigma": params.max_sigma, "min_transits_each": params.min_transits_each}
    expected_in = candidate.duration / cadence_days
    metas = [
        a0.event_meta(flat.time, flat.sector, ctr, n / expected_in, ev.min_coverage)
        for ctr, n in zip(measured.centers.tolist(), measured.n_in.tolist(), strict=True)
    ]
    odd = [i for i in range(len(measured)) if int(measured.epochs[i]) % 2 != 0]
    even = [i for i in range(len(measured)) if int(measured.epochs[i]) % 2 == 0]
    note = " (phase-0.5 windows excluded: a secondary detected)" if exclude else ""
    if len(odd) < params.min_transits_each or len(even) < params.min_transits_each:
        return odd_even_inconclusive(
            f"not enough measured transits: {len(even)} even, {len(odd)} odd{note}",
            "not_enough_data",
            thresholds,
            n_odd=len(odd),
            n_even=len(even),
        )
    errors = measured.errors

    def group(index):
        w = np.array([1.0 / float(errors[i]) ** 2 for i in index])
        w = w / np.sum(w)
        return float(np.sum(w * measured.depths[index])), w

    m_odd, w_odd = group(odd)
    m_even, w_even = group(even)
    weights = np.zeros(len(measured))
    weights[odd] = w_odd
    weights[even] = -w_even
    h = a0.half_width(candidate.duration, ev.baseline_outer_durations)
    pooled = {s: a0.shortcut(windows, s, seed + s) for s in {m.sector for m in metas}}
    sigmas = [float(e) for e in errors]
    var = a0.group_variance(weights, sigmas, metas, windows, h, pooled)
    if var is None:
        return odd_even_inconclusive(
            f"no calibrated error for the odd/even difference{note}",
            "insufficient_sensitivity",
            thresholds,
        )
    sigma = math.sqrt(var)
    diff = m_odd - m_even
    zscore = abs(diff) / sigma
    alternative = sp.odd_even_alternative_depth_fraction * candidate.depth
    block = rule_block(
        "odd/even depth difference",
        alternative * 1e6,
        "ppm",
        "gaussian-1",
        gaussian_probability(alternative, sigma, params.max_sigma),
    )
    var_odd = a0.group_variance(
        w_odd, [sigmas[i] for i in odd], [metas[i] for i in odd], windows, h, pooled
    )
    var_even = a0.group_variance(
        w_even, [sigmas[i] for i in even], [metas[i] for i in even], windows, h, pooled
    )
    metrics = {
        "depth_odd_ppm": m_odd * 1e6,
        "depth_even_ppm": m_even * 1e6,
        "depth_odd_err_ppm": math.sqrt(var_odd) * 1e6 if var_odd else None,
        "depth_even_err_ppm": math.sqrt(var_even) * 1e6 if var_even else None,
        "difference_sigma": zscore,
        "n_odd": len(odd),
        "n_even": len(even),
        "estimator": "box depths of the measured events; errors from A0 (version 4)",
        "phase_half_windows_excluded": bool(exclude),
    }
    status = TestStatus.FAIL if zscore >= params.max_sigma else TestStatus.PASS
    return TestResult(
        "odd_even",
        status,
        Severity.FATAL,
        f"odd/even depths differ by {zscore:.1f} sigma ({len(odd)} odd, {len(even)} even)",
        metrics=metrics,
        thresholds=thresholds,
        coverage=len(measured),
        coverage_unit="measured transits",
        sensitivity={"main": block},
    )


def _coverage_valid(time, candidate, ev, cadence_days) -> bool:
    """Every event with an in-transit cadence reaches ``min_coverage`` in the in-transit and the
    baseline cadences, summed over those events (and there is at least one)."""
    duration, period, t0 = candidate.duration, candidate.period, candidate.t0
    half = duration / 2.0
    inner = half + ev.baseline_gap_durations * duration
    outer = half + ev.baseline_outer_durations * duration
    dt = np.abs(np.mod(time - t0 + 0.5 * period, period) - 0.5 * period)
    inside = dt <= half
    if not inside.any():
        return False
    epochs = np.unique(np.round((time[inside] - t0) / period))
    expected_in = epochs.size * duration / cadence_days
    expected_base = epochs.size * 2.0 * (outer - inner) / cadence_days
    near = np.isin(np.round((time - t0) / period), epochs)
    base = near & (dt > inner) & (dt <= outer)
    return bool(
        np.count_nonzero(inside) >= ev.min_coverage * expected_in
        and np.count_nonzero(base) >= ev.min_coverage * expected_base
    )


def box_after_model(time, flux, err, kept, x_all, x_kept, candidate, beta):
    """``box_after`` and its error ``sigma_r``: the box depth at the ephemeris on the flux minus
    the joint model fitted out of transit, with ``sigma_r^2 = a^T (I - H) Sigma (I - H)^T a``,
    ``H`` fitting the out-of-transit cadences and predicting all of them, ``Sigma`` the white
    errors scaled by ``beta``. Returns (nan, nan) when the box has no in-event or no other
    cadence."""
    dt = np.abs(
        np.mod(time - candidate.t0 + 0.5 * candidate.period, candidate.period)
        - 0.5 * candidate.period
    )
    inside = dt <= candidate.duration / 2.0
    if not inside.any() or inside.all():
        return float("nan"), float("nan")
    a = np.where(inside, -1.0 / np.count_nonzero(inside), 1.0 / np.count_nonzero(~inside))
    w = 1.0 / np.square(err[kept])
    xtw = x_kept.T * w
    cov = np.linalg.inv(xtw @ x_kept)
    coef = cov @ (xtw @ flux[kept])
    v = a.copy()
    v[kept] -= w * (x_kept @ (cov @ (x_all.T @ a)))
    return float(a @ (flux - x_all @ coef)), float(beta * np.sqrt(np.sum(np.square(err * v))))


def check_sinusoid(raw, candidate, sp, cp, ev, cadence_days, fail_allowed, seed):
    """Version 4's sinusoid (section 5). The fit and the flag are version 3's. A flagged harmonic
    FAILs (a warning) only with valid coverage and ``box_after + 3 sigma_r < 0.5 D``; otherwise
    it is INCONCLUSIVE (``ambiguous_sinusoid_with_transit``). With ``fail_allowed`` false, every
    flagged case is INCONCLUSIVE. Not flagged: PASS, under the sensitivity rule of its blocks."""
    name, severity = "sinusoid", Severity.WARNING
    thresholds = {
        "min_significance": sp.sinusoid_min_significance,
        "min_amplitude_ratio": sp.sinusoid_min_amplitude_ratio,
        "mask_durations": sp.sinusoid_mask_durations,
        "harmonic_max_period_days": cp.sinusoid_harmonic_max_period_days,
        "extra_frequencies": cp.sinusoid_extra_frequencies,
        "extra_min_snr": cp.sinusoid_extra_min_snr,
        "attenuation_fraction": ATTENUATION_FRACTION,
        "attenuation_sigmas": ATTENUATION_SIGMAS,
    }
    applicable = [
        (label, factor)
        for label, factor in HARMONICS
        if candidate.period * factor < cp.sinusoid_harmonic_max_period_days
    ]
    if ("P/2", 0.5) not in applicable:
        why = (
            f"period {candidate.period:.2f} d: no harmonic below the domain "
            f"({cp.sinusoid_harmonic_max_period_days} d)"
        )
        return _inconclusive(name, severity, why, inconclusive_class=OUTSIDE_DOMAIN)
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
        why = "too few out-of-transit cadences for the fit"
        return _inconclusive(name, severity, why, inconclusive_class="not_enough_data")
    t, f, e, sec = lc.time[keep], flux[keep], err[keep], lc.sector[keep]
    span = float(t.max() - t.min())
    width = 1.0 / span
    tested = [1.0 / (candidate.period * factor) for _, factor in applicable]
    extra: list[float] = []
    extra_rows = []
    for _ in range(cp.sinusoid_extra_frequencies):
        x = _design(t, sec, [1.0 / q for q in tested + extra])
        _, _, resid = _wls(x, f, e)
        peak = _ls_peak(t, resid, e, 2.0 / span, EXTRA_MAX_FREQUENCY, tested + extra, width)
        if peak is None or peak[1] <= cp.sinusoid_extra_min_snr:
            break
        try:
            _wls(_design(t, sec, [1.0 / q for q in tested + extra + [peak[0]]]), f, e)
        except np.linalg.LinAlgError:
            break
        extra.append(peak[0])
        extra_rows.append({"frequency_per_day": peak[0], "amplitude_snr": peak[1]})
    periods = [1.0 / q for q in tested + extra]
    x = _design(t, sec, periods)
    try:
        coef, cov_all, residuals = _wls(x, f, e)
    except np.linalg.LinAlgError:
        why = "the joint sinusoid model is singular for these data"
        return _inconclusive(name, severity, why, inconclusive_class="not_enough_data")
    beta = _beta(residuals, t, candidate.duration)
    n_off = len(np.unique(sec))
    depth = candidate.depth
    rows: dict[str, dict] = {}
    blocks: dict[str, dict] = {}
    flagged = []
    valid = _coverage_valid(lc.time, candidate, ev, cadence_days)
    can_fail = fail_allowed and valid
    x_all = _design(lc.time, lc.sector, periods)
    box_after, sigma_r = box_after_model(lc.time, flux, err, keep, x_all, x, candidate, beta)
    attenuated = math.isfinite(sigma_r) and box_after + ATTENUATION_SIGMAS * sigma_r < (
        ATTENUATION_FRACTION * depth
    )
    small = (
        float(0.5 * math.erfc(-((ATTENUATION_FRACTION * depth / sigma_r) - 3.0) / math.sqrt(2.0)))
        if math.isfinite(sigma_r) and sigma_r > 0
        else 0.0
    )
    for j, (label, _) in enumerate(applicable):
        a_c, b_c = float(coef[n_off + 2 * j]), float(coef[n_off + 2 * j + 1])
        cov = cov_all[n_off + 2 * j : n_off + 2 * j + 2, n_off + 2 * j : n_off + 2 * j + 2]
        cov = cov * beta**2
        amp = math.hypot(a_c, b_c)
        var = (
            (a_c * a_c * cov[0, 0] + b_c * b_c * cov[1, 1] + 2 * a_c * b_c * cov[0, 1]) / amp**2
            if amp > 0
            else float(cov[0, 0])
        )
        sigma = math.sqrt(max(var, 0.0))
        significance = amp / sigma if sigma > 0 else 0.0
        rows[label] = {
            "semi_amplitude_ppm": amp * 1e6,
            "semi_amplitude_err_ppm": sigma * 1e6,
            "significance": significance,
        }
        probability = _sinusoid_power(cov, depth, depth, sp, seed + j)
        # the decision needs both the flag and the small residual; their joint probability is
        # bounded below without any independence assumption (the Frechet bound)
        blocks[label] = rule_block(
            f"sinusoid explaining the dip at {label}",
            depth * 1e6,
            "ppm",
            "compound-sim-1",
            max(0.0, probability + small - 1.0) if can_fail else 0.0,
        )
        if significance > sp.sinusoid_min_significance and amp >= (
            sp.sinusoid_min_amplitude_ratio * depth
        ):
            flagged.append(label)
    for label, factor in HARMONICS:
        if (label, factor) not in applicable:
            limit = cp.sinusoid_harmonic_max_period_days
            blocks[label] = not_applicable_block(
                f"{label} = {candidate.period * factor:.2f} d is outside the domain (< {limit} d)"
            )
            rows[label] = {"applicable": False}
    metrics = {
        "fits": rows,
        "beta": beta,
        "extra_frequencies": extra_rows,
        "n_cadences": int(keep.sum()),
        "box_depth_after_model_ppm": box_after * 1e6 if math.isfinite(box_after) else None,
        "box_depth_after_model_err_ppm": sigma_r * 1e6 if math.isfinite(sigma_r) else None,
        "probability_residual_small": small,
        "coverage_valid": valid,
        "fail_allowed": fail_allowed,
    }
    common = {
        "metrics": metrics,
        "thresholds": thresholds,
        "coverage": int(keep.sum()),
        "coverage_unit": "out-of-transit cadences",
    }
    if not flagged:
        tested_labels = ", ".join(label for label, _ in applicable)
        return TestResult(
            name,
            TestStatus.PASS,
            severity,
            f"no sinusoid above the thresholds at {tested_labels}",
            sensitivity=blocks,
            **common,
        )
    if can_fail and attenuated:
        return TestResult(
            name,
            TestStatus.FAIL,
            severity,
            f"significant sinusoid at {', '.join(flagged)} removes at least half of the dip",
            sensitivity=blocks,
            **common,
        )
    # the closed set of classes (refute.core.inconclusive) is not extended, so that the tallies of
    # earlier versions keep their bytes; the design's name is the class's detail
    metrics["inconclusive_class"] = "insufficient_sensitivity"
    metrics["inconclusive_detail"] = AMBIGUOUS_SINUSOID
    return TestResult(
        name,
        TestStatus.INCONCLUSIVE,
        severity,
        f"significant sinusoid at {', '.join(flagged)}: it does not establish the dip's cause",
        **common,
    )
