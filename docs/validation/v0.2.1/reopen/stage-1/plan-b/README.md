# Plan B: the restricted validation of v0.2.1, consolidated (for adoption; nothing run)

The maintainer's decisions of 2026-10-23 on proposal B (`23f72f8`): one consolidated delivery to
close the plan. **No lot is authorized here; every execution keeps its own, later
authorization.** On adoption, the texts of section 1 are applied in one commit, and the work
follows the gates of section 6; optional improvements go to the backlog, and only a problem that
compromises validity, safety or execution reopens the design. **B does not turn the original study
into a success:** it is a restricted, prospective validation, informed by negative development
results; the original four-group claim stays not validated, and every earlier FAIL is kept.

The arithmetic: [scripts/budget_b.py](scripts/budget_b.py) → [budget-b.json](budget-b.json), and
the sizing of [../scope-b/scripts/sizing_b.py](../scope-b/scripts/sizing_b.py) →
[../scope-b/sizing-b.json](../scope-b/sizing-b.json).

## 1. The amendments (texts to apply on adoption)

### 1.1 ROADMAP.md, v0.2.1 (inserted after the paragraph "Population study closed by a scope decision on 2026-10-14")

> **Scope amendment B (adopted on <date>, by the maintainer).** The validation of v0.2.1 is
> restricted to one **profile proposed for validation**, `three-observing-years/1`: light curves
> with **exactly three observing years**, counted as the engine counts them (the distinct year
> labels of the cadences, before any hidden flux is read). It becomes a validated profile only
> when its confirmation succeeds; membership in it is not demonstrated performance for every
> cadence or spacing. Curves with two years or fewer, or with four or more, are outside the
> profile: under it the engine reports them INCONCLUSIVE ("outside the validated scope"), with
> each test's result kept in the dossier as a diagnostic of no verdict value. The synthetic
> population study is run on a new population generated for this profile (`population_v4`; the
> earlier generators unchanged), with the sizes, criteria and acceptance counts of the population
> study's Amendment B, fixed before any new result. The original four-group population study and
> its FAILs (development campaign 1, M0 to M3), the R_min study, and stage 1's development readings
> are kept as results; this amendment does not make them a success, and the original claim stays
> not validated. A widening beyond the profile (the timing rule's T4, the undetermined hidden
> noise) is future work with its own specifications.

The exit criteria are unchanged in their wording; when the amendment is applied, their notes say
that the synthetic population study, its confirmation and the new calibration are those of the
profile (the calibration's targets drawn among those with exactly three observing years), and that
the phase closes only after the calibration, its dossier reviews and every other exit criterion.

### 1.2 docs/validation/v0.2.1/population-study.md, "Amendment B" (a new section)

> **Precedence.** For the profile `three-observing-years/1` only, this amendment supersedes the
> population, the sizes and the SNR bands' quotas of sections 2 and 4 and the confirmation's
> population of section 5; sections 1 (the criteria), 3 (the SNR bands' definition), 5 (the rule of
> development and confirmation) and 6 to 12 apply as written. For every earlier version, the
> original sections, records and procedures stand unchanged.
>
> **The profile.** Exactly three observing years (`raw.years`, the distinct values of `raw.year`,
> as `run_holdout` counts them, `holdout.py`, line 1910), decided before any hidden-flux access.
> Never a selection of three years out of a longer curve. Three calendar years do not show capacity
> in every time geometry: the geometries represented are listed below, and the validation says
> nothing of the others, even inside the profile.
>
> **The geometries represented** (the same available geometries for every class, allocated with
> the declared rounding): two-minute cadence, full sectors of two orbits, one sector in each
> observing year; **G-a**, three consecutive years (sector starts 1325.0, 1700.0 and 2061.0 BTJD:
> 2018, 2019, 2020, the layout of `population_v2`'s `three_years`); **G-b**, three years with one gap
> year (1325.0, 1700.0 and 2420.75 BTJD: 2018, 2019, 2021; full sectors, without `few_train`'s
> first-orbit restriction).
>
> **The population (B2), per noise model** (white; AR(1) correlated; the noise models, mechanisms
> and proportions of section 4): planets, 360 per band (below, near, measurable), 180 without and 180
> with variability (`three_years`-type and `variability_some_years`-type); false positives, below
> 100, near 100, measurable 250, the four mechanisms as section 4 allocates them (for 250: 63, 63,
> 62, 62); curves without a transit, 2200 (white) and 600 (correlated), with section 4's mixture
> (40% pure noise, 30% trend, 30% trend with variability, rounded as section 4). **The layouts:**
> within each class, noise model, band (where the class has one) and regime or mechanism, the cases
> are split between G-a and G-b, G-a taking the extra case when the count is odd. Bands, mechanisms
> and parameters drawn as section 4 from the injected truth only. **The variability-free year**
> (`var_absent_year`) keeps its uniform draw over three positions, mapped to the layout's own three
> observing years (G-b: 2018, 2019, 2021), so that exactly two observed years carry variability.
>
> **The criteria:** C1 to C6 of section 1 unchanged (limits, rule, denominators), their acceptance
> counts at the new sizes: C1 at most 26 of 360 per band and noise model; C2 at least 164 of 250;
> C3 at most 59 of 360 (planets) and 39 of 250 (false positives); C4 at most 14 of 2200 (white)
> and 20 of 600 (correlated). **Added, per noise model and regime in the measurable band:** G1,
> planets delivered as SURVIVED or WEAKENED with signal identity, lower bound at least 0.60 (at least
> 120 of 180); G2, planets refuted, upper bound at most 0.10 (at most 11 of 180). **G3 = C2, G4 =
> C4, G5 = C3**, each with its per-mechanism or per-regime publication and no added limit; G6, the
> cost measured on the pilot fits the budget. One-sided 95% exact Clopper-Pearson, each criterion
> judged individually. **The holdout criteria** of specification B (B5: the false PASS per target,
> upper bound at most 0.02) and of specification A (W1e: the false FAIL at reduced depth, upper bound
> at most 0.02) are binding acceptance criteria of the main study, their sizing rules fixed in the
> pilot's declaration, before the pilot.
>
> **The planning rates** (0.70 delivered, 0.05 refuted per regime) are hypotheses for the sizing,
> not observed performance; a criterion's chance of passing at them (G1 0.85, G2 0.81, C1 0.975) is
> **not** the chance of approving the phase. Criteria and counts are fixed before any new result and
> are never lowered afterwards. A criterion whose required coverage or minimum is not reached is not
> met.
>
> **The populations and their roles:** the **development** population (the pilot, X5, and the
> before-and-after comparisons of each change, section 6 of this protocol, on identical inputs);
> the **confirmation** population (the main study, X6: B2, seeds from a future drand round declared
> before, run once at the end on frozen code; only its result counts as the validation); the
> **reserve** (X7: an independent replication of X6, the same composition and sizes, run only if
> X6 passes). **The configuration is chosen on development data and frozen before X6**; nothing is
> chosen on X6's data. X7's drand round is declared at its own checkpoint, after X6's result and
> before that round is available. Spec C's confirmation is a separate lot (an error model's
> confirmation, not the population study).

## 2. The boundary and the treatment outside it

- **The boundary:** exactly three observing years, counted as the engine counts them
  (`raw.years`; `holdout.py`, line 1910; `types.py`, line 137), read before any hidden-flux access;
  any further eligibility property only if defined before and available before any hidden-flux
  access. Curves with four or more years are outside this version's profile; three years are
  never selected silently out of a longer curve.
- **What it does not claim:** capacity in every time geometry. The represented geometries are G-a
  and G-b; other spacings, cadences and coverages inside the profile are not validated, and the
  protocol says so. Until its confirmation succeeds, the profile is **proposed for validation**,
  not validated.
- **Outside the profile (O2):** a new, versioned profile (`three-observing-years/1`) in the plan's
  configuration; with it, a curve outside the profile gets the target verdict INCONCLUSIVE with the
  reason "outside the validated scope (N observing years; the profile admits exactly 3)"; the tests
  that are computed stay in the dossier as diagnostics with no verdict value. Without the profile
  (every earlier configuration), the engine behaves exactly as today: no historical result
  changes, and every earlier version reproduces (tested, as the X1 and X1b switches were).
- **The reach analysis** (after 2026-10-27, its own declaration and authorization) informs the
  profile's utility and a future widening; it does not decide this attempt's layouts.

## 3. The new generator: specification and acceptance (acceptance before tests and code)

**What it is:** `population_v4.py`, a new module; `population_v2.py` and `population_v3.py` stay
unchanged (their pinned SHA-256 checked). It reuses `population_v2`'s parameter distributions and
noise models by import (`draw_parameters`, `_place_in_band`, `_noise`, the bands), so the signals
are the protocol's; new are only the layouts (G-a, G-b) and the mapping of the variability-free
year to the layout's years.

**Its acceptance criteria, committed before its tests and code:**
1. **The profile:** every case of every class has exactly three observing years by the engine's
   count (`LightCurveData.years`), checked on the generated curves.
2. **Compatible layouts across classes, by exact counts:** within each class, noise model, band
   (where the class has one) and regime or mechanism, G-a and G-b hold the declared allocation
   exactly (an even split, G-a taking the extra case of an odd count: for example 126 G-a and 124
   G-b among 250 measurable false positives, 180 and 180 among 360 planets); compliance with that
   allocation and rounding is checked by counting, not by a classifier. The rounding leaves small,
   declared differences of proportion between classes, not a literal absence of information.
3. **The classes, mechanisms and variability of the protocol:** the planets' regimes, the four
   false-positive mechanisms (63, 63, 62, 62 for 250), the three no-transit mechanisms (40%, 30%,
   30%, rounded as section 4); the noise models white and AR(1) with `population_v2`'s parameters;
   **exactly two observed years with variability in every `variability_some_years` planet** (the
   only mechanism with a variability-free year); the other variability mechanisms
   (`variability_masked`, `trend_variability`) unchanged, variable in every observed year.
4. **An independent band check:** for every case with an injected transit, every expected SNR the
   band uses (global, each year's train and each hidden year) recomputed by a separate script (not
   the engine, not the generator's own function) and equal to the generator's within a relative
   tolerance of 1e-9; for every curve without a transit, no injected transit in its model.
5. **No adaptation of the signals to help approval:** the parameter distributions are those of
   `population_v2`, never redrawn or filtered by any engine output; any redraw is the generator's
   own declared rule (band, depth limit), recorded with its reason.
6. **Determinism:** three generations (different worker counts and orders) byte-identical, as the
   development manifest's.
7. **The correspondence with X2f:** G-a reproduces `population_v2`'s three-year geometry exactly
   (the same sector starts and cadences), checked on a sample against `population_v2`'s layouts.
8. **Tests first, then the code, then sabotages** (each acceptance criterion broken once and
   caught), and Codex's review, before any population is generated for a lot.

## 4. The population B2, the criteria and the sizing

As section 1.2. The sizes ([../scope-b/sizing-b.json](../scope-b/sizing-b.json), design B2) are
**accepted as the sizing, without a promise of success** (the maintainer's decision of
2026-10-23). The holdout's necessary count (275 of 360 measurable planets per noise model, from C1
and C3) is a necessary condition, never a success criterion, and takes no second adjustment.

## 5. X2f reduced, the confirmation, and the dependencies

- **X2f = S1 + S2** (no S3): 184 independent cases, 18 400 realizations; after the update of
  2026-10-27, with the environment fixed and recorded before S1 and unchanged until S2 ends; its
  declaration ([../after-x2e/x2f-declaration.md](../after-x2e/x2f-declaration.md)) and the code
  (`X2F_SEQUENCE`) lose S3 on adoption, with their tests, before X2f runs.
- **The correspondence:** X2f's cases are `population_v2` cases (prefix `refute-v0.2.1-x2-3`) of
  the layouts `three_years` and `variability_some_years`, that is G-a, with the protocol's parameter
  distributions; spec C's choice is therefore made on G-a. **Spec C's confirmation** runs on
  `population_v4` (G-a and G-b in equal parts), seeds from a future drand round, the same regimes,
  sizes and criterion, for the chosen candidate only, once: G-b is first seen there; its conclusion
  concerns that mixture, not each geometry apart; a failure is recorded, and no second candidate is
  tried on its data.
- **Kept apart:** the choice of the error model (X2f), its confirmation, and the evaluation of the
  complete engine (X5, X6, X7). **No result of X2f alone approves v0.2.1.**

## 6. The gates, in order, and what each needs

| # | Step | Needs before | Its result |
|---|---|---|---|
| 0 | Adoption: sections 1.1 and 1.2 applied in one commit | the maintainer's approval of this plan | the profile and the protocol in force |
| 1 | The generator `population_v4`: acceptance record, tests, code, sabotages, Codex | 0 | the generator accepted; no lot yet |
| 2 | The profile O2 in the engine: acceptance, tests (earlier versions unchanged), code, Codex | 0 | the profile available, off by default |
| 3 | The dependency update (2026-10-27): the whole lock diff read; a change of the numeric stack stops for the maintainer | 0 | the final environment, recorded |
| 4 | X2f S1, then S2 (its authorization) | 3, and X2f's code without S3 | the choice data |
| 5 | Spec C's analysis (C5), then the chosen candidate's code (C8) with tests, sabotages and Codex | 4 | the error model chosen, or none |
| 6 | Spec C's confirmation on `population_v4` (a drand round declared before; its authorization) | 1, 5 | confirmed, or failed: a failure blocks the gates after it |
| 7 | X3 (b and s) on three-year curves of `population_v4`, then X4 (the criteria's compatibility, arithmetic) | 6 | the thresholds, the compatibility |
| 8 | X5, the pilot, on the development population (the complete engine, the profile on), and the before-and-after comparisons of each change on its identical inputs (its authorization) | 2, 7 | yields, the final configuration's measured cost, the comparisons |
| 9 | **The gate before X6:** X6's and X7's sizes from X5's yields (B2 and the holdout criteria's minima), checked against the budget | 8 | X6 declared, **or a new investment decision** |
| 10 | X6, the main study: the confirmation population B2, once, frozen code; C1 to C6, G1 to G6 **and the holdout criteria** (B5, W1e) (its authorization) | 9 | the validation of the profile, or its failure (which blocks X7) |
| 11 | X7, the reserve: an independent replication of X6 (its drand round declared at its own checkpoint, before the round is available; the same composition and sizes; its authorization) | 10 passed | the replication |
| 12 | **The synthetic study's review** (an independent review of X6 and X7) | 11 | the synthetic study accepted, or not |
| 13 | The new pre-registered calibration on real targets inside the profile (its own protocol, lock, budget and authorization), its dossier reviews, the remaining exit criteria; **then the v0.2.1 phase gate** | 12 | the phase closed, or not |

## 7. The budget up to X7, and the stop rules

Every step at its ceiling (1.5 times its estimate), in logical-processor hours (LP-h) and wall
time on 22 workers ([budget-b.json](budget-b.json)):

| Item | LP-h | Wall |
|---|---|---|
| Consumed: the lots | 386.2 | 51.2 h |
| Consumed: the local suites whose JUnit files are kept (24 processors × their wall time, a proxy, not measured CPU) | 85.4 | 3.6 h |
| The new generator: four populations (development, confirmation, reserve, spec C's confirmation), three generations each, at the dev population's measured cost, and 20 LP-h of self-tests (an allowance) | 75.3 | 3.1 h |
| X2f S1 + S2 (the declared ceilings) | 302.5 | 13.75 h |
| Spec C's confirmation (as S1 + S2) | 302.5 | 13.75 h |
| X3 on three-year curves (1300 curves, a planning size) | 33.4 | 1.5 h |
| X5, the pilot (1500 curves, a planning size) | 38.5 | 1.75 h |
| The before-and-after comparisons (2 changes, on X5's inputs) | 77.0 | 3.5 h |
| X6, B2's floor (5860 curves: white 3730, correlated 2130) | 150.4 | 6.8 h |
| X7, as X6's floor | 150.4 | 6.8 h |
| The local suites and mandatory checks ahead (20 rounds, one full suite each, the proxy, 1.5 times) | 490.7 | 20.4 h |
| **Total at the ceilings** | **about 2092** | **about 126 h** |
| **Left of 4000 LP-h and 200 h** | **about 1908** | **about 74 h** |

- **Conditional funding through successive gates:** the steps up to X7 fit the ceiling **at their
  floors** (at the highest cost per curve measured, 61.6 LP-s on X2's diagnostic runs; the complete
  analysis of the earlier configuration cost about 17.7), with about 74 h left. The statistically
  necessary completed studies are **not yet shown to fit**: X3's 1300 and X5's 1500 curves are
  planning sizes, fixed by their declarations' precision and sizing rules.
- **Where a new investment decision may be needed:** **gate 9** decides whether X6's yield-derived
  minima (B2 and the holdout criteria, for example Amendment 26's 866 eligible constant targets per
  group) and X7 fit what is left in LP-h and wall time. It is not necessarily the first stop: any
  earlier declaration or measured cost that exceeds the allowance stops the work at its own gate,
  by the rule below.
- **The stop rules:**
  - each lot stops submitting at its ceiling; what ran is evaluated as its declaration says;
  - a failed task stops the sequence for the maintainer;
  - at every gate, the consumed plus the next step at its ceiling plus the later steps at their
    floors must fit 4000 LP-h and 200 h, or the work stops for the maintainer;
  - a change of the numeric stack in the lock's diff stops the work;
  - a criterion whose required coverage or minimum is not reached is not met, and approval fails;
  - a failed confirmation (spec C's, or X6) blocks every gate after it;
  - a failed criterion is a result, under the maintainer's rule for criterion failures (an
    amendment declared after the result, Codex's design review, new seeds, the same criterion and
    size); any later attempt needs a recorded decision of the maintainer and its own
    authorization;
  - **a sample is never reduced below its declared size to fit the clock**, and the ceiling never
    rises after an unfavourable result;
  - the CI is tracked (job-hours, storage, runners, durations), never blocked automatically.

## 8. The maintainer's final decisions (short)

1. Adopt this plan, with the amendments' precedence (section 1.2) and the corrected order of the
   final gates (12, then 13), applied in one commit.
2. The represented geometries G-a and G-b, and the generator's acceptance (section 3).
3. B2 and the fixed counts of G1 (at least 120 of 180) and G2 (at most 11 of 180) per regime.
4. The binding status of specification B's B5 (0.02) and specification A's W1e (0.02), their sizing
   in the pilot's declaration.
5. The roles of the development, confirmation (X6) and reserve (X7) populations, and the budget as
   accounted (section 7).
6. Each execution's own authorization, later: X2f, spec C's confirmation, X3, X5, X6, X7, each drand
   round, and the investment decision at gate 9 if needed.
