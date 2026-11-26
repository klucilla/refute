Opened on the maintainer's decision of #218 comment 7197519001, item 2. Labels of the work it refers to: `exploratory`, `method_status: not_validated`.

**What is not established.** Correction 2, revision 1 (`docs/plans/v0.5.12-spec-correction-2-r1.md`, adopted at SHA-256 `c24e7fd936929d713f53755b53233cc453e3e65a043f887b2f9e1511869873db`, commit `38c02ae`) declares that F1's null calibration and sensitivity under correlated noise remain unestablished (its section 6, Codex's round-3 limit).

**The evidence so far** (exploratory, post hoc; `docs/validation/v0.5.12/step4/explore-candidate3.json`):
- **B6 with red noise:** 15 and 16 null rejections per 1,000 at σ_r = 3e-4 and 1e-3 (nominal rate about 2.7 per 1,000). The median estimated σ_r is about 15 % below the injected value (2.53e-4 against 3e-4, and 8.51e-4 against 1e-3).
- **The sensitivity control's rule** adds the white depth only: `5 × sqrt(1/Σw_odd + 1/Σw_even)`. Under red noise, every cell fell below 281 of 300.
- **The check's limits:** one geometry; synthetic boxes; red offsets in blocks aligned to the transit windows and the estimator's bins.

**What it asks:** before any use of F1 on real data:
- a pre-registered measurement of F1's null rate and sensitivity under correlated noise, B6 included;
- a decision on the sensitivity control's rule under red noise.

Nothing is adjusted now. The v0.5.13 proposal records this issue as a precondition.
