# v0.4 pilot protocol (`refute-tess-discover-v0.4`)

Approved at P1 by the maintainer on 2026-10-29 (issue #177), with three adjustments: the
injection depth floor of 100 ppm; the frame and catalog downloads before this commit; the
per-sector cyclic rotation instead of block shuffles. Plan: [docs/plans/v0.4-pilot-plan.md](../../docs/plans/v0.4-pilot-plan.md);
acceptance: [docs/plans/v0.4-acceptance.md](../../docs/plans/v0.4-acceptance.md).

**Clarifications made while building WP1 to WP5**, with the maintainer's assessment of
2026-10-29 (marked "(clarification)" where they apply):

- *Design conventions, accepted with their limits:* the injected model is a trapezoid with 15 %
  ingress and egress, a limited model of this pilot: the measured recovery does not represent
  every transit shape (9). The injected dip also enters the SAP flux scaled by CROWDSAP, to
  account for dilution; the PDCSAP-SAP depth relation is tested, and a sector without CROWDSAP
  is recorded and counted apart, never as equivalent to a known one (9). The per-sector target
  lists and the frame stay out of git, with a versioned manifest and a preserved, checked copy
  (4.0). The ladder of an empty control pool is cumulative (4.3).
- *A choice that changes the eligible sample:* the Gaia DR3 EB exclusion within 21 arcsec (4.2),
  with its justification. Its cost, measured on the frozen frame of 175739 stars
  (`inputs.json`, `exclusion_preview.gaia_cost`): it excludes 2875 stars, 1621 of them excluded
  by no other rule (680 within 2 arcsec, 66 from 2 to 5, 875 from 5 to 21); 164010 stars are
  kept after every exclusion.
- *The freeze by assembly (the maintainer's decisions of 2026-10-30; an exception to 4.0):* the
  target lists of tess.mit.edu answered HTTP 502, so the inputs of attempt 7 are assembled from
  the files of attempt 4 (2026-10-29), whose log was reconstructed after it ran; its times are
  estimates. Attempt 7 supersedes attempt 6, whose MAST counts were of every cadence
  (4.0; approvals in #177).
- *Status of WP4 (ROADMAP v0.4 amendment 5, the maintainer's decision of 2026-10-29):* the
  duration-uncertainty method did not pass its acceptance and is recorded as not accepted; the
  duration goes without an uncertainty, with the justified absence citing
  `trapezoid-least-squares-1` (coverage 0.54 and 0.55 at SNR 20 and 40, against 0.61 to 0.74);
  the error is never rescaled to pass on the same set, and no other method is tried in this
  phase (11).
- *TESS-EB (the maintainer's decision of 2026-10-29, option A):* after VizieR did not answer
  during the freeze, the table is the VizieR copy obtained on 2026-10-18, as a static edition
  whose content equals the v0.2 snapshot's; used privately for the exclusion and the
  deduplication, never redistributed (#33) (2, 4.0;
  `docs/validation/v0.4/freeze-attempts-2026-10-29.md`).
- *Gaia DR3 EB (the maintainer's decision of 2026-10-30):* the source is the v0.2 snapshot, the
  v0.2.0 release asset that the freeze already used, checked against its SHA-256 and its 2184477
  data rows (`calibration/v0.2/eb_snapshot/retrieval.json`); it never depended on VizieR. A query
  of the ESA archive restricted to the frame was proposed and not adopted (2, 4.0). *Epochs:*
  Gaia positions are at J2016.0; the target lists state no epoch for theirs; no proper motion is
  applied, so a fast-moving star can be associated with a source on the wrong side of the radius
  (a limitation of the rule).
- *Still open:* how third parties can lawfully obtain the files kept out of git, which is
  written with its `sources/` records before any publication (4.0).

After the Codex round review of 2026-10-29: the selection is bound to the protocol commit's
bytes (12), S_max limits every download and read (3), the promotion record is recomputed before
stage 2 (7), and the catalog test runs on injected and transformed curves as the draft said
(9, 10). A promotion that needs the draw is never accepted offline, since only the GitHub API can
confirm the push run that fixes R_prom; that refusal avoids a network access offline, and it does
not make every promotion by draw verifiable offline (7).

Nothing in v0.4 is a validated method: every report carries `method_status: not_validated`.

## 0. What the lock covers

Every piece of code that this protocol executes lives under `src/refute`
(`refute.packs.tess.discover`: `protocol.py`, `selection.py`, `pilot.py`, `steps.py`,
`dedup.py`, `funnel.py`, `injection.py`, `transforms.py`, `measure.py`, `case.py`;
`refute.core.ledger`; `refute.packs.tess.duration`), inside the code hash of the lock
(`refute-code-1`: every file under `src/`, plus `pyproject.toml` and `uv.lock`).
`calibration/v0.4/run_selection.py` only parses its arguments and calls `steps.py`.
The values of this protocol are code in `refute.packs.tess.discover.protocol`; the block in
section 13 states them, and `tests/test_v04_protocol.py` checks that the two agree. The SHA-256
of this file, of the frame file and of each catalog snapshot go into every claim
(`test_plan.discovery.inputs`), so the lock covers them.

## 1. Claim family and meaning of the verdicts

Discovery family: SURVIVED, WEAKENED, REFUTED, INCONCLUSIVE (`docs/verdicts.md`, rules
unchanged). The verdict aggregates only the **decisive** tests (section 5), with the severity
each test emits.

**Meaning of SURVIVED in v0.4:** "the signal survived the declared decisive battery; temporal
confirmation was not required; the method is not validated". A SURVIVED is never described as a
signal repeated in time, as validated, or as a planet.

Every report, export and ledger entry carries `method_status: not_validated` (reference:
`docs/validation/v0.2.1/closing-2026-10-27.md`) and `temporal_diagnostic` (`pass`, `fail`,
`inconclusive` or `not_run`, with the aggregation rule, the per-year results and the inability
reasons).

The human conclusion of a case is one of these forms (`refute.packs.tess.discover.case`):

- "no significant signal in these data";
- "signal with a likely alternative explanation: <which>, by the test <name>";
- "signal matches a known object: <catalog, identifier, alias>";
- "signal survived the declared decisive battery; temporal diagnostic: <state>; method not validated";
- "not evaluated past stage 1: <reason>";
- "insufficient data to decide: <reason>".

Never "confirmed", "discovery", "TRUE" or a planet letter.

## 2. Sources

Authoritative only; the URL, retrieval time, size and SHA-256 of every response are recorded in
`calibration/v0.4/inputs.json`.

| Use | Source |
|---|---|
| Sampling frame | TESS two-minute target lists, all targets, per sector: the page `https://tess.mit.edu/public/target_lists/target_lists.html` and each `.../target_lists/2m/all_targets_S<sss>_v<k>.csv` it links (one per sector; two different lists for a sector stop the freeze) |
| TIC fields | TESS Input Catalog via MAST (`astroquery.mast.Catalogs`, columns `logg`, `rad`, `e_rad`, `Teff`, `Tmag`, `contratio`, `ra`, `dec`; a missing column stops the selection) |
| Availability | MAST through `lightkurve.search_lightcurve` and `search_targetpixelfile` (SPOC, 120 s), listing only |
| Last sector | MAST `Observations.query_criteria_count` (SPOC, timeseries, `t_exptime` in [119.5, 120.5] s, by sector; a filter astroquery skips stops the count, since a single value of this continuous column is skipped); the 20-s count ([19.5, 20.5] s) of each queried sector is recorded as a check by cadence and never decides S_max |
| Exclusions and deduplication | ExoFOP-TESS TOI table (`download_toi.php`); ExoFOP CTOI table (`download_ctoi.php`); NASA Exoplanet Archive `pscomppars` (TAP); TESS-EB (VizieR `J/ApJS/258/16/tess-ebs`, the static edition obtained on 2026-10-18: raw SHA-256 `61cb8749...a323`, content SHA-256 `a31936ce...949c`, equal to the v0.2 snapshot's content, `calibration/v0.2/eb_snapshot/retrieval.json`; not redistributed, #33); Gaia DR3 `vari_eclipsing_binary` joined with `gaia_source` positions (ICRS, epoch J2016.0): the v0.2 snapshot, obtained from the ESA archive on 2026-10-09, published as the v0.2.0 release asset `https://github.com/klucilla/refute/releases/download/v0.2.0/gaia_dr3_vari_eclipsing_binary.csv` (166493796 bytes, SHA-256 `5183528b8984d16b305b1fb3ce62b96cf7160961f9a59b0cbb85497e5454c3df`, 2184477 data rows, header `source_id,ra,dec,frequency`; `calibration/v0.2/eb_snapshot/retrieval.json`), downloaded into each attempt and checked against that hash and row count before use |
| Randomness | drand mainnet, default chain (`src/refute/drand.py`) |

Data credits and license statements are written with their `sources/` records (URL, retrieval
date, literal excerpt) before any publication, per CLAUDE.md; this file makes none.

## 3. Domain (common to controls and the funnel)

| # | Rule |
|---|---|
| D-1 | SPOC 120-s light curves listed in MAST in at least **3 sectors** |
| D-2 | their sector starts in at least **2 calendar years**, at least **300 days** from the first to the last |
| D-3 | a target pixel file listed in MAST for every sector of D-1 (a listing check, not a download) |
| D-4 | TIC `logg >= 4.0` |
| D-5 | TIC radius and its error present, `e_rad / rad <= 0.25` |
| D-6 | TIC Teff present, from **3200 K to 7000 K** |
| D-7 | TIC Tmag from **8.0 to 12.0** |
| D-8 | TIC contamination ratio present, `<= 0.10` |
| D-9 | sectors **1 to S_max**: S_max is the highest sector, at or below the highest sector on the target lists page, for which MAST lists SPOC 120-s light curves when the inputs are frozen; its number and every query are in `inputs.json`. Products of later sectors never count in the domain (the walk records them apart), and are never downloaded or read for an analysis (`test_plan.discovery.max_sector`) |

A star is rejected only by metadata and the existence of products, with the first failing rule
named; never by a gate result, the absence of a signal, or a test that depends on the signal.

## 4. Selection

### 4.0 Frozen before the selection round

`calibration/v0.4/run_selection.py freeze` makes one freeze attempt, before this commit: the
target lists page and the lists of sectors 1 to S_max; the frame built from them; the TOI, CTOI,
`pscomppars` snapshots; a copy of the TESS-EB static edition, read from its local path and
checked against its raw and content SHA-256 before any download (a missing or different file
stops the attempt); and the Gaia DR3 EB asset of v0.2.0 (section 2), kept as `gaia_dr3_eb.csv`
only when its SHA-256 is `5183528b...c3df` and it has one header `source_id,ra,dec,frequency`, LF
endings, no empty line and 2184477 data rows; otherwise its bytes are kept under `rejected/`, the
failure is logged, and the attempt stops. Each attempt has its own folder
(`.cache/v04/inputs-attempts/attempt-NN`), never written over, with its events appended to
`attempt.jsonl` as they happen (each file's URL, time, size and SHA-256; each failure with every
retry). Only an attempt that delivered every input becomes `inputs.json`, which names it; no file
of one attempt is ever mixed with another's. The URLs, retrieval times, sizes and SHA-256 are
committed with this protocol in `inputs.json`, with the exclusion counts and the cost of the Gaia
rule (`exclusion_preview`); files of at most 5 MB are committed in `inputs/`, except the
per-sector target lists, the frame (the frame is rebuilt from the lists), the TESS-EB table,
which is not redistributed (#33), and the Gaia asset (166 MB, above the limit; it stays
available as the v0.2.0 release asset with its SHA-256); every input is
archived to the Drive with a checked SHA-256 manifest (`run_selection.py archive`, #172), and the
selection checks every file against its hash before it reads it. A hash alone does not make the
data available: each file's public origin is in `inputs.json`, and how third parties can lawfully
obtain each file is written, with its `sources/` records, before any publication (CLAUDE.md).
Their volume counts against the 10 GB cap. Only the per-star checks of D-1 to D-8 are live
queries during the walk, each answer kept. The attempts of 2026-10-29 and 2026-10-30 are
recorded in `docs/validation/v0.4/freeze-attempts-2026-10-29.md`.

**Exception: the inputs are assembled from attempt 4** (the maintainer's decisions of
2026-10-30; approvals recorded before each run in #177:
https://github.com/klucilla/refute/issues/177#issuecomment-6523790533 and
https://github.com/klucilla/refute/issues/177#issuecomment-6525660565). The target lists of
tess.mit.edu answered HTTP 502 on every try of attempt 5 and for more than an hour after it, so
instead of the freeze above, `run_selection.py assemble` (`pilot.assemble`) built attempt 7 from
three kinds of input:

- **Original acquisition (attempt 4, 2026-10-29):** the page, the lists of sectors 1 to 107,
  TOI, CTOI and `pscomppars`, downloaded by attempt 4. That attempt ran before `attempt.jsonl`
  existed; its log was reconstructed at 2026-10-29T23:48:33Z from the files on disk (names,
  sizes, SHA-256 and write times, no URL). Its times are therefore **estimates** of the
  retrieval times, from the files' write times:
  - page 21:21:03 UTC;
  - lists 21:21:12 to 21:23:41 UTC;
  - TOI 21:24:18 UTC;
  - CTOI 21:24:21 UTC;
  - `pscomppars` 21:24:34 UTC.

  Their URLs are rebuilt from the code's constants and the page's links. The reconstructed log
  proves that today's bytes are those it records; it does not prove the HTTP responses of
  2026-10-29. Attempt 4's code was not recorded: it ran between the commits `12043a3` and
  `9c69745`, with uncommitted edits.
- **Copy (attempt 7, 2026-10-30, code `ef6fc6d`):**
  - every file of attempt 4 was checked against the size and SHA-256 of its log (the log's
    SHA-256 is `15aacb0c…f7fc`), the old frame included;
  - the files above were copied, never moved or changed, each record keeping its estimated
    time with its basis, `copied_from` and `copied_utc`;
  - S_max was found from MAST at 14:50 UTC with the cadence filter of section 2, from the
    highest sector of the copied page (111): 0 light curves of 120 s for sectors 111 to 108,
    13000 for 107, and 2160 of 20 s for 107. It had to be attempt 4's S_max (107);
  - the TESS-EB static edition (obtained 2026-10-18) and the Gaia DR3 EB asset (obtained from
    the ESA archive on 2026-10-09; downloaded again at 14:50:56 UTC) were taken as above.
- **Derivation:** the frame was derived again from the copied lists, never reused; it had to
  have, and has, attempt 4's SHA-256 (`58504462…c903`) and 175739 stars.

Attempt 6 (the same assembly, code `fa69747`) is superseded: astroquery skipped its filter
`t_exptime=120`, so its counts were of every SPOC cadence. It recorded 15160 for sector 107 under
the 120-s label; S_max was 107 with either filter. Its folder is kept as the record of that
defect, its publication moved to `.cache/v04/inputs-attempts/attempt-06/publication-withdrawn/`.

`inputs.json` records the source log's hash, the approval, the code's commit (refused had `src`,
`pyproject.toml` or `uv.lock` differed from it), attempt 6's counts as history, and the state of
the seed: R_sel was not yet determined when these inputs were obtained or assembled, since it is
fixed by the CI push run of this protocol's commit (8, 12).

*Limitation:* the exclusions and the deduplication use TOI, CTOI and `pscomppars` as obtained on
2026-10-29, and may miss entries added later.

### 4.1 Known targets (excluded before any shuffle)

From their files, by `refute.packs.tess.discover.selection.known_targets`: the targets of v0.1
(`calibration/targets.yaml`) and v0.2 (`calibration/v0.2/targets.yaml`), development targets
included, and the planets eligible in the v0.2.1 gate-3b screening
(`docs/validation/v0.2.1/reopen/stage-1/real-controls/result.json`). The pre-document runs of
v0.2.1 used synthetic data only (their record says so) and add none.

### 4.2 Funnel stars

1. **Frame:** the union of the TIC IDs in the lists of sectors 1 to S_max, with the sectors each
   appears in; kept: stars listed in at least 3 sectors. Tmag and position are those of the
   star's lowest sector. Sorted by TIC ID, written as `frame.csv`.
2. **Exclusions:** the known targets; any TIC with a TOI, a CTOI, a `pscomppars` planet or a
   TESS-EB entry (by TIC ID); any star with a Gaia DR3 EB within **21 arcsec** (by position;
   clarification: the radius is the deduplication radius of section 6, one TESS pixel, the
   scale on which a neighbor's eclipse can enter the photometric aperture). Each excluded star is
   counted by its first reason and by every reason that applies. *Cost of the Gaia rule:* it
   changes the eligible population, and it can exclude a star because of a nearby binary without
   showing that the binary contaminates the star's photometry; the freeze records how many frame
   stars it excludes, how many it alone excludes, and those by separation (0 to 2, 2 to 5 and 5 to
   21 arcsec; within 2 arcsec the binary is likely the star itself) in `exclusion_preview`.
3. **Order:** sorted by TIC ID, shuffled with `random.Random(int(randomness, 16))` of R_sel
   (`refute.drand.shuffled`).
4. **Walk:** in order, D-1 to D-8 from live queries; each star accepted or rejected with the
   rule. Stops at **100 accepted**: the first 50 in walk order run, the next 50 are the reserve
   of the N rule (4.4).
5. **Transient errors** (a connection error, a timeout, an HTTP 5xx answer): **5 attempts, 120 s
   apart**. When exhausted, the walk stops for the maintainer; no star is skipped (#22). Any
   other error stops the selection.

### 4.3 Controls

The same domain and known-target exclusion; each pool with its own order (section 8):

- **Planet:** `pscomppars` rows with `tran_flag = 1`, `sy_pnum = 1`, a TIC, `0.5 < pl_orbper <
  13 d` and `pl_trandep >= 0.1 %`, one row per TIC. Walk until 1 is accepted.
- **False positive:** TOI rows with TFOPWG disposition `FP`, `0.5 < period < 13 d`, depth at
  least 1000 ppm, exactly one TOI for the TIC, and no `pscomppars` planet. Walk until 1 is
  accepted. The TFOPWG comment is copied as information only.
- **Empty pool:** a ladder, each step at most once, in order, then the maintainer decides:
  step 1 allows Tmag up to 13.0; step 2 keeps step 1 and lowers the depth to 500 ppm (false
  positive) or 0.05 % (planet) (clarification: the steps are cumulative).
- **Signal identity** (H7 of v0.2.1): the existing rules of `refute.packs.tess.calibration` with
  a relative `period_tolerance` of 0.001: the planet's found period within it of the published
  period (aliases not counted); the false positive's at one of the factors (1, 2, 0.5),
  written in the claim as `flag_signal_period_factors`. The epoch difference is reported, not
  required.

### 4.4 The N and K rule

Claims for all 100 accepted funnel stars are written and locked. After the two controls have
run and before any funnel star runs, `refute.packs.tess.discover.funnel.choose_n_k` takes the
controls' measured costs only:

- **Measurement prefix** of each control: one stage-1 analysis, the holdout, the three
  transformed curves and the first 5 injections of its stream (injection `i` is draw `i` of the
  star's stream for any K). The means are over these runs of both controls; their cost is part
  of the hours used. After K is chosen, each control continues with injections 6 to K of the
  same stream (a declared continuation, not a rerun).
- `H(N, K) = 1.5 N (h_stage1 + h_holdout + K h_injection + 3 h_transform)`, rounded up to
  0.01 h; `G(N) = 1.5 N g`, with `g` the mean bytes of one control's light-curve files, rounded
  up to 1 MB.
- The first of `(100, 20)`, `(50, 20)`, `(50, 10)`, `(50, 5)` with `H <= 0.5 (100 h - used)` and
  `G <= 0.5 (10 GB - used)`. If none fits, nothing runs and the maintainer decides. Agent-days
  and calendar weeks are not projected; they stop the phase when reached.
- The inputs, the four evaluations and the choice are committed before any funnel run. Stars
  beyond the chosen N are recorded as "not evaluated past stage 1: N rule".
- Measurements run through `runs.run_measurements`: the output folder is reserved before any
  task is dispatched (a repeated call never repeats the work), records are appended per chunk,
  a task's own failure is a record (it stays in the denominators), and `cost.jsonl` holds each
  whole task's logical-processor seconds. The continuation of a control's prefix runs only
  injections 6 to K; the same task recorded twice is refused, never counted twice.

## 5. Tests, roles and stages

Thresholds: the v0.2 values unchanged (`docs/gauntlet-tess-v0.2.md`), on the legacy path with
H4, H7 and H9a, M4 corrections off.

| Test | Severity emitted | Role | Stage |
|---|---|---|---|
| `snr` | gate | decisive | 1 |
| `odd_even` | fatal | decisive | 1 |
| `secondary_eclipse` | fatal or warning, by `fatal_depth_ratio` | decisive | 1 |
| `period_alias` | fatal | decisive | 1 |
| `plausibility` | fatal (companion radius) or warning (duration ratio) | decisive | 1 |
| `systematics` | warning | decisive | 1 |
| `nearby_contamination` | warning | decisive | 1 |
| `eb_catalog` | fatal; warning for an own-TIC same-photometry match (H9a) | decisive | 1 |
| `centroid_shift` | fatal | decisive | 2 |
| `aperture_depth` | fatal | decisive | 2 |
| `holdout_by_year` | (not aggregated) | **diagnostic**, required | 1 |

- At stage 1 (`refute discover --stage 1`), no target pixel file is downloaded or read;
  `centroid_shift` and `aperture_depth` are INCONCLUSIVE with zero coverage and the reason "not
  run at this stage", never PASS. A valid fatal FAIL after the gate gives REFUTED.
- `holdout_by_year` runs on every funnel star at stage 1 and never changes a verdict; for a
  promoted star or a control its absence makes the case incomplete.

## 6. Deduplication

Every stage-1 signal that passes the gate is compared with each of TOI, CTOI, `pscomppars`,
TESS-EB and Gaia DR3 EB (`refute.packs.tess.discover.dedup`, the indexes of
`pilot.catalog_indexes` from the frozen snapshots; the Gaia period is 1 / frequency): the same
TIC, or a catalogued object within 21 arcsec, with a period equal within 1 % at a factor of 1, 2,
1/2, 3 or 1/3 (the factor is named). Each catalog has its own state and coverage: `match`;
`no_match` with rows scanned > 0 and every comparison decidable; or INCONCLUSIVE (no snapshot,
nothing scanned, the star without a position, or a nearby entry without a period). The overall
result is `no_match` only when every catalog is.

## 7. Promotion to stage 2

A funnel star is eligible when the gate passes; every decisive stage-1 test is present and is
PASS with coverage or a FAIL whose emitted severity is warning (none INCONCLUSIVE, none a fatal
FAIL); and deduplication is `no_match` in every catalog. The diagnostic never enters. With **3 or
fewer** eligible, all are promoted; with more, the eligible are sorted by TIC ID and shuffled
with the seed of R_prom, and the first 3 are promoted (`funnel.promote`). The others are "not
evaluated past stage 1: cap". **No replacement** of a promoted star that falls at stage 2. Zero
eligible is an acceptable outcome. The stage-1 entries (`runs.stage1_entries`: each star's
`verdict.json` SHA-256, deduplication and eligibility) are committed in the results commit, which
fixes R_prom. The promotion record (`refute-promotion-1`, `funnel.promotion_record`) holds the
claim's id and locked hash, `n_chosen`, the entries, the R_prom beacon when a draw is needed, the
promoted stars, and its provenance (the results commit and the entries' path in it, the
committed (N, K) decision, the committed `inputs.json` named in the claim, the frozen inputs and
the stage-1 run directory); it is committed. `refute discover --stage 2 --promotion <record>`
(and `refute fetch --stage 2`) first checks it (`steps.promotion_problems`): each stage-1 dossier
must be this claim's (target key, TIC, stage 1, claim id, locked claim hash and locked code hash;
otherwise the star is not eligible), the deduplication uses the locked target's position from the
selection walk, and the entries, recomputed from the dossiers' bytes and the frozen snapshots
(checked against their hashes), must equal both the record's and the results commit's (an
ancestor of HEAD); `n_chosen` is the N of the (N, K) decision read from its own commit, unchanged
since, committed before every stage-1 run (an ancestor of each run's commit) and equal to what
`choose_n_k` gives on the costs it records; the eligible list and the cap follow; a draw needs the
beacon of exactly R_prom, the round after the CI push run of the results commit, whose creation
time the record carries and the GitHub API must confirm (a draw is therefore never accepted
offline), its signature verified. A record the protocol would not produce is refused; then only the stars it promotes
(and the controls) run.

## 8. Randomness

drand mainnet, default chain (`refute.drand`): chain hash
`8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce`, genesis 1595431050, period
30 s, BLS signature verified, `seed = int(randomness, 16)`. If drand is unavailable or a
signature fails, the step stops and the maintainer decides. Each round is the first published at
least 1 hour after the creation time of **the CI push run** of a given commit: the run of
workflow `ci.yml` with event `push`, `head_sha` equal to that commit and `run_attempt` 1, read
from the GitHub API (`pilot.push_run_created_at`, `refute.drand.round_after`); no such run, or
more than one, stops the step. A commit of only `docs/**/*.md` has no push run, so each of
these commits carries a file outside that filter.

| Round | Fixed by the CI push run of | Seeds |
|---|---|---|
| R_sel | this protocol's commit | frame order `int(randomness, 16)`; planet pool `int(sha256(randomness_hex + "|v0.4|planet-pool"), 16)`; false-positive pool `"|v0.4|fp-pool"` |
| R_inj | the lock's commit B | per star: injections `"|v0.4|injection|" + TIC`; transformations `"|v0.4|transform|" + TIC` |
| R_prom | the commit recording every stage-1 result | the promotion draw, only with more than 3 eligible: `int(sha256(randomness_hex + "|v0.4|promotion"), 16)` (`funnel.promotion_seed`, as approved at P1), the eligible sorted by TIC ID and shuffled (`funnel.promote`) |

## 9. Injection-recovery (#175)

- Into every run funnel curve and both control curves, at stage 1, **before detrending**: the
  dip multiplies the normalized PDCSAP flux, and the same dip scaled by the sector's CROWDSAP
  multiplies the normalized SAP flux, so that the systematics test sees it as it would see a
  transit on the target (clarification; the relation SAP dip = CROWDSAP x PDCSAP dip is tested,
  for the injection and for the synthetic generator); the background is unchanged; no pixel
  file is injected.
- **Missing CROWDSAP:** a sector whose light-curve file gives no CROWDSAP has its SAP dip left
  undiluted (1.0), an assumption without evidence. Each injection record lists those sectors
  (`crowdsap_missing_sectors`), and the injections into such a curve are counted apart
  (`crowdsap_missing` in the per-curve summary), never in the headline recovery rate and never
  presented as equivalent to a known CROWDSAP.
- **K** injections per curve from section 4.4 (20, 10 or 5).
- Per injection `i` of a star's stream (`refute.packs.tess.discover.injection`): period
  log-uniform in [0.5, 13] d; flat-bottom depth log-uniform in **[100, 10000] ppm**; impact
  parameter uniform in [0, 0.8]; total duration of a circular orbit from the period, the TIC
  radius, the mass from logg and radius, and the impact parameter; epoch uniform over one period
  from the first cadence. The model is a trapezoid with ingress and egress of 15 % of the
  duration each (clarification).
- **Recovery:** period within 1 % and epoch within half the injected duration (modulo the
  period), and the gate passes; a period at 2x, 1/2x, 3x or 1/3x is counted apart as a declared
  alias. The stage-1 outcome on each injected signal is recorded (the catalog test included).
- **Published per curve:** counts, denominators, 95 % Wilson intervals, the sampling unit (one
  injection into that curve) and the approximate independence; across curves, descriptive only.

## 10. Transformed curves (#9, funnel amendment)

Per run curve: one **inverted** curve and **two per-sector cyclic rotations**
(`refute.packs.tess.discover.transforms`, the adapter's readers). Funnel stars: the stage-1
tests (the catalog test included); promoted stars and controls: the full battery. The holdout
does not run on transformed curves. Each measurement applies its stage's plan before it reads
anything, so a stage-1 measurement never reads a pixel file.

- **Inverted:** in each sector, the normalized PDCSAP and SAP flux reflected about their median
  (1), and each pixel's flux about its own median; errors, background, quality flags, metadata
  and times unchanged.
- **Rotation:** on the raw cadence grid of each sector's light-curve file, before the quality
  mask, every per-cadence column but the time (PDCSAP and SAP flux with errors, background,
  quality) moves by the same offset `k`: index `i` to `(i + k) mod n`. The mask and the
  momentum-dump extraction come after, so a dump moves with its cadence. The pixel cadences move
  by the same `k` when their raw time grid equals the light curve's; otherwise the pixel file
  cannot be aligned, reading it fails and its tests are INCONCLUSIVE, never passed. Per-sector
  metadata (aperture, target position, CROWDSAP, FLFRCSAP) never changes.
- **Offsets:** per sector and per rotation, from the star's transform seed, uniform in
  `[ceil(0.1 n), floor(0.9 n)]` (no identity); a second rotation equal to the first is redrawn
  from the next draws, at most 100 times, then INCONCLUSIVE; a sector with fewer than 100 raw
  cadences is not rotated (the rotation is reported as partial).
- **Limits:** a rotation can reduce the phase coherence of a periodic signal between sectors,
  but this is not guaranteed; a signal with several transits inside one sector stays visible.
- **Counted apart:** detections that pass the gate, and detections that survive the declared
  tests of their stage (`survived_stage_tests`: the decisive tests of that stage, the deferred
  ones left out; the overall verdict is kept as well), with separate denominators (eligible,
  promoted by the cap, survivors). Named "detections on transformed curves", not a false-alarm
  rate.

## 11. Exporter and duration (#176)

The parameter sheet carries `method_status` and the temporal diagnostic. The duration method
`trapezoid-least-squares-1` was specified before its code
(`docs/plans/v0.4-duration-method.md`) and **failed its acceptance** on 2026-10-29
(`docs/validation/v0.4/wp4-duration-acceptance.md`): its values are recorded in `verdict.json`,
but no duration uncertainty is exported; the sheet states the reason. By the maintainer's
decision of 2026-10-29 the pilot goes on with that justified absence, which the phase's export
criterion allows: the method is recorded as not accepted and the uncertainty as unavailable.
The covariance error is never rescaled (for example by the 1.4 of the diagnosis) to pass on the
same set; the two strict expected failures keep the result visible and are not an acceptance.
A replacement needs the maintainer's decision and a new specification with new seeds. The
failure of this estimator alone does not stop the search and the documentation of the cases.

## 12. Budget and order of steps

Caps: 22 agent-days, 8 calendar weeks (to 2026-12-24), 100 logical-processor hours, 10 GB in
`.cache`; when one is reached, stop and report. Workers: the CPUs of the process's affinity mask
minus 2, on logical processors 8 to 31.

Each step is a separate commit:

1. This protocol, the code, `run_selection.py`, `inputs.json` and the small inputs (frozen by
   the assembly of 4.0): commit and push (fixes R_sel).
2. After R_sel: `run_selection.py select --protocol-commit <this commit>`, refused unless the code, this
   protocol, the selection script, the inputs and the files of the exclusions are this commit's
   bytes (`steps.bound_problems`); the selection output (P2).
3. The claims for the 2 controls and the 100 funnel stars (`test_plan.discovery.inputs` with the
   hashes of this file, the frame and the snapshots; `max_sector` = S_max).
4. Lock: commit A (code), commit B (lock), push (fixes R_inj) (P3).
5. Controls first (stage 1 measurement prefix and stage 2); only their hashes are published
   (P3a); the N and K choice committed.
6. Funnel stage 1 (holdout, injections, transformed curves) under the lock; every stage-1 result
   committed (fixes R_prom).
7. Promotion record; pixel files of the promoted stars; stage 2 under the lock.
8. Reviews (P4), prepared material (P5), gate (P6), publication (P7).

Any rerun needs its approval recorded in an issue before it runs. A defect found in locked code
is reported; nothing is rerun without that approval.

## 13. The values (checked against `refute.packs.tess.discover.protocol`)

```yaml
domain: {min_sectors: 3, min_years: 2, min_span_days: 300.0, pixel_files_every_sector: true,
         min_logg: 4.0, max_radius_rel_err: 0.25, teff_min_k: 3200.0, teff_max_k: 7000.0,
         tmag_min: 8.0, tmag_max: 12.0, max_contamination: 0.1}
selection: {funnel_accepted: 100, controls_per_pool: 1, retry_attempts: 5,
            retry_backoff_seconds: 120.0, match_radius_arcsec: 21.0}
controls: {period_min_days: 0.5, period_max_days: 13.0, planet_min_depth_percent: 0.1,
           fp_min_depth_ppm: 1000.0, ladder_tmag_max: 13.0, ladder_planet_min_depth_percent: 0.05,
           ladder_fp_min_depth_ppm: 500.0, identity_period_tolerance: 0.001}
dedup: {period_tolerance: 0.01}
promotion: {cap: 3}
injection: {period_min_days: 0.5, period_max_days: 13.0, depth_min_ppm: 100.0,
            depth_max_ppm: 10000.0, impact_max: 0.8, period_tolerance: 0.01,
            epoch_tolerance_durations: 0.5, measurement_prefix: 5}
transforms: {rotations: 2, offset_min_fraction: 0.1, offset_max_fraction: 0.9,
             min_sector_cadences: 100, max_redraws: 100}
budget: {max_logical_processor_hours: 100.0, max_cache_bytes: 10000000000, margin: 1.5,
         share_of_remaining: 0.5, sequence: [[100, 20], [50, 20], [50, 10], [50, 5]]}
```
