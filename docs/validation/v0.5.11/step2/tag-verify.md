# v0.5.11, proof (iii): the locked tags after the src/ change

This is the charter's section 2.3, proof (iii).
- **The run:** the metered unit `tag-verify` (launch_v9), 2026-11-25, with `src/` at `a896c49`
  in the main checkout.
- **The script:** `scripts/verify_locked_tags.py`, as committed.
- **Its conditions:**
  - each tag is verified in its own warm environment under `.cache/lock-compat/`;
  - `UV_OFFLINE=1` (amendment 2, section 15), with no download;
  - the output folder is `.cache/v0511/tag-verify/`.

**Joint result: PASS, 10 of 10.**

| Tag | Claim | Result |
|---|---|---|
| v0.1.0 | calibration/self_claim.yaml | PASS (verify PASS) |
| v0.2.0-calibration-lock | calibration/v0.2/self_claim.yaml | PASS (verify PASS) |
| v0.3.0-main-lock | calibration/v0.3/main/claims/2302.12465/claim/claim.yaml | PASS (verify PASS) |
| v0.3.0-main-lock | calibration/v0.3/main/claims/2305.19518/claim/claim.yaml | PASS (verify PASS) |
| v0.3.0-main-lock | calibration/v0.3/main/claims/2309.15704/claim/claim.yaml | PASS (verify PASS) |
| v0.3.0-main-lock | calibration/v0.3/main/claims/2407.11735/claim/claim.yaml | PASS (verify PASS) |
| v0.3.0-main-lock | calibration/v0.3/main/claims/2502.16782/claim/claim.yaml | PASS (verify PASS) |
| v0.4.0-pilot-lock | calibration/v0.4/claim.yaml | PASS (verify PASS) |
| v0.5.0-calibration-lock | calibration/v0.5/claim.yaml | PASS (verify PASS) |
| v0.5.6-partb-lock | calibration/v0.5.6/claim.yaml | PASS (verify PASS) |

- **The summary file** (`.cache/v0511/tag-verify/summary.json`, kept outside git) has SHA-256
  `4e9491dd7c7a959717a7a9a9909d2d54b22fa6289d7c1e5625c5873c042f9a9c` (4,198 bytes).
- **The unit's record** is in the journal: its attempt, CPU, disk and the machine transfer as
  information.
