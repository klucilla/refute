**A related limit from the v0.5.12 gate: F1 with a trapezoidal transit at very high SNR**

This comes from the v0.5.12 gate review, minor finding 8. The review is stored unchanged in [`docs/gates/v0.5.12-review.md`](https://github.com/klucilla/refute/blob/main/docs/gates/v0.5.12-review.md), section 3, row 8. The maintainer's decision is #218 comment 7202383280, item 1.

**The finding** (an English rendering of the review's Portuguese text):

> By the oracle of the corrected rule, F1 rejects trapezoids of **equal** depths when the noise is very low.
> - C05 has OE_box 396.2.
> - The giant's case with sigma 1e-7 gave OE_box 44, "on the cadence sampling alone". That case was moved to sigma 5e-5 "so that F1 passes", and this is written only in a tolerance label (`step2/cases.json:20`; `step2/cases_build.py:781-784`; commit `beb4fa9`).
> - The null of M1 and M2 is a box on F1's exact mask, which by construction does not measure this effect.
> - C06's tolerance (1e-3, "about seven standard errors") is none of the charter's classes (`charter.md:268-272`: five standard errors, if justified).
>
> From the scale of the two numbers, the threshold would be a depth/sigma ratio of thousands per cadence in one sector (the reviewer's own exploratory estimate). That is outside the usual regime, but the limit is declared nowhere.

**The review's suggested correction:**
- record the null rate of F1 with a realistic transit shape at high SNR as an open item;
- justify or correct C06's tolerance.

It is recorded here beside the correlated-noise limit, as another condition under which F1's null rate is not yet established. Nothing is corrected in `src/`.

Labels: `exploratory`, `method_status: not_validated`.
