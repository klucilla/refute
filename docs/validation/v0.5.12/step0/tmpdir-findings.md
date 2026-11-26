# v0.5.12 step 0: the temporary-folder fixture failed on part (ii) (2026-11-26)

The maintainer's decision of #218 comment 7190662570, item 2: "if the fixture fails: STOP (option
(b), with a charter amendment, goes back to being the maintainer's decision)". The repetition of
`golden-local before`, the "before" claim hashes, M1's input identity and M1 have not run.

## What ran (journal `log.jsonl`)

| Unit | Status | What it showed |
|---|---|---|
| `inspect` sddl-from-dll | failed | A malformed regular expression in the diagnostic script itself; it read nothing. |
| `inspect` sddl-from-dll-2 | ok | The list that `os.mkdir(0o700)` applies, read from the container's `python313.dll` (SHA-256 `147c7d4d…`): `D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FA;;;OW)`. |
| `sitecustomize-install` | ok | The sitecustomize was copied into the cvenv only, with its SHA-256 checked before and after (record in the run folder). |
| `tmpdir-fixture` (the one approved run) | **failed** | (i) held; (iii) held; **(ii) failed**. |
| `inspect` pytest-parent-diag | ok | A diagnostic, exploratory and post hoc: pytest's full trace. |

**Part (i):** `tempfile.mkdtemp`, then a write, a read, a child process's write and the removal.
All held, inside the container.

**Part (iii):** the folder's list was exactly
`D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FA;;;OW)(A;OICI;FA;;;<the container's SID>)`. It is
protected, with no extra entry and none missing.

**Part (ii):** the minimal pytest case did not run. pytest stopped during collection with one
error (JUnit: 1 test, 0 failures, **1 error**, 0 skipped): `PermissionError: [WinError 5]` on
`C:/Projetos`.

## The cause (from the diagnostic's trace)

- During collection, pytest's `PytestPluginManager._getconftestmodules(path)` is called for every
  folder above the test file. It first calls `_get_directory(path)`, which calls
  `path.is_file()`, so a `stat` runs on each folder above the project too, before any
  `confcutdir` limit applies.
- `C:/Projetos`, the folder that holds the project, grants nothing to the container's SID. So the
  `stat` is denied, and the collection fails.
- The temporary folders are not the cause: part (i) and part (iii) held.
- The same applies to **any** pytest run in the container, the project's test suite included,
  because the test files' ancestors include `C:/Projetos`.

## What a fix needs (not done; the maintainer's decision)

- **(b) Run the pytest units outside the AppContainer,** in a job with `UV_OFFLINE=1` and
  pytest's `--disable-socket`. This is option (b) of the decision, and it needs a dated charter
  amendment. The other units can stay in the container: the "golden", claim hashes and M1 run no
  pytest.
- **(c) Grant the container's SID only the right to read attributes** on `C:/Projetos`, not to
  list it or read its files.
  - This changes an ACL outside the project, so it is the maintainer's alone.
  - It may also be needed on `C:/`, if that folder's list does not admit application packages.

In either case, the fixture's part (ii) is repeated, and then `golden-local before`. Since
`golden-local` runs no pytest, it might pass with the sitecustomize alone. Running it now would
be a repetition beyond the approval, so it has not run.
