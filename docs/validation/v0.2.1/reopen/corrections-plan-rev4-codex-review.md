# Codex review 4 of the corrections plan (revision 4), 2026-10-17

One read-only consultation (sandbox read-only, logical processors 0 to 7, no subagents) in four
rounds on the same thread, on the draft `corrections-plan-rev4.md` while it was uncommitted; the
draft was corrected after each of the first three rounds. The question and the replies were in
Portuguese; this record summarizes them in English. The raw answers are kept in the worktree's
`.cache/` (not committed), with these SHA-256:

| Round | Raw answer | SHA-256 |
|---|---|---|
| 1 | `resposta-1.txt` | `c21dd5398f3e33e09cf080d61491336992ee532db33e28f298a72856013879d9` |
| 2 | `resposta-2.txt` | `b986628c7531def06b979c4516e4c9aa4c379c49882289335122c2f91846ae0c` |
| 3 | `resposta-3.txt` | `446c70c49b3129dc34cbf83c34ab97ea7366a2ba9660f233ce109f49ef90b629` |
| 4 | `resposta-4.txt` | `8b671510bc66914e7cba319b956fd430313a596980dfdc757e47c395ceea3eb2` |
| 5 (check of Amendment 1 only) | `resposta-5.txt` | `e8ea2b5fc6ce23ad8d1682051e8f31647dcfb862420d2d375d53c70686dd79de` |

## Verdicts by round ("closed" means a specification sufficient for the objection examined, not a validated method)

| Row | Round 1 | Round 2 | Round 3 | Round 4 |
|---|---|---|---|---|
| B1 | open: comparability after the detrending not shown; no unique placement rule; geometry (the span is `4 T14 + 6 σ_t`; at `σ_t = T14` no replica fits); the stack variance not justified | closed | closed | closed |
| B3 | closed | closed | closed | closed |
| B4 | closed | closed | closed | closed |
| B5 | open: how the power and the object are rebuilt after the clipping | closed | closed | closed |
| B6 | open: the twin froze coefficients (the baseline noise vanished from the twin's value; the timing pull could be zero by construction); `f` measured is not `f` known; 21 conditions, not 19 (the old marginals give about 0.788) | open: no simultaneous coverage of the bounds; no trigger for the enlargement; the order of the records; the twin's ephemeris for K3 and K4 | open: the budget did not cover the configurations; one sentence kept the old order | **closed** |
| B7 | open: the M5 settings | open: M5-2 starts and the choice among them | closed | closed |
| R3-1 | closed | closed | closed | closed |
| R3-2 | open | closed | closed | closed |
| R3-3 | closed | closed | closed | closed |
| R3-4 | open | open | open | **closed** |
| R3-5 | closed | closed | closed | closed |
| R3-6 | open | open | closed | closed |

Codex also confirmed, in round 1, that the cost estimate of section 8 (revision 3's worst case scaled
from 24 to 6 workers: about 2.7 days and 0.8 day) is coherent as an ideal scaling, and that it is not
revision 4's worst case; the text says so.

**Round 4, final:** "B1, B3, B4, B5, B6, B7 e R3-1 a R3-6 estão FECHADOS" (Codex's words), with the
earlier closures of B2, B8 and N kept. Implementation and validation remain pending, and the
decision to resume is the maintainer's.

**Check of Amendment 1 (the 21 conditions), a fifth exchange on the same thread.** Asked by the
maintainer as a consistency correction, not a new round of design: Codex only checked that the
amendment replaces every inherited reference to "all 17 conditions" (selection, reserves, M5, the
joint power) with the 21 conditions, without adding, removing or moving a condition, limit or
threshold. Verdict: agreement; no other active contradiction found; the SHA-256 of revision 3 still
matches.

The agreement closes the **specification**; it does not show that the methods work. That depends on
the implementation, its tests, the calibration of the estimators and the confirmation.
