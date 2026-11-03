**Verdict: WEAKENED (changes required).** The compatibility architecture is sound, but enforcement scope and execution wiring need clarification.

1. **Hashes: yes, conditionally.** Omitting `stronger` when `None`, retaining `discovery.version = 1`, and leaving existing defaults untouched preserves historical resolved dumps. No canonicalization or historical-lock projection change is needed.

   Other output risks remain:
   - `build_result()` embeds the plan; `TestResult.to_dict()` already omits absent sensitivity.
   - `PixelData` has no `to_dict()`. Generic `to_jsonable()` serializes every dataclass field, so `sky_jacobian=None` would leak. Also, omitting only `None` is insufficient if the adapter populates WCS for historical claims. Keep historical record projections unchanged.
   - Gate report additions, exporter fixes and manifest additions by v2. Changing any emitted file also changes dossier seals. Current `data_manifest()` uses explicit fields, so adding the in-memory Jacobian alone does not affect it.
   - Source/provenance hashes are separate from resolved claim hashes. Old locks still require their own tags.

2. **Decisive-only aggregation is correct; decisive-only enforcement is narrower than the acceptance text.** WP1 says every fatal/warning PASS requires sensitivity, while case 1.5 specifically limits load-time registry checking to decisive tests. Diagnostics never deciding does not itself exempt their PASS semantics. Either enforce registered scientific diagnostics too, or explicitly amend acceptance to exempt them. Preserve holdout semantics with a clearly labelled exemption.

3. **Wrappers are sound for compatibility, but are not sufficient proof.** Keep historical preprocessing, errors, ordering, severities, messages and serialization unchanged too. V2 needs dilution-corrected event depths and calibrated red-noise errors; attaching blocks to existing results cannot establish those requirements. Separate implementations for changed rejection rules are appropriate.

4. **Missing wiring and contracts:**
   - Make `expected_tests()` version-aware. Merely extending `DISCOVERY_TESTS` does not update completeness checking: `expected_by_role()` currently intersects roles with the old execution list.
   - Cover no-candidate placeholders, stage deferral, v2 warning severities and direct `TessGauntlet.run()` callers, which bypass `conclude_analysis()`.
   - Define applicable sub-checks explicitly. The engine currently requires every registered sub-check, including potentially inapplicable edge/sinusoid branches.
   - Special-case `period_alias`: acceptance requires **45/50**, whereas `rule_block()` uses **0.95**. Reporting `45/50` directly would incorrectly mark it undetectable.

Static review only. No files changed, no tests run, and no paths outside the repository accessed.