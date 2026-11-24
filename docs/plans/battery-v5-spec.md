# Battery version 5: draft specification

> **DRAFT, not approved.** A deliverable of the v0.5.9 exploratory prototype (#218; the plan,
> "Deliverables", item 2; the maintainer's decision of 2026-11-24, received at 05:07 local,
> comment 7125778250, item 3). Nothing here is implemented, locked or opened. Every change it
> names in `src/` is a maintainer stop. It opens no phase. Opening one is the maintainer's
> decision; a phase opened from now on follows Process diet 2 (a charter first).
>
> **Limits label: 'WEAKENED; does not meet D1, D2, D4, T2a'.** It applies while version 5 uses
> the v0.5 tests (the advance rule's case (c)). `method_status: not_validated`. No earlier verdict
> changes.

## 1. What this answers

- **Codex's 7 blocking items** on the first v5 design: REFUTED, stored in
  [v0.5.9-consensus/codex-answer.md](v0.5.9-consensus/codex-answer.md). Section 4 answers each
  one.
- **The research of 2026-11-23:** the two-level architecture
  ([research-2026-11-23/](research-2026-11-23/README.md), section 5) and its review by Codex
  (WEAKENED, with four blocking items). Section 3 answers that review.
- **The proposal** [next-phases-2026-11-24.md](next-phases-2026-11-24.md), step 4: "battery
  version 5 in two levels".
- **What the v0.5.9 prototype measured:** the measured results and costs are in
  `docs/reports/v0.5.9-report.md`, and section 6 uses them. They are exploratory. They choose
  hypotheses; they never confirm one.

## 2. The design in one page

Version 5 keeps today's verdict as it is and adds two things around it.

1. **An entry rule** (from the prototype). It answers the question "does the output depend on
   where the fit starts?"
   - **E, the catalog ephemeris:** a bounded refit around the TOI's period and epoch.
   - **S, the battery's own search:** the search, then the battery's own refit.
   - **The output:** both arms are evaluated at their final ephemeris, held fixed.
   - **Consensus:** six local probes per decided arm. Any disagreement demotes the arm to
     INCONCLUSIVE; consensus never promotes.
2. **Two output levels** (from the research):

| Level | Field | Says | Rule | Measured where |
|---|---|---|---|---|
| 1, screen | `screen` (new, not a verdict) | "no assessed core test failed" | Section 3 | in a population: completeness, effectiveness |
| 2, verdict | `verdict` (unchanged vocabulary) | today's certificate | `aggregate` unchanged: SURVIVED only with every test decided, covered and sensitive | per signal; decidability reported |

- **The verdict is not redefined.** SURVIVED keeps its meaning. A redefinition would be a rule
  change that needs a blind review; it is not proposed here.
- **"Not assessed" is never a PASS.** A test with zero coverage stays INCONCLUSIVE in the
  verdict. In the screen it is "unassessed", and it is counted.

## 3. The screen (level 1): defined before any tuning

This section answers the blocking items of Codex's review of the research
([research-2026-11-23/codex-answer.md](research-2026-11-23/codex-answer.md), "Blocking").

**3.1 Outcomes.** Every eligible signal gets exactly one of three outcomes:
- **`retained`:** every required core test was assessed and none failed;
- **`rejected`:** at least one required core test was assessed and failed;
- **`unassessed`:** no required core test failed, but at least one was not assessed (zero
  coverage, a missing input, or a guarded numerical failure).

**3.2 Precedence.** Rules apply in this order, and the first that applies decides:
1. the gate fails: the signal is not eligible, and the screen is not computed;
2. a required core test failed, measured with coverage: `rejected`. A measured failure takes
   precedence over a missing test;
3. a required core test is not assessed: `unassessed`;
4. otherwise: `retained`.

**3.3 The required core tests.** They are fixed in the acceptance document before any data:
- **Today's astrophysical false-positive tests,** with their fixed thresholds: odd and even,
  secondary eclipse, centroid, and the catalog test where an EB catalog is attached. They
  continue to decide REFUTED in the verdict.
- **False-alarm tests whose thresholds may be calibrated.** The research names three candidates:
  model-shift uniqueness, transit-to-transit SNR consistency, and shape. Which of them enter, and
  how each one reports coverage, is fixed before tuning. Calibrating a threshold is a
  deterministic, seeded script run only on the exploration half. Its output goes into the claim
  before the lock.

**3.4 Denominators.** Every rate counts `unassessed` in its eligible denominator. It is credited
neither as retained nor as rejected. Each rate is reported three ways: as retained, as
rejected, and as unassessed.

**3.5 The verdict is preserved.** The screen reads the same inputs, test roles and results as the
verdict, and never changes them. A record holds both fields. The verdict is computed exactly as
today, and a test asserts it is byte-identical with and without the screen.

**3.6 Scope of adoption.**
- **An exploratory field** may be added after an approved `src/` change.
- **Using the screen to select or claim** (confirmatory work) is a rule change. It needs a blind
  review and the maintainer's decision.

**3.7 Calibration samples, sized by independent detections.**
- **Two-sided 95 % Wilson intervals,** as declared in section 4.5. At 250 independent cases per
  endpoint (checked by `.cache/v059/tools/wilson_check.py`):
  - completeness of at least 0.85 at the lower bound needs **224 of 250** retained injections;
  - effectiveness of at least 0.90 at the lower bound needs **235 of 250** rejected null
    detections;
  - a planet guard (point rate at most 0.05, upper bound at most 0.10) allows **12 of 250**
    planet refutations;
  - zero nulls retained gives an upper bound of **1.51 %**.
- **Yield is the constraint.** C2 gave only 40 of 200 rotation and 24 of 100 inversion gate
  detections. One transform per host is one independent trial; more transforms on the same host
  are not.
- **Before any lock:**
  - a pilot measures scramble yield and residual signal leakage, split by host;
  - shared sector effects are accounted for;
  - the minimum yield and the power are pre-registered.
- **Flux injection cannot validate pixel tests.** The pixel tests (centroid) need their own
  evidence; see section 4.3.

## 4. Codex's 7 blocking items, one by one

### 4.1 The execution path (item 1)

- **Version checks made explicit.**
  - `schema.py` (`_validate_discover`) treats every version 3 or above as needing
    `duration_excess`. It becomes explicit for versions 3 and 4.
  - Version 5 declares its own expected tests: the v2 test path, plus the screen's core tests.
  - The same audit covers the version checks in `params.py`.
- **One path for every caller.** The entry and the consensus go through `TessAnalyzer.analyze`,
  `analyze_data` and `build_result`, and through `discover.measure.chain`. A caller that cannot
  pass the entry is refused, never silently run as version 2.
- **The TOI ephemeris is an explicit input.** It is frozen in the claim's target attachment with
  its source and retrieval date. If it is missing or invalid, arm E is `INCONCLUSIVE` with the
  reason "no entry ephemeris". It is never replaced by the search.
- **Order of rules.** The consensus applies after coverage, sensitivity and role aggregation, to
  the aggregated class only. The dossier holds the base output, the six probes and the consensus
  output, and the verdict it returns equals the dossier's.
- **Tests.** Both arms go through the normal claim path, end to end, on synthetic data: a planet,
  an EB, a missing ephemeris and an off-window ephemeris.

### 4.2 The fixed evaluation and the probes (item 2)

- **Extracted from the pipeline.** The post-fit evaluation becomes a function that
  `attack_candidate` and the fixed path share, so no refit is patched.
  - The prototype did this with an in-process patch (`evaluate_fixed`). Version 5 does it in
    code.
  - The fixed path remeasures, at the given ephemeris: the depth, its error, the SNR and the
    transits covered, all from one membership (finite points with a positive noise, in a
    half-open box with at least three points).
- **Frozen, and recorded in the claim:**
  - the detrending mask at the evaluated ephemeris;
  - the objective: the weighted-box likelihood, 0.5·SNR², positive depths only;
  - the epoch pivot: the cycle nearest the middle of the light curve;
  - the tie rule: the first maximum in period, epoch, duration order;
  - the boundary rule: an optimum on the period or epoch edge is an unresolved entry;
  - the inputs both arms share: the files, the test plan and the stage.
- **The grid actually used.**
  - The steps are computed from the raw light curve's span and the final fit, not from the input
    hints.
  - The period step is at most the battery's fine step, with exact window ends.
  - Every record holds the steps it used.
- **The probes** are described as local probes, not as a resolution argument: epoch ±D/20, period
  ±one fine step, duration ±D/20, in a frozen order.
- **Tests:**
  - end-of-baseline drift and gaps;
  - two sectors years apart;
  - a competing signal and a cycle alias (P/2, 2P) in the synthetic acceptance;
  - a target-keyed simulation seed (see the confound in section 5).

### 4.3 The centroid (item 3)

- **Guards in `centroid_v5` itself,** following the prototype's `guarded_centroid`:
  - every sky and combined covariance finite, symmetric relative to its scale, and positive
    definite (Cholesky);
  - every quadratic form finite and non-negative within tolerance, in the observed statistic and
    in each of `sky_power`'s simulated draws.
  - A guarded failure gives `centroid_shift: INCONCLUSIVE` with its reason and zero coverage.
  - Any other exception propagates unchanged.
- **Tests at stage 2,** on the existing synthetic pixel and sky-Jacobian fixtures: a singular
  inverse, an overflow, and the simulation path.
- **The centroid is checked directly in acceptance,** not only through the aggregate class.
  It was diagnostic in v0.5.6, so an aggregate can hide a regression.
- **Zero coverage and the consensus.** A probe whose class changes because a test lost coverage
  disagrees, like any other change of class. No other coverage condition invalidates the
  consensus; this is fixed before any data.

### 4.4 A symmetric paired claim (item 4)

- **Both arms on every drawn TIC,** E and S, on the same input bytes (SHA-256 checked per unit).
- **The informative pair:** a pair where at least one arm gives a decided class on the catalog
  signal (identity matched by v0.5.6's rule).
- **A flip:** only one arm is decided, or both are decided with different classes.
- **Counted apart, never as flips:**
  - wrong-signal fits (an identity miss), per arm;
  - joint abstentions (both arms INCONCLUSIVE);
  - operational losses (download failures and resource stops).
- **Both arms' decision rates** are reported over all drawn targets.
- **The guard on the decision rate.** The 0.10 floor is kept only as a declared operational
  floor, with its reason; it is not a scientific threshold.
- **Improvement claims.** A claim of improvement over version 2, or one that credits a specific
  change, pre-registers the same-input comparator first. Agreement between E and S can be
  falsified on its own, even though each arm's consensus is enforced by construction.

### 4.5 Thresholds, power and stopping (item 5)

- **The interval convention, declared:** two-sided 95 % Wilson, z = 1.959964.
- **What the convention implies** (checked by `.cache/v059/tools/wilson_check.py`):

| Pairs | Largest flip count whose upper bound is at most 0.10 |
|---|---|
| 60 | 1 |
| 100 | 4 |
| 150 | 7 |
| 200 | 11 |
| 250 | 15 |
| 300 | 19 |
| 400 | 28 |

  At 5 of 107 the upper bound is 10.48 %, so that pair count fails.
- **0.10 is a tolerance,** justified as an operational one, never a property of a planet.
- **An upper bound above 0.10** means the claim was not established at that precision. It is a
  failed acceptance criterion, not a scientific REFUTED. REFUTED is reserved for evidence that
  the flip rate is above 0.10, with the lower bound above it.
- **A fixed sample, with no interim stop.** The 200-target stop of the first design is removed.
  The sample is sized from the informative-pair yield (section 6) and a flip rate that matters
  scientifically, declared before the lock.
- **Every door has a denominator.**
  - Identity misses in arm S are counted explicitly.
  - The exit criteria name which doors block the lock and which only report.

### 4.6 Freeze and compatibility (item 6)

- **The entry field:**
  - `entry` is required for version 5;
  - an authored `entry` on an older version is refused;
  - an absent `entry` is left out of the older versions' resolved dumps, so their hashes do not
    move.
- **Executable checks:**
  - the full resolved claim hash is compared before and after the change;
  - the locked hashes of every historical lock are checked directly, or by the existing frozen
    projection where the lock already uses one (two do);
  - `scripts/verify_locked_tags.py` passes on every tag.
- **Frozen attachments, with declared hashes:** the pool, the exposure record, the evaluator, the
  draw script and the runner.
- **A lock rule without self-reference.** A commit cannot hold its own final SHA. The steps are:
  1. commit and tag the lock;
  2. register the lock's identity (commit SHA, tag, claim hash) in a following commit.
  Old locks, projections and verdicts stay as they are.

### 4.7 Process and sampling (item 7)

- **Process diet 2 applies:**
  - a charter approved before work starts;
  - one Codex round for exploratory work, up to three for a lock, a verdict or a rule change;
  - the stops of item 2 kept;
  - every rerun approved in an issue before it runs.
- **Bounded acquisition retries.** At most 3 tries inside one approved attempt (the prototype's
  rule), each recorded. A rerun needs its own recorded approval.
- **No second attempt of a gate** without a fresh pre-registration, a fresh synthetic family and
  issue approval.
- **A confirmatory synthetic suite** (S8 of the first design) has its own pre-registration and
  lock.
- **Blind review:** a fresh reviewer, a hashed blind bundle, only for rule changes.
- **The paired panel's pool:**
  - its rules and exposure exclusions are frozen before the lock;
  - it adopts v0.5.6's order: the pool before the claim, the draw after the lock;
  - the drand chain, the signature check and the product cutoff are pinned;
  - exposure is reconciled by TIC and by TOI, across both earlier draw trails, Part A and
    v0.5.9's 24 TOIs;
  - the limits of archive and cache coverage are stated.

## 5. What the prototype changes in this draft

These items come from the v0.5.9 run. Its numbers are in `docs/reports/v0.5.9-report.md`.
They are exploratory and post hoc, so they only shape the hypotheses below.

- **The entry point matters.** In all 13 changes the S arm gave the v0.5.6 class. In 10 of the
  12 that v0.5.8 left INCONCLUSIVE, the E arm did too. Both arms read the same bytes. So the
  paired claim of section 4.4 tests a real effect, not noise in the inputs. It is a hypothesis
  from exposed, selected TOIs; only fresh targets can test it.
- **The epoch is the fragile axis.** Of the 10 consensus demotions, 8 started at an epoch probe
  of D/20. `systematics` changed in 6 of the 10. The screen's calibration (section 3) and the
  probes' step should be designed with that in mind.
- **The simulation-seed confound.** The battery's simulation seeds read the candidate's period,
  epoch and depth (`power.candidate_seed`). A probe therefore moves both the ephemeris and the
  seeds. Version 5 keys the seeds to the target, not to the fitted parameters, so a probe moves
  only the ephemeris.
- **The guarded centroid.** The prototype's guard is the model for section 4.3. The report
  (Q3) shows what it gave on the two numerical ERRORs of v0.5.8.
- **The consensus's cost in decidability.** The report (Q4) measures it per arm. Decidability
  at the verdict level is already 0.23 on known planets. A rule that only demotes is
  therefore reported beside the screen, never in place of it.
- **The resource control.** The prototype's supervisor provides:
  - a process per unit, journaled before it starts;
  - a Windows job with a kernel CPU limit;
  - the download limit at the HTTP stream boundary;
  - an independent pilot measure.
  It is the model for any version-5 runner. Its fixes of `331ca03` were checked by the pilot, not
  reviewed by Codex.

## 6. Pair yield and cost model

A planning model for the next phase, not a result. It uses the v0.5.9 run's measured unit costs
(`docs/reports/v0.5.9-report.md`, Q5) and the Wilson convention of section 4.5. The arithmetic is
in `.cache/v059/tools/yield_model.py`. Nothing is drawn.

**6.1 Cost per drawn target.** These are the run's measured means:
- one fetch: 8 CPU-s and 0.245 GB;
- one base per arm: 74 CPU-s per unit, the fit included;
- one probe unit: 59 CPU-s.

The cost is fetch + 2 × base + 6 × probe × (d_E + d_S), where d_E and d_S are the two arms' base
decision rates.

| d_E | d_S | CPU-s per target | Informative-pair yield q (between max(d_E, d_S) and d_E + d_S) |
|---|---|---|---|
| 0.10 | 0.30 | 298 | 0.30 to 0.40 |
| 0.20 | 0.30 | 333 | 0.30 to 0.50 |
| 0.30 | 0.40 | 404 | 0.40 to 0.70 |

- **Overhead:** the run's whole charge (process start-up, the controller and the supervisor's
  sample second) was 0.172 CPU-h per target, at 7.5 probes per target.
- **Planning figure:** 0.1 to 0.2 CPU-h and 0.25 GB per drawn target.
- **Where the decision rates come from.** They are unknown for PCs. On matched TOIs, v0.5.6's
  search arm decided 107 of 364 (0.29). The 24 prototype TOIs are selected and cannot calibrate
  the rates. An exposed-PC yield check must measure d_E, d_S and q before any panel is sized.

**6.2 Power.** The table gives the probability that the upper bound of the flip rate is at most
0.10, for a true flip rate f, with n informative pairs:

| n | f = 0.01 | f = 0.02 | f = 0.03 | f = 0.05 |
|---|---|---|---|---|
| 100 | 0.997 | 0.949 | 0.818 | 0.436 |
| 150 | 1.000 | 0.989 | 0.917 | 0.523 |
| 200 | 1.000 | 0.999 | 0.982 | 0.700 |
| 300 | 1.000 | 1.000 | 0.999 | 0.881 |
| 400 | 1.000 | 1.000 | 1.000 | 0.969 |

**6.3 What the prototype adds, as a warning.**
- **On these 24 TOIs:**
  - without consensus: 20 informative pairs, 10 of them flips;
  - with consensus: 12 informative pairs, 4 flips;
  - on the 8 controls: 0 flips, in 8 controls of which 6 are decided.
- These TOIs were chosen for flipping, so the numbers bound nothing. But a true flip rate near
  0.05 or above would need 400 or more informative pairs, at q of about 0.3, 1,300 or more drawn
  targets. That is about 130 to 260 CPU-h and 320 GB.
- **A 0.10 tolerance may therefore be out of reach** at a feasible size.
- **The consensus lowers q.** In the prototype, S lost 8 of its 20 decided outputs to the
  consensus. A panel sized without the consensus overestimates its informative pairs.
- **Sizing rule:** the panel is sized only after the yield check, from the declared scientific
  flip rate (section 8, question 3) and a power of at least 0.9. It runs as a fixed sample, with
  no interim stop, and a disjoint PC reserve is set aside for the prospective reading.

## 7. What changes, and who decides

| Change | Where | Stop |
|---|---|---|
| Explicit version checks; the version-5 path; the entry field | `src/refute/packs/tess/schema.py`, `params.py`, `pipeline.py`, `discover/measure.py` | `src/`, the maintainer's |
| The shared post-fit evaluation | `src/refute/packs/tess/pipeline.py` | `src/`, the maintainer's |
| The centroid guards | `src/refute/packs/tess/centroid_v5.py`, `power.py` | `src/`, the maintainer's |
| The target-keyed seed | `src/refute/packs/tess/power.py` | `src/`, the maintainer's; it moves no old verdict, because old versions keep their seed |
| The `screen` field | `src/refute/core/verdict.py` (a new function; `aggregate` unchanged) | `src/`, and a blind review before any confirmatory use |
| New false-alarm tests | the TESS pack | `src/`; an engine from a third party is the maintainer's stop (first run, licence record in `sources/`) |
| Dependencies | none planned | the maintainer's |

## 8. Questions for the maintainer (none is decided here)

1. Should the screen be an exploratory field first, with its blind review only before
   confirmatory use? This draft says yes.
2. Should the first version-5 phase be the paired-entry panel on PCs, or the screen's
   calibration? The proposal puts route (e) and the screen first.
3. What flip rate matters scientifically for the paired claim? It sets the panel's size
   (section 6).
