# Consensus record: v0.5.7 The TOI's own signal

Every answer and attachment here is stored unchanged, with its SHA-256. Codex's answers carry the
model, the effort and the Codex CLI version.

## The independent recommendation (the phase's basis)

The basis of the maintainer's decision of 2026-11-23 (received at 10:41 local, #218, comment
7102888515), item 0. It is one read-only session of Claude Fable 5.2, launched by the maintainer's
adviser at the maintainer's request, on `8d51c13`, with 185,834 tokens, outside Codex's lines. It
is written in Brazilian Portuguese, as asked. Its recounts are exploratory and were not reviewed
by Codex.

The file is the maintainer's attachment, stored unchanged. Its SHA-256 was checked against the
attachment before the commit.

| File | SHA-256 |
|---|---|
| [independent-recommendation.md](independent-recommendation.md) | `8067b08805bea8bee12abd3b7bda4ac8e0636a5fc526f6eaf89909786606cdfe` |

## The design round, before the pilot (one round)

The maintainer's decision of 2026-11-23 (received at 10:41 local), item 2, asked one Codex round on the design question before the pilot: how to fix the candidate, the depth and the SNR without touching `src/`. The round reviewed the plan, the runner `docs/validation/v0.5.7/fixed_run.py`, the report script and the tests, in the working tree (uncommitted, never run). It ran in a new conversation `v057design` (thread `01a208ac-54d7-7480-95af-38a8aa56bac1`). Codex CLI 0.167.0-alpha.3.2, model gpt-6.2-sol, effort high. The answer is stored unchanged.

| Round | File | Verdicts | SHA-256 |
|---|---|---|---|
| 1 | [design-round-1-answer.md](design-round-1-answer.md) | 1 REFUTED, 2 SURVIVED, 3 REFUTED, 4 WEAKENED, 5 REFUTED, 6 REFUTED, 7 WEAKENED; five blocking items; **OVERALL: REFUTED** | `9137e274d67ca3974717fc3a1958929c19b01dd05c49c52e375170dc2aea73fc` |

The round used 1,794,259 input tokens (1,674,880 cached) and 17,820 output tokens. The conversation counts **137,199** review tokens: the uncached input plus the output.

**The pilot did not run.** The first blocking item is a conflict with the maintainer's decision, so it is the maintainer's to resolve.
- The decision fixes the TOI's period and bounds the epoch to a window.
- The unchanged battery's `attack_candidate` refits the period by up to ±1 step, the epoch over the whole phase, and the duration, before any test.
- So, with the battery unchanged, the tests measure a fit **seeded** by the TOI, not the fixed ephemeris.
- Holding the period and the epoch inside the tests would change the battery's behaviour, either by a run-time patch or by a change in `src/`.
- By the rule on divergence, the more conservative option is taken: STOP before the pilot.

The other four blocking items are implementation corrections, to apply before any pilot:
- the epoch grid;
- binding the pilot to its historical inputs;
- validating the cohort in the doors;
- the operational limits and cache isolation.
**The maintainer's decision on the design** (received at 11:01 local, #218, comment 7103371874):
- **Mode A, TOI-seeded.** The opening's item 2 is revoked. The battery runs unchanged, seeded by the TOI's ephemeris.
- **Every record** keeps the ephemeris fields and `stayed_on_toi_ephemeris`.
- **Every door** is counted in total and over the records that stayed.
- **The round's other four blocking items** are applied before the pilot.
- **There is no new Codex round:** the pilot is the check.
## The pilot stop, the diagnostic and the closing

**The pilot** (commit 4201b40) reproduced 8 of 10 TOIs test by test, against the 9 required, so the run stopped. The maintainer's decision (received at 11:55 local, #218, comment 7104767892) did three things:
- kept the pilot rule as written;
- approved one diagnostic rerun, whose procedure was posted on #218 before it ran (script fdc4e8b, result bd4f29f; answer for both TOIs: the seeding);
- closed v0.5.7 at its pilot gate, with declared limits, with one Codex round on the draft report and the closing.

That round ran in a new conversation `v057close` (thread `01a208fa-85f0-7562-8c88-b0157fa0171d`). Codex CLI 0.167.0-alpha.3.2, model gpt-6.2-sol, effort high. The answer is stored unchanged.

| Round | File | Verdicts | SHA-256 |
|---|---|---|---|
| 1 | [closing-round-1-answer.md](closing-round-1-answer.md) | 1 REFUTED, 2 WEAKENED, 3 WEAKENED, 4 SURVIVED, 5 SURVIVED, 6 SURVIVED; two blocking items; **OVERALL: REFUTED** | `82af9b440c6d16bfdd964fcb407578d4a814096189b98a24270d20d055fccb75` |

The round used 597,905 input tokens (497,536 cached) and 10,057 output tokens. The conversation counts **110,426** review tokens: the uncached input plus the output.

**Applied as Codex wrote them** (the conservative option):
- **The fitted-period comparison of TOI-1062.01.** The two fits differ by about 3.45 × 10⁻⁷ d and 1.83 minutes. The earlier 3.5 × 10⁻⁶ d was the seeded fit's difference from the TOI's published period. The same slip is in commit 4201b40's message and in #218, comment 7104106385; it is corrected by a new record, never an edit.
- **The diagnostic's recording gap is disclosed.** The unchanged search runner does not record the fitted duration and depth that the procedure asked for.
- **The boundary sentence** is now specific to TOI-1062.01.
- **ROADMAP criterion 4** reads "TOI-seeded", in both door versions.

There was one round, so there is no second round on these corrections.