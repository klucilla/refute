# Lock format and verification

Pre-registration means the claim, the test plan and the code that will judge the
claim are fixed **before** hidden data are revealed. Refute does this with a lock.

## Canonical claim hash (`refute-cjson-1`)

1. Load `claim.yaml` and resolve it with its domain pack (every default written out).
2. Convert to plain JSON values; normalize every string to Unicode NFC.
3. Serialize with sorted keys, separators `,` and `:`, no ASCII escaping, no NaN.
4. Encode as UTF-8 and take the SHA-256.

YAML key order, comments and whitespace do not change the hash. Any value does.

## Attachment hashes

Each attachment is hashed with SHA-256. Text files (valid UTF-8 without NUL bytes)
have CRLF normalized to LF first, so a Windows checkout and a Linux checkout give
the same hash. Binary files are hashed as raw bytes.

## Code hash (`refute-code-1`)

Every regular file under `src/` (excluding `__pycache__/`, `*.pyc`, `*.pyo`,
`*.egg-info/`, `*.dist-info/`) plus `pyproject.toml` and `uv.lock` at the project
root. For each file: its POSIX path relative to the project root and its SHA-256
(text normalized as above). Lines `"<sha256>  <path>\n"` are sorted by path; the
SHA-256 of their concatenation is the code hash. The file list is stored in the
lock, so a mismatch names the files that changed.

Consequence: **any code change after locking makes the claim `TAMPERED`.** To
continue, the claim must be re-locked with `--force --reason`, which is recorded.

## The lock file

`refute lock path/to/claim.yaml` writes `path/to/claim.lock.json`:

```json
{
  "lock_version": 1,
  "canonicalization": "refute-cjson-1",
  "claim_path": "self_claim.yaml",
  "claim_id": "tess-calibration-v0.1",
  "claim_kind": "calibration",
  "claim_sha256": "…",
  "attachments": [{"path": "targets.yaml", "role": "targets", "sha256": "…"}],
  "code": {"algorithm": "refute-code-1", "sha256": "…", "files": [{"path": "…", "sha256": "…"}]},
  "git_commit": "…",
  "git_dirty": false,
  "git_dirty_paths": [],
  "claim_path_in_repo": "calibration/self_claim.yaml",
  "locked_at_utc": "2026-10-07T00:00:00Z",
  "refute_version": "0.1.0",
  "python_version": "3.13.5"
}
```

The claim file itself is never modified by `refute lock`.

## Clean-tree rule

For `calibration` claims, `refute lock` refuses (exit code 1) unless the claim is
inside a git repository with at least one commit and the working tree is clean
(`git status --porcelain --untracked-files=all` is empty). The only files ignored
are the two that the lock itself writes: the lock file and `LOCK_HISTORY.md`.
The recorded `git_commit` therefore contains exactly the code, claim and
attachments that were hashed. `replicate` claims may be locked from a dirty tree
or outside git; the lock records `git_dirty: true` (or `null`) and a warning.

## Lock history (`LOCK_HISTORY.md`)

Every `refute lock` appends one entry to `LOCK_HISTORY.md` in the claim's
directory:

```markdown
## 2026-10-07T00:00:00Z | self_claim.yaml

- action: lock
- claim_id: tess-calibration-v0.1
- claim_sha256: …
- previous_claim_sha256: none
- attachments: targets.yaml=…
- code_sha256: …
- git_commit: …
- git_dirty: false
- refute_version: 0.1.0
- reason: initial lock
```

Re-locking an already locked claim requires `--force` and a non-empty `--reason`
and is recorded as `action: relock`. Entries are never rewritten. The git history
of this file is the evidence of when each lock happened.

## `refute verify`

Recomputes the claim hash, every attachment hash and the code hash, and checks
that the lock is the latest `LOCK_HISTORY.md` entry for that claim.

### What verify compares with the history (issue #65)

The latest entry for the claim (selected by its `claim_path`) must record exactly the
lock: every field the entry shares with the lock file is compared, each by its rule.
There is no normalization of case, whitespace, Unicode or paths: the lock's value is
turned into the text `refute lock` writes, and the two texts must be equal.

| Entry field | Lock file field | Rule |
|---|---|---|
| `locked_at_utc` (the heading) | `locked_at_utc` | a string, as is |
| `claim_id` | `claim_id` | a string, as is |
| `claim_sha256` | `claim_sha256` | a string, as is (lowercase hex as written) |
| `attachments` | `attachments` | a list of objects with a string `path` and `sha256`, written `path=sha256` joined by `, ` in the lock's order; `none` when empty |
| `code_sha256` | `code.sha256` | a string, as is |
| `git_commit` | `git_commit` | a string, or null; null or an empty string is written `none` |
| `git_dirty` | `git_dirty` | `true`, `false` or null, written `true`, `false` or `none` |
| `refute_version` | `refute_version` | a string, as is |

`action`, `previous_claim_sha256` and `reason` have no counterpart in the lock file and
are not compared. **A missing field is never skipped:** a field missing from the lock
file, from the entry, or from both is a difference (one per missing side), and so is a
lock value of a type its rule does not accept. Any difference makes `verify` `FAIL`, and
its message names each field.

This comparison only reads the lock file and `LOCK_HISTORY.md`; it never rewrites
either. The two historical locks (v0.1 and v0.2) match every shared field of their
entries (`tests/test_lock_history_fields.py`).

| Exit code | Status | Meaning |
|---|---|---|
| 0 | `PASS` | Every hash matches and the lock is the latest history entry, which records every shared field exactly. |
| 1 | `FAIL` | No lock, unreadable lock, invalid claim, missing attachment, lock not recorded as the latest history entry, or a shared field of that entry that differs or is missing. |
| 2 | `TAMPERED` | The claim, an attachment or the code differs from the lock. The output names the component and the changed files. |

`TAMPERED` takes precedence over `FAIL`. `refute replicate` and `refute calibrate`
run `verify` first and stop with the same exit code unless it is `PASS`.

## Historical locks: projection of the claim hash

The claim hash covers the *resolved* claim, so an optional field added to the schema
after a lock changes the resolved hash of the older claim even though its file is
unchanged (issue #30). For the historical locks listed in
`src/refute/core/lock_compat.py` (the v0.1 and v0.2 calibration claims), `verify`
then tries a projection of the claim:

- **Which locks.** A lock gets a projection only when its `lock_version`,
  `canonicalization`, `claim_id`, `claim_kind`, `claim_path_in_repo`, `claim_sha256`,
  code hash, `git_commit` and `locked_at_utc` all equal a table entry.
- **What is removed.** The projection removes exactly the key paths listed for that
  lock, the fields added since it. It applies only if each listed path still has its
  frozen value, compared as canonical JSON, and none of them is written in the claim
  file.
- **The result.** If the remaining resolved claim hashes to the locked `claim_sha256`,
  the claim component matches. The output then names the table entry and gives the
  full resolved hash and the projected hash.

The projection shows that the claim content and the values resolved at lock time are
intact. It does not show that the current code evaluates the claim the same way. The
attachment, code and history checks are unchanged, so a code difference keeps the
result `TAMPERED`, and `calibrate` and `replicate` still stop. The table is frozen, and
its provenance is the fixtures in `tests/fixtures/locked_canonical/`: each is the
canonical form computed with the lock commit's own code, and each hashes to its locked
`claim_sha256`. The acceptance criteria are in
[validation/v0.3/lock-compat-acceptance.md](validation/v0.3/lock-compat-acceptance.md).
The verification at each lock's tag, in its own environment, remains the complete check
(see the README and
[validation/v0.3/lock-compat-record.md](validation/v0.3/lock-compat-record.md)).

## Interoperability

The format is deliberately small (one JSON file, one Markdown log, SHA-256 and a
documented canonical JSON) so it can be mapped to other pre-registration formats
such as PRML later. A compatibility statement is planned for v1.0.
