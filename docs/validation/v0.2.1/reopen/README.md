# Records of the reopening of v0.2.1 (Phase I, from 2026-10-17)

The maintainer reopened v0.2.1 on 2026-10-17, in parallel with v0.3, until every exit criterion
of ROADMAP.md, "v0.2.1 Gauntlet fixes", is met with evidence and its gate review returns
`SURVIVED` (or `WEAKENED` with its issues tracked). The plan is
[`../../../plans/v0.2.1-reopen-plan.md`](../../../plans/v0.2.1-reopen-plan.md). Everything here is
on branch `claude/v0-2-1-reopen` until the maintainer approves its merge.

| File | What it is |
|---|---|
| `audit-criteria-1-4-5.md` | the audit of exit criteria 1, 4 and 5 at the reopening, with its read-only scripts and outputs (`audit_*.py`, `audit-*.json`) |
| `issue-23-acceptance.md` | issue #23: the report sentence on how blind the holdout is (acceptance criteria, amendments with sabotages and the review corrections) |
| `issue-33-evaluation.md`, `sources/issue-33-sources.md` | issue #33: can the TESS-EB snapshot be redistributed (an evaluation for the maintainer's decision, with sources) |
| `correlated-noise-acceptance.md` | correlated-noise cases for the changes already made (prospective extension of exit criterion 1), with the generator's mode |
| `correlated/` | the digests of the white-noise generator before the change (`white_reference.py`, `white-reference.json`) |
| `corrections-plan-rev4.md` | revision 4 of the plan of TESS corrections (M4, M5), answering the open rows of review 3; every row closed as a specification; implementation waits for the maintainer's approval of the resumption |
| `corrections-plan-rev4-codex-review.md` | the four-round Codex review of revision 4, and the check of its Amendment 1 |
| `corrections-plan-rev4.sha256` | the SHA-256 of the approved version of revision 4 (as committed) |
| `population-resumption.md` | the resumption of the population study: the maintainer's decisions of 2026-10-17 and the four conditions of the closure record |

Related records outside this folder: `../baseline/justifications.txt` (exit criterion 4),
`../ci-time-option-d-acceptance.md` (Amendment 4: commit 3b of option D), and the documents of the
changes themselves (`../H7-acceptance.md`, `../H4-acceptance.md`, `../H9a-acceptance.md`,
`../workers-equivalence-acceptance.md`).
