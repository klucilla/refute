# Calibration protocol (v0.1)

This protocol was written on 2026-10-07, **before** `select_targets.py` was run
and before any calibration light curve was downloaded or analyzed. It fixes how
the calibration targets are chosen, so that the choice is reproducible and cannot
be tuned to make Refute look good.

## Goal

Test the pre-registered self-claim in `self_claim.yaml`: Refute recovers known
TESS planets, flags known false positives, and does not refute known planets.

## Sources (authoritative only)

| Pool | Source | Access |
|---|---|---|
| Confirmed planets | NASA Exoplanet Archive, Planetary Systems Composite Parameters (`pscomppars`) | TAP sync query, CSV |
| False positives | ExoFOP-TESS TOI table | `https://exofop.ipac.caltech.edu/tess/download_toi.php?sort=toi&output=csv` |
| Data availability | MAST, through `lightkurve.search_lightcurve` | SPOC 120-s light curves |

Every catalog response is saved in `pool_snapshot/` with its URL, retrieval time
(UTC) and SHA-256. Every value copied into `targets.yaml` comes verbatim from
those snapshots. Nothing is typed by hand.

## Planet pool

All rows of `pscomppars` with:

- `tran_flag = 1` (transiting) and `tic_id` not null;
- `0.5 < pl_orbper < 10` days;
- `pl_trandep >= 0.1` (percent, i.e. at least 1000 ppm; rows without a depth are excluded);
- `sy_tmag <= 12`;
- `sy_pnum = 1` (a single known planet in the system, so the strongest periodic
  signal is the planet).

## False-positive pool

All rows of the ExoFOP TOI table with:

- disposition rule: `TFOPWG Disposition` is `FP`, **or** `TESS Disposition` is `EB`
  and `TFOPWG Disposition` is not one of `CP`, `KP`, `PC`, `APC`;
- `0.5 < Period (days) < 10`;
- `Depth (ppm) >= 1000`;
- `TESS Mag <= 12`;
- the TIC has exactly one TOI in the table (mirrors the single-planet rule);
- the TIC does not host any planet in `pscomppars` (no confirmed planet host can
  be counted as a false positive).

The TFOPWG comment, when present, is copied into `targets.yaml` as `fp_reason`.
It is information only, never a filter.

## Data-availability rule (both pools)

A candidate target is accepted only if MAST lists SPOC 120-s light curves for it
(`author = SPOC`, `exptime = 120`, matching TIC) whose observation start times
(`t_min`) fall in at least **two different calendar years**, with at least
**300 days** between the first and the last sector start.

## Sampling

1. Each pool is sorted by numeric TIC ID (ties: planet name or TOI number).
2. Each sorted pool is shuffled with Python's `random.Random(20261007).shuffle`.
   The seed is the date this protocol was written.
3. The shuffled pools are walked in order. Each candidate is checked against the
   data-availability rule and accepted or rejected, with the reason logged in
   `selection_log.md`.
4. The walk stops at **11 accepted planets** and **3 accepted false positives**.
   The first 10 planets are calibration targets. The 11th accepted planet is the
   **development target**.

## Development target

The development target is the only real target that may be analyzed before the
self-claim is locked. It is used to find crashes, unit errors and I/O problems in
the adapter and pipeline. Thresholds are never changed because of its outcome. It
is marked `kind: development` in `targets.yaml` and is excluded from
`refute calibrate`.

## What is fixed before any calibration data is seen

- the selection rules and seed above;
- every gauntlet threshold, chosen from synthetic tests and documented in
  `docs/gauntlet-tess-v0.1.md`, and written explicitly into `self_claim.yaml`;
- the self-claim and its pass criteria, including the degeneracy guard.

## After the lock

`self_claim.yaml`, `targets.yaml` and the code are locked together (claim hash,
targets hash, code hash, git commit) and the lock is committed and pushed before
`refute calibrate` runs. If the self-claim fails, the failure is reported in
`POSTMORTEM.md`. Thresholds, targets and data are never changed to make it pass.

## Scope

This calibrates only an **easy regime**: short periods (0.5 to 10 days), deep
transits (at least 1000 ppm), bright stars (TESS magnitude 12 or brighter),
single-planet systems, and SPOC 2-minute data in at least two calendar years. The
result says nothing about longer periods, shallower transits, fainter stars,
multi-planet systems or other data products.
