## Verdict: WEAKENED

The round-2 objection is resolved. `box_measure` and the cadence-index check now use the same half-open window, and `pseudo_windows` excludes the exact `2h` boundary. The matched window also remains narrower than the grid spacing.

I found two blockers to a fair, interpretable acceptance run, plus two corrections needed in the A0.6 specification and cost estimate.

## Objections

1. **Critical, the freeze check will reject the reviewed source.** `common.py` pins the code hash to commit `063ac1f`, and `check_freeze()` compares that hash against the current source tree. The hash covers every file under `src/`; `src/refute/packs/tess/a0.py` is modified in this working tree. The runner checks the freeze before constructing units or acceptance seeds, so it cannot proceed with this change.  
   **Exact change required:** Freeze and record the hash of the final A0 source, including the endpoint fix, before the acceptance run. Keep that recorded hash fixed for the run. See [common.py](C:/Projetos/refute/docs/validation/v0.5.1/acceptance/common.py:42) and [codehash.py](C:/Projetos/refute/src/refute/core/codehash.py:6).

2. **High, the runner records measurements but does not decide acceptance.** Its entry point calls `run_section()` and writes unit records, but the runner has no reducer that selects the first 400 pulls per stratum and statistic, computes the required bands, or classifies rows and sabotages. It also does not call `write_result()`. In particular, absent group errors and sparse A0.8 branches need explicit `NOT DECIDABLE` or diagnostic outcomes; without a reducer, the recorded pulls alone cannot show whether a row passed.  
   **Exact change required:** Add a deterministic per-section evaluator that reports the sample count, bands and outcome for each required stratum, statistic and branch. Treat unavailable errors as diagnostic or `NOT DECIDABLE`, never as passing observations. The plan requires each row to be reported in each stratum, and makes statistics relying on failed calibration diagnostic. See [a0.py](C:/Projetos/refute/docs/validation/v0.5.1/acceptance/a0.py:835) and the acceptance requirements at [v0.5.1-acceptance.md](C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:165).

3. **Medium, A0.6’s candidate periods do not match its measured lags.** `unit_a06()` draws a random period through `_candidate()`, then measures at lags calculated from the fixed periods 1, 3 and 10 days. The pseudo-windows are excluded around the random ephemeris, so these are not measurements at the specified candidate-period lags.  
   **Exact change required:** Schedule A0.6 candidates at periods 1, 3 and 10 days, and record the period and corresponding lag with each result. See [a0.py](C:/Projetos/refute/docs/validation/v0.5.1/acceptance/a0.py:549) and the A0.6 row at [v0.5.1-acceptance.md](C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:198).

4. **Medium, the A0.5 cost in the design is half the runner’s scheduled workload.** The schedule yields 252,000 units: 108,000 each for p1 and p2, plus 36,000 for p3. The design states 126,000 units and 7.4 processor-hours. At the reported 0.21 seconds per unit, this schedule is about 14.7 hours, putting the total estimate near 55 hours instead of 48. The scheduled 400 units for each pattern, spacing, noise, coverage kind and sector count do match the acceptance grid; the discrepancy is in the estimate.  
   **Exact change required:** Correct the A0.5 unit count and total processor-hour estimate in the design before the run. The common projection uses actual scheduled units, but the design should describe the workload accurately. See [a0.py](C:/Projetos/refute/docs/validation/v0.5.1/acceptance/a0.py:753) and [a0-design.md](C:/Projetos/refute/.cache/v051/accept/a0-design.md:141).

## Development smoke interpretation

The finding for periods below about 1.5 days is consistent with the adopted rule: when the required lag correlation cannot be estimated, `group_variance` returns `None` and the version-3 odd/even result is `INCONCLUSIVE` for insufficient sensitivity. That is a sensitivity limit to report, not a reason to change the rule. A0.5 at P = 1 day must remain diagnostic or `NOT DECIDABLE` where it lacks calibrated errors; it must not be counted as a pass. The design notes this, but the runner still needs the explicit outcome handling described above.

The coverage kinds are a reasonable way to produce computed partial and minimal strata with enough pseudo-windows for calibration: evaluation uses measured strata rather than declared kinds. The small-period limitation remains visible in the acceptance outcome. I made no changes and ran no scripts or tests.

