# Evidence dossiers

Every target analyzed by `refute replicate` or `refute calibrate` gets a dossier:
a directory with everything needed to check and reproduce the verdict.

```
dossiers/<run_id>/
  summary.json, summary.md          run summary (and the calibration self-claim result)
  <TIC-123>/
    claim.yaml                      the locked claim file, byte for byte
    claim.lock.json                 its lock
    integrity.json                  `refute verify` result at the start of the run
    target.json                     the target entry that was analyzed
    attachments/                    copies of the claim's attachments (e.g. targets.yaml)
    verdict.json                    verdict, every test result, candidate, holdout rounds
    report.md                       human-readable report
    data/manifest.json              input files (light curves and, from v0.2, target
                                    pixel files): SHA-256, sector, year, MAST URL;
                                    product, flux column, quality bitmask;
                                    TIC stellar parameters with version and retrieval
                                    time; TIC neighbors (v0.2)
    plots/                          full.png, phase.png, odd_even.png, secondary.png,
                                    holdout_<year>.png
    environment/                    environment.json (Python, platform, package versions),
                                    numeric_runtime.json (v0.2.1: BLAS thread pools and
                                    thread variables of the analyzing process),
                                    requirements.txt (installed distributions), uv.lock
    export/                         candidate_parameters.md and .json: a parameter sheet
                                    for a human, never submitted; not an ExoFOP upload
                                    (see the note below)
    REPRODUCE.md                    exact commands to reproduce this dossier
    review/                         v0.2, only if reviewed: reviewer reports, index.json
                                    (report hashes and pre-review fingerprints), index.md
    MANIFEST.sha256                 SHA-256 of every other file in the dossier
```

`run_id` is `<UTC timestamp>-<first 8 hex digits of the claim hash>` unless
`--run-id` is given.

ExoFOP accepts community candidates only after they are published in a
peer-reviewed journal, or in a Research Note of the AAS that cites a peer-reviewed
methodology, and only with ExoFOP's approval (news of 2026-08-19 and
https://exofop.ipac.caltech.edu/tess/candidate_help.php). A dossier is therefore never
sent to ExoFOP directly; the `export/` sheet only gathers parameters for that later,
human step (publication path: issue #18).

## Integrity

`refute check-dossier <dir>` recomputes `MANIFEST.sha256` and reports missing,
modified or unlisted files.

## Independent reviews

Reviewer reports are attached after the verdict with `refute review attach`
([reviewer-protocol.md](reviewer-protocol.md)). `review/index.json` records the
SHA-256 of every report, of `verdict.json` and of the manifest lines of every
analysis file at review time. `refute check-dossier` recomputes them, so the
analysis, the verdict and the reports cannot change unnoticed after a review.

## Reproduction

`REPRODUCE.md` lists the commands: clone the repository, check out the run's commit,
`uv sync --frozen`,
`refute verify`, re-run the single target into a new directory with
`--workers 1`, then

```bash
uv run refute check-dossier repro/repro/TIC-123 --against <original dossier>
```

which also requires:

- identical input data hashes (`data/manifest.json`);
- identical verdict, status and test statuses;
- `key_values` in `verdict.json` (period, epoch, duration, depth, SNR, hidden-year
  SNRs) equal within a relative tolerance of 1e-6.

The lock records the commit that contains the locked code (commit A). The run is
made from a later commit that also contains the lock file (commit B). `REPRODUCE.md`
checks out the run commit; `refute verify` proves that its code hash equals the
locked one.

## Archives

`refute archive dossiers/<run_id>` writes a deterministic zip (sorted entries,
fixed timestamps and permissions) and `<zip>.sha256`, suitable as a release asset.
The same input always gives the same bytes.
