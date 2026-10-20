# Plan of corrections for M4 and M5, revision 4 (specification; no code)

Status: **revision 4 with Amendment 1, every row closed as a specification by Codex review 4
(`corrections-plan-rev4-codex-review.md`, four rounds, 2026-10-17); the resumption was approved by
the maintainer on 2026-10-17 on this text (section 8). Nothing is implemented yet.** The agreement
of Codex closes the specification; it does not show that the methods work (section "What the
agreement of Codex does and does not show"). Written 2026-10-17 on branch `claude/v0-2-1-reopen` (Phase I). It amends revision 3
(`../population/corrections-plan/m4-plan-rev3.md`, SHA-256
`cc9b0cd85d4f77028b82f977b72f3ff0376e6ef506d34e820dc0e4b1b3004f18`, kept unchanged): every section
of revision 3 not named here stays as it is. It answers the six rows that Codex review 3 found open
(`../population/corrections-plan/codex-review-3.md`: B1, B3, B4, B5, B6, B7) and the new points R3-1
to R3-6, following the recommendations of Claude's critique in that file where they hold.

**Known exposure (closure record, condition 4):** these corrections were chosen after the
development failures of M0 to M3 were seen. Every record of the resumption says so.

Fixed and not reopened: C1 to C6 and their limits; the results of M0 to M3; the frozen development
manifest; at most two candidate versions (M4, M5); `points.json` append only; the general mode only
(the directed mode stays a separate pending item, issue #42); the decision thresholds listed in
revision 3, section 9.2 (min_snr 7.1 and 5.0, `max_timing_sigma_durations` 1, k = 1, the FAIL rule's
3, g* = 10, α_H, α_A, δ).

## 0. Closure table (revision 4)

| Row | Open point (review 3) | Revision 4 (section) | Numeric criterion |
|---|---|---|---|
| B1 | var(d) of the hidden window used `β²(X′WX)⁻¹`; the cross term was not shown conservative; dependence after the detrending | the variance is estimated by **empirical replicas** of the same operation, placed by a deterministic metadata-only rule, masked in the detrending as the windows are; the remaining approximations (comparability after the detrending, independence of windows, the MAD scale) declared and checked (1) | K5 to K8 unchanged (they check the result); unit: the variance of a known AR(1) within 15%, and the full operation's pulls within the K margins |
| B3 | b and s per noise model, which the tool does not receive; T1 pooled the noise models | **one b and one s** for every case (no label); T1 split by noise model (2) | T1a-w, T1a-r, T1b-w, T1b-r, each ≤ 0.02 (upper bound), n ≥ 725 conclusive each |
| B4 | the input curve of `period_alias`; undefined statistics | the input is the **raw** light curve, as today; d_box ≤ 0, a singular fit or a non-finite value give INCONCLUSIVE (3) | T2a, T2b, L1 unchanged; unit: the three undefined cases |
| B5 | the Lomb-Scargle and FAP operation not unique; paired comparisons incomplete; T5 and M1 only without variability | one-term periodogram, its normalization, frequency limits and sampling fixed, and the same in the FAP call; the FAP is an **operational statistic** calibrated by T6; empty bins; "found" defined; T5 and M1 also with variability (4) | T5, T5v, M1, M1v, T6w, T6r |
| B6 | joint power not shown for the actual design; the twin protocol; missing denominators; M1's false pass | union bound; M1 power by simulation; the twin protocol listed step by step; the probability of a sufficient denominator; what an approval authorizes (5) | computed by a new sizing script before any run |
| B7 | the reserve guarantee by a commit hash is false; M5 defaults, variants and triggers | **reserve seeds from a future drand round**, declared in the freeze commit before the round is published; the commit identifier is the 40-character git hash; M5 configurations complete (6) | mechanical rule |

The rows B2, B8 and N stay closed as revision 3 wrote them.

## 1. B1: the variance of a hidden window's depth by empirical replicas

**Why the change.** The depth of a window is `d = mean over the box of (baseline model − flux)`,
with a baseline fitted by weighted least squares (revision 3, 4.1). Under correlated noise its
variance is `Var(mean in box) + Var(baseline prediction) − 2 Cov(...)`, where the baseline
prediction weights cadences with signs of both kinds, so no simple bound holds (review 3, B1).
Revision 4 does not derive this variance: it **measures** it, by applying the same operation where
there is no predicted signal.

**Replica spans (registered from metadata, before any hidden read).** After the windows are fixed
and before `HiddenYear` is built, `plan_round` registers replica centers by this deterministic rule.
Let `L = 2 × baseline_outer` be the full measurement span of a window (box plus baseline bands; with
the timing slack, `L = 4 T14 + 6 σ_t` at the default parameters, `holdout.py`), and let the *sector
spans* be the `[t_start, t_end]` of the hidden sectors (metadata; data gaps inside a sector are not
known before the read and are not used).

1. Candidate phases, in this order: 0.25, 0.75, 0.125, 0.375, 0.625, 0.875, then the next dyadic
   level (0.0625, 0.1875, …, 0.9375), down to a spacing of 1/64. For each phase in that order, the
   candidate centers are `t0 + (n + phase) P` for every epoch `n` whose center lies in a sector span,
   in increasing time.
2. A candidate is **accepted** if its span `[c − L/2, c + L/2]` lies wholly inside one sector span,
   does not overlap the measurement span of any transit or control window, nor of a replica accepted
   before it, **and** the *masked time fraction* of its sector stays at most 0.5 once it is added.
   The masked time fraction of a sector is the length of the union, clipped to the sector span, of
   the masked intervals of every window and accepted replica (each `±baseline_inner` around its
   center, as `HiddenYear` masks), divided by the sector span's length.
3. Otherwise the candidate is rejected and the next one is tried. Acceptance depends on metadata and
   the train ephemeris only.

The replica spans are registered like windows (kind `replica`) and are read only through
`HiddenYear` and its access log.

**Geometry.** The number of replicas depends on `σ_t`. Example (P = 3.7 d, T14 = 2.5 h, two 27-day
sectors, computed by Codex review 4): at `σ_t = 0` about 28 replicas from the phases 0.25 and 0.75
alone; at `σ_t = 0.75 T14`, 13; at `σ_t = T14`, none fits between a transit and a control window.
So `R_min` is reachable with a precise ephemeris and not across the whole admitted range
(`max_timing_sigma_durations` = 1). A round below `R_min` is INCONCLUSIVE; this enters the
conclusive fractions of the sizing (section 5) and the predictions of M4.

**The same detrending treatment.** The hidden-year detrending masks every accepted replica span
exactly as it masks the windows (out to `baseline_inner`), so the box cadences of replicas and
windows never feed the trend. This makes the two **comparable by construction only approximately**:
the trend is a set of local fits shared between neighboring spans (`detrend.py`), so positions near
the edges of a sector or near other masks can be treated differently. The approximation is declared
and checked by K5 to K8 and by the unit criteria below; it is not claimed as an identity.

**The estimate.** Each replica gives `d_j` by the same operation as a window (the same box
half-width, the same baseline model of revision 3, 4.1, with the train frequencies, the same
degeneracy rules). With `n_rep` valid replicas, `var_rep = (1.4826 · MAD(d_j))²`: a robust scale
turned into a variance under a near-normal shape, a declared approximation. A round needs
`n_rep ≥ R_min` (20 in every configuration); with fewer, decision 2 and the measurement are
INCONCLUSIVE with reason `hidden_noise_undetermined`. The stacked hidden depth is the mean of the
`N` window depths (equal weights: the windows share the geometry). With `s_d` the sample standard
deviation of the window depths (ddof 1), the error is `max(sqrt(var_rep / N), s_d / sqrt(N))` when
`N ≥ 3`, else `sqrt(var_rep / N)`. The division by `N` assumes the window depths independent with a
common variance (windows a period apart; the covariance the detrending may add between them is not
estimated): a declared approximation, checked by K5 to K8.

**Decision 1 (train only).** The same estimator on the train data: replica centers at the train
ephemeris' phases 0.25 and 0.75 in the train years (and further phases as above), with the train
detrending masks; `e_pred = sqrt(var_rep,train / n_windows_pred)`, inflated by the margin `m_β` of
the configuration (revision 3, 9.2). Revision 3's `g′Σg` and `β_b` are withdrawn.

**What is assumed, declared.** Stationarity of the noise within a year (replicas and windows have
the same noise distribution) and independence of windows separated by at least a period; the
replicas measure everything else (the baseline fit, its negative weights, the detrending). K5 to K8
check the consequence on the calibration population; a failure there reopens this row.

**Unit criteria (added to revision 3, section 10).** White noise: `sqrt(var_rep)` within 15% of the
analytic error of the operation over 200 seeded light curves (median ratio); AR(1) of known
parameters: within 15% of the variance measured by Monte Carlo on the same geometry; the full
operation (stacked depth and its error) on 200 seeded AR(1) hidden years without signal: the
fraction of |pull| ≤ 1 and ≤ 2 inside the K margins of revision 3, 8.3; a hidden year with too few
replicas: INCONCLUSIVE `hidden_noise_undetermined` with an empty measurement; the accepted replica
spans never overlap a window's measurement span, and the masked time fraction never exceeds 0.5
(checked on every unit case); the rule gives the same list for the same metadata (determinism).

## 2. B3: one b and one s, and T1 by noise model

- **b and s** (revision 3, 4.6) are estimated on the selection part **from every round of injected
  constant signals with `S_pred ≥ min_snr`, pooled over both noise models**, as the median and
  `1.4826 × MAD` of `S_meas − S_pred`. The tool uses the same two numbers for every light curve: it
  never receives, and never infers, a noise label (revision 3, 1.2).
- **T1 by noise model:** T1a-w, T1a-r (planets without variability, white and correlated noise) and
  T1b-w, T1b-r (with variability), each with its own one-sided 95% upper bound ≤ 0.02 and at least
  725 conclusive targets. This matches C1, which is evaluated per noise model.
- The joint power is recomputed over all 21 conditions (5). The four T1 conditions bound the
  holdout FAIL rate per noise model and variability, conditional on a conclusive round; they give
  no bound per SNR band and no unconditional bound.

## 3. B4: the input of `period_alias` and its undefined cases

- **Input:** the raw normalized light curve (`data.lc`), as today (`pipeline.py`, `battery_tests`:
  `check_period_alias(data.lc, ...)`), with the test's own long-window detrending. Revision 3's
  "L1 ... as today" in its section 1.4 is corrected to this. No prewhitening reaches the test.
- **Undefined statistics:** if `d_box ≤ 0`, if a design matrix of `F` or `F+box` is singular
  (condition number above 1e10 after column scaling), or if any of `Z_F`, `f`, `G` is not finite, the
  test is INCONCLUSIVE with that reason. Unit cases, one each.

## 4. B5: one prewhitening operation

- **Periodogram:** `astropy.timeseries.LombScargle(t, r, dy, fit_mean=True, center_data=True,
  nterms=1, normalization="standard")`, with `dy` the per-cadence `σ_w` of the cadence's sector (A1),
  on `autofrequency(samples_per_peak=10, minimum_frequency=f_lo, maximum_frequency=f_hi)`,
  `f_lo = 1 / (half the longest segment)`, `f_hi = 1 / (2 h)`.
- **The sequence of one iteration (unique):**
  1. Object `L0` on every cadence of the current residual `r` (with its `dy`); its power on the grid;
     the candidate frequency `f*` is the grid frequency of the highest power.
  2. The robust asymmetric fit of revision 3 (fundamental and one harmonic at `f*`, per-sector
     amplitudes) gives the clip set: the cadences more than `k_clip σ_w` below the final model.
  3. Object `L1`: the same constructor on the cadences **not** in the clip set (the same `dy` for each
     kept cadence), the same grid; `p1 = L1.power(f*)` at the single frequency `f*`.
  4. `FAP = L1.false_alarm_probability(p1, method="baluev", minimum_frequency=f_lo,
     maximum_frequency=f_hi, samples_per_peak=10)`. (Astropy computes the FAP from the power it is
     given and the object's own data; it does not recompute the periodogram.)
  5. Accept `f*` if `FAP < fap_max` and the few-harmonic test passes (on the kept cadences); if
     accepted, subtract the robust fit's model from **every** cadence (clipped ones included) and
     iterate; otherwise stop.
- **The FAP is an operational selection statistic**, not a probability valid for the clipped,
  iterated procedure; its threshold `fap_max` is a configuration setting whose consequence is
  calibrated by T6w and T6r.
- **Subtraction model:** the robust asymmetric fit of revision 3 (fundamental and one harmonic,
  per-sector amplitudes) is used only to subtract the accepted frequency and for the few-harmonic
  test; it never enters the periodogram or the FAP.
- **Few-harmonic test, empty bins:** 50 phase bins; a bin with fewer than 3 cadences is dropped; if
  fewer than 40 bins remain, the frequency is not accepted (reason `too_few_phase_bins`).
- **"Found":** a transit is found when the final candidate passes the SNR gate and has signal
  identity (P, 2P or P/2 within 0.001 of the injected period). T5 and M1 use this definition, at the
  final candidate, the same stage with and without prewhitening.
- **With variability:** T5v and M1v repeat T5 and M1 on planets with variability (the same limits),
  so a conclusion about preserving the transit covers them; if the selection part cannot give their
  minimum denominators, the configuration fails selection.

## 5. B6: power, twin, denominators and what an approval says

- **Joint power:** a lower bound by the union inequality, `1 − Σ P(condition fails)`, over the 21
  conditions (K1 to K8, T1a-w, T1a-r, T1b-w, T1b-r, T2a, T2b, T5, T5v, T6w, T6r, L1, M1, M1v), **plus
  the probability that each condition with a minimum misses it** (below); target 0.80. M1 and M1v
  power by simulation of the distribution-free interval under the declared spread (0.05), not by the
  lower bound `max(0, p_lo + p_hi − 1)`. Carrying revision 3's marginals over to 21 conditions
  already gives about 0.788 (Codex review 4): the sizes are therefore recomputed, and the sizing
  script raises the size of the condition with the largest failure probability, step by step, until
  the bound reaches 0.80. Nothing is measured to set these sizes; they follow from the declared
  reference rates.
- **Sufficient denominators (replaces revision 3's rule with `1.8 f`):**
  1. For each condition with a minimum `m` (T1a-w, T1a-r, T1b-w, T1b-r, T2a, T2b, T5, T5v, L1, M1,
     M1v; eleven) and each stratum of its group (band × mechanism, the strata of the generation),
     the selection part gives the fraction `f` of usable cases (conclusive, found, or with identity,
     as the condition defines it). Let `S_total` be the number of (configuration, condition, stratum)
     triples over **every configuration that may be examined** (the six of the budget, revision 3,
     9.1), fixed now from the declared strata.
  2. **A simultaneous budget for the bounds:** `α_den = 0.01` for every lower bound of every look at
     the selection, over every configuration, together. With at most two looks per configuration
     (step 4), each `f_L` is the one-sided Clopper-Pearson lower bound at level
     `1 − α_den / (2 S_total)` (Bonferroni), so all the bounds of the whole selection hold together
     with probability at least 0.99.
  3. The reserve's stratum sizes keep the selection's proportions; the group size `N` is the smallest
     for which the probability of at least `m` usable cases is at least **0.999** when every
     stratum's usable fraction equals its `f_L` (a sum of independent binomials, computed exactly).
     If `N` exceeds 3000 per noise model, the configuration fails selection.
  4. **The one enlargement, and its trigger.** After the first evaluation of a configuration on the
     selection part, the block (one replica set of the groups concerned, declared now) is added
     **if and only if** some condition has fewer than `m` usable cases in the selection part, or its
     `N` of step 3 exceeds 3000. The bounds are then computed again on the enlarged part (the second
     look of step 2) and the selection part is final; otherwise the selection part is final as it is.
  5. A reserve that still gives fewer than `m` is a **terminal failure** of that configuration in that
     reserve; it is never enlarged after its generation.
  6. **What enters the union bound:** `α_den` (the bounds), plus at most 0.001 per condition with a
     minimum (a missing denominator when the bounds hold), 0.011 for the eleven. The resulting 0.80 is
     a lower bound on joint approval **conditional on the declared reference rates** of the
     marginals (design assumptions, revision 3, section 2 of the study); it is not a measured power.
  7. **Order of the records.** The sizing algorithm (script and its reference-rate inputs) is
     committed before the selection part is generated. The reserve sizes it computes from the
     selection results are its output, committed in the freeze commit of the configuration, before
     the reserve's drand round is published and before the reserve is generated.
- **The twin protocol, per estimator.** The estimand of an operation is its value on the noiseless
  twin with the **structures** taken from the noisy analysis and the **coefficients** estimated again
  on the twin by the same code:

| Operation | Frozen from the noisy analysis | Estimated again on the twin |
|---|---|---|
| detrending | the trend (the twin is divided by the noisy curve's trend), the masks, the clipped cadences (removed from the twin) | — |
| prewhitening | the accepted frequencies, their order, the clip set | the per-sector amplitudes and phases, by the same robust fit on the twin |
| per-event and stacked depth (K1, K2) | the ephemeris, the box and baseline spans, the cadence set, the weights | the baseline coefficients and the depths |
| hidden-window depth (K5 to K8) | the windows, the replica spans, the train frequencies in the baseline design, the cadence set, the weights | the baseline coefficients and the depths |
| transit time (K3, K4) | the template shape (depth, T14, τ) fitted on the noisy curve, the scan range, the step, the cadence set; the epochs used and the per-transit weights of the noisy fit; the reference transit (the first of the last observing year) | each center, by the same chi-square scan on the twin; then the weighted linear ephemeris refitted on the twin's centers (same epochs, same weights, same reference epoch) and evaluated at the reference transit |

  So the noise of the baseline fit enters the noisy value and not the twin's, and the timing pull of
  K3 and K4 is `(noisy extrapolated time − twin extrapolated time) / noisy propagated error` at the
  same reference transit, not zero by construction. The twin check (twin plus regenerated noise
  equals the case's flux, bit for bit) checks the generation only.
- **What an approval authorizes:** that the operation's stated error covers the scatter of the
  operation around its own estimand (coverage), on synthetic data of this population; not that the
  operation is accurate against the injected value. The bias against the injected value is a separate
  selection condition (revision 3, 8.2) and is reported for the reserves.
- A new sizing script (`calc/calibration_sizing_rev4.py`) computes all of the above. Its records
  follow the order of item 7 of the denominator rule: the script, its reference-rate inputs and its
  sizes of the selection part are committed before the selection part is generated; the reserve
  sizes, which depend on the selection results, are committed in the freeze commit, before the
  reserve's drand round is published.

## 6. B7: reserves that cannot be anticipated, and complete M5 configurations

- **Reserve seeds from a future drand round.** The freeze commit of a configuration declares the
  number of a future round of the drand chain used by the project
  (`8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce`); the reserve's prefix is
  `refute-v0.2.1-calibration-r4-<randomness>` (and `-r5-` for M5), with `<randomness>` the round's
  hex randomness, its signature verified as in the v0.2 selection. The commit is pushed before the
  round is published; the round number and the commit's 40-character git identifier are recorded.
  **Each declaration of a drand round is approved by the maintainer** (working mode, item 3).
- **M5 candidates, complete** (revision 3, 9.4, with the settings it lacked):

| Candidate | Default | The one variant | Trigger and its aggregation |
|---|---|---|---|
| M5-1 joint train ephemeris | trapezoid of the timing template fitted to all train data by weighted least squares in (P, t0), shape fixed; error from the fit's covariance times β(n_τ) | shape (depth, T14, τ) free in the joint fit | over the white planets without variability of the selection part, the median of (timing error propagated to the hidden year) / (Carter reference) > 1.5 |
| M5-2 parametric correlated noise | AR(1) plus white, maximum likelihood per segment, replacing the binned rms in A1 | the same with τ bounded below by 5 cadences | over the correlated light curves of the selection part, the median across light curves of (1.4826 MAD / median of β(n_T) over each curve's sectors) > 0.3, or the pooled fraction of sectors excluded by the few-bins rule > 0.10 |
| M5-3 flexible hidden-window baseline | Legendre polynomial on the baseline bands, order 0 to 3 chosen by BIC | order 0 to 2 | over the variability light curves of the selection part, the pooled fraction of windows dropped as degenerate > 0.10, or their conclusive fraction < 0.5 × that of the light curves without variability |
| M5-4 quasi-periodic variability | each accepted frequency with 3 harmonics and amplitudes per orbit | 2 harmonics | over the variability light curves of the selection part, the pooled fraction whose residual periodogram keeps a peak at an accepted frequency with FAP < `fap_max` > 0.10 |

  **The settings each candidate needs, fixed now:**
  - **M5-1, the Carter reference.** For each train transit time, `σ_C = (σ_w / depth) ·
    sqrt(τ · cadence / 2)` (Carter et al. 2008, eq. 43, the form already cited in revision 3,
    section 3), with `σ_w`, depth and τ of the train template and the cadence of the plan. These
    `σ_C` replace the tool's per-transit errors in the same weighted linear fit, at the same epochs;
    the reference is that fit's covariance propagated to the first hidden transit,
    `sqrt(Var(t0) + 2 n Cov(t0, P) + n² Var(P))`, without the reduced chi-square inflation. The
    ratio uses the tool's propagated error at the same epoch.
  - **M5-2, the likelihood.** Per segment (the A1 segments, split further at 2000 cadences), the
    residuals have covariance `σ_w² I + σ_r² exp(−|Δt| / τ)` with the real times; parameters
    `σ_w > 0`, `σ_r ≥ 0`, `τ` in [1 cadence, 1 d] (the variant: [5 cadences, 1 d]); exact Gaussian
    log-likelihood; maximized by L-BFGS-B from three starts, in this order, with `σ` the robust
    standard deviation of the segment's residuals: (`σ_w` = σ, `σ_r` = 0, τ = 1 h), (`σ_w` = σ/√2,
    `σ_r` = σ/√2, τ = 1 h), (`σ_w` = σ/2, `σ_r` = σ, τ = 1 h), with `σ_r` = 0 started at 1e-6 σ inside
    the bound. A start counts as converged when L-BFGS-B reports success with finite parameters and a
    finite log-likelihood. The result is the converged start of highest log-likelihood; a tie (equal
    within a relative 1e-9) goes to the earlier start. Only when no start converges does the segment
    fall back to the binned rms of A1, and the fallback is recorded. Conversion to the tool:
    `β(n)² = (σ_w² n + σ_r² (n + 2 Σ_{k=1}^{n−1} (n − k) φ^k)) / (σ_w² n)`, `φ = exp(−cadence / τ)`,
    per sector from the segment-length-weighted parameters.
  - **M5-3, the criterion.** `BIC = n ln(RSS_w / n) + k ln n`, with `RSS_w` the weighted residual
    sum of squares on the baseline bands, `k` the order plus one, `n` the baseline cadences; an
    order whose design fails the degeneracy rule of revision 3, 4.1 is not considered; ties go to
    the lower order; with no admissible order, the window is dropped (reason recorded).
  - **M5-4, the orbits.** An orbit is a run of a sector between gaps longer than 1 day (the TESS
    orbit gap); per orbit the mean and, for the fundamental and the harmonics 2 and 3 (variant: 2),
    a cosine and a sine amplitude are free, with the frequencies `f`, `2f`, `3f` common to the
    sector.

  Every trigger is computed on the selection part at the M4 freeze, before M4 is measured, and
  recorded in the freeze commit.

## 7. What this revision does not change, and what it needs before any code

- Revision 3's sections 1, 2, 3, 4.2 to 4.5, 6, 8 (except its sizes, recomputed by the new script),
  9.1 to 9.3, 10 (plus the unit criteria added above), 11, 12, 13 and its appendices.
- **Before any code** (closure record, conditions 1 to 3): an independent read-only review of this
  revision (Codex) with every row closed (done: `corrections-plan-rev4-codex-review.md`); the
  maintainer's approval of the resumption and the decision on the development population (both
  taken on 2026-10-17, section 8); this file committed, with the SHA-256 of the approved version
  recorded in `corrections-plan-rev4.sha256`; the updated sizing and the ceiling of execution to the
  maintainer before the calibration population is generated; no constant tuned on the M0 to M3
  numbers.

## Amendment 1 (2026-10-17): the 21 conditions in the selection, the reserves and M5

A consistency correction asked by the maintainer on 2026-10-17, after Codex review 4 and before
revision 4 was committed; not a new round of design. Revision 4 works with 21 conditions (section 5),
but it inherits from revision 3 the rules that name "all 17 conditions": the choice of the M4
configuration (revision 3, 9.3: "passes all 17 conditions and the bias tolerances on the selection
part"), the validation column of the M5 candidates (9.4: "all 17 conditions on selection, then R5"),
the evaluation of M5 (9.4: "with all 17 conditions"), and the title and joint power of 8.3.
Revision 3 is not edited (it is a historical record). In revision 4 these rules read:

- **The conditions** are the 21 of section 5: K1 to K8; T1a-w, T1a-r, T1b-w, T1b-r; T2a, T2b; T5,
  T5v; T6w, T6r; L1; M1, M1v. Each keeps the group, size rule and limit of revision 3, 8.3, with the
  changes of sections 2, 4 and 5 (the four T1 split by noise model; T5v and M1v the same as T5 and M1
  on planets with variability).
- **Selection (revision 3, 9.3):** the M4 configuration is the first in the order of 9.2 that passes
  **all 21 conditions** and the bias tolerances on the selection part.
- **Reserves:** R4 (and R5) are examined once on **all 21 conditions**; a configuration that fails
  any of them in its reserve is not measured (revision 3, 9.3), and a missing denominator in a reserve
  is a terminal failure (section 5).
- **M5 (revision 3, 9.4):** each candidate's validation is **all 21 conditions** on the selection part,
  then R5; M5's configurations are evaluated with all 21 conditions.
- **The joint power** is the union bound of section 5 over the 21 conditions (it replaces 8.3's 0.838
  for 17 conditions under an independence approximation).

Nothing else changes; no condition, limit or threshold is added, removed or moved. The pertinent
conditions are all 21 in each of these steps: none is dropped for any configuration.

## What the agreement of Codex does and does not show

Codex review 4 closes revision 4 **as a specification**: every open point of review 3 has a
definition precise enough that two implementations should not differ. It does **not** show that the
methods work. Whether they do depends on the implementation, its unit tests (section 1 and revision 3,
section 10), the calibration of the estimators on the calibration population (21 conditions, its
reserves), the measurement M4 (and M5) on the development population, and, at the end, the
confirmation on new seeds from a future drand round, which can fail the whole package.

## 8. Decisions of the maintainer (2026-10-17)

1. **Resumption: approved** on revision 4 with Amendment 1. The design is approved; the updated
   sizing of section 5 (the new script and its output for the selection part) and a **ceiling of
   execution** go to the maintainer **before** the calibration population of the estimators is
   generated. The figures of item 4 below are revision 3's worst case scaled, not revision 4's.
2. **The development population: reuse the frozen one**, with these conditions: C1 to C6 and their
   limits stay; M0 to M3 and the manifest stay; the limit of two candidate versions (M4 and M5)
   stays; the inherited counters, journals and attempt limits are **not** reset by the reopening; the
   confirmation stays unseen, on frozen code, with randomness from a future drand round. The
   confirmation must be able to fail the package, and a failure does not authorize another attempt
   automatically: it goes to the maintainer.
3. **drand rounds:** the reserve R4 (and R5 if M5 is measured), and later the confirmation, each
   declared one by one with the maintainer's approval; so are protocols and locks.
4. **Compute:** with heavy work on logical processors 0 to 7 and 6 workers, the cost of revision 3,
   section 13 (24 workers) is about four times longer: of the order of 2.5 days of machine time for
   the calibration worst case, plus about 0.8 day per development campaign of two points. This is
   revision 3's worst case scaled; it is **not** yet revision 4's: the new sizes (section 5), the
   paired evaluations T5v and M1v and the cost of the replicas are not included, and the new methods
   add an unmeasured cost. The sizing script of section 5 states the new worst case before any run. A
   wider affinity when v0.3 is sealed shortens this.
