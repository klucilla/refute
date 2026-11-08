**Verdict: WEAKENED, round 3, with one LOW-severity correction remaining.**

The four round-2 objections are substantively met:

- **Validation:** the permission gate retains 0.95 coverage and 0.05 familywise error, with enumerated scenarios and an explicit certification target.
- **Availability:** A0.8 uses branch-curve estimates; A0.1’s assumed availability is disclosed. Neither is presented as measured distinct-curve availability.
- **Cost interpretation:** integer schedules, expected-count pricing, retained diagnostic expenditure, ideal-day labels and the requirement for every applicable member are explicit.
- **Inference specification:** variance contributions now centre correctly; the moment statement is qualified; **rank 1,935 is correct** for the stated construction; the degenerate-replicate rule and positive sabotage distances are specified.

All nine main repricing scenarios reproduce their JSON.

1. **LOW: The new A0.1 sensitivity ignores the availability floor.**

   **Evidence:** [worksheet_reprice.py:174](C:/Projetos/refute/docs/validation/v0.5.2/stage1/worksheet_reprice.py:174) reports the same additional cost for availability 0.25 at every floor. At `T = 3,300`, **+15.858 processor-hours** is correct when A0.1 remains priced, including floors 0.25 and 0.10.

   At floor **0.50**, however, availability 0.25 excludes all 15 A0.1 members from pricing. Applying `_price` consistently instead produces **−4.966 processor-hours**, retaining their old diagnostic expenditure. The unconditional [“16 more processor-hours” statement](C:/Projetos/refute/docs/validation/v0.5.2/stage1/README.md:227) therefore mixes two counterfactuals.

   **Exact change:** Either label the sensitivity **“holding priced membership fixed”**, or recompute it through `_price` after changing availability. Under the latter interpretation, report the loss of 15 priced members at floor 0.50 and restrict the approximately +16-hour statement to floors at or below 0.25.

The maintainer can assess both interpretations: the additional cost is valid with membership held fixed; it is not the result of applying the published floor policy unchanged. No other objection remains within this round’s scope.