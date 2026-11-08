# v0.5.2 consensus: Codex's answers

The maintainer's decision of 2026-11-08 (#208; `docs/plans/v0.5.1-plan.md`, amendment 11): the scope
of v0.5.2 by consensus with Codex, with a stop before any code. Codex ran read-only (sandbox
`read-only`, logical processors 8 to 31, through `.cache/v04/tools/codex_affinity.ps1`), on
2026-11-08. Its answers are kept here unchanged; the prompts stay local because they name a private
folder the session was told not to open.

The answer files hold Codex's text only. The tables below give, for each answer, the model and the
effort used; the Codex CLI version of every answer is `codex-cli 0.167.0-alpha.3.2`.

## The scope

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [scope-round-1-answer.md](scope-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (14 objections) | `51c824bb197a43d4a4da55f76b1ec0b7ec52a65d43f5c040edda6172cc7768a1` |
| 2 | [scope-round-2-answer.md](scope-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (6 objections) | `91c00eab42041deceaa1875d60b57d63aeb31e0d69409160c028e8188d73e0e4` |
| 3 | [scope-round-3-answer.md](scope-round-3-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `3a93ba3bd9b045caf4e63059cbc456510f955b39bc34e858b96c568488c0c4b1` |

Every objection was accepted and applied in [../v0.5.2-scope-proposal.md](../v0.5.2-scope-proposal.md).
No divergence remained.

## The stage 1 experiment designs

Reviews of each frozen design, before it ran (`docs/validation/v0.5.2/stage1/`).

| Design | Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|---|
| E1 | 1 | [e1-design-round-1-answer.md](e1-design-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` | `2510115be7fb085e18ef6c0696f376ff2175d9dc8b936123acd152a27ec11784` |
| E1 | 2 | [e1-design-round-2-answer.md](e1-design-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` | `a01e28c19a96d6f1e8e1a934822e3d115335b5b24e6c592a5d1d1432f0b08f7c` |
| E1 | 3 | [e1-design-round-3-answer.md](e1-design-round-3-answer.md) | gpt-6.1-sol, high | `SURVIVED` | `27ea228e63420f526cb46fc303c9ea93bcebbe6ce6728ae268cff4c057113dc2` |
| E3 | 1 | [e3-design-round-1-answer.md](e3-design-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` | `ce47b54e5c30763cbc5c0717b264abe28ac7a04bfdcab3f59270678326a47b4c` |
| E3 | 2 | [e3-design-round-2-answer.md](e3-design-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` | `34ca298261a2713451fccb177ed5b62248c63dea05c69b6992cd1a2e6db69e11` |
| E3 | 3 | [e3-design-round-3-answer.md](e3-design-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` | `ade9984a4033fc31041ff9bff74c945186f3de5019f2d02551172aa385210713` |
| E2 | 1 | [e2-design-round-1-answer.md](e2-design-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` | `7023e978e38b72a05eed84e4d5c716d629d1a7139ac7b64aebdc0d34feb31199` |
| E2 | 2 | [e2-design-round-2-answer.md](e2-design-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` | `c58822197158ec6e7e8bf5d166e33b90a93b3ac37aa51d402e43f35623d35032` |
| E2 | 3 | [e2-design-round-3-answer.md](e2-design-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` | `8409069c0726abf18851e22dcc72f83f5787039de6a5afa268aa239fd4313149` |

E3 and E2 ended their three rounds in `WEAKENED`. One divergence stayed open after the three rounds
(E3 round 3, objection 3; E2 round 2, objection 3): Codex asks for live termination of workers at the
cap, and these experiments enforce the cap per batch. It goes to the maintainer with both arguments, in
[the stage 1 report](../../validation/v0.5.2/stage1/README.md).

## The stage 1 report

The review of [the stage 1 report](../../validation/v0.5.2/stage1/README.md) before the stop, and Codex's
judgements on the T3b population and the D1 margin (round 1).

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [stage1-report-round-1-answer.md](stage1-report-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (9 objections) | `e52cb1e69997d12ae394221a9ca20d9ac4c70ee6b8f80a8d59cc609214dae339` |
| 2 | [stage1-report-round-2-answer.md](stage1-report-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (4 objections) | `639b2f94cd96af0262be1eb17c486a286f66324642dcbc10757074b947d85da4` |
| 3 | [stage1-report-round-3-answer.md](stage1-report-round-3-answer.md) | gpt-6.1-sol, high | `WEAKENED` (1 objection, LOW) | `7dd4f33d769754e5cf79d06705eff7511735d502524be9e7ffa4e735f24385d3` |

Round 3's single low-severity objection (the label of one sensitivity) was applied as it asked; no fourth
round ran. The conversation holds one more turn than the three rounds: a first launch of round 2 was stopped
within seconds, because the rewritten report had not yet been saved; it produced no answer.

## The stage 2 design

Reviews of [the stage 2 design](../v0.5.2-stage2-design.md), under the maintainer's delegation of 2026-11-08 (#216).

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [stage2-design-round-1-answer.md](stage2-design-round-1-answer.md) | gpt-6.1-sol, high | `REFUTED` | `d71bfa417472487672ee44bb67362087240ef37096354e46221af74c071d4d62` |
| 2 | [stage2-design-round-2-answer.md](stage2-design-round-2-answer.md) | gpt-6.1-sol, high | `REFUTED` | `9b475913068e1f8c8ba301df35ceda9411caeca85acff210075e1b06ef6566af` |
| 3 | [stage2-design-round-3-answer.md](stage2-design-round-3-answer.md) | gpt-6.1-sol, high | `REFUTED` | `56d5c6e0bcd8759900004746b30661d0d05e80973ee936ce5b48c2d0657c4a02` |

**The tie-break, applied.** After three rounds Codex's verdict stayed `REFUTED`. By the maintainer's rule the option more conservative against a false PASS
wins, with both arguments recorded, and the work goes on without a stop. Round 3 accepted the four points on which Claude had not taken round 2's correction as
written (sizing before the code with a frozen adequacy check; batches never interrupted; the sinusoid rule; `J` = 4) and raised six defects. Every one was adopted as Codex wrote it:

| Round 3's defect | Claude's position before | Adopted |
|---|---|---|
| The adequacy check could pass a configuration that cannot deliver `G_min`; 300 curves cannot see a one-in-524 pull | a cheap check (300 curves per noise model, thresholds on availability and on the pooled fourth moment) | the whole A0 round 2 schedule on version 4 development seeds, the complete evaluation repeated with the schedule frozen; pooled moments diagnostic only |
| The tail sensitivity mixed location, scale and tail, and inferred that a larger `T` buys little | an unadjusted perturbation | relabelled, restandardized variant added, the inference removed; the extreme curve stays |
| The selector's rule could grant permission without equivalence | point estimates inside, intervals intersecting | default INCONCLUSIVE; only simultaneous intervals wholly inside, as its own family; the same for a sabotage's accepted baseline |
| The aggregate checks were pooled by section | one aggregate per section | section x statistic x noise model |
| CPU charges could be incomplete after a crash or failed queries | the last value kept; a fixed 20-second surcharge | a failed query stops dispatch and charges elapsed time for every worker; restart refused while a worker lives; a crashed batch charged a whole shard per worker; workers end with their controller |
| A stop did not bind the evaluator | a state returned | `stop.json`: no continuation and no bytes until a reason is recorded; the evaluator needs a completed run |
