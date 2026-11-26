# Correction of 2026-11-26: the token total of the v0.5.13 charter's Codex rounds

**What was wrong.** [README.md](README.md) of this folder, at `04402e7` (the commit whose charter
the maintainer approved), gives "the sum over the three rounds: 7,433,502 input tokens (7,042,560
of them cached) and 62,201 output tokens". The README itself is not edited; this file is its
correction.

**Why it was wrong.** The three rounds ran in one thread, `01a219cf-3590-70f0-8f18-1b98fe4f39ae`:
round 1 opened it, and rounds 2 and 3 resumed it with `-Thread`. The usage that a resumed round
reports is cumulative over the thread. The figures show it: each round's numbers grow, and they
are not separate amounts. So adding the three rounds counts the earlier rounds two or three times.
This is the rule recorded after the slip of 2026-11-21 (`docs/validation/v0.5.5/pause-tokens-correction.md`):
a resumed thread is counted by its **last** round.

**The corrected total** is round 3's report, which already covers rounds 1 and 2:

| | Input | of them cached | Output |
|---|---|---|---|
| The thread, rounds 1 to 3 | **3,159,180** | 3,008,256 | **24,350** |

**Impact.**
- The earlier figure overstated the cost by 4,274,322 input tokens and 37,851 output tokens.
- No cap, verdict, criterion or decision depended on it: the charter's drafting was outside any
  phase's caps (the v0.5.12 charter's rule, section 6).
- The per-round figures in the README's table are what each round reported, read cumulatively.
