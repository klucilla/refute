**Verdict: WEAKENED, round 1.**

The negative experimental verdicts are faithfully retained: E1 **NOT ESTABLISHED**, E2 **no candidate qualifies**, E3 **NOT ESTABLISHED**. The E1/E2 tables and the worksheet’s displayed arithmetic agree with their JSON, subject to the exceptions below. The experiment scripts, designs, and source hashes match the recorded manifests.

The acceptance specification and cost worksheet still need material corrections before they support a stage-2 decision. This review made no changes or experimental runs and did not access the excluded directory.

### Numbered objections

1. **HIGH: The acceptance specification is not yet concrete enough.**

   **Evidence:** [README, acceptance procedure](C:/Projetos/refute/docs/validation/v0.5.2/stage1/README.md:109) specifies whole-curve resampling but `s / sqrt(n)` and a sample-kurtosis scale error. Those are not generally the standard errors of event-weighted statistics with correlated events and unequal contributions per curve. Whole-curve resampling preserves clustering, but does not make those formulas cluster-consistent.

   The exact simultaneous family, retention rules, independent-curve minimum, moment assumptions, treatment of degenerate resamples, and numerical validation success criteria also remain unspecified. The worksheet supplies illustrative Gaussian sizes, not those missing choices. Sabotage power is not specified.

   **Required change:** Freeze the family and sampling/retention rules; define both estimands and their curve-cluster standard errors, recomputed inside resamples. Alternatively, explicitly justify and validate a differently scaled bootstrap-root procedure. Specify minimum contributing curves, bootstrap failure handling, quantile-uncertainty handling, and numerical validation and sabotage-power requirements. Express variance bounds consistently with the sd bounds, namely **[0.81, 1.21]**.

2. **HIGH: The sequential comparison does not establish savings with preserved error control.**

   **Evidence:** The fixed design correctly has **one look**. However, [worksheet.py](C:/Projetos/refute/docs/validation/v0.5.2/stage1/worksheet.py:227) uses illustrative boundaries: `z / sqrt(t)`, `1.2z`, and `1.5z`. It neither calibrates repeated-look familywise error nor measures incorrect permission near the tolerance boundaries. A constant `1.5z` inflation is not, by itself, a confidence sequence. A confidence sequence requires coverage uniformly over time. [Howard et al.](https://arxiv.org/abs/1810.08240)

   Certification probabilities also differ: at 500 cells, approximately **90.7%, 92.6%, 97.6%, and 99.5%**. Their expected sample sizes therefore do not compare equally powered designs.

   **Required change:** Label the current results **illustrative boundary scenarios**. Replace “sequential designs save little” and “pay only where many cells are bad” with a conclusion restricted to these scenarios. Before recommending a sequential option, calibrate its error across looks, cells, parameters and tails, and compare designs at matched certification power. Preserve the current outputs as the original calculation.

3. **HIGH: The cost arithmetic is reproducible, but it does not price the specified acceptance.**

   **Evidence:** [worksheet.py](C:/Projetos/refute/docs/validation/v0.5.2/stage1/worksheet.py:344) multiplies the old schedule by **3,300/400**. Yet the old schedule uses **200, 700, 400 or 100 curves**, depending on the section, and its evaluation retains the first 400 finite **pulls**. Scaling that schedule does not establish 3,300 independent contributing curves per required cell.

   The 500-cell family is illustrative. The old result contains **3,558 entries across its main calibration-band tables**, including empty and undecidable entries. Their mapping into the new simultaneous family is missing. The proposed sector expansion, corrected implementations, reference checks, known-answer validation, sabotages, remaining acceptances, C2/C3 probes, and review reserves are not priced.

   Option B leaves required A0.5 protections diagnostic. Option C divides every section by three, although A0.7 and A0.5’s p3 construction do not contain three interchangeable coverage runs.

   **Required change:** Retain A–E as **old-grid scenario estimates**, not complete acceptance budgets. Add the actual family-to-task mapping, independent-curve counts, availability/branch allowances, chosen sector list, omitted workloads and uncertainty allowances. B cannot satisfy unchanged acceptance without a validated substitute for the required constructions. Recompute C from the tasks actually eliminated and include envelope-validation cost.

4. **HIGH: E3 contains transcription errors and overstates identifiability.**

   **Evidence:** [README, E3](C:/Projetos/refute/docs/validation/v0.5.2/stage1/README.md:65), compared with `e3-sinusoid.json` and the records:

   - The separated subset contains **430**, not **438**, planets.
   - “0.48 to 0.15 … in one cell” combines cells. SNR-20/trend is **0.478 → 0.348**; SNR-20/correlated_trend is **0.421 → 0.158**.
   - Of the 430 separated planets, **320 PASS and 110 are INCONCLUSIVE** in the built arm.
   - All 112 failures having `s < 1` establishes concentration in that category. It does not prove that every such trend “cannot be separated”. The frozen design explicitly calls this a nominal separation category.

   **Required change:** Correct both numbers, report the separated subset’s final statuses, and replace the categorical impossibility statement with: **“Failures were concentrated within one nominal frequency-resolution unit; this experiment does not establish identifiability or impossibility throughout that region.”** Keep the conflict unresolved for the maintainer.

5. **MEDIUM: The contention contrast is supported; the A0 and machine claims are too strong.**

   **Evidence:** [README, measured cost](C:/Projetos/refute/docs/validation/v0.5.2/stage1/README.md:80). At 16 workers, A0 throughput improves by **7.8–9.7 times**, while processor-seconds per unit rise by **47–99%** relative to one worker. Thus “processor-hours … not for A0” is false, and “nearly linearly” is too generous across the whole range.

   The sinusoid’s throughput peaks around four workers and then deteriorates. That supports a saturation/contention finding, with its cause unidentified. It does not establish that the machine is not the bottleneck.

   **Required change:** Say **“A0 continues scaling through 16 workers, sublinearly; the sinusoid saturates around four.”** Replace the machine conclusion with a conditional affordability statement about the probed workload and old grid. Give the sinusoid its own worker-count table rather than putting its 12-worker result under “16”.

6. **MEDIUM: C1’s extrapolation uses the wrong family weights and an unmatched historical comparison.**

   **Evidence:** [worksheet-probe.json](C:/Projetos/refute/docs/validation/v0.5.2/stage1/worksheet-probe.json:5) gives the equal-family mean of **46.977 seconds**, which produces **31.318 processor-hours**. C1 actually allocates 100 curves each to PA/PX and 200 to the other families. Weighting by those sizes gives **30.229 hours** from these measurements.

   The historical **110 seconds** was for family P. The new P measurement is **80.167 seconds**, not 47. Also, the probe executes the existing version-3 paired chain, not an implemented version-4 correction.

   **Required change:** Weight by planned family sizes. Label the estimate as a small development probe of the existing chain, qualify the 8.5-hour wall extrapolation, and compare P with P when discussing improvement over 110 seconds.

7. **MEDIUM: Budget reporting is not fully auditable.**

   **Evidence:** [README, caps](C:/Projetos/refute/docs/validation/v0.5.2/stage1/README.md:231) names `.cache/v052/cost.jsonl`, but that file is absent. The mandatory working-round ledger therefore cannot substantiate agent-day compliance.

   E1’s final JSON reports **2.482 hours**; its earlier records add **0.118 hours**, already exceeding its frozen 2.5-hour allocation in aggregate. The report states **2.66 hours** without reconciliation or naming the deviation. Batch sizing from mean cost also does not bound an executing batch’s processor-time overshoot.

   **Required change:** Reconcile experiment records, probes, timing work, initialization and summary overhead. Record the E1 allocation deviation. Supply the agent-time ledger with provenance, identifying retrospective reconstruction and unknown time honestly. Describe batch enforcement as a budget guard, not a hard maximum. The available evidence does not show a breach of the overall 12-hour cap.

8. **MEDIUM: “About 19 catalogued stars would do” converts an expectation into sufficiency.**

   **Evidence:** The T3b JSON arithmetic is correct: **856 = 63 + 793**, 22 remain unwalked, and the historical yield is **11/41**. Nineteen additions bring the expected yield to eleven only if that yield transfers. They do not establish sufficient eligible controls or reserves.

   The [sources record](C:/Projetos/refute/docs/plans/sources/v0.5.2-candidate-sources-2026-11-08.md:35) also overstates the absence of ExoFOP cross-matching: the article discusses ExoFOP planet candidates in its positional comparison, although it does not establish the required TOI-FP overlap.

   **Required change:** Say **“19 additional catalogued pool members would bring expected acceptances to eleven under the historical-yield assumption; actual sufficiency is unknown.”** Correct the source description while retaining the unknown overlap and unconfirmed catalog terms.

9. **MEDIUM: The `.cache/v04` proposal leaves known dependencies unresolved and omits much of the inventory.**

   **Evidence:** The quoted folder sizes agree with the local inventory. However, [protocol §4](C:/Projetos/refute/calibration/v0.5/PROTOCOL.md:145) and [C2 code](C:/Projetos/refute/src/refute/packs/tess/calib05/c2.py:30) explicitly read the pilot dossiers and measurement records. Their dependency is already established, rather than merely unchecked. Numerous other subdirectories receive no disposition.

   **Required change:** Mark the required pilot files **KEEP locally**, unless an authenticated restoration procedure is demonstrated before removal. Add an explicit keep/archive/delete disposition for every remaining directory and identify literal log paths. Retain the checked-manifest and prefix-guard requirements. No deletion is justified by this review.

**CI assessment:** The proposed moves are reasonable. The cited JUnit evidence supports approximately **2,007 → 1,467 local seconds**, with destination totals around **647 seconds for heavy-b** and **915 for heavy-c**. The 27-minute figure is a proportional forecast. Preserve exact test coverage and verify every OS/Python/shard job below 30 minutes after implementation.

### (a) T3b population judgment

**Qualified yes for the intended class; no for the literal frozen sampling frame.**

Keeping the **TOI FP requirement** and intersecting it with T10K’s **10,001 vetted eclipsing binaries** preserves the intended class, “TOI false positives that are catalogued eclipsing binaries”. T10K’s photometric, photocenter and human vetting supplies relevant catalog evidence. Its approximately 900,000 unvetted candidates do not. [Kostov et al., catalog description](https://arxiv.org/html/2506.05631v1)

The frozen protocol explicitly requires **TESS-EB membership**, however. T10K changes the source selection and potentially the difficulty distribution. Population-level performance is not automatically interchangeable.

**Recommendation:** Accept it as an explicit maintainer-approved sampling-frame amendment, retaining all TOI, depth, period, uniqueness, exclusion, product, identity, eight-outcome and reserve rules. Match the target TIC, preserve evaluation without catalog lookup, and report source membership separately. Do not call it the unchanged frozen T3b population or claim demonstrated distributional equivalence.

### (b) D1 margin and INCONCLUSIVE ceiling

**Keep both 0.10 conditions as provisional empirical safeguards.**

In plain terms, they permit up to **ten fewer binary rejections per 100 eligible curves**, and up to **ten additional undecided outcomes**, compared with v0.4 on those same curves. That is a meaningful concession, not proof of equivalent performance. Matching D2’s margin is consistency, not scientific justification for its optimality.

The ceiling matters independently: historical EB2 meets the proposed rejection floor, but **73 INCONCLUSIVE outcomes exceed its ceiling of 24.6**. Keep both conditions per family, alongside the original D1 requirements, and report paired uncertainty without silently changing the decision rule.