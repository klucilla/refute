# v0.2.1: development runs before the acceptance documents, and amendments after the code

Status: **declaration**, written 2026-10-11 at the maintainer's request. It covers H7,
H4 and H9(a). It changes no criterion, threshold, test or result.

The rule of the roadmap holds for all three: each acceptance document was committed
before the tests and the code of its change (ROADMAP.md, v0.2.1, Exit criteria: "Every
change has acceptance criteria, metrics and regression cases committed before its tests
and code"). Some development runs on synthetic data were made **before** a document was
committed, and some amendments were made **after** the code. One criterion was weakened
in the code commit itself: B1 of H4 (Amendment 1, section B); the test committed before
the code already asserted the weakened wording. This file declares all of it so that a
reader can weigh it.

**Sources.** The session transcript of 2026-10-10 (tool calls and their outputs), which
is not published. The scripts and their outputs are kept in
[`pre-document-runs/`](pre-document-runs/): each script as it was written (the only
change is the Windows user name in paths, replaced by `<user>`), and each output
transcribed literally from the transcript, with a header saying so, because no output
was saved to a file at the time. A transcribed output records what the session showed;
it is not a machine capture, and its SHA-256 fixes only the transcription. Each script
can be rerun on the commit in the column "Code at", which also lists the uncommitted
changes to `src/` or `tests/` that the transcript shows between that commit and the run
(file edits, and shell commands that write files or run `git checkout`, `apply` or
`stash`). `SHA256SUMS` lists the SHA-256 of
every file of the folder. All times are UTC.

## Order of the documents, tests and code (2026-10-10, UTC)

| Change | Acceptance document | First tests | First code |
|---|---|---|---|
| H7 | `a58ea97` 15:51:39 | `04e6221` 16:11:19 | `3217db7` 16:23:48 |
| H4 | `1fadc06` 16:46:28 | `462f141` 16:53:43 | `78d79f5` 17:18:08 |
| H9(a) | `7829912` 18:10:07 | `cd69ce5` 18:17:58 | `9d3f369` 22:21:52 |

The seeds of each change, and the H4 thresholds 0.2 and 0.5, are fixed in the first
commit of its acceptance document.

## A. Development runs

| Started (UTC) | Script | Code at | Seeds | What was measured | Result (summary) | Decision it influenced |
|---|---|---|---|---|---|---|
| 16:04:13 | `premises.py` (run 1) | `a58ea97`; no uncommitted change found in the transcript | 0-2 | nothing: the launch with `start /affinity` failed with "Acesso negado" | no result | none |
| 16:06:03 | `premises.py` (run 2) | `a58ea97`; no uncommitted change found in the transcript | 0-2 | the period found and the verdict for a prototype of `fp_variability_dominates` (2.9 d eclipse plus a 4000 ppm sinusoid at 0.7 d), `eb_secondary`, `eb_odd_even`, `eb_equal`, `planet`, `planet_three_years` | the prototype finds 0.6993 d (the sinusoid) and is REFUTED; the binaries find their injected period and are REFUTED; the planets find 3.7 d and SURVIVE | none on the H7 document: it ran **after** it (`a58ea97`, 15:51:39), to check the premises that the H7 end-to-end tests then assert |
| 16:36:13 | `h4_survey.py` | `f1b133a`; between that commit and this run the transcript shows two sabotages of `src/refute/packs/tess/calibration.py` (16:27:05 and 16:27:39), each applied and restored with `git checkout` in the same command, with an empty `git diff` after each; no other change found | 0-9 | per holdout round of every existing scenario plus `fp_variability_dominates`: status, train SNR, train duration/period (D/P), fraction of the hidden time covered by the windows; and the rounds with SNR < 7.1, D/P > 0.2 and window fraction > 0.5 | only `sinusoid` and `fp_variability_dominates` exceed D/P 0.2 (0.357) and window fraction 0.5 (up to 1.000), 20 rounds each, all PASS on the code of that time; `noise` exceeds D/P 0.2 in 2 rounds and SNR < 7.1 in 20, all already INCONCLUSIVE; `vanishing` has 10 rounds with SNR < 7.1, already INCONCLUSIVE | the thresholds **0.2 and 0.5 were already in the script**, so they were seen against development data before the maintainer approved them (16:40:14). The H4 document records these numbers as its "Baseline on the development set" and derives the thresholds from the window geometry |
| 16:40:48 | `h4_proto.py` (run 1, first version) | `f1b133a`; between that commit and this run the transcript shows two sabotages of `src/refute/packs/tess/calibration.py` (16:27:05 and 16:27:39), each applied and restored with `git checkout` in the same command, with an empty `git diff` after each; no other change found | 0-4 | a weak planet at 400-800 ppm, and a planet with a 4000 ppm sinusoid at 0.7 d in 2018-2019 only | weak planet: train SNR 9.16 to 23.96, never below 7.1; sinusoid: the 2020 round trains at 0.7 d (D/P 0.357) and is FAIL; in seed 3 the 2019 round is PASS (hidden SNR 5.2) | the weak planet at these depths cannot show rule (a) alone; the sinusoid prototype became the `variability_train_only` scenario (same amplitude and period) |
| 16:41:48 | `h4_proto.py` (run 2, after a `sed` edit) | `f1b133a`; between that commit and this run the transcript shows two sabotages of `src/refute/packs/tess/calibration.py` (16:27:05 and 16:27:39), each applied and restored with `git checkout` in the same command, with an empty `git diff` after each; no other change found | 0-9 | the weak planet at 200, 230 and 260 ppm | all 60 rounds are already INCONCLUSIVE through the timing-uncertainty rule | **`weak_planet` discarded** (recorded in the H4 document, "Scenario tried and discarded") |
| 16:45:59 | `vanishing_rounds.py` | `f1b133a`; between that commit and this run the transcript shows two sabotages of `src/refute/packs/tess/calibration.py` (16:27:05 and 16:27:39), each applied and restored with `git checkout` in the same command, with an empty `git diff` after each; no other change found | 0-9 | the status and train SNR of every `vanishing` round | 2018 rounds INCONCLUSIVE (train SNR 4.2 to 5.4); 2020 rounds FAIL except **seed 4, INCONCLUSIVE** | **seed 4 excluded** from B2 and B6 of H4, decided after seeing that its 2020 round is INCONCLUSIVE (recorded in the H4 document) |
| 18:09:48 | `h9_premise.py` | `817ea13`; no uncommitted change found in the transcript | 0-4 | `planet` with a TESS-EB row under its own TIC at 3.7 d, and `blend` with a neighbor's row at 2.3 d, on the code before H9(a) (the behavior that `same_photometry_catalogs: []` restores) | `planet`: REFUTED, `eb_catalog` the only fatal failure; `blend`: REFUTED by `centroid_shift`, `aperture_depth` and `eb_catalog` | none derived: it checked the premises of B1 and B3. It finished at 18:10:00, 7 s before the H9(a) document was committed |

Notes on the preserved files:

- `h4_proto.py` is the file as it was on disk after the `sed` edit of 16:41:48 (the
  version of run 2). The version of run 1 exists only in the transcript and is
  transcribed as `h4_proto.first-version.py`.
- The output of `h4_proto.py` run 2 is what its command printed through a filter
  (`grep`, `awk`, `sed`); the unfiltered output was never shown and does not exist.
- `affinity_run.py`, the launcher that set the CPU affinity of these runs, is not part
  of the analyses and is not copied.
- No output is missing.

## B. Amendments made after the code

| Amendment | Commit (UTC) | Relative to the code | Classification |
|---|---|---|---|
| H7 Amendment 1 (A11 stronger, B6 added) | `e5ddee1` 16:25:49; tests `f1b133a` 16:26:57 | 2 min after `3217db7` | **strengthens a criterion** |
| H4 Amendment 1 (wording of B1) | `78d79f5` 17:18:08 | in the code commit itself | **weakens a criterion**, see below |
| H4 Amendment 2 (sabotage results) | `eb594e6` 17:23:20 | after the code | **records results** |
| H9(a) Amendment 1 (sabotage results) | `4d3734c` 22:24:16 | after the code | **records results** |

**H7 Amendment 1.** Written after the code, in answer to two sabotages that the
original cases did not catch. A11 became an exact difference plus a strict inclusion
on at least one development seed; B6 forces the published period to 2x and 1/2x the
injected one. **B6 was written after the code and never had a red phase** against the
code before H7. The only evidence that the new cases fail on a defect is the rerun of
the two sabotages, never committed; their outputs are transcribed in
`pre-document-runs/` (`h7_sabotage2_rerun.output`, `h7_sabotage3_rerun.output`).
Sabotage 2 (factors ignored, 16:27:05) failed the 6 B6 cases, and sabotage 3 (flag
ignored, 16:27:39) failed A11. Both ran on `f1b133a` with the sabotage applied to
`src/refute/packs/tess/calibration.py` as an uncommitted change, restored with an
empty `git diff` after each.

**H4 Amendment 1.** The change to B1, in the same commit as the code:

```diff
   the hidden year is not read. The other rounds of this scenario fail with a *valid*
   train (the sinusoid in their hidden year lowers the SNR); that is outside H4 and
-  they must stay FAIL. Seeds 0-4.
+  ~~they must stay FAIL~~ *(Amendment 1)* they have no reason and the same status with
+  the guard on and off. Seeds 0-4.
```

The meaning changed. The original required the 2018 and 2019 rounds of
`variability_train_only` to be FAIL; the amended text requires only that H4 gives them
no reason and leaves their status unchanged. That removes an expectation, so it is
classified as weakening a criterion. The removed expectation was already false on the
development data before the document was written: in `h4_proto.py` run 1 (16:40:48),
the 2019 round of seed 3 is PASS. The test committed before the code (`462f141`,
16:53:43) already asserted the amended wording (no reason, same status), not FAIL, so
for 24 minutes the document and the test disagreed; the amendment aligned the document
with the test.

**H4 Amendment 2** records the sabotage results; it also corrects the table of planned
catches (D3 did not catch S1) and records that S5 is undetectable by the H4 cases. No
criterion of the cases changes. **H9(a) Amendment 1** records the sabotage results,
including a first sabotage run that did not execute.

## Statement

All the runs above were development runs on synthetic data, with no known target. The
confirmation set, with seeds derived from a future drand round, will have no run before
its document, and no exclusion decided after seeing a result, and no scenario chosen,
changed or discarded after seeing a result.
