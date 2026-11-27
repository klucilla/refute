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

**v0.5.13 Battery version 5: calibration on development data is open,** since
2026-11-27T00:13:24Z.
- **The opening.** It opened with the record of the maintainer's approval (#218, comment
  7206278853) of the charter at `04402e7a`:
  [docs/plans/v0.5.13-charter.md](docs/plans/v0.5.13-charter.md), SHA-256 `2832dc48…6230c813`.
  The decision is comment 7204660147, item 5.
- **The time box** runs to 2026-12-04T00:13:24Z.
- **The scope.** This phase is the charter's Part A: the preconditions #226, #227 and #224, the
  reason map, and the meter of #228. Part B (v0.5.14) needs its own charter.
- **Amendment 1 is approved** (#218, comment 7207651312, item D2), at `69de5f9f` (SHA-256
  `cd2a6892…cdbaefc`): [docs/plans/v0.5.13-charter-amendment-1.md](docs/plans/v0.5.13-charter-amendment-1.md).
  The full 307-case KELT-FP cohort stays the confirmatory FP population, and the 135 non-SB1 and
  the 172 SB1 are descriptive groups. The scope question (only the types photometry can refute, or all
  307) is #230, to be decided with a blind review before v0.5.14.
- **Part A is stopped at step 1** (#226: the pinned BLAS settings change two golden outputs of
  versions 3 and 4). No pin and no `src/` change were approved (item D1).
- **Records:** `docs/validation/v0.5.13/`.
- **Labels:** `exploratory`, `method_status: not_validated`.

## Proposals

Documents only: none is adopted, and none opens a phase.

- **v0.5.13** is no longer a proposal: its charter is approved, and the phase is open (above). The
  earlier proposal stays as a record:
  [docs/plans/v0.5.13-proposal.md](docs/plans/v0.5.13-proposal.md).
- **Two lanes, engineering and confirmatory:**
  [docs/plans/two-lanes-proposal.md](docs/plans/two-lanes-proposal.md) (item A5a). It would
  change rules, so it needs a blind review before it could hold.
- **`refute demo`, then `refute check`:**
  [docs/plans/refute-demo-proposal.md](docs/plans/refute-demo-proposal.md) (item A5b).

## Closed phases

Their records and sections are in [docs/history/roadmap-archive.md](docs/history/roadmap-archive.md), moved there literally on 2026-11-26 (#218,
comment 7203695669, item A1). One row per closed phase, in the order they closed; the label
is the one its record gives.

| Phase | Closed | Result | Record | Report |
|---|---|---|---|---|
| v0.1 Calibration | 2026-10-07 | gate `WEAKENED`; self-claim FAIL | [archive](docs/history/roadmap-archive.md#v01-calibration) | [post-mortem](calibration/POSTMORTEM.md) |
| v0.2 Gauntlet | 2026-10-11 | gate `WEAKENED`; self-claim FAIL | [archive](docs/history/roadmap-archive.md#v02-gauntlet) | [post-mortem](calibration/v0.2/POSTMORTEM.md) |
| v0.3 Replicate papers (ML pack) | 2026-10-20 | gate `WEAKENED` | [archive](docs/history/roadmap-archive.md#v03-replicate-papers-ml-pack) | [gate record](calibration/v0.3/main/gate/README.md) |
| v0.2.1 Gauntlet fixes | 2026-10-27 | ended as not approved | [archive](docs/history/roadmap-archive.md#v021-gauntlet-fixes) | [closing record](docs/validation/v0.2.1/closing-2026-10-27.md) |
| v0.4 Discover (pilot with a funnel) | gate 2026-11-01; release 2026-11-03 | gate `SURVIVED`; published (P7); release v0.4.0 | [archive](docs/history/roadmap-archive.md#v04-discover) | [results](calibration/v0.4/results/README.md) |
| v0.5 Stronger tests | 2026-11-05 | `WEAKENED` | [archive](docs/history/roadmap-archive.md#v05-stronger-tests) | [closing record](calibration/v0.5/results/closing-record.md) |
| v0.5.1 Battery corrections | 2026-11-08 | not approved | [archive](docs/history/roadmap-archive.md#v051-battery-corrections) | [closing record](docs/validation/v0.5.1/closing-record.md) |
| v0.5.2 Battery corrections, round 2 | 2026-11-10 | not approved | [archive](docs/history/roadmap-archive.md#v052-battery-corrections-round-2) | [closing record](docs/validation/v0.5.2/closing-record.md) |
| v0.5.3 Battery corrections, round 3 | 2026-11-12 | not approved | [archive](docs/history/roadmap-archive.md#v053-battery-corrections-round-3) | [closing record](docs/validation/v0.5.3/closing-record.md) |
| v0.5.4 Information checks | 2026-11-13 | closed, neither passed nor failed a target; the v0.5 line paused | [archive](docs/history/roadmap-archive.md#v054-information-checks-change-of-approach-after-round-3) | [pause record](docs/validation/v0.5.4/pause-record.md) |
| v0.5.5 Core resolution | 2026-11-21 | paused, not approved; the v0.5 line closed with declared limits: 'WEAKENED; does not meet D1, D2, D4, T2a' | [archive](docs/history/roadmap-archive.md#v055-core-resolution-change-of-approach-after-the-pause) | [pause record](docs/plans/v0.5.5-v05-line-pause-record.md) |
| v0.5.6 Apply with declared limits | 2026-11-23 | gate `SURVIVED` | [archive](docs/history/roadmap-archive.md#v056-apply-with-declared-limits) | [report](docs/reports/v0.5.6-report.md) |
| v0.5.7 The TOI's own signal | 2026-11-23 | closed at the pilot gate, with declared limits | [archive](docs/history/roadmap-archive.md#v057-the-tois-own-signal) | [report](docs/reports/v0.5.7-report.md) |
| v0.5.8 Output stability | 2026-11-23 | gate `WEAKENED` | [archive](docs/history/roadmap-archive.md#v058-output-stability) | [report](docs/reports/v0.5.8-report.md) |
| v0.5.9 Ephemeris entry: exploratory prototype | 2026-11-24 | gate `WEAKENED` | [archive](docs/history/roadmap-archive.md#v059-ephemeris-entry-exploratory-prototype) | [report](docs/reports/v0.5.9-report.md) |
| v0.5.10 Census and feasibility | 2026-11-24 | declared limits (gate `REFUTED`) | [archive](docs/history/roadmap-archive.md#v0510-census-and-feasibility) | [report](docs/reports/v0.5.10-report.md) |
| v0.5.11 Battery version 5: specification and software | 2026-11-25 | declared limits (gate `REFUTED`: criterion 6 not demonstrated) | [archive](docs/history/roadmap-archive.md#v0511-battery-version-5-specification-and-software) | [report](docs/reports/v0.5.11-report.md) |
| v0.5.12 Battery version 5: corrections before calibration | 2026-11-26 | declared limits (gate `REFUTED`: criteria 2 and 6 not met) | [archive](docs/history/roadmap-archive.md#v0512-battery-version-5-corrections-before-calibration) | [report](docs/reports/v0.5.12-report.md) |

## Horizon

The later phases, as they were written. None is open.

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
