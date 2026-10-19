# WP3 addendum: a claim that needs declared weights, in version 1

Addendum to [wp3-acceptance.md](wp3-acceptance.md) and
[wp3-data-sources-acceptance.md](wp3-data-sources-acceptance.md), committed before its tests
and code (plan section 11). It implements the maintainer's decision 4 of 2026-10-18 for the
main sample: the CLIP claims of 2305.19518 are declared at the lock as `INCONCLUSIVE` by an
unsupported capability (declared weights), with no run, while its SimCLR claim runs
normally; the support of declared weights (fetch, check, read-only mount) and #338 come after
the seal (an item of #59). Found while writing the claims package: the engine refuses a whole
paper whose `test_plan.weights` is not empty (`production.prepare_inputs`), before any run and
with no dossier, so no claim of such a paper could run, and a claim on pre-trained weights that
it trains with (not a checkpoint it evaluates) could not name them.

## 1. The rule (generic)

- **Schema.** A claim names the weights it needs with `weights` (an entry of
  `test_plan.weights`): required for `scope: checkpoint_evaluation`, as today, and allowed for
  `scope: full_training` when the run loads a pre-trained model as an input (for example a
  frozen encoder). A name that is not a declared entry is refused, as today.
- **Version 1 does not fetch weights.** A paper whose `test_plan.weights` is not empty is no
  longer refused: its datasets are fetched, its setup (the ladder, the container readers)
  runs as for any paper, and its weights are not fetched, checked or mounted (recorded in the
  dossier's setup).
- **The claims that need weights are not run.** A claim needs weights when it names
  `weights`, or when its dataset is generated with weights among its `inputs` (the reason the
  paper was refused until now, Codex review of the data sources: such a run would read no
  weights). Such a claim gets no container: its base steps and its attack steps are recorded as not executed, with the
  reason "declared weights are not fetched, checked or mounted by version 1 (an unsupported
  capability)", and they are charged nothing. Its `run_completed` gate is `INCONCLUSIVE` with
  the cause `refute_error` and that reason (a stop of the setup or of the paper, if any, is
  kept with it, and the claim's notes repeat the reason), so the claim is `INCONCLUSIVE` on
  Refute's side. The core's verdict order is unchanged: when an earlier gate already
  establishes an artifact failure with its prerequisites (`environment_build`: every rung
  failed by its procedure; `data_present`: the dataset proved absent in every attempt), that
  conclusion holds for this claim as for any other, since it does not depend on the weights;
  the weights never turn an unproven case into an artifact's failure (Codex round 1: the
  precedence, kept on purpose). Its other gates are recorded as for any claim with no run.
- **The other claims of the paper run normally**, in the drawn order. The budget is unchanged:
  `n` (the number of claims of the paper) counts every drawn claim, so each reserve is the
  same; a claim that is not run consumes nothing, and its reserve stays in the balance of the
  claims that follow (plan 7.3, rule A2, as for a claim whose base ends early).
- **The dossier** is written as for any run; it states, per claim, that it was not run and
  why.

## 2. Cases

**Must pass:** a claim on `full_training` that names a declared weights entry validates; a
paper with weights and two claims, one naming the weights and one not: the first is not run
(no container, nothing charged, `run_completed` `INCONCLUSIVE` with `refute_error` and the
reason), the second runs and gets its verdict; the dossier records both; a paper whose every
claim names weights runs its setup, runs no claim, and every claim is `INCONCLUSIVE` with that
reason, in the absence of an artifact failure validly established by an earlier gate.

Also: a claim needing weights whose setup stops (a Dockerfile not built by version 1, as in
2502.16782) keeps both reasons in its `run_completed` gate; a blocked claim before and after
a runnable one; the dependency through a generated dataset's `inputs`; no backend call for a
blocked claim; only the setup charged when no claim runs.

**Must fail:** a claim naming weights that `test_plan.weights` does not declare (refused at
validation); `checkpoint_evaluation` without `weights` (refused, as today).

## 3. Regression

A paper with no weights runs, charges and is judged as today.
