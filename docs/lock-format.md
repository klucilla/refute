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

- **The history is read literally.** No whitespace is removed from a value or from the
  heading; any field written twice in an entry, shared or not (a bullet that repeats the
  heading's `locked_at_utc` or `claim`, and a second `reason`, included), is a
  difference, never replaced by another value.
- **Ambiguous attachments.** When an attachment path in the lock file holds `, `, `=` or a
  line break, two different lists could give the same text, so the comparison reports a
  difference for `attachments`. `refute lock` still writes such a lock as before.
- **The lock file itself.** For `verify`, a lock file without a string `claim_path` or
  `code.sha256`, or whose `attachments` or `code.files` (when present) is not a list of
  objects with a string `path` and `sha256`, is `FAIL`, with the field named. `refute
  lock` reads an existing lock as before.
- **An unreadable `LOCK_HISTORY.md`** (not UTF-8, or a read error) is `FAIL` with the
  reason; `TAMPERED` still takes precedence.
- **A lock file whose JSON cannot be converted** (an integer longer than Python's limit for
  converting a string to an integer, 4,300 digits by default, or nesting too deep for the
  parser) and **an attachment that cannot be read or examined**
  (a permission error, for example) are `FAIL` with the reason, never an exception. For the
  attachment, `TAMPERED` from another component still takes precedence. So is **a lock file
  that cannot be examined** (its `stat` fails, for example with a permission error).

This comparison only reads the lock file and `LOCK_HISTORY.md`; it never rewrites
either. The two historical locks (v0.1 and v0.2) match every shared field of their
entries (`tests/test_lock_history_fields.py`).

| Exit code | Status | Meaning |
|---|---|---|
| 0 | `PASS` | Every hash matches and the lock is the latest history entry, which records every shared field exactly. |
| 1 | `FAIL` | No lock, unreadable lock, invalid claim, missing or unreadable attachment, lock not recorded as the latest history entry, or a shared field of that entry that differs or is missing. |
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

### Extensions of the table

Each extension of the table is approved by the maintainer before it is made, is recorded here
with its date, the paths and frozen values it adds, and the full resolved hashes it records
(L10.2 of the acceptance), and keeps every safeguard above. Extensions so far:

1. **The corrections section of v0.2.1 (2026-10-18; Phase I, branch `claude/v0-2-1-reopen`
   only, until its merge).** Approved by the maintainer on 2026-10-18. Adds, to both historical
   entries, the path `test_plan.gauntlet.corrections` with its frozen value: the section at
   exactly its defaults, `enabled: false` (`b_min` 20, `enabled` false, `fap_max` 0.0001,
   `gap_split` 5.0, `h_min` 0.9, `k_clip` 2.5, `m_beta` 1.2, `max_components` 3, `r_min` 20),
   written in the table as a literal, not read from the code. The section is removed from the
   projection only when its resolved value equals that literal as canonical JSON (so `5` and
   `5.0` differ) and it is not written in the claim file; any other value, or a later change of
   a default, leaves it in and the claim is `TAMPERED`. Full resolved hashes from this extension,
   with the code of `676b076`: v0.1
   `05ec2b63b9b94874e393bb46884ab152b74ed3ad235ff46798bcbed1a1b8a48f`, v0.2
   `a68d2bac0663b035e979b17147e9234a7246233abdb5af0a201cdc3df4e64b75` (before it, with main
   `78822a7`: `6f54b834…365dc` and `5fe1a3de…6d502`). Tests: `tests/test_lock_compat.py`
   (the projection still reaches both locked hashes; six non-default values and a changed
   default are refused; the section written in the claim file, even at its defaults, is
   refused). Sabotages: skipping the frozen-value comparison, removing the section whatever its
   value, leaving the path out of the v0.2 entry, and skipping the guard against a field written
   in the claim file each make cases fail. Every later field or default of the section changes
   this frozen value, so it needs a new extension, approved before it is made.
2. **The version key of the corrections section (2026-10-18; branch `claude/v0-2-1-reopen` only,
   until its merge).** The maintainer's decision of 2026-10-18 (14:00) set a version rule for the
   section: `version` 1 is the legacy block, always on the M3 path; version 2 is M4, written
   explicitly in new claims; no default of the section changes. This extension adds `"version": 1`
   to the frozen value of extension 1 (the same path, `test_plan.gauntlet.corrections`, for both
   historical entries); every other frozen value is unchanged. With it, both historical claims still
   reach their locked `claim_sha256` by the projection (the claim component matches; `verify` stays
   `TAMPERED` in the code component only, as before). Full resolved hashes from this extension: v0.1
   `045a980e55e7427902405e8c4cfc6b6786aa2417c84a1f4f432d00c314fe6936`, v0.2
   `27213d9406ed419ae12ea445e0ef2b8ad09507c5399c6400627dd6f70f9a04be`. The cases and sabotages of
   extension 1 cover it (a non-default value, the version 2 among them, is refused).

## When only the code differs (issue #66)

Any code change after a lock makes `verify` `TAMPERED` (exit code 2), and that does not
change: the status, the exit code and the JSON output (`--json`) stay as above.

When the code is the **only** problem (the code is the only tampered component, and there
is no missing attachment, history problem or unreadable code), the text output adds one
line after the messages:

> note: only the code component differs from the lock; the claim (directly or by its
> historical projection), every attachment and the LOCK_HISTORY.md entry match it. This
> names the component that differs; it does not say whether the change is legitimate or
> harmless.

The note names the component; it does not judge the change. In every other case (the
claim or an attachment tampered, or a `FAIL`-level problem next to the code) there is
no note.

**The historical locks.** The v0.1 and v0.2 calibration locks are `TAMPERED` with the
current code, because the code changed after them, and their claim matches by the
historical projection. The complete check of such a lock is `refute verify` at the
lock's own tag, in its own environment: `scripts/verify_locked_tags.py` does it, and
[validation/v0.3/lock-compat-record.md](validation/v0.3/lock-compat-record.md) records
the result (`PASS` at both tags).

## Interoperability

The format is deliberately small (one JSON file, one Markdown log, SHA-256 and a
documented canonical JSON) so it can be mapped to other pre-registration formats
such as PRML later. A compatibility statement is planned for v1.0.
