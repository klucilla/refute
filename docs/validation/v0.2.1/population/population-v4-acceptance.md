# population_v4: the acceptance record (gate 1 of plan B; committed before its tests and code)

Plan B ([../reopen/stage-1/plan-b/README.md](../reopen/stage-1/plan-b/README.md), adopted and frozen
on 2026-10-23), section 3, and the population study's Amendment B
([../population-study.md](../population-study.md)). This record fixes what the generator
`population_v4` and the domain function must do, how each acceptance criterion of plan B section 3
is checked, and how each check is shown to catch a broken generator (the sabotages). It is
committed **before its tests are committed, and the tests are committed (and their first run
recorded as failing) before any code exists**; git shows the order (criterion 9). It changes
nothing of plan B: where plan B leaves a detail open, the detail is fixed here and named as such
(section 6).

**The sequence, as it happened.** While this record's first version awaited Codex's review, drafts
of the two test files were written in the working tree; Codex's review saw one of them. They were
moved out of the working tree, are revised to this version of the record, and are committed only
after it. No code of the generator, the domain function or the checks existed at any point before
the tests' commit.

**No lot runs at this gate.** Nothing here runs the engine (no search, no gauntlet, no holdout, no
verdict). The gate's evidence is the tests, the acceptance checks on the acceptance population
(built in full, in memory, three times; section 4), the sabotages, and Codex's review. Every lot
keeps its own declaration and authorization.

## 1. The files

| File | What it is |
|---|---|
| `src/refute/packs/tess/domain.py` | The domain function of the profile `three-observing-years/1`: D1 to D5 on per-sector kept time stamps. The same function the profile O2 (gate 2) calls; at this gate nothing in the engine imports it, so no earlier behaviour changes. |
| `docs/validation/v0.2.1/population/population_v4.py` | The generator. A new module; `population_v2.py` and `population_v3.py` are not changed (their SHA-256 checked by a test: `8b3b6ad6…1f82` and `3620cca0…3787`). It loads `population_v2` by path (its SHA-256 checked first, as `population_v3` does) and reuses `draw_parameters`, `_place_in_band`, `_mechanism_condition`, `_noise`, `_fp_mechanism`, `_notransit_mechanism`, `_catalog`, `_scene`, `_signal_spec`, `case_seed`, `sub_seed`, `data_to_parts`, `serialize`, `deserialize`, `plain`, the bands, the depth limits, the noise and trend constants, the mechanism tuples and `CATALOG_VARIANTS`. New are only the layouts (section 2) and the mapping of the variability-free year. |
| `docs/validation/v0.2.1/population/population_v4_check.py` | The acceptance checks of criteria 1 to 4 and 6 to 9 (section 3). |
| `docs/validation/v0.2.1/population/band_check_v4.py` | The independent band check (criterion 5). It imports only the standard library and NumPy: not `refute`, not `population_v2`, not `population_v4` (checked by a test on its import statements). Its own reader of `refute-population-serialization/1`, its own `sub_seed`, trapezoid, crowding, in-transit selection, expected SNR, noise stream and flux model, written from the protocol's text (population-study.md sections 3 and 4, and `population_v2`'s declared `CALL_SEQUENCE`). |
| `docs/validation/v0.2.1/population/population_v4_sabotage.py` | The sabotages (section 5): each breaks one criterion once, in its own process, and records whether the check caught it for the named reason, with an unbroken control. |
| `tests/test_domain.py`, `tests/test_population_v4.py` | The tests, committed after this record and before any code, their first run recorded as failing. |
| `docs/validation/v0.2.1/population/v4-acceptance/` | The gate's outputs (JSON): the acceptance population's checks and digests, the sabotages, the order check. |

## 2. The definitions (fixed here, before any test)

### 2.1 The domain function (Amendment B's input and definitions)

**Input:** per sector, the array of its **kept** cadence time stamps (BTJD days). In the synthetic
harness these are the generated time stamps; for real products the profile O2 (gate 2) supplies the
cadences kept by the plan's quality mask, before any flux-based filter. A sector with no kept
cadence contributes no observing year and is left out. Each sector's **label** is
`btjd_to_year(first kept time stamp)` (`refute.packs.tess.types`), as the adapter labels a sector;
if that first time stamp is not finite, the label is unavailable (`None`).

**Constants:** cadence `Δ = 120 s`; timing tolerance 0.5 s; `k` from 1 to 4; internal gap: an
interval **> 600 s**; orbit 12.5 to 14.0 d; orbit gap 0.5 to 2.0 d; at most 4 other internal gaps,
each **≤ 21 600 s** (6 h); coverage **≥ 0.84**; about one year 345 to 385 d; about two years 710 to
750 d; every bound inclusive except the internal gap's strict `> 600 s`.

**Per sector** (time stamps read in the order given; the function never sorts within a sector):
- intervals `dt` = consecutive differences, in seconds;
- **span** = last − first + `Δ`; **coverage** = `n_kept × Δ / span`;
- **internal gaps** = intervals `> 600 s`; the **orbit gap** = the longest (the first one on a
  tie); the two **orbits** = the time stamps before it and after it; an **orbit's length** = its
  last − first + `Δ` (the span's convention);
- the **other internal gaps** = every internal gap but the orbit gap;
- for every interval `≤ 600 s`: `k = round(dt / Δ)` and the residual `dt − kΔ`.

A quantity that cannot be computed is unavailable (`None`), never a number: the span, the coverage
and the orbits when a time stamp is not finite; the orbit gap and the orbits when the sector has no
internal gap (a sector of one cadence has no interval and no internal gap).

**The conditions, in this order** (the result names the first that fails, with its measured value):
- **D1:** every sector has a label, and there are exactly three distinct labels.
- **D2:** exactly three sectors (so exactly one in each observing year).
- **D3:** every time stamp finite; every interval `≤ 600 s` has `1 ≤ k ≤ 4` and `|residual| ≤ 0.5 s`
  (an interval `≤ 0`, or one that rounds to `k < 1`, fails).
- **D4:** every sector has an orbit gap of 0.5 to 2.0 d, both orbits 12.5 to 14.0 d, at most four
  other internal gaps, each `≤ 21 600 s`, and coverage `≥ 0.84`; an unavailable quantity fails.
- **D5:** with the sectors ordered by their first time stamp (sectors with an unavailable label or
  first time stamp make D5 fail), there are exactly two separations between consecutive first time
  stamps, each 345 to 385 d or 710 to 750 d, at most one of them 710 to 750 d.

Every condition is computed on every input (no short circuit), so the measured quantities are
always recorded. The result carries, per sector, the label, the number of kept cadences, the span,
the coverage, the orbits' lengths, the orbit gap, the other gaps, the counts of `k` = 1 to 4 and
the residuals' range; and the separations.

### 2.2 The generator's layouts (Amendment B's represented geometries)

**Geometry, allocated, not drawn.** Within each group (class, noise model, band where the class
has one, and mechanism, the planets' regime being their mechanism), the cases in index order take
the positions `j = 0, 1, 2, …` of the group; `j mod 2 = 0` → **G-a** (both separations about one
year), `j mod 4 = 1` → **G-b, short then long**, `j mod 4 = 3` → **G-b, long then short**. So G-a
takes the extra case of an odd group, and within G-b "short then long" takes the extra case. For
250 measurable false positives (groups 63, 63, 62, 62): G-a 126, G-b 124; for 360 planets per band
(groups 180, 180): 180 and 180. The geometry is recorded in the case's `extra`
(`{"geometry": "G-a"}` or `{"geometry": "G-b", "order": "short-long" | "long-short"}`).

**The layout's random draws** (the layout stream, `numpy.random.default_rng(sub_seed(seed,
"layout", a))`, `a = 0, 1, …` the layout attempt; independent of the parameters' stream, which
stays `population_v2`'s: `seed` for attempt 0, `sub_seed(seed, "redraw", k)` after), in this fixed
order:
1. the first sector's nominal start `s1 = 1325.0 + 365.25 u`, `u` uniform in [0, 1);
2. the first separation, then the second: uniform in [345, 385) d (about one year) or [710, 750) d
   (about two years), as the geometry and its order say;
3. for each sector in time order: the first orbit's length `L1` uniform in [12.5, 14.0) d, the
   orbit gap `g` uniform in [0.5, 2.0) d, the second orbit's length `L2` uniform in [12.5, 14.0) d;
   the number of loss blocks, an integer uniform in 0 to 4 (`integers(0, 5)`); for each block, its
   length `ℓ` uniform in [600, 21 600) s, then its place `v` uniform in [0, 1); the single-cadence
   loss probability `ρ` uniform in [0, 0.05); one uniform number per nominal cadence (the single
   losses); one jitter per nominal cadence, uniform in [−0.25, 0.25) s.

**The time stamps built from the draws** (`Δ = 120 s`), in this order:
1. **Nominal cadences.** Sector `k` starts at `s_k` (`s2 = s1 + sep1`, `s3 = s2 + sep2`); its first
   orbit holds the nominal cadences `s_k + iΔ`, `i = 0 … n1 − 1`, `n1 = round(L1 / Δ)`; its second
   orbit starts at the first orbit's last nominal cadence plus `g` and holds `n2 = round(L2 / Δ)`
   nominal cadences (an orbit's realized length is `L` quantized to within 60 s, before the
   jitter).
2. **Blocks.** A block of length `ℓ` removes `m = floor(ℓ / Δ)` consecutive nominal cadences, so the
   interval across it is `(m + 1)Δ`, from 720 s to 21 600 s before the jitter (the jitter can carry
   a 21 600 s interval above 6 h; the domain then rejects the layout). Its **admissible places** are
   the anchors `i = 0 … n − m − 2` of either orbit (`n` the orbit's nominal cadences): it removes
   cadences `i + 1 … i + m`, keeping cadence `i` and cadence `i + m + 1`, so it never touches an
   orbit's first or last cadence. The admissible places of the first orbit, then of the second, are
   numbered `0 … A − 1` and the block takes place `floor(v × A)`. Blocks may overlap; the union of
   the blocks' removed cadences is the block mask; the domain decides.
3. **Single losses.** The eligible cadences are those not in the block mask, except each orbit's
   first and last cadence and every cadence adjacent to a block-removed cadence. An eligible cadence
   is lost when its uniform number is below `ρ`. Then, **in the single-loss mask only**, within any
   run of consecutive lost cadences the 4th, 8th, … are restored, so never four or more adjacent
   cadences are lost by single losses (no single loss touches a block, so `k ≤ 4` holds). `ρ` is the
   primitive probability; the realized loss rate is lower (the exclusions and the restoring) and is
   recorded.
4. **Jitter.** Every kept cadence gets its jitter (seconds, converted to days); every D3 residual is
   the difference of two jitters, inside (−0.5, 0.5) s.

**The rejection:** the time stamps of the attempt go through the domain function; if any condition
fails, the layout is drawn again with `a + 1`, the reason recorded as `layout:D<n>` (the first
failing condition) in the case's `redraws`. Nothing else rejects a layout. At most 1000 attempts
(`MAX_ATTEMPTS`), as for the parameters; more is an error, never a silent case.

**A sector across a year boundary is not rejected.** Plan B's text gives "a sector across a year
boundary" as an example of a draw outside D1 to D5. By Amendment B's normative definitions a sector
is labelled by its first kept cadence, so a sector across a year boundary is inside the domain when
the three labels are distinct (for example a first sector starting on 2018-12-20 with separations
of 365 and 365 d: labels 2018, 2019 and 2020). The generator's only rule is D1 to D5; the example
does not add a condition (section 6, item 1, for the maintainer's ratification).

**The parameters and the signals:** exactly `population_v2`'s `draw_parameters`, called with the
layout's first time stamp; `_mechanism_condition` and `_place_in_band` (bands, depth limits, three
passes for the planets' duration) on the layout's time stamps and labels; the parameters' redraw
loop and its reasons as `population_v2.build_case`; the noise by `_noise` from `sub_seed(seed_k,
"noise")`, per sector in time order; the trend; the variability; the pixel and auxiliary data as
`population_v2.build_case` makes them (`make_aux`, or the blend's pixels), with the same operations
in the same order. **The variability-free year:** `draw_parameters` draws `var_absent_year` from
(2018, 2019, 2020) as before; its position in that tuple (0, 1 or 2) is recorded as
`var_absent_position` and `var_absent_year` becomes the curve's label at that position (its sectors
in time order), so exactly two of the curve's three observing years carry the variability.

**The population (B2, per noise model):** planets `three_years` and `variability_some_years`, 180
each per band (indexes 0 to 179 and 180 to 359), catalog variant `CATALOG_VARIANTS[i mod 5]`; false
positives below 100, near 100, measurable 250 (`_fp_mechanism`), the same variant rule; curves
without a transit 2200 white and 600 correlated (`_notransit_mechanism`). Case ids and seeds as
`population_v2` (`case_seed(prefix, class, band, noise, index)`), with the population's prefix.
The **acceptance population** of this gate is the whole B2 structure (5860 cases: 3730 white, 2130
correlated) with the prefix `refute-v0.2.1-population-v4-acceptance`; a **selftest** population (a
few cases per cell) serves the tests and the sabotages; the development population, X6 and X7 get
their prefixes in their own declarations. The serialization is
`refute-population-serialization/1`; the metadata adds `generator: "refute-population-v4/1"`, the
layout's draws (`layout`) and the domain function's measured summary (`domain`).

## 3. The acceptance criteria (plan B section 3) and their checks

Every check is deterministic code, and passes only with evidence that it examined data: it reports
its coverage (cases and cadences read); zero coverage is a failure, never a pass. Criteria 1, 4, 5
and 6 are checked on **every built case** of the acceptance population, in memory (no curve is
stored).

1. **The domain.** Every case of every class meets D1 to D5: the domain function on the built
   curve's own time stamps (per sector, from the serialized curve), and the built curve's time
   stamps and labels equal to the layout's exactly.
2. **The domain covered, every dimension.** For each of the six groups (three classes × two noise
   models), over the accepted layouts: the drawn first start, the separations (the about-one-year
   and the about-two-years intervals separately), the orbits' lengths, the orbit gaps, the blocks'
   lengths and places, the loss probabilities and the jitters populate each third of their declared
   intervals; the blocks' count takes every value 0 to 4. **Checked apart** (realized, from the
   domain function's summary, per sector): the counts of intervals with `k` = 1, 2, 3 and 4 (each
   count's thirds of its realized range, minimum to maximum over the group's sectors), the
   residuals, the orbits' lengths, the orbit gaps, the other gaps' lengths, their number per sector
   and the coverage populate each third of their realized range.
3. **Compatible layouts, by exact counts.** Within each group of section 2.2, the numbers of G-a,
   G-b short then long and G-b long then short equal the declared allocation exactly, counted from
   the cases (not inferred by a classifier); and each case's measured separations agree with its
   recorded geometry (both about one year for G-a; for G-b, the long one where its order says).
4. **The protocol's classes, mechanisms and variability.** The counts per class, noise model, band
   and mechanism (planets 180 + 180 per band; false positives 25 per mechanism of 100, and 63, 63,
   62, 62 of 250; without a transit 880, 660, 660 and 240, 180, 180); the noise and trend constants
   are `population_v2`'s objects; on every built `variability_some_years` planet, `var_absent_year`
   is one of the curve's labels at `var_absent_position` and exactly two labels carry variability
   (shown by criterion 5's reconstruction); `variability_masked` and `trend_variability` keep the
   variability in every year.
5. **The independent band check** (`band_check_v4.py`). For every built case with an injected
   transit: the per-unit-depth profile recorded in `expected_snr` (global, each label's train and
   each label's hidden SNR per unit depth, and `min_unit_ratio`) recomputed from the stored time
   stamps, labels and parameters, with the AR(1) covariance on the real time differences (for a
   blend, the crowding recomputed from the recorded scene), equal within a relative tolerance of
   1e-9; the physical SNRs (`depth ×` the profile) and `r_actual = depth × min_unit_ratio`
   recomputed and inside the case's band. For every case except blends (whose flux comes from the
   pixels): the flux reconstructed from the recorded parameters, the protocol's model (signal, then
   `× (1 + trend)`, then `+ variability`, then `+ noise`, the order of `population_v2.build_case`)
   and the declared noise stream equals the stored flux within 1e-12 absolute; for a curve without
   a transit this reconstruction contains no transit, and its parameters hold no transit parameter
   (`period`, `t0`, `depth`, `duration`).
6. **No adaptation of the signals.** On every built case: (a) the **primitive** fields drawn by
   `population_v2.draw_parameters(case, default_rng(attempt_seed), first time stamp)` equal the
   recorded ones (with `var_absent_year` mapped as section 2.2 says); the **derived** fields are
   checked apart: (b) the **attempts are replayed**: every rejected layout attempt fails the domain
   with its recorded condition and the accepted one passes; every rejected parameter attempt fails
   `_mechanism_condition` or `_place_in_band` with its recorded reason and the accepted one passes,
   its parameters after `_place_in_band` (`depth`, `r_actual`, `dilution`, the planets' `duration`
   and `ingress_fraction`) and `var_amplitude = var_amplitude_factor × depth` equal to the recorded
   ones exactly; the recorded `redraws` equal the replayed counts exactly (and criterion 5 checks
   `depth`, `r_actual` and the crowding independently); (c) on `population_v4.py`'s source, the
   modules it imports from `refute` are only `synthetic`, `params`, `types` and `domain`, the
   attributes it reads from `synthetic` and from `population_v2` belong to declared lists (none that
   runs an analysis, such as `synthetic`'s helpers that call `analyze_data`), and it never imports
   an engine module.
7. **Determinism.** The acceptance population built three times, with three worker counts and
   three different orders, gives byte-identical cases (the SHA-256 of every case, in a manifest per
   generation; the three manifests identical). The lots' populations keep the development
   manifest's rule (three generations, byte-identical) in their own declarations.
8. **The correspondence with X2f.** The time stamps of X2f's cases (`population_v2`'s `three_years`
   and `variability_some_years` layout: sectors at 1325.0, 1700.0 and 2061.0, two 13-day orbits, a
   1-day gap) pass D1 to D5, with separations 375 and 361 d (G-a), orbits of 13.0 d, an orbit gap of
   1 d plus at most one cadence, no other gap, and coverage about 0.963. One point of the domain,
   not its whole.
9. **Tests first, then the code, then the sabotages, then Codex**, before any population is
   generated for a lot. *Check:* an order check over the git history (the record's commit, then the
   tests' commit with the recorded failing first run, then the code's commit, then the sabotages'
   output); it is tested to reject an invalid sequence (code before tests, tests before the record).

## 4. The gate's evidence (no lot, no engine)

- **The acceptance population, in full:** every case of B2 under the acceptance prefix (5860)
  built in memory, checked (criteria 1, 4, 5, 6) and hashed, then discarded; criteria 2, 3 and 4's
  counts on the cases and their layouts; criterion 8. Built **three times** (criterion 7) with
  different worker counts and orders. Outputs `v4-acceptance/population.json` (the checks, their
  coverage, the redraw counts by class, band, mechanism and reason) and
  `v4-acceptance/manifest-<g>.json` (the per-case digests of each generation).
- **The sabotages:** output `v4-acceptance/sabotages.json` (section 5).
- **The order check:** output `v4-acceptance/order.json`.
- The environment is the project's current one (before the update of 2026-10-27); after that
  update the acceptance population's digests are generated again and compared, and a difference is
  recorded (a change of the numeric stack stops for the maintainer in any case).

## 5. The sabotages (each criterion broken once, and caught)

Each runs in its own process, patches one thing, runs the matching check, and records
`caught: true` only if the check fails for the reason named; each also runs the same check
unbroken on the same cases (the control), which must pass with positive coverage. None runs at the
same time as a full suite.

| # | Criterion | The sabotage (on the cases named) | Caught by, for the reason |
|---|---|---|---|
| S1 | 1 | on the selftest population, each case's accepted layout (the control's) with only its orbit gaps changed: every second orbit moved rigidly by 2.0 d, so that each orbit gap is its drawn `g` plus 2.0 d (2.5 to 4.0 d; every other cadence, label and separation as the control's, so D1 to D3 and D5 still pass) | the domain check: D4 on every case, an orbit gap above 2.0 d named, and no other condition failing |
| S2 | 2 | the first start drawn in [1325.0, 1325.0 + 365.25/3), on the acceptance population's layouts | the thirds of the first start: the middle and upper thirds empty |
| S3 | 3 | G-a given to `j mod 3 = 0`, on the acceptance population (groups of 25 to 180) | the exact allocation counts (for 63: 21 instead of 32) |
| S4 | 4 | the variability-free year left unmapped, on a `variability_some_years` planet whose drawn year (2018 to 2020) is not one of its labels (chosen by scanning the selftest population) | criterion 4 (the absent year not a label) and criterion 5's reconstruction (variability in three years) |
| S5a | 5 | the recorded global per-unit SNR multiplied by 1 + 1e-6, on one planet and one false positive | the independent band check: the global SNR's relative difference |
| S5b | 5 | a 1000 ppm box of 60 cadences added to one curve without a transit | the flux reconstruction |
| S6 | 6 | `draw_parameters` wrapped to redraw any period below 2 d, recorded as `band`, on a case whose first attempt draws a period below 2 d | the replay of the attempts (the recorded reason and count differ from the replay) |
| S7 | 7 | the noise seed mixed with the worker's process id, on the selftest population built with 1 and 2 workers | the generations' digests differ |
| S8 | 8 | the domain's about-one-year interval narrowed to 345 to 370 d | the X2f correspondence (D5, the 375 d separation) |
| S9 | 9 | an invented history with the code's commit before the tests' | the order check |

## 6. Details fixed here that plan B leaves open

1. A sector across a year boundary is not rejected (section 2.2): the generator's only rule is
   D1 to D5; plan B's parenthetical example is read as not adding a condition. **For the
   maintainer's ratification** (an editorial reading of plan B's text, not a change of D1 to D5).
2. An orbit's length uses the span's convention (last − first + one cadence).
3. The G-b order is allocated (alternating), not drawn, so the 50 : 50 is exact per group.
4. The loss blocks' count is uniform over the integers 0 to 4; a block of drawn length `ℓ` removes
   `floor(ℓ / Δ)` cadences (an interval of 720 s to 21 600 s before the jitter); blocks spare each
   orbit's ends; single losses spare each orbit's ends and each block's borders; the restoring of
   the 4th of four adjacent losses acts on the single losses only.
5. The loss probability is drawn per sector; "one year" for the first start is 365.25 d.
6. The domain function leaves out a sector without kept cadences, reads the time stamps in the
   order given (an unsorted sector fails D3) and reports an incomputable quantity as unavailable
   (it fails its condition).
