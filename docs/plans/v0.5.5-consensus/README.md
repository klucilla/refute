# Consensus record: v0.5.5 Core resolution

Codex's reviews under the maintainer's decision of 2026-11-20, 15:40, part 2 (#218). Codex ran
read only (sandbox read-only), through `.cache/v04/tools/codex_affinity.ps1` on processors 8 to 31.
Every answer is stored here unchanged, with the model, the effort and the Codex CLI version. The
charter's decisions were delegated to the maintainer's advisor and to Codex; a divergence left
after three rounds is settled by the most conservative option, recorded here. Agents propose;
nothing here is a verdict on a claim.

## The check of the Fable plan's facts (item 2)

Codex's check of the factual claims of `docs/plans/v0.5.5-fable-core-plan.md` (sections 1 to 3, the 14 points of section 8, and the finding of `c1.py:77-80` with `c1.py:366`): each claim accepted, accepted with a caveat, or rejected with its reason (the maintainer's decision of 2026-11-20, 15:40, part 2, item 2). One round: a check of facts, not a design. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [facts-round-1-answer.md](facts-round-1-answer.md) | gpt-6.1-sol, high | a check, not a verdict on a design: most claims ACEITO or ACEITO COM RESSALVA; REJEITADO: the Gaussian-prior range 4.6 to 14.1, an absolute INCONCLUSIVE cap of 0.10, the odd/even arithmetic as a rigorous lemma, two strict D2 floors of 8 and 11, T3b's frame growing only by new FP dispositions; the central caveat holds (no stellar precision is enough only at alpha = 0.0027) | `26f2751b7b475da55c19ca04db5185245c9836b29e07154a59b54e8aa9555f7c` |

The tokens are cumulative over the conversation `facts`:

- round 1: 1,658,446 input (1,509,632 cached) and 19,941 output;

The conversation counts **168,755** review tokens (the last round's uncached input plus output).

The accepted points that ask for a correction of an existing record are applied as a new record, `docs/validation/v0.5.4/pause-record-corrections.md`, with Codex's corrected texts; the old records keep their bytes.

## The charter (R0), the designs of the four checks (R1) and their code

Codex's review of the charter's five decisions (the maintainer's advisor's, delegated: items 4a to 4e), C1 version 2, the designs of D2-F, D1-P, T2a-E and T3b's recount with their code, the corrections record and the ROADMAP's opening of v0.5.5 (the maintainer's decision of 2026-11-20, 15:40, part 2, items 3 to 5), up to 3 rounds. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [r0r1-round-1-answer.md](r0r1-round-1-answer.md) | gpt-6.1-sol, high | 1a, 1c, 1e `SURVIVED`; 1b, 1d, 2 `WEAKENED`; D2-F `REFUTED` (certificate failures are not retention losses; RULE_3's mean); D1-P `REFUTED` (calibration not established; three fits; fatal price not measured); T2a-E, T3b `WEAKENED`; common `REFUTED` (pause_at None, no resume counter, the resume's cap, incomplete identity); 4 `WEAKENED`; 20 corrections | `b1c7a07fe7402a46eb372bc3deefd291ac536d334185ac1b89962e0e6ee32071` |
| 2 | [r0r1-round-2-answer.md](r0r1-round-2-answer.md) | gpt-6.1-sol, high | 1a, 1c, 1d, 1e, 2, T3b, 4 `SURVIVED`; 1b, D2-F, D1-P, T2a-E `WEAKENED`; common `REFUTED` (identity compared without the source hash; the real lock in the tests; preparation outside the run's lock); pinned_hash `WEAKENED`; 10 corrections | `ad95f8c179433a2a927fc80fcd78d73518d61ef6581b03cb8d7e29a26125f5c7` |
| 3 | [r0r1-round-3-answer.md](r0r1-round-3-answer.md) | gpt-6.1-sol, high | every item `SURVIVED`; no remaining blocker to the freeze; three wording adjustments, applied | `d5555c8fbdd4291dfff0d2b8dab07bd90c892fe728a3553fa4c342cb60a9a284` |

The tokens are cumulative over the conversation `r0r1`:

- round 1: 2,591,696 input (2,414,336 cached) and 17,009 output;
- round 2: 6,563,995 input (6,281,856 cached) and 29,792 output;
- round 3: 9,802,651 input (9,444,736 cached) and 37,122 output;

The conversation counts **395,037** review tokens (the last round's uncached input plus output).

Applied as Codex wrote them, with the conservative option wherever one was offered (no divergence left after round 3):
- **D2-F** has no "closed" outcome; its counts are diagnostics, not demonstrated lower bounds on unavoidable retention losses; RULE_3 uses the box's GLS projection of a normalized transit approximation.
- **D1-P** is an oracle surrogate with a nominal score; planet-side calibration is not established; the fatal exit is reported as scenarios only; three fits.
- **C1 version 2** draws the star with no artificial truncation; its use is serial.
- **T2a-E** compares each replay with I1's historical record; its chi-square inflation is heuristic; `pinned_hash.py` locates the earlier records under commit 8653911's code hash (the manifest checked file by file, two locks admitted) and never wraps the replay.
- **The common code:** pause_at is never None; R1 uses at most 10 workers at every hour; one lock covers the whole run; every start is recorded, one beyond the first being the pre-approved resume; the cap is cumulative over the identity; the complete code identity is compared between stages.
- **The ROADMAP** keeps the historical sentence with a pointer only.

## The night decision: I4's diagnosis, D2-F's redesign, amendment 1 and the fixes

Codex's review of the work of the maintainer's decision of 2026-11-20 (night) on the independent review (#218, comment 7050514004): I4's convergence diagnosis (item 3a), D2-F's redesign and its decision-value test (3b, 3c), amendment 1 to the charter (item 2), D1-P's and T2a-E's fixes (4a, 4b), the code's fixes (4c), the offline tests (4d) and the designs' revision, up to 3 rounds. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [night-round-1-answer.md](night-round-1-answer.md) | gpt-6.1-sol, high | I4, 3a, 3b, 3e, 3f, T2a-E `SURVIVED`; D2-F, 3c, 3d, D1-P, tests, revision `WEAKENED`; D2-F's plausibility reading and the code `REFUTED` (a race in the stale lock's recovery; partial coverage accepted by `d1p_exit_outcome`); 11 corrections | `73b178edf9516b663943ea83b0435135fceb805e55f338a2ebc8d8dbdd598ee9` |
| 2 | [night-round-2-answer.md](night-round-2-answer.md) | gpt-6.1-sol, high | every item `SURVIVED` but the revision `WEAKENED` (the bridge summary's cost); no blocker to D1-P or T2a-E; two wording corrections, applied | `a26be6db25ec56e1f6998b61ccfc719df0d20f6f44595adab202327e470a046e` |

The tokens are cumulative over the conversation `night`:

- round 1: 2,482,266 input (2,318,208 cached) and 15,163 output;
- round 2: 3,752,100 input (3,548,800 cached) and 20,234 output;

The conversation counts **223,534** review tokens (the last round's uncached input plus output).

Applied as Codex wrote them, with the conservative option wherever one was offered (no divergence left after round 2):
- **D2-F does not run.** It was not shown that "route" is implausible under the charter (about 0.11, a conditional predictive estimate, not an upper bound for generator version 2); D2-F stays unrun while the justification of its decision value and the funding of its two stages are not resolved, and this stop is not a conclusion on D2's feasibility. The decision is the maintainer's.
- **The lock:** acquisition, release and recovery under an operating-system guard; a recovered lock's identity is checked again just before its removal, recorded after it; a release removes only its own instance; files opened in binary mode.
- **D1-P:** the eight cells (two views, sets A and B, EB1 and EB2) are required, and incomplete coverage is INCONCLUSIVE; the bridge compares the same 100 indices under version 1 and version 2 side by side.
- **The texts:** the decision-value figures rectified as conditional estimates (the record kept as written); the provenance disclosures; the amendment's joint ceilings and qualified directions; the bridge summary's cost (three blocks, about 432 CPU-s).

## The 21:00 decision: T2a-E's completion with a fixed cap, D2-F's reason, the projection's lesson

Codex's review of the maintainer's decision of 2026-11-20 (21:00) on R1's stop (#218, comment 7053729723): the fixed-cap runner for T2a-E's stage-1 completion and stage 2 (items 1 and 3), and the maintainer's advisor's reason for not running D2-F (item 2), up to 3 rounds. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [g1-round-1-answer.md](g1-round-1-answer.md) | gpt-6.1-sol, high | the runner `REFUTED` (the crash charge can pass the allocation; no operational identity before the dispatch; no accounted completion before the assembly); 1c `SURVIVED`; 1b, 1d, 1e, 1f `WEAKENED`; D2-F's reason `REFUTED` (0.114 is a conditional estimate, not a ceiling; route allows up to 14 per set and 18 pooled, not 9 per set); Codex held that D2-F set A should run | `c0607bbba186fbcb368cfc46eed1c937dda5c1201a35b7cce3567907c86aec37` |
| 2 | [g1-round-2-answer.md](g1-round-2-answer.md) | gpt-6.1-sol, high | 1b, 1c `SURVIVED`; 1a, 1d, 1e, 1f `WEAKENED`; D2-F not run `WEAKENED`: it survives now by insufficient authorized funding (at most 12.9 CPU-h of cap from 14.2 against 13.52 needed) and a pending adapter, not by the decision-value rule; Codex withdrew its round-1 position on running set A | `330a10329bfd123259b3c19f864e5f068a75d1ec303c89c4365c0578d63e8888` |
| 3 | [g1-round-3-answer.md](g1-round-3-answer.md) | gpt-6.1-sol, high | 1a, 1b, 1c `SURVIVED`; 1d `REFUTED` (an old summary charge can be taken as proof of a recovered attempt's charge; the wrapper is not charged on an exception); 1e, 1f `WEAKENED` (stage 2's margin checked against the protected cap, not the effective one); D2-F not run `SURVIVED` with the agreed text; **the runner is not released after the three rounds** | `d5a071abf824510c4d1d68069c0860df1b180705f4643ac177bb035e635ab943` |

The tokens are cumulative over the conversation `g1`:

- round 1: 742,962 input (623,104 cached) and 11,109 output;
- round 2: 1,326,484 input (1,178,368 cached) and 20,727 output;
- round 3: 1,862,171 input (1,691,648 cached) and 27,973 output;

The conversation counts **198,496** review tokens (the last round's uncached input plus output).

Settled by the most conservative option at the end of round 3 (the maintainer's rule):
- **T2a-E's completion and stage 2 do not run.** The runner (`docs/validation/v0.5.5/r1_fixed_cap.py`) stays unreleased: pending are the proof that a recovered summary's charge belongs to that attempt, the wrapper's charge on an exception, and stage 2's margin against the effective cap. Stage 1's stop at its cap stays on file, with every consumption recorded.
- **D2-F is not run**, recorded as "D2-F not run: authorized funding insufficient; fixed-cap adapter pending", with Codex's text: no demonstrated implausibility of route under the rule (e)1, no infeasibility conclusion on D2.
- The maintainer's advisor's reason for D2-F (0.114 as a ceiling; at most 9 per set) was refuted on its facts; the not-run outcome stands on the funding.
