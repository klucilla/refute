# v0.5.12 step 4: Codex's first round on correction 2 did not complete (2026-11-26)

The correction's draft and the round's prompt are committed (`step4/`,
`docs/plans/v0.5.12-spec-correction-2.md`,
`docs/plans/v0.5.12-correction-2-consensus/r1-codex-prompt.md`). The round itself did not
complete. No Codex answer exists for correction 2.

## The two attempts (journal `log.jsonl`, unit `codex`, label `corr2-r1`)

| Attempt | Outcome | Cause |
|---|---|---|
| 1 | failed (exit 1), 2.4 CPU-s | The wrapper's events file was asked for under `.cache/v0512/codex/`, a folder that did not exist, so PowerShell's `Out-File` failed when the pipeline started. No events file and no answer were written, and no Codex thread is recorded. The agent's path error. |
| 2 | **interrupted** by the meter, `disk allowance` | The paths were moved to `.cache/v0512/`, which exists. The Codex thread `01a21826-635e-7ac3-9a15-aad43b8235f2` started, and its events show 1 turn started and 10 items completed, with no `turn.completed`. The job had written 128,834,173 bytes when the launcher stopped it at the unit's 50 MB disk reservation. Most of that is Codex's own state, written outside the project. |

**Tokens:** unknown. The interrupted turn reported no usage, and the service may still count it.

**Attempt 2 was a second execution of the unit `codex`.** Its logical key differed from attempt 1's,
because the output paths differed, so the launcher let it run. Attempt 1 had started no Codex
thread. This record states it for the maintainer's review.

## What a further attempt needs (not done; the maintainer's decision)

- **A new unit file** (rule (c)), for example `units/codex2.json`, with a disk reservation that
  covers Codex's own writes. Attempt 2 wrote 129 MB before it was stopped, so about 600 MB is
  proposed, which keeps the phase-wide bound under 1 GB of its 2 GB.
- **Approval in #218** (rule (d)). The round has a recorded start, so a further attempt is a
  repetition.
  - It may resume thread `01a21826-…`.
  - It may also open a new thread.
  - It counts against the three rounds the maintainer allowed for this correction.
