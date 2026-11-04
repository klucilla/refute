# The S4 deviation of the v0.5 calibration (C3 claim packaging)

**Status:** approved by the maintainer on 2026-11-04 (option C: the original draw kept), recorded
on #199 before any commit:
https://github.com/klucilla/refute/issues/199#issuecomment-6639920251

Every report of C3 says: **original code and selection kept; claim packaging and input
preparation under a deviation approved on 2026-11-04.** C3 is never described as run without an
exception to its protocol.

## What failed

The calibration was frozen at `5f987db` (code hash `15a9c256b5aa8f6b6f1eb9db511420ee1efca15b95edd9343322d7c3bb52bf8e`)
and the C3 selection committed at `3e44e42` (drand round 6612465). At S4, before any lock and
before any C3 fetch or run, four defects of the frozen code were found:

1. **Extra fields in the targets attachment** (blocking). `c3select.targets_document` writes
   `c3_place` (every target) and `fp_class` (the false positives) into `selection/targets.yaml`;
   the TESS targets schema (`TargetsFile`, extra fields forbidden) refuses them, so the claim
   written by `run_calibration.py claim` could be neither loaded, locked nor run (33 errors).
2. **TESS-EB missing from the C3 cache** (blocking for C3). `c3-run` resolves the claim's
   TESS-EB reference rows from `<c3-fetch cache>/v04/tess-eb/tess_ebs_prsa2022.tsv`, but the frozen
   `c3-fetch` never places the edition there: every control would be an error record.
3. **No `reproduction` section in the claim.** `refute prepare-inputs` has nothing to fetch; a
   dossier run fetches the TESS-EB table itself from the URL recorded in `eb_catalog_scan.json`
   and checks its content SHA-256 (the frozen claim-level preparation, as in v0.4).
4. **No check of the claim against its lock before running.** `c3-fetch` and `c3-run` check the
   freeze and the budget decision but read `claim.yaml` without `refute verify`.

**Why no new draw:** a second draw after the first selection is public would be a discretionary
restart with knowledge of the first sample; the defects are in packaging and input placement,
not in the walk, the randomness or the chosen controls.

## The scope (nothing else)

Nothing in `src/`, `pyproject.toml`, `uv.lock`, the snapshots, the selection or the protocol
changes; no analysis code, threshold, test role or frozen input changes. The files:

| File | What it is |
|---|---|
| `claim.generated.yaml` | the claim exactly as the frozen `run_calibration.py claim` wrote it (2026-11-04) |
| `project_targets.py` | writes `../claim-targets.yaml` (the bytes of `../selection/targets.yaml` with only the target-level `c3_place` and `fp_class` lines removed) and `../claim.yaml` (the generated claim with its targets attachment pointing at `claim-targets.yaml`, `selection/targets.yaml` attached as `selection-targets`, and two header comment lines) |
| `projection.json` | the SHA-256 of every input, output and of the script; every removed line with its number; the checks |
| `claim-targets.diff`, `claim.diff` | the complete unified diffs |
| `prepare_tess_eb.py` | copies the static TESS-EB edition (raw SHA-256 `61cb8749…`, content SHA-256 `a31936ce…`, both as frozen in `inputs.json`) to the path the resolver reads in a given cache; never writes over a file |
| `guarded_c3.py` | `refute verify` against the lock (PASS only), the lock's coverage of the C3 inputs, the projection, the plan `c3-run` rebuilds and the catalog in the cache; then the frozen `c3-fetch` or `c3-run`, unchanged |

The C3 steps keep reading `selection/targets.yaml` (with `c3_place`, which the replacement rule
needs); `refute discover` reads `claim-targets.yaml`. The lock covers both.

## The procedure

From the repository root, with the project's environment:

1. Done on 2026-11-04 (the hashes are in `projection.json`):
   `.venv/Scripts/python.exe calibration/v0.5/deviation/project_targets.py`
2. S4: the claim commit; commit A (the frozen code hash); commit B, the lock
   (`uv run refute lock calibration/v0.5/claim.yaml`); `uv run refute verify calibration/v0.5/claim.yaml`.
3. C3, only after its approval:
   - `.venv/Scripts/python.exe calibration/v0.5/deviation/prepare_tess_eb.py --cache <dir>`
   - `.venv/Scripts/python.exe calibration/v0.5/deviation/guarded_c3.py c3-fetch --cache <dir>`
   - `.venv/Scripts/python.exe calibration/v0.5/deviation/guarded_c3.py c3-run`
4. The dossiers: `uv run refute verify calibration/v0.5/claim.yaml` (PASS), then `refute discover`
   on the claim. The TESS-EB edition is fetched by the frozen claim-level preparation
   (`TessAdapter.prepare_claim_data`) from the URL recorded in the claim's scan and checked by its
   content SHA-256 before any analysis, unless `prepare_tess_eb.py --cache <the run's cache>`
   placed the exact static edition first.

## Two preparation paths

- **C3 execution** (`c3-fetch`, `c3-run`, on the maintainer's machine): `prepare_tess_eb.py` places
  the exact static edition of 2026-10-18 (raw SHA-256 `61cb8749…`), which must be present
  locally at the path `inputs.json` records. It is not a clean-clone tool: a fresh VizieR answer
  with the same content has other header comments (a request date), so its raw SHA-256 differs
  and the script stops.
- **Clean-clone dossier reproduction** (criterion 6): no preparation script is needed and none
  is used. The frozen claim-level preparation fetches the TESS-EB table from the scan's recorded
  URL and checks its content SHA-256, the rule the resolver applies.

## Criterion 6 (not waived)

The maintainer's decision of 2026-11-04
(https://github.com/klucilla/refute/issues/199#issuecomment-6640383170):
`prepare_tess_eb.py` applies to the C3 execution on the maintainer's machine; exit criterion 6
(one C3 dossier reproduced in a clean clone, nothing placed by hand) is judged only by a real
reproduction in a clean clone, with nothing placed by hand, the TESS-EB table obtained by the
frozen claim-level preparation above; if that source does not answer, or answers other content,
criterion 6 stays open and is reported as open. **Not yet demonstrated:** static inspection (Codex, 2026-11-04) establishes a plausible
route, not a successful reproduction; criterion 6 stays open until a clean-clone reproduction
succeeds.

## Limits of these helpers

- The three scripts are outside the code hash (`refute-code-1` covers `src/`, `pyproject.toml`
  and `uv.lock`) and are not claim attachments: `refute verify` authenticates the claim and the
  frozen code, not these helpers. Every execution record names the git revision of the helpers it
  ran; `projection.json` records the SHA-256 of `project_targets.py` as it ran.
- `project_targets.py`'s docstring says "a failure writes nothing"; that is inaccurate (Codex,
  2026-11-04): the staging copy is written before it is validated, the outputs are created one by
  one (each exclusively, never over a file) and the repository's claim is validated after they
  are written, so a failure can leave a partial set of new files. The script is not edited, so
  that the SHA-256 in `projection.json` stays the one of the script that ran.
- The diff checks compare changed lines as multisets and split lines without their endings;
  the outputs were also compared exactly with the declared transformations (Codex, 2026-11-04:
  22 `c3_place` and 11 `fp_class` lines removed; the claim's attachment substitution and two
  header comment lines, nothing else).
- `prepare_tess_eb.py`'s link and junction checks guard a controlled workspace, not a concurrent
  hostile replacement of a folder; the publication needs hard links (it fails closed without
  them); a failed copy can leave this call's `.part` file.
- The synthetic tests (`tests/test_v05_deviation.py`) cover the projection, the placement, the
  guard's lock refusal before the frozen step, its plan check and its catalog check on synthetic
  inputs; they are not a reproduction.

## The lesson

Before a freeze, exercise the claim packaging end to end with synthetic targets: write the claim
with the frozen code, load it, lock it and run each step on synthetic data, so that a schema or
input-placement defect is found before the code is frozen (`docs/plans/v0.5-plan.md`, section 9b).
