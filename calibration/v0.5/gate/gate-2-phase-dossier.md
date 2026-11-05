# v0.5 Stronger tests: the phase dossier for the second gate review

Prepared by the agent that ran the phase, on 2026-11-05, for the second (and last) independent
gate review approved by the maintainer. It **proposes** a status per exit criterion with pointers
to the evidence; the gate checks the evidence itself and decides. Repository:
`C:\Projetos\refute`, branch `main`, head `6c724cb` (pushed; `88cc530` is the last commit before
the records of the final suite). Local evidence under `.cache/` is
named where it is the only copy.

**The first gate review** (fresh Opus session, 294,689 tokens) returned **REFUTED (narrow)**:
criteria 1 to 6 met (6 with the recorded, approved mirror deviation); criterion 7 not met; minor
findings M1 to M8. Its report and the dossier it was given are committed unchanged:
`calibration/v0.5/gate/gate-1-report.md`, `gate-1-phase-dossier.md`, `gate-1.json`. Section 2
below says what was done in answer to each finding. Everything else in the first dossier still
holds, and is repeated in sections 3 to 7 (with finding M5 corrected).

## 1. What the phase set out to do

- ROADMAP.md, section "v0.5 Stronger tests" (scope and the 8 exit criteria).
- Plan: `docs/plans/v0.5-plan.md` (section 2 scope and "partial answers stay open"; section 5
  exit criteria; section 6 what does not enter; section 7 caps, the disk-cap decision of
  2026-11-05, the stop rule; section 8 stops; sections 9a and 9b decisions).
- Acceptance documents: `docs/plans/v0.5-acceptance.md`. Calibration protocol (frozen):
  `calibration/v0.5/PROTOCOL.md`.
- Tracking issue #199. The full thread **with created and updated times** (finding M7):
  `.cache/v05/gate2/issue-199-thread-timestamps.md`. Every scope issue in full, with times:
  `.cache/v05/gate2/issues/issue-<n>.md`.

## 2. What was done in answer to the first gate

| Finding | Done | Where |
|---|---|---|
| I1: criterion 7 not applied | The dispositions applied on GitHub, one comment per issue: 12 closed, 8 kept open with the part left, 2 moved with the reason; validated with Codex in 3 rounds first | `calibration/v0.5/results/criterion7.md` (commit `88cc530`); the comments on each issue (#199 comment of 2026-11-05) |
| I2: #195 must stay open for item 4 | Kept open, item 4 as the part left. It was **closed by accident** at 19:08:47Z by GitHub, which read "close #195" in a phrase of commit `f895f9c`'s message (quoting the first gate); reopened the same day with an explanation on #195; no other commit message of the phase has a closing keyword | `criterion7.md`; issue #195; `.cache/v05/gate2/issues/issue-195.md` |
| M1: acceptance counts not from JUnit | The 133 recorded rows recounted from a JUnit XML (a recount of the recorded outcomes, not a rerun): 133 tests, 11 failures, 3 skipped (119 passed) | `docs/validation/v0.5/acceptance/acceptance_rows_junit.py`; `calibration/v0.5/results/criterion2/README.md` (commit `1c6c66b`) |
| M2: the baseline checker's FAIL record without a note | The note: the 2 "missing" IDs are the zip-parameter cases whose IDs embed a timestamp; both pass in both runs | `calibration/v0.5/results/criterion2/` (README, `baseline-check.json`, `compare_param_ids.py`, `v0.4.0-passing-tests.txt`) |
| M3: criterion 2 should cite the v0.5 compatibility tests | Cited: `tests/test_lock_compat.py` (all passed), `tests/test_v05_battery.py::test_a_v04_analysis_is_unchanged_by_the_v05_code`, C2's 0 mismatches over 1,400 curves | `criterion2/README.md` |
| M4: the end suite predates the last commits | The full suite run after the last commit (`88cc530`) through `scripts/run_tests_affinity.ps1`: 4,538 tests, 0 failures, 0 errors, 91 skipped (JUnit XML); the same 2 timestamp-dependent baseline IDs, both passing; no `.cache/test-*` folder after it | `calibration/v0.5/results/criterion2/suite-final.md` (commit `6c724cb`) |
| M5: D3 on the wrong side of the trade-off | Corrected in section 3 below | this dossier |
| M6: the CDS incident's source without a URL | A `sources/` record: the CDS Facebook post (URL, read by the maintainer on 2026-11-05; the page is not readable by the agent's tools, so no excerpt from it), and the CDS Bluesky notice of 2026-10-28 (read by the agent on 2026-11-05, literal excerpt), which corroborates the incident; the mirror list from the v0.4 record | `calibration/v0.5/sources/cds-incident-2026-11-05.md` |
| M7: the saved thread without timestamps | Saved again from the GitHub API with created and updated times (31 comments; edited comments marked) | `.cache/v05/gate2/issue-199-thread-timestamps.md` |
| M8: no per-objection map | Each of the 24 objections (6 important, 18 minor) mapped to its issue; the 5 minors that had none tracked on #205 | `calibration/v0.5/reviews/objections-map.md` |

Also decided by the maintainer on 2026-11-05: the Codex-agent divergence on the absolute project
paths in the criterion-6 logs is settled for the agent (the logs stay as they came out: no user
name; the project path is already public in CLAUDE.md), and any new log is checked for
"Users", "AppData" or a user name before it is committed.

## 3. The measurements (C1, C2, C3), as they came out

Claim `calibration/v0.5/claim.yaml` (SHA-256 `48acfe24…`; code hash `15a9c256…`; lock commit B
`b6249b5`). `method_status: not_validated`. The maintainer's decision 1 of 2026-11-05 records the
failed targets as results (no rerun, no retuning).

| Step | Commit | Result (targets) | Records |
|---|---|---|---|
| C1 confirmation (2,400 synthetic curves, once, round 6613448) | `e8e4816` | D1: EB1 FAIL, EB2 FAIL, ER/NR/SE/V1/V2 PASS, NW NOT DECIDABLE; D2 FAIL; D3 PA/PG/PV PASS; D4 FAIL; D5 PASS | `calibration/v0.5/runs/c1-confirmation/` |
| C2 run (100 real stars, both batteries, 10 injections per curve) | `a9ec11a` | compatibility established (1,400 curves, 0 mismatches); T2a FAIL; T2b-inverted PASS; T2b-rotated PASS; T2c PASS | `calibration/v0.5/runs/c2/` |
| C3 fetch, dossiers and run (8 planets + 8 EB false positives) | `c0453ed` | T3a PASS; T3b PASS (bounds of adverse outcomes, not classification accuracy) | `calibration/v0.5/runs/c3/`, `c3-fetch.json`, `c3-dossiers/` |

**The trade-off (finding M5 corrected).** *Fewer spurious signals survive:* D1 PASS for the
correlated-noise, single-event, edge-ramp and variability families (NR, SE, ER, V1, V2), T2b
(inverted and rotated curves) and T2c (original candidates). *More planets end INCONCLUSIVE:* D2,
D4 and T2a FAIL; SURVIVED → INCONCLUSIVE is the dominant paired transition. *Planets not
refuted:* D3 PASS (PA, PG, PV) and T3a PASS. *Spurious signals that still survive:* D1 FAIL
for EB1 and EB2 (about 18 % and 22 % survive; no decisive centroid). Findings: #201, #202;
structural sources: #203 (`sinusoid` domain), #204 (`period_alias` sensitivity simulation).

**The T3b record:** TIC-101395259 is INCONCLUSIVE only because the `period_alias` PASS was
refused by its sensitivity simulation; without that refusal it would be SURVIVED; T3b would still
PASS (1 of 8, the rule allows 2), but its count of 0 depends on that refusal (#199).

## 4. Deviations and decisions after the lock (each recorded on #199 before it ran)

1. S4 claim packaging (2026-11-04): `calibration/v0.5/deviation/README.md`.
2. Budget decision: 10 injections per curve (`calibration/v0.5/runs/budget.json`).
3. Disk cap 15 → 20 GB (2026-11-05; plan section 7).
4. C2 fetch: two transient MAST failures before any record; attempt 3 completed.
5. Processor-hour accounting corrected (Codex: the C2 prefix counted twice).
6. Criterion 6, the mirror deviation (2026-11-05): `calibration/v0.5/reviews/criterion6/`,
   `calibration/v0.5/deviation/fetch_tess_eb_mirror.py`, `reproduce_c6_mirror.py`,
   `calibration/v0.5/reviews/evaluate_c6.py`; source record (M6) above; issue #206.

## 5. The exit criteria: the agent's proposed status and the evidence

| # | Criterion (ROADMAP) | Proposed | Evidence |
|---|---|---|---|
| 1 | Acceptance before tests and code; synthetic cases run, counts from a JUnit XML; each test decisive or diagnostic | MET | `559eaf0` (acceptance, 08:41:16 -03) before `0deb97f` (first code, 08:50:00); revision 2 `ca5f68b` changes section C1 only; the acceptance run's roles table (`docs/validation/v0.5/acceptance/README.md`); its 133 rows counted from a JUnit XML (M1: 133, 11 failures, 3 skipped); the suite's v0.5 cases from the final suite's JUnit (section 2, M4) |
| 2 | No synthetic test passing at the start fails at the end without a prior justification; historical claims give their verdicts and hashes | MET | `calibration/v0.5/results/criterion2/README.md` (M2, M3); `verify_locked_tags.py` 8 of 8 PASS; the final suite (M4) |
| 3 | No fatal or warning test can PASS without its declared sensitivity, shown by a sabotage case | MET | `tests/test_sensitivity.py` (68 passed), `tests/test_v05_battery.py` (32), `tests/test_v05_centroid.py` sabotage cases; the final suite |
| 4 | C1 run once on frozen code and reported | MET | section 3 |
| 5 | C2 and C3 locked, run and reported; reviewer reports for the drawn dossiers | MET | section 3; `calibration/v0.5/reviews/` (RULE.md, draw.json, reports/, index.json, objections-map.md) |
| 6 | One new-control dossier reproduced in a clean clone from the generated instructions; the empty-checkout test in CI | MET with one recorded deviation | `calibration/v0.5/reviews/criterion6/attempt-02/evaluate.json` (PASS); the deviation, section 4 item 6; the note that criterion 6 as written requires nothing placed by hand; `tests/test_v05_reproduce.py::test_8_1_and_8_2_the_dossier_is_reproduced_in_an_empty_checkout` in the suite CI runs |
| 7 | Every scope issue closed, kept open with the part left, or moved with its reason; no `.cache/test-*` after the suite | MET | `calibration/v0.5/results/criterion7.md` (applied 2026-11-05); no `.cache/test-*` after the final suite (`criterion2/suite-final.md`) |
| 8 | Gate | (this review) | — |

## 6. S5: the draw and the four dossier reviews

`calibration/v0.5/reviews/RULE.md` (commit `5ee4f0a`), `draw.json` (round 6615406),
`reports/` (byte for byte) with `index.json`, and `objections-map.md` (M8). Assessments:
TIC-280206394 OBJECTIONS; TIC-17746821 NO OBJECTION; TIC-101395259 OBJECTIONS; TIC-286355915
OBJECTIONS. No critical objection. Tokens 803,269.

## 7. Caps (plan section 7)

| Cap | Used |
|---|---|
| Calibration processor-hours | 84.79 of 100 |
| Logical-processor hours (phase) | about 105 of 150 (test-suite wall time reported, not counted) |
| Disk | peak 18.25 GB of 20 (cap raised from 15 GB on 2026-11-05) |
| Reviewer tokens | 1,097,958 before this session (four reviews 803,269; first gate 294,689); this session's cap 400,000 (total at most 1,497,958 of 1.5 M) |

## 8. Codex reviews

`.cache/v05/codex-s5-round-answer.md`; `codex-s5-draw-answer*.md`; `codex-c6-dev-answer*.md`;
`codex-s5-stage-answer*.md` (round 3 left the absolute-paths divergence, settled by the
maintainer for the agent); `codex-c7-answer*.md` (the criterion-7 list, 3 rounds).
