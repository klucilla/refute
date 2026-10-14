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
3. Evaluate uv's `python-preference = "only-managed"` (section 3) and record a
   recommendation, adopted only by a decision of the maintainer.
4. Keep the CI runner image pinned and recorded (`ubuntu-24.04`, `windows-2025`;
   PR #37), with the migration to `ubuntu-26.04` as a separate commit with its own
   green run.
5. Record the Docker Engine version inside the VM in every dossier; the 7-day
   cooldown applies to it by hand (plan section 10.5; the VM is built in WP6).

## 2. Dependency plan (candidates, no change yet)

Versions checked on PyPI on 2026-10-14 (JSON API, first upload time of each
version), against the 7-day cooldown on that date:

| Package | Needed by | Newest | Eligible on 2026-10-14 | Status |
|---|---|---|---|---|
| `pyarrow` | WP5: read the Parquet frame (D-18), `calibration` group | 26.0.0 (2026-10-09) | 25.0.1 (2026-08-10) | Decided (D-18). 26.0.0 becomes eligible from 2026-10-16. The version is the one `uv lock` resolves under `exclude-newer` on the day of the change. |
| `scikit-learn` | WP3: an independent implementation for `metric_recompute` (plan section 6.3 names it as an example) | 1.9.1 (2026-09-10) | 1.9.1 | **Open, for the maintainer.** The alternative is metric code written in Refute (numpy). That avoids a large dependency, but it is less independent from Refute's own code. |

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
  - Ubuntu (`ubuntu-24.04`) and Windows (`windows-2025`) in CI: the step "Evaluate
    uv only-managed interpreter" of `.github/workflows/ci.yml`, information only.
- Each check runs once with the default preference and once with `only-managed`.

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

### 3.4 Recommendation (not adopted here)

Option recommended for the maintainer's decision, in this order:
1. pin the uv version, the same locally and in CI (the `version` input of
   `setup-uv`, and the local install), under the 7-day rule;
2. pin the exact Python versions (`.python-version` with major.minor.patch, and the
   CI matrix with the same patch versions), choosing patches that exist as
   uv-managed builds for both systems;
3. then adopt `python-preference = "only-managed"` in `[tool.uv]`, so that every
   system uses the same build source.

**Concessions:**
- managed interpreters are downloaded from uv's Python builds, a source outside
  PyPI; the 7-day rule has to be applied to them by hand;
- the first run on a new machine needs the network;
- the system Python on the maintainer's machine is no longer used by Refute.

Without step 2, step 3 still leaves the patch version moving.

The decision is not obvious, so nothing is adopted in this commit.

## 4. Acceptance criteria

1. This document is on main before any change to `pyproject.toml`, `uv.lock`,
   `.python-version` or the Python versions of the CI matrix.
2. The CI evaluation step prints, for each of the four jobs, the interpreter chosen
   with `only-managed` in a fresh clone: exact version, and whether it is uv-managed.
   Its output is recorded with the decision of section 3.4.
3. Every later dependency change of WP0 satisfies the acceptance of section 2.
4. The decisions of sections 2 (`scikit-learn`) and 3.4 are recorded with the
   maintainer's answer before the first v0.3 lock.
5. The CI comment on `concurrency` describes the behavior with `paths-ignore` (issue
   #41).

No synthetic test cases apply to this package: it adds no code. Its regression check
is the existing CI suite, which must stay green.
