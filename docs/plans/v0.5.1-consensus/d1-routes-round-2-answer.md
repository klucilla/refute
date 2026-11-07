## Verdict: **WEAKENED**

Claude’s main conclusion is supported as a **development finding**: the separation comes from transit geometry, and with both TIC radius and mass errors the idealized EB2 estimate is above the D1 allowance. That supports keeping the new route diagnostic and waiting for the measured C1′ result. It does not prove that D1 is infeasible.

The report’s values match the tables: at the TIC’s 5% errors, radius-only estimates are 4.57 EB1 and 7.90 EB2 survivors; with radius and mass both free they are 7.55 and 12.32. The C1′ projection halves 388 and 372 eligible cases to 194 and 186, respectively. These are estimates from the oracle’s survival proxy, not observed survivor counts. The implementation uses \(1-\Phi(d-1.645)\), with \(d\) the Mahalanobis distance between noiseless curves. That is an optimistic scalar proxy, not a measured full-chain pass probability or Wilson-bound result. See the [feasibility report](C:/Projetos/refute/docs/validation/v0.5.1/feasibility/d1-routes.json) and [route script](C:/Projetos/refute/docs/validation/v0.5.1/feasibility/d1_routes.py).

## Objections

1. **Important, the oracle result needs a tighter boundary.** Evidence: the 12.32 EB2 estimate uses the proxy \(1-\Phi(d-1.645)\), then scales to 186 eligible cases. It is not an observed count or a calibrated acceptance result. **Exact change:** describe “above the D1 bound” as a forecast under the stated oracle proxy. Keep any infeasibility conclusion conditional on the actual C1′ acceptance result and joint D2 evidence.

2. **Important, the high-quantile flags are not all zero.** Evidence: at the reported planet quantiles, raw-score `dchi2` flags 1/75 correlated EB2 cases and 1/73 correlated P cases; covariance-scored `dchi2_cov` flags 1/59 white PG cases. The quantile is pooled over P and PG and rests on about one tail observation. **Exact change:** replace any unqualified “flags none” statement with the per-group fractions, and keep both quantiles exploratory, not calibrated thresholds.

3. **Important, the PG tail’s cause is unresolved.** Evidence: the summary reports a 90th percentile of 64.25 and 30.5% flagged at 9 for white PG, but the route records do not retain the generator’s true impact parameter or enough fit diagnostics to attribute the tail. The largest recorded PG case has a fitted impact parameter of about 0.834, which does not identify the cause. **Exact change:** do not assign a cause yet. If revisited, retain truth geometry, fit convergence and bound status, and residual diagnostics before proposing how to handle the tail.

4. **Important, “covariance-aware” describes scoring, not fitting.** Evidence: `geometry_dchi2` fits both models with white weights, then computes `dchi2_cov` by rescoring those residuals under the AR(1) covariance. **Exact change:** call it covariance-scored, and require covariance-aware fitting plus full-chain calibration before treating it as a route candidate.

5. **Important, the authorized cost was exceeded.** Evidence: the report records 12.04 processor-hours against the 10-hour cap in amendment 10, item 3. **Exact change:** retain the overrun in the record and do not measure another candidate route within this round. The existing evidence supports no additional C1 measurement: BEER signals were not generated, identical eclipse shapes provide no designed asymmetry signal, and the geometry route was already measured.

## Recommendation to the maintainer

Keep D1 for EB1 and EB2 in the planned C1′ measurement and report its measured results. Add no new decisive test in v0.5.1; retain transit-geometry consistency only as a weakened, non-fatal diagnostic pending the listed calibration and tail work. If measured D1 fails, the joint infeasibility path with D2 is reasonable, but cite the oracle result as supporting forecast evidence, not proof. The 12.04-hour overrun leaves no room for another route measurement in this round.

