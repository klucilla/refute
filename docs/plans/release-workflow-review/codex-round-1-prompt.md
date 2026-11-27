You are a read-only reviewer for the Refute repository (C:\Projetos\refute). Do not modify any file and open no folder outside this repository. You may read public GitHub pages or APIs only if your sandbox allows it; otherwise review from the file. This is a new conversation, for one round only.

The file to review is `.cache/v0513prep/m45/release.yml` (a proposed `.github/workflows/release.yml`, not committed). The maintainer's decision (#218, comment 7204660147, item M5) requires:
- triggered ONLY by `workflow_dispatch`, with the input `target` = testpypi | pypi;
- a build job: `uv build`, wheel and sdist, uploaded as an artifact, with the metadata check;
- a publish job running in the GitHub environment of the same name as the target (`testpypi` or `pypi`), with `permissions: id-token: write` ONLY in that job, the rest of the workflow with minimal permissions;
- `pypa/gh-action-pypi-publish` pinned by the full SHA of a release at least 7 days old (the URL and date recorded), with the TestPyPI `repository-url` when target = testpypi;
- no secret, no token, no `PYPI_*` anywhere; the names must match exactly the registrations: pending publishers of project `refute` on PyPI (environment `pypi`) and TestPyPI (environment `testpypi`), owner `klucilla`, repository `refute`, workflow `release.yml`; GitHub environments `pypi` and `testpypi` with a required reviewer and only the `main` branch.
- Other actions: reuse the pins of `.github/workflows/ci.yml` (checkout, setup-uv); new pins (upload-artifact v7.0.2 at cf430e030ddbb5b0abf93d22962f4752f3646cd9, download-artifact v8.0.2 at 9000827ccba6bdab643e8b6fd33ac0654aef8333, gh-action-pypi-publish v1.14.3 at 7245906fb61fa33a13554f9d5fb856fe61758086, the commit its annotated tag points to) were read from the GitHub API on 2026-11-26.

Closed question. Answer in English:
1. **Permissions:** is `id-token: write` granted only to the publish job, and is everything else minimal? Any token or credential persisted or exposed?
2. **Trigger:** can the workflow run by any event other than `workflow_dispatch`, from a ref other than `main`, or publish to an index other than the chosen target?
3. **Pins:** is every `uses:` pinned to a full commit SHA with its tag in a comment? Any reason to distrust the stated SHAs from what you can check?
4. **Secrets:** is there any secret, token, `PYPI_*` or password anywhere? Do the environment and workflow names match the registrations exactly?
5. **Anything else blocking** (artifact handling, the metadata check, the `repository-url` logic, the environment URL expression, concurrency).
6. **Verdict:** `APPROVABLE` or `NOT_APPROVABLE`, with the exact replacement lines for every blocking item.
