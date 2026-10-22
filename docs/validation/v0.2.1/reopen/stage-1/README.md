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

## After X0c and X1b (the maintainer's decisions of 2026-10-21)

| Item | Decision | Where |
|---|---|---|
| 1 | X1b and X0c accepted (`acc9dda`). C3's seed, chosen among 12 to meet its precondition, is fit to test the aggregation, its selection documented; the other 11 (FAIL in years with the signal) stay as development and alert controls: they do not estimate the population's failure rate and are not an independent confirmation | [x1b-results.md](x1b-results.md) |
| 2 | X0c's reading: the twin's depth far below the train's justifies investigating the train against the predicted measurement; it does **not** identify the cause (the twin keeps the model's variability and trend, uses the trend fitted to the noisy curve and depends on the masks, the detrending and the fit; a much inflated train depth can also give a ratio near zero; noise can also cause an ephemeris or trend error). Causes to separate: a wrong candidate, an imprecise extrapolation, an attenuation in the processing, an inflated depth | [x0c/README.md](x0c/README.md) |
| 3 | X2 revised before any realization, in two blocks: X2-A, geometry and identity (evaluator only; the synthetic truth never reaches the engine), and X2-B, the calibration of the uncertainties (decided by the standard deviation); realizations with a wrong candidate stay in the denominators and the report | [x2-declaration.md](x2-declaration.md) |
| 4 | No identity gate and no new reference given to the engine; identity is diagnosed (X2-A). Comparing the train with the global search's candidate could break the independence contract (that search may have used the hidden year); a truly independent external ephemeris would be another information contract, close to the directed mode, with its own specification and validation | [x2-declaration.md](x2-declaration.md), section 2 |
| 5 | An external Kepler or TESS reference must name the procedure and the data it used; a general precedent validates no gate here | [sources/](sources/) |
| 6 | Before X2 runs: the resumption condition (a lot interrupted and relaunched gives records byte for byte equal to a continuous run's); if not resumable, specified and tested first | [x2-execution-package.md](x2-execution-package.md) |
| 7 | Then X2's execution package comes back for the maintainer's authorization, and the work stops. X3's definitive calibration waits for X2's result. No threshold or gate changes only to correct the old cases | [x2-execution-package.md](x2-execution-package.md) |
| 8 | heavy-a's CI duration checked against the 15-minute target per job | [x2-execution-package.md](x2-execution-package.md), section 6 |

**X2 ran** on 2026-10-22 as authorized (8000 curves, 4.03 h, no failure); its results, development
evidence only: [x2/README.md](x2/README.md).

## After X2 (the maintainer's decisions of 2026-10-22)

| Item | Decision | Where |
|---|---|---|
| 1 | The decision-2 error model: its **specification** authorized (not the code), testing the `m_β` hypothesis explicitly | [spec-c-error-model.md](spec-c-error-model.md) |
| 2 | The extension of the cells without variability: its execution package, before the correction's code | [x2e-declaration.md](x2e-declaration.md), [x2e-execution-package.md](x2e-execution-package.md) |
| 3 | The attenuation in the processing recorded as the next front; the hidden year's detrending read, nothing changed | [attenuation-front.md](attenuation-front.md) |
| 4 | The evaluator's stored intervals fixed with its own test; X2's recorded results unchanged | `tests/test_x2.py`, [x2/README.md](x2/README.md) |
| 5 | The Dependabot alerts listed and a treatment proposed; nothing changed or dismissed | [dependabot-2026-10-22.md](dependabot-2026-10-22.md) |
| 6 | X2's lot records archived on the Drive (manifest checked), then removed from `.cache` | [x2/README.md](x2/README.md) |
| 7 | X3 waits for the error model's correction | |

**X2e ran** on 2026-10-22 as authorized (4000 curves, 0.92 h, no failure): pooled with X2, `ρ_2` is
overestimated in the two cells without variability too, so in all four cells (cell-level, mixing the
regimes; see below); development evidence only: [x2/x2e/README.md](x2/x2e/README.md).

## After X2e (the maintainer's decisions of 2026-10-22; readings and proposals, nothing run)

| Item | Decision | Where |
|---|---|---|
| 1 | Spec C's eligibility with the data C6 allows: no regime eligible, no model chosen; the C4/C6 amendment proposed, the scope alternatives for the maintainer | [after-x2e/README.md](after-x2e/README.md), [after-x2e/spec-c-amendment-proposal.md](after-x2e/spec-c-amendment-proposal.md) |
| 2 | The pooled result's scope, per regime: every regime of the cells without variability unvalidated | [after-x2e/README.md](after-x2e/README.md) |
| 3 | The grid's maximum: how to tell fluctuation from real differences; what the records allow | [after-x2e/README.md](after-x2e/README.md) |
| 4 | Measurement FAIL and "wrong candidate" apart from the engine's false FAIL | [after-x2e/README.md](after-x2e/README.md), [x2/README.md](x2/README.md), [x2/x2e/README.md](x2/x2e/README.md) |
| 5 | One prospective package (proposal; not authorized) | [after-x2e/prospective-package-proposal.md](after-x2e/prospective-package-proposal.md) |
| 6 | Dependencies: reachability read, early correction and a frozen comparison environment proposed; nothing changed | [after-x2e/dependencies-reachability.md](after-x2e/dependencies-reachability.md) |
| 7, 8 | Attenuation its own front; the historical FAIL kept; X3 waits | |
| 9 | Joint objectives, the effort ceiling and the viability check (proposal); the ideas issue (draft, not opened) | [after-x2e/success-viability-effort-proposal.md](after-x2e/success-viability-effort-proposal.md), [after-x2e/ideas-issue-eb-variability-draft.md](after-x2e/ideas-issue-eb-variability-draft.md) |
