# v0.2.1 workers equivalence: acceptance criteria

Status: **criteria fixed before any validation runs.** This file is committed on its
own, before the tests and the code it describes. Written 2026-10-10 on branch
`claude/v0-2-1-gauntlet-fixes-13f5e7`.

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
variables into `os.environ`). Every subprocess gets the test process's environment
with `REFUTE_WORKERS` removed; the thread variables are left as inherited and are
recorded, not set by the test.

- **O** (original): the full claim with `--workers 3` (one spawned worker per target).
- **F**: the full claim with `--workers 1` (all targets in the main process).
- **R11, R12, R13**: the `REPRODUCE.md` command for each target,
  `--target <key> --workers 1`, each in its own process.

### Level (a): the REPRODUCE.md contract (pass/fail criterion)

For each target, `check_dossier(R_k, against=O_k)` and `check_dossier(F_k,
against=O_k)` must be OK: manifest integrity of both dossiers, and
`compare_dossiers` equal (verdict, status, every test's status, `key_values` within
relative tolerance 1e-6, input data hashes identical). For the full runs, F and O must
also have the same self-claim result and criterion values, and the same verdict per
target in `summary.json`.

### Level (b): exact equality (diagnostic, recorded)

The canonical bytes of each `verdict.json` (F and R against O) and of `summary.json`
(F against O), after removing only the allowed operational differences below, are
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
6. Names of the run directories and absolute paths.

The partial runs R11-R13 have a NOT_EVALUATED self-claim by design (`--target`); their
`summary.json` is not compared.

## Acceptance criteria

- E1. Level (a) holds for every target, for F and for each R_k, and for the full-run
  summary.
- E2. Every dossier of every execution has `environment/numeric_runtime.json` with
  the fields listed above; the test report prints, per execution and target, the
  loaded BLAS libraries and their thread counts and the four thread variables.
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
not write `numeric_runtime.json`; the test records its absence instead of failing E2
for that run. The result says whether the `REPRODUCE.md` contract holds **for these
synthetic scenarios** on the locked code. It is evidence for these scenarios, **not**
proof that the real v0.2 dossiers reproduce. If a discrepancy appears, its scope and
impact go into the release notes; the v0.2 results and lock are preserved unchanged.

## Place in the v0.2.1 plan and cost

An engine item independent of the H hypotheses, required **before the v0.2.1 lock**
(it supports the reproducibility of every dossier), alongside the coverage
requirement. It comes before the CI change of option D. Estimated CI cost: five
offline executions of a 3-target calibration (O, F, R11-R13), about 2 minutes per job
(an estimate by analogy with `test_calibration_run_evaluates_the_self_claim`, 23 to
27 s for one 3-target execution in CI; not yet measured).
