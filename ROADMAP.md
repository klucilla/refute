# Refute Roadmap

This file is the single source of truth for project phases.
Agents working in this repo must read it before planning any work.

## How phases work

- **One phase at a time.** Each phase is planned and built in its own session.
  Never plan or build work from a future phase.
- **Every phase ends with a gate.** The next phase starts only when:
  1. All exit criteria of the current phase are met, with evidence.
  2. An independent review (fresh, read-only session) returns `SURVIVED`,
     or `WEAKENED` with every issue tracked as a GitHub issue.
- **Results are never tuned to pass a gate.** If a pre-registered claim fails,
  the failure is reported and analyzed, never hidden by changing thresholds,
  targets or data.

## Cross-cutting principles

These hold for every phase. They add no work to the current phase; they constrain
how later work is done.

- **"Everyone can use it".** The volunteer client (v0.7 Refute@Home) must work
  for non-technical users: one-click installers for Windows and macOS, no Python
  or terminal required, a graphical interface, Portuguese and English from day
  one, results explained in plain language, and nothing sent anywhere without
  explicit confirmation. Technical decisions in earlier phases must not block
  this.

## Current phase

**v0.2 Gauntlet**

---

## v0.1 Calibration

Prove the engine works by replicating published TESS planets.

**Scope**
- Repository setup: packaging, CI (no network), license, community files.
- Engine core: claim spec, lock/verify (SHA-256, TAMPERED detection), verdict
  model, domain pack interface (entry points), dossier writer, parallel runner.
- TESS pack: data adapter (lightkurve + MAST, local cache), BLS period search,
  gauntlet v0.1 (SNR, odd/even depth, secondary eclipse, duration plausibility,
  blind holdout by year), CTOI-oriented exporter (never submits).
- Calibration set: 10 confirmed planets observed in 2+ years, 3 known false
  positives, all traceable to authoritative sources.
- Self-claim locked before the first run.

**Exit criteria**
- [x] `ruff` and `pytest` pass in CI without network.
- [x] `refute calibrate` produces one dossier per target plus a summary.
- [x] Self-claim result reported honestly (pass or fail).
- [x] Any dossier can be reproduced with the commands it contains.

**Closed on 2026-10-07.** Gate review: WEAKENED, with both important findings
resolved ([docs/gates/v0.1-review.md](docs/gates/v0.1-review.md)). Self-claim
result: FAIL ([calibration/POSTMORTEM.md](calibration/POSTMORTEM.md)). Evidence:
[release v0.1.0](https://github.com/klucilla/refute/releases/tag/v0.1.0).

---

## v0.2 Gauntlet

Make the attacks serious and add independent review.

**Scope**
- Full TESS false-positive battery: centroid shift and nearby-star
  contamination (target pixel files), aperture-dependent depth, period alias
  checks, known eclipsing binary cross-match, systematics and momentum-dump
  checks.
- Independent reviewer protocol: a documented procedure and prompt for
  fresh, read-only agent sessions; reviewer report stored inside the dossier.
- Optional second reviewer from a different model family.
- Re-run calibration with the full battery under a new locked claim.

**Exit criteria**
- [ ] Every new test has synthetic positive and negative cases.
- [ ] Reviewer reports are stored and linked from dossiers.
- [ ] New calibration claim locked, run and reported.

---

## v0.3 Replicate papers (ML pack)

The original "Replica" idea: re-derive published results.

**Scope**
- Paper intake: arXiv ID or DOI plus public code and data.
- Claim extraction: an agent proposes claims in `claim.yaml`; a human must
  approve them before locking.
- Sandboxed reproduction from scratch (container), with resource limits.
- Robustness attacks: seeds, data splits, ablations, holdout.
- Paper verdicts: `REPRODUCED`, `FRAGILE`, `NOT_REPRODUCED`, `NOT_REPRODUCIBLE`.
- Right of reply: generated email draft for authors and a waiting period
  before any negative result is published.
- Scope limited to papers that run on consumer hardware.

**Exit criteria**
- [ ] 5 papers processed end to end, including at least one `NOT_REPRODUCIBLE`.
- [ ] Right-of-reply workflow documented and exercised.

---

## v0.4 Discover

Search for new candidates in TESS data.

**Scope**
- Target selection: stars with no registered TOI or CTOI.
- Multi-year stitching, long-period and single-transit search.
- Deduplication against current TOI and CTOI lists before reporting.
- Candidate ledger with full gauntlet and reviewer history.
- Exporter output with the parameters (period, epoch in BJD, depth in ppm and duration, with
  uncertainties) and supporting material a human needs for the publication path. A dossier is
  never uploaded to ExoFOP directly: since 2026-08-19 ExoFOP accepts community candidates only
  after peer-reviewed publication (or an RNAAS citing a peer-reviewed methodology) and with its
  approval. Publication path and exporter requirements: issue #18.

**Exit criteria**
- [ ] Injection-recovery test on real light curves (injected synthetic
      transits) with published recovery rates.
- [ ] Every surviving candidate has a complete, reproducible dossier.

---

## v0.5 Variable stars pack

Reuse TESS data to find and classify variable stars.

**Scope**
- Eclipsing binaries and pulsating stars: detection and classification.
- Cross-match with existing variable star catalogs.
- Exporter for the relevant community catalog submission format.

---

## v0.6 Mathematics pack

The purest form of refutation: counterexample search.

**Scope**
- Conjecture spec format with exact, machine-checkable predicates.
- Parallel counterexample search with verifiable certificates.
- Every reported counterexample re-verified independently.

---

## v0.7 Refute@Home (Swarm)

Volunteer computing.

**Scope**
- Work units, a lightweight coordinator and a worker client.
- Each unit runs on two independent workers; results must agree.
- Signed results and reproducibility checks.
- CPU and GPU workers (GPU-accelerated search where it pays off).
- AI-assisted triage that never decides verdicts.
- Evaluation of BOINC (the open-source platform behind SETI@home and
  Einstein@Home) versus a custom coordinator.
- The client follows the "Everyone can use it" principle (see Cross-cutting
  principles above).

---

## v1.0 Stable

- Stable claim spec and lock format, with a compatibility statement for PRML.
- Pack SDK, templates and documentation site.
- Governance and contribution model for community packs.
