# Search for TESS-EB values (2026-10-11)

Read-only search, run twice on 2026-10-11 from branch
`claude/v0-2-1-gauntlet-fixes-13f5e7` with the same script (`tess_eb_search.py`) and
the same inputs. A third and a fourth run on the same day (below) used the same script
and tokens on other archives. The original of this record is kept outside the repository; a copy
is published in `calibration/v0.2/audit/tess-eb-search/` (see "Changes in the
published copy").

| Run | Started (UTC) | Duration | Output | Refs |
|---|---|---|---|---|
| First | 2026-10-11T01:25:13Z | 1.8 s | `tess_eb_search.txt` | listed by name in the output |
| Second | 2026-10-11T13:05:54Z | about 2 s (finished 13:05:56Z) | `tess_eb_search_2026-10-11T1305Z.txt` | `refs_2026-10-11T1305Z.txt` (name and commit of every ref) |
| Third | 2026-10-11T13:13:02Z | about 2 s (finished 13:13:04Z) | `tess_eb_search_2026-10-11T1313Z.txt` | `refs_2026-10-11T1313Z.txt` (identical to the second run's) |
| Fourth | 2026-10-11T14:02:16Z | about 6 s (finished 14:02:22Z) | `tess_eb_search_2026-10-11T1402Z.txt` | `refs_2026-10-11T1402Z.txt` (identical to the third run's) |

All four runs were preceded by `git fetch -q origin`.

## Inputs (both runs)

- **TESS-EB snapshot:** `C:/Projetos/refute/.cache/eb_snapshot_v02/tess_ebs_prsa2022.tsv`,
  content SHA-256 `a31936ce4dc1bfbb27c4e372b145653ef1d97df250df8d1b0fadaa3f0f1b949c`
  (checked: OK in both runs), 4584 rows, columns TIC, m_TIC, RAJ2000, DEJ2000, Per.
- **v0.1 release assets:** the local copies of `refute-v0.1-calibration.zip` (586
  members) and `refute-v0.1-reproduction.zip` (218 members), each SHA-256 checked
  against the v0.1.0 release notes (OK in both runs).

## Scope of each run (versioned repository)

Every blob reachable from any ref (`git rev-list --objects --all`).

- **First run:** 379 blobs. Refs: `main` (then `3dec26f`), `origin/main`, this branch
  (then `3f1c36c`) and its `origin/` copy, `claude/v0-3-planning-draft-abff23`, tag
  `v0.1.0`, `origin` (HEAD) and one `codex/turn-diffs/checkpoints/...` ref.
- **Second run:** 402 blobs. Refs (`refs_2026-10-11T1305Z.txt`): `main` and
  `origin/main` at `6fb86a1`, so the `main` commits `358f7a7`, `b7fb2e3`, `54ed0dc`,
  `962f162` and `6fb86a1` are now covered; this branch at `552554c`, so its local
  commits `f0fb1b1`, `2fbc142`, `38cadf9` and `552554c` are covered (its `origin/` copy
  at `3f1c36c`); `claude/v0-3-planning-draft-abff23` at `a2c9161`; tag `v0.1.0` at
  `6bb5e78`; the `codex/turn-diffs/checkpoints/...` ref at `09fbf43`.

## Method (both runs)

- **Search values:** every Per, RAJ2000 and DEJ2000 of the snapshot, as written in the
  file and as Python's `repr` of its float: 18724 tokens. Values with fewer than 6
  significant digits would have been skipped as unspecific; none was.
- **Match:** every decimal number in every blob or zip member is compared, as a
  string, with the tokens. A hit is **paired** when the decimal digits of the row's
  TIC also appear somewhere in the same file.
- **Not found by this method:** values rounded or written with other digits, values
  inside compressed or binary formats other than the zips listed, and TIC IDs alone
  (they are used only for pairing).

## Result

**The two runs give the same hits** (14 in the repository, 0 in the v0.1 assets); the
blobs added between them contain none.

| Where | Hits |
|---|---|
| The four review files `calibration/v0.2/results/20261009T155044Z-c9f341d2/reviews/TIC-{158561566,316916655,317507345,350445771}/opus-1.md` | the known period of that target (4) |
| `docs/release-v0.2.0-drafts/DATA_CREDITS_v0.2_draft.md` (this branch) | the four known periods (4), on purpose: it is the credits table |
| `calibration/pool_snapshot/exofop_toi.csv` and `calibration/v0.2/pool_snapshot/exofop_toi.csv` | 1.2168732 (paired with TIC 71612483), 0.22867 and 0.803801 (unpaired): numeric coincidences, see below |
| v0.1 assets | none |

The four known records: Kepler-14 b TIC 158561566, 6.7899645 d; TOI-441.01
TIC 316916655, 2.8747759 d; TOI-1615.01 TIC 317507345, 3.9400619 d; TOI-258.01
TIC 350445771, 3.1904288 d.

**The ExoFOP hits are not TESS-EB data** (checked after the first run, at
01:25:29-01:25:38 UTC): 1.2168732 is in line 1441 of `exofop_toi.csv`, TOI 1410.01
(TIC 199444169), column "Period (days)". TIC 71612483, whose TESS-EB Per is also
1.2168732, is in line 1902 of the same file as TOI 1834.01 with ExoFOP period
1.2164402; that is why the hit counted as paired. 0.22867 and 0.803801 equal TESS-EB
periods of TIC 24450633 and TIC 399729481, which do not appear in those files. The
two `exofop_toi.csv` blobs are the same in both runs (`0370a4cf`, `0a992310`).

**Conclusion:** within the scope and method above, no TESS-EB value other than the
four known records appears in the versioned repository (as of the second run) or in
the v0.1 assets.

## Third run (2026-10-11T13:13:02Z): the v0.2 calibration archive and the reproduction record

**Why.** The `DATA_CREDITS.md` of the v0.2 calibration archive states that no TESS-EB
row other than the four records is in that archive, and no earlier run had read the
archive's members.

**Inputs.** The same script, snapshot (content SHA-256 checked: OK) and tokens
(18724), preceded by `git fetch -q origin`. The script reads archives only as zip
files, and it labels their section of the output "v0.1 ASSETS" (a fixed label in the
script); in this run that section covers:

- **(a)** `refute-v0.2-calibration.zip`, the staging build in
  `.cache/release-v0.2/build3/` of the main checkout, SHA-256
  `43032da921fba2e3987eb8143aae705cfb3dc6fc0e447ca36f66c4bbf0093ac7` (checked by the
  script before scanning: OK), 596 members.
- **(b)** the 7 files of `.cache/repro/record/` as they were at the time of the run,
  packed unchanged by `zip_record.py` into a scratch zip `repro-record-files.zip`
  (members named by file name, stored, SHA-256
  `d1b878dd734e70233b3109f884c58bcb9aa79b483e287d8228be67a2568612ef`), so that the
  script could read them. Member names, sizes and SHA-256:
  `record_zip_members_2026-10-11T1313Z.txt`. The `REPRODUCTION.md` scanned is the
  version before its later edit of the same day.

The script also scanned the repository again (it always does): 402 blobs, the refs of
the second run, and the same 14 hits as the second run.

**Lines.** The script reports hits per file. The line of each hit was found by
`locate_hits.py`, which builds the tokens and the number pattern with the same code as
the script and reads the same two zips; its totals (14 and 4) equal the script's
count for the archives (18). Output: `hits_located_2026-10-11T1313Z.tsv`.

### Result (a): `refute-v0.2-calibration.zip`, 14 hits

Member paths below are under
`refute-v0.2-calibration/20261009T155044Z-c9f341d2/` unless they start with
`refute-v0.2-calibration/`.

| Member | Line | Value | TESS-EB row (TIC, column) |
|---|---|---|---|
| `TIC-158561566/review/opus-1.md` | 8 | 6.7899645 | 158561566, Per |
| `TIC-158561566/verdict.json` | 2885 | 6.7899645 | 158561566, Per |
| `TIC-316916655/review/opus-1.md` | 11 | 2.8747759 | 316916655, Per |
| `TIC-316916655/verdict.json` | 827 | 2.8747759 | 316916655, Per |
| `TIC-317507345/review/opus-1.md` | 12 | 3.9400619 | 317507345, Per |
| `TIC-317507345/verdict.json` | 2386 | 3.9400619 | 317507345, Per |
| `TIC-350445771/review/opus-1.md` | 35 | 3.1904288 | 350445771, Per |
| `TIC-350445771/verdict.json` | 8502 | 3.1904288 | 350445771, Per |
| `refute-v0.2-calibration/DATA_CREDITS.md` | 16 | 6.7899645 | 158561566, Per |
| `refute-v0.2-calibration/DATA_CREDITS.md` | 17 | 2.8747759 | 316916655, Per |
| `refute-v0.2-calibration/DATA_CREDITS.md` | 18 | 3.9400619 | 317507345, Per |
| `refute-v0.2-calibration/DATA_CREDITS.md` | 19 | 3.1904288 | 350445771, Per |
| `TIC-158561566/data/manifest.json` | 770 | 47.33305 | 158561566, DEJ2000 |
| `TIC-158561566/data/manifest.json` | 776 | 287.708814 | 158561566, RAJ2000 |

- **Expected and found:** the four known periods in `verdict.json` and
  `review/opus-1.md` of the four dossiers, and in the table of `DATA_CREDITS.md`.
- **Expected and not found:** `report.md` of the four dossiers. Their line 40 gives
  the period rounded to six significant digits (for example 6.78996 d), which this
  method does not match (see "Not found by this method").
- **Not expected:** the two hits in `TIC-158561566/data/manifest.json`. The values
  are in the member's `star` block (lines 769-785): `dec_deg` 47.33305 (line 770) and
  `ra_deg` 287.708814 (line 776). The source that the same block declares is the TESS
  Input Catalog via MAST ("TESS Input Catalog via MAST (astroquery.mast.Catalogs,
  catalog='TIC')", `tic_version` 20190415, retrieved 2026-10-09T15:35:32Z). The values
  coincide with the position that TESS-EB gives for the same star (TIC 158561566:
  RAJ2000 `287.7088140000`, DEJ2000 `+47.3330500000`). No conclusion is drawn beyond
  this.

### Result (b): the reproduction record, 4 hits

| Member | Line | Value | TESS-EB row (TIC, column) |
|---|---|---|---|
| `session_transcript_extract.txt` | 158 | 6.7899645 | 158561566, Per |
| `session_transcript_extract.txt` | 159 | 2.8747759 | 316916655, Per |
| `session_transcript_extract.txt` | 160 | 3.9400619 | 317507345, Per |
| `session_transcript_extract.txt` | 161 | 3.1904288 | 350445771, Per |

No hit was expected. Where the numbers come from: lines 158-161 are output of the tool
call at 2026-10-11T00:38:14Z (lines 137-164 of that extract), which listed the
`eb_catalog` matches of catalog TESS-EB in the `verdict.json` files of the local
v0.2 calibration dossiers (`20261009T155044Z-c9f341d2`). That call is not part of the
reproduction; it fell in the extract's time window. No other file of the record has a
hit.

## Fourth run (2026-10-11T14:02:16Z): the two final v0.2 release archives, the Gaia asset and this folder

**Why.** The third run scanned a staging build of the calibration archive and the
original reproduction record. The `DATA_CREDITS.md` of the calibration archive states
the scope of the check (all refs, the v0.1 assets, the members of that archive and the
other v0.2.0 release assets), so the final archives had to be scanned.

**Inputs.** The same script, snapshot (content SHA-256 checked: OK) and tokens (18724),
preceded by `git fetch -q origin`; run by the release session (Phase A) from the main
checkout, on logical processors 8-31. The refs (`refs_2026-10-11T1402Z.txt`) are the
same as in the third run. As before, the script labels the archives' section of its
output "v0.1 ASSETS" (a fixed label); in this run that section covers:

- **(a)** `refute-v0.2-calibration.zip`, the final archive, SHA-256
  `05b23627ea9dd567e0ae56ccc29f625ded979a7081a43b72968391f211792039` (checked by the
  script: OK), 596 members. It differs from the third run's staging build
  (`43032da9...`) only in `DATA_CREDITS.md`.
- **(b)** `refute-v0.2-reproduction.zip`, the final archive, SHA-256
  `549830c6d918402fe68ab07c79bb390900e8d327c46759b9cdd9d04480291268` (OK), 61 members.
- **(c)** the Gaia DR3 snapshot `gaia_dr3_vari_eclipsing_binary.csv`, to be published
  as a release asset (SHA-256
  `5183528b8984d16b305b1fb3ce62b96cf7160961f9a59b0cbb85497e5454c3df`, checked before
  packing), packed unchanged by `zip_record.py` into a scratch zip `gaia-asset.zip`
  (SHA-256 `a45be6f22565ce29b9e2dda01192d0254962c2676dd795ff4ae82ee2572593a9`), 1 member.
- **(d)** the 12 files of the published copy of this folder as they were at the time
  of the run (with the changes listed in "Changes in the published copy", before this
  section was added), packed unchanged by `zip_record.py` into a scratch zip
  `audit-staging-files.zip` (SHA-256
  `1abed91c5a2a3ab2e12906e1f874366ac9b7f6355a90f4a4a8066f4cbb59e29d`), 12 members.

The repository was scanned again: 402 blobs.

**Lines.** `locate_hits.py` over the four zips: `hits_located_2026-10-11T1402Z.tsv`.
Its totals (14, 0, 0 and 84) equal the script's count for the archives (98).

### Result

| Scope | Hits | Detail |
|---|---|---|
| Repository (all refs) | 14 | the same 14 as the second and third runs |
| (a) calibration archive | 14 | the same members, lines and values as the third run: the four known periods in `verdict.json` and `review/opus-1.md` of the four dossiers and in the table of `DATA_CREDITS.md` (lines 16-19), and the position of TIC 158561566 in that dossier's `data/manifest.json` (lines 770 and 776) |
| (b) reproduction archive | 0 | |
| (c) Gaia DR3 asset | 0 | |
| (d) this folder (published copy) | 84 | the four known periods (48); the position of TIC 158561566 (8, and 1 in the form `287.7088140000` in this file); 1.2168732 (15), 0.22867 (6) and 0.803801 (6) |

Hits in (d), by file: `SEARCH.md` 33, `hits_located_2026-10-11T1313Z.tsv` 18,
`session_transcript_extract.txt` 15, `tess_eb_search.py` 4, `tess_eb_search.txt` 4,
`tess_eb_search_2026-10-11T1305Z.txt` 4, `tess_eb_search_2026-10-11T1313Z.txt` 6. All
are values already described in this file. The two coordinates of TIC 71612483 that
the ExoFOP check printed (line 129 of the transcript extract) are not in the published
copy (see "Changes in the published copy").

## Not covered

~~(The list below was written after the second run; it is replaced by the list after
it.)~~

~~- Any commit made after 2026-10-11T13:05:54Z, on any branch.~~
~~- Commits that exist only in other clones or worktrees and were never fetched into
  this repository (the search reads the refs of this repository after
  `git fetch origin`; other remotes are not configured).~~
~~- Unreachable objects (for example from rewritten history) and the reflog: only blobs
  reachable from a ref are scanned.~~
~~- Files that are not versioned: git-ignored data such as `.cache/` and the local
  dossiers (the v0.2 calibration dossiers hold the four records by design).~~
~~- The v0.2 release assets: none exists yet.~~ *(Wrong after the third run: the
  calibration archive exists in staging and was scanned.)*
~~- Values in other forms (see "Not found by this method").~~

~~(The list below was written after the third run; it is replaced by the list after
it.)~~

- ~~Any commit made after 2026-10-11T13:13:02Z, on any branch.~~
- ~~Commits that exist only in other clones or worktrees and were never fetched into
  this repository (the search reads the refs of this repository after
  `git fetch origin`; other remotes are not configured).~~
- ~~Unreachable objects (for example from rewritten history) and the reflog: only blobs
  reachable from a ref are scanned.~~
- ~~Files that are not versioned, such as the rest of `.cache/` and the local dossiers
  (the v0.2 calibration dossiers hold the four records by design), except the two
  archives of the third run.~~
- ~~**The v0.2 calibration archive as published.** The third run scanned the staging
  build (`build3`, SHA-256 `43032da9...`). The archive will be regenerated and is
  expected to differ only in `DATA_CREDITS.md`; the release session (Phase A) checks
  that member by member. The regenerated archive itself is not scanned here.~~
- ~~**The v0.2 reproduction archive:** it does not exist yet. The third run scanned
  the original files of `.cache/repro/record/`; its 4 hits (result (b)) are in lines
  158-161 of `session_transcript_extract.txt`, inside lines 57-164, which are not in
  the published copy of that file (see `REPRODUCTION.md`, "Changes in the published
  archive"). The search over the two final archives (calibration and reproduction)
  will be a fourth run, made by the release session (Phase A).~~
- ~~**The audit folder published in `main`** (`calibration/v0.2/audit/tess-eb-search/`)
  will contain the four known periods in the outputs of the runs (the hit lists) and
  in this file; future searches must find them there.~~
- ~~Values in other forms (see "Not found by this method").~~

**After the fourth run:**

- Any commit made after 2026-10-11T14:02:16Z, on any branch, including the commit that
  publishes this folder in `main`.
- Commits that exist only in other clones or worktrees and were never fetched into
  this repository (the search reads the refs of this repository after
  `git fetch origin`; other remotes are not configured).
- Unreachable objects (for example from rewritten history) and the reflog: only blobs
  reachable from a ref are scanned.
- Files that are not versioned, such as the rest of `.cache/` and the local dossiers
  (the v0.2 calibration dossiers hold the four records by design), except the archives
  scanned by the third and fourth runs.
- **The audit folder published in `main`** (`calibration/v0.2/audit/tess-eb-search/`)
  contains the four known periods in the outputs of the runs (the hit lists) and in
  this file; future searches must find them there. This section and the files of the
  fourth run were added after the fourth run and were not scanned.
- Values in other forms (see "Not found by this method").

## Changes in the published copy

In `session_transcript_extract.txt`, the Windows user name in the paths
`C:\Users\<name>\` is replaced by `<user>`: 13 occurrences, on lines 6, 9, 12, 15,
19, 28 (two), 31, 79, 81, 90, 93 and 96. The only other change is the one in the next
paragraph. The count was made on the original with the pattern
`(C:[\\/]+Users[\\/]+)<name>(?=[\\/])`, which matches single and doubled separators;
the name does not occur anywhere else in the file. The GitHub owner name in
repository URLs is not changed (it does not occur in this file).

In line 129, the right ascension and declination of TIC 71612483 from the TESS-EB
snapshot, printed by the ExoFOP check, are replaced by `<withheld>`; its period,
1.2168732, is kept. They are withheld because, with the period, they would form a
complete TESS-EB row of a star other than the four records (see
`calibration/v0.2/eb_snapshot/DATA_LICENSE.md` in the repository).

The original files of this folder are not changed.

Line endings: the logs and outputs of this record keep the line endings they were
written with; some lines end in CR LF (Windows). Nothing was normalized, and every
SHA-256 cited for them matches these bytes.

## Files

| File | What it is |
|---|---|
| `SEARCH.md` | This file |
| `tess_eb_search.py` | The script, as run in all three runs (copied unedited) |
| `tess_eb_search.txt` | Output of the first run (copied unedited) |
| `tess_eb_search_2026-10-11T1305Z.txt` | Output of the second run, with its start and end times and exit code |
| `refs_2026-10-11T1305Z.txt` | Every ref and its commit at the second run |
| `tess_eb_search_2026-10-11T1313Z.txt` | Output of the third run, with its start and end times and exit code |
| `refs_2026-10-11T1313Z.txt` | Every ref and its commit at the third run |
| `tess_eb_search_2026-10-11T1402Z.txt` | Output of the fourth run, with its start and end times and exit code |
| `refs_2026-10-11T1402Z.txt` | Every ref and its commit at the fourth run |
| `zip_record.py` | Packs the files of a folder unchanged into a zip (used for input (b) of the third run) |
| `record_zip_members_2026-10-11T1313Z.txt` | Names, sizes and SHA-256 of the 7 record files packed for the third run, and the zip's SHA-256 |
| `locate_hits.py` | Gives the line of every hit in the archives of the third run (same tokens and number pattern as the script) |
| `hits_located_2026-10-11T1313Z.tsv` | Its output for the third run: archive, member, line, value, TIC, column, paired |
| `hits_located_2026-10-11T1402Z.tsv` | Its output for the fourth run, same columns |
| `session_transcript_extract.txt` | Tool calls and outputs of the session transcript from 01:14:20 to 01:25:40 UTC: the first version of the script (lines 5-10) and its run, stopped after 600 s (11-29: the call, a read of its empty output, the stop), the failed patch (30-88), the rewritten script and the first run (89-122), and the ExoFOP check (123-147). Every call in it belongs to the search. Unedited here; for the published copy see "Changes in the published copy" |

Before the first run, a first version of the script (one git process per blob) was
started at 01:14:27 UTC, did not finish within 600 s and was stopped without output;
an attempt to patch it failed with a syntax error before running. The script was
rewritten (one `git cat-file --batch` process) and that version produced both outputs.
These steps are in the transcript extract.
The third run used the same rewritten script.
