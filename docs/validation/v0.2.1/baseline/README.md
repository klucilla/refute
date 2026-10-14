# v0.2.1 test baseline: the tests that pass at tag v0.2.0

`v0.2.0-passing-tests.txt` lists the 225 pytest node IDs that pass at tag `v0.2.0`
(commit `f4798230f1bca607bcc0e98fe47711a26ec4ee59`), one per line, in collection order,
with the case of every identifier kept. It defines "a synthetic test that passes at the
start of v0.2.1" (ROADMAP.md, v0.2.1, Exit criteria: "No synthetic test that passes at
the start of v0.2.1 fails at its end without a justification written before.").

| File | SHA-256 |
|---|---|
| `v0.2.0-passing-tests.txt` | `85af47aafc334052a539525c4bbb0dccaaefffe143c139038e2aafef4fe92c08` |
| `v0.2.0-junit.xml` | `d264659e9ae5ad80b31b74c9eeb843cdda92625d33f1645ac4b563cce2459461` |

## How it was produced (2026-10-11)

1. A git worktree of the tag, inside the project folder:
   `git worktree add --detach .worktrees/v0.2.0 f4798230f1bca607bcc0e98fe47711a26ec4ee59`,
   with its own environment from its lock file (`uv sync --frozen`; Refute 0.2.0,
   Python 3.13.5, Windows).
2. The full suite in that worktree, with the worktree's Python and the CPU affinity set
   to logical processors 8-31:
   `.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider -rfE --junitxml=<file>`.
   Result from the JUnit XML: 225 tests, 225 passed, 0 failures, 0 errors, 0 skipped,
   89.2 s (`v0.2.0-junit.xml`).
3. The node IDs from the collection of the same worktree:
   `.venv/Scripts/python.exe -m pytest --collect-only -q -o addopts="--disable-socket" -p no:cacheprovider`
   (225 collected), each matched to its JUnit test case by file and name; every one
   passed, so the list has 225 lines.

`v0.2.0-junit.xml` is the JUnit file of step 2 with one change: the `hostname` attribute
of the test suite is replaced by `<host>`. It contains no user path. The SHA-256 of the
unredacted file was
`9e4d1aeca6d46a6d135408c5ea541c88bc369aa866024c00326992ddab74068b`.

On the branch at commit `a3f66c4` (2026-10-11), all 225 node IDs exist and pass (full
suite: 505 tests, 489 passed, 16 xfailed, 0 failures).
