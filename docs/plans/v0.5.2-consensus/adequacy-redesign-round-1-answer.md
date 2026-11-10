**The prospective redesign and STOP are sound.** There is a cheaper targeted-pilot option worth pricing, but the current evidence does not establish that it fits the complete 3,100 CPU-hour budget.

1. **HIGH: The current fresh-check options require STOP.**

   I reconciled stage expenditure to **155.05 CPU-h**, including previous attempts. The other six lines sum correctly to **1,226 CPU-h**.

   Using the supplied 85 CPU-hour fresh-check estimate:

   | Sizing | Total CPU-h |
   |---|---:|
   | Point | 2,970.8 |
   | Per-member lower bound | 3,109.6 |
   | Family lower bounds | 3,397.8 |
   | Per-member lower bound, in-sample check | 3,045.6 |

   **Required:** retain STOP for the fresh-check `lower` and `lower_family` options as currently priced. Do not round 3,109.6 down to the ceiling. Update `budget.md`, executable budget allocations and the ledger consistently before launching a redesigned workload. Removing the crash surcharge from the unit-cost estimate is reasonable; it must remain in expenditure already incurred.

2. **LOW: Per-run sizing genuinely equals component sizing here.**

   The tables contain **717 components and 717 runs**: every component contains exactly one run. Consequently, taking the maximum factor over that run’s members equals taking the component’s maximum. No global enlargement beyond the member requirements is necessary.

   The JSON nevertheless reports **9,770,215 versus 9,770,216 curves** for `global` and `point`. This is floating-point ceiling arithmetic, not a substantive scheduling difference.

   **Required:** use exact integer arithmetic for the point rule:

   `N_r = max_m ceil(9000 × n_r / g_m)`

   Record the equivalence as a property of this table, not a general requirement for future components.

3. **MEDIUM: Choose the availability assurance explicitly; acceptance FWER does not choose it for you.**

   A one-sided 95% lower bound **per member** is a defensible planning margin. It does not provide 95% simultaneous coverage across 2,293 members. Conversely, the acceptance’s familywise 0.05 requirement does not automatically require Bonferroni confidence bounds on these planning quantities.

   **I would permit `lower` as a planning rule, combined with the unchanged independent whole-family adequacy gate.** I would not describe it as an analytic guarantee of family-wide delivery.

   If an analytic delivery guarantee is wanted, specify separate confidence and delivery budgets. For these single-run components, a possible construction is:

   - Obtain appropriately simultaneous lower bounds `p_L,m`.
   - Choose each run’s size so that, for every carried member,
     `P(Binomial(N_r, p_L,m) < 8550) ≤ δ_m`.
   - Require `sum δ_m ≤ δ`, with `δ` fixed prospectively.

   **Required:** distinguish confidence about availability from future count fluctuations. The 0.95 fraction supplies retention headroom; it does not authorize replacing the 9,000 target with 8,550. If “at least T expected contributors” remains a required sizing condition, retain that constraint alongside any prediction-based rule.

4. **HIGH: Freeze absolute run sizes before the fresh check.**

   Your fresh-records proposal is the right separation: estimate availability on the failed check’s development records, freeze the sizing rule and schedule, then assess that schedule against independently generated records.

   **Required:** freeze an explicit manifest of absolute `N_r` values. The fresh reference must be sampled at those sizes. Do not recompute the factors from its own availability or transplant training `min_g` values into a table with different source counts.

   This matters particularly after a pilot: training might contain 1,000 curves in an event run while the fresh check contains 100. Rescaling by the wrong table’s denominator would change the intended schedule.

   Preserve the exact 2,293-member family, `T = 9000`, `G_min = 8550`, bootstrap procedure, evaluation bound and failed historical result. Use new curve and draw labels.

5. **MEDIUM: A targeted A0.8 event pilot is substantially cheaper than the broad pilot.**

   I independently calculated this **what-if**, retaining your per-member 95% lower-bound rule and assuming the observed availability proportions persist:

   | Item | CPU-h |
   |---|---:|
   | Acceptance after increasing only A0.8 event training runs to 10× | 1,603.8 |
   | Additional pilot | 8.2 |
   | Previously spent | 155.1 |
   | Other lines | 1,226.0 |
   | Fresh check | 85.0 |
   | **Total** | **3,078.0** |

   This pilot covers **45 runs and 40,500 additional curves**, rather than 352 runs and 1.38 million additional curves.

   **Required:** treat 3,078 as a prospective scenario, not demonstrated affordability. The pilot must use actual new records. Multiplying existing success counts by ten is legitimate for this forecast, not for reporting narrower confidence intervals as measured evidence.

   Pooling the failed check’s records with new **training-pilot** records is legitimate. If advertising exact confidence coverage after data-dependent sample expansion, account for that sampling rule, or use an independently fixed pilot sample for the bounds.

6. **HIGH: The targeted option has insufficient headroom to leave schedule-dependent costs unchanged without verification.**

   Its approximately **22 CPU-hours of headroom** is small relative to the unmeasured lines. The targeted schedule contains about **10.323 million acceptance curves**, roughly **6.8% more** than the original schedule.

   The nested adequacy evaluation and known-answer gate reproduce the relevant sampling layout. Their costs therefore need reassessment under the proposed schedule. As an illustration, scaling 820 CPU-hours by 6.8% adds about 55 hours, already exceeding the apparent headroom. That is a sensitivity calculation, not a measured forecast.

   Section-wide mean curve costs also conceal changes in the mix of event, group, noise and sector constructions.

   **Required:** reprice the known-answer gate, redesigned check and materially changed A0 workloads, including pilot and pricing costs. Preserve the prescribed planning allowances and stops. A measured reduction in an estimated line is legitimate; simply reducing its reservation to cross the ceiling is not.

7. **MEDIUM: An in-sample check cannot replace the proposed independent assessment.**

   New resampling seeds on the same records assess conditional performance under the fitted empirical availability distribution. They do not independently test the fitted availability estimates.

   **Required:** keep those results diagnostic. If fresh records are pooled into sizing, reserve a separate untouched record set for evaluation. Otherwise the proposed out-of-sample protection disappears.

8. **LOW: Correct the diagnosis’s deterministic wording.**

   The 102 members have **expected contributor counts below `G_min`** under the old schedule. That does not mean all 102 fall below it in every resampled dataset. The observed minimum of 91 unmeasured members already demonstrates the distinction.

   **Required:** correct that label while retaining the failure and observed counts. Also preserve the distinction between passing this standardized-reference check and calibrating the original version-4 errors; the latter still requires acceptance.

WEAKENED