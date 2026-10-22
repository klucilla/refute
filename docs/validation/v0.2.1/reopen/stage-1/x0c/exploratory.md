# X0c: not declared, written apart (nothing here was run)

## A reading of the reported values

In 6 of the 13 FAIL rounds `d_twin / d_train` is 0.08 or less, or negative (`white-0080`,
`white-0002`, `white-0048`, `white-0152`, `white-0017`, `correlated-0245`), and in two more it is
0.12 (both `correlated-0211`): the noiseless twin, measured at the predicted windows and the
chosen `dP`, holds almost none of the transit. A train depth above the truth would leave the twin's
depth near the truth, so a ratio that small would need a train depth many times the injected one;
predicted windows that missed the transits is the simpler reading. The declared rules do not make
this distinction, and these records cannot confirm it. **Qualified by the maintainer (2026-10-21):**
the twin keeps the model's variability and trend, is measured with the trend fitted to the noisy
curve and depends on the masks, the detrending and the fit, so a small twin depth can also come
from the processing; a much inflated train depth can also give a ratio near zero; and noise can
cause the ephemeris or trend error itself. The reading above is not a finding.

Five of the six R = 8 cases in `white, no variability` are `two_years` (one train year, the hidden
year about two years away), and one is `few_train` (three train transits): both are layouts where
the train ephemeris is extrapolated far, which is compatible with the reading above. The seven
variability cases are `variability_some_years`.

## Codex's algebraic probe (the round's review, 2026-10-21; not declared, not run by the script)

With `d_hidden` set to `d_twin` and every other field kept, `S_meas` would be 5.28 instead of 4.81
for `rmin-study-16/planet-measurable-white-0246` and 5.50 instead of 4.91 for
`rmin-study-4/planet-measurable-correlated-0231`: both PASS. (`S_meas` is the hidden depth over its
error, so the counterfactual is `d_twin / e_hidden`; both values check against `x0c.json`.) For
these two near-limit cases the hidden noise, although within its usual range (`Z_hidden` 0.44), was
needed for the detection to fail. It is a counterfactual on recorded fields, not a run of the
engine.

## Proposals (none authorized)

1. **Where the predicted windows fall:** with X1's fields (`train_ephemeris`, `n_transit_times`,
   `max_timing_sigma_days`) recorded in a future lot, compare the predicted transit times with the
   injected ones (the evaluator's truth, never the engine's) per round, and report the offset in
   units of the train duration and of `σ_T`, by layout. That would say whether the false FAIL come
   from the windows, and whether the timing rule's limit lets such rounds through.
2. **The train depth against the injected depth:** with the evaluator's truth recorded since X1,
   `(d_train − depth) / e_train` per round, to see whether the train depth is biased in the
   `variability_some_years` cases.
3. Both belong to a declared experiment with its own authorization (they need a lot); X2 could carry
   them at no extra cost, if the maintainer adds them to its declaration before it runs.
