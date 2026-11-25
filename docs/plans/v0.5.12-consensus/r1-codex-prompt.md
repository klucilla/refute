Rules: read-only sandbox, repository C:/Projetos/refute; no writing, editing, committing or network. Never open any path on the K: drive. You may run the project's .venv Python in isolated mode (`.venv/Scripts/python.exe -I`) to check arithmetic and recount committed records, without writing files. Do NOT run F1, the screen or any measurement of the charter: no item of this charter may start before the maintainer approves it.

## Context
v0.5.11 (battery version 5: specification and software) closed with declared limits; its gate (docs/gates/v0.5.11-review.md) was REFUTED on criterion 6 (caps not demonstrated) and had two important findings, #222 (F1's noise with unequal weights) and #223 (step 1's cases and the report-only `computed` values). Its report (docs/reports/v0.5.11-report.md, section 6) recorded F-1 (version 3's last digits depend on the process's state).

The maintainer decided (#218, comment 7172688755): v0.5.12 is a SHORT correction phase, "Battery version 5: corrections before calibration", with only #222, #223 and F-1; synthetic data and repository fixtures only; no download, no real data, no new target; no named rerun ("in doubt it is a rerun, and it stops"); versions 1 to 4 change no byte (else stop); caps proposed at 3 CPU-h, 0 GB downloads, 2 GB peak disk, with ALL work through the phase's launcher so the caps are demonstrable; gate by a new read-only Claude session given only the gate-review protocol and the phase name; time box 7 days. For #222 the maintainer proposed, for you to assess, a 95% Wilson upper bound of at most 1%, with cases, seeds and limit fixed before measuring and derived from the specification's threshold 3. The calibration work moved to docs/plans/v0.5.13-proposal.md.

## Files (uncommitted in the working tree, except where noted)
- docs/plans/v0.5.12-charter.md (SHA-256 1267bbf4cf48b9ff0eb4cf1856ac3aa18ddee846d40bc4add8bb03ac0695e855): the charter under review.
- docs/plans/v0.5.12-consensus/wilson_design.py (SHA-256 9aea36b7b99fcace28ae1b9b8e5243d7970c896c1351014bfd306d8c6d0aab59): the agent's arithmetic for the limit.
- ROADMAP.md: the new v0.5.12 section ("charter pending approval").
- Committed: docs/plans/v0.5.13-proposal.md (renamed at 506d9d2), docs/plans/v0.5.11-spec.md, docs/plans/v0.5.11-spec-correction-1.md, src/refute/packs/tess/screen_d5.py, src/refute/packs/tess/synthetic.py, docs/gates/v0.5.11-review.md (findings 1, 2, 7, 8, 11 and its section 4.3), docs/validation/v0.5.11/ (launchers, units, caps-ledger.json).

## The one question of this round
Is this charter, as written, sound and complete to be approved, so that its rules are fixed before any measurement? Check, with path:line evidence:
1. #222 (step 1, step 4): the limit and its derivation (erfc(3/sqrt(2)), Wilson at z = 1.959964, n = 3000, at most 19 `fail` and 0 `not_assessed` per family; the pass probabilities stated); the seven families (including the ratio 9.5), the recipe, the chosen cadences, the seeds (M1: 1 to 3000; M2: 100001 to 103000); whether M2 on new seeds is correctly not a rerun; whether a power check is missing; whether the limit is too lax or too strict for the question.
2. #223 (step 2): the cases, the tolerance rule (1e-9 closed form, 1e-3 fitted, 5 standard errors for noisy quantities), the handling of unreachable reasons and of tests that fail on the current code.
3. F-1 (step 3): the method, the definition of "found", the 0.8 CPU-h budget, the stop if versions 1 to 4 would change.
4. Section 4: the classification of reruns versus software tests and verification, in particular v0.5.11's step1/f1-calibration.json.
5. Sections 5 and 6: the caps (3 CPU-h, 0 GB downloads, 2 GB peak disk) against v0.5.11's measured ledger; whether they are realistic and demonstrable; the definition of "download" and of the network units; the launcher plan (a single-file port of launch_v9 and its chain; its own commit metered by v0.5.11's commit-check unit); Codex rounds as launcher units.
6. Sections 7, 8 and 10: the gate (protocol and phase name only), the exit criteria (checkable from the repository), the stops (the maintainer's list: before the first src/ commit with your diff review, before adopting any specification correction, before the gate, before the report's approval), Process diet 2 items 1, 2, 4, 5 and 7.

A finding outside this question is listed as a recorded item, not argued.

## Answer (English, concise, at most about 80 lines)
- OVERALL: SURVIVED / WEAKENED / REFUTED for approving this charter.
- BLOCKING items, each with the exact replacement wording.
- NON-BLOCKING items.
- In one line each: your choice for #222's limit (keep, or a stated alternative) and for the three caps.
