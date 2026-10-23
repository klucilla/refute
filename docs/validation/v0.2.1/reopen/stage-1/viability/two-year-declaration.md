# The two-year barriers: a read-only diagnosis (declaration, before the reading)

The maintainer's decision of 2026-10-23 on the viability check (`0bdb3e3`), item 1, option 2: a
read-only diagnosis of the barriers of the two-year regimes, on the same archived records, declared
before it is read, with Codex's review. **No lot, no change of a criterion, of the engine or of the
environment; X2f stays unauthorized.** This declaration is committed before the script reads any
record for it; the results are a separate commit.

## The data

- **The records:** the R_min study's archive (`rmin-study-run-2e4ff99.zip` on the maintainer's
  Drive, read in place, never extracted into the project): the `constant` scenario, every target
  derived at R = 8 with bs-choice's pair, as in [README.md](README.md) (section 3).
- **Integrity, each check failing the run before any output is written:** the archive's SHA-256 is
  `51fa9b3fab62eda7ed8dee24dd521d251ea12cd7dab77d94902353e6624fba30`; every `constant` record's
  bytes match the study's committed `record-digests.json`, and the records read are exactly the
  committed ones, each once; every record's rounds are one per observing year, checked on the
  rounds as recorded, before they are keyed by year (so a duplicated year cannot hide a FAIL); the
  study's committed INCONCLUSIVE counts are reproduced; every timing message parses.
- **The scope:** the measurable band; items a to c on the two-year regime (`two_years`,
  `few_train`), item d on every regime.
- **The geometry, rebuilt from the generator, not from the engine** (as Amendment 28's diagnosis
  did, `m4-implementation-map.md`, section 1 of that amendment): for each two-year target, its case
  from `population_v2.population_cases("confirm:<prefix>")`, its layout (`_layout`,
  `_sector_cadences`) and its injected period, epoch and duration by the frozen generator's own
  functions (`draw_parameters`, `_mechanism_condition`, `_place_in_band`, the redraws of
  `build_case`), without the noise, the light curve or any engine call. Checked: the rebuilt layout's
  observing years equal the record's `years` for every target; and **a stratified spot check**: the
  first 3 targets, in archive order, of each stratum noise × layout (`two_years`; `few_train` at 1, 2
  and 3 years), whose parameters (period, epoch, duration) must equal those of `build_case` itself.
  That spot check is **the only place** where a case's light curve is built (to compare its
  parameters; no engine call). The geometry is the injected one; the engine's train fit (its
  accepted transit times, weights and `χ²` inflation) can differ, so it is an approximation,
  stated as such. **The train epochs** are those with at least half of `T14` covered by the train
  cadences; **the hidden epochs** those whose injected centre lies in the hidden sector's span (as
  Amendment 28's diagnosis, and as the engine predicts from the spans before any coverage); a round
  with no injected hidden epoch is reported apart from an engine round with no predicted window.

## The questions and how each is read

**a. The timing rule.** It stops a round when the largest train-only `σ_T` over the hidden year's
predicted transits exceeds one train duration (`holdout.py`, lines 1078 to 1105). Read: the
fraction of rounds stopped by it, by layout (`two_years`; `few_train` by its distance of 1, 2 or 3
years), by hidden year, by the number of injected train transits (each with at least half of `T14`
covered by the train data), by the injected period (bins 1.5–2.5, 2.5–3.5, 3.5–4.5, 4.5–5.5 d) and
by the lever `g√N = √(1 + m²/Var_pop(n))` (Amendment 28's identity: `m` the farthest hidden epoch
from the train epochs' mean, `Var_pop(n)` the population variance of the train epochs); and, for
the stopped rounds, `σ_T/T14` from the rule's own message (`σ_T` and the train duration in hours,
two decimals; every message must parse), its point value in the right-closed bins `(1, 1.5]`,
`(1.5, 2]`, `(2, 3]`, `> 3`, and its interval compatible with the rounding of both hours
(`(σ ± 0.005)/(T ∓ 0.005)`). The rounds that pass the rule carry no `σ_T` in these records: **not
identifiable** for them.

**b. T4 at its best (Amendment 28, variant A).** A round is *admitted* by T4 when its curve has
exactly two observing years, its train fundamentals are absent, and its `σ_T/T14` lies in `(1, 3]`.
The records do not hold the train fundamentals: **not identifiable**; the bound assumes them absent
(the favourable case). Only curves with **exactly two observing years** in the record are admitted
(Amendment 28 excludes the others). With the rounded ratio, a stopped round is **definitely
admitted** when its whole rounding interval lies at or below 3, **excluded** when it lies above 3,
and **ambiguous** otherwise; the bound is given twice, with the definite rounds only and with the
ambiguous ones too (the optimistic one). **The optimistic, descriptive bound:** every admitted round counted as PASS
(T4 never gives FAIL; its PASS gates — replicas at `R` at every `dP`, the hidden noise determined, a
finite measurement, the SNR above the calibrated threshold — assumed met), every other round as
recorded; the target by specification B (and by the legacy rule, for reference); per noise model.
What still blocks: the targets left INCONCLUSIVE, by the kinds of their undecided rounds.

**c. The undetermined hidden noise.** The engine's causes (`holdout.py`, `replica_stats`, lines
619 to 694; `derive_round`, lines 1795 to 1800; `rednoise.py`): (i) the hidden noise model
undetermined (the record's field `hidden_noise_undetermined` is `true`): no replica band covered,
or every sector excluded by A1 (too few bins at the scale, or no noise scale); (ii) the noise
determined (the field `false`) but the replica count below `R` at some `dP`; (iii) fields missing
or inconsistent, reported apart. The stage alone (`hidden_noise`) does not separate (i) from (ii).
Read, per cause and noise: by layout and hidden year; the grid's size; the fraction of `dP` points
below `R`; whether every count is zero (an empty count list named apart); the largest count. Which
of (i)'s sub-causes, and how many replicas were registered: **not identifiable** with these
records (not recorded). Whether the engine observes it: from the code. Whether a planned front
treats it: from the committed plans.

**d. The combined optimistic bound.** Every round INCONCLUSIVE by a capacity decision, by the
timing rule and by the undetermined hidden noise counted as PASS, every other round as recorded; in
two readings: (d1) the timing rule only in T4's scope (two observing years, `σ_T/T14 ≤ 3` with the
ambiguous rounds included), (d2) every timing round;
per noise model and regime, legacy and specification B; standardized to the population study's
quotas (150, 50, 50) against the **195** of C1 and C3, and per regime against G1's counts (101 of
150; 37 of 50). The same caveats as the viability check: a reading of these records, not an engine
run, not a bound on a future sample or on the final configuration.

## Outputs

`two-year-reading.json` and `two-year-geometry.json` beside this file, by
[scripts/two_year_reading.py](scripts/two_year_reading.py) (written with this declaration, run
after its commit), and a short results section in [README.md](README.md).
