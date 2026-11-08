**Revision 3 resolves the main conceptual disagreements, but several implementation and frozen-criterion defects remain blocking.** This was a read-only review; I did not run tests or experiments.

**The four proposed departures**

1. **Sizing before version-4 code: acceptable.** This follows guideline 1. A prospectively frozen adequacy check followed by STOP and recorded redesign is a legitimate way to handle a failed proxy assumption. The problem is the check’s numerical form, discussed below.

2. **Non-interrupting batches: acceptable as an operating policy.** Reserving the declared shard duration before closing dispatch respects the no-interruption instruction. An overrun must remain a recorded deviation and a persistent STOP. It is not an unconditional mathematical guarantee of a 30-minute maximum. The allowance should cover dispatch through completion, including worker initialization.

3. **New sinusoid rule: acceptable as an empirical candidate.** The upper-confidence-limit condition fixes the direction of the uncertainty problem: an uncertain residual now tends toward INCONCLUSIVE. The predeclared withdrawal of FAIL is conservative. **Withdrawal must leave the retained detection requirements binding:** rows requiring FAIL then fail their acceptance; they cannot be waived.

4. **Keeping `J = 4`: acceptable.** No further objection to that choice.

**HIGH: The adequacy check can pass a configuration that cannot deliver `G_min`.**

The schedule expects `T` contributors under the proxy. The check permits availability to fall to `0.9` of that value, while requiring at least `0.95T` contributors.

At `T = 10,000`, a passing adequacy result can therefore imply **9,000 expected contributors against a minimum of 9,500**. More trials under the unchanged schedule do not fix that contradiction. Section-level availability also conceals a failing required member or conditional branch.

The pooled fourth-moment criterion has a corresponding problem. One fragile member can deteriorate substantially while the section’s pooled moment stays within 1.25 times its reference. Marginal fourth moments also do not determine the distribution of cluster contributions when event counts and dependence differ.

**Correction:** check delivery and proxy compatibility per required member and branch. The delivery criterion must establish that the frozen schedule supplies `G_min` with the probability required by the whole-family calculation. Define tail and cluster-influence checks for the fragile constructions, with insufficient evidence producing STOP. Treat the pooled fourth moment as a diagnostic, not a certificate of reference adequacy.

Three hundred generic curves per noise model cannot reliably characterize an event originally represented once in 524 contributing curves.

**MEDIUM: The tail sensitivity is not a comparison between equally standardized reference models.**

In [plasmode_member.py](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/plasmode_member.py), changing the curve’s sampling weight does **not** recenter and rescale the resulting distribution.

Doubling its weight changes this member’s population quantities approximately to:

- Mean: **0.0162**
- Variance: **1.1349**
- Standard deviation: **1.0653**

It changes the distance to the equivalence boundary as well as the tail shape. Moreover, the reported event is only crossing the **upper variance bound at fixed `q = 4.58`**, not failure of the complete member or family procedure.

**The 90% statement may remain conditional on the explicitly declared empirical reference.** The approved interpretation does not require 90% power throughout every distribution inside the tolerances. Consequently, 0.985 does not refute that conditional statement.

**Correction:** label these results as location, scale and tail perturbations. For a tail-shape robustness comparison, restandardize each perturbed reference. Use the complete procedure if claiming family power. Remove the inference that these results establish that larger `T` buys little against tail uncertainty.

Keep the extreme curve in the original reference.

**HIGH: The selector’s validation rule can grant permission without establishing equivalence.**

Section 2 requires point estimates inside the tolerances and 95% intervals **intersecting** them. Once the point estimate is inside its own interval, the intersection condition adds essentially nothing.

A selected-sector procedure whose population scatter exceeds 1.10 can pass this rule through sampling variation. Calling the evaluation a diagnostic outside the acceptance family does not supply the missing calibration evidence for the selected-data procedure.

**Correction:** either demonstrate that the selector is covered by the existing accepted constructions, or validate its required constructions using simultaneous equivalence intervals wholly inside the tolerances, with the familywise error budget accounted for. Otherwise, those selected-data cases remain INCONCLUSIVE.

Likewise, where the sabotage specification requires an **accepted baseline**, a baseline point estimate inside the tolerances is insufficient.

**HIGH: `complete_procedure` changes the required aggregate grouping.**

The adopted scope defines additional aggregate checks by **statistic × noise model**. [complete_procedure](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/plasmode.py:373) instead accumulates them by section:

`section = comp["members"][0][0]`

This pools different statistics and noise models. A deviation in one required aggregate can be diluted by the others.

**Correction:** implement the specified aggregate keys, preserving shared-curve bootstrap weights. Use those same groups in the sizing evaluation and eventual acceptance.

The one-dataset agreement is useful evidence that the primary critical-value calculation was preserved. It does not validate the newly added aggregate checks.

**HIGH: CPU charges remain unboundedly incomplete after a crash or persistent query failure.**

Two paths in [driver.py](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:157) remain unsafe:

- Failed CPU queries retain the last value, but continuing workers can consume arbitrarily more CPU while accounting remains frozen. A monotone counter is not necessarily a conservative counter.
- An unclosed batch adds only `workers × 20 seconds`. Killing the controller does not establish that its workers stop within that interval. They can continue executing an expensive shard after the watchdog disappears. Python explicitly documents that terminating a process does not terminate its descendants. [Python documentation](https://docs.python.org/3/library/multiprocessing.html#multiprocessing.Process.terminate)

The crash test verifies that the fixed surcharge exists, not that it bounds actual consumption.

**Correction:** on accounting failure, stop dispatch and use conservative elapsed-time charging until measurements recover. Across controller failure, retain an independent accounting/watchdog owner, or refuse restart until owned workers have stopped and their complete consumption has been reconciled. Do not classify 20 seconds as the worst unseen interval without enforcing that bound.

**HIGH: STOP states are not binding on the sizing evaluator or subsequent invocation.**

[evaluate_phase](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/plasmode.py:547) checks that every shard exists, but does not require successful run completion.

If the final shard exceeds its declared limit, the driver keeps its result and returns STOP. All shards can nevertheless exist, allowing `evaluate_phase` to publish a passing size. Similarly, `execute()` does not enforce a previous shard-limit STOP before resuming.

**Correction:** persist unresolved STOP conditions and require their explicit reconciliation before continuation. The evaluator must require a valid completion state and reconciled budget/batch records, not merely complete scientific files. Add a final-shard-overrun case showing that complete bytes cannot bypass STOP.

These remaining objections concern the permitted failure paths and the frozen specification. They do not require changing the maintainer’s targets.

VERDICT: REFUTED