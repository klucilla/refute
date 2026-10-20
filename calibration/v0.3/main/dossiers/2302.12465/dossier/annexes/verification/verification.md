# Dossier verification of 2302.12465

Item (a) of section 10.2 of docs/plans/v0.3-plan.md, by calibration/v0.3/verify_dossiers.py
(docs/validation/v0.3/dossier-verification-acceptance.md), with the frozen code of the locks.

**Result: VERIFIED.**

Sealed core: `d18e74776aa886de1ec271c3d31f40dc7f9001452b4aaca41031a674e20366f1`.

## Claims (recomputed and recorded)

- `arXiv-2302.12465v3-C1`: REPRODUCED
- `arXiv-2302.12465v3-C2`: REPRODUCED
- `arXiv-2302.12465v3-C3`: REPRODUCED

Profile: 3 of 3 drawn claims: REPRODUCED

## Findings

None: checks V1 to V5 passed.

## Limits

- The verification shows that the classification is deterministic from the recorded outputs, not that the experiment is repeatable (plan, lines 69-72).
- It replays the recorded check results; it does not re-read the logs and sources those checks were computed from.
- The completeness of the accounting is taken from the recorded status: the dossier does not record the parent cgroup's usage and the tolerance, so that comparison cannot be repeated numerically.
- The lock (claim.lock.json) is read from the published claim folder, not from the dossier; its history file is not read.
- The sample has no executed attack: the rebuilding of attack records is shown by a round-trip test on synthetic records.
