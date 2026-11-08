## Verdict: WEAKENED, round 2 of at most 3

**Objections 1, 2 and 5 are answered. Objections 3 and 4 remain partially open.** I found no new defect in the four arms, masks, dispatch or reference construction.

The code now gates all 16 constructions separately using actual A0 empirical errors, counts availability disagreements, preserves paired curve resampling and event identities, and separates records by fingerprint. The descriptive decision wording is appropriate.

I confirmed 24 existing smoke records with no recorded errors. No E1 units were executed during this review, no files changed, and the prohibited directory was not accessed.

## Remaining objections

### 1. Medium: availability still lacks the promised uncertainty

**Evidence:** The [design](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e1-design.md:52) promises intervals for every measure and its paired contrast. However, [_cell](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e1_mask.py:337) computes only point estimates for `fraction_with_an_error` and `availability_minus_A`. Neither receives a bootstrap interval.

**Exact change required:** Store each curve’s availability numerator and denominator. Using the existing shared bootstrap draws, recompute their pooled ratio for each arm and its paired difference against A. Report both 95% intervals. Treat a zero denominator as unavailable, rather than converting it to zero availability with `max(..., 1)`.

### 2. High: undefined statistics can still produce an evaluated decision

**Evidence:** [_stats](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e1_mask.py:293) divides by `n` and `n−1` without checking sample sufficiency. The [validation loop](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e1_mask.py:428) checks retained event values, but an empty collection passes vacuously. Derived statistics and bootstrap intervals are not checked.

An in-memory check using the actual summarizer, with a complete synthetic schedule and passing reference gates but no retained events, returned:

- `state: EVALUATED`
- `prespecified_development_pattern_observed: false`
- No reasons, despite `rho` being NaN.

Thus insufficient measurement can be reported as a pattern not observed. JSON serialization also permits nonstandard `NaN` values.

**Exact change required:**

- Guard insufficient event counts and zero denominators before calculating statistics.
- Freeze a minimum number of contributing independent curves and a policy for undefined bootstrap replicates.
- Require finite, defined decision statistics; insufficient measurement must yield **NOT ESTABLISHED**, with the affected arm/cell identified.
- Serialize undefined quantities as `null`, and use `allow_nan=False` to prevent silent invalid output.

**The reference comparison, J justification, fingerprint isolation and numerical decision thresholds need no further change from this review.**

