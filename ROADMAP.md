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

## Current phase

**v0.1 Calibration**

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
- [ ] `ruff` and `pytest` pass in CI without network.
- [ ] `refute calibrate` produces one dossier per target plus a summary.
- [ ] Self-claim result reported honestly (pass or fail).
- [ ] Any dossier can be reproduced with the commands it contains.

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
- Exporter output a human can use to prepare an ExoFOP CTOI submission.

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

---

## v1.0 Stable

- Stable claim spec and lock format, with a compatibility statement for PRML.
- Pack SDK, templates and documentation site.
- Governance and contribution model for community packs.
