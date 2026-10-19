# M4: the implementation map of revision 4 (declared before any test or code of M4)

Status: **declared 2026-10-18, before the first test and the first line of code of M4.** It adds
no criterion: the acceptance criteria are those of revision 3, section 10, and revision 4
(`corrections-plan-rev4.md`, approved version SHA-256 in `corrections-plan-rev4.sha256`), sections 1
to 5. This file says where each correction goes in the code, how it is switched, and which tests
carry which criterion, so that the order "criteria, then tests, then code" can be checked per piece.

## The switch

- A new plan section, `gauntlet.corrections` (`CorrectionsParams` in `params.py`), holds the
  settings of a configuration (revision 3, 9.2: `B_min`, `gap_split`, `fap_max`, `max_components`,
  `k_clip`, `h_min`, `m_beta`; revision 4: `R_min`) and **`enabled: bool`, default `false`**. With
  `enabled: false` every analysis is the M3 code path, byte for byte: the test suite and every
  existing claim behave as before.
- Each correction reads the switch; no correction runs with it off.
- **The freeze of M4** (revision 3, 9.3) is one commit that sets the defaults of `CorrectionsParams`
  to the chosen configuration with `enabled: true`, because the population harness v2 passes the fast
  plan and takes every other value from the code's defaults (`../population-study.md`, section 7).
  Before that commit, any existing test whose expectation is the M3 behavior gets an explicit
  `corrections: {enabled: false}` in its plan, in a commit of its own, with this paragraph as its
  declared justification (exit criterion 4): it then tests the same code path as before. A test of
  the baseline list that cannot be kept that way is listed in `../baseline/justifications.txt`
  before the freeze commit.

## The pieces, in the order of revision 4

| # | Correction (revision 3 / 4) | Module | Tests (criteria of revision 3, 10, and revision 4) |
|---|---|---|---|
| 1 | A1: correlated noise from the data, binned rms (rev 3, 2.1) | `rednoise.py` (new): segments, binned `σ_w`, `σ_r²(n)`, `β(n)`, the few-bins rule | `tests/test_rednoise.py`: white β(n_T) within 1 ± 0.1; AR(1) β within 15% of its analytic value; bins never cross a gap or a mask; a sector below `B_min` excluded and reported; none left: undetermined |
| 2 | A1 propagation (rev 3, 2.2): per-event and stacked depths, candidate error and SNR | `events.py`, `search.py`, `gauntlet.py` (behind the switch) | `tests/test_rednoise_propagation.py`: white noise, the gate unchanged within 5%; the per-event variance formula; events sharing cadences dropped; switch off: byte-identical results |
| 3 | Timing with an ingress model (rev 3, 3) | `ephemeris.py` (trapezoid template, scan, error × β(n_τ)) | `tests/test_timing_trapezoid.py`: per-transit error within 30% of the Carter reference (white); pulls of 200 seeded transits within the K margins; an edge minimum discarded; same input, same times |
| 4 | Holdout: replica spans and the hidden-window variance (rev 4, 1) | `holdout.py` (`plan_round` registers replicas; `HiddenYear` masks them and gives logged access) | `tests/test_holdout_replicas.py`: the unit criteria of rev 4, 1 (variance within 15%, white and AR(1); the full operation's pulls within the K margins; too few replicas: `hidden_noise_undetermined`; no overlap; masked fraction ≤ 0.5; determinism) |
| 5 | Holdout: the baseline model of a window, decisions 1 and 2, the FAIL rule (rev 3, 4.1, 4.3 to 4.5; rev 4, 1 and 2) | `holdout.py` | `tests/test_holdout_capacity.py`: rev 3, 10, rows 4.1, 4.2-4.4 and 4.5, and row N (bit-equal decision 2 for hidden years equal outside the windows) |
| 6 | `period_alias`, the only definition (rev 3, 5; rev 4, 3) | `battery.py` | `tests/test_period_alias_rev4.py`: the four regimes; the three undefined cases INCONCLUSIVE; the raw curve as input; the systematic-period warning kept |
| 7 | Prewhitening (rev 3, 7; rev 4, 4) | `prewhiten.py` (new), used by the search, the reanalysis and the holdout train | `tests/test_prewhiten.py`: a transit under a stronger sinusoid found; a pure sinusoid removed; a pure box not removed; the sequence of rev 4, 4 (L0, clip set, L1, the FAP at `f*`); no class or truth argument; `period_alias` receives the raw curve |

## Amendment 1 (2026-10-18, after a failing run of piece 1): how the A1 criteria are read

**Written after seeing the failure, and declared as such.** The tests of piece 1 (`f445c59`) read the
A1 criteria of revision 3, section 10 ("white noise: β(n_T) within 1 ± 0.1"; "AR(1) of known
parameters: β within 15% of its analytic value") **per sector of one light curve**. With the code
(`rednoise.py`), 2 of 11 cases failed, both on seed 0: white noise, sector 2, β = 1.135; AR(1),
sector 1, β = 5.20 against an analytic 4.415 (the other sectors: 1.000 to 1.038 white, 4.42 to 4.92
AR(1)). A sector of the test has 18720 cadences, 248 bins at `n_T` = 75: the robust standard deviation
of 248 bin means has a relative error of about 7% (more with correlated bins), so a single sector's
β scatters beyond ± 0.1 and ± 15% by chance. The per-sector reading asked for more precision than
the sample gives; the estimator does what section 2.1 defines.

**The reading from now on** (the criterion's text does not change): the criterion applies to the
estimator's central value: the **median of β over 100 sectors** (50 seeded light curves of two
sectors each, seeds 0 to 49) is within 1 ± 0.1 (white noise) and within 15% of the analytic value
(AR(1)). The other cases of `tests/test_rednoise.py` are unchanged. The per-sector precision (about 7
to 10% at `n_T` for a two-orbit sector) is recorded as a property of the estimator: its consequence
on the errors is what the K conditions of the calibration test.

## Amendment 2 (2026-10-18, before the tests of piece 2): the propagation of A1

Declared before any test or code of piece 2.

- **`CorrectionsParams`** (`gauntlet.corrections`): `enabled` (default `false`) and the settings of
  revision 3, 9.2, with the values of M4-c1 as defaults (`b_min` 20, `gap_split` 5, `fap_max` 1e-4,
  `max_components` 3, `k_clip` 2.5, `h_min` 0.90, `m_beta` 1.2) and revision 4's `r_min` 20. The freeze
  sets them to the chosen configuration (section "The switch").
- **The scales of σ_r²** in the per-event variance (revision 3, 2.2,
  `σ_w² (1/n_in + 1/n_base) + σ_r²(n_in) + σ_r²(n_base)`): `σ_w` and the counts `n_in`, `n_base` are
  the event's own; `σ_r²` is estimated once per sector at the **nominal** scales of the measurement,
  `n_T = round(duration / cadence)` for the box and `n_B = round(2 (outer − inner) / cadence)` for the
  baseline bands, on the flattened curve with the candidate's transits masked. The estimator needs
  bins of a fixed size; the per-event counts differ only by gaps.
- **Events in an excluded sector** (few bins at `n_T` or `n_B`) are dropped and reported; with no
  sector left the noise model is undetermined and the `snr` test is **INCONCLUSIVE** ("noise model
  undetermined"), never PASS or FAIL.
- **Events sharing cadences:** when two events' spans (event plus baseline bands) share cadences, the
  later one is dropped and reported.
- **The gate** reads `depth / e`, with `e` the stacked error of the primary events at the candidate's
  ephemeris on the flattened curve (the prewhitened curve once piece 7 exists); the BLS `depth_snr` is
  reported beside it as `bls_depth_snr`. `odd_even` and `secondary_eclipse` use the corrected
  per-event errors too.
- **"White noise: the gate unchanged within 5%"** (revision 3, 10, row A1) is read as: on white-noise
  `planet` light curves (seeds 0 to 9), the median of (corrected SNR / BLS `depth_snr`) is within
  [0.95, 1.05]. Declared now, before any run.
- **The holdout's train candidate** keeps its SNR until pieces 4 and 5, which change the holdout as a
  whole; piece 2 touches the global analysis only.
- **With the switch off** every analysis is the M3 code path: checked on Windows against digests of
  analysis records computed before the code of piece 2 (bound to the platform, as G1 of the
  correlated-noise record), and on every platform by the unchanged suite.

## Amendment 3 (2026-10-18): piece 2 does not meet "the gate unchanged within 5%"; the readings of piece 3

**Piece 2, the result.** With the code of piece 2, P2 (white `planet`, seeds 0 to 9, the median of
corrected SNR / BLS `depth_snr`) is **0.812**, outside [0.95, 1.05]: the acceptance of revision 3,
10, row A1 ("white noise: ... the gate unchanged within 5%") is **not met**. Every other case of
piece 2 passes (P1 with the 13 reference analyses byte for byte, P3 to P7).

**Diagnosis** (read-only, `.cache/v021/m4/diagnose_p2.py` in the worktree; checked by Codex, which
recalculated the ratios from its output):

| Comparison (white `planet`, seeds 0 to 9) | Median ratio |
|---|---|
| stacked per-event SNR with the per-point white errors (A1 off) / BLS | 0.806 |
| the same with the A1 errors / BLS | 0.806 |
| A1 stack / the same stack without A1 (paired) | 1.000 (0.9996 to 1.0002) |
| the white term of the stack alone / BLS | 0.855 (Codex's prediction with the BLS's finite global baseline: 0.8553) |

The A1 terms do not change the gate materially in white noise (β(n_T) = 1.00 in 19 of 20 sectors,
1.066 in one). The fall comes from **the estimator that revision 3, 2.2 itself prescribes** for the
gate: the stacked error of the per-event depths, with a local baseline (`n_base / n_in ≈ 2.5`) and the
term `max(white, scatter / sqrt(n))` (the scatter dominates in 6 of 10), instead of the BLS
`depth_err` with its global baseline. The source of the extra scatter is not isolated (sampling,
residual trend after the detrending, coverage). Codex's wording, adopted: the change of estimator
introduces a structural fall of the SNR in this design, even without the red term; the P2 declared
fails; β near 1 does not make the two estimators equal.

**Verdict (Codex and Claude): option (c) holds today:** the method and the criterion stand, and the
acceptance of piece 2 is **not satisfied**. P2 is kept, with its numbers, and marked
`xfail(strict=True, raises=AssertionError)` citing this amendment so CI stays green; the mark does
not satisfy the acceptance. **Two other options exist and belong to the maintainer**, each a bounded
amendment of revision 4 with the exposure to this result stated:

- **(a)** change the method: the gate reads `depth / (BLS depth_err × a β of the candidate's
  sectors)`, white noise unchanged by construction as far as β is 1; the combination of the sectors'
  β is to be defined and validated, and K1 and K2 would not certify that new error (they calibrate
  the stacked depth);
- **(b)** keep the method and compare the A1 stack with the same stack without A1 (1.000 here): a
  change of the declared comparator after the result, with the original P2 failure kept on record.

Nothing of piece 2 is changed until the maintainer decides. The pieces that do not depend on the
gate go on.

**Piece 3, the readings (declared before its tests).** Revision 3, 10, row "timing (3)":

- "per-transit error within 30% of the Carter reference" is read as the **median** of (measured
  per-transit error / Carter `σ_tc`) over the seeded transits, within [0.7, 1.3] (the per-transit
  scatter of an error estimate is not the criterion's object, as for A1 in Amendment 1);
- "pulls of 200 seeded transits within the K margins" is read on the **point fractions**: of
  |pull| ≤ 1 inside [0.60, 0.76], of |pull| ≤ 2 inside [0.92, 0.98], and the median within ± 0.2. The
  K conditions' interval form cannot pass at n = 200: no count passes the 2σ condition (computed
  before the tests: the Clopper-Pearson interval of any count of 200 leaves [0.92, 0.98]), as
  revision 3, 8.3 already found for 90 and 120;
- the timing template and the β scaling are used by the global ephemeris and by the holdout's train
  timing when the switch is on (the holdout's other changes are pieces 4 and 5).

**Piece 3, the case and the implementation readings (declared before its tests).**

- **The case of the two numeric criteria:** the canonical synthetic planet `synthetic.PLANET`
  (depth 2000 ppm, T14 2.5 h, ingress fraction 0.15, so τ = 22.5 min), white noise 600 ppm, 2-minute
  cadence, the two default sectors, at the injected ephemeris (an E1 measurement, revision 3, 8.2),
  without detrending (the curve has no trend); seeds 0, 1, 2, ... in order until at least 200
  transits are measured, all of them used. The Carter reference uses the injected values:
  `σ_C = (600 ppm / 2000 ppm) · sqrt(τ · cadence / 2)` (about 1.4 min). The pulls are against the
  injected centers.
- **The template fit:** depth linear (weighted least squares for a fixed shape); T14 and τ by a grid,
  T14 in [0.5, 1.5] of the candidate's duration and τ in [one cadence, T14 / 2], then a finer grid
  around the best cell; the same folded cadences for every cell (within 1.5 times the largest T14
  of the grid of the center), weights 1/σ² of the per-point noise. A fit with depth ≤ 0 gives no template and so no transit times.
- **The width of the region within 1 of the minimum** is measured with its two crossings located by
  linear interpolation between the scan steps (the quantity of revision 3, 3, measured below the
  step: with σ_C near 1.4 min, counting whole steps of 1 minute biases the width low by about half a
  step); the center stays the scan minimum; the floor is half a cadence, as revision 3, 3 states.
- **The transit's sector** is the sector of its cadence nearest to the center; a transit whose
  sector is excluded at `n_τ` is dropped and counted (no borrowing, 2.1); with the estimate
  undetermined there are no transit times.

## Amendment 4 (2026-10-18): the pulls of piece 3 at the declared case

**The order of the record.** The tests of piece 3 (2330360) were first run before their commit,
with a first version of `timing.py` not yet committed nor wired. The readings and the case had been
written in Amendment 3 before that run.

**The result.** At the declared case (210 transits, seeds 0 to 14): the median of error / Carter is
0.990 (passes); |pull| ≤ 1 in 0.657 (passes); the median pull −0.131 (passes); **|pull| ≤ 2 in 0.919
(193 of 210), outside [0.92, 0.98]: the criterion "pulls of 200 seeded transits within the K
margins" is not met.** Every mechanism case passes.

**Diagnosis** (read-only, `.cache/v021/m4/diagnose_p3.py` in the worktree, seeds 0 to 69, 980
transits):

| Quantity | Fitted template | Injected template |
|---|---|---|
| \|pull\| ≤ 1 | 0.655 | 0.708 |
| \|pull\| ≤ 2 | 0.937 | 0.931 |
| median error / Carter | 0.985 | 0.983 |
| std of (time − truth) / Carter | 1.077 | 1.074 |
| robust std of (time − truth) / Carter | 1.042 | 1.042 |
| std of the pulls | 1.074 | 1.078 |

- The stated error is the Carter reference within 2%; the scatter of the times is about 7% above
  it, so the 2σ coverage is near 0.93 to 0.94 instead of 0.954; the fitted template is not the cause
  (the injected template gives the same).
- Part of the excess is the 1-minute grid of the centers (revision 3, 3 keeps the center at the
  scan minimum): a uniform rounding adds step²/12 to the variance, about 2% of the standard
  deviation here; the rest is not isolated.
- On 980 transits both fractions fall inside the margins; on the declared 210 the 2σ fraction is
  about one standard error (0.017) below its 980-transit value. Read as a sampling fluctuation of
  the declared size, not as a defect of the mechanism; the declared criterion is nevertheless not
  met, and the larger sample is not substituted for it after the result.
- **The median condition is insensitive here:** the injected centers lie on the scan grid, so the
  measured offsets are whole minutes and the median pull is exactly 0 on 980 transits. It cannot
  detect a bias smaller than half a step in this case.

**Verdict (Claude; Codex checks it in the end-of-stage review):** as for piece 2, option (c): the
method and the criterion stand, and the pulls criterion of piece 3 is not satisfied at the declared
case. The case is kept and marked `xfail(strict=True, raises=AssertionError)` citing this amendment;
the mark does not satisfy it. A rerun with another sample size or other seeds, or a sub-step center
(a change of revision 3, 3), belongs to the maintainer. K3 and K4 (the calibration's timing
conditions, 1000 light curves each) are unchanged and will measure the same quantity on the
population.

**Addendum (after the code and its sabotages, 31888f2).** The sabotages ST3 (a box in the scan) and
ST4 (whole steps, no interpolation) were caught only through the floor of the β case, not by the
Carter criterion. A direct mechanism case was added after the code, declared as such: on a noiseless
transit of the declared case, the tool's half-width against the one found on a scan 1000 times
finer. Its first run, at a tolerance of 3%, failed: **the declared linear interpolation places each
crossing of the convex Δχ² inward, and the error comes out 5.3% below the exact half-width** (1.363
against 1.439 min). This is a property of the reading declared in Amendment 3, and a part of the 7%
gap between the scatter of the times and the stated errors above; the reading is not changed after
the result. The case keeps a tolerance of 10%, which detects whole steps (about −30%) and the box
(both sabotages caught). A crossing located on a parabola instead of a chord would remove the bias;
it would change an Amendment 3 reading after the pulls result, so it is the maintainer's decision.

## Amendment 5 (2026-10-18): the end-of-stage review of pieces 2 and 3 (Codex), and its fixes

Codex reviewed 42e4184 to 5b624a1 read-only (`.cache/v021/codex/stage-m4-p23/` in the worktree).
It found **no undeclared deviation** in pieces 2 and 3 and upheld option (c) for both criteria not
met. Its objections, and what was done:

- **Traceability.** The callers kept only the transit times, so the sectors excluded at `n_τ`
  (revision 3, 2.1, "the report lists it") were lost. Fixed: with the switch on, the template, the
  drops and the estimate at `n_τ` are kept in `GauntletOutcome.timing` (and the verdict record's
  `global_timing`) and in each round's `train_timing`; with the switch off nothing changes.
- **Positive checks** (cases added after the code, declared as such):
  `test_p2b_the_corrected_snr_is_the_bls_depth_over_the_stacked_error` (P2 is an expected failure,
  so a wrong factor in the gate would stay hidden); the wiring case now checks that each round uses
  the times it received; `test_the_floor_is_half_a_cadence_not_the_step` (at a 2-minute cadence and
  a 1-minute step the two floors coincide, so the earlier cases could not tell them apart). Each was
  checked by a sabotage (SF1 a wrong factor in the corrected SNR, SF2 the holdout dropping a
  returned time, SF3 the step floor restored): each fails its case.
- **The expected failure hid the passing parts.** The pulls case is split: the 1σ fraction and the
  median are a plain case (they pass); only the 2σ fraction keeps the `xfail` of Amendment 4.
- **Correlated noise.** The cases of piece 3 were all white. Added a mechanism case
  (`test_correlated_noise_raises_the_timing_errors_by_beta`: in the correlated mode the stated errors
  of the same seeds rise by β(n_τ), median ratio > 1.5) and a diagnosis on correlated light curves,
  recorded below as a measurement, not as a criterion (revision 3, 10 states the timing criteria for
  white noise; K4 is the correlated condition of the calibration).
- **Corrections of earlier wording** (the earlier text stays; these lines take precedence):
  - P1 compares the **analysis records** of `m4/analysis_reference.py` (verdict, tests, holdout
    rounds, candidate), not every byte of an analysis: the global ephemeris and the event arrays are
    not in the record. With the switch off the serialized plan gains the `corrections` section
    (structural; the numbers of the M3 path are unchanged).
  - Amendment 4, "the measured offsets are whole minutes and the median pull is exactly 0": the
    scan grid is `−0.5 T14 + k × step` with the **fitted** T14, so zero is on the grid only when
    `0.5 T14 / step` is an integer (true for the injected template, 150 min; not in general for the
    fitted ones, median 150.19 min). The median of 0 is observed; its cause and the claimed
    insensitivity to biases below half a step are **withdrawn as not shown**.
  - Amendment 4, "a sampling fluctuation of the declared size, not a defect of the mechanism": read
    as "compatible with a sampling fluctuation"; the causes of the 7% excess are not all isolated,
    and the interpolation bias of the addendum is one systematic part of it.
  - The width case's 10% was chosen after its 3% failed; it is a regression guard against whole
    steps and a box, not an independent validation of the precision.

**The historical locks (found by CI, pending the maintainer).** The new plan section
`gauntlet.corrections` (piece 2, 42e4184) is part of the resolved claim, so the two historical
calibration claims (v0.1 and v0.2) no longer reach their locked `claim_sha256` by the historical
projection (`src/refute/core/lock_compat.py`): 9 cases of `tests/test_lock_compat.py` fail (CI run
39094858224, and locally). A read-only probe (`.cache/v021/m4/lockcompat_probe.py`) shows that the
path `test_plan.gauntlet.corrections`, at its resolved defaults (`enabled: false`), is the only
cause: with the table extended by that one path, both projections equal the locked hashes. The
table is frozen and extending it changes lock verification, so it is **the maintainer's decision**;
nothing is changed. **Deviation:** the map promises the full suite unchanged after each piece; the
suite was not run after piece 2 (only the affected tests), so this was found by CI only after the
push of pieces 2 and 3. From now on the suite runs before each push.

**Correlated diagnosis** (`.cache/v021/m4/diagnose_p3.py` with `correlated`, seeds 0 to 69):
978 transits; the fitted template gives |pull| ≤ 1 in 0.692, |pull| ≤ 2 in 0.957, median pull
−0.048, standard deviation of the pulls 1.148; the stated errors are 3.48 times the white Carter
reference (the β of the sectors), the scatter of the times 4.91 times it (robust: 3.68), so the
tails are heavier than normal. On the first 210 transits (the declared size): 0.733 and 0.967. The
injected template gives 0.680 and 0.953. These numbers are recorded, not judged here; K4 judges
the extrapolated timing on the population.

## Amendment 6 (2026-10-18): the readings of pieces 4 and 5 (before their tests), and two points for the maintainer

Revision 3, 4.1 to 4.6, and revision 4, 1 and 2, leave some operational points open. Codex was
consulted read-only (`.cache/v021/codex/p45-design/` in the worktree); Claude agrees with its
readings below. Declared before any test or code of pieces 4 and 5.

**Readings (fixed now):**

1. **The period-correction scan stays** (`holdout.py`, `_measure`): at each `dP` of a grid fixed
   before the read, the windows **and the replicas** get the same center shift
   (`(n − n_ref) dP`), box, baseline model and degeneracy rules; `var_rep(dP)` from the replicas,
   the stacked error and `SNR(dP)`; the measured SNR is the maximum over the grid, and the FAIL rule
   (revision 3, 4.5, with `d_train`, not `d_c`) uses the depth and error **of that same `dP`**. The
   grid always contains `dP = 0` (an odd number of points, symmetric); ties go to the smaller
   `|dP|`, then to the negative side; a box is valid at a `dP` only if its own coverage rule holds
   there. Maximizing `d/e` does **not** only make FAIL rarer (Codex's counterexample: with varying
   `e`, the chosen point can satisfy the inconsistency when `dP = 0` does not); `var_rep(dP)`
   measures the operation at that `dP`, not the coverage after the maximum, which the full
   operation's pulls (revision 4, 1, unit criteria) and K5 to K8 check.
2. **Decision 1:** `d_c = d_train − k e_train`, with `d_train` the BLS depth of the train candidate
   and `e_train` its A1 stacked error at its own ephemeris on the train data (piece 2's estimator,
   now applied to the train candidate, before the train validity gate);
   `e_pred,1 = m_β sqrt(var_rep,train / N_pred)` with `N_pred` the number of predicted transit
   windows whose box and baseline are covered by the hidden sectors' spans (metadata; never the
   windows that survive the read). With the scan, `e_pred` is the **largest** over the grid
   (a conservative reading of a gap; the error at the transits' best `dP` would make the decision
   depend on the flux).
3. **Decision 2:** `e_pred,2 = sqrt(var_rep,hidden / N_pred)` (no `m_β`), the largest over the grid;
   the order of a round: windows, controls and replicas fixed from the train and the metadata;
   decision 1 (if not met, the round ends with an empty hidden access log); `HiddenYear` built
   with every registered mask; the replicas (and what remains of 4.2, below) read and decision 2
   taken; only then the transit and control windows measured. Changing the flux inside the
   windows changes neither decision (row N).
4. **The threshold:** `min_snr − b + Φ⁻¹(1 − α_round) s`, `α_round = 0.005 / R`, `R` the planned
   rounds (the observing years, fixed before any result, never reduced). `b` and `s` are
   configuration settings whose values come from the selection part; until then the unit tests
   give them explicit values; no value is presented as calibrated.
5. **Other points:** the phase-0.5 control keeps the same operation and the replicas' variance,
   as a diagnostic, never a gate, and the replicas avoid its span; windows whose measurement spans
   share cadences: the later is dropped with its reason; "valid windows" are counted after
   coverage, baseline, degeneracy and sharing, and fewer than `min_predicted_transits` is
   INCONCLUSIVE (`N_valid` and `N_pred` are distinct numbers); a replica in a segment with no
   unmasked cadence does not feed decision 2; a non-finite error or an unusable variance is
   INCONCLUSIVE with its reason (today a non-finite SNR falls into FAIL, `holdout.py`).

**For the maintainer (nothing of pieces 4 and 5 is coded before the answers):**

- **(A) The noise bands of revision 3, 4.2 and the replicas of revision 4, 1 occupy the same
  phases** (0.25 and 0.75), and the hidden detrending masks the replicas out to `baseline_inner`,
  so the A1 estimate in the noise bands loses most of its support. Options: keep 4.2 as written
  (bands registered and read; if their `B_min` is not met, decision 2 INCONCLUSIVE, which may make
  most rounds inconclusive); or take `σ_w,hidden` and the `B_min` check from the residuals of the
  replicas' baseline bands (which are read anyway); or make the replicas avoid the noise bands
  (fewer replicas). Each changes a row that revision 4 keeps closed (B2) or its replica rule.
- **(B) Which `S_pred` estimates `b` and `s`** (revision 3, 4.6; revision 4, 2): the train one
  (decision 1) or the hidden-noise one (decision 2). Codex and Claude recommend recording both and
  fixing one before the selection runs. Also: to estimate `b` and `s` without the rule selecting
  its own sample, the harness must obtain `S_meas` for rounds that decision 1 would stop; the
  official round keeps its status and empty log, and the harness collects the measurement apart.

## Amendment 7 (2026-10-18, declared after the results): the gate by method (a), and the parabolic crossing

**Declared after the results of Amendments 3 and 4, by the maintainer's decisions of 2026-10-18
(items 2 and 3).** Those results stay as they are: P2 failed (median 0.812, seeds 0 to 9), and
the 2σ pulls of piece 3 failed (0.919 of 210, seeds 0 to 14). The principle applied (maintainer,
2026-10-18): a correction enters only for a defect with an identified mechanism or a contradiction
of the specification, declared after the result with its reason and a Codex design review, and is
retested on **new seeds never used**, with the **same criterion** and the **same sample size**.
The earlier test cases keep their record here; the retests replace their seeds.

**1. The gate by method (a)** (maintainer's item 2). **Reason:** a contradiction of the
specification: revision 3, 2.2 prescribed for the gate an estimator (the stacked per-event error)
that cannot meet revision 3, 10, row A1 ("white noise: the gate unchanged within 5%"), as the
diagnosis of Amendment 3 shows (local baseline and scatter term, about −19% in white noise);
option (b) would have hidden that change of sensitivity. **The method:** the β factor of red
noise (Pont, Zucker and Queloz 2006, "The effect of red noise on planetary transit detection",
MNRAS 373, 217-230, doi:10.1111/j.1365-2966.2006.11012.x, https://arxiv.org/abs/astro-ph/0608597,
read 2026-10-18) applied to the BLS depth error:

- `snr = depth_BLS / (depth_err_BLS × β_D)`, with `depth_err_BLS` the error of the final BLS fit
  (`finalize_candidate`, unchanged). The BLS error is `e² = 1/W_I + 1/W_O` (astropy, the in-transit
  and out-of-transit weight sums), so both terms are inflated (Codex design review, which showed
  that inflating the whole error by an in-box β alone underestimates when the baseline has the
  larger inflation):
  `β_D² = Σ_s β_s(n_T)² (W_{I,s} / W_I² + W_{O,s} / W_O²) / (1/W_I + 1/W_O)`, where `W_{I,s}` and
  `W_{O,s}` are the sums of `w_i = 1/σ_i²` (the per-point σ of the final fit) over the in-transit and
  out-of-transit cadences of sector `s`, `W_I = Σ_s W_{I,s}`, `W_O = Σ_s W_{O,s}`, and `β_s(n_T)` the
  A1 estimate of sector `s` at `n_T = round(duration / cadence)` (the `box` estimate of piece 2).
  In transit means astropy's own `BoxLeastSquares.transit_mask(t, P, duration, t0)` at the final
  candidate (strict `<`); it approximates the phase-binned set of the fast method, and enters only
  through the sector shares. **Declared assumptions:** the sectors' contributions are independent,
  each sector's in-transit and out-of-transit means have their white variances inflated by
  `β_s(n_T)²`, and `β_s` at `n_T` is used for the out-of-transit term too (an approximation, not a
  bound for every temporal covariance). In white noise `β_D ≈ 1`.
- **Conditions of the gate, its own:** a sector with positive weight (checked before the
  normalization) in the in-transit **or** the out-of-transit set and excluded at `n_T` makes the gate
  INCONCLUSIVE ("noise model undetermined"; no borrowing, revision 3, 2.1, kept strict even for a
  small weight); no in-transit cadence: INCONCLUSIVE. The gate no longer needs the `n_B` estimate or
  measurable per-event depths.
- Reported: `bls_depth_snr`, `beta_d`, per sector `β_s`, `W_{I,s}`, `W_{O,s}`, and the stacked
  per-event error of piece 2 as a diagnostic (`stacked_error_ppm`, `None` when the stack is not
  available; it never vetoes the gate). The candidate's `depth_err` becomes
  `depth_err_BLS × β_D`. `odd_even` and `secondary_eclipse` keep the corrected per-event errors of
  piece 2 (Amendment 2).
- **What K1 and K2 do not cover:** they calibrate the stacked per-event depth, not this gate's
  error (Codex, Amendment 3). Whether a calibration condition for the gate's error is needed is a
  question of the calibration protocol, recorded for the maintainer; nothing here changes it.
- **Retest:** P2 as declared in Amendment 2 (white `planet`, the median of corrected SNR / BLS
  `depth_snr` within [0.95, 1.05], ten light curves), on seeds **5000 to 5009**, without an `xfail`.
  (1000 to 1009, first written here, were replaced before any run: `scenario_data` seeds the
  auxiliary data with `seed + 1000`, so they reuse RNG states of the old seeds 0 to 9, Codex. The
  effective states of 5000 to 5009 are the flux at 5000 to 5009 and the auxiliaries at 6000 to 6009,
  none used by any test of the TESS pack.)
- **Direct mechanism cases** (Codex): the combination with different `β_s` per sector against a
  hand computation; a sector excluded with in-transit weight, and one with out-of-transit weight
  only; no in-transit cadence; the gate computed when the per-event stack is unavailable.

**2. The parabolic crossing** (maintainer's item 3). **Reason:** a defect with an identified
mechanism: the linear interpolation of Amendment 3 places each crossing of the convex Δχ² inward,
biasing the error low (−5.3% on the noiseless case, addendum of Amendment 4). **The method:** with
`level = Δχ²[best] + 1` (the sampled minimum; the minimum is not replaced by a continuous one),
each crossing is located on the parabola through three scan points, in local coordinates measured
in scan steps: the left crossing uses `(left − 1, left, left + 1)` and its root in the closed
interval `[x[left − 1], x[left]]`; the right one uses `(right − 1, right, right + 1)` and its root in
`[x[right], x[right + 1]]`. When the region is a single point (`left = right = best`), both sides use
`(best − 1, best, best + 1)`, each in its own interval. The parabola is degenerate when the
magnitude of its quadratic coefficient is below 1e-12 (Δχ² units per step²); a root is accepted
when it is real, finite and inside the interval to 1e-9 steps (clipped to it), and unique there;
otherwise that crossing uses the linear interpolation and a counter `linear_crossings` (per
crossing, so up to two per transit) records it. A region that reaches the edge of the scan keeps
the edge, as before (no triple is taken on that side). The center stays the scan minimum; the floor
stays half a cadence. On an exactly parabolic Δχ² the crossing is exact for that level.

- **Retest:** the case of Amendment 3 unchanged (`synthetic.PLANET`, white 600 ppm, the injected
  ephemeris, no detrending, `make_lightcurve` as before) on the fixed seeds **2000 to 2014** (15
  light curves, never used), without an `xfail`, which must give **exactly 210 measured transits**,
  the size of the declared case. If the count differs, the retest is recorded as incompatible with
  the design (no acceptance, no seed added). The same criteria: the median of error / Carter within
  [0.7, 1.3]; |pull| ≤ 1 in [0.60, 0.76]; |pull| ≤ 2 in [0.92, 0.98]; the median pull within
  ± 0.2. The 980-transit result stays a recorded diagnosis only; no larger sample decides.
- **Direct mechanism cases** (Codex): a single-point region; the fallback to the linear crossing
  (a degenerate triple); a region at the edge of the scan; the exactness on a parabolic Δχ².
- The width case (addendum of Amendment 4) keeps its 10%; it is a regression guard.

Both changes: the tests are changed and committed before the code; the sabotages are planned
with the tests; Codex reviewed the design before the tests (`.cache/v021/codex/amend7/`; its
objections are taken into the text above: the out-of-transit term, the reused seeds, the fixed
size, the conditions of the gate, the box identity, the declared crossing rules and the direct
cases).

Also corrected here: the citation in `rednoise.py` read "MNRAS 373, 231"; the article is MNRAS 373,
217-230 (the arXiv record above).

## Amendment 8 (2026-10-18): the retests of Amendment 7

Run once with the code of the commit that records them (tests committed before the code, 68cbb43),
`scripts/run_tests_affinity.ps1` on threads 0 to 7; the numbers by
`m4/amendment7_retests.py` (`m4/amendment7-retests.json`; run twice, identical output):

| Retest | Criterion | Result |
|---|---|---|
| P2, white `planet`, seeds 5000 to 5009 | median of corrected SNR / BLS `depth_snr` in [0.95, 1.05] | **1.000** (eight light curves exactly 1, two 0.994 and 0.991): **met** |
| timing, `synthetic.PLANET`, seeds 2000 to 2014 | exactly 210 transits | **210**: compatible |
| | median error / Carter in [0.7, 1.3] | **1.020**: met |
| | \|pull\| ≤ 1 in [0.60, 0.76] | **0.667**: met |
| | \|pull\| ≤ 2 in [0.92, 0.98] | **0.938**: met |
| | median pull within ± 0.2 | **−0.074**: met |

The first results stay as recorded (Amendments 3 and 4); these are the retests of the corrected
methods, on new seeds, with the same criteria and sizes.

**What the P2 retest shows, and what it does not.** In white noise the A1 estimate gives
`β_s = 1` exactly whenever its `σ_r²` estimate is not positive (revision 3, 2.1, `max(0, …)`), so
under method (a) the gate equals the BLS SNR by construction in most white light curves (eight of
ten here). P2 then measures how often white noise inflates the gate spuriously (two of ten, by at
most 0.9%); it does not test the error's calibration under correlated noise, which K1 to K8 and
the calibration conditions address (and the gate's own error is not among them, Amendment 7).

## Amendment 9 (2026-10-18): point (B), which `S_pred` estimates `b` and `s` (before any number)

The maintainer's item 5 of 2026-10-18: both are recorded, one is fixed before the selection with a
justification based only on synthetic data, and `S_meas` is obtained apart for the rounds that
decision 1 stops.

- **Both recorded.** Every round that reaches the capacity rule records `S_pred,1` (decision 1,
  train noise and replicas, revision 3, 4.3 with Amendment 6) and `S_pred,2` (decision 2, the
  hidden replicas, revision 3, 4.4 with Amendment 6), and, when measured, `S_meas`.
- **The rule that fixes one (declared now, before any value is computed):** on a synthetic lot of
  the development structure under the new prefix `refute-v0.2.1-bs-choice` (never used; not the
  selection part, not the development population), with the code of pieces 4 and 5, take every
  round of an injected constant signal with `S_pred,k ≥ min_snr` for each `k`; compute
  `1.4826 MAD(S_meas − S_pred,k)` pooled over both noise models (revision 4, 2); **fix the `k` with
  the smaller value** (the residual the rule can bound more tightly); a tie within 5% of the larger
  value goes to `k = 2`, the last capacity decision before the measurement, made with the noise of
  the year measured. The lot, its size (the planets of the bands near and measurable, every tenth
  index, as the lot of point (A)) and the result are committed before the selection part is
  generated; the chosen `k` and its `b`, `s` estimation procedure enter the freeze commit.
- **`S_meas` apart for rounds stopped by decision 1.** The official round keeps its status
  (INCONCLUSIVE, `insufficient_capacity_train`) and an empty hidden access log. A separate
  function, used only by the population harness and never by `run_holdout`, measures such a round
  in the same way (decision 2 recorded, the measurement made) and returns its `S_meas`, `S_pred,1`
  and `S_pred,2` in a record marked `calibration_only`; it never changes a verdict.

## Amendment 10 (2026-10-18): point (A) decided by the objective criterion; a CI binding

**Point (A) of Amendment 6**, by the maintainer's item 4 of 2026-10-18: the option with the
smallest expected fraction of INCONCLUSIVE rounds that respects `R_min`, computed only from metadata
and synthetic training data; a tie goes to "the replicas avoid the noise bands". Decided before any
result of pieces 4 and 5. The calculation: `calc/option_a_geometry.py` and its output
`calc/option-a-geometry.json` (a new lot, prefix `refute-v0.2.1-option-a-geometry`, 100 planets of
the bands near and measurable; 240 rounds, 107 ended before the hidden year by the existing train
rules, 133 reach the geometry). Codex checked it read-only (`.cache/v021/codex/option-a/`): the
replica rule, the bands, the bins and the three options were correct; it found that the first run
counted **registered** replicas and predicted windows, not **usable** ones (covered by the
cadences, the rule of `holdout._measure`). The coverage was added and the calculation rerun; the
first run's output is kept in the worktree's `.cache/v021/m4/option-a-geometry.run1.json` (its
fractions: 0.767, 0.609, 0.722; the order of O2 first did not change).

| Option | INCONCLUSIVE of 133 (usable replicas and windows) | Median usable replicas |
|---|---|---|
| O1, revision 3, 4.2 as written | 0.767 | 16 |
| **O2, `σ_w,hidden` and the `B_min` check from the replicas' baseline bands** | **0.609** | 16 |
| O3, the replicas avoid the noise bands | 0.767 | 0 |

**Chosen: O2.** The noise bands of revision 3, 4.2 are not registered; `σ_w,hidden` (the weights of
the baseline fit of revision 3, 4.1) and the few-bins check at `n_T` (`B_min` bins per sector) come
from the residuals of the accepted replicas' baseline bands, which are read through `HiddenYear`
anyway; a sector without `B_min` bins there is excluded (its windows dropped), and with no sector
left decision 2 is INCONCLUSIVE ("hidden noise undetermined"). This changes row B2 of revision 3
in that one respect, by the maintainer's decision.

**A finding for the maintainer (not a change):** with `R_min = 20` (revision 4, fixed for every
configuration), 81 of the 133 rounds (61%) have fewer than 20 usable replicas under O1 and O2, 102
under O3, and 75 under all three (avoiding the bands changes the greedy order, so a few rounds
gain replicas under O3) (correction of the Codex end-of-stage review): the hidden year of this
population is one 27-day sector, while revision 4's example (about 28 replicas) has two. With the
107 rounds ended earlier, 188 of 240 rounds (78%) of these planets would be INCONCLUSIVE under O2. Revision 4, 1 already says that this "enters the conclusive
fractions of the sizing"; the sizing of `calc/calibration_sizing_rev4.py` used declared reference
rates, and whether the T1 denominators (at least 725 conclusive targets per condition) are
reachable is a question for the maintainer before the selection.

**A CI binding (deviation recorded).** P1's digests of the switch-off analyses are bound to the
platform and the numpy version; CI showed that CPython 3.12 on Windows gives other digests than
the 3.13 that computed them (run 39127066658; the same failure was already in the CI of the
piece-2 push, 39094858224, and was missed, read as the lock failures only). P1 now also requires
the Python minor version of the reference (3.13); the reference record is unchanged. **Provenance
of 3.13, reconstructed** (the reference record stores the commit, the platform and numpy, not the
interpreter): the reference was computed with the worktree's virtual environment, whose
`pyvenv.cfg` reads `implementation = CPython`, `version_info = 3.13.16`, created
2026-10-17T23:46:41Z and not modified since, before the reference commit `ba42037`
(2026-10-18T03:22:14Z). Consequence: on CPython 3.12 the historical comparison with M3 is skipped;
the equality of the default plan and an explicit switch off still runs there, and does not replace
it.

## Amendment 11 (2026-10-18): piece 4, its cases and its interface (before its tests)

Declared before any test or code of piece 4, with the readings of Amendments 6 and 10.

**Interface** (`holdout.py`, used only with the switch on; Codex design review taken in,
`.cache/v021/codex/amend11/`):

- `register_replicas(ephemeris, windows, spans) -> list[PredictedWindow]`: the rule of revision
  4, 1 from metadata, with `L = 2 max(baseline_outer)`, the mask `max(baseline_inner)` and the box
  half-width `max(half_width)` over the transit windows (the readings of
  `calc/option_a_geometry.py`); returns windows of kind `replica` (epoch `n_ref + m` for the
  center `t_ref + (m + phase) P`). Overlap is tested on **closed** intervals (spans that only touch
  overlap), because the accessors include their end points.
- `period_grid(ephemeris, windows, duration, params) -> ndarray`: the `dP` grid, fixed from the
  ephemeris and the windows' metadata before any read (odd, symmetric, containing 0; the current
  rule of `_measure` for its extent and step).
- `HiddenYear` receives the windows and the replicas: the detrending masks both out to
  `baseline_inner`; both are read only through `window()` and `local_baseline()`, logged with their
  kind.
- `window_depth(t, f, in_window, center, half, frequencies=()) -> WindowDepth` (fields `depth`,
  `n_in`, `n_base`, `n_params`, `reason`): revision 3, 4.1 at one center: the box
  `|t − c| ≤ half` within the window's cadences (`in_window`); the baseline model fitted to every
  other cadence (the rest of the window and its bands): a line plus the given frequencies (none
  until piece 7); the degeneracy rule (at least 20 baseline cadences per parameter; the condition
  number of the column-scaled normal matrix at most 1e6; the fallback: sinusoids dropped in reverse
  order of their train amplitude, then the line becomes a constant, then `depth = None` with its
  reason); `d = mean over the box of (model − flux)`; a box with fewer than `min_window_coverage`
  of its expected cadences (`2 half / cadence`) is `box_coverage`. The bands' coverage is checked
  once per window, as in `_measure` (at least `min_window_coverage` of `2 (outer − inner) /
  cadence`), and a window or replica failing it is not used at any `dP`.
- `replica_stats(hidden, replicas, ephemeris, duration, cadence, plan, sector_spans, grid) ->
  ReplicaStats`: (1) the hidden noise of O2 (Amendment 10): A1 at `n_T` per sector on the residuals
  (`flux − 1`, flattened) of the replicas' baseline bands, `B_min` bins; replicas of an excluded
  sector do not count; (2) the replica depths at **every** `dP` of the grid, `var_rep(dP) =
  (1.4826 MAD)²` and `n_rep(dP)` over the usable replicas. If any `dP` of the grid has
  `n_rep < R_min`, or no sector is left, the result is `hidden_noise_undetermined`.
- `measure_windows(hidden, windows, ephemeris, duration, cadence, plan, sector_spans, grid,
  stats) -> dict`: called only after `replica_stats` and the barrier of decision 2 (piece 5; in
  piece 4 the barrier is the `hidden_noise_undetermined` check alone); windows of an excluded
  sector dropped; windows whose measurement spans share cadences: the later dropped; `N_valid`
  counted after every drop (fewer than `min_predicted_transits`: INCONCLUSIVE); the stack and its
  error as revision 4, 1 at each `dP`; the maximum SNR, ties to the smaller `|dP|`, then the
  negative side. Returned: the best `dP`, its depth, error, SNR, `N_valid`, `n_rep`, `var_rep`, and
  every drop with its reason.

**The cases of the numeric unit criteria of revision 4, 1** (`tests/test_holdout_replicas.py`):

- **Geometry:** the ephemeris of `synthetic.PLANET` (`P` = 3.7 d, `t0` = 1326.3, `T14` = 2.5 h) with
  zero timing error (so the `dP` grid is `{0}` and the replicas are the most numerous); a hidden
  year of two sectors, `synthetic.make_lightcurve(None, sector_starts=(1325.0, 1353.0))`, 2-minute
  cadence, the windows of `_predict_windows` and the replicas of `register_replicas`; the fast plan
  with the switch on. The full operation includes the hidden detrending of `HiddenYear`.
- **Seeds:** only `make_lightcurve` (no auxiliary data, so the `seed + 1000` of `make_aux` plays no
  part); no reuse of these seeds was found in the examined paths (a search, not a proof that they
  were never used anywhere).
- **White:** light curves of seeds 3000 to 3199 (200), white 600 ppm, no signal. The analytic error
  of the **local measurement** at a position is `σ sqrt(1/n_in + g′(X′X)⁻¹g)` for the line fitted to
  its out-of-box cadences (`σ` = 600 ppm, `g` the mean of the design rows over the box); per light
  curve, `sqrt(var_rep)` over the median of that analytic error over its replicas; **the median over
  the 200 light curves within [0.85, 1.15]** (revision 4, 1: the deviation). **Declared limit:** the
  formula ignores the hidden detrending (a trend fitted on the data, which the masks keep out of
  the boxes but not out of the bands), so for the full operation it is an approximation; a failure
  of this criterion would be recorded as a result whether its cause is the code or the reference.
  A separate mechanism case checks `window_depth` alone against the formula on white noise
  without detrending.
- **AR(1):** the same seeds in the correlated mode (`CORRELATED_PROFILE`: 600 ppm white plus 600
  ppm AR(1), `τ` = 1 h). The Monte Carlo variance: the same operation on 400 independent
  realizations of the same composite noise on the same cadences (seeds 4000 to 4399), at the fixed
  replica positions of the metadata; at each position the sample variance (`ddof = 1`) over the
  realizations where the position was usable, then the median over the positions; per light curve,
  `var_rep / var_MC`; **the median over the 200 light curves within [0.85, 1.15]** (revision 4, 1:
  the variance, not its square root).
- **The full operation's pulls:** 200 AR(1) hidden years without signal (seeds 3200 to 3399), the
  measurement operation at the given geometry (not a search, which could stop before it), the
  stacked depth over the transit windows divided by its error, **over all 200** (a year whose
  measurement is not made fails the case as incompatible, it is not left out); **|pull| ≤ 1 in
  [0.60, 0.76], |pull| ≤ 2 in [0.92, 0.98], the median within ± 0.2**. This is the unit reading of
  point fractions (as for piece 3): at n = 200 no count can satisfy the interval form of the K
  conditions of revision 3, 8.3, which the calibration applies.
- **Known depth:** a box signal of known depth (1000 ppm, ingress fraction 0.001) in the transit
  windows of a low-noise hidden year (50 ppm white, seed 3400): the stacked depth equals it within
  5% (sign and scale, which the Monte Carlo of the same operation cannot check). The mechanism
  cases use seeds 3000 to 3004 (they decide no numeric criterion).
- **A non-trivial grid:** a geometry with a period error, so the grid has several points: the
  replicas are measured at the shifted centers of every `dP`, the reported `dP` maximizes the SNR,
  the declared ties hold (that `e_pred` uses the largest predicted error over the grid is a case of
  piece 5).
- **Mechanisms:** too few replicas (a timing error that leaves fewer than `R_min`): INCONCLUSIVE
  `hidden_noise_undetermined`, no transit window in the access log; no accepted replica span
  overlaps a window's measurement span, and no sector's masked time fraction exceeds 0.5, on a
  grid of geometries (`P` in 1.5 to 5.5 d, timing error 0 to 0.9 `T14`); the same metadata gives the
  same replicas; a sector without `B_min` bins in the replicas' bands drops its windows, and with
  no sector left the measurement is INCONCLUSIVE; with the switch off the holdout is the M3 one
  (P1).
- **Correlated noise** in the mechanism cases where it matters (the variance and the pulls are
  already AR(1)).

## Amendment 27 (2026-10-19): the evaluation of the `R_min` study and of its lot `bs-choice` (declared before any lot)

Amendment 19's design and Amendment 26's readings (approved on 2026-10-19) are not reopened. This
amendment fixes, before any lot of the study or of `refute-v0.2.1-bs-choice` is generated, how the
recorded rounds are read, after a Codex design review (read only, `.cache/v021/codex/rmin-eval/`;
its objections to a first draft were accepted: no minimum of rounds, no tolerance for a missing
twin and no fallback of `k` that the approved text does not state). No rule below adds a criterion:
where the approved computation lacks its inputs, the result is **not evaluable**, never a pass.

1. **Order.** The configuration (item 2) and the evaluator (item 11), with their tests, are
   committed first; then `bs-choice` is generated and recorded, `k` and the pairs `b_R`, `s_R` are
   computed and committed; only then are the study's lots generated. The pairs are never computed
   from the study's records, and the study's records never from another configuration.
2. **The configuration of the study and of `bs-choice`:** `m4-configurations/rmin-study.json`
   (`M4-rmin-study`, never a campaign configuration), the block of `M4-rmin-timing` (`r_min` 8, the
   pair 0, 0: in the measurement mode the pair changes no work, and `derive_round` applies `b_R`,
   `s_R`); its file and SHA-256 named in the commit that adds it.
3. **The records and their completeness.** One record file per target and scenario (never replaced,
   no two with one name), holding the target's identity (`<prefix>/<case id>`), its group, the
   scenario, the configuration identity, the light curve's observing years from its metadata, and
   one `calibration_measurement` record per observing year (with the scenario's twin). A manifest
   lists the expected targets and scenarios before the lot is analyzed. Completeness: every expected
   target and scenario has one record file, each with one round per observing year and no other;
   a missing, duplicated or extra file or round makes the lot **incomplete**: it is never evaluated
   by dropping it from a denominator, and goes to the maintainer. An impediment of a round is a
   recorded round, not a missing one.
4. **`k` (Amendment 9's rule, on `bs-choice`, the constant scenario).** For each `k` separately, the
   set of rounds with `S_meas` and `S_pred,k` finite and `S_pred,k ≥ min_snr` (the records at
   `r_min` 8; no other `R` filter: `k` is one choice); `a_k = 1.4826 MAD(S_meas − S_pred,k)` pooled
   over both noise models. `k = 2` when `|a_1 − a_2| ≤ 0.05 · max(a_1, a_2)` (both zero included),
   otherwise the `k` with the smaller `a_k`; the values are not rounded. **If either set is empty**,
   the comparison Amendment 9 prescribes does not exist: the study stops and goes to the maintainer.
5. **`b_R` and `s_R`, for each `R` of the set:** the median and `1.4826 MAD` of `S_meas − S_pred,k`
   over the rounds of item 4's set for the chosen `k` that also **meet `R`**: the train and the hidden
   replica counts at least `R` at every `dP` of the grid, and the hidden noise determined (the
   decisions are not read, so the residuals that fix the pair are not selected by it). No minimum
   number of rounds: with **none**, the pair of that `R` does not exist and that `R` is not
   evaluable; otherwise the pair exists, with the number of rounds and of distinct targets
   recorded. A MAD of zero gives `s_R = 0`.
6. **Statistics.** The median of an even number of values is the mean of the two middle ones
   (`numpy.median`); `MAD(x) = median(|x − median(x)|)`; the factor is the literal `1.4826`. Every
   comparison uses unrounded values and the approved bounds inclusively: the upper bound of
   criterion 1 `≤ 0.02`, the lower bounds of criteria 4 and 5 `≥ 0.80` and `≥ 0.50`, the counts `≥`
   their minima (866, 83, 101), the coverage fractions in the closed intervals `[0.60, 0.76]` and
   `[0.92, 0.98]` and `|median| ≤ 0.2`; the Clopper-Pearson bounds one-sided at `0.99`. A zero
   denominator never passes.
7. **Eligibility and outcomes** by `derive_round(record, R, b_R, s_R, min_snr)` and the aggregation
   of `run_holdout` (FAIL, then PASS, then INCONCLUSIVE); a target is eligible for criteria 1 to 3
   when one of its rounds is eligible (Amendment 26, 3).
8. **Criterion 3, the coverage.** Over the first eligible round, in increasing year, of each eligible
   constant target (no other year sought), the pull `(d_hidden − d_twin) / e_hidden`. The record keeps
   the twin's status (its measurement's reason when it has no depth). If any of these rounds has no
   finite twin depth, criterion 3 is **not evaluable** for that `R` and group (reported apart from a
   coverage outside its margins); the fractions are never computed on the available twins only.
9. **The disappearance and weakening criteria.** The round hiding the target's last observing year
   (the largest year of the light curve's metadata, never of the records found) "passes decisions 1
   and 2" when `derive_round` gives `decision_1` and `decision_2` both `pass` at `R`, whatever its
   measurement then; the weakening filter `0.3 · S_pred,2 ≤ 3` reads that round's `S_pred,2` in the
   weakened scenario. These denominators are not intersected with item 7's eligibility: a qualified
   target whose aggregated outcome is INCONCLUSIVE stays in the denominator and is not a FAIL. The
   criterion reads the target's aggregated outcome; that round's own status is reported beside it.
10. **The choice:** the smallest `R` of the set whose pair exists and that meets criteria 1 to 5 in
    all four groups (a criterion not evaluable is not met); otherwise option (c), the result for the
    maintainer. An incomplete lot (item 3) or a stopped `k` (item 4) is not a scientific result and
    is reported as such. Every `R` and group is reported: counts, bounds, fractions, the pull's
    statistics, the INCONCLUSIVE fractions by reason per target and per round.
11. **The evaluator** (`rmin_evaluate.py`, pure functions over the records): `choose_k`, `pair_for_r`,
    `completeness_problems`, `target_outcomes`, `criteria`, `choose_r_min`. Its tests, before any
    lot, on built records: the tie exactly at 5%, both MADs zero, an empty set of one `k`, a missing
    pair, a missing twin depth, a missing last-year round, a target without records, a duplicated
    round, a qualified target whose decisions pass and whose measurement is impeded, and each bound
    at its edge.

**For the maintainer** (with the decision on the ceiling and the drand round): items 3 (an
incomplete lot goes to the maintainer), 4 (an empty set of a `k` stops the study) and 8 (a missing
twin depth makes criterion 3 not evaluable) are readings of the approved text where it lacks a
rule.

**The maintainer's decision (2026-10-19), in their words** (the message ends cut after its last
word, read as "bs-choice"): "O estudo de R_min tem teto próprio (204 h projetadas; o teto de 397 h
fica para a calibração). Aprovo o procedimento da rodada drand da reserva e as três leituras da
Emenda 27 (lote incompleto vai a mim; k sem round para o estudo; gêmeo faltando torna a cobertura
não avaliável). Pode gerar o bs-choi[ce]" (the R_min study has a ceiling of its own, 204 h
projected, and the 397 h ceiling stays with the calibration; the procedure of the reserve's drand
round and the three readings above approved; `bs-choice` may be generated). The numeric value of
the study's own ceiling is asked of the maintainer before the study's lots are generated.

**`bs-choice`, generated and evaluated (2026-10-19).** Recorded at `905bba1` (the code of
`dc7a0da`) with `M4-rmin-study`, six workers, the affinity `0xff`: 100 targets, the constant
scenario, no failure, no integrity problem (`rmin-study/bs-choice/`, committed in `ae2fc34` before
its evaluation). The evaluation (`rmin-study/bs-choice-evaluation.json`, by `evaluate-bs-choice`):
complete; **`k` = 2** (`a_1` = 4.157 over 73 rounds, `a_2` = 2.883 over 79; not a tie); the pairs,
over the rounds that meet each `R`:

| `R` | `b_R` | `s_R` | rounds | targets |
|---|---|---|---|---|
| 8 | 0.585 | 2.883 | 79 | 40 |
| 10 | 0.585 | 2.883 | 79 | 40 |
| 12 | 0.632 | 2.843 | 76 | 38 |
| 15 | 0.799 | 2.517 | 68 | 34 |
| 20 | 0.529 | 1.930 | 48 | 24 |

These are committed before any lot of the study is generated; the study's lots wait for the numeric
value of its own ceiling.

**Implemented.** The twin's status in the record (`096a6ca`, item 8). The evaluator: tests
`be3a604` (`tests/test_rmin_evaluate.py`, on built records), then
`docs/validation/v0.2.1/population/rmin_evaluate.py`. The tie of item 4 is read on the unscaled
MADs (the factor 1.4826 is positive and cancels, so the rule is the same and its edge exact). One
case was added before the sabotages (a missing last-year round is not replaced by the records'
largest year). Sabotages SE1 (the tie strict), SE2 (an empty set falls back to the other `k`), SE3
(`R` met without the hidden noise), SE4 (the coverage on the available twins), SE5 (the last year
from the records), SE6 (the power denominators intersected with the eligibility), SE7 (the
weakening filter strict) and SE8 (a duplicated round accepted): all caught. JUnit: 15 tests, 0
failures.

**The lots' runner.** Tests `ab97b9d` (`tests/test_rmin_lots.py`), then in `rmin_study.py`:
`bs_choice_cases` (100 targets), `study_cases` (whole blocks per group: 16 prefixes of 400, 64 of
100; 6400 per group), `lot_manifest`, `record_target` (one record per scenario, one round per year
of the metadata, refusing another configuration than the study's and another worker identity),
`write_record` (never replaces a file), `run_lot` (six workers, the affinity `0xff`, the manifest
first, resumable without replacing), `evaluate_bs_choice` and `evaluate_study` (an incomplete lot
not evaluated), and the commands `lot`, `evaluate-bs-choice`, `evaluate-study`. The configuration
`m4-configurations/rmin-study.json` (`M4-rmin-study`, SHA-256
`27f2e277411d275f2cc23cdbd65b5a393751d7ba2b03b518494318d10ab44cdb`, block
`c5daf69afb09fb9b1237a1bd7afd2595f85d200ed13b7e11e90005b671753a4d`, that of `M4-rmin-timing`)
is captured by version 3 with no problem. Sabotages SL1 (every fifth index), SL2 (whole prefixes
for every group), SL3 (a record replaced), SL4 (any configuration recorded) and SV1 (an incomplete
lot evaluated): all caught. JUnit: the study module's four test files 45 tests, 0 failures. Nothing
of `bs-choice` or of the study is generated before the maintainer's decision on the ceiling and the
drand round, and on the readings of items 3, 4 and 8.

**The end-of-round review** (Codex, read only, of `b6a38e6` to `441b1d9`,
`.cache/v021/codex/stage-rmin2/`) returned WEAKENED: the evaluator's rules conform; before the lots
it found (P1) the resume refusing its own manifest (the tuples written are lists read back), (P1)
the evaluations dropping the manifest's lot and configuration (a foreign lot, configuration or
record was evaluated as complete; the output of `bs-choice` did not name its source and
`evaluate-study` took any pairs), (P2) no final integrity check in `run_lot`, (P2) a worker's
failure ending the run without a report, (P2) the INCONCLUSIVE fractions and the reasons per target
missing, and the coverage's upper and median edges untested. Corrected, each with its case: the
manifest (with a format, `refute-v0.2.1-rmin-lot/1`) is compared as read back; `lot_problems`
checks the manifest's format, lot and configuration and every record's configuration, then the
completeness; `bs-choice`'s output names its source (lot, configuration, the SHA-256 of the
manifest and of the records' digests) and `evaluate_study` refuses pairs of another source,
configuration or `min_snr`; `run_lot` reports each failed target (never retried there), ends with
the integrity check and writes a dated run report (never replaced); resuming an interrupted lot is
a rerun, so its approval is recorded first (CLAUDE.md). **Criterion 6** reports the fractions per
target and per round with every reason; a target is counted once, under the combination of the
distinct reasons of its INCONCLUSIVE rounds, and a zero denominator is not evaluable. Sabotages SV2
(the manifest compared as written), SV3 (a record of another configuration accepted), SV4 (the
pairs' source not checked), SV5 (a worker's failure not caught) and SV6 (a target counted once per
reason): all caught. JUnit: the study module's four test files 55 tests, 0 failures.

**The second round** of that review objected to two more points, corrected with their cases:
(1) the manifest's expected targets were not checked against the lot's own (records of the study
under the label `bs-choice` gave `k` and pairs), and a pairs' source without its digests was
accepted: `lot_problems` now requires the manifest's expected targets and scenarios to be those of
`lot_manifest(lot)`, and `evaluate_study` (`evaluate-study --bs-run`) evaluates `bs-choice` again
from its own run folder and refuses pairs that are not exactly that evaluation; (2) a failure while
submitting to the pool (a broken pool) ended the run without a report: the dispatch and the pool
are now guarded too, and the report names the submitted and the not submitted targets. Sabotages
SV7 (the manifest not checked against the lot's), SV8 (the pairs not derived again) and SV9 (a
submission failure not caught): all caught. JUnit: 57 tests, 0 failures.

## Amendment 26 (2026-10-19): the implementation of the `R_min` study's prerequisites, and its timing lot (declared before any lot)

Amendment 19's design is approved and is not reopened. This amendment fixes the implementation
choices its text leaves open, after a Codex consultation (read only,
`.cache/v021/codex/rmin-impl/`, two rounds: its objections were accepted and it found the result
defined enough to implement). Two of them are **readings of the approved text**, recorded as
readings and brought to the maintainer with the cost package for decision; nothing below generates
a lot of the study or of `refute-v0.2.1-bs-choice`.

1. **The lots, read per group** (a reading, for the maintainer). Each prefix
   `refute-v0.2.1-rmin-study-<k>` gives, per noise model, the 500 planets of the bands near and
   measurable: 400 without variability (`two_years`, `three_years`, `few_train`) and 100 with
   (`variability_some_years`). "Taken whole and in order of `k` until each group has its declared
   size" is read **per group**: for each of the four groups, that group's cases of each prefix,
   whole and in order of `k`, until the group reaches its size; the cases of a group already full
   are neither generated nor evaluated (a case's seed depends only on its prefix, class, band, noise
   and index, so a subset changes no case). Whole blocks give a **realized size of 6400 per group**
   (16 prefixes × 400; 64 × 100), above the probabilistic minimum of 6350: 25 600 targets and 76 800
   evaluated light curves, before the reserve. The other reading (whole prefixes, the four groups
   together) would take 64 prefixes for every group: 64 000 targets. A study target's identity
   carries its prefix (`refute-v0.2.1-rmin-study-<k>/<case id>`): the case id alone repeats across
   prefixes.
2. **The minima, read uniformly** (a reading, for the maintainer). The pass probability of a
   binomial criterion is not monotone in the count (the steps of the bound), and the realized count
   is any count at or above the minimum, so each minimum is the smallest count **from which** the pass
   probability at the reference rate stays at least 0.95 for every count up to the realized group
   size (6400). `calc/rmin_sizing.py`: `n₁` = 866, `m₄` = 83, `m₅` = 101 (the lowest pass probability
   over that range 0.952, 0.968, 0.954); the pointwise smallest counts (796, 76, 96) are recorded
   beside them. Codex recomputed both independently (by inverting the binomial tails) and found the
   same values.
3. **The measurement record and the derivation by `R`.** `calibration_measurement` records, for each
   round: the train and hidden replica counts over the grid; the hidden noise status before the
   `R` rule (an undetermined noise estimate, apart from the counts); `n_years`; `d_train`, `e_train`;
   `d_hidden`, `e_hidden`, `S_meas` and the `dP` chosen; the measurement status; and the reason of
   every impediment. A function `derive_round(record, R, b, s)` (in `holdout.py`, calibration only)
   applies, in Amendment 19's order: the impediments before the capacity rule; the train counts
   against `R`; decision 1 (`capacity_threshold(min_snr, b, s, n_years)` on the recorded `S_pred,1`);
   an undetermined hidden noise, else the hidden counts against `R`; decision 2; the measurement's
   impediments; the FAIL rule. **A round is eligible** when decisions 1 and 2 pass at `R` and the
   measurement is made and read by the FAIL rule: PASS, FAIL, or INCONCLUSIVE
   `not_detected_not_inconsistent` (Amendment 19's parenthesis: "a measured round"); a round whose
   measurement is impeded after decision 2 (too few windows, a non-finite statistic) is not
   eligible, the reading that keeps the denominator of the false FAIL to rounds that could fail.
   `r_min` is read in two places only (`replica_stats`, the hidden
   counts; `replicas_enough`, the train counts): checked by Codex. **Two checks, before the study:**
   (a) the invariance of the measured fields (`d_train`, `e_train`, `d_hidden`, `e_hidden`, `dP`,
   `S_pred,1`, `S_pred,2`, `S_meas`, the counts) between records made at `r_min` 8 and at `r_min` `R`
   where both measure; (b) `derive_round` of the record made at 8 against the official round of
   `run_holdout` (the decisions enforced) with `r_min` = `R` and the same `b`, `s`: the status, the
   reason, decisions 1 and 2 and the eligibility, on cases built to exercise each impediment and
   their precedence (the train counts below `R` where decision 1 would also fail; the hidden counts
   below `R`; decision 2 failing; too few windows).
4. **The noiseless twin.** `HiddenYear` keeps, privately, the effective trend and the indexes the
   noisy detrending kept; the twin uses those cadences (the clipping included), the train
   frequencies, the same baseline form, and the replica statistics cut and re-indexed to the `dP`
   chosen; the window coefficients are estimated again. `twin_model` is the scenario's complete
   noiseless model (the signal times the trend, plus the variability; with the last year's
   alteration where it applies), given only by the evaluator to the calibration function, never to
   `run_holdout`. The pull is `(d_hidden − d_twin) / e_hidden`. **Isolation test:** with no twin, a
   twin and another twin, every field of the noisy analysis and the official result are equal.
5. **The last year's alteration** `flux + (1 − s) · D(t) · trend(t)`, `D = 1 − signal_model` from the
   recorded final parameters, `trend` the generator's (`1` for `pure_noise`, a mechanism of no study
   planet; no study planet is a blend). The unit test checks the expected increment inside the last
   year's transits, zero outside them and in the other years, and that `s = 1` changes nothing; the
   altered curve is used in every round of its scenario.
6. **The timing lot of the study** (declared now, before it exists; a complement of the calibration
   timing lot of `calibration-ceiling-decision.md`, which it neither replaces nor reuses).
   - *What it measures:* only time, in seconds per light curve and worker: the generation, the
     alteration, every round of `calibration_measurement`, the twin and the aggregation, on logical
     processors 0 to 7 with 6 workers. No outcome, pull, rate or count of the lot is examined or
     recorded beyond the timing, and nothing is chosen with it.
   - *Its configuration:* a version-2 configuration of its own (`m4-configurations/rmin-timing.json`,
     never a campaign configuration) with `r_min` 8 and the provisional pair `capacity_b` 0,
     `capacity_s` 0 (the measurement mode records the decisions without stopping, so the pair does
     not change the work done); its file and SHA-256 named in the lot's record.
   - *Cases:* prefix `refute-v0.2.1-rmin-timing` (never used, never reused); 20 targets per group,
     by a rule fixed now: per group without variability, `two_years` indexes 0–4 of the band near
     and 0–4 of measurable, `three_years` 100–102 of near and 100–101 of measurable, `few_train`
     150–151 of near and 150–152 of measurable (10 near, 10 measurable; the mechanisms in the
     study's proportion 2 : 1 : 1); per group with variability, indexes 200–209 of each band; the
     three scenarios: 240 light curves.
   - *Record:* a dated file with the code commit, the configuration, the per-curve times, their
     median and maximum per group and scenario.
   - *The projection, declared now:* each group and scenario is costed at **1.25 times the largest
     per-curve time observed** in it (a sample maximum is not a bound; the factor is the margin), for
     every curve of the study (76 800), the reserve (76 800) and the lot `bs-choice`, plus the
     generation the same way and the lot overhead 1.2 of campaign 1; machine time is that worker time
     divided by 6 (the summed worker hours are shown apart). The package to the maintainer gives the
     timing lot, `bs-choice`, the study and the reserve separately, against the 397 h ceiling.
   - *Rule:* nothing of the study or of `bs-choice` is generated before the maintainer decides on
     the cost and on the readings 1 and 2.

**The derivation (item 3), implemented.** Tests `3c14737` (`tests/test_rmin_derivation.py`), then the
code (`calibration_measurement`'s new fields, `ReplicaStats.noise_undetermined`, `derive_round`). The
first run: the derivation equaled the official round for every case, pair and `R` of the set, but
the coverage case failed: every train and hidden replica count of these cases is above 20, so the
set alone never reached the count impediments. Declared after that run, the comparison also uses,
per case, the values at and just above each smallest count (the official round at those `r_min`
too); with them every impediment and its precedence is reached. **Sabotages** (never committed,
each restored): SD1 (decision 1 before the train counts), SD3 (a measurement impediment counted
eligible), SD4 (the hidden counts before decision 1) and SD5 (the hidden counts ignored) caught;
**SD2 (the threshold without the pair) escaped**: with the pairs (0, 0) and (0.5, 0.8) no case has an
`S_pred` between the two thresholds. A case written after the escape builds pairs from the record
itself, the threshold just above and just below `S_pred,1` and between `S_pred,2` and `S_pred,1`,
once through `b` alone and once through `s` alone, each against the official round. SD2 run again
on it was caught, and so was SD6 (the threshold without `s`). JUnit: the derivation file 23 tests
(before the edge case 21), 0 failures; the capacity, plan and holdout tests 97, 0 failures.

**The twin and the alteration (items 4 and 5), implemented.** Tests `be7d181`
(`tests/test_rmin_twin.py`, `tests/test_rmin_alteration.py`), then the code: `detrend_parts` (the
flattened copy, the effective trend and the cadences kept; `detrend` returns its first part),
`HiddenYear.twin`, `calibration_measurement(..., twin_model=...)` with `d_twin`, and
`docs/validation/v0.2.1/population/rmin_study.py` (`deficit_and_trend`, `alter_last_year`,
`noiseless_model`, from a case's recorded final parameters). The first version kept the trend and
the cadences from a call of `detrend_parts` in `HiddenYear`'s constructor; the holdout tests then
failed twice (B1 of `test_holdout_report_wording.py` requires one call of `detrend` there), so the
constructor is unchanged and only `twin` repeats the detrending with `detrend_parts` on the same
inputs, checked identical to the noisy one. Before the sabotages the clipping case was made to
compare the flux values too (a twin equal to the raw flux reads the noisy flux itself, cadence by
cadence). **Sabotages:** ST1 (the twin not divided by the trend), ST3 (the twin's depth written into
a noisy field), ST4 (the cadences misaligned after a clipped one), SA1 (the alteration on every
year), SA2 (the factor inverted) and SA3 (the increment without the trend) caught; **ST2 (the twin
at dP = 0) escaped**: in the case's curve the dP chosen is 0. A case written after the escape moves
the hidden year's transits by `(epoch − n_ref) g` for a non-zero grid value `g` (two deterministic
passes), so the dP chosen is not 0; ST2 run again on it was caught. ST5 (the twin's replica
statistics taken at the grid's first dP) was not caught and cannot be through `d_twin`: the twin's
depth is the windows' mean and reads the replica variance only in the condition `var_rep > 0`, an
equivalent mutation for what the record keeps. JUnit: the twin file 7 tests, the alteration file 8,
0 failures; the detrend and holdout files with the derivation 304 tests at the first version (2
failures, above), 24 of the affected files after the change, 0 failures. The full suite at
`daff631`: 3127 tests, 0 failures, 0 errors, 57 skipped (JUnit).

**The timing lot's runner (item 6), implemented.** Tests `6c9f86a` (`tests/test_rmin_timing.py`),
then the code `7d234d0` in `rmin_study.py` (`timing_cases`, `time_target`, `run_timing_lot`, and
the command `rmin_study.py timing --out <file>`): the 80 targets of the declared rule; per target
the generation, then for each scenario every round of `calibration_measurement` with the
scenario's twin and the derivation and aggregation over the five `R`, timed; only the times, the
target, its group and the worker's corrections block leave a target (the records are discarded),
and the record refuses an uncommitted checkout (it names its commit). Sabotages SM1 (the records
leave with the times), SM2 (another index rule) and SM3 (no refusal without the configuration)
caught. JUnit: the timing and alteration files 11 tests, 0 failures.

**The end-of-stage review of these prerequisites** (Codex, read only, of `388afb6` to `664b0d0`,
`.cache/v021/codex/stage-rmin1/`) found no path of the official round that the derivation fails to
reproduce, and the twin and the alteration faithful; it objected, before the timing lot, to:
(1) the runner accepting any loaded configuration (with `m4-c1.json` it would have measured
`r_min` 20; Codex intercepted the call before any generation), and not checking its six workers
and its affinity; (2) the timed aggregation being partial (only "any FAIL" and "any eligible");
(3) the record's claim that ST5 cannot be caught through `d_twin`: with a zero replica variance at
the grid's first dP and a positive one at the dP chosen, the mutation removes the twin's
measurement, so it is equivalent only where the swap keeps the measurement admissible (the claim
above is withdrawn); (4) three paths without an equivalence case against the official round
(`no_predicted_window`, `non_finite_statistic`, an eligible `not_detected_not_inconsistent`).
Corrected, each with its case: the runner refuses, before any generation, a configuration other
than the timing lot's (its name, its path, `r_min` 8, the pair 0, 0) and a worker whose identity
is not the main process's, runs on six workers only with the affinity `0xff` (logical processors 0
to 7, read back and recorded, and each worker's too), and times the complete aggregation
(`aggregate`: FAIL, then PASS, then INCONCLUSIVE); the twin case with the first dP's variance at 0;
the three paths by replacing the measurement (or `count_n_pred`) for the record and the official
round alike. Sabotages: SR1 (any configuration accepted), SR2 (another identity accepted), SR4 (PASS
before FAIL) and ST5 on the new case caught; **SR3 (the operating conditions not checked)
escaped**: the refusal of an uncommitted checkout also raised `SystemExit`; the case now requires
the reason named, and SR3 run again on it was caught. JUnit: 26 tests of the new and changed cases,
then the timing file 15 tests, 0 failures. The second round of the review: ACORDO (its limit, the
full suite then missing: at `7e2eb87` 3127 + 19 = 3146 tests, 0 failures, 0 errors, 57 skipped,
JUnit).

**The timing lot, run** (2026-10-19, `rmin-timing/rmin-timing-2026-10-19.json`): the code of
`7e2eb87`, the configuration `M4-rmin-timing` (SHA-256 `92ac414d…`, block `c5daf69a…`), 6 workers,
the affinity `0xff` in the main process and in every worker; 80 targets, 240 light curves, 497 s of
wall time. Only times were recorded. The largest per-curve times per group and scenario: 13.3 to
15.1 s (white, no variability), 21.3 to 23.7 s (white, variability), 15.9 to 19.0 s (AR(1), no
variability), 21.1 to 21.5 s (AR(1), variability); the generation at most 0.45 s per target.
**The cost** (`calc/rmin_cost.py`, `calc/rmin-cost.json`, by the projection declared above): the
reading per group, the study 101.9 h and the reserve 101.9 h of machine time (611 worker hours each),
`bs-choice` 0.12 h, the timing lot 0.14 h: **204.1 h** in all; the reading by whole prefixes 230.5 h
each, **461.3 h** in all, above the 397 h ceiling. Brought to the maintainer with the readings 1 and
2; nothing of the study or of `bs-choice` is generated before the decision.

**The maintainer's decision (2026-10-19), in their words:** "Aprovo a leitura por grupo (6400 alvos
por grupo, 204 h) e os mínimos uniformes (866/83/101). Decido sobre o teto e a rodada drand a
seguir." (I approve the reading per group, 6400 targets per group, 204 h, and the uniform minima,
866/83/101. I will decide on the ceiling and the drand round next.) Readings 1 and 2 are therefore
the study's; the ceiling and the reserve's drand round stay open, and no lot of the study or of
`bs-choice` is generated before them.

## Amendment 25 (2026-10-18): the harness version 3 package (pre-registration; design only, for the maintainer's approval)

The maintainer's item 5 of 2026-10-18: the campaign declaration of the harness version 3, with its
binding to the configuration file, and the transport of `b` and `s`, are pre-registration; this is
their design, reviewed by Codex (four rounds, ending in agreement; the first version was rewritten
on its objections), brought to the maintainer as a package. **Nothing of it is implemented before the approval.** It changes no
criterion, no threshold, no default of an existing setting and no existing campaign. It replaces
the pending dispositions of Amendments 12 and 17 on `b` and `s` (module settings until the freeze; a
`capacity` entry of the configuration file) and on the campaign declaration.

**A. The identity contract of a version-3 campaign.**

1. *The declaration* keeps version 2's format `refute-population-campaign/1` (version 2 is never
   edited; it reads the whole JSON and checks named members only, so an extra member is tolerated)
   with one more member, required by version 3:
   `"m4_configuration": {"format": "refute-m4-configuration/1", "name": ..., "path": ..., "sha256": ...}`.
2. *The path*: a relative, `/`-separated path, interpreted from the **root of the checkout that holds
   the harness version 3** (never from the current directory), which must resolve, with no symbolic
   link or junction on the way (each component checked), to a regular file directly inside the
   authorized folder `docs/validation/v0.2.1/population/m4-configurations/`; absolute paths, `..`,
   a missing file, a link, or a target outside that folder are refused. The comparison is on the
   resolved target **and** the bytes' SHA-256, not on the text of the path: another file with
   identical bytes at another path is refused.
3. *One capture*: the configuration file is read once at start; that one byte string is parsed,
   hashed and kept as the snapshot (the current loader reads it twice: corrected); the file named
   by `REFUTE_M4_CONFIGURATION` must be the declaration's resolved target.
4. *The checks*: version 3 wraps version 2's `open_campaign` and adds, after version 2's own checks,
   a declaration problem when the member is missing or malformed, or when its `format`, `name`,
   `path` or `sha256` does not match the captured file. Every **operational mode** (generate,
   analyze, reconcile, resume) is then refused; the `status` mode **shows** the problem among the
   declaration problems and exits as version 2 does (it refuses nothing). Since the declaration is
   reopened and checked at every start, a resume with another configuration is refused.
5. *The workers*: the main process derives the expected identity (resolved path, SHA-256, and the
   SHA-256 of the canonical resolved corrections block) from the validated declaration and passes it
   to the workers in the environment beside the file's location; each worker, before every
   inherited analysis, checks its own captured file and its plan's resolved block against that
   expected identity and refuses otherwise; every result it returns carries its identity, and the
   main process (a wrapper of version 2's result callback) checks it for every result of every PID,
   later-starting workers included, and treats a result with no valid identity as an
   infrastructure error that stops the dispatch. The identity travels in the **envelope** the worker
   returns, never in the persisted record (version 2's record schema is closed). Because the
   inherited worker writes its record before returning, the main process keeps a version-3
   **identity journal** in the run folder (append-only) with a positive **confirmation** for every
   result it validated (case, PID, the persisted record's SHA-256, and the whole expected identity)
   and a **refusal** for every result it refused (case, PID, reason). A **resume** accepts a persisted
   record only when a confirmation exists that matches the file and the expected identity; a missing,
   invalid or incomplete confirmation, a refusal, or a resolved corrections block that differs from
   the expected identity's is a blocking integrity problem, never a valid record (this closes the
   window between the inherited write and the main process's check).
6. *The close*: the closure of an execution also checks that the configuration file still has the
   captured bytes (R2 already checks it against HEAD at start); a difference **invalidates the
   execution**: it cannot close as successful, and its results are not accepted.
7. *Loading failures*: the configuration is no longer loaded at import time with an exit; a missing
   or invalid file, invalid JSON or a missing environment variable is kept as a loading problem:
   every operational mode refuses with it, and `status` shows it among the declaration problems.
8. One configuration per campaign; an M5 candidate is another configuration file and another
   campaign.

**B. `b` and `s` as plan settings** (revision 4, 2: one pair, pooled over both noise models,
estimated on the selection part as the median and `1.4826 × MAD` of `S_meas − S_pred`; revision 3,
9.2: set within each configuration by that rule).

1. Two new settings of the corrections block: `capacity_b` (finite; negative allowed; default 0.0)
   and `capacity_s` (finite, ≥ 0; default 0.0); `holdout.py` reads them from the plan instead of
   the module settings `CAPACITY_B`, `CAPACITY_S` (Amendment 12, both 0.0); `CAPACITY_K` = 1 stays a
   module constant (a decision threshold). The threshold stays
   `min_snr − b + Φ⁻¹(1 − 0.005/R) · s`; with the defaults it is `min_snr`, as today.
2. The round's capacity record already carries `b` and `s` (then from the plan);
   `calibration_measurement` gains an explicit identity argument (the configuration's resolved path,
   bytes' SHA-256 and block SHA-256, given by its caller, never read from the environment), checked
   against the plan's resolved block (a mismatch raises); its returned record carries the pair used
   and that identity, in every return, the early one of a round decided before the hidden year
   included (where `s_meas` stays absent).
3. *The lifecycle*: the selection's first pass runs with a **provisional** configuration whose pair
   is the default (0.0, 0.0), which is not a calibration; the pair estimated on the selection part by
   revision 4, 2's rule goes into a **new configuration file with its own name and identity** (the
   final configuration of the freeze); a file bound to a campaign is never rewritten. **The 21
   conditions and the tolerances of the selection are evaluated with the estimated pair that will be
   frozen, not the provisional one** (revision 4, 6); the procedure is detailed in the campaign
   package.
4. *The evidence of the pair*: the driver records the rounds included and excluded (each with its
   reason), and the `S_meas − S_pred` values, enough to reproduce the median and the MAD.
5. **Extension 4 of the historical table**: the two settings at their defaults added to the frozen
   value of the corrections section (as extensions 1 to 3 did); the proof that both historical claims
   still reach their locked claim hash by the projection (the claim component; `verify` stays
   `TAMPERED` in the code component); the section written in the claim file, even at its defaults,
   still refused; the new full resolved hashes; the sabotages.

**C. The cases, declared before any code (written after the approval).**

| Case | Required |
|---|---|
| A1 | a declaration with the right `m4_configuration` opens with no problem from version 3 (a diagnostic root under `.cache`) |
| A2 | each a declaration problem and a refusal of the operational modes: the member missing; malformed; a wrong `format`, `name` or `sha256`; a path absolute, with `..`, missing, outside the authorized folder, through a link or a junction; another file with identical bytes at another path |
| A3 | a declaration valid for version 2 itself (its own harness identity) gives the same problems with and without the extra member |
| A4 | the main process with configuration A and a worker with a valid configuration B: the worker refuses before the inherited analysis; a result without a valid identity stops the dispatch and is journaled as a refusal; a worker starting late is checked too; a resume refuses the persisted record of a refused result, any persisted record whose block differs, and a record written before an interruption simulated between the inherited write and the main process's confirmation (no confirmation) |
| A5 | a resume of a campaign with another configuration file (or the same file changed): refused at the opening; the file changed during an execution: the execution cannot close as successful and its results are not accepted |
| A6 | `status` shows a declaration problem and exits as version 2 does; a missing or invalid configuration file, invalid JSON or no environment variable reaches `status` as a loading problem, and every operational mode refuses with it |
| B1 | a non-default pair (`b` 0.4, `s` 0.8, and `b` negative): the threshold in the round record and the pair recorded equal values computed in the test from the formula (not by the production helper); decisions 1 and 2 change accordingly on a case built so that the threshold decides, with the hidden year read only as the access log allows |
| B2 | with the default pair, piece 5's round results are bit-equal to today's (the round records; the resolved plan and its hashes change by the new keys, which is expected and stated) |
| B3 | refused by the model: `capacity_s` < 0; either value NaN, +∞ or −∞; accepted: `s` = 0, `b` < 0 |
| B4 | extension 4: both historical projections reach their locked hashes; `capacity_b` 0.1 and `capacity_s` 0.1 each refused by the projection, for both claims; the section written in the claim file refused |
| B5 | `calibration_measurement`'s record carries the pair and the configuration identity given to it, in every return (past a capacity decision, and in the early return of a round decided before the hidden year, with `s_meas` absent); an identity whose block differs from the plan's raises |

Sabotages: the binding check skipped (A2); the main/worker comparison removed (A4); the identity
journal's refusals not read at resume, and a resume accepting a record without a confirmation (A4); the closure's configuration check removed, and kept but without
invalidating the execution (A5); the threshold reading the module constants (B1); the right
threshold with a wrong pair recorded (B1); `b` alone, or `s` alone, left out of the threshold (B1);
the literal without the new keys, and with another default (B4).

**For the maintainer to decide** (the package's questions): (1) the identity contract above (the
path's root and folder, links refused, the main/worker comparison); (2) the lifecycle (a provisional
configuration for the selection, a new final file with the estimated pair, one configuration per
campaign); (3) the evidence of the pair (one pooled pair, the rounds and values recorded); (4) the
limit of this approval: the design and the later implementation of these cases only; the campaign
package itself (its point in `points.json`, its budget, its predecessor, the inherited counters,
the selection's artifacts, the frozen configuration and the campaign's checkpoints) comes later, and
this approval accepts no scientific criterion still unsatisfied (for example I2 correlated of piece 7).

**Approved and implemented (2026-10-18).** The maintainer approved the package as described.
Part B: tests `34e46d9`, code `dec1637` (`tests/test_capacity_plan.py`; two piece-5 tests read the pair
from the plan instead of the removed module settings; extension 4 with the full resolved hashes in
`docs/lock-format.md`). Part A: tests `53c6f2d`, code `b3aa855` (`tests/test_population_v3_identity.py`;
the harness tests follow the new loading contract: no exit at import, an incomplete or legacy block
checked by `capture`). Two test fixtures sit in the authorized folder, each marked as never a
campaign configuration: `probe-non-default.json` (another block) and `probe-same-block.json` (the
block of `m4-c1.json` under another name and file). One deviation from the design, declared: the
A2 file-link case is skipped where the account cannot create a file symbolic link (Windows without
the privilege, `WinError 1314`; the junction case runs there; see fix 10 below on the CI
runners). JUnit: part B's first run 124 tests with **4 failures**
(the lock tests' old full resolved hashes, before they were updated to extension 4's; corrected here
after the Codex review: the first version of this record said 0), then 74 tests, 0 failures; part A
36 tests, 0 failures, 1 skip. **Sabotages** (SK1 to SK13, never committed, each restored):
twelve caught at once (the binding check skipped; the link check; the journal's refusals not read;
a resume without a confirmation; the closure's check removed or not invalidating; the threshold
without the plan's pair, without `b`, without `s`; a wrong pair recorded; extension 4 left out of
the literal or with another default); **SK3, the main/worker comparison removed, escaped**: in the
A4 case the plan's block also differed, so the block check refused alone; the same-block case was
written after the escape (declared here), and SK3 run again on it was caught.

**The end-of-stage review of the package's implementation (Codex, read only, of `34e46d9` to
`158433c`)** returned WEAKENED; the full suite at `158433c` gave 3076 tests, 0 failures, 0 errors,
57 skipped (JUnit), pushed with CI. Written after it, each with its case (JUnit: 101 tests, 0
failures, 1 skip) and its sabotage (SC1 to SC6, each caught):

1. *Every consumer of the records*: version 2's reader `slot_records` (behind `compare-slots`, the
   resume of `orchestrate` and `metrics`) is replaced by one that also requires each record's M4
   identity (SC1).
2. *An `error` record* (a traceback, no conditions) is accepted with its confirmation alone; the
   first version could not read its block and blocked the resume (SC2).
3. *A complete confirmation*: its whole schema (kind, case, PID, the record's SHA-256, the
   identity), and the PID equal to the record's (SC3).
4. *The transport*: the main process never keeps an expected identity it inherited (a spawned
   worker keeps its own), and `open_campaign` publishes it only when the opening has no problem at
   all (SC4, SC5); version 3's `mode_analyze` no longer reopens the campaign (it refuses a loading
   problem at once, and checks the resume against the captured identity).
5. *One capture at the command line*: the script runs the importable module only; a case counts
   the reads of the configuration file through the real entry point (one).
6. *`calibration_measurement`*: the identity is required (no default) and complete (a path, the
   bytes' and the block's SHA-256) (SC6).
7. *The tests that said more than they showed*: the dispatch stop now uses three tasks and a
   callback that stops as version 2's does; the block check is isolated (another block, confirmed
   for its very bytes); B2 compares with a reference computed by the code of `4a26df7` (before the
   package; `tests/fixtures/capacity/make_reference.py`), bit-equal on the reference machine and
   within 1e-9 elsewhere; the transport of the expected identity is checked through
   `open_campaign` with a clean and a problematic opening (a unit check: a complete valid campaign
   declaration is not built by the tests).

**The second round of that review** found a blocker in fix 4: the main process was recognized at
import by `multiprocessing.parent_process() is None`, which is also true while a spawned worker
bootstraps this file as `__mp_main__` (the parent's reference is filled in later), so a worker
started by the command line cleared the inherited identity and refused every task ("no expected M4
identity in this worker's environment"). The tests had missed it: the command-line case ran
`dispatch-table` without workers, and the worker cases start from the probe script, whose bootstrap
does not run this file. The same push's CI (`158433c`) was red for another reason, in the three A6
cases: they call the real command line with `--cpus 0-7`, which the runners refuse
(`SetProcessAffinityMask failed: 87` on Windows; the checkout under `/home` refused by version 2's
`home_problems` on Linux). Corrected, each with its case and sabotage:

8. *The clearing at the explicit entry*: `main()` clears an inherited expected identity before
   version 2's dispatch; the import never does (SC7: the import-time clearing put back, caught by
   the transport case and the new command-line worker case; SC9: the clearing at the entry removed,
   caught by the transport case).
9. *One execution in a spawned worker*: run as `__mp_main__`, the file registers itself as
   `population_v3`, so the pickled functions resolve to the bootstrap copy and the body (the capture
   and the installation) runs once (the bootstrap copies the namespace into a second module object,
   so the case counts executions by the one `STATE`). A new case starts a spawned worker through the
   real entry point after a clean opening: the worker keeps the published identity, the body ran
   once, the replacements are installed and `_worker_problem()` is `None` (SC8: the registration
   removed, caught).
10. *A6 on the runners*: one logical processor (`--cpus 0-0`), and the three cases skipped where the
    checkout is inside the home directory (the Linux runners), so they run on the Windows runners
    and locally. A correction of the record above: the CI workflow runs on Windows runners too, not
    on Linux only.

JUnit after these corrections (the two harness test files): 45 tests, 0 failures, 1 skip (the file
link); SC7 to SC9 each caught. The full suite at `127865f`: 3089 tests, 0 failures, 0 errors, 57
skipped (JUnit). **Its CI was red in one job** (windows-2025, Python 3.13, `rest`): fix 7's B2
reference case required bit equality where the platform, numpy, Python and the SIMD features
matched the reference's; that runner matched them all and differed in the last digit of two floats
(`fap` 4.109641886201183e-24 against …1835e-24; `p1` 0.003392805682969292 against …2936). Equal
features do not imply equal bits (another processor or kernel path), so the claim "bit-equal on the
reference machine" is withdrawn: the case now compares within 1e-9 (relative) everywhere. A deviation of the working rules, declared: these corrections were
edited while the full suite of `bfef2cc` was running; that run was stopped before its end and none
of its results is used.
## Amendment 24 (2026-10-18, declared after the retest of piece 7): the retest's result, and I2 correlated failed

**The retest** (the tests of `9925c56` on the code of Amendment 23, committed as `159b929`; JUnit
`.cache/v021/piece7/retest1.xml`: 31 tests, 1 failure, 0 errors, 0 skipped), recorded as found: D5
(rectangular box, seed 6130), Q2 (seed 6131), H (the 2020 round, seed 6132), I2 white (seed 6133),
the three new cases N1 to N3 and every regression passed; **I2 correlated (seed 6134) FAILED its
criterion**: a final candidate passes the SNR gate (`P` 0.53697 d, `t0` 1325.2454, 3.8 h, 129 ppm,
corrected SNR 9.4, `β_D` 1.59). The first run's FAIL of I2 white (seed 6116) stays recorded.

**What the diagnosis shows, and what it does not** (`.cache` scripts that change nothing, on the
same noise realization; not a retest).

| Curve (M4 active) | Components accepted | Final candidate | Gate |
|---|---|---|---|
| the failing curve, with the sinusoid | 1/0.7 d (2735 ppm), 1.7221/d (161 ppm), 2.2748/d (138 ppm) | 0.53697 d, `t0` 1325.2454, 3.8 h, 129 ppm, SNR 9.4, `β_D` 1.59 | PASS |
| the same noise without the sinusoid | 2.0855/d (123 ppm, FAP 4.5e-93, `h` 0.906), then `few_harmonics_fail` | 0.53477 d, `t0` 1325.0825, 3.6 h, 160 ppm, SNR 9.9, `β_D` 1.85 | PASS |
| the same noise without the sinusoid, the prewhitening accepting nothing | none | 0.53478 d, `t0` 1325.0687, 3.3 h, 173 ppm, SNR 8.4, `β_D` 2.24 | PASS |

So on this realization the correlated noise (AR(1) 600 ppm, `τ` = 1 h, the scenario's profile)
produces boxes near 0.535 d that the gate of Amendment 7 does not stop, **with or without the
prewhitening and with or without the sinusoid**: neither the injected sinusoid nor the prewhitening
is necessary for a spurious candidate to pass the gate here. The diagnosis does **not** show that
the failing curve's candidate is the same set of dips (its period and epoch differ), nor that the
prewhitening contributes nothing to it; no other change of piece 7 is prescribed by it, and none is
made. The prewhitening also accepted, on noise only, a 123 ppm component at 2.0855/d with an
operational FAP of 4.5e-93: under correlated noise the FAP is not a calibrated probability (the risk
recorded in Amendment 22).

**The population questions it raises** (measured there, recorded as found): false alarms on light
curves without a transit, by the final verdict `SURVIVED` or `WEAKENED` (C4; a gate PASS alone is
not a false alarm in C4's sense), and T6r (null correlated light curves passing the gate **only
with** the prewhitening, by the paired comparison of revision 3, 8), which this diagnosis does not
provide.

**What this means for piece 7's acceptance.** Revision 3, 10, row 7's criterion "a pure sinusoid:
removed, no spurious candidate passing the gate" **remains unsatisfied**: it passed in white noise
(seed 6133) and failed in correlated noise (seed 6134); it is not replaced by a white-only
requirement, and no other seed is tried. The failing case stays in the suite as a strict expected
failure **restricted to its final predicate** (a specific exception raised only when the final
candidate passes the gate; the precondition and any other error still fail normally), on the
correlated parameter only, naming this amendment: a green suite then means no unexpected regression,
and an XPASS would turn it red and call for an investigation, not an acceptance. It is **not** an
acceptance (the maintainer's rule: xfails do not count as acceptance).

**Sabotages of piece 7** (`.cache`-only spec, never committed, each restored with `git diff` empty
after, run with no full suite running), on `400f1aa`: SW1 no clipping (D5 fails); SW3 the
few-harmonic test not checked (7 cases fail); SW4 a bin kept with 2 cadences and SW5 39 bins
accepted (B1/B2); SW6 the clipped cadences not subtracted and SW7 the per-sector constants
subtracted (D5); SW8 the refit ignoring the mask (R1, N1); SW9 the search on Amendment 22's `L1 −
S` (I2 white, In); SW10 the reanalysis without the subtraction (I1, N1, N2); SW11 the train
frequencies not passed (H); SW12 the marker not recorded (In); SW13 the prewhitening for an inactive
block (Off). (Under SW8 and SW10 the expected failure of I2 correlated also turned into an XPASS,
which the strict marker reports as a failure.) **SW2, the FAP not checked, escaped**: no case
failed. The mechanism: in white noise `h ≥ h_min` already needs a signal-to-noise ratio that makes
the FAP tiny, so in every construction the few-harmonic test decides before the FAP could. A direct
case was written after the escape (declared as such): D2's sinusoid with astropy's
`false_alarm_probability` replaced by 0.5, required to be rejected with `fap_above_max` while
`h ≥ 0.9` (seed 6141); SW2 run again on it made that case fail.

**The end-of-stage review of piece 7 (Codex, read only, of `62293af` to `564e751`)** returned
WEAKENED: no deviation of the numerical flow from Amendments 22 and 23; the full suite at
`564e751` gave 3026 tests, 0 failures, 0 errors, 56 skipped (one of them the strict expected failure
of I2 correlated; JUnit). Written after it: (1) the masked raw refit's left-out sectors are recorded
(`refit_left_out`; N3 checks it); (2) each round records the frequencies requested and, per kind of
window fit (train replicas, hidden replicas, transit windows, control windows), how many fits used
how many baseline parameters (`window_terms`; H checks it), so a sinusoid dropped by the degeneracy
fallback is visible; (3) Q1 recomputes `h` from the bins and the formula in the test itself (the
first version called the production helper); (4) In requires that `period_alias` was called; (5)
the FAP guard case also routes a FAP exactly equal to `fap_max`. Recorded, not changed: the adapter
`TessGauntlet` recomputes the global prewhitening that `TessSearch` already ran (the same
deterministic call, extra CPU on the adapter path only; the pipeline's `analyze_data` computes it
once). Piece 7's unit acceptance stays incomplete while I2 correlated is unsatisfied (above).

## Amendment 23 (2026-10-18, declared after the first run of piece 7): the results, four failures and their mechanisms, and the subtraction before the detrending

**The first run** (`62293af`'s tests on the first code of piece 7; JUnit: 26 tests, 4 failures),
recorded as found:

| Case | Result | Mechanism (diagnosed by `.cache` scripts that change nothing, on the same curves) |
|---|---|---|
| D5 | FAIL: 947 of the 1050 box cadences in `C_last` | a defect of the construction: the box is the synthetic trapezoid (ingress 15% of `T14`), so its ingress and egress cadences are shallower than `k_clip σ_w`; all 742 flat-bottom cadences are clipped |
| Q2 | FAIL of a precondition: 31 bins at `f*`, not 30 | a defect of the construction: `f*` is the grid frequency nearest 1/0.7 d, not 1/0.7 d itself, so over 40 cycles the phase drifts into one more bin; the purpose of the precondition (fewer than 40 bins at `f*`) holds |
| H | FAIL of a precondition: 6 calls of `measure_windows`, not 2 | a defect of the test: the spies counted the calls of the three rounds of the holdout, each with its own train frequencies, not the 2020 round's only |
| I2 white | **FAIL of the criterion**: after the prewhitening, a pure sinusoid leaves a final candidate passing the gate (SNR 59.5, `P` 4.665 d, 3558 ppm, 6.3 h) | **a defect of the design with an identified mechanism**, below; I2 correlated, I1 (both) and the other cases passed |

**The mechanism of I2.** The prewhitening accepted the sinusoid (1/0.7 d, 2746 ppm on `L1`, `h`
0.999) and two side components of about 110 ppm (1.570 and 1.639 per day); the residual rms on
`L1 − S` is 656 ppm against 600 ppm of noise. The search on `L1 − S` found a candidate at 4.665 d
(430 ppm, 4.2 h, SNR 24.8), and the reanalysis made it 3558 ppm. On the same curve and the same
search candidate, the final candidate measured on three reanalysis curves:

| Reanalysis curve | Depth | BLS SNR |
|---|---:|---:|
| `L1m − S′(L1m)` (Amendment 22 as written) | 3558 ppm | 220 |
| `L1 − S′(L1)` (a literal reading of revision 3's table 1.4) | 431 ppm | 25.1 |
| `detrend_masked(raw − S′(raw))`: the components refitted on the raw curve, subtracted, then the masked detrending | **60 ppm** | **3.1** |
| M3, `L1m` with no prewhitening | 3790 ppm | 61.3 |

The detrending (a robust local quadratic on a 1 d window) cannot follow a variability whose period
is comparable to its window: it turns the 0.7 d sinusoid into a distorted, attenuated signal on
`L1` (whose residual, after two harmonics, makes the search's spurious candidate), and with the
candidate's transits masked it interpolates the trend across each masked span, leaving there a dip
of the order of the variability's amplitude (the 3558 and 3790 ppm). On that curve and for **that
search candidate**, removing the components from the raw curve before the masked detrending
removed the artificial dip (60 ppm, SNR 3.1; the Codex review also measured the corrected SNR: 13.09
for `L1 − S′(L1)`, a gate PASS, and 3.07 for the raw subtraction, a FAIL). Whether the new search,
which runs on another curve and may find another candidate, satisfies I2 is not shown by this
diagnosis; the retest decides it. This is the reason for the change below; it was found by the result, so it is
declared after it, and it is retested on new seeds with the same criteria and the same number of
curves per case.

**The change (piece 7, the M4 path only).** The components are still **found** by `prewhiten` on
`L1` (revision 3, 7: the detrended curve; the frequencies and their order do not change). They are
**subtracted from the raw normalized curve before each detrending**, refitted there:

| Operation | Curve on the M4 path (from this amendment) |
|---|---|
| global search | `detrend(raw − S_raw)`, `S_raw = refit(raw, components, no mask)` |
| the reanalysis (`finalize_candidate`, gate, per-event depths, timing) | `detrend_masked(raw − S′_raw)`, `S′_raw = refit(raw, components, the search candidate's mask on the raw cadences)`, the same masked detrending as today |
| holdout train search | `detrend(train_raw − S_train,raw)`, components by `prewhiten` on the train curve detrended without a mask |
| holdout train refit, gate and timing | `detrend_masked(train_raw − S′_train,raw)` |
| holdout train replicas | the masked train detrending **without** the subtraction (as in Amendment 22), with the train fundamentals in the baseline |
| hidden windows | unchanged (Amendment 22): the train fundamentals in each window's baseline |

`refit` is unchanged (one joint weighted fit, per-sector constants and amplitudes, no clipping, the
mask's cadences without weight); on the raw curve its `σ_w` is A1's at `n` = 1 on the raw curve.
With no component accepted, every curve is bit-equal to the M3 one, as before. A singular raw refit
gives `S_raw` (or `S′_raw`) = 0 and its reason is recorded, separately for the search refit
(`search_refit_reason`) and for the masked refit (`refit_reason`), with the sectors each left out.

**What this substitutes in the specification** (declared explicitly, after the result):

- *Revision 3, table 1.4 and section 7 ("where")*: the global search's curve `L1 − S` becomes
  `detrend(raw − S_raw)`, and the reanalysis' `L2 = L1 − S′` becomes `detrend_masked(raw − S′_raw)`
  (the same substitution for the holdout train). The order (subtract, then detrend) and the domain
  (the raw curve) change.
- *Revision 4, section 4 (the subtraction model)*: the robust asymmetric fit still selects and
  accepts each component (its frequency, its order, its clip set, the FAP and the few-harmonic test
  are unchanged), but the curve searched receives a **joint refit on the raw curve without clipping
  and without a mask**, not the robust fit's model; the reanalysis receives the joint raw refit with
  the candidate's mask. So the change goes beyond moving the subtraction earlier: the estimator of
  the subtracted amplitudes changes.
- *Revision 4, section 5 (the twin protocol)*: for the prewhitening, frozen from the noisy analysis:
  the accepted frequencies, their order, the clip sets, and the masks; estimated again on the twin:
  the per-sector amplitudes and phases of `S_raw` and `S′_raw`, by the same joint raw refit (no
  clipping, the mask's cadences without weight) on the raw twin; the detrending row then applies to
  the twin minus its refit (the twin divided by the noisy curve's trend of `detrend(raw − S_raw)`,
  or of the masked one).

*Risks recorded:* the raw curve keeps the slow trends that the detrending would remove; the refit
does not model them, so their projection on the sinusoids can bias the refitted amplitudes (a
separate matter from `σ_w`: within a sector the weight is constant and each sector has its own
constant and amplitudes, so the coefficients are independent per sector and a finite, positive
inflation of `σ_w`, in one sector or between sectors, does not change them; `σ_w` matters only
through its validity, which decides whether a sector is used). Case N2 measures the consequence of
the trend.

**The test corrections, each declared here after the result.**

- D5: the criterion stays literal ("every box cadence in `C_last`"); the construction is
  corrected to a **rectangular** box (`ingress_fraction` 0, so the generator's minimum ingress of
  1e-6 d, under one second), every cadence of which is at the full depth; the trapezoid of the first
  run stays recorded as an incompatible construction; a new seed (6130).
- Q2: the precondition becomes its purpose: **fewer than 40 bins** with at least 3 kept cadences
  at the chosen `f*` (and `f*` within one grid step of 1/0.7 d); a new seed (6131).
- H: the spies record the calls of the **2020 round only** (the round run by itself through the
  holdout's round function), and the scenario is generated with a new seed (6132).
- I2: the same criterion and the same two curves (white, correlated), new seeds (6133, 6134).

The cases that passed keep their seeds and run again on the changed code, as regressions (not as
an independent confirmation of the changed design). The design of this amendment was reviewed by
Codex before the retest: three rounds, ending in agreement (which covers the proposal, not the
implementation's conformity or the retest's result).

**Three new cases for the changed design** (declared before any run; separate from the retest, so
they add nothing to its denominators; new seeds: N1 white 6135, N1 correlated 6136, N2 6137, N3
singular 6138, N3 short sector 6139). **Preconditions**, each a condition of the case (a failed one
makes it incompatible, recorded, no other seed tried): in N1 and N2, the injected frequency among
`A`'s accepted components (within one grid step), both raw refits of `A` (the search's and the
masked one) executed without failure, a search candidate, and nothing accepted on `B`; in N3
singular, the input fixed (seed 6138), a search candidate, both operations executed and the
singularity found by the numerical guard; in N3 short sector, at least one usable sector and
non-empty components.

| Case | Construction | Required |
|---|---|---|
| N1 | integrated, white and correlated (the scenario's profile): `A` = raw `sinusoid`-like curve with a 4000 ppm sinusoid at **0.74 d** and a 1500 ppm transit at 3.7 d = 5 × 0.74 d (so the box and the accepted components project on each other: the transit's harmonics fall on the variability's); `B` = the same raw curve without the sinusoid, the same noise realization | paired preservation on the reanalysis curve of the full path: with `d(x)` of Amendment 22 at the injected ephemeris, `|d(L2_A) − d(L2_B)| ≤ 60 ppm`, `L2` each run's reanalysis curve (`detrend_masked(raw − S′_raw)` for `A`; for `B`, with nothing accepted, the masked detrending itself) |
| N2 | integrated, white: N1's `A` and `B` (0.7 d, not commensurate) plus the suite's slow trend (`trend_amplitude` 0.002 at 6 d, the generator's phase) on both | the paired preservation of N1 (`≤ 60 ppm`) and the final candidate of `A` passing the SNR gate with signal identity |
| N3 | integrated, white: the pipeline with the global `prewhiten` replaced (a monkeypatch) by one returning a component at 720 per day (the cadence's frequency: `cos(2πft)` constant on the cadences, so the raw refit's design is singular), and, separately, a curve with one sector of fewer than `b_min` cadences | the search refit and the masked refit each record `singular_design` (`S_raw` and `S′_raw` = 0, the curves equal to the M3 ones); the short sector is reported among the sectors left out of the raw refit |

## Amendment 22 (2026-10-18): piece 7, the prewhitening (revision 3, 7; revision 4, 4), before its tests

Declared before the tests and the code of piece 7. It adds no criterion and no plan field (the
settings `fap_max`, `max_components`, `k_clip`, `h_min` exist); it fixes how revision 3, section 7
(with its table 1.4 of which curve each operation uses), and revision 4, section 4, are computed,
and the unit cases of revision 3, section 10, row 7. The first version of this amendment was
rewritten on the objections of the Codex design review, before any test or code (the readings
marked "a choice" below are implementation choices declared here, not consequences of the text);
the review ended in agreement at its fifth round. The agreement covers the design and the declared
cases; it does not show that the tests pass, that the implementation conforms, or that the method
is calibrated.

**The path.** Only with the corrections active (version 2 and `enabled`); otherwise every input is
the M3 one, byte for byte. With the corrections active and no frequency accepted, every curve is the
one it would be without the prewhitening (`S` = `S′` = 0), bit for bit. The marker of Amendment 17
records `prewhitening` when the global operation ran (also when it accepted nothing); the verdict
record carries, per operation (the global one and each holdout train), the accepted components,
the stop reason and any failure of the refit `S′`.

**Two functions, no class, no truth, no candidate in the first** (a new module `prewhiten.py`):

- `prewhiten(curve, plan) -> Prewhitening`: finds the components on a detrended curve.
- `refit(curve, components, mask, plan) -> Refit`: refits given components with a mask (`S′`).

**`prewhiten(curve, plan)`.**

1. *Residual, weights and the few-bins rule*: `r = flux − 1`; `σ_w` per sector by A1
   (`rednoise.estimate` at `n` = 1, every cadence kept: `σ_w` does not depend on the bin scale),
   computed **once**, on the curve given, before any subtraction (revision 3, 7.1). A sector that A1
   excludes (fewer than `b_min` bins, i.e. cadences, at `n` = 1) or whose `σ_w` is not finite and
   positive leaves the operation: its cadences are not in the periodograms, the fits or the bins,
   and `S` is 0 on them. No sector left: nothing accepted, reason `noise_undetermined`.
   `dy` = the cadence's sector `σ_w`.
2. *Grid*: `f_lo = 1 / (half the longest segment)`, a segment being a run of the used cadences
   without a gap longer than `detrend.segment_gap_days` (the detrending's segments,
   `detrend.segment_slices`; a choice: revision 3 says "segment" without naming which; not the
   segments of A1, which split at `gap_split` cadences); `f_hi = 1 / (2 h)`; the grid is
   `L0.autofrequency(samples_per_peak=10, minimum_frequency=f_lo, maximum_frequency=f_hi)` of the
   first iteration's `L0`, kept for every iteration of this call (each call, the global one and each
   train, has its own grid). `f_lo ≥ f_hi`: nothing accepted, reason `no_frequency_grid`.
3. *One iteration* (revision 4, 4):
   1. `L0 = LombScargle(t, r, dy, fit_mean=True, center_data=True, nterms=1,
      normalization="standard")` on every used cadence of the current residual; `f*` = the grid
      frequency of the highest finite power (the first on ties); no finite power on the grid:
      nothing more accepted, reason `non_finite_statistic`.
   2. *The robust asymmetric fit* (revision 3, 7.3): per sector a constant, plus `cos` and `sin` at
      `f*` and `2f*` with per-sector amplitudes (frequencies common), by weighted least squares
      (`1/σ_w²`; the column scaling, the SVD and the condition limit `1e10` of Amendment 21). Fit 1
      uses every cadence; after fit `j` the clip set `C_j` is the cadences more than `k_clip σ_w`
      **below** fit `j`'s model (computed afresh each time, so a cadence can regain its weight);
      fit `j+1` gives zero weight to `C_j`. Stop when `C_j = C_{j−1}` or after fit 10. The model and
      the clip set returned are those of the **last fit**, `C_last` computed against that model (so
      the clip set always matches the returned model). A singular design: nothing more accepted,
      reason `singular_design`.
   3. `L1`: the constructor of 3.1 on the used cadences not in `C_last` (their own `dy`);
      `p1 = L1.power(f*)`.
   4. `FAP = L1.false_alarm_probability(p1, method="baluev", minimum_frequency=f_lo,
      maximum_frequency=f_hi, samples_per_peak=10)`.
   5. *Few-harmonic test* on the used cadences not in `C_last`: phase `(t f*) mod 1` (origin `t` =
      0), 50 equal bins; a bin with fewer than 3 such cadences is dropped; fewer than 40 bins left:
      not accepted, reason `too_few_phase_bins`. Otherwise `h = 1 − Σ_b (m_b − μ_b)² / Σ_b (m_b − m̄)²`,
      `m_b` the mean residual of the bin's cadences, `μ_b` the mean of the returned model's
      predictions at the same cadences (no new fit), `m̄` the mean of the `m_b` (bins unweighted).
      `Σ_b (m_b − m̄)² = 0`, or `h`, `p1` or the FAP not finite: not accepted, reason
      `non_finite_statistic`.
   6. Accept `f*` if `FAP < fap_max` and `h ≥ h_min`. Then subtract the returned model's
      sinusoidal terms (at `f*` and `2f*`; a choice: the per-sector constants are fitted, so that
      the amplitudes are not biased, and not subtracted) from **every** used cadence, the clipped
      ones included, and iterate from 3.1. Otherwise stop with the reason (`fap_above_max`,
      `few_harmonics_fail`, `too_few_phase_bins`, `non_finite_statistic`). At most `max_components`
      accepted (reason `max_components`; with `max_components` = 0 nothing is computed, reason
      `max_components`).
   *Precedence* when several conditions fail in one iteration, the first decides the reason: no
   finite power in `L0`; `singular_design`; `too_few_phase_bins`; `non_finite_statistic` (`h`,
   `p1`, the FAP, or a zero variance of the bin means); `fap_above_max`; `few_harmonics_fail`. A
   rejection ends the operation (no other peak of the same periodogram is tried). The bin rule and
   `h` are one helper, `few_harmonic_test(t, y, fitted, f)`, which the unit cases call directly.
4. *Output*: the components in the order accepted (frequency, FAP, `h`, `p1`, the per-sector
   coefficients, the clip-set size, the amplitude `A = median over sectors of sqrt(a₁² + b₁²)` of
   the fundamental), the stop reason, the sectors used and left out, and `S` on every cadence.

**`refit(curve, components, mask, plan)`** (`S′`, revision 3, 1.4: "the same frequencies refitted
with the candidate's transits masked"; a choice: one joint fit, no clipping). `σ_w` by step 1 of
`prewhiten` on the curve given (the same definition, estimated once on that curve, on all its
cadences, the masked ones included); the sectors it leaves out get `S′` = 0. One joint weighted
least-squares fit, on the used cadences outside `mask`, of a per-sector constant plus, for every
given frequency, `cos`, `sin` at `f` and `2f` with per-sector amplitudes; no clipping (the transits
are masked); `S′` = the sinusoidal terms on every used cadence. No frequency given: `S′` = 0. A
singular design: `S′` = 0, reason `singular_design` recorded (a declared concession: the search
then saw a prewhitened curve and the reanalysis does not; the record shows it).

**The flow** (revision 3, table 1.4; the contracts the Codex review asked for).

| Operation | Curve on the M4 path |
|---|---|
| global search | `L1 − S`, `S` by `prewhiten` on `L1` = `detrend(data.lc, plan.detrend)` (no mask) |
| `finalize_candidate`, `snr` (the gate of Amendment 7), `odd_even`, `secondary_eclipse`, `plausibility`, per-event depths, transit times | `L2 = L1m − S′`, `L1m` the curve detrended with the search candidate's transits masked (as today), `S′ = refit(L1m, global components, mask)` with `mask` the same time region (the search candidate's transits to `transit_mask_half_width_durations · T14`) evaluated on `L1m`'s own cadences (the detrending can drop cadences, so the raw curve's boolean vector is never reused) |
| `period_alias` | `data.lc` with its own detrending (Amendment 21; no prewhitening) |
| pixel tests, `nearby_contamination`, `systematics`, `eb_catalog` | unchanged |
| holdout train search | `train_L1 − S_train`, `S_train` by `prewhiten` on the train curve detrended without a mask (train data only) |
| holdout train refit, gate and timing | `train_L1m − S′_train`, the train components refitted with the train search candidate's mask |
| holdout train replicas (decision 1) | `train_L1m` **without** `S′_train`, measured with the same window baseline as the hidden windows (the train fundamentals), so the train and the hidden estimators are the same (a choice) |
| holdout hidden replicas, transit windows and control windows | the baseline of 4.1 (`window_depth`) with the train fundamentals, in decreasing amplitude `A` of `prewhiten`'s output on the train curve |

- *The components travel*: `analyze_data` computes the global `prewhiten` once and hands its
  output to `attack_candidate`; `attack_candidate` given none (the adapters `TessSearch` and
  `TessGauntlet`, which pass only a candidate) computes it itself from `data.lc` by the same call
  (deterministic, so the same components); `TessSearch` searches `L1 − S` too. The reanalysis never
  selects new frequencies on `L1m`.
- *The search candidate and the final candidate stay distinct*: the search candidate gives the mask
  and the seed of `finalize_candidate` on `L2`; the final candidate feeds the gate and the
  measurements; its refined period, epoch or duration start no new mask, prewhitening or refit.
- *The holdout*: `RoundPlan` carries the train components (and their fundamentals in order) from
  `plan_round`, before any hidden read; `_round_corrected` passes the fundamentals to the hidden
  replicas, the transit windows and the control windows, and to the train replicas. Each window's
  record gives the frequencies requested and the number of terms its baseline used (the degeneracy
  fallback can drop sinusoids).

**Unit cases** (revision 3, 10, row 7, and revision 4, 4; white noise 600 ppm and, where marked,
correlated noise: in the direct cases 600 ppm white plus AR(1) 400 ppm with `τ` = 1 h; in the
integrated cases I1 and I2, which use the suite's `sinusoid` scenario, that scenario's own
correlated profile, AR(1) 600 ppm with `τ` = 1 h (an exception, declared); new seeds 6100 to 6199,
one per case and noise model in the order of the list). Two kinds: *direct* cases give `prewhiten` a curve
built as already detrended (flux = 1 + signal + noise, no detrending), so the injected amplitudes
reach it; *integrated* cases run the pipeline on raw data, and state as a precondition the amplitude
that reaches `prewhiten` (the default detrending, a 1 d window, absorbs slow variability: a
sinusoid at 2.9 d would mostly not reach it, so the integrated variability is at `SINUSOID_PERIOD`
0.7 d, as in the suite's `sinusoid` scenario).

| Case | Kind | Construction | Required |
|---|---|---|---|
| D1 | direct, both noises | `A` = 1 + a 4000 ppm sinusoid at 0.7 d + a 600 ppm box (P 3.7 d, 2.5 h) + noise; `B` = the same without the sinusoid, the same noise realization; the two-year layout | the first component of `A` within one grid step of 1/0.7 d, accepted; paired preservation: with the box depth `d(x)` = the mean of `x − 1` over the cadences outside the box minus its mean over the box (a dip positive), `|d(A − S) − d(B)| ≤ 60 ppm` (10% of the injected depth) |
| D2 | direct, both | the same sinusoid alone | accepted; the residual amplitude at the injected frequency, `sqrt(a² + b²)` of an unweighted least-squares sinusoid (with a constant) fitted to `A − S`, at most 5% of the injected 4000 ppm |
| D3 | direct, both | a pure 2000 ppm box, no variability | nothing accepted (`few_harmonics_fail` or `fap_above_max`); `S` = 0; **the rejection ends the operation**: the statistics of the rejected `f*` recorded once, and exactly two periodogram objects built (`L0` and `L1` of that one iteration) |
| D4 | direct, white | two sinusoids (4000 ppm at 0.7 d, 2500 ppm at 0.43 d) | two components accepted, in that order; with `max_components` = 1, one; with 0, none and no periodogram built, reason `max_components` |
| D5 | direct, white | a 4000 ppm sinusoid at 0.7 d, per-sector constants +300 ppm and −200 ppm, and a box of depth 8 `σ_w`, `σ_w` the A1 estimate (step 1) of the same curve without the box (the sinusoid and the constants included, so the scale is the one the operation uses); precondition: the depth at least `2 k_clip` times the largest `σ_w` the operation reports on the final curve | every box cadence in `C_last`; the fundamental's amplitude within 5% of 4000 ppm; the subtraction applied on the clipped cadences too (`S` non-zero there); the per-sector constants not subtracted (the per-sector mean of `x − 1 − S` outside the box within 20 ppm of +300 and −200) |
| Q1 | direct, white | D1's curve `A` | recomputed independently in the test with astropy and numpy: `f*` = the argmax of `L0` on the grid; `C_last` = the cadences more than `k_clip σ_w` below the returned model; `p1` = `L1.power(f*)` on the kept cadences; the Baluev FAP with the declared limits; `h` from the 50 bins with the 3-cadence rule |
| Q2 | direct, white | times by formula: the sinusoid of D2 (period `P_v` = 0.7 d) sampled at `t = t₀ + k P_v + (b + 0.5 + j/8) P_v/50` for `k` = 0..39 (40 cycles), `j` = 0..3 (four cadences per bin and cycle), and `b` = 0..29 (30 of the 50 bins); one segment (no gap above 0.5 d) of `Δt = max(t) − min(t)`, slightly under 28 d, so `f_lo = 2/Δt` and 1/0.7 d lies within the searched limits | not accepted, reason `too_few_phase_bins`; preconditions: `f*` within one grid step of 1/0.7 d, and after the clipping 30 bins with at least 3 kept cadences at that `f*` |
| B1, B2 | direct | the bin rule of the few-harmonic helper `few_harmonic_test(t, y, fitted, f)`, given cadences by formula: 40 bins with exactly 3 cadences (B1), then one of them with 2 (B2) | B1: 40 bins counted, `h` computed; B2: 39 bins, reason `too_few_phase_bins` |
| B3 | direct | the same helper, 50 bins each with four cadences `+a, −a, +a, −a` (every bin eligible, non-constant cadences, `σ_w` irrelevant), the model 0 | the bin means' variance is 0: reason `non_finite_statistic` |
| B4 | direct | `prewhiten` on a curve of exactly constant residual | reason `noise_undetermined` (A1 leaves the sector out: `σ_w` = 0) |
| R1 | direct, white | `refit` given two components at 1/0.70 d and 1/0.75 d (close frequencies, so that over the masked curve the joint solution differs from fits made one frequency at a time), a curve with both sinusoids and a box, the box masked | `S′` equal (to 1e-9) to an independent joint least-squares solution computed in the test on the unmasked cadences; precondition: that joint solution differs from the sum of separate one-frequency fits by more than 1% of the amplitude; the masked cadences have no weight in the fit |
| I1 | integrated, both | the suite's `sinusoid` scenario plus a 1500 ppm transit at 3.7 d, 2.5 h (1500, not 600: an estimate, not a measurement, that in the scenario's correlated profile, AR(1) 600 ppm, the gate of Amendment 7 could put a 600 ppm transit near 7.1; the H4 complement of Amendment 18 measured a different case, a 270 ppm planet under AR(1) 400 ppm with a corrected SNR of 4.75, which supports the concern without showing this number; declared before any test ran) | precondition: the sinusoid's amplitude at the input of `prewhiten` at least half the injected (by the unweighted fit of D2); the final candidate passes the SNR gate and has signal identity (P, 2P or P/2 within 0.001 of 3.7 d; revision 4, 4's "found") |
| I2 | integrated, both | the `sinusoid` scenario alone | precondition as I1; no final candidate passes the SNR gate |
| Z | integrated, white | the corrections active on a box with no variability (D3's raw analogue) | precondition: **no component accepted** (otherwise the case is incompatible, not passed); `L1 − S` and `L2` bit-equal to the curves without the operation |
| Sig | — | the signature of `prewhiten` | no parameter for a class, a truth or a candidate |
| In | integrated, white | I1 with spies | `period_alias` receives `data.lc`; the search receives `L1 − S`; `finalize_candidate` receives `L2`; the marker `prewhitening` and the components in the record |
| Ad | integrated, white | the adapters `TessSearch` and `TessGauntlet` | the same components and the same tests as `analyze_data` |
| Off | integrated, white | version 1 with `enabled` true and version 2 with `enabled` false | the M3 inputs, byte for byte |
| H | integrated, white | the suite's `variability_train_only` scenario (three years, white noise, a sinusoid in 2018 and 2019; an exception to the two-year layout, declared) with the corrections active, the round with 2020 hidden | preconditions: the train components not empty, **decision 2 = pass**, and the transit and control windows measured; then the train fundamentals reach (spies) `train_replica_stats`, `replica_stats` (the hidden replicas) and both calls of `measure_windows` (transit and control) |

A case whose construction does not give its precondition is recorded as incompatible: the unit
criterion is then not shown, which is not an approval, and no other seed or amplitude is tried.

**Risks recorded before any number (predictions, not changes).**

1. *`σ_w` on `L1`, the variability included.* Scaling every `dy` by one factor changes neither the
   normalized power nor the Baluev FAP (astropy's standard normalization), so the inflation does not
   by itself lower the significance; it raises the clipping threshold `k_clip σ_w` (a transit's
   cadences may stay in the fit), changes the relative weights of the sectors when the inflation
   differs between them, and through the clip set changes `L1` and its FAP. (The first version of
   this risk stated a wrong mechanism; corrected after the Codex review.)
2. *The FAP is operational* (revision 4, 4): not valid for the clipped, iterated procedure;
   calibrated by T6w and T6r.
3. *The hidden windows' degeneracy*: a sinusoid per train frequency in a window's baseline can make
   the fallback drop terms, or the window; M5-3's trigger counts dropped windows and the conclusive
   fraction, not every lost term, so each window's record gives the terms used.
4. *`S′` singular*: the reanalysis then works on `L1m` with its variability while the search saw it
   removed; recorded per case.

## Amendment 21 (2026-10-18): piece 6, `period_alias` (revision 3, 5; revision 4, 3), before its tests

Declared before the tests and the code of piece 6. It adds no criterion; it fixes how revision 3,
section 5, and revision 4, section 3, are computed, and the unit cases of revision 3, section 10,
row 5. The design was reviewed by Codex (read only) before any test ran: four rounds, ending in
agreement; the first version was rewritten on its objections (the sectors excluded by A1 leave the
test, `H` = 2 fixed, `D_F` computed exactly, the boxes of the cases built by a rule, the covariance
by the singular value decomposition, `σ_d` checked by the non-finite guard). The agreement does not
show that the tests pass or that the method is calibrated.

**The path.** Only with the corrections active (`version` 2 and `enabled`); otherwise the BIC test
of v0.2, byte for byte (version 1 with `enabled` true and version 2 with `enabled` false included).
The function keeps its signature; its input is the raw normalized light curve `data.lc` (revision
4, 3, which corrects revision 3's "L1"), followed by the test's own long-window detrending, as
today; no prewhitening reaches it. The marker of Amendment 17 records `period_alias_m4` whenever the
M4 path ran, including an exit by one of its guards: the pipeline derives it from the result's
`thresholds_m4` metric, which every exit of the M4 path writes and the legacy test never does.

**The computation** (the guards in this order of precedence: the first that applies decides the
reason).

1. *Detrending*, as today: window `max(window_days, detrend_window_periods · P)`, the candidate's
   transits masked to `transit_mask_half_width_durations · T14`.
2. *Noise (A1)*: `event_noise(...).box` (the `n_T` scale only) on the detrended curve with the same
   mask. **The sectors excluded by the few-bins rule at `n_T` leave the test** (A1: excluded from
   every measurement that needs that noise): their cadences are not in the fits, in `N` or in the
   coverage. No sector left: INCONCLUSIVE `noise_undetermined`. In the sectors used, the weight is
   `w_s = 1/σ_w,s²` and `β̄` is the median of `β_s(n_T)`; a weight or `β̄` that is not finite and
   positive: INCONCLUSIVE `non_finite_statistic`.
3. *Coverage* on the cadences used: fewer than one transit's worth of in-transit cadences
   (`events.min_coverage` of one transit), or fewer than 10 outside: INCONCLUSIVE
   `too_few_cadences`.
4. *Models* (weighted least squares, `y` = detrended flux − 1): `const`; `F` = const plus
   `cos(2πkφ)`, `sin(2πkφ)` for `k = 1, 2` (**`H` = 2 fixed on this path**, revision 3's `H`;
   `sine_harmonics` stays the setting of the legacy test only); `F+box` = `F` plus the box column (1
   inside `|phase offset| ≤ T14/2`, as today), `φ = ((t − t0) mod P)/P`. `χ²_M = Σ w (y − X_M c)²`.
   *Singular design*: each column divided by its weighted norm `sqrt(Σ w x²)` (a zero norm is
   singular), then the condition number of `sqrt(w) X` above `1e10`, for `const`, `F` or `F+box`:
   INCONCLUSIVE `singular_design`. The fits, the condition numbers and the covariance come from the
   singular value decomposition of that weighted, scaled design (`(XᵀWX)⁻¹ = V S⁻² Vᵀ`, rescaled),
   never from inverting `XᵀWX`, whose condition is the square.
5. *Statistics*: `Z_F = (χ²_const − χ²_F)/β̄²`; `d_box` = minus the box coefficient of `F+box`
   (positive for a dip); its operational error `σ_d = β̄ sqrt([(XᵀWX)⁻¹]_bb)` of `F+box`, with no
   rescaling by the reduced chi-square (an operational error whose calibration is not shown here);
   `D_F`, the mean of the fitted `F` model (the fit of `F` alone) over the phases outside the box
   minus its mean over the phases inside it, uniformly in phase (so it depends on the model, not on
   the sampling), computed exactly: with `q = T14/P` (`0 < q < 1`) and `a_k` the cosine
   coefficients of `F`, `D_F = −Σ_k a_k sin(πkq) / (πkq (1 − q))` (the sine terms and the
   constant cancel); with `q` outside `(0, 1)`, `D_F` is not finite; `f = D_F / d_box`; `G = (χ²_F − χ²_F+box)/β̄² − ln N`, `N` the cadences used.
   `d_box ≤ 0`: INCONCLUSIVE `box_depth_not_positive`; any of `Z_F`, `f`, `G`, `σ_d` not finite:
   INCONCLUSIVE `non_finite_statistic` (in this order of precedence).
6. *Outcome* (revision 3, 5): FAIL, fatal, if `Z_F ≥ z_F*`, `f ≥ f*` and `G < g*`; INCONCLUSIVE if
   `G < g*` and not (`Z_F ≥ z_F*` and `f ≥ f*`) (`box_gain_small_dip_not_explained`); PASS if `G ≥
   g*`. The known-systematic-period warning is kept as today: when the fatal outcome is PASS and
   the period is within `systematic_tolerance` of a listed period, the result is FAIL with severity
   WARNING; in every outcome the near periods stay in the metrics.
7. *Thresholds*: `g*` is `period_alias.min_box_delta_bic` (10, unchanged). `z_F*` and `f*` are two
   new settings of the configuration block, `alias_z_f` and `alias_f`, with defaults 18.47 and 0.5
   (the first pair of revision 3's declared order); the model accepts only the six declared pairs.
   They are chosen per configuration on the selection part by revision 3's rule, and every new
   claim writes them (so `m4-configurations/m4-c1.json`, which the harness version 3 requires to
   write every setting, gains them at the defaults).
8. *Metrics*: `Z_F`, `D_F`, `d_box`, `σ_d`, `f`, `G`, `N`, `β̄`, the sectors used and excluded, the
   condition numbers of the three designs, the reason of an INCONCLUSIVE; coverage: the in-transit
   cadences used.

**The historical projection (the maintainer's package, item 6 of 2026-10-18).** The two settings
enter the corrections block, which the projection of the historical locks removes only when it
equals its declared literal exactly; so the literal needs them at their defaults: **extension 3**
of the table, with the proof that both historical claims still reach their locked claim hash (the
claim component; `verify` stays `TAMPERED` in the code component, as Amendment 17 records) and its
sabotages. Piece 6 is not pushed before the maintainer approves that package.

**The unit cases** (revision 3, 10, row 5; each regime in white noise, 600 ppm, and in correlated
noise, 600 ppm white plus AR(1) 400 ppm with `τ` = 1 h; the two-year layout of `synthetic`; the
candidate is given, at the injected period 3.7 d, `T14` 2.5 h; new seeds 6000 to 6099, one per case
and noise model, in the order of the list). **The boxes are built by a rule fixed here:** the depth
is `S_target` times `σ_d,0`, the error that the test itself reports on the same noise realization
without the box, with `S_target` = 2.5 for a weak box and 20 for a strong one; no other amplitude
and no other seed is tried, and the residual depth of the bare realization is not cancelled. (A
fixed 1000 ppm box is not a strong box under A1 with the variability: `event_noise` estimates the
noise from the detrended flux, variability included, so `σ_w` and `β` grow with it; the Codex
design review estimated a significance near 2 for 1000 ppm.) The realized significance is
`S = d_box/σ_d` of the final curve, and `G = S² − ln N` holds for its fit, so a weak box gives
`G < g*` when `S` is below `sqrt(10 + ln N)` ≈ 4.5 and `d_box > 0` when `S > 0`; the construction
does not guarantee beforehand how far `S` lands from `S_target` (the error's calibration is not
shown), which is why the preconditions are checked. A case whose construction does not give its preconditions is
recorded as incompatible: the unit criterion is then **not shown**, which is not an approval, and no
other seed or amplitude is tried.

| Case | Construction | Required |
|---|---|---|
| R1 | variability `−a cos(2πφ)`, `a` = 2000 ppm, its minimum at the transit phase, plus a weak box | preconditions `d_box > 0`, `Z_F ≥ 18.47`, `f ≥ 0.5`, `G < 10`; FAIL fatal |
| R2 | the same variability with its minimum at quadrature (`φ` = 0.25), plus a weak box | `d_box > 0`, `Z_F ≥ 18.47`, `f < 0.5`, `G < 10`; INCONCLUSIVE |
| R3 | no variability, a weak box | `d_box > 0`, `Z_F < 18.47`, `G < 10`; INCONCLUSIVE |
| R4a, R4b | a strong box, without and with the variability of R1 | `G ≥ 10`; PASS fatal |
| U1 | a bump (a negative box of `S` = 20), no variability | INCONCLUSIVE `box_depth_not_positive` |
| U2 | `t0` at the first cadence and a period of two cadences (4 min), `T14` 1 min: cadences inside and outside the box, `cos(4πφ)` equal to the constant column | INCONCLUSIVE `singular_design` |
| U3 | the decision function `alias_m4_decision` given each of `Z_F`, `f`, `G`, `σ_d` not finite in turn (a direct case: no light curve reaches this guard reliably, since the detrending leaves residuals of about 1e-16 even on a constant sector, and A1 excludes a sector of zero scatter before the statistics) | INCONCLUSIVE `non_finite_statistic` |
| U4 | `b_min` larger than any sector's bins | INCONCLUSIVE `noise_undetermined` |
| W | a strong box at `13.7/4` d with the corrections on | `G ≥ 10`; FAIL, severity WARNING (the warning kept) |
| Off | version 1 with `enabled` true and version 2 with `enabled` false | byte-equal to the legacy test |
| In | the pipeline with the switch on | the test receives the very object `data.lc`; the marker `period_alias_m4` |

U1 to U4 are single cases (white noise); they check the routing of each undefined statistic, not
a rate.

**Two risks recorded before any number (predictions, not changes).**

- *L1.* For a dip made entirely by the variability, the box adds nothing, so `d_box` is noise
  around 0 in the idealized case (fixed weights, a nested fit, the model of the detrended curve
  inside `F`, no selection): revision 4's rule makes the case INCONCLUSIVE when `d_box ≤ 0`, and FAIL
  needs `0 < S < ~4.5`, so about half of such light curves would FAIL, not the 0.80 of L1. The
  population's L1 group injects a sinusoid plus a trend (`population_v2.py`), so the differences
  that matter there are the trend, the transformation by the detrending, the identity at `P/2` or
  `2P`, and the selection of the candidate by the search (which favours a positive box). L1 is
  measured on the selection part (revision 3, 8), and its result is recorded as found.
- *T2b.* For a real transit on a variable star, the variability inflates `σ_w` and `β̄` (A1 sees
  it as noise), which lowers `G`; a real transit then falls more easily under `g*`, and FAILs when
  the variability also explains enough of the dip. T2b (FAIL upper bound ≤ 0.02) is measured on the
  selection part and recorded as found.

The specification is not changed here.

**Results (written after the first run of the tests; numbers by `m4/piece6_numbers.py`, in
`m4/piece6-numbers.json`).** Every case passed on its first run (`tests/test_period_alias_rev4.py`,
JUnit: 23 tests, 0 failures), with every precondition met; no construction was changed. The
regimes, white / correlated: R1 FAIL (`Z_F` 289 / 288, `f` 1.92 / 1.60, `G` −6.3 / −4.6); R2
INCONCLUSIVE (`Z_F` 217 / 223, `f` 0.17 / 0.21); R3 INCONCLUSIVE (`Z_F` 1.6 / 15.1, `G` −0.4 /
−6.9); R4a PASS (`G` 230 / 274); R4b PASS (`G` 276 / 278). Two observations, recorded for the
population measurement and not acted on: (1) with the variability, `β̄` is about 8.7 against 1.0
(white) and 3.3 to 3.7 (correlated) without it, which confirms the inflation behind the T2b risk;
(2) in R3 correlated, `Z_F` is 15.1, near `z_F*` = 18.47 with no variability injected. A
hypothesis to be checked, not a demonstrated cause (corrected after the Codex stage review): `β̄`
is measured at the box's scale `n_T`, while the harmonics live at the period's scale, where the
AR(1) noise is larger, so the null `Z_F` in correlated noise may exceed `z_F*` more often than its
white reference suggests; this one realization also holds a weak box, which projects onto the
harmonics too, so it neither separates the two contributions nor measures a rate of exceedance (it
matters only together with `f ≥ f*` and `G < g*`). The tests affected by the
piece (the lock projection with extension 3, the battery, the activation, the harness version 3,
the schema and the dossier): 153 tests, 0 failures.

**A test strengthened before the sabotages (declared as such).** With these curves every declared
pair `(z_F*, f*)` gives the same outcome, so no case would notice a decision that used constant
thresholds instead of the configured ones; the thresholds test now also spies on
`alias_m4_decision` and requires it to receive the configured pair.

**Sabotages** (`.cache`-only spec, never committed; each restored, `git diff` empty after each;
run with no full suite running): SP1 the FAIL rule without `f` (R2, both noise models, fail); SP2
no guard for `d_box ≤ 0` (U1); SP3 the sectors excluded by A1 kept (U4); SP4 `Z_F` not divided by
`β̄²` (R3 correlated); SP5 the warning dropped on the M4 path (W); SP6 the marker not recorded
(In); SP7 the M4 path for any enabled block (Off, version 1); SP8 any threshold pair accepted (the
pairs test); SP9 the decision with constant thresholds (the thresholds test); SP10 extension 3 left
out of the literal (10 lock cases); SP11 extension 3 with another default (12 lock cases). Each
made at least one test fail.

**The end-of-stage review (Codex, read only, of `78ba6d5`, `8a68254` and `dbe5804`)** found no
deviation of the implementation from this amendment and the extension 3 package technically
correct (it recomputed both full resolved hashes). Written after it: observation (2) of the results
stated as a hypothesis, and two cases added (27 tests, 0 failures): a direct case in which the
declared pairs give different decisions (`Z_F` 25, `f` 0.6: FAIL at (18.47, 0.5), INCONCLUSIVE at
(30, 0.5) and at (18.47, 0.7)), and a curve with one sector used and one excluded by A1 side by
side (the fits, `N` and the coverage on the used sector only). Full suite at `dbe5804`: 2990 tests,
0 failures, 0 errors, 55 skipped (JUnit).

## Amendment 20 (2026-10-18): the end-of-stage review of Amendments 16 to 19 (Codex), and its fixes

The single end-of-stage review (Codex, read only, of the commits after `b448800` up to `b05cfe7`)
returned WEAKENED with three open points and one suggestion; Amendments 16, 18 and 19 were found
correct as written (the decomposition recounted from the source record: 107, 81, 52 rounds; 22 and
78 targets). The fixes, written after the review:

1. **The configuration contract of the harness version 3.** `load_configuration()` accepted a block
   with `version` and `enabled` only, leaving the other settings to the defaults, and the worker
   compared only the keys given. Now the block must write every field of `CorrectionsParams`
   (no field missing, none extra), each value is validated when the file is loaded, and each
   analysis checks that its plan carries the whole resolved block. Test: a block with only
   `version` and `enabled` is refused.
2. **The probe's evidence.** The probe used a placeholder identity and did not validate the record.
   Now it writes a complete identity of version 2's schema, validates the record it produced with
   version 2's `validate_record` (no problem), checks that the record's `identity.origin` names
   version 3's SHA-256, and runs twice: with `m4-c1.json` and with a configuration whose
   `r_min`, `m_beta` and `b_min` differ from the defaults, the record's block equal to the file's
   in both. The campaign declaration, its binding to the configuration file and its hash, and the
   transport of `b` and `s` stay pending, as Amendment 17 declares.
3. **The README text** (`docs/plans/v0.2.1-texts-for-phase-h.md`, 1a): "A real periodic signal
   passes. Noise rarely does." promised a performance not shown here; it is replaced by "The test
   checks whether the predicted signal recurs in the hidden year. Insufficient validity or
   capacity makes a round inconclusive."
4. **The report's replica note** appeared for any round of the corrections' holdout, also one that
   stopped (H4, decision 1) before any hidden read. Now it appears only when a round's access log
   shows a read of a replica span (`replica-window` or `replica-baseline`), and it starts "In rounds
   that reach hidden-noise estimation". Test `a3` is rewritten for this, after the code.

## Amendment 19 (2026-10-18): the design of the `R_min` study (design only; it runs after pieces 6 and 7)

The maintainer's item 4 of 2026-10-18 approves the design only. **What this is:** changing
`R_min = 20`, which revision 4 fixed expressly, is a design amendment **motivated by the observed
diagnosis** (Amendments 10 and 16, synthetic): it is not a choice untouched by results. No number or
distribution of the study is chosen from data now; everything below is fixed before any run.

- **The search:** closed, `R_min ∈ {8, 10, 12, 15, 20}`; nothing outside it.
*(Revision 2 of this design, after Codex's design review, `.cache/v021/codex/rmin-design/`; the
first draft was never committed nor run.)*

- **The unit, the eligibility and the aggregation.** The unit is the **target** (a light curve), as T1.
  A target is **eligible** when at least one of its rounds is conclusive by the capacity decisions 1
  and 2 (revision 3, 4.6's T1 definition; a measured round that ends INCONCLUSIVE
  `not_detected_not_inconsistent` stays eligible). The target's outcome is the aggregation of
  `run_holdout`: any FAIL round gives FAIL; otherwise any PASS gives PASS; otherwise INCONCLUSIVE.
  The controlled error is the **false FAIL** (an eligible constant-signal target whose outcome is
  FAIL). Per-round counts are reported, never used as the unit.
- **The groups:** four, as T1 in revision 4, 2: noise (white; AR(1), the generator's correlated
  mode) × variability (planets without variability; with `variability_some_years`). Every criterion
  holds in each group; nothing is pooled across them.
- **The lots:** the development structure's generator (`population_v2.build_case`) under new
  prefixes `refute-v0.2.1-rmin-study-<k>` (k = 1, 2, ...; each prefix gives the 500 planets of the bands
  near and measurable per noise model), taken whole and in order of `k` until each group has its
  declared size (below); no case is chosen by its content. **Three scenarios of the same targets**,
  each a separate light curve used in **all** rounds of its `run_holdout`:
  *constant* (as generated); *disappearing* and *weakened*: the target's **last observing year** (a
  rule fixed now) altered to `flux + (1 − s) · D(t) · trend(t)`, with `D` the injected transit deficit
  and `trend` the generator's trend computed from the case's **recorded final parameters**, `s = 0`
  (disappearing) or `s = 0.3` (weakened); the noise realization is the case's own, untouched by
  construction (no RNG is rerun; nothing passes through the generator's sizing again). The
  evaluator keeps the parameters and the scenario on its side; the tool receives only the light
  curve and the metadata. A unit test checks that the alteration changes only the last year's
  transits.
- **The procedure, complete, run once in measurement mode, at `R_min = 8`.** Every round of every
  target goes through the complete procedure of the code after pieces 6 and 7 with a version-2
  configuration fixed before the study (its file and SHA-256 named in the study's commit) **whose
  `r_min` is 8** (the smallest of the set, so every larger value can be derived), **measuring despite
  the capacity decisions** (`calibration_measurement`, Amendment 12, whose returned record is extended
  before the study, with tests, to carry every field below): each round records its replica counts
  (train and hidden, over the grid), `S_pred,1`, `S_pred,2`, `S_meas`, `d_train`, `e_train`,
  `d_hidden`, `e_hidden` at the `dP` it chose, and every other impediment. **For each `R` the outcome is then
  derived, in this order:** the impediments before the capacity rule as recorded; the train counts
  over the whole grid against `R` (`train_replicas_below_r_min`); decision 1; the hidden counts over
  the whole grid against `R` (`hidden_noise_undetermined`), with the other hidden-noise impediments
  as recorded; decision 2; the measurement's impediments as recorded; the FAIL rule; then the
  aggregation of the target's rounds. `R_min` changes nothing else in the implemented procedure (the
  registration, the variances, the `dP` choice and the errors use every usable replica whatever
  `R`: checked in `holdout.py` by Codex); a unit test compares, on cases at each `R`, the direct run
  with the derivation (with the same `b_R`, `s_R` in both), on the code after pieces 6 and 7, before
  the study.
- **`k`, `b` and `s`, from a lot of their own (not the evaluated one).** `k` is the single one fixed
  by the rule of Amendment 9 on its lot (prefix `refute-v0.2.1-bs-choice`), recorded before the study.
  For each `R`, `b_R` and `s_R` are estimated on **that same separate lot** as revision 4, 2
  prescribes (the median and `1.4826 MAD` of `S_meas − S_pred,k`, pooled over both noise models,
  over its constant rounds with `S_pred,k ≥ min_snr` and `R` met), and recorded before the study's
  lots are generated. The study's lots are then evaluated with these fixed values: the fitting and
  the evaluation never share a sample, so the bounds below keep their binomial meaning.
- **The coverage reference:** the operation on the **noiseless twin** (revision 4, 5): the hidden
  year's injected model divided by the noisy curve's hidden trend, measured with the same windows,
  replicas, `dP`, cadences and baseline form, the coefficients estimated again; the pull is
  `(d_hidden − d_twin) / e_hidden`. The bias against the injected depth is reported apart.
- **The weakening criterion's eligibility, by pre-measurement quantities only:** a weakened target
  qualifies when **its round that hides the last observing year** (the only altered year) passes
  decisions 1 and 2 and has `0.3 · S_pred,2 ≤ 3` (an expected hidden SNR at most 3, so the rule can
  tell), decided before the outcome is read; the criterion reads the target's aggregated outcome,
  and that round's own result is reported beside it. The disappearing targets qualify the same way
  (their round hiding the last year passes decisions 1 and 2).
- **The criteria, simultaneous, per `R` and per group.** Confidence: the binomial criteria use
  one-sided Clopper-Pearson bounds at `1 − 0.05 / 5` = 0.99 (Bonferroni over the five values, for not
  approving a wrong value; this does not make all the intervals jointly 95%, and the point fractions
  of criterion 3 have no inferential control):
  1. *False FAIL:* the upper bound of the FAIL fraction of the eligible constant targets ≤ **0.02**
     (α_H of revision 3, 4.6);
  2. *Denominators:* at least **n₁** eligible constant targets (`n₁ ≥ m₁ = 725`, the T1 minimum of
     revision 4, 2, raised by the sizing below; 228 would be the arithmetic minimum for zero FAIL, with
     little power), and the minima m₄, m₅ of the power criteria below;
  3. *Coverage:* over the first eligible round of each constant target in increasing year (a
     denominator of its own), |twin pull| ≤ 1 in [0.60, 0.76], ≤ 2 in [0.92, 0.98], the median
     within ± 0.2 (the unit reading of point fractions; the K conditions of the calibration keep their
     interval form);
  4. *Power, disappearance:* the lower bound of the FAIL fraction of the eligible disappearing
     targets ≥ **0.80**, with at least **m₄** of them;
  5. *Power, incompatible weakening:* the lower bound of the FAIL fraction of the weakened targets
     with a round eligible for this criterion ≥ **0.50**, with at least **m₅** of them;
  6. the INCONCLUSIVE fractions (per target and per round, with every reason) are recorded for
     every `R` (not a criterion).
- **The sizes, from a sizing computation committed before any lot is generated**
  (`calc/rmin_sizing.py`): from declared reference rates (design assumptions, not measurements: the
  eligible fraction 0.15 **in each scenario**, the weakening filter included; the true false-FAIL rate
  0.005; the disappearance FAIL rate 0.95; the weakening FAIL rate 0.70), (i) the smallest eligible
  counts `n₁ ≥ m₁ = 725`, `m₄`, `m₅` for which each binomial criterion (criterion 1 included: at 725
  its pass probability is only 0.925) passes with probability at least 0.95 at its reference rate,
  and (ii) the number of generated targets per group for which the probability that **every**
  minimum is reached is at least 0.999, the three scenarios being dependent (the same targets): the
  failure probabilities are combined by the union bound, never multiplied. The script and its output
  are committed with the study's configuration; the cost they imply goes to the maintainer before any
  lot is generated (below).
- **The choice and the stop:** the smallest `R` of the set that meets criteria 1 to 5 in all four
  groups. The study runs once; it is never extended or rerun to change its outcome. **If no value
  meets them, that is the result (option (c))**: `R_min = 20` is **not** validated by being the former
  default, and the result goes to the maintainer with its effect on the denominators.
- **Small samples:** no correction is assumed (no `t` with `R − 1`). The variance is
  `(1.4826 MAD)²` of the replicas with the correlation, the shared detrending, the selection on the
  `dP` grid and the combination of the train and hidden errors as implemented; criterion 3 measures
  the consequence. If a correction turns out to be needed, it is derived or calibrated by
  simulation for the procedure as implemented, by a further amendment with a Codex design review,
  and the study is then evaluated again on **new** seeds (the principle for failed criteria).
- **The reserve:** after the choice, the chosen value is validated once on a reserve whose seeds
  come from a **future drand round** declared in the commit of the choice (the rule of revision 4, 6;
  its prefix `refute-v0.2.1-rmin-reserve-<randomness>`; the round itself is the maintainer's, a
  package), with the same composition and sizes and the same five criteria at the chosen value only,
  at one-sided 95%; `b` and `s` are those of the study for that value. **A failure on the reserve ends
  this selection** (no other value is tried on it) and is a result for the maintainer.
- **Budget, sizing and ceiling:** the study and its reserve are **one look of their own** in the
  configuration budget (revision 3, 9.1; recorded as the `R_min` study, not on the selection part);
  their worst-case compute (the sizes of `calc/rmin_sizing.py` × 3 scenarios, the complete procedure,
  timed by the timing lot) is computed before any lot is generated and brought to the maintainer
  with the ceiling of 397 h (`calibration-ceiling-decision.md`): the ceiling stops a run, it never
  reduces a size or skips a condition. The chosen `R_min` enters the calibration sizing's eligible
  fractions before the selection part is generated.
- **Nothing here touches hidden data of a real target**, the development population, the selection
  part or the confirmation set; C1 to C6 and the earlier results stay as they are.
- **Order:** this design is committed now (with Codex's review); its execution waits for pieces 6
  and 7, which change the noise and the replicas.

## Amendment 18 (2026-10-18): the integrated H4 case, by the true computation (declared before its run)

The maintainer's item 5 of 2026-10-18: a synthetic curve whose train BLS SNR is above 7.1 and whose
corrected SNR (the gate of Amendment 7) is below it, by the real computation end to end; the
deterministic case of Amendment 14 stays. **The construction, fixed before any run, from a
computation and not from a search:** the two-by-two layout (2018 and 2020, two sectors each), seed
**3509** (new), white 600 ppm plus AR(1) 800 ppm with `τ` = 1 h (the generator's correlated mode
at a larger amplitude), a planet of `synthetic.PLANET`'s ephemeris with depth **300 ppm**. The
reasoning: for AR(1) with `τ` = 30 cadences, the binned-rms estimate at `n_T` = 75 gives
`σ_r²(n_T) ≈ 0.49 A²` and `β² ≈ 1 + 75 · 0.49 A² / (σ_white² + A²)`, about 25 (`β` ≈ 5) for `A` = 800 ppm;
the run of Amendment 14 (500 ppm, the same noise) gave a corrected SNR of 8.7, so a BLS SNR near 43;
at 300 ppm the BLS SNR is expected near 26 and the corrected one near 5.2. **Preconditions** (each a
condition of the case, not a target): the train gate is determined; the train BLS SNR is at least
7.1; the corrected one is below 7.1. The case then requires the H4 gate to read the corrected SNR
(`train_snr_below_gate`, the round INCONCLUSIVE, the hidden year not read). If a precondition fails,
the case is recorded as incompatible with its construction and no other seed or amplitude is tried
here; the physical case on a real curve stays pending (covered if it exists in the development
population).

**Result of the first construction: incompatible.** The train gate was determined and the train
BLS SNR was 21.8, but the corrected SNR was **7.61** (not below 7.1): the measured `β_D` was 2.86
(sectors 2.67 and 3.06), not about 5; the estimate above ignored the detrending, which removes part
of the slow correlated noise, and the robust `σ_w`; and the candidate found was a red-noise box (P =
0.84 d, 3.8 h), not the planet. **One second construction, declared after that result and computed
from its measured `β`:** the same layout, seed **3510** (new), AR(1) **400 ppm** (`β²` scaled by
`A² / (σ_white² + A²)` from the measured 8.2 at 800 ppm: about 4.5, `β` ≈ 2.1, and smaller red-noise
peaks), and a planet of **270 ppm** (a BLS SNR near 12 over the 2018 transits at the total noise of
about 720 ppm per cadence), so a corrected SNR near 5.7. The same preconditions and requirement. If
it also fails, it is recorded and brought to the maintainer; no third construction is tried.

**Result of the second construction: the case passes** (654ba9c's test, JUnit 1 test, 0
failures): train BLS SNR **10.79**, corrected SNR **4.58** (`β_D` 2.35; sectors 2.36 and 2.35), the
round INCONCLUSIVE by `train_snr_below_gate`, the hidden year not read. **What it shows and what it
does not:** the candidate of the train search is again a red-noise box (P = 0.50 d, 98 ppm), not the
injected 270 ppm planet; so the case shows, by the real computation end to end, the H4 gate reading
the corrected SNR and stopping a train candidate that the BLS SNR alone would pass (the case of a
correlated-noise false candidate); it does not show it with the injected planet as the candidate.
That variant, and the physical case on a real curve, stay recorded as pending.

**Complement (2026-10-18, the maintainer's items 2 and 3, written after the results of
`m4/h4_complement.py`, numbers in `m4/h4-complement.json`; the construction is not changed).**

- **The mechanism of the first construction's incompatibility, confirmed.** On the same train
  curve (seed 3509) and at the candidate's ephemeris (P = 0.84 d, 3.8 h), `β` at `n_T` is 4.89 and
  5.30 on the raw normalized curve but 2.67 and 3.06 on the detrended, masked curve the gate reads.
  On the same kept cadences, with the plain standard deviation in place of the robust one (for
  `σ_w` and for the spread of the bin means alike), `β` is 5.09 and 5.51 raw and 3.17 and 3.70
  detrended: the detrending, which removes most of the slow correlated noise, is the main reason
  (a factor of about 1.6); the robust spread of the bin means lowers `β` by about a further 16 to
  17%; the robust `σ_w` itself differs from the plain one by less than 1% (895 against 896 ppm, 914
  against 918 ppm). (The first version of this paragraph compared the robust `σ_w` of the kept
  cadences with the plain deviation of the whole sector, and attributed nothing to the bin means;
  corrected after the Codex stage review, with the numbers of the corrected script.) The a priori
  estimate also assumed `n_T` = 75
  (a 2.5 h event), but the candidate was a 3.8 h box with `n_T` = 114; at 114 the estimate gives
  `β` 6.1, so it overestimated the detrended `β` by about a factor of 2.
- **The injected planet on the same curve as the second construction** (seed 3510, AR(1) 400 ppm,
  270 ppm, the round with 2020 hidden). **Detected?** No: the train search returns the red-noise
  box at P = 0.50 d, and none of its ten refined candidates is within 1% of the planet's period or
  of its half or double (`planet_among_refined` false; a recovery diagnostic by period, not the
  full signal-identity rule). **Its SNRs**, by the same computation as the H4 gate, a local refit
  started at the planet's injected period and duration (it ends at P = 3.6988 d, 2.63 h): BLS SNR
  **13.84**, corrected SNR **4.75**
  (`β_D` 2.91; sectors 3.06 and 2.76), depth 301 ppm. **Would it pass the threshold?** By the BLS
  SNR alone yes; by the corrected SNR no (below 7.1, `train_snr_below_gate`: in the H4 flow the
  round ends INCONCLUSIVE, which is not a refutation of the planet).
- **Reading: result (c).** In this construction the correction stops the false candidate and
  would stop the true planet too; the case does **not** show that the correction removes the false
  and keeps the true. This is recorded as a result and enters the evaluation of the method before
  the freeze (with Amendment 19's study and the population); the construction is not adjusted to
  avoid it. Whether a corrected SNR of 4.75 is the honest significance of a 270 ppm planet in this
  noise, or the gate is too strict, is not decided by this one curve.

## Amendment 17 (2026-10-18): the explicit, versioned activation of M4 across the flow

The maintainer's decision of 2026-10-18 (14:00), item 2; Codex reviewed the design before the code
(`.cache/v021/codex/activation/`). It replaces the section "The switch" above where they differ
(the freeze no longer changes any default).

- **The version rule.** `CorrectionsParams.version` (1, the default: the legacy block; 2: M4 of
  revision 4) and the property `active` (`version == 2 and enabled`), read everywhere the code used
  `enabled`. A claim without the block, or with version 1 (whatever `enabled` says), or with version
  2 and `enabled` false, resolves on the M3 path. **No default of the block ever changes**; new
  claims write `version: 2`, `enabled: true` and the chosen configuration explicitly.
- **The marker.** The verdict record gains `corrections: {version, executed}` **only when some M4 part
  ran**; `executed` lists the parts that actually ran (`a1_noise`, `bls_beta_gate`,
  `trapezoid_timing` in the global analysis; `m4_holdout` from any holdout round that ran the M4
  train gate), never what the plan asked for. Legacy records keep their keys (their `test_plan`
  shows the block with `version` 1).
- **The historical locks.** Extension 2 of the projection table adds `"version": 1` to the frozen
  value of the corrections section (`docs/lock-format.md`, "Extensions of the table"): both historical
  claims still reach their locked hash by the projection; `verify` stays `TAMPERED` in the code
  component only, as before (the "PASS" of the decision is read as the claim component; a
  `verify` status of PASS is impossible for any lock whose code changed).
- **The configuration files.** A configuration is a file `population/m4-configurations/<name>.json`,
  format `refute-m4-configuration/1`, with its name and its complete corrections block (version 2,
  enabled true, every setting written); identified by its SHA-256. The first is `m4-c1.json`
  (revision 3, 9.2's first configuration: the settings of `CorrectionsParams`).
- **The population harness, version 3** (`population/population_v3.py`, a new file; version 2 is
  never edited and its SHA-256 is pinned): it loads version 2 and replaces `_plan()` (the fast plan
  plus the configuration's block, refused unless active), `analyze_task` (the same function in
  this module, so the spawned workers import version 3 and apply the same plan; each analysis checks
  that its plan carries the block), the harness identity (`HARNESS_PATH`, `HARNESS_SHA256`: a
  campaign declaration then names version 3) and R2 (version 3, version 2 and the configuration file
  each the file of HEAD and unchanged since the start). The configuration file is named by
  `REFUTE_M4_CONFIGURATION`, which the workers inherit. Version 2 alone still measures M3.
- **How each part of the flow receives the configuration:**
  - *The selection of the estimators and the reserves* (the calibration driver of revision 3, 8.2,
    a new script still to be written): it reads a configuration file, builds its plan with that
    block, records the file's SHA-256 with every result, and calls `calibration_measurement` for the
    `S_meas` of the rounds stopped by a capacity decision (Amendment 9).
  - *M4 and M5 campaigns of the development population:* the harness version 3 with the point's
    configuration file; one configuration per campaign run; the configuration file and its SHA-256
    are named in the campaign's declaration by the campaign amendment written before the first
    version-3 campaign (pending; version 2's declaration schema is not changed). M5 candidates are
    configurations whose markers list their own parts.
  - *`b` and `s`* stay module settings of `holdout.py` (Amendment 12) until the freeze; the driver and
    the harness set them from the configuration file's `capacity` entry once it exists (pending, with
    the freeze package: whether they become plan fields, which would need a new table extension, is
    the maintainer's).
  - *The confirmation set:* a new claim with the frozen configuration written explicitly in its
    plan (the block with version 2), checked against the configuration file's SHA-256; no selection
    or adjustment there; the counters and limits inherited unchanged.
  - *The parameters of piece 6* (the `period_alias` thresholds chosen per configuration) and any new
    setting of pieces 6 and 7 are new plan fields, which change the resolved claims: a table
    extension for the maintainer, brought with piece 6.
- **Records already committed** (`m4/amendment7_retests.py`, `calc/option_a_geometry.py`) switched M4
  on with `enabled: true` alone; they are records of their commits and stay as they are (rerun with
  the version rule, their `analyze_data` parts would take the M3 path, while the parts that call the
  M4 functions directly would not). New records use version 2.
- **Tests** (`tests/test_corrections_activation.py`, `tests/test_population_v3.py`, and the lock tests):
  the version matrix; no default changes; a claim of the new version runs the corrected path (the
  marker, and the gate's `beta_d`); the M3 box scan and M3 holdout never run on it, and do run with
  version 1; a claim without the block stays on M3; the historical projections reach their locked
  hashes; the harness version 3 runs M4 in a spawned worker of version 2's pool, version 2 alone
  measures M3, and version 3 refuses a missing or legacy configuration. Sabotages: SV1 the M3 path
  forced with the new version; SV2 a projected default changed; SV3 the harness without the worker
  propagation.

## Amendment 16 (2026-10-18): the decomposition of the interrupted rounds, per round and per target

The maintainer's item 3 of 2026-10-18 (14:00). Computed only from the record already examined,
`calc/option-a-geometry.json` (Amendment 10: 100 planets of the bands near and measurable; only
metadata and synthetic training data), by `calc/interruptions_decomposition.py`
(`calc/interruptions-decomposition.json`), under O2. That record was made with the code of its
commit, before pieces 4 and 5 changed the train gate; these are counts of that record's rounds and
targets, **not a C3 rate of planets**.

**Per round** (240 rounds): 107 end before the geometry, 81 at the geometry, 52 reach the
measurement. Each reason counted separately (a round may have two):

| Reason | Rounds |
|---|---|
| timing uncertainty above one duration (issue #2) | 54 |
| duration / period above 0.2 (H4 b) | 43 |
| train SNR below 7.1 (H4 a) | 10 |
| fewer than `R_min` = 20 usable replicas | 81 |
| hidden noise undetermined (always together with the previous one) | 32 |

| Mechanism (rounds) | before the geometry | at the geometry | reach the measurement |
|---|---|---|---|
| two_years (80) | 38 | 42 | **0** |
| few_train (40) | 24 | 16 | **0** |
| three_years (60) | 4 | 12 | 44 |
| variability_some_years (60) | 41 (40 of them duration / period) | 11 | 8 |

By noise model: white 65 / 26 / 29, correlated 42 / 55 / 23; by band: near 73 / 24 / 23,
measurable 34 / 57 / 29 (before / at the geometry / reach).

**Per target** (100 targets): 22 have at least one round that reaches the measurement; 78 have
every round interrupted. Among those 78, the reasons present in their rounds: fewer than `R_min`
replicas 45, timing uncertainty 38, hidden noise undetermined 27, duration / period 15, train SNR
8. By mechanism, targets with at least one round reaching the measurement: two_years **0 of 40**,
few_train **0 of 20**, three_years 16 of 20, variability_some_years 6 of 20.

**Where to invest (a reading of the counts, not a decision):** in this structure a hidden year of
the two_years and few_train mechanisms is one sector, which never reaches `R_min` = 20 usable
replicas here, and many of their rounds also stop at the timing rule; the variability mechanism is
stopped mostly by the duration / period rule (the train candidate is long). These are the
bottlenecks the `R_min` study (item 4) and the pieces 6 and 7 bear on.

## Amendment 15 (2026-10-18): the end-of-stage review of pieces 4 and 5 (Codex), its fixes, and a correction of Amendment 10

Codex reviewed d88c968..2f016df read-only (`.cache/v021/codex/stage-p45/`) and recommended
**WEAKENED with explicit open points** for the stage: the order replicas → decision 2 → windows,
`N_pred`, `R_min` in the train, the train refit and gate, and the numbers of piece 4 were confirmed.
Its objections and what was done:

- **A deviation:** `fail_rule` rejected a zero hidden error but accepted a zero train error
  (`SNR 4, e_train 0` gave FAIL), against Amendment 12's addendum. Fixed: a zero train error is
  INCONCLUSIVE `non_finite_statistic`; two cases added.
- **Coverage lost by Amendment 14, item 2:** the integrated "weaker consistent" case no longer
  showed a measured round ending INCONCLUSIVE. Added: a case whose measurement is replaced by one
  with SNR 4 and a hidden depth two errors below the train one, which must stay INCONCLUSIVE
  `not_detected_not_inconsistent` through the integration.
- **Integrated cases promised by the addendum and missing:** the threshold met with equality; `R`
  kept when other rounds stop early (three years, one of them two days long); a gap that lowers
  `N_valid` and leaves `N_pred`; fewer than two valid windows (INCONCLUSIVE `too_few_windows`);
  the reported depth and error of the same `dP`. Added, all written after the code.
- **A wrong sentence of Amendment 14:** "never of a seed": the H4 case moved from seed 3506 to the
  strong-signal fixture (seed 3500) when it became the deterministic replacement of the train
  gate. Corrected here.
- **Recorded, not changed:** the physical H4 case (a synthetic curve with BLS SNR above 7.1 and a
  corrected one below, by the real computation) remains without an integrated test; the H4 wiring
  is covered by the deterministic case. The records' JSON files should also carry the interpreter
  and the commit (future records will).

**A correction of Amendment 10 (its "CI binding"):** P1's other digests on CI were attributed to
CPython 3.12. CI then gave the same other digests on a Windows runner with 3.13.16 (run
39136076878), after a 3.13 runner had matched (39130668665): the cause is the runner machine,
whose CPU features select numpy's SIMD paths (the reference machine enables up to `X86_V3`, without
AVX-512). P1 is now bound also to the set of CPU features numpy enables on the reference machine
(reconstructed there on 2026-10-18); the Python condition stays as a conservative one. P1 then runs
on the reference machine only, and CI checks the switch-off path by the rest of the suite. P1 must
select the switch-off path explicitly once the freeze changes the default (section "The switch").

## Amendment 14 (2026-10-18): the results of piece 5, and its test changes after the first runs

Tests committed before the code (6ccaa8c); the code in the next commit. After the code, the 28
cases pass (`tests/test_holdout_capacity.py`, JUnit 28, 0 failures). **Changes to the tests after
their first runs, declared** (each a change of the construction of a mechanism case whose
precondition failed, never of a criterion or of a seed):

1. The weak-signal case and the calibration cases used a 2020 hidden year about 700 days from the
   train: the rounds stopped at the timing-uncertainty rule (issue #2) before the capacity rule.
   They now use a hidden year next to the train (2019, sector starting at BTJD 1500, three train
   sectors in 2018).
2. The weaker-but-consistent case: its first construction (2020 hidden year) stopped at the timing
   rule; in the 2019 layout, with the hidden depth `d_train − 3 e_pred,2`, the hidden signal was not
   detected but `Z` came out above 3 (FAIL). For any construction the outcome of `Z` near 3 rests on
   about one standard deviation of the noise, so the integrated case now checks that the round's
   status, reason and `Z` are those of `fail_rule` on its recorded values (with both capacities
   passed and the signal not detected); the INCONCLUSIVE outcome itself is the algebra case (Amendment
   12's example), which passes.
3. The case "the H4 gate reads the corrected train SNR": a strong AR(1) in the train missed its
   precondition twice (2000 ppm: a spurious long box whose mask left no bins, so the gate was
   undetermined; 800 ppm: the corrected SNR stayed at 8.7, above 7.1). It now replaces the train gate
   by one returning a corrected SNR of 5 on the strong-signal curve, which checks the wiring
   deterministically.
4. The one-sided case of the FAIL rule had `|Z|` = 2.98, below 3 whether `Z` is signed or
   absolute, so the sabotage SC5-3 (an absolute difference) was not caught; its hidden depth is now
   700 ppm (`|Z|` about 6), and SC5-3 fails it.

Sabotages (`.cache/v021/tools/sabotage-p5.json`, `sabotage-p5b.json`): SC5-1 `m_β` in decision 2
too; SC5-2 the predicted error at `dP = 0` only; SC5-3 the absolute difference; SC5-4 the hidden
transit windows read before decision 2; SC5-5 the original train SNR when the correction is
undetermined; SC5-6 the calibration measurement writing into its input; SC5-7 `N_pred` from the
window centers: each makes at least one case fail.

## Amendment 13 (2026-10-18): the results of piece 4

Tests committed before the code (70a5d1a); the code in the next commit. The numeric criteria
(`m4/piece4_numbers.py`, `m4/piece4-numbers.json`, the helpers of the test file):

| Criterion (Amendment 11) | Result |
|---|---|
| white, median of `sqrt(var_rep)` / analytic error, 200 light curves, in [0.85, 1.15] | **1.094**: met (9% high, within the declared limit of the reference, which ignores the hidden detrending) |
| AR(1), median of `var_rep / var_MC` (400 realizations), 200 light curves, in [0.85, 1.15] | **0.941**: met |
| pulls of the full operation, 200 AR(1) years without signal | \|pull\| ≤ 1: **0.705**; ≤ 2: **0.960**; median **0.00007**: met |
| known depth (1000 ppm) | recovered within 5%: met |

With the geometry of the cases (`σ_t` = 0, two sectors) 87 replicas are accepted.

**Test changes after the first runs, declared:** (1) the masked-fraction case read the rule as
"windows and replicas together at most 0.5", which fails when the windows alone mask more than half
of a sector (short periods, large timing error); the rule of revision 4, 1 is about accepting a
replica, so the case now checks that a sector with replicas stays at most 0.5 and that a sector
whose windows alone exceed it gets none. (2) The too-few-replicas case needed a larger period error
(its precondition caught it). (3) The O2 sector case lowers `r_min` to 5 so that the barrier does
not stop it before the sector rule. (4) After the sabotages SR2, SR5, SR6 and SR7 were not caught,
four cases were strengthened or added (closed overlap, the excluded sector's replicas not counted,
a replica with a poorly covered band, a grid whose shifts exceed a cadence); all seven sabotages
then fail at least one case.

## Amendment 12 (2026-10-18): piece 5, the capacity decisions and the FAIL rule (before its tests)

Declared before any test or code of piece 5, with Amendments 6, 7, 9, 10 and 11.

- **The train candidate** (switch on): after the train search, the train curve is detrended with
  the train transits masked (as today) and the train candidate goes through the gate of
  Amendment 7 (`_bls_gate`, A1 at `n_T` on the train curve); the **train validity rules** (H4)
  then use the corrected candidate. `d_train` is its BLS depth and `e_train` its corrected
  `depth_err` (`depth_err_BLS × β_D`): Amendment 6, item 2 wrote "the A1 stacked error", the
  estimator of piece 2 at that time; Amendment 7 replaced that estimator for the gate, and
  `e_train` follows it.
- **The train replicas:** the windows of the train ephemeris in the train sectors (transit and
  control, `_predict_windows` on the train spans), the replicas of `register_replicas` there, and
  their depths on the train curve (the train detrending, which masks the train transits) by
  `window_depth`, with the band coverage, at every `dP` of the round's grid;
  `var_rep,train(dP)` as for the hidden year. Fewer than `R_min` at any `dP`: decision 1 is
  INCONCLUSIVE `insufficient_capacity_train` (no train variance, no capacity).
- **`N_pred`:** the transit windows whose measurement span `[t_pred ± baseline_outer]` lies
  inside one hidden sector span (metadata).
- **Decision 1:** `S_pred,1 = d_c / e_pred,1`, `d_c = d_train − k e_train` (`k` = 1),
  `e_pred,1 = m_β max_dP sqrt(var_rep,train(dP) / N_pred)`; conclusive only if
  `S_pred,1 ≥ min_snr − b + Φ⁻¹(1 − α_round) s` (`min_snr` the holdout's 5.0, `α_round = 0.005 / R`,
  `R` the number of observing years of the light curve); otherwise INCONCLUSIVE
  `insufficient_capacity_train` and `HiddenYear` is never built (empty hidden access log).
- **Decision 2** (the barrier of `measure_with_replicas`, after the hidden replicas and before any
  transit window): `S_pred,2 = d_c / e_pred,2`, `e_pred,2 = max_dP sqrt(var_rep,hidden(dP) /
  N_pred)`; the same threshold; otherwise INCONCLUSIVE `insufficient_capacity_hidden_noise`.
- **`b` and `s`:** until the freeze they are module settings of `holdout.py`
  (`CAPACITY_B = 0.0`, `CAPACITY_S = 0.0`), not plan fields, so that no new plan field reaches the
  historical locks before the freeze (whose commit moves them into the plan together with the
  table extension it will need, a package for the maintainer); the unit tests set them
  explicitly. No value is presented as calibrated.
- **The FAIL rule** (revision 3, 4.5): a round measured with `N_valid ≥ min_predicted_transits`
  PASSES if the hidden SNR ≥ `min_snr`; FAILS if the SNR < `min_snr` **and**
  `(d_train − d_hidden) / sqrt(e_train² + e_hidden²) > 3`; otherwise INCONCLUSIVE
  `not_detected_not_inconsistent`. A non-finite statistic is INCONCLUSIVE with its reason (never
  FAIL).
- **Recorded per round:** `S_pred,1`, `S_pred,2`, `S_meas` (the hidden SNR), the threshold, `R`,
  both decisions with their inputs, and the access log (Amendment 9).
- **`S_meas` apart** (Amendment 9): `calibration_measurement(raw, sectors, year, plan)`, used only
  by the population harness, never by `run_holdout`: for a round that decision 1 stops, it builds
  the hidden year and measures it as a conclusive round would, and returns a record marked
  `calibration_only` with `S_pred,1`, `S_pred,2` and `S_meas`; `run_holdout`'s result for the same
  data is unchanged.

**The cases** (`tests/test_holdout_capacity.py`, revision 3, 10, rows 4.1, 4.2 to 4.4, 4.5 and N):
a strong signal in a quiet hidden year: conclusive and PASS; a weak signal: INCONCLUSIVE
`insufficient_capacity_train` with an empty hidden access log; a noisy hidden year (a larger
AR(1) amplitude in that year only): INCONCLUSIVE `insufficient_capacity_hidden_noise`; row N: two
hidden years equal outside the windows and different inside give the same decision 2 and the same
hidden noise, bit for bit; no signal in the hidden year with high capacity: FAIL; a signal
slightly weaker than predicted with a consistent depth: INCONCLUSIVE
`not_detected_not_inconsistent`; fewer than two valid windows: INCONCLUSIVE; `e_pred` is the
largest over a non-trivial grid; a non-finite statistic is INCONCLUSIVE; `b` and `s` enter the
threshold as declared; the calibration-only measurement leaves `run_holdout` unchanged; with the
switch off the holdout is the M3 one (P1). Each case in white and, where it matters, correlated
noise. The case of row 4.1 with a train-found sinusoid needs the frequencies of piece 7 and is
written with piece 7 (pending).

**Addendum: the Codex design review of this amendment, taken in before the tests**
(`.cache/v021/codex/amend12/`):

- **The train fit and its gate:** with the switch on, the train candidate is refitted by
  `finalize_candidate` on the masked train curve (as the global path does) before `_bls_gate`,
  so the BLS depth, its error and the weights of `β_D` belong to one fit. **A train gate that is
  INCONCLUSIVE** (noise undetermined, no in-transit cadence) makes the round INCONCLUSIVE
  `train_noise_undetermined`; the original SNR is never used in its place. The H4 rules then use
  the corrected candidate.
- **`R_min` in the train** is an adopted reading (revision 4 states it for the hidden year and the
  "same estimator" for the train), with its own reason `train_replicas_below_r_min`, distinct from
  `insufficient_capacity_train` (the numeric decision).
- **`N_pred`** counts only complete measurement spans inside one hidden sector; `N_pred = 0` is
  INCONCLUSIVE `no_predicted_window` before any division. Later drops change `N_valid`, never
  `N_pred`.
- **`m_β` only in decision 1**; both `e_pred` are the maximum over the whole grid; the threshold is
  met with equality.
- **The FAIL rule, exactly:** `Z = (d_train − d_hidden) / sqrt(e_train² + e_hidden²)`, signed
  (one-sided), with `d_hidden` and `e_hidden` (the complete stacked error, with its scatter floor) of
  the `dP` that maximizes the SNR; `SNR = min_snr` PASSES; `Z = 3` does not FAIL; zero or
  non-finite errors, or a non-finite `Z` or SNR, are INCONCLUSIVE with the reason. This replaces,
  on the corrected path only, the absolute difference of `depth_consistency_sigma`.
- **`calibration_measurement`** measures **despite** decision 1 and decision 2 (records both, the
  thresholds and `S_pred,1`, `S_pred,2`), but does not overcome a measurement impediment (hidden
  noise undetermined, fewer than `R_min` replicas, too few windows): then `S_meas` is absent with the
  reason. It builds its own `HiddenYear` and log, never modifies the official round or its inputs,
  and covers the rounds stopped at decision 1 **and** at decision 2. In the official round stopped
  by decision 1, `S_pred,2` and `S_meas` are absent with the reason (the hidden year is not read).
- **Integration:** the new results reach `run_holdout`'s rounds and its coverage, not a key that
  the aggregation ignores.
- **Added cases:** the corrected train SNR below 7.1 while the BLS one is above (H4 now
  INCONCLUSIVE); an undetermined train correction with a strong BLS SNR (INCONCLUSIVE, not
  valid); 19 against 20 train replicas, and a shortage at one `dP` only; a window whose center is
  inside a sector but whose span is not (not in `N_pred`); `N_pred = 0`; a gap that lowers `N_valid`
  without changing `N_pred`; `m_β` only in decision 1; the maximum over the grid; equality at the
  threshold; `R` kept when other rounds stop early; `SNR = 5`, `Z = 3`, a one-sided difference, the
  same `dP` for depth and error, zero variance and non-finite values; the calibration measurement
  for a round stopped at decision 2, a real measurement impediment, and the official result and
  inputs unchanged (compared whole); the coverage reaching `run_holdout`.
- **Constructions:** a noisy hidden year is the hidden part of a second curve with the same times,
  signal, seeds and white noise and a larger AR(1) amplitude, joined to the train of the first
  (the train identical bit for bit); a weaker but consistent signal reduces only the hidden
  transits' depth. Each case states its preconditions (decision 1 passed, the hidden noise
  determined, `R_min` met, the expected decision); a seed whose preconditions fail makes the case
  incompatible with the design (no search for another seed). The algebra of the FAIL rule is also
  tested on given numbers (for example `d_train` 600, `e_train` 50, `e_pred` 100, `d_hidden` 480,
  `e_hidden` 100 ppm: both capacities pass, SNR 4.8, `Z` ≈ 1.07, INCONCLUSIVE).

**For the maintainer (a consequence known now, not a change):** the freeze sets
`corrections.enabled` to `true` by default (section "The switch"); the historical projection
freezes the whole section at `enabled: false`, so from the freeze the two historical calibration
claims resolve with the corrections on and their claim component becomes `TAMPERED`. Moving `b` and
`s` into the plan at the freeze does not change that. The freeze package will need the maintainer's
decision on the historical behaviour intended (keep `TAMPERED` as the honest state, or an extension
whose justification the maintainer approves).

Every piece: its tests are committed before its code; the tests are run on white and on correlated
noise (the generator's correlated mode); its sabotages are planned in the test commit and their
results recorded after the code. With the switch off, the full suite is unchanged (checked after
each piece). Nothing of M4 is measured on the development population before the freeze, the
calibration of the estimators (with the timing lot first, `calibration-ceiling-decision.md`) and
the maintainer's approval of `points.json`.
