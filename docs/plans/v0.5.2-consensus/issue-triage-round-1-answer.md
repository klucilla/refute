The GitHub connector allowed read-only issue inspection despite `gh` failing. No changes made.

Corrections:

- **#24, #25 | Disagree: move, keep open | Deferred (no target version).** Rule (c) removes v0.4 from every open issue. Rule (d) preserves their open status and undecided scope, not their milestone. This is administrative triage, not a scope decision. Close v0.4 once empty.
- **#180 | Disagree: keep open, assign milestone | Deferred (no target version).** Its remaining work concerns signal-bearing hosts. T2a uses original-gate-negative hosts, so the proposed rationale does not establish a round-3 dependency.
- **#211, #215 | Partly disagree: separate their assignments | #211 Deferred; #215 v0.5.3.** #211 collects alternatives, including modulation absent from frozen C1, improved stellar inputs that cannot change its fixed errors, and radial velocities outside Refute’s data. #215 contains the specific transit-geometry candidate relevant to the outstanding D1 target. Cross-reference #211 without scheduling all its routes.
- **#191 | Agree with qualification: assign milestone | v0.5.3.** Limit the triage rationale to the shape/geometry work relevant to D1. Timing and depth-stability work are not automatically round-3 commitments.
- **#16 | Agree with qualification: move | v0.6.** Explicitly retain the unresolved planetary-transit catalog portion. Only its variable-star catalog portion maps directly to v0.6.
- **All “Deferred” destinations | Normalize | Deferred (no target version).** Use one exact milestone name.

Agreement on every remaining row:

| Issue(s) | Action and destination | Assessment |
|---|---|---|
| #15, #47, #52, #59, #135, #158–#162, #171 | None, unchanged | Agree. **v0.3 protected through November 17**, including comments and milestone changes. |
| #210 | Close by factual evidence comment | Agree. Independently checked all 28 jobs in run `42919751104`: longest logged span approximately 26.55 minutes. Each OS/Python entry has seven shards and 4,797 unique IDs, with zero additions, removals or duplicates against `42891422886`. The stated two technical conditions hold. [Run evidence](https://github.com/klucilla/refute/actions/runs/42919751104). |
| #201 | Move to v0.5.3 | Agree, outstanding D2/D4/T2a. |
| #202 | Move to v0.5.3 | Agree, outstanding EB1/EB2 D1. |
| #203 | Move to v0.5.3 | Agree, sinusoid dependency. |
| #204 | Move to v0.5.3 | Agree, alias sensitivity dependency. |
| #209 | Move to v0.5.3 | Agree, calibrated errors, domain and combined non-regression. |
| #10 | Move to v0.5.3 | Agree, geometry candidate alongside #215. |
| #181 | Assign v0.5.3 | Agree, plausible EB discrimination work. |
| #182 | Assign v0.5.3 | Agree, relevant variability/sinusoid work; the full proposal remains subject to scoping. |
| #212 | Assign v0.5.3 | Agree, reproduction risk. |
| #213 | Assign v0.5.3 | Agree, earlier-claim interpretation safeguards. |
| #214 | Assign v0.5.3 | Agree, execution cost blocks measuring long-sector hosts. |
| #183, #200 | Assign Deferred | Agree, no established outstanding-target dependency. |
| #184 | Assign Deferred | Agree for its residual scope; #209 retains the overlapping per-event work. |
| #192 | Assign Deferred | Agree. |
| #205 | Assign Deferred | Agree. |
| #206 | Assign Deferred | Agree. |
| #9 | Assign Deferred | Agree. |
| #54, #56, #176, #178 | Assign Deferred | Agree. |
| #168 | Assign v1.0 | Agree, pack SDK dependency separation. |
| #167 | Assign v0.6 | Agree, variable-star results. |
| #207 | None, unchanged | Agree. **Touches v0.3**, preserve the freeze. |
| #33, #35 | Move to Deferred | Agree. |
| #11, #12, #18, #19, #26–#29 | Move to Deferred | Agree. #29 depends on #24, but deferral decides no scope for #24. |
| #216 | Conditional closure by comment | Agree only after the specified closing-commit CI condition is evidenced. Close as the recorded phase termination, not scientific completion. Currently pending. |

Creating v0.5.3 and closing empty, closed-phase milestones is allowed. Keep v0.3 open. Broad #212/#213/#214 work must explicitly exclude frozen v0.3 work before November 18.

WEAKENED

