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

## 2. 2026-11-26: golden-before-findings.md gets the cause's source

- **Source commit:** `918a485`, `docs/validation/v0.5.12/step0/golden-before-findings.md`.
- **Correction:** the cause was "the agent's reading, not confirmed".
  - Added the source the maintainer gave (#218 comment 7190662570, item 1): since Python 3.12.4,
    `os.mkdir(mode=0o700)` on Windows applies a restricted permission (CVE-2024-4030;
    https://mail-archive.com/python-checkins@python.org/msg03194.html, read on 2026-11-26).
  - Added the exact list read from the interpreter's DLL by the read-only `inspect` unit
    `sddl-from-dll-2`.
  - The earlier text is kept.
- **Impact:** none on any outcome; it supports the reading with a source and the binary's own
  bytes.
