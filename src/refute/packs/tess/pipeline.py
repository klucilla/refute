"""Analysis of one target: search, gauntlet a-d, v0.2 battery, blind holdout, verdict.

The holdout (test e) is called with the raw light curve and sector metadata only.
It never receives the candidate found by the global search, nor the pixel data,
auxiliary columns, neighbors or catalogs used by the v0.2 battery.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import numpy as np
from astropy.timeseries import BoxLeastSquares

from refute.core.verdict import (
    RoleAggregate,
    Severity,
    TestResult,
    TestStatus,
    aggregate,
    aggregate_roles,
    defer_tests,
    diagnostic_state,
    enforce_coverage,
)
from refute.packs.tess.battery import (
    check_aperture_depth,
    check_centroid_shift,
    check_nearby_contamination,
    check_period_alias,
    check_systematics,
)
from refute.packs.tess.detrend import detrend
from refute.packs.tess.ebcatalog import (
    EbEntry,
    check_eb_catalog,
    load_catalogs,
    load_scan,
    resolve_references,
)
from refute.packs.tess.ephemeris import Ephemeris, fit_linear_ephemeris, measure_transit_times
from refute.packs.tess.events import (
    EventDepths,
    group_mean,
    per_event_depths,
    per_point_sigma,
    transit_mask,
)
from refute.packs.tess.gauntlet import (
    check_odd_even,
    check_plausibility,
    check_secondary_eclipse,
    check_snr,
    star_inputs,
)
from refute.packs.tess.holdout import HoldoutOutcome, run_holdout
from refute.packs.tess.params import METHOD_STATUS_REFERENCE, TessTestPlan
from refute.packs.tess.prewhiten import Prewhitening, prewhiten, refit
from refute.packs.tess.rednoise import EventNoise, bls_beta, event_noise
from refute.packs.tess.search import SearchResult, finalize_candidate, search_period
from refute.packs.tess.timing import corrected_transit_times
from refute.packs.tess.types import BTJD_OFFSET, Candidate, LightCurveData, TessData

SearchFn = Callable[[LightCurveData, Any], SearchResult]


@dataclass
class GauntletOutcome:
    candidate: Candidate | None
    flattened: LightCurveData | None
    primary: EventDepths | None
    secondary: EventDepths | None
    tests: list[TestResult]
    ephemeris: Ephemeris | None
    # M4 piece 3, with the corrections switch on: the template, the drops and the A1 estimate
    # at n_tau of the global transit times (TemplateTimes.to_dict); None with the switch off.
    timing: dict | None = None
    # The M4 parts that actually ran in the global analysis (map Amendment 17); empty on M3.
    executed: list[str] = field(default_factory=list)
    # M4 piece 7 (map Amendment 22): the global components and the reason of a failed refit S'.
    prewhitening: Prewhitening | None = None
    refit_reason: str | None = None
    refit_left_out: list[int] = field(default_factory=list)


def _minus(curve: LightCurveData, model: np.ndarray) -> LightCurveData:
    return LightCurveData(curve.time, curve.flux - model, curve.flux_err, curve.sector, curve.year)


def global_prewhitening(
    data: TessData, plan: TessTestPlan, flat: LightCurveData | None = None
) -> tuple[Prewhitening | None, LightCurveData]:
    """M4 piece 7 (map Amendments 22 and 23): the global components found on ``L1``, and the
    curve the search receives, ``detrend(raw − S_raw)`` with ``S_raw`` their joint refit on the
    raw curve (``L1`` itself when nothing was accepted, so the curve is bit-equal). The search
    refit's reason and left-out sectors are recorded on the returned operation."""
    if flat is None:
        flat = detrend(data.lc, plan.detrend)
    if not plan.gauntlet.corrections.active:
        return None, flat
    pw = prewhiten(flat, plan)
    if not pw.components:
        return pw, flat
    fitted = refit(data.lc, pw.components, np.zeros(data.lc.time.size, bool), plan)
    pw.search_refit_reason = fitted.reason
    pw.search_left_out = list(fitted.sectors_left_out)
    if fitted.reason is not None:
        return pw, flat
    return pw, detrend(_minus(data.lc, fitted.model), plan.detrend)


@dataclass
class Analysis:
    search: SearchResult
    flattened_search: LightCurveData
    gauntlet: GauntletOutcome
    holdout: HoldoutOutcome
    tests: list[TestResult]
    verdict: str
    verdict_reason: str
    extras: dict[str, Any] = field(default_factory=dict)
    # v0.4 (issue #174), discover claims only: the role outcome and the stage of the run.
    roles: RoleAggregate | None = None
    stage: int | None = None
    deferred: list[str] = field(default_factory=list)


def _not_run(name: str, severity: Severity, reason: str) -> TestResult:
    return TestResult(name, TestStatus.INCONCLUSIVE, severity, reason)


BATTERY_TESTS = (
    ("centroid_shift", Severity.FATAL),
    ("aperture_depth", Severity.FATAL),
    ("nearby_contamination", Severity.WARNING),
    ("period_alias", Severity.FATAL),
    ("systematics", Severity.WARNING),
)


def battery_tests(
    data: TessData,
    candidate: Candidate,
    plan: TessTestPlan,
    catalogs: list[EbEntry] | None = None,
    catalog_scan: dict | None = None,
) -> list[TestResult]:
    """The v0.2 battery against the final candidate (see docs/gauntlet-tess-v0.2.md)."""
    aux = data.aux
    pixels = aux.pixels if aux else []
    crowds = [a.crowdsap for a in aux.sectors if a.crowdsap is not None] if aux else []
    tests = [
        check_centroid_shift(pixels, candidate, plan),
        check_aperture_depth(pixels, candidate, plan),
        check_nearby_contamination(
            aux.neighbors if aux else None,
            data.star,
            candidate.depth,
            crowds,
            plan.gauntlet.nearby_contamination,
            aux.neighbor_radius_arcsec if aux else None,
        ),
        check_period_alias(data.lc, candidate, plan),
        check_systematics(aux.sectors if aux else [], candidate, plan),
    ]
    if catalogs is not None:
        tests.append(eb_catalog_test(data, candidate, plan, catalogs, catalog_scan))
    return tests


def eb_catalog_test(
    data: TessData,
    candidate: Candidate,
    plan: TessTestPlan,
    catalogs: list[EbEntry],
    catalog_scan: dict | None,
) -> TestResult:
    """The ``eb_catalog`` test of the battery for the final candidate."""
    return check_eb_catalog(
        catalogs,
        catalog_scan,
        data.target_key,
        data.star,
        candidate.period,
        plan.gauntlet.eb_catalog,
    )


def attack_candidate(
    data: TessData,
    candidate: Candidate | None,
    plan: TessTestPlan,
    catalogs: list[EbEntry] | None = None,
    catalog_scan: dict | None = None,
    prewhitening: Prewhitening | None = None,
) -> GauntletOutcome:
    """Gauntlet tests a-d and the v0.2 battery against a candidate found on all data.

    ``catalogs`` is None when the claim has no eclipsing-binary catalog attached;
    the ``eb_catalog`` test is then not part of the gauntlet (the report says so).
    With the corrections active, ``prewhitening`` is the global operation of M4 piece 7; when it
    is not given (the adapters), it is computed here by the same call (map Amendment 22).
    """
    gp = plan.gauntlet
    pw = prewhitening
    if gp.corrections.active and pw is None:
        pw, _ = global_prewhitening(data, plan)
    # the M4 parts that actually ran (map Amendment 17, the marker)
    executed: list[str] = ["prewhitening"] if pw is not None else []
    if candidate is None:
        tests = [
            check_snr(None, gp.snr),
            _not_run("odd_even", Severity.FATAL, "no candidate"),
            _not_run("secondary_eclipse", Severity.FATAL, "no candidate"),
            _not_run("plausibility", Severity.FATAL, "no candidate"),
            *(_not_run(name, severity, "no candidate") for name, severity in BATTERY_TESTS),
        ]
        if catalogs is not None:
            tests.append(_not_run("eb_catalog", Severity.FATAL, "no candidate"))
        if plan.v05:
            tests += [_not_run(name, severity, "no candidate") for name, severity in V05_TESTS]
        return GauntletOutcome(
            None, None, None, None, tests, None, executed=executed, prewhitening=pw
        )

    cadence = plan.data.exptime_seconds / 86400.0
    mask_half = plan.detrend.transit_mask_half_width_durations * candidate.duration
    mask = transit_mask(data.lc.time, candidate.period, candidate.t0, mask_half)
    refit_reason = None
    refit_left_out: list[int] = []
    raw = data.lc
    if pw is not None and pw.components:
        # M4 piece 7 (map Amendment 23): S'_raw, the global frequencies refitted on the raw curve
        # with the search candidate's transits masked, subtracted before the masked detrending
        fitted = refit(data.lc, pw.components, mask, plan)
        refit_reason = fitted.reason
        refit_left_out = list(fitted.sectors_left_out)
        if fitted.reason is None:
            raw = _minus(data.lc, fitted.model)
    flat = detrend(raw, plan.detrend, mask=mask)
    sigma = per_point_sigma(
        flat, transit_mask(flat.time, candidate.period, candidate.t0, mask_half)
    )
    final = finalize_candidate(
        flat, candidate.period, candidate.duration, plan.search, candidate.sde, sigma
    )
    noise = None
    if gp.corrections.active:
        # M4 piece 2: the A1 noise model for every per-event measurement and the gate.
        noise = event_noise(flat, None, final.period, final.t0, final.duration, plan)
        executed.append("a1_noise")
    primary = per_event_depths(
        flat, final.period, final.t0, final.duration, cadence, gp.events, 0.0, sigma, noise
    )
    secondary = per_event_depths(
        flat, final.period, final.t0, final.duration, cadence, gp.events, 0.5, sigma, noise
    )
    if noise is None:
        snr_test = check_snr(final, gp.snr)
    else:
        final, snr_test = _bls_gate(final, flat, sigma, noise, primary, gp)
        executed.append("bls_beta_gate")
    tests = [
        snr_test,
        check_odd_even(primary, gp.odd_even),
        check_secondary_eclipse(primary, secondary, gp.secondary_eclipse),
        check_plausibility(final, data.star, gp.plausibility),
        *battery_tests(data, final, plan, catalogs, catalog_scan),
    ]
    if any(t.name == "period_alias" and "thresholds_m4" in t.metrics for t in tests):
        executed.append("period_alias_m4")  # M4 piece 6 ran (map Amendment 21)
    if plan.v05:
        tests = v05_tests(tests, data, flat, final, primary, secondary, plan)
    timing = None
    if gp.corrections.active:
        # M4 piece 3: the trapezoid template, the scan and the error times beta(n_tau).
        corrected = corrected_transit_times(
            flat, final.period, final.t0, final.duration, sigma, plan
        )
        times, timing = corrected.times, corrected.to_dict()
        executed.append("trapezoid_timing")
    else:
        times = measure_transit_times(
            flat,
            final.period,
            final.t0,
            final.duration,
            final.depth,
            sigma,
            cadence_days=cadence,
            step_minutes=gp.holdout_by_year.timing_step_minutes,
            scan_half_width_durations=gp.holdout_by_year.timing_scan_half_width_durations,
        )
    ephemeris = fit_linear_ephemeris(times) if len(times) >= 2 else None
    return GauntletOutcome(
        final,
        flat,
        primary,
        secondary,
        tests,
        ephemeris,
        timing,
        executed,
        pw,
        refit_reason,
        refit_left_out,
    )


V05_TESTS = (
    ("single_event", Severity.FATAL),
    ("event_consistency", Severity.FATAL),
    ("edge_events", Severity.WARNING),
    ("sinusoid", Severity.WARNING),
    ("duty_cycle", Severity.FATAL),
)


def v05_tests(
    tests: list[TestResult],
    data: TessData,
    flat: LightCurveData,
    final: Candidate,
    primary: EventDepths,
    secondary: EventDepths,
    plan: TessTestPlan,
) -> list[TestResult]:
    """A v0.5 claim (discovery version 2): the sensitivity blocks of the v0.4 tests, the
    two-sided phase-0.5 check in place of the v0.4 one, and the v0.5 tests (WP1 to WP3 of
    docs/plans/v0.5-acceptance.md). The v0.4 check functions are unchanged. The per-event
    measurements of the v0.5 tests use the red-noise error model (A1, ``rednoise.event_noise``).
    ``centroid_shift`` is the per-sector v0.5 test (WP4, ``centroid_v5``)."""
    from refute.packs.tess import battery_v5 as v5
    from refute.packs.tess import battery_v51 as v51
    from refute.packs.tess import battery_v51_diff as v51d
    from refute.packs.tess import power

    sp = plan.stronger
    gp = plan.gauntlet
    cadence = plan.data.exptime_seconds / 86400.0
    noise = event_noise(flat, None, final.period, final.t0, final.duration, plan)
    events = per_event_depths(
        flat, final.period, final.t0, final.duration, cadence, gp.events, 0.0, None, noise
    )
    events_half = per_event_depths(
        flat, final.period, final.t0, final.duration, cadence, gp.events, 0.5, None, noise
    )
    seed = power.candidate_seed
    aux = data.aux
    per_event = events
    secondary = v5.check_secondary_two_sided(
        events, events_half, gp.secondary_eclipse, sp, seed("secondary_eclipse", final)
    )
    a0_note = None
    if plan.is_v051:
        # v0.5.1 A0 (docs/plans/v0.5.1-acceptance.md): the per-event tests use the empirical
        # errors of pseudo-event windows; the phase-0.5 windows enter unless the candidate's
        # own secondary_eclipse detects a secondary (amendment 5); the v0.5 path is unchanged
        from refute.packs.tess import a0

        exclude = secondary.status is TestStatus.FAIL
        per_event, _, _ = a0.empirical_events(
            flat, final, events, gp.events, cadence, exclude_phase_half=exclude
        )
        if exclude:
            a0_note = "phase-0.5 windows excluded: a secondary detected"
    out: list[TestResult] = []
    for test in tests:
        if test.name == "odd_even" and plan.is_v051:
            # v0.5.1 WP3 (d): the matched-trapezoid estimator with A0's errors
            test = v51.check_odd_even(
                flat, final, gp, sp, cadence, a0_note is not None, seed("odd_even", final)
            )
        elif test.name == "odd_even":
            # v0.5: measured again on the red-noise events (whatever the corrections switch),
            # so that its sensitivity rests on calibrated errors (Codex's review of round 2)
            test = check_odd_even(events, gp.odd_even)
            test = power.attach(test, power.odd_even_blocks(test, final.depth, sp))
        elif test.name == "secondary_eclipse":
            test = secondary
        elif test.name == "plausibility":
            test = power.attach(test, power.plausibility_blocks(test))
        elif test.name == "centroid_shift":
            from refute.packs.tess.centroid_v5 import check_centroid_v5

            test = check_centroid_v5(
                aux.pixels if aux else [],
                aux.sectors if aux else [],
                final,
                plan,
                seed("centroid_shift", final),
            )
        elif test.name == "aperture_depth" and plan.is_v051:
            # WP3 (a): the large-minus-core difference on its own series, A0's error
            test = v51d.check_aperture_depth(
                aux.pixels if aux else [], final, plan, seed("aperture_depth", final),
                a0_note is not None,
            )  # fmt: skip
        elif test.name == "systematics" and plan.is_v051:
            # WP3 (a): the SAP-minus-expected series and the background with A0's errors
            test = v51d.check_systematics(
                aux.sectors if aux else [], final, plan, seed("systematics", final),
                a0_note is not None,
            )  # fmt: skip
        elif test.name == "aperture_depth":
            test = power.attach(
                test, power.aperture_blocks(test, sp, seed("aperture_depth", final))
            )
        elif test.name == "systematics":
            blocks = power.systematics_blocks(
                test, aux.sectors if aux else [], final, plan, seed("systematics", final)
            )
            test = power.attach(test, blocks)
        elif test.name == "period_alias" and plan.is_v051:
            # WP3 (c): version 3 measures again with more harmonics, and its sensitivity with
            # an exact lower bound over more realizations (the v0.5 path below is unchanged)
            alias_plan = power.period_alias_plan(plan)
            test = check_period_alias(data.lc, final, alias_plan)
            if test.status is TestStatus.PASS:
                blocks = power.period_alias_blocks_v51(
                    data.lc, final, alias_plan, check_period_alias, seed("period_alias", final)
                )
                test = power.attach(test, blocks)
        elif test.name == "period_alias" and test.status is TestStatus.PASS:
            blocks = power.period_alias_blocks(
                data.lc, final, plan, check_period_alias, seed("period_alias", final)
            )
            test = power.attach(test, blocks)
        elif test.name == "nearby_contamination":
            test = power.attach(test, power.catalog_blocks(test, "neighbors within the radius"))
        elif test.name == "eb_catalog":
            test = power.attach(test, power.catalog_blocks(test, "catalogued eclipsing binaries"))
        out.append(test)
    out += [
        _with_a0_note(v5.check_single_event(per_event, sp, seed("single_event", final)), a0_note),
        _with_a0_note(v5.check_event_consistency(per_event, sp), a0_note),
        v5.check_edge_events(flat.time, events, final.duration, gp.snr.min_snr, sp),
        (
            v51.check_sinusoid(data.lc, final, sp, plan.v051, seed("sinusoid", final))
            if plan.is_v051
            else v5.check_sinusoid(data.lc, final, sp, seed("sinusoid", final))
        ),
        v5.check_duty_cycle(final, sp),
    ]
    return out


def _with_a0_note(result: TestResult, note: str | None) -> TestResult:
    """A per-event test left INCONCLUSIVE after A0 excluded the phase-0.5 windows says so
    (amendment 5); any other result is unchanged."""
    from dataclasses import replace

    if note is None or result.status is not TestStatus.INCONCLUSIVE:
        return result
    return replace(result, message=f"{result.message} ({note})")


def _bls_gate(
    final: Candidate,
    flat: LightCurveData,
    sigma: np.ndarray,
    noise: EventNoise,
    primary: EventDepths | None,
    gp,
) -> tuple[Candidate, TestResult]:
    """M4 piece 2, the gate by method (a) (m4-implementation-map.md, Amendment 7): the BLS depth
    over the BLS depth error times ``β_D`` (``rednoise.bls_beta``), with the in-transit and
    out-of-transit weights of each sector from astropy's own transit mask. A sector with weight
    that is excluded at ``n_T``, or no in-transit cadence, is INCONCLUSIVE. The stacked per-event
    error of the primary events is reported as a diagnostic only."""
    noise_record = noise.to_dict()
    in_transit = BoxLeastSquares(flat.time, flat.flux, dy=sigma).transit_mask(
        flat.time, final.period, final.duration, final.t0
    )
    weight = 1.0 / np.square(sigma)
    w_in: dict[int, float] = {}
    w_out: dict[int, float] = {}
    for s in np.unique(flat.sector):
        sel = flat.sector == s
        w_in[int(s)] = float(np.sum(weight[sel & in_transit]))
        w_out[int(s)] = float(np.sum(weight[sel & ~in_transit]))
    why = None
    if not sum(w_in.values()) > 0:
        why = "no in-transit cadence"
    else:
        for s in sorted(w_in):
            if w_in[s] > 0 or w_out[s] > 0:
                estimate = noise.box.sectors.get(s)
                if estimate is None or estimate.excluded:
                    why = "noise model undetermined"
                    break
    if why is not None:
        return final, TestResult(
            "snr",
            TestStatus.INCONCLUSIVE,
            Severity.GATE,
            f"{why}: the corrected SNR cannot be computed",
            metrics={"bls_depth_snr": final.snr, "noise": noise_record},
            thresholds={"min_snr": gp.snr.min_snr},
        )
    betas = {s: noise.box.sectors[s].beta for s in w_in if w_in[s] > 0 or w_out[s] > 0}
    beta_d = bls_beta(betas, w_in, w_out)
    corrected = replace(final, snr=final.snr / beta_d, depth_err=final.depth_err * beta_d)
    test = check_snr(corrected, gp.snr)
    stacked = None
    if primary is not None and len(primary) > 0:
        stacked = group_mean(primary.depths, primary.errors).error * 1e6
    metrics = {
        **test.metrics,
        "bls_depth_snr": final.snr,
        "beta_d": beta_d,
        "sectors": {
            str(s): {"beta": betas[s], "w_in": w_in[s], "w_out": w_out[s]} for s in sorted(betas)
        },
        "stacked_error_ppm": stacked,
        "events": 0 if primary is None else len(primary),
        "events_dropped": {} if primary is None else dict(primary.dropped),
        "noise": noise_record,
    }
    return corrected, replace(test, metrics=metrics)


def expected_tests(catalogs_configured: bool, v05: bool = False) -> list[str]:
    """Every test a complete TESS analysis must contain (with the v0.5 tests in a v0.5
    claim)."""
    names = ["snr", "odd_even", "secondary_eclipse", "plausibility"]
    names += [name for name, _ in BATTERY_TESTS]
    if catalogs_configured:
        names.append("eb_catalog")
    if v05:
        names += [name for name, _ in V05_TESTS]
    return [*names, "holdout_by_year"]


def analyze_data(
    data: TessData,
    plan: TessTestPlan,
    search_fn: SearchFn = search_period,
    catalogs: list[EbEntry] | None = None,
    catalog_scan: dict | None = None,
    stage: int | None = None,
) -> Analysis:
    flat = detrend(data.lc, plan.detrend)
    pw, searched = global_prewhitening(data, plan, flat)  # M4 piece 7; L1 itself without it
    search = search_fn(searched, plan.search)
    gauntlet = attack_candidate(data, search.candidate, plan, catalogs, catalog_scan, pw)
    # Blind holdout: raw data and sector metadata only. Never the global candidate.
    holdout = run_holdout(data.lc, data.sectors, plan)
    return conclude_analysis(
        search, flat, gauntlet, holdout, catalogs is not None, plan=plan, stage=stage
    )


def expected_by_role(plan: TessTestPlan, catalogs_configured: bool) -> tuple[list[str], list[str]]:
    """For a discover claim: the decisive tests a complete analysis must contain, and the
    required diagnostics (v0.4, issue #174)."""
    discovery = plan.discovery
    if discovery is None:
        raise ValueError("expected_by_role needs a plan with a discovery section")
    names = expected_tests(catalogs_configured, plan.v05)
    decisive = [n for n in names if discovery.roles.get(n) == "decisive"]
    return decisive, list(discovery.required_diagnostics)


def conclude_analysis(
    search: SearchResult,
    flattened: LightCurveData,
    gauntlet: GauntletOutcome,
    holdout: HoldoutOutcome,
    catalogs_configured: bool,
    *,
    plan: TessTestPlan | None = None,
    stage: int | None = None,
) -> Analysis:
    """The end of an analysis: the coverage rule over every test, then the verdict.

    For a discover claim (a plan with a discovery section; v0.4, issue #174) the tests of a
    later stage are reported INCONCLUSIVE with zero coverage, and the verdict aggregates the
    decisive tests only; the diagnostics are returned apart, in ``roles``."""
    # Domain-agnostic coverage rule: a PASS that examined nothing is INCONCLUSIVE.
    tests = enforce_coverage([*gauntlet.tests, holdout.test])
    if plan is not None and plan.v05:
        # v0.5 (#185): and a fatal or warning PASS without its declared sensitivity, whatever
        # its role, is INCONCLUSIVE (the holdout diagnostic has no rule in v0.5)
        from refute.core.sensitivity import enforce_sensitivity
        from refute.packs.tess.power import registry_for

        tests = enforce_sensitivity(tests, registry_for(plan))
    if plan is None or plan.discovery is None:
        verdict, reason = aggregate(tests, expected=expected_tests(catalogs_configured))
        return Analysis(search, flattened, gauntlet, holdout, tests, verdict.value, reason)
    discovery = plan.discovery
    run_stage = discovery.last_stage if stage is None else int(stage)
    tests, deferred = defer_tests(tests, dict(discovery.stages), run_stage)
    if plan.is_v051:
        # v0.5.1 WP4: every INCONCLUSIVE of a version-3 claim carries its class (after the
        # deferral, which builds new results; Codex's WP4 design review)
        tests = classify_v051(tests, deferred)
    decisive, required = expected_by_role(plan, catalogs_configured)
    roles = aggregate_roles(tests, dict(discovery.roles), decisive, required)
    if plan.is_v051:
        from refute.core.inconclusive import with_classes

        roles.reason = with_classes(roles.reason, roles.decisive)
    return Analysis(
        search,
        flattened,
        gauntlet,
        holdout,
        tests,
        roles.verdict.value,
        roles.reason,
        roles=roles,
        stage=run_stage,
        deferred=deferred,
    )


def classify_v051(tests: list[TestResult], deferred=()) -> list[TestResult]:
    """v0.5.1 WP4: the class of every INCONCLUSIVE test of a version-3 claim
    (``refute.core.inconclusive`` with the TESS table)."""
    from refute.core.inconclusive import annotate
    from refute.packs.tess.inconclusive import TESS_TABLE

    return annotate(tests, TESS_TABLE, deferred)


GATE_NOT_PASSED = "gate_not_passed"
EXPECTED_TESTS_MISSING = "expected_tests_missing"
DATA_FETCH_FAILED = "data_fetch_failed"
ANALYSIS_ERROR = "analysis_error"


def _is_v051(test_plan: dict[str, Any] | None) -> bool:
    """Whether a raw plan is a version-3 plan (False when absent or not a valid plan)."""
    if not test_plan:
        return False
    try:
        return TessTestPlan.model_validate(test_plan).is_v051
    except Exception:  # noqa: BLE001 - an invalid plan is not a version-3 plan here
        return False


def v051_record(analysis: Analysis) -> dict[str, Any]:
    """The v0.5.1 fields of ``verdict.json`` (WP4): the verdict's INCONCLUSIVE class (from its
    decisive INCONCLUSIVE tests only, ``refute.core.inconclusive.PRIORITY``), the condition when
    the aggregation stopped at the gate or at a missing expected test, and every INCONCLUSIVE
    test's class and source."""
    from refute.core.inconclusive import CLASS_KEY, SOURCE_KEY, verdict_class

    condition = None
    cls = None
    if analysis.verdict == "INCONCLUSIVE":
        if analysis.verdict_reason.startswith("gate test "):
            condition = GATE_NOT_PASSED
        elif analysis.verdict_reason.startswith("expected tests missing"):
            condition = EXPECTED_TESTS_MISSING
        else:
            decisive = analysis.roles.decisive if analysis.roles is not None else analysis.tests
            cls = verdict_class(decisive)
    return {
        "inconclusive_class": cls,
        "inconclusive_condition": condition,
        "inconclusive_classes": {
            r.name: {"class": r.metrics[CLASS_KEY], "source": r.metrics[SOURCE_KEY]}
            for r in analysis.tests
            if r.status is TestStatus.INCONCLUSIVE and CLASS_KEY in r.metrics
        },
    }


def duration_record(analysis: Analysis, plan: TessTestPlan) -> dict[str, Any]:
    """The WP4 duration estimate of the final candidate (docs/plans/v0.4-duration-method.md)."""
    from refute.packs.tess.duration import METHOD, estimate_duration

    candidate, flat = analysis.gauntlet.candidate, analysis.gauntlet.flattened
    if candidate is None or flat is None:
        return {"method": METHOD, "estimable": False, "reason": "no candidate"}
    mask_half = plan.detrend.transit_mask_half_width_durations * candidate.duration
    sigma = per_point_sigma(
        flat, transit_mask(flat.time, candidate.period, candidate.t0, mask_half)
    )
    return estimate_duration(
        flat.time,
        flat.flux,
        sigma,
        candidate.period,
        candidate.t0,
        candidate.duration,
        candidate.depth,
        plan.data.exptime_seconds / 86400.0,
    )


TEMPORAL_AGGREGATION_RULE = (
    "legacy rule of holdout_by_year: any hidden year FAIL gives FAIL; otherwise any PASS gives "
    "PASS, even with inconclusive years; otherwise INCONCLUSIVE (refute.packs.tess.holdout)"
)


def discovery_record(analysis: Analysis, plan: TessTestPlan) -> dict[str, Any]:
    """The v0.4 fields of ``verdict.json`` for a discover claim (issue #174)."""
    discovery = plan.discovery
    assert discovery is not None and analysis.roles is not None
    holdout = analysis.roles.diagnostics.get("holdout_by_year")
    rounds = analysis.holdout.rounds if holdout is not None else []
    temporal = {
        "state": diagnostic_state(holdout),
        "test": "holdout_by_year",
        "role": discovery.roles.get("holdout_by_year"),
        "aggregation_rule": TEMPORAL_AGGREGATION_RULE,
        "message": holdout.message if holdout is not None else "not run",
        "per_year": [
            {
                "hidden_year": r.hidden_year,
                "status": r.status.value,
                "reason": r.metrics.get("reason"),
            }
            for r in rounds
        ],
        "inability_reasons": [
            {"hidden_year": r.hidden_year, "reason": r.metrics.get("reason") or r.message}
            for r in rounds
            if r.status is TestStatus.INCONCLUSIVE
        ],
    }
    return {
        "method_status": discovery.method_status,
        "method_status_reference": discovery.method_status_reference,
        "temporal_diagnostic": temporal,
        "discovery": {
            "stage": analysis.stage,
            "last_stage": discovery.last_stage,
            "roles": dict(discovery.roles),
            "decisive_tests": [r.name for r in analysis.roles.decisive],
            "diagnostic_tests": sorted(analysis.roles.diagnostics),
            "deferred_tests": list(analysis.deferred),
            "required_diagnostics": list(discovery.required_diagnostics),
            "missing_diagnostics": list(analysis.roles.missing_diagnostics),
            "diagnostics_complete": analysis.roles.diagnostics_complete,
            "survived_meaning": discovery.survived_meaning,
        },
    }


SDE_NOTE = (
    "the candidate's `sde` is the stage-1 SDE of the per-sector peak that seeded it (with a "
    "kept period at a multiple of the seed's, not the SDE of the kept peak); `sde_kept_peak` is "
    "the SDE of the kept period itself, computed for this report after the selection (#186)"
)


def v05_record(analysis: Analysis, data: TessData, plan: TessTestPlan) -> dict[str, Any]:
    """The v0.5 fields of ``verdict.json`` (docs/plans/v0.5-acceptance.md, WP6): the claim's
    discovery version and rule, the period, its error and the epoch from one fit, the cadences
    used per sector, the holdout train ephemeris against the candidate, and the SDE label."""
    candidate = analysis.gauntlet.candidate
    ephemeris = analysis.gauntlet.ephemeris
    cadence = plan.data.exptime_seconds / 86400.0
    sectors = {}
    for info in data.sectors:
        used = int(np.sum(data.lc.sector == info.sector))
        expected = max(1, int(round((info.t_end - info.t_start) / cadence)))
        sectors[str(info.sector)] = {
            "cadences_used": used,
            "cadences_in_span": expected,
            "fraction_used": used / expected,
        }
    if ephemeris is not None:
        params = {
            "source": "linear ephemeris fit of the transit times (one fit)",
            "period_days": ephemeris.period,
            "period_err_days": ephemeris.period_err,
            "epoch_bjd_tdb": ephemeris.t_ref + BTJD_OFFSET,
            "epoch_err_days": ephemeris.t_ref_err,
        }
    elif candidate is not None:
        params = {
            "source": "BLS search (no ephemeris fit; no uncertainties)",
            "period_days": candidate.period,
            "period_err_days": None,
            "epoch_bjd_tdb": candidate.t0 + BTJD_OFFSET,
            "epoch_err_days": None,
        }
    else:
        params = None
    rounds = []
    for r in analysis.holdout.rounds:
        train = r.metrics.get("train_candidate") or {}
        match = None
        if candidate is not None and train.get("period"):
            rel = abs(train["period"] - candidate.period) / candidate.period
            offset = (train["t0"] - candidate.t0) / candidate.period
            phase = abs(offset - round(offset)) * candidate.period
            match = bool(rel <= 0.01 and phase <= 0.5 * candidate.duration)
        rounds.append(
            {
                "hidden_year": r.hidden_year,
                "train_matches_candidate": match,
                "train_period_days": train.get("period"),
                "depth_consistency_sigma": r.metrics.get("depth_consistency_sigma"),
            }
        )
    from refute.packs.tess.search import kept_peak_sde

    return {
        "discovery_version": 3 if plan.is_v051 else 2,
        "sensitivity_rule": "refute.core.sensitivity.enforce_sensitivity (#185)",
        "parameters": params,
        "sde_kept_peak": None
        if candidate is None
        else kept_peak_sde(analysis.flattened_search, candidate, plan.search),
        "sde_note": SDE_NOTE,
        "cadences_per_sector": sectors,
        "holdout_rounds": rounds,
    }


ALIAS_FACTORS = (("P", 1.0), ("2P", 2.0), ("P/2", 0.5), ("3P", 3.0), ("P/3", 1.0 / 3.0))


def matching_factor(
    published: float | None,
    found: float | None,
    factors: Sequence[float],
    tolerance: float,
) -> float | None:
    """The first factor ``f`` with ``|found - f * published| / (f * published) <= tolerance``
    (inclusive), or None. Missing or non-positive periods match nothing."""
    if published is None or found is None or published <= 0:
        return None
    for factor in factors:
        if abs(found - factor * published) / (factor * published) <= tolerance:
            return factor
    return None


def period_comparison(
    published: float | None, found: float | None, tolerance: float | None
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "published_period_days": published,
        "found_period_days": found,
        "relative_error": None,
        "tolerance": tolerance,
        "within_tolerance": None,
        "alias": None,
    }
    if published is None or found is None or published <= 0:
        return out
    out["relative_error"] = abs(found - published) / published
    check = tolerance if tolerance is not None else 0.001
    names = {factor: name for name, factor in ALIAS_FACTORS}
    factor = matching_factor(published, found, [f for _, f in ALIAS_FACTORS], check)
    if factor is not None:
        out["alias"] = names[factor]
    if tolerance is not None:
        out["within_tolerance"] = out["relative_error"] <= tolerance
    return out


def data_manifest(data: TessData) -> dict[str, Any]:
    files_by_name = {f["name"]: f for f in data.manifest.get("files", [])}
    files = []
    for sector in data.sectors:
        record = files_by_name.get(sector.filename, {})
        files.append(
            {
                "name": sector.filename,
                "sha256": record.get("sha256", sector.sha256),
                "sector": sector.sector,
                "year": sector.year,
                "t_start_btjd": sector.t_start,
                "t_end_btjd": sector.t_end,
                "n_cadences_used": sector.n_points,
                "url": record.get("url", sector.url),
                "data_uri": record.get("data_uri"),
            }
        )
    for record in data.manifest.get("pixel_files", []):
        files.append(
            {
                "name": record["name"],
                "sha256": record["sha256"],
                "sector": record["sector"],
                "kind": "target pixel file",
                "url": record.get("url"),
                "data_uri": record.get("data_uri"),
            }
        )
    return {
        "schema": "refute-tess-data-manifest-2",
        "target_key": data.target_key,
        "retrieved_utc": data.manifest.get("retrieved_utc"),
        "query": data.manifest.get("query"),
        "product": data.product.to_dict(),
        "files": files,
        "star": data.star.to_dict() if data.star else None,
        "neighbors": data.manifest.get("neighbors"),
        "software": data.manifest.get("software"),
    }


def data_quality_warnings(target: dict[str, Any], data: TessData, plan: TessTestPlan) -> list[str]:
    """Warnings for the report. They are not tests and never change a verdict."""
    warnings = []
    star = data.star
    catalog = target.get("catalog") or {}
    reference = None
    for key in ("sy_tmag", "TESS Mag"):
        try:
            reference = float(catalog[key])
            break
        except (KeyError, TypeError, ValueError):
            continue
    limit = plan.gauntlet.plausibility.max_tmag_mismatch
    if star is not None and star.tmag is not None and reference is not None:
        if abs(star.tmag - reference) > limit:
            warnings.append(
                f"TIC Tmag {star.tmag:.2f} differs from the target's catalog Tmag "
                f"{reference:.2f} by more than {limit:g} mag: the TIC row may describe "
                "another source"
            )
    if star is not None and star.disposition:
        warnings.append(f"TIC row disposition: {star.disposition}")
    return warnings


def build_result(
    target: dict[str, Any],
    data: TessData,
    plan: TessTestPlan,
    analysis: Analysis,
    context: dict[str, Any],
) -> dict[str, Any]:
    candidate = analysis.gauntlet.candidate
    criteria = context.get("pass_criteria") or {}
    published = target.get("published", {}).get("period_days")
    comparison = period_comparison(
        published, candidate.period if candidate else None, criteria.get("period_tolerance")
    )
    key_values: dict[str, Any] = {}
    if candidate is not None:
        key_values.update(
            {
                "period_days": candidate.period,
                "t0_btjd": candidate.t0,
                "duration_days": candidate.duration,
                "depth": candidate.depth,
                "snr": candidate.snr,
            }
        )
    for round_ in analysis.holdout.rounds:
        key_values[f"holdout_{round_.hidden_year}_snr"] = round_.metrics.get("hidden_snr")
    ephemeris = analysis.gauntlet.ephemeris
    record = {
        "schema": "refute-tess-verdict-1",
        "target_key": target["key"],
        "tic_id": int(target["tic_id"]),
        "target_kind": target.get("kind"),
        "target_name": target.get("name"),
        "status": "OK",
        "error": None,
        "verdict": analysis.verdict,
        "verdict_reason": analysis.verdict_reason,
        "candidate": candidate.to_dict() if candidate else None,
        "global_ephemeris": (
            {**ephemeris.to_dict(), "t_ref_bjd": ephemeris.t_ref + BTJD_OFFSET}
            if ephemeris
            else None
        ),
        "published": target.get("published"),
        "period_comparison": comparison,
        "tests": [t.to_dict() for t in analysis.tests],
        "holdout_rounds": [r.to_dict() for r in analysis.holdout.rounds],
        "search_diagnostics": analysis.search.diagnostics,
        "data_summary": {
            "n_cadences": len(data.lc),
            "sectors": [s.sector for s in data.sectors],
            "years": data.lc.years,
            "product": data.product.to_dict(),
            "star": star_inputs(data.star),
        },
        "key_values": key_values,
        "data_quality_warnings": data_quality_warnings(target, data, plan),
        "eb_catalog_configured": analysis.extras.get("eb_catalog_configured", False),
        "expected_tests": expected_tests(analysis.extras.get("eb_catalog_configured", False)),
        "test_plan": plan.model_dump(mode="json"),
        "provenance": {
            k: context.get(k)
            for k in (
                "claim_id",
                "claim_sha256",
                "code_sha256",
                "run_id",
                "lock_git_commit",
                "run_git_commit",
                "refute_version",
                "pack",
            )
        },
    }
    if plan.discovery is not None and analysis.roles is not None:
        # v0.4, discover claims only (records of other claims keep their keys): the method
        # status, the temporal diagnostic, the roles, the stage; the decisive expected tests.
        decisive, required = expected_by_role(
            plan, analysis.extras.get("eb_catalog_configured", False)
        )
        record["expected_tests"] = decisive
        record["required_diagnostics"] = required
        record.update(discovery_record(analysis, plan))
    if plan.v05:
        # v0.5 claims only (WP6), so the records of earlier claims keep their keys and bytes.
        record["v05"] = v05_record(analysis, data, plan)
    if plan.is_v051:
        # v0.5.1 claims only (WP4), so the records of earlier claims keep their keys and bytes.
        record["v051"] = v051_record(analysis)
    if analysis.gauntlet.timing is not None:
        # M4 piece 3 (switch on only, so records with the switch off keep their keys).
        record["global_timing"] = analysis.gauntlet.timing
    executed = list(analysis.gauntlet.executed)
    executed += sorted(
        {
            r.metrics["corrections_path"]
            for r in analysis.holdout.rounds
            if "corrections_path" in r.metrics
        }
    )
    if executed:
        # The marker of map Amendment 17: what ran, not what the plan asked for; absent on M3.
        record["corrections"] = {
            "version": plan.gauntlet.corrections.version,
            "executed": executed,
        }
        pw = analysis.gauntlet.prewhitening
        if pw is not None:  # M4 piece 7 (map Amendment 22); the trains are in the rounds
            record["corrections"]["prewhitening"] = {
                "global": pw.to_dict(),
                "search_refit_reason": pw.search_refit_reason,
                "search_left_out": pw.search_left_out,
                "refit_reason": analysis.gauntlet.refit_reason,
                "refit_left_out": analysis.gauntlet.refit_left_out,
            }
    return record


class TessSearch:
    def run(self, data: TessData, params: dict[str, Any]) -> SearchResult:
        plan = TessTestPlan.model_validate(params)
        _, searched = global_prewhitening(data, plan)  # M4 piece 7; L1 itself without it
        return search_period(searched, plan.search)


class TessGauntlet:
    def run(
        self, data: TessData, candidate: Candidate | None, target: dict, params: dict
    ) -> list[TestResult]:
        plan = TessTestPlan.model_validate(params)
        tests = attack_candidate(data, candidate, plan).tests
        if plan.v05:
            # a caller that aggregates these results directly gets the v0.5 rule too
            from refute.core.sensitivity import enforce_sensitivity
            from refute.packs.tess.power import registry_for

            tests = enforce_sensitivity(enforce_coverage(tests), registry_for(plan))
        if plan.is_v051:
            tests = classify_v051(tests)
        return tests


class TessHoldout:
    def run(self, data: TessData, params: dict[str, Any]) -> HoldoutOutcome:
        return run_holdout(data.lc, data.sectors, TessTestPlan.model_validate(params))


class TessAnalyzer:
    def analyze(
        self,
        target: dict[str, Any],
        data: TessData,
        test_plan: dict[str, Any],
        context: dict[str, Any],
        writer: Any,
    ) -> dict[str, Any]:
        from refute.packs.tess import plots

        plan = TessTestPlan.model_validate(test_plan)
        writer.write_json("data/manifest.json", data_manifest(data))
        catalog_paths = [
            writer.root / "attachments" / a["path"]
            for a in context.get("attachments", [])
            if a.get("role") == "eb-catalog"
        ]
        catalogs = load_catalogs(catalog_paths) if catalog_paths else None
        scan_paths = [
            writer.root / "attachments" / a["path"]
            for a in context.get("attachments", [])
            if a.get("role") == "eb-catalog-scan"
        ]
        catalog_scan = load_scan(scan_paths[0]) if scan_paths else None
        if catalogs is not None:
            # Reference rows of catalogs that are not redistributed are resolved from
            # the local snapshot verified before the run (prepare_claim_data).
            catalogs = resolve_references(
                catalogs, catalog_scan, Path(context.get("cache_dir", "."))
            )
        analysis = analyze_data(
            data, plan, catalogs=catalogs, catalog_scan=catalog_scan, stage=context.get("stage")
        )
        analysis.extras["eb_catalog_configured"] = catalogs is not None
        result = build_result(target, data, plan, analysis, context)
        if plan.discovery is not None:
            # v0.4 WP4 (issue #176): the duration with its uncertainty, or a justified absence.
            result["duration_estimate"] = duration_record(analysis, plan)
        result["plots"] = plots.write_all(writer, data, analysis, plan)
        return result

    def error_result(
        self,
        target: dict[str, Any],
        error: str,
        context: dict[str, Any],
        test_plan: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        criteria = context.get("pass_criteria") or {}
        record = self._error_record(target, error, context, criteria)
        if context.get("claim_kind") == "discover":
            # v0.4: the required fields are present on an error too (issue #174).
            record["method_status"] = "not_validated"
            record["method_status_reference"] = METHOD_STATUS_REFERENCE
            record["temporal_diagnostic"] = {"state": "not_run", "test": "holdout_by_year"}
            record["discovery"] = {"stage": context.get("stage"), "diagnostics_complete": False}
        if _is_v051(test_plan):
            # v0.5.1 WP4 (Codex's end-of-round review of round 4): a version-3 error record says
            # why its INCONCLUSIVE has no class, as a condition counted apart in the tallies
            condition = (
                DATA_FETCH_FAILED if error.startswith("data fetch failed") else ANALYSIS_ERROR
            )
            record["v051"] = {
                "inconclusive_class": None,
                "inconclusive_condition": condition,
                "inconclusive_classes": {},
            }
        return record

    def _error_record(
        self,
        target: dict[str, Any],
        error: str,
        context: dict[str, Any],
        criteria: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "schema": "refute-tess-verdict-1",
            "target_key": target["key"],
            "tic_id": int(target["tic_id"]),
            "target_kind": target.get("kind"),
            "target_name": target.get("name"),
            "status": "ERROR",
            "error": error,
            "verdict": "INCONCLUSIVE",
            "verdict_reason": "the analysis could not be completed (see error)",
            "candidate": None,
            "global_ephemeris": None,
            "published": target.get("published"),
            "period_comparison": period_comparison(
                target.get("published", {}).get("period_days"),
                None,
                criteria.get("period_tolerance"),
            ),
            "tests": [],
            "holdout_rounds": [],
            "key_values": {},
            "plots": [],
            "provenance": {
                k: context.get(k)
                for k in ("claim_id", "claim_sha256", "code_sha256", "run_id", "refute_version")
            },
        }

    def report(self, result: dict[str, Any], context: dict[str, Any]) -> str:
        from refute.packs.tess.report import render_report

        return render_report(result, context)
