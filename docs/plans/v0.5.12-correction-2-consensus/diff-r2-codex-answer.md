**OVERALL: SURVIVED.** The exact patch with SHA-256 `056d0814…0953` matches the working tree and is sound to commit. The round 2 changes are limited to the three requested fixes.

1. **Applied.** Production and the oracle check the red moment for finiteness before clipping it at zero. [Production](C:/Projetos/refute/src/refute/packs/tess/screen_d5.py:222), [oracle](C:/Projetos/refute/tests/v0512_oracles.py:89)
2. **Applied.** Both derive `W_par` from `np.sum(w_e)` before calculating the effective epoch count and variance. [Production](C:/Projetos/refute/src/refute/packs/tess/screen_d5.py:290), [oracle](C:/Projetos/refute/tests/v0512_oracles.py:137)
3. **Applied.** Both check the denominator first, then return the parity-specific reason for a nonpositive variance. N14 retains `denominator not positive` when both variances are zero. [Production](C:/Projetos/refute/src/refute/packs/tess/screen_d5.py:300), [oracle](C:/Projetos/refute/tests/v0512_oracles.py:145), [N14](C:/Projetos/refute/docs/validation/v0.5.12/step2/cases.json:1504)

**Recorded:** This was a static review. The 97-test result is the supplied run result.