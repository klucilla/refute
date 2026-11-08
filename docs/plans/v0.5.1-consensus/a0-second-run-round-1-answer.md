## Verdict: WEAKENED

The correction appears to build the same flattened series as `pipeline.attack_candidate` for the **same raw curve, plan, and candidate**, with corrections inactive as this plan specifies. But the required proof is incomplete: it does not spy on `rednoise.event_noise`, one of the four functions named in the decision and the first-run defect. I would not start the run until that proof gap is closed and the test is committed.

## Objections

1. **High, the proof does not cover `event_noise`.**  
   **Evidence:** `_Spies` patches `per_event_depths`, `empirical_events`, and `check_odd_even`, but not `rednoise.event_noise`. The test therefore cannot establish that both the corrected runner and the pipeline pass the expected series to the noise estimator, even though the recorded cause explicitly includes that function.

   **Exact change required:** Spy on `rednoise.event_noise` in both runner and pipeline calls, include its received light curve in the byte comparisons, and check that the old raw-series behavior fails for that call too. Keep the test in the suite and commit it before the run.

2. **Medium, the equivalence claim needs a scope boundary.**  
   **Evidence:** `_flat` matches the pipeline’s mask, correction handling, and detrend for its input candidate. But `attack_candidate` then computes `sigma`, calls `finalize_candidate`, and uses the refined candidate for later measurements. The runner uses the declared candidate and does not reproduce those later steps. The test compares series bytes, not candidate, cadence, sigma, or downstream measurement equivalence.

   **Exact change required:** Keep the declared ephemeris if the acceptance target is calibration conditional on that predetermined candidate, as revision 3 specifies. State clearly that the proof establishes **series construction for a fixed candidate**, not end-to-end equivalence to the pipeline’s refined-candidate measurements. If the target is end-to-end equivalence, the runner and test would need to use and verify `finalize_candidate`’s result, which would be a broader change than the stated correction.

## Other checks

- `_flat` matches the active pipeline’s flattening path for the current inactive-corrections plan. The runner applies it after the scenario cuts and injections, consistent with the pipeline receiving the resulting curve.
- The pipeline’s A0 calls in `v05_tests` use `flat` and `sigma=None` for their event measurements; the runner’s `_events` likewise passes the flattened curve and `None`. The fixed two-minute cadence matches the plan’s configured cadence.
- A0.8’s noise-free truth flattened before the same box estimator is consistent with defining truth through the full estimator path. It measures the signal after the same preprocessing used for the noisy curve.
- I found no threshold, band, acceptance-row, or acceptance-text change in the shown diff. The seed label, run name, output paths, and design note are consistent with the second-run procedure.
- The procedure is otherwise fair as stated. Pass **cumulative development hours used so far** to each section as it begins, updating the initial ~36.4 hours with completed sections. The projection and stop account for failed Python units because `_timed` records their CPU time.

I made no changes and ran no tests or acceptance units.

