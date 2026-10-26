# X2f: spec C's choice lot, option A executable (declaration, not run)

Prepared on 2026-10-22 after the maintainer's decisions on the delivery `0abc6de` (spec C: amendment
A0 and direction A1 adopted; the package to come back executable, without running). **Nothing here
runs; no authorization is assumed.** It replaces sections 3 to 7 of
[prospective-package-proposal.md](prospective-package-proposal.md) for option A; the other options
are no longer proposed. The aim is not that a candidate passes: it is that the lot can answer spec
C's question in every regime it covers, or says beforehand where it may not.

> **Revision 1 (2026-10-26): X2f is S1 + S2, without S3.** Decided by the maintainer on
> 2026-10-26, as plan B (adopted 2026-10-23, [section 6](../plan-b/README.md)) foresaw. It
> supersedes every mention of S3 below; nothing else of the declaration changes.
>
> - **The lot:** S1 (94 cases, 9400 curves) then S2 (90 cases, 9000 curves): **184 cases, 18 400
>   curves**. The two-year regimes of S3 are not run: they lie outside the profile
>   `three-observing-years/1`, and X2f says nothing about them.
> - **The cost:** estimate 47.6 + 153.9 = **201.5 LP-h, 9.16 h**; ceilings 3.25 h and 10.50 h, **13.75 h
>   in all** (302.5 LP-h at 22 workers, the figure of plan B section 8).
> - **The order and the evaluation:** S1 → S2; no evaluation is read until **S2** has ended; the
>   environment fixed before S1 is unchanged until S2 ends. Section 10's stated exception (`white,
>   no variability, 2 years`) no longer applies.
> - **The seeds:** the 18 400 seeds of S1 and S2 are among the 63 000 checked distinct in section
>   5; [x2f-seeds.json](x2f-seeds.json) stays as the record of the earlier version (S3's seeds are
>   never used).
> - **The runner, after Codex's audit of 2026-10-26:** each submission is recorded before it runs
>   (`attempts/`) and each failure at once (`failed/`); a task that failed, or whose outcome is
>   unknown because its run was cut short, is **not submitted again** unless a decision recorded
>   in the run folder (`retry-decisions/`) names that marker (R2). The **ceiling counts across
>   the invocations** of one sub-lot (`consumption/`, R3): every invocation records its time and
>   closes the record at its end; an invocation that did not close it (it was killed) stops every
>   relaunch until a recorded decision gives its time. A relaunch therefore passes the sub-lot's
>   own ceiling (3.25 h or 10.50 h), never a remaining budget computed by hand.
> - **The resumption, as it stands** (it supersedes section 8 and section 6's "a relaunch would
>   retry it"; the resumption issue is opened with this text): (1) the SHA-256 of every record
>   present, to a dated file in `.cache`; (2) if an earlier invocation did not close its
>   consumption record, the maintainer records a decision (`retry-decisions/<n>.json`, with its
>   text, the invocation's time in `consumption`, and, only if the maintainer allows it, the
>   markers of the tasks cut short in `covers`); (3) `x2_study.py run <run_dir> --lot x2f-s<n>
>   --workers 22 --deadline-hours <the sub-lot's ceiling>` on processors 8 to 31, in the same run
>   folder; (4) the digests of step 1 compared after the run, every one unchanged; (5)
>   `x2_study.py check <run_dir> --full` before any evaluation. **Not covered:** a change of code,
>   seeds, sizes, criteria, configuration, environment or order; a retry of a failed task or of
>   one cut short without a decision naming it; re-running a task that has a record.
> - **The code:** `x2_study.py`, `X2F_SEQUENCE = ("x2f-s1", "x2f-s2")`, `LOTS` without S3, and the
>   command line refusing an unknown lot; the tests in `tests/test_x2.py` (written before the code,
>   [../../../audit-2026-10-26/README.md](../../../audit-2026-10-26/README.md)).

## 1. The question and the data that decide

- **The question:** spec C's choice of an error model for each capacity decision (C2 to C5 of
  [../spec-c-error-model.md](../spec-c-error-model.md), with A0), per regime (cell × number of
  observing years).
- **The data that decide: X2f's records alone** (the maintainer's decision of 2026-10-23; spec C's
  C6 says the same). X2's and X2e's records **inform only** (both already read); nothing is pooled
  across them (A0).
- **This lot chooses; it does not confirm.** The confirmation is a separate lot (section 9).

## 2. The population and the cases

- **Prefix** `refute-v0.2.1-x2-3`, never used; the population, configuration and measurement of X2
  (the M4 configuration `m4-configurations/rmin-study.json`, the capacity decisions recorded and not
  enforced, the noiseless twin).
- **What the prefix holds**, per noise: 300 two-year cases (`two_years` 200, `few_train` 100), 100
  `three_years`, 100 `variability_some_years` (`population_v2.py`, `_planet_mechanism` and the
  generation loop; `rmin_study._planets`, bands `near` and `measurable`).
- **The selection** (`x2_study.py`, `LotSpec.selection`, tested in `tests/test_x2.py`): in each
  regime, X2's rule among that regime's cases (in band then index order, every `len // n`-th, the
  first `n`), both bands present.
- **100 realizations per case**, as X2 and X2e; only new independent cases count toward a regime's
  minimum (15) and its target (40).

| Sub-lot | Regime | Cases | Curves |
|---|---|---|---|
| S1 (`x2f-s1`) | white, no variability, 3+ years; AR(1), no variability, 3+ years | 47 + 47 | 9 400 |
| S2 (`x2f-s2`) | white, variability, 3+ years; AR(1), variability, 3+ years | 45 + 45 | 9 000 |
| S3 (`x2f-s3`) | white, no variability, 2 years; AR(1), no variability, 2 years | 300 + 146 | 44 600 |
| | | **630** | **63 000** |

**The order S1 → S2 → S3 is fixed now** (`X2F_SEQUENCE`), and every sub-lot runs whatever another
one shows: none is cancelled, added, resized or reordered by a result. The order is kept by the
procedure (the runner does not enforce a sequence across sub-lots); each sub-lot's run reports and
environment records, committed in order, show it. Between sub-lots only the lot check
(`x2_study.py check <run_dir> --full`: every declared task once, each record complete, its group,
mechanism and band its case's) is run; **no evaluation is read until S3 has ended** (complete or
stopped by its ceiling).

## 3. The size, from one rule fixed now

**Sizing rule:** in each regime, the smallest number of cases whose probability of reaching **40
contributing cases** is at least **0.95** under the beta-binomial predictive with a Jeffreys prior
on the regime's contribution rate (from the pooled development counts), or every case the prefix
holds if no number reaches it ([scripts/sizing_a.py](scripts/sizing_a.py),
[sizing-a.json](sizing-a.json)). 40 is the precision target (a half-width near 0.07; see the
proposal's section 3); 15 stays the eligibility minimum.

**The probabilities with the cases planned** (the counts are development data, used for planning
only):

| Regime | Cases | Development counts (X2e alone; pooled or X2) | P(≥ 40): plug-in X2e / plug-in pooled / Jeffreys / uniform / at the 95% lower rate | P(≥ 15): Jeffreys / at the 95% lower rate |
|---|---|---|---|---|
| AR(1), no variability, 3+ years | 47 | 6 of 6; 12 of 12 | 1.00 / 1.00 / 0.95 / 0.88 / 0.16 | 1.00 / 1.00 |
| white, no variability, 3+ years | 47 | 6 of 6; 12 of 12 | 1.00 / 1.00 / 0.95 / 0.88 / 0.16 | 1.00 / 1.00 |
| AR(1), variability, 3+ years | 45 | –; 20 of 20 | – / 1.00 / 0.97 / 0.91 / 0.39 | 1.00 / 1.00 |
| white, variability, 3+ years | 45 | –; 20 of 20 | – / 1.00 / 0.97 / 0.91 / 0.39 | 1.00 / 1.00 |
| AR(1), no variability, 2 years | 146 | 5 of 14; 12 of 28 | 0.99 / 1.00 / 0.95 / 0.96 / 0.48 | 1.00 / 1.00 |
| white, no variability, 2 years | 300 (all) | 2 of 14; 5 of 28 | 0.71 / 0.99 / **0.77** / 0.81 / **0.0002** | **0.99** / **0.96** |

- "~42 expected" was not "0.9 of reaching 40": with the rates' uncertainty, `white, no variability,
  2 years` reaches 40 with probability about 0.77 even with every case of the prefix, and about
  **0.0002** at the 95% lower bound of its rate (0.073: about 22 contributing expected); it reaches
  the eligibility minimum of 15 with probability 0.96 or more under every reading.
- **What these probabilities are:** planning probabilities conditional on the model (each case
  contributes independently with one rate per regime, the rate's uncertainty described by the
  prior). The regimes mix bands and mechanisms in fixed quotas (for example `two_years` and
  `few_train`), whose rates may differ; that exchangeability is not established. The half-width of
  0.07 at 40 cases is a heuristic (scaled as `1/√cases` from the variability cells), not a
  demonstrated precision.
- The three-year rates were 1.00 on 12 and 20 cases; at their 95% lower bounds (0.78 and 0.86) the
  three-year regimes would miss 40 more often than not; that risk is accepted at the rule's 0.95.
- The sensitivity to the number of cases (`sizing-a.json`, `by_cases`): with 60 cases the
  three-year regimes reach 40 with probability 0.985 or more even at the lower rate; 200 cases do it
  for `AR(1), no variability, 2 years`. These are not planned; they show how the risk moves.

## 4. What happens in each regime, fixed now

| Contributing cases at the end | What follows |
|---|---|
| **40 or more** | eligible (C4); judged by C5 |
| **15 to 39** | eligible (C4: the minimum is 15, unchanged); judged by C5 exactly as at 40, its interval reported with the note "below the precision target"; a `not determined` there is what C5 says it is (the candidate not admissible in its decision) |
| **fewer than 15** | ineligible (C4): it counts neither for nor against a candidate; **the corrected model stays unvalidated in that regime** and every later use of it there says so (X3, X5, X6 and the confirmation); C5's rule that each cell needs one eligible regime applies |

In every case: **no extension** of the lot (more cases are a new package with new seeds and its own
authorization), and the result is never read again with another minimum, criterion, sample or
precision target.

## 5. Seeds and criteria

- **Seeds:** `SHA-256("refute/v0.2.1/stage-1/X2f/refute-v0.2.1-x2-3/<group>/<case>/<j>")`, the
  first 8 bytes big-endian (`x2_study.realization_seed`). [x2f-seeds.json](x2f-seeds.json)
  ([scripts/x2f_seeds.py](scripts/x2f_seeds.py)): **63 000 seeds, all distinct** (9400, 9000 and
  44 600 per sub-lot), **none equal to any of 729 600 earlier seeds** (the case and first-noise seeds
  of bs-choice, the timing lot, the R_min study's prefixes, X2's, X2e's and X2f's own prefixes, and
  X2's and X2e's realization seeds); the full list's SHA-256
  `f459a1814884dfd7fede8c3b638ae8cb1ce1a2df66dd629d831a9a447f439059` (the list itself, about 12 MB,
  is regenerated by the script, and every seed is also in the lot's manifest when it runs). Tested:
  no seed shared with X2, X2e or another sub-lot.
- **Criteria:** spec C's C3 to C5 unchanged with A0, and X2-B's quantities (`τ = 0.10`; at least 30
  measured realizations per case-year; at least 15 contributing cases; the SD deciding, the MAD
  checking; the cluster bootstrap over cases, 2000 resamples, X2-B's bootstrap seed). Each record
  names its sub-lot (format and target), so no record of one sub-lot passes another's check.

## 6. Cost, workers and ceilings

Processors 8 to 31, 22 workers. Unit costs from the X2 and X2e runs (diagnostic runs of this same
measurement; 18.216 and 61.578 logical-processor seconds per curve, the second by subtraction). The
ceiling of each sub-lot is 1.5 times its estimate, rounded up to 0.05 h:

| Sub-lot | Estimate | Ceiling |
|---|---|---|
| S1 | 47.6 LP-h, 2.16 h | **3.25 h** |
| S2 | 153.9 LP-h, 7.00 h | **10.50 h** |
| S3 | 225.7 LP-h, 10.26 h | **15.40 h** |
| Total | 427.2 LP-h, 19.42 h | 29.15 h |

A sub-lot that reaches its ceiling stops submitting (the tasks already in flight end); what ran is
kept; the next sub-lot still runs in the fixed order. **A failed task does not stop the run it
happens in** (the runner reports it and goes on), but it **stops the sequence**: the maintainer
decides before the next sub-lot or any relaunch (a relaunch would retry it).

**A sub-lot stopped by its ceiling, fixed now.** The runner submits the tasks case by case in the
selection's order (each case's 100 realizations together; each sub-lot lists white first), so the
tasks left out by a stop are a suffix of that order, whatever their results: the AR(1) cases first,
and white cases too if the run was slow enough. The incomplete cases actually left are listed. Such
a sub-lot is evaluated on its **complete cases only** (every one of
the 100 realizations recorded); a case with some records is left out whole and listed with its
count; the regimes are then counted by section 4 on the cases that remain. The manifest is never
changed after the fact. **The code for this** (an evaluation of the complete cases of a stopped
lot; today `lot_rows` refuses any incomplete lot) is written with its tests before the lot runs, as
part of the authorization; it is not written now.

## 7. The environment

The lot runs in one environment fixed and recorded before S1, never changed until S3 ends: the
interpreter, every installed distribution's version and the lock's SHA-256 (the environment record,
[scripts/env_record.py](scripts/env_record.py)), beside the manifest (which binds the code digest,
`uv.lock` included). **Decided by the maintainer (2026-10-23):** X2f, when authorized, runs
**after** the dependency update of 2026-10-27 and its checks
([dependencies-reachability.md](dependencies-reachability.md)), with the code, the interpreter,
the lock and the effective environment fixed before S1 and unchanged until S3 ends; the
confirmation uses the final environment declared. **If the lock's diff changes the numeric stack**
(for example numpy, scipy, astropy, lightkurve or their compiled dependencies), the work
**stops** and the diff goes to the maintainer before anything else. The lot is offline: no
download.

## 8. Resumption (the issue's text; not opened)

> **Title:** v0.2.1 stage 1: pre-approved resumption of spec C's choice lot X2f
>
> **Reason:** a sub-lot of X2f (`docs/validation/v0.2.1/reopen/stage-1/after-x2e/x2f-declaration.md`)
> may be interrupted by a power cut, a reboot or a crash of the machine. This issue records, before
> the lot runs, the only resumption allowed.
>
> **Conditions, all checked before a relaunch:** every earlier run of the sub-lot has a complete
> dated run report (the runner writes it only at the end; a run without one leaves its consumption
> and failures unverified, so the resumption is **not** covered here); no report lists a failed
> task (a relaunch would retry it); the same code, plan, configuration and environment as the
> manifest (the runner refuses another manifest) and the environment record unchanged; and a
> positive remaining budget: the sub-lot's ceiling less the summed elapsed time of its earlier runs.
>
> **Procedure:** (1) the SHA-256 of every record present, to a dated file in `.cache`; (2)
> `x2_study.py run <run_dir> --lot x2f-s<n> --workers 22 --deadline-hours <remaining budget>` on
> processors 8 to 31, in the same run folder (the deadline counts from the run's own start, so the
> remaining budget is passed explicitly; the deadline stops submissions, and the tasks in flight
> end; only tasks without a record run, written atomically, never replaced; a failure in this run
> does not stop it, and is handled as in the declaration, section 6); (3) the digests of step 1
> compared after the run, every one unchanged; (4) `x2_study.py check <run_dir> --full` before any
> evaluation. The order of the sub-lots and the environment record are checked by the procedure
> (they are not enforced by the runner).
>
> **Not covered:** a change of code, seeds, sizes, criteria, configuration or environment; a new
> sub-lot or extra cases; a retry of a failed task; a resumption with no remaining budget or after a
> run without a complete report; re-running a task that has a record; a change of the order. Each
> needs its own approval, in its own issue, before it runs.

## 9. Choice apart from confirmation

The confirmation, after the chosen candidate is coded in a new corrections field and frozen (spec C,
C8): a separate lot with seeds from a future drand round declared before (the maintainer's to
approve), the same regimes, sizes and criterion, for the chosen candidate only, run once, in the
same final environment; a failure is recorded as a result and no second candidate is tried on its
data. Neither replaces the confirmation of false PASS, false FAIL and utility (X5, X6, the reserve).

## 10. Before it runs (the maintainer's)

Decided on 2026-10-23: X2f alone decides (section 1); it runs after the update of 2026-10-27
(section 7); **the sizing risk is accepted for discussion**: the 0.95 are predictive probabilities
conditional on the model, not a guarantee of precision or of approval; `white, no variability, 2
years` is the stated exception (about 0.77 with every case of the prefix); no automatic enlargement
if coverage is short (section 4). **X2f is not authorized**; the authorization, with these sizes,
workers, affinity, cost and ceilings, and the resumption issue opened with the text of section 8,
come only after the maintainer's review of the viability check
([../viability/README.md](../viability/README.md)).
