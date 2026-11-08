## Verdict: WEAKENED

The design covers the main A0 rows and names the expected sabotage cases. I found gaps that could produce incorrect exclusions, an untested version of the battery’s estimator, or a run that reads acceptance seeds before verifying the freeze. The runner at `docs/validation/v0.5.1/acceptance/a0.py` is not present in the checkout, so I could review its design and the cited implementation modules, but not confirm how the rows and sabotages are wired together.

## Numbered objections

1. **Critical, acceptance seeds are not guarded at the point of use.**  
   **Evidence:** [`common.py`](</C:/Projetos/refute/docs/validation/v0.5.1/acceptance/common.py:53>) exposes `accept_seed()` without a freeze check. The check occurs later inside `run_section()` ([lines 170–178](</C:/Projetos/refute/docs/validation/v0.5.1/acceptance/common.py:170>)). The design calls for acceptance-seed-derived units, but does not specify that the freeze is checked before constructing them ([design](</C:/Projetos/refute/.cache/v051/accept/a0-design.md:8>)).  
   **Exact change required:** Make the runner call `check_freeze()` before generating any acceptance seed or seed-dependent unit, and keep all seed generation after that check. The missing runner prevents verifying that this ordering is implemented.

2. **High, the code approximates cadence overlap with center distance.**  
   **Evidence:** The acceptance text requires pseudo-windows that share no *cadences* with real or conditionally excluded phase-0.5 windows ([acceptance](</C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:102>), [lines 105–114](</C:/Projetos/refute/docs/plans/v0.5.1-acceptance.md:105>)). `pseudo_windows()` instead excludes based on center distance (`< 2h`) ([`a0.py`](</C:/Projetos/refute/src/refute/packs/tess/a0.py:100>), [lines 103–110](</C:/Projetos/refute/src/refute/packs/tess/a0.py:103>)). Across gaps or irregular sampling, center distance does not establish whether the two windows share a cadence. The A0.3 check could repeat the same approximation and pass while violating the stated rule.  
   **Exact change required:** Determine overlap from the actual cadence indices in each event and phase-0.5 window. Have A0.3 independently verify those index sets against the kept pseudo-windows.

3. **High, A0.2’s odd/even case does not test the battery’s actual event estimator.**  
   **Evidence:** The design specifies “box per-event depths” and calls that the battery path ([design](</C:/Projetos/refute/.cache/v051/accept/a0-design.md:25>)). But `check_odd_even()` measures events and pseudo-windows using a fitted trapezoid matched estimator ([`battery_v51.py`](</C:/Projetos/refute/src/refute/packs/tess/battery_v51.py:297>), [lines 302–314](</C:/Projetos/refute/src/refute/packs/tess/battery_v51.py:302>)); `a0.empirical_events()` uses `box_measure()` ([`a0.py`](</C:/Projetos/refute/src/refute/packs/tess/a0.py:310>), [lines 336–361](</C:/Projetos/refute/src/refute/packs/tess/a0.py:336>)).  
   **Exact change required:** Make A0.2’s odd/even pulls use the same fitted-shape measurement path as `check_odd_even()`, including its event and pseudo-window measurements, or explicitly narrow the acceptance claim to the box estimator and add a separate calibration for the matched estimator.

4. **High, missing same-stratum lag correlations can be treated as zero.**  
   **Evidence:** `stratum_error()` estimates each autocorrelation from pairs exactly `k` grid steps apart ([`a0.py`](</C:/Projetos/refute/src/refute/packs/tess/a0.py:187>), [lines 190–198](</C:/Projetos/refute/src/refute/packs/tess/a0.py:190>)). `effective_count()` treats a missing correlation as zero ([lines 175–184](</C:/Projetos/refute/src/refute/packs/tess/a0.py:175>)). In a sparse coverage stratum, windows can exist without any same-stratum pairs at a given grid lag. Treating that unavailable estimate as zero can inflate `n_eff`, allowing an event to be measured with insufficient evidence of its dependence structure.  
   **Exact change required:** Define the per-event `r_k` estimator to match the acceptance wording, pooling valid within-segment lag pairs in the stratum’s time-ordered series. If a required lag cannot be estimated under that definition, do not silently substitute zero; specify and report the consequence, then verify calibration for that rule.

5. **High, A0.8’s branch decision needs an explicit guarantee that it receives the A0 errors used to set injection depths.**  
   **Evidence:** The design sets secondary depths from the pre-injection A0 phase-0.5 error, then delegates the branch to `check_secondary_two_sided()` ([design](</C:/Projetos/refute/.cache/v051/accept/a0-design.md:77>)). That function computes its group error from the `EventDepths.errors` it receives ([`battery_v5.py`](</C:/Projetos/refute/src/refute/packs/tess/battery_v5.py:63>), [lines 66–79](</C:/Projetos/refute/src/refute/packs/tess/battery_v5.py:66>)). The design does not state that those inputs are A0-adjusted before the call.  
   **Exact change required:** Specify that the pre-injection phase-0.5 event errors passed to the branch check are the A0 errors, and record the exact combined error used for each injection and branch decision.

6. **Medium, the projection and stop can undercount failed units.**  
   **Evidence:** Worker exceptions are recorded with `cpu_seconds: 0.0`; projection and elapsed totals sum that field ([`common.py`](</C:/Projetos/refute/docs/validation/v0.5.1/acceptance/common.py:197>), [lines 206–230](</C:/Projetos/refute/docs/validation/v0.5.1/acceptance/common.py:206>)). If a unit consumes substantial CPU before failing, that time is omitted from the 5% projection and the 1.5× stop.  
   **Exact change required:** Measure and record CPU time for failed units too, and include it in both the projection and stop calculation. Keep failed units in the denominator as the code already does.

I did not run the runner or tests, and made no file changes.

