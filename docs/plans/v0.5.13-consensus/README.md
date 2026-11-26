# v0.5.13 charter: Codex consensus record

This record follows the maintainer's decision of 2026-11-26, item B2 (#218, comment 7203695669):

- Codex reviews the draft in up to three rounds, in a new conversation for this charter.
- Its answers are stored unchanged here.
- Where Codex and the draft diverge, the more conservative option is taken.

**Codex's verdict is an opinion on the text, not an approval.** Approving the charter and opening
the phase are the maintainer's.

## The rounds

**The setup of every round:**
- Codex CLI 0.167.0-alpha.3.2, with the model of its local configuration;
- read only, sandbox read-only, threads 8 to 31, through `.cache/v04/tools/codex_affinity.ps1`;
- one thread, `01a219cf-3590-70f0-8f18-1b98fe4f39ae`: round 1 opened it, and rounds 2 and 3
  resumed it.

| Round | Reviewed | Prompt / answer | Verdict | Tokens (as each round reported: input, of them cached, output) |
|---|---|---|---|---|
| 1 | `65e83be`, draft r0 | [prompt](round-1-prompt.md) / [answer](round-1-answer.md) | `NOT_APPROVABLE`: seven blocking items | 1,585,627; 1,483,136; 15,038 |
| 2 | `a7fba55`, draft r1 | [prompt](round-2-prompt.md) / [answer](round-2-answer.md) | `NOT_APPROVABLE`: all seven applied; six integration defects | 2,688,695; 2,551,168; 22,813 |
| 3 | `e66bd22`, draft r2 | [prompt](round-3-prompt.md) / [answer](round-3-answer.md) | **`APPROVABLE`**: all six applied, and one editorial cleanup "needs no further review" | 3,159,180; 3,008,256; 24,350 |

**The sum over the three rounds:** 7,433,502 input tokens (7,042,560 of them cached) and 62,201
output tokens. These are the figures each round's events reported, added together; a resumed round
reads the thread again, so it is billed again.

**The SHA-256 of the answers:**
- round 1: `5b6ce509…12aa43`;
- round 2: `350ce544…0e5d60`;
- round 3: `5a1dfb94…806906`.

## What was applied

- **Every blocking item** of rounds 1 and 2, and round 3's cleanup, are applied by quoting Codex's
  text as written. They are marked in the charter "Codex r1, item N", "Codex r2, item N" and
  "Codex r3".
- **Where Codex's wording replaces a sentence inside earlier quoted text,** the replacement is
  marked in brackets.
- **No divergence remained** to resolve: in every case Codex's wording was the stricter one, and it
  was taken.

## Codex's choices (the answers to item B1)

- **The targets:**
  - X = 0.25, Y = 0.80 and Z = 0.70, with coverage counted on all frozen cases, both "not
    assessed" buckets in the denominator;
  - two expected-SNR bands (< 20 and ≥ 20), each with a safety floor of 0.40, a sensitivity floor
    of 0.65 and a coverage floor of 0.60;
  - a signed symmetry rule, the 90 % Newcombe interval within [−0.15, 0.15];
  - per-type FP results reported descriptively, with no change to the pooled target.
- **The power:** the joint pass probability of the full AND rule is 0.9459 in the planning model.
  `power_v2.py` gives 0.945942, and Codex's own enumeration gave 0.9459418125.
- **The injection into real light curves:**
  - 20 quiet and 20 active stars, DEV-H first and DEV-T only as a fallback, ordered by hash;
  - an activity index A on 2-hour weighted bins, quiet below 1.5 and active at 3 or above;
  - 50 slots per star in three SNR bands, each with four paired injections (equal depths,
    alternating depths at a 0.60 ratio, a white control and a red control);
  - the null rule: at most 3 rejections in 1,000 per activity class;
  - the red-control rule: at least 937 rejections in 1,000;
  - zero `not_assessed`, a lost slot counting as `not_assessed`;
  - fresh seeds for each approved measurement.
- **The caps rule:**
  - the job object is the only meter;
  - a journal entry opens before each execution;
  - an execution outside the meter is recorded at once, with a conservative estimate and its
    basis;
  - the reconciliation covers the sealed cursor and then the post-seal tail;
  - the named retry classes: checkers, formatters, and one infrastructure retry with no case
    value. A scientific measurement is never a retry.
- **The split:** v0.5.13 (Part A) and v0.5.14 (Part B), with no merge by extension. Part A's caps
  are 8 CPU-h, 3 GB and 5 GB.

## Non-blocking notes of round 1, for the maintainer

- The charter's link to this record was premature in r0. This record now exists.
- `power.py` ran with no "before" entry in the preparation log. The gap is recorded there by a
  note, and no receipt is backdated.
- The 171 strict ground-discovered planets come from a facility-string heuristic that also passes
  an empty facility. It is usable for sizing only, and v0.6 needs an authoritative facility
  provenance.
