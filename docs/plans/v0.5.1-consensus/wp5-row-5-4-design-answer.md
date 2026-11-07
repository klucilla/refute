## Verdict: SURVIVED

**No open design objections.** The rehearsal scope matches row 5.4 and the passed WP5 design: it uses a separate `calib051` package, minimal synthetic paths for each step, temporary Git state, and local synthetic data. The plan explicitly defers pools, draws, and replacement rules to the calibration protocol stop, so leaving those protocol-dependent paths for a later rehearsal is acceptable. [Acceptance row 5.4](</C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:518>), [WP5 round 2 answer](</C:/Projetos/refute/docs/plans/v0.5.1-consensus/wp5-design-round-2-answer.md:1>), [Plan sections 5–6](</C:/Projetos/refute/docs/plans/v0.5.1-plan.md:190>)

## Checks to preserve in implementation

1. **Important, packaging path.** The v0.5 S4 lesson calls for exercising claim creation, loading, locking, and execution on synthetic targets. The proposal covers that lifecycle and includes the locked-claim CLI path. Keep the synthetic substitution at the network adapter boundary: it must not bypass claim schema validation, attachment resolution, or cache-path handling. Assert that the generated claim includes the required reproduction and catalog data, and that the local cache is resolved through the production path. [S4 deviation and lesson](</C:/Projetos/refute/calibration/v0.5/deviation/README.md:114>)

2. **Minor, cross-platform evidence.** Taking #212 as stated, limit cross-platform comparisons to candidate, verdict, and test statuses. Record those fields explicitly; do not treat platform-dependent full outputs as matching evidence.

These are implementation conditions, not design blockers. The proposed cut is consistent with the plan’s explicit protocol stop. This is a design review only, not evidence that the rehearsal has been implemented or passed.

