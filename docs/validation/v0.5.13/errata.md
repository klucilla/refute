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

## 2026-11-27: ROADMAP.md, the abbreviation of the charter's SHA-256

- **Source:** `ROADMAP.md`, line 80, written when the phase opened (`61055e1b`). It abbreviated
  the charter's SHA-256 as `2832dc48…c230c813`.
- **Why it was wrong:** the full SHA-256, cited in the maintainer's approval (#218, comment
  7204660147, item 5), is `2832dc4870b0fb094e724a3ff6d6fb6c5710f2da5827791b8fa102c06230c813`.
  Its abbreviation is `2832dc48…6230c813`; one character was mistyped.
- **The correction,** under the maintainer's decision G3 (#218, comment 7219180143): the line now
  reads `2832dc48…6230c813`. The approved and hashed records that carry the same error are not
  edited. They are listed in
  [correction-2026-11-27-charter-sha-abbreviation.md](correction-2026-11-27-charter-sha-abbreviation.md).
- **Impact:** a typed abbreviation. No file, hash, approval or result changes.
