# Codex's opinion on the diagnosis delivery

A read-only review (Codex CLI, `codex exec -s read-only`, logical processors 8 to 31) of this
folder's delivery, its outputs and its script, after the analysis. Two rounds, one conversation;
the answers are kept verbatim in [codex/](codex/) (`opinion-round-1.md`, `opinion-round-2.md`).

**Round 1, OBJECAO.** The implementation was found faithful for the gates, the denominators, the
Q3 categories, the Q5 bootstrap and ICC and the Q8 denominators, with its numbers reproduced, but:
- Q3 had pooled the three scenarios, a departure from the declaration's default;
- the train-SNR fraction's denominator needed stating;
- the three-round targets of Q5 needed mention;
- problem 1 needed the R = 20 qualification, and problem 2 needed the threshold's unmeasured share;
- problems 3 and 4 needed sharper refuting tests (variability regimes; an equivalence margin);
- the proposal needed acceptance records before tests and code, non-vacuous controls, a sizing rule
  declared before the pilot, the reserve's contract, and a scope rule fixed before with an
  engine-observable boundary;
- the "blocks" list needed three qualifications: T4's own validity path, T4's own pilot, and the
  reserve not being the v0.2.1 confirmation.

All were applied: the script was corrected to key Q3 by scenario as declared and run again (the
declaration unchanged; the other five outputs byte-identical), and the README revised.

**Round 2, ACORDO.** "The revised delivery resolves my objections. I have no remaining blocking
finding." It confirmed the per-scenario Q3 counts, the byte-identical outputs and the declaration's
match with its frozen `254f447` version, and added: "No R_min is validated. Acceptance of the
delivery does not authorize execution; stage-specific declarations and the maintainer's decision
remain required."
