OBJECAO: **The declaration is broadly faithful, but not complete enough to freeze before analysis.** I found no explicit attempt to tune toward passing. The main risks are unspecified denominators, treatment of undefined values, and statistical choices left to implementation.

This was a read-only source review at `9b892006e75bc1bc40e1379622a5c887c4a71a2a`. No diagnosis, engine run, or file modification was performed.

1. **Q8 must distinguish evaluable targets from decided targets.**  
   [DECLARATION.md:117](docs/validation/v0.2.1/reopen/rmin-study/diagnosis/DECLARATION.md:117) defines safety among decided targets. However, study eligibility includes measured `not_detected_not_inconsistent` rounds, and an eligible target can remain INCONCLUSIVE ([holdout.py:1717](src/refute/packs/tess/holdout.py:1717), [rmin_evaluate.py:152](docs/validation/v0.2.1/population/rmin_evaluate.py:152)).

   **Declare separately:** total targets, study-eligible targets, decided targets, and errors. Report error/eligible, error/decided, error/total, and decided/total with explicit denominators. The all-population error fraction is error frequency under abstention, not evidence of safety for undecided targets. Keep the historical disappearance and weakening qualification rules identifiable.

2. **Q1 and Q2 do not fully fix reason classification or target counting.**  
   [DECLARATION.md:53](docs/validation/v0.2.1/reopen/rmin-study/diagnosis/DECLARATION.md:53) references `classify.py` for reason parsing, but that script classifies criterion failures. The reason parser is actually [summarize.py:19](docs/validation/v0.2.1/reopen/rmin-study/study/scripts/summarize.py:19).

   G3 also combines undetermined hidden noise with insufficient hidden replicas, although the recorded fields permit separate subcategories. `derive_round` intentionally gives them the same outward reason ([holdout.py:1737](src/refute/packs/tess/holdout.py:1737)).

   **Declare:** the exact parser or mapping, preservation of raw reasons, unknown-kind handling, and G3 subcause precedence, including overlaps. For targets, specify whether interruption counts mean:
   - Aggregated INCONCLUSIVE targets, counted once by their combination of reason kinds.
   - Any target with an interrupted round, including targets ultimately PASS or FAIL.

   The existing evaluator uses the first convention ([rmin_evaluate.py:192](docs/validation/v0.2.1/population/rmin_evaluate.py:192)). Also specify full `<prefix>/<case id>` identity, gate-reach versus population denominators, and target reducers for round-valued Q3 quantities. Otherwise different implementations can produce different “per target” tables.

3. **Q3’s algebra is valid, but its two capacity categories are not exhaustive.**  
   The proposed reconstruction matches the implementation: `d_c = d_train − e_train`, and finite, nonzero `S_pred` permits `e_pred = d_c/S_pred` ([holdout.py:1411](src/refute/packs/tess/holdout.py:1411), [holdout.py:1493](src/refute/packs/tess/holdout.py:1493), [holdout.py:1517](src/refute/packs/tess/holdout.py:1517)).

   However, capacity also rejects missing or nonfinite `S_pred`, which belongs to neither inequality category in [DECLARATION.md:71](docs/validation/v0.2.1/reopen/rmin-study/diagnosis/DECLARATION.md:71). Zero denominators or zero `S_pred` can also prevent the proposed ratios.

   **Predeclare an undefined category**, validity conditions for each ratio, and valid/invalid counts beside every quantile. Do not silently discard these cases. Describe the ratios as an algebraic diagnostic, not independent causal contributions. The unavailable variance/transit-count decomposition is appropriately acknowledged.

4. **Q5’s cluster bootstrap is appropriate in principle, but still underspecified.**  
   Resampling targets with their selected rounds preserves within-target dependence. Fixed `k = 2` and the `pair_for_r` selection also match the committed estimator ([rmin_evaluate.py:104](docs/validation/v0.2.1/population/rmin_evaluate.py:104)).

   [DECLARATION.md:88](docs/validation/v0.2.1/reopen/rmin-study/diagnosis/DECLARATION.md:88) still needs to fix:
   - Whether bootstrap clusters are the selected targets at each R or all 100 targets followed by the fixed selection. These answer different stability questions.
   - That `s* = 1.4826 MAD*`, preserving duplicate sampled clusters and round weighting.
   - That each bootstrap threshold uses the **paired** draw `(b*, s*)`, followed by threshold percentiles. Combining separate interval endpoints would lose their dependence.
   - The variance-component/ICC estimator for unequal cluster sizes, handling of negative estimates, correlation type and chronological pairing, standard-deviation convention, quantile method, and whether “beyond 3s” means `|residual − b| > 3s`.

   These are computational choices that belong before analysis.

5. **Q5 needs a direct output for per-target behaviour and mixtures.**  
   Pooled quantiles plus regime medians/MADs can conceal different residual patterns. Term 5 explicitly asks about per-target stability and mixtures.

   **Add a declared residual table** keyed by target, hidden year, R and regime, including the two-round difference where available. A fixed empirical distribution output would expose mixtures without fitting another estimator. Report empty regimes explicitly. These outputs require only existing fields; they do not justify lowering dispersion or gates.

6. **The timing parse is feasible, but the bins need a rounding policy.**  
   The reason contains both quantities to two decimal places ([holdout.py:1079](src/refute/packs/tess/holdout.py:1079)). Consequently, a genuinely stopped round can have a rounded ratio equal to 1, outside all bins declared at [DECLARATION.md:68](docs/validation/v0.2.1/reopen/rmin-study/diagnosis/DECLARATION.md:68).

   **Declare** handling for ratios at or below 1, zero printed duration, parse failures and boundary ambiguity. Label these as bins of the rounded textual ratio. Keep every such round in the timing-stop total.

7. **Add an explicit multiple-comparison limitation.**  
   “As descriptions only” at [DECLARATION.md:123](docs/validation/v0.2.1/reopen/rmin-study/diagnosis/DECLARATION.md:123) is helpful but insufficiently precise. Amendment 19 already says its 0.99 bounds do **not** make all intervals jointly 95% ([implementation map:2077](docs/validation/v0.2.1/reopen/m4-implementation-map.md:2077)).

   Declare no simultaneous guarantee across the expanded cuts, no significance-based subgroup selection, no binomial intervals treating rounds as independent, and no validation claim from the bootstrap.

8. **Exploratory separation is present, but its operating boundary should be explicit.**  
   [DECLARATION.md:7](docs/validation/v0.2.1/reopen/rmin-study/diagnosis/DECLARATION.md:7) already requires a separate `exploratory.md`. Add that incidental findings cannot change declared cuts, denominators, outputs or conclusions. An undeclared follow-up calculation should remain an unexecuted proposal pending a separate declaration, rather than becoming automatically permissible because its output is labelled exploratory.

**The requested feasibility checks otherwise hold:**

- **Labels:** recoverable without RNG or curves. Explicitly state `_few_train_extra(index − 150, 50)`, as used by [population_v2.py:299](docs/validation/v0.2.1/population/population_v2.py:299). These are generator design labels, not recovered transit counts.
- **Geometry and identity:** full injected geometry and candidate identity are unavailable. Q4/Q7 appropriately disclose that limitation. Narrow Q2’s wording to *injected geometry*: measured `d_train` exists, and rounded recovered duration exists for timing-stopped rounds.
- **Weakening:** Q6 correctly preserves the maintainer’s scientific choice and the PASS-before-depth-test ordering. Clarify that Q8’s unlabelled weakening fractions are descriptive outputs, not substitute criteria.
- **Later delivery:** lines 127 through 135 retain the requested correction/refutation structure and single next-step proposal.

**Recommendation:** revise the declaration before freezing it. Terms 0, 1, 2, 3, 5 and 8 need the specifications above; terms 4, 6 and 7 are substantially faithful. The proposed cuts themselves show no evident tuning toward PASS, but the remaining discretion could permit selective omission. The maintainer retains the final decision.

