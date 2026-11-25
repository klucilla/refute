# v0.5.12 step 0: the meter's demonstration, three failures (2026-11-25)

The charter's step 0 runs the meter's demonstration before M1; "if one fails, the work stops
before M1" (charter, step 0; stop 7). Three of the fixtures failed: transient, commit and network.
The work stopped there: M1 has not run, and no fixture was repeated. *(Corrected in place on
2026-11-25: the title and this sentence said "two"; errata entry 1.)*

## The outcomes, from the journal (`log.jsonl`)

| Fixture (label) | Status | What it showed |
|---|---|---|
| cpu | ok | The job counted 5.0 CPU-s (2.0 in the process, 3.0 in its child); the launcher's whole tree counted 6.8 CPU-s. |
| transient | **failed** (exit 1) | The fixture could not open its file under `TEMP`. Nothing was written, so the disk bound was not exercised. |
| retain-a | ok | 30 MiB written and kept; bound 219,163,320 bytes. |
| retain-b | ok | Its `o_start` carried retain-a's 30 MiB; bound 250,623,576 bytes. |
| commit (the container's `commit-check`) | **failed** (exit 2) | `scripts/commit_checked.py` refused before any check: "run this script with the project's virtual environment (.venv)". Nothing was committed. |
| network | **failed** (exit 1) | Every external attempt failed, from the process and from its child: TCP to 1.1.1.1:443 was refused with WSAEACCES (10013), and DNS for pypi.org and github.com failed. A TCP connection on loopback **to a listener opened by the same contained process** succeeded, in the process and in the child. |

## The causes

- **transient: a defect of the launcher's environment** (`launch_v1.py`, `private_env`).
  - For a process in an AppContainer, Windows sets `TEMP` and `TMP` to
    `<local application-data folder>/Packages/<container>/AC/Temp`, where the folder is the one
    the environment names.
  - The launcher had pointed that variable to a fresh private folder, which has no such
    subfolder, so the path did not exist.
  - This is a defect of the launcher, not of the accounting.
- **network: a defect of the fixture's expectation** (`demo.py`, mode `network`).
  - An AppContainer with no capability may still connect on loopback to a socket of **the same
    container**; Windows' loopback isolation blocks connections to processes outside the
    container.
  - v0.5.10's isolation test put the listener **outside** the sandbox, in the driver
    (`docs/validation/v0.5.10/engines/isolation_test.py`). This fixture put it inside, and so
    expected a failure that the design does not give.
  - No traffic left the machine.

- **commit: a defect of the container's interpreter setup** (`container_setup.py`).
  - The container runs the base interpreter's copy (`.cache/v0512/cpy`), whose `sys.prefix`
    equals `sys.base_prefix`, so `commit_checked.py` refuses it.
  - A second defect was seen with it, before it could matter: the container's environment has no
    `USERNAME`. `commit_checked.py`'s privacy check builds one of its terms from the Windows user
    name, so in the container it would have checked without that term.
  - It refused before that check, and nothing was committed through it. The stop records were
    committed through v0.5.11's `commit-check` (the outer meter), after staging through the
    container's `stage` unit, which worked.

## What a fix needs (not done; the maintainer's decision)

- **A new launcher version.** `launch_v2.py`, never an edit of `launch_v1.py` (rule (c)), would
  create `Packages/refute.v0512.offline/AC/Temp` under the private local application-data folder
  before the start, and point `TEMP` and `TMP` there.
- **A corrected network fixture.** A new file would put the listener in the launcher's process,
  outside the container, and count connections accepted from the contained run (expected 0).
  Contained-to-contained loopback would be recorded as information, not as a failure.
- **A container virtual environment.** A new setup step would create `.cache/v0512/cvenv`, whose
  `pyvenv.cfg` points to the copy, with the `.pth` and `ruff.exe` there. The new launcher would
  run `{python}` from it and pass `USERNAME` into the container's environment.
- **Repetitions.** Each corrected fixture is a repetition of a demonstration unit with a recorded
  outcome, so it needs approval in #218 first (charter, section 4; rule (d)): the transient
  fixture, the network fixture and the container's commit, and then `demo-check` over the full
  set.
