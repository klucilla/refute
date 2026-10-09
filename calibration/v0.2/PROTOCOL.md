# Calibration protocol (v0.2)

This protocol was written on 2026-10-08 and completed on 2026-10-09, **before** the
v0.2 target selection was run and before any v0.2 calibration target was chosen,
downloaded or analyzed. It
fixes how the targets are chosen, how the random seed is obtained, which dossiers
are reviewed and what the claim will say, so that none of these can be tuned after
the data are seen. It follows the process rules in `CLAUDE.md` ("Pre-registration
process") and closes the process part of issue #6.

## Goal

Test the v0.2 self-claim: with the full v0.2 gauntlet (`docs/gauntlet-tess-v0.2.md`),
Refute recovers known TESS planets, flags known false positives by analyzing their
signals, and does not refute known planets.

## Order of steps (each a separate commit, verifiable with git)

1. **This protocol** with the selection and review scripts, the eclipsing-binary
   catalog snapshot index and the fixed drand rounds: committed and pushed
   **before** drand round 6537566 is published (2026-10-09T15:00:00Z). The push
   time is checked with GitHub's repository activity API and recorded in the run
   log. If the push cannot happen at least one hour before that time, the rounds
   are recomputed and this file is changed **before** it is committed.
2. **Selection**: `select_targets.py` is run after the round is published; its
   outputs (`targets.yaml`, `selection_log.md`, `pool_snapshot/`, `eb_catalog.csv`,
   `eb_catalog_scan.json`) are committed unchanged.
3. **New development target**: the 11th accepted planet is analyzed only to find
   crashes and I/O errors (declared in the run log).
4. **Claim**: `self_claim.yaml` is written and committed.
5. **Lock**: `refute lock`, then the lock is committed and pushed.
6. **Calibration**: `refute fetch` (one target at a time), then
   `refute calibrate --offline`. Any rerun needs a GitHub issue with the reason
   and the exact procedure, approved by the maintainer, before it runs.
7. **Results**, then **reviews** (see below), then the release.

## Sources (authoritative only)

| Pool | Source | Access |
|---|---|---|
| Confirmed planets | NASA Exoplanet Archive, Planetary Systems Composite Parameters (`pscomppars`) | TAP sync query, CSV |
| False positives | ExoFOP-TESS TOI table | `https://exofop.ipac.caltech.edu/tess/download_toi.php?sort=toi&output=csv` |
| Data availability | MAST, through `lightkurve.search_lightcurve` and `search_targetpixelfile` | SPOC 120-s light curves and target pixel files |
| Target coordinates | TESS Input Catalog via MAST (`astroquery`) | for the eclipsing-binary extraction |

Every catalog response is saved in `pool_snapshot/` with its URL, retrieval time
(UTC) and SHA-256. Every value in `targets.yaml` is copied from those snapshots.

## Known targets (excluded)

The 14 targets of v0.1 are a known set (`calibration/POSTMORTEM.md`, rules for
v0.2): their results have been seen, so they cannot be drawn again. They are
removed from both pools before shuffling. `select_targets.py` checks this list
against `calibration/targets.yaml` and stops if they differ.

| TIC | Name | v0.1 role |
|---|---|---|
| 207141131 | HD 18599 b | planet |
| 138819293 | GJ 436 b | planet |
| 77031414 | WASP-173 A b | planet |
| 440872576 | TOI-3160 A b | planet |
| 36592530 | WASP-75 b | planet |
| 369327947 | LHS 475 b | planet |
| 398572544 | WASP-28 b | planet |
| 283621618 | TOI-5806 b | planet |
| 374530847 | WASP-2 b | planet |
| 36452991 | TOI-2969 b | planet |
| 207339000 | TOI-4427 b | development target |
| 285524410 | TOI-2848.01 | false positive |
| 404610583 | TOI-5966.01 | false positive |
| 95129101 | TOI-1704.01 | false positive |

## Pools (same filters as v0.1)

**Planets**: rows of `pscomppars` with `tran_flag = 1`, `tic_id` not null,
`0.5 < pl_orbper < 10` days, `pl_trandep >= 0.1` (percent), `sy_tmag <= 12`,
`sy_pnum = 1`.

**False positives**: rows of the ExoFOP TOI table with `TFOPWG Disposition` = `FP`,
or `TESS Disposition` = `EB` and `TFOPWG Disposition` not in `CP`, `KP`, `PC`,
`APC`; `0.5 < Period (days) < 10`; `Depth (ppm) >= 1000`; `TESS Mag <= 12`; exactly
one TOI for the TIC; the TIC hosts no planet in `pscomppars`. The TFOPWG comment is
copied as `fp_reason`, information only.

## Data rule (both pools)

A candidate is accepted only if MAST lists SPOC 120-s light curves **and** SPOC
120-s target pixel files for it (matching TIC), each with sector start times in at
least **two calendar years** and at least **300 days** between the first and the
last sector start. The target-pixel-file part is new in v0.2: without pixel data
the centroid and aperture tests are INCONCLUSIVE.

## Random seed: drand

The seed is not chosen by anyone. It is the output of a public randomness beacon,
**drand mainnet**, default chain, published after this protocol is pushed:

| Item | Value |
|---|---|
| Chain hash | `8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce` |
| Scheme | `pedersen-bls-chained` |
| Public key | `868f005eb8e6e4ca0a47c8a77ceaa5309a47978a7c71bc5cce96366b5d7a569937c529eeda66c7293784a9402801af31` |
| Genesis, period | 1595431050 (Unix time), 30 s; round N is published at genesis + (N - 1) x 30 s |
| **Target selection round** | **6537566**, published **2026-10-09T15:00:00Z** |
| **Reviewer selection round** | **6542966**, published **2026-10-11T12:00:00Z** |
| Endpoint | `https://api.drand.sh/<chain hash>/public/<round>` |

The rounds were set on 2026-10-09 at about 02:56Z, at the maintainer's request and
before this protocol was committed (an uncommitted draft had used later rounds,
6540086 and 6551606). Their numbers follow from the formula above and were checked
against the latest published round at that time, 6536118 (2026-10-09T02:56:00Z):
6537566 = 6536118 + 1448 rounds of 30 s.

Chain information was checked on 2026-10-08 at two independent endpoints
(`api.drand.sh` and `drand.cloudflare.com`), which returned the same hash, public
key, genesis and period.

**Verification.** The script refuses to run before the round time. It checks that
the chain information matches the table above, verifies the round's BLS signature
over `sha256(previous_signature || round as 8 big-endian bytes)` with the public
key (py_ecc 8.0.0, `G2Basic`, locked in `uv.lock`; see "Dependency exception"
below), and checks that the randomness equals `sha256(signature)`. The verification
was tested on 2026-10-08 on published rounds 1000 and 6534674 (valid) and on a
tampered signature (rejected); `tests/test_drand.py` repeats it offline, in CI, on
the recorded round 1000.

**Seed.** `seed = int(randomness_hex, 16)`, used as `random.Random(seed)`.
Everything about the round (number, time, URL, randomness, signature, verifier
version, retrieval time) is written to `selection_log.md` and `targets.yaml`.

**If drand is unavailable** or the signature does not verify, the selection stops
and the maintainer decides. The source of randomness is never switched by an agent.

## Dependency exception

The WP0 dependency update of v0.2 froze `pyproject.toml` and `uv.lock` (commit
`2fa7dbc`). One exception was made afterwards, on 2026-10-08, with the maintainer's
explicit approval, before this protocol was committed and long before the lock:

- **What**: `py-ecc>=8.0.0,<9` in a new dependency group `calibration`, installed by
  default (`[tool.uv] default-groups`). Locked: py-ecc 8.0.0 and its dependencies
  cytoolz 1.1.0, eth-hash 0.8.0, eth-typing 6.0.0, eth-utils 6.0.0, toolz 1.1.0.
  No version of any existing package changed.
- **Why**: to verify the drand signature inside the locked environment, instead of
  an ephemeral one outside `uv.lock`.
- **Cooldown**: the 7-day rule held; the newest file of these packages was uploaded
  on 2026-03-25.
- `pyproject.toml` and `uv.lock` are part of the code hash; the v0.2 claim will be
  locked with them as they are now.

## Sampling

1. Each pool is filtered, the known targets are removed, and the pool is sorted by
   numeric TIC ID (ties: planet name or TOI number).
2. Each pool is shuffled with `random.Random(seed).shuffle`.
3. The shuffled pools are walked in order; each candidate is checked against the
   data rule and logged as accepted or rejected, with the reason.
4. The walk stops at **11 accepted planets** and **10 accepted false positives**.
   The first 10 planets are calibration targets; the 11th is the new
   **development target**.

## Development targets

- **New development target** (the 11th planet): the only v0.2 target that may be
  analyzed before the lock, to find crashes, unit errors and I/O problems.
  Thresholds are never changed because of it.
- **TIC 207339000** (v0.1 development target, in the known set): used before this
  protocol for I/O crash hunting only, with the maintainer's approval, after the
  v0.2 thresholds were committed (commit `78824cf`). See the next section.

## Development target observations

Recorded for transparency. Everything below was observed on TIC 207339000 (TOI-4427 b,
v0.1 development target), with the v0.2 code and thresholds already committed.

1. **No crash.** The full v0.2 fetch (5 light curves and 5 target pixel files,
   sectors 40, 47, 53, 60 and 74), the offline load and the full analysis ran
   without errors. The WCS gave target positions within 0.25 pixel of the center of
   the SPOC aperture in every sector.
2. **Cadence misalignment, found and corrected.** In 4 of 5 sectors the target pixel
   file kept cadences that the SPOC light curve drops because their PDCSAP flux is
   empty: 2534 (sector 40), 2378 (47), 1540 (60) and 5168 (74); none in sector 53.
   The pixel tests were using those cadences. Correction (commit `627e6c2`,
   approved by the maintainer): each target pixel file keeps only the cadences of
   the same sector's light curve, so the tests use the same data as the official
   SPOC light curve. It was validated on synthetic data only, and the number of
   dropped cadences is reported in every dossier. A rerun confirmed no crash and
   identical cadences in light curves and pixel files.
3. **Centroid observation, no change.** The centroid test reported an offset of
   0.13 pixel with a significance of 26.9 sigma before the correction (24.5 sigma
   after). It passed because of the 0.5-pixel floor, which exists for exactly this
   case: at high signal-to-noise a tiny systematic offset becomes formally
   significant. The threshold was not changed.
4. **No threshold was changed because of this target.** Every threshold is the one
   committed in `docs/gauntlet-tess-v0.2.md` before this target was analyzed.

## Eclipsing-binary catalogs

Snapshots taken on 2026-10-08 and 2026-10-09, before this protocol, with
`snapshot_eb_catalogs.py`; their index is `eb_snapshot/retrieval.json`. TESS-EB was
downloaded again by each run of the script; its content SHA-256 was the same on
2026-10-08 (checked on a download at 17:20Z) and 2026-10-09:

| Catalog | Rows | SHA-256 | Where |
|---|---|---|---|
| TESS-EB, Prsa et al. 2022 (VizieR J/ApJS/258/16/tess-ebs), retrieved 2026-10-09T02:44:20Z | 4584 | content `a31936ce4dc1bfbb27c4e372b145653ef1d97df250df8d1b0fadaa3f0f1b949c` (raw file `39b73495a09156959f4ae80ca6231cf3268f60075a1c44990e1add7e8dcb2bac`) | `.cache/eb_snapshot_v02/tess_ebs_prsa2022.tsv` (not redistributed; downloaded and checked on every run) |
| Gaia DR3 eclipsing-binary candidates (`gaiadr3.vari_eclipsing_binary` with `gaia_source` coordinates), joined from 20 parts | 2184477 | `5183528b8984d16b305b1fb3ce62b96cf7160961f9a59b0cbb85497e5454c3df` | `.cache/eb_snapshot_v02/gaia_dr3_vari_eclipsing_binary.csv` (too large for git; published as a release asset with this hash) |

TESS-EB source URL: `https://vizier.cds.unistra.fr/viz-bin/asu-tsv?-source=J/ApJS/258/16/tess-ebs&-out=TIC,m_TIC,RAJ2000,DEJ2000,Per&-out.max=unlimited`.

**Gaia download in parts.** A single job for the whole table failed on 2026-10-08
with a server-side error of the ESA Gaia archive while recording the anonymous
user's file quota (a database lock timeout); no file was produced. With the
maintainer's approval the same table was then downloaded from the same source
(`https://gea.esac.esa.int/tap-server/tap`, asynchronous TAP) in 20 parts:

- after a second anonymous attempt (part 1) failed with the same quota error, the
  parts were downloaded with the maintainer's registered Gaia archive account
  (`kjohanes`; asynchronous jobs up to 120 minutes and 200 GB of results, as stated
  by the maintainer). The maintainer ran the script with a local credentials file
  outside the repository; the password is never printed, logged or stored here;
- only the four columns the `eb_catalog` test uses: `source_id`, `ra`, `dec`,
  `frequency`;
- 20 equal ranges of `source_id` covering `[0, 12 x 4^12 x 2^35)`, which
  contains every Gaia DR3 `source_id` (the table's minimum and maximum were checked:
  46626164993792 and 6917527893770190080);
- one job at a time in the anonymous attempts and the first authenticated run, then
  at most 2 jobs in parallel (approved by the maintainer); each job was deleted on the
  server after its result was downloaded, to free the quota;
- the parts were joined in ascending `source_id` order with one header line and LF
  line endings; no `source_id` appeared twice and every row fell inside its part's
  range;
- the joined file has exactly 2184477 rows, equal to `SELECT COUNT(*) AS n FROM gaiadr3.vari_eclipsing_binary` at download time (2184477).

**Authenticated runs.** The first authenticated run (login 2026-10-08T18:40:58Z)
downloaded part 1 and was interrupted by an accidental Ctrl+C during part 2
(job `fde1de85-c34f-11f1-826d-bc97e148b76b-O`, left on the server; the script had
logged out at 19:52:49Z). The script was then changed to resume (reuse a part only
if its file, SHA-256, range and ADQL match the record), to run 2 parts in parallel
(approved by the maintainer after part 1 took 57 minutes; the join stays ordered by
`source_id`), to delete the orphan job after login, and to handle Ctrl+C. The second
authenticated run (login 2026-10-08T20:02:40Z) downloaded 17 parts; parts 06 and 07
failed on the server, and that version of the script stopped recording the parts that
were still queued, although they kept downloading. The script was then changed to
recover such parts from `snapshot.log` (only if the file's rows and SHA-256 equal the
logged completion) and to halve a part that fails on the server. The third run (login
2026-10-09T01:11:31Z) downloaded parts 06 and 07 whole, without halving, and was
stopped by an accidental Ctrl+C right after part 06 (confirmed by the maintainer),
before the join; both parts had been downloaded and verified. The fourth run (login
2026-10-09T02:44:19Z) reused all 20 parts and joined them. The column Run says which
run downloaded each part.

| Part | `source_id` range | Run started (UTC) | Submitted (UTC) | Downloaded (UTC) | Rows | SHA-256 of the part |
|---|---|---|---|---|---|---|
| 1 | [0, 345876451382054092) | first authenticated run (login 2026-10-08T18:40:58Z) | 2026-10-08T18:41:58Z | 2026-10-08T19:38:32Z | 50945 | `8519dae798b00966bf58643ac287126bf13d67399f614537fefd2015372c529c` |
| 2 | [345876451382054092, 691752902764108185) | 2026-10-08T20:02:39Z | 2026-10-08T20:03:45Z | 2026-10-08T21:05:57Z | 75530 | `ad1eac562e6116b53f85e558c8560971e80f578dbd0ea4743fdf89a147b2dfe4` |
| 3 | [691752902764108185, 1037629354146162278) | 2026-10-08T20:02:39Z | 2026-10-08T20:03:45Z | 2026-10-08T20:16:03Z | 14260 | `53d40bf99d7dfb818e6a726f341e95a4716ae062f15447e8e4fc183a7989ccab` |
| 4 | [1037629354146162278, 1383505805528216371) | 2026-10-08T20:02:39Z | 2026-10-08T20:17:04Z | 2026-10-08T20:24:51Z | 8073 | `c0529efa0f0a1d83d39abd4929f0811a1404a1c2836c958eba2db7bb8fa2fa37` |
| 5 | [1383505805528216371, 1729382256910270464) | 2026-10-08T20:02:39Z | 2026-10-08T20:25:51Z | 2026-10-08T20:37:19Z | 5234 | `4043a60593e3ed4f61da053ad7b1d0250ca3506fad8b90fa0c07468648d9ae43` |
| 6 | [1729382256910270464, 2075258708292324556) | 2026-10-09T01:11:31Z | 2026-10-09T01:11:35Z | 2026-10-09T01:29:48Z | 216463 | `4171c5e16951272d587a5e795f5c1d64baea6c0828700883a80f4857554cef79` |
| 7 | [2075258708292324556, 2421135159674378649) | 2026-10-09T01:11:31Z | 2026-10-09T01:11:35Z | 2026-10-09T01:17:56Z | 71369 | `df468f5071bce3bd6f49269b50291b619fcdd9d1fbed36ab4b81f77b7d3d8f62` |
| 8 | [2421135159674378649, 2767011611056432742) | 2026-10-08T20:02:40Z | 2026-10-08T21:40:24Z | 2026-10-08T21:51:55Z | 4944 | `08f70b690235143aacc7dbb220ff6213e23b623da97d97e0ed437cd2ecf30a2c` |
| 9 | [2767011611056432742, 3112888062438486835) | 2026-10-08T20:02:40Z | 2026-10-08T21:51:55Z | 2026-10-08T22:26:47Z | 59222 | `e4e17276120370c7c2a12448b785d2e19f283f3cc0866ed6fcf7bcb92ca561df` |
| 10 | [3112888062438486835, 3458764513820540928) | 2026-10-08T20:02:40Z | 2026-10-08T22:26:47Z | 2026-10-08T23:02:16Z | 66808 | `d278d0e1d69db9bf6b9db7517c419391b9b82578ffef0cd50c7e5fbb6e0a0471` |
| 11 | [3458764513820540928, 3804640965202595020) | 2026-10-08T20:02:40Z | 2026-10-08T22:39:34Z | 2026-10-08T22:45:37Z | 7155 | `d6a9a81d6e3cbdd7ec3e771b9ed69480e61ae8e9dac68fcce325ec4cef85c272` |
| 12 | [3804640965202595020, 4150517416584649113) | 2026-10-08T20:02:40Z | 2026-10-08T22:45:37Z | 2026-10-09T00:33:51Z | 441448 | `3721dd08193051b723bda92d69e1021033ea26689f8723800f4e3f5c8b1ab5f1` |
| 13 | [4150517416584649113, 4496393867966703206) | 2026-10-08T20:02:40Z | 2026-10-08T23:02:16Z | 2026-10-08T23:55:59Z | 205559 | `419aa871754e3e73d24e218be7b9f1a735312b32b8b0e43f07b3046206c9fcdb` |
| 14 | [4496393867966703206, 4842270319348757299) | 2026-10-08T20:02:40Z | 2026-10-08T23:55:59Z | 2026-10-09T00:15:43Z | 80853 | `d00e03ceac6c00bd171dcf3b3a0d8ef7e6f51d3bd7c59867aaaf64d0b662597f` |
| 15 | [4842270319348757299, 5188146770730811392) | 2026-10-08T20:02:40Z | 2026-10-09T00:15:43Z | 2026-10-09T00:18:38Z | 4001 | `7eb0ba21d87dad1b904750ef40878ec8d485b14f79c69f0d1dc8e87b370fe018` |
| 16 | [5188146770730811392, 5534023222112865484) | 2026-10-08T20:02:40Z | 2026-10-09T00:18:38Z | 2026-10-09T00:42:20Z | 204243 | `614476ad76c61d73c9bd22eed70cdb071dc3ccf04ae164464d8bd6bf107e5813` |
| 17 | [5534023222112865484, 5879899673494919577) | 2026-10-08T20:02:40Z | 2026-10-09T00:33:51Z | 2026-10-09T00:48:37Z | 244590 | `830e59b01ce89e18a88de6f40070e28ea1d59db696b336299ea29810a12e5ee1` |
| 18 | [5879899673494919577, 6225776124876973670) | 2026-10-08T20:02:40Z | 2026-10-09T00:42:20Z | 2026-10-09T01:08:07Z | 347333 | `bf3bb589823d5232cc62819cc87770ee9c963dafac639a5b8293598afd854a26` |
| 19 | [6225776124876973670, 6571652576259027763) | 2026-10-08T20:02:40Z | 2026-10-09T00:48:37Z | 2026-10-09T00:51:11Z | 15478 | `c90d5db5b58ef3b9c3a459fe76da294776a17300d9493fbfe2af273cc75dff9e` |
| 20 | [6571652576259027763, 6917529027641081856) | 2026-10-08T20:02:40Z | 2026-10-09T00:51:11Z | 2026-10-09T00:57:47Z | 60969 | `bf9f7b7458724a015b30b7cec14500152e55c12389a0caa0b18dbd7e9d8b6979` |

**Failed or interrupted attempts** (also in `eb_snapshot/gaia_failed_attempts.json`).
The server-side error is a database lock timeout while the archive records the size
of the job's result against the owner's file quota; it happened for anonymous jobs and,
on 2026-10-08, also for one job of the registered account (part 07).

| Attempt | Job | Range | Started (UTC) | Outcome | Error |
|---|---|---|---|---|---|
| anonymous, whole table | `22e96005-c32e-11f1-826d-bc97e148b76b-O` | whole table | 2026-10-08T15:37:15Z | ERROR | JDBC exception executing SQL [update uws_o.uws_owner ... set files_current_size=... where ... (files_current_size+?)<files_quota] [ERROR: ca |
| anonymous, part 01 | `0d1e9d6e-c339-11f1-826d-bc97e148b76b-O` | [0, 345876451382054092) | 2026-10-08T16:55:23Z | ERROR | same database lock timeout while recording the anonymous file quota |
| account kjohanes, part 02 (first authenticated run) | `fde1de85-c34f-11f1-826d-bc97e148b76b-O` | [345876451382054092, 691752902764108185) | 2026-10-08T19:39:35Z | interrupted (accidental Ctrl+C); the script logged out at 2026-10-08T19:52:49Z | none |
| account kjohanes, part 06 (second authenticated run) | `330cba00-c358-11f1-826d-bc97e148b76b-O` | [1729382256910270464, 2075258708292324556) | 2026-10-08T20:38:23Z | failed (no completion; the job was deleted by the script after the failure) | not captured: the previous version of the script reported only the first failure, which was part 07's |
| account kjohanes, part 07 (second authenticated run) | `33757ee3-c35c-11f1-826d-bc97e148b76b-O` | [2075258708292324556, 2421135159674378649) | 2026-10-08T21:07:01Z | ERROR | JDBC exception executing SQL [update uws_o.uws_owner ujoe1_0 set files_current_size=(ujoe1_0.files_current_size+?) where ujoe1_0.owner_id=?  |
| account kjohanes, third authenticated run (parts 06 and 07) | `604b1b12-c37e-11f1-826d-bc97e148b76b-O` | parts 06 and 07 | 2026-10-09T01:11:31Z | both parts downloaded (07 at 01:17:56Z, 06 at 01:29:48Z); then an accidental Ctrl+C by the maintainer (confirmed on 2026-10-09) at 01:29:48Z, before the join; logged out at 01:29:49Z | none |

**Halved parts.** A part that failed on the server (time limit or server error) was
halved and retried, as pre-approved by the maintainer: same query, same columns, at
most 2 jobs in parallel, at most 4 halvings. Before the join the script checked that
the ranges of the parts used tile `[0, 12 x 4^12 x 2^35)` exactly.

No part needed to be halved.

The exact ADQL of every part (also in `eb_snapshot/gaia_parts.json`, with the job
URL and the download time):

```sql
-- part 1
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 0 AND eb.source_id < 345876451382054092 ORDER BY eb.source_id;
-- part 2
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 345876451382054092 AND eb.source_id < 691752902764108185 ORDER BY eb.source_id;
-- part 3
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 691752902764108185 AND eb.source_id < 1037629354146162278 ORDER BY eb.source_id;
-- part 4
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 1037629354146162278 AND eb.source_id < 1383505805528216371 ORDER BY eb.source_id;
-- part 5
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 1383505805528216371 AND eb.source_id < 1729382256910270464 ORDER BY eb.source_id;
-- part 6
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 1729382256910270464 AND eb.source_id < 2075258708292324556 ORDER BY eb.source_id;
-- part 7
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 2075258708292324556 AND eb.source_id < 2421135159674378649 ORDER BY eb.source_id;
-- part 8
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 2421135159674378649 AND eb.source_id < 2767011611056432742 ORDER BY eb.source_id;
-- part 9
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 2767011611056432742 AND eb.source_id < 3112888062438486835 ORDER BY eb.source_id;
-- part 10
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 3112888062438486835 AND eb.source_id < 3458764513820540928 ORDER BY eb.source_id;
-- part 11
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 3458764513820540928 AND eb.source_id < 3804640965202595020 ORDER BY eb.source_id;
-- part 12
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 3804640965202595020 AND eb.source_id < 4150517416584649113 ORDER BY eb.source_id;
-- part 13
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 4150517416584649113 AND eb.source_id < 4496393867966703206 ORDER BY eb.source_id;
-- part 14
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 4496393867966703206 AND eb.source_id < 4842270319348757299 ORDER BY eb.source_id;
-- part 15
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 4842270319348757299 AND eb.source_id < 5188146770730811392 ORDER BY eb.source_id;
-- part 16
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 5188146770730811392 AND eb.source_id < 5534023222112865484 ORDER BY eb.source_id;
-- part 17
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 5534023222112865484 AND eb.source_id < 5879899673494919577 ORDER BY eb.source_id;
-- part 18
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 5879899673494919577 AND eb.source_id < 6225776124876973670 ORDER BY eb.source_id;
-- part 19
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 6225776124876973670 AND eb.source_id < 6571652576259027763 ORDER BY eb.source_id;
-- part 20
SELECT eb.source_id, gs.ra, gs.dec, eb.frequency FROM gaiadr3.vari_eclipsing_binary AS eb JOIN gaiadr3.gaia_source AS gs ON gs.source_id = eb.source_id WHERE eb.source_id >= 6571652576259027763 AND eb.source_id < 6917529027641081856 ORDER BY eb.source_id;
```

**When and how the catalog attachments are made.** Both files are generated by
`select_targets.py` in the same run as the target selection, that is **after** drand
round 6537566 is published and the targets are drawn, and only from the two
snapshots above:

1. The script reads `eb_snapshot/retrieval.json` (committed with this protocol). It
   recomputes the SHA-256 of the Gaia snapshot and the content SHA-256 of the
   TESS-EB snapshot (downloading TESS-EB from its recorded VizieR URL if it is not
   in the cache), and stops if either differs from the recorded hash.
2. It takes the TIC coordinates of every selected target (the 10 planets, the 10
   false positives and the new development target).
3. It writes `eb_catalog.csv` (format `refute-eb-catalog-1`): every snapshot entry
   within 120 arcsec of a selected target, and every TESS-EB entry with the
   target's TIC ID. Gaia DR3 entries are written in full. TESS-EB entries are written
   only as reference rows (catalog name and identifier `TIC <tic> (<m_TIC>)`, no
   coordinates, no period), because TESS-EB is not redistributed (see "Data credits
   and licenses"). Gaia periods are `1 / frequency` (frequency in d^-1, checked in
   the Gaia archive's `TAP_SCHEMA.columns`). Gaia positions are at epoch J2016.0 and
   TIC positions at J2000.0; the 16-year difference matters only for stars moving
   faster than about 1 arcsec per year, against a 21-arcsec match radius.
4. It writes `eb_catalog_scan.json` (format `refute-eb-catalog-scan-1`): each
   snapshot scanned with its file, hash and number of rows (for TESS-EB also its
   VizieR URL, its cache path, the content SHA-256 and `redistributed: false`), the
   120-arcsec radius, and every target the extraction was made for with its count of
   entries. It contains no catalog values. An empty extraction around a target is a valid result only because
   this record proves the catalogs were searched there; without it, or for a target
   not listed in it, the `eb_catalog` test is INCONCLUSIVE.
5. Both files are committed unchanged with the other selection outputs (step 2 of
   the order of steps), before the claim is written.
6. The claim attaches both: `eb_catalog.csv` with role `eb-catalog` and
   `eb_catalog_scan.json` with role `eb-catalog-scan`. `refute lock` hashes them
   with the claim, so any later change to either, including the recorded TESS-EB
   hash, makes the claim TAMPERED.
7. On every run and reproduction, before any analysis, `refute fetch`,
   `refute calibrate` and `refute replicate` download the TESS-EB file from VizieR if
   it is not in the cache and check its content SHA-256 against the locked scan
   record; if it does not match, the run stops with no dossier. The analysis then
   resolves the reference rows from that verified local copy.

Because these catalogs
may share information with the dispositions used to select the false positives,
`eb_catalog` does **not** count toward "flagged" (`flag_excluded_tests`), as the
maintainer decided; the count with every test is reported as information.

## Data credits and licenses

Checked on 2026-10-08 on the official pages; the full texts are in the README
("Data and acknowledgments").

- **Gaia DR3** (`vari_eclipsing_binary`, `gaia_source` coordinates): acknowledgement
  and citations from the Gaia DR3 "Credit and citation instructions"
  (https://gea.esac.esa.int/archive/documentation/GDR3/Miscellaneous/sec_credit_and_citation_instructions/):
  the ESA/Gaia/DPAC acknowledgement, Gaia Collaboration, Prusti et al. 2016 (A&A 595,
  A1, doi:10.1051/0004-6361/201629272), Gaia Collaboration, Vallenari et al. 2023
  (A&A 674, A1, doi:10.1051/0004-6361/202243940), and for the table Mowlavi et al. 2023
  (A&A 674, A16, doi:10.1051/0004-6361/202245330). `_citation.txt` and `_license.txt`
  of https://cdn.gea.esac.esa.int/Gaia/gdr3/ point to
  https://www.cosmos.esa.int/web/gaia-users/credits and
  https://www.cosmos.esa.int/web/gaia-users/license.
- **License of Gaia data: CC BY-NC 3.0 IGO**, with credit to ESA/Gaia/DPAC. The Gaia
  snapshot (release asset) and the Gaia rows of `eb_catalog.csv` keep that license,
  not the Apache-2.0 license of the code; `eb_snapshot/DATA_LICENSE.md` says so.
- **TESS-EB**: Prsa et al. 2022, ApJS 258, 16, doi:10.3847/1538-4365/ac324a, through
  VizieR J/ApJS/258/16/tess-ebs (doi:10.26093/cds/vizier.22580016), with the VizieR
  acknowledgement requested by the CDS
  (https://cds.unistra.fr/vizier-org/licences_vizier.html).
- **TESS-EB is not redistributed** (maintainer's decision, 2026-10-08), neither in the
  repository nor in the release. Reason: the terms differ between the publisher
  (CC BY 4.0 on the article, from Crossref) and the CDS (which states CC BY-NC for
  AAS-journal tables and links to CC BY-NC-ND). The repository keeps only the
  download script, URL, retrieval time, raw and content SHA-256, and identifiers;
  details in `eb_snapshot/DATA_LICENSE.md`. VizieR writes the query date in comment
  lines, so the raw SHA-256 changes at every download (checked on 2026-10-08 with
  two downloads); the content SHA-256 is identical and is the one checked.

## Thresholds

Every threshold is the default of the claim schema at the lock, documented with its
reason and its synthetic validation in `docs/gauntlet-tess-v0.2.md`, and written out
in the resolved, locked claim. All were set on synthetic data only.

## The claim (to be written after the selection)

> Refute recovers at least 9 of 10 known TESS planets (period within 0.1% of the
> published value), flags at least 6 of 10 known false positives by analyzing
> their signals, and gives the verdict REFUTED to at most 1 of the 10 known
> planets.

```yaml
pass_criteria:
  period_tolerance: 0.001
  expected_planets: 10
  min_recovered_planets: 9
  expected_false_positives: 10
  min_flagged_false_positives: 6
  max_refuted_planets: 1
  flag_excluded_tests: [eb_catalog]
```

- *recovered*: as in v0.1 (aliases do not count).
- *flagged*: a known false positive whose verdict, recomputed without `eb_catalog`
  by the same deterministic rules, is REFUTED.
- *refuted planet*: a known planet whose full verdict is REFUTED (any test,
  including `eb_catalog`).
- The claim passes only if all three criteria hold on a complete run; analysis
  errors count against it.

## Reviews

Following `docs/reviewer-protocol.md`, after the results are committed:

- reviewed: every false positive, every unexpected verdict (a planet REFUTED or a
  false positive SURVIVED), and 3 planets drawn with the reviewer round: the
  planets whose verdict is not REFUTED, sorted by TIC ID, shuffled with
  `random.Random(int(randomness_hex, 16))`, the first three
  (`select_reviews.py`);
- reviewer: Claude Opus 5.5, one fresh session per dossier;
- second reviewer for unexpected verdicts only: Codex, if its connection works;
  otherwise the run log records that it was left out and why;
- reviews never change a verdict.

## Scope

As in v0.1, this calibrates only an **easy regime**: periods 0.5 to 10 days, depths
of at least 1000 ppm, TESS magnitude 12 or brighter, single-planet systems, and SPOC
2-minute light curves and pixel files in at least two calendar years. The result
says nothing outside it.
