**B is valid conditionally as a new development revision. A remains binding on the failed revision-2 run. C is inadmissible under the stated rules.**

B repairs an implementation without relaxing the equivalence requirement, provided that:

- **Only the diagnostic label changes.** Keep `min(powers)` as the decisive sensitivity probability. Selecting a nearby event must not substitute its higher probability. For example, replacing `0.9499999998` with `0.95` could create a false PASS.
- Apply the same documented label convention to both version-4 comparison paths. Preserve versions 2 and 3, thresholds, statuses and classes.
- Freeze the corrected code, tie convention, fresh seed schedule and single third-run rule before execution. Changing `LABEL` alone does **not** refresh production scenarios: [fast_equivalence.py:39](C:/Projetos/refute/docs/validation/v0.5.2/stage2/fast_equivalence.py:39) fixes their seeds separately.
- Retain both earlier results with their original dispositions. Treat the three failing scenarios as regression cases, not fresh evaluation evidence.
- Fix the independent defects below before that evaluation. If it fails, apply A without another unplanned retry.

Until a new revision passes, the production-path failure requires reference-code pricing and the stated budget STOP. The label’s lack of decision influence does not retrospectively pass revision 2.

**Commit `3b08639`: REFUTED**

1. **Rescaling bypasses the reference’s numerical-rank behavior on narrow windows.** [detrend_fast.py:108](C:/Projetos/refute/src/refute/packs/tess/detrend_fast.py:108), [detrend_fast.py:118](C:/Projetos/refute/src/refute/packs/tess/detrend_fast.py:118)  
   Reproduced with default parameters, `time = 100 + linspace(0, 1e-7, 60)`, and `flux = 1 + default_rng(22).normal(0, 5e-4, 60)`. The rescaled system passes conditioning checks and invokes no knot fallback. Both paths retain 60 cadences, but flattened flux differs by approximately **`1.56738e-4`**, versus the frozen `1e-11` tolerance. Conditioning the rescaled system does not establish equivalence to `lstsq` in the reference coordinates.  
   **Smallest correction:** restore a narrow-span reference fallback, or additionally guard the reference design’s conditioning and effective rank. Add this constructed case before freezing the next revision.

2. **The expanded compatibility recorder cannot run as committed.** [compat_v3.py@3b08639:64](C:/Projetos/refute/docs/validation/v0.5.2/stage2/compat_v3.py:64)  
   `record()` accesses `g.final` and `g.flat`, while `GauntletOutcome` defines `candidate` and `flattened`. Calling the committed recorder reproduces `AttributeError: 'GauntletOutcome' object has no attribute 'final'`; therefore it cannot produce the expanded compatibility evidence. The working-tree correction is outside this commit.  
   **Smallest correction:** commit the existing attribute-name fix, then execute the expanded comparison against both source revisions and retain its paired results.

