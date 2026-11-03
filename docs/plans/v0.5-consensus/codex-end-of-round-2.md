## Round verdict: WEAKENED

Reviewed `86ec0a2..80c5468` on `main`, including the design review and acceptance revision 2. **Changes are required before acceptance.** The compatibility architecture is largely sound, but sensitivity enforcement has a bypass, several power calculations do not reproduce their declared decision rules, and parts of WP6/WP7 remain incomplete.

This was a static review. No files were modified, no pytest or scientific study was run, and no paths outside the repository were opened.

## Findings

### 1. Critical: the measurement chain bypasses sensitivity enforcement

**Location:** [discover/measure.py:47](C:/Projetos/refute/src/refute/packs/tess/discover/measure.py:47), exposed by the newly accepted discovery version 2.

`measure.chain()` accepts a v0.5 plan, calls `attack_candidate()`, then applies coverage and aggregates without `enforce_sensitivity()`. Consequently, a statistical PASS with `sensitivity=None` or `detectable:false` can reach a measurement verdict. Existing injection and transformation workers call this chain.

`conclude_analysis()`, `TessGauntlet.run()` and the new paired `_outcome()` apply enforcement correctly. No-candidate placeholders are INCONCLUSIVE, and stage deferral does not create a PASS. Those fixes do not close this remaining route.

**Fix:** apply sensitivity enforcement conditionally for v0.5 immediately after coverage in `measure.chain()`, preserving the v1 path. Alternatively, explicitly reject v2 plans there and route all v2 workers through an enforced chain. Add a sabotage case through this entry point.

### 2. Important: v0.5 can attach power to historical, white-noise event errors

**Location:** [pipeline.py:250](C:/Projetos/refute/src/refute/packs/tess/pipeline.py:250), [pipeline.py:350](C:/Projetos/refute/src/refute/packs/tess/pipeline.py:350).

The original `primary` and `secondary` measurements receive the red-noise model only when `gauntlet.corrections.active`. Discovery version 2 does not require that switch. `v05_tests()` computes new red-noise primary events, but uses them only for the new event tests. It attaches odd/even power to the original result and passes the original events into the replacement secondary test.

The provided `discovery_v05_plan_dict()` exercises precisely this configuration: version 2 with corrections inactive.

**Impact:** odd/even and secondary sensitivity can be overstated on correlated noise, contrary to WP1’s error-calibration contract.

**Fix:** recompute the v2 odd/even and phase-0.5 results from consistently calibrated event measurements, independently of the historical corrections switch. Keep candidate generation and the v1 measurements unchanged.

### 3. Important: sinusoid power simulates a different statistic

**Location:** [battery_v5.py:429](C:/Projetos/refute/src/refute/packs/tess/battery_v5.py:429).

The observed amplitude uncertainty uses the fitted cosine/sine covariance, including its off-diagonal term. The simulation then:

- draws the two coefficients independently, discarding that covariance;
- places the alternative along the cosine axis;
- divides every simulated amplitude by the uncertainty calculated from the observed coefficients.

For anisotropic or correlated coefficient errors, this is not the test’s rejection statistic under the alternative. Taking the minimum over P/2, P and 2P does not correct that mismatch.

**Fix:** draw joint coefficients using the full covariance and recompute the amplitude uncertainty and rejection statistic for each draw. Handle the alternative’s phase explicitly, with conservative treatment of eligible orientations.

### 4. Important: centroid power omits sector agreement

**Location:** [centroid_v5.py:284](C:/Projetos/refute/src/refute/packs/tess/centroid_v5.py:284), [centroid_v5.py:294](C:/Projetos/refute/src/refute/packs/tess/centroid_v5.py:294).

The real decision requires qualified sectors to agree. The power simulation draws only the already-combined mean and checks significance and distance. It never simulates individual sector offsets or applies the heterogeneity rejection.

Thus its probability is for a reduced decision rule, rather than the WP4 rule specified in the sensitivity table. Near 0.95, omitting the agreement condition can change detectable status.

There is also incomplete covariance propagation at [centroid_v5.py:170](C:/Projetos/refute/src/refute/packs/tess/centroid_v5.py:170): the pixel covariance is forced diagonal despite paired control measurements and a shared uncertain transit depth.

**Fix:** simulate the sector offsets jointly, combine each realization, and apply the heterogeneity and offset conditions together. Propagate the available cross-coordinate covariance, including the shared-depth contribution.

### 5. Important: systematics power freezes uncertain ratio denominators

**Location:** [power.py:159](C:/Projetos/refute/src/refute/packs/tess/power.py:159), [power.py:175](C:/Projetos/refute/src/refute/packs/tess/power.py:175).

For SAP versus PDCSAP, the simulation collapses uncertainty into a difference but holds `expected` fixed in the relative-difference condition. The actual relative difference uses the measured PDCSAP depth.

For background, only the background rise is drawn; the uncertain SAP depth remains fixed in the fraction condition.

These are not joint sufficient-statistic simulations of the full compound regions. The discrepancy matters when denominator uncertainty is appreciable.

**Fix:** jointly draw the underlying measured depths, with covariance where available, and evaluate the same positivity, significance and ratio branches as the actual sub-checks.

### 6. Important: pairing validation does not guarantee identical final candidates

**Location:** [discover/paired.py:34](C:/Projetos/refute/src/refute/packs/tess/discover/paired.py:34).

The v0.4 side structurally follows `measure.chain()`: the generation calls and subsequent v1 evaluation match. That supports compatibility for the supplied v0.4 plan, apart from intentionally omitting `survived_stage_tests`.

However, `check_pairing()` compares only `data`, `detrend`, `search` and corrections. Each side then independently calls `attack_candidate()`, which refinalizes the candidate and can change its gate SNR using `gauntlet.events`. Different event parameters are currently accepted.

**Impact:** the search candidate is shared, but the final candidate and gate need not be.

**Fix:** freeze and share candidate preparation, including finalization and gate measurement, or validate every parameter affecting those operations. Add a corrections-active pairing case with deliberately different event parameters. Historical per-curve/count comparisons required by plan section 4 remain outstanding; three synthetic scenarios do not establish those comparisons.

### 7. Important: injection summaries omit the required recovery conditioning

**Location:** [discover/paired.py:162](C:/Projetos/refute/src/refute/packs/tess/discover/paired.py:162), [discover/paired.py:199](C:/Projetos/refute/src/refute/packs/tess/discover/paired.py:199).

`injection_groups()` uses the generic summary, which selects gate-passing detections without examining injection recovery. A surviving detection at an unrelated period can therefore enter the injection verdict counts.

Plan section 4 requires both:

1. survival among **recovered, gate-passing injections**;
2. recovery-and-survival among **all attempted injections**.

Neither measurement is supplied here.

**Fix:** add an injection-specific summary using recovery identity, explicit attempted and recovered denominators, and separate verdict counts. Retain the current host separation. The four verdict categories, transition table, empty groups and separate transformed-curve categories are otherwise appropriate.

### 8. Important: labelling the seed SDE does not satisfy case 6.3

**Location:** [pipeline.py:624](C:/Projetos/refute/src/refute/packs/tess/pipeline.py:624), [test_v05_reporting.py:62](C:/Projetos/refute/tests/test_v05_reporting.py:62).

Recording the failure honestly and keeping #186 open is correct. Treating the replacement label test as fulfillment of 6.3 would not be correct. The stop rule permits bounded repairs to meet the frozen specification; it does not make a reporting requirement optional.

**There is a repair that preserves shared candidate generation:** freeze the selected candidate, then compute its SDE as a reporting-only measurement using an explicit periodogram reference and the existing SDE normalization. Apply this only to v2 records, after selection and battery evaluation, with no feedback into ranking or gating.

**Fix:** implement and verify that reporting-only calculation. Until then, keep 6.3 explicitly unaccepted. It cannot use the scientific-test fallback of becoming diagnostic.

### 9. Important: #188 substitutes box SNR for the specified BLS power

**Location:** [study_188.py:99](C:/Projetos/refute/docs/validation/v0.5/study_188.py:99).

The frozen specification requires BLS power at the true period. The script records `box.snr` instead. Moreover, `finalize_candidate()` searches a local period neighborhood, so this is not strictly an evaluation at the exact true period.

I recomputed the counts from the committed JSON. The Markdown accurately reports:

| Family | Without prewhitening | With prewhitening |
|---|---:|---:|
| EB-like, gate passed | 10/10 | 10/10 |
| EB-like, gate passed at true period or alias | 7/10 | 7/10 |
| Sinusoid, gate passed | 5/10 | 2/10 |

The descriptive conclusion is supported by those records, but **the study does not fully meet its specification**.

**Fix:** record the missing measurement as a deviation. Preserve the existing records. Any additional computation or rerun needs the approval required by the repository’s rerun rule, with a separate correction artifact.

### 10. Minor: remaining reporting and operating-rule gaps

- **Epoch precision:** [report.py:122](C:/Projetos/refute/src/refute/packs/tess/report.py:122) rounds to six decimals, rather than preserving `verdict.json` precision as case 6.8 requires. **Fix:** use round-trip positional formatting.
- **Unqualified-sector evidence:** [centroid_v5.py:131](C:/Projetos/refute/src/refute/packs/tess/centroid_v5.py:131) returns a reason before retaining an offset. WP4 requires an unqualified sector’s offset to be reported. **Fix:** preserve an available measurement alongside qualification reasons, or explicitly record why it cannot be measured.
- **Secondary limitations:** the eccentric-secondary and classification caveats exist in the function docstring, but are absent from the generated report. **Fix:** add them to the v2 report.
- **CPU distribution:** [study_188.py:119](C:/Projetos/refute/docs/validation/v0.5/study_188.py:119) runs the independent searches serially, contrary to CLAUDE.md’s CPU-heavy-work rule. **Fix:** use bounded process workers for future authorized execution and account for worker cost. Do not rerun this study merely to repair execution style.

## Compatibility and acceptance assessment

**Historical compatibility:** I found no demonstrated change to the standard historical resolved hashes, verdicts, reports or exporter outputs. Absent `stronger` is omitted, discovery defaults remain version 1, and reporting additions are gated. Existing synthetic `PixelData` generators retain their fields.

The adapter now creates `SkyPixelData` for historical inputs too. Standard result and manifest projections do not serialize the Jacobian, so I found no standard dossier-byte regression from that change. Generic `to_jsonable()` serialization of adapter-returned pixels would nevertheless gain a field. Byte-identical reproduction remains something to verify on recorded fixtures, and historical locked dossiers still require their recorded code provenance.

**Sensitivity rows:** odd/even and secondary alternatives, aperture ratio increment, worst-event single-event simulation, event-consistency noncentrality, conditional edge comparison, and deterministic categories broadly match the declared design. `period_alias` correctly has a trusted **0.9 requirement**, with default **45/50**. The mathematical exceptions are findings 2 through 5. WP5 registry entries do not constitute implemented or accepted WP5 tests.

**WP2 to WP4:** default domains and severities are largely correct. The qualification guard, two-sector minimum, heterogeneity check and sky-frame combination are present. Short periods yielding fewer than ten controls correctly produce nonqualification and potentially INCONCLUSIVE. Preserve and report that limitation; do not relax the frozen thresholds to rescue coverage.

**Evidence boundary:** the added tests mainly establish mechanisms. They do not establish the frozen 200-trial acceptance rates or error calibration. Those results remain pending. I also cannot establish commit-time checks, issue approvals or budget compliance from these source changes alone.

**WEAKENED:** retain the implementation, repair the enforcement and statistical-contract gaps, and keep unmet acceptance cases explicitly open.