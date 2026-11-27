# J2: what is left of Part A, and the two possible exits (no choice made)

The maintainer's decision J2 (#218, comment 7222879969). Labels: `exploratory`,
`method_status: not_validated`. This is an estimate from the measured pace. Choosing between the
exits, extending or closing the phase, is the maintainer's.

## The measured pace

- **The time box.** The phase opened at 2026-11-27T00:13:24Z and its time box ends at
  2026-12-04T00:13:24Z (charter section 9). At this record, about 6.3 days remain.
- **Day 1** (2026-11-27), done:
  - step 0 (the meter, ID-BEFORE);
  - step 1's measurement (NR-A1), which stopped;
  - D1a;
  - amendment 2 through five revisions, with three Codex rounds and two blind-review packages;
  - the TestPyPI and PyPI publication;
  - the CI work.

  Of the charter's steps, only step 0 is complete. Step 1 (#226) is not met yet.
- **The charter's own checkpoints** (section 9): step 0 and step 1 by day 2; step 2 by day 3; step 3
  by day 5; step 4 and the seal by day 7. Step 1 is on schedule only if #226 passes by day 2. With
  revision 5's blind review still pending, it cannot.
- **The cost so far:** 0.68 of 8 CPU-h. The time box, not the CPU cap, binds.

## The work left, by item

A *session* is one working session of the agent; *days* are calendar days including the
maintainer's approvals. The estimates assume no failed check.

| Item | What it needs | Sessions | Days |
| --- | --- | --- | --- |
| #226 (scope of revision 5) | The blind review and the adoption of revision 5. Then the decision-layer manifest (about 170 to 250 predicates; floor count 173), the comparator, the schema and the span map, with tests on synthetic tokens. The freeze commit, Codex's round and the maintainer's approval by hash. Then the comparisons at 1 and 4 threads, NR-A2 at 2 threads, and the margin check. | 3 to 4 | 2 to 3 |
| #227 (step 2) | The branch-to-assertion manifest pushed before the probe; assertions derived from the generating model, independent of the oracles; frozen JUnit IDs; the probe; corrections if any (a source correction is a stop). | 1 to 2 | 1 to 1.5 |
| #224 (step 3) | Synthetic families: 8 cells x 3,600 cases plus controls, about 30,000 F1 calls. The real-TESS panel: screening of up to 80 stars from MAST, downloads, 8,000 F1 calls and the stress cases. The manifests, seeds and order proofs, Codex, and the maintainer's approvals. A failure needs a specification correction with a fresh blind review. | 3 to 5 | 2.5 to 4 |
| Step 4 (the reason map) | Tests first, then a `src/` change behind the source stop (Codex on the exact diff, the maintainer's approval). | 1 to 2 | 1 to 1.5 |
| Step 5 (the seal) | ID-AFTER; full CI on the last code SHA (about 1 h or more); the reconciliations; the final Codex review; the Fable gate; the report and its approval. | 1 to 2 | 1 to 1.5 |
| **Total** | | **9 to 15** | **about 7.5 to 11.5** |

**Reading.** The remaining Part A does not fit the 6.3 days left, even without a failed check.
#224 is the largest and least certain item.

## Exit (a): an extension amendment, with a new date

- **The rule.** The charter (section 9) allows one extension, recorded by the maintainer before
  expiry, with its reason and new deadline.
- **The date.** From the estimate, a deadline about 8 to 12 days after the current one:
  2026-12-12 to 2026-12-16.
- **Implications for v0.5.14 (Part B):**
  - Part B can start only after Part A's recorded close with the preconditions passed (charter
    section 2).
  - If #226, #227 and #224 pass, v0.5.14 starts with all three preconditions met. It relies on #226
    only with amendment 2's label (decision I1).
  - The start of Part B moves by the length of the extension.
  - The risk is that a check fails within the extension: a specification correction with a fresh
    blind review could need more than one extension, and the charter allows one.

## Exit (b): close Part A at the deadline, with declared limits

- **The rule.** At 2026-12-04T00:13:24Z every criterion is marked met, failed or not run. Expiry
  closes and advances nothing; the maintainer records the close under the advance rule (charter
  section 9; ROADMAP's 2026-11-21 amendment).
- **The likely state at close:**
  - #226 met or not;
  - #227 likely not run or partial;
  - #224 and steps 4 and 5 not run;
  - no ID-AFTER, so no seal.
- **Implications for v0.5.14 (Part B):**
  - "A close with declared limits does not satisfy a failed precondition" (charter section 2,
    and the end of section 3).
  - Part B's calibration of U1 waits for #227. Ordinary real-data use of F1 waits for #224.
  - So v0.5.14 could not run Part B as sketched. Its charter would first have to carry the unmet
    preconditions as its own work, with fresh caps and time box, or change scope by a new decision.
  - In practice, v0.5.14 would begin where Part A stopped.
