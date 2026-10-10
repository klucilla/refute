# TESS gauntlet v0.2.1

This document describes what changes in the TESS pack in v0.2.1 ("Gauntlet fixes"),
after the v0.2 calibration failed. It extends [gauntlet v0.2](gauntlet-tess-v0.2.md):
everything there still applies unless this document says otherwise. All thresholds
are defaults of the claim schema and are written explicitly into every locked claim.

**How the thresholds were set.** Each threshold below follows from reasoning about
the measurement and was checked on synthetic data only, with acceptance criteria
committed before the validation ran (`docs/validation/v0.2.1/`). No threshold was
set, tuned or checked on a known target or on real data. Synthetic scenes are
idealized (Gaussian point-spread function, no pointing jitter, no scattered light);
they **do not establish bounds for real data**, in either direction, because an
effect missing from the simulation can make any rate better or worse. Synthetic
numbers compare versions of the engine and test known mechanisms; they do not predict
performance on real data.

Calibration evaluation (not a gauntlet test): from v0.2.1 a calibration claim can
require the analyzed signal to be the catalogued one before a false positive counts
as flagged (`flag_requires_signal_recovery`, H7); see [claim-spec.md](claim-spec.md).

## holdout_by_year: train validity (H4)

A round of the blind holdout hides one observing year, searches the other years and
predicts transit windows in the hidden year from the train-only candidate. Before
v0.2.1 the round used that candidate whatever it was. On synthetic variable stars
(`sinusoid`, `fp_variability_dominates`) every round **passed** with a train box of
duration/period 0.357 whose windows covered the whole hidden year: there was no part
of the year outside the prediction, so the round could not fail. A round trained on
variability present only in the train years (`variability_train_only`) **failed**,
although the failure said nothing about the signal.

From v0.2.1 a round's train-only candidate must be a valid basis for a prediction.
It is **invalid** when:

| Rule | Condition | Parameter (default) |
|---|---|---|
| (a) gate | its SNR fails the SNR gate of the full analysis (same function) | `gauntlet.snr.min_snr` (7.1) |
| (b) duration | duration / period above the limit | `max_train_duration_period_ratio` (0.2) |
| (c) windows | the transit windows cover more than this fraction of the hidden sectors' time spans | `max_hidden_window_fraction` (0.5) |

Equality is valid in every rule. (a) and (b) are checked right after the train
search; then transit times, the train ephemeris and the windows are computed, the
timing-uncertainty rule of v0.2 (issue #2) is applied unchanged, and (c) last. An
invalid round is **INCONCLUSIVE, never FAIL**, with a message listing the rules that
triggered, and it is decided **before the hidden year is read**: no hidden-year object
is built and the round's access log is empty. Every round reports `train_validity`:
the three values, the limits, whether the rules were applied, and the reasons.

**Why these limits.**

- (b) 0.2: a transit window's baseline band extends to
  `duration/2 + baseline_outer_durations * duration` from the predicted time. It
  reaches the phase-0.5 control box when duration/period exceeds
  `1 / (2 * (1 + baseline_outer_durations))`, which is 0.2 for the default 1.5. Above
  that, the transit and control measurements are not independent.
- (c) 0.5: windows covering more than half of the observed hidden time overlap the
  phase-0.5 control windows, so no part of the year is outside the prediction.

**Isolation.** The three rules use only the round's train data, the claim's
parameters and the hidden sectors' time spans (metadata already used to predict the
windows; (c) never uses the hidden cadences). They never compare with the full-data
analysis or with other rounds: the train data of any other round contain this round's
hidden year. The pre-read step (`plan_round`) does not receive hidden-year flux, and
a test replaces the hidden year's flux (noise, another signal, nothing) and checks
that no pre-read decision changes.

**Switch.** `require_valid_train: false` computes and reports the three rules without
applying them (the v0.2 behavior). It exists for before/after studies.

**Not covered (open item).** A *directed* mode, requiring the train candidate to
match a published period and epoch, is not implemented: it would pass target
information into the holdout.

**Effect.** On the synthetic scenarios (development seeds 0-9): planets, eclipsing
binaries and blends are unchanged (no rule triggers: train SNR at least 53,
duration/period at most 0.055, window fraction at most 0.164); `noise` and
`vanishing` change only the reason of rounds that were already INCONCLUSIVE; the
`vanishing` rounds that fail with a valid train still fail; `sinusoid` and
`fp_variability_dominates` rounds go from PASS to INCONCLUSIVE. The guard never turns
a round into PASS or FAIL. A planet whose every round is invalid gets an
INCONCLUSIVE holdout (and verdict) instead of SURVIVED. A real contact binary with
duration/period above 0.2 gets an INCONCLUSIVE holdout; the blind holdout is not the
eclipsing-binary test.

Acceptance criteria and validation: `docs/validation/v0.2.1/H4-acceptance.md`.
