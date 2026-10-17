# WP0 acceptance: dependency planning for v0.3

Work package WP0 of [docs/plans/v0.3-plan.md](../../plans/v0.3-plan.md) (section 11;
items recorded in section 10.5). Issue #43. Written on 2026-10-14, before any change
to `pyproject.toml`, `uv.lock` or the Python version used by Refute.

This document is committed **before** any dependency change. It changes nothing in
`src/`, `pyproject.toml` or `uv.lock`. Dependency changes come before any v0.3 lock:
`pyproject.toml` and `uv.lock` are part of the code hash (`docs/lock-format.md`), so
a change after a lock makes that lock `TAMPERED`.

## 1. What the package must do

1. Decide every new Python dependency that v0.3 needs before its first lock, each
   with a version uploaded at least 7 days before it is resolved (CLAUDE.md;
   `exclude-newer = "7 days"` in `pyproject.toml`, `exclude-newer-span = "P7D"` in
   `uv.lock`).
2. Fix the exact Python versions (major.minor.patch) used by Refute locally and in
   CI, and how they are pinned.
3. Evaluate uv's `python-preference = "only-managed"` (section 3) and record the
   maintainer's decision (section 3.4).
4. Keep the CI runner image pinned and recorded (`ubuntu-24.04`, `windows-2025`;
   PR #37), with the migration to `ubuntu-26.04` as a separate commit with its own
   green run.
5. Record the Docker Engine version inside the VM in every dossier; the 7-day
   cooldown applies to it by hand (plan section 10.5; the VM is built in WP6).

## 2. Dependency plan (candidates, no change yet)

Versions checked on PyPI on 2026-10-14 (JSON API, first upload time of each
version), against the 7-day cooldown on that date. The check used a working script
(`pypi_cooldown.py`, kept outside the repository with the evaluation records). **Its
limitation:** it uses the first upload time of each version, not the upload time of
each file. The final check of the cooldown has to look at the upload time of every
artifact actually used: the files listed with their hashes in `uv.lock`, the uv
Python builds and the uv binary. The script is not a permanent verifier.

| Package | Needed by | Newest | Eligible on 2026-10-14 | Status |
|---|---|---|---|---|
| `pyarrow` | WP5: read the Parquet frame (D-18), `calibration` group | 26.0.0 (2026-10-09) | 25.0.1 (2026-08-10) | Decided (D-18). An eligible earlier version, such as 25.0.1, can be used now. 2026-10-16 matters only if 26.0.0 is chosen: its first file was uploaded on 2026-10-09T08:13Z, and each of its files reaches 7 days at its own upload time plus 7 days. The version is the one `uv lock` resolves under `exclude-newer` on the day of the change. |
| `scikit-learn` | WP3: a candidate independent implementation for `metric_recompute` (plan section 6.3, line 486: "recompute the metric with an independent implementation"; the plan names no library) | 1.9.1 (2026-09-10) | 1.9.1 | **Decided:** two independent implementations, Refute's own (numpy) the primary and scikit-learn 1.9.1 the second ([wp3-acceptance.md](wp3-acceptance.md), section 1.7, approved with #77 on 2026-10-15). Already in `uv.lock` as a transitive dependency of `lightkurve` 2.6.0 (`uv.lock`, the `lightkurve` entry), at 1.9.1. The alternative is metric code written in Refute (numpy). |

No other new runtime dependency is planned. The Docker CLI is called as a
subprocess (no SDK). arXiv, GitHub and Hugging Face are queried over HTTP with the
standard library or `gh`. Third-party paper code installs its own dependencies inside
its containers, never in Refute's environment.

**Acceptance of a dependency change** (a later commit, after this document):
- `uv lock` runs with the existing `exclude-newer`;
- the diff of `uv.lock` is reviewed, since a change of cutoff can bring other
  updates;
- CI is green on the four jobs, and the "Record environment" step lists the new
  package with the same version on both systems.

## 3. Evaluation of `python-preference = "only-managed"`

### 3.1 Method

- Each check starts from a **new environment created from scratch**: a fresh clone
  of the repository with no `.venv`, and an empty uv Python install directory of its
  own.
- The **effective interpreter is recorded**: the exact version (`sys.version`) and
  its origin (`sys.base_prefix`, compared with the uv Python install directory, and
  `uv python list --only-installed`).
- **Both systems:**
  - Windows locally: the maintainer's machine, with the process and its children on
    CPU threads 8 to 31 (mask `FFFFFF00`);
  - Ubuntu (`ubuntu-24.04`) and Windows (`windows-2025`) in CI: a temporary
    information-only step, "Evaluate uv only-managed interpreter", added to
    `.github/workflows/ci.yml` in commit `1087b3b` and removed after its run
    (section 3.2).
- Locally, each check runs once with the default preference and once with
  `only-managed`; in CI, only with `only-managed` (the default is the CI's normal
  install, recorded by the "Record environment" step).

### 3.2 Local result (Windows, 2026-10-14T20:35:20Z)

uv 0.12.1, repository at `4a1d7c7`, `.python-version` = `3.13`, affinity mask
`0xFFFFFF00`.

| Mode | Interpreter | Origin |
|---|---|---|
| default (`UV_PYTHON_PREFERENCE` unset) | CPython 3.13.5 (MSC v.1943) | not uv-managed: the system install under `C:\Users\<user>\AppData\Local\Programs\Python\Python313` |
| `only-managed` | CPython 3.13.14 (MSC v.1944) | uv-managed, downloaded into the empty install directory of the check |

For comparison, the CI run of 2026-10-14 on PR #37 (uv 0.13.1, default preference)
used 3.12.3 and 3.13.16 on `ubuntu-24.04`, and 3.12.10 and 3.13.15 on
`windows-2025`.

### 3.2.1 CI result of the temporary step (commit `1087b3b`)

Run: https://github.com/klucilla/refute/actions/runs/38633597971 (PR #57, all four
jobs `success`). The step had `continue-on-error: true`, so a failure of the step does
not show in the job status: the outcome below comes from each job's log. Lines are
transcribed from the logs (timestamps in UTC).

| Job id | Job | Step outcome | Interpreter with `only-managed` | Origin |
|---|---|---|---|---|
| 116091070882 | ubuntu-24.04 / Python 3.12 | ran, completed | CPython 3.12.15 | uv-managed |
| 116091070768 | ubuntu-24.04 / Python 3.13 | ran, completed | CPython 3.13.16 | uv-managed |
| 116091071034 | windows-2025 / Python 3.12 | **ran, failed** before `uv sync` | none (no data) | — |
| 116091071083 | windows-2025 / Python 3.13 | **ran, failed** before `uv sync` | none (no data) | — |

Log lines, job 116091070882 (ubuntu-24.04 / Python 3.12):

```
2026-10-14T20:37:25.2906122Z uv 0.13.1 (x86_64-unknown-linux-gnu)
2026-10-14T20:37:27.0818054Z python=3.12.15 (main, Oct 14 2026, 01:05:27) [Clang 23.1.3 ]
2026-10-14T20:37:27.0818906Z base_prefix=/home/runner/work/_temp/uv-python-only-managed/cpython-3.12.15-linux-x86_64-gnu
2026-10-14T20:37:27.0819562Z uv_managed=True
2026-10-14T20:37:27.1577130Z cpython-3.12.15-linux-x86_64-gnu    /home/runner/work/_temp/uv-python-only-managed/cpython-3.12-linux-x86_64-gnu/bin/python3.12
```

Log lines, job 116091070768 (ubuntu-24.04 / Python 3.13):

```
2026-10-14T20:37:26.7726091Z uv 0.13.1 (x86_64-unknown-linux-gnu)
2026-10-14T20:37:28.6780716Z python=3.13.16 (main, Oct 14 2026, 01:04:01) [Clang 23.1.3 ]
2026-10-14T20:37:28.6781281Z base_prefix=/home/runner/work/_temp/uv-python-only-managed/cpython-3.13.16-linux-x86_64-gnu
2026-10-14T20:37:28.6781741Z uv_managed=True
2026-10-14T20:37:28.7268119Z cpython-3.13.16-linux-x86_64-gnu    /home/runner/work/_temp/uv-python-only-managed/cpython-3.13-linux-x86_64-gnu/bin/python3.13
```

**Windows jobs: observed facts.** The command of the step that failed, as echoed in
both logs:

```
git archive HEAD | tar -x -C "$fresh"
```

with `fresh="$RUNNER_TEMP/fresh-only-managed"`.

Log lines, job 116091071034 (windows-2025 / Python 3.12):

```
2026-10-14T20:37:46.4074795Z tar: D\:\a\\_temp/fresh-only-managed: Cannot open: No such file or directory
2026-10-14T20:37:46.4075564Z tar: Error is not recoverable: exiting now
2026-10-14T20:37:46.4163507Z ##[error]Process completed with exit code 2.
```

Log lines, job 116091071083 (windows-2025 / Python 3.13):

```
2026-10-14T20:37:48.9279508Z tar: D\:\a\\_temp/fresh-only-managed: Cannot open: No such file or directory
2026-10-14T20:37:48.9281152Z tar: Error is not recoverable: exiting now
2026-10-14T20:37:48.9364091Z ##[error]Process completed with exit code 2.
```

The step stopped at `tar`, before any `uv` command, so it says nothing about uv on
Windows. The only Windows data is the local result of section 3.2, with a different
uv version (0.12.1).

**Hypothesis, not verified:** GNU tar may have read the drive letter (`D:`) of the
Windows form of `$RUNNER_TEMP` as a remote host name. This was not reproduced, so it is
not established as the cause.

On Ubuntu, `only-managed` gave uv-managed 3.12.15, while the normal CI install of the
same job used 3.12.3 (PR #37). The origin and the patch version both change with the
preference.

### 3.3 What the result shows

- **The origin of the interpreter changes with the preference.** On this machine,
  the default takes the system Python; `only-managed` takes a uv-managed build.
- **The patch version still moves.** With `only-managed` and `.python-version` =
  `3.13`, uv 0.12.1 chose 3.13.14. The CI, with uv 0.13.1, reported 3.13.15 and
  3.13.16. The managed patch version depends on the uv version and on what was
  already installed.
- **The uv version is not pinned:** 0.12.1 locally, 0.13.1 in CI.

**Choosing the origin of the interpreter does not replace fixing its exact version.**
`only-managed` alone would still let the patch version move with uv's managed builds.

### 3.4 Decision (approved by the maintainer on 2026-10-14)

To be implemented in a dependency PR of its own, not in this document's PR, in this
order:
1. pin the uv version, the same locally and in CI (the `version` input of
   `setup-uv`, and the local install);
2. pin the exact Python versions, major.minor.patch, in `.python-version` and in the
   CI matrix, choosing patches that exist as uv-managed builds for both systems;
3. then adopt `python-preference = "only-managed"` in `[tool.uv]`;
4. validate on Windows (locally, with CPU affinity on threads 8 to 31, and in CI) and
   on Ubuntu (CI): in a fresh environment, the recorded interpreter has the pinned
   exact version and is uv-managed.

**The 7-day cooldown counts from the upload time of the artifacts that are actually
installed, not from the date of the version:** the wheel or sdist files on PyPI, the
uv Python builds, and the uv binary.

**Concessions accepted:**
- managed interpreters come from uv's Python builds, a source outside PyPI;
- the first run on a new machine needs the network;
- the system Python on the maintainer's machine is no longer used by Refute.

**Choosing the origin does not replace fixing the exact version.** Step 2 is
required; step 3 alone still lets the patch version move.

### 3.5 Implementation plan of the decision (recorded on 2026-10-16, before the change)

Written in the interpreter PR, in a commit of its own before the commit that changes
`.python-version`, `pyproject.toml` and `.github/workflows/ci.yml`.

**State before the change.** CI run 38852395034 (2026-10-16, PR #110, default
preference, uv not pinned), from each job's "Install" and "Record environment" lines:

| Job | uv | Interpreter | Origin |
|---|---|---|---|
| ubuntu-24.04 / Python 3.12 | 0.13.1 | CPython 3.12.3 | system, `/usr/bin/python3.12` |
| ubuntu-24.04 / Python 3.13 | 0.13.1 | CPython 3.13.16 | uv-managed, downloaded in the job |
| windows-2025 / Python 3.12 | 0.13.1 | CPython 3.12.10 | runner tool cache, `C:\hostedtoolcache\windows\Python\3.12.10` |
| windows-2025 / Python 3.13 | 0.13.1 | CPython 3.13.16 | runner tool cache, `C:\hostedtoolcache\windows\Python\3.13.16` |

`setup-uv` logged "Could not determine uv version from uv.toml or pyproject.toml.
Falling back to latest." in every job: uv 0.13.1, released 2026-10-14T05:15:30Z, was
inside the 7-day cooldown on the day of the run.

**Chosen versions and their sources** (GitHub API, retrieved 2026-10-16):

- **uv 0.12.24.** The releases of `astral-sh/uv`: 0.13.1 (2026-10-14T05:15:30Z),
  0.13.0 (2026-10-09T19:49:55Z), 0.12.24 (2026-10-08T20:06:20Z). On 2026-10-16 the
  newest release at least 7 days old is 0.12.24. Its assets
  `uv-x86_64-pc-windows-msvc.zip` and `uv-x86_64-unknown-linux-gnu.tar.gz` were
  uploaded at 2026-10-08T20:06:17Z.
- **CPython 3.12.15 and 3.13.16.** The download metadata embedded in uv 0.12.24
  (`crates/uv-python-managed/download-metadata.json` at tag `0.12.24`) lists, as the
  newest builds for x86_64 Windows and Linux (glibc), `cpython-3.12.15` and
  `cpython-3.13.16`, both of the python-build-standalone release `20261003`
  (published 2026-10-03T14:56:28Z). Their `install_only_stripped` archives for
  `x86_64-pc-windows-msvc` and `x86_64-unknown-linux-gnu` were uploaded between
  2026-10-03T14:54:03Z and 2026-10-03T14:54:37Z. A uv version fixes the build it
  downloads for a given patch, from the catalog embedded in that version, so pinning
  uv also fixes the build **of a new download**. It does not fix the build of an
  installation of the same patch that already exists in the install directory, nor of
  one taken from a catalog or mirror replaced by configuration; the build is fixed only
  in a fresh install directory with uv's own catalog (as in CI, where the install
  directory of each job starts empty).

**The change** (the next commit of the PR):
1. `.github/workflows/ci.yml`: the `version: "0.12.24"` input of `setup-uv`; the
   matrix `python: ["3.12.15", "3.13.16"]`; the "Record environment" step adds
   `uv python find <matrix version>` and `uv python list --only-installed`; a new
   step, "Check interpreter", fails the job unless the interpreter of the environment
   is CPython, has exactly the matrix version and has its base installation under the
   uv Python install directory of the job (`scripts/check_interpreter.py`, with unit
   tests). This step is a permanent check, not an evaluation step (criterion 2 of
   section 4). It shows where the base installation is and which version it reports;
   it does not authenticate the build (any CPython of that version placed in the
   directory passes), which rests on the pinned uv and the fresh install directory.
2. `.python-version`: `3.13.16`.
3. `pyproject.toml`, `[tool.uv]`: `python-preference = "only-managed"`.

`uv.lock` does not change (the preference and the interpreter do not enter the
resolution). The local install of uv 0.12.24 and the local validation of step 4 of
section 3.4 (Windows, CPU threads 8 to 31, a fresh environment) are done by the
maintainer before the merge; until then the criterion 4 below is not met.

### 3.6 Local environment: uv's Pythons outside AppData (recorded on 2026-10-16)

A record of the local environment, not a criterion.

**The local failures and their probable cause.**
- **What was observed:** on this machine, `uv python install` run from a session of the
  Claude desktop app failed with "Missing expected target directory for Python minor
  version link", for 3.12.13 on 2026-10-07 and for 3.13.16 on 2026-10-16. The files of
  3.13.16 written from that session were found in the app's private per-package folder
  (`AppData\Local\Packages\<the app's package>\LocalCache\Roaming\uv\python`), not in
  the real `AppData\Roaming\uv\python`, which is uv's default install directory.
- **What the source says:** the Claude desktop app is installed as an MSIX package. For
  packaged apps that are virtualized, on Windows 10 version 1903 and later, "All newly
  created files and folders in the user's `AppData` folder [...] are written to a
  private per-user, per-app location; but merged at runtime to appear in the real
  `AppData` location"; the page states that this section "applies only to virtualized
  apps"
  (https://learn.microsoft.com/en-us/windows/msix/desktop/desktop-to-uwp-behind-the-scenes#appdata-operations-on-windows-10-version-1903-and-later,
  accessed 2026-10-16).
- **The hypothesis, not verified:** the new interpreter folder was redirected to the
  private location, while uv's minor-version link needed it in the real AppData, so the
  link step failed. Where the link pointed, and whether an interpreter installed that
  way would work from a terminal outside the app, were not checked.
- **What is confirmed:** with uv's Pythons installed outside AppData (the rule below),
  the install, the virtual environment and the full suite work (the result below).

**The rule.**
- **uv's Pythons stay outside AppData.** The user environment variable
  `UV_PYTHON_INSTALL_DIR` is `C:\uv\python`.
- **A new environment variable applies only to processes started after it is set.** The
  Windows Terminal keeps the environment it started with, so every Terminal window must
  be closed before a new one sees the variable.
  - The first installation of 2026-10-16, from a Terminal opened before the variable,
    still went to AppData.
  - The Claude desktop app also has to be restarted.

**The result.** The maintainer, from a normal terminal opened after the variable was
set, ran `uv python install 3.13.16`, `uv venv --clear --python 3.13.16` and
`uv sync --frozen` in the main folder.

Checked on 2026-10-16 from a session of the app restarted after that, in the main
folder:
- `UV_PYTHON_INSTALL_DIR` is `C:\uv\python`;
- `.venv\Scripts\python.exe -VV` gives CPython 3.13.16;
- `sys.base_prefix` is `C:\uv\python\cpython-3.13.16-windows-x86_64-none`;
- `scripts/check_interpreter.py 3.13.16` is OK;
- the full suite on `main` at `f942692`, through `scripts/run_tests_affinity.ps1`:
  JUnit tests=1901 failures=0 errors=0 skipped=51.

The copies of 3.13.16 left under AppData, both the app's private copy and the real one,
are outside the project and are the maintainer's decision.

## 4. Acceptance criteria

1. This document is on main before any change to `pyproject.toml`, `uv.lock`,
   `.python-version` or the Python versions of the CI matrix.
2. The evaluation of section 3 is recorded with its sources: the local result, and
   the CI run with its job ids and transcribed log lines (section 3.2.1), including
   the Windows jobs whose step failed. The temporary CI step is removed after its run,
   so `.github/workflows/ci.yml` carries no evaluation step.
3. Every later dependency change of WP0 satisfies the acceptance of section 2, and the
   7-day cooldown counts from the upload time of every installed artifact (section
   3.4).
4. The interpreter change of section 3.4 is made in its own dependency PR and is
   accepted only when, in a fresh environment, the recorded interpreter has the
   pinned exact version and is uv-managed on Windows (local and CI) and on Ubuntu
   (CI).
5. The decision on `scikit-learn` (section 2) is recorded with the maintainer's answer
   before the first v0.3 lock.
6. The CI comment on `concurrency` describes the behavior with `paths-ignore` (issue
   #41).

No synthetic test cases apply to this package: it adds no code. Its regression check
is the existing CI suite, which must stay green.
