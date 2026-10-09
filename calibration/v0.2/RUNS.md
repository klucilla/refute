# Run log of the v0.2 calibration

Each step of `calibration/v0.2/PROTOCOL.md` is recorded here with its evidence.

## Step 1: protocol committed and pushed

- Protocol commit: `16e880d` (with `989b997`, `46bdb34`, `25b8956`, `eb30567`,
  `27f32d7` and `627e6c2` in the same push).
- Push time, from GitHub's repository activity API
  (`GET /repos/klucilla/refute/activity`): **2026-10-09T02:58:52Z**, push to
  `refs/heads/main` from `78824cf` to `16e880d` by `klucilla`.
- Target-selection drand round 6537566 is published at **2026-10-09T15:00:00Z**:
  the protocol was pushed **12 h 01 min 08 s** before it, more than the 1 hour the
  protocol requires.
- Reviewer-selection drand round: 6542966, published at 2026-10-11T12:00:00Z.
- The latest published round when the rounds were set was 6536118
  (2026-10-09T02:56:00Z).

## Step 2: selection

- Command: `uv run --frozen python calibration/v0.2/select_targets.py`, from commit
  `16e880d` with a clean tree except this file; started 2026-10-09T15:00:45Z, ended
  2026-10-09T15:18:54Z, exit code 0.
- drand round 6537566 retrieved 2026-10-09T15:00:50Z from `api.drand.sh`; signature
  verified (py_ecc 8.0.0, G2Basic). Randomness
  `6203178f500788b092dafc8557309f4225cee9fa7b907eefe819b69525ce325d`. Checked again
  on `drand.cloudflare.com`: same randomness, signature verified,
  same seed.
- Pools after exclusions: 475 planets, 456 false positives. Walk: 13 planet positions
  (11 accepted), 40 false-positive positions (10 accepted). 21 targets written, 5
  eb-catalog rows.
- **Error during the walk.** False-positive position 35, TIC 239638934 (TOI-2571.01),
  was rejected with "MAST query failed: Timeout limit of 600 exceeded." instead of a
  data-rule decision. Under the maintainer's instruction to stop on any error, the
  run stopped there: the outputs were not committed and nothing after this step
  was run until the maintainer decided.
- Diagnostic only (no output changed): at 2026-10-09T15:19:37Z the same check
  (`mast_availability`) for TIC 239638934 found one sector (83, 2024) of light curves
  and pixel files, so the data rule would have rejected it; the selected targets would
  be the same.
- **Maintainer's decision (2026-10-09, recorded at 15:25Z):** commit the
  outputs exactly as produced, without any change. Reason: the protocol requires the
  selection outputs to be committed unchanged, and a rerun could change the pools
  (the catalogs are live). The timeout is recorded here; the issue for handling such
  errors in future selections is https://github.com/klucilla/refute/issues/22
  (future phase; nothing implemented now). Nothing was rerun.

## Step 3: new development target (crash and I/O hunt only)

- Target: WASP-93 b (TIC 240681314), the 11th accepted planet, kind `development`
  in `targets.yaml`; excluded from the claim.
- Procedure: a scratch script that follows the per-target path of `refute calibrate`
  without a lock (TESS-EB content-hash check, fetch, offline load, analysis with the
  `eb_catalog.csv` and `eb_catalog_scan.json` attachments, plots, parameter sheet,
  verdict and report), writing a throwaway dossier under the git-ignored `dossiers/`.
  Code at commit `2d4d5ec`, claim-schema default thresholds.
- Time: 2026-10-09T15:26:13Z to 15:27:28Z.
- Data: SPOC 120-s light curves and target pixel files of sectors 17, 57 and 84
  (years 2019, 2022, 2024); 46570 cadences. In every sector the target pixel file
  kept exactly the light curve's cadences (12507, 17990 and 16073).
- Result: **no crash, no I/O or reading error** in any stage. For transparency, the
  analysis found a period of 2.732534 d (published 2.7325321 d) and the verdict
  SURVIVED, with every test PASS.
- Nothing was changed because of this target: no code, threshold, criterion or target.
