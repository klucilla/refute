Same rules as stated at the start of this thread: read-only, no network, never open any path on the K: drive, no run of M1, M2, the control, the project's tests or any phase unit, and never seeds 1-3000, 100001-103000 or 200001-200300 (nor 500001-501000, 600001-600300, 700001-701000, 800001-800300, used by the exploratory checks).

Your previous turn in this thread was stopped by the project's meter before you answered (its disk reservation was too small for your own state files; recorded in docs/validation/v0.5.12/step4/codex-r1-interrupted.md). The maintainer approved this repetition (#218 comment 7196269069, item 3); it is round 1 of at most 3. Please answer the question below from the start; the earlier prompt (docs/plans/v0.5.12-correction-2-consensus/r1-codex-prompt.md) still holds, with these updates.

## Updates since that prompt
- docs/plans/v0.5.12-spec-correction-2.md is at HEAD (the launcher's journal records HEAD). Its section 1 now adds the second exploratory check; section 4's estimator text is unchanged since be14460.
- The second exploratory, post hoc check (docs/validation/v0.5.12/step4/explore-candidate2.json and explore_candidate2.py; new seeds only) computed section 4's estimator exactly, with the inverse-variance weighted red term. Null fails of 1,000 per family: U 1, S9.5 0, P2.4 4, P9.5 2, T2 1, T6 2, B6 1. Sensitivity fails of 300 (odd depth + 5*sqrt(1/sum w_odd + 1/sum w_even)): U 294, S9.5 296, P2.4 292, P9.5 294, T2 290, T6 288, B6 294. No pre-registered flag was raised. The estimator was not adjusted after it.

## The one question of this round
Is the correction, as written, sound to go to the maintainer's blind review? Check with path:line evidence:
1. The diagnosis of section 2 against src/refute/packs/tess/screen_d5.py.
2. The sourcing of section 3 (stored excerpts only; [choice] marked; is the charter's step-4 condition met by the reading that Eq. (11) gives one uncertainty per parity?).
3. The estimator of section 4 (scale s^2; the weighted red term; per-parity sigma; equal-sigma reduction of section 5). Give the estimator you choose, with exact wording.
4. Decision (i): the scope, F1 only or the whole noise function with F2 and U1.
5. Decision (ii): the order of steps 2 (#223) and 4, without breaking "the suite before src/".
6. Anything that would keep M2 or the sensitivity control (charter, step 4, points 6 and 7; unchanged rules) from judging the correction fairly.

A finding outside this question is listed as a recorded item, not argued.

## Answer (English, at most about 80 lines)
- OVERALL: SURVIVED / WEAKENED / REFUTED for sending this correction to the blind review.
- BLOCKING items, each with the exact replacement wording.
- One line each: your estimator; your scope decision (i); your order decision (ii).
- NON-BLOCKING items.
