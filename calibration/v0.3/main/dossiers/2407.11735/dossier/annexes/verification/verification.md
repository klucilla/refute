# Dossier verification of 2407.11735

Item (a) of section 10.2 of docs/plans/v0.3-plan.md, by calibration/v0.3/verify_dossiers.py
(docs/validation/v0.3/dossier-verification-acceptance.md), with the frozen code of the locks.

**Result: VERIFIED.**

Sealed core: `dc84b305a59e2a3ea8ede04d0702412ed565f834ef616fdd2c20c896e43fb9cb`.

## Claims (recomputed and recorded)

- `arXiv-2407.11735v2-C1`: INCONCLUSIVE
- `arXiv-2407.11735v2-C2`: INCONCLUSIVE
- `arXiv-2407.11735v2-C3`: INCONCLUSIVE

Profile: 3 of 3 drawn claims: INCONCLUSIVE

## Findings

None: checks V1 to V5 passed.

## Limits

- The verification shows that the classification is deterministic from the recorded outputs, not that the experiment is repeatable (plan, lines 69-72).
- It replays the recorded check results; it does not re-read the logs and sources those checks were computed from.
- The completeness of the accounting is taken from the recorded status: the dossier does not record the parent cgroup's usage and the tolerance, so that comparison cannot be repeated numerically.
- The lock (claim.lock.json) is read from the published claim folder, not from the dossier; its history file is not read.
- The sample has no executed attack: the rebuilding of attack records is shown by a round-trip test on synthetic records.
