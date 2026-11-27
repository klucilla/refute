# E5: the TestPyPI run and the SHA-256 check

The maintainer's decision E5 (#218, comment 7216128796). Labels: `exploratory`,
`method_status: not_validated`.

**Not a publication on the real PyPI.** No token was handled by the agent. The `testpypi`
deployment was approved by the maintainer, never by the agent.

## Preconditions, checked before the run

- **The Actions policy** was read through the API (read only). It now allows
  `pypa/gh-action-pypi-publish@7245906fb61fa33a13554f9d5fb856fe61758086`, besides GitHub-owned
  actions and `astral-sh/setup-uv@*`; `verified_allowed` is false. The maintainer changed it.
- **`scripts/ci_evidence.py 3a5eba51a649d187ca53dc32761d521d54001fbb --level full`:** run
  [45984036489](https://github.com/klucilla/refute/actions/runs/45984036489)
  (`workflow_dispatch`), 28 jobs, all success, "evidence holds".
- **The tip of `main` on GitHub** was `3a5eba51a649d187ca53dc32761d521d54001fbb`, read through
  the API just before the dispatch.

## The run

| Item | Value |
| --- | --- |
| Run | [45997324235](https://github.com/klucilla/refute/actions/runs/45997324235) |
| Trigger | `workflow_dispatch` from `main`, `target=testpypi` |
| Commit | `3a5eba51a649d187ca53dc32761d521d54001fbb` |
| Jobs | build (wheel and sdist): success; publish to testpypi: success |
| Conclusion | success |

The one approved execution; nothing was re-run.

## The SHA-256 check

**The build job's listing** ("List what would be published", `sha256sum dist/*`):
```
2d211437a6dd31a12df6b8954b5c294a250b74c2760298a4b568f1e6dc3de23f  dist/refute-0.5.12-py3-none-any.whl
c15ac524404d1118d976f79eaf4592bd05db7ceb1e5077f42aaeb8a206d8842e  dist/refute-0.5.12.tar.gz
```

The two files were downloaded from TestPyPI and **not installed**, by the metered unit
`testpypi-fetch` (`tools/testpypi_fetch.py 0.5.12`, standard library, no credentials). The full
record is [testpypi-fetch.json](testpypi-fetch.json).

| File | Bytes | SHA-256 (downloaded) | = build listing | = index digest |
| --- | --- | --- | --- | --- |
| `refute-0.5.12-py3-none-any.whl` | 619,512 | `2d211437…dc3de23f` | yes | yes |
| `refute-0.5.12.tar.gz` | 1,343,910 | `c15ac524…a206d8842e` | yes | yes |

**Result:** both files on TestPyPI are byte for byte the files the build job listed.
