"""The tests of a battery version 4 claim (v0.5.2): ``pipeline.v05_tests`` with version 4's
measurements, in a path of its own so that versions 3 and earlier run unchanged."""

from __future__ import annotations

import numpy as np

from refute.core.verdict import Severity, TestResult, TestStatus
from refute.packs.tess import a0, a0_v4, power
from refute.packs.tess import battery_v5 as v5
from refute.packs.tess import battery_v51 as v51
from refute.packs.tess import battery_v51_diff as v51d
from refute.packs.tess import battery_v52 as v52
from refute.packs.tess.events import per_event_depths
from refute.packs.tess.rednoise_fast import event_noise

OUT_OF_DOMAIN_CLASS = "outside_domain"


def _refused(name: str, severity: Severity, why: str) -> TestResult:
    return TestResult(
        name,
        TestStatus.INCONCLUSIVE,
        severity,
        f"A0's errors are not available: {why}",
        metrics={"inconclusive_class": OUT_OF_DOMAIN_CLASS},
    )


def v052_tests(tests, data, flat, final, primary, secondary, plan, detrender):
    """The sensitivity blocks and tests of ``pipeline.v05_tests``, through version 4."""
    from refute.packs.tess.battery import check_period_alias
    from refute.packs.tess.pipeline import _with_a0_note

    sp, gp = plan.stronger, plan.gauntlet
    cadence = plan.data.exptime_seconds / 86400.0
    seed = power.candidate_seed
    aux = data.aux
    noise = event_noise(flat, None, final.period, final.t0, final.duration, plan)
    events = per_event_depths(
        flat, final.period, final.t0, final.duration, cadence, gp.events, 0.0, None, noise
    )
    events_half = per_event_depths(
        flat, final.period, final.t0, final.duration, cadence, gp.events, 0.5, None, noise
    )
    two_sided = v5.check_secondary_two_sided(
        events, events_half, gp.secondary_eclipse, sp, seed("secondary_eclipse", final)
    )
    exclude = two_sided.status is TestStatus.FAIL
    a0_note = "phase-0.5 windows excluded: a secondary detected" if exclude else None
    choice = v52.choose_sectors(
        flat.time, flat.sector, final, gp.events, cadence, plan.v052.selector_certified
    )
    refused = choice.refused
    measured = windows = chosen_flat = None
    if refused is None:
        chosen_flat = flat.select(np.isin(flat.sector, choice.chosen))
        chosen_events = per_event_depths(
            chosen_flat,
            final.period,
            final.t0,
            final.duration,
            cadence,
            gp.events,
            0.0,
            None,
            noise,
        )
        half = plan.detrend.transit_mask_half_width_durations * final.duration
        measure = a0_v4.comb_measure(
            detrender.flat, detrender.lc.time, chosen_flat, final.duration, half, gp.events, cadence
        )
        measured, windows, _ = a0_v4.empirical_events(
            chosen_flat, final, chosen_events, gp.events, cadence, measure, exclude
        )
        contributing = {
            a0.sector_of(chosen_flat.time, chosen_flat.sector, c) for c in measured.centers
        }
        if len(contributing) not in v52.GRID_SECTORS:
            refused = f"{len(contributing)} sector(s) contribute measured events: outside the grid"
    in_sectors = (lambda s: s in choice.chosen) if refused is None else (lambda s: False)
    pixels = [p for p in (aux.pixels if aux else []) if in_sectors(p.sector)]
    sectors = [a for a in (aux.sectors if aux else []) if in_sectors(a.sector)]
    out: list[TestResult] = []
    for test in tests:
        if test.name == "odd_even":
            test = (
                _refused("odd_even", Severity.FATAL, refused)
                if refused
                else v52.check_odd_even(
                    chosen_flat,
                    measured,
                    windows,
                    final,
                    gp,
                    sp,
                    cadence,
                    exclude,
                    seed("odd_even", final),
                )  # fmt: skip
            )
        elif test.name == "secondary_eclipse":
            test = two_sided
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
        elif test.name == "aperture_depth":
            test = (
                _refused("aperture_depth", Severity.FATAL, refused)
                if refused
                else v51d.check_aperture_depth(
                    pixels,
                    final,
                    plan,
                    seed("aperture_depth", final),
                    exclude,
                    depth=a0_v4.a0_depth,
                )  # fmt: skip
            )
        elif test.name == "systematics":
            test = (
                _refused("systematics", Severity.WARNING, refused)
                if refused
                else v51d.check_systematics(
                    sectors,
                    final,
                    plan,
                    seed("systematics", final),
                    exclude,
                    depth=a0_v4.a0_depth,
                )  # fmt: skip
            )
        elif test.name == "period_alias":
            alias_plan = power.period_alias_plan(plan)
            test = check_period_alias(data.lc, final, alias_plan)
            if test.status is TestStatus.PASS:
                blocks = power.period_alias_blocks_v51(
                    data.lc, final, alias_plan, check_period_alias, seed("period_alias", final)
                )
                test = power.attach(test, blocks)
        elif test.name == "nearby_contamination":
            test = power.attach(test, power.catalog_blocks(test, "neighbors within the radius"))
        elif test.name == "eb_catalog":
            test = power.attach(test, power.catalog_blocks(test, "catalogued eclipsing binaries"))
        out.append(test)
    if refused:
        single = _refused("single_event", Severity.FATAL, refused)
        consistency = _refused("event_consistency", Severity.FATAL, refused)
    else:
        single = _with_a0_note(
            v5.check_single_event(measured, sp, seed("single_event", final)), a0_note
        )
        consistency = _with_a0_note(v5.check_event_consistency(measured, sp), a0_note)
    out += [
        single,
        consistency,
        v5.check_edge_events(flat.time, events, final.duration, gp.snr.min_snr, sp),
        v52.check_sinusoid(
            data.lc,
            final,
            sp,
            plan.v051,
            gp.events,
            cadence,
            plan.v052.sinusoid_fail_allowed,
            seed("sinusoid", final),
        ),  # fmt: skip
        v5.check_duty_cycle(final, sp),
        v51.check_duration_excess(
            flat, final, data.star, gp, cadence, seed("duration_excess", final)
        ),
    ]
    return out
