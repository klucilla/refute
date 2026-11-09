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
