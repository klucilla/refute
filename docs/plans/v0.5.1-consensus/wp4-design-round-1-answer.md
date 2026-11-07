# Verdict: **WEAKENED**

The proposal has the right compatibility boundary in principle: annotate only version 3, keep shared v0.4/v0.5 test functions unchanged, and verify historical outputs byte-for-byte. I found two classification problems and one ordering bug that would leave some version-3 INCONCLUSIVE results without a class.

# Objections

1. **High severity: Stage deferral is misclassified as `outside_domain`.**  
   The acceptance defines `outside_domain` as a declared domain excluding the candidate before data are read. Stage deferral means the test was not run at that stage; it does not exclude the candidate from the test’s domain. The engine replaces deferred results with zero-coverage INCONCLUSIVE results, which fits the acceptance’s `not_enough_data` definition. Evidence: [v0.5.1-acceptance.md](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:481), [verdict.py](/C:/Projetos/refute/src/refute/core/verdict.py:157).  
   **Required change:** Classify deferred tests as `not_enough_data`, with source `stage`. Reserve `outside_domain` for a declared domain rule that excludes the candidate before reading data.

2. **High severity: The proposed classification pass runs before deferral discards its metrics.**  
   `conclude_analysis` applies coverage and sensitivity rules, then calls `defer_tests`. For deferred tests, `defer_tests` constructs a new `TestResult` without copying the original metrics. A class added immediately after the enforcement rules is therefore lost for these results. Evidence: [pipeline.py](/C:/Projetos/refute/src/refute/packs/tess/pipeline.py:583), [verdict.py](/C:/Projetos/refute/src/refute/core/verdict.py:167).  
   **Required change:** Ensure the final version-3 classification pass runs after `defer_tests`, or have the version-3 deferral path assign its class as it creates the replacement result. Keep `TessGauntlet.run` classification for its direct callers.

3. **Medium severity: The verdict-class rules assign semantic classes to workflow failures.**  
   A missing expected test is not necessarily a missing scientific input. It can indicate a plan, execution, or implementation problem. Likewise, “gate not passed” is too broad to imply `not_enough_data`; a gate can fail for other reasons. The acceptance specifies classes for inconclusive test results and requires verdict reasons and tallies to count them apart, but it does not define these two verdict-level mappings. Evidence: [v0.5.1-acceptance.md](/C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:481), [pipeline.py](/C:/Projetos/refute/src/refute/packs/tess/pipeline.py:598).  
   **Required change:** Derive any verdict-level class from the actual decisive INCONCLUSIVE test classes under the stated priority. Treat missing expected tests and failed gates as separate verdict conditions unless the acceptance explicitly assigns them a class.

4. **Medium severity: The version-3 record currently identifies itself as discovery version 2.**  
   `v05_record` hard-codes `discovery_version: 2`, while `TessTestPlan.is_v051` identifies version-3 plans. This blocks accurate version-specific reporting unless corrected. Evidence: [pipeline.py](/C:/Projetos/refute/src/refute/packs/tess/pipeline.py:748), [params.py](/C:/Projetos/refute/src/refute/packs/tess/params.py:532).  
   **Required change:** Set the value to `3` only when `plan.is_v051` is true, retaining `2` for v0.5. Use that version boundary consistently in `verdict.json`, `case.json`, and `report.md`.

# Historical byte identity

The current code gives the change a workable isolation point: `build_result` adds the v0.5 record only for `plan.v05`, and `build_case` currently projects tests to name, status, and severity. Evidence: [pipeline.py](/C:/Projetos/refute/src/refute/packs/tess/pipeline.py:945), [case.py](/C:/Projetos/refute/src/refute/packs/tess/discover/case.py:146).

Keep all added fields and report text conditional on version 3. In particular, do not add a class field unconditionally in shared serializers or alter shared test metrics. The unchanged v0.4/v0.5 byte-identity fixtures are necessary evidence for that boundary, as row 4.2 requires.

This review was read-only; I did not modify files or run tests.

