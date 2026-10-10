# v0.2.1 H3 (timing uncertainty in the blind holdout): measurement protocol

Status: **part 1, the measurement protocol, is fixed before any measurement runs.**
This file is committed on its own, before the measurement it describes. Written
2026-10-10 on branch `claude/v0-2-1-gauntlet-fixes-13f5e7`. The acceptance criteria
for the implementation (part 2) are written after the maintainer chooses `N_min`
from the results of part 1.

## Problem

Each blind-holdout round fits a linear ephemeris to the train-only transit times and
predicts windows in the hidden year with half-width `duration/2 + 3 sigma_T`. The
error of each transit time is the half-width of the region where the chi-square of a
**box** is within 1 of its minimum. A box has instantaneous edges; a real transit has
an ingress, so the box error underestimates the real timing error, even with white
noise. The fit inflates the covariance by the reduced chi-square when it exceeds 1,
which works with many degrees of freedom but not with few: with 3 or 4 transit times
the reduced chi-square is mostly noise, and a chance value near 0 leaves the error
uninflated.

A planning survey (development seeds 0-9, before this file) showed it: `planet`
(7 train times) had 2 of 20 rounds with a hidden transit more than 3 sigma from its
prediction; a 4-time planet had 4 of 20 (white noise) and 4 of 20 (red noise), with
1 and 2 FAIL rounds of a real planet. The v0.2 post-mortem reports TOI-6038 A b (3
train times, 1 degree of freedom, 13.4 sigma off); it is cited **only as
motivation**. No known target is used to measure, choose or validate anything here.

**Direction approved (option A):** a timing-error floor applied only when a round has
fewer than `N_min` train transit times; scope the blind holdout only; on by default
with a switch. The floor is the Carter et al. (2008) timing precision
`sigma_t = (sigma_1 / depth) * sqrt(tau * cadence / 2)` with the ingress `tau` at its
geometric maximum, the box duration: `sigma_floor = (sigma_1 / depth) *
sqrt(duration * cadence / 2)`, with `sigma_1` the median per-point error of the train
data, and `depth`, `duration` those of the train candidate. A transit time's error
becomes `max(error, sigma_floor)`; the reduced chi-square inflation still applies.
**`N_min` is pending**: it is chosen by the maintainer from the measurement below,
with the rule in "Decision rule".

## Part 1: measurement protocol

### What is measured

For a number of train transit times `N` in {3, 4, 5, 6, 7, 8}, the calibration of the
round's timing uncertainty **without the floor**, and the round outcomes **with and
without the floor**.

### Scenarios

Two observing years. The **train year** (2018, sector start 1325.0 BTJD) has two
orbits of length `o` separated by a 1-day gap; the **hidden year** (2020, start 2061.0
BTJD) has the standard two 13-day orbits. Only the round that **hides 2020** is
evaluated, so each seed gives exactly one round and rounds are independent across
seeds (rounds of the same seed are never counted as separate trials).

For each `N` and each signal, `o` is the shortest orbit length on a 0.05-day grid from
2 to 16 days for which exactly `N` injected transits lie inside the train year with at
least one transit duration of margin from every edge and from the gap. The measured
number of transit times can be lower (a transit can be rejected by the timing scan);
trials are grouped by the designed `N`, and the measured counts are reported.

Signals (the existing synthetic specifications):

- **planet**: `PLANET` (P = 3.7 d, 2000 ppm, 2.5 h), present in both years.
- **false positive**: the `eb_secondary` eclipsing binary (P = 2.9 d, 5000 ppm primary,
  1500 ppm secondary, 3 h), present in both years.
- **vanishing**: `PLANET` in the train year only; nothing in the hidden year.

Noise, each signal with each:

- **white**: 600 ppm Gaussian.
- **red**: the same white noise plus an AR(1) process with a 1-hour correlation time
  and 600 ppm amplitude.

Every light curve also has the usual slow trend (0.2% sinusoid, 6-day period). The
test plan is the fast plan used by the test suite, with every default (including the
H4 train-validity rules).

That is 3 signals x 2 noises x 6 values of `N` = 36 cells.

### Seeds

**Development seeds 0 to 59** for every cell: 60 independent trials per cell (one
light curve and one round per seed). This extends the development set used by H7 and
H4 (0 to 9) for this measurement only. The confirmation set is not generated and not
used; it stays reserved per rule 5 of the v0.2.1 plan.

### Metrics

For each hidden-year transit of a periodic signal (planet, false positive), with its
true mid-time `t_true` and the round's prediction `t_pred` and `sigma_T` from the
train ephemeris (epoch assigned with the injected period):

- **pull** = `|t_pred - t_true| / sigma_T` (the modulus).
- **3-sigma deviation**: pull > 3. Computed for every round that produced a train
  ephemeris (including rounds then INCONCLUSIVE by the timing-uncertainty rule).
- **window loss**: the true mid-time is outside the window the round actually
  registered and read, `|t_pred - t_true| > duration/2 + 3 sigma_T`. Only rounds that
  read the hidden year (status PASS or FAIL) can have a window loss.

Rates are counted **per trial** (per seed, which is per round here):

- **window-loss rate** (the criterion): the fraction of the 60 trials whose round read
  the hidden year **and** has at least one window loss. Rounds that end INCONCLUSIVE
  before the read cannot produce a false FAIL and count as trials without a loss.
- **3-sigma rate** (reported, not a criterion): the fraction of trials with an
  ephemeris that have at least one 3-sigma deviation. A perfectly calibrated Gaussian
  error gives about 0.27% per transit, so several percent per trial with about 7
  hidden transits; this is why 3-sigma deviations are reported and not used as the
  criterion.
- Per-transit counts of both are also reported (descriptive only).

Trials whose train candidate is not within 1% of the injected period are reported
separately ("other signal": an identity problem, H4's domain) and count as trials
without a loss for the criterion; their number is shown in every table.

Outcomes: PASS, FAIL and INCONCLUSIVE counts per cell, without and with the floor
(with the floor applied at every `N`, so that the effect of any `N_min` can be read
from the table). For **vanishing**, the power is the fraction of FAIL.

### Confidence and sample size

- **X = 5%**: the largest acceptable per-round probability that a round reads the
  hidden year with a true transit outside its window. Rationale: the calibration
  claims allow at most 1 refuted planet in 10 (10%); a timing miscalibration should
  not use more than half of that budget by itself.
- **Confidence: 95%, one-sided**, exact (Clopper-Pearson) upper bound on a binomial
  rate.
- **60 trials per cell**: with 0 window losses in 60 the upper bound is
  `1 - 0.05^(1/60) = 4.87%` < 5%. One loss in 60 gives 7.7%, which does not pass. (For
  comparison, 0 in 20 would only bound the rate below 13.9%.)

### Decision rule (applied by the maintainer, not by the agent)

A value `N` **satisfies the criterion** when, in each of the four periodic cells at
that `N` (planet white, planet red, false positive white, false positive red),
**without the floor**, the 95% upper bound of the window-loss rate is below 5%.

`N_min` is the smallest measured `N` that satisfies the criterion **and** every larger
measured `N` also satisfies it. If no `N` qualifies, the result is that **no limit was
sustained** by this measurement, and that is recorded as such.

The measurement also tests, rather than assumes, that the floor does not increase
FAIL: the floor changes the fit weights, the period and the predictions. For every
cell, FAIL with the floor is compared with FAIL without it, and any increase is
reported.

## Open items

- **H3b**: measure transit times with a model that has an ingress (trapezoid) instead
  of a box, so the formal timing error is realistic without a floor. It will need its
  own validation against correlated noise and low SNR. Not part of H3.
- **Global ephemeris** (dossier and exporter): reported only; its errors have the same
  underestimation. Linked to H13; not part of H3.
