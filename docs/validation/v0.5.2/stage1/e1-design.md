# v0.5.2 stage 1, experiment E1: the detrending mask (frozen before it runs)

Development seeds only: `int(SHA-256("refute-v052-dev:e1:<noise>:<kind>:<i>")[:16], 16)`. No
acceptance or confirmation seed; nothing in `src/` changes (the variants are patches inside the
experiment's own processes). It decides nothing about any target. `method_status: not_validated`.
Script: [e1_mask.py](e1_mask.py), output `e1-mask.json`.

**Question.** In the version-3 pipeline the real event windows are masked out of the detrending and
the pseudo-windows that give their error are not. Is that asymmetry the cause of the pull standard
deviation of 1.10 to 1.21 in correlated and long noise (`docs/validation/v0.5.1/feasibility/strategy/README.md`)?

**The curves.** The construction of A0.1 and A0.2 (`acceptance/a0.py`): `common.noise_curve` (2
sectors, 1,000 ppm white), a transit-free candidate of duration 0.10 d and period log-uniform in 1
to 10 d, the coverage kinds `full` and `partial`. Noise: white, correlated, long, correlated_trend.
300 curves per noise and kind.

**Frozen details.** The real mask: `transit_mask_half_width_durations` = 1.0, half-width T = 0.10 d
about each event centre (as the pipeline). The pseudo-window grid: A0's (`2 h` = 0.40 d, from each
sector's first cadence of the series the arm measures). A pseudo-window's mask: the same half-width T
about its centre. The detrending: the plan's, unchanged (window 1.0 d, knots every 0.1 d, quadratic
blend, clip 3 sigma, sector-wide upper clip at 5 sigma, segment gap 0.5 d). Other real masks stay in
every masked detrending. Coverage and strata: A0's. The measurements: `events.per_event_depths` and
`a0.box_measure`, unchanged.

**Four arms, on the same raw curve.**

| Arm | Real windows measured on | Pseudo-windows measured on |
|---|---|---|
| A, as built | detrending with the real mask | the same series |
| B, no mask | detrending with no mask | the same series |
| C, crossover | detrending with no mask | detrendings masking the pseudo-windows (no real mask) |
| D, both masked | detrending with the real mask | detrendings masking the pseudo-windows and the real mask |

**The reference and the comb.** The reference masks one pseudo-window at a time and takes that
window's value from that detrending (per sector; a sector's detrending does not depend on the other
sector's cadences). The comb masks the windows whose grid index is `j` modulo `J`, for each `j`, and
takes each window's value from its own comb. **J = 4**: the windows of a comb are 1.6 d apart, and a
mask's local influence reaches about 0.7 d from its centre (knots 0.1 d apart, each fitted on a 1.0 d
window, blended). J establishes local separation only: the sector-wide clipping scale depends on all
unmasked cadences, so the complete procedure's equivalence is established by the reference check.

**The reference check, for each construction (arm C or D x noise x kind, all 16), on 20 curves
each.** Both collections are built with `a0.pseudo_windows` (sector, segment, grid index, coverage,
stratum), and the errors with `a0.stratum_error` per sector and stratum. A construction is
*established* only if: (i) pooling all its windows measured in both, the root mean square of
(comb - reference) is at most 10 % of the reference windows' standard deviation; (ii) the mean of
`|error_comb / error_reference - 1|` over the sector-strata where both exist is at most 2 %; (iii)
the sector-strata where only one has an error (`n_eff < 10`, or no windows) are at most 1 % of the
total. Windows present in only one are counted and reported. An arm in a construction not established
is reported as not established.

**The measure.** For each arm, noise and kind, every event weighted equally: `Var(d)`, `mean(e^2)`
(A0's error, `max(model, empirical)`), the depth bias `mean(d)`, the availability (the fraction of
events with an error), and `rho = sqrt(Var(d) / mean(e^2))`. Each with a 95 % interval from 500
bootstrap replicates over whole curves, **the same scheduled curves resampled across arms** (curves
with no retained event kept), and each arm's paired contrast against arm A with its interval; the
availability's numerator and denominator are resampled the same way. A statistic is undefined with
fewer than two events or a non-positive denominator; an interval is undefined when more than 1 % of
its replicates are, and a cell needs at least 100 contributing curves for each arm. Undefined
quantities are written as null, and any of them in a decision statistic makes the result NOT
ESTABLISHED, with the affected arm and cell named. When the retention differs, `rho` on the events measured in both arms is given beside it. Also the group
statistics (`box_odd`, `box_even`, `box_diff`) for `full`.

**The decision rule, fixed now, a descriptive stage-1 rule.** On a complete run (every scheduled unit
present once, none failed, finite inputs, every construction established), the *prespecified
development pattern is observed* if, in each of correlated, long and correlated_trend (`full` and
`partial`), arm D's `rho` lies in [0.95, 1.05], and in white noise `|rho_D - rho_A|` is at most 0.05.
Otherwise the result is NOT ESTABLISHED (with its reasons) or the pattern is not observed. The
crossover is reported, and its direction is read as evidence; it is not required as a fixed pattern.
The rule uses point estimates; an observed pattern does not establish population equivalence,
calibrated pulls or a unique causal mechanism, and a pattern not observed does not show the mask has
no role. The result goes to the stop of stage 1.

**Identity of the run.** Records carry a fingerprint of this design, the script, the runner files,
the code hash, the resolved plan, the constants and the versions; they live in a folder named after
it, and a record of another fingerprint is refused. Earlier smoke records stay apart.

**Cost.** At most 2.5 processor-hours (a probe of the first units first). Runs through
`scripts/launch_affinity.ps1`, resumable.
