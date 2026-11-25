# v0.5.12 step 0: demo-check2 failed on a defect of its own (2026-11-25)

The maintainer's decisions of #218 comments 7174740316 (item 2) and 7176253382 (item 3): the
approved repetitions run once each, in order, and "if any repetition fails, STOP again". The
last of them, `demo-check2`, failed. The work stopped there: the "before" proofs and M1 have not
run.

## What ran, in order (journal `log.jsonl`)

| Unit | Launcher | Status | Record |
|---|---|---|---|
| `pth_copy.py` (v0.5.11's bootstrap unit, outside the container) | launch_v9 | ok | `step0/pth-copy.json`: the editable `.pth` was copied; SHA-256 `17fe44c3…` before and after. |
| `cvenv-check` (the one approved repetition) | launch_v2 | ok | `step0/cvenv-check.json`: `refute` resolves from `src/refute/__init__.py`. The pre-approved `src` grant was not used. |
| `demo` transient (repetition) | launch_v2 | ok | 52,428,857 bytes written by the job, for the 50 MiB written and deleted. |
| `demo-net2` (the new network fixture) | launch_v2 | ok | All 8 counted attempts failed, and the launcher's listener outside the container accepted 0 connections. Same-container loopback was recorded as information. |
| `commit-check` in the container (repetition) | launch_v2 | ok | Commit `2f2cdbc`. |
| `demo-check2` | launch_v2 | **failed** (exit 1) | No record. |

## The cause: a defect of `demo_check2.py`

Its helper `runs()` parses the last line of every unit's stdout as JSON. The `commit-check`
unit's stdout is git's and `commit_checked.py`'s plain text (`[main 2f2cdbc] ...`), so
`json.loads` raised `JSONDecodeError`. The script stopped before it wrote any check. It reached
the commit check last, after the other four, but it records nothing until all five are done, so
the other four have no result either.

This is a defect of the checker, not a failure of a meter fixture. Still, `demo-check2` is the
deterministic test that decides the demonstration, and it gave no `passed`. **The demonstration
is therefore not established.** The journal facts in the table above are not a substitute for
the checker's verdict.

## What a fix needs (not done; the maintainer's decision)

- **A new checker**, `demo_check3.py` (rule (c): `demo_check2.py` is not edited). It would read
  the JSON summary only for the units that print one (`demo`, `demo-net2`). For `commit-check` it
  would use the journal's `after` entry alone. Its five checks would be the same as
  `demo_check2.py`'s, on the same records.
- **Its one run,** approved in #218 (it reads the same records again, so in doubt it is a
  repetition).
