# A0 verdict: **SURVIVED**

Both round-2 objections are resolved in the current diff:

- \(r_{k,a,b}\) and pooled \(r_k\) now use paired-sample Pearson correlations, with the means and centered sums defined, and both are recomputed inside each bootstrap replicate.
- A0.7 assigns the added long-timescale noise using the candidate’s actual partial-coverage windows, specifies independent AR(1) components, and preserves equal marginal standard deviation across strata.

The earlier objections also appear resolved: the shortcut requires intervals to fit inside a fixed equivalence margin; lag direction and sign are defined; invalid covariance matrices or variances force INCONCLUSIVE; and forced pooling has a measurable failure condition.

I found no remaining issue that needs a text change before code. A0 is acceptable for adoption under the stated rule: its code may start after this **SURVIVED** verdict, with the required A0 pull and shortcut checks still to pass in the acceptance run.