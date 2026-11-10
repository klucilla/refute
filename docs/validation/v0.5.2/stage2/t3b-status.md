# v0.5.2 stage 2: T3b's status, for the protocol stop

Written 2026-11-09 under the maintainer's item 3 of that date (#216). Counts only: no draw, no target
selected, no light curve read. `method_status: not_validated`. Inputs and hashes are in `toi-fetch.json`,
`obsnotes-fetch.json`, `t3b-inventory-r2.json` and `t3b-alternatives.json`. Codex's two answers are in
[`docs/plans/v0.5.2-consensus/`](../../../plans/v0.5.2-consensus/README.md).

## The approved frame

TOI false positive catalogued as an eclipsing binary: 856 false positives, 63 members of TESS-EB, 22 never
walked; T10K adds 0; Gaia DR3 adds 0 at the identity rule.

Under the historical TESS-EB acceptance rate (11 of 41), the 22 remaining stars forecast **5.9 acceptances**,
against 11 required. The scaled-rate interval, 3.1 to 9.4, describes uncertainty in the assumed mean and is
not a prediction interval for an accepted count. This is a shortage forecast, not proof of infeasibility.

## The definitions examined

None is adopted, and none may be without the maintainer's approval.

| Set | Status | Never walked | Flat-rate scenario | Two-strata scenario |
|---|---|---|---|---|
| A: TESS disposition EB, without nearby-source text | screening set | 165 | 44.3 | 32.6 |
| B: EB in the TOI comments, without nearby-source text | screening set | 145 | 38.9 | 29.4 |
| C: A and B | screening set | 124 | 33.3 | 26.1 |
| E: a TFOP note states an eclipsing binary on the target | lexical candidates, not adjudicated | 103 | 27.6 | 20.8 |
| Approved frame together with E | lexical candidates, not adjudicated | 120 | 32.2 | 24.0 |

Scenarios assume that historical rates transport to these sets, which is not validated, and correct nothing for
class contamination. A, B and C do not say which star eclipses. E is the only set with positive evidence
about the target; Codex's reading of 40 of its 116 members (reviewer annotations, not adjudication or measured
purity) found 35 coherent statements of a stellar eclipsing binary on the target, 4 unresolved and 1 substellar.
115 of the 116 carry a copied SEB disposition, so E mostly extracts summarized classifications.

**The statement for the maintainer:** E contains 103 never-walked lexical candidates. Its two-strata planning
scenario is 20.8 metadata acceptances under historical rate transport, but the expected yield for an
admissible, adjudicated E population is unknown; reaching 11 has not been established.

## The proxy corrected (2026-11-10, the maintainer's item 3 dated 2026-11-09)

**Why the first proxy rejected 4 of the 11 accepted stars** ([`t3b_proxy_diagnosis.py`](t3b_proxy_diagnosis.py), [`t3b-proxy-diagnosis.json`](t3b-proxy-diagnosis.json)): three failed D-1/D-2 because the TOI table's `Sectors` column lists the sectors of the TOI's alert (one each), not every sector with a 120-s light curve (3 to 6 measured by the walk); one failed D-4 because the TOI table's stellar log g (3.9) is not the TIC value the walk read (4.02).

**The correction** ([`t3b_alternatives_r2.py`](t3b_alternatives_r2.py), [`t3b-alternatives-r2.json`](t3b-alternatives-r2.json); the first record stays as it was): D-1 and D-2 from TESS's 120-s target lists S001 to S107 (v0.4's attempt 4, retrieved 2026-10-29), D-2's span approximated by sector numbers, D-7 from the lists' magnitude; D-4 to D-6 no longer applied, since the TOI table's stellar columns are not TIC values (no tolerance band fitted to the accepted stars). Each kept clause agrees with the walk on 41 of 41 walked stars; no accepted star is rejected; the strata become 11 of 25 (passing) and 0 of 16 (failing).

| Set | Never walked | Passing the proxy | Flat-rate scenario | Two-strata scenario |
|---|---|---|---|---|
| A | 165 | 39 | 44.3 | 17.2 |
| B | 145 | 37 | 38.9 | 16.3 |
| C | 124 | 31 | 33.3 | 13.6 |
| E | 103 | 17 | 27.6 | 7.5 |
| The approved frame (TESS-EB) | 22 | 9 | 5.9 | 4.0 |
| The approved frame with E | 120 | 23 | 32.2 | 10.1 |

**Disclosures** (Codex's round 3): the same 41 walked outcomes informed the correction and its check, so 41 of 41 is development agreement, not independent validation; every walked star passes D-2 and their smallest sector gap is 26, so the 11-sector boundary is untested, and sector numbers are neither elapsed time nor calendar years; D-7 uses the first list's magnitude, not the walk's exact TIC value; list membership is not an available SPOC product; 0 of 16 is an observed rate, not a zero probability. The proxy is still never a domain exclusion; the real domain keeps its TIC-based thresholds.

**The recommendation among A, B and C: none as written (Claude and Codex agree).** Correcting the domain proxy does not touch the class: A's TESS disposition does not say which star eclipses, B's comment match is not an affirmative target classification, and C intersects correlated information without adding localization, so it is smaller but not shown to be purer. None is the more conservative choice for validity. A qualified version would need positive, attributable evidence that the target eclipses, a frozen conflict rule (nearby-source evidence and unresolved identity or period make a star ineligible), an independent human adjudication with its rubric and acceptance criterion fixed first, and qualification before any of Refute's results. Under the further assumption that the passing-stratum rate (11 of 25) survives qualification, A, B and C would need to keep about 64 %, 68 % and 81 % of their proxy-passing stars to reach a mean of 11: conditional thresholds, not measured retention. A, B or C alone would also drop 23, 35 and 36 members of the approved frame: replacing the frame and adding to it are different proposals.

## What the union would need before adoption

1. Review by a knowledgeable person of a reproducibly selected sample, of all identity, period and class
   conflicts and of representative exclusions, under a rubric and a required precision frozen first.
2. A corrected, frozen rule: classifications told apart from hypotheses, observing requests, clearance results
   and superseded conclusions; evidence bound to the target, the TOI and the ephemeris; residual ambiguity
   ineligible; a stated policy for later notes that supersede earlier ones.
3. The approved frame's eligibility kept unless the maintainer changes it, with memberships and contradictions
   recorded per source.
4. One deduplicated order, its seed and exclusions frozen before selection; no legacy-first walk, no
   prioritizing of note classes, no use of the proxy as an exclusion.
5. **ExoFOP's data use policy resolved.** The notes belong to the users who filed them and the policy asks
   that the owner be contacted before use. Operational or published reliance on them needs documented owner
   authorization or an authoritative ExoFOP clarification. It is an open condition, not an established
   prohibition.
6. Disclosure of the counts, alternatives and annotations seen: the amendment would be prospective, not blinded.

## The treatment proposed if none is adopted

T3b alone is **deferred**, recorded as pending, with the scientific verdict **`INCONCLUSIVE`** and its gate
permission **not granted**. The 11 accepted stars and the eight valid outcomes stay as they are. Other results can
be reported, but a gate that requires T3b cannot receive an overall PASS by omitting it. Release needs an
approved population and procedure, the source-use conditions resolved, the frozen selection process and the original
measured acceptance criteria. A forecast reaching 11 is only a feasibility checkpoint.

## Not counted

The M&M catalog (no machine-readable location found); new members of the live TESS-EB portal (not established); Gaia
DR3 non-single-star solutions (additions unmeasured). See
[the source record](../../../plans/sources/v0.5.2-t3b-sources-2026-11-09.md).
