# v0.2.1 workers equivalence: acceptance criteria

Status: **criteria fixed before any validation runs.** This file is committed on its
own, before the tests and the code it describes. Written 2026-10-10 on branch
`claude/v0-2-1-gauntlet-fixes-13f5e7`. Amended twice (below): Amendment 1, before
any test was written (the adversarial execution F4 and the exact path normalization);
Amendment 2, after the first test run and before the code of the record (an explicit
environment, the legacy mode, a stricter E2 and checked premises).

## Problem

A calibration runs its targets in parallel (`--workers N`, one spawned process per
target), but every dossier's `REPRODUCE.md` reproduces one target with
`--target <key> --workers 1`, which runs the analysis **in the current process**
(`run_processes` with one task or one worker does not spawn). The existing tests prove
that results keep the task order and that a run reproduces with `workers=1`; no test
compares the same analysis with `workers=1` and `workers >= 2`.

Until such a test exists, the correct statement is: **the number of workers should
change only the execution, preserving the scientific results.** (Commit `2d51f25`
replaced an earlier "never changes results" in `runner.py` and `ci.yml`.)

### Correction of an earlier diagnosis (recorded at the maintainer's request)

In the planning message of 2026-10-10 the agent suggested that the `workers=1` path
might use a different BLAS threading than the worker processes because "init_worker
forces one BLAS thread in the children but the `workers=1` path runs in the main
process without it". **That was wrong on both counts:**

- the `workers == 1` (or single-task) path of `run_processes` **also calls
  `init_worker()`**, in `cc9d104` and in the current code;
- `init_worker()` uses `os.environ.setdefault(name, "1")` for `OMP_NUM_THREADS`,
  `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS` and `NUMEXPR_NUM_THREADS`: it keeps any
  value already set and **does not force** one thread.

The suspicion is therefore not confirmed. The right question, which this test must
answer with evidence, is: **which BLAS configuration is effectively active in each
path**, given the environment each process inherits and **when** the numerical
libraries are loaded relative to `init_worker()` (a thread variable set after a BLAS
library was loaded may have no effect on it).

## What is built

1. **Record of the numerical runtime (engine).** Each target's dossier gets
   `environment/numeric_runtime.json`, written by the process that analyzes the
   target, at the start of the analysis: the BLAS/LAPACK libraries actually loaded
   and their active thread counts (from `threadpoolctl`, which is in `uv.lock` as a
   dependency of scikit-learn; it is imported only if available, and the record says
   so otherwise, so no dependency is added), the NumPy version and BLAS name, the
   values of the four thread variables at that moment, and whether the analysis runs
   in the main process or in a spawned worker. It is operational metadata (see the
   list of allowed differences) and it is reported, not used to decide.
2. **The equivalence test** (`tests/test_workers_equivalence.py`), described below.

Not changed: any analysis, threshold, verdict rule or the contract of
`refute check-dossier`.

## The test

### Claim and data (frozen)

A calibration claim locked in a temporary git repository, as in
`tests/test_dossier.py`, with the fast test plan and every default, run offline from a
synthetic cache written with `write_synthetic_cache` (light curve, star and auxiliary
data). Three targets, so that the multi-worker run spawns a process per target:

| Target | Scenario | Role | Blind holdout represented |
|---|---|---|---|
| TIC-11 | `planet` | planet | rounds that read the hidden year (PASS) |
| TIC-12 | `eb_secondary` | false positive | periodic eclipsing binary |
| TIC-13 | `vanishing` | planet | a round that FAILs (signal absent in the hidden year) |

Every scenario uses development seed 0 (the synthetic data are deterministic in the
seed). The confirmation set is not used.

### Executions

Each execution is a **new, independent process** (a subprocess of the test running the
`refute` command line), never two executions in the same process: the first would
change the environment inherited by the second (`init_worker()` writes the thread
variables into `os.environ`). ~~Every subprocess gets the test process's environment
with `REFUTE_WORKERS` removed; the thread variables are left as inherited and are
recorded, not set by the test.~~ *(Amendment 2)* Every subprocess gets the test
process's environment with `REFUTE_WORKERS` **and the four thread variables**
(`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`, `NUMEXPR_NUM_THREADS`)
removed. F4 starts from the same clean base and sets only its three variables.

- **O** (original): the full claim with `--workers 3` (one spawned worker per target).
- **F**: the full claim with `--workers 1` (all targets in the main process).
- **R11, R12, R13**: the `REPRODUCE.md` command for each target,
  `--target <key> --workers 1`, each in its own process.
- **F4** *(Amendment 1)*: the full claim with `--workers 1`, in a new process whose
  environment has `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` and `MKL_NUM_THREADS`
  set to `4` **by the test** before the process starts (from the clean base of
  Amendment 2, so `NUMEXPR_NUM_THREADS` is not inherited either). `init_worker()` keeps those
  values (`setdefault`), so this is the case that can break: the inherited environment
  without those variables is the easy case.

### Level (a): the REPRODUCE.md contract (pass/fail criterion)

For each target, `check_dossier(R_k, against=O_k)`, `check_dossier(F_k,
against=O_k)` and `check_dossier(F4_k, against=O_k)` must be OK: manifest integrity of both dossiers, and
`compare_dossiers` equal (verdict, status, every test's status, `key_values` within
relative tolerance 1e-6, input data hashes identical). For the full runs, F and O must
also have the same self-claim result and criterion values, and the same verdict per
target in `summary.json`; so must F4 and O.

### Level (b): exact equality (diagnostic, recorded)

The canonical bytes of each `verdict.json` (F, F4 and R against O) and of
`summary.json` (F and F4 against O), after removing only the allowed operational differences below, are
compared for exact equality. Any difference is **recorded** (a test warning listing
each differing field, and a JSON report in the test's temporary directory); it does
not fail the test. A difference only in the last digits of a number, or in a PNG, is
**not** called a failure of scientific reproduction. If level (b) shows differences,
their cause is investigated (starting with the recorded numerical runtime) before any
tolerance or code change is proposed.

### Reports and plots (diagnostic, separate)

`report.md` and every PNG under `plots/` are compared byte for byte, apart from the
scientific results, and recorded in the same report. They never fail the test.

### Allowed operational differences (closed list)

Only these may differ without being reported as a level (b) difference:

1. `verdict.json`: `provenance.run_id`.
2. `report.md`: the line `- Run: \`<run_id>\`, Refute <version>`.
3. `MANIFEST.sha256` of each dossier (it hashes the files above).
4. `environment/numeric_runtime.json` (recorded and reported for every execution).
5. `summary.json`: `run.run_id`, `run.started_utc`, `run.finished_utc`,
   `run.workers`; `summary.md`: the footer lines with those fields.
6. The run directory of each execution: before any comparison, every occurrence of
   that execution's run-directory path (the exact absolute path string, as written by
   the run) is replaced by the fixed marker `<RUN_DIR>`. **Nothing else is
   normalized**: no removal or rewriting by a generic pattern of anything that looks
   like a path *(Amendment 1)*.

The partial runs R11-R13 have a NOT_EVALUATED self-claim by design (`--target`); their
`summary.json` is not compared.

## Amendment 1 (2026-10-10, before the tests): F4 and exact path normalization

Requested by the maintainer after the first version of this file, before any test was
written:

- **F4**, the adversarial case of `setdefault`, is added to the executions, to level
  (a) and level (b), and to E1 and E2 (see above).
- **Paths** are normalized only by exact replacement of each execution's run-directory
  prefix with a fixed marker; no generic pattern is used.

## Amendment 2 (2026-10-10, after the first test run, before the record's code)

Requested by the maintainer after the second commit (`b7e34dd`):

1. **Explicit environment.** O, F and R11-R13 run with the four thread variables
   removed from the subprocess environment; F4 starts from that clean base and sets
   only `OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS` and `MKL_NUM_THREADS` to `4`. The
   reason is to have **explicit, repeatable scenarios**. This file makes **no claim**
   about how often either environment occurs on real machines; that was not measured.
   **The first run of the test (`b7e34dd`) is an exploratory observation only**: its
   subprocesses inherited the test process's environment, which may already hold
   thread variables written by `init_worker()` in earlier in-process runs of the suite,
   so its environment possibly depended on the order of the suite.
2. **Legacy mode, `REFUTE_EQUIVALENCE_LEGACY_CODE=1`.** In normal mode (the variable
   unset) E2 requires `environment/numeric_runtime.json` in every dossier. In legacy
   mode E2 requires the file to be **absent** in every dossier **and** the code hash
   of the Refute code under test (computed with the lock's own mechanism,
   `refute.core.codehash.compute_code_hash`, on the installed source tree, not on the
   claim's temporary repository) to equal the code hash locked in `cc9d104`
   (`calibration/v0.2/self_claim.lock.json`,
   `2cd8b5c16c9ded3e32335cd95d8b68f46e0676d5183f3129a6cef4e8dfbd1752`). Anything
   else fails. The mode exists only for the one-off run against `cc9d104`.
3. **Stricter E2 (see below).** The record must come from `threadpoolctl`, with an
   identified BLAS backend and valid, non-empty thread counts. If the introspection
   does not provide that, E2 fails and the BLAS question is recorded as **NOT
   MEASURED**. F4 is checked by the threads `threadpoolctl` reports, not by the
   variables. **Configured threads do not mean that every operation uses all of
   them**: the record shows the libraries' thread settings, not the threading of each
   call.
4. **Checked premises.** Before any comparison, the test confirms in O that the
   planet's blind holdout PASSES with at least one round that read the hidden year,
   that the vanishing planet's blind holdout FAILS, and that the false positive is
   flagged (verdict REFUTED, counted in the flagged criterion). If a premise fails,
   the test fails before comparing.
5. Socket blocking stays on; no warning is silenced generically.

## Acceptance criteria

- E0 *(Amendment 2)*. The premises of item 4 hold in O.
- E1. Level (a) holds for every target, for F, F4 and each R_k, and for the full-run
  summaries of F and F4.
- E2. Every dossier of every execution has `environment/numeric_runtime.json` with
  the fields listed above, with `process` equal to `worker` in O and `main` in F, F4
  and R; ~~in F4 the three variables set by the test are recorded as `4`~~.
  *(Amendment 2)* `threadpoolctl_available` is true, the BLAS backend is identified,
  and every reported thread pool has a positive integer thread count (the list is not
  empty); in F4 every BLAS pool reported by `threadpoolctl` has 4 threads. Otherwise
  E2 fails and the BLAS question is recorded as NOT MEASURED. The test report prints,
  per execution and target, the loaded BLAS libraries and their **effective** thread
  counts and the four thread variables. In legacy mode E2 is as described in
  Amendment 2, item 2.
- E3. The level (b) and report/PNG results are recorded (warning and JSON report),
  whatever they are.
- E4. The full existing suite passes; `ruff check` and `ruff format --check` pass.

## Planned sabotages (run after the code passes, never committed)

Each is applied only when the analysis runs in a spawned worker (so it separates the
two paths), run against this test only, and reverted with an empty `git diff`.

| Sabotage | Expected |
|---|---|
| S1. A `key_values` number changes by 1e-3 relative in workers | level (a) fails |
| S2. The same number changes by 1e-9 relative in workers | level (a) passes; level (b) records the difference |
| S3. One test status changes in workers | level (a) fails |
| S4. A data-manifest hash changes in workers | level (a) fails |
| S5. A non-contract field (`verdict_reason`) changes in workers | level (a) passes; level (b) records it (the allowed list does not hide it) |

## Running it against the locked v0.2 code (`cc9d104`)

After the test exists and passes here, it is run **once** against a separate checkout
of `cc9d104` (the v0.2 calibration lock), with nothing committed there. That code does
not write `numeric_runtime.json`; the run uses the legacy mode of Amendment 2 (item 2),
which requires that absence and the locked code hash. The result says whether the `REPRODUCE.md` contract holds **for these
synthetic scenarios** on the locked code. It is evidence for these scenarios, **not**
proof that the real v0.2 dossiers reproduce. If a discrepancy appears, its scope and
impact go into the release notes; the v0.2 results and lock are preserved unchanged.

## Place in the v0.2.1 plan and cost

An engine item independent of the H hypotheses, required **before the v0.2.1 lock**
(it supports the reproducibility of every dossier), alongside the coverage
requirement. It comes before the CI change of option D. Estimated CI cost: six
offline executions of a 3-target calibration (O, F, F4, R11-R13), about 2 to 3 minutes per job
(an estimate by analogy with `test_calibration_run_evaluates_the_self_claim`, 23 to
27 s for one 3-target execution in CI; not yet measured).
