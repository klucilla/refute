# Command-line interface

All commands are run with `uv run refute ...` from a source checkout.

| Command | What it does | Exit codes |
|---|---|---|
| `refute --version` | Print the version. | 0 |
| `refute packs` | List installed domain packs (entry-point group `refute.packs`). | 0, 1 if none |
| `refute lock CLAIM [--force --reason TEXT]` | Hash the resolved claim, its attachments and the code; write `CLAIM.lock.json`; append to `LOCK_HISTORY.md`. Calibration claims need a clean, committed git tree. | 0 locked, 1 refused |
| `refute verify CLAIM [--json]` | Recompute every hash and compare with the lock. | 0 PASS, 1 FAIL, 2 TAMPERED |
| `refute fetch CLAIM [--target T]... [--cache-dir DIR]` | Download and cache the targets' public data (network). | 0, 1 if any target failed |
| `refute replicate CLAIM [options]` | Verify, fetch, analyze every target in parallel, write dossiers and a summary. Needs a `replicate` claim. | 0 run completed, 1 not verified or invalid, 2 TAMPERED |
| `refute calibrate [--claim CLAIM] [options]` | Same for a `calibration` claim (default `calibration/self_claim.yaml`); evaluates the self-claim. | as `replicate` |
| `refute check-dossier DIR [--against DIR]` | Verify a dossier's manifest; with `--against`, compare key results with an original dossier. | 0 OK, 1 problems |
| `refute archive RUN_DIR [--out ZIP]` | Deterministic zip of a run directory plus `ZIP.sha256`. | 0, 1 if not found |

Run options for `replicate` and `calibrate`:

- `--target TIC-123` (repeatable): run only these targets. A calibration self-claim
  is only evaluated on a complete run.
- `--out DIR` (default `dossiers`), `--run-id NAME`.
- `--workers N`: analysis processes (default: CPU count minus 2).
- `--offline`: use cached data only.
- `--cache-dir DIR` (default `<project>/.cache`).

The exit code of a run says whether the run completed. Whether a self-claim
passed is a scientific result, reported in `summary.md` and `summary.json`.

Refute never submits anything to any scientific body. The `export/` files in each
dossier help a human prepare a submission by hand.
