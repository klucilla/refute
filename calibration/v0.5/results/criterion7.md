# v0.5 exit criterion 7: the scope issues' dispositions (applied 2026-11-05)

The maintainer's decision 3 of 2026-11-05 (#199), in answer to the first gate review
(`calibration/v0.5/gate/gate-1-report.md`, criterion 7 not met). The list was validated with
Codex in 3 rounds (round 1: the saved issue texts were incomplete; round 2, on the full texts:
#190 needed explicit evidence, #191 is kept open by plan section 2; round 3: one wording fix for
#190, adopted). Each issue got one comment naming its evidence, part left or reason, then its
action. Close: completed. Keep open and move: the v0.5 milestone removed (no target version).

| Issue | Action | State after |
|---|---|---|
| #185 sensitivity rule | close | closed |
| #184 signal versus noise | keep open: decisive per-event tests with an error model that passes its acceptance | open |
| #193 partial sectors, edge ramps | close | closed |
| #182 variability | keep open: a multi-frequency, prewhitened model; the sinusoid domain (#203) | open |
| #181 secondary eclipse | keep open: a secondary's depth against a planet's possible occultation | open |
| #183 per-sector centroid | move to #200: built, not accepted (rows 4.1, 4.5 INVALID) | open |
| #190 report wording | close (its three items done) | closed |
| #187 blend caveat | close | closed |
| #191 shape and depth stability | keep open (plan section 2): the whole of optional WP5, not started | open |
| #179 exporter label | close | closed |
| #186 labels and values | close (S5 wording items in #205) | closed |
| #194 catalog period uncertainty | close | closed |
| #180 injection-recovery competition | keep open: masking the host's own signal | open |
| #188 reflected curve | close | closed |
| #9 null distribution | keep open: a validated null and a per-star false-alarm rate | open |
| #189 REPRODUCE.md self-sufficient | close (criterion 6; single-host dependency #206) | closed |
| #195 reproduction criterion | **keep open: item 4** (PROTOCOL.md lines 67-68; plan 9a.3) | open (see below) |
| #196 frozen TESS-EB folder | close | closed |
| #176 duration uncertainty | move: optional WP9, not started | open |
| #192 neighbors beyond 21 arcsec | keep open: not in scope (plan section 6) | open |
| #197 test folders, flaky test | close | closed |
| #198 paired comparison split | close | closed |

Totals: 12 closed, 8 kept open with the part left, 2 moved with their reason.

**#195, an accidental close, reverted.** GitHub closed #195 at 2026-11-05T19:08:47Z when commit
`f895f9c` (the first gate report) was pushed: its message quotes the gate's words "the proposal
to close #195", which GitHub read as a closing keyword. It was reopened the same day with a
comment explaining it (issue #195). Every commit message of the phase (`ad5fd5c..HEAD`) was
checked for other closing keywords; there is none.

**No `.cache/test-*` folder after the suite:** none after the end-of-phase suite of 2026-11-05;
checked again after the final suite (`criterion2/suite-final.md`).
