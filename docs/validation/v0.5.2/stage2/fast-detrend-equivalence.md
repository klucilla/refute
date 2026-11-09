# v0.5.2 stage 2: the faster code's equivalence criteria, frozen before the evaluation

Section 8 of the [design](../../../plans/v0.5.2-stage2-design.md) allows faster code only with the same numbers, under tolerances frozen before the evaluation.
This is that freeze. It was committed before [`fast_equivalence.py`](fast_equivalence.py) was run. `method_status: not_validated`.

**What is compared.** `detrend_fast.detrend` and `detrend_fast.MaskAwareDetrender` against `detrend.detrend`, and `rednoise_fast` against `rednoise`, on the same inputs.
A speed probe of one curve per sector count was run before this freeze; it measured time and printed one maximum difference, and no criterion below was chosen from it (each is at
least 100 times looser than rounding and tighter than any physical quantity in A0).

**The set** (development seeds of the label `refute-v052-dev:fast-equivalence`; 1,200 curves):

- Noise models white, correlated, long and correlated with a trend; 2, 3 and 4 sectors; kinds full and partial; 25 curves per cell, each under the candidate's real mask.
- Each curve also under each of the four comb masks of A0 version 4, through the reuse of `MaskAwareDetrender`.
- Constructed cases, in the unit tests: a residual placed on the clipping threshold, a window with too few cadences, a narrow cluster of cadences, a constant flux (zero median absolute deviation), a non-finite flux.

**The criteria, all on every curve:**

| Quantity | Requirement |
|---|---|
| Cadences kept (time array) | byte-identical |
| Flattened flux and flux error | maximum absolute difference at most 1e-11 |
| `rednoise_fast` runs and bins | identical index arrays |
| `rednoise_fast` estimates (sigma_w, sigma_n, sigma_r2, beta, excluded flag, bin count) | excluded flags and bin counts identical; values within 1e-11 |

**End to end,** on the first 5 curves of each cell of the set (300 curves), the A0 measurement of [`a0_v4`](../../../../src/refute/packs/tess/a0_v4.py) through the fast code and through the reference code:

| Quantity | Requirement |
|---|---|
| Availability: which windows and events are measured | identical |
| Strata, branch choices and the shortcut's decisions | identical |
| Covariance validity (a group statistic with or without a calibrated error) | identical |
| Depths and errors of events and groups | maximum absolute difference at most 1e-9 |
| A fixed decision on each group statistic (absolute pull at or above 3) | identical |

**A failure of any row keeps the reference code in that path**, recorded, and the cost goes into the budget at the reference code's price. No tolerance is changed after the evaluation.
