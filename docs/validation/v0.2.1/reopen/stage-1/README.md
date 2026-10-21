# Stage 1 after the R_min study: specifications, acceptance record and plan

The maintainer's decisions of 2026-10-21, after the diagnosis of the R_min study and its
discussion. **No lot is authorized and no `R_min` is validated.** The study failed by the false-FAIL
minima not reached in three groups, and also by the incompatibility of the weakening criterion, by
coverage outside its band in some configurations, by the disappearance criterion not met in one
group, and by a gap in the control of the target's PASS
([../rmin-study/study/README.md](../rmin-study/study/README.md)).

| Item | Document |
|---|---|
| A. The weakened scenario under "presence of the signal" (a change of objective after the negative result; the new metric before any data) | [spec-a-weakened-scenario.md](spec-a-weakened-scenario.md) |
| B. The target's PASS: the necessary years, the aggregation, the controls, the false PASS per target | [spec-b-target-pass.md](spec-b-target-pass.md) |
| C. The scope rule (to study, never automatic), in the pilot's declaration | [experiments-plan.md](experiments-plan.md), "The scope rule" |
| D. The instrumentation's acceptance record (no decision changed) | [instrumentation-acceptance.md](instrumentation-acceptance.md) |
| The experiments needed, with their cost | [experiments-plan.md](experiments-plan.md) |
| Codex's review | [codex-review.md](codex-review.md) |

Nothing here changes code, a threshold, a criterion of a past study or a result. The code of items B
and D comes after its acceptance record; the calibration, the pilot and the main study each need
their own criteria, budget and authorization.

## After X0 and X1 (the maintainer's decisions of 2026-10-21)

| Item | Decision | Document |
|---|---|---|
| 1 | X1 closed, in the instrumentation's scope; AC5's limit kept (exact only on the snapshot's machine; structure elsewhere; no numerical equivalence across machines shown); the guard and the sabotages strengthen the information contract, they do not show `e_pred` or `b`/`s` right | [x1-results.md](x1-results.md) |
| 2 | X1b authorized as an **experimental** implementation of spec B: one function for the engine and the evaluator, on the experimental M4 path only, asked for by name; the legacy rule and the frozen evidence kept; B6 revised first; the year without a predicted window included; Codex's review | [spec-b-target-pass.md](spec-b-target-pass.md) B6, [x1b-acceptance.md](x1b-acceptance.md), [x1b-results.md](x1b-results.md) |
| 3 | X0c authorized, read only, declared first: the constant scenario's false FAIL at R = 8 and R = 20 | [x0c/DECLARATION.md](x0c/DECLARATION.md), [x0c/README.md](x0c/README.md) |
| 4 | X2 and X3: their declarations prepared, **not run**; each run comes back with its size, seeds, affinity, workers, cost and ceiling | [x2-declaration.md](x2-declaration.md), [x3-declaration.md](x3-declaration.md) |
| 5 | Qualifications kept in every record: "no false PASS under B" = none observed in this lot; B does not correct a detection by noise when every year PASSes; the threshold is not raised only to remove such cases; releasing the gates is not presumed good | [x0/README.md](x0/README.md), spec B B6 |
| 6 | External research allowed for X0c, X2 and X3: every external fact with its URL, the date it was read and a short literal excerpt kept in the repository | [sources/](sources/) |

The pilot, the main study, the reserve and any scientific adoption still depend on their own
acceptances.
