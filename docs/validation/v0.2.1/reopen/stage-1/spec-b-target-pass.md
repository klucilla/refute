# Specification B: the aggregation of a target's rounds (the target's PASS)

The maintainer's decision of 2026-10-21, item B: specified now, before the pilot, without waiting
for another lot. The failure it answers is already shown: in `AR(1), variability`, 26 PASS among the
241 **decided** disappearing targets at R = 8 (10.8%; the fraction is of that group's decided
targets, never of its 6400), none of them seen by the study's criteria
([../rmin-study/diagnosis/README.md](../rmin-study/diagnosis/README.md), problem 5). A specification
only: no lot, no code. The change needs its own validation (B6).

## B0. The rule today

`holdout.run_holdout` (and `rmin_evaluate.aggregate` for the studies): any FAIL round gives FAIL;
**otherwise any PASS round gives PASS**, even when other years are INCONCLUSIVE; otherwise
INCONCLUSIVE. So a target whose altered year could not be decided can PASS on another year.

## B1. The necessary years, fixed before any round

The **necessary years** of a target are **all the observing years of its light curve as the engine
receives it**: `raw.years`, the distinct years of the cadences given to `run_holdout` (from the
sectors' metadata). Each is hidden once, by its own round. This set is fixed from the metadata
alone, before any round runs, and never from a round's outcome or from anything a round computes
(the train ephemeris, the predicted windows, the capacity). The claim the test supports is "the
predicted signal is detected in every observing year when that year is hidden".

(Considered and not adopted: a subset of the years, for example the years with a predicted transit
window; it would read the train ephemeris, a quantity computed by the round, and so is excluded.)

## B2. The aggregation

In this order:
1. **A valid FAIL takes precedence:** if any round's status is FAIL, the target is FAIL. A valid FAIL
   is a FAIL of `holdout.fail_rule` reached after both capacity decisions passed and the measurement
   succeeded (the only way the engine produces a FAIL); its years are listed.
2. **Otherwise, PASS needs evidence in every necessary year:** if every necessary year's round is
   PASS, the target is PASS.
3. **Otherwise, INCONCLUSIVE:** a PASS in another year does not settle a necessary year left
   INCONCLUSIVE. The reason is `necessary_years_undecided`, with each undecided year and its round's
   reason, and the years that did PASS.

The coverage of a PASS is the windows measured in all its rounds; of a FAIL, as today; of an
INCONCLUSIVE, the windows of its conclusive rounds, as today (zero coverage is never PASS). The same
function serves the engine and every study's evaluator; no second implementation.

## B3. Examples with their expected outcomes (rounds in year order)

| Rounds | Today | Under B |
|---|---|---|
| PASS, PASS | PASS | **PASS** |
| PASS, PASS, PASS | PASS | **PASS** |
| PASS, INCONCLUSIVE | PASS | **INCONCLUSIVE** (`necessary_years_undecided`: the second year) |
| INCONCLUSIVE, PASS, PASS | PASS | **INCONCLUSIVE** (the first year) |
| PASS, FAIL | FAIL | **FAIL** |
| INCONCLUSIVE, FAIL | FAIL | **FAIL** |
| FAIL, PASS, INCONCLUSIVE | FAIL | **FAIL** |
| INCONCLUSIVE, INCONCLUSIVE | INCONCLUSIVE | **INCONCLUSIVE** |
| PASS, INCONCLUSIVE `no_predicted_window` (a necessary year without a predicted window) | PASS | **INCONCLUSIVE** (`necessary_years_undecided`: the second year, reason `no_predicted_window`) |
| FAIL, INCONCLUSIVE `no_predicted_window` | FAIL | **FAIL** (a valid FAIL keeps its precedence) |
| one year only (the engine already refuses: fewer than 2 years) | INCONCLUSIVE | **INCONCLUSIVE** (unchanged) |

(The two `no_predicted_window` rows were added on 2026-10-21 at the maintainer's request, before
the tests and the code of X1b: the X0 records never reached that reason, so B's behaviour there was
not exercised. They follow from B2 as written; no rule changed.)

## B4. The controls, positive and negative (synthetic, fixed before the code)

Each control is a synthetic case with its expected target outcome, in white and in AR(1) noise, with
two and with three observing years:
- **C1, positive:** a constant planet whose every round passes the decisions and is measured (a
  strong signal, a well-sampled hidden year in each round): **PASS**.
- **C2, negative, precedence:** a disappearing planet (the last year without the signal) whose
  last-year round is measured and FAILs, the other rounds PASS: **FAIL**.
- **C3, the problem-5 case:** a disappearing planet whose last-year round is stopped before the
  measurement (for example its hidden year's replicas below `r_min`, or the hidden noise
  undetermined), the other rounds PASS: **INCONCLUSIVE** (today PASS).
- **C4, the cost of the rule:** a constant planet whose last-year round is stopped the same way, the
  other rounds PASS: **INCONCLUSIVE** (today PASS), reported as abstention, not as an error.
- **C5, refusal:** a curve with no transit, or with a train candidate rejected before the capacity
  rule: **never PASS**.
- **C7, a necessary year without a predicted window** (added on 2026-10-21, before the code): a
  planet whose last-year round stops with `no_predicted_window`, the other rounds PASS:
  **INCONCLUSIVE** (today PASS); the same with another round FAIL: **FAIL**.
- **C6, no leak:** changing year Y's hidden flux leaves unchanged, **in the round that hides Y**,
  the train-only preparation and every decision made **before any hidden datum is read** (the train
  candidate, the ephemeris, the timing rule, the train replicas and decision 1; the existing
  blindness property, `tests/test_holdout_blindness.py`, kept). The hidden-noise estimate and
  decision 2 come after the hidden replicas are read and may legitimately change, as may the other
  rounds, which train on Y.

Plus unit tests of the aggregation over every row of B3 and over every permutation of the round
order (the outcome does not depend on the order), and **completeness checks**: exactly one round per
necessary year, else the aggregation refuses (an error, never an outcome) for a missing year, a
duplicated year, a year not in `raw.years`, or an empty list of rounds; and the existing guard of
fewer than two observing years (INCONCLUSIVE before any round) kept for zero and one year. The
studies' evaluator (`rmin_evaluate.target_outcomes`, which keys the rounds by year) uses the same
function and the same checks.

## B5. The criterion of false PASS per target, and what is reported

In a corrected study, for the **disappearing** scenario, per group in scope and per R:
- **The false PASS per target:** the fraction of PASS among **all decided targets** (aggregated PASS
  or FAIL, final outcome under B), **including** the targets the old power filter left out (those
  whose last-year round did not pass both decisions); its one-sided Clopper-Pearson upper bound at
  the study's level ≤ **L**. Proposed `L` = 0.02 (the false-FAIL limit), **for the maintainer**,
  with a minimum of decided targets set by the sizing.
- **Reported apart, never merged:** the error among the decided (above); the utility over **all**
  targets (decided / total) under B **and** under today's rule on the same records, so that the rise
  of INCONCLUSIVE is shown; the targets turned from PASS to INCONCLUSIVE by B, per scenario; and,
  for the constant scenario, the false FAIL: its **count** is unchanged by B (FAIL keeps its
  precedence), but its **fraction among the decided** can change, because PASS targets become
  INCONCLUSIVE and leave that denominator; so both FAIL / decided and FAIL / total are reported,
  with the decided count, under B and under today's rule.

## B6. What this needs before it counts: implementation is not adoption

Revised on 2026-10-21 (the maintainer's decision after X0 and X1, item 2), before the tests and the
code of X1b. The change is a change of the engine's verdict rule, in two separate steps:

1. **Implementation (X1b, authorized as experimental):** one function, in the engine, used by the
   engine and by every study's evaluator; reached **only** on the experimental M4 path and only when
   it is asked for by name (`aggregation="spec_b_experimental"`), never by default and never from a
   configuration file; refused outside the M4 path (the corrections switch off). The legacy rule
   stays the default everywhere, with its outputs unchanged, and every frozen record (the R_min
   study, the diagnosis, X0, the v0.3 dossiers) keeps its bytes and its reading. Its acceptance
   record ([x1b-acceptance.md](x1b-acceptance.md)), the tests before the code, the controls above
   and a Codex review are what X1b needs. Implemented, the rule is **not** adopted: no verdict, no
   study result and no dossier uses it.
2. **Adoption (not authorized):** only after its validation inside a corrected study whose criteria
   include B5, with its own authorization; until then no result resting on the blind holdout by year
   is published (the containment of 2026-10-21), and nothing is promoted to SURVIVED.

**What B does not do** (the maintainer's qualification of 2026-10-21, item 5): "no false PASS under
B" means none **observed** in the X0 lot; B does not correct a detection by noise when every year
PASSes (the two last-year detections of X0a, `S_meas` 5.15 and 5.41, were removed only because
another year of those targets was undecided). The threshold is not raised only to remove such cases;
their control comes from the whole operation, evaluated on independent data. And releasing the
gates (X2, X3) is not presumed good: it can bring new PASS and new FAIL, so safety and utility are
measured again.
