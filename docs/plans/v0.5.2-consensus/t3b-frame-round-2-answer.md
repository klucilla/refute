**1. E improves the evidence, but does not yet establish class preservation**

I reproduced the note snapshot’s hash and the **129 positive, 545 nearby-flagged, 13 overlapping and 116 retained** counts.

I reviewed a deterministic, hash-ordered sample of **40 of E’s 116 members**, including the surrounding narrative. My conservative, text-only assessment was:

| Row kind | Count | Proportion |
|---|---:|---:|
| Coherent statement supporting a stellar EB on this target/TOI | 35 | 87.5% |
| Unresolved host component, ephemeris, confirmation status or stellar/substellar boundary | 4 | 10.0% |
| Explicit substellar-companion interpretation | 1 | 2.5% |

These are **reviewer annotations of statements**, not measured astrophysical purity or independent human adjudication. They do not justify extrapolating 87.5% purity to E.

Across all E members, **115 of 116 contain a copied master SEB disposition**. Thus E mostly extracts summarized classifications rather than independently interpreting observational evidence.

**SEB1 and SEB2 are the appropriate TFOP spectroscopic EB codes**, referring to single-lined and double-lined classifications. They are stronger than generic SB1/SB2. However, their occurrence does not resolve every host/component ambiguity or guarantee a stellar companion in these notes. Hierarchical systems are also included in the broader EB classification. [RAVEN, section 4.2](https://arxiv.org/html/2509.17645v1#S4.SS2)

**One current TOI per TIC does not bind every historical note to its signal.** Notes can discuss aliases, another TOI, revised periods or different components. I found an E member explicitly relating its signal to another TIC/TOI. That could be an alias or duplicate signal rather than contamination, but it requires identity adjudication.

The important rule defects are:

- **`POSITIVE` loses subject context.** A disposition summary can match after an earlier sentence discusses another source. `OTHER_TIC` checks only the matching sentence.
- **`HEDGE` does not implement the stated semantics.** It misses likelihood language, question-mark qualifications and contractions. Conversely, unrelated negation can suppress a valid statement. A detached summary remains positive despite qualifications elsewhere.
- **`NEARBY` detects mentions, not unrefuted detections.** I reviewed all 13 positive/nearby overlaps: **six are requests to search for nearby binaries, four describe field clearance, and three contain an actual or possible conflicting classification.** The first ten do not substantiate the label assigned to them.
- **The sentence splitter is not context preservation.** Abbreviations and semicolons can detach identity or qualification; a single newline without subsequent whitespace need not split. Its boundaries determine which qualifications count.
- **Chronology is ignored.** The function combines matches across notes without determining whether later evidence supersedes an earlier interpretation.

These defects cause both unjustified inclusion and unnecessary exclusion. **Recovering excluded members is not automatically the correction**, their qualification must be adjudicated under an approved rule.

**2. The revised scenarios are honest, with the stated limitations**

The arithmetic checks out, including retained/dropped counts, union accounting and both proxy strata:

| Set | Never walked | Flat scenario | Two-strata scenario | Proxy-passing subset only |
|---|---:|---:|---:|---:|
| E | 103 | 27.6 | 20.8 | 8.9 |
| Frame ∪ E | 120 | 32.2 | 24.0 | 10.2 |

The third column of scenarios is **not a lower bound** on the full-set yield. E has 89 proxy-failing unwalked members, whose acceptance probability is not established to be zero.

The historical intervals are correctly described as rate intervals, without claiming prediction or contamination coverage. The two-strata scenario still assumes that historical acceptance rates transport within strata. That assumption remains unvalidated.

**The single statement I would send to the maintainer is:**

> E contains 103 never-walked lexical candidates. Its two-strata planning scenario is 20.8 metadata acceptances under historical rate transport, but expected yield for an admissible, adjudicated E population is unknown; reaching 11 has not been established.

**3. Bring a conditional union proposal to the stop, not an adoption-ready amendment**

**Yes, the union merits discussion at the protocol stop. No, the current lexical E is ready for adoption or a draw.**

The union is preferable to replacing the frame with E: replacement drops **45 approved members**, whereas the union retains 63 and adds 98 lexical candidates.

Conditions before adoption:

- **Human adjudication:** a knowledgeable person reviews a reproducibly selected sample, all identity/period/class conflicts and representative exclusions. Freeze the rubric and required precision before evaluating it. My annotations are development evidence, not that acceptance assessment.
- **A frozen corrected rule:** distinguish classifications, hypotheses, observing requests, clearance results and superseded conclusions. Bind evidence to the target, TOI and applicable ephemeris. Fix residual-ambiguity handling before recounting for adoption.
- **Membership preservation:** preserve the approved frame’s eligibility rule unless the maintainer explicitly changes it. Retention does not establish that every grandfathered member satisfies E. Record source memberships and contradictions separately.
- **Walk order:** freeze sources, eligibility, prior-use exclusions, seed and a single deduplicated ordering before selection. Do not walk the legacy frame first, prioritize promising note classes or use the proxy as an exclusion.
- **Disclosure:** record the inspected counts, alternatives and development annotations. The amendment would be prospective, not blinded.

**The data policy is an unresolved adoption condition.** It applies its guidelines to public as well as proprietary data, requests owner contact before utilization and anticipates negotiated publication credit. Public accessibility, aggregate output and elapsed time do not establish an exemption. [ExoFOP policy](https://exofop.ipac.caltech.edu/tess/pcp.php)

The maintainer can decide Refute’s procedure, but cannot supply third-party permission. Before operational or published reliance on the notes, obtain documented owner authorization or an authoritative ExoFOP clarification covering the intended bulk, aggregate and frame-publication uses. Establish the applicable proprietary status and acknowledgment requirements. **`Lastmod` alone does not establish observation age or public-release eligibility.**

This is an unresolved policy gate, not a demonstrated blanket legal prohibition. The source record’s implication that internal counting settles the distinction is unsupported.

**4. Until those conditions are met, the round 1 treatment stands**

Record T3b as **deferred/pending**, with scientific verdict **`INCONCLUSIVE`** and **gate permission not granted**.

Keep the original 11 accepted stars and eight valid outcomes. Record the inventory, hashes, scenario assumptions, semantic defects and unresolved policy condition. These note counts provide no new T3b outcome coverage. Other results cannot turn an omitted T3b requirement into an overall PASS.

Release requires an approved population and procedure, resolved source-use conditions, the frozen selection process and the original measured acceptance criteria.

**Verdict on the script and counts: `WEAKENED`.** The lexical counts and scenario arithmetic survive. E’s class meaning and “unrefuted nearby” interpretation remain unvalidated.

1. **High, subject binding is sentence-local.** [t3b_alternatives.py:116](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:116), [line 120](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:120). **Smallest correction:** retain note-wide subject context and require explicit target/TOI association; unresolved cross-references remain ineligible.

2. **High, positive classification ignores material qualifications.** [t3b_alternatives.py:58](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:58), [line 63](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:63). **Smallest correction:** treat E as evidence screening until host, companion class and qualification conflicts are adjudicated. Adding hedge words alone is insufficient.

3. **Medium, nearby flags are mislabeled as unrefuted evidence.** [t3b_alternatives.py:118](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:118), [line 212](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:212). **Smallest correction:** label current output as lexical nearby flags; distinguish detections, requests, clearance and uncertainty before assigning eligibility.

4. **Medium, sentence boundaries and aggregation do not resolve context or chronology.** [t3b_alternatives.py:57](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:57), [line 125](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/t3b_alternatives.py:125). **Smallest correction:** preserve note context and provenance, and freeze an explicit supersession/conflict policy.

5. **High, internal use is not an established policy exception.** [source record:20](/C:/Projetos/refute/docs/plans/sources/v0.5.2-t3b-sources-2026-11-09.md:20). **Smallest correction:** mark operational and published note-derived use unresolved pending owner authorization or authoritative policy clarification.

6. **Medium, the source record overstates the NSS bound.** [source record:43](/C:/Projetos/refute/docs/plans/sources/v0.5.2-t3b-sources-2026-11-09.md:43). **Smallest correction:** mark NSS additions unmeasured. The prior variability-table positional/period check does not establish that NSS model periods produce zero qualifying additions.

