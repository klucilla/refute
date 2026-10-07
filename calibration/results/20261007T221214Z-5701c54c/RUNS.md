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
- The run directory is preserved without changes and is published in the
  release archive as the "failed technical run", with its `summary.json`.
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
