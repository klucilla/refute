# The C3 white INCONCLUSIVE planets: train timing precision (M3, slot 1)

Version 2 (2026-10-14). The version reviewed in `codex-m4-plan-review-2.md` is preserved unchanged in `dev1-c3-inconclusive-v1.md` (SHA-256
`38372427b10c7c36802f24ce9607ac7979345993fefb0a93378d36c74503899e`). This version changes only the text
(the class names, the caveats of the method and the presentation of the 40 of 250); the numbers are the same, from the same script and the same records.

<!-- translation-note -->

Translated by script from the maintainer's Portuguese record `dev1-c3-inconclusive.md`, version 2 (SHA-256 `3c1b2732775cdbe0b7c655af6f55521fa75362a00dbaa15f734ab77bf00dda5b`), with the same numbers (`investigations/check_numbers.py`), plus the dated errata below. The Portuguese records and the review files named here are kept in the archive of the study. File and line references are to commit `605fac1`.

<!-- /translation-note -->

<!-- translation-note -->

## Errata (2026-10-14)

Version 2 is translated below without changes; this section corrects it and does not rewrite it, in four separate items, each with its source. The sources are Codex review 3, section 5, and section 4 of Claude's critique, both in `../../corrections-plan/codex-review-3.md`; the code lines are those of the Portuguese script that the review read (`dev1/c3_inconclusive.py`, in the archive of the study). The Portuguese record keeps the same errata, item for item, in `dev1-c3-inconclusive-errata-v2.md`.

1. **C01 (method (a)).** The omission affects the reported lever arm, not directly the counts 21 and 38. The counts compare the `max_timing_sigma` recorded by the tool, scaled by sigma_tc,approx / sigma_tc,tool (method (b)), with one duration (`dev1/c3_inconclusive.py:103-104`); the lever arm m of method (a) (`dev1/c3_inconclusive.py:96`), which leaves out C01 and the integer reference epoch, is only reported. The sentence of method (a) that gives the counts "an uncertainty of a few cases" because of these two approximations is therefore wrong. The approximation that does weigh on the counts is the scaling by err(t_ref) x sqrt(N) of method (b). *Source:* Codex review 3, section 5, correction 1; Claude's critique, section 4, item 1.
2. **Uncertainty of the counts.** The effect of that scaling on the counts is an unquantified sensitivity, not "a few cases" (method (a) and the caveats of section (d)). *Source:* Codex review 3, section 5, correction 2; Claude's critique, section 4, item 2.
3. **"Do not change".** In the last caveat of section (d), the other paths to INCONCLUSIVE (4 of the 61) do not change only inside the conditional scenario of (d); the M4 package could change candidates, capacity and other paths to INCONCLUSIVE (corrections plan, revision 3, section 6). *Source:* Codex review 3, section 5, correction 3; Claude's critique, section 4, item 3.
4. **Medians.** With an even number of values the medians take the upper central value (`vals[len(vals) // 2]`, `dev1/c3_inconclusive.py:152-154`), not the mean of the two central values; this does not change the counts 21 and 38. *Source:* Codex review 3, section 5, correction 4; Claude's critique, section 4, item 4.

<!-- /translation-note -->

Read only: the result records and the frozen manifest. Script: `investigations/c3_inconclusive.py`. Cases: white measurable planets of `two_years` and `few_train` with verdict INCONCLUSIVE at M3: **57**. The generation parameters (injected ingress, depth and duration) enter **only the diagnosis**, never as a proposed input to the tool.

## Method

- **(a) The tool:** in each round, `max_timing_sigma` is the train-only timing uncertainty at the farthest hidden transit; the rule declares the round INCONCLUSIVE when it exceeds 1 duration of the train candidate (`holdout.py:513-537`). The lever arm m (epochs between the reference epoch and the farthest hidden transit) is **approximated** by sigma_max² = err(t_ref)² + m² err(P)². The tool's actual prediction is sigma_pred² = C00 + 2·m·C01 + m²·C11 (`ephemeris.py:103`), with the reference epoch **rounded to an integer** (`ephemeris.py:124`); the cross term C01 was left out here because `Ephemeris.to_dict` does not export it. The effect of these two approximations **was not quantified**; at least two cases lie close to the limit of 1 (ratios 1.0116 in `planet-measurable-white-0062` and 1.0304 in `planet-measurable-white-0044`), so the counts below have an uncertainty of a few cases <!-- translation-note -->(see the errata, item 1)<!-- /translation-note -->. The per-transit precision that the ephemeris implies is sigma_tc,tool = err(t_ref) × √N (equal weights; includes the chi-square inflation).
- **(b) The Carter approximation:** Carter, Yee, Eastman, Gaudi and Winn 2008 (arXiv:0805.0238, DOI 10.1086/592321, eq. 43; reference and formula checked on arXiv on 2026-10-14): Q = √(ΓT)·δ/σ, θ = τ/T, σ_tc = Q⁻¹·T·√(θ/2), with T the duration between the midpoints of ingress and egress, τ the ingress duration, Γ the sampling rate (1 per 2 min) and σ the per-point noise. **Eq. 43 holds for a uniform source, white noise and uniform sampling**; with limb darkening it underestimates the uncertainties (the abstract of the paper). Two versions: **approximation with train numbers** (δ, T14 and σ of the train candidate, σ taken from the depth error and the in-transit cadences, neglecting the baseline term and counting partial transits; δ and the duration are those of the BLS box, not the δ and T14 of the trapezoid; τ = **injected** ingress fraction × T14, because the box has no ingress) and **approximation with the truth** (injected δ, T14 and τ, σ = 600 ppm). Neither is an optimal estimator computed only from information that can be estimated from the train. The prediction scales the tool's: σ_pred,approx = σ_pred,tool × σ_tc,approx / σ_tc,tool, which is exact only if the new covariance is proportional to the old one (same epochs, equal weights, chi-square 1). The direct calculation, σ_pred² = σ_tc² [1/N + (n_hidden − mean(n))² / Σ(n_i − mean(n))²], would need the epochs of the train times, which are not in the records.
- **(c) Classification per round (a description of the calculation, a hypothesis; it does not show that the case is recoverable):**
  - **(i) uncertainty below one duration by the Carter approximation** (train version);
  - **(iii) above one duration by the approximation, with the train epoch below 0.1 duration** (σ_tc,approx/√N < 0.1 duration): by the approximation, the shortfall comes from the extrapolation over many periods;
  - **(ii) above one duration by the approximation, with the train epoch at 0.1 duration or more.**
  A case counts as (i) if some round is (i); otherwise (iii) if some round is (iii); otherwise (ii). The threshold of 0.1 duration is a choice of this diagnosis (`GOOD_EPOCH` in the script), not a physical boundary. The file `dev1/c3-rounds.json` of the Portuguese record, written by the run of its script, keeps the old class names, in Portuguese: "current estimator overestimates" corresponds to (i) above, and "measurable SNR, but the extrapolation exceeds one duration" corresponds to (iii)<!-- translation-note -->; `investigations/c3-rounds.json` is written with the class names of version 2, in English<!-- /translation-note -->.

## Result

| mechanism | classification | cases |
|---|---|---|
| few_train | (i) uncertainty below one duration by the Carter approximation | 7 |
| few_train | (iii) above one duration by the approximation, train epoch below 0.1 duration | 8 |
| two_years | (i) uncertainty below one duration by the Carter approximation | 14 |
| two_years | (iii) above one duration by the approximation, train epoch below 0.1 duration | 28 |

**two_years** (84 rounds with timing data), medians: tool ratio 2.43; tool σ_tc 9.58 min; σ_tc by the approximation (train) 4.95 min; σ_tc by the approximation (truth) 4.23 min; ratio by the approximation (train) 1.21; ratio by the approximation (truth) 0.983; lever arm 241 periods; N times 8; reduced chi-square 53.6; estimated noise 611 ppm.

**few_train** (30 rounds with timing data), medians: tool ratio 2.14; tool σ_tc 4.05 min; σ_tc by the approximation (train) 3.79 min; σ_tc by the approximation (truth) 3.15 min; ratio by the approximation (train) 2.04; ratio by the approximation (truth) 1.55; lever arm 241 periods; N times 6; reduced chi-square 12.3; estimated noise 614 ppm.

## Examples (3 per mechanism, the round with the smallest ratio by the approximation)

- `planet-measurable-white-0004`, hidden year 2020: tool σ_max 8.11 h against duration 2.1 h (ratio 3.86); N = 12, chi-square 163, lever arm 339 periods; tool σ_tc 20.2 min, train approximation 7.09 min, truth approximation 5.78 min (ingress fraction 0.05); ratio by the approximation, train 1.35, truth 1.1; class (iii)
- `planet-measurable-white-0006`, hidden year 2018: tool σ_max 4.75 h against duration 2.55 h (ratio 1.86); N = 8, chi-square 54.1, lever arm 216 periods; tool σ_tc 9.69 min, train approximation 6.41 min, truth approximation 6.29 min (ingress fraction 0.05); ratio by the approximation, train 1.23, truth 1.21; class (iii)
- `planet-measurable-white-0007`, hidden year 2018: tool σ_max 7.23 h against duration 2.2 h (ratio 3.29); N = 10, chi-square 151, lever arm 254 periods; tool σ_tc 15 min, train approximation 4.95 min, truth approximation 3.89 min (ingress fraction 0.05); ratio by the approximation, train 1.08, truth 0.85; class (iii)
- `planet-measurable-white-0157`, hidden year 2018: tool σ_max 3.97 h against duration 2.3 h (ratio 1.73); N = 8, chi-square 81.7, lever arm 113 periods; tool σ_tc 11.4 min, train approximation 4.29 min, truth approximation 3.29 min (ingress fraction 0.05); ratio by the approximation, train 0.648, truth 0.498; class (i)
- `planet-measurable-white-0170`, hidden year 2018: tool σ_max 2.72 h against duration 2.6 h (ratio 1.05); N = 6, chi-square 12.3, lever arm 187 periods; tool σ_tc 3.97 min, train approximation 3.38 min, truth approximation 2.52 min (ingress fraction 0.05); ratio by the approximation, train 0.89, truth 0.663; class (i)
- `planet-measurable-white-0171`, hidden year 2018: tool σ_max 5.41 h against duration 2.55 h (ratio 2.12); N = 9, chi-square 95.1, lever arm 232 periods; tool σ_tc 10.8 min, train approximation 6.05 min, truth approximation 4.11 min (ingress fraction 0.05); ratio by the approximation, train 1.19, truth 0.806; class (iii)

## Observations (hypotheses marked)

1. **No case fell into (ii).** By the approximation, in every round the train epoch would be fixed to well under 0.1 duration; what exceeds 1 duration is the extrapolation over ~240 periods to the hidden year (two years away). The boundary between (ii) and (iii) is the diagnostic threshold of 0.1 duration, chosen here; with another threshold the partition changes.
2. **The tool's ephemeris fit has a reduced chi-square far above 1** (median 53.6 in `two_years`, 12.3 in `few_train`): the individual times measured with the box scatter much more than the errors the tool assigns to them, and the √chi-square inflation (`ephemeris.py:133`) recovers the scatter. The effective per-transit precision (median 9.6 min in `two_years`) is about twice that of the approximation (4.9 min). **Hypothesis:** the per-transit error of the box scan (half-width of Δchi² = 1, with the floor of half a cadence, `ephemeris.py:64-78`) is optimistic, and the box measurement, without ingress, is less efficient than a model with ingress. **The chi-square of 53.6 does not by itself identify the cause**, and **does not guarantee that the trapezoidal model corrects it**: the scatter may also come from other sources (the residual variability, the trend, the selection of the train candidate); the model with ingress is what the ROADMAP asks for (`ROADMAP.md:132-133`), and its effect has to be measured on the calibration population<!-- translation-note --> (the planned noise-calibration population of the corrections plan, never generated nor analyzed; distinct from `calibration/v0.2/` and from the tag `v0.2.0-calibration-lock`)<!-- /translation-note -->.
3. **In all these planets the ingress fraction is 0.05**, the floor of the generator (section 4.3): a short ingress, the most favorable case for timing precision according to eq. 43.
4. **The two years of distance dominate.** Even by the approximation with train numbers, the median ratio stays at 1.21 (`two_years`) and 2.04 (`few_train`): most of these cases still cannot test the hidden year by timing. **Hypothesis:** it is a consequence of the declared geometry of the mechanisms (section 4.3), which the definition of "measurable" by SNR does not consider; it is not a defect of the population.

## (d) What this implies for C3 (without changing the criterion)

- Cases of the 57 with some round below 1 duration by the Carter approximation: **21** (train version) and **38** (truth version).
- The C3 white of planets at M3 is 61 of 250; the one-sided 95% upper limit (Clopper-Pearson) stays ≤ 0.20 with at most **39** of 250 (computed here; it agrees with `population-study.md:72`).
- **Sensitivity, not a bound:** if the 21 cases of the train version stopped being INCONCLUSIVE and nothing else changed, the C3 white would be 61 − 21 = 40 of 250; with the truth version, 61 − 38 = 23. It is a conditional scenario (same candidates, same epochs, a valid proportional scaling, all 21 conclusive and no other transition).
  **The approximation puts C3 near the approval threshold. There is a relevant risk of it staying FAILS; the probability of approval has not been estimated yet.**
- Caveats: a round that becomes conclusive can give PASS or FAIL (a FAIL would increase the C1 measurable white, now 58 of 250), or stay INCONCLUSIVE because of capacity, coverage or `period_alias`; the new model may recover discarded times and change the geometry of the fit; the approximations of (a) and (b) change the counts in a few cases; other paths to INCONCLUSIVE (4 of the 61 are outside these mechanisms) do not change<!-- translation-note --> (see the errata, items 2 and 3)<!-- /translation-note -->.
