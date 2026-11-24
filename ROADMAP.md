# Refute Roadmap

This file is the single source of truth for project phases.
Agents working in this repo must read it before planning any work.

## How phases work

- **One phase at a time.** Each phase is planned and built in its own session.
  Never plan or build work from a future phase.
- **Every phase ends with a gate.** The next phase starts only when *(for advancement from
  2026-11-21 on, the amendment to the advance rule below applies)*:
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
- **Amendment of 2026-11-21 (the maintainer's decision, #218).** A phase may advance when the
  previous phase (a) met its exit criteria, or (b) has an infeasibility record, or (c) closed with
  declared limits: its failed targets are listed, its battery carries a limits label (for v0.5:
  'WEAKENED; does not meet D1, D2, D4, T2a'), and every later result that uses that battery
  carries the label. (c) relaxes no target and changes no verdict. This amendment was adopted with
  the results of v0.5 to v0.5.5 known. *(Dated: it applies from 2026-11-21 on, and the rule above
  stays as it was for every earlier phase.)*
- **Process diet 2** (adopted by the maintainer's decision of 2026-11-24, #218, comment
  7122240195, as the final text of its blind review; record:
  [docs/plans/process-diet-2/](docs/plans/process-diet-2/README.md)). Applies to phases opened
  after its adoption is recorded; v0.5.9 keeps the rules it was opened with. Items 3 and 6 are
  here; items 1, 2, 4, 5 and 7 are in CLAUDE.md, "Exploratory and confirmatory work". The numbers
  1 to 7 are the same in both files.
  - **3. Time box.** Execution stops seven calendar days after the charter's approval, unless the
    maintainer has recorded, before expiry, an extension with its reason and a new deadline (one
    at a time). A locked run that has started finishes as registered, and the time box shortens no
    right-of-reply period, dependency cooldown or registered wait. At the stop, record each
    criterion as met, failed or not run. Expiry closes nothing and advances nothing: the phase
    waits for the maintainer, who alone records a close under case (a), (b) or (c) of the
    2026-11-21 amendment, as written in "How phases work". Expiry opens no automatic rescue round.
    Any later correction phase follows the advance rule.
  - **6. Gate.** For a solely exploratory phase with no lock, scientific verdict, scientific
    acceptance, change of a rule or threshold in `src/`, or separately mandated review, one fresh,
    read-only Codex session may serve as the independent gate. Fresh means a new thread, never a
    resumed one, that has seen neither the design round nor any other thread of the phase. It
    receives only the dossier: a clean checkout of a pushed SHA, with the gate-review protocol and
    the phase name as its whole prompt, and no summary from the builder. Store its review
    unchanged with the model, thread id, prompt and SHA. A `WEAKENED` gate has every issue
    tracked; a `REFUTED` gate closes nothing, and a review after fixes is another fresh session,
    with every review stored. It also counts as the round's final Codex review only when it is
    that fresh session. Retain the required independent reviews for confirmatory work and
    infeasibility decisions. Rule changes receive a fresh blind review before adoption.

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

**v0.5.9 Ephemeris entry: exploratory prototype** (opened on 2026-11-23 by the maintainer's
decision received at 19:28 local, #218, comment 7115813315; see
[the section below](#v059-ephemeris-entry-exploratory-prototype)).
- **Exploratory from start to end:** nothing is a verdict; no lock, no drand round, no change in
  `src/`, no new target. Every record carries the label 'WEAKENED; does not meet D1, D2, D4, T2a'
  and `method_status: not_validated`.
- **The question:** when the v0.5 battery enters through the TOI's ephemeris, with a bounded and
  declared refit, and its output is checked on a declared set of local perturbations, do the cases
  that changed class in v0.5.8 stabilise, and at what cost in decidability and CPU?
- **The set:** 24 TOIs already exposed: the 13 decided class changes of v0.5.8's completed runs, the
  one change the other way (TOI-6450.01), the 2 numerical ERRORs (TOI-734.01, TOI-5218.01), and 8
  unchanged controls with provenance `same`, drawn per class with a committed rule and seed. Both
  entry modes (E, the TOI's ephemeris; S, the battery's own search) run on all 24, on the same
  input bytes.
- **Caps:** 15 GB of downloads, 8 CPU-h, 10 GB of disk peak. No dependency changes.
- **The run starts only with the maintainer's recorded approval.**
- **Since the previous phase:** a second dated correction to the v0.5.8 report,
  [docs/reports/v0.5.8-report-correction-2-2026-11-23.md](docs/reports/v0.5.8-report-correction-2-2026-11-23.md).
- **After v0.5.9, a proposal only (no phase is opened):**
  [docs/plans/next-phases-2026-11-24.md](docs/plans/next-phases-2026-11-24.md), from the research
  of 2026-11-23 ([record](docs/plans/research-2026-11-23/README.md)).

### Previous phase record: v0.5.8 Output stability

**v0.5.8 Output stability: closed on 2026-11-23, gate `WEAKENED` (one important finding,
corrected)** (opened on 2026-11-23 by the maintainer's decision received at 13:27 local, #218,
comment 7107165120; see [the section below](#v058-output-stability)).
- **All five exit criteria are met,** each with its evidence in the v0.5.8 section.
- **The question:** how many outputs and test statuses of the v0.5 battery change between v0.5.6's
  search mode and a TOI-seeded rerun of the same TOIs. Everything is exploratory.
  - Doors 1, 2 and 4 were not found, and door 3 was found.
  - No verdict, rule or threshold changed.
- **The gate review** returned `WEAKENED`, with one important finding and no critical one
  ([docs/gates/v0.5.8-review.md](docs/gates/v0.5.8-review.md)).
  - **The important finding** (door 1's reading in the report) is tracked in #219. It is answered
    by a dated correction,
    [docs/reports/v0.5.8-report-correction-2026-11-23.md](docs/reports/v0.5.8-report-correction-2026-11-23.md).
    The approved report is not edited.
  - **The minor findings** are on #59.
  - **The lock tags:** `verify_locked_tags.py` gave joint PASS, 10 of 10, including the v0.5.6 tag
    ([docs/gates/v0.5.8-verify-locked-tags.md](docs/gates/v0.5.8-verify-locked-tags.md)).
- **Method status:** `method_status: not_validated` stands, under the limits label 'WEAKENED; does
  not meet D1, D2, D4, T2a'.

### Previous phase record: v0.5.7 The TOI's own signal

**v0.5.7 The TOI's own signal: closed at the pilot gate, with declared limits, on 2026-11-23** (the
amended advance rule, case (c); see [the section below](#v057-the-tois-own-signal)).
- **The pilot:** the TOI-seeded pilot reproduced 8 of 10 TOIs test by test, against the 9 required,
  so the 540 TOIs were not run. The rule was kept as written.
- **The diagnostic:** an approved rerun traced both flips to the seeding, not to the environment or
  to nondeterminism.
- **Unmet exit criteria:** 2 to 5, listed in the section. None is ticked without evidence.
- **The report:** [docs/reports/v0.5.7-report.md](docs/reports/v0.5.7-report.md), approved by the
  maintainer on 2026-11-23 (#218, comment 7106670379).
- `method_status: not_validated` stands, and no earlier verdict changes.

### Previous phase record: v0.5.6 Apply with declared limits

**v0.5.6 Apply with declared limits: closed on 2026-11-23, gate `SURVIVED`** (opened on 2026-11-21
by the maintainer's decision of 21:00, #218, which relaunched Refute under "Explore freely, conclude
strictly"; see [the section below](#v056-apply-with-declared-limits)).
- **All five exit criteria are met**, each with its evidence in the v0.5.6 section.
- **Part B's claim** (agreement of the labelled battery with TFOPWG dispositions) is `SURVIVED`,
  under the limits label 'WEAKENED; does not meet D1, D2, D4, T2a'. It is agreement, not
  independence.
- **The public report** is [docs/reports/v0.5.6-report.md](docs/reports/v0.5.6-report.md).
  - **Its addendum of 2026-11-23** (a new file; the report is not edited):
    [docs/reports/v0.5.6-report-addendum-2026-11-23.md](docs/reports/v0.5.6-report-addendum-2026-11-23.md).
    It records how the claim's events moved in v0.5.8. The locked verdict stands as recorded.
- **The reviews:**
  - Codex's review of the phase returned `SURVIVED`;
  - the independent gate review returned `SURVIVED`, with no critical or important finding
    ([docs/gates/v0.5.6-review.md](docs/gates/v0.5.6-review.md));
  - its two checks passed in the pinned environment
    ([docs/gates/v0.5.6-verify-outputs.md](docs/gates/v0.5.6-verify-outputs.md)).
- **The gate's minor findings** are on #59.
- **Method status:** `method_status: not_validated` stands.

### The v0.5 line's declared limits

- **The v0.5 line is closed with declared limits** (the amendment of 2026-11-21 to the advance
  rule, case (c)). Its failed targets stay listed and unmet: D1 (EB1 and EB2), D2, D4 and T2a. Its
  battery carries the limits label **'WEAKENED; does not meet D1, D2, D4, T2a'**, and every later
  result that uses it carries the label. v0.5 stays `WEAKENED`; no target is relaxed and no
  verdict changes. No exit criterion of any v0.5 correction phase, nor of v0.5.5, is ticked.
- **The pause ends with this relaunch.** The pause of 2026-11-21 stays as history: its
  [record](docs/plans/v0.5.5-v05-line-pause-record.md), its
  [corrections](docs/plans/v0.5.5-v05-line-pause-record-corrections.md) and its triggers. T3b's
  trigger (NExScI's answer, until 2026-12-05) still holds. The pause of 2026-11-13 and its record
  ([pause record](docs/validation/v0.5.4/pause-record.md),
  [pause-record corrections](docs/validation/v0.5.4/pause-record-corrections.md)) remain historical.

### Previous phase record: v0.5.4 Information checks

**v0.5.4 Information checks: closed on 2026-11-13** (the maintainer's decision of 2026-11-13, #217;
[first-half report](docs/validation/v0.5.4/h1-stop-report.md),
[second-half report](docs/validation/v0.5.4/h2-stop-report.md),
[pause record](docs/validation/v0.5.4/pause-record.md)). It was not a correction round, and it
neither passed nor failed a target.
- **First half.** I1 placed 103 of T2a's 169 `systematics` losses in class (i). I4 returned
  `route`.
- **Second half.** It followed the independent audit's plan, steps 1 to 7.
  - Step 1 read the D2 and T2a floors from the records.
  - Steps 2 and 3 (I3's population version), steps 5 and 6 (I2's first stage) and step 7 were
    `INCONCLUSIVE`.
  - Step 4 found that no stellar precision of 1, 2 or 3 % is shown to be enough for D1 under B0's
    oracle. *(See [pause-record corrections](docs/validation/v0.5.4/pause-record-corrections.md).)*
  - T3b's count showed a shortage of 9.
- **Method status.** v0.5.4 did not deliver a validated method (`method_status: not_validated`).

### Previous phase record: v0.5.3 Battery corrections, round 3

**v0.5.3 Battery corrections, round 3: closed on 2026-11-12 as not approved, by item 2 of its
criterion** (the maintainer's decision of 2026-11-12, #217;
[closing record](docs/validation/v0.5.3/closing-record.md),
[independent review](docs/validation/v0.5.3/closing-review.md)).

- **T2a and D2 fail their frozen rules** in the development forecasts. T2a's `K_B` is 331 against
  552 needed. D2 keeps 141 of 178 against 156 needed.
- **D1 has no route.** D4 passes only in a forecast, and T3b was not executed.
- **No target has a basis for an infeasibility record.** No acceptance ran, no confirmation data was
  used, and no drand round was drawn. No exit criterion is ticked.
- **Method status.** v0.5.3 did not deliver a validated method (`method_status: not_validated`).

### Previous phase record: v0.5.2 Battery corrections, round 2

**v0.5.2 Battery corrections, round 2: closed on 2026-11-10 as not approved** (the maintainer's
decision of 2026-11-10, #216; [closing record](docs/validation/v0.5.2/closing-record.md))

- No target passed or was declared infeasible; all stay outstanding. It counts as the second of the
  three correction rounds of the advance rule. No acceptance ran, no confirmation data was used, and
  no drand round was drawn.
- The adequacy check of the acceptance's sizing failed; development forecasts showed D2 and T2a
  failing with battery version 4. The frozen diagnosis of T2a's losses detected no class-(a) or
  class-(c) blocker among the 51 losses and no instrumentation quarantine; the losses carried unmet
  sensitivity requirements and procedural refusals whose information limits remain undetermined. No
  gate review was run, and no exit criterion is ticked.
- **Method status.** v0.5.2 did not deliver a validated method (`method_status: not_validated`).

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

Scope: [docs/plans/v0.5.2-scope-proposal.md](docs/plans/v0.5.2-scope-proposal.md). Tracking: #216.
Stage 1, a bounded diagnostic, ended on 2026-11-08; stage 2 (correction code, acceptance runs,
protocol) runs under the maintainer's delegation of the same date, whose hard maxima are 2,000
processor-hours of development and acceptance, 150 of calibration, 1.0 M review tokens and 12
agent-days.

**Closed on 2026-11-10 as not approved, before any acceptance** (the maintainer's decision;
[closing record](docs/validation/v0.5.2/closing-record.md)). No target passed or was declared
infeasible.

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

## v0.5.3 Battery corrections, round 3

Tracking: #217. Stage A (bounds, audits and diagnoses) and stage B (B0 and B0b on D1, and B1's
candidate battery version 5 with its development forecasts) ran under the maintainer's decisions of
2026-11-11 and 2026-11-12.

**Closed on 2026-11-12 as not approved, by item 2 of its criterion** (the maintainer's decision;
[closing record](docs/validation/v0.5.3/closing-record.md),
[independent review](docs/validation/v0.5.3/closing-review.md)). No target passed or was declared
infeasible, and none has a basis for an infeasibility record.

**Why.** v0.5.2 closed as not approved, with every failed target of v0.5 outstanding (D1 for EB1 and
EB2, D2, D4, T2a). This is correction round 3, the last of the advance rule. **If round 3 also ends
without success, the maintainer decides between changing the approach, recording infeasibility, or
pausing the line.**

**Lessons of v0.5.2** ([closing record](docs/validation/v0.5.2/closing-record.md)): forecast the
targets before pricing an acceptance; keep the message and the inputs of every INCONCLUSIVE; a warning
test's INCONCLUSIVE blocks the verdict while its FAIL only weakens it, a design question for the
maintainer; an estimator's calibrated domain is a coverage limit, to be sized against the target's
population; check each power requirement against the target population's noise before building the
test; size on the code that will run; an information bound is not attainability; review a design
before its run; hosts of many sectors outlast the 30-minute batch.

---

## v0.5.4 Information checks (change of approach after round 3)

Tracking: #217. Design: [docs/plans/v0.5.3-after-round3-decision.md](docs/plans/v0.5.3-after-round3-decision.md).

**Closed on 2026-11-13. The v0.5 line is paused by the maintainer's decision of that day**
([pause record](docs/validation/v0.5.4/pause-record.md)). The pause relaxes no target, declares
none infeasible and changes no verdict.

**Why.** Round 3 closed as not approved, and the maintainer chose to change the approach (the
decision of 2026-11-12). The cheap information checks come before any new estimator, each with a
pre-registered rule frozen before its data are read.

**Limits.** It is not a fourth correction round. There is no new battery, no acceptance, no draw, no
change to `src/`, and no target or test rule changes. Development data only.

**The checks and their possible outcomes:**
- **I1, the diagnosis** of which `systematics` sub-check holds T2a's losses and of D2's missing
  classes: route or unresolved, never a draft.
- **I2, the per-host bound on T2a's background error:** route or unresolved, never a draft until
  controls on `systematics`' FAILs survive review.
- **I3, D1's joint test with the planet side and the severities:** route or unresolved until its
  planet side is designed. At most a fatal-class finding, never a general D1 draft.
- **I4, `odd_even`'s bound with the transit shape as a nuisance:** route, draft infeasibility of D2,
  or unresolved.

A draft infeasibility is a draft only. Recording it is the maintainer's stop, with Codex's and an
independent review.

**The first half:** I1, then I4, run; I2's and I3's designs are written on paper and frozen only
after I1's result. It stops at its end, or earlier on a code defect, a rerun that does not reproduce
its verdict, or a draft infeasibility.

**Caps:**

| Cap | The first half | The whole phase |
|---|---|---|
| CPU-h | 25 | 50 |
| Review tokens | 2.0 M | 3.5 M, plus one independent review of up to 0.35 M |
| Agent-days | 4 | 10 |
| Disk | | 5 GB |

The phase stops at 80 % of any cap.

**Lessons of v0.5.3** ([closing record](docs/validation/v0.5.3/closing-record.md)):
- **Count blockers from what the verdict aggregates.** Two blocker lists of B1 counted diagnostic
  tests and warning FAILs as blockers. The corrected record changed which tests block (`systematics`
  and `sinusoid`, not `duration_excess`), though not T2a's answer.
- **Run information checks before building estimators.** Version 5's estimators fell back on most
  curves (E3) or ran without changing the outcome (E4, E2), and D2 did not move. A bound or
  diagnosis on the blocking sub-check would have shown where an estimator could help.
- A part's checkpoint can underestimate its cost (by 1.68 in B1.4). A cap stop on development work
  is recorded, and resolved only by an approved, recorded completion.

---

## v0.5.5 Core resolution (change of approach after the pause)

Tracking: #218. Plan (an agent's proposal, stored unchanged; it decides nothing):
[docs/plans/v0.5.5-fable-core-plan.md](docs/plans/v0.5.5-fable-core-plan.md). Charter:
[docs/plans/v0.5.5-charter.md](docs/plans/v0.5.5-charter.md). Designs of the checks:
[docs/plans/v0.5.5-r1-designs.md](docs/plans/v0.5.5-r1-designs.md). Amendment 1 to the charter
(from the independent review): [docs/plans/v0.5.5-charter-amendment-1.md](docs/plans/v0.5.5-charter-amendment-1.md).
The report at the gate G1: [docs/plans/v0.5.5-g1-report.md](docs/plans/v0.5.5-g1-report.md).
The second report at the gate G1: [docs/plans/v0.5.5-g1-report-2.md](docs/plans/v0.5.5-g1-report-2.md).
The third report at the gate G1: [docs/plans/v0.5.5-g1-report-3.md](docs/plans/v0.5.5-g1-report-3.md).
R2 on paper, the stop with the blind bundle ready: [docs/plans/v0.5.5-r2-paper-stop.md](docs/plans/v0.5.5-r2-paper-stop.md).
R2 on paper, the second stop with the second blind bundle ready: [docs/plans/v0.5.5-r2-paper-stop-2.md](docs/plans/v0.5.5-r2-paper-stop-2.md).
R2's closing record (closed without a freeze): [docs/plans/v0.5.5-r2-closing-record.md](docs/plans/v0.5.5-r2-closing-record.md).

**Paused on 2026-11-21, not approved** (the maintainer's decision of 2026-11-21, 18:30, #218;
[the v0.5 line's pause record](docs/plans/v0.5.5-v05-line-pause-record.md);
[its corrections](docs/plans/v0.5.5-v05-line-pause-record-corrections.md)). No exit criterion is
ticked.

**The v0.5 line closed with declared limits on 2026-11-21** (the maintainer's decision of 21:00,
#218: the amendment to the advance rule, case (c)), which ended the pause. Limits label: 'WEAKENED;
does not meet D1, D2, D4, T2a'. The next phase is v0.5.6.

**Note on R1's frozen files.** The 21:00 token-accounting update had changed an R1 frozen file
(`docs/validation/v0.5.5/ledger_v055.py`, whose SHA-256 R1's records carry), in commit `edfd81e`.
By the maintainer's decision of 2026-11-21 (22:30, #218) it is **restored** to its anchored bytes
(SHA-256 `65e65400…0a17`, as in R1's records); the corrected count lives in a new module,
[`docs/validation/v0.5.6/codex_tokens.py`](docs/validation/v0.5.6/codex_tokens.py), which v0.5.5's
and R2's readings use.

**Opened on 2026-11-20** by the maintainer's decision of that day (15:40, #218), which resumed
the v0.5 line through a new change of approach. **The advance rule is not amended, and no phase
advances** (as decided on 2026-11-20; the rule was amended later, on 2026-11-21, see "How phases
work"). It is not a correction round: there is no new battery, no acceptance and no draw.

**Why.** The pause left every failed target outstanding, and two conventions that decide whether
D1 can PASS or be shown infeasible were never fixed: the price on the planet side of denying
SURVIVED, and how a test may use the catalog star. The cheap checks that say whether the core has
any route come before any build.

**The scope up to the gate G1:**
- **R0, the charter.** The planet-side price per exit; the catalog star used with its declared
  uncertainty (and a generator version that draws the true star within it, for new draws); the
  standard of proof for an infeasibility record; the prospective route open, with its safeguards;
  the process changes. It changes no target, rule or verdict, and decides no design question.
- **R1, designs for four checks**, each frozen in a commit before any data is read: D2-F (D2's
  rule counts at the oracle, three variants), D1-P (D1's price curve per exit, an oracle
  surrogate), T2a-E (a model-free error census of T2a's background cases) and T3b's recount,
  whose execution the decision-value test defers to G1. **R1 runs only on the maintainer's
  release**, after an independent review of the charter and of the designs.
- **G1, the gate**: going on to R2 (the prospective version, on paper), proposing a record, or a
  pause. The maintainer's.

**Limits.** No infeasibility record, no R2 and no decision on the design questions, no lock or
drand round, no selection of real targets, no acceptance and no confirmation without the
maintainer's stop. Development data only.

**Caps up to G1:**

| Cap | Up to G1 |
|---|---|
| CPU-h | 80 |
| Review tokens | 3.0 M (Codex; the independent review counts apart) |
| Agent-days | 9 |
| Disk | 5 GB |

The phase stops at 80 % of any cap.

---

## v0.5.6 Apply with declared limits

**Closed on 2026-11-23, gate `SURVIVED`** (the maintainer's decision received at 09:50 local, #218,
comment 7101712940; [gate review](docs/gates/v0.5.6-review.md)).

Tracking: #218. Opened on 2026-11-21 by the maintainer's decision of 21:00 (the relaunch). Plan:
[docs/plans/v0.5.6-plan.md](docs/plans/v0.5.6-plan.md); open sources:
[docs/plans/sources/v0.5.6-open-sources-2026-11-21.md](docs/plans/sources/v0.5.6-open-sources-2026-11-21.md).

Apply the v0.5 battery, unchanged and with its limits label ('WEAKENED; does not meet D1, D2, D4,
T2a'), to public TOIs. Explore first (part A, exploratory: outputs are never verdicts), then
confirm what exploration picks on targets it did not use, under a lock (part B, confirmatory).
Nothing depends on `tfopwg_disp` until NExScI answers. `method_status: not_validated`.

- **T3b availability record** (adopted by the maintainer's decision of 2026-11-22, 09:00, #218):
  [docs/plans/v0.5.6-t3b-availability-record.md](docs/plans/v0.5.6-t3b-availability-record.md).
  Both frames give 2 domain-eligible stars against the 11 needed. It is **not** an infeasibility
  record, and T3b stays deferred (`INCONCLUSIVE`).
- **Part B, amendment 1** (the maintainer's decision of 2026-11-22, 13:00, #218):
  [docs/plans/v0.5.6-plan-amendment-1.md](docs/plans/v0.5.6-plan-amendment-1.md). Door 3 is
  found and not pursued, a departure from "the first door proceeds" decided by the maintainer.
  Part B is instead a claim of **agreement** with TFOPWG dispositions (FP against the planet arm,
  in the confirmation half), suggested by part A's table and disclosed as such:
  `calibration/v0.5.6/claim.yaml`. Its lock and drand round waited for the maintainer; both are
  done (next item).
- **Part B's verdict** (2026-11-23, #218): `SURVIVED` under the limits label (lock fdd87e7, draw
  185fd91, verdict 57c4160): [calibration/v0.5.6/part-b-verdict.md](calibration/v0.5.6/part-b-verdict.md).
- **The phase's public report** (approved by the maintainer on 2026-11-23, #218):
  [docs/reports/v0.5.6-report.md](docs/reports/v0.5.6-report.md). Nothing on the site yet.
- **Its dated addendum** (the maintainer's decision of 2026-11-23, #218; a new file, the report is
  not edited): [docs/reports/v0.5.6-report-addendum-2026-11-23.md](docs/reports/v0.5.6-report-addendum-2026-11-23.md).

**Exit criteria** (detail in the plan; ticked on 2026-11-23 by the maintainer's decision of 08:30,
item 2, #218, where the evidence exists)
- [x] Part A ran on the set and within the cost the maintainer approved; the frame, the split by
      TIC and the draw were committed before any light curve was read; every output carries its
      coverage, "exploratory" and the limits label.
      *Evidence:*
      - Order: the frame and the split were committed in 099c67c and the draw in 2f0d95e. Both
        precede the pilot (1d4bdcf) and the run (2e734b5, 240 records).
      - Cost: 5.95 CPU-h charged against the 50 CPU-h cap. The maximum sampled disk use after the
        maintainer's decision of 2026-11-22 (09:00) was 9.14 GB against 20 GB
        ([part-a-ledger.json](docs/validation/v0.5.6/part-a-ledger.json)). That decision came after
        the pilot's stop on disk.
      - Labels and coverage: every record is `exploratory`, with the limits label and
        `not_validated`. Every test of the 239 OK records carries its coverage or the reason it
        has none. The one ERROR is counted as a coverage loss ([part-a-records.json](docs/validation/v0.5.6/part-a-records.json),
        [part-a-report.md](docs/validation/v0.5.6/part-a-report.md)).
- [x] An exploratory report is committed, with each pre-written "door" marked found or not found.
      *Evidence:* [part-a-report.md](docs/validation/v0.5.6/part-a-report.md) (2e734b5). Door 1
      and door 2 were not found; door 3 was found and, by the maintainer's decision of 2026-11-22
      (13:00), not pursued.
- [x] Either a part B claim was locked before its targets were read, ran once and its verdict is
      reported as it came, or no door was found and the phase closes with declared limits. A door
      found whose part B cannot be locked or run is reported as incomplete, and this criterion
      stays open.
      *Evidence:*
      - The round: drand round 6665418 was fixed in the claim (fd62b0a) before the lock.
      - The lock: fdd87e7, whose time on GitHub is 2026-11-22T23:56:20Z (CI push run
        45085907521).
      - The round was published at 2026-11-23T00:26:00Z, after the lock.
      - The draw (185fd91) was committed and pushed before any light curve was read.
      - One execution: terminal state `complete`, with no rerun
        ([part-b-ledger.json](calibration/v0.5.6/part-b-ledger.json)).
      - The verdict, `SURVIVED`, is reported as it came
        ([part-b-verdict.md](calibration/v0.5.6/part-b-verdict.md), 57c4160; #218).
- [x] A public report is drafted for the maintainer's approval, with the limits label and v0.5's
      failed targets in view.
      *Evidence:* the draft was approved with five changes by the maintainer's decision of
      2026-11-23 (08:30, #218). The report is [docs/reports/v0.5.6-report.md](docs/reports/v0.5.6-report.md).
      Its facts, numbers and quotations were checked against the records in one Codex round, and
      its blocking items were applied
      ([report-round-1-answer.md](docs/plans/v0.5.5-consensus/report-round-1-answer.md)).
- [x] Codex's review (up to three rounds, one conversation) and a gate review.
      *Evidence:*
      - Codex's review of the phase: round 1 returned `SURVIVED`, with no blocking item
        ([phase-round-1-answer.md](docs/plans/v0.5.5-consensus/phase-round-1-answer.md)).
      - The gate review was a fresh, read-only session that did not build the phase, launched by
        the maintainer's adviser with the maintainer's approval. It ran on dde966d and returned
        `SURVIVED`, with no critical or important finding
        ([docs/gates/v0.5.6-review.md](docs/gates/v0.5.6-review.md), stored unchanged).
      - The two checks the gate asked for passed in the pinned environment
        ([docs/gates/v0.5.6-verify-outputs.md](docs/gates/v0.5.6-verify-outputs.md)).

**Recorded correction (2026-11-23, after the gate review).** In criterion 1's evidence, "carries its
coverage" now reads "carries its coverage or the reason it has none": 273 of part A's tests have
`coverage: null`, and all of them are `INCONCLUSIVE` (the gate review, a minor finding; the
maintainer's decision of 2026-11-23, item 3).

**Stops that stay the maintainer's:** running part A (its set and cost), drand rounds and locks,
any change in `src/`, public text and deploys, third-party code, dependencies.

---

## v0.5.7 The TOI's own signal

**Closed at the pilot gate, with declared limits, on 2026-11-23** (the maintainer's decision
received at 11:55 local, #218, comment 7104767892).
- **The pilot:** 8 of 10 reproduced, against 9 required
  ([seeded-pilot.json](docs/validation/v0.5.7/seeded-pilot.json)). The rule was kept as written,
  and the 540 were not run.
- **The diagnostic rerun** (procedure in comment 7104767892) found the seeding to be the cause for
  both differing TOIs ([diagnostic-rerun.md](docs/validation/v0.5.7/diagnostic-rerun.md)).
- **Report:** [docs/reports/v0.5.7-report.md](docs/reports/v0.5.7-report.md), approved by the
  maintainer on 2026-11-23 (#218, comment 7106670379). Records:
  [docs/validation/v0.5.7/](docs/validation/v0.5.7/README.md).

Tracking: #218. Opened on 2026-11-23 by the maintainer's decision received at 10:41 local (comment
7102888515). Plan: [docs/plans/v0.5.7-plan.md](docs/plans/v0.5.7-plan.md). Basis: an independent
recommendation, stored unchanged in [docs/plans/v0.5.7-consensus/](docs/plans/v0.5.7-consensus/README.md).

Run the v0.5 battery's tests, unchanged and with the limits label ('WEAKENED; does not meet D1, D2,
D4, T2a'), on the TOI's ephemeris instead of the search's strongest signal, for the same 540 TOIs as
v0.5.6, and publish what each test says.
- **TOI-seeded** (the maintainer's design decision received at 11:01 local, comment 7103371874,
  which revoked the opening's "the period fixed, the epoch held in a window"; a recorded
  correction): the TOI's ephemeris seeds the unchanged battery, which refits it before any test.
  Every record says whether the fit stayed on the TOI ephemeris, and every door is counted in
  total and over those that stayed.
- **Everything is exploratory:** never a verdict, a candidate or a disposition.
- **No change** in `src/`, rules, thresholds, sensitivity refusals or aggregation.
- `method_status: not_validated`.

**Exit criteria** (detail in the plan)
- [x] The runner, the four doors (both versions) and the report script are committed before the
      first result.
      *Evidence:* `seeded_run.py`, `seeded_report.py` and `tests/v057` were committed in fdafa8a.
      The pilot's results came after it, in 4201b40.
- [ ] The pilot of 10 TOIs that matched in search mode reproduces at least 9, test by test;
      otherwise STOP. **Not met:** 8 of 10
      ([seeded-pilot.json](docs/validation/v0.5.7/seeded-pilot.json)). The run stopped there.
- [ ] The 540 records exist, each with a machine `started_utc`, `mode: exploratory`, the limits
      label and coverage. **Not met:** they were not run, because the pilot stopped the phase.
- [ ] An exploratory report holds the paired table (search against TOI-seeded) and marks each
      door found or not found, in both versions (total and stayed). **Not met:** without the 540,
      no door can be marked. The report covers the pilot and the diagnostic only.
- [ ] One Codex round on the design (before the pilot) and a short gate review. **Not met:** the
      design round ran (OVERALL: REFUTED, then the maintainer's decision), but no gate review was
      run.

**Stops that stay the maintainer's:**
- any change in `src/`;
- public text, and publishing on Zenodo;
- the site's merge and deploy;
- third-party code;
- dependencies;
- changing old targets;
- deletions outside `.cache`.

This phase has no lock and no drand round.

---

## v0.5.8 Output stability

Tracking: #218. Opened on 2026-11-23 by the maintainer's decision received at 13:27 local (comment
7107165120). Plan: [docs/plans/v0.5.8-plan.md](docs/plans/v0.5.8-plan.md). Basis: an independent
recommendation, stored unchanged in [docs/plans/v0.5.8-consensus/](docs/plans/v0.5.8-consensus/README.md).

**The goal:** measure how many outputs and test statuses of the v0.5 battery change when the same
TOI signal is refitted from another seed, and publish that per test.

**The opening text:**
- **Another question, the same mode:** the phase reuses v0.5.7's TOI-seeded mode for another
  question, stability rather than equivalence.
- **v0.5.7's stop stands.**
- **The old runner is not edited:** the stop guard of `seeded_run.py` is unchanged, and a new script
  in `docs/validation/v0.5.8/` imports its functions.

**The rule:** nothing changes in the v0.5 battery or in any verdict, and any proposal of a new
threshold ends the phase. Everything is exploratory, and `method_status: not_validated` stands.

**Status: closed on 2026-11-23, gate `WEAKENED` (one important finding, corrected)**, by the
maintainer's decision received at 17:15 local (#218, comment 7112815055).
- The gate review: [docs/gates/v0.5.8-review.md](docs/gates/v0.5.8-review.md).
- The important finding is tracked in #219 and answered by the dated correction (below).
- The minor findings are on #59 (comment 7112886489).

**The report and the note** (both approved by the maintainer on 2026-11-23, #218):
- the exploratory report: [docs/reports/v0.5.8-report.md](docs/reports/v0.5.8-report.md);
- its dated correction (a new file; the approved report is not edited):
  [docs/reports/v0.5.8-report-correction-2026-11-23.md](docs/reports/v0.5.8-report-correction-2026-11-23.md).
  It reads door 1 as the note does, records the 4 fits that left the TOI ephemeris, and corrects
  the header and stage 0's wording;
- its second dated correction (a new file; neither the report nor the first correction is edited):
  [docs/reports/v0.5.8-report-correction-2-2026-11-23.md](docs/reports/v0.5.8-report-correction-2-2026-11-23.md).
  Of the 15 SNRs that moved by more than 10 %, 13 were lower and 2 higher, not 12 lower. No door
  or verdict changes (#59; the maintainer's decision of 2026-11-23, comment 7115813315);
- the note "How stable is a Refute output?":
  [docs/reports/v0.5.8-stability-note.md](docs/reports/v0.5.8-stability-note.md). Its facts were
  checked in one Codex round, whose corrections were applied
  ([record](docs/plans/v0.5.8-consensus/README.md)). Nothing on the site;
- the records: [docs/validation/v0.5.8/](docs/validation/v0.5.8/README.md);
- **on Zenodo:** DOI [10.5281/zenodo.24485272](https://doi.org/10.5281/zenodo.24485272) (all
  versions: 10.5281/zenodo.24485271), published by the maintainer on 2026-11-23; the record's
  files are checked in [docs/validation/v0.5.8/zenodo/](docs/validation/v0.5.8/zenodo/README.md).

**Exit criteria** (detail in the plan; ticked on 2026-11-23 by the maintainer's decision of 17:15,
item 3, #218, with the evidence below; the gate review checked each one)
- [x] The scripts, the draw of the 60 and the doors are committed before the first result.
      *Evidence:*
      - The doors and their counting rules were in the plan from 2ba0232.
      - The runner, the report script and the set were in 1f3e5f9, pushed at 16:48:30Z (GitHub's
        clock).
      - The first record's `started_utc` is 16:48:38Z (the machine's clock).
      - The three files' SHA-256 equal the fingerprints of every batch in
        [stability-ledger.json](docs/validation/v0.5.8/stability-ledger.json).
      - The reviewer reproduced the draw.
- [x] Stage 0 reproduces the table of section 1 of the recommendation, or records the difference.
      *Evidence:* [stage0-records.md](docs/validation/v0.5.8/stage0-records.md) (0066087). It did
      not reproduce exactly, and records two differences: 31 near refusals against 30, and
      TOI-2111.01, which cannot be checked.
- [x] The stage-1 records exist, with a machine `started_utc`, `mode: exploratory`, the limits
      label, coverage and provenance.
      *Evidence:* [stability-records.json](docs/validation/v0.5.8/stability-records.json) (bbfdecc):
      - 167 records, one per key of the set;
      - each with `started_utc`, `mode: exploratory`, the label and `not_validated`;
      - coverage: 162 `measured` and 5 `unavailable` (the failed runs);
      - provenance: 83 `same`, 84 `unknown`.
- [x] A report with flips per test and per output, Wilson intervals, and every door marked (in
      total and over provenance `same`).
      *Evidence:*
      - [stability-report.md](docs/validation/v0.5.8/stability-report.md) (bbfdecc) and
        [the report](docs/reports/v0.5.8-report.md), with
        [its correction](docs/reports/v0.5.8-report-correction-2026-11-23.md).
      - The marks, in total and over `same`: doors 1, 2 and 4 not found; door 3 found.
      - The reviewer's own recount gave the same marks.
- [x] One Codex round on the design, and a short gate review.
      *Evidence:*
      - The design round: [design-round-1-answer.md](docs/plans/v0.5.8-consensus/design-round-1-answer.md).
        It returned `REFUTED` with five blocking items, applied before the run (item 4 in part, as
        stated).
      - The short gate review: [docs/gates/v0.5.8-review.md](docs/gates/v0.5.8-review.md),
        `WEAKENED`.

**Stops that stay the maintainer's:**
- any change in `src/`;
- a change of rule or threshold;
- public text;
- publishing on Zenodo;
- the site's merge and deploy;
- third-party code;
- dependencies;
- changing old targets;
- deletions outside `.cache`.

---

## v0.5.9 Ephemeris entry: exploratory prototype

Tracking: #218. Opened on 2026-11-23 by the maintainer's decision received at 19:28 local (comment
7115813315). Plan: [docs/plans/v0.5.9-plan.md](docs/plans/v0.5.9-plan.md). Origin: a proposal of a
full battery version 5, which Codex's round returned `REFUTED`; by the most conservative option,
the phase is its smaller alternative, an exploratory prototype. Both are stored unchanged in
[docs/plans/v0.5.9-consensus/](docs/plans/v0.5.9-consensus/README.md).

**The question:** when the v0.5 battery enters through the TOI's ephemeris, with a bounded and
declared refit, and its output is checked on a declared set of local perturbations, do the cases
that changed class in v0.5.8 stabilise, and at what cost in decidability and CPU?

**The set:** 24 TOIs already exposed (the plan, "The set"): the 13 decided class changes of
v0.5.8's completed runs; the change the other way (TOI-6450.01); the 2 numerical ERRORs (TOI-734.01,
TOI-5218.01); 8 unchanged controls with provenance `same`, 2 per class, drawn with a rule and seed
committed before the draw. The 3 network ERRORs are not repeated.

**What runs:** two entry modes on all 24, on the same input bytes (SHA-256 checked): E (the TOI's
ephemeris, a bounded two-pass refit) and S (the battery's own search). Per TOI and mode: the base
output and the output with the consensus rule over six local probes; the fit's identity; the first
disagreeing probe; the measured costs. A new script in `docs/validation/v0.5.9/` imports the
battery's functions without editing `src/`, and handles Codex's first three blocking items at
prototype level. If the prototype needed a change in `src/`, the work would STOP.

**Caps:** 15 GB of downloads, 8 CPU-h, 10 GB of disk peak. No dependency changes.

**Exit criteria** (detail in the plan)
- [ ] The consensus record and correction 2 of the v0.5.8 report are committed.
- [ ] The plan, the control rule, the seed, the script and the report script are committed, and the
      pushed SHA checked with `gh api`, before the run.
- [ ] The 48 records (24 TOIs × 2 modes) exist, each with a machine `started_utc`,
      `mode: exploratory`, the label, coverage and provenance.
- [ ] A report with Q1 to Q5 marked and the costs measured.
- [ ] A version-5 specification draft (`docs/plans/battery-v5-spec.md`) that answers Codex's 7
      blocking items.
- [ ] One Codex round on the round's work, and a short gate review.

**Stops that stay the maintainer's:**
- running the run;
- any change in `src/`;
- locks and drand rounds;
- reruns beyond the approved set;
- public text and the site;
- Zenodo (a token, a draft or a publication);
- third-party code;
- dependencies;
- changing old targets;
- deletions outside `.cache`.

---

## v0.6 Variable stars pack

*(Numbered v0.5 until 2026-11-03; renumbered by the consensus of 2026-11-03 under the
maintainer's delegation.)*

*(Starts only under the advance rule of 2026-11-05, as amended on 2026-11-21: after the current
line of work meets its exit criteria, has an infeasibility record, or closes with declared limits.)*

Reuse TESS data to find and classify variable stars.

**Scope**
- Eclipsing binaries and pulsating stars: detection and classification.
- Cross-match with existing variable star catalogs.
- Exporter for the relevant community catalog submission format.

---

## v0.7 Mathematics pack

*(Numbered v0.6 until 2026-11-03; renumbered by the consensus of 2026-11-03 under the
maintainer's delegation.)*

*(Starts only under the advance rule of 2026-11-05, as amended on 2026-11-21: after the current
line of work meets its exit criteria, has an infeasibility record, or closes with declared limits.)*

The purest form of refutation: counterexample search.

**Scope**
- Conjecture spec format with exact, machine-checkable predicates.
- Parallel counterexample search with verifiable certificates.
- Every reported counterexample re-verified independently.

---

## v0.8 Refute@Home (Swarm)

*(Numbered v0.7 until 2026-11-03; renumbered by the consensus of 2026-11-03 under the
maintainer's delegation.)*

*(Starts only under the advance rule of 2026-11-05, as amended on 2026-11-21: after the current
line of work meets its exit criteria, has an infeasibility record, or closes with declared limits.)*

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

*(Starts only under the advance rule of 2026-11-05, as amended on 2026-11-21: after the current
line of work meets its exit criteria, has an infeasibility record, or closes with declared limits.)*

- Stable claim spec and lock format, with a compatibility statement for PRML.
- Pack SDK, templates and documentation site.
- Governance and contribution model for community packs.
