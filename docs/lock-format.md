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

| Exit code | Status | Meaning |
|---|---|---|
| 0 | `PASS` | Every hash matches and the lock is the latest history entry. |
| 1 | `FAIL` | No lock, unreadable lock, invalid claim, missing attachment, or lock not recorded as the latest history entry. |
| 2 | `TAMPERED` | The claim, an attachment or the code differs from the lock. The output names the component and the changed files. |

`TAMPERED` takes precedence over `FAIL`. `refute replicate` and `refute calibrate`
run `verify` first and stop with the same exit code unless it is `PASS`.

## Interoperability

The format is deliberately small (one JSON file, one Markdown log, SHA-256 and a
documented canonical JSON) so it can be mapped to other pre-registration formats
such as PRML later. A compatibility statement is planned for v1.0.
