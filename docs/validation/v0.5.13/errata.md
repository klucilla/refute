# v0.5.13 errata log

This log is append-only. Each entry is dated and gives the source commit, the correction and its
impact. It follows Process diet 2, item 5.

## 2026-11-27: docs/STATUS.md, the header's sentence on links

- **Source:** `docs/STATUS.md`. The header, written with the draft README (`f3d1843`) and merged
  in `d8987228` (PR klucilla/refute#229), said: "Its relative links were written for the
  repository root and are kept as they were: read them from the root (...)."
- **Why it was wrong:** that stopped being true when M2 re-prefixed the moved links (`c897e40`,
  #218 comment 7204660147, item M2). The sentence was left unchanged then, because M3's check
  allowed only link changes in that commit.
- **The correction,** approved by the maintainer (#218, comment 7207651312, item D3), in its own
  commit: "Its relative links were re-prefixed on 2026-11-26 to work from this folder (#218,
  comment 7204660147, item M2); only their targets changed."
- **Impact:** a statement about the file's links. No moved line, link target, result or record
  changes.
