You are reviewing a CI change in the Refute repository (the working tree at C:\Projetos\refute; read
only). Do not edit anything. Never open K:\Meu Drive\Pessoal\Segurança. Answer in English.

## The maintainer's decision (2026-11-24, #218 comment 7133936093, item 2)

Two-level CI:
- on every push to main and on PRs, a fast matrix: only ubuntu-24.04 with Python 3.12.15 and
  windows-2025 with Python 3.13.16, with the 7 shards (14 jobs);
- the full matrix (the 4 pairs, 28 jobs): when the push touches src/**, pyproject.toml, uv.lock,
  calibration/** or .github/workflows/**; once a night (schedule); on tags; and by
  workflow_dispatch;
- intermediate pushes that exist only to prove pre-registration order (for example the seed before
  the draw) carry "[skip ci]" in the commit message; the round's final push runs CI. The rule is
  written in CLAUDE.md ("Working mode (v0.3)", item 1).
The maintainer's question for this round: does the change break any recorded guarantee (for
example docs/validation/v0.3/wp0-acceptance.md sections 3.4 and 3.5, reproduction on both systems
and both versions, the locks, or the shard tests)? If a recorded rule requires the full matrix (or
anything else this change removes), say which rule and where, and what it requires.

## The change (uncommitted, in the working tree)

- `.github/workflows/ci.yml`: a `plan` job (python3 `scripts/ci_plan.py`, standard library only)
  outputs the (OS, Python) pairs; the `test` job's matrix is `pair: fromJSON(...)` times the
  literal shard list, and is skipped when the pairs are empty. New triggers: `create` (a tag runs
  the full matrix; a branch runs only the plan job), `schedule` (nightly, full), `workflow_dispatch`
  (full). The concurrency group now includes the event name.
- `scripts/ci_plan.py` and `tests/test_ci_plan.py`: the levels and their tests.
- `CLAUDE.md`, "Working mode (v0.3)", item 1: the written rule.

## One deliberate deviation from the decision's wording, for you to judge

The decision says intermediate order-proof pushes carry "[skip ci]". GitHub's documentation
(https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs, read
2026-11-24) says such a push triggers no push/pull_request workflow run at all. But the
repository's pre-registration proofs read the created_at of the commit's push run of ci.yml:
`src/refute/selection/publication.py` (check_publication / fetch_push_runs) and
`src/refute/packs/tess/discover/pilot.py` (push_run_created_at, used by calib05/steps.py,
calib05/c3select.py and discover/steps.py, including the online re-check). So the change uses a
marker "[ci: order-proof]" instead: the run is created (the plan job only) and runs no tests,
only for a single-commit push to main outside the full matrix's paths. Likewise tags come through
`create`, not `push`, so a tag never adds a second event=push run for a commit
(push_run_created_at requires exactly one first-attempt push run, and check_publication refuses a
push run of another workflow).

## What to check, concretely

1. Any recorded guarantee, protocol, acceptance document, lock procedure or test that requires
   every commit (or every lock commit, every release, every pre-registration step) to be tested on
   all four (OS, Python) pairs. Search docs/, calibration/, ROADMAP.md, CLAUDE.md, tests/.
2. Whether the order-proof marker design preserves the proofs above, and whether "[skip ci]" as
   worded would have broken them. Any other code or record that reads CI runs (event, path,
   conclusion, jobs, run_attempt, total_count), including how a skipped test job or a
   `create`/`schedule` run could change what those readers see.
3. Whether the plan logic can wrongly give the fast matrix when a full-matrix path changed (for
   example pushes skipped by paths-ignore or by a marker before the final push, multi-commit
   pushes, merge commits, force pushes, PRs from forks), and whether the nightly full run is a
   sufficient backstop under the recorded rules.
4. The shard tests (tests/test_ci_shard.py) and any test that parses ci.yml.
5. Anything in the workflow change itself that is unsafe or wrong (expression injection through
   the commit message, outputs, fromJSON of an empty list, `create` events, concurrency).

Give a verdict (SURVIVED, WEAKENED or REFUTED), then numbered findings, each marked BLOCKING or
NON-BLOCKING, with the file and line and the exact fix. Cite file paths and line numbers for every
claim.
