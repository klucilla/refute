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
