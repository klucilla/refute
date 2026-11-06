# v0.5.1 scope consensus: Codex's answers

The maintainer delegated, on 2026-11-06, the scope of v0.5.1 Battery corrections to a consensus
between Claude and Codex, within one direction: correct the targets that failed in v0.5 without
losing the ones that passed. Codex ran read-only (sandbox `read-only`, logical processors 8 to 31,
through `.cache/v04/tools/codex_affinity.ps1`) on the drafts of
[../v0.5.1-plan.md](../v0.5.1-plan.md) in three rounds of one conversation on 2026-11-06. Its
answers are kept here unchanged; the prompts stay local because they name a private folder the
session was told not to open.

| Round | Time (UTC) | What Codex reviewed | Verdict | File | SHA-256 |
|---|---|---|---|---|---|
| 1 | 13:15 to 13:24 | the first draft | `WEAKENED` (8 objections) | [round-1-answer.md](round-1-answer.md) | `e2a5d6a02a501a6c85e716c1a000b1d01521bcbb2577aef1462afc27eea501b4` |
| 2 | 13:27 to 13:33 | the plan with the round-1 changes | `WEAKENED` (6 objections) | [round-2-answer.md](round-2-answer.md) | `0eaea60624c2653e36bee63d109442e24162dfc225ca5c994cd690584cad8c7e` |
| 3 | 13:35 to 13:39 | the plan with the round-2 changes | `SURVIVED`; scope adopted | [round-3-answer.md](round-3-answer.md) | `c1de4c984fa16b915fc47663a134ad6333a7786063b2198e9e4a619954f96a39` |

How each objection was handled: the consensus record at the end of the plan. No disagreement
remained, so nothing went to the maintainer.

The numbers of the plan's section 2 come from
[../v0.5.1-wp0/diagnose_v05_records.py](../v0.5.1-wp0/diagnose_v05_records.py) (its output:
[../v0.5.1-wp0/diagnosis.json](../v0.5.1-wp0/diagnosis.json)), run on the v0.5 records, which this
phase uses for development only.
