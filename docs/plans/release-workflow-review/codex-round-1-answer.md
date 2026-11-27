## Verdict: `NOT_APPROVABLE`

The workflow needs one fix before approval. GitHub Actions compares strings case-insensitively, so the current `main` guard also accepts a ref such as `refs/heads/Main`. That ref can reach the build steps. The reported `main`-only environment rules should still block publication from it. [Proposed workflow](C:/Projetos/refute/.cache/v0513prep/m45/release.yml:48)

1. **Permissions.** `id-token: write` is granted only to `publish`. The workflow defaults to `permissions: {}`, and `build` gets only `contents: read`. Checkout disables credential persistence. The YAML contains no step that saves or prints a credential.

2. **Trigger and index.** `workflow_dispatch` is the sole trigger. A manual dispatch can create a run record for another ref. Ordinary off-main refs skip both jobs, while case variants of `main` pass the current YAML guards. For the two declared choices, TestPyPI uses `https://test.pypi.org/legacy/`, and PyPI uses the publish action’s default endpoint. There is no user-supplied URL or fallback between indexes.

3. **Pins.** All six `uses:` entries have a 40-character SHA and a version-tag comment. Checkout and setup-uv match CI exactly. The three new pins match the supplied values, and their recorded release dates clear the seven-day minimum. The sandbox could not reach GitHub, so I could not independently verify the new tag-to-commit mappings or release dates. The local evidence shows no discrepancy. [CI workflow](C:/Projetos/refute/.github/workflows/ci.yml:106)

4. **Secrets and registrations.** The YAML supplies no secret, static token, password, or `PYPI_*` variable. The wildcard appears only in a comment. Trusted Publishing uses a short-lived OIDC token at runtime. The intended filename `release.yml` and environments `pypi` and `testpypi` match the recorded registrations for `klucilla/refute`, project `refute`. The local decision record reports a required reviewer, no administrator bypass, and a `main`-only branch policy for both environments. I could not verify those settings live. [M5 decision record](C:/Projetos/refute/.cache/v0513prep/c-decisions-2.md:25)

5. **Artifacts, metadata, URL, and concurrency.** `uv build` produces the wheel and sdist. Strict Twine checks both before upload, and `publish` downloads the same run’s `dist` artifact. The environment URL points to the selected index’s project page and does not control uploads. The shared concurrency group keeps the active run going, though a newer dispatch can replace an older pending one. No additional blocker found.

## Exact replacement

Replace line 52, the build job’s `steps:` line, with the block below. Keep the checkout step immediately after it. The exact comparisons run before checkout, and `needs: build` prevents publication if either check fails.

```yaml
    steps:
      - name: Require the exact release ref and target
        shell: bash
        env:
          TARGET: ${{ inputs.target }}
        run: |
          [[ "$GITHUB_REF" == refs/heads/main ]] || {
            echo "::error::Release requires refs/heads/main."
            exit 1
          }
          [[ "$TARGET" == testpypi || "$TARGET" == pypi ]] || {
            echo "::error::Release target must be testpypi or pypi."
            exit 1
          }
```

No files were changed and no workflow was run.