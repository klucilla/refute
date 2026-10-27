# The comparative viability package C/D (for the maintainer's authorization; nothing run)

**The maintainer's decision of 2026-10-27**, after plan B ended
([../plan-b/closing-2026-10-27.md](../plan-b/closing-2026-10-27.md)): **one** comparative viability
package, of limited effort and with a defined output, prepared for authorization. **Nothing here
runs before it is authorized; no case is generated now.** Not authorized: generation, T4, a new
domain, any lot. After the screening, the maintainer chooses an executable proposal within the
ceiling, or ends v0.2.1 as not approved.

**What it screens.** On synthetic planets laid on **geometries derived from real TESS metadata**,
the current holdout (its measurement per round, then specification B's aggregation per target) is
run under two candidate geometries of the viability diagnosis
([../viability-3b/report.md](../viability-3b/report.md), section 6, and its
[corrected readings](../viability-3b/readings-corrected.md)):

- **C (H7), evaluated first, as a bounded possibility, without adoption:** exactly three observing
  years, every sector of them kept, any spacing. H7 stays marked as **derived after the
  diagnosis's run**; any later choice is justified by the geometry and this screening's viability,
  **not by the count of controls**.
- **D (H5), a limited comparison:** four or more observing years, every sector kept, any spacing; a
  possible expansion that would need its own sizing. More years can improve the period, but
  specification B needs a PASS in every necessary year, which can reduce the utility.

The screening is **not** a population study, does not choose a domain, and does not measure false
PASS or false FAIL safety (it has no false positives and no curves without a transit).

## 1. The geometries (the composition rule, fixed here)

- **Source:** gate 3b's saved metadata, `.cache/real-controls/mast-rows.json` (SHA-256
  `57fb8a014e8aacc5c0de5fc30dcbf46f6bd8315b30c5642281381fdfd46567c2`, checked first): for each of
  the 911 TICs, its SPOC 120-s light-curve rows (sector, `t_min`, `t_max`, MJD) and its target pixel
  files. Rows of the same sector are consolidated as the viability diagnosis did
  (`viability-3b/scripts/viability.py`, `sectors_of`): the earliest `t_min` (gate 3b's rule) and the
  latest `t_max`. **A geometry** is a set of light-curve sectors with those dates; it carries no
  flux, no class and no catalogue value. Times in BTJD as `MJD − 56999.5` (the barycentric
  correction, at most about 8.3 min, is ignored: it does not change a geometry's eligibility at the
  scales below).
- **Eligible for C:** exactly three distinct years (the UTC calendar year of each sector's
  `t_min`, gate 3b's proxy); a target pixel file for every light-curve sector; **every sector's span
  `t_max − t_min` within 25.5 to 30.0 d** (D4's two orbits of 12.5 to 14.0 d and a gap of 0.5 to
  2.0 d; a longer sector, for example the four-orbit sectors 97 and 98, makes the geometry
  ineligible, recorded with its reason). **Eligible for D:** the same, with four or more distinct
  years.
- **Unique geometries, equal weight:** a geometry is identified by its sorted tuple of sector
  numbers; TICs that share a tuple count once, and **the TIC with the lowest number among the
  eligible ones supplies its dates** (TICs sharing sectors can have different `t_min` and `t_max`).
  The screening samples the variety of geometries, not their frequency among the known controls.
- **The selection:** the eligible unique geometries in the order of their sector tuples, shuffled by
  `numpy.random.default_rng(seed)` with `seed` the first 8 bytes (big-endian) of
  `SHA-256("refute/v0.2.1/viability-cd/geometries/<C or D>")`; the first **24** for C and **12** for
  D, or all of them if fewer, recorded. **With no eligible geometry**, that alternative does not run
  and its outcome is INDETERMINATE ("no geometry"). *A reading by Codex during this package's
  review, on the saved metadata:* 39 eligible unique geometries for C and 23 for D, D's covering
  four or five years only; the authoritative counts are those of the geometry list's commit (step 2),
  and D's conclusions would concern four and five years only.
- **The assignment:** within each alternative, noise model and regime, case `i` takes the selected
  geometry `i mod G`, in the selection's order.
- **The cadences** of a sector of real span `S` (BTJD `t_min'` to `t_max'`), by `population_v4`'s
  declared rules: the orbit gap `g` uniform in 0.5 to 2.0 d; the first orbit
  `(S − g)/2 + δ` with `δ` uniform in ±0.5 d, the second `S − g` minus the first; both must lie in
  12.5 to 14.0 d, else `g` and `δ` are drawn again, up to `population_v2`'s `MAX_ATTEMPTS`
  (exhausted: a defect that stops the lot, never a silent replacement); the time stamps by
  `population_v4._sector` from `t_min'`, whose last nominal cadence lies at
  `t_min' + (round(L1/DT) + round(L2/DT) − 2) DT + g` (`L1`, `L2` the orbits, `DT` the cadence), so
  one to three nominal cadences short of `t_max'` by its rounding (the time stamps' own D3 and D4
  checks below apply);
  0 to 4 loss blocks, single-cadence losses and the ±0.25 s jitter as `population_v4`. Each sector
  labelled by the UTC calendar year of its first kept cadence (the adapter's rule). The real dates
  are kept (the prewhitening bins the absolute phase).
- **Checked on every case's time stamps**, by the domain function (`refute.packs.tess.domain`,
  each condition computed on every input): **D3 and D4** for both alternatives; **D1** (exactly
  three years) for C; **four or more labels** for D, by the module's own check (D1, D2 and D5 of the
  domain are not applied to D, and D2 and D5 not to C). A case failing them is redrawn by the same
  rule, recorded.
- **Recorded before any case is generated:** the eligible geometries with their representative
  TIC, the ineligible ones with their reasons, and the selected lists, as the first commit of the
  authorized execution.

## 2. The cases

- **Planets only, the measurable band**, `population_v2`'s parameter distributions and noise models
  (white and AR(1)), placed in the band on their own layout (`_place_in_band`), signals never
  redrawn by an engine output (as `population_v4`'s criterion 6).
- **C:** per noise model **360 planets**, as B2's measurable band: 180 without variability
  (`three_years`-type) and 180 with variability in two of the three years (`variability_some_years`
  -type, the variability-free year uniform among the three). **720 curves.**
- **D:** per noise model **120 planets without variability**. **240 curves.** Compared with C's 180
  without variability per noise model.
- **Seeds:** case `i` of alternative `a`, noise `n` and regime `r` from the first 8 bytes of
  `SHA-256("refute/v0.2.1/viability-cd/<a>/<n>/<r>/<i>")`; one realization per case. Prefix
  `refute-v0.2.1-viability-cd-1`. Seeds fixed by this text, before any run.
- **The task order:** interleaved across noise model, regime and geometry (round-robin), so that any
  first part of a sub-lot is balanced (for the cost check of section 7).

## 3. The measurement

- **Every round** (one per observing year) by `calibration_measurement` on the R_min study's
  configuration (`m4-configurations/rmin-study.json`, its identity checked by the runner, as in
  X2), with the noiseless twin; the evaluator's truth made before the engine calls
  (`rmin_study.EvaluatorTruth`) and attached after them; the truth never reaches the engine.
- **Each round derived** by `derive_round` at R = 8 with the R_min study's committed pair (b 0.585,
  s 2.883; [../viability/README.md](../viability/README.md), section 3), as the earlier readings.
- **Each target:** `spec_b_outcome` over **all** its observing years (specification B, complete),
  and the legacy aggregation for reference. A completeness error of specification B is an
  **integrity error** (it stops the reading, apart from any scientific INCONCLUSIVE). A target's
  rounds are recorded together (one record per target), so a target is complete or absent.
- **Per round recorded:** the status, the **exact engine reason** and stopping stage, the primary
  barrier (section 4), and the identity flag.
- **Not run:** the full-curve search, the gauntlet and the global gate (the holdout only, as the
  R_min study). A holdout FAIL here is therefore a **holdout diagnostic**, not a REFUTED verdict.
- **The identity flag** (read by the evaluator after the calls): when the record holds the train
  ephemeris (the rounds that reached the timing step or beyond), its period more than 1% from the
  injected period (an alias or another signal); for a round stopped earlier, **not identifiable**
  (no extra search is run). The flag coexists with any status and any barrier.

## 4. The barriers (a primary barrier per round; the exact reason always kept)

| Barrier | The round's reason |
| --- | --- |
| **X, no train data** | `no training data` |
| **S, the train search** | the train-only search found no candidate; an invalid train candidate for its train SNR or its duration/period ratio (`train_validity`) |
| **G, the train gate** | `train_noise_undetermined` |
| **K, the train's capacity** | fewer train transit times than the minimum; `train_replicas_below_r_min`; `insufficient_capacity_train` (decision 1) |
| **T, timing** | "train-only timing uncertainty in the hidden year" |
| **W, the windows** | `no_predicted_window`; an invalid train candidate for its windows' fraction of the hidden year (`train_validity`) |
| **N, the hidden noise** | `hidden_noise_undetermined`; `insufficient_capacity_hidden_noise` (decision 2) |
| **M, the measurement** | `too_few_windows` and the other measurement statuses the code enumerates (listed by the acceptance record from the code) |
| **decided** | PASS, FAIL, or INCONCLUSIVE `not_detected_not_inconsistent` |

A round whose train candidate is invalid for several reasons takes the first of them in the order
S, W. **An unmapped reason stops the reading** (a defect, never a silent class). The primary barrier
is the stopping point, not a causal separation: a round stopped by K could also have met T or N
later.

## 5. The readings (all fixed here)

- **R1, as measured:** per alternative, noise model and regime, the targets' specification-B PASS,
  FAIL and INCONCLUSIVE counts; the rounds' statuses, barriers and identity flags; for the
  INCONCLUSIVE targets, the barriers of their undecided years; **by geometry and by the number of
  observing years**; the variability regime reported apart.
- **R2, the optimistic substitution (exactly):** each round INCONCLUSIVE with its primary barrier in
  the set released is counted PASS, every other round as recorded, then specification B; three
  sets: **R2-K** (K), **R2-KT** (K and T), **R2-KTN** (K, T and N). X, S, G, W and M are never
  released. A substitution assumes a PASS where none was measured; a released round could have
  given a FAIL.
- **R3, the evaluator's diagnostic oracle (exactly), descriptive only:**
  - for each injected transit `k` whose centre `t_k` lies in a hidden sector: the in-transit
    cadences `|t − t_k| ≤ T14/2` and the baseline cadences `T14 ≤ |t − t_k| ≤ 3 T14`, excluding
    every cadence within `T14` of another injected transit's centre; the transit is **kept** when it
    has at least 5 in-transit cadences and at least 10 baseline cadences on each side, otherwise
    skipped (counted);
  - per kept transit, a straight line fitted to its baseline by ordinary least squares; the
    in-transit deficits `d_i` = line minus flux; the residuals of the baseline;
  - the year's depth `D` = the mean of every kept transit's `d_i`; its error
    `E = σ / √N_in`, with `σ² = Σ r² / (N_B − 2 K)` pooled over the kept transits' baseline residuals
    (`N_B` their count, `K` the kept transits) and `N_in` the in-transit cadences; **the line's own
    uncertainty and the noise's temporal covariance are not included** (so `E` understates the
    error under correlated noise, and the oracle is optimistic there);
  - the year **oracle-detectable** when `E > 0`, `D` and `E` finite and `D / E ≥ min_snr` (the
    plan's value); a year with no kept transit, or a non-finite or zero `E`, is not detectable, with
    its reason; the target **oracle-PASS** when every observing year is detectable.
  - **R3 is a diagnostic oracle of the evaluator:** the truth never reaches the engine; it is **not**
    T4's performance nor any method's; it describes what this estimator finds at perfect windows,
    and is **not an upper bound** on the recoverable information (variability, correlated noise and
    the baseline limit it). **R3 decides nothing.** An engine still limited by capacity or hidden
    noise sets no ceiling for a corrected method.
- **C against D:** on the planets without variability only, the difference of the
  specification-B PASS fractions (R1, and R2-KTN) per noise model, with a two-sided 95% Newcombe
  (Wilson) interval, described, not decided; the rounds' PASS fraction by the number of observing
  years. C's variability regime is reported apart and enters no C/D comparison.

## 6. The viability rule (fixed before any run)

- **Population and denominator:** per alternative and noise model, every declared planet (C: 360,
  both regimes; D: 120). **Completeness, per noise model:** if more than 5% of an alternative's
  planets in a noise model have no record (the sub-lot stopped at its ceiling), that alternative's
  outcome is INDETERMINATE, whatever the counts. Otherwise every decision below must hold **under
  the worst assignment of the missing planets** (for a PASS condition, each missing planet counted
  as not PASS and as FAIL; for a FAIL condition, as PASS and not FAIL); the bounds are reported with
  the missing planets assigned both ways.
- **Uncertainty:** one-sided 95% exact Clopper-Pearson bounds, `L` and `U`, per noise model, each
  judged on its own; **no simultaneous coverage is claimed** across noise models, readings or
  alternatives. The binomial model treats the per-noise-model planets as independent cases **of
  this fixed composition** (the selected geometries, the regimes' halves); the bounds say nothing
  about geometries not selected.
- **The benchmark:** B2's **275 of 360** (0.764) measurable planets per noise model, a necessary,
  not sufficient, condition of plan B's design (plan B, section 4). For D's limited lot it is a
  **screening benchmark only**, not an established condition of D's eventual design.
- **PASS** (the alternative may be proposed as an executable plan): in **both** noise models, R1's
  PASS fraction has `L ≥ 275/360` and R1's holdout-FAIL fraction has `U ≤ 0.10`. **This is a
  conservative screening hurdle chosen here, stronger than B2's count:** with complete records it
  needs at least 289 PASS and at most 26 FAIL of 360 (C), at least 100 PASS and at most 6 FAIL of
  120 (D). The maintainer may choose instead the point benchmark (`PASS/n ≥ 275/360`); the choice is
  made before authorization.
- **FAIL** (the alternative abandoned in this form, with this engine family): in **either** noise
  model, **R2-KTN's** PASS fraction has `U < 275/360` (even with the train's capacity, timing and the
  hidden noise released, the barriers X, S, G, W and M keep it below the benchmark), or R1's
  holdout-FAIL fraction has `L > 0.10` (a holdout diagnostic limit, not a demonstrated violation of
  G2, the global gate not being run).
- **INDETERMINATE:** every other case, reported with the binding barriers (which of R2-K, R2-KT or
  R2-KTN would reach `L ≥ 275/360`) and with R3 as a description. The decision goes back to the
  maintainer, with no automatic extension, no rerun and no change of rule. **A low R1 alone is
  INDETERMINATE**: the R_min study already found specification-B PASS of 0.245 (white) and 0.310
  (AR(1)) for one-sector three-year planets, mostly stopped by the train's capacity
  ([../viability/README.md](../viability/README.md), section 3), so a low R1 can mean an unresolved
  engine limit while the geometry stays promising.
- **The outcomes cannot conflict:** R2 only turns INCONCLUSIVE rounds into PASS, so its PASS
  fraction is never below R1's, and a PASS (R1's `L ≥ 275/360`) excludes a FAIL by R2-KTN; the FAIL
  fraction's two conditions (`U ≤ 0.10`, `L > 0.10`) exclude each other.
- **What an outcome does not show.** PASS does not show safety against false PASS or false FAIL
  (no false positives, no curves without a transit, G1 and the global gate not measured), nor that
  a full study would pass. FAIL of D's limited lot (12 geometries of four or five years) can justify
  abandoning D in this form; it **does not show** that every domain of four years or more is
  infeasible. FAIL or INDETERMINATE says nothing on a corrected method (T4, a repair of the hidden
  noise, another capacity model, a changed search).

## 7. The budget, the ceilings and the resumption

**The ceiling's balance** ([balance.json](balance.json), [scripts/balance.py](scripts/balance.py),
read only, 2026-10-27): accounted consumption **702.1 LP-h and 66.0 h**, so **3297.9 LP-h and
134.0 h unspent** of 4000 LP-h and 200 h. Its parts and their precision:

| Part | LP-h | Wall | Precision |
| --- | ---: | ---: | --- |
| Plan B's snapshot (budget-b.json) | 491.1 | 55.6 h | as recorded there |
| The suites since (JUnit times, 24 processors) | 182.3 | 7.6 h | budget_b.py's proxy, not measured CPU; a file of the snapshot's minute possibly counted twice (disclosed, not shown) |
| The two X2 subsets of 2026-10-27 | 0.8 | 0.04 h | their run reports' elapsed hours times workers (a proxy) |
| The acceptance population's generation of 2026-10-27 | 4.0 | 0.18 h | an upper bound from two files' write times, 22 workers |
| Gate 1's three generations | 11.9 | 1.05 h | **estimated** at the 2026-10-27 generation's cost |
| Gate 1's sabotages | 12.0 | 1.0 h | **an allowance**, not recorded |
| The real controls' check | 0 | 0.57 h | queries only |

Plan B's reserved steps no longer hold a claim (it ended). Codex's reviews and the interactive work
are outside the ceilings, as in budget_b.py.

**The estimate of this package** (planning, labelled as such): the per-curve cost (the case's
generation, its rounds, the twin and R3, all inside the task) grows with the rounds and the
cadences; measured 46.4 LP-s per curve on the 2026-10-27 X2 subset (three one-sector years, with
the twin) and 61.6 on X2's diagnostic runs (budget-b's unit); planned at **2 times 61.6 = 123 LP-s
for C** and **5 times = 308 LP-s for D**, assumptions **checked separately for each sub-lot** on its
first balanced 10% of tasks.

| Item | Estimate | Ceiling |
| --- | --- | --- |
| C, 720 curves | 24.6 LP-h | 37.0 LP-h, **1.70 h** of submission on 22 workers |
| D, 240 curves | 20.5 LP-h | 30.8 LP-h, **1.40 h** of submission |
| The drain after a stop (the runner keeps up to 4 × 22 tasks in flight: 88 tasks at C's and D's assumed units; an **estimated reserve**, not a maximum; the actual drain enters the cumulative accounting) | 10.5 LP-h | 10.5 LP-h, 0.5 h |
| The generation's determinism check (a subset generated three times) and the geometry list | 2 LP-h | 3 LP-h, 0.15 h |
| The implementation's suites and checks (4 full suites, budget_b's proxy) | 67 LP-h, 2.8 h | 100 LP-h, 4.2 h |
| **Total** | | **about 181 LP-h and 8.0 h** |

After it, about **3117 LP-h and 126 h** would remain for the executable proposal.

- **Two sub-lots, in this order:** `viability-c` then `viability-d`, each with its submission ceiling
  (1.70 h and 1.40 h); a sub-lot stops submitting at its ceiling, drains what is in flight, and what
  ran is evaluated as section 6 says. If a sub-lot's first balanced 10% of tasks measures a cost per
  curve that would exceed its ceiling for the whole sub-lot, it stops there and the decision goes
  back to the maintainer (no ceiling is raised after a result).
- **The environment:** the lock `a49bfdf2…`, the environment record before each sub-lot and after,
  equal; logical processors 8 to 31, 22 workers.
- **The resumption:** **one resumption is included only if the maintainer authorizes this execution
  package**: of an interrupted sub-lot (a crash, a power loss; not its ceiling), with the same code,
  environment record and manifest, by the runner's resume (records written once and never replaced;
  an interrupted run relaunched gives the same record bytes, tested), the consumed time accumulated
  across attempts and an interrupted attempt's time reconciled as `x2_study.py`'s runner does.
  Recorded in the lot's issue. Any other rerun needs its own approval in a GitHub issue (CLAUDE.md).

## 8. The steps, each with its own authorization

1. **The implementation** (authorization 1): the acceptance record of the new module (the criteria
   of sections 1 to 6, the measurement statuses enumerated from the code), then tests (synthetic,
   offline), then the code (`viability_cd.py` beside the population modules, reusing
   `population_v2`, `population_v4`, `rmin_study` and `x2_study`'s runner pattern without editing
   them), sabotages (each criterion broken once and caught), Codex's review. About **two to three
   days**. No case of the lot is generated; the tests use their own small prefix.
2. **The geometry list** committed (section 1), before any case.
3. **The run** (authorization 2): `viability-c`, then `viability-d`.
4. **The report:** R1 to R3, the C/D comparison and the rule's outcome per alternative, as fixed
   here; Codex's review; the maintainer's decision. The output is defined: for C and for D, PASS,
   FAIL or INDETERMINATE with its readings and barriers; nothing else is decided.
