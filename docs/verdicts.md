# Verdicts

A claim is never "proven". It survives the attacks, or it does not. There is no
`TRUE`.

## Discovery verdicts (signals)

| Verdict | Meaning |
|---|---|
| `SURVIVED` | The signal is significant and every test passed. |
| `WEAKENED` | No fatal failure, but at least one warning-level failure. |
| `REFUTED` | At least one fatal failure. |
| `INCONCLUSIVE` | The signal is not significant (gate failed), or a required test could not be decided. |

## Paper verdicts (from v0.3)

Paper claims: `REPRODUCED`, `FRAGILE`, `NOT_REPRODUCED`, `NOT_REPRODUCIBLE`,
`INCONCLUSIVE` (Refute could not decide for reasons on its side, such as an
exhausted budget or the hang guard; never a failure of the artifact).

All five are defined in the code (`PaperVerdict`). The rules are in
[docs/plans/v0.3-plan.md](plans/v0.3-plan.md), section 8.

**Status.** The rules below are the specification of the v0.3 plan. The verdict of
one claim (order, attribution, minimum coverage) and the result of a paper are
implemented in `refute.core.paper` (core work package WP2). The budget rules that
these verdicts refer to are not implemented yet.

`INCONCLUSIVE` means that Refute could not decide, for reasons on its side. It is
treated as a possibly correct answer that is less informative, with no value
judgment (plan, section 8.2).

### Gates and prerequisites

- **Gates of the base reproduction:** `environment_build`, `data_present`, and
  `run_completed` and `metric_extracted` of the **base** runs.
- **Prerequisites of an attack:** the run and the metric of **that** attack. An
  interruption or a failed prerequisite of an attack makes only that attack
  `INCONCLUSIVE`; it never reopens the base reproduction.

(Plan, section 8.1.)

### Order of verdicts for one claim

The first rule that matches decides. This order deliberately differs from the order
used for discovery verdicts (section "Aggregation" below), so that a valid robustness
failure is not erased by an attack that did not run:

0. coverage enforcement (see "Coverage for paper claims" below);
1. a gate of the base reproduction that did not pass: `NOT_REPRODUCIBLE` or
   `INCONCLUSIVE`, by the attribution rule below;
2. a valid fatal failure (`base_reproduction`, `metric_recompute`):
   `NOT_REPRODUCED`;
3. a base reproduction that is incomplete, with no valid negative conclusion:
   `INCONCLUSIVE`;
4. any attack with a valid failure and its prerequisites met: `FRAGILE`; the attacks
   not executed are recorded and the incomplete coverage is flagged;
5. any expected attack missing or `INCONCLUSIVE`: `INCONCLUSIVE`, with the status
   "Basic reproduction obtained; robustness inconclusive";
6. otherwise: `REPRODUCED`.

"Basic reproduction obtained" is declared only after `metric_recompute`, where it
applies. (Plan, section 8.1.)

### Attribution: `NOT_REPRODUCIBLE` or `INCONCLUSIVE`

At every stage (build, data, run, metric, attacks):

- **`NOT_REPRODUCIBLE`** only for a failure of the artifact's own documented
  procedure, shown by complete attempts:
  - every rung of the build ladder ran to its end and failed with an error of the
    procedure itself; or
  - the documented command fails in the built environment; or
  - a declared artifact answers as absent (for example HTTP 404 or 410) in all of the
    N attempts fixed before the lock, spaced by an interval fixed before the lock.
- **`INCONCLUSIVE`** for everything else: an exhausted budget, an operational guard,
  an error of Refute, a transient network failure, a stage interrupted before its
  end, or an undetermined cause.

In the code, a failed gate carries its recorded cause and the attempts completed and
required (`GateFailure`). `NOT_REPRODUCIBLE` needs all the required attempts and a
cause that applies to the gate:
- a build-ladder failure applies to `environment_build`;
- a failure of the documented command applies to `data_present` only;
- an absent artifact applies to every gate, and only with its evidence: one recorded
  HTTP status per attempt, each 404 or 410, whatever the gate's coverage.

Anything else is `INCONCLUSIVE`.

This mapping per gate is not in plan section 8, which states the attribution rule only.
It was introduced by `314a420` (2026-10-14); `c5d8b12` (2026-10-16) limited the
documented command to `data_present`; `c3d9514` (2026-10-16) required the HTTP evidence
for an absent artifact, whatever the coverage. The maintainer confirmed this document as
the record of the rule on 2026-10-16, at the acceptance of WP1 (#44); plan section 8 is
unchanged.

**A failed run or metric extraction is `INCONCLUSIVE` by default** (decided by the
maintainer on 2026-10-16). At `run_completed` and `metric_extracted`, an exit code from
1 to 125, even in every attempt, is not evidence that the artifact caused the failure:
a wrong argument in the transcribed command, a resource limit, a configuration on
Refute's side or an unknown cause give one too. These gates are never attributed to
the documented command; only a proven absence of a declared artifact applies there.
Cases where positive, deterministic evidence could justify attributing such a failure
to the artifact are left for a later decision of the maintainer and are not
implemented.

(Plan, section 8.2.)

### Partial results

Verdicts are per claim. An exhausted budget does not erase a conclusion already shown
with its prerequisites met:

- budget exhausted during the base reproduction, with no conclusion: `INCONCLUSIVE`
  (`budget_exhausted`), never `NOT_REPRODUCIBLE`;
- base reproduction obtained, robustness incomplete, and no valid negative
  conclusion: `INCONCLUSIVE`, with the status "Basic reproduction obtained;
  robustness inconclusive";
- a claim already shown to be `NOT_REPRODUCED`, or `FRAGILE` by a valid failure: the
  conclusion is kept, and the remaining checks are recorded as not executed.

Partial values go into the dossier as information only. (Plan, section 8.3.)

### The result of a paper

The result of a paper is the profile of its claims, never a single verdict:

- the report always shows the full profile of the claims, in the drawn order, with
  `INCONCLUSIVE` in the denominators;
- a headline appears only when every claim has the same verdict, with count and
  scope, for example "3 of 3 drawn claims: REPRODUCED"; otherwise the headline is
  "Mixed results: see the claims";
- no single claim defines the paper;
- a paper whose claims are all `INCONCLUSIVE`, or `INCONCLUSIVE` and `REPRODUCED`, is
  described as inconclusive for those claims, never as positive or reproduced, and
  stays in the denominators;
- any negative claim verdict starts the right of reply for that paper
  ([right-of-reply.md](right-of-reply.md)).

(Plan, section 8.3.)

### Coverage for paper claims

Each check has a coverage unit and a **minimum coverage**, fixed per claim before the
lock, separately for a positive and for a negative conclusion (for example, the base
reproduction must complete the number of seeds declared in the claim). Coverage below
the minimum gives no conclusion: it never yields a pass, and it yields a negative
conclusion only where the valid evidence already obtained establishes it.

**Proven absence of a declared artifact** (decided by the maintainer on 2026-10-16): a
gate that failed because a declared artifact answered HTTP 404 or 410 in **all** of the N
attempts fixed before the lock, with one recorded status per attempt, has examined no
example but its evidence is complete. It is decided by its attribution
(`NOT_REPRODUCIBLE`, section "Attribution") before the zero-coverage rule. Any other zero
coverage stays `INCONCLUSIVE`.

| Check | Coverage unit | Zero coverage means |
|---|---|---|
| claim extraction | approved claims | the paper cannot be `REPRODUCED` |
| `data_present` | examples per split (train, validation, test, holdout) | an empty split, or one smaller than the paper states (tolerance fixed), does not pass the gate |
| `metric_extracted` | examples the metric was computed on | a metric on zero examples does not pass the gate |
| `base_reproduction` | runs completed | no run: not decided |
| `metric_recompute` | base runs recomputed in full (all the claim's examples, by both implementations) | no run recomputed: `INCONCLUSIVE`, never PASS; one valid failure establishes the failure |
| `seeds`, `data_split` | valid runs completed | `INCONCLUSIVE`, never PASS |
| comparison | paired comparisons made | nothing compared: `INCONCLUSIVE` |
| the repository's own test suite | tests collected and not skipped | zero collected or all skipped: `INCONCLUSIVE` for that check, never PASS |
| `leakage` | example pairs hashed | `INCONCLUSIVE` |

The `metric_recompute` row is not in plan section 8: it was added by `c7a76ae`
(2026-10-15), from W3.17 of the WP3 acceptance
([wp3-acceptance.md](validation/v0.3/wp3-acceptance.md)). The maintainer confirmed this
document as its record on 2026-10-16, at the acceptance of WP1 (#44).

The repository's own test suite is information only: its result is reported with its
coverage and never decides a verdict. (Plan, section 8.4.)

## Test results

Every test returns `PASS`, `FAIL` or `INCONCLUSIVE` (never a silent skip), with a
severity that says what a failure means:

- `gate`: the signal itself is not significant, so nothing can be attacked;
- `fatal`: the failure refutes the claim;
- `warning`: the failure weakens the claim.

A test may report a different severity for different outcomes. For example the
secondary-eclipse test is fatal for a deep eclipse at phase 0.5 and a warning for a
shallow one.

## Coverage: no PASS without examined data

Every test result declares its **coverage**: how much data the check actually
examined (transits measured, cadences used, catalog rows scanned, sub-checks run),
with its unit. A `PASS` with zero coverage, or with no declared coverage, is turned
into `INCONCLUSIVE` by the engine before aggregation, with the reason. A check that
examined nothing has shown nothing. This rule lives in the core
(`refute.core.verdict.enforce_coverage`) and applies to every domain pack.

"Nothing found" is a valid `PASS` only when the data were examined: for example a
catalog that was searched around the target and has no entry there (coverage: the
rows scanned), or a TIC cone query that returned no neighbor (coverage: one query).

## Aggregation (deterministic)

Rules are applied in order; the first that matches decides:

0. a `PASS` without positive coverage counts as `INCONCLUSIVE`;
1. a gate test that did not `PASS` -> `INCONCLUSIVE`;
2. any fatal `FAIL` -> `REFUTED`;
3. any expected test missing, or any `INCONCLUSIVE` test -> `INCONCLUSIVE`;
4. any warning `FAIL` -> `WEAKENED`;
5. otherwise -> `SURVIVED`.

The pack declares the tests a complete analysis must contain (`expected_tests` in
`verdict.json`); a result missing any of them can never be `SURVIVED` or
`WEAKENED`.

A fatal failure refutes even when another test is inconclusive. A missing stellar
radius can never turn into a pass: the plausibility test is then `INCONCLUSIVE`,
and so is the verdict unless something else already refuted the signal.

## Calibration claims

For a calibration claim, per-target verdicts feed the claim's pass criteria. A
known planet *recovered* means its period was found within the tolerance. A known
false positive *flagged* means its verdict is `REFUTED`. The degeneracy guard caps
how many known planets may be `REFUTED`, so a gauntlet that refutes everything
fails the claim. Analysis errors count against the claim.

From v0.2 a calibration claim may list `flag_excluded_tests` in its pass criteria
(for example `eb_catalog`, whose catalogs may share sources with the dispositions
used to select the false positives). A false positive then counts as flagged only
if its verdict, recomputed with the rules above from the other tests, is `REFUTED`;
the count with every test is reported as information. The degeneracy guard always
uses the full verdict.

Verdicts are about claims, never about the people who made them.
