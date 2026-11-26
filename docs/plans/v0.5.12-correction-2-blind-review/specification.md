# Battery version 5: the screen's specification (v0.5.11, step 0)

> **Status.** This is step 0's output under the charter
> ([v0.5.11-charter.md](v0.5.11-charter.md), approved at `eb70c13`).
> - It is frozen when its commit and SHA-256 are recorded in #218 after Codex's rounds.
> - A later change is a separate dated file.
> - This text applies Codex's blocking items of step 0's first round (`REFUTED`), recorded in
>   [v0.5.11-consensus/](v0.5.11-consensus/README.md).
>
> **Labels.**
> - `exploratory`, `method_status: not_validated`. Level 2 carries 'WEAKENED; does not meet D1,
>   D2, D4, T2a'.
> - Nothing here is a verdict, an acceptance or a claim.
> - Version 5 is not adopted for confirmatory use.
> - No population target is set: A1 to A3 belong to v0.5.12.
>
> **Sources.**
> - The equations and thresholds:
>   [sources/v0.5.11-screen-papers-2026-11-24.md](sources/v0.5.11-screen-papers-2026-11-24.md).
> - What was read:
>   [../validation/v0.5.11/source-manifest.json](../validation/v0.5.11/source-manifest.json).
> - Every choice that is this specification's own, and not the paper's, is marked **[choice]**.
>   A formula or a domain left unresolved is **unavailable**.

## 1. Outputs and the handoff from level 2

A version-5 analysis returns:
- **level 2:** version 2's analysis, unchanged;
- **level 1:** one new field, `screen` (section 3).

Version 5 runs the version-2 path with the same inputs, configuration, roles, stage, seeds and
error behavior.

**The screen's inputs** are exactly:
- the version-2 gauntlet's transit-masked flattened curve, `GauntletOutcome.flattened`: the curve
  on which the final candidate was fixed (`pipeline.attack_candidate`);
- the final candidate, `GauntletOutcome.candidate`: period P, epoch t0 and duration T, in days;
- for report-only F3 only, the star record.

The screen never writes to them. It never reads the search-detrended curve.

## 2. Identity and integrity (A4, A5): software invariants

- **A5, identity.** For the same inputs, version 5 and version 2 give the same canonical bytes of
  the legacy outputs, through every supported entry point:
  - **`analyze_data` and `conclude_analysis`:** the verdict, its reason, the list of test
    results (`TestResult.to_dict`), the decisive and diagnostic sets, the deferred tests and the
    stage;
  - **`discover.measure.chain`:** every field, the stage verdict and its reason included;
  - **`TessAnalyzer.analyze`:** the result record of `build_result`;
  - **`TessAnalyzer.error_result`:** the error record.

  Every legacy error keeps its type and message. The only differences allowed:
  - the field `screen`;
  - the recorded `discovery_version` (5);
  - the plan's own `entry` field (section 3).
- **A4, integrity.**
  - The verdict can be SURVIVED only when every expected decisive test was assessed: today's
    `aggregate`, kept as it is.
  - The screen can be `retained` only when every required core test was assessed.
- **Separation.**
  - Screen results are never passed to `aggregate`, `aggregate_roles`, `enforce_coverage`,
    `enforce_sensitivity` or `defer_tests`.
  - The screen draws no random number.
  - A report-only outcome (computed, unavailable, or past its displayed paper threshold) changes
    only its own record. It never changes `outcome`, the core, eligibility, or level 2.
- **Versions 1 to 4.** Every comparison such as `version >= 2` or `version >= 3` becomes an
  explicit version set. Version 5 joins version 2's set (the `stronger` section and the v0.5
  tests), and no other. `centroid_v5` and `power.candidate_seed` are not edited.

## 3. The screen record and the plan

**The plan's `entry`.**
- `discovery.entry` is a new optional field.
  - **Version 5** requires `entry: search`. Any other value is refused when the plan is
    validated.
  - **Versions 1 to 4** refuse an authored `entry`.
- An absent `entry` is left out of the plan's dump, so the resolved bytes of every plan of
  versions 1 to 4 do not change.

```
screen:
  version: 5
  spec_sha256: <SHA-256 of this file's frozen bytes>
  entry: "search"
  eligible: true | false
  outcome: "retained" | "rejected" | "unassessed" | null
  reason: <text>
  core: {F1: <core test>}                 # {} when not eligible
  report_only: {F1_trap, F2, F3, F4, U1}  # {} when not eligible
  labels: ["exploratory", "method_status: not_validated"]
<core test>:  state "pass" | "fail" | "not_assessed"; reason; coverage; coverage_unit; metrics;
              threshold
<report-only>: state "computed" | "unavailable"; reason; coverage; coverage_unit; metrics;
              paper_thresholds (display only)
```

- **Eligibility.**
  - The gate test `snr` is present and PASS in the version-2 analysis's final results: after
    `enforce_coverage`, `enforce_sensitivity` (version 2's rule) and `defer_tests` at the run's
    stage.
  - The final candidate has a finite P > 0, a finite t0 and a finite T > 0.
  - Otherwise `eligible` is false, `outcome` is null, `core` and `report_only` are empty, and no
    screen computation runs.
- **Precedence.** The first rule that applies decides:
  1. not eligible: null;
  2. a core test is `fail`: `rejected`;
  3. a core test is `not_assessed`: `unassessed`;
  4. otherwise: `retained`.

## 4. The core: F1, by OE_box only

The core is **F1, decided by OE_box alone** (K25 IV.4, Eq. 11, threshold 3):
- `fail` if OE_box > 3;
- `pass` if OE_box ≤ 3;
- `not_assessed` if OE_box is not computed (section 6).

No other statistic can decide F1. The trapezoid forms are report-only.

**Why the threshold 3 applies to this estimator.**
- OE_box is the absolute difference of two depths divided by the standard error of that
  difference. K25 defines the depths and their noise in II.1 (the weighted box depth and the
  pink noise of Eq. 2); this estimator is that one, with the choices of section 5 marked.
- Under the null of equal depths, with the noise correctly estimated, OE_box is the absolute
  value of a standard normal variable. "OE_box > 3" is then a three-standard-error rule, whatever
  the code that computes it, provided the noise is calibrated.
- That proviso is checked, not assumed. **Step 1's calibration rule** is fixed here before any
  code, in Codex's wording of step 0's second round:

  > F1 is the sole exploratory core at freeze. Step 1 uses a test-only reference evaluator of the
  > frozen equations, with no `src/` change. For each seed 1–200, call the unchanged baseline
  > `synthetic.make_lightcurve(PLANET, seed=seed)` with its defaults for white noise, and with
  > `**CORRELATED_PROFILE` for correlated noise. Use the true P, t0 and T. Record assessed,
  > unavailable and `OE_box > 3` counts per family. Each family must have all 200 results
  > assessed and at most four exceedances. A failed reference check stops the phase before
  > Step 2. Step 2 must reproduce the reference decisions on the same fixtures. This is a
  > software check on two fixed noise families. The weighted noise formula remains an
  > exploratory approximation for unequal weights, and the check establishes no population error
  > rate.

  - The expectation is about 0.5 exceedances of 200 under exact calibration.
  - **If either family fails** (a result not assessed, or more than four exceedances):
    - the threshold has no effect;
    - F1 becomes report-only, and the core is empty;
    - the phase **stops before step 2**, as the charter's empty-core stop requires.

    The rule is not tuned after the fact.

**Why the legacy tests are not core** (Codex's wording of step 0's first round):
- The 295-row table of step 0's recount is a descriptive replay of recorded statuses, before any
  filtering for gate passage or TOI identity.
- Among the 100 matched, gate-passing planet records, the tested legacy subset yields 82
  retained, 1 rejected and 17 unassessed. That is Codex's recount, not a table of
  `recount.json`.
- In the full planet arm, 14 of 28 unassessed rows have at least one sensitivity refusal.
- This motivates excluding the legacy tests from the exploratory core. The assessability of the
  new tests remains unknown.
- The legacy tests keep deciding the verdict, and they are reported beside the screen,
  unchanged. The centroid (pixel level) and the catalog test are outside the screen.

## 5. Shared quantities (frozen numerical choices)

Times are in days.

**Valid points:**
- t, f and σ finite, and σ > 0. The others are dropped and counted (`dropped`).
- The weight is w = 1/σ².
- Fewer than 20 valid points: every test is not assessed or unavailable **[choice]**.

**Weighted statistics [choice]:**
- the mean x̄ = Σwx/Σw;
- the standard deviation s = √(Σw(x−x̄)²/Σw);
- an empty set has neither.

**Epochs:**
- k = ⌊(t − t0)/P + 0.5⌋ **[choice]**: a tie goes to the later epoch.
- The in-transit set is |t − (t0 + kP)| ≤ T/2, inclusive.

**The circular phase distance** to phase φ, in days:
- d(t, φ) = |((t − t0 − φP + P/2) mod P) − P/2|, with `numpy.mod`.

**The out-of-transit baseline** [choice]: the points with d(t, 0) > T (strict). Every box depth
uses this one baseline.

**White noise** (K25 II.1): σ_w is the weighted standard deviation of the baseline.

**Red noise** (K25 Eq. 3) **[choice in each step]:**
- Bins of width T over the baseline, with edges t_b + mT, where t_b is the first valid time.
  Bin m holds t_b + mT ≤ t < t_b + (m+1)T.
- Only bins with n_b ≥ 2 are used.
- σ_bin is the weighted standard deviation of the bins' weighted means, each weighted by the
  bin's total weight.
- σ_bin,xpt² is the mean over the used bins of σ_w²/n_b.
- σ_r² = max(0, σ_bin² − σ_bin,xpt²) (K25).
- Fewer than 3 used bins: the noise is **unavailable**.

**Pink noise** (K25 Eq. 2): σ_tr(n, N) = √(σ_w²/n + σ_r²/N).
- n is the number of in-event points, and N the number of distinct epochs among them.
- A σ_tr that is not finite and positive is unavailable.

### Report-only MES series (for F2 and U1)

- **The box depth at phase φ:** δ(φ) = x̄(baseline points with d(t, φ) > T) − x̄(points with
  d(t, φ) ≤ T/2). N counts the distinct values of ⌊(t − t0 − φP)/P + 0.5⌋ among the in-event
  points.
- **The grid [choice]:** φ_j = j·(T/4)/P, for j = 0 … ⌈4P/T⌉ − 1.
  - Before the grid is allocated, it is **unavailable** if 4P/T is not finite or exceeds the
    number of valid cadences. That bounds the work as T/P approaches zero.
  - A cell needs at least 3 in-event points and 10 reference points.
  - MES_j = δ(φ_j)/σ_tr is positive for a dip.
- **The events [choice: ties to the smallest j; distances are circular, in days]:**
  - pri: the largest MES;
  - sec: the largest MES at least 2T from pri;
  - ter: the largest MES at least 2T from pri and sec;
  - pos: the largest −MES at least 3T from pri and sec.

  An event with no candidate cell is unavailable.
- **F_red [choice]:** the standard deviation (denominator n) of MES over the cells at least 2T from
  pri and sec. It needs at least 10 cells. Zero or unavailable makes MS1 and MS4 unavailable.
- **FA1 and FA2:** FA1 = √2·erfcinv(T/(P·N_TCE)) and FA2 = √2·erfcinv(T/P), with
  `scipy.special.erfcinv` (T18 A4, A5).
  - **N_TCE = 1 [choice]**, which makes FA1 = FA2. T18's across-TCE correction is therefore
    absent, which is one reason F2 is report-only.
- **MS1 to MS6:** K25 Eqs. 7 and 9.

### Report-only trapezoid (F1_trap, F3, F4)

**The model** (K25 II.2): m(t) = f0 − δ·s(t).
- s = 1 for |Δ| ≤ qP/2 − τ, falling linearly to 0 at |Δ| = qP/2, and 0 beyond.
- Δ = ((t − t0 + P/2) mod P) − P/2, and τ = q_in·qP.

**The data:** points with |t − (t0 + kP)| ≤ 2T.

**The parameters [choice]:**
- P is fixed at the candidate's period: the version-2 path fixes it.
- Free: t0 ∈ [t0_c − T/2, t0_c + T/2], δ ∈ [0, 1], q ∈ [T/(10P), 0.5] and f0 ∈ [0.5, 1.5].
- Start: t0_c, the box depth δ(0) clipped into its bounds, q = T/P clipped, and f0 = 1.

**The fits [choice]:**
- Reduced fits with q_in fixed at 0.1, 0.15, 0.2, 0.25, 0.3, 0.35 and 0.4 (K25). The lowest χ²
  wins; a tie goes to the first in this order.
- The final fit has q_in ∈ [0, 0.5] (K25).
- **The solver:** `scipy.optimize.least_squares`, `method="trf"`, `x_scale="jac"`,
  `ftol = xtol = gtol = 1e-10`, `max_nfev = 2000`, residuals (f − m)/σ.
- **Converged:** `status > 0` and finite parameters.

**The uncertainties [choice]:** √diag((JᵀJ)⁻¹·χ²_red), with χ²_red = Σr²/(N_pts − k). They are
**refused** (unavailable) when:
- a parameter is at a bound (`active_mask ≠ 0`);
- the condition number of JᵀJ exceeds 1e12;
- or N_pts − k < 1.

**Per parity (F1_trap):** only δ and t0 are free (K25). The other parameters are fixed at the
final overall fit, which must be converged.

## 6. The tests

### F1, core: OE_box. Coverage unit: "parity epochs with data"

- **Its inputs:**
  - δ_par = x̄(baseline) − x̄(in-transit points of that parity), where parity is k mod 2;
  - σ_par = σ_tr(n_par, N_par).
- **OE_box** = |δ_odd − δ_even| / √(σ_odd² + σ_even²) (K25 Eq. 11).
- **Computed only when:**
  - each parity has at least one epoch with at least 3 in-transit points, and n_par ≥ 3
    **[choice]**;
  - the baseline has at least 10 points;
  - the noise is available;
  - every quantity is finite, and the denominator is positive.

  Otherwise F1 is `not_assessed`, with the reason.
- **Coverage:** the number of distinct epochs with at least 3 in-transit points.
- **Recorded:** δ_odd, δ_even, σ_odd, σ_even, n_odd, n_even, N_odd, N_even, OE_box, σ_w and σ_r.

### Report-only

Each is `computed` or `unavailable`, with its paper thresholds shown for reference only.

**Coverage and conditions** (Codex's wording of step 0's second round):

> Each report-only record includes `coverage` and `coverage_unit`. Use valid fit cadences for the
> trapezoid outputs, with counts by parity for F1_trap, and valid phase cells for F2 and U1. F4
> additionally requires at least one valid cadence strictly inside the fitted flat interval.
> Before allocating the MES grid, mark it unavailable if `4P/T` is nonfinite or exceeds the
> number of valid cadences. Record `would_be_significant` and `exception_first_condition` as
> null when their required inputs are unavailable. The depth comparison requires finite depths
> and `δ_pri > 0`. Exercise a dedicated diagnostic failure in Step 1 and assert that only its own
> record changes.

The coverage units:
- **F1_trap:** "fit cadences", by parity;
- **F2 and U1:** "phase cells with data";
- **F3 and F4:** "fit cadences".
- **F1_trap:** OE_trap and OE_trap,T (K25 Eqs. 12, 13). Paper thresholds: 3 and 10.
- **F2:** MES_pri, MES_sec, MES_ter and MES_pos with their phases; δ_pri, δ_sec, F_red, FA1,
  FA2, MS4, MS5 and MS6.
  - Also recorded: the K25 significance conjunction and the occultation branch, as they would
    read (`would_be_significant`, `exception_first_condition`).
  - The F2 domain is T/P ≤ 0.1 **[choice]**.
- **F3:**
  - Rp = R⋆·√ΔF (SM03 Eq. 6), with ΔF = δ_trap/f0, f0 > 0 finite and 0 < ΔF < 1, from the
    converged overall trapezoid.
  - R⋆ comes from the star record, only under the legacy plausibility rule's reliability
    conditions (`PlausibilityParams`): a relative error of at most
    `max_stellar_radius_rel_err`, and a TIC disposition not in `unreliable_tic_dispositions`.
  - Paper threshold: 22 R⊕ (K25, for a limb-darkened fit).
- **F4:**
  - V = √ΔF + b, with b from SM03 Eq. 7.
  - t_T = qP and t_F = qP(1 − 2q_in), which needs q_in < 0.5, a resolved flat bottom.
  - It also needs a finite, positive denominator 1 − sin²(t_Fπ/P)/sin²(t_Tπ/P), and a
    non-negative bracket.
  - Paper threshold: 1.5 (K25).
- **U1:** MS1, MS2 and MS3. Paper thresholds: 0.2, 0.8 and 0.8 (K25). U1's own thresholds come
  only from v0.5.12's frozen calibration.

## 7. Rules (rule (b) of the charter)

- **Aggregation:**
  - sectors to target: the gauntlet curve of section 1, every sector together;
  - events to test: sections 5 and 6.
- **Invalid values:** NaN, infinite, or outside a stated range give `not_assessed` for F1 and
  `unavailable` for report-only, with the reason. They never give a pass or a fail.
- **Availability:**
  - F1 needs the curve and the candidate.
  - F3 also needs the star's radius under the legacy rule.
  - F3 and F4 need the converged overall trapezoid.
- **Ties:** section 5.
- **Vocabulary:**
  - `retained`, `rejected`, `unassessed`;
  - `pass`, `fail`, `not_assessed`;
  - `computed`, `unavailable`.

  Never a verdict word.
- **Determinism:** no random number, fixed grids, fixed starting values and a fixed solver. The
  same inputs give the same bytes.

## 8. What the synthetic tests must show (step 1)

- **The calibration rule of section 4,** exactly as written, with a test-only reference
  evaluator of the frozen equations. Step 2's implementation must reproduce the reference
  decisions on the same fixtures.
- **A dedicated report-only failure** (for example F4 past 1.5, or F2 would-be significant):
  only its own record changes.
- **F1:**
  - planets pass;
  - binaries at half the period with unequal depths (`odd_depth_factor` 0.75 or less) fail;
  - every `not_assessed` path is reached (too few points per parity, an empty baseline, the
    noise unavailable, a non-finite input).
- **Report-only:** each `unavailable` path is reached. A report-only quantity past its paper
  threshold changes only its own record.
- **Eligibility:** a failed or deferred gate gives `outcome: null` and empty maps.
- **A4 sabotage:**
  - an expected decisive test INCONCLUSIVE or missing can never give SURVIVED;
  - a core test `not_assessed` can never give `retained`.
- **A5:**
  - version 5 against version 2 on the synthetic fixtures, through the four entry points of
    section 2, including an error case per entry point;
  - versions 1 to 4 against the golden snapshot;
  - `entry` refused for versions 1 to 4, required for version 5, and absent from the
    version-1 to version-4 dumps.

## Appendix: not adopted

The draft specification's parts listed here stay a draft. Nothing in v0.5.11 depends on them:
- the entry rule E and its probes;
- the consensus;
- the paired panel;
- f\*, q (the draft's), n_min and N;
- both uses of 0.10;
- the calibration sizes of the draft's 3.7.
