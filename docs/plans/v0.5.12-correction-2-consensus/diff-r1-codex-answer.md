**OVERALL: REFUTED for committing this exact diff.** I verified the patch SHA-256 and matched all four hunks sets to the working tree. Three F1 implementation details need correction.

### Blocking items

1. **Check the red moment before clipping.** The patch turns a negative overflow into zero and can assess F1 despite non-finite noise arithmetic. With finite `s2 ≈ 6.67e305`, `Q₀ = 0`, three bins and `C ≈ 8e-6`, the quotient is `-inf`. Replace the clipping and guard with the following. Apply the same ordering in the oracle. [Production code](C:/Projetos/refute/src/refute/packs/tess/screen_d5.py:222), [oracle](C:/Projetos/refute/tests/v0512_oracles.py:89), [adopted guard](C:/Projetos/refute/docs/plans/v0.5.12-spec-correction-2-r1.md:195)

   ```python
   sigma_r2 = (q0 - s2 * (mu.size - 1)) / c
   if not _finite(sigma_r2):
       return None
   return s2, max(0.0, sigma_r2), m_b
   ```

2. **Compute `W_par` from the epoch totals.** The adopted rule sums `W_par,e` in epoch order. The direct cadence sum is algebraically equivalent but can round differently. In production and the oracle, compute `w_e` first, then set `w_par = float(np.sum(w_e))` before calculating `n_eff` and the variance. [Production code](C:/Projetos/refute/src/refute/packs/tess/screen_d5.py:289), [oracle](C:/Projetos/refute/tests/v0512_oracles.py:136), [adopted rule](C:/Projetos/refute/docs/plans/v0.5.12-spec-correction-2-r1.md:188)

3. **Preserve the parity guard when only one variance underflows.** A zero variance currently passes the parity check if the other variance is positive. Insert this immediately after the denominator guard, preserving N14’s documented reason when both variances are zero. Mirror it in the oracle using `_na(reason, counts)`. [Existing positivity guard](C:/Projetos/refute/src/refute/packs/tess/screen_d5.py:228), [insertion point](C:/Projetos/refute/src/refute/packs/tess/screen_d5.py:300), [N14](C:/Projetos/refute/docs/validation/v0.5.12/step2/cases.json:1480)

   ```python
   for name, var in (("odd", v_odd), ("even", v_even)):
       if var <= 0.0:
           reason = f"depth or pink noise unavailable for the {name} parity"
           return _core("not_assessed", reason, coverage, counts)
   ```

### Verified and recorded

- The positive prefix sum, direct OE numerator, metric keys and adopted SHA-256 field match revision 1. Production changes are confined to version 5’s F1 and its provenance field. F2 and U1 still use the legacy noise path, and the patch contains no versions 1–4 changes. [Prefix sum](C:/Projetos/refute/src/refute/packs/tess/screen_d5.py:214), [F1 metrics](C:/Projetos/refute/src/refute/packs/tess/screen_d5.py:303), [report-only path](C:/Projetos/refute/src/refute/packs/tess/screen_d5.py:729), [record hash](C:/Projetos/refute/src/refute/packs/tess/screen_d5.py:785)
- The `src/` tree at `98117ef` matches HEAD. The patch removes all ten recorded xfails and replaces the frozen OE assertions with oracle comparisons. The ordinal checks and legacy report-only tests are retained. This was a static review. [Before-src JUnit](C:/Projetos/refute/docs/validation/v0.5.12/step2/junit-suites-before-src.xml:1), [marker removals](C:/Projetos/refute/docs/validation/v0.5.12/step4/src-diff-proposed.patch:249), [oracle comparisons](C:/Projetos/refute/tests/test_v0511_screen.py:77)