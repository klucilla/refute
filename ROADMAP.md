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

**v0.2.1 Gauntlet fixes (resumed)**

Resumed on 2026-10-20 by the maintainer's decision, after v0.3 closed: after v0.3 the
focus returns to TESS. **v0.4 Discover** comes after it (the order decided on 2026-10-17;
the order of the sections below is unchanged, and no exit criterion of any phase changes).
The v0.2.1 work continues from branch `claude/v0-2-1-reopen` and reaches `main` only by
the maintainer's approval. Its exit criteria do not change, and the FAIL of the v0.2
calibration stays a valid result. Plan:
[docs/plans/v0.2.1-reopen-plan.md](docs/plans/v0.2.1-reopen-plan.md).

**History of the exception.**
- **v0.3 opened** on 2026-10-14 by the maintainer's decision, as an explicit exception to "How
  phases work". It was not an approved gate of v0.2.1: no v0.2.1 exit criterion was ticked,
  its population study was closed by a scope decision, and no gate review was run
  ([closure record](docs/validation/v0.2.1/population/closure-record.md)).
- **v0.2.1 reopened in parallel** on 2026-10-17, with v0.3 keeping the priority until its
  seal.
- **v0.3 closed** on 2026-10-20 with a gate review `WEAKENED` and its issues tracked (see its
  section). The limits that the parallel work kept while v0.3 was open ended with its seal:
  logical processors 0 to 7, and nothing under `src/`, `pyproject.toml` or `uv.lock` reaching
  `main`.
- **Gate rule.** The exception applied only to the transition from v0.2.1 to v0.3; the gate
  requirements of every later phase are unchanged.

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
- [x] Every new test has synthetic positive and negative cases. Evidence:
      [tests/test_battery.py](https://github.com/klucilla/refute/blob/v0.2.0/tests/test_battery.py),
      [tests/test_ebcatalog.py](https://github.com/klucilla/refute/blob/v0.2.0/tests/test_ebcatalog.py),
      [docs/gauntlet-tess-v0.2.md](https://github.com/klucilla/refute/blob/v0.2.0/docs/gauntlet-tess-v0.2.md).
- [x] Reviewer reports are stored and linked from dossiers. Evidence: 17 reports in the
      dossiers of the release asset `refute-v0.2-calibration.zip` (`review/` in each
      `MANIFEST.sha256`, linked from `report.md`); copies in
      [calibration/v0.2/results/20261009T155044Z-c9f341d2/reviews/](https://github.com/klucilla/refute/tree/v0.2.0/calibration/v0.2/results/20261009T155044Z-c9f341d2/reviews).
- [x] New calibration claim locked, run and reported. Evidence: lock
      [calibration/v0.2/self_claim.lock.json](https://github.com/klucilla/refute/blob/v0.2.0-calibration-lock/calibration/v0.2/self_claim.lock.json)
      (`refute verify` returns `PASS` at tag `v0.2.0-calibration-lock`, commit `cc9d104`),
      run [summary.json](https://github.com/klucilla/refute/blob/v0.2.0/calibration/v0.2/results/20261009T155044Z-c9f341d2/summary.json),
      report [calibration/v0.2/POSTMORTEM.md](https://github.com/klucilla/refute/blob/v0.2.0/calibration/v0.2/POSTMORTEM.md).

**Closed on 2026-10-11.** Gate review: Claude's gate verdict: WEAKENED; Codex
provided a second review but did not assign a gate verdict
([docs/gates/v0.2-review.md](docs/gates/v0.2-review.md)). The closing requirement
asked for the problems of a WEAKENED gate to be recorded in issues; instead, the
important findings (rows 4, 5 and 7) were fixed before the close (commits 4c6d805
and f479823, and tag v0.2.0-calibration-lock), and every finding has its resolution
in docs/gates/v0.2-review.md. Self-claim result: FAIL. Planets recovered: 10 of 10
(required at least 9); false positives flagged without `eb_catalog`: 7 of 10
(required at least 6); planets refuted: 4 of 10 (required at most 1)
([calibration/v0.2/POSTMORTEM.md](calibration/v0.2/POSTMORTEM.md)). Evidence:
[release v0.2.0](https://github.com/klucilla/refute/releases/tag/v0.2.0), archived
on Zenodo with version DOI
[10.5281/zenodo.23301001](https://doi.org/10.5281/zenodo.23301001) and concept DOI
[10.5281/zenodo.23301000](https://doi.org/10.5281/zenodo.23301000).

---

## v0.2.1 Gauntlet fixes

Fix what the failed v0.2 calibration exposed, and test the changes with a new
pre-registered calibration. The goal is to measure correctly, not to raise a count:
if the honest count of flagged false positives falls, that is a result.

Requirements fixed by the maintainer on 2026-10-09, recorded here on 2026-10-11,
before any v0.2.1 lock or result.

**Scope**
- Order: hypothesis 7 (signal identity) comes first, before any evaluation of
  performance.
- Calibration measure: a known false positive counts as flagged only if the analyzed
  signal is the catalogued one (hypothesis 7 of the v0.2 post-mortem).
- Blind holdout: a round with an invalid train candidate is INCONCLUSIVE, using only
  that round's train data and the claim's parameters; a test shows that changing the
  hidden-year data changes no decision taken before the windows are read; the
  directed mode (published period) stays separate from the general mode (hypothesis
  4 of the v0.2 post-mortem). A round whose expected SNR, from the train depth and
  the hidden-year noise, is near or below `min_snr` is INCONCLUSIVE, not FAIL;
  whether a FAIL also requires the measured hidden depth to be inconsistent with the
  train prediction is decided in its acceptance criteria (hypothesis 1 of the v0.2
  post-mortem). Transit times measured with an ingress model, so that the timing
  error is realistic (hypothesis 3 of the v0.2 post-mortem). Robust stacking of
  window depths (issue #35) and the error model of a round (hypothesis 2 of the v0.2
  post-mortem; issue #35).
- `eb_catalog`: a period match under the target's own TIC in a catalog built from
  the same TESS photometry is a warning, not a fatal failure (hypothesis 9 of the
  v0.2 post-mortem).
- Engine: the number of workers should change only the execution, preserving the
  scientific results (workers-equivalence test; numerical runtime recorded in every
  dossier); the environment leak of `init_worker()` with one worker (issue #32, to
  be decided); a coverage requirement fixed before the lock: how many targets and
  holdout rounds must give a conclusive result, with INCONCLUSIVE kept in the
  denominators.
- CI: at most 15 minutes per job (maintainer's target).
- Documentation: how blind the holdout is, in the documentation and in the report
  sentence of every dossier, changed under the new lock (issue #23); AI use
  statement and what the blind holdout does and does not prove (issue #14).
- Process: every legal or license statement has a URL, a date and a stored literal
  excerpt (issue #34); evaluate redistributing the TESS-EB snapshot (issue #33).
- The self-claim of the new calibration (targets, numbers and thresholds) is defined
  in the v0.2.1 protocol before the lock.
- The calibration report states every definition change since v0.2 (hypothesis 7
  changes "flagged"; hypothesis 9 changes "refuted").
- Synthetic scenes are idealized: synthetic numbers compare engine versions and test
  known mechanisms; they set no bounds for real data.
- The v0.2 calibration is never re-locked or re-run.
- Hypotheses of the v0.2 post-mortem and open items not listed here are not part of
  v0.2.1. Hypotheses 6, 10, 11(a), and 8 with 12, enter only if their validation is
  ready before the protocol; 8 and 12 also need the adversarial case of a planet
  with a persistent systematic bias toward a neighbor, using each sector's
  pixel-to-sky transform.

**Population study closed by a scope decision on 2026-10-14**, without a demonstration
that approval was impossible
([closure record](docs/validation/v0.2.1/population/closure-record.md)):
- M0 to M3: FAILS on the development population, with full integrity.
- Confirmation: not run; no drand round was declared.
- M4 and M5: not implemented, not measured.
- Proposed corrections: hypotheses and plans, with 6 of the 9 rows of their last revision
  still open.
- The calibration population of the corrections plan: never generated nor analyzed.

The exit criteria below are not met and none is marked done. Each pending criterion is
**deferred**, with its reason; no gate is scheduled.

**Exit criteria**
- [ ] Every change has acceptance criteria, metrics and regression cases committed
      before its tests and code, and synthetic cases that must pass and must fail,
      including correlated noise.
      *Deferred.* The changes made in v0.2.1 (H7, H4, H9(a), workers equivalence, CI
      option D) have acceptance records committed before their tests and code
      (`docs/validation/v0.2.1/*-acceptance.md`); whether each one covers correlated
      noise was not audited at the closure. The TESS corrections never reached that
      stage (6 open rows).
- [ ] A synthetic population study with known truth measures, before and after each
      change, the rate of refuted planets, the rate of flagged false positives, the
      false-alarm rate on noise-only light curves (white and correlated) and the
      INCONCLUSIVE fraction; its metrics and acceptance limits are committed before
      it runs.
      *Deferred.* The study and its limits were committed before it ran, and M0 to M3
      were measured (FAILS); the measurement after the remaining changes (M4, M5)
      belongs to the deferred TESS corrections.
- [ ] Synthetic seeds and scenarios are split, before use, into a development set
      and a confirmation set; the confirmation set, with seeds derived from a future
      drand round, runs once, at the end, on frozen code, and only its result counts
      as validation.
      *Deferred.* The split is declared (the development prefix and the confirmation
      rule of the population study, section 5); the confirmation never ran and no drand
      round was declared. Nothing of v0.2.1 counts as validated.
- [ ] No synthetic test that passes at the start of v0.2.1 fails at its end without
      a justification written before.
      *Deferred.* It can be checked on the suite against the baseline of the population
      study, section 12; it was not checked at the closure of the study.
- [ ] No threshold is set, tuned or checked on a known target or on real data; every
      target used in the v0.1 and v0.2 calibrations, including development targets,
      is used only for declared debugging.
      *Deferred.* The rule stays in force. The population study used synthetic data
      only, and the development runs on real targets are declared in
      `docs/validation/v0.2.1/pre-document-runs.md`; no audit was made at the closure.
- [ ] New thresholds are in the code and in the gauntlet documentation before the
      protocol of the new calibration.
      *Deferred.* No protocol of a new calibration was written; this applies when one
      is.
- [ ] The workers-equivalence test passes and the coverage requirement is defined,
      both before the v0.2.1 lock.
      *Deferred.* There is no v0.2.1 lock. The workers-equivalence test exists and runs
      in CI (`docs/validation/v0.2.1/workers-equivalence-acceptance.md`); the coverage
      requirement was never defined (population study, "Still to fix before the v0.2.1
      lock").
- [ ] New pre-registered calibration (new lock of protocol, code, dependencies and
      claim; newly drawn targets, excluding every target used in the v0.1 and v0.2
      calibrations, including development targets), run and reported, even if it
      fails.
      *Deferred.* Its prerequisite, a population study approved on frozen code, was not
      reached; a new calibration now would test code that failed the synthetic
      criteria.
- [ ] If the new calibration fails, the maintainer records an explicit decision;
      there is no automatic new attempt.
      *Deferred* with the new calibration. The closure record is the maintainer's
      explicit decision about the population study.
- [ ] Reviewer reports stored and linked from the dossiers of the new calibration,
      as in v0.2.
      *Deferred* with the new calibration.
- [ ] Every issue of milestone v0.2.1 closed, or moved to a later milestone with the
      reason stated.
      *Deferred.* Six issues were open at the closure of the study (#14, #23, #32, #33,
      #34, #35); each is closed or moved, with its reason, by a decision of the
      maintainer. #35 (robust stacking and the error model of a round) belongs to the
      deferred TESS corrections.

**Deferred work, with no target version**
- **TESS corrections** (holdout capacity and FAIL rule, correlated noise, timing with an
  ingress model, prewhitening, `period_alias`): deferred with no target version. Input:
  revision 3 of the corrections plan and its 6 open rows
  ([corrections plan](docs/validation/v0.2.1/population/corrections-plan/README.md)),
  under the resumption conditions of the closure record.
- **Directed mode** of the holdout (a claimed ephemeris): a separate pending item, outside
  the TESS corrections and their budget (corrections plan, revision 3, Appendix A).

Neither moves to v0.3 automatically; v0.3 is unchanged.

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

**Exit criteria** (changed on 2026-10-14 by the maintainer, before any selection;
plan: [docs/plans/v0.3-plan.md](docs/plans/v0.3-plan.md))
- [x] 5 papers processed end to end (the main sample), with every verdict path,
      including `NOT_REPRODUCIBLE`, shown to be handled correctly by a controlled
      test (an artifact built to be non-reproducible), whether or not the real
      sample contains one.
- [x] Right of reply: the notification was made and recorded; the reply period
      remains open.

**Closed on 2026-10-20: gate review `WEAKENED`**, with every issue it named tracked
(#47, #159, #160, #161, #162). Both criteria are met as written. The weaknesses:
- the reviews of 2309.15704 are held until its reply period ends;
- no reviewer checked the inventories or the triage;
- four of the five papers were locked with claims that could not be decided;
- some WP4 acceptance rows are not covered;
- some deviations from the plan were recorded only at the gate.

Record: [calibration/v0.3/main/gate/README.md](calibration/v0.3/main/gate/README.md).

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
- Discovery performance needs a requirement of its own; closing v0.2.1 is not enough.

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
