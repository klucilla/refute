# v0.5.3 stage B, B1: addendum to the stop report (decisive blockers, and D2/D4 completed)

**A new record; [`b1-stop-report.md`](b1-stop-report.md) is not edited.** The maintainer's decision
of 2026-11-12 (#217), items 1 and 2. `method_status: not_validated`. Development data only. It
decides nothing.

## What changed, and what did not

- **Unchanged: T2a's answer.** It is **no**. `K_B` is 331 and `U_B` is 0, against the 552 needed
  of 559. C keeps 373 of 615, so a certification above 20 sectors cannot rescue it.
  [`b1_blockers_decisive.py`](b1_blockers_decisive.py) recomputes A's, B's and C's kept counts from
  the same verified records and refuses to write if any differs from
  [`b1-forecast.json`](b1-forecast.json). None differs.
- **Changed: the blocker lists.** A verdict aggregates only the decisive tests, and a stage verdict
  only those not deferred at that stage:
  - `core/verdict.aggregate` runs over `pipeline.expected_by_role`'s decisive set;
  - `discover/measure.py` defines `stage_tests`.

  `duration_excess`, `event_consistency`, `single_event`, `centroid_shift` and `holdout_by_year` are
  diagnostics (`calib051/values.py`, `V051_DIAGNOSTIC`). A warning FAIL gives WEAKENED, which is
  kept, so it never blocks.

  The stop report's two blocker lists counted every INCONCLUSIVE or FAIL test, diagnostics and
  warning FAILs included:
  - the T2a list, from [`b1_t2a_blockers.py`](b1_t2a_blockers.py);
  - the D2 list, from `b1_b14.d2d4_summary`'s `v5_blockers`.

  The stop report's D2 list ("INCONCLUSIVE: `event_consistency` 31, `duration_excess` 27, … `centroid_shift` 17") is wrong for the same reason. Three of its T2a statements are wrong too:
  - "`duration_excess` 217 … `event_consistency` 188" as blockers, and "`nearby_contamination` 68" as
    a FAIL blocker: these are diagnostics, or warnings;
  - "only 5 of the 228 have a single blocker";
  - "`duration_excess` and `event_consistency`, the two most frequent blockers, are outside [version
    5's estimators]".

  The corrected lists are below. Neither script nor any of their outputs is edited.
- **New: D2 and D4 on the completed part.** The part `b1_forecast_d2d4` stopped at its cap (7.01
  CPU-h) at 7.09 CPU-h, with 181 of 200 curves. That stop stays recorded as a fact: it is under
  `reconciled` in [`ledger.json`](ledger.json). The 19 missing curves then ran as part
  `b1_forecast_d2d4_rest`, under the maintainer's approval and the procedure posted first on #217
  (comment 6826073464):
  - with the same code, fingerprint (`5bb3277e4a908c18`) and rows ([`b1_d2d4_rest.py`](b1_d2d4_rest.py));
  - in 0.707 CPU-h, of the 1.5 approved, with no new stop, so the pre-approved rerun was not used.

  On the 200 curves (178 eligible, 122 in D4's subset; 1 generation failure, 0 errors), by the frozen
  rules ([`b1-forecast-d2d4-complete.json`](b1-forecast-d2d4-complete.json)):

  | Battery | Kept (fraction, Wilson 95 %) | D2 (minimum 0.872) | REFUTED (Wilson upper) | D4 INCONCLUSIVE of 122 | D4 (at most 0.30) |
  |---|---|---|---|---|---|
  | v0.4 | 173 (0.972 [0.936, 0.988]) | PASS | 4 (0.056) | 1 | PASS |
  | Version 4 | 142 (0.798 [0.733, 0.850]) | **FAIL** | 2 (0.040) | 7 | PASS |
  | **Version 5** | **141 (0.792 [0.727, 0.845])** | **FAIL** | 3 (0.048) | 7 (0.057) | **PASS** |

  - **D2 fails with version 5.** It keeps 141, and passing would need at least 156. Of its 37
    losses, v0.4 kept 32. Version 5 keeps no planet that v0.4 loses.
  - **D4 passes.**
  - **Version 5 does not move D2:** it keeps 141 where version 4 keeps 142.
  - **The stop report's** "NOT DECIDED" for D2 and D4 is superseded by these decisions, read on the
    completed part.

## T2a: the decisive blockers (configuration B, 2 to 20 sectors)

From [`b1-blockers-decisive.json`](b1-blockers-decisive.json), `t2a.B`. The 228 losses are 140
of 302 in 2 to 4 sectors and 88 of 257 in 5 to 20. v0.4 kept 226 of them. 223 are INCONCLUSIVE and 5
REFUTED.

| Blocking test (decisive) | Losses it blocks | As the only decisive blocker |
|---|---|---|
| `systematics` | **169**: 107 insufficient sensitivity, 42 outside the domain (the selector's refusals), 20 not enough data | **72**: 59 insufficient sensitivity, 13 not enough data |
| `sinusoid` | **95**, all insufficient sensitivity | **29** |
| `odd_even` | **89**: 43 insufficient sensitivity, 42 outside the domain, 4 FAIL | **9**: 5 insufficient sensitivity, 4 FAIL |
| `period_alias` | **17**: 16 insufficient sensitivity, 1 FAIL | **11** |

- **121 of the 228** have a single decisive blocker, not 5. "Single" means single in the branch of
  `aggregate` that gave the verdict: removing a fatal FAIL could reveal INCONCLUSIVEs it hides. One
  loss can carry several, so the
  column "losses it blocks" does not sum to 228.
- **The losses by their set of blocking tests:**
  - `systematics` alone 72;
  - `odd_even` + `systematics` 35;
  - `odd_even` + `sinusoid` + `systematics` 33;
  - `sinusoid` alone 29;
  - `sinusoid` + `systematics` 23;
  - `period_alias` alone 11;
  - `odd_even` + `sinusoid` 10;
  - `odd_even` alone 9;
  - `period_alias` + `systematics` 4;
  - `odd_even` + `period_alias` + `systematics` 2.
- **The selector's refusals:** 42 losses are injections whose measured events fall outside A0's
  grid. In each, `odd_even` and `systematics` are INCONCLUSIVE "outside the domain", and version 5's
  E2 and E4 are never reached.
- **Not blockers, counted apart:**
  - warning FAILs in the losses: `nearby_contamination` 68, `period_alias` 4, `systematics` 3;
  - diagnostics INCONCLUSIVE or FAIL in the losses: they never enter the verdict.
- **Configurations A and C:** the same file has them by stratum.
  - A loses 453, with 257 refusals "the selector not certified", and above 20 sectors A did not run.
  - C loses 242, all INCONCLUSIVE or REFUTED, with the same 42 grid refusals.
  - C above 20 sectors loses 14 of 56, all INCONCLUSIVE: `systematics` 9 and `odd_even` 8, all
    insufficient sensitivity.

**A what-if, not a forecast** (it designs nothing). Removing every blocker of a class keeps the
losses whose blocking tests all belong to it.
- `systematics` alone recovers 72.
- With `sinusoid` too, 124.
- With `odd_even` too, 211.
- All four, 228.

`K_B` needs 221 more. So T2a's minimum needs essentially every blocker class resolved at once,
including the 42 grid refusals, which stage A's report already said.

## D2: the decisive blockers (version 4 and version 5, the completed part)

From `b1-blockers-decisive.json`, `d2`.
- **The decisive set** is the version-4 plan's (`expected_by_role(p4, False)`), with nothing
  deferred at stage 2.
- **Severity:** the D2 records keep none.
  - In an INCONCLUSIVE loss, every decisive FAIL is a warning, because a fatal one would have given
    REFUTED.
  - In a REFUTED loss, the decisive FAILs are listed with their severity marked unknown.
- **The losses:** version 5 loses 37 of 178 (34 INCONCLUSIVE, 3 REFUTED), and version 4 loses 36.

| Blocking test (decisive) | Version 5: losses it blocks | Only blocker | Version 4: losses it blocks | Only blocker |
|---|---|---|---|---|
| `odd_even` | **26**: 24 INCONCLUSIVE with no class recorded, 1 not enough data, 1 FAIL | **9** | 25 | 7 |
| `sinusoid` | **25**: 17 with no class recorded, 8 insufficient sensitivity | **8** | 25 | 8 |
| `period_alias` | 3 (2 FAIL, 1 INCONCLUSIVE) | 3 | 3 | 3 |
| `systematics` | 1 (not enough data) | 0 | 3 | 0 |
| `aperture_depth` | 0 | 0 | 3 (not enough data) | 0 |

- **Version 5's losses by their set of blocking tests:**
  - `odd_even` + `sinusoid` 16;
  - `odd_even` alone 9;
  - `sinusoid` alone 8;
  - `period_alias` alone 3;
  - `odd_even` + `sinusoid` + `systematics` 1.
- **Not blockers, counted apart:** these are what the stop report's D2 list had counted.
  - diagnostics: `event_consistency` 36, `duration_excess` 33, `centroid_shift` 20;
  - one warning FAIL of `systematics`.
- **A what-if, not a forecast.** D2 needs at least 15 more kept.
  - Removing `odd_even` alone recovers 9.
  - Removing `sinusoid` alone recovers 8.
  - Removing both recovers 33, or 34 with `systematics`.

  So D2 needs both `odd_even` and `sinusoid` resolved.

## The estimators: did they act where their test blocks? (item 2(b))

E2 is `odd_even`'s estimator, E3 is `sinusoid`'s (`box_after_model`), and E4 is `systematics`'
background sub-check. For each loss whose decisive blockers include that test, the record's counters
say whether the estimator **operated** in that attack, **fell back** to version 4's computation, or
was **not reached**. E4 has no fallback to version 4: without a completed measurement it returns
none (`battery_b1.py`), so its middle column reads "called, no measurement completed".
- E2 operated if `e2.gls` ≥ 1;
- E3 operated if `e3.gls` ≥ 1;
- E4 operated if `e4.measured` ≥ 1.

| Estimator (test) | T2a B, losses with the test blocking | operated | fell back (E4: called, no measurement) | not reached | D2 version 5, losses with the test blocking | operated | fell back (E4: called, no measurement) | not reached |
|---|---|---|---|---|---|---|---|---|
| E2 (`odd_even`) | 89 | 35 | 12 | 42 (grid refusals) | 26 | 22 | 4 | 0 |
| E3 (`sinusoid`) | 95 | **0** | 95 | 0 | 25 | **2** | 23 | 0 |
| E4 (`systematics`) | 169 | 110 | 17 | 42 (grid refusals) | 1 | 0 | 1 | 0 |

- **E3 never operated** in a T2a loss that `sinusoid` blocks. Over every T2a record of B, it operated
  in 12 of 559 attacks. Its AR(1)-per-sector moments fall back on almost every curve: φ outside (0,
  0.99), `gamma1` or `gamma2` not positive. **So the sinusoid's 95 losses are version 4's
  computation.** E3 was never tested on them.
- **E4 measured in 110 of the 169** `systematics` losses, and `systematics` stayed INCONCLUSIVE in
  each: 107 insufficient sensitivity, 3 not enough data. `systematics` combines several sub-checks.
  These records do not show which one kept it INCONCLUSIVE, so they do not show that the
  background sub-check lacked power. In the other 17, E4 was called and completed no measurement;
  its quadratic windows ran in each of those 17.
- **E2 operated in 35 of the 89** `odd_even` losses. 42 are grid refusals, where it is never reached.
- **On D2, E2 operated in 22 of the 26** `odd_even` losses, and E3 in 2 of the 25 `sinusoid`
  losses. Over every eligible D2 attack:
  - E2 operated in 174 of 178;
  - E3 in 29 of 178;
  - E4 in 177 of 178.

  In the 22 D2 losses where E2 operated, `odd_even` stayed INCONCLUSIVE in 21. In one (planet
  3129) it was a FAIL.

## Earlier blocker tables (item 2(c))

Checked: every script of v0.5.2's stage 2 and of v0.5.3's stage A that tallies blockers, and every
committed table that names a diagnostic test.

| Table | Diagnostics counted as blockers? | Note |
|---|---|---|
| **B1:** `b1-t2a-blockers.json` (`blockers`, `sole_blocker`) and the stop report's T2a list | **yes, affected** | also lists warning FAILs; superseded by `b1-blockers-decisive.json` |
| **B1:** `b1-forecast.json`, `d2_d4.v5_blockers`, and the stop report's D2 list | **yes, affected** | the same |
| **B1:** `b1-forecast.json`, `t2a.configurations.*.blockers` | empty (the dict-versus-string defect already disclosed) | |
| Stage A: `d2_bounds.py` (`d2-bounds.json`) | no | a fixed decisive set; warnings recoverable by severity |
| Stage A: `t2a_bounds.py` (`t2a-bounds.json`) | no | reads v0.5.2's diagnosis reading, which keeps decisive stage tests and drops warning FAILs |
| Stage A: `above20.py` | no | stage tests only; it never ran |
| Stage A: `a0_refusals.py` (`a0-refusals.json`) | no | no blocker table: A0's refusing branches |
| v0.5.2: `forecast-paths.md` (blocker counts and removal tables) | no | derived from the decisive readings of `forecast_v4_paths.py`, `forecast_v4_paths_r2.py` and `forecast_t2a_paths.py` (added in Codex's round 1 of this record) |
| v0.5.2: `forecast_t2a.py` (`forecast-t2a.json`, `blockers_of_losses_overlapping`) | no | decisive and not deferred, but **every FAIL is listed, warnings included** (`nearby_contamination` FAIL 6 and 8 to 11 per configuration): a different, smaller defect, listed for completeness |
| v0.5.2: `forecast_t2a_diagnosis.py` (`forecast-t2a-diagnosis.json`) | no | stage tests; its class (e) lists every FAIL, warnings included, and `forecast_t2a_diagnosis_reading.py` drops warning FAILs |
| v0.5.2: `forecast_t2a_paths.py` | no | decisive, not deferred; INCONCLUSIVE or fatal FAIL |
| v0.5.2: `forecast_v4_losses.py`, `forecast_v4_paths.py`, `forecast_v4_paths_r2.py` | no | the plan's decisive set. The D2 records keep no severity, so a warning FAIL can be listed; `paths_r2` gives both readings |
| v0.5.2: `forecast-v4.json` (`tests`) | not a blocker table | a status tally per test over every curve, diagnostics included, labeled by test |
| v0.5.2: `closing-record.md`, and stage A's README | no | they quote the tables above |

**Affected by the same problem: only B1's two lists.** v0.5.1 has no blocker table.

## Consumption of this addendum

- **CPU:**
  - the D2/D4 completion took 0.707 CPU-h, of the 1.5 approved;
  - the two read-only scripts (`summarize`, `b1_blockers_decisive.py`) are reads of committed
    records, not charged.
  - Stage B now stands at 53.273 of 150 CPU-h.
- **Review tokens:**
  - Codex's review of the completion script, 114,130;
  - this addendum's review, in the consensus record;
  - the totals are in the closing record.
- **Disk:** `.cache/v053/stageB/` holds 1.46 GB, of 5 GB.
