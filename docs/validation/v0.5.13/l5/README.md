# L5: the index refresh, and the Dependabot alerts (read only)

The maintainer's decision L5 (#218, comment 7223634913). Labels: `exploratory`,
`method_status: not_validated`. Nothing was changed: no commit of content, no dependency.

## (a) The files that showed as modified with an empty diff

`git status` listed `src/refute/packs/tess/a0.py`, `tests/test_junit_counts.py`,
`tests/test_v051_a0.py` and `tests/test_v051_wp2.py` as modified, while every `git diff` of them
was empty.
- **The refresh:** the metered unit `index-refresh` (`git update-index --refresh`, index only, no
  path) ran. It reported each of the four as "needs update", and `git status` still lists them.
  It is **not clean**.
- **What was read:**
  - `git ls-files --eol`: index and working tree are both LF (`i/lf w/lf`, `text=auto eol=lf`);
  - `git status --porcelain=v2`: the same blob at HEAD and in the index, and the same mode;
  - `git diff`, `git diff --raw --no-ext-diff --no-textconv` and `git diff HEAD`: all empty.
- **The bytes** (the committed read-only unit `bytes-vs-head`, raw bytes, no filter): each
  working-tree file equals its HEAD blob in size and SHA-256. For example, `a0.py` is 17,782 bytes,
  SHA-256 `cf1b47a0ad94c4102b18a9dd97ae12b14db84d57bdb722e1b0fecbb6ed1ae5f1` on both sides.
- **So:** the content of `a0.py`, which is on version 3's golden path, is unchanged. What git
  reports is a state of the index entries, not of the files. No `--really-refresh`, checkout or
  re-staging was tried; each would write to the index or the working tree beyond what L5a
  approved.

## (b) The open Dependabot alerts

Read with `gh api repos/klucilla/refute/dependabot/alerts --paginate` and a `--jq` filter that
names only alert fields (no `config`), on 2026-11-27. Four alerts are open, all for `setuptools`
(pip), scope `runtime`, in the recorded environment files of v0.5.10, which pin
`setuptools==80.10.2`:

| Alert | Manifest | Advisory | Severity | Vulnerable | Fixed in | Fix released (PyPI) |
| --- | --- | --- | --- | --- | --- | --- |
| 75 | `docs/validation/v0.5.10/engines/requirements.txt` | GHSA-h35f-9h28-mq5c (CVE-2026-59890) | medium | < 83.0.0 | 83.0.0 | 2026-07-04 |
| 76 | `docs/validation/v0.5.10/engines/requirements.txt` | GHSA-xmj3-9gf7-h52w | low | >= 38.2.2, < 84.1.0 | 84.1.0 | 2026-10-19 |
| 77 | `docs/validation/v0.5.10/engines/requirements-install.txt` | GHSA-h35f-9h28-mq5c (CVE-2026-59890) | medium | < 83.0.0 | 83.0.0 | 2026-07-04 |
| 78 | `docs/validation/v0.5.10/engines/requirements-install.txt` | GHSA-xmj3-9gf7-h52w | low | >= 38.2.2, < 84.1.0 | 84.1.0 | 2026-10-19 |

- **The advisories' summaries:**
  - GHSA-h35f-9h28-mq5c: "MANIFEST.in exclusion bypass in sdist via Unicode normalization
    collision (NFC/NFD) on macOS APFS/HFS+";
  - GHSA-xmj3-9gf7-h52w: "Windows path escape via namespace_packages.txt during legacy wheel
    installation".
- **The release dates** are the upload times of the files of each version, read on 2026-11-27
  from https://pypi.org/pypi/setuptools/83.0.0/json (2026-07-04T15:31:20Z, the wheel) and
  https://pypi.org/pypi/setuptools/84.1.0/json (2026-10-19T20:11:41Z, the wheel). Both are older
  than the 7-day cooldown.
- `setuptools` is not in the project's `uv.lock` or `pyproject.toml`. The two manifests are
  records of v0.5.10's engine environment. Whether and how to treat them belongs to the dependency
  plan before v0.5.14's lock, which is the maintainer's.
