Read CLAUDE.md, ROADMAP.md and README.md first. We are building Refute v0.1
("Calibration"). Plan ONLY this phase; future phases are listed in ROADMAP.md
for context, not for implementation.
Show me a plan first. Do not execute until I approve it.

GOAL OF v0.1
Prove the engine works by replicating published TESS planets, running a blind
holdout test, and producing a reproducible evidence dossier. No discover mode yet.
No AI reviewers yet.

1. REPOSITORY SETUP
- pyproject.toml (Python 3.12+, uv), package name "refute", CLI entry point "refute".
- LICENSE (Apache-2.0), CONTRIBUTING.md, CODE_OF_CONDUCT.md (Contributor Covenant),
  SECURITY.md, CITATION.cff.
- .gitignore (Python + .cache/ + dossiers/ outputs), .pre-commit-config.yaml
  (ruff + gitleaks).
- .github/workflows/ci.yml: ruff + pytest. CI must not use the network.
- Keep the existing README.md; only update it if something in the plan changes.

2. ENGINE CORE (domain-agnostic, src/refute/core/)
- Claim spec schema (claim.yaml) with validation.
- Lock: canonicalize claim + test plan, SHA-256, write a sidecar lock file.
  `refute lock <claim>` and `refute verify <claim>` (PASS / FAIL / TAMPERED,
  deterministic exit codes, documented).
- Verdict model with the verdict enums from CLAUDE.md.
- Domain pack interface (data adapter, search, gauntlet, holdout strategy,
  exporter), discovered via Python entry points so packs can live in other repos.
- Dossier writer: verdict JSON, Markdown report, plots, data hashes,
  environment lockfile, exact commands to reproduce.
- Parallel runner: ProcessPoolExecutor, default workers = os.cpu_count() - 2,
  configurable via --workers.

3. TESS DOMAIN PACK (src/refute/packs/tess/)
- Data adapter with lightkurve: download light curves from MAST, cache in .cache/,
  record data hashes.
- Period search with astropy BoxLeastSquares.
- Gauntlet v0.1 (each test deterministic, with documented pass/fail criteria):
  a. Signal-to-noise threshold
  b. Odd/even transit depth consistency
  c. Secondary eclipse search at phase 0.5
  d. Transit duration plausibility given the star's catalog parameters
  e. Blind holdout by year: hide one observing year, fit ephemeris on the others,
     predict transit times, check the hidden year ONLY at predicted windows.
     Repeat for each year available.
- Exporter: dossier summary formatted to help a human prepare an ExoFOP CTOI
  submission. It must never submit anything.

4. CALIBRATION SET
- Select 10 confirmed planets observed by TESS in at least 2 different years,
  and 3 known false positives (e.g., eclipsing binaries flagged as FP).
- Pull targets and published parameters ONLY from authoritative sources
  (NASA Exoplanet Archive and/or ExoFOP). Do not invent IDs or values.
  Record source URL and retrieval date in calibration/targets.yaml.
- Write and LOCK the self-claim BEFORE the first run:
  "Refute recovers at least 9 of 10 known TESS planets (period within 0.1%
   of the published value) and flags at least 2 of 3 known false positives."
- `refute calibrate` runs all targets in parallel and produces one dossier
  per target plus a summary.

5. TESTS
- Synthetic light curves with injected transits (known period, depth, duration)
  and injected eclipsing-binary signals. No network.
- Tests for: lock/verify/tamper, each gauntlet test, holdout logic, verdict
  aggregation, dossier generation.

AT THE END
- Run ruff and pytest and show me the results.
- Run `refute calibrate` on the real calibration set and show me the summary,
  including whether the locked self-claim passed or failed. If it failed,
  do NOT change thresholds or targets; report the failure honestly.
- Do not commit, push, or create remote resources without asking me.
