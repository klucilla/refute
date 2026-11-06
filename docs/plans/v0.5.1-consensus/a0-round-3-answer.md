## A0 verdict: WEAKENED

The two round 2 corrections are present. The finite-sample weights now appear in `n_eff`, and A0.4 has the specified group strata, pull bands, and failure consequence.

One issue remains: **the group covariance rule does not define which autocorrelation to use for events with different coverage.** Per-event `r_k` is defined from pseudo-windows in the same coverage stratum as that event. But the group formula sets `rho_ij = r_k` for any two events in a segment, including the unequal-coverage cases explicitly tested by A0.2 and A0.5. When events `i` and `j` have different coverage strata, the text does not say whether to use either event’s `r_k`, pool strata, or estimate a cross-coverage correlation. Those choices can produce different group errors and different verdicts.

**Exact text change:** Define the coverage-specific cross-correlation used by group statistics, for example, `r_{k,a,b}` as the correlation at grid lag `k` between pseudo-window values from coverage strata `a` and `b` in the same sector and segment, paired at available grid positions. Then define `rho_ij = r_{k,c_i,c_j}` for events in that segment. Add the mixed-coverage group pulls to A0.2 and A0.5. If the required cross-coverage correlation cannot be estimated, or the resulting group variance is invalid, the decisive test must be INCONCLUSIVE.

This needs to be fixed before code because it determines the error used by WP2 and WP3 group statistics. Leaving the choice to implementation would make the acceptance rule non-reproducible and could allow different verdicts from the same data. The acceptance run can check a frozen rule, but it cannot choose one after the code is written.

Since this is round 3, A0 is not adopted on my review. The unresolved covariance definition and this objection should go to the maintainer under the agreed stop.

