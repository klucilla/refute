Rules: read-only sandbox, repository C:/Projetos/refute; no writing, editing, committing or network. Never open any path on the K: drive. You may run the project's .venv Python in isolated mode (`.venv/Scripts/python.exe -I`) to check arithmetic or algebra on your own small synthetic arrays, without writing files. Do NOT run M1, M2, the sensitivity control, the project's tests, or any unit of the phase, and never use seeds 1-3000, 100001-103000 or 200001-200300.

## Context
v0.5.12 (charter docs/plans/v0.5.12-charter.md, approved at 7df389c; amendment 1 at bb6292c) measured #222 with M1 (docs/validation/v0.5.12/step1/m1-summary.json, m1-result.md): F1's rejection rate on equal-depth curves with correct but unequal sigma. P2.4, P9.5 and B6 fail the pre-registered rule; U, S9.5, T2 and T6 pass. By the charter's step 4, a dated specification correction is written from the stored paper excerpts only (no download), then up to three Codex rounds (a rule change), then a blind review launched by the maintainer; adoption is the maintainer's stop. The maintainer's decision (#218 comment 7193864189) asks you to decide, besides the estimator: (i) whether the correction covers the whole noise function (F1 and the report-only MES grid of F2 and U1) or only F1; (ii) the order between step 2 (#223's cases and tolerances) and step 4, so that #223 is not written against the old noise, without breaking "the suite before src/".

## Files
- docs/plans/v0.5.12-spec-correction-2.md, as committed at HEAD when this round runs (the launcher's journal records that HEAD and the file's identity): the correction under review.
- Committed: docs/plans/v0.5.11-spec.md (sections 4 to 6), docs/plans/v0.5.11-spec-correction-1.md, docs/plans/sources/v0.5.11-screen-papers-2026-11-24.md (the stored excerpts), src/refute/packs/tess/screen_d5.py (the current code; lines 88-93, 143-182, 209-270, 293-320, 658-700), docs/validation/v0.5.12/step1/m1-summary.json, docs/validation/v0.5.12/step4/explore-candidate.json and explore_candidate.py (an exploratory, post hoc check of a FIRST candidate with an unweighted red term, on new seeds), the charter's step 4 and section 4.

## The one question of this round
Is the correction, as written, sound to go to the blind review? Check with path:line evidence:
1. The diagnosis of section 2 against the code.
2. The sourcing of section 3: does it use only what the stored excerpts say, and mark the rest [choice]? Is the charter's step-4 condition ("if the committed excerpts do not settle it, the work stops") met by the reading that Eq. (11) gives one uncertainty per parity?
3. The estimator of section 4: the scale s^2, the inverse-variance weighted red term (untested; the first candidate's unweighted red term lost sensitivity in S9.5, 212/300), the per-parity sigma. Is it correct, robust to the M1 families (including a single precise baseline point and a noisier parity), and does it reduce to the current form for equal sigma (section 5)? Give the estimator you choose, with exact wording.
4. Decision (i): the scope, whole noise function or F1 only.
5. Decision (ii): the order of steps 2 and 4.
6. Anything that would make M2 or the sensitivity control (charter, step 4, points 6 and 7; unchanged rules) unable to judge the correction fairly.

A finding outside this question is listed as a recorded item, not argued.

## Answer (English, at most about 80 lines)
- OVERALL: SURVIVED / WEAKENED / REFUTED for sending this correction to the blind review.
- BLOCKING items, each with the exact replacement wording.
- One line each: your estimator; your scope decision (i); your order decision (ii).
- NON-BLOCKING items.
