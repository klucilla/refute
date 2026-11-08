**Verdict: WEAKENED, round 2.**

Round-1 objections **2, 4, 5, 6, 7, 8 and 9 are materially addressed**. Objections **1 and 3 remain partly open**.

I verified the revised E3 figures, including `extra6`; all 200 cache dispositions and their sizes; and the ledger’s recorded costs. Its known total is **5.54989 processor-hours**, with unmeasured overhead explicitly disclosed. Judgments (a) and (b) remain unchanged.

### Remaining objections

1. **HIGH: The validation gate relaxes the declared error requirement.**

   **Evidence:** [README, validation criteria](C:/Projetos/refute/docs/validation/v0.5.2/stage1/README.md:149) permits simultaneous coverage down to **0.925** and familywise incorrect permission up to **0.075**, despite specifying familywise error **0.05**. The per-cell 0.05 condition does not repair this familywise relaxation.

   **Required change:** Keep 0.925/0.075 only as diagnostic screening thresholds, not successful validation of the declared procedure. Define a permission-granting validation gate consistent with **0.95 coverage and 0.05 familywise error**, using sufficient simulation precision or a conservative internal error allocation. Explicitly enumerate both mean boundaries, both scale boundaries, nearby alternatives, and defective-cell mixtures. State whether certification probability is required to reach the worksheet’s 0.90 or merely the proposed 0.80.

2. **HIGH: `_row` mistakes event-pull availability for contributing-curve availability.**

   **Evidence:** [worksheet_reprice.py](C:/Projetos/refute/docs/validation/v0.5.2/stage1/worksheet_reprice.py:74) assigns A0.8 event availability as `min(available / 100, 1)`.

   A concrete counterexample is `correlated/full/2.5/excluded`: the source records **233 event pulls**, while the corresponding run has only **26 excluded curves out of 100**. Under the script’s own run-mapping assumption, its contributing-curve fraction cannot exceed **0.26**, yet `_row` assigns **1.0**. It therefore retains this row at floor 0.50 and prices 3,300 scheduled curves where even the point-estimate calculation requires at least **12,693**.

   A0.1’s unconditional assignment of availability 1.0 is likewise not established by event counts. Calling these conversions conservative is incorrect.

   **Required change:** Obtain distinct contributing-curve counts per member from existing records, preserving stratum and branch membership. If unavailable, report bounds or unresolved costs. Recompute the floors, family counts, prices, grouping and expansion scenarios. These errors affect the new table, not just its commentary.

3. **MEDIUM: “Units needed” supplies expected counts, not the stated fixed-design delivery of T curves.**

   **Evidence:** [_price](C:/Projetos/refute/docs/validation/v0.5.2/stage1/worksheet_reprice.py:116) uses `T / observed_availability`, without integer rounding, availability uncertainty or an allowance for random counts in the new run. Even with availability known exactly, this generally delivers **T contributing curves in expectation**, not with a specified high probability.

   The availability floor selects rows to price. It does not establish that they are measured or accepted.

   **Required change:** Either label the table explicitly as an **expected-count cost scenario**, or preregister integer schedules with a stated probability of obtaining T contributing curves, accounting for availability uncertainty and multiple required rows. Retain insufficient rows as NOT MEASURED. Explicitly preserve the requirement that operational permission needs **every applicable required member**, including noise models and branches; dropping a member at a floor cannot waive that requirement.

   Also label `CPU-hours / (22 × 24)` as **ideal fully occupied 22-worker equivalent days**, rather than an established wall-time forecast.

4. **MEDIUM: Several details of the inference specification still need correction or freezing.**

   **Evidence:** [README, estimators and bootstrap](C:/Projetos/refute/docs/validation/v0.5.2/stage1/README.md:131):

   - With the stated `V = Σ residual²/(n−1)`, the proposed variance contributions satisfy **`Σ U_i = −V`**, rather than zero. This is a small asymptotic discrepancy, but the finite-sample convention and claimed reduction need clarification.
   - A finite eighth moment is presented as universally required for studentization. The cited theorem instead requires consistent studentization and bootstrap approximation; it does not establish that blanket requirement. [Romano and Wolf, §4.1](https://users.ssc.wisc.edu/~behansen/718/RomanoWolf2005.pdf)
   - “Past 1.1” still does not specify a positive minimum effect distance at which sabotage power can be planned as 0.90.

   **Required change:** Use coherently centred variance contributions, for example with `V_n = Σ residual²/n`, or document the finite-sample adjustment and first-order approximation. Describe the eighth-moment condition as a deliberately chosen sufficient assumption if that is intended, with appropriate cluster-level conditions. Specify each sabotage’s baseline and positive violation distance before its power calculation.

   Freeze the quantile convention explicitly: for 2,000 independent bootstrap replicates, the proposed one-sided 95% upper-rank construction gives **order statistic 1,917**, using  
   `k = 1 + BinomialQuantile(0.95; 2000, 0.95)`.  
   The infinite-root rule is conservative as written; specify observed-error failures too, and that **11 or more** degenerate replicates trigger NOT MEASURED.

### Checks that passed, with their limits

- **Historical spending:** **100.742526 hours** without sabotages and **101.871541** including them are correct. The difference from 64.926432 is real. Attribute it to differing workloads and worker counts collectively; their individual causal contributions were not isolated.
- **Sizing:** The reported **3,700–3,800** values are supported by the original independent-Gaussian sizing model, conditional on the stated family counts. A separate numerical integration gives approximately **0.9089, 0.9021 and 0.9137** certification probability at the respective selected sizes. Those family counts need recalculation after objection 2.
- **Grouping:** `_price` correctly takes a maximum over the grouped coverage runs and leaves A0.7 and p3 ungrouped. This remains conditional on the stated, unvalidated envelope.
- **Baseline minimum:** Charging the old run size even when no row clears the floor matches the declared rule. Identify this retained diagnostic expenditure explicitly.
- **Sector expansion:** **34/9** is the stated linear-exposure calculation. Clarify that it holds availability, per-curve targets and cost-per-sector assumptions fixed; it does not establish the expanded family’s required sizing.
- **Small numerical correction:** A0’s measured processor-cost increase is approximately **47–99%**, rather than 50–98%.