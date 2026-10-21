# Q6. The weakening scenario: what was intended, and what the engine does (text only)

Declared in [DECLARATION.md](DECLARATION.md), Q6. No substitute number is computed here.

## How the scenario is built

`rmin_study.SCENARIOS = {"constant": 1.0, "disappearing": 0.0, "weakened": 0.3}`, and
`alter_last_year`: on the cadences of the target's **last observing year** the flux becomes
`flux + (1 − s) · D(t) · trend(t)`, `D` the injected transit deficit, the noise untouched. In the
weakened scenario the last year's transits keep **30% of their depth**; the earlier years are
unchanged (map Amendment 19, "The lots").

## What its criterion expected

Map Amendment 19, criterion 5, is titled **"Power, incompatible weakening"**: "the lower bound of
the FAIL fraction of the weakened targets with a round eligible for this criterion ≥ 0.50". Its
eligibility: "a weakened target qualifies when its round that hides the last observing year (the
only altered year) passes decisions 1 and 2 and has `0.3 · S_pred,2 ≤ 3` (an expected hidden SNR at
most 3, so the rule can tell), decided before the outcome is read". So the design meant the
weakened signal as **no longer at its predicted depth, to the point of being undetectable** in
the hidden year (its expected SNR at most 3), and expected the rule to FAIL it by the depth
inconsistency.

## What the engine does

`holdout.fail_rule` (Revision 3, 4.5, Amendment 12): **PASS if `S_meas ≥ min_snr`** (5); only if
not, FAIL when `Z = (d_train − d_hidden)/√(e_train² + e_hidden²) > 3`; otherwise INCONCLUSIVE
`not_detected_not_inconsistent`. A weakened signal still detected at `S_meas ≥ 5` is therefore a
PASS, whatever its depth against the train's; the depth inconsistency is tested only when the
signal is not detected. The filter `0.3 · S_pred,2 ≤ 3` was the design's way to keep the criterion
on targets where detection is not expected, so that the FAIL branch can be reached.

## Why the criterion became empty

The study's own settings had `capacity_b = capacity_s = 0` (`rmin_study.STUDY_SETTINGS`), with
which the capacity threshold is `min_snr` = 5 and the filter's window is `5 ≤ S_pred,2 ≤ 10`. The
evaluation applies the pairs of bs-choice instead (b from 0.53 to 0.80, s from 1.9 to 2.9), with
which the threshold is 11.27 to 13.13 at R = 8 to 15 and 9.89 at R = 20 for two years
([../study/diagnosis-weakening.json](../study/diagnosis-weakening.json)): the window is empty at
R = 8 to 15 and `[9.89, 10]` at R = 20. The incompatibility appears only **after** the b/s
calibration; no check between the calibrated gate and the filter existed before the lot.

## The question for the maintainer

Which event should the weakened scenario test?
- **(a) "The signal is still present"**: a weakened but detected transit is a correct PASS (the
  claim of a periodic transit survives); then the scenario measures detection power at reduced
  depth, and a FAIL would be an error.
- **(b) "The signal no longer has its predicted depth"**: a FAIL is expected whenever the hidden
  depth is inconsistent with the train's, detected or not; then the current rule (PASS before the
  depth test) cannot express it, and testing it needs a rule with its own specification and
  validation (not the current `fail_rule`).

Until that definition, the weakened scenario's outcomes are reported without an error label
(Q8), and no other filter, threshold or rate is proposed for it.
