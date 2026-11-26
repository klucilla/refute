**The independence of the #223 case oracle**

This comes from the v0.5.12 gate review, important finding 4. The review is stored unchanged in [`docs/gates/v0.5.12-review.md`](https://github.com/klucilla/refute/blob/main/docs/gates/v0.5.12-review.md), section 3, row 4. The maintainer's decision is #218 comment 7202383280, item 1(b).

**The finding** (an English rendering of the review's Portuguese text):

> Of the 130 numeric values asserted in `docs/validation/v0.5.12/step2/cases.json`, 124 have `source: oracle` and only 6 have `source: model`.
>
> The oracle (`tests/v0512_oracles.py`) was written in the same session that read `screen_d5.py` for the inventory.
> - It does not import `src/`.
> - Still, 36 of its 184 substantive lines are textually equal to lines of `screen_d5.py` at the approval commit (an exploratory count, spaces removed).
> - It reuses the noise of `tests/screen_reference.py`.
>
> No phase, depth or MES is asserted against the recipe's parameters, although they are there. For example, in C03 a shift of 1.6 d gives phase 0.4324, while the oracle gives 0.4293.
>
> Why it matters: #223 was opened because "an error ... with a wrong value would pass every test". An error in reading the specification that the oracle shares with `src/` would still pass. v0.5.13 intends to calibrate U1 on these values.

**The review's suggested correction:** add assertions against the generating model where the model decides the value:
- the secondary's phase within one grid step;
- `delta_pri` and `delta_sec` against the injected depths;
- MES against depth, sigma and count.

The oracle's limit is recorded as an open item. The review's own spot check of C01, C03, C04 and FA1 found the oracle's values coherent with the recipes.

**Status:** this issue is a **precondition before calibrating U1**, and it is cited as such in the v0.5.13 proposal. Nothing is corrected in `src/` by this issue.

Labels: `exploratory`, `method_status: not_validated`.
