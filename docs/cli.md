# Command-line interface

All commands are run with `uv run refute ...` from a source checkout.

| Command | What it does | Exit codes |
|---|---|---|
| `refute --version` | Print the version. | 0 |
| `refute packs` | List installed domain packs (entry-point group `refute.packs`). | 0, 1 if none |
| `refute lock CLAIM [--force --reason TEXT]` | Hash the resolved claim, its attachments and the code; write `CLAIM.lock.json`; append to `LOCK_HISTORY.md`. Calibration claims need a clean, committed git tree. | 0 locked, 1 refused |
| `refute verify CLAIM [--json]` | Recompute every hash and compare with the lock. | 0 PASS, 1 FAIL, 2 TAMPERED |
| `refute fetch CLAIM [--target T]... [--cache-dir DIR] [--stage S [--promotion FILE]]` | Download and cache the claim-level data (for example a reference catalog that is not redistributed, checked against its locked hash) and the targets' public data (network), one file at a time; incomplete FITS files are deleted and retried. A `discover` claim needs `--stage`: stage 1 downloads no target pixel file, and stage 2 of a funnel star needs its promotion record, as `refute discover`. | 0, 1 if any target failed or a hash does not match |
| `refute replicate CLAIM [options]` | Verify, fetch, analyze every target in parallel, write dossiers and a summary. Needs a `replicate` claim. | 0 run completed, 1 not verified or invalid, 2 TAMPERED |
| `refute calibrate [--claim CLAIM] [options]` | Same for a `calibration` claim (default `calibration/self_claim.yaml`); evaluates the self-claim. | as `replicate` |
| `refute discover CLAIM --stage S [--promotion FILE] [options]` | v0.4: the same for a `discover` claim, at funnel stage `S` (1 or 2). Stage 1 reads no target pixel file, and the tests of stage 2 are reported `INCONCLUSIVE` with zero coverage. A stage-2 run of a funnel star (a target that is not a control) needs `--promotion`, the committed promotion record (`refute-promotion-1`: `claim_id` and the `promoted` target keys), whose SHA-256 goes into the summary and every dossier. Discover claims need a clean, committed git tree to be locked. | as `replicate` |
| `refute check-dossier DIR [--against DIR]` | Verify a dossier's manifest; with `--against`, compare key results with an original dossier. | 0 OK, 1 problems |
| `refute archive RUN_DIR [--out ZIP]` | Deterministic zip of a run directory plus `ZIP.sha256`. | 0, 1 if not found |
| `refute review attach DOSSIER REPORT --reviewer ID --model NAME` | Attach an independent reviewer's report to an intact, unsealed dossier ([reviewer-protocol.md](reviewer-protocol.md)); the verdict never changes. A sealed dossier is refused: its reports are annexes (`refute annex`). | 0 attached, 1 refused |
| `refute seal DOSSIER...` | Seal the experimental core of each dossier: write `SEAL.json` with the SHA-256 of a deterministic archive of the core (every file except `SEAL.json` and `annexes/`), and print each core hash and the combined hash of the set. A dossier is sealed once; its core never changes afterwards. Dossier names must be unique within the set. | 0 sealed, 1 refused |
| `refute annex DOSSIER NAME SOURCE_DIR` | Add the files of `SOURCE_DIR` as `annexes/NAME/` of a sealed, intact dossier, with an `ANNEX.json` manifest that cites the core hash (a reviewer's report, a reply record, the authors' reply). An annex is never rewritten and never changes the core hash. Prints the number of files, the core hash and the SHA-256 of `ANNEX.json`. | 0 added, 1 refused |
| `refute reply-draft DOSSIER --contact FILE --out FILE` | Write an email draft to a paper's authors from a sealed dossier, for a human to review and send. The contact file and the draft live under `private/`. **Never sends anything**; prints only the SHA-256 of the draft and of the address. | 0 written, 1 refused |

Run options for `replicate`, `calibrate` and `discover`:

- `--target TIC-123` (repeatable): run only these targets. A calibration self-claim
  is only evaluated on a complete run.
- `--out DIR` (default `dossiers`), `--run-id NAME`. The run directory `DIR/NAME` must
  not exist: an existing one is refused before any download, and a run never overwrites a
  dossier file.
- `--workers N`: analysis processes (default: CPU count minus 2).
- `--offline`: use cached data only.
- `--cache-dir DIR` (default `<project>/.cache`).

Before any analysis, runs prepare claim-level data and check its recorded hashes;
a mismatch stops the run with no dossier. A claim that lists one target key twice
(case and spacing ignored) is refused by `fetch`, `replicate` and `calibrate` before any
download. A cached data manifest that is not the requested target's is refused: that target's
analysis stops with an error (`INCONCLUSIVE`), never a verdict from another target's data.
Runs download one target at a time. The
exit code of a run says whether the run completed; a problem while printing the summary never changes it. Whether a self-claim
passed is a scientific result, reported in `summary.md` and `summary.json`.

Refute never submits anything to any scientific body. The `export/` files in each
dossier only gather parameters for a human. They are not an ExoFOP upload: ExoFOP
accepts community candidates only after peer-reviewed publication (or an RNAAS citing a
peer-reviewed methodology) and with its approval (issue #18).
