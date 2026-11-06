# A0 verdict: **WEAKENED**

The round-1 changes fix the shortcut’s goal, event ordering, and the observable sabotage condition. One critical estimator inconsistency remains, and A0.7 still needs a small design clarification before I can mark A0 **SURVIVED**.

1. **Critical, the stated cross-correlation calculation is not Pearson correlation.** The text standardizes each window by its stratum’s mean and standard deviation over the whole sector, then defines \(r_{k,a,b}\) as the sum of paired products divided by the pair count. Those whole-sector standardizations do not ensure that the *lag-selected pairs* have zero means and unit variances. So this calculation is a cross-moment, not necessarily a correlation in \([-1,1]\). The phrase “pooled Pearson correlation” conflicts with the explicit formula. The same ambiguity affects pooled \(r_k\) and the bootstrap differences.

   **Exact text change:** Replace “the sum of the products of the standardized values over all such pairs … divided by their number” with the Pearson correlation computed over the pooled paired values: subtract the paired-sample means and divide the centered cross-product sum by the two centered sums of squares. Define pooled \(r_k\) with the same estimator, and recompute both correlations inside each bootstrap replicate.

2. **Important, A0.7 does not ensure the edge windows actually belong to partial-coverage strata.** “Centre lies within 1 day of a segment edge” does not by itself imply partial coverage; that depends on the event-window width and the coverage cutoffs. Also, the stated total variance for the sum of two AR(1) components is \(\sigma_r^2\) only if their covariance is zero.

   **Exact text change:** Define the edge condition by the window’s resulting coverage stratum, or specify the relation between segment-edge distance, window width, and coverage cutoffs that guarantees partial coverage. State that the two AR(1) components are independent, or specify their covariance and adjust the component variances accordingly.

The revised equivalence rule is appropriately framed as an equivalence check, and the fallback to pair-specific estimates is clear. The 200-replicate block bootstrap and the forced-pooling pull-band condition are now explicit. After the two changes above, I’d consider A0 suitable for **SURVIVED**, subject to its required A0.7 results.

# Duration measurement

Your proposed report covers the key comparisons. **One addition:** show the counts and uncertainty bounds needed to assess the actual gates, not only the fractions. For P and PG, report D2’s kept/eligible rate and REFUTED/eligible rate with its upper Wilson bound, under each alternative. For binary cases, include the denominator and uncertainty around the detectable fraction and warning rate. Keep the results separated by impact parameter and report the per-geometry effect’s size, including non-positive excesses. That makes it possible to distinguish weak warning power from a sensitivity definition that excludes most of the cases.

The development-only comparison without retuning is the right basis for the next recommendation.

