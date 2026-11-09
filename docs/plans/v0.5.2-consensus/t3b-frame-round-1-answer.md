**The counts support further feasibility work. They do not establish an admissible expansion of T3b that reaches 11 expected acceptances. I would take no A/B/C amendment to the maintainer for adoption yet.**

**1. Class preservation**

**A, B and C do not reliably preserve “an eclipsing binary on the target.”**

- **A, TESS disposition EB:** TFOPWG FP establishes rejection of the planet interpretation, while EB supplies a classification. Neither field alone establishes which star eclipses. Guerrero’s vetting table also uses EB for V-shaped events and as a tie-break between nonplanetary dispositions. It is not a localization certificate. [Guerrero et al., sections 7.1–7.3](https://arxiv.org/pdf/2103.12538)
- **B, EB-related comment:** this admits spectroscopic binaries, tentative classifications, negations and references to other stars.
- **C, both:** agreement between these fields is stronger evidence of an EB interpretation, but does not supply missing localization. The fields can also repeat the same underlying assessment.

**The surviving contaminant proportion is unknown.** The script measures lexical matches, not sensitivity or specificity against adjudicated on-target/NEB labels. Of 397 EB-disposition members, 204 match `NEB_TEXT`; that is a word-hit fraction, not a measured NEB fraction. I reproduced **four blank comments among A’s 193 survivors**. B and C require matching text, so their vulnerability is ambiguous or misleading text rather than blank comments.

Specific defects, demonstrated by constructed row kinds rather than claimed catalog quotations:

| Row kind | Failure |
|---|---|
| A comment saying `SB1`, or `not an EB` | `EB_TEXT` admits both. A spectroscopic binary need not eclipse, and negation is ignored. |
| A comment saying `SEB2 on TIC ...` referring to another star | `EB_TEXT` matches; the special `NEB_TEXT` branch matches only unnumbered `SEB on`. |
| A comment saying `SEB on target`, or reporting no centroid displacement | `NEB_TEXT` rejects affirmative on-target evidence or a negative contamination finding. |

Additionally, `EB_TEXT` misses standalone plural `EBs` and the spelling `eclipsing-binary`. Neither regex handles uncertainty, chronology, attribution or superseded conclusions.

**A frozen deterministic text rule is legitimate as an operational filter.** Determinism makes it reproducible, not scientifically valid. These expressions can support screening and conflict flags; they cannot presently certify class membership. Improving them after seeing counts requires a recorded prospective revision.

**No listed table column supplies the missing certificate.**

- `Time Series Observations` and `Spectroscopy Observations` are counts, not observation results.
- `Source` and `Detection` describe provenance or discovery pipelines.
- Depth and stellar radius can identify an implausible planet interpretation under assumptions. They cannot localize the eclipse. Calculating a companion radius from depth already assumes the signal belongs to the target.

A stronger honest rule would require **positive, attributable follow-up evidence identifying the target as eclipsing**, with the applicable TOI/ephemeris, source, date and conflict policy recorded. Unresolved cases remain ineligible. This needs evidence beyond those summary columns.

**2. Yield**

**11/41 is a historical metadata-acceptance rate, not T3b’s scientific success rate.** It is a planning reference for the remaining TESS-EB population. Transport to A/B/C is unvalidated because those definitions change the stellar and observational population.

The reported counts and arithmetic are internally consistent:

| Definition | Members | Beyond approved frame | Never walked | Flat-rate scenario |
|---|---:|---:|---:|---:|
| Current frame | 63 | 0 | 22 | 5.9 |
| A | 193 | 153 | 165 | 44.3 |
| B | 166 | 138 | 145 | 38.9 |
| C | 144 | 117 | 124 | 33.3 |

I independently reproduced the pool and membership counts from the TOI bytes, whose SHA-256 matches the manifest. The “beyond approved frame” column and “never walked” column describe different quantities.

**The proxy-conditional rate, 7/11, is a valid description of that historical subset.** Rejecting four accepted stars does not invalidate that conditional fraction. It does invalidate treating proxy failure as zero acceptance probability, or calling the proxy an equivalent implementation of the domain rules.

The script’s proxy expectations estimate acceptances **within the proxy-passing subset**, subject to transport assumptions. They are not full-population expectations.

For illustration, retaining both historical strata gives:

\[
E = N_{\rm proxy}\frac7{11}
  + (N-N_{\rm proxy})\frac4{30}.
\]

That produces **32.6, 29.4 and 26.1** for A/B/C, rather than 13.4, 12.7 and 12.1. These are sensitivity calculations, not validated replacement forecasts. They still assume transport and do not correct class contamination.

**The single forecast I would headline to the maintainer is:**

> Under the historical TESS-EB acceptance-rate assumption, the current 22-star remainder forecasts **5.9 acceptances**, with a **scaled-rate interval of 3.1–9.4**, against 11 required. Expected yield for a newly adjudicated A/B/C population is not established.

The underlying reported rate interval is **14.2%–42.9%**, a two-sided Clopper–Pearson calculation. The scaled interval describes uncertainty in the assumed mean, **not a prediction interval for the actual accepted count**. The stopped historical walk and finite remaining population also limit its interpretation. Eleven acceptances remain possible; shortage is a forecast, not proven infeasibility.

**3. Definition and safeguards before any draw**

**I would adopt none of A/B/C as written.** I would put forward a proposed **positive-evidence TFOP branch for a counts-only inventory**, with its semantic rule and evidence requirements approved before adopting it. C is a useful search subset for that work, but not an eligibility certificate.

Before any draw:

- **Identity:** require the same TIC target, with explicit handling of aliases, duplicate signals and ambiguous associations. A neighboring object’s binary classification does not transfer to the target.
- **Membership and precedence:** qualify each source independently, then take the union. Apply TESS-EB/T10K/Gaia precedence only to display labels. Preserve all memberships and conflicts.
- **Periods:** retain section 6’s frozen TESS-EB asymmetry. New catalog branches need the preregistered 1% comparison against \(P/2,P,2P\), with missing/conflicting periods handled explicitly. Comparing the TOI period with itself provides no independent corroboration.
- **Domain:** use the actual metadata/product checks. Do not replace D-1/D-2 with sector-number arithmetic or substitute TOI stellar parameters silently.
- **Walk:** freeze the input population, exclusions, seed and complete ordering before selection. Walk that order without ranking by comments, proxy score or anticipated acceptance. Preserve the transient-error stop.
- **Prior use:** exclude all previously walked stars under the existing rule, including rejected ones.

The candidate sets are **replacements**, not simple additions to the approved frame: A/B/C retain only **40/28/27 of its 63 members**. Any proposed union needs its own deduplicated inventory.

**Seeing these counts creates a design-selection opportunity, but does not automatically invalidate a later frame.** The guard is to disclose every alternative examined, justify the chosen rule by scientific meaning rather than its favorable count, record the prospective decision, and freeze it before selection. Keep future scientific outcomes unseen and use the required protocol/seed commit, selection commit and claim ordering. Do not describe this design process as blinded.

**4. Other catalogs**

Every additional count needs the same funnel: exact identity, `fp_pool`, prior-use exclusions, qualifying binary evidence, period/conflict handling, overlap with existing memberships, then unique never-walked additions. Catalog size is not that count.

| Source | Potential contribution and terms | Judgment |
|---|---|---|
| **M&M catalog, Oddo et al.** | Publishes TIC/Gaia identities and periods for 1,292 systems. Uses data through sector 55, but starts from prime-mission candidates. Its localization threshold is **20 arcsec**, and the authors acknowledge residual off-target cases. The arXiv article is CC BY 4.0; verify the complete machine-readable supplement’s applicable terms separately. | **Worth one bounded count**, after terms are established. Count target-qualified additions and domain overlap, especially temperature and brightness. No yield or positive addition is established yet. [Paper](https://arxiv.org/html/2508.13941v1) |
| **Gaia DR3 NSS** | Restrict to `EclipsingBinary` and `EclipsingSpectro`, not generic astrometric or SB solutions. The eclipsing channel takes its input from `vari_eclipsing_binary`, so this is principally a richer subset, not fresh sky coverage. Repository-recorded terms: CC BY-NC 3.0 IGO; the license page could not be refreshed here. | **Worth a small identity/period check**, especially whether model periods change qualification. Do not assume new additions or assume zero solely from subset membership. [Gaia documentation](https://gea.esac.esa.int/archive/documentation/GDR3/Data_analysis/chap_cu4nss/sec_cu4nss_intro/ssec_cu4nss_intro_inputfiltering.html) |
| **Live TESS-EB portal versus frozen MAST product** | The live portal displays later observing sectors. That alone does not establish new catalog members. The MAST v1.0 product covers sectors 1–26 and has explicit CC BY 4.0 terms; those terms should not automatically be extended to a separate live export. | **Worth checking version, terms and TIC-set difference first.** Count genuinely new memberships, not additional sectors for existing stars. [MAST product and access distinctions](https://archive.stsci.edu/hlsp/tess-ebs) |
| **T10K** | Current inventory adds **zero** qualifying FPs. Catalog terms remain unconfirmed in the repository record. | **No repeat download warranted for this decision.** Preserve the zero result and unresolved terms. |

M&M and NSS could preserve the **catalogued target EB/candidate** population if their identities and qualification rules are satisfied. Neither should be promoted to proof that the binary caused the TOI signal.

**5. Treatment of T3b if no expansion is admissible**

**Defer T3b alone as pending, with an `INCONCLUSIVE` scientific verdict.**

Record:

- Required **11 accepted stars** and **eight valid outcomes**, unchanged.
- Current inventory, input hashes, retrieval dates, prior-use exclusions and forecast assumptions.
- No new T3b selection or outcome coverage in this round.
- Reason: insufficient established feasibility under the approved population; alternative definitions remain unadopted.
- Administrative state such as `pending` or `deferred`, separately from the scientific verdict.

The gate must say **T3b has not granted permission**. Other independently supported results can be reported, but a gate requiring T3b cannot receive an overall PASS by omitting it. Preserve `method_status: not_validated` wherever the unmet requirement applies.

“NOT DECIDABLE” in the scope proposal is descriptive shortage language. It should map to **`INCONCLUSIVE`**, consistent with [CLAUDE.md:55](/C:/Projetos/refute/CLAUDE.md:55) and its [zero-coverage rule](/C:/Projetos/refute/CLAUDE.md:86), rather than becoming a new scientific verdict.

Release requires a recorded, approved prospective procedure: a sufficiently replenished qualifying pool, frozen identities/terms/inputs, the required selection approvals, 11 accepted stars and the original eight-valid-outcome acceptance criterion. A forecast reaching 11 is only a feasibility checkpoint.

**Verdict on the script and counts: `WEAKENED`.** The membership counts and arithmetic survive. Their interpretation as class-preserving populations with established sufficient yield does not.

1. **High, class membership is unestablished.** [t3b_alternatives.py:36](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:36), [line 115](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:115). **Smallest correction:** label A/B/C as screening sets; require attributable positive target-EB evidence before eligibility.

2. **High, proxy forecast omits historically productive failures.** [t3b_alternatives.py:109](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:109), [line 135](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:135). **Smallest correction:** rename it as a proxy-passing-subset scenario; report the failing stratum and prohibit its use as a domain exclusion.

3. **Medium, proxy does not implement the domain contract.** [t3b_alternatives.py:54](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:54), [selection.py:391](/C:/Projetos/refute/src/refute/packs/tess/discover/selection.py:391). **Smallest correction:** document the different parameter sources, missing calendar-year/product checks and measured false exclusions.

4. **Medium, replacement counts do not describe an expanded union.** [t3b_alternatives.py:118](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:118). **Smallest correction:** add retained/dropped approved members and separately counted qualifying union totals before presenting an amendment.

5. **Medium, interval meaning is underspecified.** [t3b_alternatives.py:77](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:77), [t3b-inventory-r2.json:7](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b-inventory-r2.json:7). **Smallest correction:** identify the interval’s method and assumptions, and distinguish mean uncertainty from prediction and transport uncertainty.

6. **High, deferral must remain an unmet gate.** [scope-proposal:213](/C:/Projetos/refute/docs/plans/v0.5.2-scope-proposal.md:213), [stage2-design:203](/C:/Projetos/refute/docs/plans/v0.5.2-stage2-design.md:203). **Smallest correction:** explicitly record T3b as pending/`INCONCLUSIVE`, with unchanged release criteria and no PASS through omission.

