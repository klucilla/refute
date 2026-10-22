# Specification C: the C4/C6 amendment (proposal, not adopted)

The maintainer's decision after X2e, item 1: propose an amendment that clarifies the inconsistency
between C4 and C6 of [../spec-c-error-model.md](../spec-c-error-model.md); the alternatives that
change the decision's scientific scope go to the maintainer's choice and are not resolved as a
wording fix. **Nothing here is adopted; spec C's text is unchanged until the maintainer decides.**
The amendment is declared after a result (X2e's), so its reason is stated and Codex reviews it; it
changes no criterion and no sample. It does withdraw a reading: the earlier pooled, cell-level
reading of eligibility in C4's note.

## The inconsistency

- **C4** defines the regimes as the cells × the number of observing years (2; 3 or more) and fixes
  eligibility by coverage (at least 15 contributing cases) before any candidate. Its note on the
  expected coverage counts X2e **"pooled with X2"** (28 and 12 cases) and ends: "the cells themselves
  (all years together) are the regimes that can decide there".
- **C6** lets only data never used decide (X2e, and a variability replicate); X2 informs only.
- So C4's note relies on pooling with X2, which C6 forbids for the decision, and names the cells
  (all years together) as deciding regimes, which C4's own definition does not include.

## A0. The clarifying amendment (keeps the scope)

Replace C4's second paragraph with:

> **Coverage note (amended after X2e, 2026-10-22; the reason: the earlier note relied on pooling with
> X2, which C6 excludes from the decision).** Eligibility is computed only on the data C6 lets
> decide: X2e's records for the cells without variability, the variability replicate's for the cells
> with variability. X2's records never count toward a regime's 15 cases. The regimes are those of the
> first paragraph only (cell × number of years); a cell with all its years together is not a regime.
> With X2e alone, no regime is eligible (2 years: 5 and 2 contributing cases; 3 or more years: 6 and
> 6), so no candidate can be judged and the choice waits for new data with new seeds.

And add to C6: "Data that decide are never pooled with data that inform, for eligibility or for a
verdict."

Effect: spec C decides nothing until a new package supplies new independent cases (item 5); the
minimum stays 15, X2 stays informative only.

## The ways forward (for the maintainer's choice; A2 and A3 are not wording fixes)

| | Alternative | What it changes | Consequence |
|---|---|---|---|
| A1 | **Keep the regimes; require new data** (A0 alone, plus the package of item 5 sized for every regime) | nothing: **keeps the scope** | the most data; the two-year regimes of `white, no variability` need about 334 cases for 40 contributing (about 138 for 15), at the rate seen, and one population prefix holds 300 |
| A2 | **Validate the corrected model only in the three-year regimes**; the two-year regimes stay outside its validated scope and keep today's model, reported as unvalidated | **changes the scope**: the corrected model would not be claimed for two-year layouts | much less data; the two-year layouts, where the measurement is rarest, stay with an unvalidated error model; that boundary is published exactly |
| A3 | **Decide at cell level (all years together) on new data only** | **changes the regime definition**: a cell's verdict mixes layouts whose contribution differs (three-year cases dominate), so a calibrated cell can hide a miscalibrated layout | fewer cases than A1, but the result is not per regime; item 2 shows why this hides the two-year layouts |

Not an option: pooling X2 to reach 15 (excluded by the maintainer), or lowering the minimum.

**A note on C5 for the maintainer (no change proposed):** an eligible regime blocks each candidate
that fails C5 there, an inconclusive interval included; with limited precision (a regime that barely
reaches 15 cases), the intervals are wider and no candidate may be admissible in that decision.
Reaching only 15 cases does not by itself block a candidate (a narrow interval inside the window is
admissible, and a wide one entirely outside it is `overestimated` or `underestimated`, not
inconclusive; Codex's review), and candidates can differ in width. The package (item 5) sizes for
precision for this reason; whether C5 should treat an eligible but imprecise regime differently is a
criterion question, the maintainer's, declared before the new data if at all.
