**Verdict: WEAKENED. Round 2 of at most 3.**

Original objections **3, 4, 5, 6 and 9 are answered**. In-memory checks confirmed that pooled cancellation, zero alternative power, undefined required cells, and metadata mismatches no longer produce a recommendation. The narrowed period question is explicitly flagged, the pseudo estimator is correctly distinguished, and provenance is improved.

Objections **1, 2, 7 and 8 remain partially open**. No new estimator-routing or patch-restoration defect was found. Reviewed fingerprint: `c03bd6a5df242249`.

1. **HIGH: Pseudo-ephemeris affordability does not constrain selection, and incomplete repeats can pass.**

   **Evidence:** [Affordability calculation](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2_matched.py:670) is disconnected from [eligibility](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2_matched.py:687). Complete fixtures selected `pseudo_ephemeris` with:
   
   - `affordable=false`, at 6 seconds per curve.
   - `affordable=null`, with no repeat pairs.
   - `affordable=true`, using only **1 of 120 scheduled repeat pairs**.

   Filtering truthy `pseudo_repeat` values silently removes unsuccessful precision measurements.

   **Exact change required:** Require `affordable is True` before `pseudo_ephemeris` can qualify. Validate repeat outcomes against the prescribed first five curves of every null cell. Missing repeats must leave precision unestablished unless a coverage requirement and missingness rule are explicitly frozen. An undefined required precision statistic must produce the stated NOT ESTABLISHED result.

2. **HIGH: Validation still allows crashes instead of the promised NOT ESTABLISHED output.**

   **Evidence:** [_validate](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2_matched.py:533) does not validate timing or repeat fields. Reproduced cases included:

   - Missing `timing`: validation passed, then summary raised `KeyError`.
   - `pseudo_repeat=[0,1]`: validation passed, then `math.log` raised `ValueError`.
   - Invalid CPU text: validation recorded a reason, but [output construction](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2_matched.py:651) still converted it and raised.
   - `[1e308,1e-308]`: accepted as a valid result, although its pull is infinite.

   **Exact change required:** Validate required containers, timing keys and finite nonnegative values, positive repeat errors, applicable repeat identities, positive finite depth, and finite derived pulls. Reject Boolean numeric substitutes. After structural failure, construct the failure report without converting or aggregating invalid fields. Preserve named reasons and serialize strict JSON successfully.

3. **HIGH: The budget detects overspending after execution but still does not enforce the hard cap.**

   **Evidence:** [runlib’s dispatch](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/runlib.py:109) uses historical mean costs, without enforcement during the probe or an executing batch. A mocked 2.5-second cap allowed a three-second unit to finish before reporting over-budget.

   The new over-budget state and E2’s rejection of non-complete states correctly fix the reporting side. The 5% reserve does not guarantee prevention.

   **Exact change required:** Enforce aggregate worker CPU during execution, reserving monitoring and termination overhead. Retain actual-spending checks after every batch, including the last, and the NOT ESTABLISHED gate for capped or over-budget runs.

4. **MEDIUM: A valid zero matched difference is still discarded.**

   **Evidence:** [_odd_even](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2_matched.py:185) still reconstructs the error as `abs(diff)/z` and returns `None` when `z=0`. A stubbed successful production result with equal depths and positive uncertainty reproduced this. Fixing `_valid([0,error])` does not fix the extraction.

   **Exact change required:** Obtain the actual combined difference variance from the measurement calculation and retain `[0, positive_error]`. Do not replace it with the sum of marginal variances, which could omit covariance.

5. **MEDIUM: Repeat timing underestimates the ordinary pseudo-estimator cost.**

   **Evidence:** [Timing](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e2_matched.py:392) divides the entire repeated calculation by two. That calculation performs the real-ephemeris difference once and the phase dispersion twice. If their costs are \(R\) and \(S\), it records \(R/2+S\), whereas an ordinary evaluation costs \(R+S\).

   **Exact change required:** Time the real difference plus first phase set as the ordinary estimator evaluation. Record the second phase set separately as precision-validation overhead. Use ordinary evaluation timing for the five-second qualification gate.

All checks were read-only and in memory. No experiment units ran, no files were written, and the prohibited directory was not accessed.