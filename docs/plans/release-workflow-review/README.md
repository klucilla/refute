# The sdist configuration, PyPI metadata and release workflow: prepared, not committed

This record follows the maintainer's decisions of 2026-11-26, items M4 and M5 (#218, comment
7204660147). **Nothing here is applied.**
- `pyproject.toml` is unchanged.
- There is no `.github/workflows/release.yml`.
- Nothing was published, and no token was handled.

The two prepared files stay out of git until the maintainer approves them by their SHA-256:

| File (local, under `.cache/v0513prep/m45/`) | SHA-256 |
|---|---|
| `pyproject.diff`: the exact diff, M4 and M5b together | `70b4aeaba5019b399cfe282e68366409fc951a316abfa193eb393e47f4d2ff6e` |
| `pyproject.patched.toml`: the result | `bf27f1881be3922c05bc5d8bf7b143ad802fa2c8bfe6ad0346f318a821cffb08` |
| `release.yml`: the workflow, with Codex's fix applied | `b48adbef34360ec58cd0b3ecf9424b3c64ddaded320657602b2bb5c072d0f448` |

## M4: the sdist

The builds were run on `d898722`, the main after PR klucilla/refute#229. Each was an offline
`uv build` of a `git archive` copy, by [m45_build.py.txt](m45_build.py.txt). That file is a byte
copy of the script that ran, stored as text so that its bytes stay as they ran. Their record is
[m45-builds.json](m45-builds.json).

| Build | Wheel | Sdist |
|---|---|---|
| 1. As committed | 619,402 bytes | 69,377,188 bytes (the whole repository) |
| 2. + the sdist include list (M4) | 619,402 bytes, **byte-identical** to build 1 | **1,343,771 bytes** (379 files, 5,338,134 uncompressed) |
| 3. + the metadata (M5b) | 619,498 bytes; only `METADATA` and `RECORD` of the dist-info differ from build 1 | 1,343,926 bytes |

- **What the sdist holds:** `src/refute` (126 files), `tests/` (with `tests/fixtures`), `LICENSE`,
  `README.md`, `CITATION.cff`, `pyproject.toml`, `PKG-INFO` and `.gitignore`.
- **What is unchanged:** no dependency, the build backend (`hatchling>=1.26`) and the version.
- `uv lock --check --offline` passes on the patched copy, with 108 packages resolved.

## M5b: the metadata

- **The classifiers.** Five are added to the six already there:
  - `Environment :: Console`;
  - `Operating System :: Microsoft :: Windows` and `Operating System :: POSIX :: Linux` (the two
    systems CI tests);
  - `Programming Language :: Python :: 3 :: Only`;
  - `Topic :: Scientific/Engineering`.

  Each of the eleven exists on https://pypi.org/classifiers/ (read 2026-11-26).
- **`[project.urls]`:**
  - Homepage `https://refute.science`: the `site` of `refute-site`'s `astro.config.mjs`, which
    answered HTTP 200 on 2026-11-26;
  - Repository `https://github.com/klucilla/refute`;
  - Issues `https://github.com/klucilla/refute/issues`.
- **Unchanged:**
  - `readme = "README.md"`, giving `Description-Content-Type: text/markdown`;
  - `license = "Apache-2.0"` with `license-files = ["LICENSE"]`, giving `License-Expression:
    Apache-2.0` and `License-File: LICENSE`.

  These are the project's own licence and file, so no external licence statement is made.
- **No licence classifier.** PEP 639 metadata carries the licence as an expression.

## M5c: what the index would show

- **The metadata check.** Twine was not run locally: it would be third-party code, so its first
  run is the maintainer's to approve. The workflow runs `twine check --strict` (7.0.0) in its build
  job.
- **The README on PyPI.** 20 of the README's link targets are relative (3 images, including the
  banner). They do not resolve on a PyPI page. The README's bytes were approved in M3 and are not
  changed here; the choice is the maintainer's (for example, absolute URLs, or a separate
  long-description file).
- **What would be published:** the sdist and wheel of build 3 are those the workflow would build
  from the same tree.

## M5a and M5d: the workflow and Codex's round

**The workflow** (described here; the file is not committed):
- **Trigger:** `workflow_dispatch` only, with `target` = `testpypi` or `pypi`. The top level has
  `permissions: {}`.
- **The build job** (`contents: read`):
  1. an exact shell check of `refs/heads/main` and of the target;
  2. checkout, with `persist-credentials: false`;
  3. setup-uv 0.12.24;
  4. `uv build`;
  5. `uvx --from twine==7.0.0 twine check --strict dist/*`;
  6. the upload of the artifact.
- **The publish job:**
  - it has `id-token: write` only;
  - it runs in the environment `${{ inputs.target }}`;
  - it downloads the artifact;
  - it runs `pypa/gh-action-pypi-publish`, with `repository-url:
    https://test.pypi.org/legacy/` for TestPyPI.
- **There are** no secret, no token and no `PYPI_*`.

**The pins** (full commit SHAs, each from a release at least 7 days old; read 2026-11-26):

| Action | Release | Published | Commit |
|---|---|---|---|
| pypa/gh-action-pypi-publish | [v1.14.3](https://github.com/pypa/gh-action-pypi-publish/releases/tag/v1.14.3) | 2026-10-20 | `7245906fb61fa33a13554f9d5fb856fe61758086` (the commit its annotated tag points to) |
| actions/upload-artifact | [v7.0.2](https://github.com/actions/upload-artifact/releases/tag/v7.0.2) | 2026-10-07 | `cf430e030ddbb5b0abf93d22962f4752f3646cd9` |
| actions/download-artifact | [v8.0.2](https://github.com/actions/download-artifact/releases/tag/v8.0.2) | 2026-10-07 | `9000827ccba6bdab643e8b6fd33ac0654aef8333` |
| actions/checkout, astral-sh/setup-uv | the pins of `ci.yml` | | |

Twine 7.0.0 was released on 2026-07-27 (https://pypi.org/project/twine/7.0.0/).

**Codex: one round,** in a new thread, `01a21a03-0c00-7c01-a946-4ee84d6673cd`. The prompt and the
answer are stored unchanged: [prompt](codex-round-1-prompt.md) and
[answer](codex-round-1-answer.md), whose SHA-256 is `9369028b…48800d`. It used 205,403 input
tokens (178,176 cached) and 5,193 output tokens.
- **Its verdict was `NOT_APPROVABLE`, with one item:** expression comparisons are
  case-insensitive, so `github.ref == 'refs/heads/main'` also accepts `refs/heads/Main`.
- **Its exact replacement was applied:** a shell step that requires `refs/heads/main` and a valid
  target before checkout.
- **There was no second round** (one round was the decision), so Codex has not seen the
  application.
- **Its other answers:** permissions minimal; `workflow_dispatch` the only trigger; all six
  `uses:` pinned by SHA with the tag in a comment; no secret; the names match the registrations.

## The version: a proposal (the decision is the maintainer's)

**The proposal: `0.5.12`,** if the first public release is built from a `main` with no v0.5.13
change in `src/`.
- `0.5.0` already names a different tree, the tag `v0.5.0` and its Zenodo record. Publishing the
  current code as 0.5.0 would give one version two trees.
- `0.5.12` names the last closed phase, whose code the current `main` carries. It is above 0.5.0,
  and no tag has it.
- **If the release waits until after v0.5.13's `src/` changes, propose `0.5.13`.**

**What a version change touches:**
- `pyproject.toml`;
- `src/refute/__init__.py`, which is a stop (`src/`); `refute.__version__` also enters new locks
  and dossiers;
- `uv.lock`, whose project entry is a stop (dependencies and lock);
- `CITATION.cff` and `.zenodo.json`.
