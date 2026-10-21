# X0a and X0b: read-only analyses of the R_min study's records, declared before they run

Authorized by the maintainer on 2026-10-21 (after specifications A and B were approved as they
stand in `c5d1287`). **Development evidence, not validation.** From the recorded fields only: no
light curve, no run of the engine, no lot. This declaration is committed and pushed before either
analysis runs; only what it declares is computed, and anything else is written apart in
`exploratory.md`, never run. The same data, code and conventions as the diagnosis
([../../rmin-study/diagnosis/DECLARATION.md](../../rmin-study/diagnosis/DECLARATION.md), sections 2
and 3): the 76 800 records of the R_min study checked against their committed digests; the study's
code at `2e4ff99` (`.cache/wt-v021`, read only, no bytecode written); `derive_round` and
`target_outcomes` at each `R ∈ {8, 10, 12, 15, 20}` with bs-choice's committed pair; the gates G0 to
G6 and the reason kinds as in the diagnosis's script. Every fraction states its numerator and
denominator. No inferential claim.

## X0a. Where the disappearing scenario's false PASS come from

Per R and group, over the disappearing targets whose aggregated outcome **under today's rule** is
PASS (`x0a.json`):
1. their count, beside the decided disappearing targets of the cell;
2. per target: its observing years, each round's hidden year, status, gate and reason kind, and the
   `S_meas` of each PASS round;
3. the distribution of the **last round's** gate (and reason kind for G0) over those targets;
4. which hidden years PASS, as their position from the last year (the last year itself, one year
   before it, two years before);
5. the quantiles (5, 25, 50, 75, 95%) of `S_meas` of the PASS rounds, with their count;
6. the number of observing years of those targets, beside that of all decided disappearing targets
   of the cell.

## X0b. Specification B applied to the current records

Per R, group and scenario (`x0b.json`), with specification B's aggregation (B2: any FAIL round gives
FAIL; otherwise PASS only when every observing year's round is PASS; otherwise INCONCLUSIVE),
computed from the same derived rounds as today's rule:
1. PASS, FAIL and INCONCLUSIVE targets under today's rule and under B, and the transitions (in
   particular PASS → INCONCLUSIVE); total, decided, decided / total under both;
2. constant scenario: FAIL count, FAIL / decided and FAIL / total under both; disappearing scenario:
   PASS count (false PASS), PASS / decided and PASS / total under both, and FAIL / decided; weakened
   scenario: PASS and FAIL under both, without an error label;
3. **separated, as the maintainer asked:** of the targets INCONCLUSIVE under B, how many have at
   least one undecided year whose round stopped with `no_predicted_window` (a year without a
   predicted transit window), and how many have no other undecided reason; the same two counts for
   the targets turned from PASS to INCONCLUSIVE by B;
4. the undecided years of the targets turned from PASS to INCONCLUSIVE, by gate and reason kind
   (round counts).

Completeness (one round per observing year, as specification B requires) is checked on every record
first; the R_min lot already passed it (its integrity check), and any failure stops the analysis.
