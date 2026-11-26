# v0.5.12, correction 2: the blind review's result

Stored on 2026-11-26 on the maintainer's decision of #218 comment 7197099779, item 1. The two
files beside this README are stored **unchanged**, each checked by SHA-256 before and after the
copy (the `store-file` units of the journal). The package that was reviewed,
[v0.5.12-correction-2-blind-review/](../v0.5.12-correction-2-blind-review/), is not changed.

| File | Bytes | SHA-256 |
|---|---|---|
| `v0.5.12-correction-2-blind-review.md` | 21,901 | `9e55f7f2d96115c4128c46f9d17e70d4028d9efa6cec68729a49f0d0d8bd43eb` |
| `v0.5.12-correction-2-blind-review-prompt.txt` (the exact prompt) | 3,004 | `06e5765aaaf74f8dd75123fd8d0948e05a3cdfdee78c01a6555e57e29ac6c451` |

**The review, as the maintainer reported it:**
- **The reviewer:** Claude Fable 5.2, a new read-only session, launched by the maintainer's
  adviser with the maintainer's approval, at the default effort.
- **The cost:** 179,854 tokens (the total the environment reported), 7 tool uses, 383 s.
- **The input:** only the package whose `MANIFEST` has SHA-256
  `4455786b8d32de8580acb72d827c9e93a4ddf4c183e8706170825ffbbf3f4b64` (commit `db48356`), in a
  clean folder.
- **The verdict:** `WEAKENED`, with two blocking findings (B1, B2) and ten non-blocking ones (N1
  to N10).
- **The tokens line** of the review file was filled in by the adviser before the copy. It is the
  only line the reviewer did not write.

**What follows from it** (the same decision, items 2 to 6): B1 in its alternative A and B2 are
applied with the review's exact wording in a new file,
[v0.5.12-spec-correction-2-r1.md](../v0.5.12-spec-correction-2-r1.md). The reviewed file,
[v0.5.12-spec-correction-2.md](../v0.5.12-spec-correction-2.md), is not changed.

**The reviewer's own exploratory check** (the review's section 4, B1, and section 6) is the
reviewer's, not a project result. Its seeds (`20261126 + family index + int(red·1e6)`) are not
reused by the project.

Labels: `exploratory`, `method_status: not_validated`.
