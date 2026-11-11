# v0.5.3 stage B, B0: the stop report

**For the maintainer's decision; nothing is decided here.** The maintainer's decision of 2026-11-11
(#217, comment 6799266241) approved stage B with B0 first, as D1's gate. B0 was to look for a new
route that separates EB1/EB2 from the planets, grazing PG included. If no route reaches D1's target
on development data, B0 stops and brings the result, and D2, D4 and T2a do not start without a new
approval. **This is that stop.** `method_status: not_validated`. Development data only. Nothing in
`src/` or in T2a's fingerprint changed, and no confirmation data was drawn or used.

## What ran

| Step | Record | CPU-h |
|---|---|---|
| Literature and inventory of routes | [design, section 2](../../../plans/v0.5.3-stageB0-design.md); [sources](../../../plans/sources/v0.5.3-stageB0-literature-2026-11-11.md) | 0 |
| Two smoke runs of the bound (index 100000, outside the measured set) | `ledger.json`, charges | 0.008 |
| D1's information bound, 800 new development binaries | [`d1_bound.py`](d1_bound.py), [`d1-bound.json`](d1-bound.json) | 2.448 |
| The summary | `ledger.json`, charge | 0.008 |

**Order of events.** The design, its scripts and the decision rule went through Codex's review in
three rounds (`WEAKENED`, `WEAKENED`, `SURVIVED`). They were committed and pushed in `b00a78d`, and
the exact procedure was posted on #217 (comment 6799994466) before the run. The run was complete:
80 shards, 0 errors, and 5 generation failures, which are counted in the projection's denominator.

## The inventory (the design's section 2)

The literature's routes reduce to the channels below, all inside the light curve once the catalog
star is given:

- the odd/even depths (Robovetter A.4.1.4; LEO-Vetter IV.4);
- the secondary at phase 0.5 (the Robovetter and LEO-Vetter MS tests);
- the duration, ingress and shape against the star's density (Seager and Mallen-Ornelas 2003;
  Morton 2012; the V shape).

C1 does not generate the other channels:

- ellipsoidal variation, beaming and reflection (SWEET; Faigler and Mazeh 2011);
- a centroid or halo signal, since the binaries are on target and have the same pixel model as a
  planet;
- better stellar parameters.

The candidate's size is a different null. C1's planets and binaries share the SNR rule for depth,
and the binaries' depth quantiles are in `d1-bound.json`. So the full-likelihood oracle (v0.5.1's,
imported unchanged) bounds every route that tests the planet hypothesis on the light curve, under
the stated assumptions. Those assumptions are stated as requirements, not shown:

- the per-planet level, over a null whose star is anywhere in the whole ±3-sigma box of its
  catalog radius and mass errors;
- a selection (eligibility and the found period, from the same noisy curve) that leaves the noise
  along the binary-to-planet difference unchanged;
- the forecast's eligibility rule standing for C1's gate.

## The bound (`d1-bound.json`, fingerprint `cc407aecdd294028`)

Eligible counts: 381 of 400 EB1 (246 folded at half the true period) and 373 of 400 EB2 (349
folded). Projected to C1' size, that is 190 EB1 and 186 EB2. D1's allowance at the projection is at
most **10** SURVIVED in each family (the Wilson 95 % upper end at most 0.10).

The table gives the expected non-rejected binaries at the projection. Each binary's non-rejection
is `Phi(z_alpha - d)`: the most powerful level-`alpha` test of its nearest planet still fails to
reject it with that probability. In brackets: the median and 95th-percentile probability, over
bootstrap cohorts, that the count is at most the allowance.

| Level `alpha` | EB1, catalog star | EB1, star known | EB2, catalog star | EB2, star known |
|---|---|---|---|---|
| 0.05 | 14.1 [0.08, 0.60] | 4.6 [1.00, 1.00] | 12.5 [0.25, 0.67] | 4.1 [1.00, 1.00] |
| 0.01 | 22.5 [0.00, 0.005] | 8.6 [0.85, 1.00] | 24.8 [0.00, 0.001] | 7.9 [0.92, 1.00] |
| **0.0027 (primary)** | **29.2 [0.00, 0.00]** | **11.9 [0.28, 0.94]** | **35.5 [0.00, 0.00]** | **11.2 [0.39, 0.95]** |
| 0.00135 | 32.6 [0.00, 0.00] | 13.6 [0.08, 0.76] | 41.1 [0.00, 0.00] | 12.9 [0.15, 0.86] |

**Where the non-rejected binaries are.** At 0.0027 with the catalog star:

- EB1: the non-rejection fraction is 0.217 among folded binaries and 0.037 among unfolded ones;
- EB2: it is 0.204 among folded binaries (almost all of them are folded);
- the median distance is 6.26 (EB1) and 4.88 (EB2) with the catalog star, against 9.08 and 9.34
  with the star known.

Most of the separation that remains is in the transit's geometry against the star's density, and
the catalog's 5 % radius and mass errors remove much of it. This matches v0.5.1's decomposition.

## The outcome: (C), by the rule fixed before the run (the design's section 4)

- **Not (D):** no error, at least 150 eligible per family, and every distance finite.
- **Not (A):** with the star known, the expected counts (11.9 and 11.2) are above the allowance of
  10. But the median cohort's probability of meeting it (0.28 and 0.39) is not below 0.05.
- **Not (B):** with the catalog star, neither family has room (29.2 and 35.5 against 10).
- **So (C):** the bound does not settle the question under the catalog star. Under the rule, B0
  stops and brings the bound, with no infeasibility claim and no claim about what would solve it.
  **No route was built**, because a route needs (B). **No draft infeasibility record is written**,
  because one needs (A).

What the figures say, within the bound's assumptions:

- With the information C1 gives a test (the light curve and a catalog star with 5 % errors), even
  the oracle leaves an expected 29 EB1 and 36 EB2 non-rejected at the primary level, about three
  times D1's allowance. At the most permissive level reported, 0.05, it still leaves 14 and 12.5.
- With the star known exactly, the expected counts come down to near the allowance.
- These are bounds on separation only. They are not counts of SURVIVED. A binary held INCONCLUSIVE
  does not survive under D1's frozen rule. The illustrative expected excess over the allowance, as
  a fraction of the projection, is 0.101 (EB1) and 0.137 (EB2) with the catalog star. That is not a
  proven required share, and nothing about it is decided.

**D2, D4 and T2a (B1) did not start** and do not start without a new approval (the maintainer's
decision, B0).

## Consumption

| Cap | Used | B0 sub-cap | Stage B cap |
|---|---|---|---|
| CPU-h | 2.464 (the bound 2.448, smokes and summary 0.016) | 30 | 150 |
| Review tokens (Codex, uncached input plus output; the rule of 2026-11-11) | 186,883 for the design's review, plus the end-of-B0 review: 76,514 after its round 1, so 263,397 then, and its final figure is in the consensus record | 1.5 M (stop at 1.2 M) | 4.5 M (stop at 3.6 M) |
| Agent-days (wall clock over 8-hour days, since 14:45Z) | about 0.11 at the summary | 2 | 8 |

No cap or sub-cap was reached. The independent review sessions used 0 tokens.
