# Dossier verification of the main sample (acceptance)

Item (a) of section 10.2 of [docs/plans/v0.3-plan.md](../../plans/v0.3-plan.md), and condition 3
of "processed end to end" (plan, lines 54-67): "the hashes are checked, the execution states and
the reasons of every interruption are checked, and the verdicts are recomputed from the recorded
outputs, without running the experiments again". The frozen code (f7601b9) has no tool that
does this for the production dossiers of the ML pack: `refute check-dossier` checks the
manifest, the seal and the reviews only. Approved by the maintainer on 2026-10-19 (a script
outside the code hash that calls the frozen functions, with the two additions of the Codex
review of the same day). This document is committed before the script and its tests.

## 1. What the verifier is

- A script, `calibration/v0.3/verify_dossiers.py`, outside the code hash of the locks (the code
  hash covers `src/`, `pyproject.toml` and `uv.lock`). It changes nothing in `src/` and runs
  with the frozen package.
- It reads one published dossier (`calibration/v0.3/main/dossiers/<arxiv>/dossier/`) and the
  published claim folder (`calibration/v0.3/main/claims/<arxiv>/claim/`), and writes a report
  (Markdown and canonical JSON). It never runs an experiment and never opens a network
  connection.
- Its result for a dossier is `VERIFIED` (every check below passes) or `NOT VERIFIED` with the
  list of findings. A finding never changes a verdict; it is reported.

## 2. What it checks

**V1. Hashes.** `refute check-dossier` logic on the dossier: every line of `MANIFEST.sha256`,
and the core against `SEAL.json`. `dossier.json`'s `claim_file_sha256` is the SHA-256 of
`claim_file.json`; `claim_input.json` and `claim_file.json` have the same bytes; their SHA-256
is the `claim_sha256` of the published `claim.lock.json` of the same paper.

**V2. Verdicts recomputed.** For each claim of `outcome.claims`, in the order of the claim
file's `targets` (keys equal, same order):
- the inputs of the frozen `refute.core.paper.aggregate_claim` are rebuilt from the record:
  `base` (TestResult), `attacks` (Attack with its run, metric and result), `failures`
  (GateFailure) from `dossier.json`; `expected_attacks` (the applicable attacks, in the claim's
  order), `metric_recompute_applies`, `minimums` and `not_applicable` from the target in
  `claim_file.json`, through the frozen `ClaimContext` (`applicable`, `minimums`,
  `not_applicable`);
- the recomputed verdict equals the recorded `computed`;
- **the accounting rule (Codex, addition 1):** when `outcome.run` exists and
  `accounting_valid` is false, the expected verdict is INCONCLUSIVE with the reason
  `"the accounting of the paper is invalid: <invalid reasons>"` and the recomputed
  `gates_not_applicable`, as in integration.py lines 1800-1806; otherwise the expected verdict
  is the recomputed one;
- the expected verdict equals the recorded `verdict` in every field (verdict, reason, status,
  basic reproduction obtained, attacks not executed, attacks incomplete, incomplete coverage,
  gates not applicable).

**V3. Profile recomputed.** The frozen `paper_profile` of the recorded claim verdicts, in the
targets' order, equals `outcome.profile` in every field (claims, counts, total, headline,
has negative).

**V4. Execution states and the reasons of every interruption (Codex, addition 2),** checked
from the step records themselves, not from the verdicts:
- *expected steps:* the steps recorded are exactly the plan's: `build` and `data/<dataset>` for
  each dataset the frozen `container_datasets` names (setup); `base` for each claim; one step
  per applicable attack in the frozen `CONTAINER_ATTACKS` (attacks), except an ablation switched
  by a configuration file. No step is missing, none is extra, none is recorded twice. With no
  run (`outcome.run` null), no applicable rung is the only allowed reason, shown by the ladder;
- *order:* the steps with containers ran in the plan's order (setup, then the base of each
  claim in the drawn order, then the attacks); no attack step with containers comes before the
  last base step with containers;
- *outcome of each step with containers:* for a step without a fallback (base, attacks), the
  recorded outcome and reason are those of the frozen `orchestrate._outcome` on its container
  records, or REFUTE_ERROR with a reason that holds them (a rejected record or invalid
  accounting closes the step so). For a step with a fallback (`build`, `data/*`), the outcome is
  that of the last container when it is a stop on Refute's side; otherwise COMPLETED only if
  the last container exited 0, else FAILED; every earlier container of the build ladder exited
  with a non-zero code;
- *steps without containers:* NOT_EXECUTED, BUDGET_EXHAUSTED or REFUTE_ERROR, each with a
  non-empty reason; a step recorded as NOT_EXECUTED has one of the frozen runner's reasons:
  the setup did not complete, the setup budget exhausted, the claim not run (with its reason),
  "step <name> did not complete (<outcome>)", not eligible for attacks, or the paper stopped /
  not reached;
- *every interruption has its reason:* every step not COMPLETED has a non-empty reason; a
  container with no result has an error; a stopped container has a known stop cause;
- *the run's own record:* `base_obtained[claim]` is true only if every base step of the claim
  completed; `stopped` non-empty implies `accounting_valid` false and `stopped` among
  `invalid_reasons`; `attack_claims` are claims whose base was obtained and that have an
  attack step; `setup_exhausted` true implies every base step NOT_EXECUTED with the setup's
  budget reason.

**V5. The ladder.** The `build` step's containers are `setup/build/<rung>` for the applicable
rungs of `outcome.ladder.attempts`, in the ladder's order; a COMPLETED build names its last
container's rung as `built_with`.

## 3. Limits (stated in every report)

- The verification shows that the **classification is deterministic** from the recorded
  outputs, not that the **experiment is repeatable** (plan, lines 69-72).
- It replays the recorded check results; it does not re-read the logs and sources those checks
  were computed from.
- The completeness of the accounting is taken from the recorded status: the dossier records the
  status, not the parent cgroup's usage and the tolerance it was computed from, so that
  comparison cannot be repeated numerically.
- The dossier does not hold `claim.lock.json` and its history: V1 reads them from the published
  claim folder.

## 4. Synthetic and regression cases

Must pass:
- each of the five published dossiers of the main sample (they are in the repository, so the
  tests need no network);
- a copy of a dossier whose step order and records are untouched but whose folder has another
  name.

Must fail (each on a copy in a temporary folder, with the finding named):
- a manifest line changed (V1); `claim_input.json` changed and the manifest updated to match
  (V1, the lock's hash);
- a recorded verdict changed (V2); a recorded `computed` changed (V2);
- `accounting_valid` set to false with the verdicts left as they were (V2, the accounting
  rule);
- the profile's headline or a count changed (V3);
- a base step's outcome changed from FAILED to COMPLETED (V4, the outcome of its containers);
- a step removed, a step duplicated, a step not in the plan added (V4, expected steps);
- the reason of a NOT_EXECUTED step emptied (V4, reasons);
- `base_obtained` set to true for a claim whose base step failed (V4);
- `built_with` naming a rung that did not complete (V5);
- a malformed `dossier.json` (not JSON, a missing field): a finding, never a crash.

## 4a. Corrections after the Codex review of 420c844 (2026-10-20)

The review found false accepts in V4, a crash on a malformed record, and a V1 that trusts the
seal it is given. These rules replace the matching ones above; nothing else changes.

- **V1, anchored.** The core hash in the dossier's `SEAL.json` equals the one committed for that
  paper in `calibration/v0.3/main/SEAL-RECORD.md`. The annexes in the dossier are exactly the
  ones `calibration/v0.3/main/ANNEX-RECORD.md` lists for that paper, each with the listed
  SHA-256 of its `ANNEX.json`.
- **Shapes first.** Before V2, the fields the checks decide on have their recorded types:
  booleans are JSON booleans (`accounting_valid`, `setup_exhausted`, `base_obtained` values),
  `stopped` and reasons are strings, `steps`, `attack_claims`, `invalid_reasons` and
  `ladder.attempts` are lists, and the ladder lists the frozen rungs (`ladder.RUNGS`) in order.
  A record that does not have them is a finding, never a crash; any unexpected error while
  reading is a finding too.
- **No run.** `outcome.run` null is accepted only when the ladder lists every frozen rung, none
  applicable, and no claim's `environment_build` check passed.
- **Fallback steps, as the frozen code runs them.** `build` (the ladder): every container but the
  last ended FAILED by the frozen `_outcome` (a rung classified "next"); a container with no
  result or stopped on Refute's side is the last one and the step has its outcome and reason;
  otherwise a last container that exited 0 gives COMPLETED with no reason or FAILED with "the
  container ended but is not a success", and one that failed gives FAILED with its reason.
  `data/<dataset>` (a container reader, whose fallback always answers "completed"): its outcome
  and reason are the container's when that is a stop on Refute's side or a missing result, and
  COMPLETED with no reason otherwise, whatever the exit code; the reader's failure shows in the
  data evidence, not in the step. This replaces "COMPLETED only if the last container exited 0"
  for the readers.
- **REFUTE_ERROR, with its consequences.** A recorded REFUTE_ERROR where the containers give
  another outcome is accepted only when its reason is the containers' reason followed by
  rejected-record messages of the step's own containers or by entries of `invalid_reasons`. The
  first REFUTE_ERROR step in the record sets `stopped` to `"<phase> <claim> <step>: <reason>"`;
  a `stopped` with no REFUTE_ERROR step is one of the frozen runner's own stops (an unexpected
  error, the completeness check); a stopped run has invalid accounting with `stopped` among
  `invalid_reasons`. A container stopped for a cause outside the frozen known stops is a finding.
- **NOT_EXECUTED reasons, by cause.** "the setup did not complete" only for a base step when a
  setup step did not complete; the setup's budget reason only when `setup_exhausted` is true
  and the setup completed, and then for every base step; the claim's not-run reason only when
  it equals the frozen `not_run_reason` of that claim (with the repository weights the dossier
  records), and then for that claim's base step; "step X did not complete (Y)" only when X is
  an earlier step of the same phase and claim, recorded with outcome Y other than completed;
  "not eligible for attacks" only for a claim outside `attack_claims`; "the paper stopped: S"
  only with `stopped` equal to S. "not reached" is never given by a run that did not stop. A
  base step with no containers named `base_obtained` is accepted only as REFUTE_ERROR with "the
  base evaluation failed: ...".
- **Attack eligibility.** In a run that did not stop, `attack_claims` is exactly the claims whose
  base was obtained and that have an attack step.
- **Limits.** The lock is read from the published claim folder (`claim.lock.json`); its history
  file is not read. The five dossiers have no executed attack, so the rebuilding of attack
  records is shown by a round-trip test on synthetic records.
- **Tests added:** each false accept the review reproduced (a build FAILED with an exit-0 last
  container; a REFUTE_ERROR invented on a failed base step; an unknown stop cause; each wrong
  NOT_EXECUTED reason; `setup_exhausted` with the wrong reason; a stop with no REFUTE_ERROR; a
  `run` of null with an empty ladder; `accounting_valid` as a string; a ladder that is not an
  object); an order mutation; a positive case of the accounting rule (verdicts and profile
  updated: no V2, V3 or V4 finding); a missing field with its own finding; a seal or an annex
  that does not match the committed records; the attack round trip.

## 4b. Three paths of the frozen runner that 4a rejected (Codex check of 2e57b81, 2026-10-20)

- **A stopped container has no exit code.** Both backends record `exit_code` null when
  supervision stops a run; the shape accepts null when the container's `stopped` is set, and an
  integer otherwise.
- **A refused grant between rungs.** After a rung that failed and was classified "next", the
  grant of the next applicable rung can be refused: the build step then ends with the refusal
  (BUDGET_EXHAUSTED with `"budget_exhausted (setup)"`, or REFUTE_ERROR with the refusal's
  reason) and keeps the earlier containers. This is accepted when every recorded container
  failed and fewer containers ran than the ladder has applicable rungs.
- **The classifier failed.** When classifying a rung raises, the frozen fallback ends the step
  with REFUTE_ERROR and `"the fallback failed: <exception>"`; this is accepted after a last
  container that was not stopped on Refute's side. Its stop and accounting consequences are
  checked as for every REFUTE_ERROR.
- **Positive tests:** a threshold stop with no exit code, a refusal between two rungs, and a
  classifier failure give no V4 finding on their steps.

## 5. Evidence

- Test counts from a JUnit XML file; ruff exits 0.
- A Codex review (read only) of the script and its tests.
- The report on the five dossiers of the main sample is attached to each dossier as an annex
  (`refute annex <dossier> verification <folder>`), and the SHA-256 of each annex's
  `ANNEX.json` is committed and pushed at once (plan, section 9.1, item 2).
