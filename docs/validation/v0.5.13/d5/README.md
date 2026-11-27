# D5: the TestPyPI run (the maintainer's decision of 2026-11-26 (2), #218 comment 7207651312)

**Before it:**
- D4's commit `124bdd92a2be870ca16d53e280a1d84ac07986f9` was pushed.
- `scripts/ci_evidence.py 124bdd92… --level full` held: run 45925553671 (push), 28 jobs, all
  success.

**The one approved run:**
- It was dispatched through the meter, with `gh workflow run release.yml --repo klucilla/refute
  --ref main -f target=testpypi` (unit `gh2`).
- **The run:** https://github.com/klucilla/refute/actions/runs/45932597261 (`workflow_dispatch`,
  `head_sha` = `124bdd92`).
- **The outcome: `startup_failure`.** No job started, nothing was built or published, and no
  deployment was requested of the `testpypi` environment.

**The probable cause.** The repository's Actions policy was read with `gh api`, read only, with
a `--jq` filter. It permits only selected actions:

| Policy field | Value |
|---|---|
| `allowed_actions` | `selected` |
| `sha_pinning_required` | `true` |
| `github_owned_allowed` | `true` |
| `verified_allowed` | `false` |
| `patterns_allowed` | `["astral-sh/setup-uv@*"]` |

`pypa/gh-action-pypi-publish` is neither owned by GitHub nor in the allowed patterns, so a
workflow that uses it cannot start. The policy also requires SHA pins, and the workflow pins
every action by commit SHA.

**What the agent did not do:** change the policy, any environment or any protection rule. These
are the maintainer's alone. Nothing was re-run: the one approved run was used.

**Not done, since nothing was published:**
- the download from TestPyPI (`tools/testpypi_fetch.py`, unit `testpypi-fetch`);
- the SHA-256 comparison with the build job's listing.
