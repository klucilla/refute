# v0.5.6 Apply with declared limits: the phase dossier for the gate review

Prepared by the agent that ran the phase, on 2026-11-23, for the independent gate review that the
maintainer's decision of 2026-11-23 (08:30, item 2, #218) asks for. It **proposes** a status per exit
criterion, with pointers to the evidence. The gate checks the evidence itself and decides.

Repository: `C:\Projetos\refute`, branch `main`. The review checklist is
`.claude/commands/gate-review.md`.

## 1. What the phase set out to do

- **ROADMAP.md**, section "v0.5.6 Apply with declared limits": the scope and the five exit
  criteria, with the evidence written under criteria 1 to 4.
- **The plan** [docs/plans/v0.5.6-plan.md](../../../plans/v0.5.6-plan.md). It has two amendments
  and a source record:
  - amendment 1: [v0.5.6-plan-amendment-1.md](../../../plans/v0.5.6-plan-amendment-1.md), with
    door 3 found and not pursued, and part B made a claim of agreement;
  - the lock plan: [v0.5.6-part-b-lock-plan.md](../../../plans/v0.5.6-part-b-lock-plan.md);
  - the open sources: [v0.5.6-open-sources-2026-11-21.md](../../../plans/sources/v0.5.6-open-sources-2026-11-21.md).
- **The rules:**
  - `CLAUDE.md`, with the amendment of 2026-11-21 (case (c), declared limits) and "Explore freely,
    conclude strictly";
  - the limits label 'WEAKENED; does not meet D1, D2, D4, T2a'.
- **Tracking:** #218. The maintainer's decisions are recorded there before each action (21:00,
  22:30 and 22:45 on 2026-11-21; 09:00, 13:00, 14:30 and 19:30 on 2026-11-22; 08:30 on
  2026-11-23). Known defects are logged on #59.

## 2. Proposed status per exit criterion

| # | Criterion | Proposed | Evidence |
|---|---|---|---|
| 1 | Part A on the approved set and cost; frame, split and draw before any light curve; coverage, "exploratory" and the label on every output | MET | The frame and split are in 099c67c and the draw in 2f0d95e, both before the pilot (1d4bdcf). The run is 2e734b5, with 240 records. [part-a-ledger.json](../part-a-ledger.json): 5.95 CPU-h of 50. [part-a-records.json](../part-a-records.json): 240 records, all `exploratory`, labelled and `not_validated`, and every test of the 239 OK records with its coverage |
| 2 | The exploratory report, with each door marked | MET | [part-a-report.md](../part-a-report.md) (2e734b5) |
| 3 | The part B claim locked before its targets were read, run once, verdict as it came | MET | The round is fixed in fd62b0a and the lock is fdd87e7, at 23:56:20Z on GitHub (CI run 45085907521). Round 6665418 came out at 00:26:00Z. The draw is 185fd91, and the runner refuses a draw not on `origin/main` (`calibration/v0.5.6/part_b_run.py:147`). [part-b-ledger.json](../../../../calibration/v0.5.6/part-b-ledger.json) shows one execution ending `complete`. The verdict is 57c4160, [part-b-verdict.md](../../../../calibration/v0.5.6/part-b-verdict.md): `SURVIVED`. The draw can be checked with [verify_part_b_draw.py](../verify_part_b_draw.py) |
| 4 | A public report drafted for the maintainer's approval, with the label and v0.5's failed targets | MET | The maintainer approved it with five changes (2026-11-23, 08:30; #218, comment 7099686672). It is [docs/reports/v0.5.6-report.md](../../../reports/v0.5.6-report.md) (3665521, 532ba44). The Codex round on its text is [report-round-1-answer.md](../../../plans/v0.5.5-consensus/report-round-1-answer.md) |
| 5 | Codex's review (up to three rounds, one conversation) and a gate review | open until this gate | Codex's review of the phase: round 1 `SURVIVED`, with no blocking item ([phase-round-1-answer.md](../../../plans/v0.5.5-consensus/phase-round-1-answer.md), ffaea2f) |

## 3. Departures, all decided by the maintainer and recorded

- **Door 3 found and not pursued.** This departs from the plan's "the first door proceeds". It
  was decided on 2026-11-22 at 13:00 and is recorded in amendment 1 and the consensus record,
  section "v0.5.6 part B: the independent review of the options".
- **Part B's claim was suggested by part A's descriptive table.** This origin is disclosed in the
  claim (`calibration/v0.5.6/claim.yaml`, hypothesis), in amendment 1 and in the report.
- **Codex rounds 4 and 5 on part B** went beyond the usual three, as the maintainer's exceptions
  of 14:30 and 19:30. The relock path was removed at 19:30. The details are in the consensus
  record, `docs/plans/v0.5.5-consensus/README.md`, sections "round 4" and "round 5".
- **T3b stays deferred** (`INCONCLUSIVE`), by
  [the availability record](../../../plans/v0.5.6-t3b-availability-record.md), which is not an
  infeasibility record.

## 4. Losses, defects and open items

- **Part A:** 1 ERROR, the `OverflowError` in `centroid_v5`, and 2 half-period identity cases
  (#59, comment 7081325757).
- **Part B:** 5 ERRORs (2 planet, 3 FP), each counted as a non-event and a loss under the frozen
  rule, against a cap of 15 per stratum. Four were network failures. One is `LinAlgError` in
  `centroid_v5.combine` (#59, comment 7099778438). None was rerun.
- **Non-blocking items, on #59:**
  - the ledger state on a resumed run (comment 7086792355);
  - the lock plan's batch window (comment 7100100258).
- **Nothing changed** in `src/`, `pyproject.toml` or `uv.lock` during the phase, nor any earlier
  verdict, lock or published record.

## 5. Checks a reviewer can run (read only)

```
uv run --frozen refute verify calibration/v0.5.6/claim.yaml
uv run --frozen python docs/validation/v0.5.6/verify_part_b_draw.py --offline
git diff fdd87e7 HEAD --stat -- src pyproject.toml uv.lock calibration/v0.5.6
```

The suite runs through `scripts/run_tests_affinity.ps1`. The v0.5.6 tests are in `tests/v056`.
