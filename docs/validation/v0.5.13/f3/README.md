# F3: refute 0.5.12 on PyPI, the SHA-256 check and the tag

The maintainer's decision F3 (#218, comment 7218843893), resumed by G7 (comment 7219469262).
Labels: `exploratory`, `method_status: not_validated`.

**Credentials and approvals.** No token was handled by the agent. The maintainer approved the
`pypi` deployment, never the agent. No GitHub release was made.

## Preconditions, checked before the run

- **F2** is committed at `3dbb713c7fa40960d8f7941826e0a9c91a4b1b74`, after G7's checks passed
  (`docs/validation/v0.5.13/g7/`).
- **`scripts/ci_evidence.py 3dbb713c7fa40960d8f7941826e0a9c91a4b1b74 --level full`:** run
  [46007761301](https://github.com/klucilla/refute/actions/runs/46007761301) (push, a full matrix
  because `pyproject.toml` changed), 28 jobs, all success, "evidence holds".
- **The tip of `main` on GitHub** was that commit, read through the API just before the dispatch.

## The run

| Item | Value |
| --- | --- |
| Run | [46023627248](https://github.com/klucilla/refute/actions/runs/46023627248) |
| Trigger | `workflow_dispatch` from `main`, `target=pypi` |
| Commit | `3dbb713c7fa40960d8f7941826e0a9c91a4b1b74` |
| Jobs | build (wheel and sdist): success; publish to pypi: success |
| Conclusion | success |

The one approved execution; nothing was re-run.

## The SHA-256 check

**The build job's listing** (`sha256sum dist/*`):
```
038b507b1dfc827cd4169eaa161bd55e5a84a3fc876a14b4415cc6d4fe3bac29  dist/refute-0.5.12-py3-none-any.whl
037e58d92d58b2075095062d9e3723e6f036c436751e9115c74eeed8a3b33851  dist/refute-0.5.12.tar.gz
```

The two files were downloaded from PyPI and **not installed**, by the metered unit `pypi-fetch`
(`tools/pypi_fetch.py 0.5.12`, through `launch_v4.py`). The record is
[pypi-fetch.json](pypi-fetch.json). The launcher copied it from a tool that writes CRLF, so the
journal's hash of it is of the CRLF bytes (G9).

| File | Bytes | SHA-256 (downloaded) | = build listing | = index digest |
| --- | --- | --- | --- | --- |
| `refute-0.5.12-py3-none-any.whl` | 619,565 | `038b507b1dfc827cd4169eaa161bd55e5a84a3fc876a14b4415cc6d4fe3bac29` | yes | yes |
| `refute-0.5.12.tar.gz` | 1,348,177 | `037e58d92d58b2075095062d9e3723e6f036c436751e9115c74eeed8a3b33851` | yes | yes |

## The tag

Once the check held, the metered unit `make-tag` created the annotated tag **`v0.5.12`** on
`3dbb713c7fa40960d8f7941826e0a9c91a4b1b74`, and pushed it alone (`refs/tags/v0.5.12`).
- The tag message names the run, the CI evidence and both SHA-256.
- Its creation starts a full CI run through the `create` event.
