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

## 3. 2026-11-26: correction 2's revision 1 gets Codex's round 3 wording

- **Source commit:** `e7f652e`, `docs/plans/v0.5.12-spec-correction-2-r1.md` (SHA-256
  `a122c88c22e95c82c87879008b6c0546bb78624404c6b59d5971364347cf592d`, the bytes check 3 tested).
- **Correction:** Codex's round 3 (`WEAKENED`;
  `docs/plans/v0.5.12-correction-2-consensus/r3-codex-answer.md`) asked for a declared limit
  after check 3, a prefix and a sentence on the check's history, and a new T2/T6 bullet; its
  recorded item on N7 is quoted beside N7. Applied as written, by the standing rule that a
  divergence goes to the more conservative option. A header bullet says so.
- **Impact:** the estimator, the thresholds and every number are unchanged; check 3's result
  stands for the estimator. The file's SHA-256 changes; the maintainer's adoption is against the
  new one. Revision 1 was not approved, published or locked.
