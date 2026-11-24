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

## 3. 2026-11-24: estimated time windows in meter-gaps.json and the consensus README

- **Source:** `meter-gaps.json` (G5, G7, G8; commits `f2e977c` and `ab828ce`) and the section
  title "Step 0: the two rounds on the specification (2026-11-24 and 25)" of
  `docs/plans/v0.5.11-consensus/README.md` (`ec595f4`).
- **The error:** the UTC windows of G5, G7 and G8, and the "and 25" of the title, were written
  as estimates, without reading the clock.
  - The journal's machine timestamps show that all of step 0 and the work up to this entry fell
    on 2026-11-24, before 23:35Z.
  - G8 happened about 23:15Z, not at 00:00Z on the 25th.
- **The correction:** the journal (`log.jsonl`) is the authority for every time. The gap
  entries are kept as written, and this entry corrects their windows.
- **Impact:** none on any measured quantity.

## 4. 2026-11-24: the golden-local "before" unit was interrupted by the transfer bound

- **Source:** the journal, attempt `f85b96ff27bc4a2d91c3e59577c2c939` (unit `golden-local`,
  label `before`, launch_v3, 23:28:33Z to 23:30:26Z).
- **What happened:**
  - The unit reads no network.
  - The launcher's transfer bound is the machine's `netstat -e` bytes, which count every
    program on the machine. That count reached 45,081,465 bytes, the stop level of a 50 MB
    reservation, and the job was stopped after 106.6 CPU-s.
  - No output was written.
- **Consequences:**
  - Under rule (d), a repetition needs the maintainer's approval in #218 first. It is requested
    at the stop.
  - Until then, `src/` in the main checkout stays at its parent, so that the "before" record
    can still be made at the parent.
  - The differential test (`tests/test_v0511_identity.py`) compares versions 1 to 4 with the
    source of `eb70c13` on every machine.
- **A design limit:** a machine-wide upper bound makes long units that use no network
  vulnerable to unrelated traffic. It is recorded for the report.
