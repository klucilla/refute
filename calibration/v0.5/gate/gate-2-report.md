## Summary (three sentences)
The pre-registration still holds at head `6c724cb`. `refute verify` returns PASS. Nothing in `src/`, `pyproject.toml`, `uv.lock`, the protocol, the selection, the claim, the claim targets or the lock changed after `b6249b5`. The only non-additive change since the lock is the recorded disk-cap note in the plan. Every commit after the first gate (`f895f9c`, `1c6c66b`, `88cc530`, `6c724cb`) only adds files.

Criterion 7, the reason for the first REFUTED, is now applied and recorded: 22 scope issues, with 12 closed, 8 kept open with the part left and 2 moved. #195 is kept open for item 4, in line with PROTOCOL.md 67-68 and plan 9a.3. I recomputed the other criteria's evidence (baseline comparison, final JUnit, C3 targets, criterion-6 `check-dossier`) and it holds.

All eight criteria are met, criterion 6 with the approved and honestly reported mirror deviation. The phase still leaves important scientific limits that must stay open: planets lost to INCONCLUSIVE, synthetic eclipsing binaries that still survive, structural INCONCLUSIVEs, no decisive centroid, and a single-host dependency for reproduction. So my verdict is WEAKENED, not SURVIVED.

## Exit criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | Acceptance before tests and code; cases run with JUnit counts; each test decisive or diagnostic | MET | `559eaf0` (2026-11-03 08:41:16 -03) comes before the first code commits `ab782ed` (08:49:57) and `0deb97f` (08:50:00). Revision `ca5f68b` changes two hunks of `v0.5-acceptance.md` only (lines 6-12, the preamble; lines 339+, C1), per `git diff 559eaf0 ca5f68b`. Roles: `docs/validation/v0.5/acceptance/README.md:62-75`. The failed tests are diagnostic: `single_event`, `event_consistency` and `centroid_v5`, as in `claim.yaml:220-224`. Acceptance rows from JUnit: `.cache/v05/gate2/acceptance-rows-junit.xml` (SHA-256 `e31448ef…`, as cited), my recount gives 133 tests, 11 failures, 0 errors, 3 skipped. That matches `acceptance-run.json`: 119 PASS, 11 FAIL, 3 INVALID. |
| 2 | No synthetic test that passed at the start fails at the end; historical claims give their verdicts and hashes | MET | My own comparison of `criterion2/v0.4.0-passing-tests.txt` (4,176 IDs) with `.cache/v05/gate2/junit-final.xml`: 4,174 pass by exact ID and none fails. The 2 "missing" IDs are the zip-parameter cases of `test_host_readers_count`, and they pass under timestamp-dependent IDs (`compare_param_ids.py` output; the same 2 in `baseline-check-final.json`). Historical claims: `test_lock_compat` 65 passed and `test_v05_battery` 32 passed in the final JUnit; C2 compatibility shows 1,400 curves and 0 mismatches (`runs/c2/report.json`). I did not rerun `verify_locked_tags.py` (8 of 8, as cited). |
| 3 | No fatal or warning test can PASS without its declared sensitivity, shown by a sabotage case | MET | `tests/test_sensitivity.py:202-235`: the sabotage at lines 210 and 233. In the final JUnit: `test_sensitivity` 68 passed, `test_v05_centroid` 13 passed. |
| 4 | C1 run once on frozen code and reported | MET | Only one folder exists: `.cache/v05/calibration/c1-confirmation-attempts/attempt-01`. `runs/c1-confirmation/report.json` has D1 EB1 FAIL (35 of 190) and EB2 FAIL (40 of 186), D2 FAIL (kept 0.538 against 0.968), D3 PASS, D4 FAIL (0.327), D5 PASS. All are reported. |
| 5 | C2 and C3 locked, run and reported; reviewer reports for the drawn dossiers | MET | `refute verify` gives PASS (claim `48acfe24…`, code `15a9c256…`, 7 attachments). I recounted C3 from `runs/c3/records.jsonl` with the ledger replacement TIC-62483237 → TIC-310002617 (identity not matched). T3a: REFUTED 0 of 8 (S3 W1 I4). T3b: SURVIVED 0 of 8 (W4 I3 R1). Both equal `report.json`. C2 targets: T2a FAIL (0.424 against 0.997, n=637), T2b PASS, T2c PASS. The 4 reports are in `reviews/reports/`, unchanged since `6ecb238`. |
| 6 | One C3 dossier reproduced in a clean clone; the empty-checkout test in CI | MET with one recorded deviation | I reran `refute check-dossier .cache/v05/repro-c6-attempt-02/refute/repro/repro/TIC-101395259 --against .cache/v05/c3/dossiers/c3-dossiers/TIC-101395259`: "OK: manifest intact; key results reproduced". On the original: "OK: manifest intact". `criterion6/attempt-02/evaluate.json`: PASS. Order: the deviation was decided on #199 at 17:22:59Z, its scripts committed in `b9cfb33` at 17:32:29Z, the fetch ran at 17:32:39Z. The text is honest: it says criterion 6 as written requires nothing placed by hand. The empty-checkout test passes in the final JUnit and runs in `ci.yml:127-128`. |
| 7 | Every scope issue closed, kept open with the part left, or moved with its reason; no `.cache/test-*` left | MET | `.cache/v05/gate2/dispositions-applied.json` has 22 issues, acted on between 19:17:58Z and 19:19:28Z. That is after Codex round 3 (19:17:39Z, file time of `codex-c7-answer-3.md`). Each of the 22 has a comment text (`disposition-*.md`). Plan section 2's keep-open list is respected: #181, #182, #191, #180, #9 and #192 are open. #195 is kept for item 4. The ROADMAP's scope issues plus #192, #197 and #198 are all covered. No `.cache/test-*` exists now (checked). The #195 reopen has a gap in its local evidence (finding 1). |
| 8 | Gate | WEAKENED (this review) | See the verdict. |

## The first gate's findings

| Finding | Answered? | Evidence |
|---|---|---|
| I1 criterion 7 not applied | Yes | `criterion7.md` (`88cc530`); `dispositions-applied.json`; #199 comment 32 (19:20:22Z); maintainer decision 3 (comment 31, 19:08:19Z) came before the application. |
| I2 #195 must stay open | Yes, with an evidence gap | `disposition-195.md` names item 4. GitHub closed #195 at 19:08:47Z (event `closed`, commit `f895f9c`, in `issue-195-events.json`); this is disclosed in `criterion7.md:37-41`. The reopen is recorded only as the agent's statement plus the draft `.cache/v05/comment-195-reopen.md`; no saved API state shows it (finding 1). My search of `ad5fd5c..HEAD` commit messages found no other closing keyword. |
| M1 acceptance counts not from JUnit | Yes (as the maintainer decided) | `acceptance_rows_junit.py` turns the recorded rows into pytest cases. It is disclosed as "a recount of the recorded outcomes, not a rerun" (`criterion2/README.md:43-53`). The JUnit counts match my recount. |
| M2 baseline FAIL record without a note | Yes | `criterion2/README.md:24-31`; `baseline-check.json`; `compare_param_ids.py` (rerun by me, both cases pass in both runs). |
| M3 cite the v0.5 compatibility tests | Yes | `criterion2/README.md:32-41`. |
| M4 end suite predates the last commits | Yes | `junit-final.xml`: timestamp 16:20:54 -03, 10 s after `88cc530` (16:20:44). 4,538 tests, 0 failures, 0 errors, 91 skipped (my recount; SHA-256 `b67cc3fd…` as cited). It includes `test_v05_deviation_c6` (7 passed). `6c724cb` only adds an .md file. |
| M5 D3 on the wrong side of the trade-off | Yes | `phase-dossier-2.md:61-66` (but see finding 3). |
| M6 CDS incident source without a URL | Yes | `calibration/v0.5/sources/cds-incident-2026-11-05.md`: Facebook URL with the maintainer's reading marked unconfirmed; Bluesky excerpt matching `calibration/v0.4/sources/data-licenses-2026-11-01.md:95-98`. |
| M7 thread without timestamps | Yes | `issue-199-thread-timestamps.md` has created and updated times, and the edited comment 12 is marked. |
| M8 no per-objection map | Yes | `reviews/objections-map.md`: 24 rows (7+6+4+7), matching the four reports' tables; 6 important objections, each with an issue (but see finding 2). |
| No published record edited | Confirmed | `git diff --name-status b6249b5 HEAD` shows only additions, apart from the plan's disk-cap note. The reports are unchanged since `6ecb238`. `gate-1-report.md` SHA-256 `a1f3e374…` equals `gate-1.json`. `gate-1-phase-dossier.md` equals the original `.cache/v05/gate/phase-dossier.md`. The new files contain no "Users", "AppData" or user name. |

## Findings

| Severity | File and line | Problem | Why it matters | Suggested fix |
|---|---|---|---|---|
| minor (1) | `.cache/v05/gate2/dispositions-applied.json:131-136`; `issue-195-events.json` | The only saved state of #195 after the dispositions is `CLOSED` (19:19:08Z). The saved events end with `demilestoned` and contain no `reopened` event. The reopen is stated only in #199 comment 32 and `criterion7.md:37-41`. | I2 and criterion 7 depend on #195 being open. Offline, the record does not show it. | At S6, save #195's issue state and events from the API (after the reopen) as a new record. |
| minor (2) | `calibration/v0.5/reviews/objections-map.md:25` | It maps TIC-17746821 objection 3 to "#191 (moved)". `criterion7.md:20` and `disposition-191.md` keep #191 open; the map was committed (`1c6c66b`, 16:12) before Codex round 2 changed that. | The two committed records contradict each other on one disposition. | Correct it in a new record (the closing record), not by editing. |
| minor (3) | `.cache/v05/gate2/phase-dossier-2.md:61-66` | T2c (the original curves of the v0.4 funnel, real candidates whose truth is unknown) is listed under "fewer spurious signals survive". The summary also leaves out that on C3, v0.5 REFUTED fewer known false positives than v0.4 (1 against 2 of 8, without the catalog test). TIC-233681149 went from REFUTED to INCONCLUSIVE, and T3b's 0 SURVIVED comes with 3 INCONCLUSIVE. The thread reports the counts (comments 17, 27). | This summary feeds the S6 release text, which must state the trade-off with numbers. | In the release text, describe T2c as "fewer original candidates survive (truth unknown)" and give the C3 REFUTED 2 → 1 next to T3b. |
| minor (4) | `calibration/v0.5/results/criterion7.md:4-7` | It says "validated with Codex in 3 rounds", but round 3 returned `DISAGREEMENT` (`.cache/v05/codex-c7-answer-3.md:1`) on the wording of #190. The fix was adopted in full (`disposition-190.md`), so no divergence remains. | Small imprecision in the record. | State the round-3 label in the closing record. |
| minor (5) | `.cache/v05/gate2/phase-dossier-2.md:41` | It says "31 comments"; the saved thread (line 3) has 32. | Trivial. | None needed beyond the closing record. |

What I did not verify offline: the GitHub states of the issues after 19:19Z, CI run 42092997835, `verify_locked_tags.py` (not rerun), and the Facebook source (marked unconfirmed in the record).

## Verdict: WEAKENED

All eight exit criteria are met. Criterion 6 uses one recorded deviation, approved before it ran (an input placed from an official VizieR mirror and checked by the claim's content hash), and it is honestly reported. The pre-registration holds: verify PASS, no protected path changed after `b6249b5`, one attempt per run, and the failed targets (D1 EB1/EB2, D2, D4, T2a) are reported with no rerun or retuning (maintainer decision 1). The records found contain no claim of a discovery or a confirmed planet, and T3a/T3b are described as bounds, not classification (PROTOCOL.md:223-227).

It is WEAKENED rather than SURVIVED because the phase leaves important open limits, which must stay open in tracked issues:
- #201: planets lost to INCONCLUSIVE (D2, D4, T2a FAIL).
- #202: synthetic eclipsing binaries still survive (about 18 % and 22 %), and no decisive test separates EBLM/SB1 companions.
- #203: the `sinusoid` domain limit.
- #204: the `period_alias` sensitivity simulation refusing a supported PASS (T3b's count of 0 depends on it).
- #200 (with #183): no accepted decisive centroid.
- #206: reproduction depends on a single host for TESS-EB.
- #195: item 4.
- #205: report wording.
- The kept-open scope issues: #184, #182, #181, #191, #180, #9, #192, and #176 (moved).

Minor findings 1 to 5 above can be fixed directly in the closing record at S6, as new records.
