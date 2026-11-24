# v0.5.11 errata log (append-only)

This is Process diet 2, item 5. Each entry gives the date, the source commit, the correction and
its impact. Recorded outputs are never edited.

## 1. 2026-11-24: the recount's Markdown omits part of R7

- **Source:** `docs/validation/v0.5.11/recount/recount.md`, written by the recount unit (rules
  committed in `d0d2ba1`).
- **The discrepancy** (Codex, step 0's first round, blocking item 4): R7 of
  [recount/RULES.md](recount/RULES.md) promises "the same tables" in Markdown as in JSON. The
  Markdown leaves out:
  - the per-test counts of the subgroups (arm, match);
  - the host summaries (records per host, hosts all retained).
- **The correction:** none to the outputs, which are kept as they are. `recount.json` holds the
  full R6 tables and is the reference.
- **Impact:** none on any count. The specification cites the JSON and Codex's own recount.

## 2. 2026-11-24: launch.py version 1's telemetry

- **Source:** `docs/validation/v0.5.11/tools/launch.py`, used for the units of 2026-11-24 from
  23:01Z to 23:47Z.
- **The problems** (Codex, step 0's first round, blocking item 5):
  - transfer taken modulo 2^32;
  - polls that could pass a reservation;
  - disk-scan errors skipped;
  - admission not serialized;
  - the repetition key tied to the worker's hash.
- **The correction:** `tools/launch_v2.py` (commit `f2e977c`) for every later unit. Version 1's
  rows are kept. The ledger treats them as incomplete and charges each the larger of its
  reservation and its measured use (gap G6 of `meter-gaps.json`).
- **Impact:** exit criterion 6 (caps) is "not demonstrated" while a gap remains.
