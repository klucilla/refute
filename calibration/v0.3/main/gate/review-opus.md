Reviewer: claude-opus-5-5 (independent session), gate of v0.3

## Summary (three sentences)
The formal exit criteria of v0.3 hold. All five main-sample dossiers are locked, sealed and VERIFIED (I re-ran `verify_dossiers.py`, `refute check-dossier` and `refute verify`, and every one passed). The WP4 set shows all five verdict paths, including the controlled NOT_REPRODUCIBLE and its twin, and issue #158 comment 6280792481 records two notices with send date, sealed-core SHA-256 and reply deadline. The claim survives only in a weakened form: the review report of 2309.15704 exists only as a hash, no reviewer could check the inventories or triage that plan 10.3 asks for, several deviations from plan 9.1/9.2/9.3 are not recorded anywhere, and the WP4 rows left uncovered are not actually listed on #47.

## Criterion 1, paper by paper (table: paper, conditions 1-5, evidence)

Condition key: C1 locked, C2 run + seal, C3 dossier verification, C4 independent review, C5 notification if a claim is negative.

| Paper | C1 | C2 | C3 | C4 | C5 | Evidence |
|---|---|---|---|---|---|---|
| 2302.12465 (3/3 REPRODUCED) | yes | yes (sealed after publication) | yes | yes (Opus + Codex) | n/a (no negative claim); courtesy notice sent | `refute verify` PASS (claim cb7720a2…, code 3165e141…, 9 attachments); lock 13:31Z (#158 c.6268436675) before engine start 14:53:54Z (`provenance.times`). Core d18e7477… equals SEAL-RECORD.md:18, and `git diff ca2b7f1 HEAD` shows no core change. Verification VERIFIED (ANNEX-RECORD:60; re-run today). Reviews at ANNEX-RECORD:18,42. Log values 0.9625/0.6053/0.9625 vs 0.5799 at log lines 870/1615/1265/39 |
| 2305.19518 (3/3 INCONCLUSIVE) | yes | yes (same) | yes | yes (Opus + Codex) | n/a; **no courtesy notice** | verify PASS (ff1ac093…); lock 13:49Z, engine 18:44Z; core e4f2ca2d… unchanged since 48682b7; ANNEX-RECORD:19,43,61 |
| 2309.15704 (3/3 INCONCLUSIVE) | yes | yes (same) | yes | **only a SHA-256**: both reports held under the right of reply, no review annex in the dossier | n/a; notice sent anyway | verify PASS (59854389…); lock 14:07Z, engine 23:29Z; core 314ec192… unchanged since 4d0e9c2. `check-dossier` lists only `annex verification`. Held reports: ANNEX-RECORD:23-27 (e2e16a80…, 9,039 B) and 47-49 (c34c8724…, 6,702 B) |
| 2407.11735 (3/3 INCONCLUSIVE) | yes | yes (same) | yes | yes (Opus + Codex) | n/a; **no courtesy notice** | verify PASS (dcea7ed1…); lock 14:24Z, engine 15:46Z; core dc84b305… unchanged since ec29309; ANNEX-RECORD:20,44,63 |
| 2502.16782 (3/3 INCONCLUSIVE) | yes | yes (same) | yes | yes (Opus + Codex) | n/a; **no courtesy notice** | verify PASS (3e59b835…); lock 14:42Z, engine 18:41Z; core 490a819b… unchanged since 33122ef; ANNEX-RECORD:21,45,64 |

What I checked beyond the table:
- **Hashes.** Every `SEAL.json` and `ANNEX.json` SHA-256 matches SEAL-RECORD/ANNEX-RECORD. The combined hash recomputes to 22814a7e…. Every `MANIFEST.sha256` hash matches the run comments on #158.
- **Inventories and draws.** Each inventory matches `inventories/SHA256SUMS` and the copy in its claim folder. Each `draw.json` cites the right inventory hash.
- **Code.** Every dossier records Refute 04054f2 with `tracked_files_unchanged: true`, and its code hash is the lock's.

Two limits on condition 3:
- The verifier replays the *recorded check results* through the frozen `aggregate_claim`. It does not re-extract metrics from the logs or re-apply tolerances (acceptance §3, "Limits"). For 2302.12465, I and the Opus reviewer checked the arithmetic against the logs by hand.
- None of the five records ever takes the REFUTE_ERROR override path: every step has a plain outcome, accounting is valid and `invalid_reasons` is empty. So the last correction (§4d) does not bear on these five VERIFIED results.

## Criterion 1, controlled tests

`.cache/seal/wp4-junit.xml` reports tests=63, failures=0, errors=0, skipped=0 (2026-10-19T23:32Z). That is after the last change to the WP4 files (090da06) and to `src/` (f7601b9).

**What is covered** (`tests/wp4_papers.py`, `test_the_definitions_cover_the_verdict_paths`):
- **REPRODUCED:** `reproduced`, `no-attack`, `no-seed-option` and the route papers.
- **FRAGILE:** seed, split, leaky, ablation, holdout, and `interrupted-attack`.
- **NOT_REPRODUCED:** `metric-bug`, through `metric_recompute` only.
- **NOT_REPRODUCIBLE:** `not-reproducible`. Every rung fails by its procedure, with cause `artifact_build_ladder` (lines 141-149).
- **The twin:** a guard stops a rung, giving INCONCLUSIVE with cause `operational_guard` (lines 150-159).
- **INCONCLUSIVE:** `failed-run`, the twin and the route papers.
- **W4.5:** every paper runs twice with the same profile.

**Limits:**
- The controlled NOT_REPRODUCIBLE uses the synthetic classifier. That classifier is told beforehand which rungs are procedure errors (`synthetic.py:349-375`). So the test proves the path from a classified ladder to the verdict. It does not prove that `production.classify_build` (`production.py:335-370`) classifies real build logs correctly.
- NOT_REPRODUCED is shown only through `metric_recompute`, never through a base value outside tolerance.

**Acceptance rows not covered.** PR #111 lists them under "Not in this set":
- comparison modes and the `direction` tie;
- budget exhaustion at setup, base and attacks (the twin's "exhausted budget" variant);
- the #15 coverage papers (zero claims, empty split, metric on zero examples, nothing to compare);
- the repository's own test suite with zero tests collected;
- the `metric_recompute` boundary case;
- `trivial_baseline` FRAGILE;
- three of four W4.3b holdout cases, and its not-applicable cases;
- all of W4.3c;
- the development profile;
- the reply draft;
- W4.4: seal, dossier verification, reason text and accounting record per paper;
- byte-identical `verdict.json`.

**On #47:** it is open, but it has 0 comments and was last updated 2026-10-14. Its body does not list these rows. I found no record of the maintainer's decision to track them there, in the repository or on #47.

**Does that weaken the criterion?** The criterion text ("every verdict path, including NOT_REPRODUCIBLE … by a controlled test") is met. The WP4 acceptance it rests on is not complete, and its tracking is not evidenced. That weakens it, and it needs a recorded list on #47.

## Criterion 2

Met. Comment 6280792481 on #158 (created 2026-10-20T00:57:22Z; `updated_at` equals `created_at`, so it has not been edited) records two notices sent 2026-10-20T00:56Z:
- **2309.15704:** notice of the run, core 314ec192….
- **2302.12465:** courtesy notice with an optional period (plan 9.2), core d18e7477….

Both deadlines are 18 November 2026: 30 days in the maintainer's time zone (D-15), since 00:56Z is 21:56 on 2026-10-19 in Brasília. Both core hashes match SEAL-RECORD.md. So "at least one notification … with the send date, the SHA-256 of the sealed core and the reply deadline" (plan 9.3, item 2) holds, and the period is open.

The only record is that issue comment. Two things plan 9.1 item 5 asks for are missing:
- there is no `reply/` annex;
- the draft's SHA-256 is not recorded.

The text of the notices is therefore not on record. Their neutral wording (9.1 item 4) cannot be audited.

## Deviations

| Deviation | Recorded? | Justified? | Evidence |
|---|---|---|---|
| Seal after publication, not "at once" (9.1, item 1) | yes, maintainer 2026-10-19 | yes. The bytes were fixed by the publication commits and by the MANIFEST hashes on #158; no core file changed since (my `git diff` per paper) | SEAL-RECORD.md:36-43 |
| Dossiers and verdicts published before the gate (9.3) and during the embargo (9.1, item 3) | **no**. I found nothing in SEAL/ANNEX-RECORD, the publication reviews, #158, #59, the commit messages or the docs. The "(A) full publication" decisions apply the log-publication rule, not the 9.3 order | partly. There is no negative claim, so no negative result leaked. But the traceback of 2309.15704 is public while its analysis is held | commits ca2b7f1, ec29309, 33122ef, 48682b7, 4d0e9c2 (2026-10-19, before the seal and the gate); #158 comments 6271344451 to 6279811447; the repository is PUBLIC |
| No courtesy notice for 2305.19518, 2407.11735, 2502.16782 (9.2, D-14: "with the same courtesy notice") | **no** | not stated | #158 c.6280792481 lists two papers only |
| `refute reply-draft` / `refute review attach` unusable on production dossiers, so no `reply/` annex and no draft hash | **no**. Reviews were attached with `refute annex`; I found no record of the gap | the gap is real: `core/reply.py:209-211` needs `verdict.json`, `claim.yaml` and `REPRODUCE.md`, which production dossiers lack | `git log` since 2026-10-19; grep of the repo and #59 |
| Primary reviewers got only their dossier and the protocol | yes, maintainer 2026-10-19 | it costs the 10.3 checks (inventory, transcription, triage rejections), which no reviewer could do; tracked going forward in #161 | ANNEX-RECORD:11-14; all eight attached reviews ("Checks I could not do") |
| Second reviewer on all five, with no draw | yes | yes | ANNEX-RECORD:33-38 |
| 2309.15704 reviews held | yes | plausible, but it leaves condition 4 evidenced by a hash only | ANNEX-RECORD:23-27, 47-49 |
| Plan 8.2 "documented command fails" route limited to `data_present`; run failures always INCONCLUSIVE | yes, maintainer 2026-10-16 | yes; the run-phase attribution is tracked on #59 c.6279815040 | docs/verdicts.md:80-105 |
| Ladder stops on a Refute-side rung (2407.11735) | design choice in WP3; tracked as #160 | open | orchestrate.py:403-410; #160 |
| Protocol clarifications C1-C9 decided after candidates were seen | yes, dated, applied to all candidates | acceptable, disclosed | PROTOCOL-clarifications.md:12-113 |
| Patches not in the dossier ("Every patch is a diff in the dossier", plan 6.1) | no; tracked as #161 | — | review-opus 2407.11735 line 16 |
| Per-paper run approvals (plan 6.1, "Who executes") | not evidenced in the records I read | — | #158 lock comments say "does not start before its own approval", but no approval comment follows |

## Objections (table: severity critical/important/minor, evidence, why it matters)

| Severity | Evidence | Why it matters |
|---|---|---|
| important | 2309.15704 has no review annex; its two reports exist only as SHA-256 values (ANNEX-RECORD:23-27, 47-49; `check-dossier` lists only `verification`) | Condition 4 ("its dossier has an independent reviewer report", plan line 62; 10.3: "Its report is an annex") is met for this paper only by a commitment I cannot verify. Read strictly, 2309.15704 is at 4 of 5 conditions until the annex is attached with those hashes after 2026-11-18. This must be tracked |
| important | No reviewer checked the inventory, the draw or the triage rejections (10.3), on any paper; #161 | The 10.3 adaptation is unmet for the whole sample. It is mitigated only by the maintainer-side checks on #158 (c.6252536898, c.6254783816) and my own hash checks. Triage rejections remain unreviewed |
| important | Publication before the gate and during the embargo, unrecorded (see Deviations) | A pre-registered order (D-17) was broken without a record. It does not falsify criterion 1 or 2, but it must be recorded as a deviation |
| important | Courtesy notices missing for three papers, unrecorded (plan 9.2 / D-14) | Procedure deviation; criterion 2 still holds through the two notices |
| important | The WP4 rows not covered are not listed on #47 (0 comments) | The tracking that the prompt assumes is not evidenced. It must be written on #47 |
| important | The verifier replays recorded check results, not logs (acceptance §3) | Condition 3 shows that the *aggregation* is deterministic, not that metric extraction or tolerance checks are. This is disclosed |
| important | 4 of 5 papers were locked undecidable by construction; no attack ran anywhere in the sample (#159, #160; #158 "as planned") | It does not refute the criterion (plan line 66: "verdicts do not matter"). But "end to end" exercised a real run and verdict on only one paper, and robustness attacks never ran on real data |
| minor | §4d (`verify_dossiers.py:404-431` against `orchestrate.py:362-368, 430-435, 550-569`; `budget.py:188-189, 378-382`). Join order and prefix logic are correct: invalid reasons are append-only and accounting is valid exactly when the list is empty. No reachable false rejection: `"next"` only follows a nonzero exit (`integration.py:1441-1445`). One leniency: once the remainder starts with `"<cid>: record rejected: "`, any trailing text is accepted (`head.startswith(rejected)`, k=0) | It cannot be closed, because exception text is free. Stop and accounting consequences are still checked elsewhere. The test for §4d (`test_verify_dossiers.py:502-515`) is only positive: it has no 4d-specific negative case, and its breach string does not use the accountant's real "breach: container …" format. No real dossier takes this path |
| minor | No `reply/` annex and no draft SHA-256; `reply-draft` cannot read production dossiers (`reply.py:209-211`); no `REPRODUCE.md` in any dossier | The content and neutrality of the notices cannot be audited |
| minor | Commit messages and publication reviews call the dossiers "sealed" before `SEAL.json` existed (e.g. 4d0e9c2; 2309 publication-review.md:5) | Loose wording; SEAL-RECORD corrects it |
| minor | The 2302.12465 headline "3 of 3 drawn claims: REPRODUCED" is unqualified although no attack applied (review-opus, 2302.12465, line 10) | Allowed by plan 8.3 and disclosed in the claim, but a reader of the headline cannot see that robustness was never tested |

Neither the primary nor the second reviewers' objections refute a criterion. They concern:
- **the claims:** transcription choices (batch size; BOLT and the approximation note) and undecidable coverage routes;
- **the procedure:** missing inventory, draw, lock and patch records in the dossier, and the ladder stop.

All of them say the verdicts follow the rules.

On wording, I found no record that calls an inconclusive paper positive or says anything about authors. The four INCONCLUSIVE papers stay in the denominators as "3 of 3 drawn claims: INCONCLUSIVE".

## Verdict: WEAKENED

Issues that must be tracked:
1. Attach the two held reviews of 2309.15704 after the reply period and check them against the recorded SHA-256 values (condition 4).
2. Record the deviation "dossiers and verdicts published before the gate, during the embargo" (plan 9.1 item 3, 9.3).
3. Record the missing courtesy notices for 2305.19518, 2407.11735 and 2502.16782, and either send them or record a decision not to.
4. Record that `refute reply-draft` and `refute review attach` cannot be used on production dossiers, and that the notices have no `reply/` annex or draft hash. Store the sent text, or its hash, as a record.
5. Write the uncovered WP4 acceptance rows on #47, with the maintainer's decision.
6. Keep #159, #160 and #161 open. Note in the phase record that no reviewer checked the inventories or triage of the main sample, and that the verifier replays check results rather than logs.

I changed no record.
