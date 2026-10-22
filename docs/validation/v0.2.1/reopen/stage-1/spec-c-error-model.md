# Specification C: the predicted error of the capacity decisions (specification only)

Authorized on 2026-10-22 as a **specification, not code** (the maintainer's decision after X2, item
1), with Codex's review. It answers X2-B ([x2/README.md](x2/README.md)): `e_pred,2` overestimated in
both variability cells (`ρ_2` 1.25 and 1.21), the cells without variability not determined. It is
**not** a scale factor ("divide by 1.2"): it states candidate models, the data they are judged on and
a criterion, all fixed before the data that decide. Nothing here changes the engine; X3's definitive
calibration waits for its outcome.

## C0. The model today, from the code (`src/refute/packs/tess/holdout.py`)

- `predicted_error(var_rep, n_pred, margin=1.0) = margin · sqrt(max over the dP grid of var_rep(dP) /
  N_pred)` (lines 1258 to 1263); `var_rep(dP)` is the robust variance (`(1.4826 · MAD)²`, line 612)
  of the replica depths at that `dP`; `N_pred` the predicted transit windows in the hidden year.
- **Decision 1:** `e_pred,1 = predicted_error(train_var_rep, n_pred, m_beta)`: the train replicas
  (measured on the masked train curve) **with the margin `m_β`** (1.2 in the study's configuration).
- **Decision 2:** `e_pred,2 = predicted_error(hidden_var_rep, n_pred)`: the hidden year's replicas,
  **without `m_β`** (margin 1).

## C1. The hypothesis, as given, against the code

The maintainer's hypothesis: the measured excess (`ρ_2` 1.21 and 1.25) is close to `m_β` = 1.2; the
replicas may already carry the correlated noise, and `m_β` would count it twice. **The code does not
apply `m_β` to `e_pred,2`.** So:
- for **decision 1**, the hypothesis is direct: `e_pred,1` carries `m_β` on top of replicas that
  already see the train curve's correlated noise; X2 measured `ρ_1` 1.40 and 1.34 with variability,
  that is `ρ_1 / m_β` ≈ 1.17 and 1.12;
- for **decision 2**, the near-equality `ρ_2 ≈ m_β` cannot be `m_β` counted twice; it is either a
  coincidence or another mechanism. One candidate mechanism, from the code: the **maximum over the
  `dP` grid** of variances each estimated from a finite set of replicas is biased upward (the maximum
  of noisy estimates), more so with more grid points and fewer replicas.

Both are tested; neither is assumed.

## C2. The candidate models (fixed now)

Each is computable from fields every calibration record has since X1 (`train_var_rep`,
`hidden_var_rep`, `grid_dp`, `n_pred`, `m_beta`), so no engine run differs between candidates.

| Decision | Candidate | `e_pred` |
|---|---|---|
| 1 | `E1.0` (today) | `m_β · sqrt(max_G train_var_rep / N_pred)` |
| 1 | `E1.nomargin` | `sqrt(max_G train_var_rep / N_pred)` (the hypothesis: no `m_β`) |
| 1 | `E1.dp0` | `m_β · sqrt(train_var_rep(dP_0) / N_pred)` |
| 1 | `E1.dp0.nomargin` | `sqrt(train_var_rep(dP_0) / N_pred)` |
| 2 | `E2.0` (today) | `sqrt(max_G hidden_var_rep / N_pred)` |
| 2 | `E2.dp0` | `sqrt(hidden_var_rep(dP_0) / N_pred)` |
| 2 | `E2.median` | `sqrt(median_G hidden_var_rep / N_pred)` |

`dP_0 = 0`, always a point of the grid (`period_grid`, lines 472 to 487: odd, exactly symmetric,
containing 0; a single point 0 when there is no period uncertainty). `max_G`, `median_G` over the
round's grid. The
candidates without the grid's maximum test the second mechanism; `E1.nomargin` tests the first.

## C3. The reference and the quantities

As X2-B: per case-year, `σ_meas` = the standard deviation (deciding) and the 1.4826 MAD (the check) of
`d_hidden − d_twin` over the measured realizations with their twin (at least 30); `ρ_c =
median(e_c) / σ_meas`; the cell's value the median over its case-years, its 95% interval by a cluster
bootstrap over the cases (2000 resamples, the bootstrap seed of X2-B); at least 15 contributing cases.
Every realization measured counts, whatever its X2-A class.

## C4. The regimes

The four cells (white and AR(1), without and with variability) and, within each, the number of
observing years (2; 3 or more). **Which regimes are eligible is fixed by the data's coverage alone,
before any candidate is computed, and is the same for every candidate:** a regime is eligible when at
least 15 cases contribute (case-years with at least 30 measured realizations with their twin; the
reference `σ_meas` does not depend on the candidate). An ineligible regime does not count for or
against a candidate.

Expected coverage (Codex's review): X2e has, per cell, 14 cases with two observing years
(`two_years` and `few_train`) and 6 with three; pooled with X2, 28 and 12. So the three-year regimes of
the cells without variability cannot be eligible, and their two-year regimes only if enough of those
cases contribute; the cells themselves (all years together) are the regimes that can decide there.

## C5. The criterion (fixed now)

With `τ = 0.10` and the candidate's design value `D` (`m_β` for the candidates with the margin, 1
otherwise), in each determined regime: `calibrated or conservative as designed` if `[lo, hi] ⊂
[1 − τ, (1 + τ)·D]` by the SD, the MAD agreeing (otherwise `not determined`); `underestimated` if
`hi < 1 − τ`; `overestimated` if `lo > (1 + τ)·D`.

- **A candidate is admissible** if it is `calibrated or conservative as designed` in **every eligible
  regime**; an inconclusive interval, a disagreement of the SD and the MAD, `overestimated` or
  `underestimated` in any eligible regime makes it not admissible; each cell must have at least one
  eligible regime (else no candidate is admissible in that cell's decision).
- **The choice**, among the admissible candidates of each decision, in this order (the smallest change
  first): decision 1 `E1.0`, `E1.dp0`, `E1.nomargin`, `E1.dp0.nomargin`; decision 2 `E2.0`, `E2.dp0`,
  `E2.median`. Today's model is chosen whenever it is admissible: no change without evidence.
- **No admissible candidate** for a decision: no correction is proposed for it; the result is
  reported and goes to the maintainer.

## C6. The data that decide, and the data that only inform

- **Decide:** data never used, with new seeds: the extension of X2's cells without variability
  ([x2e-execution-package.md](x2e-execution-package.md)), and, for the cells with variability, a
  replicate with new seeds (its own package, not requested here). Until both exist, a candidate can be
  judged only in the regimes they cover, and the choice waits.
- **Inform only:** X2's lot (already seen, its X2-B read): every candidate is computed on it and
  reported as development evidence, never as the decision.

## C7. What is reported beside the decision (descriptive)

`ρ_c` of every candidate in every regime; `ρ_2` against the grid's size and the smallest replica count
(the second mechanism predicts a larger excess with more grid points and fewer replicas);
`ρ_1 / m_β`; and, for the chosen candidate, the rounds whose capacity decision would change, with no
claim that this is better (a released round can be a new PASS or a new FAIL).

## C8. After the decision (not authorized)

The code of a chosen candidate (a new corrections field and configuration file, so that today's
configuration and every frozen record keep their meaning), with tests before the code, sabotages and
Codex's review; then X3's definitive calibration with it. No threshold or gate changes in the
meantime.
