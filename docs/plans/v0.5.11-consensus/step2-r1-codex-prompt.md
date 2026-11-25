Same rules as before: read-only sandbox, repository C:\Projetos\refute, no writing, editing, committing or network. Never open K:\Meu Drive\Pessoal\Segurança. No GPL implementation. You may run the project's .venv Python in isolated mode for read-only checks, without writing files, but do not run the test suite.

## Context
v0.5.11 step 2: the src/ change, reviewed before the maintainer's stop, before the first commit in src/ (charter docs/plans/v0.5.11-charter.md, step 2; Process diet 2 item 2). The specification is frozen at ab828ce (docs/plans/v0.5.11-spec.md, SHA-256 d498a82a...). The step-1 tests were committed and pushed at 84010d0 before any src/ change (docs/validation/v0.5.11/step1/expected-tests.json lists the expected IDs and reasons).

The change is in the working tree, uncommitted. The full diff (src and tests) is .cache/v0511/step2/step2.diff; the new module is src/refute/packs/tess/screen_d5.py.
- params.py: discovery version 5, explicit version sets (V05_VERSIONS = 2..5, V051_VERSIONS = 3,4), discovery.entry ("search" required for 5, refused for 1-4, left out of the dump when absent).
- schema.py: the explicit sets in _validate_discover.
- pipeline.py: analyze_data computes analysis.extras["screen"] for version 5 from GauntletOutcome.flattened/.candidate and the final tests; build_result adds record["screen"]; v05_record writes discovery_version 5.
- discover/measure.py: chain adds "screen" for version 5 from the stage's final tests.
- screen_d5.py: F1 core by OE_box; report-only F1_trap, F2, F3, F4, U1; compute_screen.
- tests: the strict expected-failure markers removed (no other test change).

Local results through the metered tests unit (JUnit): the four v0511 test files plus tests/test_v05_battery.py, test_v052_battery.py, test_v051_wp4.py: 161 tests, 0 failures, 0 errors, 0 skipped. Every ID of expected-tests.json passed. The full CI matrix will run on the src commit.

## Review, with path:line evidence
1. Faithfulness to the frozen spec, sections 1-8: every [choice], every unavailable/not_assessed path, the report-only isolation, eligibility, precedence, determinism, the record schema.
2. Identity (A5) and versions 1-4: can any change alter a version 1-4 output, a plan's resolved bytes or a lock's identity (lock_compat, codehash, claim canonical form)? Are the explicit sets complete (any remaining version comparison anywhere in src)?
3. Bugs in screen_d5.py (numerics, edge cases, the trapezoid model at q_in = 0, the MES grid, the event selection, F_red, the would_be_significant logic, F3 units), and in the integration (measure.chain's tests, the extras key, error paths).
4. Anything that must change before the first src/ commit.

## Answer (English, concise, at most ~100 lines)
- OVERALL: SURVIVED / WEAKENED / REFUTED for committing this diff.
- BLOCKING items with exact replacement wording or code-level fix.
- NON-BLOCKING items.
