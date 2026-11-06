## A0 verdict: WEAKENED

The round 1 fixes are present: scaling is gone; the minimum is an effective count; group calibration is specified across noise, coverage, and sector-count strata; unequal-event patterns are fixed; and A0.6’s autocorrelation band is descriptive, with the pull rows as the gate. The rule also says an uncalibrated error cannot support a decisive result.

One critical formula issue remains, so I cannot recommend adoption yet.

1. **Critical, the stated sample-variance identity still omits the finite-sample autocorrelation weights.** For a sample of size `n`, the exact expectation under a stationary process whose autocorrelation vanishes beyond lag 5 is:

   `E[s²] = σ² [1 − (2/(n−1)) Σ_{k=1..5}(1−k/n)ρ_k]`

   The text instead uses `n − n/n_eff`, where its `n_eff` uses an unweighted sum of autocorrelations. That is the large-`n` approximation; it is not the stated exact identity for finite `n`. Because the rule permits an effective count as low as 10, the text should not rely on the approximation without validating it.

   **Exact text change:** Replace both the A0 provenance row and the A0 per-event formula with the finite-sample version. For example, define  
   `n_eff = n / [1 + 2 Σ_{k=1..min(5,n−1)}(1−k/n) max(0,r_k)]`, and use `sigma_i² = s_i² (n−1)/(n−n/n_eff)`. Describe this as an estimator using positive-part autocorrelations, rather than claiming the exact expectation identity for arbitrary autocorrelations. Keep the per-stratum pull rows as its acceptance gate.

2. **Important, A0.4 is missing from the explicit calibration-failure rule.** A0.4 is the dedicated check for different sector noise, but the rule names only A0.1, A0.2, and A0.5 as pull rows that invalidate errors. Also, A0.4 does not specify the full group strata or the pull bands.

   **Exact text change:** In the bold failure rule, change `(A0.1, A0.2, A0.5)` to `(A0.1, A0.2, A0.4, A0.5)`. In A0.4, specify the group strata and require the same pull bands as A0.2 in each one.

Once those two points are corrected, the round 1 objections appear resolved in the acceptance text. I have no additional objection to the no-scaling design or to the stated INCONCLUSIVE/diagnostic fallback.

## Other shifted-ephemeris dependencies

In the acceptance document, the only remaining operative use of the **old shifted ephemerides** is `duration_excess`’s `sigma_T` measurement. The other matches are historical revision text. WP2 and WP3 (a) and (d) depend on A0’s errors, but their text points to A0’s pseudo-events or errors generally; I found no remaining dependency on the old shifted-ephemeris method in those sections. Since you’ve agreed to make `duration_excess` diagnostic by the maintainer’s decision, I see no additional old-shift dependency there that requires another maintainer decision.

The A0 formula and A0.4 changes above remain within the round 2 review; I have not changed any files. This is a read-only review of the current acceptance text.

