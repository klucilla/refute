# v0.5.12 step 0: the "before" golden record failed in the container (2026-11-26)

After step 0's demonstration was established (`step0/demo-check3.json`, all five checks), the
"before" proofs began (the maintainer's decision of #218 comment 7190454518, item 3). The first
one, `golden-local before`, failed. The work stopped there: `claim-hashes before`, M1's input
identity and M1 have not run.

## What ran (journal `log.jsonl`)

| Unit | Launcher | Status |
|---|---|---|
| `golden-local` (label `before`) | launch_v2, in the AppContainer, with the cvenv | **failed** (exit 1), after 2.25 CPU-s; no record |

## The cause (from the run's stderr)

- `tests/baseline_code_v0511.py` (`outputs()`) creates a temporary folder with
  `tempfile.TemporaryDirectory()`. It then starts a fresh subprocess that writes the outputs into
  that folder.
- The folder was created under the container's `AC/Temp`, where `launch_v2.py` points `TEMP`.
  - The subprocess's `mkdir` inside it was denied (`PermissionError`, WinError 5).
  - The cleanup of the folder was denied too, by the process that had created it.
- **The agent's reading, not confirmed against Python's documentation (no download in this
  phase):**
  - `tempfile.mkdtemp` creates its folder with mode `0o700`.
  - On Windows, the Python 3.13 in use turns that mode into an access-control list limited to the
    current user, administrators and SYSTEM.
  - An AppContainer process needs its container's SID (or "all application packages") in the
    list as well. A folder made that way is closed to the container itself.
- **The source, added on 2026-11-26** (errata entry 2), as the maintainer gave it in #218 comment
  7190662570, item 1:
  - since Python 3.12.4, `os.mkdir(mode=0o700)` on Windows applies a restricted permission, and
    `tempfile.mkdtemp` uses it;
  - this is the mitigation of CVE-2024-4030;
  - https://mail-archive.com/python-checkins@python.org/msg03194.html, read on 2026-11-26.
- **The exact list this interpreter applies,** read from the container's copy of `python313.dll`
  (SHA-256 `147c7d4d…`) by the read-only `inspect` unit labelled `sddl-from-dll-2`:
  `D:P(A;OICI;FA;;;SY)(A;OICI;FA;;;BA)(A;OICI;FA;;;OW)`. That is SYSTEM, the administrators and
  the owner, in a protected list. An earlier attempt, labelled `sddl-from-dll`, failed on a
  malformed regular expression in the diagnostic script and read nothing.
- **It is not a defect of `golden_local.py`, nor of the data,** so the maintainer's advance
  approval for checker defects (comment 7190454518, item 2) does not apply. The same cause would
  affect every unit in the container that uses a temporary folder: the test suite's `tmp_path`,
  `baseline_code_v0511`'s differential, and any probe that does.

## What a fix needs (not done; the maintainer's decision)

Two options, each a new file and an approved step:
- **(a) A container-only adjustment.**
  - A `sitecustomize.py` in `.cache/v0512/cvenv/Lib/site-packages`, a local file of the cvenv
    and never in `src/`.
  - When a folder is created with mode `0o700` inside the container, it adds an inherited
    full-control entry for the container's SID to that folder's ACL.
  - It changes nothing outside the container's interpreter, and its effect is shown by a new
    fixture (a `tempfile.TemporaryDirectory` used by a subprocess, then removed).
- **(b) Run the units that need temporary folders outside the AppContainer.**
  - They would run in a job with `UV_OFFLINE=1` and pytest's `--disable-socket`.
  - This gives up the charter's "offline across the process tree" for them, so it needs a dated
    charter amendment.

Then `golden-local before` again (a repetition), and the rest of the "before" proofs and M1.
