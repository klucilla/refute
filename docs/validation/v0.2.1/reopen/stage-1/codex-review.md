# The Codex review of stage 1

A read-only review (Codex CLI, `codex exec -s read-only`, logical processors 8 to 31) of this
folder's documents and of the item-0 wording added to the R_min study's README and its diagnosis.
Three rounds, one conversation; Codex's answers are kept verbatim in [codex/](codex/) (the questions,
which carry the protocol's rules in Portuguese, stay in the working folder).

| Round | Codex's position | What it raised | What was done |
|---|---|---|---|
| 1 | OBJECAO | Spec A: class N not exhaustive (non-finite `S_pred,2`); "detectable" to be qualified as predicted by the engine's error model; W1's role and limit left open. Spec B: C6 wrong (the round hiding Y, not the others, keeps its preparation); completeness checks missing; the constant false FAIL's fraction among the decided can change. Instrumentation: a field source missing (`plan_round` does not return the candidate at `train_noise_undetermined`); AB2 wrong for an empty grid; one matrix for two behaviours (calibration does not stop at decisions 1 and 2); no source-equality checks; sabotages S2, S5, S6 not sure to bite. Plan: the smallest yield is 0.64%, not 1.3%; X3's precision is of the threshold, its 520 a normal approximation; X2's regimes not disjoint. The item-0 wording found faithful; the arithmetic of costs found right | all applied (spec A, spec B, instrumentation revision 2, the plan) |
| 2 | OBJECAO | AC1 not piecewise (all-zero variances; `None` against `NaN`); the matrix missing the post-window validity rejection and other early branches; C6 to be bounded at the first hidden-data read | all applied |
| 3 | ACORDO | "Agreement covers the specifications, acceptance design and experiment plan. Implementation and validation remain pending; calibration, pilot and main study remain unauthorized." | the documents are frozen as committed |
