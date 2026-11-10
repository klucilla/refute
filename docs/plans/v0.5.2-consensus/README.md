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

**Codex's token use (the maintainer's decision of 2026-11-09, #216).** Codex's tokens do not count against stage 2's review limit. From that date each table below gives the use per round when the CLI reports it. The five calls of stage 2 before that date, together: 928,026 input tokens not cached, 121,922 output, 19.5 M cached.

## T3b's population

The maintainer's item 3 of 2026-11-09 (#216). Counts only; no definition is adopted.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [t3b-frame-round-1-answer.md](t3b-frame-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (6 findings) | `bbde9eb4e37f9242053102360d6eff983db3e97e7fcba11b15aaea5d33a02d32` |

| 2 | [t3b-frame-round-2-answer.md](t3b-frame-round-2-answer.md) | gpt-6.1-sol, high | `WEAKENED` (6 findings) | `94c3b494fe84a460a737a0ab510705356ca80876e34096bd38170c0cb281fadb` |

Round 1 used 913,557 input tokens (817,920 cached) and 14,759 output tokens; round 2, 2,783,950 (2,625,024 cached) and 31,750. The findings of both rounds were applied, and the status for the protocol stop is [`t3b-status.md`](../../validation/v0.5.2/stage2/t3b-status.md). No definition was adopted.

Round 3 answers the maintainer's item 3 dated 2026-11-09 (#216): why the first proxy rejected 4 of the 11 accepted stars, its correction, and the recommendation among A, B and C. Codex CLI 0.167.0-alpha.3.2.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 3 | [t3b-frame-round-3-answer.md](t3b-frame-round-3-answer.md) | gpt-6.1-sol, high | `SURVIVED` as a counts-only planning proxy; recommendation among A, B, C: none as written (5 findings) | `2a24e0dca486a2ce8e44fa5fec9caca2f67e8b05c9b2c5585803f180d5ff0bd0` |

Round 3 used 5,349,921 input tokens (4,967,424 cached) and 48,021 output tokens (24,940 of them reasoning). Its five findings are disclosures, applied in `t3b-alternatives-r2.json` (`proxy.limits`) and in `t3b-status.md`. Claude agrees with its recommendation: none of A, B or C as written.

## The stage 2 implementation

The end-of-round review of the first version 4 commits (`569d127`, `94eec96`, `d94bef3`), which checks the code against the agreed design.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [stage2-impl-round-1-answer.md](stage2-impl-round-1-answer.md) | gpt-6.1-sol, high | `REFUTED` (11 findings) | `95ffd933e32a0ab6c08b99f8ecca1ab0d7358e4f50314d7b62f401ae4bd5626b` |
| 2 | [stage2-impl-round-2-answer.md](stage2-impl-round-2-answer.md) | gpt-6.1-sol, high | `REFUTED` (2 findings, and a judgement on a failed row) | `064c962753390af52f4285ffdd4a5dcbbf9b9879ad2a1afa6548a143b4e12798` |

| 3 | [stage2-impl-round-3-answer.md](stage2-impl-round-3-answer.md) | gpt-6.1-sol, high | `REFUTED` (6 findings) | `c1125e64138a74165afd262410d17f16a03cb37380296ab0a27050e0b01ecb93` |
| 4 | [stage2-impl-round-4-answer.md](stage2-impl-round-4-answer.md) | gpt-6.1-sol, high | `REFUTED` (7 findings) | `6a3e08e5d8308b681375d5aba423ba8c5e09eae42703b330871ade9f04c68898` |
| 5 | [stage2-impl-round-5-answer.md](stage2-impl-round-5-answer.md) | gpt-6.1-sol, high | `REFUTED` (7 findings) | `f34b94ba4094c3f42f24083ee966e755d99b68abc620d16ca3025d481b8bea8a` |

Round 5 is the end-of-round review of `28a8258` to `ac39ffc`; it used 16,126,126 input tokens (15,134,848 cached) and 73,930 output tokens (43,119 of them reasoning). Applied: every stop the driver issues now binds in the ledger, a pause stays resumable (1, with a test; a test that passed only through the hole was corrected); the two worker probes are charged in the ledger at their measured CPU, 8.1 CPU-h, a lower bound, and the probe keeps one folder per configuration (2); the forecast's shard limit sits inside the batch (3); D2 and D4 use the frozen rules, with the Wilson bound and NOT DECIDABLE below the floor (4); the T2a sector reading uses v0.5's C2 fetch record on T2a's own denominator (6); a family member no curve carries stops the sizing (7). Finding 5 is applied in part: the measured T2a forecast needs the C2 hosts' light curves again, by their recorded URLs and SHA-256, and is planned after the maintainer's decision on the redesign; the sector reading already bounds T2a without a certified selector.

## The advisor (an opinion only)

The maintainer's decision of 2026-11-10 (#216, item 4) approves at most three consultations of the advisor in this round, as an opinion only (it replaces neither Codex nor any decision), on the acceptance's sizing, T2a's margin and the rule above 20 sectors; read only, no confirmation data. The advisor is a tool of the Claude Code session that sees the whole conversation; it does not report its model, and the maintainer calls it "fable" (Claude Fable 5.1). **Round 1 ran on 2026-11-10 before that approval** (a slip, disclosed on #216): it reviewed the redesign stop. It is counted as one of the three, so two remain.

| Round | Date | File | Model | Topic | SHA-256 |
|---|---|---|---|---|---|
| 1 | 2026-11-10 | [advisor-round-1-answer.md](advisor-round-1-answer.md) | advisor tool ("fable", per the maintainer) | the redesign stop: planning margin, agent-days, T2a's ceiling | `4c8f43ea3cf85c717c26c45c33d02c971c8a119382826d13c1079097de3924e0` |

Applied from round 1: the 30 % margin stated honestly (`c4b29f1`), agent-days measured, `choose_sectors` read (every sector of the light curve, so the T2a ceiling holds approximately), the forecast offered to the maintainer.

## The adequacy redesign

After the failed adequacy check (`c1e717e`), the maintainer's decision dated 2026-11-09 (#216, item 1): a prospective redesign of the sizing through this consensus, loosening nothing, sized cell by cell from version 4's availability, repriced before launch, and a STOP if the total projection passes 3,100 CPU-h. Codex CLI 0.167.0-alpha.3.2, in the stage 2 design conversation.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [adequacy-redesign-round-1-answer.md](adequacy-redesign-round-1-answer.md) | gpt-6.1-sol, high | `WEAKENED` (8 findings) | `74a06eb44aab9a454287dd848817e0283717cef7c5e383fb4631bc589fe00dc1` |

Round 1 used 8,877,523 input tokens (8,278,912 cached) and 56,006 output tokens (36,308 of them reasoning). Applied: exact integer sizing; the run-by-run rule recorded as equal to the component rule because every component of this table holds one run; the per-member 95 % lower bound as the planning rule, with the whole-family check unchanged and no claim of simultaneous delivery; the targeted A0.8 event pilot priced; the diagnosis's wording corrected (expected contributors below `G_min`, not "every dataset"). Agreed: a fresh out-of-sample check on a frozen manifest of absolute run sizes, new curve and draw labels; an in-sample check stays diagnostic. Every option with a margin passes 3,100 CPU-h once the known-answer gate is rescaled with the schedule (`sizing-v4.json`), so the maintainer's condition (b) applies: a STOP before launch, with the options.

Round 4, a narrow review before the first long run (11,433,335 input tokens, 10,948,736 cached; 57,970 output): every finding was applied; a failed adequacy gate persists and blocks later work; the rebuilt reference is verified by bytes in each worker; the constructions are shuffled into the shards so that the first 5 % is representative, weighted by units; every part is declared before dispatch; the cap follows the frozen projection; a stop binds across code changes until reconciled; the total is checked after the last batch.

Round 3, the end-of-round review, used 8,816,615 input tokens (8,368,256 cached) and 42,499 output tokens; every finding was accepted and applied: the noise-free truth of A0.8 goes through the production preprocessing again (the shortcut changed which windows are measurable, so A0 is repriced); reuse keeps a fresh run's batches and widths, with a byte test of the real series and all four combs; each budget line runs through `budgeted.py`, with a persisted first-5 % checkpoint and a ledger read before each batch; a run that passes its cap at the end binds; the comb reference check has a budget line; the deletion guard refuses parent traversal and checks the resolved path.

In round 1, every finding was accepted and applied: the final upper clip and poorly conditioned windows now go to the reference; the time is rescaled per knot; the global refit runs inside the preprocessing; the real mask follows the final ephemeris
through one construction shared with the runner; the sectors are chosen before any event is measured and recorded; the grid holds for the additive statistics; the dumps sub-check sees every sector; the sinusoid's sensitivity is zero where the rule cannot FAIL; the
compatibility claim was narrowed and its record widened; the comparator no longer absorbs non-finite values; and the equivalence was re-frozen with the omitted paths and run again.

Round 2 judged a failed row of the equivalence evaluation (a tied epoch label): changing the code under the unchanged criterion is valid under stated conditions, changing the criterion inadmissible, and the failure stands for the code it measured. Both findings were applied; its conditions are in `fast-detrend-equivalence.md`, revision 3.

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
