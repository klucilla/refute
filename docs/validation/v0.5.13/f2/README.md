# F2: the checks before the commit of the index README (STOPPED)

The maintainer's decision F2 (#218, comment 7218843893) set the deterministic checks to run
before the commit, and said: if any fails, stop. Labels: `exploratory`,
`method_status: not_validated`.

## Result: one check failed, so F2 stopped

The unit `check-f2` (`docs/validation/v0.5.13/tools/check_f2.py`, committed at `6b7caf59`) wrote
[check-f2.json](check-f2.json).

| Check | Result |
| --- | --- |
| README.md unchanged against HEAD (SHA-256 `c63218bf…466f013d7`) | pass |
| README-pypi.md differs from README.md only in link targets (md_links; 32 targets, 20 rewritten) | pass |
| README-pypi.md up to date (`make_pypi_readme.render()`) | pass |
| The new wheel differs from 0.5.12 on TestPyPI only in METADATA and RECORD | **fail** |

**The wheel check.** The two wheels have the same 131 entry names. Three entries differ:
- `refute-0.5.12.dist-info/METADATA` (allowed);
- `refute-0.5.12.dist-info/RECORD` (allowed);
- `refute/packs/tess/a0.py` (not allowed).

**The likely cause, from a read-only check.** In the agent's working tree, that file has CRLF line
endings. `git ls-files --eol` gives `i/lf w/crlf attr/text=auto eol=lf`, and `git diff HEAD` on it is
empty. The committed content is unchanged; the local build packed the working-tree bytes.
- The wheel on TestPyPI was built by CI from a clean checkout.
- A normalized rebuild was not made, so this cause is not yet confirmed by a byte comparison.

## What was not done (stopped)

- **F2:** nothing was committed. The proposed files stay in the working tree, uncommitted:
  - `scripts/make_pypi_readme.py`;
  - `tests/test_pypi_readme.py`;
  - the generated `README-pypi.md`.

  The `pyproject.toml` change was set aside and kept in `.cache/v0513/f2/pyproject.f2.toml`, so
  `pyproject.toml` is as at HEAD. The tests were not run.
- **F3**, which depends on F2: no PyPI run, no download and no tag.
