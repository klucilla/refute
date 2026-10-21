# X3: the calibration of b and s, sized by the threshold's precision (declaration, not run)

Prepared on 2026-10-21 at the maintainer's request (decisions after X0 and X1, item 4). **Not
authorized to run.** Its execution comes back to the maintainer with its size, seeds, affinity,
workers, cost and ceiling (section 7). **Order:** if X2 leads to a change of the error model, X3's
definitive calibration uses the corrected model; a calibration made before that is development
evidence only.

## 1. The question

The capacity threshold is `T(n_years) = min_snr − b + z(n_years)·s`, with
`z(n) = Φ⁻¹(1 − 0.005 / n)`. Its precision depends on `b` and `s` together. X3 estimates `b` and
`s` on **independent** targets, in **regimes the engine observes**, with a size set by a declared
precision of `T`, not of `s` alone. Separating the regimes is not presumed to lower the thresholds:
it may raise some (the pooled `s` of the R_min study, 2.88, sat between 2.13 for three-year curves
and 7.71 for two-year curves).

External precedent, not a method adopted: a vetting rule's behaviour measured on simulated data
sets apart from the data it decides on
([sources/thompson-2018.md](sources/thompson-2018.md)).

## 2. The design

- **Targets:** constant-scenario planets of the bands near and measurable, the four groups in equal
  numbers, from new prefixes never used (`x3-1`, `x3-2`, ...), taken in index order; seeds derived as
  X2's (`refute/v0.2.1/stage-1/X3/<prefix>/<index>`), listed and checked against every earlier lot
  before the run.
- **One round per target, chosen before:** the round hiding the target's **last observing year** (the
  largest year of its metadata), whatever its outcome; the other rounds are not used.
- **The estimator:** Amendment 9's, as the study (`k` chosen on the set of rounds with a finite
  `S_meas` and `S_pred,k ≥ min_snr`; `b` the median and `s` the 1.4826 MAD of `S_meas − S_pred,k` over
  that set meeting `R`), at each `R ∈ {8, 10, 12, 15, 20}`. No other estimator is tried, and none is
  chosen because it admits more rounds.
- **Regimes, by quantities the engine observes, fixed now:** `n_years = 2` and `n_years ≥ 3` (from the
  metadata). `b` and `s` per regime, and pooled, all reported; the pooled pair is never substituted
  for a regime's.

## 3. The precision of the threshold

For each regime and `R`: `T` at that regime's `n_years` (2, and 3 for `≥ 3`) and its 95% interval by
a bootstrap over the targets (one round each), 2000 resamples, seed fixed in the execution package.
**Each resample recomputes the whole estimator** (the choice of `k`, then `b` and `s`, then `T`); a
resample whose set is empty for a regime and `R` gives no estimate and is counted; if more than 1% of
the resamples give none, that regime's precision at that `R` is `not determined`. **The precision
target (proposed, for the maintainer):** the interval's half-width at most **10% of `T`**.

## 4. The size rule (fixed now)

- **Stage 1:** 1300 targets per regime (planning, from the experiment plan: about 520 rounds per
  regime in the set, if about 40% of the targets reach it).
- If the precision target is met in every regime **at every `R` of the set** {8, 10, 12, 15, 20}:
  stop. (Revised before any data after Codex's review of the round: "the `R` the pilot will use" was
  not fixed here and could be chosen after the precision was seen. No `R` is chosen by its interval;
  a later choice of `R` reads every `R`'s precision as reported.)
- Otherwise the size needed is computed as `n₁ · (h₁ / h*)²` (the half-width `h₁` reached, the target
  `h*`), and **requested** from the maintainer as a stage 2 with new prefixes; the final estimate
  pools both stages. There is no third stage; a regime still short after stage 2 is reported as not
  calibrated to the target, with its interval.

## 5. Reported

Per regime and `R`: the rounds in the set (and the targets), `k`, `b`, `s`, `T` and their intervals;
the pooled values; the rounds that do not reach the set and why (the replica counts, the hidden
noise, `S_pred`). X4 (the compatibility check of every criterion's filter at each number of years)
follows, on these values.

## 6. What X3 does not do

It does not choose `R_min`, it does not validate a configuration, and it does not presume that new
thresholds are better: lower thresholds can bring new PASS and new FAIL, so safety and utility are
measured again in the pilot (X5), with spec B's false PASS per target.

## 7. To be given with the request to run

The size (2 × 1300 = 2600 targets at stage 1, planning), the seeds, the affinity (processors 8 to
31), the workers (the project's default for that affinity, measured), the estimated cost (≈ 1.5 h at
6 workers; the gain of more workers measured) and a ceiling (1.5 times the estimate). Whether X2's
answer has been read and applied is stated in the request.
