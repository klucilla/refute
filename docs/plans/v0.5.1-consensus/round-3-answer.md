## Verdict: SURVIVED

I agree to adopt the scope. All six round-two objections are resolved by the revised plan.

1. **Composite-null and conditional D1 bound, resolved.** WP1 is now explicitly a diagnostic forecast, not a target decision. It also acknowledges that D1 is conditional on search and eligibility, and that its metric counts SURVIVED only. Any later infeasibility case must address the actual end-to-end conditional experiment jointly with D2. The simple-hypothesis Neyman–Pearson calculation is no longer presented as a bound on that experiment. [Plan, section 4](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:141)

2. **Cramér–Rao and T2a floors, resolved.** The plan now treats them as indications, not bounds that settle a target. That is appropriate: the classical Cramér–Rao bound does not establish the behavior of a rule that uses an estimator’s reported error, and the plan now says so. [MIT estimation notes](https://web.mit.edu/gallager/www/papers/chap4.pdf) [Plan, section 4](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:145)

3. **Bootstrap decision rule, resolved.** The bootstrap percentile no longer determines feasibility or settles any target. This removes the concern about its coverage and post-result choice affecting an infeasibility decision.

4. **Combined gates and warning pathway, resolved.** The first sabotage run is now screening only. If a change is removed, the reduced configuration is accepted on a second, fresh seed set; the final confirmation remains separate. The duration warning has a defined false-warning acceptance criterion, and SURVIVED-to-WEAKENED transitions are reported separately. [Plan, combined gates](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:103) [Plan, EB route](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:128)

5. **`period_alias`, resolved at scope level.** The proposed fix corrects the penalty for searched box parameters, keeps the pre-data sensitivity rule, forbids conditioning on the observed statistic, and requires both planet false-failure and sinusoid power checks on the full chain. The exact calculation must be frozen in the acceptance section before code, as the plan requires. [Plan, WP3(c)](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:97)

6. **Folded-binary geometry, resolved.** The route now distinguishes unequal-depth binaries, near-equal-depth binaries, and binaries found at their true period. The odd/even comparison is specified at the found period for alternating eclipses. [Plan, section 3a](/C:/Projetos/refute/docs/plans/v0.5.1-plan.md:122)

## Adoption

**Yes, adopt the scope.** I have no remaining scope objection. The acceptance sections still need to freeze their detailed procedures before code, but that is already a stated gate, not a reason to withhold adoption.

The current plan’s consensus record ends with Round 2. After this decision, its Round 3 outcome should be added to the record. I made no changes.

