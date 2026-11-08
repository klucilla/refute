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
- Here: `t10k-fetch.json` (URLs, UTC time, SHA-256 and sizes of the two downloads) and
  `t3b-inventory.json` (counts). The copies stay in the git-ignored `.cache/v052/t10k/<sha256>/`.
- Citation owed if the table is used in any record: the article above.

## The other catalogs counted by `t3b_inventory.py`

`t3b-inventory.json` also counts members of TESS-EB, of the Gaia DR3 snapshot and of the v0.5 TOI table.
Those counts keep the terms of their tables, stated in
[../../../../calibration/v0.5/DATA_LICENSE.md](../../../../calibration/v0.5/DATA_LICENSE.md) and
[../../../../calibration/v0.2/eb_snapshot/DATA_LICENSE.md](../../../../calibration/v0.2/eb_snapshot/DATA_LICENSE.md).
No row of them is in this folder.

## The plasmode records

`plasmode-diag.json` and `plasmode-member.json` are Refute's own development results on synthetic curves,
archived from the v0.5.1 acceptance runs.
