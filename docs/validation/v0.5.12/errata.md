# v0.5.12 errata log

Append-only (Process diet 2, item 5). Each entry: the date, the source commit, the correction and
its impact. Working records only; approved records get separate dated correction files.

## 1. 2026-11-25: demo-findings.md counted two failures instead of three

- **Source commit:** `15dce04`, `docs/validation/v0.5.12/step0/demo-findings.md`.
- **Correction:** its title and first sentence said "two failures", but its own table lists three
  failed fixtures (transient, commit, network). Both now say three; the rest of the file is not
  changed. Asked by the maintainer's decision recorded at 19:15 local (#218, comment 7174740316),
  item 4.
- **Impact:** none on any outcome; the table and the journal were right. The stop comment
  (7174043137) listed all three.
