# Consensus record: the two-level CI (2026-11-24)

**The decision.** The maintainer's decision of 2026-11-24, received at 11:09 local (#218,
comment 7133936093), item 2, asked for:
- a fast matrix on every push to main and every PR;
- the full matrix on changes to `src/**`, `pyproject.toml`, `uv.lock`, `calibration/**` or
  `.github/workflows/**`, nightly, on tags and by `workflow_dispatch`;
- "[skip ci]" on intermediate pushes that only prove pre-registration order.

Before the commit, one Codex round in a new thread asked whether the change breaks a recorded
guarantee. Blocking items are applied, and the maintainer is told if a recorded rule requires the
full matrix.

## The round

| File | SHA-256 |
|---|---|
| [round-1-prompt.md](round-1-prompt.md) | `03b754b63e0380823fa084ee722f67fddeb146cf60530f74b671456404386dbf` |
| [round-1-answer.md](round-1-answer.md) | `747023ad2974a4297633224cbf6e629531980b835a4f914f94b971c7168d4eab` |

- **Codex:** Codex CLI 0.167.0-alpha.3.2, model gpt-6.2-sol, effort high, a new thread
  (`01a20dea-c0c2-74d3-b8a4-067b0cff04b2`).
  - It ran read-only through `.cache/v04/tools/codex_affinity.ps1` (processors 8 to 31).
  - The answer is stored unchanged, its SHA-256 checked against the original.
- **Its tokens, the real sum of its events:** 1,847,735 input (1,713,280 cached) and 13,098
  output, so **147,553** review tokens.
- **A first launch failed before Codex's output was recorded:** the folder for its events did
  not exist. Whether it used tokens is not known; it is not counted above.
- **Verdict: `WEAKENED`**, with 4 blocking items and 3 non-blocking. One round only, the
  default; the fixes below were not reviewed by Codex.

## The blocking items, applied

1. **A recorded rule requires the recorded-value tests on all four pairs.** The sources are
   `docs/validation/v0.3/wp3-acceptance.md`, line 393, and `tests/test_ml_schema.py`,
   `tests/test_ml_papers.py`.
   - So, as the decision asks, the rule is kept: when the fast matrix runs, a `recorded-values`
     job runs those tests on the two other pairs (ubuntu-24.04 with 3.13.16, windows-2025 with
     3.12.15).
   - The other four-pair gates (WP0 dependency changes; the WP2 to WP5 and lock-compatibility
     acceptances) apply to the change being accepted. A dependency change touches
     `pyproject.toml` or `uv.lock`, so it gets the full matrix.
   - Any gate that names four green jobs requires `scripts/ci_evidence.py --level full` on the
     exact commit (CLAUDE.md).
   - **For the maintainer:** no recorded rule requires the whole suite on four pairs for every
     commit. This one rule required part of it, and it is kept.
2. **`paths-ignore` could prevent the planner from running.** Both trigger-level filters are
   removed: every push and PR starts a run, and `scripts/ci_plan.py` is the only path
   classifier. A documentation-only change runs no test job, but its run exists.
3. **The diff could choose the wrong level.**
   - A push that is not a fast-forward gets the full matrix.
   - The touched paths are the union of the net diff and every commit's paths
     (`git log --name-only -m`). So an edit reverted within a batch, and a merged branch, still
     count.
   - Paths are read NUL-separated (`-z`, `--no-renames`), so a non-ASCII name cannot hide a
     prefix.
   - Real git tests cover a rollback, a change and its revert, a merge, a non-ASCII path,
     documentation, order-proof pushes and a pull request against its merge base
     (`tests/test_ci_plan.py`).
4. **A green run could pass for test evidence.** A new script, `scripts/ci_evidence.py`, accepts
   evidence only when a completed `ci.yml` run on the exact SHA has every expected test job
   with conclusion `success`:
   - 28 jobs for `full`;
   - 14 jobs plus the 2 recorded-value jobs for `fast`.

   The CLAUDE.md rule makes it the evidence for any gate that requires green CI before a lock, a
   tag or a release.
   - The stored release procedure of 2026-11-19 (`docs/plans/publication-2026-11-19.md`) and its
     waiter in `.cache` are records and are not edited. The rule applies from now on.

## The non-blocking items

- **5. The custom marker is the right deviation from "[skip ci]".** "[skip ci]" would have
  removed the push run that both proof readers need. The marker is tightened as suggested:
  - an exact trailer line, `CI: order-proof`;
  - one non-merge, fast-forward commit;
  - no code path (`src/`, `scripts/`, `tests/`, `calibration/`, `.github/`, `pyproject.toml`,
    `uv.lock`, `.python-version`, `.gitattributes`, any `.py`).

  A regression test of the proof readers with a plan-only push is left for #59.
- **6. `scripts/ci_ids_check.py` should check the expected matrix.** It is not changed here;
  this is recorded on #59.
- **7. Workflow details:**
  - applied: the concurrency group of tag, nightly and manual runs is the run id, and is never
    cancelled;
  - applied: the test jobs check their pair against an allowlist kept in the workflow;
  - written in CLAUDE.md: tags are created one at a time, because GitHub creates no `create`
    event for more than three tags at once.

## Where the decision's wording was not followed, and why

- **Intermediate order-proof pushes do not use "[skip ci]".** GitHub creates no workflow run
  for such a push (https://docs.github.com/en/actions/how-tos/manage-workflow-runs/skip-workflow-runs,
  read 2026-11-24). The recorded order proofs need that run's `created_at`:
  - `src/refute/selection/publication.py`;
  - `push_run_created_at` in `src/refute/packs/tess/discover/pilot.py`, used by the calib05 and
    discover steps.

  The trailer `CI: order-proof` keeps the run and skips the tests. Codex agreed (item 5).
- **Tags start CI through `create`, not `push`.** A tag push would add a second event=push run
  for the tagged commit. `push_run_created_at` requires exactly one, and `check_publication`
  refuses a push run of another workflow.
- **Documentation-only changes run no test job,** as before; their run now exists.
