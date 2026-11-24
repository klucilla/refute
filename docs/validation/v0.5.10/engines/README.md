# v0.5.10, part (f): the engine trial, isolation and plan

> **Status (2026-11-24): stopped for the maintainer before any engine was installed or run.**
> - **The stop:** Codex's round on part (f) returned `WEAKENED`
>   ([record](../../../plans/v0.5.10-consensus/README.md)). Its blocking item 9 changes the
>   scope: the planned TLS search, and exoVetter's odd/even and centroid outputs, overlap
>   quantities that v0.5.9 already recorded. Process diet 2, item 4, then calls it a rerun.
>   That needs the maintainer's approval or a dated amendment to the charter.
> - **The other blocking items** (1 to 5 and 8) are applied to this plan in the last section,
>   "After Codex's round".

**Exploratory.** Nothing here is a verdict, a candidate or a claim. Every output carries
`mode: exploratory` and `method_status: not_validated`, and the v0.5 limits label 'WEAKENED; does
not meet D1, D2, D4, T2a' where Refute's v0.5.9 records are used. This is a new diagnostic under
Process diet 2, item 4: it yields quantities no recorded run yielded (third-party engines'
metrics), is logged before it runs (`../log.jsonl`), and re-scores no recorded result.

## Isolation (the charter, part (f))

- **One environment:** `.cache/v0510/engines/venv`, created by uv with the uv-managed CPython
  3.12.15 (the CI's pinned 3.12 build). It is never the project's `.venv`, and `pyproject.toml`
  and `uv.lock` do not change.
- **The tools,** each pinned to an exact PyPI version uploaded at least 7 days before 2026-11-24
  (upload times read from PyPI on 2026-11-24):

  | Tool | Version | First upload |
  |---|---|---|
  | exovetter | 0.0.16 | 2026-04-27 |
  | triceratops | 1.1.0 | 2026-09-02 |
  | wotan | 2.1 (2.1.1 is 6 days old and excluded) | 2026-11-06 |
  | transitleastsquares | 2.3.0 | 2026-11-12 |
  | leo-vetter | 1.2.0 | 2026-07-29 |

- **The resolution:** [requirements.in](requirements.in) resolved to
  [requirements.txt](requirements.txt), 119 packages, every one pinned with its SHA-256 hashes:

      uv pip compile docs/validation/v0.5.10/engines/requirements.in --python-version 3.12 \
        --python-platform x86_64-pc-windows-msvc --generate-hashes --only-binary :all: \
        --no-binary fbpca --exclude-newer 2026-11-17T00:00:00Z --no-header \
        -o docs/validation/v0.5.10/engines/requirements.txt

  - `--exclude-newer 2026-11-17` keeps every package, the tools and their dependencies, at
    least 7 days old.
  - `--only-binary :all:` installs wheels only, so no package's build code runs.
  - The one exception is `fbpca` 1.0, a pure-Python dependency of lightkurve with no wheel on
    PyPI; its sdist is built (its hash is pinned).
- **The install** (in the isolated environment only):

      uv venv .cache/v0510/engines/venv --python 3.12.15
      uv pip sync --python .cache/v0510/engines/venv/Scripts/python.exe --require-hashes \
        --only-binary :all: --no-binary fbpca docs/validation/v0.5.10/engines/requirements.txt

  After the install, `uv pip freeze` of the environment is committed as `installed.txt` and
  compared with `requirements.txt`.
- **Licences:** [docs/sources/engines-licences-2026-11-24.md](../../../sources/engines-licences-2026-11-24.md)
  for the five tools and the GPL dependencies, and [licences.json](licences.json) for all 119
  packages, from PyPI metadata.
  - **GPL code:** leo-vetter (GPL-3.0+), its dependency batman-package (GPLv3), and pytransit
    (GPLv2, a dependency of triceratops). It is never imported by `src/refute`, never copied into
    the repository, and runs only in the isolated environment.
  - **LEO-Vetter** runs as a separate process, through a driver that imports it. That driver is
    **not** committed (the charter: "never imported into Refute's code"). It stays under
    `.cache/v0510/engines/`, is archived with its SHA-256, and the committed record gives its
    hash and the calls it makes.
  - **TRICERATOPS:** the committed driver imports `triceratops` (MIT), which imports `pytransit`
    (GPLv2) at run time. The driver runs as its own process in the isolated environment; no GPL
    file is copied or distributed.

## The targets and their data

- **Targets:** only the 24 TOIs of v0.5.9 (`../../v0.5.9/prototype-set.json`), all already
  exposed. No new target is looked at.
- **Data:** the SPOC 2-minute light curves and target pixel files listed in the v0.5.9 fetch
  units' manifests (`light_curve_manifest`, `tpf_manifest` in `../../v0.5.9/prototype-units.json`).
  - Each file is downloaded again from its recorded MAST URL by a committed fetch script, in the
    project's environment (no third-party code).
  - Each file is checked against the recorded SHA-256. A mismatch or a missing hash is recorded,
    and that file is not used.
  - The files live under `.cache/v0510/data/` and are deleted at the end, with a committed
    record.
- **The ephemerides:** each TOI's catalog values (period, epoch, duration, depth) as v0.5.9
  recorded them, the same input for every engine.
- **The TFOPWG disposition:** read from the NASA Exoplanet Archive's TOI table (`tfopwg_disp`),
  with the query URL and its date, for description only.
- **Catalog queries made by the tools:** TRICERATOPS queries the TIC and Gaia through
  astroquery.
  - Gaia data stay under `.cache` and are never committed: only TRICERATOPS's derived
    probabilities are.
  - Gaia's terms are restricted in this project's records (`docs/data-publication.md`).

## The engines and what each records

Every engine runs per TOI, as its own process, at BelowNormal priority on processors 8 to 31,
with at most 10 workers in business hours. Each run writes one JSON per TOI and engine, with:
- every metric;
- its pass or fail against the threshold the tool publishes (quoted with its source);
- the coverage;
- the failures, with the exception text;
- the CPU seconds.

| Engine | What it computes | Published decision rule used |
|---|---|---|
| wotan + transitleastsquares | detrending (biweight), then a TLS search; the period, epoch and SDE found, against the catalog ephemeris | TLS: SDE ≥ 9 (Hippke & Heller 2019) as detection; recovery = the catalog period, or a harmonic, within tolerance |
| exovetter | its vetters (ModShift, LPP, OddEven, TransitPhaseCoverage, SWEET, and the centroid vetter on the pixel files) | each vetter's threshold as given in exovetter's documentation or its cited paper |
| TRICERATOPS | FPP and NFPP from the light curve, the pixel aperture and the catalog neighbours | FPP < 0.015 and NFPP < 0.001: validated; NFPP > 0.1: likely a nearby false positive (Giacalone et al. 2021) |
| LEO-Vetter | its false-alarm and false-positive tests, and its final flags | the classification LEO-Vetter returns |

**Questions written before the run** (the charter, part (f)):
- **G1:** where Refute was INCONCLUSIVE, does each engine decide?
- **G2:** do the engines agree with each other?
- **G3:** how do they relate to the TFOPWG disposition? Description only, never a verdict.
- **G4:** the cost per TOI and per engine.
- **G5:** what each engine does when a metric cannot be computed (pass, fail or missing),
  recorded per metric.

## After Codex's round: changes to this plan (its blocking items 1 to 5 and 8)

They change no scope and take effect if part (f) resumes. The sections above are kept as
written.

1. **Verified artifacts.** Before installing, a committed manifest records, for each of the 119
   pins, the one wheel selected for Windows x64 CPython 3.12: its filename, PyPI URL, upload
   timestamp and SHA-256.
   - A missing, late (after 2026-11-17T00:00:00Z) or mismatched artifact is rejected.
   - The install then runs from that verified wheelhouse only: `--no-index --offline
     --require-hashes`.
   - The uv and CPython builds are recorded. `uv pip freeze` is a version check only.
2. **The `fbpca` build is sealed.**
   - Its exact sdist's build files and licence are inspected first.
   - The pinned `setuptools` is installed from its verified wheel.
   - `fbpca` is built offline with `--no-build-isolation` and no dependency resolution, and the
     resulting wheel joins the wheelhouse.
   - The hashes of the source, the backend and the wheel are recorded.
   - Any further build dependency is a stop (dependencies).
3. **No runtime fetch or shared cache.**
   - **Workers:** they run with the network denied by the operating system, a controlled import
     path, read-only verified inputs, and fresh private caches. That includes Numba, with no
     shared cache, and Astropy, with automatic IERS downloads off.
   - **No fetching:** no Lightkurve `search`/`download` call, and no TLS catalog helper.
   - **exoVetter's LPP** needs a remote `.mat` file. It is either a separately verified,
     hash-recorded local input with its terms checked, or recorded as unavailable.
   - **LEO-Vetter** runs its flux path only; its pixel metrics are recorded as unavailable.
     Adding `transitDiffImage`, `tess_stars2px` or FFI products changes scope and is a stop.
4. **TRICERATOPS without implicit data acquisition.**
   - Its aperture and WCS come from the hash-verified local pixel files.
   - The TIC and Gaia queries for the 24 fields are staged and logged before an offline run.
     Catalog neighbours are only hypotheses within the TOI's aperture.
   - No TRILEGAL fallback and no neighbour plots; only target-level FPP and NFPP are exported.
   - If the local path cannot keep the calculation, it is recorded as unavailable. Fresh
     cutouts or neighbour-level photometry are a stop.
5. **Both GPL chains behind one boundary.** A committed launcher exchanges file names and plain
   JSON with a private worker process.
   - The worker imports TRICERATOPS (and PyTransit), or LEO-Vetter (and batman), and stays
     outside the repository.
   - The wheels' own notices are recorded before any run.
   - PyTransit 2.2.0's metadata and `LICENSE` say GPLv2, while its tagged model headers say
     GPLv3-or-later (Codex's reading). This discrepancy goes into criterion 10, and no
     GPL-dependent implementation enters an Apache-2.0 adaptation proposal.
8. **Committed data and wording.**
   - **Export schema:** it excludes Gaia and TIC rows, neighbour IDs, star-indexed scenario
     tables, and catalog content in logs or exceptions. Gaia DR3's provenance, terms and the
     ESA/Gaia/DPAC credit are recorded.
   - **Outcome vocabulary:** each outcome is `threshold_met`, `threshold_not_met` or
     `unavailable`, with its coverage and the published threshold. A tool's native flags are
     kept as attributed observations. A degenerate FPP or a missing input is unavailable
     coverage.
   - **Wording:** "validated", "likely a nearby false positive" and "decide" do not appear in
     report-facing fields.
   - **Comparisons** are labelled exploratory and post hoc. The original E and S classes are
     kept, and G1 to G3 are descriptive, with no replacement class and no vote.
