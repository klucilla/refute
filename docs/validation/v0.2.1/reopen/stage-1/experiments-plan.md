# The experiments needed, in order, with their estimated cost

The maintainer's decision of 2026-10-21: the plan of the experiments needed, each with its
estimated cost. **None is authorized by this plan.** The calibration, the pilot and the main study
each need their own criteria, budget and authorization; each experiment below has its own
declaration (questions, sizes, criteria) committed before it runs.

**The cost unit, measured:** the R_min study ran 76 800 light curves in 45.24 h on 6 workers
(processors 0 to 7): **12.7 worker-seconds per light curve**, or about **1700 light curves per hour
on 6 workers**. Since the v0.3 seal the lots may use the project's default workers; the gain is
measured on the first lot that uses them, not assumed. The hours below are at 6 workers.

| # | Experiment | Needs | Size (planning) | Cost |
|---|---|---|---|---|
| X0a | Read-only declaration: where the 26 false PASS come from (exploratory proposal 1 of the diagnosis): per disappearing PASS target, the year and SNR of its passing rounds and the gate of its last round | the existing records | the R_min lot's 76 800 records | minutes, no curve |
| X0b | Read-only declaration: specification B applied to the existing records, to show the rise of INCONCLUSIVE it causes (development evidence, not validation) | the existing records | the same | minutes, no curve |
| X1 | The instrumentation (acceptance record of this stage): code and tests | this stage's acceptance record | tests only | CI only |
| X1b | Specification B's code (the aggregation) and its controls C1 to C6 | its own acceptance record (from spec B) | a few synthetic cases | CI only |
| X2 | Is `e_pred` inflated? `e_pred` against the empirical scatter of the hidden-year depth over repeated noise realizations, in four disjoint cells (white without variability, white with, AR(1) without, AR(1) with), with a tolerance declared before | X1 accepted | 20 cases per cell × 100 realizations, constant scenario: 8000 curves | **≈ 4.7 h** |
| X3 | The b/s calibration lot (independent): new seeds; targets as the unit, with **the one round per target selected before** (by a rule fixed in its declaration, never by its outcome); its size from a declared precision of the **threshold** `min_snr − b + z·s` (which depends on `b` and `s`), checked by a cluster bootstrap; the regimes by quantities the engine observes (for example the number of observing years), defined before; never the estimator that admits more cases | X1 accepted | for planning only: about 520 rounds per regime give `s` to ±10% at 95% under the normal approximation for a MAD-based `s` (not a distribution-free guarantee); if about 40% of the targets reach the complete selected set (bs-choice's rate at R = 8, the `k` set with each R's replica restriction), about 1300 constant targets per regime; two regimes: about 2600 curves | **≈ 1.5 h** |
| X4 | The mandatory compatibility check: for the calibrated `(b, s)`, every filter of every criterion (spec A's classes, the eligibility of each criterion) has a non-empty window at each number of years, with its numbers; an empty one stops the study | X3 | arithmetic | minutes, no curve |
| X5 | The pilot: the yields per group and scenario (eligible, decided, qualified, the classes of spec A) with the corrected gates and spec B; its precision, sizing rule, ceilings and **the scope rule** declared before its numbers are read | X1, X1b, X3, X4 | for planning only, the pointwise normal approximation: the smallest yield seen in the R_min lot, 0.64% (41 decided of 6400 disappearing targets in `white, variability`), to ±25% at 95% needs about 9500 targets of that group; a yield of 1.3% needs about 4700. With 9500 targets per group, 4 groups × 3 scenarios: about 114 000 curves; with 4700, about 56 400. Spec B and spec A's classes bring new, unknown yields; the pilot's declaration fixes which yield drives its size | **≈ 67 h** (9500 per group) or **≈ 33 h** (4700 per group) |
| X6 | The main study: seeds from a future drand round, sizes from the pilot, criteria fixed before (with spec B's false PASS per target and spec A's W1, W1e), the choice rule and budget fixed before; run once | X5 and the maintainer's scope decision | from the pilot; for scale, a group whose eligible yield is 1.3% needs about 66 600 targets (200 000 curves, ≈ 118 h) to reach a minimum of 866, which is why the scope rule comes first | **from the pilot** |
| X7 | The independent reserve, only if a configuration is chosen: the map's contract (seeds from a future drand round declared at the choice, the same composition and sizes, the pairs frozen, no second R after a failure) | X6 | the same as X6 | **the same as X6** |
| later | A depth-stability test (dilution, aperture, contamination): its own specification | spec A, A1 | not planned | not estimated |
| later | T4 (map Amendment 28): its own pilot of its own population (the two-year layouts) and path, after a chosen `R_min` | X6, X7 | from its own pilot | not estimated |

**The scope rule (item C of 2026-10-21)**, part of X5's declaration: fixed before the pilot, by
quantities the engine observes. "No train fundamentals detected" is not "no variability": the
validation covers the operational boundary chosen, including its misclassifications (a variable star
whose fundamentals go undetected is inside it). If the scope shrinks, the validated population and
where the result stays INCONCLUSIVE are published exactly; that is not the validation of the
original four-group claim. No automatic exclusion.

**The dependencies, explicit:** every lot that relies on the new fields (X2, X3, X5) needs the
instrumentation accepted first (X1); if X2 leads to a change of the error model, the instrumentation
and the calibration are accepted and run again before X4; X4 establishes algebraic compatibility
only, X5 the practical yields; X6 needs X5 and the maintainer's scope decision; X7 needs a chosen
configuration.

**Not assumed:** that separating `b` and `s` by regime lowers the thresholds (it may raise some; the
pooled `s` of 2.88 sits between 2.13 for three-year curves and 7.71 for two-year curves); that more
workers give a proportional gain; that the pilot's yields equal the main lot's.
