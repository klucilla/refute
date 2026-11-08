# v0.5.2 stage 1: the result, the acceptance specification and the cost worksheet

Stage 1 of [the scope proposal](../../../plans/v0.5.2-scope-proposal.md), authorized by the maintainer on
2026-11-08 (#216). Development data and development seeds only; no acceptance or confirmation seed, no
drand round, no change in `src/`, no correction code. **It decides nothing about any target.**
`method_status: not_validated`. It ends in a stop for the maintainer.

Codex reviewed this report in three rounds (`docs/plans/v0.5.2-consensus/`). Its round 3 was `WEAKENED` with one low-severity
correction, the label of one sensitivity, which is applied here; its other objections of rounds 1 and 2 are answered in the text.

## What ran, as it came out

Each experiment's design was frozen and committed before it ran. Codex's answers are in
`docs/plans/v0.5.2-consensus/`.

### E1, the detrending mask ([design](e1-design.md), [result](e1-mask.json))

**Frozen rule: NOT ESTABLISHED.** One of the 16 comb constructions, arm C in correlated noise and partial
coverage, failed the availability check (2.5 % against 1 %), and the frozen rule required all 16. No
threshold was changed. The numbers, which the rule's verdict does not change:

| Noise, coverage | `rho` as built (A) | Both masked (D) | Crossover (C) | No mask (B) |
|---|---|---|---|---|
| correlated, full | 1.066 | 1.008 | 0.935 | 0.986 |
| correlated, partial | 1.057 | 1.006 | 0.950 | 0.998 |
| long, full | 1.063 | 1.006 | 0.918 | 0.967 |
| long, partial | 1.058 | 0.994 | 0.930 | 0.982 |
| correlated_trend, full | 1.059 | 0.999 | 0.918 | 0.969 |
| correlated_trend, partial | 1.040 | 0.983 | 0.924 | 0.972 |
| white, full | 1.000 | 0.969 | 0.914 | 0.942 |
| white, partial | 1.005 | 0.982 | 0.941 | 0.962 |

Arm D's `rho` is in [0.95, 1.05] in every correlated, long and correlated_trend cell, and white moves by
at most 0.031. The paired decomposition shows the mechanism's direction: the real windows' variance is
unchanged from A to D (2.009e-07 against 2.010e-07, correlated/full), and the empirical error's variance
rises by 12 % (1.768e-07 to 1.980e-07). The crossover goes below 1 in every cell, as the asymmetry
predicts. The comb agrees with the window-by-window reference within 1 % (RMS) for all arm D constructions.
This is the prespecified pattern in its values, but the frozen rule returned NOT ESTABLISHED and it
stands; the pattern's values do not establish population equivalence or a unique mechanism.

### E2, the matched estimator ([design](e2-design.md), [result](e2-matched.json))

**Frozen rule: EVALUATED; no candidate qualifies.** Restricted to periods 3.3 and 7.0 d; the short-period
question is carried forward (flagged in the design as an outcome-informed amendment).

| Estimator | Pull sd white / correlated / long (pooled, null) | Mean power on the alternative | Availability |
|---|---|---|---|
| `built` (baseline) | 1.254 / 1.961 / 2.013 | 0.653 | 0.83 to 0.85 |
| `built_masked` | 0.999 / 1.123 / 1.093 | 0.561 | 0.84 to 0.85 |
| `candidate_shape` | 1.016 / 1.088 / 1.064 | 0.567 | 0.84 to 0.85 |
| `crossfit` | 1.125 / 1.108 / 1.131 | 0.497 | 0.93 to 0.96 |
| `pseudo_ephemeris` | 0.956 / 1.579 / 1.430 | 0.533 | 0.97 to 0.98 |
| `box` | 0.959 / 1.056 / 1.026 | 0.528 | 0.83 to 0.86 |

The mask treatment brings the matched scatter from about 2 to about 1.1, and pooled means are within 0.06 in
every candidate. They fail on two required sets. (1) **Cells:** 9 or 10 of 24 null cells for `box`,
`built_masked` and `candidate_shape`, nearly all of them the 0.20 d shape. (2) **Power:** in 7 or 8 of the
12 alternative cells, detection is below the exploratory 0.80. SNR 12 in correlated noise is 0 to 3 of 30
for every estimator, baseline included, and the alternative has only the odd events at depth, so the
statistic's signal is smaller than the candidate's. `pseudo_ephemeris` does not qualify: its scatter is 1.43 to
1.58 in correlated and long noise, and 2 of its 120 due repeats are missing, so its precision is not
established. At 1.5 d the estimators are available on only 42 to 43 % of curves (`box`, `built`, `built_masked`,
`candidate_shape`), 67 % (`pseudo_ephemeris`) and 78 % (`crossfit`): the short-period limit is real.

### E3, the sinusoid under trends ([design](e3-design.md), [result](e3-sinusoid.json))

**Frozen rule: NOT ESTABLISHED**, because the near-harmonic control's own baseline recovers its target only
at 0.74 and 0.20 (the rule required 0.90), so preservation cannot be judged. The tables stand.

| Cell | `built` failures of 150 | Failures with `s < 1` | `s < 0.5`, `built` to `narrow` | `0.5 <= s < 1`, `built` to `narrow` |
|---|---|---|---|---|
| SNR 12, trend | 34 (0.227) | 34 | 24/25 to 21/25 | 10/18 to 8/18 |
| SNR 12, correlated_trend | 24 (0.160) | 24 | 18/21 to 14/21 | 6/19 to 1/19 |
| SNR 20, trend | 31 (0.207) | 31 | 20/23 to 16/23 | 11/23 to 8/23 |
| SNR 20, correlated_trend | 23 (0.153) | 23 | 15/22 to 15/22 | 8/19 to 3/19 |

**All 112 failures of the `built` arm have `s < 1`**, the trend within one nominal frequency-resolution unit
(`1 / T_span`) of a tested harmonic, mostly 2P. **Of the 430 planets with `s >= 1`, none fails: 320 end PASS and 110
INCONCLUSIVE** (all 110 in SNR 12 with correlated_trend, the cell where no planet has every harmonic detectable,
0 of 150). Failures were concentrated within one nominal frequency-resolution unit; this experiment does not establish
identifiability or impossibility throughout that region. The exact-harmonic alternatives are detected at 100 % by every
arm. `narrow` lowers the failures below `s = 1` and loses the near-harmonic control (0.74 to 0.10, and 0.20 to 0.03);
`extra6` barely changes the failures (one more in three of the four cells) and raises the near-harmonic control to 0.90
and 0.39. **The conflict between the 0.0027 limit and the detectability requirement stays unresolved, for the maintainer.**

Three cost mistakes were made and corrected on the record in E3's design: two wrong explanations of its
probe's cost and the true one (below).

## The cost: measured

**A0's work continues scaling through 16 workers, sublinearly; the sinusoid saturates around four.** Per-unit
measurements on development seeds (`worksheet-probe.json`), units per second and processor-seconds per unit:

| A0 work | 1 process | 4 | 8 | 16 |
|---|---|---|---|---|
| A0.1 per-event unit | 4.7, 0.21 | 18.4, 0.21 | 33.9, 0.23 | 44.0, 0.32 |
| A0.2 group unit | 1.6, 0.61 | 6.1, 0.64 | 10.6, 0.73 | 12.7, 1.21 |
| A0.5 pattern unit | 5.5, 0.18 | 21.3, 0.18 | 39.2, 0.20 | 52.4, 0.27 |
| A0.8 unit | 1.9, 0.53 | 7.4, 0.53 | 13.9, 0.57 | 18.3, 0.80 |

At 16 workers A0's throughput is 7.8 to 9.7 times that of one worker, while its processor-seconds per unit rise by 47 to
99 %. The sinusoid (E3's unit), its own scan: units per second and processor-seconds per unit at 1 worker, 0.76 and 1.32;
at 4, 1.75 and 2.17; at 8, 1.47 and 5.18; at 12, 1.42 and 7.69; up to about 18 processor-seconds per unit at 22. Its
throughput stops at about 4 workers and then falls; the cause was not isolated (a shared resource). So a run of the sinusoid
should use few processes, and its processor-hours at 22 workers overstate the work.

**A C1 curve** (a small development probe of the existing version-3 paired chain, not of a version-4 correction: 13 families,
3 curves each, 4 workers, 493 s wall) costs a mean of 47 processor-seconds. Weighted by C1's planned family sizes (100 curves for
PA and PX, 200 for the others), 2,400 curves project to **about 30.2 processor-hours** (the equal-family mean gives 31.3), and
about 8 wall hours at 4 workers, an extrapolation from 39 curves. Family P, the one the historical 110 seconds (at 22 workers)
measured, costs 80 seconds here. C2' and C3' were not measured for version 4: the earlier allocation of 24 hours for them is an
allocation, not a measurement.

## The acceptance specification (for the maintainer's decision; nothing is run under it yet)

**Cells.** Coverage stratum x sector count, for each statistic, in each noise model and each required
construction and conditional branch: one member of the family per row of that product. A cell never inherits
from a neighbour.

**The tolerances (unchanged):** population `|mean pull| <= 0.1` and pull standard deviation in [0.9, 1.1], that is,
population variance in **[0.81, 1.21]**.

**The rule per cell.** A cell is *accepted* if the simultaneous intervals of its mean and its variance lie inside the
tolerances; *miscalibrated* if an interval lies wholly outside; *not measured* otherwise (fewer contributing curves than
the minimum, or an interval straddling a bound). Only an accepted cell's error is decisive; otherwise its test is
INCONCLUSIVE. Failing to establish equivalence is not evidence of miscalibration; the two classes are reported apart.
Operational permission needs **every applicable required member**, including every noise model and branch; a member left
out by a floor or a minimum count stays not measured and is never waived.

**The procedure, fixed before use.**

- **Family and level:** a declared familywise error of 0.05 over all members, both parameters and both tails, run at an
  **internal level of 0.04**, the remaining 0.01 being reserved for the simulation precision of the validation gate below.
- **Sampling and retention:** a fixed schedule, every finite pull of it used (no "first 400"). A curve is a cluster.
  Unavailable curves stay in the availability denominators and are reported per cell. A member needs at least `G_min`
  contributing curves; below that it is *not measured* and leaves the family before any resampling, on the count alone. A
  member whose observed error is zero or undefined is not measured in the same way.
- **Estimands and errors, one form for all members:** a curve `i` contributes pulls `y_ij`, `n = sum n_i` in all, `G`
  curves. Mean: `m = sum y_ij / n`, with `S_i = sum_j (y_ij - m)`. Variance: `V = sum (y_ij - m)^2 / n`, with
  `U_i = sum_j [(y_ij - m)^2 - V]`, so that `sum U_i = 0` exactly. Cluster-robust errors:
  `se(m)^2 = G/(G-1) sum S_i^2 / n^2`, `se(V)^2 = G/(G-1) sum U_i^2 / n^2`. With one pull per curve these are the usual
  error of the mean and the delta-method error of the variance. Both are recomputed inside every resample.
- **Simultaneity:** a studentized max-t bootstrap with centred roots,
  `T* = max over members, parameters and tails of +-(theta* - theta) / se*`, 2,000 replicates, resampling whole curves
  within each independently generated run, so that shared curves stay shared across the statistics of a run. The critical
  value is the order statistic `k = 1 + BinomialQuantile(0.95; 2000, 0.96)`, which is **1,935**: its own Monte Carlo
  uncertainty is on the conservative side. Intervals are `theta +- q se`.
- **Degenerate replicates:** a replicate in which a retained member's error is zero or undefined takes an infinite root.
  With **11 or more** such replicates (over 0.5 %), the family's result is *not measured*, reported with the fraction.
- **Moments:** the guarantee is asymptotic and needs consistent studentization and bootstrap approximation (Romano and
  Wolf 2005), not finite-sample. A finite eighth moment of the cluster-level contributions is a sufficient assumption chosen
  here to support the variance's studentization, not a requirement of that theorem; the controls below measure the
  behaviour.
- **Additional checks, which can only reject:** per family, the concatenated mean and variance within the tolerances,
  with the same curve resampling.

**Validation before any use (a stage-2 step; proposal of its criteria, each with Monte Carlo uncertainty).** The
known-answer control of the proposal: a fixed linear box contrast on raw noise of known covariance with fixed masks, with
the real shared-curve layout, unequal contributions and missingness, and Student's t (5 degrees of freedom) as a
non-Gaussian control outside the moment condition. **The gate that grants permission**, on at least 4,000 replications per
scenario, one-sided 95 % Clopper-Pearson bounds: simultaneous coverage with a lower bound of at least 0.95; familywise
incorrect permission with an upper bound of at most 0.05; incorrect permission per cell with an upper bound of at most 0.05 at
each of the four boundaries (mean +0.10 and -0.10, sd 0.90 and 1.10) and at the nearby alternatives beyond them (mean +-0.105
and +-0.11, sd 0.895, 0.89, 1.105 and 1.11); and in mixtures with 0, 1, 10 and 50 % of the members defective at those boundaries,
familywise incorrect permission under the same bound. Certification of a correct cell: a lower bound of at least 0.90 at the
chosen size, or the different target the maintainer states explicitly when choosing `T`. Student's t is judged against the same
gate and a failure there goes to the maintainer. Development runs may use 0.925 and 0.075 as diagnostic screening thresholds; these
never validate the procedure. It validates the inference machinery, not errors after adaptive preprocessing.

**Sabotages.** Each specified before the code, with the baseline accepted in the cell it protects and the sabotage violating
the criterion by a positive distance: **0.05 beyond the protected bound** (sd at least 1.15 or at most 0.85, or `|mean|` at
least 0.15), the distance at which a planned power of at least 0.90 is computed, at level 0.05, on paired whole-curve resampling:

| Sabotage | Protects | Direction | Minimum meaningful effect | Note from v0.5.1 |
|---|---|---|---|---|
| `model_errors_alone` | empirical errors | scale up | sd at least 1.15 | +0.40, a real effect |
| `rho_zero` | event correlations | scale up | sd at least 1.15 in the long-noise cells | +0.043, real but small: needs longer-noise cells or a stronger noise |
| `neff_equals_n` | the `n_eff` correction | scale up | sd at least 1.15 | +0.012 in 3 rows, not distinguishable: needs a design decision |
| `pool_sectors` | per-sector errors | scale | sd at least 1.15 in the unequal-noise cells | +0.016, not distinguishable: needs a design decision |
| `force_phase_half` | the conditional exclusion | scale | sd at least 1.15 or at most 0.85 with the secondary | -0.019, not distinguishable: needs a design decision |
| `share_event_cadences` | window disjointness | structural | a deterministic invariant | detected |

Dropping or replacing a required protection is a decision for the maintainer.

**Left open for the maintainer:** `G_min`, the list of sector counts, and the availability floor below which a required
member stays not measured.

## The cost of the acceptance

### Per cell

(`worksheet-sizes.json`; independent Gaussian pulls, Bonferroni critical values, conservative against a max-t.) To certify
a calibrated cell with 90 % probability takes **3,000 trials with 150 members, 3,300 with 500, 3,600 with 1,500**, and with
the old grid's 2,170 to 2,874 members, **3,700 to 3,800** (`worksheet-reprice.json`; at a Bonferroni level of 0.05, before
the internal 0.04 of the specification). The 2,800 to 3,500 the maintainer asked about certify below 90 % at that family size
under this idealization, by an amount not computed here.

Sequential designs, as **illustrative boundary scenarios** (four looks; the fixed design has one). These are not calibrated
designs: their boundaries (`z / sqrt(t)`, `1.2 z`, `1.5 z`) were not calibrated for repeated-look familywise error, a
constant `1.5 z` is not by itself a confidence sequence, and their certification probabilities differ, so their expected
sizes do not compare equally powered designs. The original calculation, for 500 members:

| Design | Certification probability | Calibrated cell, expected n | Clearly miscalibrated cell |
|---|---|---|---|
| Fixed | 0.907 | 3,300 | 3,300 |
| O'Brien-Fleming type | 0.925 | 3,187 | 2,474 |
| Pocock type (1.2 z) | 0.976 | 3,872 | 2,309 |
| Confidence-sequence type (1.5 z) | 0.995 | 5,831 | 3,693 |

In these scenarios, expected savings for calibrated cells are small, and the larger ones appear on clearly miscalibrated
cells. No sequential option is recommended here: one would first be calibrated across looks, cells, parameters and tails,
and compared at matched certification power (Jennison and Turnbull 1993; Howard et al.). Grouping cells changes the total
far more, but only under a validated worst-case envelope.

### Totals, on the old grid

`worksheet.py` scaled the old schedule by `n / 400` from probes at two sectors, one noise model and each section's best
worker count. Those outputs stay as **the original calculation, not an acceptance budget** (`worksheet-table.json`): E, the
old grid at 400 per row, 64.9 processor-hours; A, 3,300 per cell, 536; B, A0.5 left at 400, 399; C, a division of every
section by three, 179; D, O'Brien-Fleming looks, 517. **A0 round 2 of v0.5.1 actually spent 100.7 processor-hours** on the
same grid (101.9 with its sabotages; 22 workers; `a0r2-result.json`), not 64.9. The difference reflects different workloads
and worker counts collectively; the individual contributions were not isolated.

**The repricing** (`worksheet-reprice.json`, from the measured CPU per section and each row's availability) is an
**expected-count cost scenario** on the old grid's 3,558 entries, not a complete budget. `T` is the expected number of
contributing curves in a priced member; a preregistered schedule with a stated probability of delivering `T` in every required
member would cost more. The floor selects which rows are priced: it does not establish that they are measured or accepted, and it
waives nothing. A run's units are those its most demanding priced row needs. A0.8's event rows use the curves of their branch in
the run of the same coverage kind (an estimate); A0.1's curve fraction is not in the result file and is priced at 1.0 (at 0.25, holding the priced membership
fixed, about 16 more processor-hours at `T` = 3,300; under the floor policy, at floor 0.50 its 15 members would instead leave
the pricing and about 5 processor-hours less would be spent). The days are **ideal fully occupied 22-worker-equivalent days**, not a forecast of wall time:

| Availability floor | Members priced / below the floor / with no observation | T = 2,800 | T = 3,300 | T = 3,500 |
|---|---|---|---|---|
| 0.50 | 2,170 / 724 / 664 | 611 h, 1.16 d | 716 h, 1.36 d | 758 h, 1.44 d |
| 0.25 | 2,587 / 307 / 664 | 918 h, 1.74 d | 1,080 h, 2.05 d | 1,145 h, 2.17 d |
| 0.10 | 2,874 / 20 / 664 | 1,433 h, 2.71 d | 1,687 h, 3.20 d | 1,789 h, 3.39 d |

The totals include the old size of runs with no row at the floor, retained as diagnostic expenditure: 22.2 processor-hours at floor
0.50, 11.5 at the others. Variations at T = 3,300 with floor 0.25 (1,080 processor-hours):

| Option | Processor-hours | Ideal days (22) | Status |
|---|---|---|---|
| Coverage strata grouped: one run per stratum group, the most demanding | 460 | 0.87 | needs a validated worst-case envelope, whose cost is not priced; A0.7 and A0.5's p3 have no strata to group |
| A0.5 left at its old size, diagnostic | 892 | 1.69 | **not admissible** without a validated substitute for the required constructions |
| With 5, 8 and 12 sectors added, linear scaling (3.78 times) on the rows indexed by sectors | 3,607 | 6.83 | holds availability, per-curve targets and cost per sector fixed; it does not establish the expanded family's required size |

**Not priced:** the corrected code's extra cost, the reference checks, the known-answer validation, the sabotages at the
new sizes, A0.3 and the remaining acceptances, C2' and C3', an envelope validation, and reviews. The model uses each
section's mean CPU per unit, which hides the differences between sector counts. A planning allowance is a judgement, not a
measurement: Claude proposes 30 % on what is priced. Rows with no observation (664) are structurally empty or absent from
the old run and are counted apart. **Stage 2's caps are to be set by the maintainer** from this table and the choice below.

## The T3b pool

From the frozen v0.5 inputs (`t3b-pool.json`; no catalog read): **856** TOI false positives with the depth rule and not
already known; 63 in TESS-EB (the v0.5 pool; 22 never walked), **793 outside TESS-EB**. Upper bound on new stars from any
crossing with the TESS Ten Thousand Catalog: **793**, if all were catalogued. The actual overlap cannot be known without
the table, which is not read before the maintainer's approval. At v0.5's yield (11 of 41, 0.268), the 22 give about 5.9
acceptances, 5.1 short of the 11 needed for one confirmation; **19 additional catalogued pool members would bring expected
acceptances to eleven under the historical-yield assumption; actual sufficiency is unknown**. The article queried about
10,000 ExoFOP-TESS planet candidates in its positional comparison, but it does not state the overlap with TOI false
positives. The catalog is reached through the article's machine-readable supplements and VizieR's `J/ApJS/279/50`, which
did not load; its license is **unconfirmed** (`docs/plans/sources/v0.5.2-candidate-sources-2026-11-08.md`).

**Does the swap preserve the population? Codex's judgement, round 1: a qualified yes for the intended class; no for the
literal frozen sampling frame.** Keeping the TOI false-positive requirement and intersecting it with T10K's 10,001 vetted
binaries preserves the intended class, "TOI false positives that are catalogued eclipsing binaries"; its roughly 900,000
unvetted candidates do not. The frozen protocol requires TESS-EB membership, so the swap is an explicit,
maintainer-approved **sampling-frame amendment**, keeping all the TOI, depth, period, uniqueness, exclusion, product,
identity, eight-outcome and reserve rules, matching the target TIC, keeping the evaluation free of catalog lookups, and
reporting source membership separately. It must not be called the unchanged frozen population, nor claim demonstrated
distributional equivalence. Claude agrees.

## The D1 margin, in simple terms

The proposed condition says that a D1 PASS only counts if the new battery rejects binaries about as often as the old one
(v0.4) did on the same curves. **The margin of 0.10 says how much worse it may be:** up to ten fewer rejections per 100
eligible curves. The second condition says the new battery may not leave undecided more than ten more per 100 than v0.4
did. Without them, a battery that refutes nothing could pass D1 by surviving nothing. On the v0.5 record the conditions
would have failed EB1 at the floor (62 REFUTED of 190 against 91 needed) and EB2 at the ceiling (73 INCONCLUSIVE of 186
against a ceiling of 24.6), while EB2 meets the floor (69 against about 52).

**Recommendation, Claude and Codex (round 1):** keep both conditions at 0.10 as provisional empirical safeguards, per
family, alongside D1's original requirements, reporting the paired uncertainty without silently changing the decision
rule. Matching D2's margin is consistency, not a scientific justification that 0.10 is the right value: it is a
concession, for the maintainer's approval.

## CI (#210)

The longest job reached 37 minutes after the WP3 (b) proof entered `rest` (373 s locally). Proposal: move
`tests/test_v051_accept_wp3b_series.py` to `heavy-b` (274 s locally, then about 647) and
`tests/test_population_v3_identity.py` (167 s) to `heavy-c` (747 s, then about 915). `rest` falls from about 2,007 to about
1,467 local seconds, a proportional forecast of about 27 minutes on the slowest job. Exact test coverage is preserved, and
every OS, Python and shard job is to be checked below 30 minutes after the change. Nothing is changed in this stage.

## `.cache/v04` (examined; nothing deleted)

Every entry has one disposition in [`cache-v04-disposition.json`](cache-v04-disposition.json), with its literal path and
size, for the maintainer's approval:

| Disposition | Entries | Size | What |
|---|---|---|---|
| KEEP | 4 | 780 MB | `tools`; `pilot` (read by v0.5's C2 and its protocol, section 4); `inputs-attempts` (read by `discover/steps.py`, named by `calibration/v0.4/inputs.json`); `tess-eb` (the reproductions' local frozen copy, never on the public Drive) |
| CHECK_THEN_DELETE | 2 | 247 MB | `inputs-archive`, after a SHA-256 check against its Drive copy `arquivo-v0.4-inputs`; `reexport`, an empty folder |
| ARCHIVE_THEN_DELETE | 194 | 27 MB | the closed packages' folders and loose logs, process files, commit messages and comment drafts, to the Drive with a checked SHA-256 manifest |

Deletion only by literal path with a prefix guard, and only after that approval.

## What is asked of the maintainer at this stop

1. The acceptance: the specification above, `G_min`, the availability floor, `T`, the sector list, and the grouping.
2. The matched estimator: none qualifies under the frozen rule; which direction to design.
3. The sinusoid: the unresolved conflict between the 0.0027 limit and detectability within one resolution unit.
4. The D1 margin.
5. The T3b pool: whether to approve reading the TESS Ten Thousand table (a download of third-party data), and the
   sampling-frame amendment.
6. Stage 2's caps.
7. Sabotages whose effect was not distinguishable.
8. **One disagreement with Codex (E3 round 3, objection 3; E2 round 2, objection 3):** it asks for live termination of
   workers at each experiment's cap; these experiments enforce the cap per batch, with a reserve and a persisted state,
   which is a **budget guard, not a hard maximum**: sizing a batch from a mean cost does not bound an executing batch's
   overshoot. Claude's argument: a cap of 1.5 to 3 hours inside a 12-hour stage cap does not justify killing workers, and
   the overshoot is small and recorded. Codex's argument: a mean-based estimate cannot enforce a stated hard maximum, and
   a run can end above it. The stage's total is well within its cap.
9. The CI rebalancing and the `.cache/v04` proposal above.

## Use of the caps

Reconciled in the ledger `.cache/v052/cost.jsonl` (a retrospective reconstruction from dated sources: each line names its
provenance):

| Item | Processor-hours | Source |
|---|---|---|
| E1 final run | 2.482 | records |
| E1 earlier runs | 0.118 and 0.057 | records |
| E2 final run and earlier | 0.675 and 0.049 | records |
| E3 final run | 0.819 | records |
| E3's three stopped probes | 0.197, 0.210 and 0.200 | records |
| Worksheet scan | 0.084 | estimate from `worksheet-probe.json` |
| Worksheet C1 curves | 0.509 | curves x mean cost |
| E3 timing and scaling tests | about 0.15 | estimate by hand, no record kept |
| **Known total** | **about 5.55 of 12** | |

Worker start-up, imports and summary steps are in no record and are not counted. **One deviation:** E1's frozen allocation
was at most 2.5 processor-hours; its final run was 2.482, and with its two earlier smokes the aggregate is 2.657, above the
allocation. The stage cap of 12 is not affected. Agent time: stage 1 began at 14:28 UTC on 2026-11-08 by the session's
clock, and the ledger lists the commit times; this is wall time of the session, not active work, and the 1.5-day cap was
not approached. Disk: under 0.1 GB.

## Literature (read on 2026-11-08 unless stated)

- Jennison and Turnbull 1993, "Sequential equivalence testing and repeated confidence intervals", Biometrics 49, 31:
  https://pubmed.ncbi.nlm.nih.gov/8513110/ (search excerpt; not read in full).
- Howard, Ramdas, McAuliffe and Sekhon, "Time-uniform, nonparametric, nonasymptotic confidence sequences":
  https://arxiv.org/abs/1810.08240 (search excerpt; not read in full).
- Others: the scope proposal's list.
