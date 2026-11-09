"""v0.5.1 WP3 (a), discovery version 3: ``aperture_depth`` and ``systematics`` with the error of
the difference measured by A0 on the **difference series** itself
(docs/plans/v0.5.1-acceptance.md, WP3 (a)).

The rejection regions and the alternatives of v0.5 are kept; the v0.4 check functions of
``battery`` are not changed (a version-2 claim runs exactly them).

- ``check_aperture_depth``: the large-minus-core depth difference measured on the series
  ``large / median(large) - core / median(core)``, its error the A0 error of that difference;
  the sensitivity simulation draws the core depth and the difference from their A0 errors and
  their correlation measured at the pseudo-events.
- ``check_systematics``: the SAP sub-check on the series
  ``SAP / median(SAP) - CROWDSAP x PDCSAP / median(PDCSAP)`` per sector, its error the A0 error of
  that series; a sector where SAP and PDCSAP are identical up to a constant factor has no
  corrected flux to compare with, so the sub-check is **not applicable** there (never a PASS,
  never "detectable"); with no sector where it applies, the sub-check is not applicable and the
  test rests on its other sub-checks. The background sub-check is v0.5's with A0's error.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

import numpy as np

from refute.core.sensitivity import (
    category_block,
    not_applicable_block,
    rule_block,
    simulated_probability,
)
from refute.core.verdict import Severity, TestResult, TestStatus
from refute.packs.tess import a0
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.types import Candidate, LightCurveData, PixelData, SectorAux

# Amendment 6 (acceptance, WP3 (a)): SAP is an exact affine function of PDCSAP in a sector (no
# correction applied there) when the largest absolute residual of the standardized least-squares
# fit is at most this (normalized flux)
AFFINE_TOLERANCE = 1e-9
# provisional operational cutoffs (a declared convention, not calibrated): below either, the SAP
# sub-check is not applicable in that sector, class not_enough_data
SAP_MIN_CADENCES = 100
SAP_MIN_PDCSAP_SD = 1e-5
# a per-event error at or below this (normalized flux units, 1e-6 ppm) is rounding, not a
# measurement: the series has no scatter and its error is "not measurable" (acceptance, WP3 (a))
MIN_MEASURABLE_ERROR = 1e-12


@dataclass(frozen=True)
class A0Depth:
    """The A0 group depth of one series: the inverse-variance weighted mean of its per-event
    depths, its error from A0's group rule, and the pseudo-windows it was calibrated on."""

    mean: float
    error: float
    n_events: int
    windows: list
    epochs: tuple = ()
    depths: tuple = ()
    weights: tuple = ()
    sectors: tuple = ()


def a0_depth(
    time: np.ndarray,
    values: np.ndarray,
    sector: np.ndarray,
    candidate: Candidate,
    plan: TessTestPlan,
    seed: int,
    exclude_phase_half: bool = False,
) -> A0Depth | None:
    """The measurement of ``battery.event_shift`` (an additive local trend fitted outside the
    transits, then the per-event box depths) with A0's per-event errors and A0's group rule;
    None when no event is measured or the group error is not calibrated."""
    from refute.packs.tess.battery import additive_residuals
    from refute.packs.tess.events import per_event_depths, per_point_sigma, transit_mask

    good = np.isfinite(time) & np.isfinite(values)
    time, values, sector = time[good], values[good], sector[good]
    if time.size < 10:
        return None
    order = np.argsort(time, kind="stable")
    time, values, sector = time[order], values[order], sector[order]
    half = plan.detrend.transit_mask_half_width_durations * candidate.duration
    mask = transit_mask(time, candidate.period, candidate.t0, half)
    resid = additive_residuals(time, values, sector, mask, plan)
    ok = np.isfinite(resid)
    series = LightCurveData(
        time[ok], 1.0 + resid[ok], np.ones(int(ok.sum())), sector[ok], np.zeros(int(ok.sum()))
    )
    sigma = per_point_sigma(series, mask[ok])
    cadence = plan.data.exptime_seconds / 86400.0
    ev = plan.gauntlet.events
    events = per_event_depths(
        series, candidate.period, candidate.t0, candidate.duration, cadence, ev, 0.0, sigma
    )
    if len(events) == 0:
        return None
    measured, windows, _ = a0.empirical_events(
        series, candidate, events, ev, cadence, exclude_phase_half=exclude_phase_half
    )
    if len(measured) == 0:
        return None
    expected_in = candidate.duration / cadence
    metas = []
    for centre, n_in in zip(measured.centers.tolist(), measured.n_in.tolist(), strict=True):
        meta = a0.event_meta(
            series.time, series.sector, centre, n_in / expected_in, ev.min_coverage
        )
        if meta is None:  # never: empirical_events keeps only events with a stratum
            return None
        metas.append(meta)
    errors = measured.errors
    if not np.all(np.isfinite(errors) & (errors > MIN_MEASURABLE_ERROR)):
        # a zero model error and a zero empirical scatter (to rounding): not measurable
        return None
    weights = 1.0 / np.square(errors)
    weights = weights / np.sum(weights)
    pooled = {s: a0.shortcut(windows, s, seed + s) for s in {m.sector for m in metas}}
    h = a0.half_width(candidate.duration, ev.baseline_outer_durations)
    var = a0.group_variance(weights, errors.tolist(), metas, windows, h, pooled)
    if var is None:
        return None
    mean = float(np.sum(weights * measured.depths))
    return A0Depth(
        mean,
        math.sqrt(var),
        len(measured),
        windows,
        tuple(int(e) for e in measured.epochs),
        tuple(float(d) for d in measured.depths),
        tuple(float(w) for w in weights),
        tuple(m.sector for m in metas),
    )


def window_correlation(a: A0Depth, b: A0Depth) -> float | None:
    """The Pearson correlation of two series' pseudo-event values at the same centres (the
    measured correlation of their depths), or None below A0's minimum of pairs."""
    by_centre = {(w.sector, round(w.centre, 6)): w.value for w in b.windows}
    pairs = [
        (w.value, by_centre[(w.sector, round(w.centre, 6))])
        for w in a.windows
        if (w.sector, round(w.centre, 6)) in by_centre
    ]
    if len(pairs) < a0.MIN_PAIRS:
        return None
    x, y = np.asarray(pairs).T
    return a0.pearson(x, y)


def _correlated(rng, n, rho):
    z1 = rng.standard_normal(n)
    z2 = rho * z1 + math.sqrt(max(0.0, 1.0 - rho * rho)) * rng.standard_normal(n)
    return z1, z2


# --- aperture_depth --------------------------------------------------------------------------


def check_aperture_depth(
    pixels: list[PixelData],
    candidate: Candidate,
    plan: TessTestPlan,
    seed: int,
    exclude_phase_half: bool = False,
    depth=a0_depth,
) -> TestResult:
    """v0.5's ``aperture_depth`` with the large-minus-core difference measured on its own series
    and its error from A0 (WP3 (a)); its sensitivity block is attached. ``depth`` is the A0 group
    depth (battery version 4 passes its own)."""
    from refute.packs.tess.battery import _dilate, aperture_series, core_aperture

    params = plan.gauntlet.aperture_depth
    thresholds = params.model_dump(mode="json")
    series: dict[str, list[np.ndarray]] = {k: [] for k in ("core", "large", "annulus", "time")}
    sectors: list[np.ndarray] = []
    for px in pixels:
        if not px.aperture.any():
            continue
        core = core_aperture(px, params.core_radius_pixels)
        finite = np.isfinite(px.flux).all(axis=0)
        large = _dilate(px.aperture, params.dilation_pixels) & finite
        t_c, f_c, _, _ = aperture_series(px, core)
        t_l, f_l, _, _ = aperture_series(px, large)
        common, i_c, i_l = np.intersect1d(t_c, t_l, return_indices=True)
        if common.size < 100:
            continue
        annulus = large & ~core
        t_a, f_a, _, _ = aperture_series(px, annulus) if annulus.any() else (common, None, 0, 0)
        series["time"].append(common)
        c = f_c[i_c] / np.median(f_c[i_c])
        g = f_l[i_l] / np.median(f_l[i_l])
        series["core"].append(c)
        series["large"].append(g)
        if f_a is not None:
            _, i_a, i_ca = np.intersect1d(t_a, common, return_indices=True)
            a_full = np.full(common.size, np.nan)
            a_full[i_ca] = f_a[i_a] / np.median(f_a[i_a])
            series["annulus"].append(a_full)
        else:
            series["annulus"].append(np.full(common.size, np.nan))
        sectors.append(np.full(common.size, px.sector))
    unit = "pixel-file cadences"
    if not series["time"]:
        return TestResult(
            "aperture_depth",
            TestStatus.INCONCLUSIVE,
            Severity.FATAL,
            "no target pixel data usable for aperture photometry",
            metrics={"inconclusive_class": "missing_input"},
            thresholds=thresholds,
            coverage=0,
            coverage_unit=unit,
        )
    time = np.concatenate(series["time"])
    sector = np.concatenate(sectors)
    core_f, large_f = np.concatenate(series["core"]), np.concatenate(series["large"])
    coverage = int(time.size)
    g_core = depth(time, core_f, sector, candidate, plan, seed, exclude_phase_half)
    g_large = depth(time, large_f, sector, candidate, plan, seed + 1, exclude_phase_half)
    g_diff = depth(time, large_f - core_f, sector, candidate, plan, seed + 2, exclude_phase_half)
    if g_core is None or g_large is None or g_diff is None:
        return TestResult(
            "aperture_depth",
            TestStatus.INCONCLUSIVE,
            Severity.FATAL,
            "no transit with enough coverage and a calibrated A0 error in the pixel data",
            metrics={"inconclusive_class": "not_enough_data"},
            thresholds=thresholds,
            coverage=0,
            coverage_unit="transits measured in the pixel data",
        )
    g_annulus = depth(
        time, np.concatenate(series["annulus"]), sector, candidate, plan, seed + 3,
        exclude_phase_half,
    )  # fmt: skip
    core_snr = g_core.mean / g_core.error
    large_snr = g_large.mean / g_large.error
    diff_sigma = g_diff.mean / g_diff.error
    ratio = g_large.mean / g_core.mean if g_core.mean > 0 else float("inf")
    rho = window_correlation(g_core, g_diff)
    metrics: dict[str, Any] = {
        "depth_core_ppm": g_core.mean * 1e6,
        "depth_core_err_ppm": g_core.error * 1e6,
        "depth_large_ppm": g_large.mean * 1e6,
        "depth_large_err_ppm": g_large.error * 1e6,
        "depth_difference_ppm": g_diff.mean * 1e6,
        "depth_difference_err_ppm": g_diff.error * 1e6,
        "depth_annulus_ppm": g_annulus.mean * 1e6 if g_annulus else None,
        "depth_annulus_err_ppm": g_annulus.error * 1e6 if g_annulus else None,
        "core_difference_correlation": rho,
        "detection_sigma_core": core_snr,
        "detection_sigma_large": large_snr,
        "depth_ratio_large_to_core": ratio,
        "difference_sigma": diff_sigma,
        "n_sectors": len(series["time"]),
        "estimator": "large-minus-core difference series (WP3 (a)); errors from A0",
    }
    blocks = aperture_blocks(g_core, g_diff, rho, params, plan.stronger, seed + 4)
    if max(core_snr, large_snr) < params.max_sigma:
        return TestResult(
            "aperture_depth",
            TestStatus.INCONCLUSIVE,
            Severity.FATAL,
            f"the transit is not detected in the pixel photometry (core {core_snr:.1f} sigma, "
            f"large {large_snr:.1f} sigma, both < {params.max_sigma}): the depths cannot be "
            "compared",
            metrics={**metrics, "inconclusive_class": "not_enough_data"},
            thresholds=thresholds,
            coverage=coverage,
            coverage_unit=unit,
            sensitivity=blocks,
        )
    if diff_sigma >= params.max_sigma and ratio >= params.min_depth_ratio:
        status = TestStatus.FAIL
        message = (
            f"depth grows with the aperture (ratio {ratio:.2f}, {diff_sigma:.1f} sigma on the "
            "difference series): the signal comes from outside the core aperture"
        )
    else:
        status = TestStatus.PASS
        message = (
            f"depth does not grow with the aperture (ratio {ratio:.2f}, {diff_sigma:.1f} sigma on "
            f"the difference series; transit detected at {max(core_snr, large_snr):.1f} sigma)"
        )
    return TestResult(
        "aperture_depth",
        status,
        Severity.FATAL,
        message,
        metrics=metrics,
        thresholds=thresholds,
        coverage=coverage,
        coverage_unit=unit,
        sensitivity=blocks,
    )


def aperture_blocks(g_core, g_diff, rho, params, sp, seed) -> dict | None:
    """v0.5's compound rule (difference at ``max_sigma`` and ratio at least ``min_depth_ratio``)
    under the alternative ratio ``min_depth_ratio + 0.3``, with the core depth and the difference
    drawn from their A0 errors and their measured correlation; no block without a correlation."""
    if rho is None:
        return None
    core, e_core, e_diff = g_core.mean, g_core.error, g_diff.error
    ratio_alt = params.min_depth_ratio + sp.aperture_alternative_ratio_increment
    if not (core > 0) or not (e_diff > 0):
        probability = 0.0
    else:

        def draw(rng, n):
            z1, z2 = _correlated(rng, n, rho)
            c = core + e_core * z1
            d = (ratio_alt - 1.0) * core + e_diff * z2
            return c, d

        def reject(stats):
            c, d = stats
            with np.errstate(divide="ignore", invalid="ignore"):
                ratio = np.where(c > 0, (c + d) / c, np.inf)
            return (d / e_diff >= params.max_sigma) & (ratio >= params.min_depth_ratio)

        probability = simulated_probability(draw, reject, seed)
    block = rule_block(
        "large-to-core depth ratio", ratio_alt, "ratio", "compound-sim-2", probability
    )
    return {"main": block}


# --- systematics ----------------------------------------------------------------------------


def _normalized(values: np.ndarray) -> np.ndarray:
    finite = np.isfinite(values)
    median = np.median(values[finite]) if finite.any() else np.nan
    return values / median if np.isfinite(median) and median != 0 else np.full(values.size, np.nan)


def sap_applicability(a: SectorAux) -> tuple[bool, str, str | None]:
    """Amendment 6: whether the SAP sub-check applies in this sector, with the reason and the
    class when it does not (docs/plans/v0.5.1-acceptance.md, WP3 (a)).

    On the cadences where both normalized series (each divided by its median) are finite: below
    ``SAP_MIN_CADENCES`` cadences or a PDCSAP standard deviation (population, ``ddof=0``) below
    ``SAP_MIN_PDCSAP_SD``, not applicable with the class ``not_enough_data`` (provisional
    operational cutoffs, a declared convention, not calibrated); otherwise ``SAP = a + b z`` with
    ``z`` the standardized PDCSAP is fitted by ordinary least squares, and a largest absolute
    residual at most ``AFFINE_TOLERANCE`` means SAP is an exact affine function of PDCSAP: no
    correction was applied, not applicable (class ``no_correction``)."""
    sap, pdc = _normalized(a.sap_flux), _normalized(a.pdcsap_flux)
    both = np.isfinite(sap) & np.isfinite(pdc)
    n = int(both.sum())
    if n < SAP_MIN_CADENCES:
        why = f"sector {a.sector}: {n} finite cadences (< {SAP_MIN_CADENCES})"
        return False, why, "not_enough_data"
    s, p = sap[both], pdc[both]
    sd = float(np.std(p))
    if not sd >= SAP_MIN_PDCSAP_SD:
        why = f"sector {a.sector}: PDCSAP standard deviation {sd:.3g} (< {SAP_MIN_PDCSAP_SD:g})"
        return False, why, "not_enough_data"
    z = (p - p.mean()) / sd
    design = np.column_stack([np.ones(n), z])
    coef, *_ = np.linalg.lstsq(design, s, rcond=None)
    worst = float(np.max(np.abs(s - design @ coef)))
    if worst <= AFFINE_TOLERANCE:
        why = (
            f"sector {a.sector}: SAP an exact affine function of PDCSAP (largest residual "
            f"{worst:.2g} <= {AFFINE_TOLERANCE:g}; no correction applied)"
        )
        return False, why, "no_correction"
    return True, "", None


def check_systematics(
    aux: list[SectorAux],
    candidate: Candidate,
    plan: TessTestPlan,
    seed: int,
    exclude_phase_half: bool = False,
    depth=a0_depth,
    a0_aux: list[SectorAux] | None = None,
    a0_refused: str | None = None,
) -> TestResult:
    """v0.5's ``systematics`` with A0's errors (WP3 (a)): the SAP sub-check on the
    SAP-minus-expected series over the sectors where it applies (``sap_applicability``,
    amendment 6), the background sub-check with A0's error; its blocks attached. ``depth`` is the
    A0 group depth; ``a0_aux`` the sectors of the sub-checks that use it and ``a0_refused`` why they
    may not run (battery version 4; by default every sector, and they run)."""
    from refute.packs.tess.battery import transit_centers_with_data

    params = plan.gauntlet.systematics
    sp = plan.stronger
    thresholds = params.model_dump(mode="json")
    unit = "sub-checks run"
    if not aux:
        return TestResult(
            "systematics",
            TestStatus.INCONCLUSIVE,
            Severity.WARNING,
            "no SAP flux, background or quality data available",
            metrics={"inconclusive_class": "missing_input"},
            thresholds=thresholds,
            coverage=0,
            coverage_unit=unit,
        )
    time = np.concatenate([a.time for a in aux])
    dumps = np.sort(np.concatenate([a.dump_times for a in aux]))
    centers = transit_centers_with_data(time, candidate)
    reach = candidate.duration / 2 + params.dump_margin_hours / 24
    near = [bool(dumps.size and np.min(np.abs(dumps - c)) <= reach) for c in centers]
    fraction = float(np.mean(near)) if near else 0.0
    crowds = [a.crowdsap for a in aux if a.crowdsap is not None]
    metrics: dict[str, Any] = {
        "n_transits_with_data": len(centers),
        "n_momentum_dumps": int(dumps.size),
        "n_transits_near_dumps": int(sum(near)),
        "fraction_near_dumps": fraction,
        "median_crowdsap": float(np.median(crowds)) if crowds else None,
        "estimator": "SAP-minus-expected series and background with A0 errors (WP3 (a))",
    }
    problems: list[str] = []
    not_run: dict[str, str] = {}
    not_applicable: dict[str, str] = {}
    ran: list[str] = []
    blocks: dict[str, dict] = {
        "dumps": category_block(
            "fraction",
            f"fraction of the transits near momentum dumps, against {params.max_dump_fraction}",
        )
    }

    if len(centers) >= params.min_events_for_dumps:
        ran.append(f"momentum dumps ({int(dumps.size)} in the quality column)")
        if fraction >= params.max_dump_fraction:
            problems.append(f"{sum(near)} of {len(centers)} transits are near momentum dumps")
    else:
        not_run["momentum_dumps"] = (
            f"only {len(centers)} transit(s) with data (< {params.min_events_for_dumps})"
        )

    # --- SAP versus PDCSAP on the SAP-minus-expected series -------------------------------
    a0_source = aux if a0_aux is None else a0_aux
    usable: list[SectorAux] = []
    excluded: list[dict[str, Any]] = []
    for a in a0_source:
        applies, why, kind = sap_applicability(a)
        if applies:
            usable.append(a)
        else:
            excluded.append({"sector": int(a.sector), "reason": why, "class": kind})
    metrics["sap_not_applicable_sectors"] = excluded
    if a0_refused is not None:
        not_run["sap_vs_pdcsap"] = a0_refused
    elif not usable:
        why = "not applicable in every sector: " + "; ".join(e["reason"] for e in excluded)
        not_applicable["sap_vs_pdcsap"] = why
        blocks["sap"] = not_applicable_block(why)
    elif any(a.crowdsap is None for a in usable):
        not_run["sap_vs_pdcsap"] = "no CROWDSAP value"
    else:
        t_u = np.concatenate([a.time for a in usable])
        s_u = np.concatenate([np.full(a.time.size, a.sector) for a in usable])
        pdc_n = np.concatenate([_normalized(a.pdcsap_flux) for a in usable])
        r = np.concatenate(
            [_normalized(a.sap_flux) - a.crowdsap * _normalized(a.pdcsap_flux) for a in usable]
        )
        g_pdc = depth(t_u, pdc_n, s_u, candidate, plan, seed, exclude_phase_half)
        g_r = depth(t_u, r, s_u, candidate, plan, seed + 1, exclude_phase_half)
        crowd_of = {a.sector: float(a.crowdsap) for a in usable}
        expected, crowd_eff = (
            expected_sap_depth(g_pdc, g_r, crowd_of) if g_pdc and g_r else (None, None)
        )
        if g_pdc is None:
            not_run["sap_vs_pdcsap"] = "no transit measured in the PDCSAP flux"
        elif not (g_pdc.mean > 0):
            not_run["sap_vs_pdcsap"] = "the PDCSAP depth is not positive"
        elif g_r is None or not (g_r.error > 0):
            not_run["sap_vs_pdcsap"] = "error not measurable"
        elif expected is None or not (expected > 0):
            not_run["sap_vs_pdcsap"] = "no transit measured in both the PDCSAP and SAP series"
        else:
            diff = g_r.mean
            sigma = abs(diff) / g_r.error
            rel = abs(diff) / expected
            rho = window_correlation(g_pdc, g_r)
            metrics.update(
                {
                    "depth_pdcsap_ppm": g_pdc.mean * 1e6,
                    "expected_sap_depth_ppm": expected * 1e6,
                    "effective_crowdsap": crowd_eff,
                    "sap_minus_expected_ppm": diff * 1e6,
                    "sap_minus_expected_err_ppm": g_r.error * 1e6,
                    "pdcsap_difference_correlation": rho,
                    "sap_difference_sigma": sigma,
                    "sap_relative_difference": rel,
                }
            )
            ran.append("SAP versus PDCSAP")
            if sigma >= params.max_sap_sigma and rel >= params.max_sap_rel_diff:
                problems.append(
                    f"SAP depth differs from the crowding-corrected PDCSAP depth by {rel:.0%} "
                    f"({sigma:.1f} sigma on the SAP-minus-expected series)"
                )
            block = sap_block(expected, crowd_eff * g_pdc.error, g_r, rho, params, sp, seed + 2)
            if block is not None:
                blocks["sap"] = block

    # --- background --------------------------------------------------------------------
    g_bkg = g_sap = None
    if a0_refused is None and a0_source:
        t_b = np.concatenate([a.time for a in a0_source])
        s_b = np.concatenate([np.full(a.time.size, a.sector) for a in a0_source])
        g_bkg = depth(
            t_b, np.concatenate([a.sap_bkg for a in a0_source]), s_b, candidate, plan, seed + 3,
            exclude_phase_half,
        )  # fmt: skip
        g_sap = depth(
            t_b, np.concatenate([a.sap_flux for a in a0_source]), s_b, candidate, plan, seed + 4,
            exclude_phase_half,
        )  # fmt: skip
    if a0_refused is not None:
        not_run["background"] = a0_refused
    elif g_bkg is None or g_sap is None:
        not_run["background"] = "no transit measured in the background or SAP flux"
    elif not (g_sap.mean > 0):
        not_run["background"] = "the SAP depth is not positive"
    elif not (g_bkg.error > 0):
        not_run["background"] = "error not measurable"
    else:
        rise = -g_bkg.mean
        sigma = rise / g_bkg.error
        frac = rise / g_sap.mean
        metrics.update(
            {
                "depth_sap_ppm": g_sap.mean * 1e6,
                "background_rise_in_transit": rise,
                "background_rise_err": g_bkg.error,
                "background_rise_sigma": sigma,
                "background_rise_fraction_of_depth": frac,
            }
        )
        ran.append("background")
        if sigma >= params.max_background_sigma and frac >= params.max_background_fraction:
            problems.append(
                f"the background rises in transit by {frac:.0%} of the depth ({sigma:.1f} sigma)"
            )
        blocks["background"] = background_block(g_bkg, g_sap, params, sp, seed + 5)

    metrics["sub_checks_run"] = ran
    metrics["sub_checks_not_run"] = not_run
    metrics["sub_checks_not_applicable"] = not_applicable
    if problems:
        status, message = TestStatus.FAIL, "; ".join(problems)
    elif not_run:
        reasons = "; ".join(f"{name}: {why}" for name, why in not_run.items())
        status, message = TestStatus.INCONCLUSIVE, f"sub-check(s) could not run ({reasons})"
        metrics["inconclusive_class"] = not_run_class(not_run.values())
    else:
        status = TestStatus.PASS
        message = f"no problem in {len(ran)} sub-checks: " + ", ".join(ran)
        if not_applicable:
            message += "; not applicable: " + "; ".join(
                f"{name} ({why})" for name, why in not_applicable.items()
            )
    return TestResult(
        "systematics",
        status,
        Severity.WARNING,
        message,
        metrics=metrics,
        thresholds=thresholds,
        coverage=len(ran),
        coverage_unit=unit,
        sensitivity=blocks,
    )


def not_run_class(reasons) -> str:
    """WP4: the class of a ``systematics`` INCONCLUSIVE from its sub-checks' reasons, the first
    of ``refute.core.inconclusive.PRIORITY`` among them."""
    from refute.core.inconclusive import PRIORITY

    def one(why: str) -> str:
        if why == "no CROWDSAP value":
            return "missing_input"
        if why == "error not measurable" or why.endswith("depth is not positive"):
            return "insufficient_sensitivity"
        return "not_enough_data"  # too few transits, or no transit measured

    found = {one(why) for why in reasons}
    return next(cls for cls in PRIORITY if cls in found)


def expected_sap_depth(g_pdc: A0Depth, g_r: A0Depth, crowd_of: dict[int, float]):
    """The expected SAP depth with each event's own sector CROWDSAP, under the SAP-minus-expected
    series' event weights (Codex, WP3 (a) review): ``sum_i w_i CROWDSAP_s(i) d_PDCSAP,i`` over the
    events measured in both series, and the effective CROWDSAP ``sum_i w_i CROWDSAP_s(i)``;
    (None, None) without a common event."""
    pdc = dict(zip(g_pdc.epochs, g_pdc.depths, strict=True))
    common = [i for i, e in enumerate(g_r.epochs) if e in pdc]
    if not common:
        return None, None
    w = np.array([g_r.weights[i] for i in common])
    w = w / np.sum(w)
    crowd = np.array([crowd_of[g_r.sectors[i]] for i in common])
    depth = np.array([pdc[g_r.epochs[i]] for i in common])
    return float(np.sum(w * crowd * depth)), float(np.sum(w * crowd))


def sap_block(expected, e_expected, g_r, rho, params, sp, seed) -> dict | None:
    """v0.5's compound SAP rule under the alternative relative difference
    ``max_sap_rel_diff + sap_alternative_increment``, the expected SAP depth (sector CROWDSAP
    times the PDCSAP depth) and the SAP-minus-expected difference drawn from their A0 errors and
    their measured correlation; no block without a correlation."""
    if rho is None:
        return None
    e_r = g_r.error
    rel_alt = params.max_sap_rel_diff + sp.sap_alternative_increment

    def draw(rng, n):
        z1, z2 = _correlated(rng, n, rho)
        x_hat = expected + e_expected * z1
        d_hat = rel_alt * expected + e_r * z2
        return x_hat, d_hat

    def reject(stats):
        x_hat, d_hat = stats
        expected_hat = x_hat
        diff = np.abs(d_hat)
        with np.errstate(divide="ignore", invalid="ignore"):
            rel = np.where(expected_hat > 0, diff / expected_hat, 0.0)
        return (
            (expected_hat > 0)
            & (diff / e_r >= params.max_sap_sigma)
            & (rel >= params.max_sap_rel_diff)
        )

    probability = simulated_probability(draw, reject, seed)
    return rule_block(
        "SAP relative depth difference", rel_alt, "fraction", "compound-sim-2", probability
    )


def background_block(g_bkg, g_sap, params, sp, seed) -> dict:
    """v0.5's background block with A0's errors."""
    frac_alt = params.max_background_fraction + sp.background_alternative_increment
    e_bkg, sap_depth, e_sap = g_bkg.error, g_sap.mean, g_sap.error

    def draw(rng, n):
        s_hat = sap_depth + e_sap * rng.standard_normal(n)
        rise = frac_alt * sap_depth + e_bkg * rng.standard_normal(n)
        return s_hat, rise

    def reject(stats):
        s_hat, rise = stats
        with np.errstate(divide="ignore", invalid="ignore"):
            frac = np.where(s_hat > 0, rise / s_hat, 0.0)
        return (
            (s_hat > 0)
            & (rise / e_bkg >= params.max_background_sigma)
            & (frac >= params.max_background_fraction)
        )

    probability = simulated_probability(draw, reject, seed)
    return rule_block(
        "background rise in transit", frac_alt, "fraction of the depth", "compound-sim-1",
        probability,
    )  # fmt: skip
