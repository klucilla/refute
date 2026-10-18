# Issue #33: semantic equivalence of the MAST v1.0 file and the VizieR snapshot (2026-10-17)

**The maintainer's decision (2026-10-17, item 8):** option C of `../issue-33-evaluation.md` (the
MAST high-level science product TESS-EBs v1.0, under CC BY 4.0) **only after** showing semantic
equivalence with the VizieR snapshot that the code uses, never by line order or file bytes; the
identity is `tess_id + signal_id`, as MAST states; check every signal per TIC without losing
legitimate duplicates, the periods, coordinates, units, missing values and precision, and the
records the gauntlet consumes. If a scientific difference is unexplained, option A stays for this
calibration and the difference goes to the maintainer. The historical locks and snapshots are
preserved.

## The two copies (retrieved 2026-10-17, about 21:55 UTC-3)

| Copy | Source | File | Bytes | SHA-256 |
|---|---|---|---|---|
| VizieR | `https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJS/258/16/tess-ebs&-out=TIC,m_TIC,RAJ2000,DEJ2000,Per&-out.max=unlimited` (the URL recorded by v0.2) | `tess_ebs_prsa2022.tsv` | 254392 | `61cb8749ce2ebf87d3fdf495af888b2f803064c67a23c117f742b85598f5a323` (raw; it differs from v0.2's raw hash because VizieR writes the query date in a comment line); **content SHA-256** `a31936ce4dc1bfbb27c4e372b145653ef1d97df250df8d1b0fadaa3f0f1b949c`, **equal to the value recorded by v0.2** (`calibration/v0.2/eb_snapshot/retrieval.json`), so it is the v0.2 snapshot |
| MAST | `https://archive.stsci.edu/hlsps/tess-ebs/hlsp_tess-ebs_tess_lcf-ffi_s0001-s0026_tess_v1.0_cat.csv` (product page `https://archive.stsci.edu/hlsp/tess-ebs`, DOI 10.17909/t9-9gm4-fx30) | `hlsp_tess-ebs_tess_lcf-ffi_s0001-s0026_tess_v1.0_cat.csv` | 1898138 | `97e81f6c01716a431379ab6bd37d1182b611a485107110e0eba830f817ba7a8f` |
| MAST readme | `https://archive.stsci.edu/hlsps/tess-ebs/hlsp_tess-ebs_tess_lcf-ffi_s0001-s0026_tess_v1.0_readme.txt` | | 6214 | `79c7731810ed86f169e295733be480f66649cb40e1c435c76ca9c5e4aaf07377` |

Neither file is committed (they are in the worktree's `.cache/`); the hashes above fix them.

## The comparison

`compare_tess_eb.py` (read-only; SHA-256
`598063b53c8a51e4e0c39f0131d6c83430e7792d304d5e7974e3b3bff83bcd6d`) wrote `compare-output.json`
(SHA-256 `7e103ab595fc8d62b17e5cf52a44afeaaab95af4e2ed192ef89572e8127ad85c`).

| Check | Result |
|---|---|
| Units | VizieR's units line: RAJ2000 `deg`, DEJ2000 `deg`, Per `d`; MAST readme: `ra`, `dec` in decimal degrees (J2000), `period` in days. The same units. |
| Keys (TIC, signal) | 4584 in each; **every key in both**; none only in one copy; no duplicate key in either |
| Signals per TIC | the same set of signals for every TIC; 6 TICs have more than one signal, in both copies (the legitimate duplicates by TIC are kept) |
| Missing periods | 2 keys, the same in both copies (`TIC 233866651 (1)`, `TIC 430000969 (1)`); none missing in only one |
| Periods | max relative difference 5.2e-7, max absolute difference 5.0e-8 d; VizieR gives 7 decimals |
| Coordinates | max separation 0.0043 arcsec; none above 0.1 arcsec |
| Rounding | for every common key and each of ra, dec and period: \|VizieR − MAST\| ≤ half a unit of the last decimal of the less precise copy: **0 differences beyond rounding** |
| The gauntlet's view | `parse_tess_eb` on the VizieR bytes and the same mapping (`TIC <tic> (<m>)` → ra, dec, period as floats) from MAST have **the same 4584 keys**; the four reference rows of the v0.2 claim (`calibration/v0.2/eb_catalog.csv`) agree to a relative period difference ≤ 1.4e-8 and ≤ 0.0043 arcsec |

**Against the scales the gauntlet uses:** `eb_catalog` matches periods within a relative 0.01 and
positions within 21 arcsec (`EbCatalogParams`); the largest differences are 5 orders of magnitude
below the first and almost 4 below the second. No scientific difference was found.

## Conclusion

The MAST v1.0 file and the VizieR snapshot are **semantically equivalent** for what the gauntlet
reads: the same rows by (TIC, signal), the same signals per TIC, the same missing values, and
values equal within the rounding of the less precise copy. Under the maintainer's decision, option
C can be used for the v0.2.1 calibration. What it needs before the protocol, fixed in
`../issue-33-evaluation.md`, "Decision": the file, version, hash, transformation and attribution,
and code that reads the MAST CSV (a parser beside `tess-eb-vizier-tsv`, with its acceptance record
before its tests and code). The v0.2 lock, its snapshot record and its files do not change.
