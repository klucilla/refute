# Proposal B: a restricted, prospective validation (proposal for the maintainer; nothing adopted)

The maintainer's decision of 2026-10-23 on the two-year diagnosis (`a56757b`): **B as the
direction**, a prospective proposal of a restricted validation with an explicit scope and an
independent confirmation. **Nothing is executed or adopted here**; A (the three fronts complete)
is not authorized now; C (ending the attempt) is not chosen. **B does not turn the original study
into a success:** it is a restricted, prospective validation, informed by negative development
results, and the original four-group claim stays not validated.

The arithmetic: [scripts/sizing_b.py](scripts/sizing_b.py) → [sizing-b.json](sizing-b.json).

## a. The scope amendment

**The operational boundary (proposed): the light curve has at least three observing years**,
counted exactly as `run_holdout` counts them today: the number of distinct values of the
cadences' year labels (`raw.years`, the unique labels of `raw.year`; `holdout.py`, line 1910),
not the number of sectors. It is read before any hidden flux is accessed, so it keeps the
blindness; any further eligibility property must likewise be available before any hidden-flux
access ("observable by the engine" alone is not enough: the engine later observes hidden
measurements too). It is a first boundary, simple and observable, **to be
validated**; it is **not** demonstrated capacity in each year (every round still passes, or not,
its own gates). It is never the synthetic truth, never a layout or mechanism label, and never a
retrospective exclusion of the targets on which the engine failed. Any other property would enter
only if defined before the data, by quantities the engine observes.

**The population covered.** The four groups (white and AR(1), without and with variability) can
stay; what changes is the population and its distribution of layouts. **A finding that shapes it:
in today's generator every false positive and every curve without a transit has two observing
years** (`population_v2.py`, `_layout`, lines 628 to 638: only `three_years` and
`variability_some_years` get 2018, 2019 and 2020; every other mechanism gets 2018 and 2020). The
restricted population therefore needs **a new version of the generator** (the frozen
`population_v2.py` is not edited), giving every class layouts with at least three observing years,
declared before its data, with its tests and its own population identity; the layouts' distribution
(for example three years of one sector each, as `three_years`, or also four) is the maintainer's
choice, fixed before. **The boundary, the generated population and the calibration's coverage
must agree:** X2f's S1 and S2 cases have exactly three years; admitting four-year layouts needs a
prospective justification of their coverage (in the error model's choice and in X3).

**The targets outside the boundary** (two options, the maintainer's choice):
- **O1:** the engine's verdict unchanged; every dossier says "outside the validated scope" and
  makes no claim from the validation.
- **O2 (proposed):** the engine returns INCONCLUSIVE with the reason "outside the validated scope
  (fewer than three observing years)", so no SURVIVED or WEAKENED is reported where nothing was
  validated; an engine change, with its specification, tests and review, before the study.
- The trade-off: O1 keeps the verdicts with an explicit disclaimer; O2 abstains outside the scope,
  which also suppresses REFUTED verdicts there, and needs an engine change. **Neither establishes
  the accuracy outside the scope.**

**The changes to the ROADMAP and the protocol (texts to propose, not applied):** the v0.2.1 exit
criterion of the synthetic population study names the restricted population and its boundary;
`population-study.md` gets an amendment (the population, the sizes, the boundary, the treatment of
the targets outside it); the scope rule of [../experiments-plan.md](../experiments-plan.md)
applies: the validated population and where the results stay INCONCLUSIVE are published exactly.
**The earlier FAILs are kept** and cited (development campaign 1, the R_min study, X2 and X2e's
readings, the viability check and the two-year diagnosis).

**What B changes in the declared X2f:** its S3 (the two-year regimes) has no place in a three-year
scope; X2f would keep S1 and S2 (the three-year regimes with and without variability), a change of
a declared lot **before** it runs, never after a result; the maintainer's to decide with B.

## b. The sizing of the restricted population

Every approved criterion keeps its limit and its rule (one-sided 95% exact Clopper-Pearson,
individual); its acceptance count is **recomputed at the new set size**, and its chance of passing
at the protocol's reference rates (design assumptions, not measurements) is given:

The new per-regime objectives G1 and G2 have **no approved reference rate**; the chances below use
**assumptions for the sizing only**, to be fixed by the maintainer: a delivery of 0.70 for G1 and
C1's reference 0.05 for G2, against the protocol's rule of at least 0.80 per criterion.

| Criterion (set) | B1: new, 250 planets per band (125 + 125) | **B2: new, 360 per band (180 + 180)** | B0: hypothetical, 100 per band (50 + 50) |
|---|---|---|---|
| C1 refuted planets ≤ 0.10 (per band and noise) | n 250, pass with ≤ 16, chance 0.875 | n 360, ≤ 26, 0.975 | n 100, ≤ 4, **0.436** |
| C2 flagged false positives ≥ 0.60 (measurable, per noise) | n 250, ≥ 164, 0.942 | the same | the same |
| C3 INCONCLUSIVE ≤ 0.20, planets (measurable, per noise) | n 250, ≤ 39, 0.998 | n 360, ≤ 59, 0.9999 | n 100, ≤ 13, 0.876 |
| C3 INCONCLUSIVE ≤ 0.20, false positives (measurable, per noise) | n 250, ≤ 39, 0.998 | the same | the same |
| C4 false alarms ≤ 0.01 white / ≤ 0.05 correlated | n 2200 / 600, ≤ 14 / ≤ 20, 0.855 / 0.920 | the same | the same |
| C1 and C3 together: holdout PASS needed (measurable planets) | at least 195 of 250 | at least 275 of 360 | at least 83 of 100 |
| G1 delivered ≥ 0.60 per regime (measurable) | ≥ 85 of 125, chance **0.724** at 0.70 | ≥ 120 of 180, **0.855** | ≥ 37 of 50, 0.328 |
| G2 refuted ≤ 0.10 per regime (measurable) | ≤ 6 of 125, chance **0.565** at 0.05 | ≤ 11 of 180, **0.808** | ≤ 1 of 50, 0.279 |

- **B0 is hypothetical**: today's three-year planet quotas with new three-year controls. Today's
  population filtered to three years would have **no false positive and no curve without a
  transit**, so C2, C4 and the false positives' C3 could not be evaluated at all. B0's C1 would
  pass with only 0.44 probability at its reference rate.
- **B1 does not size the per-regime objectives:** at the assumed rates G1 and G2 per regime would
  pass with 0.72 and 0.57. The smallest regime sizes that reach 0.80 at those assumptions are 143
  (G1) and 179 (G2) planets (`sizing-b.json`; the chance oscillates with n by discreteness).
  **B2 is proposed:** 360 planets per band and noise model, 180 in each regime, the false positives
  and the curves without a transit at the protocol's sizes, all with three or more observing years;
  its exact size waits for the maintainer's G1 and G2 assumptions and required probability.
- 0.80 per criterion is **not** 0.80 for the study (`population-study.md`, section 2, and its
  caveat on the fixed mixture of mechanisms, which also applies here).
- The holdout counts (195, 275, 83) are **necessary conditions, never success criteria**; they
  already carry C1's and C3's Clopper-Pearson counts and take no second adjustment.
- **Kept apart:** the choice of the error model (X2f, S1 and S2), its confirmation (seeds from a
  future drand round), and the evaluation of the complete engine (the pilot X5, the main study X6,
  the reserve X7). The criteria's numbers G1 to G6 are fixed before any new data (the maintainer's
  decision of 2026-10-23).

## c. The budget under R1

LP-h and wall time on 22 workers, the known steps at their ceilings (`sizing-b.json`, `budget`):

| Step | LP-h | Wall |
|---|---|---|
| Consumed: the lots, and the suites' proxy | ≤ 386.2 + 19.1 | ≤ 51.2 h |
| X2f's S1 and S2 (the choice): estimate 201.5, at the ceilings | 302.5 | 13.75 h |
| Its confirmation, as X2f | 302.5 | 13.75 h |
| X3 on three-year curves only (about 1300 curves at 61.6 LP-s, ceiling 1.5×) | 33.4 | 1.5 h |
| **Known steps** | **about 1044** | **about 80.2 h** |
| Remaining of 4000 LP-h and 200 h | about 2956 | about 119.8 h (about 2635 LP-h on 22 workers) |

- **The wall time binds first.** What remains is for the pilot X5, the main study X6 and the
  reserve X7 together, each at its ceiling. As an illustration only (X5's size must be redone for
  the restricted population, whose yields are not those of the R_min study): X5 at the old low size
  (56 400 curves) at 61.6 LP-s per curve and its ceiling takes about 65.8 h; X6 and X7 at their
  ceilings would then have about 27 h each: about 23 000 curves each at 61.6 LP-s, about 112 000 at
  12.7.
- **Whether X7 counts inside the 4000 LP-h and 200 h** (it was outside the ceiling until now) is
  the maintainer's choice; B includes the reserve, so it is proposed inside.
- **What these figures are:** 119.8 h is a **planning remainder**: it leaves out the local suites'
  wall time (the 2860 s kept are about 0.8 h; the older ones not recorded) and future mandatory
  checks. X3's 1300 curves are a **planning assumption**: its declaration fixes the calibration's
  coverage under the new layouts, variability mix and yields. The illustration does **not** show
  that X5, X6 and X7, sized as they must be, fit.
- **Under R1** with its proposed further amendment at the gate before X5
  ([../after-x2e/success-viability-effort-proposal.md](../after-x2e/success-viability-effort-proposal.md),
  section 4.1): before X5, the consumed and X5 at its ceiling must fit in LP-h and wall time, at
  the highest cost per curve measured then; **X6's affordability (and X7's, if inside) is decided
  at X6's own gate** from X5's measured cost; nothing is run to measure a cost.

## d. The astronomical reach (a plan; after 2026-10-27, with the downloads released)

1. **First the population the future search means to survey** (for example a magnitude range and
   cadence of TESS targets), defined by the maintainer before any data.
2. **Then, on it,** the fraction eligible by the boundary (each star's distinct observing years,
   from its sectors), and which periods, depths and stellar types are less represented within it.
3. **Method, sample and sources declared before** (for example per-star sector lists from MAST or
   the sector pointings applied to the target list; [../sources/tess-year-coverage.md](../sources/tess-year-coverage.md)
   records that no source found gives the fraction by years); **nothing runs without the
   maintainer's authorization.** It is context for the scope, not a criterion.

## e. The criterion of success on the complete engine

On independent data, with the final configuration frozen: **true planets preserved as candidates
with the correct identity** (G1, with C1 unchanged), **undue refutations and spurious signals
controlled** (G2 with C1; G4 with C4), **false positives recognized** (G3 with C2),
**INCONCLUSIVE bounded** (G5 with C3), C5 and C6 unchanged, and **utility and cost shown** (G6 on
X5's measured cost), each per noise model and regime of the restricted population, the numbers
fixed before the data. Which limits are per regime and which are pooled:

| Limit | Its set | Per regime |
|---|---|---|
| C1 (≤ 0.10 refuted) | each band, each noise model | no (G2 adds the per-regime limit) |
| G1 (delivered, with identity) | measurable band, each noise model, each regime | **yes** |
| G2 (refuted) | measurable band, each noise model, each regime | **yes** |
| C2 / G3 (false positives recognized) | measurable band, each noise model | no; G3 published per mechanism, no limit |
| C3 / G5 (INCONCLUSIVE) | each class, measurable band, each noise model | no; G5 published per regime and mechanism, no limit |
| C4 / G4 (false alarms) | the curves without a transit, each noise model (the mixture) | no; G4 published per mechanism, no limit |
| C5, C6 | as approved | as approved |

## f. Future work to widen the scope (none started)

- **T4 (the timing rule)**, Amendment 28, with its own specification, calibration and evaluation.
- **The undetermined hidden noise**, its cause to be identified first (it is deferred: cause and
  repair not established), then its own specification.
- Only after both, a widening to two-year layouts, with its own validation.

## The decisions this asks of the maintainer

1. The boundary (at least three observing years) and the treatment outside it (O1 or O2).
2. The new generator version and its layouts' distribution (three years, or also four with a
   coverage justification); the population B2 (or another), the split between the regimes, and
   the G1 and G2 sizing assumptions and required probability.
3. X2f reduced to S1 and S2.
4. X7 inside the ceiling or not.
5. The texts of the ROADMAP's and the protocol's amendments (they would be written and reviewed as
   their own step).
6. The astronomical-reach plan's population (after 2026-10-27).
