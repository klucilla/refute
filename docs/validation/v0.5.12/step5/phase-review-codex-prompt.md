Same rules as before in this thread (read-only, no network, never any path on the K: drive, no run of any test, measurement or phase unit). This is a NEW closed question: the one review of all of v0.5.12's commits (the charter `docs/plans/v0.5.12-charter.md`, step 5: "One Codex review of all the phase's commits"). One round.

**The range:** from the charter's approval commit `7df389c` to HEAD (`git log --oneline 7df389c..HEAD`). The phase's records are under `docs/validation/v0.5.12/`, `docs/plans/v0.5.12-*` and `docs/reports/v0.5.12-report.md`; its journal is `docs/validation/v0.5.12/log.jsonl`, its ledger `caps-ledger.json`, its gaps `meter-gaps.json`, and its errata `errata.md`.

**What the maintainer decided (recorded in #218; the commit messages cite each comment):**
- the order of step 2 and step 4: the inventory, the case record and the probe, then both suites pushed before `src/`, then the single `src/` commit `6f83a91`, which is the exact approved diff `step4/src-diff-proposed-2.patch`;
- M2 and the sensitivity control after `src/`, on frozen inputs;
- the "after" proofs;
- F-1 within its cap.

## The one question
Do the phase's commits respect the charter, its amendment 1 (`docs/plans/v0.5.12-charter-amendment-1.md`), and the order above? In particular:
- (a) `src/` changes only at `6f83a91`, only version 5's F1, equal to the reviewed patch;
- (b) no version 1 to 4 output, lock, claim, dependency (`pyproject.toml`, `uv.lock`) or anchored record changed;
- (c) every recorded result that the phase gives was produced after its inputs, plan or case record were committed;
- (d) every deviation and gap visible in the history is recorded in `docs/reports/v0.5.12-report.md` or `meter-gaps.json`.

Check with path:line or commit evidence. A new finding outside this question is a recorded item.

## Answer (English, at most about 45 lines)
- OVERALL: SURVIVED / WEAKENED / REFUTED for sealing the phase's criteria 1 to 6.
- (a) to (d): holds / does not hold, each with its evidence, and the exact fix if it does not.
- Recorded items, if any.
