# Gate review of v0.3

The independent review of the phase gate (CLAUDE.md, "Phases"; plan section 9.3, step 2). The
reviewer was Claude Opus 5.5 (`claude-opus-5-5`) in one fresh read-only session, approved by the
maintainer on 2026-10-19 as the second batch of the reviews. It ran on 2026-10-20 (UTC), after
the notices were sent and recorded (#158, comment 6280792481). Its report, unchanged, is
[review-opus.md](review-opus.md): SHA-256
`940c0322d107291a19d4d2c587368100c711c1259a320bea2cf2f20df9d17264`, 15,175 bytes.

**Verdict: WEAKENED.** Both exit criteria hold as written. The reviewer re-ran
`verify_dossiers.py`, `refute check-dossier` and `refute verify` on the five papers, and all
passed. The weaknesses below are tracked.

## The issues the verdict requires to be tracked

| # | Item of the review | Where it is tracked |
|---|---|---|
| 1 | Attach the two held reviews of 2309.15704 after the reply period, checked against their recorded SHA-256 (condition 4) | #162 |
| 2 | Record the deviation: dossiers and verdicts published before the gate, during the embargo | this file, "Deviations" |
| 3 | The courtesy notices of 2305.19518, 2407.11735 and 2502.16782 | this file, "Deviations"; the maintainer's decision is pending |
| 4 | `refute reply-draft` and `refute review attach` cannot read production dossiers; the notices have no `reply/` annex and no draft hash | this file, "Deviations"; #161 |
| 5 | The WP4 acceptance rows not covered by the controlled tests | #47, comment 6280921763 |
| 6 | No reviewer checked the inventories or the triage of the main sample; the verifier replays recorded check results, not logs | #159, #160, #161 stay open; this file, "Limits" |

## Deviations from the plan

- **Publication before the gate (plan 9.3), during the embargo (9.1, item 3).**
  - The five dossiers, their verdicts and their publication reviews were published in full on 2026-10-19. The commits are ca2b7f1, ec29309, 33122ef, 48682b7 and 4d0e9c2; the run comments on #158 go from 6271344451 to 6279811447. All of this came before the seal and the gate.
  - The order was decided by the maintainer at each publication, by outcome (A) of the publication rule of the logs; it was not recorded as a deviation from 9.3 at the time.
  - No negative claim was published (none exists). For 2309.15704, the run's traceback is public, while the analysis of its cause waits for the reply period.
- **Seal after publication (9.1, item 1).** See [../SEAL-RECORD.md](../SEAL-RECORD.md). The bytes were fixed before the seal by the publication commits and by the `MANIFEST.sha256` hashes on #158; no core file changed afterwards.
- **Courtesy notices (9.2, D-14).**
  - Sent: the notice of 2302.12465 (all claims REPRODUCED), and a notice for 2309.15704.
  - Not sent: the three papers with only INCONCLUSIVE claims (2305.19518, 2407.11735, 2502.16782). The plan gives them "the same courtesy notice".
  - The maintainer's decision, to send them or to record that they are not sent, is pending.
- **Notices without a `reply/` annex or a draft hash (9.1, items 4 and 5).**
  - `refute reply-draft` needs `SEAL.json`, `verdict.json`, `claim.yaml` and `REPRODUCE.md` (src/refute/core/reply.py). The production dossiers have `dossier.json`, `claim_file.json` and `claim_input.json` instead. The drafts were therefore written by hand on the model of `render()`, then reviewed and sent by the maintainer.
  - `refute review attach` needs `verdict.json` and rewrites `MANIFEST.sha256`. The reviews were therefore attached with `refute annex`.
  - The send record is #158, comment 6280792481.
- **Reviewer inputs (10.3).** By the maintainer's decision, each primary reviewer received only its dossier and the reviewer protocol. No reviewer checked the inventory, the draw or the triage rejections of a paper (#161).
- **Second reviewer on all five dossiers, with no draw.** See [../ANNEX-RECORD.md](../ANNEX-RECORD.md).
- **Reviews of 2309.15704 held** under the right of reply: #162.

## Limits stated with the result

- **The dossier verification** (calibration/v0.3/verify_dossiers.py) shows that the classification is deterministic from the recorded check results, not that the experiment is repeatable. It does not re-extract metrics from the logs.
- **The fix of the verifier's fifth Codex round** (acceptance, section 4d) was examined by this gate review and found correct. One stated leniency remains: free exception text after a rejected-record prefix. No published dossier takes that path.
- **What the five papers exercised.** Four of the five papers were locked with claims that could not be decided (#159), and no robustness attack ran on real data. "Processed end to end" holds whatever the verdicts (plan, line 66), but only one paper reached a real run with decided claims.
