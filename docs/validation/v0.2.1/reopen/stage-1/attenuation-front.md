# The next front: the attenuation in the processing (a reading of the code, nothing changed)

The maintainer's decision after X2 (2026-10-22, item 3): X2-A found the **attenuation in the
processing** the dominant cause of the measurement FAIL and of the `Z_train ≥ 3` rounds in the cells
with variability ([x2/README.md](x2/README.md)). It is recorded as the next front. This note describes,
from the code at `2593bfa` only, what the hidden year's processing does today; it changes nothing and
claims no cause.

## Does the hidden year's detrending mask the predicted transit windows? Yes.

`holdout.HiddenYear.__init__` (`src/refute/packs/tess/holdout.py`, lines 97 to 119):
- the mask is **every registered window** (in the M4 round, `_round_corrected` registers the transit
  and control windows **and their replicas**: `HiddenYear(raw.select(raw.year == hidden_year),
  windows + replicas, plan)`), each out to its `baseline_inner` around its **predicted time** `t_pred`
  (`|t − t_pred| ≤ baseline_inner`), that is the window's half-width `D/2 + timing_sigma·σ_T(epoch)`
  plus `baseline_gap_durations·D`;
- the mask is built at `t_pred`, without the period correction `dP` the measurement chooses later;
  the box moves with `dP` (`t_pred + (epoch − n_ref)·dP`), within the scan `±timing_sigma·σ_P` times
  the epoch's lever;
- the detrending window is widened to `max(window_days, hidden_detrend_window_factor × the widest
  masked span)` (issue #2: so that the knots inside a masked span still have data);
- `detrend.detrend_parts`: per segment, a knot every `knot_spacing_days`; at each knot a robust
  quadratic is fitted to the **unmasked** flux within the (widened) window, with symmetric clipping;
  between knots the trend is the linear blend of the two knots' quadratics; masked cadences never
  enter a fit but are divided by the trend; after the division only points **above** 1 are clipped.

## What is measured, and the twin

- `window_depth` (lines 510 to 559): per window, the box `|t − c| ≤ D/2` among the window's
  cadences; the baseline is every other cadence of the window and of its baseline band, fitted by a
  constant, a line and the **train fundamentals** (sine and cosine at each frequency found on the train
  curve, in decreasing train amplitude); a degeneracy rule drops sinusoids, then the line, when the
  baseline has too few points per parameter or the fit is ill-conditioned; the depth is the box's mean
  of `model − flux`.
- `HiddenYear.twin` (lines 121 to 139): the twin's flux is the noiseless model (`signal × trend +
  variability`, with `var_absent_year` where it applies) **divided by the trend fitted to the noisy
  hidden year**, on the cadences that detrending kept, measured by the same windows at the same `dP`.

## Hypotheses this suggests (not tested, not findings)

1. **The trend across a masked span:** inside a mask the trend is the neighbouring knots' quadratics
   (from a widened window); a stellar variability faster than that window is not followed there, so
   the box and its baseline carry residual variability of different phase.
2. **The baseline's sinusoids are the train's:** the window fit removes the train fundamentals; in
   `variability_some_years` the variability is absent in one year (`var_absent_year`) and its phase
   and amplitude elsewhere follow the model; a frequency fitted where it is absent, or missed where it
   is present, biases the box against its baseline.
3. **The degeneracy fallback:** when sinusoids are dropped (short baselines), a line remains under a
   sinusoidal residual.
4. **The twin carries the variability:** `d_twin` is the depth of the planet **and** of the residual
   variability after the noisy trend, so its loss (`A < 1`) mixes the three effects above; X2 did not
   record which fit (how many sinusoids) each window used (`window_terms` is in the round's metrics,
   not in the calibration record).

## What a study of it would need (not authorized)

A declared experiment that records, per window, the baseline terms used and the trend inside the
mask, and compares the twin's depth with and without the variability in the model, by layout; any
change to the detrending or the window fit with its own specification, tests and validation. No
threshold or gate changes to remove these cases.
