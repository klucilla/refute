# The viability diagnosis after gate 3b: the report

The round declared in [README.md](README.md) (committed and pushed in `7d0aa76` before it ran), run
once on 2026-10-27 at 11:38 UTC on the metadata gate 3b saved: the three files' SHA-256 matched gate
3b's record, the pools' union was the 911 TICs gate 3b searched, and the recomputed classification
(the first failing condition's counts and the eligible TICs) equalled gate 3b's. Output:
[diagnosis.json](diagnosis.json) ([scripts/viability.py](scripts/viability.py)). No download, no
query, no engine, no light curve, no change to the domain.

**This report informs a proposal. It chooses no domain and authorizes no lot; plan B stays frozen,
X2f stays blocked.** Every count below is from metadata, with D3's measured intervals and D4 pending,
as in gate 3b ([../real-controls/gate-3b.md](../real-controls/gate-3b.md)).

## 0. A fact recorded for the context

Of the **4 planets refuted in v0.2's calibration**, **3 were refuted by the holdout**
(`holdout_by_year`: TOI-244 b, Kepler-447 b, TOI-6038 A b) and **1 by the eclipsing-binary
catalogue** (`eb_catalog`: Kepler-14 b). Source: `calibration/v0.2/POSTMORTEM.md`, "Result (Fact,
dossier)".

## 1. Years, sectors, spacings and extent

SPOC 120-s light-curve sectors per TIC; each sector dated by its `t_min`, its year the UTC calendar
year of `t_min`.

| | Planets (464) | False positives (447) |
| --- | ---: | ---: |
| No SPOC 120-s sector | 13 | 97 |
| 1 distinct year | 57 | 174 |
| 2 distinct years | 129 | 91 |
| **3 distinct years** | **100** | **52** |
| 4 to 7 distinct years | 165 | 33 |
| Exactly 3 sectors | 66 | 45 |
| Most sectors in one year: 1 / 2 / 3 or more | 199 / 118 / 134 | 165 / 91 / 94 |

**Sectors per observed year** (all TIC-years): planets 845 years with one sector, 294 with two, 234
with three or more (up to 13); false positives 365, 146, 160.

**Spacings** between consecutive observed years' first sectors (D5's bands closed):

| Separation | Planets | False positives |
| --- | ---: | ---: |
| below 30 d (a sector across New Year) | 36 | 25 |
| 30 to below 345 d | 164 | 59 |
| **345 to 385 d (about one year)** | **77** | **22** |
| above 385 to below 710 d | 174 | 78 |
| **710 to 750 d (about two years)** | **321** | **80** |
| above 750 d | 150 | 57 |

Between consecutive sectors (all pairs): planets 1092 adjacent (below 30 d), 130 about one year, 245
about two years; false positives 736, 45, 54.

**Temporal extent** (latest `t_max` minus earliest `t_min`, TICs with data): planets median 1488 d
(quartiles 760 and 2146 d), 105 spanning 6 years or more; false positives median 246 d (quartiles 27
and 1081 d), 185 within one year.

**A possible reason why "about two years" dominates.** TESS's observing strategy has generally
alternated between the ecliptic hemispheres: "During the extended missions, TESS continues to
alternate between the southern and northern skies" (HEASARC, *TESS Observations*,
https://heasarc.gsfc.nasa.gov/docs/tess/sector.html, read 2026-10-27), though the same page also
lists successive cycles in the same hemisphere and ecliptic sectors. A star away from the overlaps
would then often be revisited after about two years, which fits the counts above. That this
explains them is an interpretation, not tested here.

## 2. The intersections of the constraints (each evaluated on its own)

| D1 | D2 | D3p | D5 | Planets | False positives |
| :-: | :-: | :-: | :-: | ---: | ---: |
| + | + | + | + | **11** | **0** |
| + | + | + | − | 30 | 13 |
| + | − | + | − | 59 | 39 |
| − | + | + | − | 25 | 32 |
| − | − | + | − | 338 | 363 |
| − | − | − | − | 1 | 0 |

The other ten combinations are empty in both classes. Each condition alone: planets D1 100, D2 66,
D3p 463, D5 11; false positives D1 52, D2 45, D3p 447, D5 0. D5 implies D2 (it needs exactly two
separations), so every TIC passing D5 passes D2; D3p is vacuous for the TICs without sectors (among
TICs with data, planets 450 of 451 and false positives 350 of 350 pass it). **D3p never binds; D1
and D5 do.** For false positives **D5 alone excludes every TIC that passes D1 and D2** (13 of 13).

## 3. Common coverage patterns

Sectors per year from the first to the last observed year (`0` a year without a sector; `–` not
among that class's 20 most common patterns):

| Pattern | Planets | False positives |
| --- | ---: | ---: |
| `1` (one sector) | 49 | 111 |
| `none` | 13 | 97 |
| `2`, `3`, `4` (one year only) | 6, –, – | 43, 10, 10 |
| **`1-0-1`** (two sectors two years apart) | **49** | **19** |
| `2-0-1`, `3-0-2`, `2-0-2` | 12, 11, 8 | 7, –, 3 |
| `1-0-1-1`, `1-1-0-1`, `1-0-1-0-1` | 10, 5, 6 | –, –, – |
| `1-1` (two consecutive years) | 6 | 5 |
| `1-1-1` (three consecutive years, one sector each) | – | – |

Planets show 220 distinct patterns (246 TICs outside the 20 most common), false positives 108 (97
outside). The patterns are long-tailed. They are calendar patterns: the domain's geometries are
defined by the elapsed days between the sectors' starts, not by calendar years, so no pattern here
is identified with G-a or G-b. The most common sets of three
calendar years are 2021, 2022, 2024 (14 planets, 12 false positives), 2023, 2025, 2026 (13, 2) and
2020, 2022, 2024 (12, 3); full lists in `diagnosis.json`.

## 4. The metadata proxy's sensitivity

A sector starting within 2 d of a New Year: 40 planets, 18 false positives; a separation within 2 d
of one of D5's bounds: 62 and 14. **Of the 11 planets inside, 4 are in one of these cases**; of the
41 planets and 13 false positives with three years and three sectors, 9 and 1. The 2-day window is a
chosen diagnostic window, not a bound on the difference between `t_min` and the first kept cadence:
these are potentially sensitive cases, not an exhaustive set. The products' time stamps could move
some of the 11 out, or some others in.

## 5. The limits of representativeness

- **What the 911 are:** known controls, already filtered by v0.2's pools (period 0.5 to 10 d,
  depth at least 0.1% or 1000 ppm, TESS magnitude at most 12, a single known planet or a single TOI,
  the 35 excluded targets removed); 801 of the 911 have SPOC two-minute light curves (13 planets and
  97 false positives have none). They answer the calibration's question: **how many known controls
  of v0.2's kind a domain admits.**
- **The catalogue medians, descriptively** (`diagnosis.json`, nearest-rank quantiles): planets'
  TESS magnitude 11.0 in the pool, 10.7 with three years, 10.8 inside; their period 3.8, 3.7 and
  3.5 d. False positives' TESS magnitude 10.4 in the pool and 10.3 with three years; their period
  3.0 d in the pool and 3.5 d with three years. With 11 and 0 inside, no conclusion on a shift is
  drawn.
- **What they do not measure:** the reach of `refute discover`. The stars Discover would search are
  not known planets or TOIs; their two-minute coverage, years and spacings may differ. **Another
  reference population is needed, to be defined** (for example the stars with SPOC two-minute
  products in a declared range of sectors, selected without regard to known planets, or the stars of
  the full-frame images); it is not defined here, and nothing in this report estimates that reach.
- **The counts are not success rates:** a control inside the domain by metadata is a candidate for
  the calibration's selection; whether the holdout performs on it is what the calibration measures.

## 6. Availability under hypothetical rules (counted, never adopted)

| Rule | What changes | Planets | False positives |
| --- | --- | ---: | ---: |
| The domain (D1 to D5) | – | 11 | 0 |
| H1 | several sectors per year (exactly three years) | 12 | 1 |
| H2 | both separations about two years allowed | 17 | 2 |
| H3 | H1's and H2's relaxations combined | 24 | 11 |
| H6 | D5 removed alone (three years, three sectors, any spacing) | 41 | 13 |
| H4 | three or more years, every years' separation about one or two years | 38 | 13 |
| H5 | three or more years, any spacing | 264 | 85 |
| H7 (derived after the run) | exactly three years, all sectors kept, any spacing | 100 | 52 |

**H7 was not declared:** it is derived after the run from the declared intersections (section 2:
D1 and D3p passing, whatever D2 and D5; planets 11 + 30 + 59, false positives 0 + 13 + 39), and is
reported because it changes the reading. **Under the declared rules that keep exactly three years
(H1, H2, H3, H6), the false positives stay below 20 (at most 13); keeping exactly three years but
all their sectors and any spacing (H7) gives 100 and 52.** H5 gives 264 and 85. These counts are
availability, never engine outcomes; a rule chosen after reading them is chosen knowing the known
controls' availability, and is a new plan, not a widening of this attempt (plan B, sections 5 and
8).

## 7. Alternatives for the maintainer's decision (none chosen here)

Each needs the maintainer's explicit decision to end or replace this attempt, the preservation of
gate 3b's result, and a new declared plan. Costs are **estimates**; the LP-h and hours of plan B's
steps are from [../plan-b/budget-b.json](../plan-b/budget-b.json), at their ceilings and planning
(minimum) sizes. **The budget's snapshot** (plan B's adoption, 2026-10-23; not verified as a
current balance): 491.1 LP-h consumed, so 3508.9 LP-h of the 4000 LP-h ceiling unspent; 1888.3 LP-h
of headroom after reserving plan B's own future steps. A replacement's **total** future cost
compares with the unspent ceiling (less what was consumed since); its cost **above** plan B's
reserved steps compares with the headroom. None of the subtotals below includes gate 13 (the real
calibration, with its own budget).

### A. Keep the domain; widen the source of known controls (both classes)

- **What:** gate 3b's check again on v0.2's classes without the period, depth, magnitude and
  multiplicity filters (3666 planet TICs and 1302 false-positive TICs after the exclusions, counted
  in gate 3b, never searched), or on another declared source of known false positives. The domain,
  the generator and every synthetic gate stay as they are; the calibration's population changes
  (longer periods, shallower or fainter signals), which gate 13's protocol would have to accept.
- **Implementation:** small: a declaration and the gate 3b script with the wider pools (about half a
  day).
- **Validation:** MAST searches for the about 4100 TICs of the wider classes not yet searched
  (3666 + 1302 − 911; gate 3b searched 911 in 32 min: about 2.5 h, queries only, 0 LP-h); then, if
  the minimum is reached, a declared timestamp check of D3 and D4 on the candidates (downloads; its
  own declaration and budget; **its cost not estimated here**). Plan B's later gates unchanged.
- **Closing rule:** abandoned if either class stays below 20 inside by metadata in the wider pools,
  or below 20 after the timestamp check; no further widening of the sources follows.
- **What the diagnosis says about its odds:** in v0.2's pools, 0 of 447 false positives are inside
  and D5 excludes all 13 with three years and three sectors; the in-domain rate is 2.4% for planets.
  The wider pools share TESS's observing strategy, but their coverage distribution is not known.

### B. A new profile: exactly three one-sector years, any spacing (H6)

- **What:** D1, D2, D3 and D4 kept; D5 removed (or widened to the observed spacings). By metadata,
  41 planets and **13 false positives**: the false-positive minimum is **not** reached in v0.2's
  pools, so B needs A's wider sources as well.
- **Implementation:** the domain function and `population_v4`'s layouts (new geometries: two long
  separations, separations of three years or more, separations under 345 d), their acceptance
  record, tests, sabotages and Codex (gate 1 again), and gate 2 (the profile): about two to three
  days of work.
- **Validation:** plan B's gates 1 to 12 on the new populations, at least plan B's steps from the
  populations on (the populations 75.3 LP-h, X2f 302.5, spec C's confirmation 302.5, X3 33.4, X5
  38.5, the comparisons 77.0, X6 150.4, X7 150.4, the suites 490.7: about 1621 LP-h and 72 h,
  excluding A's searches and timestamp check and gate 13), plus a possible increase of X6's and X7's
  sizes if the new geometries were to need their own coverage (an assumption: plan B confirms a
  mixture, not each geometry). The longer separations lengthen the extrapolation's lever, on which
  the stopped fraction depends steeply
  ([../viability/two-year-results.md](../viability/two-year-results.md)): the holdout's power at
  those levers is not known.
- **Closing rule:** abandoned if A's sources leave fewer than 20 false positives under B's domain,
  or at the first failed gate (spec C's confirmation, X6 or X7), with no second relaxation of the
  domain.

### C. A new profile: exactly three observing years, every sector kept, any spacing (H7)

- **What:** D1 kept (exactly three years, never a selection of three out of more), D3 and D4 kept;
  D2 and D5 removed: every sector of the three years kept, any number per year, any spacing. By
  metadata in v0.2's pools, **100 planets and 52 false positives** (H7, derived after the run from
  the declared intersections, so its count is post hoc): the minimum reached without widening the
  sources.
- **Implementation:** the domain function and `population_v4`'s layouts with several sectors per
  year (up to 13 in these controls) and free spacings, their acceptance record, tests, sabotages and
  Codex (gate 1 again), and gate 2; the engine's holdout is already defined per observing year
  (`holdout.py`, line 1837), and how it behaves on years of several sectors is part of what the
  validation would measure. About three to five days of work.
- **Validation:** as B (about 1621 LP-h and 72 h at plan B's floors, gate 13 excluded), with a
  larger uncertainty: years of several sectors change each hidden year's coverage and the train
  set's length, so X6's and X7's necessary sizes may grow, not measured here.
- **Closing rule:** abandoned if the timestamp check of D3 and D4 on its candidates leaves fewer
  than 20 per class, or at the first failed gate, with no further relaxation.

### D. A new profile over every observed year (H5)

- **What:** three or more observing years, every sector kept, any spacing. By metadata in v0.2's
  pools, **264 planets and 85 false positives**. The engine already runs the holdout on any number
  of years (two or more; `holdout.py`, lines 1911 to 1916); plan B restricted it to three for
  validation.
- **Implementation:** a new generator of layouts over 3 to 7 years and up to 13 sectors a year, a
  new domain function and its acceptance: a new population study design rather than an amendment
  (about one to two weeks of work).
- **Validation:** a new sizing; plan B's step figures do not transfer. Its total future cost
  compares with the unspent ceiling (3508.9 LP-h at the snapshot, less what was consumed since);
  whether it fits is not estimated here.
- **Closing rule:** abandoned if its declared sizing does not fit the unspent ceiling at its
  planning gate, or at the first failed confirmation; no further widening.

### Also possible: end the real calibration path of this profile

**If the maintainer records that decision**, plan B ends at gate 3b; no further scientific
execution follows under it; the profile stays proposed for validation and not calibrated; the
synthetic gates' code and records are kept. It costs nothing further, and v0.2.1's exit criterion of
a real calibration stays unmet under this profile.
