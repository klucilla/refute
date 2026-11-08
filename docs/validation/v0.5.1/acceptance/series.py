"""The series the version-3 pipeline hands to each test, for the v0.5.1 acceptance runners after
A0 (item 3 of the maintainer's decision of 2026-11-08, #208): every runner hands a test exactly
the series ``pipeline.attack_candidate`` and ``pipeline.v05_tests`` hand it, which a byte-identity
test in the suite proves runner by runner.

- ``pipeline_flat``: the flattened series of every per-event measurement (``event_noise``,
  ``per_event_depths``, A0, ``check_odd_even``, ``check_duration_excess``), built line for line as
  ``attack_candidate`` builds ``flat`` for a given candidate. The same construction as ``_flat`` of
  a0.py (A0's second run), which stays as it ran.
- The raw curve itself (``data.lc``) for the tests the pipeline calls on it (``check_sinusoid``,
  ``check_period_alias``).

Scope (as A0's proof): the series for a fixed candidate; the pipeline's refined candidate
(``finalize_candidate``) is not claimed equal to the declared one.
"""

from __future__ import annotations


def pipeline_flat(raw, cand, plan):
    """The candidate's transits masked (half-width ``transit_mask_half_width_durations``
    durations), the global components of the corrections refitted on the raw curve with that mask
    and subtracted first when the corrections are active, then the plan's detrending with the
    mask."""
    from refute.packs.tess import pipeline as pl
    from refute.packs.tess import synthetic as syn

    pw = None
    if plan.gauntlet.corrections.active:
        pw, _ = pl.global_prewhitening(syn.make_data(raw, [], None), plan)
    mask_half = plan.detrend.transit_mask_half_width_durations * cand.duration
    mask = pl.transit_mask(raw.time, cand.period, cand.t0, mask_half)
    curve = raw
    if pw is not None and pw.components:
        fitted = pl.refit(raw, pw.components, mask, plan)
        if fitted.reason is None:
            curve = pl._minus(raw, fitted.model)
    return pl.detrend(curve, plan.detrend, mask=mask)


def event_measurements(flat, cand, plan):
    """The red-noise error model and the per-event depths at phases 0 and 0.5, as ``v05_tests``
    computes them on ``flat``: (noise, events, events_half)."""
    from refute.packs.tess import pipeline as pl

    gp = plan.gauntlet
    cadence = plan.data.exptime_seconds / 86400.0
    noise = pl.event_noise(flat, None, cand.period, cand.t0, cand.duration, plan)
    events = pl.per_event_depths(
        flat, cand.period, cand.t0, cand.duration, cadence, gp.events, 0.0, None, noise
    )
    events_half = pl.per_event_depths(
        flat, cand.period, cand.t0, cand.duration, cadence, gp.events, 0.5, None, noise
    )
    return noise, events, events_half
