**1. The diagnosis is correct; the correction is suitable for a planning proxy**

I independently reproduced:

- The four historical rejections: three sector-history mismatches and one log-g mismatch.
- Agreement of each retained clause with all 41 archived walk measurements.
- The revised strata, **11/25 passing and 0/16 failing**.
- A/B/C’s revised counts and scenarios.
- All **107 target-list hashes** against the archived manifest.

**Dropping D-4 to D-6 from this proxy is preferable to inventing tolerance bands.** The problem is disagreement with the parameter source required by the domain, not a demonstrated bounded measurement error. Widening thresholds until the eleven accepted stars pass would not establish a valid approximation.

The actual domain must retain its original TIC-based thresholds. If these variables are needed for better prediction, obtain the appropriate TIC metadata under an approved procedure.

Three limitations remain:

- **D-1:** target-list membership is stronger evidence than the TOI alert sectors, but is not generally equivalent to an available SPOC 120-s light-curve product. The sector sets happen to agree for all 41 historical stars.
- **D-2:** sector-number separation is not elapsed time and does not enforce two calendar years. Sector lengths vary, including four-orbit sectors. [Official TESS observing description](https://tess.mit.edu/observations/)
- **D-7:** the script uses the first available list magnitude. Its numerical value differs from the walk’s TIC magnitude for all 41 stars, although every in-band/out-of-band decision agrees. Catalog revisions and rounding remain relevant near the boundaries.

The D-2 agreement is particularly limited: **all 41 historical cases pass D-2, and their smallest target-list sector gap is 26**. None tests the new 11-sector boundary. Changing the threshold from 11 to 12 leaves today’s A/B/C counts unchanged, but that does not validate the elapsed-time approximation.

These are possible sources of systematic stratification error, **not demonstrated errors in the reported A/B/C arithmetic**. The proxy must remain prohibited as a domain exclusion.

**2. Recommendation: none of A, B or C as written**

Correcting the domain proxy does not resolve the separate class-membership problem.

- A’s disposition does not establish which star eclipses.
- B’s comment match does not establish an affirmative, applicable target-EB classification.
- C intersects correlated information; it does not acquire independent localization evidence.

**None is the more conservative recommendation for validity.** C is smaller, but its intersection is not demonstrated to be purer. I would not recommend C merely because it removes more stars.

Any qualified version would need:

1. **Positive, attributable target evidence:** an independently catalogued target EB/candidate or follow-up evidence identifying the target as eclipsing, with unambiguous identity and applicable signal/ephemeris.
2. **A frozen conflict rule:** affirmative nearby-source evidence, uncertain attribution and unresolved identity/period conflicts cannot be converted into eligibility by the absence of a regex match.
3. **Independent human adjudication:** a reproducible audit with its rubric, sampling procedure and acceptance criterion fixed before assessment. Include ambiguous cases and relevant exclusions.
4. **Qualification before scientific outcomes:** apply the approved class rule without using Refute’s subsequent battery results to decide eligibility or replacement.

A purity audit characterizes a rule’s residual error. It does not authorize known NEBs or make unresolved stars on-target. E is not an adjudicated gold standard for measuring A/B/C purity.

**How much yield survives qualification is currently unmeasured.** Under the additional assumption that the historical passing-stratum rate remains \(11/25=0.44\) after qualification:

| Set | Never-walked proxy passers | Raw two-strata scenario | Qualified passers needed for mean 11 | Maximum losses under that assumption |
|---|---:|---:|---:|---:|
| A | 39 | 17.16 | 25 | 14 |
| B | 37 | 16.28 | 25 | 12 |
| C | 31 | 13.64 | 25 | 6 |

Thus A/B/C would need to retain approximately **64.1%, 67.6% and 80.6%** of their proxy-passing candidates, respectively.

Those are **conditional feasibility thresholds**, not measured retention, purity requirements or guarantees of eleven actual acceptances. Qualification can change the metadata-acceptance rate itself, so multiplying by an overall purity estimate is insufficient.

Also, **0/16 is an observed rate, not an established zero probability**. The output’s two-sided historical interval extends to approximately 20.6%. Likewise, 11/25 has the reported interval of approximately 24.4%–65.1%. Neither supplies a validated prediction interval for the changed populations.

**3. Required disclosure at the protocol stop**

The stop should explicitly record:

- **The development history:** the original proxy rejected four accepted stars; its sources and clauses were revised after examining those outcomes.
- **The limited validation claim:** 41/41 is agreement on the development cohort, not independent predictive validation. D-2 has no failing or boundary examples in that cohort.
- **The assumptions:** historical rates come from TESS-EB members; transport to A/B/C, and transport after class qualification, remain unvalidated.
- **The distinction between screening and eligibility:** the published counts precede class adjudication. No admissible surviving yield has yet been measured.
- **The frame change:** A/B/C alone drop 23/35/36 approved members. A replacement and an addition to the approved frame are different proposals requiring separate inventories.
- **The preregistration boundary:** all alternatives and counts already inspected belong to development. The amendment, source snapshots, qualification rules, exclusions, seed and walk order must be approved and frozen before selection. No ranking by proxy score or subsequent scientific outcome.
- **Any source-use conditions:** if contributed notes supply qualification evidence, their unresolved data-policy conditions remain applicable.

The scenario means exceeding eleven establish neither class preservation nor completed T3b coverage. If no qualified amendment is approved, T3b remains **deferred/pending, `INCONCLUSIVE`, with gate permission not granted**.

**Verdict on the diagnosis and correction: SURVIVED as a counts-only planning proxy. Recommendation among A/B/C: NONE as written.**

1. **D-2 agreement does not validate the boundary.** [t3b_alternatives_r2.py:66](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives_r2.py:66), [line 86](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives_r2.py:86). **Smallest correction:** disclose the all-positive, minimum-gap-26 comparison; use frozen dates/calendar years if a stronger proxy is required, while preserving the production product check.

2. **Target-list magnitude is not the walk’s exact TIC value.** [t3b_alternatives_r2.py:51](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives_r2.py:51). **Smallest correction:** document the first-list provenance, rounding and boundary limitation. Do not add an outcome-fitted tolerance.

3. **Zero historical failures-stratum acceptances must remain a scenario assumption.** [t3b_alternatives.py:175](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:175), [line 208](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:208). **Smallest correction:** carry the rate uncertainty and transport caveat beside the scenario; never infer domain ineligibility from proxy failure.

4. **The A/B/C class defect remains unchanged.** [t3b_alternatives.py:190](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:190). **Smallest correction:** retain screening labels; separately define, approve and count positive target qualification before claiming an admissible population or surviving yield.

5. **The comparison is development evidence.** [t3b_alternatives_r2.py:74](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives_r2.py:74). **Smallest correction:** state explicitly that the same historical outcomes informed the correction and its assessment; do not present 41/41 as independent validation.

