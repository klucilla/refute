# The viability diagnosis after gate 3b: the declaration

Requested by the maintainer on 2026-10-27, after recording gate 3b's result
([../real-controls/gate-3b.md](../real-controls/gate-3b.md): 11 planets and 0 false positives
inside D1 to D5 by metadata, against 20 + 20; X2f blocked). **One round**, declared here and
committed and pushed before it runs, reviewed by Codex before the commit and again on its report.
Script: [scripts/viability.py](scripts/viability.py); output `diagnosis.json`; report `report.md`,
next to this file.

## What it is, and what it never does

It **informs a proposal**; it does not choose a domain, does not authorize a lot, and changes
nothing in plan B, which stays frozen. Any new domain needs an explicit decision of the maintainer
to end or replace this attempt, the preservation of gate 3b's result, and a new declared plan.

**Only the metadata gate 3b saved**, under `.cache/real-controls/`: `pscomppars.csv`,
`exofop_toi.csv` and `mast-rows.json`, each checked first against the SHA-256 recorded in
[../real-controls/result.json](../real-controls/result.json); the script then recomputes gate 3b's
pools (464 planets, 447 false positives; their union must be the 911 TICs gate 3b searched) and
classifications (the first failing condition's counts and the eligible TICs themselves), which
must equal the recorded ones, or it stops. **No download, no query, no engine, no light curve, no change to the domain.**

## A fact recorded for the context (the maintainer's request)

Of the **4 planets refuted in v0.2's calibration**, **3 were refuted by the holdout**
(`holdout_by_year`: TOI-244 b, Kepler-447 b, TOI-6038 A b) and **1 by the eclipsing-binary
catalogue** (`eb_catalog`: Kepler-14 b, a TESS-EB listing at its own period). Source:
[calibration/v0.2/POSTMORTEM.md](../../../../../../calibration/v0.2/POSTMORTEM.md), "Result (Fact,
dossier)", the table's rows for those four targets.

## The quantities (fixed before the run)

Per class, on the SPOC 120-s light-curve sectors of each of gate 3b's TICs, each sector dated by its
`t_min` (MJD) and labelled by the UTC calendar year of `t_min`, as gate 3b did:

1. **Years and sectors:** the number of distinct years per TIC; the number of sectors per TIC; the
   number of sectors in each observed year; the most sectors in one year.
2. **Spacings:** every separation between consecutive sectors' `t_min`, and every separation
   between consecutive observed years' first sectors, in the bins below 30 d (adjacent sectors),
   30 to below 345, 345 to 385 (about one year, D5's band, both ends included), above 385 to below
   710, 710 to 750 (about two years, D5's band, both ends included), above 750 d.
3. **Temporal extent:** the latest `t_max` of any sector (its `t_min` when absent) minus the
   earliest `t_min`: its quantiles (0, 10, 25, 50, 75, 90, 100%) and its count by whole years of
   365.25 d (0-1 to 5-6, and 6 or more). A non-finite `t_max`, or one before its `t_min`, stops
   the script.

**The quantile convention** (items 3 and 7): the value of rank `round_half_up((n - 1) q)` in the
sorted list (nearest rank, no interpolation, so a median of an even count is the upper middle
value), recorded to three decimals.
4. **The intersections of the constraints**, each evaluated on its own (not only the first one
   failing): D1 (exactly three distinct years), D2 (exactly three sectors), D3p (a target pixel
   file for every light-curve sector; vacuous for a TIC without sectors, so reported also among the
   TICs with data), D5 (exactly two separations, each about one or two years, at most one about two
   years, as gate 3b); the count of each of the 16 pass/fail combinations, and of each condition
   passing.
5. **Coverage patterns:** the sectors per year from the first to the last observed year, written
   for example `1-1-1`, `2-0-1` or `none`; the 20 most common per class with their counts, the
   number of distinct patterns, the TICs outside the 20; and, for the TICs with three years, the 15
   most common sets of calendar years.
6. **The proxy's sensitivity:** the TICs with a sector starting within 2 d of a New Year, and with
   a separation within 2 d of one of D5's bounds (345, 385, 710, 750 d); how many of those are
   inside by metadata, or have three years and three sectors. The 2-day window is a **chosen
   diagnostic window**: nothing here bounds the difference between `t_min` and a sector's first
   kept cadence by two days, so these are potentially sensitive cases, **not an exhaustive set of
   possible reclassifications**.
7. **For the representativeness limits:** the catalogue's TESS magnitude and period quantiles, for
   the pool, the TICs with any SPOC 120-s sector, those with three years, and those inside.
8. **Hypothetical rules H1 to H6, counted, never adopted** (each on the metadata, with D3's measured
   intervals and D4 still pending as in gate 3b):
   - **H1, several sectors per year:** exactly three distinct years; any number of sectors in each,
     all kept; a target pixel file for every sector; D5 on the separations between the years'
     first sectors.
   - **H2, both separations about two years:** D1, D2 and D3p as the domain; each of the two
     separations about one or two years, with no limit on how many are about two years.
   - **H3, both relaxations combined** (not the logical intersection of H1 and H2, since H2 needs
     exactly three sectors): exactly three years, any sectors in each, the years' first sectors
     separated by about one or two years each, no limit on the long ones.
   - **H4, three or more years:** at least three distinct years, all kept; a target pixel file for
     every sector; every separation between consecutive years' first sectors about one or two
     years.
   - **H5, three or more years, any spacing:** at least three distinct years and a target pixel
     file for every sector (an upper bound for an engine whose holdout handles any number of years
     and any spacing).
   - **H6, D5 removed alone:** D1, D2 and D3p as the domain, any spacing (it separates the effect
     of the spacings from that of more sectors or more years).
   The TIC lists of H1, H2, H3 and H6 are recorded.

**What the hypothetical counts are, and are not.** They describe how the known controls fall under
other rules; they are **availability counts, never engine outcomes**, and they are **not**
widenings of this attempt's domain, which plan B forbids. A rule chosen after reading them would be
chosen with knowledge of the known controls' availability, and the report says so wherever it uses
them.

## The report (`report.md`)

- the quantities 1 to 8 (with the counts of H1 to H6), separated for planets and false positives;
- the intersections of the constraints and the common coverage patterns, with the number of
  controls of each class in each;
- **the limits of representativeness** of the 911 targets: they serve the calibration's question
  (how many known controls a domain admits); they do not measure the reach of `refute discover`,
  for which another reference population is needed, to be defined (for example stars with SPOC
  120-s data selected without regard to known planets), and is not defined here;
- **two or three concrete alternatives**, each with an estimated **implementation cost**, a
  **validation cost** (the gates of plan B it would redo, in LP-h and wall time from
  [../plan-b/budget-b.json](../plan-b/budget-b.json) where they apply, labelled as estimates), and a
  **closing rule** (the declared condition under which the alternative is abandoned);
- the fact recorded above.

The report proposes; the maintainer decides. Nothing in it starts a gate.
