# The real controls' availability, checked early: the declaration (gate 3b)

Plan B, section 5 ([../plan-b/README.md](../plan-b/README.md)), gate 3b. This declaration and its
script, [scripts/real_controls_check.py](scripts/real_controls_check.py), are committed and pushed
**before any of the check's queries**. The maintainer authorized the check on 2026-10-27 ("item 4"
of the plan for that day), after the dependency update of gate 3a. Its result is recorded in a
separate commit, in `result.md` and `result.json` next to this file.

## What it shows, and what it never does

It shows **availability, not approval**: how many confirmed planets and known false positives,
after the exclusions, have SPOC two-minute products whose sectors pass the domain's conditions that
metadata can decide. It uses catalogues and archive metadata only: **no light curve or target pixel
file is downloaded or analysed**, no output of the engine is read, and no target is chosen or
excluded by an expected outcome of the engine. Nothing found here becomes a calibration target by
itself: gate 13's own selection, on its own declaration and seeds, draws from what is available
then.

## The minimum, fixed before the queries

At least **20 confirmed planets and 20 known false positives** screened inside the domain by
metadata (a draw of ten per class and a reserve of equal size, plan B section 5), each counted in
the pools below after the exclusions. If either class has fewer than 20, **X2f stays blocked and
the decision goes back to the maintainer; the domain is never widened** for the targets found, and
no filter below is relaxed to reach the minimum.

## The exclusions (the explicit inventory)

Every TIC, read by the script from these files at the commit of the run, is excluded from both
pools:

| Source | What it holds | TICs |
| --- | --- | --- |
| `calibration/targets.yaml` | v0.1's calibration claims (10 planets, 3 false positives) and its development target, TIC 207339000 | 14 |
| `calibration/v0.2/targets.yaml` | v0.2's calibration claims (10 planets, 10 false positives), its development target, TIC 240681314, and its `excluded_known_targets` (v0.1's 14) | 35 |
| `docs/validation/v0.2.1/reopen/audit-known-targets.json` | the audit of known targets: every target of the two calibrations and their development, with the repository's mentions of each | 35 |

Their union is 35 TICs (an offline check of the script before this commit read the three files and
found that union). The runs of `pre-document-runs.md` are synthetic and add none. None of the
inventory's sources is edited for the check.

## The pools (the selection criteria, fixed before the queries)

The classes and filters of v0.2's protocol (`calibration/v0.2/PROTOCOL.md`, "Pools"), which the
new calibration keeps (plan B section 5: v0.2's structure), **without v0.2's data rule** (two
calendar years and 300 days between sectors), which the domain replaces:

- **Confirmed planets:** NASA Exoplanet Archive `pscomppars`, `tran_flag = 1`, a TIC id,
  `0.5 < pl_orbper < 10` d, `pl_trandep >= 0.1` (per cent), `sy_tmag <= 12`, `sy_pnum = 1`.
- **Known false positives:** the ExoFOP-TESS TOI table, `TFOPWG Disposition` = FP, or
  `TESS Disposition` = EB with `TFOPWG Disposition` not in {CP, KP, PC, APC};
  `0.5 < Period (days) < 10`; `Depth (ppm) >= 1000`; `TESS Mag <= 12`; exactly one TOI for the
  TIC; the TIC hosts no planet in `pscomppars`.

The same classes without their period, depth, magnitude and multiplicity filters are counted from
the catalogues only, **as information**; they are not searched in MAST and do not count toward the
minimum.

## The sources

Each read once, at the run. The two catalogues are recorded in `result.json` with their URL, the
time each was read (UTC) and the SHA-256 of the bytes received, and their snapshots are kept under
`.cache/real-controls/` (git-ignored), never in git. MAST's raw responses are not captured: MAST
is recorded by its server (astroquery's configured `conf.server`), the client and its versions, the
exact search arguments, the time of each TIC's search, and the rows each search returned for the
TIC (sector, `obs_id`, `t_min`, `t_max`, exposure, product file name), kept in
`.cache/real-controls/mast-rows.json` with that file's SHA-256 in `result.json`; those rows are
enough to recompute every classification.

- NASA Exoplanet Archive, TAP, `pscomppars`:
  `https://exoplanetarchive.ipac.caltech.edu/TAP/sync?query=select pl_name,hostname,tic_id,tran_flag,pl_orbper,pl_trandep,sy_tmag,sy_pnum from pscomppars&format=csv`
  (the query URL-encoded).
- ExoFOP-TESS, the TOI table: `https://exofop.ipac.caltech.edu/tess/download_toi.php?sort=toi&output=csv`.
- MAST, through `lightkurve` (the locked version) with the arguments the adapter gives
  `search_lightcurve` and `search_targetpixelfile` (`src/refute/packs/tess/adapter.py`, lines 336
  to 358): the query `TIC <id>`, mission TESS, author SPOC, exptime 120 s, and only the rows whose
  `target_name` is the TIC (the adapter's `_matching`). The script calls the body those two
  wrappers run, `lightkurve.search._search_products`, with the same arguments, because the wrappers
  turn a failed name resolution into an empty result (which would count as a D1 failure) and
  memoize it. Four searches at a time, each in its own process (astroquery's `Observations` keeps
  shared parser state between calls). A search raising a network or archive error is retried
  twice, and a TIC still failing is listed with its error and **never counted** as inside or
  outside; any other exception (an unexpected table, a missing column) stops the check, which then
  has no result.

## The screening by metadata

On **all** the TIC's SPOC 120-s light-curve sectors (never a selection of three out of more,
plan B: D1), each sector dated by its `t_min` (MJD) in the archive's table:

- **D1:** exactly three distinct years, each the UTC calendar year of the sector's `t_min`;
- **D2:** exactly three sectors;
- **D3, exposure and products:** 120 s (the search's own filter), and a target pixel file for each
  light-curve sector;
- **D5:** the two separations between consecutive sectors' `t_min` (compared unrounded), each 345
  to 385 d or 710 to 750 d, at most one of 710 to 750 d.

A TIC is counted inside by metadata only when all four pass; otherwise it is counted under the
first condition failing, in that order. **D3's measured intervals and D4 need the products' time
stamps and are not checked here**: they stay pending until gate 13's selection, and so do D1's
labels and D5's separations as the domain computes them, from the first kept cadence of each
sector, which `t_min` approximates (a sector starting near New Year can be labelled differently, and
a separation near a bound can fall on the other side). The metadata screening is therefore neither
a subset nor a superset of the domain, and the counts are of **metadata-screened candidates**.

## The record

`result.json` (the script's output: sources, exclusions, counts per class, the breakdown by the
first failing condition, the search errors, and the eligible lists with each TIC's sectors, years
and separations) and `result.md` (the counts and the outcome: the minimum reached, short, short
with search errors, or stopped by an unexpected error). The eligible lists are a record of availability and the reserve the plan
allows; the calibration's draw is gate 13's.
