# Archive of the v0.2.1 population study: snapshot and manifest (2026-10-14)

The working files of the study were in `.cache/population/` (git-ignored). At the closure
(`../closure-record.md`) the whole folder was fixed as one snapshot, listed file by file in a
manifest, and copied to a **private archive kept by the maintainer**. Publication (for example a
Zenodo record or a GitHub release asset) is a later decision, after a privacy review.

## Snapshot

| Item | Value |
|---|---|
| Snapshot id | `snap-v0.2.1-population-20261014T115407Z` |
| Date and time (UTC) | 2026-10-14T11:54:07Z |
| Scope | the whole folder `.cache/population/` |
| Declared exclusion | the manifest itself, which cannot contain its own hash |
| Files | 48717 |
| Bytes | 28247619426 (28.248 GB) |
| Manifest SHA-256 | `700c739c2f72feb794700903e3ff48aa35f5b7055468b3b9753c0e4622ed3a53` |
| Manifest size | 7456284 bytes |
| Manifest location inside the archive | `closure/archive-manifest-snap-v0.2.1-population-20261014T115407Z.tsv` |
| Written by | `closure/snapshot_manifest.py` (inside the archive) |

- Manifest columns: `sha256`, `size_bytes`, `path` (relative to the archive root, the former
  `.cache/population/`), `set`, `cited` (the SHA-256 appears in a text file of the
  repository), `other_copies` (other paths of the snapshot with the same SHA-256), `in_repo` (an
  identical file is in the repository).
- `cited` only means that the hash value appears in the repository. The SHA-256 of an empty file
  appears in lock files, so the 91 empty files (8 in set A, 83 in set B, such as `journal.lock`)
  count as cited.
- An earlier manifest of the same folder (`closure/archive-manifest.tsv`, SHA-256
  `1d1c4397fb663b285f91f4efa3017bdf36a1bdb11780ed51b4e49a72c0ad7bcf`, 48701 files, written
  2026-10-14T11:18:28Z) is kept unchanged inside the archive and listed in the final manifest.
  The final snapshot has 16 more files: the closure checks written after it and the four-item
  errata of the C3 investigation.
- After the snapshot nothing was written into `.cache/population/`. The reports and
  administrative outputs written afterwards are in `.cache/population-complements/`, with their
  own manifest (path, size, SHA-256), identified as complements of the snapshot.

## Sets

| Set | What it is | Files | Bytes | GB |
|---|---|---|---|---|
| A | named by the maintainer: the work folder of campaign 1 with its result records (`campaign-dev-1/`), the diagnosis and review folder (`diag/`, with `codex/`, the plan revisions 1 and 2, drafts and one-use scripts) and the closure folder (`closure/`) | 42831 | 10191359244 | 10.191 |
| B | other study caches whose files are cited by SHA-256 in the repository (for example the self-test artifacts listed in `selftest-v2*/artifacts-SHA256SUMS`, and cached inputs whose hashes are in committed manifests) | 2669 | 15530556132 | 15.531 |
| C | other study caches, not cited by SHA-256 | 3217 | 2525704050 | 2.526 |
| all | the private archive keeps all three sets, with the folder structure | 48717 | 28247619426 | 28.248 |

| Set and folder | Files | GB |
|---|---|---|
| A `campaign-dev-1/` | 42486 | 2.834 |
| A `diag/` | 304 | 7.279 |
| A `closure/` | 41 | 0.078 |
| B `v2-dev/` | 356 | 6.500 |
| B `v2-selftest-4/` | 690 | 1.693 |
| B `v2-selftest-3/` | 626 | 1.692 |
| B `v2-selftest-2/` | 586 | 1.576 |
| B `v2-selftest-final/` | 352 | 1.564 |
| B `d6-full/` | 26 | 1.141 |
| B `dev-gen/` | 15 | 1.139 |
| B `v2-selftest/` | 18 | 0.227 |
| C `d6-full/` | 1212 | 2.231 |
| C `v2-dev/` | 1992 | 0.193 |
| C `reference/` | 6 | 0.102 |
| C `v2-selftest/`, `dev-gen/`, `scan-control/` | 7 | 0.000 |

Most of the volume is cached light curves (`.rpc`), many of them byte-identical copies of the
same input in several folders. Distinct contents: A 42748 (6.546 GB); A + B 44086 (7.725 GB);
A + B + C 46593 (9.880 GB).

## Verification of a copy

With the manifest that travels inside the copy (independent of the working folder):

```
python docs/validation/v0.2.1/population/closure/verify_archive.py COPY --manifest COPY/closure/archive-manifest-snap-v0.2.1-population-20261014T115407Z.tsv --sets A,B,C --report REPORT.json
```

`COPY` is the folder that holds the copy (the former `.cache/population/`); `REPORT.json` is
written only if it does not exist. The script prints the snapshot id, the manifest path and
SHA-256, the sets, the expected and verified counts and the declared exclusion; it refuses an
unknown set, an empty selection, a missing manifest or a manifest whose SHA-256 is not the one
below; it lists extra files without failing; it never writes under `COPY`. Exit status 0 and
the line "ARCHIVE VERIFIED" mean that every file of the chosen sets is present with its size and
SHA-256. The values it expects are read from this block:

```text
[verify_archive]
snapshot_id: snap-v0.2.1-population-20261014T115407Z
manifest_sha256: 700c739c2f72feb794700903e3ff48aa35f5b7055468b3b9753c0e4622ed3a53
manifest_path_in_archive: closure/archive-manifest-snap-v0.2.1-population-20261014T115407Z.tsv
declared_exclusion: closure/archive-manifest-snap-v0.2.1-population-20261014T115407Z.tsv (the manifest itself)
files_A: 42831
files_B: 2669
files_C: 3217
files_total: 48717
bytes_total: 28247619426
```

On Windows, with the CPU affinity of this project (logical processors 8 to 31), from the root
of the repository, in PowerShell:

```
cmd /v:on /c "start `"`" /affinity FFFFFF00 /wait /b .venv\Scripts\python.exe docs\validation\v0.2.1\population\closure\verify_archive.py `"COPY`" --manifest `"COPY\closure\archive-manifest-snap-v0.2.1-population-20261014T115407Z.tsv`" --sets A,B,C --report REPORT.json & exit !errorlevel!"; "exit: $LASTEXITCODE"
```

- Use this form, not `cmd /c start ... /wait` without `exit !errorlevel!`: that earlier form
  loses the exit status of the script (a refusal with exit 2 is reported as exit 0). With
  `/v:on`, the path of `COPY` must not contain `!`.
- An unreadable destination (for example a disk whose file system is not recognized) ends with
  a Python traceback and exit 1: an input/output error is not handled by the verifiers. The
  copy is still not accepted, but exit 1 then does not necessarily mean a wrong hash or a
  missing file; read the output.

### Checks of the script (2026-10-14, the working folder in place as the archive)

Recorded in `.cache/population-complements/verify-controls.log` (a complement of the snapshot).

| Run | Expected exit | Exit | Result |
|---|---|---|---|
| all sets, final manifest | 0 | 0 | ARCHIVE VERIFIED, 48717 of 48717 files; no extra file; the declared exclusion present |
| one altered SHA-256, no override | 2 | 2 | refused: the manifest is not the expected one |
| one altered SHA-256, override, set A | 1 | 1 | not verified, 42830 of 42831 ("SHA-256 differs") |
| one row naming an absent file, override, set A | 1 | 1 | not verified, 42830 of 42831 ("missing") |
| `--sets Z` | 2 | 2 | refused: unknown set |
| `--sets ""` | 2 | 2 | refused: empty selection of sets |
| a manifest without set-A rows, override, set A | 2 | 2 | refused: empty selection |
| manifest missing | 2 | 2 | refused: manifest not found |
| one set-A row removed, override, set A | 1 | 1 | not verified, 42830 of 42831 (count differs) |

## Complements of the snapshot

The reports and administrative outputs written after the snapshot (the verification controls,
the dry run of the deletion, the inventory of the rest of the working tree, the summary of the
snapshot manifest, the negative-control manifests and a preserved copy of the untracked
`journal.lock` of campaign 1) are not part of the snapshot. They are archived next to it, in
their own folder, with their own manifest.

| Item | Value |
|---|---|
| Nature | complements written after snapshot `snap-v0.2.1-population-20261014T115407Z` |
| Location in the archive | `population-complements/` (the former `.cache/population-complements/`) |
| Manifest | `complements-manifest-snap-v0.2.1-population-20261014T115407Z.tsv`, at the root of `population-complements/` |
| Manifest SHA-256 | `cc63137710f8f4feed6a46ebaa4c6f255801eb50e64bef816ef4c4a24827114c` |
| Files listed | 15 (the manifest itself is the declared exclusion) |
| Columns | `sha256`, `size_bytes`, `path` (relative to `population-complements/`), `kind` (`complement`) |

The complements are verified by `verify_complements_copy.py`, SHA-256
`9ee102f84a04eae12949652f9141553477326b385985471dfb75bbe713f18a1c`, kept in the archive under
`archive-tools/` (the former `.cache/archive-tools/`). **It is not in the repository.** It is
read-only, requires `--manifest`, checks the manifest SHA-256 above and the 15 files (size and
SHA-256), reports extra files without failing, never writes under the copy and prints
"COMPLEMENTS VERIFIED" with exit status 0 only if all 15 files are verified. With the CPU
affinity of this project, from the root of the repository, in PowerShell:

```
cmd /v:on /c "start `"`" /affinity FFFFFF00 /wait /b .venv\Scripts\python.exe ARCHIVE_TOOLS\verify_complements_copy.py `"COMPLEMENTS_COPY`" --manifest `"COMPLEMENTS_COPY\complements-manifest-snap-v0.2.1-population-20261014T115407Z.tsv`" --report REPORT.json & exit !errorlevel!"; "exit: $LASTEXITCODE"
```

`ARCHIVE_TOOLS` is the folder that holds the script (`.cache\archive-tools` in the working tree,
or `archive-tools` in the archive) and `COMPLEMENTS_COPY` the copy of `population-complements/`.
The notes on the exit status and on an unreadable destination above apply here too.

## Deletion of the working copies

The working folder is deleted only after the maintainer has copied the archive, run the
verification above with exit status 0 and reported it. The deletion is by manifest: a file is
deleted only if its size and SHA-256 equal the manifest; a file that differs, or that the
manifest does not name, is kept and listed. Unique evidence is never deleted without a verified
copy.
