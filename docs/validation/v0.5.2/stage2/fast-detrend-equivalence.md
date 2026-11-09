# v0.5.2 stage 2: the faster code's equivalence criteria, frozen before the evaluation

Section 8 of the [design](../../../plans/v0.5.2-stage2-design.md) allows faster code only with the same numbers, under tolerances frozen before the evaluation.
`method_status: not_validated`.

**Revision 2, frozen before its own run.** The first evaluation ([`fast-equivalence-r1.json`](fast-equivalence-r1.json), kept) passed, on the code of commit `d94bef3` and on the narrow scope of revision 1. Codex's
review of that round was `REFUTED`: the batched code could still differ at the final upper clip and on poorly conditioned windows, the comparator could not see a finite against a non-finite value, and the scope omitted paths the
implementation needs. Those were corrected, the batched fits were split into small blocks (a measured slowdown with many workers), and the code changed, so **the evaluation is run again**, as a new evaluation of the corrected code. The
tolerances of revision 1 are unchanged; the rows and paths marked "revision 2" are added, all stricter. The first result decides nothing about the new code.

**Revision 3, frozen before its single run.** Revision 2's evaluation ([`fast-equivalence-r2.json`](fast-equivalence-r2.json), kept) **failed**: `production_identical`, in 3 of 24 runs, because the epoch label `worst_event` of
`event_consistency` differed (events of one sector and stratum share their error, so their powers tie and `argmin` follows the rounding). Every status, class and other number was inside the tolerance. That failure stands: revision 2's code is not admitted, and by its text the reference code would stay.
The criterion was not changed. With Codex's judgement ([round 2](../../../plans/v0.5.2-consensus/stage2-impl-round-2-answer.md)), the **code** was changed: version 4 chooses that label stably (`battery_v52.stable_consistency_label`: the earliest epoch whose power is within 1e-9, relative, of the
minimum), in both comparison paths, while the block's probability stays the minimum power; versions 2 and 3 are untouched. A knot whose kept cadences span less than a quarter of the window now also goes to the reference (Codex's finding: the rescaled system hid the reference's own conditioning).

**The rule of this revision:** the corrected code is committed, the tie convention above and the fresh seeds below are fixed, and the evaluation is run **once**. If any row fails, the reference code stays in the production path, the budget is priced at its cost, and the work stops for the maintainer. There is no fourth run. The three runs where revision 2 failed are run again as
regression cases, reported apart, and are not counted as fresh evidence.

**What is compared.** `detrend_fast.detrend`, `detrend_fast.MaskAwareDetrender` and `detrend_fast.AdditiveDetrender` against `detrend.detrend` and `battery.additive_residuals`, `rednoise_fast` against `rednoise`, on the same inputs.

**The set** (development seeds of the label `refute-v052-dev:fast-equivalence-r3`; 1,200 curves):

- Noise models white, correlated, long and correlated with a trend; 2, 3 and 4 sectors; kinds full and partial; 50 curves per cell, each under the candidate's real mask.
- Each curve also under each of the four comb masks of A0 version 4, through the reuse of `MaskAwareDetrender`.
- Constructed cases, in the unit tests: a residual placed on the clipping threshold, a cadence placed on the final upper-clip boundary, a window with too few cadences, a poorly conditioned window, a constant flux, a non-finite flux.

**The criteria, all on every curve:**

| Quantity | Requirement |
|---|---|
| Cadences kept (time array) | byte-identical |
| Flattened flux and flux error | maximum absolute difference at most 1e-11 |
| `rednoise_fast` runs and bins | identical index arrays |
| `rednoise_fast` estimates (sigma_w, sigma_n, sigma_r2, beta, excluded flag, bin count) | excluded flags and bin counts identical; values within 1e-11 |
| Finite against non-finite (revision 2) | identical classification of every compared value; any difference fails, and a non-finite value is never absorbed by a maximum |

**End to end,** on the first 15 curves of each cell of the set (360 curves), the A0 measurement of [`a0_v4`](../../../../src/refute/packs/tess/a0_v4.py) through the fast code and through the reference code, **with the phase-0.5 windows both kept and excluded (revision 2)**:

| Quantity | Requirement |
|---|---|
| Availability: which windows and events are measured | identical |
| Strata, branch choices and the shortcut's decisions | identical |
| Covariance validity (a group statistic with or without a calibrated error) | identical |
| Depths and errors of events and groups | maximum absolute difference at most 1e-9 |
| A fixed decision on each group statistic (absolute pull at or above 3) | identical |
| The additive path, on a difference series of the same curve (revision 2): measured or not, events, mean and error | identical availability; values within 1e-9 |

**The production path (revision 2).** `analyze_data` with a version 4 plan through the fast code and with every faster component replaced by its reference, on the eleven named scenarios of `synthetic.SCENARIOS`, with the fresh seeds 13 and 14 (revision 2 used 3 and 4), and on two of them with the corrections active (the global refit inside the preprocessing). On every test:
status and INCONCLUSIVE class identical, and every numeric metric within `1e-7 max(1, |a|, |b|)`, with identical finite classification.

**A failure of any row keeps the reference code in that path**, recorded, and the cost goes into the budget at the reference code's price. No tolerance is changed after the evaluation.

**What this does not establish.** Equivalence on these sets, not for every input; the fallbacks are what protect the rest. Neither code is shown to be calibrated: that is the acceptance's job.
