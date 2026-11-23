## 1. Coverage of the decision · SURVIVED

The correction carries all four approved items: Door 1’s revised reading and the caveat for “under one change of seed,” the four off-ephemeris fits and the two among the 13 completed changes, the report’s approval status, and Stage 0’s wording. It addresses gate points (a) through (d) with the file-identity limit, the two `ERROR`s and the pre-fit timeout, the four mismatches, and the search-mode versus TOI-seeded comparison. `git diff HEAD -- docs/reports/v0.5.8-report.md` was empty. [Maintainer decision](C:/Projetos/refute/.cache/v058/comment-decisions-gate.md:8) · [Gate finding](C:/Projetos/refute/docs/gates/v0.5.8-review.md:34)

## 2. Facts and numbers · SURVIVED

- **Door 1:** 15 of 107, including `ERROR`s for TOI-734.01 and TOI-531.01. File identity was verified for 83 of 167 records, with 84 `unknown`. The `same` panel had 10 changes among 54 previously decided records, including one `ERROR`. [Stability report](C:/Projetos/refute/docs/validation/v0.5.8/stability-report.md:26)
- **Failures before fitting:** TOI-2346.01 failed during light-curve download, TOI-7393.01 failed during pixel-file download, and TOI-531.01 hit a 600-second timeout while listing MAST products. The other two errors occurred during testing after the fit. [Stability records](C:/Projetos/refute/docs/validation/v0.5.8/stability-records.json:50315)
- **Off-ephemeris fits:** All four rows match the frozen set and both generations of records. Each had `status: OK` and `identity.matched: false`. The first two rows account for two of the 13 completed changes among previously decided records. [Frozen set](C:/Projetos/refute/docs/validation/v0.5.8/stage1-set.json) · [Stability records](C:/Projetos/refute/docs/validation/v0.5.8/stability-records.json)

| TIC | TOI | Set membership | v0.5.6 → Reseeded | Provenance |
|---|---|---|---|---|
| TIC-142937186 | TOI-2427.01 | Decided | SURVIVED → INCONCLUSIVE | `same` |
| TIC-401604346 | TOI-2193.01 | Decided | WEAKENED → INCONCLUSIVE | `unknown` |
| TIC-41995709 | TOI-4192.01 | Decided | WEAKENED → WEAKENED | `unknown` |
| TIC-82362447 | TOI-639.01 | Drawn INCONCLUSIVE | INCONCLUSIVE → INCONCLUSIVE | `same` |

The report quotations match after normalizing Markdown formatting and line wraps. Stage 0 records “Reproduced: False,” with 31 versus 30 near refusals and the TOI-2111.01 threshold discrepancy. Local records corroborate both #218 citations: `7111994921` for the report approval in commit `6b463b8`, and `7112815055` for the correction approval in the issue record. [Approved report](C:/Projetos/refute/docs/reports/v0.5.8-report.md) · [Stage 0 record](C:/Projetos/refute/docs/validation/v0.5.8/stage0-records.md:18) · [Local issue record](C:/Projetos/refute/.cache/v058/issue-door1-wording.md:18)

## 3. Nothing more is claimed · REFUTED

The correction preserves the published numbers, door marks, records, and verdicts. Its Door 1 reading agrees with the public note. The sentence saying an off-ephemeris record “still counts in every door” implies a broader eligibility rule than the plan uses. TIC-82362447 was drawn as `INCONCLUSIVE`, placing it outside Door 1. Only TIC-142937186 qualifies for Door 4 among the four rows. Door 2 also counts test-status changes, so “on the record’s outcome” is too broad as a description of all four doors. [Public note](C:/Projetos/refute/docs/reports/v0.5.8-stability-note.md:60) · [Door calculations](C:/Projetos/refute/docs/validation/v0.5.8/stability_report.py:159) · [Cohort selection](C:/Projetos/refute/docs/validation/v0.5.8/stability_report.py:223)

## 4. Links · SURVIVED

All six relative links resolve in the working tree. The gate review target is present as an untracked file.

## BLOCKING items

Replace the two sentences in the counting bullet. [Correction](C:/Projetos/refute/docs/reports/v0.5.8-report-correction-2026-11-23.md:49)

- **Old** “The doors are counted as the plan fixed them, on the record's outcome. A record whose fit left the ephemeris still counts in every door.”
- **New** “Each door and panel uses the plan’s fixed counting rules. The four records whose fits left the ephemeris contribute wherever they meet those rules.”

## Non-blocking items

- Name TOI-531.01 and the 600-second timeout in §1 so readers can see directly that this pre-fit failure was one of Door 1’s two `ERROR`s.

**OVERALL: WEAKENED**

