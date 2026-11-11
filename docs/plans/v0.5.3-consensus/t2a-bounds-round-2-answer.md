1. **Finding 1: retained correctly.** [t2a_bounds.py:377](C:/Projetos/refute/docs/validation/v0.5.3/stageA/t2a_bounds.py:377) preserves the valid upper bound of 1 and the above-20 scenarios. No correction needed.

2. **Finding 2: applied correctly.** [t2a_bounds.py:160](C:/Projetos/refute/docs/validation/v0.5.3/stageA/t2a_bounds.py:160) uses the adapter-normalized background directly, preserving the historical A0 units.

3. **Finding 3: applied correctly.** [t2a_bounds.py:220](C:/Projetos/refute/docs/validation/v0.5.3/stageA/t2a_bounds.py:220) includes the uninjected host multiplier and fixed sector normalizer. The normalized Fisher calculation passed an isolated synthetic check; the oracle assumption is stated.

4. **Finding 4: applied correctly.** [t2a_bounds.py:174](C:/Projetos/refute/docs/validation/v0.5.3/stageA/t2a_bounds.py:174) selects exactly **23 historical background-sensitivity losses**. Primary summaries use that cohort, other measurements are counted separately, and A0-over-sector-scatter ratios are included.

5. **Finding 5: applied correctly.** [t2a_bounds.py:370](C:/Projetos/refute/docs/validation/v0.5.3/stageA/t2a_bounds.py:370) and [t2a_bounds.py:384](C:/Projetos/refute/docs/validation/v0.5.3/stageA/t2a_bounds.py:384) explicitly distinguish measurements and conditional scenarios from bounds, including the sinusoid oracle’s limitations.

6. **Finding 6: applied correctly.** [t2a_bounds.py:275](C:/Projetos/refute/docs/validation/v0.5.3/stageA/t2a_bounds.py:275) fingerprints `forecast_v4.py`. Historical assembly remains read-only, and the ledger check remains exception-safe. T2a’s fingerprint is unchanged.

No remaining blocking implementation defect found. In-memory compilation and isolated synthetic checks passed. No pipeline was run or files edited.

**SURVIVED for the prescribed (c1)/(c2) diagnostic run under the frozen prerequisites; (c3) remains on hold.**