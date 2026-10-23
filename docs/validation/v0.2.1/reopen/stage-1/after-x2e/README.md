# After X2e: readings and proposals (the maintainer's decisions after X2e, `5294c49`)

Asked by the maintainer on 2026-10-22: the readings of items 1 to 4 and 6, the proposals of items 5
and 9, and a short list of the decisions pending. **Nothing here runs a lot, changes the engine, the
environment, a lock or an alert, or starts X3, X5, the attenuation front or any other front.**
Every number below is read from the committed evaluations by the scripts in [scripts/](scripts/);
none is a declared decision, and the development data (X2, and X2e read before this record) are not
validation.

| Item | What | Where |
|---|---|---|
| 1 | Spec C's eligibility with the data C6 allows; the C4/C6 amendment proposal | below; [spec-c-amendment-proposal.md](spec-c-amendment-proposal.md) |
| 2 | The scope of the pooled result, per regime | below |
| 3 | The maximum over the `dP` grid: fluctuation against real differences | below |
| 4 | "Wrong candidate" and the measurement FAIL against the engine's false FAIL | below; notes in [../x2/README.md](../x2/README.md) and [../x2/x2e/README.md](../x2/x2e/README.md) |
| 5 | One prospective package (proposal, not authorized) | [prospective-package-proposal.md](prospective-package-proposal.md) |
| 6 | Dependencies: security apart from the scientific comparison | [dependencies-reachability.md](dependencies-reachability.md) |
| 7, 8 | Attenuation stays its own front; the historical FAIL is kept; X3 waits | nothing done |
| 9 | Scientific success, viability and the effort ceiling (proposal); the ideas issue (draft) | [success-viability-effort-proposal.md](success-viability-effort-proposal.md), [ideas-issue-eb-variability-draft.md](ideas-issue-eb-variability-draft.md) |

## The maintainer's decisions on this delivery (2026-10-22), and what came back

| Item | Decision | Where |
|---|---|---|
| 1 | Spec C: amendment A0 adopted and direction A1 (the regimes kept, new data required); item 3's readings apart, as a diagnostic | [../spec-c-error-model.md](../spec-c-error-model.md) (C4, C6) |
| 2 | Option A to come back executable, nothing run | [x2f-declaration.md](x2f-declaration.md); the regime filter in `x2_study.py` (tests first, six sabotages caught); [x2f-seeds.json](x2f-seeds.json); [sizing-a.json](sizing-a.json) |
| 3 | The objectives restated by class and regime, never loosening an approved criterion; the cost's run identified | [success-viability-effort-proposal.md](success-viability-effort-proposal.md), sections 1 and 2 |
| 4 | The ceiling as an investment limit; the consumption completed, what counts said (the CI included), the ceiling reconciled with the viability rule, X7 and T4 outside | [success-viability-effort-proposal.md](success-viability-effort-proposal.md), sections 3 and 4; [ci-minutes.json](ci-minutes.json) |
| 5 | Downloads through the vulnerable environment suspended (approved); the environment declaration; the full diff of `uv.lock` after the update; the network paths outside `requests` | [dependencies-reachability.md](dependencies-reachability.md), "Revision 2"; [env-record-5294c49-lock.json](env-record-5294c49-lock.json) |
| 6 | The ideas issue opened, no implementation | [klucilla/refute#167](https://github.com/klucilla/refute/issues/167) |
| 7 | The stage's milestone: on independent data, the final configuration preserves a useful fraction of true planets as candidates, recognizes false positives and keeps its errors controlled; spec C alone does not resolve the attenuation, the candidates' identity or the aggregation | [success-viability-effort-proposal.md](success-viability-effort-proposal.md), section 6 |

## Item 1. Spec C's eligibility with the data C6 allows for a decision

Spec C's regimes are the cells × the number of observing years (C4): "2 years" is the `two_years`
and `few_train` cases, "3+ years" the `three_years` and `variability_some_years` cases. A regime is
eligible with at least 15 contributing cases (case-years with at least 30 measured realizations with
their twin). C6 lets only data never used decide: in the cells without variability that is **X2e
alone**; in the cells with variability, a replicate that does not exist yet. From
[regimes.json](regimes.json) ([scripts/regimes.py](scripts/regimes.py)):

| Data | Cell | Regime | Cases | Contributing | Case-years (excluded; none measured) | Eligible |
|---|---|---|---|---|---|---|
| X2e alone (may decide) | AR(1), no variability | 2 years | 14 | 5 | 28 (19; 10) | no |
| X2e alone (may decide) | AR(1), no variability | 3+ years | 6 | 6 | 18 (0; 0) | no |
| X2e alone (may decide) | white, no variability | 2 years | 14 | 2 | 28 (25; 9) | no |
| X2e alone (may decide) | white, no variability | 3+ years | 6 | 6 | 18 (0; 0) | no |
| X2 (informs only) | AR(1), variability | 3+ years | 20 | 20 | 60 (1; 0) | coverage yes, but X2 cannot decide |
| X2 (informs only) | white, variability | 3+ years | 20 | 20 | 60 (6; 0) | coverage yes, but X2 cannot decide |

- **No regime is eligible with the data that may decide.** X2e alone has 11 (AR(1)) and 8 (white)
  contributing cases per cell, and fewer per regime. **Spec C chooses no model now.** The minimum is
  not lowered and X2 is not added to cover the gap.
- Even pooled with X2 (which C6 does not allow), no regime of the cells without variability reaches
  15: AR(1) 12 and 12, white 5 and 12. The pooled cells reported as determined in X2e's results
  mixed the two regimes; C4 defines the regime by the number of years, so those cell-level verdicts
  are not spec C regimes.
- **The inconsistency** between C4 (its coverage note counts X2e "pooled with X2" and says "the
  cells themselves (all years together) are the regimes that can decide there") and C6 (only data
  never used decide) is the subject of [spec-c-amendment-proposal.md](spec-c-amendment-proposal.md):
  one clarifying amendment that keeps the scope, and the alternatives that change it, for the
  maintainer's choice.

## Item 2. The scope of the pooled result

- **The `ρ_2` excess of 1.21 to 1.26 is the median of the cells evaluated**, not a property of
  every regime or every case. In the pooled cells without variability, the contributing case-years
  are mostly three-year cases: AR(1) 36 of 56, white 36 of 43.
- **Per regime, separately** (descriptive medians of the contributing case-years; below 15 cases
  no interval and no verdict, so **not validated**):

| Cell | Regime | Contributing cases | Excluded case-years (none measured) | `ρ_1` | `ρ_2` | `ρ_h` | Status |
|---|---|---|---|---|---|---|---|
| AR(1), no variability (pooled) | 2 years | 12 of 28 | 36 of 56 (20) | 1.28 | 1.50 | 1.07 | not validated |
| AR(1), no variability (pooled) | 3+ years | 12 of 12 | 0 of 36 | 1.21 | 1.12 | 1.08 | not validated |
| white, no variability (pooled) | 2 years | 5 of 28 | 49 of 56 (24) | 1.30 | 1.53 | 0.94 | not validated |
| white, no variability (pooled) | 3+ years | 12 of 12 | 0 of 36 | 1.35 | 1.21 | 1.06 | not validated |
| AR(1), variability (X2) | 3+ years | 20 of 20 | 1 of 60 | 1.40 [1.33, 1.43] | 1.25 [1.15, 1.35] | 1.12 [1.08, 1.16] | interval read, X2 informs only |
| white, variability (X2) | 3+ years | 20 of 20 | 6 of 60 | 1.34 [1.29, 1.39] | 1.21 [1.16, 1.28] | 1.05 [1.02, 1.10] | interval read, X2 informs only |

- **What this does not show:** that every regime is overestimated; that no case is underestimated
  (the cell medians say nothing of single cases, and in the two-year regimes most case-years have no
  measurement at all); or that replacing the grid's maximum is safe. The two-year regimes' medians
  rest on 5 and 12 cases and on the minority of their case-years that were measured, a selection
  that may not represent the regime.
- **A regime without sufficient evidence stays unvalidated**: today that is every regime of the
  cells without variability; the variability cells' three-year regimes have intervals only from X2,
  which informs and does not decide.
- A spec C selection, when it happens, **does not replace** the later confirmation of the false
  PASS, the false FAIL and the utility of the configuration that uses it (X5, X6 and the reserve).

The X2e results' README carried two sentences that overstated this ("the excess is not specific to a
regime"; the pooled cells "determined" for spec C); they are marked there as withdrawn, with a
pointer here.

## Item 3. The maximum over the `dP` grid: a hypothesis, not a cause

The maximum over the grid of variances each estimated from a finite set of replicas is biased
upward (C1), but it may also protect against positions that really are noisier: a grid point `dP`
far from 0 places the replicas, and the transit if the period is off, where the curve may be worse.
Both readings predict `ρ_2 > 1` at `dP_0`; they differ in what is stable across realizations.

**How to tell them apart.** Each case-year has 100 independent noise realizations of the same case.
**The grid is not the same across them:** `period_grid` (`holdout.py`, from line 472) is built from
each realization's own fitted ephemeris, duration and predicted windows, so its points and their
number vary. Any comparison across realizations therefore needs **an alignment rule first**, fixed
before the reading (for example the grid point in units of the realization's own period
uncertainty, or the shift of the predicted transit time in durations), and a rule for realizations
whose grids do not cover the aligned point; and what follows is a **diagnostic decomposition**, not
an identification of the mechanism. For each realization the record holds the per-`dP` variance
estimates
`hidden_var_rep(dP)` and `train_var_rep(dP)` and their replica counts `hidden_n_rep(dP)`,
`train_n_rep(dP)` (`holdout.py`, lines 1541 to 1567), and `grid_dp`.
With `x` the aligned grid coordinate:
- **Differences that belong to the case** show as a mean over realizations
  `m(x) = mean_j v̂_j(x)` that is not flat beyond its standard error, and a position of the maximum
  that repeats across realizations.
- **Fluctuation** shows as `m(x)` flat within its standard error, a position of the maximum that
  moves from realization to realization, and a mean of the maxima `mean_j max_G v̂_j` above the
  maximum of the means `max_G m(x)` by about what the sampling noise of `v̂` (from `n_rep`) and the
  correlation of neighbouring grid points (estimated across the realizations) predict under equal
  variances.
- The two can coexist; the diagnostic split, per case-year, is `mean_j max_G v̂_j − max_G m(x)` and
  `max_G m(x) − m(x_0)`. A premium of the maximum alone does not show a bias against the true
  scatter of the measurement: that comparison is with `σ_meas`, which exists only at `dP_0`.

**What the current records allow, without a new curve:** the three readings above, per case-year
and per regime, for both decisions, from X2's and X2e's records. The records are archived on the
maintainer's Drive (zips checked by SHA-256); reading them means extracting them into `.cache`.
These readings are part of spec C's own analysis (C7), which is not authorized, so **none is done
here**; and under C6 X2's records inform only.

**What would need a new experiment (not authorized):**
- whether the measurement itself is noisier at `dP ≠ 0`: the records hold the measured depth and its
  twin only at the predicted ephemeris (`dP_0`), so `σ_meas` at other grid points needs measurements
  at fixed offsets across realizations;
- the sampling distribution of `v̂(dP)` within one realization: the records hold the robust variance
  and the count, not the replica depths themselves, so a bootstrap of the replicas needs a run that
  records them.

**Two separate questions.** Removing `m_β` (`E1.nomargin`) changes **decision 1 only**: the code
does not apply `m_β` to `e_pred,2`, so it cannot explain `ρ_2`. Replacing the grid's maximum
(`E1.dp0`, `E2.dp0`, `E2.median`) changes **both decisions** and, if positions really are noisier,
weakens a protection of both; it needs the stronger evidence.

## Item 4. "Wrong candidate" and the measurement FAIL

"Wrong candidate" is a **diagnostic class**, assigned by X2-A's declared rule
([../x2-declaration.md](../x2-declaration.md), 5.6: a measured round with its twin whose train
candidate's identity against the injection is not `same`, that is `alias` or `other`); it is not a
verdict and not a finding about the engine. The **measurement FAIL** is the FAIL rule applied to each
round's measurement with the capacity decisions **not enforced**, as X2 and X2e declared: the
calibration measurement bypasses the gates, so these FAIL are not the engine's false FAIL.

From the rows (each round's decisions as recorded at the lot's configuration, `b = s = 0`, so the
threshold is `min_snr`; not the full engine, which uses the calibrated `b` and `s`, spec B's
aggregation over a target's rounds and every other gate):

| Cell | Measurement FAIL | Passing both recorded capacity decisions | Wrong candidate | Wrong candidate passing both |
|---|---|---|---|---|
| AR(1), no variability (pooled) | 19 | 3 | 2 | 0 |
| white, no variability (pooled) | 94 | 55 | 72 | 51 |
| AR(1), variability (X2) | 138 | 30 | 58 | 21 |
| white, variability (X2) | 76 | 6 | 9 | 0 |

- **The 94 measurement FAIL of `white, no variability` are not 94 engine false FAIL**: 39 of them
  did not pass both capacity decisions as recorded; of the 72 wrong candidates, 51 passed both
  recorded decisions. Whether any of these would end as a false FAIL of a target depends on the
  calibrated thresholds, the other gates and spec B's aggregation, which only X5 and X6 measure.
- The distinction is recorded in X2's and X2e's results.

## Items 7 and 8

The attenuation front stays its own investigation, with acceptance before code
([../attenuation-front.md](../attenuation-front.md)); nothing of it is run or implemented. The
historical FAIL is preserved; the final configuration must be frozen and pass an independent
confirmation with new data; X3 waits.

## The decisions pending (short)

1. **Spec C, C4/C6:** approve the clarifying amendment (A0), or choose a scope alternative (A1 to A3)
   ([spec-c-amendment-proposal.md](spec-c-amendment-proposal.md)).
2. **The prospective package:** which regimes it covers (option A, B or C), the precision target,
   the regime filter in the lot code, and its authorization; the confirmation lot's drand round
   later ([prospective-package-proposal.md](prospective-package-proposal.md)).
3. **Dependencies:** approve the early correction (no download through `requests` until certifi is
   updated; the updates on their 7-day dates, or an explicit exception), and the frozen comparison
   environment ([dependencies-reachability.md](dependencies-reachability.md)).
4. **Success and effort:** the joint objectives' numbers, the cumulative ceiling, and the viability
   check's place before the package and before X5
   ([success-viability-effort-proposal.md](success-viability-effort-proposal.md)).
5. **The ideas issue** on eclipsing binaries and variability: open it as drafted, change it, or not
   ([ideas-issue-eb-variability-draft.md](ideas-issue-eb-variability-draft.md)).
6. **Item 3's readings from the archived records:** whether they are done inside spec C's analysis
   when it is authorized, or apart.

## Scripts and outputs

[scripts/regimes.py](scripts/regimes.py) → [regimes.json](regimes.json) (items 1, 2 and 4);
[scripts/sizing.py](scripts/sizing.py) → [sizing.json](sizing.json) (item 5's planning arithmetic).
Both read committed files only.
