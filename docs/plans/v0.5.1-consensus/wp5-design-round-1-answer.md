## Verdict: WEAKENED

The packaging rehearsal follows the v0.5 lesson, and the version 3 load check is a sensible goal. Three details need correction before this is a sound WP5 design.

1. **Moderate, row 5.1 defines its test set ambiguously.** The v0.5 battery constants list decisive and diagnostic tests at [values.py](/C:/Projetos/refute/src/refute/packs/tess/calib05/values.py:88), while the old registry also contains entries outside those sets and omits `holdout_by_year` ([power.py](/C:/Projetos/refute/src/refute/packs/tess/power.py:33)). So “old registry tests” and “the v0.5 decisive set plus diagnostics” are not interchangeable.

   **Required change:** Define the expected roles explicitly as every test in `V05_DECISIVE ∪ V05_DIAGNOSTIC`, and require each to appear in exactly one role in a version 3 claim. Keep the sensitivity registration check for decisive tests as a separate condition. Include a load refusal case for a missing diagnostic as well as a missing decisive test. This matches the intent of row 5.1, “a version-3 claim with a test of the old registry missing” ([acceptance.md](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:497)).

2. **Major, item 2 does not cover the acceptance claim.** Row 5.2 calls for claims v0.1 to v0.5 on their recorded fixtures, including byte-identical verdicts, reasons, and `verdict.json` ([acceptance.md](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:498)). The proposed fixtures cover synthetic version 1 and 2 claims plus v0.1/v0.2 calibration claims, but not recorded v0.3, v0.4, and v0.5 outputs. The existing compatibility test likewise lists only the v0.1 and v0.2 calibration claims ([test_lock_compat.py](/C:/Projetos/refute/tests/test_lock_compat.py:28), [hash checks](/C:/Projetos/refute/tests/test_lock_compat.py:100)).

   **Required change:** Add recorded output fixtures for each applicable claim from v0.1 through v0.5, and compare all row 5.2 artifacts against them. Keep the resolved-claim hash checks, but do not treat synthetic claims or the current v0.1/v0.2 lock test as coverage of the missing recorded fixtures.

3. **Major, item 4 assumes `paired_chain` supplies WP4 classes when it does not.** `_outcome` enforces coverage and sensitivity, then aggregates results itself; its returned test records contain status and severity, not the WP4 class fields ([paired.py](/C:/Projetos/refute/src/refute/packs/tess/discover/paired.py:49)). Therefore the proposed C1′ path through `paired_chain` cannot support the stated claim that C1′ tallies use WP4 classifications. The WP4 `v051_record` operates on an `Analysis` object ([pipeline.py](/C:/Projetos/refute/src/refute/packs/tess/pipeline.py:647)).

   **Required change:** Explicitly classify version 3 paired outcomes before producing their `v051` records and tallies, then assert the expected per-test and verdict classes in the rehearsal. Preserve version 2 behavior so the v0.5 battery remains unchanged.

## Scope and protocol boundary

The rehearsal’s end-to-end structure is supported by the lesson: write, load, lock, and run each step on synthetic targets before freeze ([deviation README](/C:/Projetos/refute/calibration/v0.5/deviation/README.md:114)). To make the **0.5 agent-day** allocation reviewable, specify that this is a smoke rehearsal: one minimal synthetic path per C1′, C2′, and C3′ step, with local adapters for network boundaries and a temporary Git repository only for the Git-dependent path. Do not omit a step, but avoid full calibration-sized runs or scientific acceptance measurements.

The proposal does **not** establish new scientific protocol values if the values in `calib051` remain test-only scaffolding and the protocol stop still controls adoption. One correction: the plan already fixes the C1′, C2′, and C3′ **minimum sizes** ([plan.md](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:206)); labeling those sizes “provisional” conflicts with the plan. The plan leaves further protocol details to the stop ([plan.md](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:198)). Mark only rehearsal-specific scaffolding provisional, and do not change the plan’s fixed minimums without an approved plan amendment.

A separate `calib051` package and version 3 gated validation need not change the v0.4 or v0.5 batteries. Preserve that boundary in the implementation and compatibility fixtures.

