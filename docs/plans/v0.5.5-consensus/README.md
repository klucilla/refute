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

## Path A at G1: the fixed-cap runner's three pending items

Codex's review of the fixed-cap runner after the three pending items of the g1 conversation's round 3 were applied in his text (the maintainer's decisions of 2026-11-21 at G1, item 1; #218): the closing receipt, the wrapper's charge in finally, stage 2's margin against the effective cap, and round 3's tests 4 to 6 (commit 09e729b), up to 3 rounds. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [g1r-round-1-answer.md](g1r-round-1-answer.md) | gpt-6.1-sol, high | items 1 to 5 `SURVIVED`; no blocker; **the runner is released** for T2a-E's completion (`r1_t2ae_1c`, 14 injections, 1.5 CPU-h, 3 workers) and, after a valid stage-1 publication, no futility and the effective margin with the 51 measured costs, for stage 2 (`r1_t2ae_2`, 51 injections, 3.1 CPU-h, 4 workers); reviewed SHA-256 `7f125394cc5898941d508c5d1fcc3119e31ee1bf6aba02e10a1385756bd65769`; two optional test improvements, applied | `c635d7e8166a12c016ed66117665c110d1809d24e243120e20f68f2ba9f598b2` |

The tokens are cumulative over the conversation `g1r`:

- round 1: 616,815 input (531,328 cached) and 6,626 output;

The conversation counts **92,113** review tokens (the last round's uncached input plus output).

Applied as Codex wrote them (no divergence; one round):
- **The runner is released** at the reviewed bytes (SHA-256 `7f125394...5769`); its bytes stay unchanged from the first dispatch on, comments and docstring included.
- The two optional test improvements (the interruption with the attempt persisted before a correct JSON; the wrapper's deduction checked exactly with a deterministic process clock, and exactly zero when the inner charge is larger) are applied in `tests/v055/test_r1_fixed_cap.py`; the runner is unchanged by them.
- The release does not certify future operating conditions nor pass any STOP.

## Path A at G1: D2-F's fixed-cap adapter

Codex's review of the fixed-cap adapter for D2-F's set A (`docs/validation/v0.5.5/d2f_fixed_cap.py`; the maintainer's decisions of 2026-11-21 at G1, item 2; #218): no budgeted_v3, the T2a-E runner's protections, the funding of 14.2 CPU-h from D1-P set B and 2.1 from the reserve (16.3 CPU-h, 4 workers), up to 3 rounds. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [d2fa-round-1-answer.md](d2fa-round-1-answer.md) | gpt-6.1-sol, high | 1, 3, 5 `SURVIVED`; 2 `REFUTED` (the receipt was saved before the wrapper's charge, with no operational closing after it); 4, 6 `WEAKENED` (the funding in two writes; the claim about `lv.declare()`'s callers incorrect; no test of a failed wrapper charge); **not released** | `3ba37f09e5303d2331b72146faac40a119bd6bdf7620936e4a7e2657691dcb00` |
| 2 | [d2fa-round-2-answer.md](d2fa-round-2-answer.md) | gpt-6.1-sol, high | items 1 to 5 `SURVIVED`; no blocker; **the adapter is released** for set A at its reviewed bytes (SHA-256 `7b980a25685df9f4b0e632b61786a598db061acda289d4f653670cbd342cd374`), 16.3 CPU-h, 4 workers, 1,200 s per shard; one optional test, applied; D2-F not dispatched in this session (the stop at G1) | `757bcdc5ab8511b045ff01d63c268a76eaf393dd765f9972d6178925100cbcce` |

The tokens are cumulative over the conversation `d2fa`:

- round 1: 823,060 input (722,176 cached) and 9,352 output;
- round 2: 1,218,355 input (1,097,728 cached) and 12,657 output;

The conversation counts **133,284** review tokens (the last round's uncached input plus output).

Applied as Codex wrote them (no divergence; two rounds):
- Round 1's corrections (commit `ab5e7e7`): the operational closing `d2f-A-closing.json`, written once only after the wrapper's charge, bound to the record, the attempt, the identity, the receipt and the wrapper's charge, with the state `final` or `stopped`; `check_closed` and the `accept` command require `final`; the funding in one atomic write; the corrected docstring on `lv.declare()`'s callers; the tests asked.
- Round 2's optional test (the wrapper's charge persisted, then the charges' room STOP: no closing, `accept` refuses) is applied; the adapter is unchanged by it.
- **The adapter is released at its reviewed bytes, which stay unchanged from the first dispatch on. D2-F was not dispatched**: T2a-E's stage 2 was refused by its margin before D2-F's turn, a request for money beyond the authorized, and the decisions' item 6 stops at G1 on such a request. The release is kept for the maintainer's decision.

## Path A2 at G1: the ledger step that raises T2a-E stage 2's allocation

Codex's review of `docs/validation/v0.5.5/r1_allocation_step.py` (the maintainer's decisions of 2026-11-21, 10:00, at G1, item 1; #218): part `r1_t2ae_2` from 3.1 to 3.55 CPU-h, 0.45 from the reserve, before its first start, in one atomic write, up to 3 rounds. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [t2s-round-1-answer.md](t2s-round-1-answer.md) | gpt-6.1-sol, high | 2, 3, 5 `SURVIVED`; 1, 4 `WEAKENED` (a repeated call checked only that a record existed and the target was 3.55; a reserve restored by mistake passed); **not released** | `a0e00ee03095d653919ac7d9527bead82d4161546c12639686f0ad6f208b4604` |
| 2 | [t2s-round-2-answer.md](t2s-round-2-answer.md) | gpt-6.1-sol, high | items 1 to 4 `SURVIVED`; no blocker; **the step is released** for the real ledger at its reviewed bytes (SHA-256 `4dd68bdfac2cf6bdee600a776a2707b2a71455794aafdc8c63cf977584702d72`); two optional improvements, one test applied | `24a5cc906d12f3c73e42f378aa2f5f86f237579d2318db61638378afcbcc4a1d` |

The tokens are cumulative over the conversation `t2s`:

- round 1: 523,649 input (451,200 cached) and 5,762 output;
- round 2: 913,652 input (829,568 cached) and 8,659 output;

The conversation counts **92,743** review tokens (the last round's uncached input plus output).

Applied as Codex wrote them (no divergence; two rounds):
- Round 1's correction (commit `9f3dc54`): the record holds the reserve before and after; a repeat writes nothing and requires exactly one record with the expected fields (no other top-level field), the reserve equal to the record's after less any later transfer that took from it, and both lines; any divergence is a STOP with no write. The procedure posted on #218 before the run carries the prohibition of `lv.declare()` and its callers, and the clarification that the slack does not get around a line restriction or a resume's cap, and that raising D2-F's 16.3 needs a new review of the adapter.
- Round 2's optional test (the later transfer as D2-F's funding really writes it, the sum of the allocations kept) is applied; the step is unchanged by it. Its other remark is recorded: "the main record's fields are exact; the later reconciliation uses the debits recorded by the authorized steps" (fields inside `reserve_hours` are not checked for extras).
- **The step was applied to the real ledger on 2026-11-21 at 13:22 UTC** (`r1_t2ae_2` 3.1 to 3.55; the reserve 20.3 to 19.85), after the procedure on #218.

## G1, third pass: the check of path B (R2 on paper) with T3b's preparation

Codex's one round on the maintainer's decisions of 2026-11-21 (13:30) at G1 (#218): path B, R2 on paper, with T3b's preparation beside it, checked against the plan's section 7, the charter (d) and amendment 1 (f); three rounds only if he held that a pause was mandatory. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [r2choice-round-1-answer.md](r2choice-round-1-answer.md) | gpt-6.1-sol, high | items 1 to 4 `SURVIVED`; **path B survives; a pause is not mandatory now**; the motivation corrected (a futile check is not a demonstrated floor); five operational corrections for the bundle and the lines, and four conditions for T3b's preparation | `5a4ed71b25f46bcd5c20944e10b271742c539a04f580daaf45da63f2d2263d72` |

The tokens are cumulative over the conversation `r2choice`:

- round 1: 472,810 input (402,560 cached) and 4,020 output;

The conversation counts **74,270** review tokens (the last round's uncached input plus output).

Applied as Codex wrote them (no divergence; one round):
- **The motivation, corrected** (his text): "R1 did not establish a route by its checks' frozen criteria. D2-F was futile and did not demonstrate a floor at D2's ceiling; T2a-E was empirically limited for the class examined. The prospective route stays open." The comparison of 14 against 13 is with D2-F's route threshold (which keeps room for the estimators), not D2's total ceiling of losses; the upper count includes unknowns, and neither count is shown to be unavoidable losses.
- **The bundle** carries no part of the questions draft (it cites results): the arguments document, cut at its disclosure section, carries the questions; amendment 1 (f) applies in full (allowlist, manifest before the review, no clone, history or network; a contaminated bundle voids the review).
- Both aggregations side by side for every future number of D2, D4 and T2a; the test suite's exception produces no number of the new version before the freeze; the two lines are counted without moving any cost incurred to get around a stop.
- **T3b's preparation:** the recount of the frozen frame kept apart from any updated frame; the frame, domain, threshold and readings fixed before the data they read (amendment 1 (e)10); each fact with its source, version and effective reading date; ExoFOP's data use unconfirmed where no applicable document is found. The preparation does not meet the standard of charter (c) and amendment 1 (e) by itself and closes nothing.

## R2 on paper: the arguments, the code semantics and the blind bundle's builder

Codex's review of R2's arguments document for logic and number leakage, of the code semantics and of the blind bundle's builder (the maintainer's decisions of 2026-11-21, 13:30, items 3 and 4; #218), up to 3 rounds. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [r2args-round-1-answer.md](r2args-round-1-answer.md) | gpt-6.1-sol, high | leakage, B1, dependencies and the builder `REFUTED`; B2, B3 and the operational proposals `WEAKENED`; retrospective references before the disclosure; B1 (e) not a mere preservation of evidence (Codex recommended (a) as primary); B2 over-stated; B3.3 a rule change to declare; the bundle lacking the code semantics; `check` leaving nested manifests out; **not ready** | `e5986c8689a3d610fb4150a9dccbb6c4ac16ec542507617a195510668b11c65a` |
| 2 | [r2args-round-2-answer.md](r2args-round-2-answer.md) | gpt-6.1-sol, high | items 1 to 5 `SURVIVED`; dependencies and the bundle `WEAKENED`; the builder `SURVIVED` static inspection; two blockers in the semantics (the emitted severities; the sinusoid's joint fit and certificate); **not ready** | `83d612d815eb9f378b5c5e41c995312cb6514d6e5e425f37e4e4381a2df979cb` |
| 3 | [r2args-round-3-answer.md](r2args-round-3-answer.md) | gpt-6.1-sol, high | every item `SURVIVED`; **no blocker; the arguments cut at the disclosure, the semantics and the builder are ready for the single build of the blind bundle**; three remarks (no build confirmed by Codex; the model-dependent alternatives stay conditional; the build uses the reviewed bytes) | `ce72a046b81818478b2b0fae2e8a9d3e5e053dc9e5f32412bb50470b40dd044a` |

The tokens are cumulative over the conversation `r2args`:

- round 1: 1,904,654 input (1,773,952 cached) and 14,925 output;
- round 2: 3,633,775 input (3,450,368 cached) and 23,217 output;
- round 3: 4,320,999 input (4,115,200 cached) and 25,866 output;

The conversation counts **231,665** review tokens (the last round's uncached input plus output).

Applied as Codex wrote them (the divergence on B1 settled by the conservative option in round 1: **B1's proposed primary is (a), the current rule**, with (e) registered beside it; B2's primary is (a); B3.2 keeps Fréchet without a derived and reviewed model):
- **The bundle was built once on 2026-11-21 at 17:05 UTC** from the reviewed bytes (commit `55e32fd`): 12 files (the arguments cut at the disclosure, the code semantics and ten source files of the frozen rules); the manifest `docs/validation/v0.5.5/r2-bundle-manifest.json` written before the files and before any review; `check` passed (12 files, the delivered manifest equal); the arguments' final bytes read in context (no disclosure section, no result). **No reviewer was launched**: the blind review is the maintainer's adviser's, read only.
- The arguments and the semantics are proposals and descriptions; nothing is decided, frozen or locked (R2's design decisions and the freezing are a stop that is not delegated).

## T3b: whether the TOI table's use for a count is confirmed

Codex's one-question check under the maintainer's decisions of 2026-11-21 (15:20), item 5 (#218): whether, by the recorded sources, the NASA Exoplanet Archive's TOI table (`tfopwg_disp`) may be used for T3b's count of an updated frame. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [r2t3b-round-1-answer.md](r2t3b-round-1-answer.md) | gpt-6.1-sol, high | **NOT CONFIRMED** for the count: the Archive's table is public but derives from ExoFOP's TOI list; whether `tfopwg_disp` is "data supplied by other users" stays open; what would settle it is the TFOP Working Group Publication Policy, or an explicit confirmation from TFOP or NExScI | `df853a16c9275914f055ee3e908052f3567e082cfd838286631c086895d88417` |

The tokens are cumulative over the conversation `r2t3b`:

- round 1: 126,059 input (105,728 cached) and 845 output;

The conversation counts **21,176** review tokens (the last round's uncached input plus output).

Applied (the conservative option of the decision):
- The TFOP Working Group Publication Policy (version 21, 12 July 2026) was then read through an extraction tool: nothing found on the dispositions or on public TOI data (not confirmed by a full human reading). The question stays **not confirmed**; an explicit confirmation from TFOP or NExScI is a human step, the maintainer's.
- **The updated frame's count did not run.** A draft of T3b's availability record was prepared instead (`docs/plans/v0.5.5-t3b-availability-record-DRAFT.md`), a draft only; the record is a stop that is not delegated.

## The first blind review of R2's bundle

The maintainer's decisions of 2026-11-21 (15:20), item 0 (#218): the blind review, round 1,
launched by the maintainer's adviser (one fresh session of Claude Fable 5.2, read only, only the
bundle's 12 files rebuilt from git at `55e32fd0` and checked against
`docs/validation/v0.5.5/r2-bundle-manifest.json`; 230,327 tokens, outside Codex's lines). Stored
unchanged; the received file's SHA-256 was checked before the commit.

| Round | File | Reviewer | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [r2-blind-review-1.md](r2-blind-review-1.md) | Claude Fable 5.2, launched by the adviser | `WEAKENED`: no contamination by numbers; directional text to remove; ten changes required before the freeze (its section 5) | `bc66ef18d98b583fd563e6e3fc73938fb8159383a5585fa7920621d28d3d5beb` |

The ten changes are applied in the revised arguments (the decisions' item 1), checked by Codex
(conversation r2rev) before the second bundle is built.

## R2 after the first blind review: the revised arguments and the second bundle

Codex's review of the arguments revised by the first blind review's ten items, the targets' definitions, the code semantics and the second bundle's builder (the maintainer's decisions of 2026-11-21, 15:20, items 1 to 3; #218), up to 3 rounds, on R2's line. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [r2rev-round-1-answer.md](r2rev-round-1-answer.md) | gpt-6.1-sol, high | items 1, 2, 6 and 10 `SURVIVED`; 4, 5, 7, 8 `WEAKENED`; 3 and 9 `REFUTED` (600 pairs do not give 80 % power and the exact interval was unspecified; directional text left; a historical acceptance outcome in `values.py`); **not ready** | `1b0e0407d31efd9e360727c5543844464047394ff713bdd63b420dd3c9c90234` |
| 2 | [r2rev-round-2-answer.md](r2rev-round-2-answer.md) | gpt-6.1-sol, high | the targets, B2, the confirmation and the earlier remarks `SURVIVED`; the power guarantee and the bundle `REFUTED` (the observed-discordance cut capped the power near 52 %; the manifest republished the removed text); VN `WEAKENED`; **not ready** | `80a6a5027ab1362ee90eae843b130b945a44ad2034cc0418bcc5d331879bf6a0` |
| 3 | [r2rev-round-3-answer.md](r2rev-round-3-answer.md) | gpt-6.1-sol, high | every item `SURVIVED`; **the second bundle can be built once; B3.3 goes to the second blind review as a conditional decisive candidate**; one editorial remark on VN's third kind | `7defab53d0dadd4c0e73dcb2b85385f88aba8a11bcf251c4a98082b1e4662ac9` |

The tokens are cumulative over the conversation `r2rev`:

- round 1: 918,180 input (825,216 cached) and 12,866 output;
- round 2: 1,417,441 input (1,294,976 cached) and 19,927 output;
- round 3: 1,847,670 input (1,710,848 cached) and 23,660 output;

The conversation counts **160,482** review tokens (the last round's uncached input plus output).

Applied as Codex wrote them (no divergence left after round 3):
- **The second bundle was built once on 2026-11-21 at 18:45:20 UTC** from the reviewed bytes (commit `5bbd8b3`): 19 files in `.cache/v055/r2/bundle-2/` (the arguments cut at the disclosure, the code semantics, the targets' definitions and sixteen source files of the frozen rules, `calib05/values.py` as a declared review copy); its manifest `docs/validation/v0.5.5/r2-bundle-2-manifest.json` checked for leaks and written before the files; `check` passed (19 files). **No reviewer was launched**: the second blind review is the adviser's, with a new session. The first bundle keeps its folder and manifest.
- **Before the freeze** (Codex, round 3): the exact test's ordering fixed, the valid size demonstrated for 80 % power over the design range, and the same power criterion applied to T2b.
- **Pending for the freeze, not applied** (to keep the bundle on the reviewed bytes): Codex's editorial remark that VN's third kind is better described as "a multi-harmonic profile with fixed relative phases" (under C1's sine convention, its phases give a shifted, symmetric sum of cosines; still a non-sinusoidal periodic control).
- If the second blind review leaves any condition of B3.3 open, the current branch stays decisive and the evidence split is a reported-only variant.

## R2 closed: is there a method route with decision value?

Codex's one round under the maintainer's decisions of 2026-11-21 (17:15), item 2 (#218): is there any method route (a better computation of the same rule, without loosening what a verdict asserts) for D1, D2 or T2a, with decision value by the evidence already recorded (D1-P, D2-F in the four variants, T2a-E, the ledger of floors and margins)? Records read only; no new number. Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [r2method-round-1-answer.md](r2method-round-1-answer.md) | gpt-6.1-sol, high | **NO METHOD ROUTE WITH DEMONSTRATED DECISION VALUE**: the joint probability (SIN_J), a better `odd_even` estimator, a better estimate of the background error (T2a), a better computation of D1's separation, each `SEM` (without demonstrated value); B3.3 (RULE_3) is a rule variant, also without | `42d6f82880dafde7882d732846136afd1d0aed54e11a3543b1100a96f7186d96` |

The tokens are cumulative over the conversation `r2method`:

- round 1: 719,454 input (647,936 cached) and 5,561 output;

The conversation counts **77,079** review tokens (the last round's uncached input plus output).

Applied (the decision's item 2): no method route with demonstrated decision value was found, so **nothing was built** and the work went on to item 3, the draft of the v0.5 line's pause record (`docs/plans/v0.5.5-v05-line-pause-record-DRAFT.md`), a draft only; pausing the line is the maintainer's.

## The second blind review of R2's bundle

The maintainer's decisions of 2026-11-21 (17:15), item 0 (#218): the blind review, round 2,
launched by the maintainer's adviser (a NEW session of Claude Fable 5.2, not the first reviewer,
read only, only the 19 files of bundle 2 rebuilt by `r2_bundle.py` from git at `621a14f5` and
checked against `docs/validation/v0.5.5/r2-bundle-2-manifest.json`, 19 of 19 equal; 209,751 tokens,
outside Codex's lines). Stored unchanged; the received file's SHA-256 was checked before the commit.

| Round | File | Reviewer | Verdict | SHA-256 |
|---|---|---|---|---|
| 2 | [r2-blind-review-2.md](r2-blind-review-2.md) | Claude Fable 5.2, a new session, launched by the adviser | `WEAKENED`: no contamination (three soft leaks); B3.3 a variant only (its conditions not met); the paired rule and T2b not decidable as written; seven blockers before any freeze | `ff6d49a9ea1e94013dc3276f4e58c69047b357d20fad1be565cde6a8a54fcbcb` |

Settled by the maintainer's decisions of 17:15: **R2 closes without a freeze** (the principled
combination is behaviour-identical to the frozen battery); the review's items 8 and 9 are what
B3.3's promotion would need, and its blockers 2 to 7 are lessons for any future version
([`../v0.5.5-r2-closing-record.md`](../v0.5.5-r2-closing-record.md)).

## The v0.5 line paused: the adopted pause record checked

Codex's final round under the maintainer's decisions of 2026-11-21 (18:30), item 3 (#218): the adopted pause record (docs/plans/v0.5.5-v05-line-pause-record.md) checked against its draft, the cited records and the ledger (numbers, citations, and that no rule, target, lock or verdict changes), with the ROADMAP's change of item 2. Up to three rounds; authorized to pass 80 % of v0.5.5's token line by up to 150,000 tokens (the ledger's cap_exceptions, 'pause-final-codex-round'). Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 1 | [pause-round-1-answer.md](pause-round-1-answer.md) | gpt-6.1-sol, high | **WEAKENED**: two blocking items (section 7 rewritten beyond the three corrections; trigger 4's wording asks for eight D1-P cells on one new seed set while the frozen design counts them across two sets) and three remarks (rounding, the T2a noise-model wording, the header's sentence on sources) | `15f535508ec997d31242444167a3196edbb89baa15f68603649481ee7c3d6623` |
| 2 | [pause-round-2-answer.md](pause-round-2-answer.md) | gpt-6.1-sol, high | **WEAKENED**: section 7 restored as history, rounding note and header applied; keeping trigger 4's adopted wording and taking the correction to the maintainer is acceptable, but the record still presented that trigger as verifiable while it diverges from the design | `e8661c1917ddeab6cb4eee43cdee06bbbc0ec759c809b322ff884ab83e1e380a` |
| 3 | [pause-round-3-answer.md](pause-round-3-answer.md) | gpt-6.1-sol, high | **SURVIVED**: no blocking item; the note under trigger 4 resolves round 2's item; remarks: the D1 and T2a wordings proposed for the maintainer's decision | `ae65aece6bb2ab47eb2b62164a2b3346b1406b9c59e49a1894d3f4ea9fad79d6` |

The tokens are cumulative over the conversation `pause`:

- round 1: 582,961 input (499,328 cached) and 9,422 output;
- round 2: 370,332 input (327,168 cached) and 4,222 output;
- round 3: 429,766 input (382,848 cached) and 5,400 output;

The conversation counts **52,318** review tokens (the last round's uncached input plus output).

Applied: round 1's section 7 item (the draft's paragraph restored byte for byte under the title 'What the draft asked the maintainer to decide'), the rounding note and the header sentence; round 2's item by a note under trigger 4 that keeps the adopted wording and points to R1's frozen design (revision 1, section 3; `d1p_exit_outcome`), and a pointer under trigger 3 to v0.5.4's pause record. Not applied, by the conservative option (they would change a resuming trigger's wording beyond the three corrections the maintainer authorized): the D1 wording 'whose D1-P price reads "route" in all eight cells across two new seed sets for a decisive exit' and the T2a wording 'or a noise model of the background series, in a new design frozen before its data, under which at least 82 of the 102 class-(i) injections are valid by all of step 6's requirements'; both are the maintainer's decision (#218). No other round follows.

## The pause record's corrections (triggers 3 and 4)

Codex's round on the corrections the maintainer accepted on 2026-11-21 (20:00), item 1 (#218): the new record docs/plans/v0.5.5-v05-line-pause-record-corrections.md (the two wordings Codex proposed in rounds 1 to 3, the reason, the pointers) and the ROADMAP's pointer on v0.5.5's line; the adopted record unchanged. Within the token allowance of the 18:30 decision, item 3 (the ledger's cap_exceptions, 'pause-final-codex-round'). Codex CLI 0.167.0-alpha.3.2 answered in Portuguese, and the answers are stored unchanged.

| Round | File | Model, effort | Verdict | SHA-256 |
|---|---|---|---|---|
| 4 | [pause-round-4-answer.md](pause-round-4-answer.md) | gpt-6.1-sol, high | **WEAKENED**: no blocking item of content (both wordings and their sources check; the adopted record is byte-identical to b654d88); two remarks of textual scope: keep trigger 3's closing parenthesis with its pointer, and drop the date after the ROADMAP's new link | `2e60dbe07f0319ab505fdaadfa3dc427eb60776774011f4fdce65c2e432a117c` |
| 5 | [pause-round-5-answer.md](pause-round-5-answer.md) | gpt-6.1-sol, high | **SURVIVED**: both remarks applied; no correction pending | `1dd3777fcaeddacff022fca03a7a512fde57424056b669a610ee0d18c2d722e5` |

The tokens are cumulative over the conversation `pause`:

- round 4: 261,563 input (219,648 cached) and 4,084 output;
- round 5: 164,413 input (139,648 cached) and 1,834 output;

The conversation counts **26,599** review tokens (the last round's uncached input plus output).

Applied: round 4's two remarks (trigger 3's parenthesis restored with the pointer to v0.5.4's pause record; the ROADMAP's diff reduced to the pointer). No other round follows.
