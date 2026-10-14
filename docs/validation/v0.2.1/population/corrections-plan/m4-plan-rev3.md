# Plan of corrections for M4 and M5, revision 3 (specification; no code)

Status: revision 3, written on 2026-10-14, the last complete revision planned. It replaces
`m4-plan-rev2.md` (SHA-256 `515fe33f352fe204213b0763d2e4d6094d21cd370e93ff5cdd104bc6c48cc468`,
kept unchanged as history) after the read-only review `codex-m4-plan-review-2.md`
(`9e65a2511660414bd51f8f7638c031bf8b00dd71e706a4a929f8f84bff531400`). Nothing in it is
implemented. The calibration sizes come from `calc/calibration_sizing.py` and its output
`calc/calibration-sizing-rev3.json` (exact binomial calculations; section 8).

Fixed by the maintainer and not changed here: C1 to C6 and their limits; the results of M0 to
M3 (FAILS); the frozen development manifest; at most two candidate versions (M4, M5); the
budget of generation sets of the development chain; `population/points.json` append only. The
directed mode (claimed ephemeris) is out of M4 and M5 (section 1.1 and Appendix A).
Implementation starts only after every blocking point below is closed and the maintainer
approves.

## 0. Closure table

Each row is a blocking point of the review of revision 2, plus its blindness note. The numeric
acceptance criteria are declared here, before any test or code (`ROADMAP.md:165-167`). "Unit"
is a synthetic unit test; "selection" is the examinable part of the calibration population;
"R4" and "R5" are its reserves (section 8). Conditions K, T, L and M are defined in 8.3.

| # | Blocking point (origin) | Solution (section) | Numeric acceptance criterion | Verified in | State |
|---|---|---|---|---|---|
| B1 | B2a needs the covariance of the baseline coefficients and a degeneracy rule (review 2, item 2.B1) | 4.1: line plus train-found sinusoids fitted by weighted least squares; window depth variance = var(mean in box) + g'Σg, with the A1 red term; conservative bound for band-window correlation; degeneracy rules, fallback order, window drop, too few windows INCONCLUSIVE; no shared cadences | K5, K6, K7, K8: per light curve, the stacked hidden depth pull; 95% two-sided Clopper-Pearson interval of the fraction within 1σ inside [0.60, 0.76], within 2σ inside [0.92, 0.98], fewer than n/2 pulls below −0.2 and above +0.2; n = 1000 per condition. Unit: degenerate design gives the declared fallback or drop | selection, R4 (R5 if M5 changes it); unit | closed |
| B2 | the train β transferred to the hidden year (review 2, item 2.B2) | 4.2: the hidden measurement uses σ_w, σ_r and β of the hidden year, from its own registered noise bands outside every window (declared input of decision 2); 4.3: decision 1 uses the train β with a declared margin, verified by the tail | K5–K8 (as B1) for the hidden measurement; T1a and T1b (B3) for the effect of decision 1 | selection, R4 | closed (the change of correlation between years in real data is a domain limit, declared in 4.2; it does not close or open this row) |
| B3 | the tail of the capacity rule (review 2, item 2.B3) | 4.6: α_H = 0.02 per target (20% of the C1 limit of 0.10), rule designed at 0.005 per target, Bonferroni over the planned rounds; b and s estimated on selection | T1a (planets without variability) and T1b (with variability): among targets with an injected constant signal and at least one round conclusive by decisions 1 and 2, the one-sided 95% upper Clopper-Pearson bound of the fraction with holdout FAIL ≤ 0.02; at least 725 conclusive targets each (power 0.988 at a true rate of 0.005; false pass 3e-6 at 0.04) | selection, R4 | closed |
| B4 | the `period_alias` statistic and the contradiction §5 / §9 (review 2, item 2.B4) | 5 (the only definition; sections 9 and 10 refer to it): weighted fits, operational statistics Z_F, f and G (not χ² nor BIC), thresholds chosen on selection by a declared rule from a declared grid | T2a and T2b: alias FAIL among real transits without and with variability, one-sided 95% upper bound ≤ 0.02 (n ≥ 725); L1: alias FAIL kept among dips made by variability, one-sided 95% lower bound ≥ 0.80 (n ≥ 200; power 0.990 at 0.90; false pass 4e-4 at 0.75) | selection (thresholds), R4 | closed |
| B5 | prewhitening can remove the transit before the search (review 2, item 2.B5) | 7: weighted generalized Lomb-Scargle on residuals of an asymmetric robust fit (points far below the model get zero weight); a frequency is removed only if its folded curve is well described by few harmonics; the same rule in every class, in the search, the reanalysis and the train | paired design on the same light curves, with and without prewhitening: T5, transits found without and lost with prewhitening, upper bound ≤ 0.02 (n ≥ 725); M1, median paired depth ratio, distribution-free 95% interval inside [0.95, 1.05]; T6w and T6r, null light curves passing the gate only with prewhitening, upper bound ≤ 0.01 per noise model (n ≥ 1450) | selection, R4; unit | closed |
| B6 | the calibration's estimand, unit and size (review 2, item 2.B6) | 8: estimand = the same operation on the noiseless twin of the light curve; unit = the light curve, one statistic per light curve and condition; sizes computed for the joint power of the 17 conditions of a reserve | joint power at least 0.80 under nominal behaviour (computed: 0.838); every K condition false pass ≤ 1e-4 at a true 2σ coverage of 0.90 (computed: 1e-5) | `calc/calibration-sizing-rev3.json` | closed |
| B7 | the revision cycle and the M5 rule (review 2, item 2.B7) | 9: budget of six configurations (M4 at most four, M5 at most two) in a declared order; the first configuration passing every selection condition is chosen; each reserve examined once; a closed list of four M5 candidates with triggers computed on selection before M4 is measured | the rule is mechanical: given the selection results, the configuration and the M5 candidate are determined; no threshold changes in M5 | selection records committed before R4 and before the M4 measurement | closed |
| B8 | M5 directed mode: holdout relevance and the mode × condition matrix (review 2, item 2.B8) | removed from M4 and M5 (1.1); proposed text kept as a pending item (Appendix A) | no section of this revision except Appendix A uses a claimed ephemeris (checkable by reading); M4 and M5 run with the harness v2 unchanged | this document | closed |
| N | blindness note of review 2: provenance of the hidden-year detrending; "outside the windows" | 1.3: declared provenance; decision 2 reads residuals of a detrending fitted with every window masked, only in noise bands whose segments have unmasked cadences; the phrase corrected, with its effect | unit: two hidden years equal outside the windows and different inside give the same decision 2 and the same hidden noise estimates (bit-equal) | unit | closed |

Every row is closed by a specification and a numeric criterion; none is closed as a declared
risk. A row reopens if its criterion fails in the reserve.

Other changes from revision 2: the predictions (section 6) use the result of
`dev1-c3-inconclusive.md` (version 2) with the declared sentence; Appendix B lists the smaller
corrections.

## 1. Scope and information contract

### 1.1 Scope

- M4 and M5 are measured in the general mode only, with the harness v2 unchanged (what the
  harness passes to the tool does not change). The directed mode is not concluded and not
  discarded: it is a separate pending item (Appendix A), outside this plan and its budget of two
  versions. `ROADMAP.md` is not edited now.
- Kept: C1 to C6 and their limits, the results of M0 to M3, the frozen development manifest,
  the limit of two versions, the budget of sets of the development chain, `points.json`
  append only.

### 1.2 What the tool receives

Exactly what it receives at M3: the light curve, the pixel data and auxiliary columns, the
sector metadata, the stellar parameters and, in condition (ii), the catalog rows. Never the
injected period, the true class, the expected SNR or any generation parameter. The harness
keeps passing the injected period to `build_result` for reporting and to its own identity
computation only (`population_v2.py:3369-3385`), unchanged.

### 1.3 The holdout's information contract

`run_holdout` keeps receiving the raw light curve, the sector metadata and the plan only
(`holdout.py:644-656`, `pipeline.py:213-214`).

| Step of a round | Reads | Never reads |
|---|---|---|
| train search, train timing, train prewhitening | the train years' flux | the hidden year's flux |
| windows, noise bands, decision 1 (4.3) | the train results and the hidden sectors' metadata (time spans, cadence) | any hidden flux |
| hidden-year detrending (`HiddenYear.__init__`, `holdout.py:99-116`) | the raw hidden flux of the whole year; the trend is fitted only on cadences outside the masked zones (every transit and control window, to its baseline gap); masked cadences enter only through the edge cases of `detrend.py:71-73` and `122-124` (a segment or sector without unmasked cadences) and the upper clip of each cadence | — |
| decision 2 (4.4): hidden noise σ_w, σ_r, β | residuals of that trend in the registered **noise bands** (4.2), only in segments that have unmasked cadences, so no in-window flux enters | flux inside any window |
| measurement (4.1) | registered windows and their baseline bands, through `HiddenYear` and its access log | anything outside registered windows, bands and noise bands |

**"Outside the windows" does not mean "no signal".** The windows are where the train-only model
predicts the transits. If the train candidate or its ephemeris is wrong, a real transit can fall
in a noise band or a baseline band. The effect is declared: the hidden noise is inflated, the
predicted capacity falls, and the round leans toward INCONCLUSIVE (never toward a false PASS).

### 1.4 Which curve each operation uses

| Operation | Curve |
|---|---|
| global search | L1 − S: detrended, minus the components accepted by the prewhitening rule (7) on the whole curve |
| `finalize_candidate`, `snr`, `odd_even`, `secondary_eclipse`, `plausibility`, per-event depths, transit times | L2 = L1 − S′, with S′ the same frequencies refitted with the candidate's transits masked |
| `period_alias` | L1 (not prewhitened), with its own long-window detrending, as today |
| pixel tests, `nearby_contamination`, `systematics`, `eb_catalog` | unchanged inputs |
| holdout train search and train timing | the same steps on the train data only (frequencies found on the train data) |
| holdout hidden windows | the baseline of 4.1, with the frequencies found on the train data |

## 2. A1: correlated noise estimated from the data

### 2.1 The estimate

- **Segments:** contiguous runs of cadences, split where consecutive cadences are more than
  `gap_split` cadences apart (orbit gaps, sector boundaries, dropped cadences) and at the edges
  of any mask in use (masked cadences are removed and split the run).
- **Binned rms (Pont, Zucker and Queloz 2006, MNRAS 373, 231):** for a scale of n cadences,
  each segment's residual flux is cut into consecutive non-overlapping bins of n cadences
  (incomplete bins dropped). Per sector: σ_w = robust per-cadence standard deviation; σ_n =
  robust standard deviation of the bin means; σ_r²(n) = max(0, σ_n² − σ_w²/n); β(n) =
  sqrt(1 + n σ_r²(n)/σ_w²).
- **Scales:** n_T = round(T14 / cadence) for depths and significance; n_τ = max(1,
  round(τ / cadence)) for timing (3).
- **Few bins:** a sector needs at least `B_min` bins at scale n. A sector with fewer is
  excluded from every measurement and decision that needs its noise at that scale (no borrowing,
  no white-noise fallback), and the report lists it. If no sector remains, the decision is
  INCONCLUSIVE ("noise model undetermined").

### 2.2 Propagation, per estimator

- **Per-event box depth** (`events.py:106-108`): var = σ_w² (1/n_in + 1/n_base) + σ_r²(n_in) +
  σ_r²(n_base). Ignoring the covariance between the event and its baseline is an upper bound when
  the noise autocorrelation is non-negative at every lag; that holds for both noise models of the
  population (white, and AR(1) with a positive coefficient) and is the declared assumption for any
  other noise; K1 and K2 check the consequence.
- **No shared cadences:** if two events' measurement spans (event plus baseline bands) share
  cadences, the later event is dropped and recorded; events are then disjoint and, separated by
  at least a period, treated as independent.
- **Stacked depth** (`events.py:142-151`): inverse-variance weights from the corrected
  per-event variances; the "white-propagated" error is 1/sqrt(Σ weights) with those corrected
  variances; the error stays max(that, scatter/sqrt(n)) when n ≥ 3.
- **Candidate depth error and SNR** (`search.py:189-224`): the BLS depth and epoch stay; the
  error is the stacked error above at the candidate's ephemeris on L2; the `snr` gate uses depth
  / that error; the BLS `depth_snr` is reported beside it.
- **Hidden-year measurement:** 4.1 and 4.2.

## 3. Timing with an ingress model (`ROADMAP.md:132-133`)

- **Template:** depth, T14 and τ of a trapezoid are fitted once to the folded L2 at the
  candidate's ephemeris (the global candidate; in a holdout round, the train candidate on the
  train data). Each transit's center is found by a chi-square scan of that fixed template over
  ±0.5 T14 in steps of 1 minute; a minimum on the edge of the scan is discarded; minimum coverage
  as today (`ephemeris.py:31-80`).
- **Error:** half the width of the region where chi-square is within 1 of its minimum,
  multiplied by β(n_τ) of the transit's sector, floored at half a cadence.
- **Ephemeris:** the weighted linear fit is unchanged (`ephemeris.py:118-141`), including the
  inflation by sqrt(reduced chi-square) and the integer reference epoch; predictions use the full
  covariance (`ephemeris.py:100-104`).
- **Reference, not part of the tool:** Carter, Yee, Eastman, Gaudi and Winn 2008
  (arXiv:0805.0238, DOI 10.1086/592321, eq. 43; uniform source, white noise, uniform sampling):
  σ_tc = Q⁻¹ T sqrt(θ/2), Q = sqrt(ΓT) δ/σ, θ = τ/T. Used by unit tests (10) and as a
  selection diagnostic for the M5 trigger M5-1 (9.4).
- **Acceptance:** K3 and K4 (extrapolated timing pull, 8.3).

## 4. Holdout

### 4.1 The hidden-window measurement (B2a with its covariance; row B1)

- **Baseline model of a window:** a straight line plus sine and cosine terms at the frequencies
  the prewhitening rule (7) accepted on the **train data** of the round (origin of the period:
  the train; never the hidden year). No model selection on hidden data. The fit uses the window's
  out-of-box cadences and its registered baseline bands, by weighted least squares with weights
  1/σ_w,hidden² (4.2).
- **Depth of a window:** d = mean over the box cadences of (baseline model − flux).
- **Variance of a window's depth:** var(d) = σ_w²/n_in + σ_r²(n_in) + g′Σg, where g is the mean
  of the design-matrix rows over the box cadences and Σ = β_b² (X′WX)⁻¹ is the covariance of the
  baseline coefficients, inflated by β_b = β(n_b) of the hidden year at the scale n_b of the
  shortest baseline band (4.2). The correlation between the baseline cadences and the box
  cadences is not estimated; the declared conservative bound is to ignore it, valid under a
  non-negative noise autocorrelation (2.2).
- **Degeneracy:** a fit needs at least 20 baseline cadences per parameter and a condition number
  of the column-scaled X′WX at most 1e6. Fallback order: drop the sinusoids in reverse order of
  their train amplitude; then the line becomes a constant; if the constant fails the cadence rule,
  the window is dropped with its reason recorded. Windows whose measurement spans share cadences:
  the later is dropped (2.2).
- **Stacking:** inverse-variance weights from var(d); error max(1/sqrt(Σ weights),
  scatter/sqrt(n)) when n ≥ 3; with fewer than `min_predicted_transits` = 2 valid windows the
  round is INCONCLUSIVE ("too few measurable windows").
- **Acceptance:** K5–K8.

### 4.2 Hidden-year noise (row B2)

- **Noise bands:** registered from metadata before any hidden read, at the train ephemeris'
  phases 0.25 and 0.75, half-width 2 T14 (train), minus any overlap with a transit or control
  window or its baseline bands; read only through a new logged `HiddenYear` accessor.
- From the residuals in the noise bands (only in segments with unmasked cadences, 1.3): σ_w,hidden,
  σ_r,hidden(n) and β_hidden(n) by the estimator of 2.1, at n_T and n_b. With fewer than `B_min`
  bins at n_T, decision 2 is INCONCLUSIVE ("hidden noise undetermined").
- **The measurement of 4.1 uses only these hidden-year values; it never uses the train β.**
- **Domain limit (declared, not a closure):** in this synthetic population the noise has the same
  model in every year, so no calibration here tests a change of correlation between years; for
  real data, the hidden measurement still uses the hidden year's own noise, and the remaining
  limit is the length of the noise bands.

### 4.3 Decision 1: capacity from the train only

- S_pred = d_c / e_pred, with d_c = d_train − k e_train (k = 1) and e_pred the error that 4.1
  would give, computed from metadata: the expected box and baseline cadences of every predicted
  window (spans and cadence), the design matrix of 4.1 on those times, σ_w,train and a
  conservative β_dec1 = m_β × (largest β(n_T) among the train sectors), with the declared margin
  m_β of the configuration (9.2).
- Conclusive only if S_pred ≥ min_snr − b + z(α_round) s (4.6); otherwise INCONCLUSIVE with
  reason `insufficient_capacity_train`.

### 4.4 Decision 2: capacity with the hidden-year noise

- Taken after decision 1 is conclusive and the windows are fixed. Recomputes e_pred with
  σ_w,hidden and β_hidden (4.2) instead of the train values; the same rule; otherwise INCONCLUSIVE
  with reason `insufficient_capacity_hidden_noise`.
- Both decisions are recorded separately (inputs, results, access log). Changing in-window
  hidden flux changes neither (unit test, row N).

### 4.5 The FAIL rule

A conclusive round FAILS only if (a) the stacked hidden SNR < min_snr (5.0, unchanged) and (b)
(d_train − d_hidden) / sqrt(e_train² + e_hidden²) > 3 (the hidden depth is inconsistent with, and
lower than, the train prediction). (a) without (b): INCONCLUSIVE (`not_detected_not_inconsistent`).
The disappearance test is kept: with high capacity and no signal, d_hidden ≈ 0 and (b) holds.

### 4.6 The tail of the capacity rule (row B3)

- **Budget:** α_H = 0.02 per target, a declared share (20%) of the C1 limit of 0.10, for holdout
  failures of real, constant signals.
- **Design:** the rule targets α_rule = α_H / 4 = 0.005 per target; a case with R planned rounds
  (its observing years, fixed before any outcome, never reduced afterwards) uses α_round =
  0.005 / R (Bonferroni, valid for dependent rounds).
- **b and s:** per noise model, estimated on the selection part from all rounds of injected
  constant signals with S_pred ≥ min_snr, as the median and 1.4826 × MAD of S_meas − S_pred. They
  are working parameters; their validity in the tail is **not** assumed: it is tested by T1.
- **Acceptance (T1a, T1b):** among targets with an injected constant signal and at least one round
  conclusive by decisions 1 and 2, the fraction whose holdout test FAILS has a one-sided 95% upper
  Clopper-Pearson bound ≤ 0.02, separately for planets without variability (T1a) and with
  variability (T1b), with at least 725 conclusive targets each (power 0.988 at a true rate of
  0.005).

## 5. `period_alias`: the only definition (row B4)

Sections 6, 9 and 10 refer to this section; no other section defines the test.

- **Models:** a constant; a Fourier series of H = 2 harmonics at the candidate period (`F`); the
  same plus the box (`F+box`). Weighted least squares, weights 1/σ_w² per sector (A1), on L1 with
  the test's own long-window detrending (`battery.py:591-595`).
- **Operational statistics (not χ², not BIC; named for what they compute):**
  - Z_F = (χ²_const − χ²_F) / β̄², with β̄ the median over sectors of β(n_T);
  - f = D_F / d_box, with D_F the mean of the `F` model over out-of-transit phases minus its mean
    over in-transit phases, and d_box the box depth of `F+box`;
  - G = (χ²_F − χ²_F+box) / β̄² − ln N, N the number of cadences.
- **Outcome:** FAIL (fatal) if Z_F ≥ z_F*, f ≥ f* and G < g*; INCONCLUSIVE if G < g* and not
  (Z_F ≥ z_F* and f ≥ f*); PASS if G ≥ g*. The warning for a known systematic period is kept.
- **Thresholds:** g* = 10 (the current `min_box_delta_bic`, now an operational threshold on G).
  (z_F*, f*) is chosen within each configuration on the selection part by this declared rule: the
  first pair, in the order (18.47, 0.5), (18.47, 0.7), (30, 0.5), (30, 0.7), (50, 0.5), (50, 0.7),
  for which T2a, T2b and L1 pass on the selection part; if none passes, the configuration fails
  selection. The thresholds are then fixed and verified once in the reserve.
- **Regimes (the unit tests of 10 follow from these, so §5 and §10 cannot disagree):** a dip that
  the `F` model explains (f ≥ f*, Z_F ≥ z_F*) and the box adds little (G < g*): FAIL; a significant
  variability that explains less than f* of the dip, box gain small: INCONCLUSIVE; a weak dip with
  no significant variability: INCONCLUSIVE; a strong box (G ≥ g*), with or without variability at
  the same period: PASS.
- **Acceptance:** T2a and T2b (real transits without and with variability: upper bound ≤ α_A =
  0.02, a second 20% share of the C1 limit); L1 (dips made by variability: lower bound ≥ 0.80).

## 6. Predictions for C1 to C6 at M4, against M3 (paired)

Provisional; the M4 record fixes the numbers before the measurement. A wrong prediction is
reported as found.

| Criterion | Prediction | How it could go the other way |
|---|---|---|
| C1, every band and noise | down; most in below and near, and in correlated noise | prewhitening exposes a planet that a test then refutes; a round that becomes conclusive FAILS |
| C2 white | uncertain: `variability_masked` is refuted today for the wrong reason; after prewhitening the eclipse may be found, but the mechanism has no secondary and may end SURVIVED or WEAKENED | — |
| C2 correlated | down (A1 lowers significance) | — |
| C3 measurable | not monotonic: the new INCONCLUSIVE paths (decisions 1 and 2, the FAIL rule, `period_alias`, undetermined noise) push it up; timing and prewhitening can push it down | a fall does not mean the new paths are unused |
| C3 white, planets | see below | — |
| C4 | not monotonic and the largest risk: the 654 refuted no-transit cases with `period_alias` among their failures can move to INCONCLUSIVE or, if every other test passes, to SURVIVED or WEAKENED; A1 can remove `odd_even` or `secondary_eclipse` FAILs (`gauntlet.py:81-97,121-144`) | prewhitening removes the variability that made those candidates |
| C5 | 0 if `eb_catalog` and the own-TIC rule stay; new candidates can change catalog matches | — |
| C6 | 0 | new fits produce non-finite values or types outside the contract (checked by contract tests) |

**C3 white, planets.** At M3, 61 of 250 white measurable planets are INCONCLUSIVE; the maximum
for the 95% upper Clopper-Pearson bound to stay at 0.20 or below is 39 of 250. 57 of the 61 are
`two_years` and `few_train`, INCONCLUSIVE by the timing rule. `dev1-c3-inconclusive.md` (version
2) finds 21 of the 57 with a round below one duration by the Carter approximation with train
numbers (38 with the true parameters, which the tool cannot have); 61 − 21 = 40 is a conditional
sensitivity, not a limit. **The approximation places C3 near the approval threshold. There is a
relevant risk that the result remains FAILS; the probability of approval has not been estimated
yet.** The criterion and `max_timing_sigma_durations` do not change.

Attribution: M3 to M4 compares a package; the per-correction evidence comes from the unit tests
(10) and the calibration (8), not from extra development measurements.

## 7. Prewhitening that protects the transit in the search (row B5)

- **Rule, the same for every light curve and class (no class or truth argument):**
  1. Residual flux r = L1 − 1, weights 1/σ_w² per sector (A1).
  2. Periodogram: the generalized (floating-mean) Lomb-Scargle of `astropy.timeseries.LombScargle`
     with those weights, on the frequency grid of its `autofrequency` with 10 samples per peak,
     limited to [1/(half the longest segment), 1/(2 h)].
  3. Candidate frequency = the highest peak. **Asymmetric robust fit:** its sinusoid (fundamental
     plus one harmonic) is fitted by iteratively reweighted least squares in which any cadence
     more than k_clip σ_w **below** the current model gets zero weight (dips are protected; points
     above are kept), up to 10 iterations or until the set of zero-weight cadences no longer
     changes.
  4. **Acceptance of the frequency:** (a) its false-alarm probability, computed by
     `LombScargle.false_alarm_probability` (method `baluev`) on the clipped residuals, is below
     `fap_max`; and (b) **few-harmonic test:** folded at that period in 50 phase bins, the
     two-harmonic model explains at least `h_min` of the variance of the binned means (a box dip
     of short duty cycle needs many harmonics and fails this test).
  5. If accepted, subtract it and repeat from 2, up to `max_components`; amplitudes and phases are
     fitted per sector (frequencies common).
- **Where:** the global search (L1 − S), the reanalysis (L2 = L1 − S′, refit with the candidate
  masked) and the holdout train; the hidden windows use the train frequencies (4.1).
  `period_alias` uses L1 (5).
- **Validity of the false-alarm probability under correlated noise is not assumed;** T6w and T6r
  test the consequence.
- **Acceptance (paired design, the same light curves with and without prewhitening):** T5
  (transits without variability found without prewhitening and lost with it: upper bound ≤ δ =
  0.02, a third 20% share of the C1 limit); M1 (median of the paired depth ratio, with/without, of
  the transits found in both: distribution-free 95% interval inside [0.95, 1.05]); T6w and T6r
  (null light curves whose strongest candidate passes the gate only with prewhitening: upper bound
  ≤ 0.01 per noise model).

## 8. The calibration population (row B6)

### 8.1 Identity, parts and reserves

- The development structure (`population_cases("confirm:<prefix>")`, `population_v2.py:282-321`)
  under calibration prefixes, generated by the harness v2 unchanged as **diagnostic** campaigns
  (outside `population/campaigns/`), restricted by a declared case list to the groups of 8.4.
  Replicas: `<part prefix>-r01`, `-r02`, … Never the development or the confirmation prefix.
- **Selection** (examinable): prefix `refute-v0.2.1-calibration-selection`.
- **Reserve R4:** prefix `refute-v0.2.1-calibration-r4-<C4>`, where `<C4>` is the full SHA-256 of
  the commit that freezes the M4 configuration (9.3). **Reserve R5:** prefix
  `refute-v0.2.1-calibration-r5-<C5>`, `<C5>` the commit that freezes the M5 configuration.
- **How the reserves stay unseen, and the evidence:** their seeds depend on the freeze commit,
  which does not exist before the freeze, so no reserve case can be generated or analyzed earlier;
  the freeze commit precedes, in git, the reserve's diagnostic declarations, and the reserve's
  journals start after it; the reserve's results are recorded once, with the SHA-256 of the
  configuration file and of the code commit. After its single examination, a reserve becomes
  selection data.
- One generation per case (K = 1): these are diagnostics, never campaign evidence; each case's
  noiseless twin (8.2) reproduces the case's bytes when its regenerated noise is added back, which
  checks the generation.

### 8.2 Estimands and unit

- **Noiseless twin:** for the planets and null light curves used here (no blends) the generator
  writes flux = model + noise (`population_v2.py:855-864`); the twin is the model alone, from the
  case's recorded final parameters. The calibration driver checks, per case, that twin plus the
  regenerated noise reproduces the case's flux bit for bit.
- **Estimand of each operation:** the value the same operation, with the same windows, masks and
  weights as on the noisy curve, measures on the twin. Pull = (noisy value − twin value) / the
  operation's error.
- **Bias against the injected value** (reported apart, with declared tolerances: depth,
  |median relative bias| ≤ 0.05; timing, |median bias| ≤ 0.2 σ): a selection condition of each
  configuration (a configuration whose bias exceeds a tolerance fails selection); in the reserves,
  reported.
- **Unit:** the light curve; one statistic per light curve per condition; events or rounds of the
  same light curve never count as independent trials. Where a light curve has several rounds, the
  condition names which one (8.3).
- **Two kinds of evaluation:** E1, operations at the injected ephemeris (the K conditions); E2,
  the full tool on the noisy curve (the T, L and M conditions, and reported E2 pulls of the
  candidates with signal identity).
- The calibration driver is a new script (not part of `src/`, not the harness), committed with its
  SHA-256 before it is first used; it uses the candidate code's functions and the harness's
  generator and serialization.

### 8.3 The 17 conditions of a reserve (the same conditions on the selection part)

K conditions: the 95% two-sided Clopper-Pearson interval of the fraction of |pull| ≤ 1 inside
[0.60, 0.76], of |pull| ≤ 2 inside [0.92, 0.98], and fewer than n/2 pulls below −0.2 and fewer than
n/2 above +0.2.

| Id | Statistic (one per light curve) | Group | n | Power | False pass |
|---|---|---|---|---|---|
| K1, K2 | E1 candidate stacked depth at the injected ephemeris, on L2 (white; correlated) | planets without variability, near and measurable | 1000 each | 0.990 | 1e-5 at a true 2σ coverage of 0.90 |
| K3, K4 | E1 predicted mid-time of the first transit of the last observing year from the train ephemeris of the other years (white; correlated) | same | 1000 each | 0.990 | same |
| K5, K6 | E1 stacked hidden depth (4.1, 4.2) in the last observing year (white; correlated) | same | 1000 each | 0.990 | same |
| K7, K8 | E1 stacked hidden depth in the last observing year with variability (white; correlated) | planets with variability (`variability_some_years`), near and measurable | 1000 each | 0.990 | same |
| T1a, T1b | holdout FAIL among targets with ≥ 1 conclusive round; upper bound ≤ 0.02 | planets without / with variability, all near and measurable, both noise models | ≥ 725 conclusive each | 0.988 at 0.005 | 3e-6 at 0.04 |
| T2a, T2b | `period_alias` FAIL with the candidate at the injected signal; upper bound ≤ 0.02 | planets without / with variability whose candidate has signal identity | ≥ 725 each | 0.988 at 0.005 | 3e-6 at 0.04 |
| T5 | transit found without prewhitening and lost with it; upper bound ≤ 0.02 | planets without variability found without prewhitening | ≥ 725 | 0.988 at 0.005 | 3e-6 at 0.04 |
| T6w, T6r | null light curve passing the gate only with prewhitening; upper bound ≤ 0.01 | null, white; null, correlated | 1450 each | 0.988 at 0.0025 | 4e-6 at 0.02 |
| L1 | `period_alias` FAIL kept on a dip made by variability: the candidate without prewhitening at the variability period (or twice or half), lower bound ≥ 0.80 | null with variability (`trend_variability`), both noise models | ≥ 200 | 0.990 at 0.90 | 4e-4 at 0.75 |
| M1 | median of the paired depth ratio (with / without prewhitening); distribution-free 95% interval inside [0.95, 1.05] | planets without variability found in both | ≥ 50 (all available are used) | 0.999 (ratio spread 0.05 assumed) | 6e-4 at a median of 0.94 |

Joint power of the 17 conditions under nominal behaviour, by an independence approximation:
**0.838** (target 0.80; each condition sized for at least 0.80^(1/17) = 0.987). Maintainer's
checks reproduced by the script: with n = 90 or 120 no count passes the 2σ condition; at a nominal
coverage of 0.9545 a cell passes with probability 0.826 (n = 530), 0.911 (650), 0.990 (1000); at a
true coverage of 0.90, below 0.001 for n ≥ 300; eight independent cells at 0.91 pass together with
probability 0.470.

### 8.4 Size of each part and cost

- Per part: planets without variability, near and measurable, 1000 per noise model (3 replicas of
  the development structure: 400 per noise model and replica); planets with variability, near and
  measurable, 1000 per noise model (10 replicas: 100 each); null 1450 per noise model (white from 1
  replica, correlated from 3). **6900 light curves per part**, 20700 for the three parts.
- **T1 enlargement rule (declared):** T1a and T1b need 725 conclusive targets each, a conclusive
  fraction of at least 0.3625 of 2000. With the conclusive fraction f measured on the selection
  part for the configuration under test, each reserve's group is N = max(1000, ceil(725 /
  (1.8 f))) per noise model; if N > 3000, the configuration fails selection (too few testable rounds
  to verify the tail). The selection part is enlarged by further selection replicas under the same
  rule when needed.
- **Cost** (12 s per light curve per worker, 24 workers, ideal division; add about 20% for the lot
  overhead seen in campaign 1): one evaluation of one configuration on one part 0.96 h + 0.68 h for
  the paired runs without prewhitening = **1.64 h**; generation of a part 0.12 h. Selection, worst
  case of six configurations: 9.8 h; R4 once 1.76 h; R5 once 1.76 h. **About 13.4 h of machine time
  in all, about 16 h with the overhead.**

## 9. Configurations, reserves and M5 (row B7)

### 9.1 Budget and order

Six configurations in all: M4 at most four (9.2), M5 at most two (9.4). The initial configuration
counts. Every configuration and every result is preserved.

### 9.2 M4 configurations, in this order

Estimator settings only; the decision thresholds (min_snr 7.1 and 5.0, `max_timing_sigma_durations`
1, k = 1, α_H, α_A, δ, the FAIL rule's 3, g* = 10) are the same in all.

| Config | B_min | gap_split | fap_max | max_components | k_clip | h_min | m_β |
|---|---|---|---|---|---|---|---|
| M4-c1 | 20 | 5 | 1e-4 | 3 | 2.5 | 0.90 | 1.2 |
| M4-c2 | 20 | 5 | 1e-5 | 3 | 2.5 | 0.90 | 1.2 |
| M4-c3 | 40 | 3 | 1e-4 | 3 | 2.5 | 0.90 | 1.2 |
| M4-c4 | 20 | 5 | 1e-4 | 2 | 2.0 | 0.95 | 1.5 |

Within each configuration, b and s (4.6) and (z_F*, f*) (5) are set on the selection part by their
declared rules.

### 9.3 Choice, freeze and R4

- The M4 configuration is the first in the order above that passes all 17 conditions and the bias
  tolerances on the selection part. If none passes: M4 is not built; record and stop for a scope
  decision.
- Freeze: one commit with the configuration file, the code, the selection results and the values
  of the M5 triggers (9.4); then R4 is generated (its prefix carries that commit) and examined once.
- If the configuration fails R4: M4 is not measured with it; record and stop for a scope decision.
- If it passes R4: M4 is appended to `points.json` and measured (11).

### 9.4 M5: a closed list of candidates

M5 exists only if M4 is not approved on the development population, and only as one candidate of
this list, each a correction of an estimator or model (never a threshold), each with a trigger
computed **on the selection part at the M4 freeze** (before M4 is measured, so the M4 development
numbers cannot choose it):

| Candidate | Principle | Trigger (selection, M4 configuration) | Validation |
|---|---|---|---|
| M5-1 joint train ephemeris: period and epoch fitted directly by the trapezoid model to all train data, replacing the linear fit of individual times | uses every in-transit cadence at once; no per-transit discards | median ratio of the train timing uncertainty propagated to the hidden year to the Carter-based reference (3), white noise, planets without variability, > 1.5 | all 17 conditions on selection, then R5 |
| M5-2 parametric correlated noise: an AR(1)-plus-white likelihood per segment replacing the binned rms | uses all lags; less variance than one bin scale | in correlated noise, median relative spread (1.4826 MAD / median) of β(n_T) across the sectors of one light curve > 0.3, or more than 10% of sectors excluded by the few-bins rule | same |
| M5-3 flexible hidden-window baseline: Legendre polynomial of order chosen by a declared information criterion on the baseline bands only, replacing the line plus train sinusoids | variability whose frequency or amplitude changes between years | in variability cases, more than 10% of hidden windows dropped as degenerate, or the conclusive fraction below half of that without variability | same |
| M5-4 quasi-periodic variability in the prewhitening: each accepted frequency with its harmonics and per-orbit amplitudes | variability that is not a stable sinusoid | after prewhitening, a periodogram peak at an accepted frequency with false-alarm probability below `fap_max` remains in more than 10% of the variability light curves | same |

- **Rule:** if M4 is not approved, M5 is the first candidate, in this order, whose trigger fired; if
  none fired, publish and pause. This holds also when M4 fails only by C3, only by C4, or by both:
  no decision threshold changes (min_snr, `max_timing_sigma_durations`, z, k, the alias thresholds,
  the 7.1 gate); without a triggered candidate, publish and pause.
- M5 uses at most two configurations (the candidate's default settings, then one declared variant),
  evaluated on the selection part (which by then includes R4) with all 17 conditions; then its
  freeze, R5 examined once; if it fails R5, M5 is not measured (record and stop).
- M5 must fit the limit of two versions and the budget of sets of the development chain.
- A correction outside this list: stop for a scope decision of the maintainer.

## 10. Unit-test acceptance criteria (declared before the tests and the code)

Synthetic cases, no network, each in white and correlated noise. The `period_alias` cases follow
the regimes of section 5.

| Correction | Must pass | Must fail or stay INCONCLUSIVE | Regression |
|---|---|---|---|
| A1 | white noise: β(n_T) within 1 ± 0.1 and the gate unchanged within 5%; AR(1) of known parameters: β within 15% of its analytic value; bins never cross a gap or a mask | a sector below `B_min` bins is excluded and reported; none left: INCONCLUSIVE | the suite green; the M0 baseline tests unchanged |
| timing (3) | trapezoid with ingress, white noise: per-transit error within 30% of the Carter reference; pulls of 200 seeded transits within the K margins | a scan minimum on the edge is discarded | same input, same times |
| 4.1 | line plus train sinusoids fitted; var(d) includes g′Σg; a transit plus a train-found sinusoid: the round does not FAIL | a degenerate design: the declared fallback, then the drop with reason; fewer than 2 valid windows: INCONCLUSIVE | windows sharing cadences: the later dropped |
| 4.2–4.4 | strong signal, quiet hidden year: conclusive | weak signal: `insufficient_capacity_train` with an empty hidden access log; noisy hidden year: `insufficient_capacity_hidden_noise` | row N: equal outside the windows and different inside, the same decision 2 and the same hidden noise, bit-equal |
| 4.5 | no signal in the hidden year, high capacity: FAIL | a signal slightly weaker than predicted, consistent depth: INCONCLUSIVE | — |
| 5 | the four regimes of section 5, one case each | — | the systematic-period warning kept |
| 7 | a transit under a stronger sinusoid: the transit period found; a pure sinusoid: removed, no spurious candidate passing the gate | a pure box transit: not removed by the prewhitening (few-harmonic test and asymmetric fit) | the function has no class or truth argument (signature); `period_alias` receives L1 |

## 11. Measuring M4 (and M5) on the development population

- **Campaign 1 cannot take a new point with the harness v2:** with its records folder,
  `orchestrate` finds records 3 without the new point and writes a lock (`population_v2.py:4152-4168`);
  with another records folder, asking for M3 too is refused before any analysis
  (`population_v2.py:4134-4151`), and asking for the new point alone would analyze it, but `metrics`
  reconciles one records folder per run (`population_v2.py:4499-4572`), so M3 to M4 could not be
  paired in one reconciled report; the campaign declaration lists M0 to M3, but `mode_analyze` does
  not check that list (`population_v2.py:3663-3677`).
- **Each version in a new campaign of the development chain, with the harness v2 unchanged:**
  campaign 2 with M3 and M4; campaign 3, only if M5 is measured, with M4 and M5. Each has its own
  declaration (predecessor with its SHA-256, sets consumed before it as counted by the chain,
  `population_v2.py:2067-2082`), generates and accepts its own set (its manifest is another file,
  `population_v2.py:3189-3208`, with every case's bytes equal to manifest B), and consumes budget for
  every set it starts, also an interrupted or divergent one.
- The new point is appended to `points.json`, with the maintainer's approval, and committed before
  its measurement; a dated record with the changes, the calibration results, the predictions of
  section 6 with numbers, and the risks is committed before the measurement.
- Prerequisites: the machine qualification stays valid while the machine does not change; the D6
  report stays formally valid while `d6.py`, the harness and the profiles do not change, but D6
  covers only M0 and M3 and its matrix and says nothing about the determinism of the new operations;
  the two slots of every lot remain the check of run-to-run equality.
- Stop at the first version approved on every criterion; if neither is: publish and pause; a failed
  version is never confirmed.

## 12. The v0.2 claim

Not affected. It is never re-locked or re-run (`ROADMAP.md:157`); its verdict is verified at its
locked commit `cc9d104`, the existing tag `v0.2.0-calibration-lock` (`ROADMAP.md:88-89`). The
corrections change this branch's code hash (where its `verify` is already TAMPERED, as recorded since
H7); no file under `calibration/` changes; a result of the corrected code never replaces or
reinterprets the v0.2 result.

## 13. Cost

Definitions: process wall time (measured by the driver that starts a process), journal time
(`started` to `closed`), internal time (recorded by the harness).

| Item | Machine time |
|---|---|
| calibration (section 8.4), worst case | about 13.4 h, about 16 h with the lot overhead |
| a development campaign with two points (campaign 1 rates: set 0.28 h, regeneration 0.18 h, 2 × (1.75 + 0.35) h, metrics about 0.1 h) | about 4.7 h, plus the extra cost of the new methods (not measured yet) |
| M5, if measured | the calibration of its two configurations and R5 (part of the 16 h above) plus about 4.7 h |
| confirmation (the chosen version, one point, two slots) | about 2.6 h, plus the new methods, plus the wait for the drand round |

The campaign 1 values behind these figures: one generation 335.3, 316.0 and 343.5 s (process
wall), about 331.1, 311.5 and 338.7 s (journal) and 328.0, 308.4 and 335.5 s (internal); one point,
one slot 3082 to 3185 s (journal, summed over 52 lots); 12.0 to 12.4 s per case and worker
(internal).

## Appendix A. The directed mode: a pending item (proposed text, not part of M4 or M5)

Not concluded and not discarded; to be planned on its own, after M4 and M5, with its own versions
and budget.

- **Information contract of its own:** the tool receives, besides the general-mode inputs, a claim
  (period, epoch, duration and their uncertainties). The directed mode is a separate condition with
  separate metrics; the general mode is always measured beside it, so a change of input never
  mixes with a change of code.
- **Claims for every case:** planets and false positives get the catalogued (injected) ephemeris
  with a perturbation; no-transit cases get a false claim drawn by a declared deterministic rule
  from the joint distribution (period, epoch, duration, and the covariance of period and epoch) of
  the claims of the other classes, with the same perturbation model; receiving a claim then reveals
  nothing about the class.
- **Perturbation from an authoritative, dated source:** the distribution of period and epoch
  uncertainties (and their covariance) from a catalog of claimed signals (for example the TOI
  catalog at ExoFOP or the NASA Exoplanet Archive), with URL, version and retrieval date recorded
  and the extracted values committed; aliased claims only if the same source gives their rate.
- **Holdout relevance:** the holdout stays blind (no claim). Its result counts for the directed
  verdict only if the round's train candidate matches the claim within a declared tolerance,
  checked **after** the blind decisions and never used to choose anything; otherwise the holdout is
  reported as "examined another signal" and does not enter the directed verdict, which is then
  INCONCLUSIVE for the holdout component. The matrix mode (general, directed) × catalog condition
  (i, ii) is declared with one metrics report per cell.
- **Requirements:** a new harness version (it passes the claim), its self-test and an independent
  review, a D6 rerun with it, an amendment defining the claim inputs, and `points.json` appended
  before any directed measurement.

## Appendix B. Smaller corrections from revision 2

- §1.2 of revision 2 said the hidden noise is read "where the transit cannot be"; corrected in 1.3.
- §11.2 of revision 2 said "harness v2 unchanged" also for a campaign 3 with a directed M5;
  coherent now that M5 is general mode only (1.1, 11).
- The C3 white prediction now uses the declared sentence (section 6) and the version 2 of the
  investigation, with its approximations stated there.
- The few-bins rule no longer borrows the largest β of another sector (an approximation, not a
  bound): the sector is excluded (2.1).
- B2a no longer uses the train β for the hidden measurement (4.1, 4.2).
- The holdout tail condition is split by variability (T1a, T1b), since the campaign 1 holdout
  failures with the right signal concentrated in the variability family.
