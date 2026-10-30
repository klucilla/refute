# v0.4 freeze attempts of 2026-10-29 and the observed unavailability of VizieR

A record of the attempts to freeze the inputs of the v0.4 pilot (calibration/v0.4/PROTOCOL.md,
section 4.0), written before any input was committed. No attempt completed. **No cause of the
VizieR failures is established here**: what was observed is that two VizieR addresses did not
answer from this machine at the times below, while other hosts did.

## Attempts

| # | Started (UTC) | What happened | Files left |
|---|---|---|---|
| 1 | about 21:16 | the wrapper `calibration/v0.4/select.py` shadowed the standard library's `select` module; the import failed before any download | none |
| 2 | about 21:18 | the target lists page was downloaded; the link pattern did not match its relative links (`2m/all_targets_S111_v1.csv`); stopped | the page, overwritten by attempt 3 |
| 3 | about 21:19 | the page, the lists of sectors 1 to 107, the frame, TOI, CTOI and `pscomppars` downloaded; then a connection timeout (URLError, WinError 10060) with no retry | overwritten by attempt 4; their hashes were never recorded |
| 4 | 21:21:03 | the same files again (written 21:21:03 to 21:24:34), then TESS-EB from VizieR failed on 5 attempts 120 s apart (URLError, WinError 10060); the last error was written at 21:34:20 | `.cache/v04/inputs-attempts/attempt-04/`, with `attempt.jsonl` reconstructed from the files' write times and SHA-256 |

S_max found by attempt 4: **107** (the highest sector on the page is 111; MAST listed no SPOC
120-s light curves for 108 to 111 at that time).

Attempts 1 to 3 overwrote each other's files before any hash was recorded, so their bytes cannot
be told apart. From now on each attempt has its own folder (`attempt-NN`), never written over,
with its events appended to `attempt.jsonl` as they happen; only the attempt named in
`inputs.json` is read (`steps.cache_dir`). No file of one attempt is ever mixed with another's.

## Checks of VizieR (no download)

| UTC | URL (query of one row) | Result |
|---|---|---|
| 21:35 | `https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJS/258/16/tess-ebs&-out=TIC&-out.max=1` | no answer within 21 s (curl code 000) |
| 21:35 | `https://vizier.cfa.harvard.edu/viz-bin/asu-tsv?...` (mirror, same query) | no answer within 40 s (curl code 000) |
| 21:43 | the first URL | no answer (000) |
| 23:16 | the first URL | no answer (000); at the same time `https://api.github.com` and `https://exofop.ipac.caltech.edu/tess/` answered 200 |

A background loop that would have repeated the freeze when VizieR answered (checking every 10
minutes) was stopped at about 23:25 by the maintainer's decision: the approved retries were used
up, and waiting must not become new attempts without end.

## For the maintainer's decision

The TESS-EB exclusion is not dropped because of the unavailability. Two sources of the same
catalog edition exist, and choosing one is the maintainer's:

- **A: the VizieR table of 2026-10-18**, already on this machine
  (`.cache/wt-v021/.cache/v021/tess-eb/vizier/tess_ebs_prsa2022.tsv`, 254 392 bytes, raw SHA-256
  `61cb8749ce2ebf87d3fdf495af888b2f803064c67a23c117f742b85598f5a323`, header `request_date=
  2026-10-18T00:56:26`, VizieR 7.6.1). Its content (non-comment lines, LF, final LF) has the
  SHA-256 `a31936ce4dc1bfbb27c4e372b145653ef1d97df250df8d1b0fadaa3f0f1b949c`, the content hash
  recorded for the v0.2 snapshot of the same query on 2026-10-09
  (`calibration/v0.2/eb_snapshot/retrieval.json`), with 4584 rows: the same table, the same
  columns (`TIC, m_TIC, RAJ2000, DEJ2000, Per`).
- **B: the MAST HLSP "TESS-EBs" v1.0** (`https://archive.stsci.edu/hlsp/tess-ebs`, read on
  2026-10-29; DOI 10.17909/t9-9gm4-fx30; released 2022-06-29; Prša et al. 2022, sectors 1 to
  26), a CSV with `tess_id`, `signal_id`, `ra`, `dec` (decimal degrees, J2000), `period` and
  other columns (its README, read on 2026-10-29). Same edition as the VizieR table, but other
  columns and possibly other row counts (the page says "about 4580"); equivalence would have to
  be shown (same TIC set and periods as A) before use.

Either needs its own record in `inputs.json` (URL or path, retrieval time, size, SHA-256) and the
reader in `selection.tess_eb_tics` / `pilot.catalog_indexes` for its format.

## The maintainer's decision (2026-10-29): option A

The TESS-EB table is the VizieR copy of 2026-10-18, as a **static edition**
(`pilot.TESS_EB_STATIC`): obtained on 2026-10-18 (the `request_date` line of its header,
`2026-10-18T00:56:26`, VizieR 7.6.1), raw SHA-256 `61cb8749…a323`, content SHA-256
`a31936ce…949c`, equal to the content hash of the v0.2 snapshot
(`calibration/v0.2/eb_snapshot/retrieval.json`, retrieved 2026-10-09T02:44:20Z). The freeze
reads it from that path and checks both hashes before any download; a missing or different
file stops the attempt with a `failure` event. Its record in `inputs.json` carries the
`static_edition` fields (path, obtained, content hash and rule, the v0.2 record it equals,
`redistributed: false`, #33). It is used privately, for the exclusion and the deduplication,
and is never redistributed: it is not copied into `calibration/v0.4/inputs/` and goes to the
Drive archive only, like the v0.2 raw file.

The Gaia DR3 EB input never depended on VizieR: the freeze takes it from the asset of release
v0.2.0 (the complete table queried from the ESA archive on 2026-10-08 and 2026-10-09,
`calibration/v0.2/eb_snapshot/`); attempt 4 stopped before that step. A change of its source is
the maintainer's decision.

## The maintainer's decision (2026-10-30): the Gaia DR3 EB asset of v0.2.0

The Gaia DR3 EB input stays the release asset of v0.2.0, as the freeze already planned
(`pilot.GAIA_EB_URL`). A query of the ESA archive restricted to the frame stars had been proposed
on 2026-10-29 on the wrong premise that the Gaia input depended on VizieR; it is not adopted, and
its code is not committed. The freeze checks the asset against its SHA-256
(`5183528b8984d16b305b1fb3ce62b96cf7160961f9a59b0cbb85497e5454c3df`) and its shape (one header
`source_id,ra,dec,frequency`, LF endings, no empty line, 2184477 data rows, the record of
`calibration/v0.2/eb_snapshot/retrieval.json`) before use; a refused asset is kept under
`rejected/` in its attempt folder.

## Attempt 5 (2026-10-30)

| # | Started (UTC) | What happened | Files left |
|---|---|---|---|
| 5 | 10:49:57 | the target lists page answered HTTP 502 on all 5 attempts, 120 s apart (10:50:00 to 10:58:13); stopped before any file | `.cache/v04/inputs-attempts/attempt-05/attempt.jsonl` only |

Checked right after, headers only (10:58 UTC): `https://tess.mit.edu/` answered 200, while
`https://tess.mit.edu/public/target_lists/`, the page and the lists of sectors 1 and 107
answered 502; ExoFOP and the Gaia asset answered 200. No cause is established here. A bounded
wait followed: a header check every 10 minutes for at most 60 minutes, and exactly one new
attempt if the page answered 200. The page answered 502 at each of the 6 checks (10:59:11 to
11:49:29 UTC), so no new attempt was made; the next one waits for the maintainer.

## Attempt 6 (2026-10-30): assembled from attempt 4

By the maintainer's decision of 2026-10-30, attempt 6 was assembled from the files of attempt
4 instead of waiting for tess.mit.edu (`pilot.assemble`, commit `fa69747`; approval recorded
before it ran in https://github.com/klucilla/refute/issues/177#issuecomment-6523790533; Codex,
read only: WEAKENED twice on the design and the code, then SURVIVED). It ran from 13:19:04 to
about 13:20 UTC and completed:
- every file of attempt 4 matched its log (whose SHA-256 is `15aacb0c…f7fc`);
- S_max came out as 107;
- the frame derived again had 175739 stars and the same SHA-256 as attempt 4's;
- it wrote 114 files, 246968498 bytes;
- 164010 stars were kept by the exclusion preview.

**A defect found after it ran.** Its standard error holds astroquery's warning "t_exptime is
continuous, and filters based on min and max values. Not enough values provided, skipping...".
`pilot.spoc_sector_count` passed `t_exptime=120`, which astroquery skips (one value of a
continuous column), so the counts behind S_max were of SPOC timeseries of every cadence, not of
120-s light curves. Attempt 4 used the same code.

The counts were measured again at about 13:25 UTC with the range `[119.5, 120.5]`, counts only,
no download:

| Sector | 120 s | 20 s |
|---|---|---|
| 111, 110, 109, 108 | 0 | 0 |
| 107 | 13000 | 2160 |

The 15160 that attempt 6 recorded for sector 107, under the label `spoc_120s_light_curves`, is
13000 + 2160. S_max is 107 with the corrected filter too, but attempt 6's record mislabels its
counts.

The fix: `SPOC_120S_EXPTIME = [119.5, 120.5]`, and an `InputWarning` (a skipped filter) now stops
the count instead of widening it. Codex (read only) checked the fix: SURVIVED. It recommends a
new attempt with the fixed code, attempt 6 kept as superseded by this defect. Moving attempt 6's
publication out of `calibration/v0.4/` is the maintainer's decision.
