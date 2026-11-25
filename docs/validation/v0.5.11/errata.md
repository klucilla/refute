# v0.5.11 errata log (append-only)

This is Process diet 2, item 5. Each entry gives the date, the source commit, the correction and
its impact. Recorded outputs are never edited.

## 1. 2026-11-24: the recount's Markdown omits part of R7

- **Source:** `docs/validation/v0.5.11/recount/recount.md`, written by the recount unit (rules
  committed in `d0d2ba1`).
- **The discrepancy** (Codex, step 0's first round, blocking item 4): R7 of
  [recount/RULES.md](recount/RULES.md) promises "the same tables" in Markdown as in JSON. The
  Markdown leaves out:
  - the per-test counts of the subgroups (arm, match);
  - the host summaries (records per host, hosts all retained).
- **The correction:** none to the outputs, which are kept as they are. `recount.json` holds the
  full R6 tables and is the reference.
- **Impact:** none on any count. The specification cites the JSON and Codex's own recount.

## 2. 2026-11-24: launch.py version 1's telemetry

- **Source:** `docs/validation/v0.5.11/tools/launch.py`, used for the units of 2026-11-24 from
  23:01Z to 23:47Z.
- **The problems** (Codex, step 0's first round, blocking item 5):
  - transfer taken modulo 2^32;
  - polls that could pass a reservation;
  - disk-scan errors skipped;
  - admission not serialized;
  - the repetition key tied to the worker's hash.
- **The correction:** `tools/launch_v2.py` (commit `f2e977c`) for every later unit. Version 1's
  rows are kept. The ledger treats them as incomplete and charges each the larger of its
  reservation and its measured use (gap G6 of `meter-gaps.json`).
- **Impact:** exit criterion 6 (caps) is "not demonstrated" while a gap remains.

## 3. 2026-11-24: estimated time windows in meter-gaps.json and the consensus README

- **Source:** `meter-gaps.json` (G5, G7, G8; commits `f2e977c` and `ab828ce`) and the section
  title "Step 0: the two rounds on the specification (2026-11-24 and 25)" of
  `docs/plans/v0.5.11-consensus/README.md` (`ec595f4`).
- **The error:** the UTC windows of G5, G7 and G8, and the "and 25" of the title, were written
  as estimates, without reading the clock.
  - The journal's machine timestamps show that all of step 0 and the work up to this entry fell
    on 2026-11-24, before 23:35Z.
  - G8 happened about 23:15Z, not at 00:00Z on the 25th.
- **The correction:** the journal (`log.jsonl`) is the authority for every time. The gap
  entries are kept as written, and this entry corrects their windows.
- **Impact:** none on any measured quantity.

## 4. 2026-11-24: the golden-local "before" unit was interrupted by the transfer bound

- **Source:** the journal, attempt `f85b96ff27bc4a2d91c3e59577c2c939` (unit `golden-local`,
  label `before`, launch_v3, 23:28:33Z to 23:30:26Z).
- **What happened:**
  - The unit reads no network.
  - The launcher's transfer bound is the machine's `netstat -e` bytes, which count every
    program on the machine. That count reached 45,081,465 bytes, the stop level of a 50 MB
    reservation, and the job was stopped after 106.6 CPU-s.
  - No output was written.
- **Consequences:**
  - Under rule (d), a repetition needs the maintainer's approval in #218 first. It is requested
    at the stop.
  - Until then, `src/` in the main checkout stays at its parent, so that the "before" record
    can still be made at the parent.
  - The differential test (`tests/test_v0511_identity.py`) compares versions 1 to 4 with the
    source of `eb70c13` on every machine.
- **A design limit:** a machine-wide upper bound makes long units that use no network
  vulnerable to unrelated traffic. It is recorded for the report.

## 5. 2026-11-24: launch_v3 refused the first tests unit; a junction in pytest's temporary folder

- **Source:** `tools/launch_v3.py` (`ab828ce`), its disk scan (`launch_v2.tree_bytes`).
- **What happened:**
  - The step-1 `tests` unit was refused before dispatch ("the disk baseline has scan errors"),
    with nothing journaled and nothing run, as version 3 requires.
  - An inspection unit found the cause: 2 scan errors in pytest's temporary folder. An old
    test's directory junction points at its own parent. `DirEntry.is_symlink()` is false for a
    Windows junction, so the scan followed it in a loop until the path was too long.
- **The correction:** `tools/launch_v4.py` follows and counts no link and no junction. Every
  other rule is version 3's.
- **A gap:** `.cache/tools/junit_counts.py` was chained after the refused launch in the same
  shell command and ran outside the meter. It found no file. This is gap G9.

## 6. 2026-11-25: the corrected step-2 tests unit was interrupted for lost telemetry

- **Source:** the journal, attempt `c1fc9e01d061448c857734e99b40ba6e` (unit `tests`, label
  `step2-b`, launch_v4, 00:32:39Z to 00:41:32Z, 532.8 CPU-s).
- **What happened:** the launcher stopped the job with reason `telemetry`, as version 4
  requires, and no JUnit file was written.
- **Two possible causes, which the journal cannot separate:**
  - pytest deletes temporary files during the run, so a file can vanish between the scan's
    listing and its `stat`, and the `FileNotFoundError` counted as a scan error;
  - a `netstat -e` counter wrapped (it may be 32 bits wide) and read as a decrease.
- **The correction:** `tools/launch_v5.py`.
  - A vanished file is skipped, not an error. Any other scan error still stops the job.
  - Each transfer counter is unwrapped once per poll when it was above 2^31.
- **What follows:**
  - The unit started, so its repetition needs the maintainer's approval in #218 (rule (d)). It
    is requested at the stop.
  - The JUnit evidence of the corrected diff is therefore not yet available.
  - The earlier step-2 run (`step2-a`, 161 passed) is evidence for the earlier diff only.

## 7. 2026-11-25: the background transfer makes a 0.1 GB reservation stop any unit after about a minute

- **Source:** the journal, attempt `85930b7ea6974b68820350fd0374bb48` (unit `inspect`, a 90 s
  read-only measurement under launch_v6, 01:29:12Z).
- **What happened:**
  - Its 50 MB reservation stopped it after 37.7 s: the machine's 64-bit counters rose by
    52,922,530 bytes, about 1.4 MB/s, with no network use by the unit.
  - Earlier readings were about 0.17 MB/s (a 1 s probe) and 0.4 MB/s (a 113 s unit).
  - The counters sum all 66 interfaces. They include virtual ones, so the same bytes may be
    counted more than once, and the bound is a loose upper bound.
- **The consequence for the amendment of 2026-11-25** (charter, section 14): at that rate, a
  unit without network that reserves 0.1 GB is stopped at 90 MB, after about a minute, whatever
  it does.
  - Its stop level is 90 % of a reservation that is not above twice the 50 MB margin.
  - R1 (golden-local, about 2 to 5 minutes), R2 (the tests, about 10 minutes) and the tag
    verification would be stopped, each wasting an approved repetition.
- **What was done:**
  - R1 and R2 were not started, and the src/ diff stays uncommitted in the working tree.
  - The stop returns to the maintainer with options.

## 8. 2026-11-25: R2' failed D1's condition on one expected ID (a numerical tolerance)

- **Source:** the journal, attempt `1223cf809f9f4452ad02dd9aaf4a0792` (unit `tests`, label
  `step2-b`, launch_v8, approved repetition, 01:45:53Z to 02:08:51Z, 1381.8 CPU-s, completed).
  The JUnit file is `.cache/v0511/junit/step2-b.xml`.
- **The counts:** 171 tests, 1 failure, 0 errors, 0 skipped. 21 of the 22 expected IDs passed.
- **The failed ID:**
  `test_v0511_screen::test_f1_reproduces_the_reference_decisions_on_the_calibration_fixtures[correlated]`.
  - The states agree (`pass`).
  - OE_box was 0.0009411271062525408 in `screen_d5`, against 0.0009411271048073127 in the
    reference, a relative difference of about 1.5e-9. The test's `rel_tol` is 1e-9.
- **The cause:**
  - The weights on a common scale ((min sigma / sigma)^2), added after Codex's second review
    of the diff, change the rounding against the reference's 1/sigma^2.
  - At OE_box near zero, the odd and even depths almost cancel, so the relative difference of
    the statistic is amplified.
- **What follows:**
  - D1's deterministic condition fails, so nothing was committed in `src/`, and the stop
    returns to the maintainer.
  - R1' completed (`golden-before.json`, 20 outputs, none an error). After `git stash pop`, the
    diff's SHA-256 was `35102b10…`, unchanged.

## 9. 2026-11-25: the ledger writer of launch_v7 charged amendment 2's information

- **Source:** `docs/validation/v0.5.11/caps-ledger.json` as written at 02:09Z and later by
  units run under launch_v7 (inspect and commit-check).
- **The defect:**
  - The ledger is rewritten from the journal at the end of every unit, by the launcher that
    ran it.
  - launch_v7 used launch_v2's charging rule, which does not know amendment 2's
    `transfer_role: information`. So it charged against the transfer ceiling the machine
    counter of R1' and R2', which amendment 2 frees.
  - The stop of 2026-11-25 (comment 7150398090) reported 4.15 GB charged from that writer.
- **The fix** (the maintainer's decision received at 00:04 local, item 5):
  `tools/launch_v9.py`.
  - Every unit writes the ledger with launch_v8's information-aware rule.
  - Amendment 2's rule applies to the units the amendment names: `"network": false` with 0
    reserved transfer.
  - Every later unit runs under version 9, and its first ledger write recomputes the whole
    ledger from the journal.
- **Impact:** none on any recorded quantity. The journal is unchanged. Only the ledger's
  charged transfer changes.

## 10. 2026-11-25: the step2-c tests unit's approval, linked

- **Source:** the journal, attempt `46cd4771161b418dabd5a238c8b8dbb9` (unit `tests`, label
  `step2-c`, launch_v9, 03:05:33Z to 03:28:30Z, line 159 of `log.jsonl`). Its `before` row has
  `repetition_approval: null`.
- **The link** (Codex, the review of all the phase's commits, blocking item 3):
  - The run was authorized by the maintainer's decision received on 2026-11-25 at 00:04 local
    (#218, comment 7151559282, recorded at 03:04Z, before the run), item 3. That item asks for a
    new tests unit, a new code state and not a repetition, on the adjusted diff checked by its
    SHA-256.
  - The adjusted diff's SHA-256 is
    `c24bc496a3afdc7d5d402dbbb1f1058adc4190271bde4d570aad677a139c6ba4`. It was checked before
    the run, and again just before the commit `a896c49`.
  - The launcher saw a new logical key (another tree state), so it required no approval
    argument.
- **The journal row is preserved.** This entry is the link.

## 11. 2026-11-25: records whose text lags behind amendment 2

- **`units/tag-verify.json`:** its `choices` text still says "0.1 GB transfer reservation". Its
  actual reservation is 0 (`5f41282`), and the run used 0 under launch_v9.
- **`caps-ledger.json`:** its `transfer_note` still names `netstat -e` for every row. Since
  launch_v6, the source is the 64-bit interface counters, and each `before` row names its own
  source (`transfer_source`).
- **The disk sampler:** it counts the growth of each `disk_extra` path above its size at the
  unit's start. So for `tag-verify` the charged disk is not the whole-path peak, which includes
  the existing warm tag environments.
- **The spec files are not edited,** since they are identities of recorded runs. These entries
  are the correction.

## 12. 2026-11-25: the weights adjustment in a896c49 can make an assessed F1 case abstain

- **Source:** the first `src/` commit `a896c49`. Codex, in the review of all the phase's
  commits, blocking item 1, stored in `docs/plans/v0.5.11-consensus/all-commits-codex-answer.md`.
- **The defect:**
  - With equal flux errors σ = 1e-154, each weight 1/σ² (1e308) is finite.
  - Their sums overflow, so a weighted mean is not available, and F1 gives `not_assessed`.
  - The reviewed common-scale path gave `pass` (OE_box ≈ 0.123) on the same curve.
- **No test caught it:**
  - the extreme-error test covers a range that cannot be represented at all;
  - the 400 reference fixtures use ordinary errors.
- **What follows:**
  - Correcting it changes `src/` again, which needs the maintainer's approval first. It is
    requested at the stop, together with a regression test that keeps the 1e-9 reference
    tolerance.
  - The defect is in the committed code until then.

## 13. 2026-11-25: E1 passed its tests, but the last Codex round refuted it; no src/ commit

- **Source:** the maintainer's decision received on 2026-11-25 at 08:47 local (#218, comment
  7161509920), items 1 and 2.
- **What was done:**
  - The regression test was committed before the fix (`912087a`), as a strict expected
    failure. On `a896c49` it gave 19 tests: 18 passed and 1 strict xfail.
  - The fix (`step2/e1-fix.diff`, SHA-256
    `40cbfb380e2e7c65acef8af60686501bc1b6cb9363ce4a6c739ff2483eafc010`) checks a bound,
    4 max(f^2) times the total weight, before using the raw 1/σ².
  - Its tests unit (label `e1-fix`) gave **172 tests, 0 failures, 0 errors, 0 skipped, with all
    23 expected IDs passing.**
- **The second and last round of Codex's review of all commits: REFUTED,** with two witnesses:
  - **A changed decision.** With equal errors of 4.5e-153, the raw reductions are finite and
    give OE_box 2.9999999999743827 (`pass`). The preflight bound overflows, though, and the
    common scale gives 3.0000000000069456 (`fail`). The bound uses max |f| instead of the
    centered terms.
  - **A missed overflow.** In a 20-point probe the raw total weight was finite
    (1.7976931348623155e308), but the bin totals overflowed after grouping.
- **What followed, by the decision:**
  - The work stops with no new round, and nothing was committed in `src/`.
  - The fix stays uncommitted in the working tree. A request to restore that tree to `HEAD` was
    refused by the session's safety classifier, so the change is kept, and its diff is recorded.
  - `a896c49` keeps the defect of entry 12.
  - Codex's proposed fix: raw weights, and a check of the actual sums, products and centered
    squares in `_wmean`, `_wstd` and the bin totals, with a retry from scratch on the common
    scale when one overflows, plus regression cases for both witnesses. It is the maintainer's
    to decide.

## 14. 2026-11-25: correction 1 of the specification withdraws the E1 test; the E1 change is overwritten

- **Source:** the maintainer's decision received on 2026-11-25 at 09:34 local (#218, comment
  7162573384), item 1, and [correction 1](../../plans/v0.5.11-spec-correction-1.md) (`7bf74b1`).
- **The E1 test is withdrawn.** It was committed at `912087a`, as
  `test_tiny_equal_errors_give_the_same_f1_as_ordinary_equal_errors`, and required σ = 1e-154
  to give the same assessed F1 as ordinary errors. The correction decides the opposite: that σ
  is outside [1e-12, 1e3], so F1 is `not_assessed`, with the reason `invalid_uncertainty`.
  - It is replaced by `test_the_case_of_errata_12_is_unassessed_in_the_core_and_the_report`.
  - `step2/expected-tests-e1.json` stays as the record of E1. The condition is now
    `step2/expected-tests-ir.json`.
- **The uncommitted E1 change is gone from the tree.** As the decision says, the file
  `src/refute/packs/tess/screen_d5.py` was overwritten with the bytes of `a896c49`, with no
  `git checkout` and no stash. Its SHA-256 is `30bd588f…`, and an inspection unit checked it
  equal to the committed blob. E1's diff stays recorded in `step2/e1-fix.diff`.
- **Tests before the code:** on `a896c49`, the tests unit labelled `ir-before` gave 30 tests,
  0 failures, 0 errors, and 6 strict expected failures (the six IDs of `expected-tests-ir.json`).
- **Small steps outside the meter,** listed in `meter-gaps.json`:
  - G11: while preparing the commit of the correction, the agent ran `python -c "print(1)"`
    once outside the launcher. It used no data and wrote nothing.
  - G12: the file copy that overwrote the E1 change.
