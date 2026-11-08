# v0.5.2 scope consensus: Codex's answers

The maintainer's decision of 2026-11-08 (#208; `docs/plans/v0.5.1-plan.md`, amendment 11): the scope
of v0.5.2 by consensus with Codex, with a stop before any code. Codex ran read-only (sandbox
`read-only`, logical processors 8 to 31, through `.cache/v04/tools/codex_affinity.ps1`), in one
conversation on 2026-11-08. Its answers are kept here unchanged; the prompts stay local because they
name a private folder the session was told not to open.

Each answer lists the model, the effort and the Codex CLI version used: `codex-cli 0.167.0-alpha.3.2`.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [scope-round-1-answer.md](scope-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (14 objections) | `51c824bb197a43d4a4da55f76b1ec0b7ec52a65d43f5c040edda6172cc7768a1` |
| 2 | [scope-round-2-answer.md](scope-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (6 objections) | `91c00eab42041deceaa1875d60b57d63aeb31e0d69409160c028e8188d73e0e4` |
| 3 | [scope-round-3-answer.md](scope-round-3-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `3a93ba3bd9b045caf4e63059cbc456510f955b39bc34e858b96c568488c0c4b1` |

Every objection was accepted and applied in [../v0.5.2-scope-proposal.md](../v0.5.2-scope-proposal.md).
No divergence remained.
