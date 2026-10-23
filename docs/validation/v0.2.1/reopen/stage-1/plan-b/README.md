# Plan B: the restricted validation of v0.2.1 (adopted and frozen on 2026-10-23; nothing run)

> **Adopted by the maintainer on 2026-10-23** ("OK, adotar o plano B (67b5a6e) e congelar"):
> sections 1.1 and 1.2 are applied, in the same commit, to `ROADMAP.md` (v0.2.1, scope amendment B)
> and to `docs/validation/v0.2.1/population-study.md` (Amendment B). **The design is frozen:**
> optional improvements go to the backlog; only a problem of validity, safety or execution reopens
> it. The work follows the gates of section 7, each execution with its own authorization.

The maintainer's decisions of 2026-10-23 on proposal B (`23f72f8`), consolidated in `649d4f4`,
then one final revision (the domain, the real controls, X7's failure, the budget's label, the
gates). **No lot is authorized here; every execution keeps its own, later authorization.** On
the maintainer's short OK, the texts of section 1 are applied in one commit and **the design is
frozen**: optional improvements go to the backlog; only a problem of validity, safety or execution
reopens the plan. **B does not turn the original study into a success:** it is a restricted,
prospective validation, informed by negative development results; the original four-group claim
stays not validated, and every earlier FAIL is kept.

The arithmetic: [scripts/budget_b.py](scripts/budget_b.py) → [budget-b.json](budget-b.json), and
the sizing of [../scope-b/scripts/sizing_b.py](../scope-b/scripts/sizing_b.py) →
[../scope-b/sizing-b.json](../scope-b/sizing-b.json).

## 1. The amendments (texts to apply on adoption)

### 1.1 ROADMAP.md, v0.2.1 (inserted after the paragraph "Population study closed by a scope decision on 2026-10-14")

> **Scope amendment B (adopted on <date>, by the maintainer).** The validation of v0.2.1 is
> restricted to one **profile proposed for validation**, `three-observing-years/1`: light curves
> inside an **operational domain** defined by quantities read before any hidden flux is accessed
> (exactly three observing years, one sector in each, two-minute cadence, the sectors' coverage and
> the spacings between the years, within declared tolerances; the population study's Amendment B).
> It becomes a validated profile only when its confirmation and its replication succeed; a curve's
> membership is not demonstrated performance, and a note in a dossier does not make the profile
> validated. Curves outside the domain are reported INCONCLUSIVE ("outside the validated scope")
> under the profile, with each available test result kept in the dossier as a diagnostic of no
> verdict value. The synthetic population study is run on a new population generated for this
> domain (`population_v4`; the earlier generators unchanged), with the sizes, criteria and
> acceptance counts of the population study's Amendment B, fixed before any new result. The
> original four-group population study and its FAILs (development campaign 1, M0 to M3), the R_min
> study, and stage 1's development readings are kept as results; this amendment does not make them
> a success, and the original claim stays not validated. A widening beyond the domain (the timing
> rule's T4, the undetermined hidden noise, other geometries) is future work with its own
> specifications.

The exit criteria are unchanged in their wording; when the amendment is applied, their notes say
that the synthetic population study, its confirmation and the new calibration are those of the
profile (the calibration's targets drawn inside the domain), and that the phase closes only after
the calibration, its dossier reviews and every other exit criterion.

### 1.2 docs/validation/v0.2.1/population-study.md, "Amendment B" (a new section)

> **Precedence.** For the profile `three-observing-years/1` only, this amendment supersedes the
> population, the sizes and the SNR bands' quotas of sections 2 and 4 and the confirmation's
> population of section 5; sections 1 (the criteria), 3 (the SNR bands' definition), 5 (the rule of
> development and confirmation) and 6 to 12 apply as written. For every earlier version, the
> original sections, records and procedures stand unchanged.
>
> **The input of the domain** (the same for the profile O2 and for the generator's check): per
> sector, the product's cadence timestamps and quality flags, the cadences kept by the plan's
> quality mask, **before any filter that reads a flux or flux-error value** (the adapter today drops
> non-finite flux before it builds the spans, `adapter.py`, lines 440 to 455; the profile's
> implementation records the pre-filter timestamps' summary per sector so that the domain never
> depends on a flux value); in the synthetic harness, the generated timestamps. Each sector is
> labelled by the year of its first kept cadence, as the adapter does (`adapter.py`, line 577).
> Definitions: a sector's **span** is its last kept timestamp minus its first plus one cadence; an
> **internal gap** is an interval between consecutive kept timestamps longer than 10 minutes; the
> **orbit gap** is the sector's longest internal gap, and the two parts on either side are its
> **orbits**; its **coverage** is the number of kept cadences times 120 s over its span.
>
> **The operational domain** (tolerances fixed here, before any result):
> - **D1, years:** exactly three observing years (the distinct year labels of the sectors; the
>   engine's count, `holdout.py`, line 1910). Never a selection of three years out of a longer
>   curve.
> - **D2, sectors:** exactly one sector in each observing year (three sectors).
> - **D3, cadence:** the two-minute cadence (full-frame-image cadences are outside): every interval
>   between consecutive kept timestamps that is not an internal gap equals `k × 120 s` within
>   ± 0.5 s, with `k` from 1 to 4 (`k − 1` missing cadences: an isolated masked cadence gives about
>   240 s); the residual `interval − k × 120 s` is the timing tolerance; the missing cadences count
>   toward the coverage of D4.
> - **D4, each sector:** each orbit 12.5 to 14.0 d long; the orbit gap 0.5 to 2.0 d; at most four
>   other internal gaps, each at most 6 h; coverage at least 0.84.
> - **D5, spacings:** the two separations between consecutive sectors' first timestamps, each
>   either **about one year** (345 to 385 d) or **about two years** (710 to 750 d), **at most one**
>   about two years.
>
> **Why these properties and these widths.** The holdout's train ephemeris and its extrapolation to
> the hidden year depend on the times through differences: the separations (D5) set the lever of
> Amendment 28's timing diagnosis, the sampling (D3) and the orbits, gaps and coverage (D4) set the
> windows' and the replica bands' coverage. The widths are design choices, fixed before any result:
> ±20 d around one and two years change the extrapolation's lever by about 5% and 3%, inside one bin
> of the stopped fraction's steep dependence on the lever read in the two-year diagnosis
> ([../viability/two-year-results.md](../viability/two-year-results.md), section a); D4 keeps a
> two-orbit sector with one downlink-like gap and limited losses; D3's ±0.5 s is far below the
> windows' width (hours) and the cadence the plan assumes (`exptime_seconds` 120). **Their adequacy
> for real sectors is not claimed:** a real sector outside them is outside the domain.
>
> **The calendar date.** The timing geometry depends on differences only, but the complete engine
> is not invariant under a shift of every date: the prewhitening bins the **absolute** phase
> (`prewhiten.py`, lines 136 to 158, which decides the components it accepts), so a shift changes
> its statistic. The domain therefore names no calendar year; the generator draws the first sector's
> start uniformly over one year, which randomizes the absolute phase of every variability period it
> injects (0.3 to 5 d), so the population represents the date's effect statistically; no
> equivalence for a particular date is claimed.
>
> **The represented geometries** (the generator's primitive proposals use the uniform
> distributions listed here, followed by the declared rejection; the realized quantities, some of
> them derived, such as the coverage, or shaped by the rejection, must meet acceptance 2; the same
> available geometries for every class, allocated with the declared rounding): **G-a**, both separations about one year; **G-b**, one about one year and one
> about two years, in either order (50 : 50); each separation uniform in its interval; the first
> sector's start uniform over one year from 1325.0 BTJD; each orbit's length uniform in 12.5 to
> 14.0 d; the orbit gap uniform in 0.5 to 2.0 d; from 0 to 4 loss blocks (uniform count), each of a
> length uniform in 10 min to 6 h, placed uniformly inside the orbits; single-cadence losses at a
> rate uniform in 0 to 5%, never four or more adjacent; each timestamp jittered uniformly by ±0.25 s
> (so every residual of D3 stays within ±0.5 s; the residuals' distribution is triangular, not
> uniform). The coverage floor 0.84 of D4 is an acceptance floor: the generator's lowest coverage is
> about 0.844, so the floor itself is not claimed as generated. A draw that would fall outside D1 to
> D5 (for example a sector across a year boundary) is redrawn by the generator's own rule, recorded
> with its reason, never by an engine output.
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
> (`var_absent_year`) keeps its uniform draw over three positions, mapped to the curve's own three
> observing years, so that exactly two observed years carry variability in every
> `variability_some_years` planet.
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
> the **main confirmation** (X6: B2, seeds from a future drand round declared before, run once at
> the end on frozen code); the **independent replication** (X7: the same composition and sizes, its
> own drand round declared at its own checkpoint after X6's result and before that round is
> available, run only if X6 passes). **The configuration is chosen on development data and frozen
> before X6**; nothing is chosen on X6's or X7's data. **The synthetic study passes only if X6 and
> X7 both pass.** Spec C's confirmation is a separate lot (an error model's confirmation, not the
> population study).
>
> **If X7 fails after X6 passed:** the failure is a result and is never ignored; both lots are
> reported in full; neither is chosen as the more favourable one, and they are never pooled to pass;
> the synthetic study is not accepted and the profile stays proposed for validation; the calibration
> on real targets does not start; any later attempt needs the maintainer's recorded decision, under
> the rule for criterion failures (an amendment declared after the result, Codex's design review,
> new seeds, the same criteria and sizes), with its own authorization.

## 2. The domain and the treatment outside it

- **The domain:** D1 to D5 of section 1.2, on the input it defines (the kept timestamps and
  quality flags, before any flux-based filter): no flux value of any year; any further property
  only if defined before, by quantities of the same kind.
- **What it does not claim:** capacity in every time geometry. Other spacings (for example two
  separations of about two years), cadences and coverages are outside the domain, not validated;
  no equivalence for a particular calendar date is claimed (section 1.2, the calendar date).
  Until the confirmation and the replication succeed, the profile is **proposed for validation**,
  not validated, whatever a dossier says.
- **Outside the domain (O2):** a new, versioned profile (`three-observing-years/1`) in the plan's
  configuration; with it, a curve outside D1 to D5 gets the target verdict INCONCLUSIVE with the
  reason "outside the validated scope", naming the first condition it fails; the tests that are
  computed stay in the dossier as diagnostics with no verdict value. Without the profile (every
  earlier configuration), the engine behaves exactly as today: no historical result changes, and
  every earlier version reproduces (tested, as the X1 and X1b switches were).
- **The reach analysis** (after 2026-10-27, its own declaration and authorization) informs the
  profile's utility and a future widening; it does not decide this attempt's domain.

## 3. The new generator: specification and acceptance (acceptance before tests and code)

**What it is:** `population_v4.py`, a new module; `population_v2.py` and `population_v3.py` stay
unchanged (their pinned SHA-256 checked). It reuses `population_v2`'s parameter distributions and
noise models by import (`draw_parameters`, `_place_in_band`, `_noise`, the bands), so the signals
are the protocol's; new are only the layouts and their coverage (section 1.2) and the mapping of
the variability-free year to the curve's years.

**Its acceptance criteria, committed before its tests and code:**
1. **The domain:** every case of every class meets D1 to D5, checked on the generated curves by the
   domain function (the same one the profile O2 uses), on section 1.2's input and definitions.
2. **The domain covered, every dimension:** over each population, the drawn separations, the
   first sector's start, the orbit lengths, the orbit gaps, the loss blocks' count and lengths, the
   single-cadence loss rates and the timestamps' jitter span their declared intervals (each
   interval's thirds all populated in every class and noise model); and, checked apart, the
   realized D3 quantities (the counts of intervals with `k` = 1, 2, 3 and 4, and the timing
   residuals' range) and D4 quantities (the orbits, the gaps, the coverage) populate the thirds of
   their realized ranges.
3. **Compatible layouts across classes, by exact counts:** within each class, noise model, band
   (where the class has one) and regime or mechanism, G-a and G-b hold the declared allocation
   exactly (G-a taking the extra case of an odd count: for example 126 and 124 among 250 measurable
   false positives, 180 and 180 among 360 planets), checked by counting, not by a classifier; the
   rounding leaves small, declared differences, not a literal absence of information.
4. **The classes, mechanisms and variability of the protocol:** the planets' regimes, the four
   false-positive mechanisms (63, 63, 62, 62 for 250), the three no-transit mechanisms (40%, 30%,
   30%, rounded as section 4); the noise models white and AR(1) with `population_v2`'s parameters;
   exactly two observed years with variability in every `variability_some_years` planet; the other
   variability mechanisms (`variability_masked`, `trend_variability`) unchanged.
5. **An independent band check:** for every case with an injected transit, every expected SNR the
   band uses (global, each year's train and each hidden year) recomputed by a separate script (not
   the engine, not the generator's own function) and equal to the generator's within a relative
   tolerance of 1e-9; for every curve without a transit, no injected transit in its model.
6. **No adaptation of the signals to help approval:** the parameter distributions are those of
   `population_v2`, never redrawn or filtered by any engine output; every redraw is the generator's
   own declared rule (band, depth limit, the domain), recorded with its reason.
7. **Determinism:** three generations (different worker counts and orders) byte-identical, as the
   development manifest's.
8. **The correspondence with X2f:** X2f's cases (`population_v2`, `three_years` and
   `variability_some_years`: one full sector in 2018, 2019 and 2020, separations 375 and 361 d,
   orbits of 13 d, the orbit gap 1 d, no loss, coverage about 0.963) lie inside D1 to D5, in G-a;
   checked by the domain function. They are one point of the domain (no jitter, no loss, one
   date), not its whole.
9. **Tests first, then the code, then sabotages** (each acceptance criterion broken once and
   caught), and Codex's review, before any population is generated for a lot.

## 4. The population B2, the criteria and the sizing

As section 1.2. The sizes ([../scope-b/sizing-b.json](../scope-b/sizing-b.json), design B2) are
**accepted as the sizing, without a promise of success** (the maintainer's decision of
2026-10-23). The holdout's necessary count (275 of 360 measurable planets per noise model, from C1
and C3) is a necessary condition, never a success criterion, and takes no second adjustment.

## 5. The real controls' availability, checked early (before X2f and the large populations)

Part of gate 3, after the environment that will download is checked (certifi corrected, the lock
diff read), **before X2f and before any large population is generated**; catalogues and metadata
only; its own declaration, committed before its queries, and its own authorization.
- **The minimum, fixed now:** the new calibration (gate 13) keeps v0.2's structure, 10 confirmed
  planets and 10 known false positives (ROADMAP, v0.2's closing note: 10 of 10 planets, 7 of 10
  false positives); the check requires **at least 20 confirmed planets and 20 known false
  positives screened inside the domain** (a draw and a reserve of equal size), after the
  exclusions below. This is an operational minimum (ten per class and an equal reserve), not a
  demonstration of statistical adequacy, nor a guarantee that ten per class will meet the
  conditions checked later.
- **Metadata-screened candidates:** D1, D2 and D5 (the sectors, their years, their dates) and D3's
  exposure time from the archive's metadata; **D3's measured intervals and D4 need the products'
  timestamps and are not checkable from metadata alone**, so the counts are of metadata-screened
  candidates, the timestamp conditions pending until the calibration's own selection.
- **Excluded:** every target used in the v0.1 and v0.2 calibrations and in development, as the
  ROADMAP requires, from an **explicit inventory recorded in the check's declaration** (the
  calibration claims of v0.1 and v0.2, their development and debugging targets, the audit of known
  targets, `docs/validation/v0.2.1/reopen/audit-known-targets.json`; the runs of
  `pre-document-runs.md` are synthetic and add none).
- **The data products:** each eligible target's two-minute light curves and target pixel files for
  its three sectors, listed as available in the archive.
- **Recorded:** the sources (for example the NASA Exoplanet Archive for confirmed planets, ExoFOP
  for the TOI dispositions, MAST for the products), each with its URL and the date read; the
  selection criteria, fixed before the queries; the counts; and, if the maintainer wants it, the
  reserve list.
- **Never:** a light curve analysed; a target chosen or excluded by an expected outcome of the
  engine. This shows **availability, not approval**.
- **If the minimum is not reached:** X2f stays blocked and the decision goes back to the
  maintainer. **The domain is never widened to accommodate the targets found.**

## 6. X2f reduced, spec C's confirmation, and the roles

- **X2f = S1 + S2** (no S3): 184 independent cases, 18 400 realizations; after gate 3 (the update
  and the controls' check), with the environment fixed and recorded before S1 and unchanged until
  S2 ends; its declaration ([../after-x2e/x2f-declaration.md](../after-x2e/x2f-declaration.md))
  and the code (`X2F_SEQUENCE`) lose S3 on adoption, with their tests, before X2f runs.
- **The correspondence:** X2f's cases are `population_v2` cases of the layouts `three_years` and
  `variability_some_years`: inside the domain, in G-a, with the protocol's parameter distributions;
  spec C's choice is made on that part of the domain. **Spec C's confirmation** runs on
  `population_v4` (the whole domain, G-a and G-b), seeds from a future drand round, the same regimes,
  sizes and criterion, for the chosen candidate only, once; its conclusion concerns that mixture,
  not each geometry apart; a failure is recorded, blocks the gates after it, and no second candidate
  is tried on its data.
- **The roles:** X6 is the main confirmation of the synthetic population, X7 its independent
  replication; the calibration on real targets and the final review stay required to close the
  phase. **No result of X2f alone approves v0.2.1.**

## 7. The gates, in order, and what each needs

| # | Step | Needs before | Its result |
|---|---|---|---|
| 0 | Adoption: sections 1.1 and 1.2 applied in one commit; the design frozen | the maintainer's OK | the profile and the protocol in force |
| 1 | The generator `population_v4` (with the domain function): acceptance record, tests, code, sabotages, Codex | 0 | the generator accepted; no lot yet |
| 2 | The profile O2 in the engine (the same domain function): acceptance, tests (earlier versions unchanged), code, Codex | 1 | the profile available, off by default |
| 3a | The dependency update (2026-10-27): the whole lock diff read (a change of the numeric stack stops for the maintainer); the downloading environment checked | 0 | the final environment, recorded |
| 3b | The real controls' availability check (section 5; its declaration and authorization) | 3a, 1 | enough controls, **or X2f blocked and the decision back to the maintainer** |
| 4 | X2f S1, then S2 (its authorization) | 3b sufficient, and X2f's code without S3 | the choice data |
| 5 | Spec C's analysis (C5), then the chosen candidate's code (C8) with tests, sabotages and Codex | 4 | the error model chosen, or none |
| 6 | Spec C's confirmation on `population_v4` (a drand round declared before; its authorization) | 1, 5 | confirmed, or failed: a failure blocks the gates after it |
| 7 | X3 (b and s) on `population_v4`, then X4 (the criteria's compatibility, arithmetic) | 6 | the thresholds, the compatibility |
| 8 | X5, the pilot, on the development population (the complete engine, the profile on), and the before-and-after comparisons of each change on its identical inputs (its authorization) | 2, 7 | yields, the final configuration's measured cost, the comparisons |
| 9 | **The gate before X6:** X6's and X7's sizes from X5's yields (B2 and the holdout criteria's minima), checked against the budget | 8 | X6 declared, **or a new investment decision** |
| 10 | X6, the main confirmation: B2, once, frozen code; C1 to C6, G1 to G6 **and the holdout criteria** (B5, W1e) (its authorization) | 9 | passed, or failed (which ends the synthetic study: X7 does not run) |
| 11 | X7, the independent replication (its drand round declared at its own checkpoint; the same composition and sizes; its authorization) | 10 passed | passed, or failed (section 1.2: the study not accepted) |
| 12 | **The synthetic study's review** (an independent review of X6 and X7) | 11 passed | the synthetic study accepted, or not |
| 13 | The new pre-registered calibration on real targets inside the domain (**its own protocol, lock, budget and authorization**), its dossier reviews, the remaining exit criteria; **then the v0.2.1 phase gate** | 12 accepted | the phase closed, or not |

## 8. The budget up to X7, and the stop rules

**What this budget is:** about **129 h of wall time and about 2112 LP-h, cumulative up to X7**,
including the earlier consumption and every step at its ceiling (1.5 times its estimate) **at its
minimum planning size** ([budget-b.json](budget-b.json)). It is **not** a demonstrated budget of
the complete phase: **the real calibration of gate 13 has its own budget, not estimated here**, and
the statistically necessary sizes of X3, X5, X6 and X7 may exceed these floors.

| Item | LP-h | Wall |
|---|---|---|
| Consumed: the lots | 386.2 | 51.2 h |
| Consumed: the local suites whose JUnit files are kept (24 processors × their wall time, a proxy, not measured CPU) | 104.9 | 4.4 h |
| The new generator: four populations (development, main confirmation, replication, spec C's confirmation), three generations each, at the dev population's measured cost, and 20 LP-h of self-tests (an allowance) | 75.3 | 3.1 h |
| The real controls' availability check (queries only; an allowance) | 0 | 2.0 h |
| X2f S1 + S2 (the declared ceilings) | 302.5 | 13.75 h |
| Spec C's confirmation (as S1 + S2) | 302.5 | 13.75 h |
| X3 on three-year curves (1300 curves, a planning size) | 33.4 | 1.5 h |
| X5, the pilot (1500 curves, a planning size) | 38.5 | 1.75 h |
| The before-and-after comparisons (2 changes, on X5's inputs) | 77.0 | 3.5 h |
| X6, B2's floor (5860 curves: white 3730, correlated 2130) | 150.4 | 6.8 h |
| X7, as X6's floor | 150.4 | 6.8 h |
| The local suites and mandatory checks ahead (20 rounds, one full suite each, the proxy, 1.5 times) | 490.7 | 20.4 h |
| **Total, cumulative, at the ceilings and the minimum sizes** | **about 2112** | **about 129 h** |
| **Left of 4000 LP-h and 200 h** | **about 1888** | **about 71 h** |

- **Conditional funding through successive gates:** the steps up to X7 fit the ceiling **at their
  floors** (at the highest cost per curve measured, 61.6 LP-s on X2's diagnostic runs; the complete
  analysis of the earlier configuration cost about 17.7). The statistically necessary completed
  studies are **not yet shown to fit**.
- **Where a new investment decision may be needed:** **gate 9** decides whether X6's yield-derived
  minima (B2 and the holdout criteria, for example Amendment 26's 866 eligible constant targets per
  group) and X7 fit what is left in LP-h and wall time. It is not necessarily the first stop: any
  earlier declaration or measured cost that exceeds the allowance stops the work at its own gate.
- **The stop rules:**
  - each lot stops submitting at its ceiling; what ran is evaluated as its declaration says;
  - a failed task stops the sequence for the maintainer;
  - at every gate, the consumed plus the next step at its ceiling plus the later steps at their
    floors must fit 4000 LP-h and 200 h, or the work stops for the maintainer;
  - a change of the numeric stack in the lock's diff stops the work;
  - too few real controls (gate 3b) block X2f, and the domain is never widened for them;
  - a criterion whose required coverage or minimum is not reached is not met, and approval fails;
  - a failed confirmation (spec C's, X6) or replication (X7) blocks every gate after it;
  - a failed criterion is a result, under the maintainer's rule for criterion failures (an
    amendment declared after the result, Codex's design review, new seeds, the same criterion and
    size); any later attempt needs a recorded decision of the maintainer and its own
    authorization;
  - **a sample is never reduced below its declared size to fit the clock**, and the ceiling never
    rises after an unfavourable result;
  - the CI is tracked (job-hours, storage, runners, durations), never blocked automatically.

## 9. For adoption

A short OK from the maintainer adopts this version: sections 1.1 and 1.2 are applied in one commit
(the date filled in), and the design is frozen. After that, the work follows the gates of section
7, each execution with its own authorization; optional improvements go to the backlog, and only a
problem of validity, safety or execution reopens the plan.
