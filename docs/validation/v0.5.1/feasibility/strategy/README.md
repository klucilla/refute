# v0.5.1: the analysis before the strategic decision (item 3 of the maintainer's decision of 2026-11-08, #208)

Development data and development seeds only; no acceptance or confirmation seed was drawn for this
analysis, and nothing in `src/` changed. It reads the recorded result of A0's second run
(`../../acceptance/a0r2-result.json`). **It decides nothing.** `method_status: not_validated`.
Processor-hours: 3.91 (approved: 10). Development total after it: about 157.8 of 200 (warning at 160).

Outputs next to this file: `strata.json`, `forecast-rule.json`, `pools.json`, `real-sectors.json`,
`diagnose-matched.json`, `diagnose-matched_nomask.json`, `diagnose-dispersion.json`; each script's
docstring states its construction and its command.

## (a) What the acceptance's rule leaves decisive

The rule (acceptance, section A0): a pull row failing in a stratum makes that stratum's errors not
accepted; a decisive test relying on them is INCONCLUSIVE, never decisive on an uncalibrated error.
At run time the code knows the coverage stratum and the sector count, not the noise model, so a
run-time cell counts as accepted only if it holds under all five noise models (`strata.py`). Three
readings are reported: `strict` (no row of the cell FAIL or NOT DECIDABLE), `ignoring_nd` (no row
FAIL), `white_only` (no row FAIL, supposing the noise known and white).

| Error of | Used by | Cells accepted (strict / ignoring_nd / white_only) | Which, under strict |
|---|---|---|---|
| per-event | `single_event`, `event_consistency` (diagnostic until WP2 is accepted) | 0 / 0 / 2 of 3 | none |
| `matched_diff` | `odd_even` (fatal) | 0 / 3 / 3 of 9 | none; the 3 of the other two readings are the minimal-coverage cells, where every row is NOT DECIDABLE, so they hold nothing |
| `large_minus_core` | `aperture_depth` (fatal) | 3 / 3 / 7 of 9 | full with 3 sectors; partial with 2 or 4 |
| `sap_minus_expected` | `systematics` (warning) | 5 / 5 / 7 of 9 | full with 3; minimal with 2 or 4; partial with 2 or 4 |

**Real data.** A0's group rows are calibrated for 2, 3 and 4 sectors. Of v0.5's real stars, 46 of
the 100 C2 stars have 5 or more light-curve files, and 16 of the 22 C3 targets 5 or more sectors
(`real-sectors.json`): outside those cells, whatever their results. So on real data: `odd_even` is
decisive nowhere; `aperture_depth` and `systematics` only on the accepted cells above and only for
stars with 2 to 4 sectors. The tests that do not rely on A0 are unaffected by this rule: `snr`,
`secondary_eclipse`, `plausibility`, `nearby_contamination`, `period_alias`, `eb_catalog`,
`edge_events`, `duty_cycle` (`sinusoid`: its WP3 (b) acceptance failed, see #208).

## (b) Development forecast of D2, D4 and T2a

**Labelled "development forecast"; it decides nothing.** 100 development C1 planets (91 eligible;
67 in the D4 subset; every group stratum `full`; 36, 29 and 26 with 2, 3 and 4 sectors). The chain
ran once per curve; each reading was applied afterwards. The v0.4 compatibility battery keeps 0.967,
so D2 needs at least 0.867.

| Reading | D2: kept | D2: REFUTED | D4: INCONCLUSIVE (limit 0.30) |
|---|---|---|---|
| as built, the rule not applied | 0.879 | 0.033 | 0.030 |
| `strict` | **0.000** | 0.000 | **1.000** |
| `ignoring_nd` | 0.000 | 0.000 | 1.000 |
| `white_only` | 0.000 | 0.000 | 1.000 |
| the three A0 tests left outside the verdict (not the acceptance's reading) | 0.945 | 0.000 | 0.015 |

With the rule, `odd_even` is INCONCLUSIVE on every eligible curve. In the aggregation
(`core/verdict.py`) a fatal FAIL of another test comes first and gives REFUTED; otherwise an
INCONCLUSIVE decisive test gives INCONCLUSIVE. Neither is kept. **T2a** is therefore 0.000 under
`strict`, whatever the curves are. The v0.5 C2 curves are not cached, so no other reading is measured
there: of the 615 recovered injections in the local records (the v0.5 report's denominator is 637:
the local file has 97 of the originals), the fraction with no decisive test outside A0 failing
fatally or undecided at v0.5's statuses is 0.836, an upper bound, against about 0.897 needed. The
v0.5 statuses are not version 3's.

Hence, under the strict reading, the new battery's kept fraction is zero regardless of the data.
Consequently, **D2's kept requirement and T2a fail whenever their paired v0.4 kept fraction exceeds
0.10**, as it does in the recorded development references (0.967 and about 0.997); this condition
has not been measured on the confirmation data. **D4 depends on the data**, because a fatal FAIL takes precedence
and REFUTED does not count in D4's numerator; the development forecast above gives 1.000 and no
REFUTED, which is a forecast only. D1 (`SURVIVED / eligible`) would be met vacuously, since no curve
is SURVIVED when `odd_even` is INCONCLUSIVE: that would not demonstrate that binaries are rejected,
and the INCONCLUSIVE outcomes stay outside its numerator.

## (c) The real pools

From the frozen v0.5 inputs and its selection record (`pools.py`; the catalogs have grown since; a
new confirmation rebuilds them, which is a stop). A confirmation of the v0.5 design needs 8 stars
and 3 reserves per pool.

| Pool | v0.5 size | Walked in v0.5 (accepted) | Acceptance rate | Never walked | Walk per confirmation | Confirmations sustained |
|---|---|---|---|---|---|---|
| Planets | 952 | 51 (11) | 0.216 | 901 | 51 | 17 |
| Eclipsing-binary false positives | 63 | 41 (11) | 0.268 | **22** | 41 | **0** (about 5.9 acceptances expected, 11 needed) |

Counting only the 11 accepted stars as used, the false-positive pool leaves 52, which sustains 1. The
30 rejected stars fell on fixed rules (for example 10 "fewer than 3 sectors", 11 `logg`). The TESS-EB
edition is static, so the false-positive pool can grow only through new TOI dispositions of stars it
already holds, or through stars gaining sectors. **The false-positive pool is the scarce resource:
about one confirmation at the observed yield, under the stated exclusions** (new sectors or changed
dispositions could raise it; the yield is an estimate from one walk).

## (d) The diagnosis of the two failures

### The bias of the matched estimators (+0.6 to +0.9)

The hypothesis of 2026-11-08 was a positivity bound on the trapezoid's depth, whose mean on a
half-normal is `sqrt(2/pi) = 0.80` standard deviations. `battery_v51._fit_shape_status` does bound the
depth at 0 (`src/refute/packs/tess/battery_v51.py:258`). 300 transit-free curves per noise model, the
fit replaced inside the process (`diagnose.py`, task `matched`, `current` the battery as built).
Mean pull of the odd plus even sum (each group's pull, summed, over sqrt 2):

| Noise | depth at the lower bound | `current` | no lower bound | `fixed_shape` (no fit) | `shift_only` | `shape_only` |
|---|---|---|---|---|---|---|
| white | 1.3 % | 1.18 | 0.13 | 0.01 | 0.55 | 0.78 |
| correlated | 0.0 % | 0.97 | -0.05 | -0.14 | 0.33 | 0.45 |
| long | 0.7 % | 0.85 | -0.11 | -0.06 | 0.26 | 0.49 |

The per-group odd pull mean is 0.85, 0.71 and 0.55 (the recorded band +0.59 to +0.89).

**Reading.** The hypothesis as stated does not hold: a half-normal needs the estimate at the bound
about half the time, and the fit is at it about 1 % of the time, because the fit searches a free
epoch shift (0.3 of a duration), duration (0.3 to 3 times) and ingress for the largest positive depth
on the same data the depths are then measured on. The bound matters only as the sign of that search:
with a free sign the search is symmetric and the mean vanishes (at the price of a larger scatter), and
with no search (`fixed_shape`) the mean vanishes too. The cause is **the selection of the shape on the
same data**, a look-elsewhere effect (Gross and Vitells 2010), with the shift and the shape
contributing roughly additively. The odd-minus-even difference is unbiased in every variant (absolute
mean at most 0.09), and the two groups are measured with the same selected shape, so the mean bias
does not by itself move `odd_even`'s decisive statistic.

**The decisive statistic fails on its scatter, which the shape does not explain.** `matched_diff`
pull standard deviations, `current` and `fixed_shape`: 1.09 and 1.12 (white), 1.41 and 1.47
(correlated), 1.55 and 1.60 (long). Without the candidate's mask in the detrending (task
`matched_nomask`, same curves): 0.85 and 0.81, 0.95 and 0.99, 1.11 and 1.05 (next section).

### The dispersion of the box statistics (1.10 to 1.21)

The hypothesis was that `n_eff`'s lag window (up to 5) is short for those correlations. Task
`dispersion`, 300 curves per noise model and coverage:

| Noise / coverage | per-event pull sd: base | lag 10 | lag 20 | no mask | `box_diff` sd: base | no mask | median `n_eff` (base, lag 10, lag 20) |
|---|---|---|---|---|---|---|---|
| correlated / full | 1.116 | 1.112 | 1.117 | **1.030** | 1.144 | 1.053 | 31, 23, 15 |
| correlated / partial | 1.105 | 1.095 | 1.098 | **1.045** | 1.082 | 1.027 | 31, 24, 15 |
| correlated_trend / full | 1.095 | 1.086 | 1.085 | **1.005** | 1.059 | 0.962 | 31, 24, 15 |
| long / full | 1.106 | 1.101 | 1.093 | **1.010** | 1.052 | 0.985 | 31, 23, 15 |
| long / partial | 1.106 | 1.097 | 1.087 | **1.030** | 1.091 | 1.033 | 32, 24, 15 |
| white / full | 1.032 | 1.031 | 1.026 | 0.969 | 1.030 | 0.980 | 34, 26, 16 |

**Reading.** In these simulations and correlation models the lag window is not the cause: at lags
10 and 20 the pull standard deviations do not move (the standard error is about 0.02 to 0.04). Grid windows are 0.4 d apart, far beyond a 1-hour
time scale, and even at 0.5 d the correlation is small by lag 5. The finite number of pseudo-windows
explains little (Student's t with the median `n_eff` of about 31 gives 1.034; the standard deviation
of the values over the root mean square of the errors is 1.06 to 1.08, so the scale itself is off).

**The leading explanation is the mask; the diagnostic supports it but does not isolate it.** In the
pipeline the real windows are masked out of the detrending (the filter interpolates across them),
but the pseudo-windows that give their error are not (the filter sees them and may absorb part of
their noise). In correlated noise the pseudo-windows would then be quieter than a real window. Run
without the mask, the standard deviation returns to 1.0 to 1.05 and the difference with white noise
closes. Removing the mask also changes the fitted trend across the whole curve, so these numbers
alone do not establish that this asymmetry is the mechanism; a test would apply a mask to the
pseudo-windows themselves. `nomask` is a **diagnostic, not a correction**: the mask is needed to
protect a real transit. A correction would treat the pseudo-windows as the real
ones (detrend with each pseudo-window masked), which is a redesign, not an adjustment. This question
was added by this analysis, inside item 3 (d); the literature below shows red noise as a known issue
in transit detection, and detrending with known transits masked as common practice, but the specific
asymmetry was not found stated there (not confirmed as a known result).

### What the sabotages say about the power of the limits

Paired with the same rows of the unsabotaged run (`strata.json`, `sabotage_vs_baseline`):

| Sabotage | Paired rows | Mean change of the pull sd (standard error over rows) | Rows failing: baseline, sabotaged | Reading |
|---|---|---|---|---|
| `model_errors_alone` | 6 | +0.399 (0.045) | 4, 6 | a real effect |
| `rho_zero` | 9 | +0.043 (0.012) | 0, 7 | a real effect |
| `neff_equals_n` | 3 | +0.012 (0.040) | 1, 1 | not distinguishable from the baseline |
| `pool_sectors` | 15 | +0.016 (0.015) | 6, 4 | not distinguishable |
| `force_phase_half` | 26 | -0.019 (0.013) | 5, 2 | not distinguishable |

Six of six sabotages were recorded as detected, but in three of them "detected" means one row failed
where the same row (or its neighbours) failed without the sabotage too: those three carry no evidence
of power. `share_event_cadences` is structural (A0.3) and is detected as designed.

**The limits themselves.** With 400 trials per row a perfectly calibrated Gaussian pull passes a row
with probability 0.950 (the mean band of ±0.1 is two standard errors). Over the 1,548 decidable rows
of A0, a perfectly calibrated estimator would fail about 77 rows (an expectation, valid with
dependent rows). Under the independent-row approximation, passing every row with perfectly
calibrated Gaussian pulls is extraordinarily unlikely (about 3e-35; rows sharing a curve are
correlated, so this figure is uncertain); A0's 597 failures, versus about 77 expected, indicate
substantial miscalibration, not an artefact of multiplicity. An
estimator with a true standard deviation of 1.10 fails its row about half the time at n = 400, so the
band has useful power only near that size of error.

## (e) The two paths

| | **A: finish this round up to the confirmation** | **B: close it before the confirmation (counted as one of the three rounds) and open the next with A0 and the matched estimator redesigned** |
|---|---|---|
| What it delivers | the runners, the gates and C1', C2', C3' for a battery whose fatal `odd_even` is INCONCLUSIVE by rule | an A0 that treats pseudo-windows like real ones and an estimator without same-data shape selection, then the same chain |
| Pros | the plan as written; the battery's other parts measured on real data; a complete record for this round | spends the confirmation only on a battery that can pass it; keeps the false-positive pool; the diagnosis points at specific, testable causes |
| Cons | the kept fraction is zero under the strict reading, so D2's kept requirement and T2a fail whenever their paired v0.4 kept fraction exceeds 0.10 (recorded references: 0.967 and about 0.997); D4 is data-dependent (forecast 1.000 INCONCLUSIVE); D1 would be met vacuously (section b); spends the false-positive pool (section c); needs a cap decision (below) | uses one of the three rounds with no confirmation; the redesign must pass its own acceptance, and the redesign may fail again |
| Development processor-hours | about 62 more (the acceptance's 180 less A0's 101.9 and WP3 (b)'s 15.6): about 220 in all, **above the 200 cap** | about 15 of A0 development, about 100 of A0 acceptance if its size is kept, about 62 for the others: about 180 in the next round |
| Calibration processor-hours | about 97: C1' 2,400 curves at the 110 s measured here (family P only, 100 curves), 73; C2' 20 and C3' 4 from the plan's allocation (C2 cost 39.13 hours for 100 stars in v0.5, so about 19.6 for 50; the version-3 chain's cost on those stars is not measured). **Above the 80 cap** | the same order, about 97, in the next round; the plan forbids reducing the sizes as a cost fallback |
| Agent-days (estimates) | about 5 (six runners 1.5, calibration 3.5) | about 8 to 9 (closing this round 0.3, A0 and the estimator 1.5, the acceptances 2, the runners 1.5, calibration 3.5) |
| Review tokens | up to 1.0 M (C3' dossiers 0.45, gate 0.35, infeasibility records 0.2) | none now; the same 1.0 M in the next round |

Under A the same redesign is still needed afterwards, so A's costs are in addition to B's, not
instead of them.

**Two decisions are needed under either path.** (1) Applied row by row, the acceptance's bands are
extraordinarily unlikely to be passed even by perfectly calibrated pulls (section d). Whether to
keep that design, to raise the trials per row, or to declare a procedure for the many rows before
the code is the maintainer's decision; it is not proposed here as a relaxation, and nothing is
changed by this analysis. (2) The calibration projection is above its cap under either path; the
projection must be settled before any confirmation.

**Recommendation of the agent: B.** The confirmation is a one-time resource, and its false-positive
pool may allow about one. Under A the kept fraction is zero under the strict reading, so D2's kept
requirement and T2a fail unless their paired v0.4 kept fraction is at most 0.10 (the recorded
references are 0.967 and about 0.997), and D4 is forecast to fail, so A spends that resource and about 160 processor-hours (62 + 97) to learn little
that section (b) does not say.

**Recommendation of Codex: B** (`docs/plans/v0.5.1-consensus/strategy-round-*-answer.md`): the
strict reading leaves `odd_even` no accepted cell, so the kept fraction is zero and D2's kept
requirement and T2a fail under the same condition on their v0.4 references; spending the one-time
confirmation on the current design has limited value; B also
addresses the mean bias and the scatter before the confirmation. Codex's condition: the budget
projection has to be resolved before any confirmation; that is a condition on the plan's
feasibility, not a reason to prefer A.

## Literature (read on 2026-11-08)

- Self and Liang 1987, JASA 82, 605, abstract (the limit of the maximum likelihood estimator is the
  projection of a Gaussian onto the admissible region):
  https://www.stat.cmu.edu/~brian/nynke/726-2007/F%20-%20Neuron%20Firing%20Features%20-%20Sommer/self-liang-87.pdf
- Half-normal distribution, `E[Y] = sigma sqrt(2/pi)`: https://en.wikipedia.org/wiki/Half-normal_distribution
- Gross and Vitells 2010, "Trial factors for the look elsewhere effect in high energy physics",
  abstract: https://arxiv.org/abs/1005.1891
- Newey and West 1994, "Automatic Lag Selection in Covariance Matrix Estimation", abstract:
  https://www.ssc.wisc.edu/~bhansen/718/NeweyWest1994.pdf
- Pont, Zucker and Queloz 2006, "The effect of red noise on planetary transit detection", abstract:
  https://arxiv.org/abs/astro-ph/0608597
- Student's t, variance `nu / (nu - 2)`: https://en.wikipedia.org/wiki/Student%27s_t-distribution
- Hippke et al. 2019, Wotan, abstract: https://arxiv.org/abs/1906.00966; its repository lists masking
  known transits during detrending (the search excerpt only): https://github.com/hippke/wotan
