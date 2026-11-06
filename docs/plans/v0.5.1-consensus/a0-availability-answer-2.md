## Recommendation

The new result changes my recommendation: **ask the maintainer to approve option (a)** for statistics that do not use phase 0.5. On the same 200 planets, the variant gives 100% with at least three measured events, 99.8% of events measured, and 98% with two events per parity. That addresses the availability loss much better than the earlier options. This is still development evidence, not acceptance, and needs explicit approval because it changes A0.

## Secondary-signal risk

The “inflates errors only, never toward a false PASS” claim is **not guaranteed**. A secondary signal may increase sample variance when it affects only some windows. But the sample variance is centered: a consistent offset can be removed by centering, while a phase-locked pattern can change the measured variance and lag correlations either way. Signed correlations feed group errors, so contamination can also reduce an estimated group variance or make it invalid. The covariance validity check catches invalid matrices, but not every biased yet valid estimate.

So including phase 0.5 windows can reduce binary detection power, cause INCONCLUSIVE results, or affect warning and false-pass rates. C1 planets in this measurement lack a secondary signal, but real planets can have phase-0.5 occultations or phase variations, so “planet unaffected” is not universal.

## Acceptance checks

Keep the existing A0 pull and dependence checks with the revised window rule. Add a prespecified secondary-injection case covering the relevant signal strengths and coverage patterns, and report pulls, warning/false-pass rates, and INCONCLUSIVE rates for both the ordinary planet controls and injected binaries. In particular, check group pulls and lag correlations, then verify binary outcomes at both the true period and half-period. Do not assume that an error increase automatically becomes INCONCLUSIVE; measure the actual verdict transitions.

The evidence is in [the no-phase-half availability summary](</C:/Projetos/refute/docs/validation/v0.5.1/feasibility/a0-window-availability-no_phase_half_exclusion.json>) and the [A0 window implementation](</C:/Projetos/refute/src/refute/packs/tess/a0.py>).