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

## Seal and annexes (from v0.3)

`refute seal <dossier>...` seals the **experimental core** of each dossier: every
file except `SEAL.json` and `annexes/`, that is the locked claims, the outputs, the
logs, `verdict.json` and `MANIFEST.sha256`. It writes `SEAL.json` with the SHA-256 of
a deterministic archive of the core, and prints the core hashes and one combined hash
of the set (`<core sha256>  <dossier name>` lines, sorted by name).

The archive (`refute-seal-1`):
- is a zip of the core files in sorted path order;
- stores them without compression;
- uses a fixed timestamp, mode 0644 and Unix as the creating system;
- holds the raw bytes of each file, as `MANIFEST.sha256` does. The repository's
  `.gitattributes` keeps text files LF on every checkout, so a change of line endings
  is a change of the core.

The combined hash is the SHA-256 of the canonical JSON of the sorted
`[name, core sha256]` pairs; dossier names may not contain path separators or control
characters.

A dossier is sealed once: the core never changes after the seal (plan section 9.1).

`refute annex <dossier> <name> <directory>` adds an annex (a reviewer report, a
`reply` record, the authors' reply) under `annexes/<name>/` with its own `ANNEX.json`.
That manifest lists the raw-byte SHA-256 of each annex file and cites the core hash.
- An annex is added only to a sealed, intact core.
- It is never rewritten, and never changes the core hash.
- Annex names and annex file names must be portable: lowercase names, no Windows
  device names, no names that differ only by case.
- Symbolic links and junctions are refused in the dossier and in the annex source.

`MANIFEST.sha256` written from v0.3 on does not cover `SEAL.json` or `annexes/`. An
older manifest that lists such paths keeps covering them.

`refute check-dossier` on a sealed dossier reports separately whether the core is
intact against its seal and whether each annex is intact against its manifest.

Limit: an annex is checked against its own `ANNEX.json`. A copy in which an annex file
and its manifest were both replaced consistently, or an annex removed whole, is not
detected from the dossier alone. `refute annex` therefore prints the SHA-256 of the
new `ANNEX.json`, so that it can be recorded publicly like the core hash. A check
against such an external list of annex manifests is not implemented.

## Archives

`refute archive dossiers/<run_id>` writes a deterministic zip (sorted entries,
fixed timestamps and permissions) and `<zip>.sha256`, suitable as a release asset.
The same input always gives the same bytes.
