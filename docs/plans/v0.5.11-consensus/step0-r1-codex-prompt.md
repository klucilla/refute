Same rules as before: read-only sandbox, repository C:\Projetos\refute, no writing, editing, committing or network. Never open K:\Meu Drive\Pessoal\Segurança. You may recount committed JSON records with the project's .venv Python in isolated mode, without writing files. Do not open any GPL implementation (LEO-Vetter, batman, PyTransit, Coughlin's Model-Shift code).

## Context
The maintainer approved the v0.5.11 charter at eb70c13 (#218 comment 7146858167); the phase is open since 2026-11-24 22:58Z. This is step 0's review: up to three rounds on this thread (a rule change). If the core is not empty, the frozen specification goes on without a maintainer stop; the stop is before the first `src/` commit.

## Files (uncommitted unless noted)
- docs/plans/v0.5.11-spec.md (the specification to freeze)
- docs/plans/sources/v0.5.11-screen-papers-2026-11-24.md (the sources record, literal excerpts; the papers were read from the arXiv HTML and ar5iv renderings because no PDF renderer is available without third-party code)
- docs/validation/v0.5.11/source-manifest.json
- committed: docs/validation/v0.5.11/recount/ (RULES.md committed in d0d2ba1 before the run; recount.json and recount.md are its outputs), docs/validation/v0.5.11/tools/launch.py and units/, log.jsonl, caps-ledger.json
- You may read the papers' text, already fetched, at .cache/v0511/papers/k25-html.md, t18-ar5iv.md, sm03-ar5iv.md (markdown of the HTML renderings).

## Check, with path:line evidence
1. Charter step 0, items 1 to 5, and your blocking items (item 4 of the draft review; items 1 and 2 of the charter round): every equation and threshold has its paper version, equation, inequality, applicability and literal excerpt; unresolved formulas are unavailable, unresolved thresholds have no effect; F4 and U1 report-only; the core is nonempty; report-only cannot change the screen or level 2.
2. The equations against the papers' text: K25 Eqs. 1-3, 7, 9-13 and IV.1-IV.4 thresholds (including the F_red > 1.8 clause), T18 A4/A5/A13-A15, SM03 Eqs. 6-7. Flag any transcription error.
3. Every [choice] of the specification: is it declared, deterministic, and does any of them silently change a paper threshold's meaning so much that the threshold should be "no effect" instead (for example the box-MES F_red, N_TCE = 1, the out-of-transit reference, the fixed period in the trapezoid, the uncertainty scaling)? Recommend the conservative option where in doubt.
4. The core choice: F1 and F2 only, with the legacy tests outside the screen core (a change from the draft spec 3.3), justified by the recount. Sound for this exploratory phase?
5. F2's decision with the occultation exception (fail only when delta_sec >= 0.1 delta_pri; not_assessed otherwise) and F1's combination (fail on any computed sub-metric; not_assessed only if OE_box cannot be computed).
6. The recount: rules before the run (git order), classes, unknown kept unknown, groups by host and population; any error in recount.py against RULES.md.
7. The launcher and metering (rules (b)-(e), item 3 of the charter round): before/after journal, repetition refusal, reservation and in-flight stops, telemetry completeness; anything that would leave the cap criterion unmet. Note: the commit that added the launcher (dbdd78d) was checked outside the meter (a bootstrap, recorded in its message).

## Answer (English, concise, at most ~100 lines)
- OVERALL: SURVIVED / WEAKENED / REFUTED for freezing this specification.
- BLOCKING items with exact replacement wording.
- NON-BLOCKING items.
