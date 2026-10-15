# Record: verification of the historical locks at their tags (option C)

Criteria L8 and L9 of [lock-compat-acceptance.md](lock-compat-acceptance.md). This is
the independent check of the historical projection: each lock is verified with the
code and environment of its own tag, not with the current code.

## Run

- **Date:** 2026-10-15 (`verified_at_utc` in each output).
- **Machine:** the maintainer's Windows 11 machine, CPU affinity on threads 8 to 31.
- **uv:** 0.12.1. **Interpreter:** CPython 3.13.5, the version recorded in both locks.
  It was passed with `--python`, because the uv-managed interpreters do not work on
  this machine.
- **Script:** [`scripts/verify_locked_tags.py`](../../../scripts/verify_locked_tags.py),
  run from the branch `claude/v0-3-lock-compat` (the commit after e8c541e). For each tag
  the script:
  1. checks out the tag in a detached worktree under `.cache/lock-compat/`;
  2. runs `uv sync --frozen` there;
  3. runs `uv run --frozen refute verify <claim> --json` there.

  The main checkout is not touched.

## Results

| Tag | Commit | Claim | Status | Claim hash (locked = now) | Code hash (locked = now) | Output | SHA-256 of the output |
|---|---|---|---|---|---|---|---|
| `v0.1.0` | `6bb5e78ad24e` | `calibration/self_claim.yaml` | PASS (exit 0) | `5701c54cb088…a53f` | `624f5f900334…4cfa` | [v0.1.0.json](lock-compat-record/v0.1.0.json) | `5192ab2b0228bc8edd2604c813f0de2a3a6ed53cb9de0d48a293c6f954983cea` |
| `v0.2.0-calibration-lock` | `cc9d104027ed` | `calibration/v0.2/self_claim.yaml` | PASS (exit 0) | `c9f341d29bea…34a8` | `2cd8b5c16c9d…1752` | [v0.2.0-calibration-lock.json](lock-compat-record/v0.2.0-calibration-lock.json) | `0ab1f639998fc96a95fbaf1f5e1a5fe7f08d94eb818f7bfc33242f818e6d3f94` |

In both outputs every attachment matches its lock, and no component is `TAMPERED`.

## How this relates to the projection

- At each tag, the claim, code and attachment hashes all equal the lock: the lock is
  intact in its own environment.
- With the current code, the projection of `src/refute/core/lock_compat.py` gives the
  same locked claim hashes (`tests/test_lock_compat.py`). The code component is
  `TAMPERED` there, as expected, because the code changed after the locks.
- The two checks are independent:
  - this record runs only historical code;
  - the projection runs only current code;
  - both reach the locked claim hashes.

## Cleanup

After this record, the worktrees and their environments under `.cache/` are deleted.
They are regenerable: the script recreates them. They are listed in the report of the
round:
- the ones created by this script under `.cache/lock-compat/`;
- the ones of the investigation under `.cache/hash-investigation/`.
