# Acceptance: verifying the historical locked claims with the current code

Decided by the maintainer on 2026-10-15: option B (versioned canonicalization) with
every safeguard and negative case proposed in the read-only Codex review, plus option C
(a verification in the historical environment) as an independent check. Option D (CI
runs the published commands at the tags) is deferred. Context: issue #30, the
investigation recorded in issue #46 (comment of 2026-10-15), and criterion W3.5 of
[wp3-acceptance.md](wp3-acceptance.md). This document is committed before the tests
and the code. The pull request is merged only with the maintainer's approval: it
changes lock verification and an acceptance criterion.

## 1. Facts this work starts from

Read-only investigation of 2026-10-15 (scripts and outputs in the pull request
record):

- The claim files `calibration/self_claim.yaml` (v0.1) and
  `calibration/v0.2/self_claim.yaml` (v0.2) are unchanged since their locks.
- The canonicalization `refute-cjson-1` (`canonical_sha256`) is unchanged since the
  first lock.
- The resolved claim hash changed only because optional fields with defaults were
  added to the schema after each lock. No value that existed at lock time changed.
  - v0.2, locked `c9f341d2…`: equal up to the v0.2.0 release (f479823); fields added at
    3217db7 (H7), 78d79f5 (H4) and 9d3f369 (H9a).
  - v0.1, locked `5701c54c…`: fields added at deaa4eb (v0.2), then at the same three
    commits.
- Keeping only the key paths that existed at each lock, the current code reproduces
  both locked hashes exactly.
- The published commands (`git checkout <tag>`, `uv sync --frozen`,
  `uv run refute verify <claim>`) return PASS at `v0.1.0` and at
  `v0.2.0-calibration-lock`.

## 2. What the package must do

### 2.1 Historical projection in `refute verify` (option B)

- **L1 Known locks only.** A projection is defined only for a lock listed in a frozen
  table in `src/`. A lock matches an entry only when all of these fields of the lock
  file are equal to the entry: `lock_version`, `canonicalization`, `claim_id`,
  `claim_kind`, `claim_path_in_repo`, `claim_sha256`, `code.sha256`, `git_commit` and
  `locked_at_utc`. Any other lock, including one that differs in a single field, gets
  no projection: its claim component is checked exactly as before.
- **L2 Exact list of removals, with frozen values.** Each entry lists the exact key
  paths added to the resolved claim after that lock, at the highest new level, each
  with its frozen value. A projection removes those paths and nothing else. It applies
  only if every listed path is present in the current resolved claim with exactly its
  frozen value, compared as canonical JSON (so `1`, `1.0` and `true` differ).
  Comparing with the current default is not allowed: a later change of that default
  must not disappear from the check.
- **L3 New fields written explicitly are refused.** If any listed path is present in
  the claim file itself (the YAML as written, before resolution), no projection
  applies. The schema of the lock's time would have rejected that file.
- **L4 Nothing else is hidden.** A resolved key that is neither in the lock-time form
  nor in the list stays in the projected form, so the projected hash differs from the
  locked one and the claim is `TAMPERED`.
- **L5 The other checks are unchanged.** The projection affects only the claim
  component. Attachments, code and `LOCK_HISTORY.md` are checked as before. A code
  difference keeps the result `TAMPERED`, and `refute calibrate` and
  `refute replicate` still stop unless `verify` is `PASS`.
- **L6 Output.** The result reports the full current claim hash, the projected hash,
  and the name of the table entry used. The message says that the projection shows the
  claim content and the values resolved at lock time are intact. It also says the
  projection does not show that the current code evaluates the claim the same way.
- **L7 Provenance of the table.** For each entry, a fixture stores the canonical form
  computed with the code of the lock commit, with that commit named. Tests check:
  - `canonical_sha256(fixture)` equals the locked `claim_sha256`, so the fixture is
    the locked content (the hash is its proof);
  - the current resolved claim equals the fixture plus exactly the listed paths with
    their frozen values.

  So any later schema change that adds a field or changes a value fails the test
  until the table is extended. Under CLAUDE.md, such an extension changes lock
  verification and needs the maintainer's approval.

### 2.2 Independent check in the historical environment (option C)

- **L8** A saved script under `scripts/` verifies each historical lock at its tag:
  - a detached worktree under `.cache/`;
  - `uv sync --frozen`;
  - `uv run --frozen refute verify <claim> --json`, saving the output.

  It changes nothing in the main checkout. It runs by hand (it needs the packages,
  which may require the network), never in the test suite.
- **L9** One run is recorded in `docs/validation/v0.3/lock-compat-record.md`:
  - the commands;
  - the tag commits;
  - the status and hashes of each verification;
  - the SHA-256 of the saved outputs.

  The worktrees and their environments are then deleted from `.cache/` and listed in
  the report.

### 2.3 W3.5 restored

- **L10** W3.5 of [wp3-acceptance.md](wp3-acceptance.md) returns to the maintainer's
  request, as two separate requirements:
  1. **Equality with the locked hashes:** with the new code, the historical
     projection of each locked claim equals the `claim_sha256` recorded in its lock
     (L7).
  2. **No regression of the full current resolution:** the full resolved hash of each
     claim equals a value recorded in the test, with the commit it comes from.

## 3. Synthetic and fixture cases

All offline, in `tests/`. The two real locked claims are read from the repository
(their files and locks, no network). The negative cases use copies in `tmp_path`.

**Must pass:**
- both real claims: the projection reproduces the locked hash (L7, L10.1);
- both fixtures hash to their locked `claim_sha256`;
- the full current hashes equal the recorded values (L10.2);
- `verify` on each real claim in the current checkout: the claim component passes by
  projection, the result is still `TAMPERED` because the code differs, and the output
  names the projection and both hashes (L5, L6).

**Must not pass (negative cases, from the Codex review):**
- an old field changed (a value that existed at lock time): `TAMPERED`;
- a new field written explicitly in the claim file, even with its frozen value: no
  projection, `TAMPERED`;
- a listed field whose resolved value differs from its frozen value, as when a later
  release changes the default: no projection, `TAMPERED`;
- an unknown field, resolved but not in the list: `TAMPERED`;
- a wrong table entry (one identity field different, or a wrong frozen value): no
  projection, `TAMPERED`;
- divergent code: the claim component passes by projection, and the result stays
  `TAMPERED` with the code component named;
- an unknown lock (no entry): checked exactly as before.

## 4. Metrics and evidence

- Test counts from a JUnit XML file.
- CI green on the four jobs.
- Each criterion L1 to L10 is listed in the pull request with its test or record.
- One Codex review, read-only, recorded in the pull request.

## 5. Regression

- The full test suite passes.
- `docs/lock-format.md` documents the projection and its limit.
- No lock file, lock history, claim file or published dossier is edited.
