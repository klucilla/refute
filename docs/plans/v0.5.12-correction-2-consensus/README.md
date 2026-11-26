# v0.5.12 correction 2: the Codex consensus record (2026-11-26)

The maintainer's decisions of #218 comments 7193864189 (item 3) and 7196269069 (item 3) called
for Codex on correction 2: up to three rounds (a rule change), resuming one thread, each on one
closed question. Answers are stored unchanged.

- **Codex:** read-only, through `.cache/v04/tools/codex_affinity.ps1` (processors 8 to 31), run as
  the phase's launcher units `codex`, `codex2` and `codex3` (rounds 2 and 3).
  - **CLI:** 0.167.0-alpha.3.2.
  - **Model and effort:** gpt-6.2-sol, high, from the Codex configuration.
  - **Thread:** `01a21826-635e-7ac3-9a15-aad43b8235f2`.

| Round | Prompt | Answer (stored unchanged) | Verdict |
|---|---|---|---|
| 1 (interrupted) | [r1-codex-prompt.md](r1-codex-prompt.md) | none: the meter stopped it at its 50 MB disk reservation | — |
| 1 (the approved repetition) | [r1b-codex-prompt.md](r1b-codex-prompt.md) | [r1-codex-answer.md](r1-codex-answer.md) (7,942 bytes, SHA-256 `12b846a79a5d6c282155e2f78614c066987dc7226e32635fb9ff20598501b66f`) | `REFUTED`, 4 blocking items |
| 2 | [r2-codex-prompt.md](r2-codex-prompt.md) | [r2-codex-answer.md](r2-codex-answer.md) (1,969 bytes, SHA-256 `f2040b097ee9eb0a96f32d8c0b8f74aa94d6df159b05f21341428773fb678cae`) | **`SURVIVED`** |
| 3, the last (revision 1, after the blind review and check 3) | [r3-codex-prompt.md](r3-codex-prompt.md) | [r3-codex-answer.md](r3-codex-answer.md) (4,624 bytes, SHA-256 `8e536f4e0a01a040eb7ea007fbe278c6485044ac2636252010e0daaf11c4a853`) | **`WEAKENED`**: B1-A and B2 applied exactly; a declared limit added, applied as written |

**Codex's choices**
- **The estimator:** keep the reduced χ² scale s², the inverse-variance weighted red moment, and
  the per-parity σ_par² = s²/W_par + σ_r²/N_par. The red moment is computed stably, with a positive
  prefix sum for C. The OE numerator is the difference of the two in-transit weighted means.
- **Scope (i):** F1 only. F2 and U1 keep the existing MES noise. Their unequal-σ treatment is a
  declared report-only limit.
- **Order (ii):**
  1. step 4's blind review and adoption;
  2. step 2's inventory, cases and approval-code probe;
  3. both suites pushed;
  4. the reviewed `src/` change;
  5. M2 and the control.

**Tokens**, the real sum of the events' `turn.completed` usage:

| Round | Input | of which cached | Output | Review (input not cached + output) |
|---|---|---|---|---|
| 1 (interrupted) | unknown | unknown | unknown | unknown (deviation 1; no estimate) |
| 1 | 1,025,801 | 904,576 | 8,958 | 130,183 |
| 2 | 1,424,253 | 1,290,624 | 10,876 | 144,505 |
| 3 | 2,277,442 | 2,114,048 | 16,170 | 179,564 |
| **Sum** (known) | **4,727,496** | **4,309,248** | **36,004** | **454,252** |

**The disk used by Codex's own state,** written by the job and counted in the phase-wide bound:
- the interrupted attempt: 128.8 MB;
- round 1: 130.6 MB;
- round 2: 17.1 MB;
- round 3: 126.1 MB (unit `codex3`, reservation 196 MB).

**Round 3** (the maintainer's decision of #218 comment 7197099779, item 5): the closed question
was the application of the blind review's B1 (alternative A) and B2 in revision 1, and check 3's
result. The events also report 5,251 reasoning output tokens, shown here apart, as the events
give them. Its wording is applied in `docs/plans/v0.5.12-spec-correction-2-r1.md`
(errata entry 3).
