# Data license record: v0.5.2 stage 2

This folder holds Refute's own scripts and counts. **It holds no line of any third-party catalog.**
Nothing here is legal advice.

## TESS Ten Thousand Catalog (T10K)

- Source: Kostov et al. 2025, ApJS 279, 50, doi:10.3847/1538-4365/ade2d8. Tables 3 and 4 only.
- Terms: **unconfirmed.** The record
  [../../../plans/sources/v0.5.2-t10k-2026-11-08.md](../../../plans/sources/v0.5.2-t10k-2026-11-08.md)
  gives the URL, the date read (2026-11-08) and the literal excerpts of the data page, which do not
  settle whether the tables carry a CC BY 4.0 grant.
- Use, by the maintainer's decision of 2026-11-08 (#216, item 5): internal only. No line of the catalog
  in git or on the public Drive; only TIC identifiers may enter a record, as with TESS-EB.
- Here: `t10k-fetch.json` (URLs, UTC time, SHA-256 and sizes of the two downloads),
  `t10k-disposition.json` (rows, hashes, paths and sizes) and `t3b-inventory.json` and
  `t3b-inventory-r2.json` (counts). **The copies were deleted from `.cache` on 2026-11-09**, by the
  maintainer's decision of that date (#216, item 4), because the catalog adds no star to T3b. The source
  record is kept; the terms stay unconfirmed: the data page cites CC BY 4.0, but gives the rights to the
  authors. `t3b_inventory.py` cannot run again without a new download by `fetch_t10k.py`, checked by SHA-256.
- Citation owed if the table is used in any record: the article above.

## The ExoFOP TOI table of 2026-11-09

`fetch_toi.py` downloaded the table again, by the maintainer's decision of 2026-11-09 (#216, item 3 (a)):
URL, UTC time, size and SHA-256 in `toi-fetch.json`. The copy stays in the git-ignored
`.cache/v052/toi/<sha256>/`; no row of it is in this folder, only counts. Its terms are those of the earlier
copies of the same table, stated in [../../../../calibration/DATA_LICENSE.md](../../../../calibration/DATA_LICENSE.md).

## The ExoFOP observing notes of 2026-11-09

`fetch_obsnotes.py` downloaded them for T3b's counts (#216, item 3 (b)): URL, UTC time, size and SHA-256 in
`obsnotes-fetch.json`. The copy stays in the git-ignored `.cache/v052/toi/<sha256>/`; **no note, username or
identifier is in this folder**, only the counts of `t3b-alternatives.json`. The notes are contributed by named
users under ExoFOP's data use policy, so operational or published reliance on them is **unresolved**: the record
[../../../plans/sources/v0.5.2-t3b-sources-2026-11-09.md](../../../plans/sources/v0.5.2-t3b-sources-2026-11-09.md)
gives the URL, the date and the literal excerpts, and the question goes to the maintainer at the protocol stop.

## The other catalogs counted by `t3b_inventory.py`

`t3b-inventory.json` also counts members of TESS-EB, of the Gaia DR3 snapshot and of the v0.5 TOI table.
Those counts keep the terms of their tables, stated in
[../../../../calibration/v0.5/DATA_LICENSE.md](../../../../calibration/v0.5/DATA_LICENSE.md) and
[../../../../calibration/v0.2/eb_snapshot/DATA_LICENSE.md](../../../../calibration/v0.2/eb_snapshot/DATA_LICENSE.md).
No row of them is in this folder.

## The plasmode records

`plasmode-diag.json` and `plasmode-member.json` are Refute's own development results on synthetic curves,
archived from the v0.5.1 acceptance runs.
