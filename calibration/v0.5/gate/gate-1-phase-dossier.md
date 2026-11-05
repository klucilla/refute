# v0.5 Stronger tests: the phase dossier for the gate

Prepared by the agent that ran the phase, on 2026-11-05, for the independent gate review. It
**proposes** a status per exit criterion with pointers to the evidence; the gate checks the
evidence itself and decides. Repository: `C:\Projetos\refute`, branch `main`, head `54b76f6`
(pushed). Local evidence under `.cache/` is named where it is the only copy (it is not in git).

## 1. What the phase set out to do

- ROADMAP.md, section "v0.5 Stronger tests" (scope and the 8 exit criteria).
- Plan: `docs/plans/v0.5-plan.md` (section 5: exit criteria with the evidence rules; section 7:
  caps and the stop rule; section 8: stops S0 to S6; section 9a and 9b: decisions and the S4
  deviation's lesson; section 7 also records the disk-cap decision of 2026-11-05).
- Acceptance documents: `docs/plans/v0.5-acceptance.md` (WP1 to WP10 and the frozen C1 design).
- Calibration protocol (frozen): `calibration/v0.5/PROTOCOL.md`.
- Tracking issue #199; its full thread as of 2026-11-05 is saved at
  `.cache/v05/gate/issue-199-thread.txt` (every maintainer decision, every run, every deviation).

## 2. The measurements (C1, C2, C3), as they came out

Synthetic and real-data calibration, pre-registered and locked (claim
`calibration/v0.5/claim.yaml`, SHA-256 `48acfe24…`; code hash `15a9c256…`; lock commit B
`b6249b5`). `method_status: not_validated`. Results are reported as they came out; the maintainer's
decision 1 of 2026-11-05 (#199) records the failed targets as results, with no rerun and no
retuning, and the phase goes on to closing.

| Step | Commit | Result (targets) | Records |
|---|---|---|---|
| C1 confirmation (2,400 synthetic curves, once, round R_c1 6613448) | `e8e4816` | D1: EB1 FAIL, EB2 FAIL, ER/NR/SE/V1/V2 PASS, NW NOT DECIDABLE (4 eligible); D2 FAIL; D3 PA/PG/PV PASS; D4 FAIL; D5 PASS (no decisive centroid in the v0.5 battery) | `calibration/v0.5/runs/c1-confirmation/` (report, manifest, cost; records on the Drive, `drive-manifest.sha256`) |
| C2 run (100 real stars of the v0.4 funnel, both batteries, 10 injections per curve) | `a9ec11a` | compatibility with v0.4 established (1,400 curves, 0 mismatches); T2a FAIL; T2b-inverted PASS; T2b-rotated PASS; T2c PASS | `calibration/v0.5/runs/c2/` |
| C3 fetch, dossiers and run (8 planets + 8 EB false positives, newly drawn) | `c0453ed` | T3a PASS; T3b PASS (bounds of adverse outcomes, not classification accuracy) | `calibration/v0.5/runs/c3/`, `runs/c3-fetch.json`, `runs/c3-dossiers/` (dossiers archived to the Drive; local copy `.cache/v05/c3/dossiers/c3-dossiers/`) |

The trade-off the targets show: fewer spurious signals survive (T2b, T2c, D1 for the noise and
variability families, D3), and many more real or injected planets end INCONCLUSIVE (D2, D4, T2a;
SURVIVED → INCONCLUSIVE is the dominant paired transition). Findings: #201 (planets lost to
INCONCLUSIVE) and #202 (synthetic EBs that still survive, about 18 % and 22 %, no decisive
centroid). Structural sources found by the reviews: #203 (the `sinusoid` domain P ≥ 10 d),
#204 (the `period_alias` sensitivity simulation at a fixed threshold).

**The T3b record (#199, the maintainer's request):** one of T3b's eight outcomes,
TIC-101395259, is INCONCLUSIVE only because the `period_alias` PASS was refused by its
sensitivity simulation; without that refusal it would be SURVIVED. T3b would still PASS (1 of 8,
the rule allows 2), but its count of 0 depends on that refusal. Reported as it came out.

## 3. Deviations and decisions after the lock (all recorded on #199 before they ran)

1. **S4, claim packaging (2026-11-04):** the frozen claim failed the TESS schema; fixed outside
   `src/` under an approved deviation (`calibration/v0.5/deviation/README.md`): a target
   projection, a TESS-EB preparation script for the C3 execution, and `guarded_c3.py` (`refute
   verify` before `c3-fetch` and `c3-run`). Original code and selection kept.
2. **Budget decision (protocol section 8):** 10 injections per curve (C1 + C2(20) + C3 did not
   fit the reserve) — `calibration/v0.5/runs/budget.json`.
3. **Disk cap raised from 15 to 20 GB** (2026-11-05, the C3 pixel files) — plan section 7.
4. **C2 fetch:** two transient MAST failures before any record; attempt 3 completed (retry rule
   recorded first).
5. **Processor-hour accounting corrected** (Codex): the C2 prefix had been counted twice.
6. **Exit criterion 6, the mirror deviation (2026-11-05):** VizieR at CDS did not answer (attempt
   1, 5 attempts); by the maintainer's decision the TESS-EB table was placed from the official
   mirror `vizier.cfa.harvard.edu`, verified by the claim's content hash; reported as "met with
   one recorded deviation: one input placed from an official CDS mirror, verified by the
   claim's content hash", with the note that criterion 6 as written requires nothing placed by
   hand. Source of the CDS incident: a CDS post on Facebook, 2026-10-28, read by the maintainer
   on 2026-11-05 — **not confirmed by another source**. Issue #206.

## 4. S5: the draw and the four dossier reviews

- Rule: `calibration/v0.5/reviews/RULE.md` (commit `5ee4f0a`, pushed alone; validated with Codex
  in 3 rounds). Draw: `calibration/v0.5/reviews/draw.json` (round 6615406, signature verified).
- Reports, byte for byte as they came out: `calibration/v0.5/reviews/reports/` with `index.json`
  (SHA-256, tokens). Assessments: TIC-280206394 OBJECTIONS; TIC-17746821 NO OBJECTION;
  TIC-101395259 OBJECTIONS; TIC-286355915 OBJECTIONS. No critical objection; each review found
  the dossier intact and the verdict the correct output of the locked rules. Important
  objections → #203, #204, #205, #202 (comment); minor ones → #205.
- Tokens: 803,269 (cap 250,000 per session; every session under it).

## 5. The exit criteria: the agent's proposed status and the evidence

| # | Criterion (ROADMAP) | Proposed | Evidence |
|---|---|---|---|
| 1 | Acceptance section committed before tests and code; synthetic cases run, counts from a JUnit XML; each test accepted (decisive) or recorded as failed (diagnostic only) | MET (to be checked) | `docs/plans/v0.5-acceptance.md` first committed in `559eaf0` (2026-11-03T08:41:16-03:00), before the first code commit `0deb97f` (08:50:00); revision 2 in `ca5f68b` changes section C1 only, before C1 code. The one acceptance run: `docs/validation/v0.5/acceptance/README.md` (133 rows: 119 PASS, 11 FAIL, 3 INVALID; the roles table: decisive tests, and `single_event`, `event_consistency`, the per-sector centroid recorded as diagnostic). Note: the acceptance harness's row counts come from its own JSON (`acceptance-run.json`), not from a JUnit file; the suite's unit and integration cases are counted from JUnit (`.cache/v05/crit2/junit-end.xml`: 4,530 tests, 0 failures, 0 errors, 91 skipped). |
| 2 | No synthetic test that passes at the start of v0.5 fails at its end without a justification written before; historical claims give their recorded verdicts and hashes | MET | Full suite at tag v0.4.0 (`ad5fd5c`) in a worktree: `.cache/v05/crit2/junit-v040.xml` (4,267 tests, 0 failures, 91 skipped) → baseline `.cache/v05/crit2/v0.4.0-passing-tests.txt` (4,176 node IDs). End suite (`junit-end.xml`) checked with `scripts/check_test_baseline.py`: 4,174 passed by exact node ID; 2 "missing" are `tests/test_ml_data_sources.py::test_host_readers_count[<zip bytes>...]` whose parameter ID embeds a zip built at collection time (its timestamp bytes differ between runs); both cases pass in both runs (`.cache/v05/tools/compare_param_ids.py`). Historical claims: `scripts/verify_locked_tags.py` → 8 of 8 PASS (v0.1.0, v0.2.0, five v0.3.0 claims, v0.4.0). |
| 3 | No fatal or warning test of the v0.5 battery can PASS without its declared sensitivity (engine rule, shown by a sabotage case) | MET | `tests/test_sensitivity.py` (68 passed in the end suite), among them `test_a_fatal_pass_that_could_not_detect_is_inconclusive`, `test_a_warning_pass_without_a_block_is_inconclusive`, `test_an_unregistered_test_cannot_pass`, `test_a_malformed_block_never_passes` (12), `test_an_empty_or_malformed_registry_entry_never_lets_a_pass_through` (3), `test_the_registry_sets_a_rule_requirement_the_result_cannot_change`; `tests/test_v05_battery.py` (32 passed; the registry covers every decisive test, `registry_problems`); sabotage cases in `tests/test_v05_centroid.py`. |
| 4 | The synthetic confirmation set run once on frozen code and reported, pass or fail | MET | C1, section 2 above; `calibration/v0.5/runs/c1-confirmation/report.json`; R_c1 after the lock; once (attempt-01). |
| 5 | The paired real-data measurements locked, run and reported, pass or fail, with reviewer reports for the dossiers the protocol draws | MET | C2 and C3, section 2; the S5 reviews, section 4. |
| 6 | One new-control dossier reproduced in a clean clone from the generated instructions alone; the empty-checkout test runs in CI | MET with one recorded deviation | `calibration/v0.5/reviews/criterion6/` (attempt 1: FAIL, the source did not answer; attempt 2: PASS by `calibration/v0.5/reviews/evaluate_c6.py`, "OK: manifest intact; key results reproduced"); the deviation, section 3 item 6; the empty-checkout test `tests/test_v05_reproduce.py::test_8_1_and_8_2_the_dossier_is_reproduced_in_an_empty_checkout` passes in the suite, which CI runs (`.github/workflows/ci.yml`). |
| 7 | Every scope issue closed, kept open with the part left, or moved with its reason; no `.cache/test-*` folder remains after the suite | PARTLY MET (dispositions proposed, not yet applied) | No `.cache/test-*` folder after the end suite (counted). Scope issues: every one is still open; the agent's proposed disposition is in section 6; applying it (closing or commenting) waits for S6. |
| 8 | Gate: an independent review returns SURVIVED, or WEAKENED with its issues open | (this review) | — |

## 6. Criterion 7: proposed disposition of the scope issues (not yet applied)

| Issue | Proposal | Reason |
|---|---|---|
| #185 sensitivity rule | close | done (WP1; criterion 3) |
| #184 signal versus noise | keep open, part left | `single_event` and `event_consistency` built but diagnostic only (failed acceptance); decisive per-event tests left |
| #193 partial sectors, edge ramps | close | `edge_events` and the report part done (WP2, WP6) |
| #182 variability | keep open, part left | sinusoid and duty cycle done; a multi-frequency, prewhitened model left (plan section 2); #203 |
| #181 secondary eclipse | keep open, part left | two-sided check done; the bound from a planet's possible occultation left (plan section 2); #202 |
| #183 per-sector centroid | move to #200 | built, not accepted (rows 4.1 and 4.5 INVALID); a new acceptance in a later phase |
| #190 report wording | close, with #205 | wording done (WP4, WP6); the hidden centroid offset found in S5 is #205 |
| #187 blend caveat | close | in every report |
| #191 shape and depth stability (WP5, optional) | move, no target version | optional, not started |
| #179 exporter label | close | done (WP6) |
| #186 labels and values | close, with #205 | done (WP6); minor S5 items in #205 |
| #194 catalog period uncertainty | close | done (WP6) |
| #180 injection-recovery competition | keep open, part left | gate-negative hosts reported apart; masking the host's own signal left |
| #188 reflected curve | close | the bounded study done (WP7), recorded with its deviation |
| #9 null distribution | keep open, part left | report part done; a validated null is out of scope |
| #189 REPRODUCE.md self-sufficient | close, with #206 | WP8 and criterion 6; the single-host dependency is #206 |
| #195 reproduction criterion | close | done (WP8, criterion 6) |
| #196 frozen TESS-EB folder | close | done (WP8) |
| #176 duration uncertainty (WP9, optional) | move, no target version | optional, not started |
| #192 neighbors beyond 21 arcsec | keep open | not in scope (plan section 2) |
| #197 test folders, flaky test | close | done (`ab782ed`, `ca5f68b`); no folder left after the suite |
| #198 paired comparison split | close | done (WP10, `paired.py`) |

## 7. Caps (plan section 7)

| Cap | Used | Notes |
|---|---|---|
| Calibration processor-hours | 84.79 of 100 | prefixes 4.28, C1 28.73, C2 38.02 (new work), C3 3.10, C3 dossiers 10.65 (wall × 22 workers); the criterion-6 runs are minutes |
| Logical-processor hours (phase) | about 105 of 150 | development about 19.9 plus calibration; test-suite wall time reported, not counted |
| Disk | peak 18.25 GB of 20 (2026-11-05T17:39Z) | cap raised from 15 GB on 2026-11-05; warnings at 16 GB reported |
| Reviewer tokens | 803,269 of 1.5 M | the gate session's cap is 400,000 |
| Agent-days | not measured precisely; the per-round log is in #199 | |

## 8. Codex reviews of the calibration stages

`.cache/v05/codex-s5-round-answer.md` (C1/C2/C3 commits: reports recomputed and reproduced; the
accounting correction), `.cache/v05/codex-s5-draw-answer*.md` (the draw rule, 3 rounds),
`.cache/v05/codex-c6-dev-answer*.md` (the mirror deviation, 3 rounds),
`.cache/v05/codex-s5-stage-answer*.md` (the S5 stage commits: the evaluator; AGREEMENT on the
blocker after round 2). Earlier phase rounds: `docs/plans/v0.5-consensus/`.
