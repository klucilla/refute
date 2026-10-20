Reviewer: codex (second reviewer, another model family), dossier 2407.11735

## Summary (two sentences)

The three recorded `INCONCLUSIVE` outcomes follow the supplied verdict rules because execution stopped at an unsupported Dockerfile build, explicitly attributed to Refute. The sealed core is intact and the selected numerical claims match the cited paper, but missing review materials and declared measurement limitations leave important procedural objections.

## Objections

| Severity | Evidence | Why it matters |
|---|---|---|
| important | `claim_file.json`, `attachments`, names `inventory.json` and `draw.json`; dossier enumeration and `Test-Path` show both absent, and no selection or triage log is supplied. | The required checks of inventory completeness, draw conformity, and every triage rejection cannot be performed. The three selected transcriptions alone cannot establish that selection followed the protocol. |
| important | `claim.lock.json` and the attached `2407-cifar-matlab-files.patch` are absent. `annexes/verification/verification.json`, `limits`, explicitly says its lock was read from the external claim folder. `dossier.json`, `setup.patches`, records hashes and manifests rather than patch contents. | Within the authorized inputs, I cannot independently compare the claim against its preregistration lock or inspect whether the applied patch changes only archive locations. A valid core seal establishes present integrity, but does not establish these separate properties; no mismatch is demonstrated. |
| important | All targets’ `coverage_evidence.method.routes[0]` selects `^test examples evaluated=([0-9]+)$`, while its own `link[0].role` says the program prints no such count and the route finds none. `complementary` is empty. Dataset split declarations and leakage reasons also state that Refute cannot read the MATLAB archives. | According to the claim’s own declarations, successful training would still lack the evidence required to pass metric coverage, and the selected reader cannot establish split coverage. These are additional Refute measurement limitations, independent of the observed build stop, and must not become evidence against the artifact. The underlying source assertions remain unverified because the pinned repository was unreachable. |

## Checks with no objection (with evidence)

- **Core integrity passed.** The standard `uv run --frozen refute check-dossier …` failed before validation because uv could not initialize its cache. Running the installed CLI with `PYTHONPATH=C:\Projetos\refute\src` and bytecode writing disabled returned:
  
  ```text
  core: intact against its seal
  OK: manifest intact
  ```
  
  Independent SHA-256 calculations also matched all six entries in `SEAL.json.files`. Both claim files hash to `dcea7ed105a99f336a124db706d1683d058b12fb8b1a2979bc838ede9a25a34f`; the validated core seal is `dc84b305a59e2a3ea8ede04d0702412ed565f834ef616fdd2c20c896e43fb9cb`.

- **Selected numerical transcriptions match version 2.** For CIFAR-10 ID and CIFAR-100 OOD, C1 records accuracy `94.50 ± 0.05%` with 4,000 labels, C2 records AUROC `0.92 ± 0.00` with 1,000 labels, and C3 records AUROC `0.93 ± 0.00` with 4,000 labels. These match page 10, Table 1; section 4 on that page specifies final test evaluation, mean and standard deviation over three runs, using EMA parameters. The targets’ `type=value` and `comparison=null` appropriately describe numerical claims. ([Paper v2, page 10](https://arxiv.org/pdf/2407.11735v2#page=10))

- **Declared principal training settings match the paper.** The targets’ `run.argv` specifies WRN-28-2, self-supervision weight 10, 50,000 warm-up steps, and 524,288 training steps, consistent with section 4.1 on page 11. Full command fidelity remains unverified without repository access. ([Paper v2, page 11](https://arxiv.org/pdf/2407.11735v2#page=11))

- **Seed quoting is valid.** Parsing `inventory.transcription.command` reproduces `run.argv` plus `seed_argument` for all three targets. A shell diagnostic using the actual seed fragment returned `<--seed=1150177701>`, exit code 0. This checks argument quoting only.

- **The observed failure is correctly attributed.** `logs/setup_build_own_environment.log` says `refute: version 1 does not build a Dockerfile`. `dossier.json`, `outcome.ladder.failure`, records `cause=refute_error` and zero completed attempts; the requirements rung was not reached. Under `docs/verdicts.md`, “Attribution,” this supports the recorded `INCONCLUSIVE` outcomes and supplies no artifact-failure conclusion.

- **Unexecuted checks receive no scientific conclusion.** Every claim’s base checks have zero coverage and `INCONCLUSIVE` status; `base_reproduction.metrics.valid_runs=0`. Attack results are null, `basic_reproduction_obtained=false`, and `incomplete_coverage=true`. No check passes without examined data.

- **Recorded dataset declarations agree.** Each `provenance.datasets` hash and size matches its corresponding `test_plan.datasets` declaration. This establishes consistency between records only: the archive bytes were not supplied, and all recorded counts are null.

- **The profile does not overstate the result.** `outcome.profile` retains all three claims in drawn order, counts all three as inconclusive, and headlines them as `3 of 3 drawn claims: INCONCLUSIVE`. It makes no positive reproduction claim or statement about the authors.

**Checks I could not complete:**

- **Inventory, draw, triage, preregistration, and patch-content verification:** the necessary files are absent, as detailed above; prohibited external claim folders and git history were not consulted.
- **Pinned-source inspection:** attempts to reach README, Dockerfile, and evaluation code at commit `8a28cf3d2cb54250f75a3f6a542f93745d1928ce` failed through GitHub/raw/API access. Consequently, command fidelity, TensorBoard tags and units, evaluation implementation, attack applicability, and the rationale for disabling metric recomputation remain unverified.
- **Data-content, metric, robustness, and repeatability checks:** archives, predictions, and successful run outputs are absent; setup prevented execution. No experiment was rerun.
- **Independent accounting and sustained resource-limit verification:** the parent cgroup usage and comparison tolerance are absent, as acknowledged in `annexes/verification/verification.json.limits`; `provenance.profile_limits` also limits its assertions to operator-recorded observations.
- **Narrative report review:** no core `report.md` is supplied, so text review covers the claim descriptions and engine profile only.
- **Visual PDF inspection:** screenshot retrieval failed; paper checks used the accessible versioned PDF text. Other reviewers’ reports were not consulted.

## Assessment: OBJECTIONS