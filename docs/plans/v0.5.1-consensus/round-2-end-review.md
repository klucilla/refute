## Verdict: WEAKENED

I found no demonstrated regression in version 2 or earlier claims, and the version 3 routing matches the plan. The round is weakened because the committed tests cover selected mechanisms, not the acceptance rates, and there is no committed WP3(b) acceptance runner among the scripts.

## Objections

1. **Important, acceptance evidence is not ready.** The 13 tests in [test_v051_sinusoid.py](/C:/Projetos/refute/tests/test_v051_sinusoid.py) check selected synthetic examples, such as a trend becoming an extra frequency and an out-of-domain harmonic becoming not applicable. They do not establish the planned rates for WP3(b) rows 3.1–3.4 and 3.8, including false-failure, power, and non-regression requirements. I also found no WP3(b) acceptance script in `scripts/`. **Change required:** provide the frozen-code, acceptance-seed runner and the row-level reports before claiming WP3(b) accepted. The commit describes these runs as future work, so this does not invalidate the mechanism tests.

2. **Important, prewhitening can select a redundant extra frequency.** In [battery_v51.py](/C:/Projetos/refute/src/refute/packs/tess/battery_v51.py), each new peak is searched outside the tested harmonics, but not outside previously selected extra frequencies. A nearby repeat could leave redundant, highly correlated columns in the final fit; `_wls` directly inverts the normal matrix. The current tests do not exercise that case. **Change required:** prevent duplicate or near-duplicate extra frequencies, handle rank-deficient fits without an uncaught exception, and add a known-truth case with closely spaced or repeated variability.

3. **Minor, version 2 compatibility is asserted more broadly than tested.** The version 2 test checks that the plan omits the new section and selects the old registry, but it does not compare pipeline, measurement-chain, or paired outputs against the previous behavior. The code changes in those routes are narrow and `registry_for(version_2_plan)` returns the original registry, so this is a coverage gap rather than a found behavior change. **Change required:** add a compatibility test through the affected routes, or narrow the test’s “runs exactly as before” claim.

## Implementation Review

- Version 2 and earlier claims appear to retain their old behavior: `battery_v5.check_sinusoid` remains the version 2 path, and `registry_for` returns `TESS_REGISTRY` unless `plan.v051` is true. The changed enforcement calls in `pipeline.py`, `measure.py`, and `paired.py` all use that selector. I found no changed call path that sends version 3 to the version 2 sinusoid or registry.
- WP3(b)’s main requirements are implemented: P/2, P, and 2P are checked separately within the 20-day harmonic domain; out-of-domain checks are marked not applicable; the conditional registry requires at least one applicable check; and sensitivity uses the v0.5 rejection rule and alternative. The per-harmonic covariance block is the corresponding marginal submatrix from the joint WLS covariance. Scaling it by the joint-residual beta squared is consistent with the v0.5 uncertainty inflation.
- Two choices are not fixed by the acceptance text: the extra-frequency search interval, 2/T_span to 10/day, and amplitude S/N as peak amplitude divided by the mean amplitude-spectrum level. They are documented in code, but should be reported as implementation choices and assessed by the acceptance runs.
- The version 3 tests use synthetic curves with known injected components for their mechanism examples. They do not prove the acceptance rate claims, which remain pending the planned acceptance runs.

## Points of Agreement and Commit Rules

The implementation correctly leaves `battery_v5.py` unchanged, separates the version 3 registry, and represents a non-applicable harmonic without letting it satisfy sensitivity by itself. Commit messages and changed repository text are in English. Neither commit has a closing keyword such as “Closes #208”; issue numbers appear in the subjects and bodies. I found no protected Drive contents or credential-bearing material in the reviewed commit diffs, and did not access the restricted path.

No files were changed and no tests or write-capable commands were run. The working tree showed no changes.

