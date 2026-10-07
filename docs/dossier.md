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
    data/manifest.json              input files: SHA-256, sector, year, MAST URL;
                                    product, flux column, quality bitmask;
                                    TIC stellar parameters with version and retrieval time
    plots/                          full.png, phase.png, odd_even.png, secondary.png,
                                    holdout_<year>.png
    environment/                    environment.json (Python, platform, package versions),
                                    requirements.txt (installed distributions), uv.lock
    export/                         ctoi_summary.md, ctoi_fields.json (never submitted)
    REPRODUCE.md                    exact commands to reproduce this dossier
    MANIFEST.sha256                 SHA-256 of every other file in the dossier
```

`run_id` is `<UTC timestamp>-<first 8 hex digits of the claim hash>` unless
`--run-id` is given.

## Integrity

`refute check-dossier <dir>` recomputes `MANIFEST.sha256` and reports missing,
modified or unlisted files.

## Reproduction

`REPRODUCE.md` lists the commands: check out the run's commit, `uv sync --frozen`,
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
