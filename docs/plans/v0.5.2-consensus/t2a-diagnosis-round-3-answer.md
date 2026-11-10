1. **Applied, correct.** [forecast_t2a_diagnosis.py:390](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_t2a_diagnosis.py:390) retains gauntlet, sensitivity and final tests, preserving `aperture_depth` before deferral.

2. **Partially applied.** [forecast_t2a_diagnosis.py:849](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_t2a_diagnosis.py:849): sensitivity refusals now receive anomaly auditing, but FAIL still becomes (e) before anomalies are considered. **Fix:** retain anomalies independently for every status; count one as a (c) blocker only after establishing that it explains the loss.

3. **Partially applied; expected response remains unsafe.** [forecast_t2a_diagnosis.py:289](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_t2a_diagnosis.py:289) uses a uniform grid rather than observed cadences, and omits baseline subtraction, preprocessing response and the host’s existing signal. A synthetic sampling probe produced expected depth 0.001692 where every observed cadence had zero injected deficit, falsely triggering an anomaly. **Fix:** evaluate the incremental response on the actual cadences through the measurement operator. Until validated, report discrepancies as unresolved audit warnings rather than explanatory code defects.

4. **Partially applied.** [forecast_t2a_diagnosis.py:794](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_t2a_diagnosis.py:794) correctly selects the sub-check’s error series and retains both measurements. However, line 790 still treats common epochs as evidence of a defect. Production also reaches that branch when the common-event weighted depth is legitimately nonpositive. **Fix:** recompute and report that weighted depth; distinguish nonpositive measurements from missing or inconsistent computation.

5. **Applied, correct.** [forecast_t2a_diagnosis.py:572](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_t2a_diagnosis.py:572): preflight now refuses before dispatch. Current records pass 80/51/48; T2a’s fingerprint remains `8f5bbe58347af71e`.

6. **Partially applied; instrumentation stop is still wrong.** [forecast_t2a_diagnosis.py:508](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_t2a_diagnosis.py:508) requires six flags regardless of type. One instrumentation quarantine therefore permits further injections, contrary to the declared immediate stop. Classification exceptions likewise become ordinary flags. **Fix:** use a separate binding stop sentinel for any instrumentation/classification failure; reserve the six-loss threshold for causal (c) findings.

7. **Applied, correct within the driver’s accounting model.** [forecast_t2a_diagnosis.py:606](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_t2a_diagnosis.py:606): both parts are counted, same-attempt spending is handled correctly, overshoot headroom is reserved, and smokes use enforced accounting.

8. **Applied, correct.** [forecast_t2a_diagnosis.py:468](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_t2a_diagnosis.py:468) attaches collections before execution; the battery’s `finally` retains captured tests, and quarantine checks instrumentation even on ERROR.

9. **Applied, correct.** [forecast_t2a_diagnosis.py:256](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_t2a_diagnosis.py:256): event lists remain lossless and `n_events` matches `A0Depth`.

10. **New blocking defect: incorrect three-error boundary.** [forecast_t2a_diagnosis.py:322](/C:/Projetos/refute/docs/validation/v0.5.2/stage2/forecast_t2a_diagnosis.py:322) measures distance from the expected mean, not from the half-to-twice interval. Expected 1, measured 0.49, error 0.16 triggers despite being only **0.0625 errors** outside the interval. **Fix:** require `mean < 0.5*expected - 3*error` or `mean > 2*expected + 3*error`, with explicit handling of nonpositive expectations.

**Verdict: REFUTED as a diagnosis design in its current form.**