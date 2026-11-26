# v0.5.12: the seal of exit criteria 1 to 6

The charter, step 5 and section 8 (#218 comment 7199932177, item 2). Sealed at the pushed SHA
`2aa20d8f526ab5b9371d551e51a9ac79fa92ffc8` and the journal cursor `669`, the last line of
`docs/validation/v0.5.12/log.jsonl` at that SHA. Labels: `exploratory`, `method_status: not_validated`.
The gate judges these criteria at this seal. **STOP before the gate.**

| # | Criterion | Sealed as | Evidence |
|---|---|---|---|
| 1 | #222 answered by the fixed rule | **met** | see "Criterion 1" below |
| 2 | #223 covered | **not met** | see "Criterion 2" below |
| 3 | F-1's cause found and recorded | **met** | see "Criterion 3" below |
| 4 | Versions 1 to 4 did not move | **met** | see "Criterion 4" below |
| 5 | Full CI | **met** | see "Criterion 5" below |
| 6 | Records complete; caps measured and met | **not met** | see "Criterion 6" below |

**Criterion 1, #222.**
- M1 failed, as recorded before its run (`step1/m1-summary.json`): P2.4, P9.5 and B6.
- Correction 2 revision 1 had its blind review (`WEAKENED`; B1 and B2 applied with its exact
  wording) and was adopted at its stop, against SHA-256 `c24e7fd9…`
  (`notes/adoption-correction-2-r1.json`).
- Its tests came before its code: `98117ef`, then `src/` at `6f83a91`.
- M2 passed in every family, with 0 `not_assessed` and fails of 5 to 12 out of 3,000
  (`step4/m2-summary.json`).
- The sensitivity control passed in every family, with 285 to 297 fails out of 300
  (`step4/control-summary.json`).
- The unequal-depth binary regression passed in the 97 tests (`step4/junit-after-src-summary.json`).

**Criterion 2, #223, not met.**
- The coverage holds:
  - 70 branches; 66 have a case (natural witness or fault injection);
  - 4 are proven unreachable, with #225;
  - every report-only record has a `computed` witness with values;
  - the 97 tests pass with 0 skips and 0 xfails, with the checker `step4/junit_check.py`.
- **The order in git does not hold.** `step2/inventory.json` entered git at `e1834c1`, after the
  first probe (`6f9925e`). The charter asks for the inventory first in git, and the journal hash
  of its run does not stand in for that without a maintainer amendment (Codex's review of all the
  phase's commits, item c; deviation 3).

**Criterion 3, F-1.** Found: the BLAS thread count, in all three pairs. The first differing
operation is `battery_v51._wls`, line 45, `normal = (x.T * w) @ x` (`step3/f1-cause.md`,
`step3/f1-result.json`). No byte of versions 1 to 4 changed.

**Criterion 4.**
- The golden and claim-hash payloads are equal before and after, provenance excluded
  (`step5/compare_after.py`).
- `verify_locked_tags.py` gives joint PASS, 10 of 10 (`step5/verify-tags-summary.json`).

**Criterion 5.**
- `scripts/ci_evidence.py 6f83a912013f8fe90c208a31467575a6d0edd385 --level full` holds: run
  45868952282 (push), 28 jobs, all success (`step5/ci-evidence-6f83a91.txt`). The background wait
  ran with no push meanwhile (`step5/ci-wait-45868952282.txt`).
- Runs 727 (`e9ef62e`) and 726 (the nightly) were cancelled by the adviser (deviation 12).
- `uv.lock` and `pyproject.toml` are unchanged in the phase.

**Criterion 6, not met.**
- 11 gaps (G0 to G10, `meter-gaps.json`).
- The ledger says the caps are "not demonstrated" under amendment 1 (the network block was
  dropped for offline units).
- Retries with no approval reference (deviations 10 and 11).
- The three measured ceilings did hold: CPU 6,994.6 CPU-s (1.94 CPU-h, the ledger as committed
  with this seal) of 3 CPU-h; downloads 0; peak disk 457.2 MB of 2 GB.

**Codex's review of all the phase's commits** (`step5/phase-review-codex-answer.md`): `REFUTED` for
sealing as it stood. Its findings are applied here:
- criterion 2 is sealed as not met;
- criterion 6 is sealed as not met;
- the JUnit evidence and its checker are committed;
- the missing deviations are recorded (10 to 12).
