# Repository weights on the VM, 2026-10-19

The proof of [wp3-repository-weights-acceptance.md](../wp3-repository-weights-acceptance.md),
section 4, on the Refute VM, from Refute checkouts made by bundle of `main`.

## The offline tests on Linux

On the VM (Linux, where symbolic links and the POSIX paths of a container plan exist), the
files `tests/test_ml_repository_weights.py`, `tests/test_vm_count_population.py`,
`tests/test_ml_data_sources.py` and `tests/test_ml_production.py`, counts from the JUnit XML:

| Refute | Tests | Failures | Errors | Skipped |
|---|---|---|---|---|
| `c820bb6` | 156 | 0 | 0 | 0 |
| `5039bdc` (after Codex's code review, round 2) | 165 | 0 | 0 | 0 |

## The production wiring with a repository weights file

`scripts/vm/production_vm_test.py --weights`, the synthetic paper `reproduced` (every attack),
the engine's base image, the ladder's build through the allowlist proxy (profile build),
the runs with no network. The repository is a Git repository holding `saved/model.bin`,
declared as weights that are a file of the commit and named by the claim; Refute verified it
as a regular blob of the commit, then the tree's file was overwritten; each run's
`train.py` runs the trainer only if the file it reads at `saved/model.bin` has the
committed bytes and cannot be opened for writing.

| Refute | Started (UTC) | Verdict | Accounting | Run logs with the check passed | Refused |
|---|---|---|---|---|---|
| `c820bb6` | 11:58:50 | REPRODUCED | complete | 15 of 15 | 0 |
| `5039bdc` | 12:11:53 | REPRODUCED | complete | 15 of 15 | 0 |

The setup's record of the weights, both runs: `{"model": {"mount_planned": true, "path":
"saved/model.bin", "reason": null, "sha256":
"e57edaa149ce044379bf547ac29b385d29feecf7c5ba6846c709237aed31b737", "verified": true}}`.

## The count before the lock of 2302.12465

The count's two containers read the repository's predictor from Refute's verified copy:
see [calibration/v0.3/main/claims/2302.12465/counts/README.md](../../../../calibration/v0.3/main/claims/2302.12465/counts/README.md)
(K = 129 in every run, at `c820bb6` and again at `5039bdc`, whose records name the mounted
weights).
