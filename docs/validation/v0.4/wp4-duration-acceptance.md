# v0.4 WP4: result of the acceptance of `trapezoid-least-squares-1` (2026-10-29)

The method was specified before its code ([v0.4-duration-method.md](../../plans/v0.4-duration-method.md),
commit `8fe848f`) and implemented as written (`src/refute/packs/tess/duration.py`). Case 4.1 of
[v0.4-acceptance.md](../../plans/v0.4-acceptance.md) was run once, on the fixed set (SNR 10, 20
and 40; seeds 0 to 199), by `tests/test_v04_duration.py`.

**Result: FAIL.** The 68 % interval covers the true duration too rarely at SNR 20 and 40.

| SNR | Estimable (of 200) | Covered | Coverage | Band (binomial 95 %) | Std of (T_fit - T_true) / err |
|---|---|---|---|---|---|
| 10 | 197 | 124 | 0.629 | 0.612 to 0.741 | 1.27 |
| 20 | 199 | 108 | 0.543 | 0.611 to 0.739 | 1.41 |
| 40 | 200 | 110 | 0.550 | 0.612 to 0.741 | 1.48 |

Diagnosis, from the same trials and not used to change anything: the fitted duration has no
appreciable bias (mean normalized error 0.02 and 0.10 at SNR 20 and 40), and the reduced
chi-square is 1.00; the covariance error is too small by a factor of about 1.4 to 1.5. A
likely cause is that the trapezoid's likelihood is not smooth in the duration at the scale of
one cadence (a cadence enters or leaves a ramp), so the local Jacobian does not describe its
curvature. This is a hypothesis, not tested.

**What follows.** Nothing is tuned on this set:

- The method is recorded as **not accepted**. The exporter writes no duration uncertainty from
  it: `duration_err_hours` is absent with the reason "the method did not pass its acceptance"
  (`refute.packs.tess.duration.METHOD_ACCEPTED = False`). The test of case 4.1 is kept, marked
  as an expected failure (strict), so that it stays visible and a pass would be noticed.
- A different method, or a change to this one, needs the maintainer's decision, a new
  specification written before its code, and a **new** set of seeds, never this one.
- Phase acceptance criterion 8 ("duration uncertainty with its method, or a justified
  absence") is met for now only by the justified absence; the decision is the maintainer's.

**The maintainer's decision (2026-10-29): ROADMAP v0.4 amendment 5.** In the pilot the
duration is exported without an uncertainty, with the justified absence that cites this
method as not accepted (coverage 0.54 and 0.55 at SNR 20 and 40, against a band of 0.61 to
0.74). No other method is tried in this phase. This FAIL stays recorded and visible; issue
#176 stays open.
