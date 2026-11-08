**Verdict: WEAKENED, round 1 of at most 3.** The decision to close v0.5.1 as **NOT APPROVED** is supported. The record needs the following corrections, primarily for completeness and precision.

1. **Important: row 5.2 obscures the comparison and omits the v0.1 failure.**  
   [Closing record, line 42](C:/Projetos/refute/docs/validation/v0.5.1/closing-record.md:42) leaves “v0.4 and v0.5 byte-identical” unqualified. Their outputs match the **v0.5.0 calibration-lock code**, while each differs from its recorded dossier in two retrieval timestamps. The initial v0.1 reproduction also failed with current-code inputs, changing SURVIVED to REFUTED, before reproduction at its locked tag satisfied amendment 7. [Evidence](C:/Projetos/refute/docs/validation/v0.5.1/wp5/README.md:24).

   **Required change:** replace the row 5.2 summary with:
   > Complete under amendments 7 and 8. v0.1 failed reproduction with current-code inputs and was reproduced at its locked tag under the approved exception. For v0.2, v0.4 and v0.5, current outputs are byte-identical to the v0.5.0 calibration-lock code on the same inputs. Against recorded dossiers, class (i)/(ii)/(iii) differences are respectively 2/13/0, 2/0/0 and 2/0/0.

2. **Minor: WP3 (b) omits an additional failed condition.**  
   The summary correctly reports all four row 3.2 cases failing their false-failure limits. However, `3.2|20|correlated_trend` also fails `every_applicable_detectable`: **183/200 against a bound of 184**. This is separate from row 3.7’s identical numerical shortfall. [Evidence](C:/Projetos/refute/docs/validation/v0.5.1/acceptance/wp3b-result.json:67).

   **Required change:** add:
   > Row 3.2’s SNR-20 correlated-trend case also fails the detectable-fraction condition, 183/200 against 184.

3. **Important: lessons 2 and 9 need the diagnosis’s qualifications.**  
   Lesson 2 asserts that unequal treatment necessarily explains unequal scatter, although the diagnostic **does not isolate that mechanism**. Lesson 9’s “battery that cannot pass” drops the explicit condition on the unmeasured confirmation comparators. [Evidence](C:/Projetos/refute/docs/validation/v0.5.1/feasibility/strategy/README.md:141), [conditional forecast](C:/Projetos/refute/docs/validation/v0.5.1/feasibility/strategy/README.md:61).

   **Required changes:**
   - Lesson 2:
     > **Test equivalent treatment of real and pseudo-windows.** The mask asymmetry is the leading explanation of the dispersion; isolate it experimentally before adopting a correction.
   - Lesson 9:
     > **The real-binary false-positive pool is scarce.** Resolve the failed acceptances and the conditional failure forecast before spending fresh confirmation controls.

4. **Minor: the cap account leaves out two recorded allocation overruns.**  
   The aggregate **157.8/200** is consistent with the recorded subtotals. However, WP1 consumed **5.03/4 processor-hours**, and the D1 route search **12.04/10**. Both stayed below their 1.5-times stopping thresholds; neither should disappear from the closing account. [WP1 evidence](C:/Projetos/refute/docs/validation/v0.5.1/feasibility/README.md:12), [route-search evidence](C:/Projetos/refute/docs/validation/v0.5.1/feasibility/README.md:121).

   **Required change:** add those two overruns and their stopping-threshold qualification below the cap table. Retain agent-days as **not measured**. The approximately 6.2 figure bounds Claude’s share only and does not demonstrate compliance with the total agent-day cap.

5. **Minor: the calibration inventory omits built scaffolding.**  
   “Not run; no protocol, no lock” correctly describes the actual confirmation, but leaves out the built claim writer and C1′/C2′/C3′ task functions exercised by the synthetic rehearsal. [Task implementation](C:/Projetos/refute/src/refute/packs/tess/calib051/tasks.py:50), [rehearsal scope](C:/Projetos/refute/tests/test_v051_rehearsal.py:1).

   **Required change:** change the calibration row to:
   > Claim and task scaffolding built and exercised on synthetic rehearsal data; confirmation not run; no confirmation protocol or calibration lock.

6. **Minor: the real-sector statement overstates its measurement.**  
   The C2 count is **46 stars with five or more light-curve files**, while C3 counts sectors. The source also warns that sectors containing measured events can be fewer. [Evidence](C:/Projetos/refute/docs/validation/v0.5.1/feasibility/strategy/real-sectors.json:3).

   **Required change:** replace the second sentence at lines 83–84 with:
   > Group rows cover 2 to 4 sectors. Of the development references, 46/100 C2 stars have at least five light-curve files and 16/22 C3 targets have at least five sectors; these counts do not establish their measured-event sector counts.

7. **Minor: the “77 failures” expectation needs its distributional assumption.**  
   The calculation assumes perfectly calibrated **Gaussian pulls**, with 400 trials per row. It is an expectation, not a guaranteed failure count for any calibrated estimator. [Evidence](C:/Projetos/refute/docs/validation/v0.5.1/feasibility/strategy/strata.py:163).

   **Required change:** write:
   > Under the perfectly calibrated Gaussian-pull model with 400 trials per row, about 77 failures are expected across A0’s 1,548 decidable rows; 597 were recorded.

The **A0 table counts, A0.7 rule counts, A0.8 combined counts, processor-hour totals, six recorded A0 sabotage detections, row 5.3’s 260/260 reproduction, and CI’s 36.4-minute maximum** check out. The remaining work-package states are consistent with the repository.

**Independent gate session: no reason identified.** This closes an incomplete phase without approval, settles no target, and ticks no exit criterion. The record does not assert target infeasibility, imply confirmation ran, or introduce an unsupported verdict category.

No files changed, tests rerun, or prohibited directory accessed.