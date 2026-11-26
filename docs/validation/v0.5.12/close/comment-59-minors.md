**The minor findings of the v0.5.12 gate**

The maintainer's decision is #218 comment 7202383280, item 1. The reviews are stored unchanged:
- Fable's (the binding verdict): [`docs/gates/v0.5.12-review.md`](https://github.com/klucilla/refute/blob/main/docs/gates/v0.5.12-review.md);
- Codex's second opinion: [`docs/gates/v0.5.12-review-codex.md`](https://github.com/klucilla/refute/blob/main/docs/gates/v0.5.12-review-codex.md).

Each item is an English summary; the review's row is the source. Nothing is corrected in `src/`.

The other minors go elsewhere:
- Finding 8 is on #224.
- Finding 13 is in the process issue.
- Finding 10 and Codex's minor are corrected in the records at the close.

**From Fable's review:**

- **5.** The `src/` commit `6f83a91` also rewrote 4 existing v0.5.11 tests in `tests/test_v0511_screen.py`, from frozen values to the corrected oracle. It also adjusted `tests/v0512_oracles.py` (3 Codex fixes).
  - Those 4 tests were not marked or replaced in the suite pushed before the code.
  - It was exposed at the stop (7198914586), reviewed by Codex and approved as the exact diff.
  - Suggested: record it as a deviation, and change legacy tests in the tests commit in future corrections.
- **6.** The "after" JUnit (`step4/junit-after-src.xml`) was produced on the working tree with the proposed diff, 16 minutes before the `src/` commit.
  - Its checker (`step4/junit_check.py`) was written later, at Codex's request.
  - `test_v0511_identity.py` and `test_v0511_f1_calibration.py` did not finish locally (deviation 7).
  - The diff equality and the full CI of `6f83a91` cover the gap.
  - Suggested: label the checker post hoc in the report.
- **7.** Before the blind review, #218 has no authorization with purpose, number and cost (the charter, stop 5; Process diet 2, item 2).
  - The comments say "already approved", and the cost (179,854 tokens) appears only afterwards.
  - The adopted text (r1) is not exactly what the blind reviewer read. Beyond B1 and B2, it received N items and the wording of Codex round 3, in the same thread.
  - Suggested: record the authorization in #218 with its date, or declare it absent in the report.
- **9.** The stored excerpts of K25 IV.4 (`docs/plans/sources/v0.5.11-screen-papers-2026-11-24.md:62`) lack the sentence that defines sigma_odd and sigma_even as "the noise over the corresponding transits".
  - The sentence is in the paper (https://arxiv.org/html/2509.10619v1, read by the reviewer on 2026-11-26).
  - The correction rightly says it is not in the excerpts and marks the estimator [choice].
  - Suggested: in a phase where reading the paper is not a stop, add the excerpt to the sources record with its URL and date.
- **11.** The committed CI evidence (`step5/ci-evidence-6f83a91.txt`) is a two-line summary without the job list.
  - The report at the seal had no results section.
  - The `inspect` units run uncommitted scripts in `.cache/v0512/diag/`; only their hash is journaled.
  - Suggested: keep the job list and complete the report before its approval.
- **12.** "One test each" for `unavailable` branches (`charter.md:304`) was met by grouped cases: 47 cases for 66 branches.
  - R42, R47, R52, R59 and R65 each cover 5 or 6 branches. B06 joins three subpaths with the same reason.
  - This is a difference of form, not coverage.
  - Suggested: declare it in the report.
- **14.** All 6 Codex rounds of the phase (correction, diff, review of all commits) used the same thread, `01a21826-…`. The final review did not come from a thread outside the design.
  - The blind review is stored in Portuguese, against "everything in English" (there is precedent in gate reviews).
  - Suggested: a new thread for the review of all commits, and a language note in the record's README.

**From Codex's second opinion (its minor):**

- Three texts still read as written:
  - `ROADMAP.md` says amendment 1 is pending;
  - `caps-ledger.json` says every offline unit runs in the AppContainer;
  - the seal says the three measured ceilings held.
- Suggested:
  - reference the approval of `bb6292c` (#218 comment 7193450494);
  - describe the network control actually used;
  - label the seal's numbers as recorded totals.

Labels: `exploratory`, `method_status: not_validated`.
