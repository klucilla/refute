# v0.5.11 Battery version 5, the screen: charter

> **DRAFT, not approved.** Written on 2026-11-24 by an independent, read-only planning session
> (one session, approved by the maintainer), from `main` at `411173ba`. It opens no phase. Under
> Process diet 2, item 1 (CLAUDE.md:71), the maintainer approves a charter in the phase issue,
> citing its commit SHA, and the time box starts then (ROADMAP.md:41). A change after approval
> is a dated amendment, approved the same way, that states which results were known.
>
> **Labels.** Every output of this phase is `exploratory` and `method_status: not_validated`.
> Nothing here is a verdict, a candidate or a claim, and no earlier verdict, lock, target or
> record changes.
> - Level 2 of version 5 runs the v0.5 tests, so it carries 'WEAKENED; does not meet D1, D2, D4,
>   T2a' (ROADMAP.md:184-190). Version 5 gets its own targets; no v0.5 target is relaxed.
> - Whatever uses v0.5.10's counts or tables carries 'closed with declared limits (gate REFUTED);
>   does not meet criteria 1, 2, 3, 4, 5, 7, 8, 9, 10' (ROADMAP.md:88-90). Here: the counts 307
>   and 171, and the TLS cost.
>
> **Sources of the plan:** step 4 of docs/plans/next-phases-2026-11-24.md:23-26; the draft
> specification, not adopted (docs/plans/battery-v5-spec.md:3-7); the incorporation plan and the
> rules carried (docs/reports/v0.5.10-report.md:279-303, 437-449).
>
> **A naming trap.** "Battery version 5" means `discovery.version: 5`. The module
> `battery_v5.py` holds the v0.5 tests of discovery version 2 (battery_v5.py:1-3), and
> `centroid_v5.py` is the v0.5 centroid. New modules use the suffix `_d5`, never `_v5`.

## 1. The question

Can a battery with `discovery.version: 5` and a two-level output be built so that:
- **level 1, the screen,** has a completeness and an effectiveness that are defined before any
  tuning, measured on a population, and worth a later lock; and
- **level 2, the verdict,** is today's verdict, byte for byte, on the same inputs, while
  versions 1 to 4 and every old lock stay as they are?

It answers with a frozen specification, code with its synthetic acceptance, exploratory
measurements on development hosts, a pre-registered acceptance document, a blind review of the
rule change and a recommendation on a lock. It produces no verdict and creates no lock.

## 2. Scope

### 2.1 The two levels

- **Level 1, `screen`** (a new field, never a verdict): `retained`, `rejected` or `unassessed`,
  by the draft's definitions and precedence (docs/plans/battery-v5-spec.md:63-87).
  - "Not assessed" is never a PASS. A `TestResult` with zero coverage stays INCONCLUSIVE
    (src/refute/core/verdict.py:119-140); in the screen it is `unassessed`, and it is counted.
  - `unassessed` is in every eligible denominator, credited neither as retained nor as rejected
    (docs/plans/research-2026-11-23/codex-answer.md:20).
  - The screen is a new, domain-agnostic function of `src/refute/core/verdict.py`.
- **Level 2, `verdict`:** `aggregate` and `aggregate_roles` are not edited
  (src/refute/core/verdict.py:208-276). Version 5 runs the version-2 test path with the
  version-2 roles. Screen-only tests have no role in the aggregation, so they cannot move a
  verdict (docs/plans/battery-v5-spec.md:103-113).

### 2.2 What enters from the v0.5.10 incorporation plan

That plan comes from an exploratory, post hoc trial, and none of it is evidence
(docs/reports/v0.5.10-report.md:432-435). It only chooses what is tested here.

| Item | Plan (report line) | In v0.5.11 |
|---|---|---|
| LEO-Vetter's astrophysical false-positive tests | keep the method (293) | **Enter, reimplemented from the papers** (section 2.3). The code is GPL-3.0 or later (docs/sources/engines-licences-2026-11-24.md:15): never copied, imported, or read while the tests are written. |
| Model-shift uniqueness, a false-alarm test | LEO-Vetter's false-alarm tests dropped as shipped (294) | **A candidate,** with thresholds calibrated here, never LEO-Vetter's defaults. It shares every quantity with the secondary test. Stage 0 decides core or report-only. |
| TLS search and wotan detrending (MIT) | keep as candidates (287-288) | **Conditional** (decision 1, section 13): a comparator arm first, a project dependency only behind the dependency stop. Version 5's search and detrending stay the pack's own. |
| exoVetter's metrics, LEO-Vetter's false-alarm tests as shipped, TRICERATOPS, LPP | drop or not assessed (289-292, 294-295) | Out. |

**TLS and wotan, the facts on record.**
- **Licence:** MIT for both (docs/sources/engines-licences-2026-11-24.md:13-14). That record
  asks for a second check, from the distributed files, before any incorporation (lines 29-31).
- **Pins on record:** wotan 2.1 (first upload 2026-11-06) and transitleastsquares 2.3.0
  (2026-11-12) (docs/validation/v0.5.10/engines/README.md:41-42); both pass the 7-day cooldown.
- **Their tree:** `batman-package` (GPLv3) came only through `leo-vetter`, not through TLS (the
  `# via` lines of docs/validation/v0.5.10/engines/requirements.txt). numba and llvmlite would
  be new. The trial used numpy 1.26.4; the project's lock has 2.5.3 (uv.lock:1609-1610), so
  nothing shows they resolve together.
- **If they become dependencies:** exact pins (`==`) in a new group, resolved under
  `exclude-newer = "7 days"` (pyproject.toml:70); a `sources/` record per package with a literal
  excerpt of the licence file inside the wheel; `scripts/ci_evidence.py <sha> --level full` on
  the exact commit first (CLAUDE.md:320); a stop if numpy, scipy, astropy or lightkurve moves.

### 2.3 The reimplemented tests (screen-only)

Sources: Kunimoto et al. 2025 (K25), sections 3.9 and 4; Thompson et al. 2018 (T18), Appendix A;
Seager and Mallén-Ornelas 2003 (SM03). URLs are in section 15. Every number was read on
2026-11-24 through a tool that summarizes pages: stage 0 checks each against the PDF and stores
a `sources/` record.

| Id | Metric and equation | Published threshold | Deterministic form | Coverage unit; `unassessed` when |
|---|---|---|---|---|
| F1 odd and even | `OE_box = abs(d_odd - d_even) / sqrt(s_odd^2 + s_even^2)` (K25 Eq. 11); the trapezoid depth form (Eq. 12); the timing form (Eq. 13) | depth forms above 3; timing above 10 | box depths on one fixed membership; the pack's own trapezoid (battery_v51.py:225-232), only depth and mid-time free, fixed starts and bounds. K25's transit-model form is left out: it needs a limb-darkened model, and the known ones are GPL. | measured odd and even events; too few events per parity (minimum fixed at stage 0); a fit not converged or at a bound; a non-finite error |
| F2 significant secondary | `MS4 = MES_sec / F_red - FA1`, `MS5 = (MES_sec - MES_ter) - FA2`, `MS6 = (MES_sec - MES_pos) - FA2` (K25 Eq. 9; T18 Eqs. A13 to A15); `FA1 = sqrt(2) erfcinv(T_dur / (P N_TCE))`, `FA2 = sqrt(2) erfcinv(T_dur / P)` (T18 Eqs. A4, A5) | significant when MS4 > 0, MS5 > -1, MS6 > -1; MS4 ignored when F_red > 1.8. Occultation exception: secondary under 10 % of the primary, b < 0.95, Rp < 22 Earth radii, albedo `d_sec (a / Rp)^2 < 1` (K25 Eq. 10) | a box-depth MES series on a fixed phase grid of the folded, detrended curve; fixed tie rule (the first maximum); separations of 2 and 3 durations (K25 section 3.9); F_red from the scatter of the depths outside the two events; `N_TCE` written in the claim before the run | phase cells with data; too few cells outside the primary; a secondary found while the exception's inputs are missing: then `unassessed`, never a pass |
| F3 size | `Rp = R_star sqrt(depth)` (K25 section 4.1) | above 22 Earth radii | depth from F1's fit; the stellar radius under the legacy reliability rule (params.py:94-95). The legacy `plausibility` keeps its own bound. | in-transit cadences; stellar radius missing or unreliable |
| F4 V shape | `V = Rp / R_star + b` (K25 section 4.2); b from the trapezoid's total and flat durations (SM03 Eq. 7: circular orbit, no limb darkening) | 1.5 or more | closed form from F1's trapezoid. The estimator is not K25's limb-darkened fit, so the threshold is not assumed to transfer: F4 is **report-only** unless its synthetic family of stage 1 passes as written at stage 0. | in-transit cadences; the flat duration not resolved; a negative bracket in SM03 Eq. 7 |
| U1 uniqueness | `MS1 = MES_pri / F_red - FA1`, `MS2 = (MES_pri - MES_ter) - FA2`, `MS3 = (MES_pri - MES_pos) - FA2` (K25 Eq. 7) | K25 fails below 0.2, 0.8, 0.8, optimized on QLP curves of M dwarfs | F2's MES series. Thresholds from a deterministic grid search on a development half (objective, grid and tie rule fixed at stage 0). | as F2 |

- **No random number** enters F1 to F4 or U1. A later need is seeded by the target, never by the
  fitted parameters (the confound of docs/plans/battery-v5-spec.md:358-361).
- **Screen-only tests carry no sensitivity block.** They are assessed with coverage above zero,
  inside their declared domain, with no guarded numerical failure. A legacy test keeps the
  draft's rule: a sensitivity refusal is not assessed (docs/plans/battery-v5-spec.md:69-80).
- **Pixel level.** Flux injection cannot validate the centroid
  (docs/plans/battery-v5-spec.md:136-137). It keeps its role in the verdict and is reported
  beside the screen, outside the calibrated screen of this phase.

### 2.4 The population sets (development only)

- **Injection into real hosts:** one per host, at flux level (`draw_injections`, `inject`:
  src/refute/packs/tess/discover/injection.py:85-105), as K25 section 5.3 does.
- **Orbit and sector scrambling** (K25 section 5.4): orbits swapped inside each sector, then the
  sector order permuted, from the host's seed. A new transform; the v0.4 rotations
  (src/refute/packs/tess/discover/transforms.py:10-17) stay as a comparison.
- **Inversion:** reported apart, never as a validated null (K25 section 5.4 says why). One
  transform per host is one independent trial (codex-answer.md:21).

### 2.5 Versions 1 to 4 and the old locks

- **Explicit version sets.** Today's `>=` comparisons would capture version 5 (schema.py:88-90,
  params.py:429-431, params.py:523-534), `pipeline.py:839` would write it as 2, and
  `DiscoveryParams.version` is `Literal[1, 2, 3, 4]` (params.py:409).
- **Guards and seeds gated by version.** The draft puts the centroid guards "in `centroid_v5`
  itself" (docs/plans/battery-v5-spec.md:212-218). That module serves versions 2 to 4, where a
  guard would turn a recorded ERROR into INCONCLUSIVE. Here the guard and the target-keyed seed
  apply only to version 5, and `power.candidate_seed` (power.py:299-302) stays as it is.
- **Proof:** (i) a golden snapshot of versions 1 to 4 on the synthetic fixtures, generated at
  the parent commit and committed before the `src/` change, equal byte for byte after it; (ii)
  the resolved hash of every committed claim, before and after; (iii)
  `scripts/verify_locked_tags.py` with joint PASS on every tag; (iv) full CI evidence.
- **Old locks** are verified at their tags, in their own environments
  (scripts/verify_locked_tags.py:1-17). `HISTORICAL_LOCKS` (lock_compat.py:84) is not extended.

### 2.6 Parked

The draft's entry rule E, its probes, the consensus and the paired panel stay a draft. With them
stay f*, q, n_min, N and both uses of 0.10, as a floor and as a tolerance
(docs/plans/battery-v5-spec.md:244-246, 267-268, 463-467). Stage 0 moves them to an appendix
marked "not adopted". Nothing in v0.5.11 depends on them; they block only that panel's lock.

## 3. Stages

Each stage ends with a check a record can run. A failed check returns the stop to the maintainer.

**Stage 0. Specification freeze.** Output: `docs/plans/v0.5.11-spec.md`; the draft stays as
history. Before any version-5 output exists, it resolves:
1. the required core tests and their roles, with an **assessability budget**: a committed
   script recounts, from committed records only (part B, C2), how often each proposed core test
   was assessed on planets. A core set whose joint assessed rate is below what A1 needs
   (section 6) is changed here, or the phase stops;
2. F4 and U1: core, report-only or out; U1's grid, objective and tie rule;
3. `N_TCE`, the phase grid, the minimum events per parity and every domain bound;
4. the scramble (orbit split rule, unequal blocks), the measure of residual signal leakage, the
   injection distributions and the futility rule of stage 3;
5. one Wilson z, that of `wilson_interval` (injection.py:187), not the draft's 1.959964; and
   the `entry` field, `search` only, any other value refused;
6. the loss ceiling, equal to the loss rate used to size N, so that passing it means the
   registered power no longer holds. No ceiling is written without that derivation;
7. 0.10: the only one kept is the upper bound of the planet guard, from D2's second clause
   (docs/reports/v0.5.6-report.md:38). A number without a written derivation is removed (the
   v0.5.9 gate's finding 8; docs/plans/battery-v5-spec.md:465-467);
8. the acceptance targets of section 6, as numbers. They do not change after stage 3.
- Codex: up to three rounds in one thread (a rule change).
- Check: the spec's SHA-256 is in the issue, and `src/` equals `411173ba`.

**Stage 1. Synthetic acceptance, written before the code.** Synthetic data only, no network.
- Cases: planets; binaries with unequal depths, with a secondary away from phase 0.5, and at
  half the period; an occultation that meets the exception; grazing binaries and high-impact
  giants (F4); nulls; every `unassessed` path.
- Sabotage: a SURVIVED with a test not assessed, or a `retained` with a core test not assessed,
  is impossible. Identity: the verdict with and without the screen; versions 1 to 4 against the
  golden snapshot.
- The tests are committed as strict expected failures, pushed before any `src/` change. The
  `src/` commit removes the markers and adds none.
- Check: git order and the push run's `created_at`; fast CI evidence on the test commit.

**Stage 2. The `src/` change.** STOP before the first commit in `src/`, with Codex's review of
the full diff attached (CLAUDE.md:82-83). Contents: the explicit version sets; one version-5
path for every caller; `screen`; the `_d5` test module; the scramble transform; the gated guard
and seed. No dependency changes in this commit.
- Check: stage 1's tests pass with no marker left; the four proofs of section 2.5.

**Stage 2b (only under decision 1). TLS and wotan.** A comparator arm in an isolated
environment under `.cache/v0511/`, on synthetic injections and nulls, with its rules and its
bar fixed at stage 0. A dependency change is a separate stop.

**Stage 3. Calibration on development hosts** (exploratory; section 4).
- Before the first run, one commit freezes `docs/validation/v0.5.11/rules/`: every aggregation
  rule (sectors to target, events to test), every invalid-value rule (NaN, infinite, out of
  range: `unassessed` with a reason, never pass or fail), every availability rule, every
  denominator, the outcome vocabulary and the tie rules.
- The first 50 hosts are a pilot of the runner and the meter. They also give the scramble yield
  and the leakage, read against the futility rule.
- U1's thresholds come from a seeded script on a development half, split by host with a
  committed seed. The other half only reports.
- Check: the runner refuses to start unless the rules commit is a pushed ancestor of `HEAD` and
  every worker and configuration hash matches (section 5).

**Stage 4. The acceptance document.** `docs/plans/v0.5.11-acceptance.md`, written before any
sealed host is drawn. To stage 0's targets it adds only what the pilot gives: the yield and
loss bounds, N, the power, the sealed frame's rule and the drand rule. No target value moves.
Codex: up to three rounds. STOP for the maintainer's approval.

**Stage 5. Blind review and the lock decision.** A fresh blind reviewer gets a hashed bundle
(the screen's decision rule, the acceptance document, the synthetic acceptance results) and
none of the builder's reasoning. The report then recommends: proceed to a lock in the next
phase, correct first, or stop. STOP: the decision is the maintainer's.

## 4. Targets and data

Nothing unexposed is read outside DEV-N. No holdout, hidden window or reserved set is read: in
particular the unexposed part of the v0.5.6 frame's confirmation half
(docs/plans/v0.5.6-plan.md:45-50) and every target of route (d1)'s census sources.

| Pool | What | Size | Chosen how |
|---|---|---|---|
| DEV-T, exposed TOIs | the 24 TOIs of v0.5.9, plus 48 TOIs of v0.5.6 part B with an identity-matched record | 72 | the 48: 24 per arm, by a rule and seed committed and pushed before the selection runs |
| DEV-H, exposed hosts | TICs with a run record, with SPOC 2-minute data, that are no TOI, CTOI, known planet host or EB-catalog entry at the frame date | up to 300 | all eligible, in a seeded order; the eligibility script committed first |
| DEV-N, **a new pool named by this charter** | unexposed SPOC 2-minute stars of the v0.4 domain (calibration/v0.4/PROTOCOL.md, section 3) | what DEV-H lacks to reach 300; at most 250 | a seeded draw from a frame rebuilt by a committed script, with sources and dates. STOP before its first read |

- **Exposure is derived again** by a committed script over every run record and draw. v0.5.10's
  1,367 TICs with a run record (docs/validation/v0.5.10/recheck-after-codex.json:5) is a
  planning number under that phase's label. The count of eligible DEV-H hosts is unknown to
  this draft; C2 had 87 hosts (calibration/v0.5/runs/c2/report.json:82).
- **DEV-N excludes** every exposed TIC, every TOI and CTOI, every TIC of the v0.5.6 frame, of
  the KELT-FP table and of the NASA Exoplanet Archive's planet hosts. Reading a catalog row
  exposes nothing. A DEV-N star is exposed from its draw on and unusable for confirmation; its
  exposure record is committed before its first light curve is read.
- **Why 300 hosts.** At C2's rotation yield, 40 of 200 (docs/plans/battery-v5-spec.md:129), 300
  hosts give about 60 null detections and a Wilson interval near 0.16 to 0.25 on the yield
  (planner's arithmetic, exploratory). That sizes a later sealed draw and accepts nothing.
- **Order** (CLAUDE.md:189-191), each step its own commit: protocol and seed pushed; the
  selection runs; its output is committed; only then are data fetched.
- **Named reruns approved with this charter** (Process diet 2, items 1 and 4):
  - **NR-1:** version 5 on DEV-T, once per TOI, on inputs fetched again and checked against
    the recorded SHA-256 where one exists. Reason: to describe the screen on real signals with
    a TFOPWG disposition. Trigger: stage 2 approved and the rules commit pushed.
  - **NR-2:** version 5 on the untransformed curve of each DEV-H host that has a recorded
    output, once per host. Reason: the observed set of the reported reliability. Same trigger.
  - Beside, never instead: no recorded class, status or verdict is replaced or re-scored.

## 5. Rules carried from v0.5.10, as obligations

From docs/reports/v0.5.10-report.md:442-449 (the decision of #218, comment 7144131066).
- **(a) Route (d1).** This phase freezes nothing of the (d1) pool and uses no (d1) count as a
  frame. The groups are derived again, with full provenance, and frozen before any lock, in the
  phase that locks.
- **(b) Rules before runs,** as stage 3 states. A rule written after a run is post hoc, and its
  counts stay out of every table of the acceptance document.
- **(c) Immutable workers.** One file per worker version under
  `docs/validation/v0.5.11/workers/`, never edited: a change is a new file. Every run record
  holds the SHA-256 of the worker and of the configuration, both of the git blob's LF bytes.
  The runner refuses an empty or mismatching hash before it starts (the findings of
  docs/reports/v0.5.9-report.md:54-62 and docs/reports/v0.5.10-report.md:425-430).
- **(d) Repetitions.** A second execution of a unit with a recorded start or outcome needs
  approval in the issue first, a bug included. Resuming dispatches only units never started; a
  unit started and not finished is recorded `abandoned`. The one repetition approved here: up
  to 3 download tries inside one attempt, each logged.
- **(e) Whole-path metering.** Every process of the phase (selection, staging, hashing,
  calibration, local tests) runs under one launcher that records CPU by job accounting, bytes
  at the HTTP boundary and the disk footprint sampled through the run, one ledger row per
  step. `within_caps` is written only if every step was metered; otherwise "not demonstrated".
  GitHub CI and the Codex process are outside the meter, and the ledger says so.

## 6. Acceptance targets of version 5, and what a lock needs

Starting values. Stage 0 freezes them before any version-5 output; stage 4 adds only sizes.

| Id | Endpoint | Target | Provenance |
|---|---|---|---|
| A1 completeness | `retained` over eligible injections (recovered, gate passed), `unassessed` in the denominator | two-sided 95 % Wilson lower bound at least 0.85 | fable-research.md:166 |
| A2 effectiveness | `rejected` over gate detections on scrambled hosts, one per host | lower bound at least 0.90 | fable-research.md:168 |
| A3 planet guard | verdict REFUTED over the same injections | point rate at most 0.05, upper bound at most 0.10 | D2's second clause, which v0.5 met; the same numbers |
| A4 integrity | SURVIVED with a test not assessed; `retained` with a core test not assessed | zero, by rule, with sabotage cases | fable-research.md:171 |
| A5 identity | version 5's verdict against version 2's, same inputs | byte-identical | section 2.5 |

- **Reported, with no target:** the `unassessed` rate per test; decidability (a verdict other
  than INCONCLUSIVE among the retained); reliability by K25 Eq. 16, only if the observed set
  exists; inverted curves, apart; the centroid's status; the screen's retention on the
  synthetic binary families, beside D1's frozen numbers (docs/reports/v0.5.6-report.md:37). D1,
  D2, D4 and T2a stay failed for the v0.5 battery.
- **Counts at 250 independent cases** (docs/plans/battery-v5-spec.md:120-128; recomputed here):
  224 retained, 235 rejected, at most 12 REFUTED.
- **Power** (planner's binomial arithmetic, exploratory; a committed script recomputes it at
  stage 4). At n = 250, A1 passes with probability 0.63, 0.93 and 0.98 at true rates of 0.90,
  0.92 and 0.93; A2 with 0.81, 0.96 and 1.00 at 0.95, 0.96 and 0.97. So the screen is worth
  sealing only near true rates of 0.92 and 0.96 or better. At a yield of 0.20, 250 null
  detections need about 1,250 hosts; the lower bound of the pilot's yield sizes N.
- **A failed target is reported and never tuned** (ROADMAP.md:15-17). A pilot far below these
  rates leads to "correct first" or "stop" at stage 5, with the targets as written.

**What version 5 must meet before the route (d1) claim is worth locking** (the next phase):
1. stages 1 and 2 passed, with full CI evidence on the commit to be locked;
2. the acceptance document approved, the blind review done, and the rule adopted by the
   maintainer for confirmatory use;
3. A1 to A5 measured once on sealed hosts drawn after their own lock, or a recorded decision to
   lock (d1) under version 5's own limits label;
4. for (d1) itself: rule (a); a common support filter on TESS magnitude and depth or SNR; the
   exposure reconciliation; label-bearing catalog inputs disabled; the counting rule for
   unmatched signals and missing data; a power and eligibility gate instead of "60 per arm"
   (codex-answer.md:23). v0.5.10's provisional 307 against 171 is not the frame.

## 7. Resource caps and the time box

Unit costs: 0.172 CPU-h and 0.245 GB per TOI on v0.5.9's whole path, with two arms and probes
(docs/reports/v0.5.9-report.md:198-200); 39.1 CPU-h for C2's 1,400 curves through two batteries
(calibration/v0.5/runs/c2/report.json:246); TLS at a median of 237 CPU-s per TOI
(docs/reports/v0.5.10-report.md:235).

| Step | Basis | CPU-h | Downloads |
|---|---|---|---|
| 300 hosts, 4 flux-level curves each (original, injected, scrambled, inverted) | 75 CPU-s per curve; light curves only, 0.02 GB per host (not measured) | 25 | 6 GB |
| DEV-T: 72 TOIs, one arm, with pixels | v0.5.9's whole-path figures, as an upper bound | 12 | 18 GB |
| Selection, hashing, calibration scripts, local tests | estimate | 3 | under 1 GB |
| **Caps, with a margin** | disk peak **20 GB** (pixel files deleted after each TOI, with a record) | **50** | **30 GB** |
| Stage 2b, only if approved: 300 curves through wotan and TLS | 250 CPU-s per curve | 25 more (cap 75) | 1 GB of wheels |

- The caps ledger applies from the start. Reaching a cap stops the work for the maintainer; the
  runner never raises a cap and stops before a step whose allowance would pass one.
- **Machine rules:** processors 0 to 7 stay free; at most 10 workers and 2 downloads in business
  hours, 20 and 6 outside them; BelowNormal priority; batches of at most 30 minutes; every
  execution resumable under rule (d).
- **Time box.** The default is seven calendar days from approval (ROADMAP.md:41-48). This phase
  has at least six maintainer stops, a blind review and a gate, and seven days are not
  realistic without repeating v0.5.10's record gaps. **Proposal:** with the approval, the
  maintainer records one extension to **14 calendar days**, with this reason. Checkpoints:
  stage 0 by day 3, stage 2's stop by day 8, stage 4's stop by day 12; a missed one is reported
  the same day. At the stop each criterion is recorded as met, failed or not run.

## 8. Records

One append-only `docs/validation/v0.5.11/log.jsonl` and one report,
`docs/reports/v0.5.11-report.md`, with an append-only errata log. The spec and the acceptance
document are hashed once approved: a correction to either is a separate dated file. Raw outputs
above 5 MB go to the Drive with a checked SHA-256 manifest. A licence statement needs its
`sources/` record first (CLAUDE.md:251-255). Cleanup only inside `.cache/`, with a record.

## 9. Exit criteria (each checkable from the repository)

1. **The specification is frozen.** `docs/plans/v0.5.11-spec.md` resolves stage 0's items 1 to
   8, with the assessability budget's script and table; its SHA-256 is in the issue before the
   first `src/` commit.
2. **The tests came first:** in a commit pushed before the first `src/` commit, as strict
   expected failures, with no network.
3. **The `src/` change passed its stop.** The approval cites the diff and Codex's review; the
   tests pass with no marker left, counted from a JUnit XML file.
4. **Versions 1 to 4 did not move.** The golden snapshot is equal byte for byte; every committed
   claim's resolved hash is unchanged; `verify_locked_tags.py` gives joint PASS;
   `ci_evidence.py --level full` holds on the `src/` commit.
5. **No GPL code entered.** Every licence used has its `sources/` record; the report lists the
   files read while the tests were written; nothing of LEO-Vetter, batman or PyTransit is in
   `src/` or in the lock.
6. **The pools are on record:** protocol and seed, selection output and exposure record, each in
   its own commit and in that order. Nothing reserved was read.
7. **The rules preceded the runs.** The rules commit is an ancestor of every run's commit and
   earlier than the log's first `before` entry; every run record has non-empty worker and
   configuration hashes that match files in the repository.
8. **The calibration is reported,** labelled exploratory: per set the yield, leakage, loss
   rate, the three screen rates with Wilson intervals, the per-test rates, U1's thresholds with
   their script, and the costs.
9. **The acceptance document is pre-registered.** Its target values equal stage 0's; N, the
   yield bounds and the power come from a committed script; the maintainer approved it.
10. **The blind review is stored unchanged,** with its bundle's hash, the model and the prompt;
    the report states the lock recommendation and the maintainer's decision.
11. **The records are complete.** The log covers every run; every step is in the ledger; the
    caps held, or "not demonstrated" is written; every repetition has its approval. The gate
    review is stored unchanged, in a commit after the reviewed SHA, which it names.

## 10. Reviews

- **Codex** (read-only): up to three rounds at stage 0 and at stage 4; the diff review attached
  to stage 2's stop; one round on stage 3's rules before the first run; one end-of-phase review
  of all commits. Later rounds resume the same thread.
- **The blind review of the rule change** (ROADMAP.md:59): one fresh, read-only Claude session,
  given only the hashed bundle. Purpose, number and cost go to the maintainer first
  (CLAUDE.md:362): one session, of the order of 350 thousand tokens, the size of the v0.5.9
  gate (docs/gates/v0.5.9-review.md:3).
- **The gate.** The phase changes a rule in `src/` and writes a scientific acceptance, so a
  fresh Codex session cannot be its gate (ROADMAP.md:49-51). It is one independent, fresh,
  read-only Claude session on a clean checkout of a pushed SHA, approved the same way. A
  `WEAKENED` gate has every issue tracked; a `REFUTED` gate closes nothing.

## 11. Stops (work halts for the maintainer)

These add to every stop of Process diet 2, item 2, and remove none.
1. The approval of this charter, with the choices of section 13 and the time box.
2. Any dependency change, TLS and wotan included; any first run of third-party code.
3. The first commit in `src/`, with Codex's review attached; any later `src/` commit that
   changes a rule or a threshold.
4. The first read of DEV-N; any pool, target or rerun beyond section 4.
5. The acceptance document (a pre-registration checkpoint, never merged with the next step).
6. Each Claude review authorization; the adoption of the rule after the blind review.
7. The lock decision (no lock, tag or drand round is created here); the report's approval;
   public text, the site, a release, Zenodo.
8. A cap reached, a missed time box, work beyond this charter, a deletion outside `.cache/`.

## 12. Risks, with early detection

| # | Risk | Early detection |
|---|---|---|
| 1 | **A1 is unreachable by construction.** `unassessed` counts against it, and a legacy core test refused by the sensitivity rule is not assessed. On part B's matched planets, 24 of 100 were decidable (docs/plans/battery-v5-spec.md:364-367). | Stage 0's assessability budget, from committed records, before any code. |
| 2 | **A2 is unreachable or unaffordable.** With every INCONCLUSIVE counted as a pass, 14 of 24 inverted and 22 of 40 rotated detections were kept (fable-research.md:74-75), and the yield may be near 0.2. | Stage 3's 50-host pilot, against the futility rule written at stage 0. |
| 3 | **A silent change in versions 1 to 4:** shared modules, `>=` checks, seeds, guards. | The golden snapshot committed before the change; claim hashes; the locked tags; full CI. |
| 4 | **Dependencies and licences.** TLS and wotan are in a burst of new major releases; numba and llvmlite are new; numpy may move; GPL code is one import away. | A dry resolution before the stop; licences read from the wheels; a stop if the science stack moves; criterion 5. |
| 5 | **v0.5.10's process failures repeat under time pressure:** post hoc rules, unapproved repetitions, empty hashes, partial metering. | A runner that fails closed; one launcher for the whole path; the checkpoints of days 3, 8 and 12. |

## 13. Open decisions for the maintainer (the recommendation first)

1. **How TLS and wotan enter.**
   - (a) **Recommended: conditionally.** A comparator arm in an isolated environment (stage
     2b); dependencies only by a later stop, if a bar written at stage 0 is met. The diagnosed
     loss is in the tests, not in the search, and the lock stays free of numba. 25 CPU-h more.
   - (b) Dependencies now, behind a version-5 option: a TLS search sooner, but `uv.lock` changes
     before any evidence, and the full CI matrix must carry numba.
   - (c) Out of version 5: simplest, and the plan's two candidates stay untested.
2. **Where the phase ends.**
   - (a) **Recommended: at the lock decision, in 14 days.** The sealed acceptance run and the
     (d1) claim are later phases, each with its own lock.
   - (b) In seven days, after stage 2: the default box holds, and calibration becomes v0.5.12.
   - (c) With the sealed run inside: a drand checkpoint and about 1,250 hosts in one time box.
3. **New stars for development (DEV-N).**
   - (a) **Recommended: up to 250, behind a stop.** The pilot needs about 300 independent hosts
     to bound the yield, and each new star is spent for confirmation.
   - (b) Exposed targets only: nothing is spent, but the yield's interval may not size N.
   - (c) Decide after DEV-H is counted: one more stop and about a day.

## 14. What this phase does not do

- It creates no lock, tag, drand round, dossier or verdict, and submits nothing.
- It makes no claim through route (d1), (e) or the Kepler field, and freezes no (d1) pool.
- It reads no sealed, hidden or reserved target, and runs no acceptance on sealed hosts.
- It changes no `aggregate` rule, no meaning of SURVIVED, no v0.5 target, no old verdict or
  lock, and it adopts neither the consensus rule, the entry rule E nor the paired panel.
- It copies, imports or links no GPL code, runs no LEO-Vetter, exoVetter or TRICERATOPS,
  validates no pixel-level test by flux injection, and changes no public text.

## 15. External sources (read on 2026-11-24) and what is not confirmed

- K25, LEO-Vetter: https://arxiv.org/html/2509.10619v1 (sections 3.9, 4.1 to 4.5, 5.3, 5.4, 6).
  Its journal reference, AJ 170, 280, is from the repository's note
  (docs/plans/sources/v0.5.2-odd-even-estimators-2026-11-10.md:13), not from this read.
- T18: https://arxiv.org/pdf/1710.06758 (Eqs. A4 to A8, A13 to A15). SM03:
  https://ar5iv.labs.arxiv.org/html/astro-ph/0206228 (Eq. 7).
- PyPI: https://pypi.org/project/transitleastsquares and https://pypi.org/project/wotan. Both
  pages gave the licence as MIT.
- **Not confirmed:** (i) the pins: this read showed TLS 2.0.1 (2026-10-11) and wotan 1.10
  (2021-09-24) as the latest, older than the repository's 2.3.0 and 2.1; the fetch may be
  stale, and stage 0 reads them again; (ii) the licence text inside each wheel; (iii) numba
  with the project's numpy and Python 3.13, and the same bytes from TLS and wotan on every pair
  of the CI matrix; (iv) K25's "F_red > 1.8" clause and every threshold of section 2.3, against
  the PDF; (v) the number of eligible DEV-H hosts and the light-curve bytes per host.
