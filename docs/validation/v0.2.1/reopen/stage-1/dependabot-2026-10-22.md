# Dependabot alerts on 2026-10-22: the list and a proposed treatment (nothing changed)

The maintainer's decision after X2 (2026-10-22, item 5): list the open alerts by manifest, package and
severity, without printing any configuration or secret; check whether they come from the v0.3
dossiers' `requirements.lock` files; propose a treatment. **No dependency is changed and no alert is
dismissed before the maintainer's approval.**

Read with `gh api repos/klucilla/refute/dependabot/alerts?state=open` and a filter that keeps only the
alert's number, manifest, ecosystem, package, severity, advisory id and vulnerable range (the script:
`.cache/merge-v021/tools/dependabot_alerts.py`).

## The open alerts: 42, all in `uv.lock`

**None comes from a dossier's `requirements.lock`.** Every one is in the root `uv.lock`, in four
packages:

| Package (locked) | Alerts | Severity | First patched | Pulled in by |
|---|---|---|---|---|
| Pillow 12.3.0 (the advisories name it `Pillow` or `pillow`) | 28 | 3 critical, 16 high, 9 medium | 13.0.0 | matplotlib, bokeh |
| aiohttp 3.14.3 | 8 | 3 high, 3 medium, 2 low | 3.14.4 | s3fs, aiobotocore |
| virtualenv 21.14.2 | 5 | 3 high, 2 medium | 21.14.9 | pre-commit (development only) |
| certifi 2026.7.22 | 1 | 1 critical | 2026.10.19 | requests |
| **total** | **42** | **4 critical, 22 high, 14 medium, 2 low** | | |

The alert numbers: Pillow #10, #21, #38 (critical); #11, #13, #14, #15, #17, #18, #23, #24, #25, #26,
#28, #33, #34, #35, #36, #39 (high); #12, #16, #22, #27, #29, #30, #31, #32, #37 (medium). aiohttp #1,
#3, #5 (high); #6, #7, #9 (medium); #2, #8 (low). virtualenv #19, #20, #40 (high); #41, #42 (medium).
certifi #4 (critical). The listing itself (`alerts.json`) stays in the working folder. Opened on
2026-10-20 (#1 to #3) and 2026-10-22 (the rest): new advisories against versions already locked, not a
change of the lock.

## The 7-day rule (CLAUDE.md) against the patched versions' release dates (PyPI, read 2026-10-22)

| Version | First upload (UTC) | Eligible under the 7-day rule from |
|---|---|---|
| aiohttp 3.14.4 | 2026-10-05 17:37 | now |
| Pillow 13.0.0 | 2026-10-16 22:15 | 2026-10-23 22:15 |
| virtualenv 21.14.9 | 2026-10-17 16:09 | 2026-10-24 16:09 |
| certifi 2026.10.19 | 2026-10-20 02:24:15 | 2026-10-27 02:25 (02:24:15 plus 7 days, rounded up) |

Source: `https://pypi.org/pypi/<package>/<version>/json`, the `upload_time_iso_8601` of the version's
first file, read 2026-10-22 (script `.cache/merge-v021/tools/pypi_dates.py`).

## Proposed treatment (for the maintainer)

- **The dossiers' `requirements.lock`:** nothing to dismiss: no alert is open on them.
- **`uv.lock`:** a single dependency update in this phase's planning, **on or after 2026-10-27 02:25
  UTC** (when all four patched versions pass the 7-day rule), by `uv lock --upgrade-package` for the
  four packages (`exclude-newer = "7 days"` in `pyproject.toml` applies the rule), then the full suite
  and CI; Pillow 13 is a major version under matplotlib and bokeh, so the dossiers' plots are made
  once with it and looked at before the update is kept. The update changes `uv.lock`, part of the
  code hash: it goes **before** any
  new lock of this phase, never between a lock and its use; the v0.3 locks are already `TAMPERED
  (code)` on main by design and are checked at their tag.
- **Until then:** the alerts stay open (no dismissal: they are real for the locked versions);
  virtualenv is a development tool only (pre-commit); aiohttp is reached only through s3fs.
