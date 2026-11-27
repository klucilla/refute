# Triage of the open issues, 2026-11-27 (the maintainer's decision V3, #218 comment 7228712102)

Labels: `exploratory`, `method_status: not_validated`. 67 issues were open when the list was read (unit `gh2`, 2026-11-27).

**What the agent may close, under V3, with a comment citing the evidence:**
- (a) resolved;
- (b) duplicated or superseded;
- (c) informative, with its role fulfilled.

**What is never closed here:**
- #218, #59, #227, #224, #223, #228, #230 and #225;
- an unresolved finding that affects a gate;
- anything about papers in a reply period;
- anything that would be closed only "without resolving".

Those go to the proposal list below. In doubt, an issue stays open.

**Closed: 4.** #226 was closed by V1. Three were closed by V3:

| # | Title | Criterion | Evidence (checked by the agent) |
| --- | --- | --- | --- |
| 226 | The versions' bytes depend on the BLAS thread count | V1 (the maintainer's declaration) | #226 met under amendment 2, revision 8, with its label. Four records in `docs/validation/v0.5.13/step1/decision-identity-*.json`, all PASS. The comparator was frozen at `493ce707c8ea967a232a39421d8d479fdd5371ac`. |
| 222 | Screen F1: the per-parity noise with unequal weights is not tested | (a) | v0.5.12's seal (`docs/validation/v0.5.12/step5/seal.md`, criterion 1, **met**, sealed at `2aa20d8f526ab5b9371d551e51a9ac79fa92ffc8`).<br>- M1 reproduced the finding with the project's code: P2.4, P9.5 and B6 fail (`docs/validation/v0.5.12/step1/m1-result.md`).<br>- Correction 2 revision 1 was adopted after its blind review (`notes/adoption-correction-2-r1.json`).<br>- Its tests came first (`98117ef6ff0357f7fcd8194b13e2da517a532ac6`), then `src/` (`6f83a912013f8fe90c208a31467575a6d0edd385`).<br>- M2 passed in every family (`step4/m2-summary.json`). |
| 231 | Survey (exploratory): where refute verify and check-dossier compare bytes of numerical outputs | (c) | Used by amendment 2: `docs/plans/v0.5.13-charter-amendment-2-rev8.md`, section 1 ("The survey of E1(e) (#231, exploratory)", line 100) and section 3.1 (line 268). Its correction comment applied Codex round 3, item 4 (header, line 66). |
| 54 | Packaging: publish to PyPI via Trusted Publishing | (a) | `refute` 0.5.12 is on PyPI (https://pypi.org/project/refute/, read 2026-11-27). Both files say "Uploaded using Trusted Publishing? Yes". The attestations name the workflow `.github/workflows/release.yml` at `3dbb713c7fa40960d8f7941826e0a9c91a4b1b74`, run 46023627248. |

**Kept open: 63**, one line each:

| # | Title (short) | Proposal | Reason |
| --- | --- | --- | --- |
| 230 | v0.6 FP population: 172 SB1 | keep | named by V3 (never closed here) |
| 228 | Process: order proofs, repetitions, decision records | keep | named by V3; Part A's scope |
| 227 | The independence of the #223 case oracle | keep | named by V3; step 2 of Part A |
| 225 | Version 5 screen: four unreachable branches | keep | named by V3 |
| 224 | F1 under correlated noise | keep | named by V3; Part A's scope |
| 223 | Screen tests: step 1's synthetic cases | keep | named by V3; v0.5.12's criterion 2 was not met |
| 218 | v0.5 line paused: pause record | keep | named by V3 |
| 215 | D1 route candidate: transit-geometry consistency | keep | a recorded idea, not resolved |
| 214 | Speed of the version-3 battery | keep | not resolved |
| 213 | Earlier claims silently reinterpreted with later defaults | keep | a finding, not resolved |
| 212 | BLS picks different peaks on different machines | list | possibly covered by F-1's cause and #226; not verified (see the list) |
| 211 | Routes not built for folded EBs (D1 EB1, EB2) | keep | a gate finding of v0.5 (D1), not resolved |
| 209 | v0.5.1 WP2: per-event error model in correlated noise | list | v0.5.1 closed not approved; overlaps #224 (see the list) |
| 207 | Release archives and papers in a reply period | list | a rule gap; needs the maintainer's rule decision |
| 206 | A single host for the TESS-EB table; VizieR mirrors | keep | not resolved |
| 205 | v0.5 review: report text of C3 controls | keep | not resolved |
| 204 | v0.5 review: period_alias sensitivity refuses a PASS | keep | not resolved |
| 203 | v0.5 review: the sinusoid domain limit | keep | not resolved |
| 202 | v0.5 finding: synthetic EBs still survive (D1) | keep | an unresolved gate finding (declared limit) |
| 201 | v0.5 finding: planets lost to INCONCLUSIVE (D2, D4, T2a) | keep | an unresolved gate finding (declared limit) |
| 200 | Per-sector centroid: a new acceptance | keep | future acceptance, not resolved |
| 195 | v0.5 proposal: a reproduction criterion with verifiable inputs | list | perhaps superseded by amendment 2's decision identity (see the list) |
| 192 | Neighbours just outside 21 arcsec not evaluated | keep | not resolved |
| 191 | No decisive test for transit shape, timing, depth stability | keep | not resolved |
| 184 | A gate-passing signal indistinguishable from noise | keep | not resolved |
| 183 | centroid_shift decided by one sector | keep | not resolved |
| 182 | No decisive test separates variability from a transit | keep | not resolved |
| 181 | secondary_eclipse one-sided | keep | not resolved |
| 180 | Injection-recovery on a curve with its own strong signal | keep | not resolved |
| 178 | Idea: a MAST source for two-minute target lists | keep | an idea |
| 176 | Exporter: transit-duration uncertainty | keep | not resolved |
| 171 | Disk quota for the ML containers on the VM | list | tied to the VM's decommissioning (#135) |
| 170 | The code hash outside a git checkout | keep | backlog, not resolved |
| 168 | Optional dependencies per pack | keep | backlog (v1.0), not resolved |
| 167 | Ideas: EBs and variability as results | keep | future-phase |
| 161 | Dossiers not self-contained for review | keep | not resolved |
| 160 | Build ladder: a rung Refute cannot run | keep | not resolved |
| 159 | Selection: a decidability filter before the draw | keep | not resolved |
| 135 | Decommission the Refute VM | list | the removal is the maintainer's (Administrator) |
| 59 | v0.3 follow-ups | keep | named by V3 |
| 56 | Repository security settings | list | the maintainer's settings decision |
| 47 | v0.3 WP4: synthetic toy papers | list | tracks unaccepted WP4 rows of the closed v0.3 line |
| 42 | Holdout directed mode: deferred | keep | deferred with no date; closing it would be without resolving |
| 35 | Holdout: robust stacking and error model | keep | not resolved |
| 33 | Redistributing the TESS-EB snapshot | keep | deferred, not resolved |
| 30 | Lock canonicalization with new optional fields | keep | future-phase |
| 29 | Amateur follow-up of predicted transits | keep | future-phase |
| 28 | Independent reanalysis | keep | future-phase |
| 27 | Extended deduplication against TESS detections | keep | future-phase |
| 26 | Observing-request template | keep | future-phase |
| 25 | Public prediction ledger | keep | future-phase |
| 24 | Prospective predictions with a DOI | keep | future-phase |
| 21 | Community dashboard | keep | future-phase |
| 19 | Root cause of stdout closing during downloads | keep | worked around, not explained |
| 18 | Publication path | keep | future-phase |
| 17 | Gaia@home and Gaia Vari as prior art | keep | future-phase |
| 16 | Gaia DR3 variability tables | keep | future-phase |
| 15 | Vacuous checks in paper replication | list | tracked by #47 (see the list) |
| 13 | Mutation testing of the gauntlet | keep | future-phase |
| 12 | False positive probability | keep | future-phase |
| 11 | Difference-image centroid | keep | future-phase |
| 10 | Transit-derived stellar density | keep | future-phase |
| 9 | Null distribution from scrambled curves | keep | future-phase |

**Proposals for the maintainer:** each could be closed or moved only by a decision, so none was closed here.
1. **#135 and #171: the VM.** The shutdown commands were prepared on #135 (2026-11-20), and the removal is the maintainer's, as Administrator. If the VM is removed, close #135 as resolved, and close #171 or move it to a future runner.
2. **#47 and #15: the v0.3 paper-replication residuals.** The v0.3 line is closed, and #47 tracks the WP4 rows its controlled tests did not cover. Decide whether they move to a future paper-replication phase, with a target, or stay as they are.
3. **#209: the per-event error model.** v0.5.1 closed not approved. Its subject, the error in correlated noise, overlaps #224 (F1 under correlated noise). Decide whether #224 supersedes it, so that it closes under (b), or whether it stays apart.
4. **#212: BLS peaks across machines.** v0.5.12 found F-1's cause, the BLAS thread count, and #226 is met under decision identity. Whether that also answers #212's across-machine search was not verified here. It could close under (a) after a check of #212's own cases.
5. **#195: a reproduction criterion with verifiable inputs.** Amendment 2's decision identity may supersede it, for versions 1 to 4 only. Decide (b), or keep it for version 5 (Part B).
6. **#207: release archives and the reply period.** A rule gap in `docs/data-publication.md`, which needs a rule decision.
7. **#56: the repository's security settings.** These are settings only the maintainer changes: non-provider secret patterns and CodeQL default setup.
