**Verdict: WEAKENED. Round 2 of 3.**

The rewrite correctly fixes target-harmonic counting, the required cell breakdown, concentration based solely on separation, retained-cadence geometry, trend projection, and fingerprint rejection. The exploratory 0.05 threshold is now clearly distinguished from acceptance.

Six gaps remain. Evidence below includes isolated in-memory fixtures, with no E3 execution or file writes.

1. **HIGH: FAIL-to-INCONCLUSIVE transitions still qualify as improvement.**

   **Evidence:** [The promotion comparison](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3_sinusoid.py:388) uses raw FAIL alone. A complete 1,080-unit fixture was recommended in both arms when every apparent improvement consisted of five baseline FAILs becoming final INCONCLUSIVE per planet cell. The SNR-20 detectable fraction remained `145/150`, exceeding 0.95. This contradicts the design’s “An INCONCLUSIVE never counts as a solved case.”

   **Exact change:** Keep raw-FAIL statistics for the original failure map, but add a promotion endpoint that counts **final FAIL or INCONCLUSIVE as adverse**. Require its paired improvement over `built`. Report the paired status-transition table so FAIL-to-INCONCLUSIVE cannot supply the claimed improvement.

2. **HIGH: The budget gate still permits work beyond the cap.**

   **Evidence:** [Budget checks occur after dispatch](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3_sinusoid.py:232). A mocked resume already at 1.5 CPU-hours dispatched another 88 units. The projection guard permits up to `1.5 × CAP_HOURS`, rather than the frozen cap. With `run 40`, the projection uses the truncated queue and reports zero remaining units, ignoring the rest of the schedule. Failed units also lose their elapsed CPU time in `_safe`.

   **Exact change:** Check cumulative spending before any dispatch, including resume. Project against the **entire unfinished schedule**, independently of the invocation limit. Refuse continuation when projected total exceeds 1.5 hours, size batches against the remaining budget, and account for failed-unit CPU time in `finally`. Enforce the stated hard cap for in-flight work, rather than checking only after a batch finishes.

3. **HIGH: Validation does not yet guarantee a NOT ESTABLISHED result for invalid records.**

   **Evidence:** [_validate](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3_sinusoid.py:285) checks only four numeric inputs. A non-finite fitted amplitude error passed through to EVALUATED. Removing an expected arm appended a reason, then aggregation raised `KeyError` instead of producing the promised result. Missing fields and invalid status/harmonic values have similar unchecked paths.

   **Exact change:** Validate the complete required schema before aggregation: scheduled metadata, arms, status enums, harmonic keys, applicability/detectability consistency, and finite fit/projection/separation values with valid errors. Stop decision aggregation after structural failure and emit **NOT ESTABLISHED with null recommendations**, naming the unit and arm. Keep invalid units in schedule accounting.

4. **MEDIUM: The paired bootstrap gives degenerate confidence intervals at the boundary.**

   **Evidence:** [_paired](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3_sinusoid.py:271) returns `[0, 0]` whenever all observed paired differences are zero. For 60 identical successful pairs, this automatically passes the −0.05 non-regression threshold. It supplies no uncertainty for unobserved losses. In the simple binomial-loss subcase, zero losses among 60 has a two-sided exact 95% upper bound of approximately **0.05963**.

   **Exact change:** Replace the percentile bootstrap used for binary decision endpoints with a boundary-valid paired-binomial interval, or conservative simultaneous bounds on gain and loss probabilities. Freeze the confidence convention and apply it consistently to both improvement and non-regression. Identical observed pairs must not imply zero uncertainty.

5. **MEDIUM: The near-harmonic control can still pass with no baseline detection.**

   **Evidence:** [The alternative rule](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3_sinusoid.py:425) applies an absolute detection benchmark only to exact harmonics. Both variants were recommended in the complete fixture despite **zero near-control detections in every arm**. Such a control establishes no preserved detection.

   **Exact change:** Require a prespecified baseline construction check for the near control, for example `built` target-harmonic recovery at least the existing 0.90 exploratory benchmark. If it fails, mark the near-control preservation decision NOT ESTABLISHED and block promotion. Do not filter its curves or tune the control after observing results.

6. **MEDIUM: Full sensitivity blocks are still discarded.**

   **Evidence:** [Unit records](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3_sinusoid.py:168) retain `runner._describe()["detectable"]`, which contains booleans only. They do not retain the per-harmonic sensitivity blocks promised by the revised design and requested in round 1.

   **Exact change:** Preserve `raw.sensitivity` through `_with_arm` and store its complete per-harmonic blocks, including alternative, probability, required probability and rule identity. Validate them before computing the detectable fractions.