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
- **Advance rule (the maintainer's decision of 2026-11-05).** A new capability phase starts only
  after the current line of work succeeds: every declared target either PASSes or is shown to be
  infeasible with the available data (one infeasibility record per such target, with evidence,
  reviewed by Codex and by an independent review, approved by the maintainer). Until then, the next phase is a
  correction phase on the same line (v0.5.1, v0.5.2, ...). Each correction round has its own
  pre-registration, targets fixed before code, a fresh confirmation set never used in
  development, caps and a stop rule; a round's targets are never relaxed after its results. After
  three correction rounds without success, the maintainer decides between a change of approach,
  an infeasibility record, or a pause. *(Clarified by the maintainer on 2026-11-05: every
  declared target that does not PASS needs its own infeasibility record.)*

## Cross-cutting principles

These hold for every phase. They add no work to the current phase; they constrain
how later work is done.

- **"Everyone can use it".** The volunteer client (v0.8 Refute@Home; numbered v0.7 until
  2026-11-03) must work
  for non-technical users: one-click installers for Windows and macOS, no Python
  or terminal required, a graphical interface, Portuguese and English from day
  one, results explained in plain language, and nothing sent anywhere without
  explicit confirmation. Technical decisions in earlier phases must not block
  this.

## Current phase

**v0.5.2 Battery corrections, round 2: to be scoped (not started)**

- **Why.** v0.5.1, correction round 1 of at most 3, closed as not approved; every failed target of
  v0.5 stays outstanding. By the advance rule (above), the next phase is a correction phase on the
  same line. Its section: "v0.5.2 Battery corrections, round 2" below. No code before its scope is
  decided by the maintainer.

### Previous phase record: v0.5.1 Battery corrections

**v0.5.1 Battery corrections: closed on 2026-11-08 as not approved** (the maintainer's decision of
2026-11-08, #208; [closing record](docs/validation/v0.5.1/closing-record.md))

- Closed before its confirmation by stop rule 6 of its plan: no target passed or was declared
  infeasible, and all stay outstanding. It counts as the first of the three correction rounds of
  the advance rule. No confirmation data was used, and no drand round was drawn.
- A0 and WP3 (b) ran their acceptances once and were not accepted; the other acceptances did not
  run. No gate review was run, and no exit criterion is ticked.
- **Method status.** No method is validated: every v0.5.1 output carries
  `method_status: not_validated`.

### Previous phase record: v0.5 Stronger tests

**v0.5 Stronger tests: closed on 2026-11-05 as `WEAKENED`** (the maintainer's decision of
2026-11-05, #199)

- **Gate.** All eight exit criteria are met, criterion 6 with one recorded deviation; they are
  ticked with their evidence in the v0.5 section. The first gate review (2026-11-05) returned
  `REFUTED` (criterion 7 not yet applied); after its findings were answered, the second gate
  review returned `WEAKENED`, with its issues open and tracked. Both reports, as they came out,
  and the dossiers they were given: [calibration/v0.5/gate/](calibration/v0.5/gate/).
- **Results.** Reported as they came out, pass or fail: the synthetic confirmation (C1), the
  paired real-data benchmark (C2) and the newly drawn real controls (C3), in
  [calibration/v0.5/runs/](calibration/v0.5/runs/); the failed targets (D1 EB1/EB2, D2, D4, T2a)
  are recorded as results, with no rerun and no retuning. The trade-off and its numbers:
  [calibration/v0.5/results/closing-record.md](calibration/v0.5/results/closing-record.md).
- **Still open:** the release v0.5.0 and its texts, after the maintainer's approval; the issues
  the second gate listed: #201, #202, #203, #204, #200 (with #183), #206, #195 (item 4), #205,
  and the scope issues kept open (#184, #182, #181, #191, #180, #9, #192) or moved (#176).
- **Method status.** No method is validated: every v0.5 output carries
  `method_status: not_validated`.
- **What the gate verdict covers.** It is about the phase's completeness, never about any
  candidate.

The opening record of v0.5, kept as it was:

- **Decision.** The maintainer's decision of 2026-11-03: v0.5 is the phase of stronger tests, from
  the findings of the v0.4 pilot (#176, #179 to #196, plus #9, #12, #195, #196). The maintainer
  delegated the scope, and the renumbering of the later phases, to a consensus between Claude
  and Codex, taken on 2026-11-03 (the consensus record is in the tracking issue, #199).
- **Plan and scope:** [docs/plans/v0.5-plan.md](docs/plans/v0.5-plan.md), with its caps and its
  stop rule; acceptance documents, written before any code:
  [docs/plans/v0.5-acceptance.md](docs/plans/v0.5-acceptance.md).
- **Renumbering.** v0.5 Stronger tests is inserted; the variable stars pack becomes v0.6, the
  mathematics pack v0.7 and Refute@Home v0.8. Each moved section keeps its text, with a note.
- **Method status.** No method is validated: every v0.5 output carries
  `method_status: not_validated`.

### Previous phase record: v0.4 Discover (pilot with a funnel)

The text below is kept as it was at the close of v0.4. Since then the release v0.4.0 was
published (2026-11-03, https://github.com/klucilla/refute/releases/tag/v0.4.0).

**v0.4 Discover (pilot with a funnel): closed; exit criteria met and published (P7); release v0.4.0 pending**

- **Gate.** The v0.4 exit criteria are met. The independent gate review of 2026-11-01 (the seventh reviewer session) returned `SURVIVED`, and the criteria are ticked with their evidence in the v0.4 section. Both gate reviews are published in [docs/gates/v0.4-review.md](docs/gates/v0.4-review.md).
- **Publication (P7), done by the maintainer's steps of 2026-11-02 and 2026-11-03 (UTC):** the two Zenodo records (https://doi.org/10.5281/zenodo.23874043, the reproduction inputs; https://doi.org/10.5281/zenodo.23898648, the five stage-2 dossiers), the results in [calibration/v0.4/results/](calibration/v0.4/results/README.md), the results comment on #177 and a note on each of #179 to #194.
- **Still open:** the release v0.4.0 and its version bump (P7, last step), after the maintainer's approval; the live re-read of VizieR's rules page, while the CDS does not answer (L9 of [calibration/v0.4/sources/data-licenses-2026-11-01.md](calibration/v0.4/sources/data-licenses-2026-11-01.md)).
- **v0.5 is not open.** It awaits the maintainer's decision.
- **Opening and scope.** v0.4 opened on 2026-10-29 by the maintainer's decision, as a pilot of complete, auditable cases. Its scope amendments are recorded in its section below: amendments 1 to 5 and the funnel amendment of #9. Tracking: issue #177.
- **Method status.** No method is validated: every v0.4 report carries `method_status: not_validated`.
- **What the gate verdict covers.** It is about the phase's completeness, never about any candidate.

### Previous phase record: v0.2.1 Gauntlet fixes (resumed)

**Ended as not approved on 2026-10-27, by the maintainer's decision**, with the hypotheses recorded
([closing record](docs/validation/v0.2.1/closing-2026-10-27.md)): no gate review passed and no exit
criterion is met or ticked. v0.4 Discover, next in the order decided on 2026-10-17, opened on
2026-10-29 by the maintainer's decision (above). The text below is kept as it was.

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

**Scope amendment B (adopted on 2026-10-23, by the maintainer).** The validation of v0.2.1 is
restricted to one **profile proposed for validation**, `three-observing-years/1`: light curves
inside an **operational domain** defined by quantities read before any hidden flux is accessed
(exactly three observing years, one sector in each, two-minute cadence, the sectors' coverage and
the spacings between the years, within declared tolerances; the population study's
[Amendment B](docs/validation/v0.2.1/population-study.md)). It becomes a validated profile only
when its confirmation and its replication succeed; a curve's membership is not demonstrated
performance, and a note in a dossier does not make the profile validated. Curves outside the
domain are reported INCONCLUSIVE ("outside the validated scope") under the profile, with each
available test result kept in the dossier as a diagnostic of no verdict value. The synthetic
population study is run on a new population generated for this domain (`population_v4`; the
earlier generators unchanged), with the sizes, criteria and acceptance counts of the population
study's Amendment B, fixed before any new result. The original four-group population study and its
FAILs (development campaign 1, M0 to M3), the R_min study, and stage 1's development readings are
kept as results; this amendment does not make them a success, and the original claim stays not
validated. A widening beyond the domain (the timing rule's T4, the undetermined hidden noise, other
geometries) is future work with its own specifications. The plan, its gates and its budget:
[plan B](docs/validation/v0.2.1/reopen/stage-1/plan-b/README.md) (frozen on adoption; optional
improvements go to the backlog, and only a problem of validity, safety or execution reopens it).

**Plan B ended on 2026-10-27, by the maintainer's decision**
([closing record](docs/validation/v0.2.1/reopen/stage-1/plan-b/closing-2026-10-27.md)). Its gate
3b (the real controls' availability) did not reach its minimum: in the metadata screening, 11
confirmed planets and 0 known false positives inside the domain D1 to D5, against 20 + 20
([gate 3b](docs/validation/v0.2.1/reopen/stage-1/real-controls/gate-3b.md)). That result and its
block, every FAIL and every criterion are preserved; X2f never ran, and no lot of plan B ran. A
viability diagnosis informed the next step
([report](docs/validation/v0.2.1/reopen/stage-1/viability-3b/report.md), with its
[corrected readings](docs/validation/v0.2.1/reopen/stage-1/viability-3b/readings-corrected.md)).
**Next:** one comparative viability package, prepared for the maintainer's authorization
([package](docs/validation/v0.2.1/reopen/stage-1/viability-cd/README.md)); after its screening the
maintainer chooses an executable proposal within the ceiling, or ends v0.2.1 as not approved. No
new domain, generation, T4 or lot is authorized.

**The package ran and v0.2.1 ended as not approved on 2026-10-27, by the maintainer's decision.**
Its lot ([report](docs/validation/v0.2.1/reopen/stage-1/viability-cd/report.md); issue #173): C
(three years) and D (four or five years) both INDETERMINATE by the rule fixed before the lot (no
holdout FAIL); the step over specification C's twelve error-model pairs met the PASS rule with no
pair, so by the investment rule the effort ended. The hypotheses for future research are recorded
in the [closing record](docs/validation/v0.2.1/closing-2026-10-27.md); this is not a proof of
infeasibility, and every result, FAIL and criterion is preserved.

**The exit criteria under amendment B.** Their wording is unchanged. Under the amendment, the
synthetic population study, its confirmation and the new calibration are those of the profile (the
calibration's targets drawn inside the domain), and the phase closes only after the calibration,
its dossier reviews and every other exit criterion.

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
  approval. Publication path and exporter requirements: issue #18. *(Amendment 5: in the pilot
  the duration goes without an uncertainty, with a justified absence.)*
- Discovery performance needs a requirement of its own; closing v0.2.1 is not enough.

**Scope amendment (adopted on 2026-10-29 by the maintainer's decision; tracking #177).** v0.4
opens as a pilot of complete, auditable cases: two known controls (one confirmed planet, one
known false positive) and a funnel over N = 50 stars with no TOI, CTOI or confirmed planet (100
only by a rule fixed before the selection, within the phase caps), drawn by a rule fixed before
the selection, with at most three promoted exploration cases. Success depends on completeness,
reproducibility and review, never on a discovery; zero promoted stars is an acceptable outcome.
The scope items above stay listed; the amendments say which are deferred or resized.
- **Funnel.** Stage 1 runs the light-curve tests on all N stars; tests that need pixel files are
  reported INCONCLUSIVE with zero coverage at that stage, never PASS. Stage 2 (pixel files and
  the full battery) runs only for promoted stars and controls, by a promotion rule fixed in the
  protocol, with no replacement of a star that falls at stage 2. Every scanned star is recorded
  in the case ledger, and the promotion is recorded apart from the verdict.
- **Amendment 1.** Long-period search beyond the current reach (`period_max_days` 20 d; stage 1
  up to half a sector) is deferred until after the pilot, with its own synthetic validation.
- **Amendment 2.** Single-transit search is deferred until after the pilot, with its own
  synthetic validation.
- **Amendment 3.** The discovery-performance requirement of the pilot is the injection-recovery
  rates and the detection counts on transformed (inverted, and cyclically rotated within each
  sector) curves, measured on the pilot's real light curves and published per curve with
  denominators, intervals and the declared scope ("these curves, this code"). The rotation
  within each sector replaced block shuffles at P1 (the maintainer's decision of 2026-10-29),
  because moving data between sectors cannot keep each sector's pixel geometry and metadata. Detections on transformed curves are not a real
  false-alarm rate, and the result is not a general performance claim.
- **Amendment 4.** Injection-recovery is resized to the pilot: injection before detrending into
  the N funnel light curves (#175). Without pixel files it measures search, gate and stage-1
  triage, not survival of the full battery.
- **Amendment 5 (2026-10-29, the maintainer's decision; #176 stays open).** In the pilot the
  exporter gives the duration without an uncertainty, with a justified absence that cites the
  method `trapezoid-least-squares-1` as not accepted: its acceptance failed (coverage of the
  68 % interval 0.54 and 0.55 at SNR 20 and 40, against a band of 0.61 to 0.74;
  [record](docs/validation/v0.4/wp4-duration-acceptance.md)). The FAIL stays recorded and
  visible; no other method is tried in this phase. Phase acceptance criterion 8
  ([v0.4-acceptance.md](docs/plans/v0.4-acceptance.md)) is met by that justified absence.
- **Funnel amendment of #9.** On the N stars, transformed curves go through the light-curve
  tests; the full battery runs only where pixel files exist (promoted stars and controls);
  denominators are kept separate (eligible, promoted by the cap, survivors); a missing test
  never counts as passed.
- The blind holdout is a diagnostic, not a decisive test, in v0.4 claims (#174): it never changes
  a verdict; `temporal_diagnostic` and `method_status: not_validated` are reported in every
  dossier, export and ledger entry. Earlier locks and verdicts are unchanged.
- Every case, with or without a candidate, has a complete, reproducible dossier.

**Exit criteria**
- [x] Injection-recovery test on real light curves (injected synthetic
      transits) with published recovery rates. *(Amendment 4: on the pilot's funnel curves.)*
      Evidence: `calibration/v0.4/runs/stage1/measurements.json` (commit 0ed4075): 100 funnel
      curves, 20 injections each, per-curve counts, denominators and Wilson 95 % intervals, with
      the sampling unit declared. Published in `calibration/v0.4/results/report-4.md`
      (injection-recovery per curve) and in the results comment on #177.
- [x] Every surviving candidate has a complete, reproducible dossier. *(Amendment: every case,
      with or without a candidate.)* Evidence:
      - complete: the case files (zero missing items) and the case ledger, anchored by hash in
        `calibration/v0.4/runs/p5_anchor.json` (ed314c1) and `p5_anchor-2.json` (bac3300);
      - reproducible: the five stage-2 dossiers were reproduced from corrected instructions
        that supersede the core's `REPRODUCE.md` without amending acceptance criterion 2 (the
        core file is written by the locked `run.py`; #189). The run used a clean clone at
        commit 95cd7d9 (CI green) and a fresh download, with nothing placed by hand; the
        approval was recorded in #177 before the run. The inputs a clone lacks are pinned by
        `calibration/v0.4/runs/reproduce_archives.json`.
      - published (P7): the five stage-2 dossiers, each with every annex, in
        https://doi.org/10.5281/zenodo.23898648; the inputs a clone lacks, with the hashes of
        `reproduce_archives.json`, in https://doi.org/10.5281/zenodo.23874043; the report, the
        case ledger (429 events) and the anchor details in `calibration/v0.4/results/`
        (commit 0b08c1c), each with the SHA-256 its P5 anchor committed. The current
        instructions are the annex `reproduce-4` (commit 6143c11: `prepare` asks the CDS and then
        VizieR's mirrors, and a `git diff` checks the locked code and records against 95cd7d9); a
        rehearsal of `prepare` only passed at 6143c11 on 2026-11-02 (`p5_anchor-6.json`). No new
        full reproduction was run.

**Gate.** The second independent gate review (the seventh reviewer session, 2026-11-01) returned `SURVIVED`: every acceptance
item MET and no critical or important finding. The first returned `REFUTED` (criteria 2 and 9),
and its findings were answered (#177, #179 to #195). Both reports are published in
[docs/gates/v0.4-review.md](docs/gates/v0.4-review.md) (an English translation; the second
review's original is in `docs/gates/v0.4-review-2.pt.md`, and the first's is cited by hash in
`calibration/v0.4/results/anchor-3-detail.json`).

**Publication (P7).** Done, by the maintainer's steps (#177):
- the Zenodo records https://doi.org/10.5281/zenodo.23874043 and
  https://doi.org/10.5281/zenodo.23898648 (2026-11-02);
- the results and the gate reviews in the repository (commit 0b08c1c, 2026-11-02);
- the results comment on #177 and a note on each of #179 to #194 (2026-11-03 UTC).

Still to do: the release v0.4.0 with its version bump, after the maintainer's approval. The live
re-read of VizieR's rules page stays open while the CDS does not answer; the publication rests on
L9 of `calibration/v0.4/sources/data-licenses-2026-11-01.md`.

**Release.** Done: v0.4.0 was published on 2026-11-03
(https://github.com/klucilla/refute/releases/tag/v0.4.0).

---

## v0.5 Stronger tests

Make the battery able to say INCONCLUSIVE when a test could not have failed, and able to refute
the spurious-signal families the v0.4 pilot exposed; measure the change against the v0.4 battery
on the same curves.

Opened on 2026-11-03 by the maintainer's decision. The scope and the renumbering of the later
phases were delegated by the maintainer to a consensus between Claude and Codex, taken on
2026-11-03 (record in the tracking issue, #199). Plan, caps and stop rule:
[docs/plans/v0.5-plan.md](docs/plans/v0.5-plan.md); acceptance documents:
[docs/plans/v0.5-acceptance.md](docs/plans/v0.5-acceptance.md).

**Scope** (the plan's work packages; WP5 and WP9 are optional and are dropped first)
- Sensitivity rule (#185): a fatal or warning test PASSes only when it could have detected its
  declared minimum effect; otherwise INCONCLUSIVE, with the sensitivity reported.
- Signal versus noise (#184, #193): single-event dominance, per-event consistency, events at
  segment edges; the transformed-curve comparison in the report (descriptive).
- Variability (#182, #181): a two-sided phase-0.5 check, a sinusoid test on the undetrended flux,
  a duty-cycle bound.
- Centroid per sector (#183, #187, #190): a fatal FAIL needs consistent offsets from at least two
  qualified sectors; the FAIL worded as a measurement; the blend caveat in every report.
- Shape and depth stability (#191), optional.
- Reporting and exporter fixes (#179, #186, #190, #193, #194).
- Measurement fixes (#180, #188, #9 report part).
- Reproducibility and hygiene (#189, #195, #196); tests leave no `.cache/test-*` folder.
- Duration uncertainty, one bounded attempt (#176), optional.
- Calibration, pre-registered: a synthetic population study (confirmation set run once, seeds from
  a future drand round); the v0.4 funnel's curves as a reused, paired benchmark (transformed
  curves and injections); newly drawn real controls with the full battery.
- Not in scope: statistical validation and third-party vetters (#12), a validated null (#9), the
  difference-image centroid (#11), the holdout corrections, new discovery runs, the variable
  stars pack.

**Exit criteria** (detail and evidence rules in the plan, section 5; closed on 2026-11-05 as
`WEAKENED`, see "Current phase")
- [x] Every new or changed test has its acceptance section committed before its tests and code;
      its synthetic cases (must pass, must fail, sensitivity, coexistence, sabotage, correlated
      noise) run with counts from a JUnit XML file; each test accepted (decisive) or recorded as
      failed (diagnostic only).
      *Evidence:* the acceptance documents (`559eaf0`) before the first code (`0deb97f`); the
      acceptance run and its roles ([README](docs/validation/v0.5/acceptance/README.md)); its 133
      rows counted from a JUnit XML (133, 11 failures, 3 skipped;
      [criterion2/README.md](calibration/v0.5/results/criterion2/README.md)).
- [x] No synthetic test that passes at the start of v0.5 fails at its end without a written
      justification made before; historical claims give their recorded verdicts and hashes.
      *Evidence:* the v0.4.0 baseline (4,176 passing tests) against the final suite (4,538 tests,
      0 failures, 0 errors, 91 skipped), the two timestamp-dependent IDs explained; the historical
      locks 8 of 8 PASS and the v0.5 compatibility tests
      ([criterion2/](calibration/v0.5/results/criterion2/README.md)).
- [x] No fatal or warning test of the v0.5 battery can PASS without its declared sensitivity
      (engine rule, shown by a sabotage case).
      *Evidence:* `tests/test_sensitivity.py` (sabotage cases), `tests/test_v05_battery.py`,
      passing in the final suite.
- [x] The synthetic confirmation set run once on frozen code and reported, pass or fail.
      *Evidence:* C1, once, round 6613448
      ([runs/c1-confirmation/](calibration/v0.5/runs/c1-confirmation/)): D1 EB1 and EB2 FAIL,
      D2 FAIL, D4 FAIL; the others PASS, NW not decidable.
- [x] The paired real-data measurements (reused benchmark and new controls) locked, run and
      reported, pass or fail, with reviewer reports for the dossiers the protocol draws.
      *Evidence:* C2 (T2a FAIL; T2b, T2c PASS) and C3 (T3a, T3b PASS)
      ([runs/](calibration/v0.5/runs/)); four independent reviews of the dossiers drawn by
      [reviews/RULE.md](calibration/v0.5/reviews/RULE.md), each objection mapped to an issue.
- [x] One new-control dossier reproduced in a clean clone from the generated instructions alone;
      the empty-checkout test runs in CI.
      *Met with one recorded deviation:* the TESS-EB table was placed from an official VizieR
      mirror, verified by the claim's content hash, while the CDS did not answer
      ([reviews/criterion6/](calibration/v0.5/reviews/criterion6/), #206); criterion 6 as written
      requires nothing placed by hand. The empty-checkout test runs in CI.
- [x] Every scope issue closed, kept open with the part left, or moved with its reason; no
      `.cache/test-*` folder remains after the suite.
      *Evidence:* [results/criterion7.md](calibration/v0.5/results/criterion7.md) (12 closed, 8
      kept open, 2 moved); none left after the final suite.
- [x] Gate: an independent review returns `SURVIVED`, or `WEAKENED` with its issues open.
      *Evidence:* the second gate review, `WEAKENED`, with its issues open and tracked
      ([gate/gate-2-report.md](calibration/v0.5/gate/gate-2-report.md)).

---

## v0.5.1 Battery corrections

A correction phase on the line of v0.5, by the advance rule (the maintainer's decision of
2026-11-05). Opened on 2026-11-06 by the maintainer's decision; the scope delegated to a Claude and
Codex consensus, taken the same day (record: [docs/plans/v0.5.1-consensus/](docs/plans/v0.5.1-consensus/README.md)).
Plan, caps and stop rule: [docs/plans/v0.5.1-plan.md](docs/plans/v0.5.1-plan.md). Tracking: #208.
Correction round 1 of at most 3.

**Closed on 2026-11-08 as not approved, before its confirmation** (the maintainer's decision; plan,
amendment 11; [closing record](docs/validation/v0.5.1/closing-record.md)). The exit criteria below
are kept as written and none is ticked.

**The targets** (v0.5's definitions, measured the same way; none relaxed): D1 for EB1 and EB2
(synthetic eclipsing binaries still survive, #202); D2 and D4 (planets lost to INCONCLUSIVE, #201);
T2a (injected planets kept, 42.4 % against 99.7 % with v0.4, #201). **Must not regress:** D1 for
SE, V1, V2, ER and NR; D3; D5; T2b; T2c; T3a; T3b; the historical locks and claims.

**Scope** (the plan's work packages)
- A feasibility forecast before the corrections (a diagnostic; it settles no target).
- A per-event error model in correlated noise, so that the per-event tests can be decisive (#209).
- The sensitivity computation's defects: a joint error model for `aperture_depth` and
  `systematics`; `sinusoid` per harmonic (#203); the `period_alias` statistic (#204).
- The eclipsing-binary route: odd/even at the found period, and a duration warning (#10).
- INCONCLUSIVE classes in the reports (#201, part of #205).
- Battery version 3 (`discovery.version: 3`); the v0.4 and v0.5 batteries unchanged; the claim
  packaging rehearsed end to end on synthetic targets before any freeze.
- CI time: every job under 30 minutes (#210).
- Calibration, pre-registered, on sets never used in development: C1' (the v0.5 generator, new
  drand seeds), C2' (new real stars), C3' (new real controls).
- Not in scope: #200, the EBLM part of #202, #205 beyond the INCONCLUSIVE classes, #206, #12, #9,
  #11, #192.

**Exit criteria** (detail in the plan)
- [ ] Every new or changed test has its acceptance section committed before its tests and code;
      its cases run with counts from a JUnit XML file; each test accepted (decisive) or recorded
      as failed (diagnostic only); the combined non-regression gates run as the plan fixes them.
- [ ] No synthetic test that passes at the start of v0.5.1 fails at its end without a written
      justification made before; historical claims give their recorded verdicts and hashes; the
      v0.4 and v0.5 batteries reproduce their recorded outputs.
- [ ] C1', C2' and C3' locked (protocol, code, dependencies, claim), run once and reported by
      v0.5's reporting rules, every target and every non-regression target pass or fail, with
      reviewer reports for the C3' dossiers the protocol draws.
- [ ] Every failed target either PASSes in the confirmation, or has an infeasibility record
      approved by the maintainer after Codex's and an independent review, or is recorded as
      outstanding for the next correction round, by the maintainer's decision.
- [ ] Every CI job under 30 minutes, with no test deleted or skipped without its recorded reason;
      every test ID of a run in exactly one shard, checked from the job logs
      (`scripts/ci_ids_check.py`).
- [ ] Every scope issue closed, or kept open with the part left, or moved with its reason; no
      `.cache/test-*` folder remains after the suite.
- [ ] Gate: an independent review returns `SURVIVED`, or `WEAKENED` with its issues open.

---

## v0.5.2 Battery corrections, round 2

To be scoped, by a Claude and Codex consensus, with a stop for the maintainer before any code. Not
started.

**Why.** v0.5.1 closed as not approved, with every failed target of v0.5 outstanding (D1 for EB1 and
EB2, D2, D4, T2a). This is correction round 2 of at most 3 under the advance rule.

**Lessons of v0.5.1** ([closing record](docs/validation/v0.5.1/closing-record.md)): a runner hands
the tests the pipeline's own series, proved before any acceptance run; treat real and pseudo-windows
equivalently, testing the mask asymmetry first; an estimator's calibration includes its selection;
"pass every row" is a design limit, so the criterion is fixed before the code; a sabotage must be
distinguishable from an ordinary run; settle what the code can know at run time before a rule
depends on it; a target must not pass vacuously; caps come from the measured cost; the real-binary
false-positive pool is scarce.

---

## v0.6 Variable stars pack

*(Numbered v0.5 until 2026-11-03; renumbered by the consensus of 2026-11-03 under the
maintainer's delegation.)*

*(Starts only under the advance rule of 2026-11-05: after the current line of work succeeds.)*

Reuse TESS data to find and classify variable stars.

**Scope**
- Eclipsing binaries and pulsating stars: detection and classification.
- Cross-match with existing variable star catalogs.
- Exporter for the relevant community catalog submission format.

---

## v0.7 Mathematics pack

*(Numbered v0.6 until 2026-11-03; renumbered by the consensus of 2026-11-03 under the
maintainer's delegation.)*

*(Starts only under the advance rule of 2026-11-05: after the current line of work succeeds.)*

The purest form of refutation: counterexample search.

**Scope**
- Conjecture spec format with exact, machine-checkable predicates.
- Parallel counterexample search with verifiable certificates.
- Every reported counterexample re-verified independently.

---

## v0.8 Refute@Home (Swarm)

*(Numbered v0.7 until 2026-11-03; renumbered by the consensus of 2026-11-03 under the
maintainer's delegation.)*

*(Starts only under the advance rule of 2026-11-05: after the current line of work succeeds.)*

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

*(Starts only under the advance rule of 2026-11-05: after the current line of work succeeds.)*

- Stable claim spec and lock format, with a compatibility statement for PRML.
- Pack SDK, templates and documentation site.
- Governance and contribution model for community packs.
