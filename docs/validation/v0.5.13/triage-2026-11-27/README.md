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

## Maintainer's decisions W1 and W2 (2026-11-27)

The decision block W is recorded on #218, comment 7229841832. It acts on this record at `7726c7990f5be0f337de12e0291a77fb62fa31ed`. Every issue was read through the meter (unit `gh4`).

**Counts.**
- 63 issues were open before W, and W closed 19 of them. GitHub lists **44 open** on 2026-11-27, read through the meter after the closings.
- Under V and W together, 23 issues are closed: 4 under V and 19 under W.

### Closed under W1 and W2 (19)

| # | Title (short) | Criterion | Evidence |
| --- | --- | --- | --- |
| 9, 10, 11, 12, 13, 16, 17, 18, 21, 24, 25, 26, 27, 28, 29, 167 | the future-phase ideas | W2 (moved) | `docs/backlog/ideas.md` at `91a7b913ae2b785eb86e2dcac2e252dbe47bdbab`, sections 1 to 16 in this order. Each closing comment names its section. Codex's round (WEAKENED: omissions, nothing invented) was applied before the commit (`codex/w2-r1-*.md`). |
| 209 | v0.5.1 WP2: per-event error model | (b), superseded by #224 | What it held of its own was carried to #224 first (https://github.com/klucilla/refute/issues/224#issuecomment-7230041229). Closing comment: https://github.com/klucilla/refute/issues/209#issuecomment-7230044850 |
| 15 | Vacuous checks in paper replication | (b), tracked by #47 | #47's W4.3 rows (https://github.com/klucilla/refute/issues/47#issuecomment-6280921763). Closing comment: https://github.com/klucilla/refute/issues/15#issuecomment-7230046156 |
| 56 | Repository security settings | a declared limit (W1(f)) | The state given by the maintainer's adviser (CodeQL default setup, secret scanning and push protection on). Generic (non-provider) patterns are available only to organization-owned repositories (`sources/github-generic-patterns-2026-11-27.md`). No setting was changed. Comment: https://github.com/klucilla/refute/issues/56#issuecomment-7230048338 |

### Kept open under W1 and W2, with the reason

| # | Title (short) | Decision | Reason |
| --- | --- | --- | --- |
| 212 | BLS peaks across machines | W1(a): kept open | The existing records give no direct evidence. #212's differences are across machines, operating systems and Python versions (CI runs 42353283742 and 42356576130). F-1's cause is the BLAS thread count on one machine. The charter keeps "the mechanism of the historical CI difference" as F-1's declared limit (`docs/plans/v0.5.13-charter.md`, line 110). #226 is decision identity across thread counts on one machine (amendment 2, revision 8, sections 3 and 6). The rerun needed is proposed below; it was not run. |
| 195 | A reproduction criterion with verifiable inputs | W1(b): kept open | Revision 8 covers decision identity: for versions 1 to 4 in its sections 2 and 3, and the serialized operands of version 5 in section 5. Items 1 to 3 of #195 were done in v0.5. Its open item 4 is not covered by revision 8: the end-to-end `verify_promotion` wiring, left library-only until a phase has a promotion step. No Part B item exists yet to inherit it, so it could not be copied there before closing. |
| 30 | Lock canonicalization and new optional fields | W2.3: kept open | An unresolved finding, not an idea: the resolved claim hash changes when the schema gains an optional field, and `refute verify` then reports TAMPERED. Codex's note: the code already projects the two historical locks it lists, under strict conditions. The `claim` component can then match, while a code difference still gives TAMPERED (`docs/lock-format.md`, section "Historical locks: projection of the claim hash", line 155; `src/refute/core/lock_compat.py`). The general defect stands for any other lock. |
| 47 | v0.3 WP4: synthetic toy papers | W1(d): kept open | The item of a future paper-replication phase, with no target now. Comment: https://github.com/klucilla/refute/issues/47#issuecomment-7230047669 |
| 207 | Release archives and papers in a reply period | W1(e): kept open | The rule diff is proposed for the maintainer's approval (`proposals/207-rule.patch` and `proposals/README.md`), not adopted. |
| 135 | Decommission the Refute VM | W1(g): kept open | It closes when the maintainer reports the removal done, citing the archive's manifests. The checklist is posted on #135 after the commit of this section. Its link is in the stop report of block W on #218. |
| 171 | Disk quota for the ML containers on the VM | W1(g): kept open | It closes with #135, under (c): no future runner is planned. |

### Proposals for the maintainer (new under W)

1. **#212: the rerun that would decide it** (not run; it needs approval of its reason and exact procedure).
   - **Reason:** to learn whether #212's cross-platform differences disappear when the BLAS and OpenMP threads are pinned to 1. If they do, F-1's cause, and #226's decision identity, would cover #212.
   - **Procedure:**
     1. Re-run, on the four CI pairs (ubuntu-24.04 and windows-2025, Python 3.12.15 and 3.13.16), the analyses of the two failing tests named in #212:
        - `tests/test_v051_wp4.py::test_4_2_earlier_claims_keep_the_bytes_of_their_outputs`, at `911c9a5`;
        - `tests/test_v051_wp5.py::test_5_2_the_plans_of_earlier_claims_produce_the_recorded_bytes` and the paired-chain test, at `6aa9531`.
     2. Set `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` and `MKL_NUM_THREADS` to 1 before any numerical import, and record the BLAS backend and the effective thread count, as NR-A1 did.
     3. Compare each platform's outputs with the same analyses run at 1 thread on the maintainer's machine. Use revision 8's comparator (decision identity) and, as a diagnostic, the byte differences of #212's fields (`search_diagnostics.stage1`, the clusters, the refined peaks, `worst_event`).
     4. An optional second arm, from #212's own plan item 2: `NPY_DISABLE_CPU_FEATURES` set to force a common code path.
   - **Outcome:**
     - decision identity on every platform at 1 thread: #212 closes under (a), with that record;
     - otherwise it stays open, with the platform cause separated.
   - **Its own approvals:** it needs a CI job that does not exist (a change under `.github/workflows`), and it re-executes exposed synthetic cases.
2. **#195: where its item 4 goes.** Either a Part B (v0.5.14) issue that inherits it, or a decision that it stays deferred until a phase has a promotion step. Then #195 can close under (b).
3. **#30:** it stays open as a finding. The fix (a schema-versioned canonical form, or hashing only set values) is a design decision for a later phase.
4. **#207:** the proposed rule, and its two open questions: whether item 2's exception is adopted, and whether a dated note is linked to v0.4.0's Zenodo record.

### Process notes under W

- **X9:** sixteen `grep` reads of the launcher's own result lines ran outside the meter while the W2 issues were closed. They were recorded at once (`exceptions.jsonl`, X9).
- **One `gh4` call failed before acting,** on an unknown flag (`--comment-file-placeholder`, a slip in the command). It closed nothing; #209 was then commented and closed in order.
- **The VM archive's summary reports one problem by design:** no file could be read from `C:\ProgramData\RefuteVm-backup` without administrator rights. Part A of the #135 checklist copies it.
- **Codex:** one round each for W2 and for the #135 checklist (W1(g)), and three rounds in one conversation for the #207 rule (W1(e), a rule change). Every answer was WEAKENED, and its findings are applied; the stored rounds are in `codex/`.

## Maintainer's decisions X1 to X5 (2026-11-27)

The decision block X is recorded on #218, comment 7230555918. It answers the stop report of block W (comment 7230234478). Every read and every GitHub operation went through the meter (units `gh5`, `git-read` and `vm-archive-admin`).

**Counts, read on GitHub after the block's actions:**
- **43 open.**
- **24 closed by the triage:** 4 under V, 19 under W, and 1 under X (#207).

| # | Decision | What was done | Evidence |
| --- | --- | --- | --- |
| 207 | X1: the rule is adopted, with item 2's exception; **closed** (resolved) | The reviewed patch was applied to `docs/data-publication.md` with X1's three changes (the heading; "Open questions" removed; item 2 without the adoption condition). | Commit `0b5697aac2b7d8cd500043759ab5f928c4b8222a`. Codex's check, one round (`codex/x1-r1-*`): the text is the same and lines 1 to 88 are unchanged. Its single difference, item 2's line breaks, was aligned to the literal substitution before the commit. Closing comment: https://github.com/klucilla/refute/issues/207#issuecomment-7230615807 |
| v0.4.0 archive | X2: yes to a dated note | A correction file and a short text for the Zenodo description are drafted in `.cache/v0513/x2/`, not committed, for the maintainer's approval. The edit on Zenodo is the maintainer's. | Checked first: arXiv:2309.15704's notice was sent 2026-10-20T00:56:06Z (`reply/notice.md`), with a deadline of 18 November 2026. The period ended on 2026-11-18 with no reply received and no extension recorded (#158, comment 7037731352). |
| 195 | X3: kept open as Part B's item | Renamed "Part B (version 5): end-to-end verify_promotion binding (from #195, item 4)", and commented: what revision 8 covers (items 1 to 3, sections 2, 3 and 5) and what is left (item 4). No new issue was created. | https://github.com/klucilla/refute/issues/195#issuecomment-7230617834 |
| 212 | X4: kept open; the rerun is not approved now | Commented: the proposed procedure, left to Part B or v0.6. No CI job was created. | https://github.com/klucilla/refute/issues/212#issuecomment-7230618516 |
| 135 | X5: part A (the maintainer) and A5 (the agent) | Part A ran 2026-11-27, 20:56 to 20:58 Brasília time. A1's EXIT=0 is a recorded deviation: `Transcripts` is empty at its source. A5 gave **problems 0**: 2 files (RefuteVm-backup 1, pssc 1, Transcripts 0), equal by relative path and SHA-256 in A4's CSV, the staging folder and the Drive copy, read back. Parts B, C and D are not started. | `vm-archive/manifest-admin-copy.tsv` (SHA-256 `9dc2a9b9226a323696460ffc9101dd8c3144add8b6d83eb8e419ffb220935fcc`), `summary-admin-copy.json`, and A4's CSV beside them. The `.reg` backup's hash equals the one recorded at its creation (`docs/validation/v0.3/wp6-results/jea-registration.md`, section 2). Comment: https://github.com/klucilla/refute/issues/135#issuecomment-7230619153 |
