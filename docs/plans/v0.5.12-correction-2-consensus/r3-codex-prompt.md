Same rules as before in this thread (read-only, no network, never any path on the K: drive, no run of M1, M2, the control, the tests or any phase unit, and none of the seeds already used). This is round 3, the last.

Since your round 2 (`SURVIVED`), the maintainer launched a blind review of the correction. It is stored unchanged in docs/plans/v0.5.12-correction-2-blind-review-result/ (verdict `WEAKENED`, blocking findings B1 and B2, non-blocking N1 to N10). The maintainer approved B1 in its alternative A (the effective epoch count) and B2, each with the review's exact wording (its section 4), A's three coherence adjustments included, and asked that only the non-blocking findings that change neither the estimator nor the numbers be applied; the others are open items in docs/reports/v0.5.12-report.md.

They are applied in a NEW file, docs/plans/v0.5.12-spec-correction-2-r1.md (revision 1, at HEAD). The reviewed file docs/plans/v0.5.12-spec-correction-2.md and the package are unchanged.

A third exploratory, post hoc check, committed before it ran, tested revision 1 (docs/validation/v0.5.12/step4/explore_candidate3.py; record docs/validation/v0.5.12/step4/explore-candidate3.json). The estimator was not adjusted after it. Its result, as a fact:
- 8 families x sigma_r in {0, 3e-4, 1e-3} (0, 0.5, 5/3 of sigma0 = 6e-4); red noise = one Gaussian offset per transit epoch window and per width-T bin elsewhere; 1,000 null and 300 sensitivity curves per cell; the sensitivity depth under the control's (white-only) rule.
- Null fails of 1,000, revision 1 (and the reviewed N_par form on the same curves): at 3e-4: U 4 (4), S9.5 3 (37), P2.4 2 (2), P9.5 0 (0), T2 4 (116), T6 4 (129), B6 15 (15); at 1e-3: U 5 (5), S9.5 0 (37), P2.4 4 (4), P9.5 1 (1), T2 3 (111), T6 3 (125), B6 16 (16). At 0: U 6, S9.5 3, P2.4 6, P9.5 4, T2 1, T6 0, B6 7 (both forms equal).
- B6's median estimated sigma_r is 2.53e-4 (true 3e-4) and 8.51e-4 (true 1e-3); the other families' are within 1 % of the truth.
- Sensitivity of 300 under red noise falls to 1 to 44 (P9.5: 262 and 35), since the control's added depth is white-only; at 0 it is 285 to 293.
- The pre-registered flag "null Wilson lower bound above 0.0027" is raised for U, P2.4 and B6 at 0, and for B6 at 3e-4 and 1e-3; "sensitivity below 281" in every red cell.
- The eighth family, S3-9.5 (sigma x 9.5 after one third of the span), gave results identical to S9.5 in every cell: in M1's two-sector geometry it selects the same cadences, so it added no case.

## The one question of this round
(a) Are B1 (alternative A, with its three coherence adjustments) and B2 applied in revision 1 exactly as the blind review wrote them, and are the applied non-blocking items free of any change to the estimator or the numbers? (b) Given the check-3 facts above, is revision 1 sound to go to the maintainer's adoption decision, with what declared limit, if any? Check with path:line evidence. Do not reopen settled items or the approved choice of alternative A; a new finding outside this question is listed as a recorded item, not argued. If you find it REFUTED, give the exact replacement wording; it will be applied without another round.

## Answer (English, at most about 45 lines)
- OVERALL: SURVIVED / WEAKENED / REFUTED for sending revision 1 to the maintainer's adoption decision.
- (a): applied / not applied, item by item (B1-A, its three adjustments, B2's three items, the applied N items), with the exact fix if not.
- (b): your reading of check 3, and the exact wording of any declared limit to add.
- Recorded items, if any.
