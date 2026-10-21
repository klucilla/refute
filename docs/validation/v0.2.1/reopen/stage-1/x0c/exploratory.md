# X0c: not declared, written apart (nothing here was run)

## A reading of the reported values

In 6 of the 13 FAIL rounds `d_twin / d_train` is 0.08 or less, or negative (`white-0080`,
`white-0002`, `white-0048`, `white-0152`, `white-0017`, `correlated-0245`), and in two more it is
0.12 (both `correlated-0211`): the noiseless twin, measured at the predicted windows and the
chosen `dP`, holds almost none of the transit. A train depth above the truth would leave the twin's
depth near the truth, so a ratio that small would need a train depth many times the injected one;
predicted windows that missed the transits is the simpler reading. The declared rules do not make
this distinction, and these records cannot confirm it.

Five of the six R = 8 cases in `white, no variability` are `two_years` (one train year, the hidden
year about two years away), and one is `few_train` (three train transits): both are layouts where
the train ephemeris is extrapolated far, which is compatible with the reading above. The seven
variability cases are `variability_some_years`.

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
