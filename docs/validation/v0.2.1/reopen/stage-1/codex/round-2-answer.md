OBJECAO: The revisions resolve most findings, but **three narrow specification issues remain**.

1. **AC1 still needs a complete piecewise definition.** Its applicability conditions include all-zero variances, making the stated SNR formula divide by zero. Its fallback also requires NaN where a quantity was never computed and must remain `None`. [instrumentation-acceptance.md:74](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/instrumentation-acceptance.md:74).

   Specify:
   - Uncomputed predicted error/SNR: `None`.
   - Computed zero predicted error: error `0`, SNR `NaN`.
   - Formula comparison: non-empty grid, valid variances and a positive computed denominator.
   - Computed invalid variance: follow the existing NaN behavior.

   This matches [holdout.py:1234](C:/Projetos/refute/.cache/wt-merge-check/src/refute/packs/tess/holdout.py:1234), [holdout.py:1493](C:/Projetos/refute/.cache/wt-merge-check/src/refute/packs/tess/holdout.py:1493) and the hidden-noise stop, where `e_pred_2` remains uncomputed.

2. **The stopping matrix omits the post-window validity rejection.** The generic candidate-rejection row says ephemeris and timing uncertainty are `None`. However, `train_validity(..., windows, hidden_spans)` can reject the predicted-window fraction **after** fitting the ephemeris and computing `max_sigma_t`. Those values already exist and are returned. [instrumentation-acceptance.md:56](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/instrumentation-acceptance.md:56), [holdout.py:1094](C:/Projetos/refute/.cache/wt-merge-check/src/refute/packs/tess/holdout.py:1094).

   Add explicit rows for no training data, no candidate, insufficient transit times, and post-window validity rejection. For the last case, all four diagnostic fields are set, while capacity fields remain `None`. Include these branches in AB3 and AC5.

3. **C6 needs an explicit read boundary.** The corrected same-round comparison is right, but “every decision taken before the windows are read” can still include decision 2. That decision follows hidden replica reads and may legitimately change when hidden flux changes, before transit-window measurement. [spec-b-target-pass.md:73](C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/reopen/stage-1/spec-b-target-pass.md:73), [holdout.py:808](C:/Projetos/refute/.cache/wt-merge-check/src/refute/packs/tess/holdout.py:808).

   Restrict the invariant explicitly to **train-only preparation and decisions made before hidden-data reads**. State that hidden-noise estimation and decision 2 may change after replica reads.

**The other revisions close my previous findings:** A’s objective and operational classes, fixed metric roles, B’s completeness and denominators, elementwise source checks, mutation witnesses, and the experiment dependencies.

The revised cost arithmetic checks out: **4.7125 h**, **1.5316 h**, **67.1531 h** and **33.2231 h** for the respective X2/X3/X5 sizes. Approximately 9,500 is an appropriate rounded planning figure for the calculated 9,534 targets.

This remains a document review. No files changed or studies ran; calibration, pilot and main study remain unauthorized. The final decision remains the maintainer’s.

