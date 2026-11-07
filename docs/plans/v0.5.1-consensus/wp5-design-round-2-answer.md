## Verdict: SURVIVED

The three round-one objections are resolved. **I found no additional design blocker** for the code work.

## Objections

1. **Row 5.1, resolved.** The revised rule names the expected set directly as `V05_DECISIVE ∪ V05_DIAGNOSTIC`, requires a claim role for every test, and keeps the decisive-test registry check separate. It also requires refusal cases for a missing decisive test and a missing diagnostic, while leaving version 2 unchanged. That matches the battery definition in [calib05/values.py](/C:/Projetos/refute/src/refute/packs/tess/calib05/values.py:88) and the version-3 load-time requirement in [v0.5.1-acceptance.md](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:497).

2. **Row 5.2, resolved.** The archived-dossier re-execution covers one published record from each version, v0.1 through v0.5, addressing the gap left by synthetic fixtures and the existing v0.1/v0.2-only compatibility test. Preparing the script and procedure without running them respects the required maintainer approval stop. This matches the acceptance row and the plan’s historical-claims requirement: [acceptance.md](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:498), [plan.md](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:32).

3. **Row 5.4, resolved.** The revised design explicitly adds version-3 classification after deferral, per-test class and source records, verdict class or condition, and assertions for classes and tallies. That addresses the gap in the current `_outcome`, which aggregates without WP4 classification: [paired.py](/C:/Projetos/refute/src/refute/packs/tess/discover/paired.py:49), [pipeline.py](/C:/Projetos/refute/src/refute/packs/tess/pipeline.py:622). **Implementation should use the existing WP4 `v051` field shape** so the tallier can consume it: [pipeline.py](/C:/Projetos/refute/src/refute/packs/tess/pipeline.py:647), [inconclusive.py](/C:/Projetos/refute/src/refute/core/inconclusive.py:121).

## Scope and boundary

The smoke rehearsal covers each required step while limiting work to minimal synthetic paths, consistent with the packaging lesson in [the v0.5 deviation README](/C:/Projetos/refute/calibration/v0.5/deviation/README.md:114). Using the plan’s C1′, C2′, and C3′ minimum sizes as fixed values does not set the remaining protocol details, which stay at the later stop: [plan.md](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:198), [plan.md](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:206).

This was a read-only design review. I did not run tests or validate implementation behavior.

