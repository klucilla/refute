# v0.5.10 consensus record

## The round on part (f) before its first run (2026-11-24)

By the maintainer's decision of 2026-11-24 received at 12:51 local (#218, comment 7136727624),
item 3. The round covered **only part (f) and its isolation**: supply chain, licences and
exposure. It came before the first run. A blocking item is applied without a new round; a
blocking item that changes the phase's scope is a stop.

| File | SHA-256 |
|---|---|
| [engines-round-prompt.md](engines-round-prompt.md) | `ae8319883a641cf63243c32b580b503adc4d10f7cae93164c2cde2e85e608797` |
| [engines-round-answer.md](engines-round-answer.md) | `1b5c49dd7defae53b5065d04c85ad40ec28e6088042cfadc9cf31a5923288ba0` |

- **Codex:** Codex CLI 0.167.0-alpha.3.2, model gpt-6.2-sol, effort high, a new thread
  (`01a20e46-71fd-73d0-97cb-1a6782b07b73`). It ran read-only through
  `.cache/v04/tools/codex_affinity.ps1` (processors 8 to 31). The answer is stored unchanged, with
  its SHA-256 checked against the original.
- **Its tokens, the real sum of its events:** 4,970,254 input (4,817,152 cached) and 17,543
  output, so **170,645** review tokens.
- **Verdict: `WEAKENED`.** Blocking items 1 to 5 and 8 change no scope. Item 9 changes the scope.

**What follows from it:**
- **Items 1 to 5 and 8** are applied to the plan in
  [docs/validation/v0.5.10/engines/README.md](../../validation/v0.5.10/engines/README.md),
  section "After Codex's round". They take effect when the engines run.
- **Item 9 is a stop for the maintainer.**
  - v0.5.9's mode S already recorded the best period, epoch and SDE of these TOIs. A TLS search
    of the same light curves, with a recovery result, would produce those same quantities.
  - A different algorithm alone does not make a new diagnostic under Process diet 2, item 4. The
    same crosswalk applies to exoVetter's odd/even and centroid outputs against the recorded
    tests.
  - So part (f) stops before any engine is installed or run: nothing of part (f) has run. Parts
    (a) to (d) do not depend on it and go on within the charter.
- **Nothing installed:** no package of `requirements.txt` was installed, and no wheel was
  downloaded for installation. Only PyPI metadata was read.
