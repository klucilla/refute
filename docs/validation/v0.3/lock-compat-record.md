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

### Run 2, with the final script

The script was then hardened after the Codex review (commit e9c9534). It now trusts a
worktree only when:
- it is at the tag's commit;
- no tracked file has changed;
- the lock has a historical identity of the table.

It checks this before and after the run, and requires exit 0 as well as `PASS`. Run 2
used this version, on the same worktrees, on 2026-10-15. The run-1 files above stay as
they are.

| Tag | Commit | Status | Claim and code hashes | Output | SHA-256 of the output |
|---|---|---|---|---|---|
| `v0.1.0` | `6bb5e78ad24e` | PASS (exit 0) | equal to the lock, as in run 1 | [v0.1.0.run2.json](lock-compat-record/v0.1.0.run2.json) | `2ada52103295f3b8a0e7cdbe14b5db2f6f51ee93678fae4a81d46e9166a8e09b` |
| `v0.2.0-calibration-lock` | `cc9d104027ed` | PASS (exit 0) | equal to the lock, as in run 1 | [v0.2.0-calibration-lock.run2.json](lock-compat-record/v0.2.0-calibration-lock.run2.json) | `c6fe8c319973c6c26b2767721af52cf4a052397370bd38ebde0db7963409e268` |

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

Pending when this record was written: deleting the worktrees and their environments
under `.cache/` (`.cache/lock-compat/` and `.cache/hash-investigation/`). They are
regenerable, since the script recreates them. Their deletion is reported in the pull
request, not here.
