# The issue triage of 2026-11-10

The maintainer's decision of 2026-11-10, third set (#216, item 3), delegated to Claude and Codex (two rounds; [consensus record](../../plans/v0.5.2-consensus/README.md)). Every move carries a short comment on its issue; issues were closed only by comment.

**Not touched:** the v0.3 issues #15, #47, #52, #59, #135, #158, #159, #160, #161, #162, #171 and #207 (it touches v0.3), until 2026-11-18. #24 and #25 stay open with no scope decision (only their closed-phase milestone was removed).

| Issue | Action | From | To | Reason |
|---|---|---|---|---|
| #9 | move | none | Deferred (no target version) | false-alarm calibration, not scheduled in the current line of work. |
| #10 | move | v0.5.1 | v0.5.3 | a candidate D1 route for folded eclipsing binaries, with #215. |
| #11 | move | v0.4 | Deferred (no target version) | v0.4 is closed; not in the current line of work. |
| #12 | move | v0.4 | Deferred (no target version) | v0.4 is closed; not in the current line of work. |
| #16 | move | v0.4 | v0.6 | its variable-star catalog part maps to the cross-match of ROADMAP v0.6; its planetary-transit catalog part stays unresolved. |
| #18 | move | v0.4 | Deferred (no target version) | v0.4 is closed; not in the current line of work. |
| #19 | move | v0.4 | Deferred (no target version) | v0.4 is closed; not in the current line of work. |
| #26 | move | v0.4 | Deferred (no target version) | v0.4 is closed; not in the current line of work. |
| #27 | move | v0.4 | Deferred (no target version) | v0.4 is closed; not in the current line of work. |
| #28 | move | v0.4 | Deferred (no target version) | v0.4 is closed; not in the current line of work. |
| #29 | move | v0.4 | Deferred (no target version) | v0.4 is closed; not in the current line of work. Its dependence on #24 decides nothing about #24's scope. |
| #33 | move | v0.2.1 | Deferred (no target version) | v0.2.1 is closed; not in the current line of work. |
| #35 | move | v0.2.1 | Deferred (no target version) | v0.2.1 is closed; not in the current line of work. |
| #54 | move | none | Deferred (no target version) | not in the current line of work. |
| #56 | move | none | Deferred (no target version) | not in the current line of work. |
| #167 | move | none | v0.6 | eclipsing binaries and variability as results of their own (ROADMAP, v0.6). |
| #168 | move | none | v1.0 | per-pack dependencies belong to the pack SDK (ROADMAP, v1.0). |
| #176 | move | none | Deferred (no target version) | not in the current line of work. |
| #178 | move | none | Deferred (no target version) | not in the current line of work. |
| #180 | move | none | Deferred (no target version) | T2a uses hosts whose own signal does not pass the gate, so this remaining work is not a round-3 dependency. |
| #181 | move | none | v0.5.3 | the eclipsing-binary route of D1 (an occultation against a binary's secondary). |
| #182 | move | none | v0.5.3 | variability against a transit, the sinusoid's blockers of D2 and T2a; the full proposal stays subject to scoping. |
| #183 | move | none | Deferred (no target version) | the centroid is not a blocker of an outstanding target; a new acceptance (#200) is a later decision. |
| #184 | move | none | Deferred (no target version) | not an outstanding target; the overlapping per-event work stays in #209. |
| #191 | move | none | v0.5.3 | the shape and geometry work relevant to D1 only; timing and depth stability are not a round-3 commitment. |
| #192 | move | none | Deferred (no target version) | not an outstanding target. |
| #200 | move | none | Deferred (no target version) | the centroid is not a blocker of an outstanding target; a new acceptance is a later decision. |
| #201 | move | v0.5.1 | v0.5.3 | D2, D4 and T2a stay outstanding; round 3 (v0.5.3, the last correction round, to be scoped) attacks them. |
| #202 | move | v0.5.1 | v0.5.3 | D1 for EB1 and EB2 stays outstanding; round 3 (v0.5.3, to be scoped) attacks it. |
| #203 | move | v0.5.1 | v0.5.3 | the sinusoid's INCONCLUSIVE blocks D2 and T2a losses in the v0.5.2 forecasts and diagnosis. |
| #204 | move | v0.5.1 | v0.5.3 | period_alias's sensitivity blocks T2a losses in the v0.5.2 diagnosis. |
| #205 | move | none | Deferred (no target version) | report text, not an outstanding target. |
| #206 | move | none | Deferred (no target version) | infrastructure, not in the current line of work. |
| #209 | move | v0.5.1 | v0.5.3 | A0's per-event errors and their calibrated domain: their refusals block D2 and T2a losses. |
| #211 | move | none | Deferred (no target version) | the D1 routes collected here (out-of-eclipse modulation absent from the frozen C1 generator, stellar inputs that cannot change its fixed errors, radial velocities outside Refute's data) are not scheduled; the transit-geometry candidate is in #215. |
| #212 | move | none | v0.5.3 | reproduction across machines is needed before any confirmation run; the v0.3 work is excluded before 2026-11-18. |
| #213 | move | none | v0.5.3 | non-regression of earlier claims under later defaults; the v0.3 work is excluded before 2026-11-18. |
| #214 | move | none | v0.5.3 | battery speed: a T2a host above 20 sectors outlasts the 30-minute batch; the v0.3 work is excluded before 2026-11-18. |
| #215 | move | none | v0.5.3 | the transit-geometry candidate for the outstanding D1 target; the other routes stay in #211. |
| #24 | remove milestone | v0.4 | none | v0.4 is closed; the scope is the maintainer's separate decision |
| #25 | remove milestone | v0.4 | none | v0.4 is closed; the scope is the maintainer's separate decision |
| #210 | close (done) | v0.5.1 | closed | done: every CI job under 30 minutes in the last 5 runs of main (longest 26.6 min) and the test IDs checked by scripts/ci_ids_check.py (OK) |

**Milestones:** v0.5.3 created (13 open issues); v0.2.0, v0.2.1, v0.4, v0.5 and v0.5.1 closed, empty; v0.3 left open (not before 2026-11-18). #216 is closed by comment after the closing commit's CI is green.
