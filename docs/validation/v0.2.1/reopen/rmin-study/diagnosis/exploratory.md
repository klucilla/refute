# Exploratory findings and unexecuted proposals

Kept apart from the declared diagnosis ([DECLARATION.md](DECLARATION.md), section 1). Nothing
here changes a declared cut, denominator, output or conclusion. No undeclared calculation was run.

1. **Unexecuted proposal: where the disappearing scenario's false PASS come from.** The declared
   Q8 output shows, in `AR(1), variability`, 26 PASS targets among 241 decided at R = 8, none of
   them in the evaluation's qualified set (all 210 qualified FAIL); at R = 20, 42 PASS among 467
   decided, 41 of them outside the qualified set (1 of the 401 qualified PASSes on its last round).
   By the aggregation rule and `derive_round` this follows without computation: a target outside the
   qualified set has a last round that does not pass both decisions, hence INCONCLUSIVE; with no
   FAIL round, its PASS comes from a round hiding an earlier year. **Which** round passed, and why
   this concentrates in `AR(1), variability` (0 or 1 in the other groups), would need a breakdown
   by round and year that this diagnosis did not declare. Proposed for a separate declaration:
   per disappearing PASS target, the year and SNR of its passing rounds and the gate of its last
   round.
2. **Observation while reading the outputs:** the G3 subcauses at R = 8 are all
   `hidden_noise_stage` (the hidden noise stage recorded as undetermined, with the replicas also
   below R), while at R = 20 most G3 rounds are `hidden_replicas_below_r` (the noise determined but
   fewer than 20 replicas). This is the declared cross-table read as it is; no further analysis.
