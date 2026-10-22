# The prospective package for spec C (proposal, not authorized)

The maintainer's decision after X2e, item 5: one prospective package that covers the variability
replicate and the insufficiency of the cells without variability. **Proposal only: nothing runs, no
seed is drawn, no issue is opened, and no approval is assumed.** The planning numbers come from
[sizing.json](sizing.json) ([scripts/sizing.py](scripts/sizing.py)) and [regimes.json](regimes.json);
they are estimates from development data (few cases), not criteria.

## 1. What is validated

- **The question:** spec C's choice of an error model for each capacity decision (C2 to C5, with the
  C4/C6 amendment A0 if adopted), per regime. This lot is **choice data** (C6 "decide"); the final
  confirmation is a separate lot (section 8).
- **The population:** the X2 design (the constant scenario, the M4 configuration of
  `m4-configurations/rmin-study.json`, the capacity decisions recorded and not enforced, the
  noiseless twin), from a **new population prefix** never used, `refute-v0.2.1-x2-3`, in the four
  cells.
- **The regimes** (C4): the cells × the number of observing years. The cells with variability have
  only three-year cases in this population (`variability_some_years`), so there are six regimes:
  no variability, 2 years (AR(1), white); no variability, 3+ years (AR(1), white); variability,
  3+ years (AR(1), white).
- **The cases** are drawn per regime, not by the population's mix (14 two-year to 6 three-year per
  20): this needs a mechanism filter in the lot's `LotSpec` (`x2_study.py`, study code, not the
  engine), with its tests before the code and Codex's review, as part of this package's
  authorization.
- **What one prefix holds** (`population_v2.py`, `_planet_mechanism` and the generation loop from
  line 295; `rmin_study._planets` keeps the bands `near` and `measurable`): per noise, 300 two-year
  cases (200 `two_years`, 100 `few_train`), 100 `three_years` and 100 `variability_some_years`. So
  one prefix covers every regime of options B and C, and option A except `white, no variability,
  2 years` (334 asked, 300 available; Codex's review). A second prefix would be a change of the
  population's design, its own declaration and authorization; it is not proposed here.

## 2. Independent cases and realizations

- **100 realizations per case**, as X2 and X2e, so a case-year's contribution keeps its meaning (at
  least 30 measured with their twin).
- **Only new independent cases count toward a regime's minimum (15) and its precision target.** New
  realizations of the same case never replace a case.

## 3. The size: precision, not only the minimum

The admissibility window is `[1 − τ, (1 + τ)·D]` with `τ = 0.10`. A calibrated candidate (`D = 1`)
with a small residual bias of 3% fits only if the interval's half-width is below about **0.07**. The
widest interval read in an eligible regime, `ρ_2` in `AR(1), variability` with 20 cases, has a
half-width of about 0.10 (`[1.15, 1.35]`); with the half-width falling as `1/√cases`,
`20 · (0.10 / 0.07)² ≈ 41`. **The target: 40 contributing cases per regime**; the minimum of 15 stays
the eligibility rule. The cells without variability have no per-regime interval today (fewer than
15 cases), so 40 may not be enough there; this is a risk, stated, not a criterion.

**Expected losses by ineligibility** (case contribution rates, the lower of X2e alone and the pooled
reading; the number of cases for 40 contributing with probability 0.90 under a binomial model):

| Regime | Rate seen | Cases for 15 | Cases for 40 | Planned |
|---|---|---|---|---|
| AR(1), no variability, 2 years | 0.36 | 54 | 131 | see the options |
| white, no variability, 2 years | 0.14 | 138 | 334 | see the options |
| AR(1), no variability, 3+ years | 1.00 (6 and 12 cases) | 15 | 40 | 44 |
| white, no variability, 3+ years | 1.00 (6 and 12 cases) | 15 | 40 | 44 |
| AR(1), variability, 3+ years | 1.00 (20 cases) | 15 | 40 | 44 |
| white, variability, 3+ years | 1.00 (20 cases) | 15 | 40 | 44 |

The three-year rates rest on few cases; 44 adds 10%. The probability 0.90 is **conditional on the
rates being the true ones**; it does not account for their own uncertainty (2 of 14, 5 of 28 and
so on), so the real probability can be much lower. Forty contributing cases is a planning target,
not a demonstrated precision.

**Options (the maintainer's choice; B changes the scope as in the amendment's A2; A and C keep every
regime under C5, C with less precision in the two-year regimes):**

| Option | Two-year regimes | Cases | Curves | Logical-processor hours | Wall on 22 workers |
|---|---|---|---|---|---|
| A (every regime at the precision target) | 131 and 334 (only 300 white available in one prefix: at most 607 cases, and about 42 contributing expected rather than 40 with probability 0.9) | 641 | 64 100 | about 430 | about 19.6 h |
| B (three-year regimes only; two-year outside the validated scope) | none | 176 | 17 600 | about 195 | about 8.9 h |
| C (three-year at the target; two-year only to eligibility) | 54 and 138 | 368 | 36 800 | about 292 | about 13.3 h |

Option C carries the risk of the C5 note: in an eligible two-year regime with little precision, a
candidate whose interval is inconclusive there is not admissible, and limited precision may leave no
candidate admissible in that decision.

## 4. Seeds and criteria

- **Seeds:** the realization seeds `SHA-256("refute/v0.2.1/stage-1/X2f/<prefix>/<group>/<case>/<j>")`
  (the X2e form with a new root), listed in a committed seed file and checked against every earlier
  lot's (`x2-seeds.json`, `x2e-seeds.json`) for no overlap before the lot runs; the prefix and the
  root never used.
- **Criteria:** spec C's C3 to C5 unchanged (with A0 if adopted), and X2-B's quantities
  (`τ = 0.10`, at least 30 measured realizations per case-year, at least 15 contributing cases, the
  SD deciding and the MAD checking, the cluster bootstrap with 2000 resamples and X2-B's bootstrap
  seed). Every candidate of C2 is computed on these records; the choice rule is C5's.
- Declared and committed before the lot: the declaration, the seed file, the code (with the regime
  filter) and its tests; the lot's identity (plan, code, environment) bound in its manifest.

## 5. Cost, ceiling and workers

Unit costs measured: 18.2 logical-processor seconds per curve without variability (X2e), 61.6 with
variability (X2 less its cells without variability at X2e's cost). Processors 8 to 31, 22 workers, as
X2 and X2e. **Three sub-lots, each with its own ceiling of 1.5 times its estimate**, run in this
order so that the cheaper evidence comes first:

| Sub-lot | Regimes | Option A estimate | Ceiling |
|---|---|---|---|
| S1 | no variability, 3+ years | 8 800 curves, about 44 LP-h, about 2.0 h | 3.0 h |
| S2 | variability, 3+ years (the variability replicate) | 8 800 curves, about 151 LP-h, about 6.8 h | 10.3 h |
| S3 | no variability, 2 years | 46 500 curves, about 235 LP-h, about 10.7 h (option C: 19 200 curves, about 4.4 h) | 16.0 h (option C: 6.6 h) |

The unit costs come from rounded run times (exactly 18.216 and 61.578 LP-s per curve), and the
variability cost is inferred by subtraction, not measured apart. The ceilings above are rounded 1.5
times the estimates (exactly 3.036, 10.263 and 16.0425 h, option C's S3 6.624 h); the execution
declaration fixes exact values.

The two-year cases are costed at X2e's mean cost per curve (they have fewer hidden years, so this
is likely an overestimate; not measured apart). A ceiling reached stops the sub-lot; what ran is recorded and evaluated as declared, with the regimes
it leaves short reported as short.

## 6. Insufficient coverage: no automatic extension

A regime that ends with fewer than 15 contributing cases is **ineligible** and the corrected model
stays **unvalidated there**; a regime that is eligible but `not determined` is reported so. **No
automatic extension of the lot**: any further cases are a new package with new seeds and its own
authorization, declared before its data; and the result already in hand is never re-read with a
different minimum, criterion or sample.

## 7. Resumption (the issue's text, a draft; not opened)

> **Title:** v0.2.1 stage 1: pre-approved resumption of the spec C choice lot (X2f)
>
> **Reason:** the lot `x2f` (sub-lots S1 to S3) of
> `docs/validation/v0.2.1/reopen/stage-1/x2f-execution-package.md` may be interrupted (a power cut, a
> reboot, a crash of the machine). This issue records, before the lot runs, the only resumption
> allowed.
>
> **Conditions, all checked before the relaunch:** the interrupted sub-lot's dated run reports list
> **no failed task** (the runner reports a failed task and writes no record, so a relaunch would run
> it again: a retry, not a resumption; with any failure, no resumption under this issue); the same
> code commit, plan, configuration and environment as the lot's manifest (the runner refuses
> another manifest); and the remaining budget is positive: the sub-lot's ceiling less the wall time
> of every earlier run of it, summed from its run reports. The runner writes its report only at the
> end of a run, so a hard interruption can leave a run with no report: **if any earlier run of the
> sub-lot lacks a complete report, its consumption and its failures are unverified and the
> resumption is not covered by this issue** (a separate decision of the maintainer). A missing report
> never counts as zero consumption or as evidence of no failure.
>
> **Procedure:** (1) the SHA-256 of every record already present, written to a dated file in
> `.cache` (`x2_lot_digests.py`); (2) `x2_study.py run <run_dir> --lot x2f --workers 22
> --deadline-hours <remaining budget>` on processors 8 to 31, in the same run folder (the runner's
> deadline counts from its own start, so the remaining budget is passed explicitly; it runs only the
> tasks without a record, with atomic no-replace writes, and stops on an incomplete record); (3) the
> digests of step 1 compared with the same records after the run: every one unchanged; (4)
> `x2_study.py check` (every task one record, at its own path, complete) before any evaluation.
>
> **Not allowed under this issue:** a change of code, seeds, sizes, criteria or configuration; a
> new sub-lot or extra cases; a retry of a failed task; resuming with no remaining budget;
> re-running a task that has a record. Any of these needs its own approval, recorded in its own
> issue, before it runs.

## 8. Choice data apart from the final confirmation

- **This lot chooses** (C6) and nothing else; its result is not the validation of the chosen model.
- **The final confirmation**, after the chosen candidate is coded in a new corrections field and
  frozen (spec C, C8): a separate lot with **seeds from a future drand round** declared before (a
  drand round is the maintainer's to approve), the same regimes, sizes and criterion, for the chosen
  candidate only, run once. A failure is recorded as a result; no second candidate is tried on the
  confirmation data. Its cost is about that of the choice lot (option A about 430 LP-h).
- Neither replaces the later confirmation of false PASS, false FAIL and utility (X5, X6, the
  reserve).

## 9. Before it runs

The maintainer's choices: the option (A, B or C), the amendment A0, the precision target, the regime
filter's code; then the declaration, the seed file and the code are committed, Codex reviews them,
and the authorization is asked with the exact sizes, workers, affinity, cost and ceilings.
