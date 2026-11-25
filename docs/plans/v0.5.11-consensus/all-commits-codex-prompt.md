Same rules as before: read-only sandbox, repository C:\Projetos\refute, no writing, editing, committing or network. Never open K:\Meu Drive\Pessoal\Segurança. No GPL implementation. Read-only .venv Python checks in isolated mode are allowed; do not run the test suite.

## Task: the charter's review of all the phase's commits, before the gate (charter docs/plans/v0.5.11-charter.md, section 7)

The phase opened at 2026-11-24 22:58Z with the charter at eb70c13. Review every commit from dbdd78d (the opening) to HEAD (`git log --oneline eb70c13..HEAD`), on main. Key points:
- Step 0: the frozen specification ab828ce (docs/plans/v0.5.11-spec.md); the sources record, the manifest, the recount (rules d0d2ba1 before the run).
- Step 1: tests and expected IDs pushed at 84010d0 before any src/ change; the F1 calibration record; the differential baseline helper (fixed forward at 64f3331 after CI run 45514526728 failed on version 3's last digits).
- Step 2: the first and only src/ commit a896c49, exactly the adjusted diff docs/validation/v0.5.11/step2/src-change-adjusted.diff (SHA-256 c24bc496...), i.e. your round-3 SURVIVED diff src-change.diff (35102b10...) plus **the weights adjustment docs/validation/v0.5.11/step2/weights-adjustment.diff (04b3f048...), a recorded deviation that no Codex round has reviewed yet (the maintainer's decision, #218 comment 7151559282): you must review it here.** Its tests unit (step2-c): 171 tests, 0 failures, 0 errors, 22/22 expected IDs passed.
- The charter amendments f186646 (transfer 10 GB) and aa1fc39 (units without network), each checked as a pure append; the launchers launch.py to launch_v9.py, the journal docs/validation/v0.5.11/log.jsonl, the ledger caps-ledger.json, meter-gaps.json (G1-G10), errata.md (entries 1-9; entry 10 pending for the after-proofs).
- The after-proofs: docs/validation/v0.5.11/step1/golden-after.json and claim-hashes-after.json (if present in the working tree) against the before records.

## Check, with path:line evidence
1. The weights adjustment: correct, faithful to the frozen spec (the spec's arithmetic is 1/sigma^2; the common scale only when unrepresentable), no regression, the extreme-error and reference-reproduction tests meaningful.
2. The src/ commit: exactly the adjusted diff; versions 1-4 untouched (proofs i-iv as far as recorded); A4/A5.
3. Process: pre-registration order (spec before tests before src; rules before runs), rule (d) repetitions with approvals, the amendments' conditions, the records' completeness, anything misreported.
4. Findings the gate should know.

## Answer (English, concise, at most ~90 lines)
- OVERALL: SURVIVED / WEAKENED / REFUTED for proceeding to the gate.
- BLOCKING items with exact fixes.
- NON-BLOCKING items.
