# X2e's execution package (for the maintainer's authorization; not run)

Prepared on 2026-10-22 (the maintainer's decision after X2, item 2). **X2e's lot has not run**; it
runs only after the maintainer's authorization, and the work stops here until then. It comes before
any code of a correction of the error model.

## 1. What is run

- **The declaration:** [x2e-declaration.md](x2e-declaration.md) (the cells without variability, 20
  new cases each from `refute-v0.2.1-x2-2` by X2's rule, 100 realizations each, the pooled analysis).
- **The lot:** 2 cells × 20 cases × 100 realizations = **4000 light curves**, every observing year's
  round by `calibration_measurement` on the study's M4 configuration, with the twin and the registered
  windows, exactly as X2's records.
- **Afterwards:** `x2_study.py check`; `x2_study.py evaluate` (X2e alone) and `x2_study.py
  evaluate-pooled x2/x2-evaluation.json <run folder>` (the pooled analysis); the results record;
  Codex's review; a stop.

## 2. The code (in this commit, with its tests)

`docs/validation/v0.2.1/population/x2_study.py` gains a lot specification (`LotSpec`): **X2 is the
default and unchanged** (its seeds equal `x2/x2-seeds.json`, its cases, its manifest's shape: tested);
X2e is `X2E` (`--lot x2e`): its prefix, cells, seed rule (with the prefix), record and lot formats; the
runner, the record check and the evaluation read the lot from the manifest (`lot: x2e`); the pooled
analysis (`pooled_rows`, `evaluate_pooled`) names each case by its prefix. `x2_evaluate.py` is
unchanged except the fix of the stored intervals (item 4; its own test). Tests (`tests/test_x2.py`,
29): X2 unchanged; X2e's cases (40, the declared composition) and seeds (the rule; none shared with
X2's); an X2e lot naming itself and refusing an X2 record; the pooled naming; and X2's tests, the
runner's resumption included.

## 3. The seeds

[x2/x2e-seeds.json](x2/x2e-seeds.json) (SHA-256
`2a14b6dd45277378b2fcce857a306d4a623b579e59047a822db2bbfb5014fba2`), made by
[x2/scripts/x2e_seeds.py](x2/scripts/x2e_seeds.py): **4000 seeds, all distinct, no collision** with the
715 200 seeds checked (X2's 8000 realizations; each case's seed and first noise seed in bs-choice, the
R_min study's 64 prefixes, the timing lot, X2's and X2e's cases).

## 4. The resumption

The runner is X2's (its resumption shown byte for byte on the real configuration, and in the tests);
X2e only passes its specification through it, and the tests run an X2e lot through it. **Pre-approval
of the resumption, to be opened as an issue if the maintainer authorizes the lot** (as
[klucilla/refute#165](https://github.com/klucilla/refute/issues/165)): if X2e's lot is interrupted by a
shutdown or restart of the PC by the maintainer, or by a failure of the process, its resumption is
approved with the exact procedure (the same command
[x2/scripts/run_x2e_lot.ps1](x2/scripts/run_x2e_lot.ps1) with `-RunDir` on the same folder, the same
code, 22 workers on processors 8 to 31, `--deadline-hours 3` read from each launch's start); any other
change needs a new approval; each resumption recorded on that issue and in the run's reports.

## 5. The run (proposed)

- **Where:** `.cache/x2e-lot/<UTC date>/` in the integration worktree.
- **Command:** [x2/scripts/run_x2e_lot.ps1](x2/scripts/run_x2e_lot.ps1) (one window, not as
  Administrator): the affinity `0xFFFFFF00`, the study's configuration, `x2_study.py run <folder>
  --lot x2e --workers 22 --deadline-hours 3`, then `check`.
- **Affinity and workers:** logical processors 8 to 31; 22 workers.
- **Cost:** X2 did 8000 curves of all four cells in 4.03 h (0.55 curves per second); these two cells'
  curves are cheaper on average (many `two_years` and `few_train` rounds stop before the measurement),
  so **about 1.2 to 2 h** for 4000.
- **Ceiling:** `--deadline-hours 3` (1.5 times the upper estimate): no task is submitted after it,
  and the tasks already in flight (at most 4 per worker) end, so the run can pass 3 h by their time
  (minutes); an incomplete lot is reported as such; nothing is extended without the maintainer. The
  wrapper exits with the run's or the check's failing code (X2's wrapper only printed them, Codex's
  review).
- **Archive:** after the results, the records to the Drive with a checked SHA-256 manifest, as X2's.

## 6. What the maintainer is asked

To authorize X2e's lot as in section 5 (or to change it), and the opening of its resumption issue.
Specification C's analysis on X2e's data, the replicate of the cells with variability (spec C, C6) and
any correction's code each need their own authorization.
