# Calibration runs of the v0.1 self-claim

The self-claim `tess-calibration-v0.1` was run twice. The first run failed for
technical reasons and is **not** a scientific result. The second run is the
result reported in `summary.json` and `summary.md` in this directory; both files
are copied byte for byte from the run directory and have not been edited.

Both runs used the locked claim (claim SHA-256
`5701c54cb088f1d33895f73d98244d0ea214ddb3f861340d8261b817e189a53f`, code SHA-256
`624f5f900334abcdc614a679a3fdc4ce9c9e8a465f2d3e553d71b24c199f4cfa`, locked from
commit `5214f2e29de98803aafff3094733ca424ae3dbde`) and were started from commit
`821b0d791c81d0c3c61d333d93b286b78321dba3` with a clean working tree.
`refute verify` returned PASS before each run.

## Run 1: failed technical run (not a result)

- Run id: `20261007T220242Z-5701c54c`
- Command: `uv run --frozen refute calibrate --out dossiers`
- Time (UTC): 2026-10-07T22:02:40Z to 2026-10-07T22:04:51Z
- Outcome: 8 of 13 targets have `status: ERROR` and were never analyzed. Their
  data download failed: one light-curve file per target was truncated at
  exactly 65536 bytes (the astropy download block size; expected sizes 1.8 to
  2.1 MB). The three fetch attempts reused the corrupt cached file, so all
  failed with "This file may be corrupt due to an interrupted download". After
  the summary was written, the CLI crashed with
  `ValueError: I/O operation on closed file` and exited with code 1.
- Affected targets: TIC 207141131, TIC 138819293, TIC 77031414, TIC 440872576,
  TIC 369327947, TIC 36452991, TIC 285524410, TIC 95129101.
- The other 5 targets (TIC 283621618, TIC 36592530, TIC 374530847,
  TIC 398572544, TIC 404610583) had complete data and were analyzed.
- Its `summary.json` evaluates the claim with the 8 errors counted against it,
  as the locked definition requires for errors. Because the errors are technical
  (download), the maintainer decided that this run is not a scientific result.
  The decision to rerun was made before any verdict of run 1 was inspected.
- The run directory is preserved without changes. It is included, unchanged and
  under the name "failed technical run", with its `summary.json`, in the dossier
  archive `refute-v0.1-calibration.zip` (SHA-256
  `6f67781dbd3790cae767ff215bb0d7ee5cfed0763112304a3b318a3e987c993d`). Until
  release v0.1.0, that archive existed only on the maintainer's machine; an
  earlier version of this file wrongly said it was already published (gate
  finding A1, https://github.com/klucilla/refute/issues/4).
  Fingerprint: the SHA-256 of the sorted `sha256sum` listing of its 260 files is
  `34c227bf639cdf0ca29f6759bb24de7686c089241a944bb757c8efe49a4ba303`, identical
  before and after the rerun.
- Defects tracked in https://github.com/klucilla/refute/issues/1 (parallel
  downloads truncate files and the corrupt cache is reused; the closed-stream
  crash). They will be fixed only after the calibration, with a new lock.

## Rerun approval and procedure

The maintainer approved the rerun on 2026-10-07, in chat, with this procedure,
which uses only existing commands and does not change the locked code:

1. The 8 truncated files (65536 bytes each) were deleted from `.cache/`.
2. Data were downloaded again one target at a time with
   `uv run --frozen refute fetch calibration/self_claim.yaml`
   (2026-10-07T22:09:45Z to 22:11:27Z): 13 of 13 ok, no truncation warning.
3. Before analysis, every cached light curve of the 13 targets was checked:
   file size equal to the size declared by its FITS structure, and SHA-256 equal
   to the fetch manifest. The TIC cache of the 13 targets was checked: valid
   JSON with every expected field. No problem was found.
4. The analysis ran offline (no downloads during the run).

## Run 2: result

- Run id: `20261007T221214Z-5701c54c`
- Command: `uv run --frozen refute calibrate --offline --out dossiers`
- Time (UTC): 2026-10-07T22:12:12Z to 2026-10-07T22:15:02Z, 30 worker processes
- Outcome: exit code 0, 13 of 13 targets with `status: OK`, every dossier
  manifest intact.
- Self-claim result: see `summary.md`.

## Reproduction check

The 5 targets analyzed in both runs were compared with
`refute check-dossier <run 2 dossier> --against <run 1 dossier>`: all 5 have
identical input data hashes, identical verdicts and test statuses, and key
numeric results equal within a relative tolerance of 1e-6.

| Target | Result |
|---|---|
| TIC 283621618 | reproduced |
| TIC 36592530 | reproduced |
| TIC 374530847 | reproduced |
| TIC 398572544 | reproduced |
| TIC 404610583 | reproduced |

## Data note

The TIC record of TIC 285524410 (TOI-2848.01) has disposition `SPLIT`: the ID now
refers to a faint Gaia source (Tmag 18.42) without radius, mass or log g, while
ExoFOP lists TESS magnitude 11.42 for the TOI. Under the locked rules, a missing
TIC radius makes the plausibility test INCONCLUSIVE.


## Reproduction from fresh clones (gate finding A2)

The v0.1 gate review (`docs/gates/v0.1-review.md`, finding A2) noted that the
literal `REPRODUCE.md` flow had never been exercised, and that the 8 targets that
failed in run 1 had no reproduction. The maintainer approved this reproduction on
2026-10-07, recorded before it ran in https://github.com/klucilla/refute/issues/5.

Procedure, for each target, one at a time (never in parallel, because of #1): a
fresh clone in `dossiers/repro-clone/TIC-<id>/refute`, checked out at commit
`821b0d791c81d0c3c61d333d93b286b78321dba3`, then the dossier's `REPRODUCE.md`
literally: `uv sync --frozen`, `uv run refute verify calibration/self_claim.yaml`,
`uv run refute calibrate --claim calibration/self_claim.yaml --target TIC-<id>
--out repro --run-id repro --workers 1` and `uv run refute check-dossier
repro/repro/TIC-<id> --against <dossier of run 2>`. Each clone had its own cache, so
the input light curves were downloaded again from MAST. The input data were also
compared file by file (SHA-256) with the dossiers of run 2.

| Target | Name | Files | verify | check-dossier | Data hashes | Verdict | Time (UTC) |
|---|---|---|---|---|---|---|---|
| TIC 440872576 | TOI-3160 A b | 2 | PASS | reproduced | identical | REFUTED | 23:06:27 - 23:07:04 |
| TIC 285524410 | TOI-2848.01 | 4 | PASS | reproduced | identical | INCONCLUSIVE | 23:07:32 - 23:08:23 |
| TIC 207141131 | HD 18599 b | 6 | PASS | reproduced | identical | SURVIVED | 23:08:24 - 23:10:07 |
| TIC 138819293 | GJ 436 b | 2 | PASS | reproduced | identical | SURVIVED | 23:10:07 - 23:10:42 |
| TIC 77031414 | WASP-173 A b | 6 | PASS | reproduced | identical | SURVIVED | 23:10:42 - 23:12:16 |
| TIC 369327947 | LHS 475 b | 10 | PASS | reproduced | identical | SURVIVED | 23:12:16 - 23:15:19 |
| TIC 36452991 | TOI-2969 b | 4 | PASS | reproduced | identical | SURVIVED | 23:15:20 - 23:16:23 |
| TIC 95129101 | TOI-1704.01 | 6 | PASS | reproduced | identical | SURVIVED | 23:16:23 - 23:17:26 |

All 48 commands (6 per target) exited with code 0. All 40 input files have the same
SHA-256 as in run 2. Every reproduced verdict equals the original one. The CLI crash
of #1 did not occur in these single-target runs.

With the 5 targets compared between run 1 and run 2 (above), all 13 calibration
dossiers have now been reproduced; the 8 above from fresh clones following their
own `REPRODUCE.md`.

The reproduced dossiers, the command logs and the file-by-file hash comparisons
are packed in the archive `refute-v0.1-reproduction.zip` (SHA-256
`1ee24bcf2d2c4843ba799c2cb64222cf7427607594c04bc9c652cbe3d698ad80`). In that copy of
the logs, one line per log printed by `uv sync` had the local Windows user folder in
the path of the Python interpreter; the folder name is replaced by `<user>`. Nothing
else was edited.
