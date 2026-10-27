# The dependency update of 2026-10-27 (gate 3a), checked in full

The update planned in [../dependencies-reachability.md](../dependencies-reachability.md)
("Proposal", item 1, and "The update of 2026-10-27, checked in full"), approved by the maintainer
on 2026-10-22 and 2026-10-23, run on 2026-10-27 after 02:25 UTC, when every version asked for
was eligible under the 7-day rule. It lands before any lock of v0.2.1.

## The update

`uv lock --upgrade-package certifi --upgrade-package aiohttp --upgrade-package virtualenv
--upgrade-package pillow` (uv resolved 108 packages; `exclude-newer-span = "P7D"` in the lock).
`uv.lock` SHA-256 before `79e16fa706c47c7896b708dcd17dbac1f927331c85a25ceca1073e3c654eca4a`,
after `a49bfdf2596e768b24bd340e968c564e916c76b71f1a2119bf3bbde20463cdda`; `pyproject.toml`
unchanged (`bea26d26…21de`).

## The whole diff of `uv.lock`

[lock-diff.json](lock-diff.json) ([scripts/lock_diff.py](scripts/lock_diff.py)): every package of
the two locks compared field by field (version, source, sdist, wheels, dependencies, optional
dependencies, metadata), plus the lock's top-level fields.

| Package | Before | After | Fields changed |
| --- | --- | --- | --- |
| aiohttp | 3.14.3 | 3.14.5 | version, sdist, wheels |
| certifi | 2026.7.22 | 2026.10.19 | version, sdist, wheels |
| pillow | 12.3.0 | 13.0.0 | version, sdist, wheels |
| virtualenv | 21.14.2 | 21.14.11 | version, sdist, wheels |

No package added or removed (108 before and after), no dependency list changed, no top-level field
changed, and **no package of the numeric stack changed** (numpy, scipy, astropy, lightkurve,
astroquery and the others listed in the script). virtualenv resolved to 21.14.11, the newest
eligible release, not the 21.14.9 the plan named as the first fixed one; it contains that fix.

## The 7-day rule

[upload-times.json](upload-times.json) ([scripts/upload_times.py](scripts/upload_times.py)): the
newest upload time uv recorded among each changed package's files, read at 03:03 UTC: certifi
7.03 days old, aiohttp 16.08, pillow 10.2, virtualenv 8.83. Every one meets the rule.

## The environments

- **Updated (the working environment):** `uv sync --frozen`, then the record
  [env-record-after.json](env-record-after.json) (103 distributions, the new lock).
- **The bundle:** [certifi-check.json](certifi-check.json)
  ([scripts/certifi_check.py](scripts/certifi_check.py)): certifi 2026.10.19, and
  `requests.certs.where()` is that certifi's `cacert.pem` in the project's environment. No VM
  downloads in the plan; the VMs' environments were not checked and are not used for downloads
  until they are.
- **Frozen (the earlier lock, for comparison only, offline):** a detached worktree of `b929aae`
  (the commit before the update) under `.cache/frozen-env-79e16fa7/`, `uv sync --frozen`, its record
  [env-record-frozen.json](env-record-frozen.json). [env-comparison.json](env-comparison.json)
  ([scripts/env_compare.py](scripts/env_compare.py)): the frozen environment's 103 distributions
  are **identical** to the committed reference of the earlier lock,
  [../env-record-5294c49-lock.json](../env-record-5294c49-lock.json); the updated environment
  differs from it only in the four packages above.

## The checks

[scripts/checks.ps1](scripts/checks.ps1), then [scripts/checks2.ps1](scripts/checks2.ps1) from its
step 3 (the first script stopped there: under `$ErrorActionPreference = 'Stop'`, Windows PowerShell
5.1 turned uv's first line on stderr into a terminating error, which left an incomplete `.venv` in
the frozen worktree; that `.venv`, inside `.cache/`, was removed and built again).

1. **The full suite** in the updated environment: **3934 tests, 0 failures, 0 errors, 89 skipped**
   (counted from its JUnit file by `scripts/junit_counts.py`).
2. **The acceptance population** of `population_v4` generated again in the updated environment
   (one generation, 22 workers): its manifest's SHA-256 is
   `aee9ecac9794af9b8c957bc85bec4fe1e27023cdcf6a8edfe5976dcf21f12ce2`, **equal** to the committed
   [population/v4-acceptance/manifest-1.json](../../../../population/v4-acceptance/manifest-1.json).
3. **The frozen comparison:** the same X2 subset (`x2_study.py run --subset 2 4`: 2 cases per
   group, 4 realizations, 32 tasks) in both environments; [subset-comparison.json](subset-comparison.json)
   ([scripts/compare_subsets.py](scripts/compare_subsets.py)): 32 records in each, the same names,
   **byte-identical**, no lot problem in either.

## Also in this commit

`x2_study.py`'s command-line docstring no longer lists `x2f-s3`, which the audit of 2026-10-26
removed from the lots (the code already refused it). The code hash (`refute-code-1`) and X2's lot
code digest cover `uv.lock` and `x2_study.py`, so both change with this commit; they are computed
again and recorded with X2f's authorization request.

## Not done here

The Dependabot alerts opened after the plan was approved are not part of this update and were not
acted on. Whether the system certificate stores used by the standard library's `urllib` clients
trust the new roots stays unverified, as recorded in the plan.
