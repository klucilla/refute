# Correction of the sidecar of the numerical environment (dated 2026-11-27)

The maintainer's decision Q2(g) (#218, comment 7226143268), on the third blind review's
non-blocking item 7. Labels: `exploratory`, `method_status: not_validated`.

**The corrected record.** [`numerical-environment.md`](numerical-environment.md), committed in
`aa4a7ce93f8114f76c96c747632961e73fb05e03`, SHA-256
`d4717097a8943c82b745613dd29b205f738d1d03f9ac2dd973ab21e1d753d485` (read from the HEAD blob by the
unit `bytes-vs-head`). It is a hashed record, so it is not edited. This file is the correction.

**The sentence corrected.** Its last line says that in any other numerical environment, "the
reproducibility criterion is decision identity (amendment 2, sections 3 and 4)".

**The correction.** It takes effect when the maintainer adopts amendment 2, revision 8
([`../../plans/v0.5.13-charter-amendment-2-rev8.md`](../../plans/v0.5.13-charter-amendment-2-rev8.md)).
From then on the sentence reads: in any other numerical environment, the reproducibility
criterion for versions 1 to 4 is decision identity under amendment 2, section 3, together with
section 4's freeze, review and void rule; the margin check of section 4 does not apply to
versions 1 to 4. Until that adoption, the sentence stays correct as written, under the adopted
revision 6.

**Impact.**
- No value of the sidecar changes: its records, environment table, claim mapping and baseline
  exception stay as they are.
- No lock, dossier, tag, verdict or recorded byte changes.
- Under revision 8, the margin from the decision thresholds is not assessed for versions 1 to 4.
  That is a declared limit of #226, named in the label of revision 8, section 6.
