# The A0 acceptance runner: design (revision 4, the second run)

Section "A0" of docs/plans/v0.5.1-acceptance.md (rows A0.1 to A0.8, the sabotage rows; A0.9 runs
with the combined gates). Runner: docs/validation/v0.5.1/acceptance/a0.py on common.py (freeze
check, seeds, bands, noise models, the 5 % projection and the 1.5-times stop). Every choice below
is one the text leaves open, fixed before any acceptance unit runs; nothing is tuned after a run.
Revision 1 was reviewed by Codex in two rounds and revision 3 with the code in a third
(docs/plans/v0.5.1-consensus/a0-runner-round-*-answer.md); the changes since revision 1 are marked
**[r3]**, with their reason.

**Common.** Seeds `refute-v051-accept:a0-<row>-<noise>-<kind>-<sectors>:<i>`, refused unless the
process checked the freeze first. Curves: `common.noise_curve` (white 1000 ppm; correlated AR(1),
half the white level, tau 1 h; long AR(1), half the white level, tau 0.5 d; trend, amplitude
U[0, 2000] ppm, period U[3, 10] d; correlated with trend), sectors of `synthetic.sector_times`
(13-day orbits with the mid-sector gap), two-minute cadence. Estimator parameters: the version-3
plan's `gauntlet.events` (min_coverage 0.5, baseline gap 0.25, outer 1.5 durations; `h` = 0.2 d).
A transit-free ephemeris: period log-uniform in [1, 10] d, duration 0.10 d, t0 uniform over one
period from the first cadence. Per-event measurement: `events.per_event_depths` with the red-noise
model errors (`rednoise.event_noise`, as `pipeline.v05_tests` calls it) and A0's errors
(`a0.empirical_events`). Truth 0 (no signal), so pull = value / error; with an injected signal,
the truth of each event is the noise-free curve measured by the same box estimator **[r3: the box
depth of a trapezoid with ingress 0.1 is 0.9 of its depth, so the injected depth is not the
truth]**. Per stratum, the first 400 pulls in unit order; fewer: NOT DECIDABLE. A statistic with no
calibrated error (`group_variance` None) gives no pull; its count is reported.

**[r3] Coverage kinds.** Revision 1 drew the partial and minimal strata from the gaps a random
ephemeris happens to hit. A TESS-like sector has four segment edges, so a sector has at most a few
partial or minimal pseudo-windows, `n_eff < 10`, and every partial or minimal event is "not
measured": those strata could never be decided, and A0.5's (p3) and A0.7 could never be built
(found on development seeds, before any acceptance unit). Each curve now has a declared kind,
applied to the curve before any measurement: `full` (no cut); `partial` or `minimal` (the first
20 % or 40 % of the in-event core, `[c - D/2, c - D/2 + fD)`, removed at every pseudo-window grid
position of `a0.pseudo_windows`' grid and at every epoch of the ephemeris: coverage 0.8 or 0.6);
`mixed` (A0.7: the odd grid positions and the odd epochs cut to 0.8, the rest full); `p3` (A0.5:
the first sector cut to 0.6, the other sectors full). A sector's first cadence is never removed, so
the grid stays where `pseudo_windows` puts it. The strata used in the evaluation are the ones the
code computes for each event and window, never the kind. This is a simplification of real data
(every window of a sector cut alike), stated in the result.

**A0.1 (per-event).** Unit: one 2-sector curve of a kind and one ephemeris; every measured event
gives a pull in the stratum (noise model, the event's computed coverage stratum). 200 units per
(noise model, kind); the fraction of events not measured (`n_eff < 10`) reported per stratum.

**A0.2 (group).** Unit: one curve of 2, 3 or 4 sectors, a kind and one ephemeris; the statistics,
each measured as the battery measures it, each required to pass on its own: (i) the box odd mean,
even mean and odd-minus-even (per-event box depths with A0's errors, inverse-variance weights, A0's
group rule `a0.group_variance` with `a0.shortcut`, seeded as `a0_depth` seeds it); (ii) the matched
trapezoid odd, even and difference of `battery_v51.check_odd_even` (the version-3 `odd_even`, its
own events, pseudo-windows and group variance; the difference's error is `|difference| /
difference_sigma`); (iii) **[r3]** the large-minus-core difference: `battery_v51_diff.a0_depth` on
the series `large / median(large) - core / median(core)` built as `check_aperture_depth` builds it
(the default `Scene`, pixels rendered from the target's series), seed `candidate_seed(
"aperture_depth") + 2` as in the test; (iv) **[r3]** the SAP-minus-expected difference: `a0_depth`
on `SAP / median(SAP) - CROWDSAP x PDCSAP / median(PDCSAP)` over the sectors where
`sap_applicability` holds, seed `candidate_seed("systematics") + 1`, SAP = the affine SAP of
`synthetic.make_sector_aux` plus independent white noise of the PDCSAP white level (row 3a.6's
second case). **[r3: (iii) and (iv) call `a0_depth` directly. Revision 1 read them from the test
results; `check_systematics` reports the SAP difference only when the PDCSAP depth is positive, a
sign selection on transit-free curves, and the full tests cost 3.6 of the unit's 3.9 processor
seconds.]** The group stratum of a unit is the lowest computed coverage stratum among its box-
measured events. 700 units per (noise model, kind, sector count) **[r3: on development seeds 8 of
9 ephemerides with P < 1.5 d had no calibrated odd-minus-even error, so about 18 % of units give no
pull; 700 leaves a margin over 400]**; per stratum and statistic the first 400 pulls.

**A0.3 (structure).** On every A0.1 and A0.2 unit, recorded booleans, by cadence index sets
(half-open windows `[c - h, c + h)`, the convention `box_measure` now uses): the kept pseudo-windows
are pairwise disjoint (every pair, not only neighbours); none shares a cadence with a real event's
window; phase-0.5 windows present or absent as the conditional rule says (here no secondary:
included); every window's centre is on the `2h` grid from its sector's first cadence, with the
right grid index; `n_eff` recomputed from the recorded `r_k` by the formula equals A0's; every
measured event's (sector, stratum) has `n_eff >= 10`. Pass: every boolean true on every unit. The
"too few events: INCONCLUSIVE `not_enough_data`" clause: the classes returned by `check_odd_even`
are recorded on every A0.2 unit.

**A0.4.** As A0.2 (box and matched statistics) with the noise model in every sector and a trend in
the first sector only (`noise_curve(trend_sectors=(1,))`), 700 units per (noise, kind, sectors).

**A0.5 (unequal events).** Spacing P in {1, 3, 10} d, combination (equal noise; a trend in the
first sector), noise model, sector count; (p1) the whole window of one odd event (the middle odd
epoch) removed (an event lost in a gap), kinds full, partial, minimal; (p2) **[r3]** the first five
consecutive measured events (time order) with 2 of one parity and 3 of the other, on the full curve
(revision 1 cut the curve to five events; on the full curve the sector keeps its pseudo-windows),
kinds full, partial, minimal; (p3) the `p3` kind (the first sector at coverage 0.6) and the group
of the first sector's events with as many events of the other sectors (the first sector holds
half), minimal stratum only (the text defines (p3) at the minimal stratum). Statistics: box odd,
even, difference with A0's rule. 400 units per (pattern, spacing, combination, noise, kind,
sectors): 252,000 units (108,000 each for p1 and p2, 36,000 for p3; revision 3's first draft said
126,000, corrected after Codex's round 3). At P = 1 d the group error is mostly not calibrated (see A0.2); reported.

**A0.6.** Per noise model and kind, 400 transit-free 2-sector curves whose candidate has the period
1, 3 or 10 d in turn (Codex's round 3: the pseudo-windows are excluded around the scheduled
ephemeris, so the lag of a period is measured on a candidate of that period): the lag-k
autocorrelation of the standardized pseudo-window values for k = 6 to 10 and at the grid lag
`round(P / 2h)` of the candidate's period (`a0.lag_correlation`, all pairs), per computed stratum,
with the descriptive band `2 / sqrt(m)`, m the pairs. Reported only.

**[r3] Evaluation** (Codex's round 3, objection 2), `a0.py evaluate`, once every section is
complete, writing `a0-result.json` once: per row, stratum, statistic (and depth and branch for
A0.8) the first 400 finite pulls in schedule order against A0's band (sd in [0.9, 1.1], absolute
mean at most 0.1), PASS, FAIL or NOT DECIDABLE (fewer than 400), with the count of units whose
statistic had no calibrated error (never counted as a passing observation); every FAIL and NOT
DECIDABLE key listed; the A0.3 booleans per unit, PASS only with no violation; A0.7: the rule's
bands on the units whose events span two strata, the forced-pooling bands, the keys where forced
pooling leaves [0.9, 1.1], the shortcut fraction, the realized `r_{k,a,b} - r_k`; A0.8: the event
and group bands per branch, the fractions excluded and INCONCLUSIVE and the median error inflation;
each sabotage: detected when at least one decided target stratum FAILs (share_event_cadences: when
an A0.3 boolean fails), void when every target stratum is NOT DECIDABLE; the forced-inclusion
sabotage undetected means A0 fails this condition. Units that ended in ERROR are counted and stay
in their denominators. Checked end to end by a tiny dry run on development seeds
(.cache/v051/accept/dryrun_eval.py), which found and fixed a name collision before any acceptance
unit.

**A0.7 (heterogeneous correlation).** The ephemeris is drawn first; the `mixed` kind is applied;
then, on the cadences of every window (grid position or event) whose coverage is below 0.9, the
correlated noise is the sum of two independent AR(1) series (tau 1 h and 0.5 d, each of variance
`sigma_r^2 / 2`), elsewhere one AR(1) (tau 1 h, variance `sigma_r^2`), `sigma_r` half the white
level, added to the white curve. **[r3: with the `mixed` kind every sector has full and partial
windows on alternating grid positions, so the cross-stratum lag pairs exist at odd lags and the
same-stratum pairs at even lags.]** 700 units per sector count; the box and matched statistics with
the rule (and the shortcut where its test takes it) and the box statistics with forced pooling;
reported: the realized `r_{k,a,b} - r_k`, the fraction of units taking the shortcut (a TESS-like
sector has two segments, below the shortcut's minimum of three, so it is never taken: reported).
Required as the text says; the homogeneous comparison is A0.2's correlated strata.

**A0.8 (secondary).** A primary at the candidate's ephemeris (trapezoid, ingress 0.1, depth for a
box SNR of 20 over the curve) and a secondary at phase 0.5 with the primary's duration and shape, at
2.5, 3 and 4 times the phase-0.5 group error of `secondary_eclipse` measured before the injection
(`group_mean` of `per_event_depths` at phase 0.5 with the red-noise errors, as the test combines
them); `battery_v5.check_secondary_two_sided` with the pipeline's inputs and seed decides the branch
(FAIL: phase-0.5 windows excluded; PASS or INCONCLUSIVE: included). Shapes: `event` (A0.1's curves,
100 units per noise, kind and depth; the primary events' pulls against their noise-free box
depths), `group` (A0.2's curves, 700 units per noise, kind, sectors and depth; the box odd, even and
difference pulls against the weighted noise-free truths), `hetero` (A0.7's curves, 700 per sectors
and depth). Per stratum, depth and branch, the first 400 pulls; a branch with fewer is NOT
DECIDABLE (the minority branch near the threshold will often be: reported). The error inflation (the
median A0 error under the rule's choice over the median A0 error of the same curve without any
secondary) and the fractions excluded and INCONCLUSIVE reported.

**Sabotage.** Each sabotage is its own section (`sabotage-<name>`), so a worker process serves one
patch only (a guard refuses a second); the patch replaces one function of the `a0` module inside
the worker, never committed: model errors alone (`stratum_error` returns no empirical error) on
A0.1 units of the two correlated models, every kind; `n_eff = n` (`effective_count`) on A0.1's long
model; **[r3]** `rho_ij = 0` as a diagonal `group_variance` (revision 1 replaced `lag_correlation`
in the module, which would also have zeroed `n_eff`'s `r_k`) on box-only A0.2 units of the long
model; pseudo-windows sharing cadences with real events (`pseudo_windows` with the event exclusion
off) on 50 A0.1 units, where A0.3's booleans must fail; the windows of all sectors pooled
(`stratum_error` over every sector's windows) on box-only A0.4-like units; forced pooling is A0.7
itself; forced inclusion of the phase-0.5 windows (`empirical_events` always including) on A0.8
`event` units at 4 sigma, every noise and kind (A0.8 must fail in at least one stratum; if it does
not, A0 fails this condition and the result goes to the maintainer).

**[r3] A finding of the development smoke (dev seeds), reported, not acted on.** A0's group rule
needs `r_{k,a,b}` with at least 20 pseudo-window pairs at each lag `k <= 5` that separates two
events of a segment. The pseudo-windows exclude `+-2h` around every event, so at periods below about
1.5 d (event lag 2 or 3) no window pair exists at the event lag and `group_variance` returns None:
the version-3 `odd_even` is then INCONCLUSIVE (`insufficient_sensitivity`) for every such
candidate. In A0.5 the spacing P = 1 d is therefore mostly undecidable. This is A0's adopted rule
working as written; whether it matters for short-period binaries is for the D1 lines and the
maintainer.

**[r4] The second run (#208, the maintainer's decision of 2026-11-08).** The first run's A0.1
FAILed in 12 of 15 strata with overestimated errors: the runner passed the raw synthetic curve to
`rednoise.event_noise`, `events.per_event_depths`, `a0.empirical_events` and
`battery_v51.check_odd_even`, which in the version-3 pipeline receive the flattened curve of
`pipeline.attack_candidate`. That result stands as recorded. The correction only aligns the runner
with the pipeline; nothing in `src/`, the thresholds, the bands or the acceptance text changes:

- `_flat(raw, cand, plan)` builds the series as `attack_candidate` does, line for line: the
  candidate's transits masked (`transit_mask_half_width_durations` durations), the corrections'
  global components refitted with that mask and subtracted first when the corrections are active
  (never with this plan), then `detrend(curve, plan.detrend, mask=mask)`. The candidate is the
  declared ephemeris, as in revision 3 (in the pipeline the mask uses the search candidate and the
  measurements use `finalize_candidate`'s refinement of it; here both are the declared one).
- Applied after the coverage cut, `_cut_one_odd`, A0.7's coloured noise and A0.8's injections, all
  on the raw curve; every measurement of the unit then uses the flattened series. The pixels and the
  SAP of A0.2's (iii) and (iv) stay raw, as the pipeline renders them from the raw data
  (`a0_depth` detrends those series itself).
- A0.8: the phase-0.5 reference error, the branch, the measured events and the reference without
  secondary are all on flattened curves; the truth of each event is the noise-free curve through the
  same path (flattened by `_flat`, then the same box estimator).
- New seeds by the fixed label `refute-v051-accept-r2` (`<label>:a0-...:<i>`), committed before
  the run; output folders `.cache/v051/accept/a0r2-<section>/`; the result `a0r2-result.json`. The
  first run's seeds and records decide nothing.
- The proof (the decision's item a): `tests/test_v051_accept_a0_series.py` runs one unit of every
  kind on development seeds and checks, byte for byte, that every series those four functions
  receive is the series `attack_candidate` gives them for the same raw curve and candidate, and
  that the first run's behaviour (the raw curve handed to all four) fails that check. Its scope
  (Codex, round 1 of the second run): the construction of the series for a fixed candidate. The
  acceptance calibrates A0 conditionally on the predetermined candidate (revision 3); the
  pipeline's refined candidate (`finalize_candidate`) is not reproduced and no candidate
  equivalence is claimed.

A consequence, not a change: `detrend` drops upward outliers, so a sector's first cadence may fall
out of the flattened curve and A0's grid then starts at the next one, a few cadences away from the
positions the coverage kinds cut; the strata used are still those the code computes.

**Order and cost** (measured on development seeds, processor seconds per unit, one process: A0.1
0.19, A0.2 1.9, A0.4 0.36, A0.5 0.21, A0.6 0.14, A0.7 0.66, A0.8 0.64). Units and projection:
A0.1 3,000 (0.2 h); A0.2 31,500 (16.6 h); A0.4 31,500 (3.2 h); A0.5 252,000 (14.7 h); A0.6
6,000 (0.2 h); A0.7 2,100 (0.4 h); A0.8 105,300 (18.7 h); sabotages about 9,000 (0.9 h): about 55
processor-hours before the parallel slow-down. Order: A0.1, A0.2, A0.4, A0.7, A0.6, A0.8, A0.5, the
sabotages; each its own section with the 5 % projection and the 1.5-times stop.
