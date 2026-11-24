You are Codex, reviewing read-only (sandbox read-only; do not write, run installs, or use the
network). Repository: the current folder (Refute). Phase: v0.5.10 Census and feasibility
(exploratory). This is the one Codex round on the phase's scripts and report that the charter
asks for before its gate (docs/plans/v0.5.10-charter.md, section 6). It is not the gate.

Read:
- the charter, including section 9 (the amendment of 2026-11-24, a named rerun in part (f));
- docs/reports/v0.5.10-report.md;
- docs/validation/v0.5.10/ (scripts, outputs, log.jsonl, errata.md, engines/, cleanup/);
- CLAUDE.md and ROADMAP.md ("How phases work", Process diet 2).

Check, and report each finding with file and line:
1. Does each number in the report match the committed output it cites (recount, route (e),
   census (d1), Kepler census, engines/table.json)? Recompute where you can by reading files.
2. Part (f): were the thresholds (engines/settings.json) committed before the first TOI run
   (git log of settings.json against the first 'before' entry of a TOI run in log.jsonl)? Is
   every TOI run logged before and after, once per TOI and engine, with no repetition? Are the
   new values shown beside v0.5.9's, never replacing or re-scoring them?
3. Isolation and supply chain: wheelhouse-manifest.json against requirements.txt, the offline
   install, the AppContainer isolation test (isolation-test.json), the exports (no Gaia or TIC
   rows, no neighbour IDs in committed files).
4. Wording: no 'validated', 'confirmed', 'discovery', 'likely a nearby false positive' or
   'decide' in report-facing fields; candidates never get a planet letter; every output labelled
   exploratory, with the v0.5 limits label where v0.5.9 records are used.
5. The ranking of the routes and the recommendation: are they supported by the counts, and does
   the report state what would change them?
6. Exit criteria 1 to 10 of the charter: for each, met, failed or not run, with evidence.

Answer in English. Start with one line: VERDICT: SURVIVED | WEAKENED | REFUTED. Then a table of
findings: severity (blocking / important / minor), file:line, problem, suggested fix.
