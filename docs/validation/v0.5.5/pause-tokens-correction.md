# Correction: the review tokens of Codex's conversation "pause"

Recorded on 2026-11-21, after the round on the pause record's corrections. It corrects figures
given earlier; the records that carry them keep their bytes.

## What was wrong

The ledger counts a Codex conversation by its **last round** (`ledger_v055.codex_tokens`; the
consensus record states it as "the last round's uncached input plus output"). That holds when the
rounds resume one Codex thread (`codex_affinity.ps1 -Thread <id>`): the usage is then cumulative
over the thread, as in every other conversation of v0.5.5 and of R2 (their rounds' inputs grow).

The five rounds of the conversation "pause" were each run as a **new** Codex session (no
`-Thread`). Each round's usage is then its own, and the last-round count leaves out the others. The
figures given for the conversation were therefore too low:

- the consensus record and the comment on #218 of 2026-11-21 gave **52,318** tokens for rounds 1 to
  3 (round 3 alone), and **26,599** for rounds 4 and 5 (round 5 alone);
- the stop of 2026-11-21 (18:30 decision) reported 52,318 of the 150,000 allowed, and the
  maintainer's decision of 20:00 relied on "about 97,000 left".

## The figures by round

Each round's own review tokens (uncached input plus output, from its last usage event, in
`.cache/v055/codex/pause-r<n>-events.jsonl`):

| Round | Input | Cached | Output | Own tokens |
|---|---:|---:|---:|---:|
| 1 | 582,961 | 499,328 | 9,422 | 93,055 |
| 2 | 370,332 | 327,168 | 4,222 | 47,386 |
| 3 | 429,766 | 382,848 | 5,400 | 52,318 |
| 4 | 261,563 | 219,648 | 4,084 | 45,999 |
| 5 | 164,413 | 139,648 | 1,834 | 26,599 |
| **Total** | | | | **265,357** |

Rounds 1 to 3 used 192,759 tokens, more than the 150,000 of the 18:30 decision's item 3, before the
round on the corrections began. Rounds 4 and 5 used 72,598 more. In all, the conversation used
115,357 tokens beyond the 150,000.

## The effect on the lines

- **v0.5.5's line (without R2):** the ledger's reading after round 5 is 1,330,561, of which 26,599
  are "pause". With the conversation's real count, the line holds **1,569,319** tokens. That is 52 %
  of the 3.0 M cap, below the stop at 80 % (2,400,000).
- **With R2** (564,672 tokens): **2,133,991**, below the same stop point.
- The 80 % stop point was not reached, so the cap exception of item 3 (`cap_exceptions`,
  "pause-final-codex-round") was not needed to pass it. The 150,000 figure that the maintainer and
  the agent used as the conversation's budget was exceeded, as above.

## What does not change

No verdict, rule, target or lock changes. The consensus answers and the ledger keep their bytes. The
ledger's counting code is not changed: whether to count an unresumed conversation by the sum of its
rounds is the maintainer's decision. Every later Codex round of this project resumes its
conversation's thread, or is counted by the sum of its rounds.
