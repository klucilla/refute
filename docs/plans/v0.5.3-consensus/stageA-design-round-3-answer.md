1. **Applied correctly.** `v0.5.3-stageA-design.md:74` preserves the distinction between evidence-qualified PASS and kept retention.

2. **Applied correctly.** `v0.5.3-stageA-design.md:93` now specifies the square root of the GLS variance. The helper implementation remains unreviewed.

3. **Applied correctly.** `v0.5.3-stageA-design.md:112` keeps the background measurements separate from an information bound.

4. **Applied correctly in the design.** `v0.5.3-stageA-design.md:84` defines the sector nuisance columns and dimensionally correct contrast. Numerical implementation remains to be reviewed before (b).

5. **Applied correctly.** `v0.5.3-stageA-design.md:97` treats unbounded blockers optimistically and enumerates D2 planets without duplication.

6. **Applied correctly.** `v0.5.3-stageA-design.md:105` separates the population threshold from 97/112; `:120` makes T2a’s plug-in calculation conditional and counts its odd/even blockers as recoverable.

7. **Applied correctly for diagnostic collection.** `a0_refusals.py:185`, `:231`, `:344` and `:419` implement dropped-event tracing, D2 depth tracing, comprehensive instrumentation quarantine and replay exclusion. **Interpretation constraint:** the branch totals count refusing calls, not independently attributable lost planets.

8. **Applied correctly concerning child CPU and candidate identity.** `v0.5.3-stageA-design.md:135` compares final candidates and keeps computation inside accounted pool workers. The remaining batch issue concerns (c3), below.

9. **Partially applied.** `ledger_a.py:54`, `:86` and `:113` preserve allocations, read transferred allocations and check reservations. **BLOCKING accounting prerequisite before (a):** [caps.json:6](C:/Projetos/refute/docs/validation/v0.5.3/stageA/caps.json:6) still records **zero review tokens** despite these reviews. Replace it with the cumulative measured count or a documented conservative upper estimate, including all three rounds. Refuse dispatch if remaining budget cannot be established. No other item-(a) code blocker was identified.

10. **Applied correctly.** `a0_refusals.py:320` checks the historical ledger in `finally`, covering preflight and execution failures.

11. **Before (c3), enforce the batch deadline.** [v0.5.3-stageA-design.md:139](C:/Projetos/refute/docs/plans/v0.5.3-stageA-design.md:139) calls the most-sector injection the “worst case,” but sector count does not establish maximum runtime. Moreover, `driver.py:525` detects excessive shard duration only after completion. **Correction:** describe that smoke as a runtime proxy and enforce the batch deadline while workers run, charging interrupted work and leaving unfinished injections unknown. Charging an outside-pool smoke also needs advance CPU reservation and exception-safe accounting.

No additional blocking design defect was identified for (b), (c1/c2) or (d). Their implementations and frozen procedures still require review before execution. Item (a)’s prescribed commit and issue-posting prerequisites also remain.

**Item (a): WEAKENED; design: WEAKENED.**