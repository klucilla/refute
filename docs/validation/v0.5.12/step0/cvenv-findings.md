# v0.5.12 step 0: the container's virtual environment did not resolve `refute` (2026-11-25)

The maintainer's decision recorded at 19:15 local (#218, comment 7174740316), item 1 c: "if it
cannot be built from local copies only, STOP." The step was built from local copies, but its own
check failed, so the work stopped there. None of the approved repetitions has run (transient,
network, commit), and neither has `demo-check2`.

## What ran (journal `log.jsonl`)

| Unit | Launcher | Status | What it showed |
|---|---|---|---|
| `setup-cvenv` | launch_v1 | **failed** (exit 1) | The three copies matched their sources by SHA-256, and the new interpreter has `sys.prefix` different from `sys.base_prefix`. `numpy` and `ruff` resolve; **`refute` does not**. The launcher copies a unit's outputs only on success, so its record stayed in the run's out folder; it is reproduced in `cvenv-failed-record.json` beside this file. |
| `inspect` (label cvenv-diag) | launch_v2 | ok | Diagnostic, exploratory and post hoc. `.venv/Lib/site-packages` is on `sys.path`, but `C:/Projetos/refute/src` is not. The `.venv`'s `.pth` files are not hidden. |
| `inspect` (label cvenv-diag2) | launch_v2 | failed (exit 1) | Diagnostic. Opening `.venv/Lib/site-packages/_editable_impl_refute.pth` from the container raised **PermissionError** (errno 13). |

The diagnostics' scripts are under `.cache/v0512/diag/`. They read only, and they give quantities
that no record held (`sys.path`, file attributes, the open's error).

## The cause

The container can list `.venv/Lib/site-packages` and read the packages in it, but it cannot open
the editable install's `.pth` file. That file evidently does not carry the read grant that
`container_setup.py` gave the project folder by inheritance. When Python's `site` module cannot
open a `.pth` file, it skips it silently. So the line that puts `src` on the path is never read,
and `refute` does not import.

## What a fix needs (not done; the maintainer's decision)

Either of these, as a new file and an approved step:
- **(a)** copy `_editable_impl_refute.pth`, one line naming the project's `src`, from `.venv` into
  `.cache/v0512/cvenv/Lib/site-packages`, from outside the container, checked by SHA-256.
  - This is a local copy, in the literal sense of item 1 c.
  - The copy inherits the grant of `.cache/v0512`.
- **(b)** grant the container's SID read on that one file, which is inside the project.

Then `setup-cvenv`'s check, which is a repetition, and the approved repetitions in their order.
