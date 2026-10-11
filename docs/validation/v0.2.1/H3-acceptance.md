# v0.2.1 H3 (timing uncertainty in the blind holdout): measurement protocol

Status: **closed: no limit was sustained and option A is abandoned.** Part 1, the
measurement protocol, was committed on its own (`ec5e30d`) before the measurement ran;
the "Part 1 result" section was added afterwards, without changing the protocol.
Written 2026-10-10 on branch `claude/v0-2-1-gauntlet-fixes-13f5e7`. There is no part 2:
the timing problem moves to H3b (see the end of this file).

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

## Part 1 result (2026-10-10)

Measured with the protocol above, unchanged, on the code of commit `78d79f5` (the
engine after H4; `ec5e30d` only added this file). 36 cells x 60 seeds x (without,
with the floor) = 4320 rounds. The scripts and the raw results are in
`docs/validation/v0.2.1/H3/` (`measure.py`, `tables.py`, `results.json`); a second run
of the committed `measure.py` reproduced `results.json` byte for byte (SHA-256
`65417d91f2e27789901fd5a6064b2eb4dcdd0b74f2f6db8545558caaa8689099`). The tables
below are the output of `tables.py`.

### Table 1. Calibration without the floor (periodic signals, 60 trials per cell)

| Signal | Noise | N | Orbit (d) | Measured N | Other signal | Trials with ephemeris | Trials with a 3-sigma deviation | Transits > 3 sigma / total | Trials that read | Trials with a window loss | 95% upper bound | < 5%? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| planet | white | 3 | 5.2 | 3-3 | 0 | 60 | 8 | 56 / 420 | 0 | 0 | 4.9% | yes |
| planet | white | 4 | 5.8 | 4-4 | 0 | 60 | 3 | 21 / 420 | 19 | 2 | 10.1% | no |
| planet | white | 5 | 8.9 | 5-5 | 0 | 60 | 3 | 21 / 420 | 20 | 1 | 7.7% | no |
| planet | white | 6 | 9.5 | 6-6 | 0 | 60 | 5 | 35 / 420 | 35 | 3 | 12.4% | no |
| planet | white | 7 | 12.6 | 7-7 | 0 | 60 | 3 | 21 / 420 | 47 | 0 | 4.9% | yes |
| planet | white | 8 | 13.2 | 8-8 | 0 | 60 | 0 | 0 / 420 | 57 | 0 | 4.9% | yes |
| planet | red | 3 | 5.2 | 2-3 | 3 | 57 | 11 | 77 / 399 | 0 | 0 | 4.9% | yes |
| planet | red | 4 | 5.8 | 4-4 | 0 | 60 | 7 | 49 / 420 | 6 | 1 | 7.7% | no |
| planet | red | 5 | 8.9 | 5-10 | 1 | 59 | 6 | 42 / 413 | 10 | 3 | 12.4% | no |
| planet | red | 6 | 9.5 | 6-6 | 0 | 60 | 4 | 28 / 420 | 5 | 1 | 7.7% | no |
| planet | red | 7 | 12.6 | 7-7 | 0 | 60 | 4 | 28 / 420 | 13 | 0 | 4.9% | yes |
| planet | red | 8 | 13.2 | 7-8 | 0 | 60 | 2 | 14 / 420 | 14 | 0 | 4.9% | yes |
| false_positive | white | 3 | 4.2 | 3-3 | 0 | 60 | 4 | 36 / 540 | 0 | 0 | 4.9% | yes |
| false_positive | white | 4 | 4.5 | 4-4 | 0 | 60 | 3 | 27 / 540 | 28 | 2 | 10.1% | no |
| false_positive | white | 5 | 7.1 | 5-5 | 0 | 60 | 1 | 9 / 540 | 38 | 0 | 4.9% | yes |
| false_positive | white | 6 | 7.4 | 6-6 | 0 | 60 | 2 | 18 / 540 | 54 | 0 | 4.9% | yes |
| false_positive | white | 7 | 10.0 | 7-7 | 0 | 60 | 1 | 9 / 540 | 60 | 0 | 4.9% | yes |
| false_positive | white | 8 | 10.3 | 8-8 | 0 | 60 | 0 | 0 / 540 | 60 | 0 | 4.9% | yes |
| false_positive | red | 3 | 4.2 | 3-3 | 0 | 60 | 4 | 36 / 540 | 0 | 0 | 4.9% | yes |
| false_positive | red | 4 | 4.5 | 4-4 | 0 | 60 | 8 | 72 / 540 | 16 | 3 | 12.4% | no |
| false_positive | red | 5 | 7.1 | 5-5 | 0 | 60 | 3 | 27 / 540 | 14 | 1 | 7.7% | no |
| false_positive | red | 6 | 7.4 | 6-6 | 0 | 60 | 7 | 63 / 540 | 26 | 3 | 12.4% | no |
| false_positive | red | 7 | 10.0 | 7-7 | 0 | 60 | 0 | 0 / 540 | 43 | 0 | 4.9% | yes |
| false_positive | red | 8 | 10.3 | 8-8 | 0 | 60 | 3 | 27 / 540 | 56 | 1 | 7.7% | no |

### Criterion by N (the four periodic cells, without the floor)

| N | planet white | planet red | FP white | FP red | N satisfies |
|---|---|---|---|---|---|
| 3 | yes | yes | yes | yes | yes |
| 4 | no | no | no | no | no |
| 5 | no | no | yes | no | no |
| 6 | no | no | yes | no | no |
| 7 | yes | yes | yes | yes | yes |
| 8 | yes | yes | yes | no | no |

Smallest N that satisfies it with every larger measured N: none: no limit sustained

### Table 2. Outcomes without / with the floor (applied at every N, 60 trials)

| Signal | Noise | N | PASS | FAIL | INCONCLUSIVE | FAIL increase with the floor? | Trials with a window loss |
|---|---|---|---|---|---|---|---|
| planet | white | 3 | 0 / 0 | 0 / 0 | 60 / 60 | no (+0, -0) | 0 / 0 |
| planet | white | 4 | 17 / 0 | 2 / 0 | 41 / 60 | no (+0, -2) | 2 / 0 |
| planet | white | 5 | 20 / 0 | 0 / 0 | 40 / 60 | no (+0, -0) | 1 / 0 |
| planet | white | 6 | 32 / 0 | 3 / 0 | 25 / 60 | no (+0, -3) | 3 / 0 |
| planet | white | 7 | 47 / 0 | 0 / 0 | 13 / 60 | no (+0, -0) | 0 / 0 |
| planet | white | 8 | 57 / 31 | 0 / 0 | 3 / 29 | no (+0, -0) | 0 / 0 |
| planet | red | 3 | 0 / 0 | 0 / 0 | 60 / 60 | no (+0, -0) | 0 / 0 |
| planet | red | 4 | 5 / 0 | 1 / 0 | 54 / 60 | no (+0, -1) | 1 / 0 |
| planet | red | 5 | 7 / 0 | 3 / 0 | 50 / 60 | no (+0, -3) | 3 / 0 |
| planet | red | 6 | 4 / 0 | 1 / 0 | 55 / 60 | no (+0, -1) | 1 / 0 |
| planet | red | 7 | 13 / 0 | 0 / 0 | 47 / 60 | no (+0, -0) | 0 / 0 |
| planet | red | 8 | 14 / 0 | 0 / 0 | 46 / 60 | no (+0, -0) | 0 / 0 |
| false_positive | white | 3 | 0 / 0 | 0 / 0 | 60 / 60 | no (+0, -0) | 0 / 0 |
| false_positive | white | 4 | 28 / 0 | 0 / 0 | 32 / 60 | no (+0, -0) | 2 / 0 |
| false_positive | white | 5 | 38 / 38 | 0 / 0 | 22 / 22 | no (+0, -0) | 0 / 0 |
| false_positive | white | 6 | 54 / 54 | 0 / 0 | 6 / 6 | no (+0, -0) | 0 / 0 |
| false_positive | white | 7 | 60 / 60 | 0 / 0 | 0 / 0 | no (+0, -0) | 0 / 0 |
| false_positive | white | 8 | 60 / 60 | 0 / 0 | 0 / 0 | no (+0, -0) | 0 / 0 |
| false_positive | red | 3 | 0 / 0 | 0 / 0 | 60 / 60 | no (+0, -0) | 0 / 0 |
| false_positive | red | 4 | 14 / 0 | 2 / 0 | 44 / 60 | no (+0, -2) | 3 / 0 |
| false_positive | red | 5 | 13 / 0 | 1 / 0 | 46 / 60 | no (+0, -1) | 1 / 0 |
| false_positive | red | 6 | 23 / 25 | 3 / 1 | 34 / 34 | no (+0, -2) | 3 / 1 |
| false_positive | red | 7 | 43 / 43 | 0 / 0 | 17 / 17 | no (+0, -0) | 0 / 0 |
| false_positive | red | 8 | 56 / 56 | 0 / 0 | 4 / 4 | no (+0, -0) | 1 / 0 |
| vanishing | white | 3 | 0 / 0 | 0 / 0 | 60 / 60 | no (+0, -0) | n/a |
| vanishing | white | 4 | 0 / 0 | 19 / 0 | 41 / 60 | no (+0, -19) | n/a |
| vanishing | white | 5 | 0 / 0 | 20 / 0 | 40 / 60 | no (+0, -20) | n/a |
| vanishing | white | 6 | 0 / 0 | 35 / 0 | 25 / 60 | no (+0, -35) | n/a |
| vanishing | white | 7 | 0 / 0 | 47 / 0 | 13 / 60 | no (+0, -47) | n/a |
| vanishing | white | 8 | 0 / 0 | 57 / 31 | 3 / 29 | no (+0, -26) | n/a |
| vanishing | red | 3 | 0 / 0 | 0 / 0 | 60 / 60 | no (+0, -0) | n/a |
| vanishing | red | 4 | 0 / 0 | 6 / 0 | 54 / 60 | no (+0, -6) | n/a |
| vanishing | red | 5 | 1 / 0 | 9 / 0 | 50 / 60 | no (+0, -9) | n/a |
| vanishing | red | 6 | 0 / 0 | 5 / 0 | 55 / 60 | no (+0, -5) | n/a |
| vanishing | red | 7 | 0 / 0 | 13 / 0 | 47 / 60 | no (+0, -13) | n/a |
| vanishing | red | 8 | 0 / 0 | 14 / 0 | 46 / 60 | no (+0, -14) | n/a |

### Conclusion

1. **No limit was sustained.** `N = 7` satisfies the criterion in the four periodic
   cells, but `N = 8` does not (false positive, red noise: 1 window loss in 60, upper
   bound 7.7%), so no `N` satisfies it together with every larger measured `N`.
   **Option A (a floor by count of train transit times) is abandoned.**
2. **The underestimation exists at every N**, not only with few train times: 3-sigma
   deviations appear in 0 to 11 of 60 trials at every `N`, up to 19% of transits per
   cell against about 0.27% for a calibrated Gaussian error; window losses that lead
   to FAIL of a real planet appear at `N` = 4, 5 and 6 (1 to 3 per cell).
3. **The floor removes the losses but removes the power.** With the ingress at its
   geometric maximum, the floor removed every window loss but one, and it never
   increased FAIL in any of the 36 cells (tested: no new FAIL). But it removed almost
   all PASS of planets up to `N = 7` and almost all the power against a vanishing
   signal (FAIL 47 to 0 at `N = 7`, 57 to 31 at `N = 8`, white noise) in this design
   (two years, prediction about 200 epochs ahead).

### A defect of the protocol's own criterion

`N = 3` "satisfied" the criterion only **vacuously**: no round with 3 train times read
the hidden year (all ended INCONCLUSIVE through the timing-uncertainty rule), and the
protocol counted rounds that were not read as trials without a loss. A criterion
that a test can satisfy by never looking is not evidence of calibration.

**Rule for the next measurement protocols:** only rounds that **read the hidden
year** count as trials of a window-loss criterion, and the protocol declares, before
measuring, the minimum number of such reads per cell below which the cell is
reported as "not enough reads" and cannot satisfy the criterion.

## Open items and follow-up

- **H3b** (moved into the v0.2.1 package by the maintainer, 2026-10-10, after the
  part 1 result; no longer an open item): measure transit times with a model that
  has an ingress (trapezoid) instead of a box, so the formal timing error is
  realistic without a floor. It needs its own plan, approved separately, and its own
  validation against correlated noise and low SNR, following the rule above.
- **Global ephemeris** (dossier and exporter): reported only; its errors have the same
  underestimation. Linked to H13; not part of H3.
