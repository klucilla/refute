# Holdout with the right signal: what the train predicted and what the hidden year gave (M3, slot 1)

Read only: the result records already written and the frozen manifest. Script: `investigations/holdout_investigation.py`. Cases: planets whose candidate has signal identity with the injected period and whose `holdout_by_year` is FAIL. Each round is one hidden year.

<!-- translation-note -->

Translated by that script from the maintainer's Portuguese record `dev1-holdout.md` (2026-10-14, SHA-256 `feeb5313361d64258c09245e3035fcc57481c7cbe68f1acc6a669a4a5fd37dfe`), with the same numbers (`investigations/check_numbers.py`); the Portuguese record is kept in the archive of the study. File and line references are to commit `605fac1`.

<!-- /translation-note -->

Quantities:

- **Predicted SNR (train only)** = (train depth / train depth error) x sqrt(predicted windows / train transits). It uses only what the tool had before reading the hidden year (the train candidate and the windows, which come from the metadata). It is an approximation of this diagnosis, not a rule of the tool.
- **True hidden-year SNR** = c_hidden(y) x injected depth, from the manifest, under the noise model of the case (including the AR(1) covariance). **The tool never has this value**; it only serves to separate the categories.
- **Window offset** = |predicted t - t of the nearest true transit| / half-width of the window; above 1, the window does not contain the center of the transit.
- The tool's FAIL: stacked SNR in the windows < 5.0 (`holdout_by_year.min_snr`).

## three_years, near: 59 of 100 planets with the right signal and holdout FAIL

| noise | round | n |
|---|---|---|
| correlated | FAIL: the train predicted a detectable signal, the true SNR is >= 5, and it did not appear | 42 |
| correlated | FAIL: windows outside the true transit | 2 |
| correlated | INCONCLUSIVE | 3 |
| correlated | PASS | 49 |
| white | FAIL: the train predicted a detectable signal, the true SNR is >= 5, and it did not appear | 33 |
| white | FAIL: windows outside the true transit | 1 |
| white | INCONCLUSIVE | 17 |
| white | PASS | 30 |

FAIL rounds in white noise (34), medians: train SNR 7.94; SNR predicted from the train only 5.77; SNR measured in the hidden year 4.24; true hidden-year SNR 6.11; white error 30.7 ppm, scatter error 31.5 ppm; depth measured in the hidden year 145 ppm against 165 injected; windows with data 8 of 8; largest window offset 0.17 half-width; timing uncertainty 0.12 duration.

FAIL rounds in correlated noise (44), medians: train SNR 33.2; SNR predicted from the train only 23.8; SNR measured in the hidden year 4.16; true hidden-year SNR 6.26; white error 36.7 ppm, scatter error 188 ppm; depth measured in the hidden year 761 ppm against 877 injected; windows with data 10 of 10; largest window offset 0.1 half-width; timing uncertainty 0.0873 duration.

Examples (3 FAIL rounds):

- `planet-near-correlated-0101`, hidden year 2019 (correlated): no significant signal at 15 predicted windows (SNR 4.7 < 5.0); train SNR 36.7, 28 transits, depth 732 ppm (injected 873); predicted SNR 26.9; hidden year: SNR 4.72, depth 631 ppm, white error 28.3, scatter 134, windows 15/15, phase-0.5 control SNR 1.47; truth: hidden-year SNR 7.25, largest offset 0.0852
- `planet-near-correlated-0105`, hidden year 2018 (correlated): no significant signal at 6 predicted windows (SNR 4.4 < 5.0); train SNR 38.2, 12 transits, depth 1.06e+03 ppm (injected 1.19e+03); predicted SNR 29.2; hidden year: SNR 4.42, depth 984 ppm, white error 43.3, scatter 223, windows 6/7, phase-0.5 control SNR -0.951; truth: hidden-year SNR 6.37, largest offset 0.0504
- `planet-near-correlated-0108`, hidden year 2019 (correlated): no significant signal at 14 predicted windows (SNR 2.9 < 5.0); train SNR 31.2, 31 transits, depth 535 ppm (injected 962); predicted SNR 22.4; hidden year: SNR 2.89, depth 701 ppm, white error 27.1, scatter 243, windows 14/16, phase-0.5 control SNR 0.626; truth: hidden-year SNR 6.19, largest offset 24.2

## variability_some_years, measurable: 43 of 100 planets with the right signal and holdout FAIL

| noise | round | n |
|---|---|---|
| correlated | FAIL: the train predicted a detectable signal, the true SNR is >= 5, and it did not appear | 42 |
| correlated | FAIL: windows outside the true transit | 20 |
| correlated | INCONCLUSIVE | 34 |
| correlated | PASS | 3 |
| white | FAIL: the train predicted a detectable signal, the true SNR is >= 5, and it did not appear | 14 |
| white | FAIL: windows outside the true transit | 4 |
| white | INCONCLUSIVE | 10 |
| white | PASS | 2 |

FAIL rounds in white noise (18), medians: train SNR 21.2; SNR predicted from the train only 15.2; SNR measured in the hidden year 0.854; true hidden-year SNR 22.6; white error 54.6 ppm, scatter error 547 ppm; depth measured in the hidden year 515 ppm against 616 injected; windows with data 9 of 9; largest window offset 0.237 half-width; timing uncertainty 0.154 duration.

FAIL rounds in correlated noise (62), medians: train SNR 55.7; SNR predicted from the train only 39.7; SNR measured in the hidden year 0.942; true hidden-year SNR 14.4; white error 168 ppm, scatter error 1.74e+03 ppm; depth measured in the hidden year 1.67e+03 ppm against 2.45e+03 injected; windows with data 7 of 7; largest window offset 0.508 half-width; timing uncertainty 0.0785 duration.

| hidden year | round | n |
|---|---|---|
| hidden year with variability | FAIL | 80 |
| hidden year with variability | INCONCLUSIVE | 1 |
| hidden year with variability | PASS | 5 |
| hidden year without variability | INCONCLUSIVE | 43 |

Examples (3 FAIL rounds):

- `planet-measurable-correlated-0200`, hidden year 2018 (correlated): no significant signal at 11 predicted windows (SNR 4.7 < 5.0); train SNR 53.2, 22 transits, depth 1.5e+03 ppm (injected 1.88e+03); predicted SNR 39.3; hidden year: SNR 4.68, depth 1.4e+03 ppm, white error 36.6, scatter 299, windows 11/12, phase-0.5 control SNR 0.151; truth: hidden-year SNR 14.1, largest offset 0.000198
- `planet-measurable-correlated-0202`, hidden year 2018 (correlated): no significant signal at 6 predicted windows (SNR 0.6 < 5.0); train SNR 28.2, 12 transits, depth 990 ppm (injected 1.42e+03); predicted SNR 19.9; hidden year: SNR 0.633, depth 1.37e+03 ppm, white error 155, scatter 2.17e+03, windows 6/6, phase-0.5 control SNR 1.54; truth: hidden-year SNR 7.95, largest offset 0.224
- `planet-measurable-correlated-0202`, hidden year 2020 (correlated): no significant signal at 6 predicted windows (SNR 0.2 < 5.0); train SNR 29.6, 12 transits, depth 1.04e+03 ppm (injected 1.42e+03); predicted SNR 22.6; hidden year: SNR 0.17, depth 393 ppm, white error 142, scatter 2.31e+03, windows 6/7, phase-0.5 control SNR 0.556; truth: hidden-year SNR 7.96, largest offset 0.503

## Observations (causal readings are marked as hypotheses)

1. **The windows are almost always in the right place.** In 131 of the 158 FAIL rounds (78 in `three_years`, 80 in `variability_some_years`) the windows contain the center of the true transit (median offset 0.1 to 0.5 half-width); 27 rounds have some window displaced (3 in `three_years`, 24 in `variability_some_years`). For these cases, the failure is not in the train ephemeris.
2. **`three_years`, near: the signal is in the hidden year, but near the threshold.** The depth measured in the hidden year stays close to the injected one (median 145 against 165 ppm in white, 761 against 877 in correlated) and the measured SNR stays just below the threshold (median 4.2 against 5.0). The true hidden-year SNR is low (median 6.1 to 6.3): a fatal test with a 5.0 threshold on a signal with a true SNR of ~6 fails often from fluctuation alone. In this reading, the round had **little capacity to test** and the FAIL is not evidence that the signal disappeared. **Hypothesis** (not tested): a rule that requires, before the hidden year is read, a predicted SNR with a margin above the threshold would turn most of these FAILs into INCONCLUSIVE, without touching the cases in which the predicted signal is strong.
3. **In correlated noise the train overestimates the capacity to test.** The train-only prediction gives a median SNR of 23.8 for `three_years` near, against a true SNR of 6.3; in the hidden year the scatter error (188 ppm) is five times the white one (37 ppm), and it is the scatter error that sets the measured SNR. It is the same pattern as item 2 of the diagnosis <!-- translation-note -->(the observations of `diagnosis.md`)<!-- /translation-note --> (SNR with a white-noise error). **Hypothesis:** a capacity rule only works here if the train error also accounts for the correlated noise.
4. **`variability_some_years`, measurable: all 80 FAIL rounds are hidden years with variability;** the 43 hidden years without variability gave INCONCLUSIVE (no FAIL). In the hidden year with variability, the scatter error is about 10 times the white one (547 against 55 ppm in white; 1740 against 168 in correlated), and the measured SNR falls to ~0.9, although the measured depth stays close to the injected one (515 against 616 ppm in white). **Hypothesis:** the local straight line of each window does not remove a sinusoid of 0.3 to 1 d with 2 to 4 times the transit depth; the scatter between windows dominates the error and the test declares that the signal did not appear. The "true SNR" of the manifest does not include the variability, so it overestimates the detectability in those years.
5. **Answer to the maintainer's question.** In both families, the train predicted (by the approximate rule above) a detectable signal and the measured SNR did not reach 5. But the records show that the signal is present (measured depth close to the injected one, correct windows): the FAIL comes from **little real capacity to test** (a true signal near the threshold in `three_years` near) or from **an error that the hidden-year measurement does not control** (variability in `variability_some_years`), not from a signal that disappeared. The case "the train did not allow a prediction" hardly appears **because the train prediction is optimistic** (item 3), not because the capacity was good.
