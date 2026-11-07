"""The corrected battery, discovery version 3 (v0.5.1; docs/plans/v0.5.1-acceptance.md).

The v0.5 tests of ``battery_v5`` are not changed: a claim with discovery version 2 runs exactly
them. A version-3 claim runs these versions where they exist.

- ``check_sinusoid`` (WP3 (b), #203): the sinusoid test per harmonic (P/2, P, 2P), each a
  sub-check applied only inside its declared domain (period below
  ``v051.sinusoid_harmonic_max_period_days``), the star's other variability modelled by
  up to ``sinusoid_extra_frequencies`` sinusoids found by iterative prewhitening (amplitude
  signal-to-noise above ``sinusoid_extra_min_snr``, frequencies outside ``1 / T_span`` of every
  tested harmonic). The rejection region and the alternative are v0.5's.
"""

from __future__ import annotations

import math

import numpy as np

from refute.core.sensitivity import not_applicable_block, rule_block
from refute.core.verdict import Severity, TestResult, TestStatus
from refute.packs.tess.battery_v5 import _beta, _box_after, _inconclusive, _sinusoid_power
from refute.packs.tess.params import StrongerParams, V051Params
from refute.packs.tess.types import Candidate, LightCurveData

HARMONICS = (("P/2", 0.5), ("P", 1.0), ("2P", 2.0))
OUTSIDE_DOMAIN = "outside_domain"
# the extra frequencies are searched between 2 / T_span and 10 per day (periods down to 0.1 d)
EXTRA_MAX_FREQUENCY = 10.0


def _design(time, sector, periods):
    """Per-sector offsets, then a cos and a sin at each period, in that order."""
    columns = [(sector == s).astype(float) for s in np.unique(sector)]
    for period in periods:
        phase = 2.0 * math.pi * time / period
        columns += [np.cos(phase), np.sin(phase)]
    return np.column_stack(columns)


def _wls(x, flux, err):
    """Weighted least squares; ``np.linalg.LinAlgError`` when the design is singular."""
    w = 1.0 / np.square(err)
    xtw = x.T * w
    normal = xtw @ x
    if np.linalg.cond(normal) > 1e12:
        raise np.linalg.LinAlgError("singular design")
    cov = np.linalg.inv(normal)
    coef = cov @ (xtw @ flux)
    return coef, cov, flux - x @ coef


def _ls_peak(time, resid, err, f_min, f_max, excluded, width):
    """The strongest Lomb-Scargle frequency in [f_min, f_max] outside ``excluded`` +- ``width``,
    with its least-squares amplitude and amplitude signal-to-noise (amplitude over the mean
    amplitude spectrum level, as in prewhitening practice)."""
    from astropy.timeseries import LombScargle

    span = float(time.max() - time.min())
    step = 1.0 / (5.0 * span)
    freqs = np.arange(f_min, f_max, step)
    if freqs.size < 10:
        return None
    keep = np.ones(freqs.size, dtype=bool)
    for f in excluded:
        keep &= np.abs(freqs - f) > width
    if not keep.any():
        return None
    power = LombScargle(time, resid, err).power(freqs, normalization="psd")
    amp_spec = np.sqrt(np.clip(power, 0.0, None))
    k = int(np.argmax(np.where(keep, amp_spec, -np.inf)))
    noise = float(np.mean(amp_spec[keep]))
    if not noise > 0:
        return None
    return float(freqs[k]), float(amp_spec[k] / noise)


def check_sinusoid(
    raw: LightCurveData,
    candidate: Candidate,
    sp: StrongerParams,
    cp: V051Params,
    seed: int,
) -> TestResult:
    """Warning when the undetrended flux, transits masked, holds a sinusoid at an applicable
    harmonic (P/2, P, 2P below the harmonic domain) with amplitude significance above
    ``sinusoid_min_significance`` and semi-amplitude at least ``sinusoid_min_amplitude_ratio``
    of the depth, in a joint model with the star's other variability. Never fatal."""
    name, severity = "sinusoid", Severity.WARNING
    thresholds = {
        "min_significance": sp.sinusoid_min_significance,
        "min_amplitude_ratio": sp.sinusoid_min_amplitude_ratio,
        "mask_durations": sp.sinusoid_mask_durations,
        "harmonic_max_period_days": cp.sinusoid_harmonic_max_period_days,
        "extra_frequencies": cp.sinusoid_extra_frequencies,
        "extra_min_snr": cp.sinusoid_extra_min_snr,
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
    # the star's other variability: iterative prewhitening outside the tested harmonics
    extra: list[float] = []
    extra_rows = []
    for _ in range(cp.sinusoid_extra_frequencies):
        x = _design(t, sec, [1.0 / q for q in tested + extra])
        _, _, resid = _wls(x, f, e)
        # a new extra frequency stays outside 1 / T_span of the tested harmonics and of the
        # extra frequencies already chosen (no redundant column; Codex's review of round 2)
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
    for j, (label, _) in enumerate(applicable):
        a, b = float(coef[n_off + 2 * j]), float(coef[n_off + 2 * j + 1])
        cov = cov_all[n_off + 2 * j : n_off + 2 * j + 2, n_off + 2 * j : n_off + 2 * j + 2]
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
        }
        probability = _sinusoid_power(cov, depth, depth, sp, seed + j)
        blocks[label] = rule_block(
            f"sinusoid semi-amplitude at {label}", depth * 1e6, "ppm", "compound-sim-1", probability
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
    }
    if flagged:
        metrics["box_depth_after_sinusoid_ppm"] = (
            _box_after(lc.time, flux, candidate, flagged[0]) * 1e6
        )
    tested_labels = ", ".join(label for label, _ in applicable)
    message = (
        f"significant sinusoid at {', '.join(flagged)}: possible stellar variability"
        if flagged
        else f"no sinusoid above the thresholds at {tested_labels}"
    )
    return TestResult(
        name,
        TestStatus.FAIL if flagged else TestStatus.PASS,
        severity,
        message,
        metrics=metrics,
        thresholds=thresholds,
        coverage=int(keep.sum()),
        coverage_unit="out-of-transit cadences",
        sensitivity=blocks,
    )


# --- odd_even with an efficient estimator (WP3 (d)) ----------------------------------------


def _unit_trapezoid(duration: float, ingress_fraction: float):
    half = duration / 2.0
    ramp = max(ingress_fraction * duration, 1e-6)

    def shape(dt):
        return np.clip((half - np.abs(dt)) / ramp, 0.0, 1.0)

    return shape


def _fit_shape_status(time, flux, candidate):
    """The trapezoid fit of ``_fit_shape`` (the same procedure, bounds and two-start selection:
    the lower-cost start), returning also the selected fit's success flag and whether any of its
    parameters is at a bound (``least_squares``'s ``active_mask``)."""
    from scipy.optimize import least_squares

    from refute.packs.tess import synthetic as syn

    p, t0, dur0 = candidate.period, candidate.t0, candidate.duration
    d0 = max(candidate.depth, 1e-6)
    dt = np.mod(time - t0 + 0.5 * p, p) - 0.5 * p
    near = np.abs(dt) <= 1.5 * dur0
    tn, yn = time[near], flux[near]

    def resid(x):
        depth, dur, f, shift = x
        return (1.0 - syn.trapezoid(tn, p, t0 + shift, depth, dur, f)) - yn

    best = None
    for f0 in (0.05, 0.2):
        fit = least_squares(
            resid,
            [d0, dur0, f0, 0.0],
            bounds=([0.0, 0.3 * dur0, 0.01, -0.3 * dur0], [10 * d0, 3.0 * dur0, 0.5, 0.3 * dur0]),
            x_scale=[d0, 0.1 * dur0, 0.05, 0.05 * dur0],
            max_nfev=300,
        )
        if best is None or fit.cost < best.cost:
            best = fit
    params = tuple(float(v) for v in best.x)
    return params, bool(best.success), bool(np.any(best.active_mask != 0))


def _fit_shape(time, flux, candidate):
    """The trapezoid fitted once on all events (depth, total duration, ingress fraction, epoch
    shift free) on the flattened curve; returns (depth, duration, ingress_fraction, shift)."""
    return _fit_shape_status(time, flux, candidate)[0]


def _inconclusive_odd_even(message, cls, thresholds, **metrics):
    return TestResult(
        "odd_even",
        TestStatus.INCONCLUSIVE,
        Severity.FATAL,
        message,
        metrics={**metrics, "inconclusive_class": cls},
        thresholds=thresholds,
    )


def check_odd_even(flat, candidate, gp, sp, cadence_days, exclude_phase_half, seed):
    """WP3 (d), version 3: the odd/even depth difference with each group's amplitude of the
    fitted trapezoid (a matched filter against the flattened baseline), the errors from A0 on
    the same estimator at pseudo-event windows; v0.4's rejection region (``max_sigma``) and
    #185's alternative (the full depth)."""
    from refute.core.sensitivity import gaussian_probability
    from refute.packs.tess import a0
    from refute.packs.tess.events import event_epochs

    params, ev = gp.odd_even, gp.events
    thresholds = {"max_sigma": params.max_sigma, "min_transits_each": params.min_transits_each}
    time, flux, sector = flat.time, flat.flux, flat.sector
    _, duration, ingress, shift = _fit_shape(time, flux, candidate)
    shape = _unit_trapezoid(duration, ingress)
    t0 = candidate.t0 + shift
    period = candidate.period
    expected_in = duration / cadence_days
    measure, measure_info = a0.matched_measure(
        time, flux, flat.flux_err, shape, duration / 2.0, expected_in, ev.min_coverage
    )
    windows = a0.pseudo_windows(
        time,
        sector,
        period,
        t0,
        candidate.duration,
        ev.baseline_outer_durations,
        ev.min_coverage,
        measure,
        exclude_phase_half=exclude_phase_half,
    )
    rows, metas, cache = [], [], {}
    for epoch in event_epochs(time, period, t0, 0.0):
        centre = t0 + epoch * period
        got = measure_info(centre)
        if got is None:
            continue
        amp, cov, info = got
        meta = a0.event_meta(time, sector, centre, cov, ev.min_coverage)
        if meta is None:
            continue
        key = (meta.sector, meta.stratum)
        if key not in cache:
            cache[key] = a0.stratum_error(windows, *key)[0]
        emp = cache[key]
        if emp is None:
            continue
        model = 1.0 / math.sqrt(info)  # the weighted information of the same estimator
        rows.append((int(epoch), amp, max(model, emp)))
        metas.append(meta)
    odd = [i for i, r in enumerate(rows) if r[0] % 2 != 0]
    even = [i for i, r in enumerate(rows) if r[0] % 2 == 0]
    note = " (phase-0.5 windows excluded: a secondary detected)" if exclude_phase_half else ""
    if len(odd) < params.min_transits_each or len(even) < params.min_transits_each:
        return _inconclusive_odd_even(
            f"not enough measured transits: {len(even)} even, {len(odd)} odd{note}",
            "not_enough_data",
            thresholds,
            n_odd=len(odd),
            n_even=len(even),
        )

    def group(idx):
        w = np.array([1.0 / rows[i][2] ** 2 for i in idx])
        w = w / np.sum(w)
        return float(np.sum(w * np.array([rows[i][1] for i in idx]))), w

    m_odd, w_odd = group(odd)
    m_even, w_even = group(even)
    weights = np.zeros(len(rows))
    weights[odd] = w_odd
    weights[even] = -w_even
    h = a0.half_width(candidate.duration, ev.baseline_outer_durations)
    pooled = {s: a0.shortcut(windows, s, seed + s) for s in {m.sector for m in metas}}
    sigmas = [r[2] for r in rows]
    var = a0.group_variance(weights, sigmas, metas, windows, h, pooled)
    if var is None:
        return _inconclusive_odd_even(
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
        "estimator": "matched trapezoid amplitude (WP3 (d)); errors from A0",
        "fitted_duration_days": duration,
        "fitted_ingress_fraction": ingress,
        "phase_half_windows_excluded": bool(exclude_phase_half),
    }
    status = TestStatus.FAIL if zscore >= params.max_sigma else TestStatus.PASS
    return TestResult(
        "odd_even",
        status,
        Severity.FATAL,
        f"odd/even depths differ by {zscore:.1f} sigma ({len(odd)} odd, {len(even)} even)",
        metrics=metrics,
        thresholds=thresholds,
        coverage=len(rows),
        coverage_unit="measured transits",
        sensitivity={"main": block},
    )


# --- duration_excess, the EB route's diagnostic (plan amendments 4 and 9) --------------------

# the 20 phase placements of the fitted trapezoid (the band around phase 0.5 left out)
DURATION_PHASES = (*np.linspace(0.20, 0.40, 10), *np.linspace(0.60, 0.80, 10))
DURATION_MIN_VALID = 10
DURATION_MAX_SIGMA = 3.0
TMAX_DRAWS = 2000
# "the battery's minimum number of events": the minimum number of transits the search requires of
# a candidate (refute.packs.tess.search, at least 2 per period); the plan has no other
MIN_EVENTS = 2


def t_max(period: float, k: float, radius: float, mass: float) -> float:
    """The circular-orbit maximum duration of a central transit (b = 0):
    ``(P / pi) asin(min(1, (1 + k) / (a / R*)))``, ``a / R*`` by Kepler's third law from the
    star's mass and radius (solar units)."""
    from refute.packs.tess.calib05.c1 import a_over_rstar

    a = a_over_rstar(period) * mass ** (1.0 / 3.0) / radius
    return period / math.pi * math.asin(min(1.0, (1.0 + k) / a))


def _positive_normal(rng: np.random.Generator, mean: float, sd: float, n: int) -> np.ndarray:
    """``n`` draws of a Gaussian truncated at positive values (non-positive draws redrawn)."""
    out = rng.normal(mean, sd, n)
    for _ in range(1000):
        bad = out <= 0
        if not bad.any():
            return out
        out[bad] = rng.normal(mean, sd, int(bad.sum()))
    raise ValueError("the Gaussian has almost no mass at positive values")


def _covered_events(time, period, t0, duration, cadence_days, min_coverage) -> int:
    """How many events at this ephemeris keep at least ``min_coverage`` of a full event's
    in-event cadences (counted over all sectors)."""
    full = duration / cadence_days
    epochs = np.unique(np.round((time - t0) / period))
    n = 0
    for e in epochs:
        inside = np.count_nonzero(np.abs(time - (t0 + e * period)) <= duration / 2.0)
        n += inside / full >= min_coverage
    return int(n)


def _inconclusive_duration(message, cls, thresholds, **metrics):
    return TestResult(
        "duration_excess",
        TestStatus.INCONCLUSIVE,
        Severity.WARNING,
        message,
        metrics={**metrics, "inconclusive_class": cls},
        thresholds=thresholds,
    )


def check_duration_excess(flat, candidate, star, gp, cadence_days, seed):
    """``duration_excess`` (the acceptance section "The eclipsing-binary route", as decided under
    amendment 9): a diagnostic, outside the verdict. ``T`` is the total duration of the trapezoid
    ``_fit_shape`` fits; ``sigma_T`` a phase-placement estimate: the fitted trapezoid removed and
    injected again at the 20 ``DURATION_PHASES``, each recovered by the same procedure, the sample
    standard deviation of the valid placements' durations (dependent placements on one curve: D.1
    measures whether it is calibrated). A warning when ``T - T_max(P) >= 3 sqrt(sigma_T^2 +
    sigma_Tmax^2)``; its sensitivity the Gaussian closed form with the alternative
    ``T_max(2P) - T_max(P)``. ``sigma_Tmax`` from ``TMAX_DRAWS`` seeded draws of the TIC radius
    and mass (independent Gaussians truncated at positive values) and of ``k`` (the depth with its
    error ``candidate.depth_err``, the error the gate reports)."""
    from dataclasses import replace

    from refute.core.sensitivity import gaussian_probability
    from refute.packs.tess import synthetic as syn

    ev = gp.events
    thresholds = {
        "max_sigma": DURATION_MAX_SIGMA,
        "placements": len(DURATION_PHASES),
        "min_valid_placements": DURATION_MIN_VALID,
        "min_events": MIN_EVENTS,
        "min_coverage": ev.min_coverage,
        "tmax_draws": TMAX_DRAWS,
    }
    values = (
        getattr(star, "radius_rsun", None),
        getattr(star, "radius_err_rsun", None),
        getattr(star, "mass_msun", None),
        getattr(star, "mass_err_msun", None),
    )
    if any(v is None or not math.isfinite(v) or v <= 0 for v in values):
        return _inconclusive_duration(
            "no TIC radius, mass or their errors: the circular-orbit maximum cannot be computed",
            "missing_input",
            thresholds,
        )
    radius, radius_err, mass, mass_err = (float(v) for v in values)
    time, flux = flat.time, flat.flux
    period = candidate.period
    (depth, duration, ingress, shift), fit_ok, fit_bound = _fit_shape_status(time, flux, candidate)
    t0 = candidate.t0 + shift
    clean = flux + syn.trapezoid(time, period, t0, depth, duration, ingress)
    recovered, rejected = [], {"fit failed": 0, "parameter at a bound": 0, "too few events": 0}
    for phi in DURATION_PHASES:
        tj = t0 + float(phi) * period
        yj = clean - syn.trapezoid(time, period, tj, depth, duration, ingress)
        start = replace(candidate, t0=tj, depth=depth, duration=duration)
        (_, dur_j, _, _), ok, bound = _fit_shape_status(time, yj, start)
        events = _covered_events(time, period, tj, duration, cadence_days, ev.min_coverage)
        if not ok:
            rejected["fit failed"] += 1
        elif bound:
            rejected["parameter at a bound"] += 1
        elif events < MIN_EVENTS:
            rejected["too few events"] += 1
        else:
            recovered.append(dur_j)
    placements = {"valid": len(recovered), "rejected": rejected}
    common = {
        "duration_hours": duration * 24.0,
        "fit_success": fit_ok,
        "fit_parameter_at_bound": fit_bound,
        "placements": placements,
        "sigma_T_kind": "phase-placement estimate (dependent placements; calibration by D.1)",
    }
    if len(recovered) < DURATION_MIN_VALID:
        return _inconclusive_duration(
            f"only {len(recovered)} valid phase placements (at least {DURATION_MIN_VALID})",
            "not_enough_data",
            thresholds,
            **common,
        )
    sigma_t = float(np.std(recovered, ddof=1))
    k = math.sqrt(max(depth, 0.0))
    tmax_p = t_max(period, k, radius, mass)
    tmax_2p = t_max(2.0 * period, k, radius, mass)
    rng = np.random.default_rng(seed)
    radii = _positive_normal(rng, radius, radius_err, TMAX_DRAWS)
    masses = _positive_normal(rng, mass, mass_err, TMAX_DRAWS)
    depth_err = candidate.depth_err
    if depth_err is not None and math.isfinite(depth_err) and depth_err > 0 and depth > 0:
        ks = np.sqrt(_positive_normal(rng, depth, float(depth_err), TMAX_DRAWS))
    else:
        ks = np.full(TMAX_DRAWS, k)
    draws = [t_max(period, kk, r, m) for kk, r, m in zip(ks, radii, masses, strict=True)]
    sigma_tmax = float(np.std(draws, ddof=1))
    sigma = math.hypot(sigma_t, sigma_tmax)
    metrics = {
        **common,
        "sigma_T_hours": sigma_t * 24.0,
        "T_max_P_hours": tmax_p * 24.0,
        "T_max_2P_hours": tmax_2p * 24.0,
        "sigma_Tmax_hours": sigma_tmax * 24.0,
    }
    if not (math.isfinite(sigma) and sigma > 0):
        return _inconclusive_duration(
            "no finite positive error for the duration excess",
            "insufficient_sensitivity",
            thresholds,
            **metrics,
        )
    excess = (duration - tmax_p) / sigma
    metrics["excess_sigma"] = excess
    alternative = tmax_2p - tmax_p
    block = rule_block(
        "duration above the circular-orbit maximum",
        alternative * 24.0,
        "h",
        "gaussian-1",
        gaussian_probability(alternative, sigma, DURATION_MAX_SIGMA),
    )
    if excess >= DURATION_MAX_SIGMA:
        status = TestStatus.FAIL
        message = (
            f"duration {duration * 24.0:.2f} h is {excess:.1f} sigma above the circular-orbit "
            "maximum for the TIC star; an eccentric orbit, a wrong stellar radius or a binary at "
            "twice the period can do this (a diagnostic: it does not enter the verdict)"
        )
    else:
        status = TestStatus.PASS
        message = (
            f"duration {duration * 24.0:.2f} h is {excess:.1f} sigma from the circular-orbit "
            "maximum for the TIC star"
        )
    return TestResult(
        "duration_excess",
        status,
        Severity.WARNING,
        message,
        metrics=metrics,
        thresholds=thresholds,
        coverage=len(recovered),
        coverage_unit="valid phase placements",
        sensitivity={"main": block},
    )
