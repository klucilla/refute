# The WP3 (b) acceptance runner: design (revision 4)

Revision 2 answers Codex's round 1 (WEAKENED, four objections), revision 3 its round 2 (WEAKENED,
one objection and a clarification) and two corrections found while coding, revision 4 its round 3
(WEAKENED, three objections, all accepted); the changes are marked **[r2]**, **[r3]**, **[r4]**.

Section "WP3 (b)" of docs/plans/v0.5.1-acceptance.md (rows 3.1 to 3.8 and the sabotage line).
Runner: docs/validation/v0.5.1/acceptance/wp3b.py on common.py (freeze check, seeds, binomial
bands, noise models, the 5 % projection and the 1.5-times stop). It replaces the draft committed in
86e0a1d, which was never run: the draft predates common.py (no freeze check, no projection), built
its own cases instead of v0.5's for the rows that say "as v0.5", passed `V051Params()` and a seed
of its own instead of the plan's parameters and the pipeline's seed, and had no sabotage. Every
choice below is one the text leaves open, fixed before any acceptance unit runs; nothing is tuned
after a run. Each row runs once.

## What the runner hands the test (item 3 of the maintainer's decision of 2026-11-08)

The pipeline calls `battery_v51.check_sinusoid(data.lc, final, plan.stronger, plan.v051,
power.candidate_seed("sinusoid", final))` (`pipeline.v05_tests`): the **raw, undetrended** light
curve as loaded, never the flattened series. The runner calls it with:

- the unit's curve itself, as `synthetic.make_data` would hold it in `data.lc` (no detrending, no
  prewhitening, no cut);
- `plan.stronger` and `plan.v051` of the version-3 plan (`TessTestPlan` of
  `synthetic.discovery_v051_plan_dict()`), not fresh `StrongerParams()` / `V051Params()`;
- the seed `power.candidate_seed("sinusoid", cand)`, the pipeline's function on the unit's
  candidate;
- then `enforce_sensitivity` with the version-3 registry (`power.TESS_REGISTRY_V3`), as the
  engine applies it.

**The proof** (tests/test_v051_accept_wp3b_series.py, in the suite): for a curve of each
construction below, `pipeline.attack_candidate(make_data(curve, [], make_star()), cand, plan)`
is run with `check_sinusoid` spied (and stopped once it is called); the light curve it receives is
byte-identical (time, flux, flux_err, sector, year) to the series the runner hands the test for
that unit, and its `sp` and `cp` equal the runner's. A negative control shows the test catches a
runner that hands the flattened series (`pipeline.detrend` with the transit mask) to
`check_sinusoid`. **[r2]** Row 3.3 also runs `secondary_eclipse` and `duty_cycle` (objection 1):
`secondary_eclipse` measures on the pipeline's flattened series, built by
`series.pipeline_flat(raw, cand, plan)` (docs/validation/v0.5.1/acceptance/series.py, the same
construction as A0's `_flat`, moved to a module the later runners share; a0.py is not changed),
then `rednoise.event_noise` and `events.per_event_depths` at phases 0 and 0.5 with the plan's
cadence, as `v05_tests` does. The proof spies those two functions too, and its negative control
also hands them the raw curve (the first A0 run's defect) and checks that it is caught. **Scope** (as A0's proof): the series and the parameters for a fixed candidate; the
pipeline's refined candidate (`finalize_candidate`) and so its seed are not claimed equal to the
declared one.

## Common

- **Seeds** `refute-v051-accept:wp3b-<row>-<case>-<noise>:<i>`, `i` = 0..199, refused unless the
  process checked the freeze first (common.py).
- **Curves**, unless a row says "as v0.5": `common.noise_curve(seed, noise, 2)`, two TESS-like
  sectors (2000.0 and 2027.4 BTJD, `synthetic.sector_times`), two-minute cadence, white 1000 ppm;
  the noise models white, correlated, trend, correlated_trend (`common.NOISES`). Signals enter as
  the multiplicative model before the noise. T_span is the curve's span (about 54.4 d).
- **Planet**: `synthetic.trapezoid`, ingress fraction 0.1, period P, duration D; the depth `d`
  for a box SNR `s` over the curve: `d = s * sigma_w / sqrt(n_in)`, `n_in` the cadences of the
  curve within D/2 of a transit centre; t0 uniform over one period from the first cadence.
- **Candidate**: the truth (period, t0, duration, depth `d`; `depth_err = d / 10`), as the A0
  runner and the v0.5 acceptance did (the test, not the search, is under test), except where a row
  says the engine finds the box.
- **Statuses**: FAIL means the test flagged a harmonic (`metrics.fits[...]`); the final status is
  the one after `enforce_sensitivity`; the emitted severity is recorded and must be `warning` in
  every trial (the test is never fatal; a fatal severity anywhere is reported as a FAIL of 3.3).
- **Bands** (common.py): "at least at rate p" = count at or above the lower 2.5 % quantile of
  Binomial(n, p); "at most a" = count at or below the upper 97.5 % quantile of Binomial(n, a).
- A unit that raises is an ERROR, kept in its denominator: a case with an ERROR is NOT DECIDABLE.

## Rows

**3.1 (v0.5 rows 3.3 and 3.8, "as v0.5").** v0.5's own constructions, imported from
docs/validation/v0.5/acceptance/acceptance.py (unchanged): the standard layout (`_std_time`, P =
3 d, T0 = 1000.3, D = 0.1 d), noise white and red (v0.5's `_lc`; the trend variant excluded for
the sinusoid rows, as v0.5 recorded: it is itself a sinusoid); 200 per noise.
- 3.1a (v0.5 3.3): the variability at `SIN_P` = 0.83 d, semi-amplitude 2000 ppm, minimum at T0,
  found as a box by the engine (`_sin_box`, `finalize_candidate` on the noise-free detrended
  curve; the version-3 plan's detrend and search sections, which equal v0.5's); the construction
  check as v0.5 (amplitude over the box depth in [1.9, 2.1], the box t0 within D/2 of T0, design
  significance above 15 at P); Must: FAIL at least at rate 0.95.
- 3.1b (v0.5 3.8): the box only (depth 2000 ppm), the construction check as v0.5 (the main block
  detectable; in version 3: every applicable sub-check detectable); Must: FAIL at most 0.0027.
- **[r3]** v0.5's decision rule, as v0.5 applied it: a case is decided only when every one of its
  trials meets its construction; otherwise it is NOT DECIDABLE, with the count not constructed
  (revision 2 said "over the constructed trials", which is not v0.5's rule).

**3.2 (a planet on a star with a C1-like trend).** "Each noise model" with the trend: the trend
is in every curve (`trend_sectors` = both sectors), on white and on correlated noise (named
`trend` and `correlated_trend`); P = 3.3 d, D = 0.12 d, SNR 12 and 20; 200 per (SNR, noise). Must:
FAIL at most 0.0027 per (SNR, noise); at SNR 20, the count of trials with every applicable
sub-check detectable at least at rate 0.95.

**3.3 (v0.5 rows 3.4 and 3.5, coexistence).** A planet at P = 3.3 d, D = 0.12 d, SNR 15; (unrelated)
a sinusoid at 2.37 P, semi-amplitude 3 d; (rotation) a sinusoid at P, semi-amplitude 1 d; random
phases; four noise models, 200 each. **[r2]** The v0.5 rows speak of every WP3 test, so each trial
runs the three WP3 tests of the version-3 battery as `v05_tests` calls them: `sinusoid` (above),
`battery_v5.check_secondary_two_sided` (the flattened series, phases 0 and 0.5, the plan's
`gauntlet.secondary_eclipse` and `stronger`, seed `candidate_seed("secondary_eclipse", cand)`) and
`battery_v5.check_duty_cycle(cand, sp)`, each through `enforce_sensitivity` with the version-3
registry. Must (as v0.5): (unrelated) no trial with a final FAIL of fatal severity from any of the
three; (rotation) at most a warning from any of them (the same condition). Each test's FAIL count
and emitted severities reported apart.

**3.4 (multi-periodic variability, V2-like).** The C1 generator's V2 construction
(`calib05.c1`, family V2): f0 = 1 / Pv, Pv log-uniform in [0.7, 10] d, frequencies f0, f0 (1 +
d1), f0 (1 + d2), d1 and d2 uniform in [0.01, 0.05], each semi-amplitude A / sqrt(3), A
log-uniform in [0.5, 5] sigma_w, random phases; no transit. The candidate (a search finding the
variability): period Pv, t0 the first minimum of the summed model after the first cadence, D = 0.1
d, depth A / 2 (v0.5 row 3.3's ratio). Four noise models, 200 each; on the same curve and
candidate the v0.5 code (`battery_v5.check_sinusoid` with `plan.stronger` and the same seed, then
the v0.5 registry) runs too. Must: the version-3 FAIL count at least the v0.5 code's (paired, same
curves), per noise model.

**3.5 (P = 12 d and 15 d planets).** D = 0.25 d, SNR 15, four noise models, 200 per (P, noise).
Must: in every trial P/2 and P applicable (a rule block), 2P "not applicable", and the status not
INCONCLUSIVE of class `outside_domain`.

**3.6 (a sinusoid at P = 14 d found as a box).** **[r2]** (objection 3) A sinusoid of period 14 d,
semi-amplitude 2000 ppm (v0.5 row 3.3's), minimum at 2003.0 BTJD, no transit. The candidate is the
box the engine finds: `search.finalize_candidate` at P = 14 d, duration hint 0.3 d, on the
noise-free curve, as v0.5's `_sin_box` builds row 3.3's. It is computed on the **undetrended**
curve: the version-3 search detrends first (`robust-local-quadratic`, 1-day window), and on the
detrended noise-free curve the 14-day sinusoid is gone (development check, noise-free and seedless,
.cache/v051/wp3b/box14.py: box depth 0.1 ppm detrended, 1,045 ppm undetrended at D = 0.45 d, t0
2010.00, P 14.0013), so no search can find it as a box; the engine's box estimator on the
undetrended flux is the nearest construction. **[r3]** It is a fixed-period box-estimator
candidate constructed for the test, as v0.5's `_sin_box`; the row does not show that the version-3
search finds it. The same candidate for every trial (one noise-free
curve). Four noise models, 200 each. Must: FAIL at least at rate 0.95 over the trials whose P block
is detectable (the count of the others reported).

**3.7 (variability within 1 / T_span of P).** A planet at P = 3.3 d, D = 0.12 d, SNR 15 with a
sinusoid of period P (1 + 0.002) (a frequency 6e-4 per day from 1 / P, inside 1 / T_span = 0.018
per day), semi-amplitude 2 d. Four noise models, 200 each. Must: no extra frequency within 1 /
T_span of 1 / P in any trial; **[r2]** (objection 4) and the harmonic carries the trend: the P
harmonic's fitted semi-amplitude within 3 of its own errors (`semi_amplitude_err_ppm`, the
joint-model error the test reports) of the expected one, in at least rate 0.95 of the trials
(binomial band). The expected semi-amplitude is computed, not assumed **[r3]** (round 2,
objection 1): the P harmonic's semi-amplitude when the trial's own fit (the same out-of-transit
cadences, the same per-sector median normalization, the same weights `1 / err^2` of the normalized
errors, and the same design: per-sector offsets, the tested harmonics and the extra frequencies the
test selected in that trial) is applied by weighted least squares (`battery_v51._wls`) to the
noise-free injected sinusoid alone, divided by the same per-sector medians; a
rate and not every trial, because a trend model's own sinusoid (period 3 to 10 d) can fall near P.

**3.8 (1.8 (a), (b), (c) of v0.5, per sub-check).** For each sub-check Q in P/2, P, 2P (P = 3.3 d,
so every sub-check applicable), four noise models, 200 each:
- (a) a planet (SNR 20, D = 0.12 d) with a sinusoid at period Q, semi-amplitude 2 d; constructed
  when the Q block is detectable; Must: Q flagged at least at rate 0.95 over the constructed;
- (b) **[r3]** the same signals (planet and sinusoid at Q, as in (a)) with the noise 25 times
  larger (`noise_curve` at 25,000 ppm; the correlated part scales with it; the planet's depth stays
  the one of SNR 20 at 1,000 ppm): the alternative below the rule. Revision 2 multiplied every flux
  deviation, the signals included, which leaves the sinusoid's significance unchanged, so the test
  would FAIL by the injected sinusoid and "never PASS" would hold without examining the rule.
  Constructed when the Q block is not detectable; Must: never a final PASS;
- (c) the planet only (no sinusoid): constructed when the Q block is detectable; Must: Q flagged
  at most at rate 0.0027 (one curve set shared by the three sub-checks of (c)).

**Sabotage** (each its own section, a patch inside the worker, never committed): (i) no extra
frequencies (`cp.sinusoid_extra_frequencies = 0`) on 3.2 at SNR 20: Must make 3.2's detectable
fraction fail; (ii) **[r2]** (objection 2) the v0.5 domain on the candidate: `check_sinusoid` wrapped so that a
candidate with P >= 10 d returns INCONCLUSIVE of class `outside_domain` before any fit (v0.5's
"for P < 10 days"; lowering `sinusoid_harmonic_max_period_days` would not do it, since P/2 of a
12-day candidate stays inside), on 3.5: Must make 3.5 fail; (iii) the exclusion window removed (the extra-frequency search with no excluded band) on
3.7: Must make 3.7 fail. A sabotage that does not make its row fail is reported as not detected. **[r4]** (Codex's round
3, objection 1) Detection is judged on the target the text names, in at least one decided case of
the section: (i) 3.2's detectable fraction (not its false-failure bound); (ii) 3.5's applicability
and domain condition; (iii) 3.7's extra frequency within 1 / T_span of P (the mechanism the
exclusion window prevents), not its amplitude criterion. Void when every case is NOT DECIDABLE.

**[r4] Paired seeds in 3.8** (round 3, objection 2): (a) and (b) of one sub-check share the seed
case `wp3b-3.8-ab-<Q>-<noise>`, so they have the same planet, sinusoid and standardized noise
draws, (b) with the noise level 25 times larger; their records stay apart.

**[r4] Records by identity** (round 3, objection 3): the evaluator refuses a record file with a
unit outside the schedule or a unit recorded twice, and counts missing units by identity.

## Units, cost and order

3.1 800; 3.2 800; 3.3 1,600; 3.4 800; 3.5 1,600; 3.6 800; 3.7 800; 3.8 5,600 ((a) and (b) 4,800,
(c) 800); sabotages 400 + 1,600 + 800: about 15,600 units. Cost from the development smoke (dev
seeds, before any acceptance unit): to be measured and recorded before the run; the 5 % projection
of each section decides. Sections: `wp3b-rows` (3.1 to 3.8), then the three `wp3b-sabotage-*`.

## Output

`.cache/v051/accept/wp3b-<section>/records.jsonl` and `projection.json`; `wp3b.py evaluate` writes
`docs/validation/v0.5.1/acceptance/wp3b-result.json` once, with every case's counts, bands and
construction counts, `method_status: not_validated`.
