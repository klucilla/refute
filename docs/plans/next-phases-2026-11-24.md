# The next phases: a proposal (2026-11-24)

**A proposal only.** Nothing here opens a phase: opening any phase is the maintainer's decision.
It follows the research of 2026-11-23 and Codex's recommended order
([docs/plans/research-2026-11-23/](research-2026-11-23/README.md)), as recorded by the
maintainer's decision of 2026-11-24 (#218, comment 7122240195), item 4. Phases opened from now on
follow "Process diet 2" (CLAUDE.md and ROADMAP.md).

## The recommended order

1. **Finish v0.5.9** within its approved exploratory scope: the run, its report and the draft
   specification of battery version 5, with the corrected recounts of the research.
2. **An exploratory phase of counting and feasibility:**
   - **reproduce by a committed script** the numbers of section 2 of the research;
   - **route (e), feasibility:**
     - the transit windows predicted in new sectors: visibility, cadence, product and dates;
     - the synthetic acceptance of the directed evaluator, pending since v0.2.1;
   - **route (d1), census:** KELT false positives against planets found outside TESS, with SPOC
     2-minute data and not exposed;
   - **the Kepler field, census:** KOIs with a certified false positive and confirmed planets, by
     TESS product (2-minute, SPOC FFI, TGLC), by brightness and depth.
3. **Route (e) first,** if it clears its gates.
4. **Battery version 5 in two levels:**
   - a screen calibrated on the population, where "not assessed" is never a PASS;
   - today's verdict, unchanged.
   - Then a pilot, a pre-registered acceptance, a blind review and a lock.
5. **The battery's first independent claim** through route (d1), or through Kepler if the census
   shows more targets.

## Engines (none is run; running third-party code is the maintainer's stop)

- **exoVetter** (licence BSD-3-Clause, *not confirmed*): a candidate metric provider.
- **LEO-Vetter** and **transit-diffImage** (licence GPL-3.0, *not confirmed*): external comparators
  only.
- **TRICERATOPS:** informational only.

The licences stay "not confirmed" until a `sources/` record holds each one's URL, retrieval date
and a literal excerpt (CLAUDE.md, rule of issue #34).

## Rules carried from v0.5.10 (added 2026-11-24)

By the maintainer's decision of 2026-11-24 received at 17:50 local (#218, comment 7144131066),
item 3. v0.5.10 closed with declared limits (gate `REFUTED`; its report, section 8). These rules
are to be written into the next charter:
- **(a) Route (d1)'s groups are derived again,** with full provenance, and frozen before any lock.
  v0.5.10's counts are not used as the frame.
- **(b) Every aggregation, invalid-value and availability rule is fixed and committed before the
  first run.**
- **(c) One immutable copy per version of each worker,** with its hash and the configuration's hash
  recorded in every run.
- **(d) Any repetition, including after a bug, needs prior approval in an issue.**
- **(e) CPU, downloads and disk are measured along the whole path,** not only in the tools.

**v0.5.10's ranking of the routes is provisional:** (d1) first, then (e), then the Kepler field
([docs/reports/v0.5.10-report.md](../reports/v0.5.10-report.md), sections 3 and 5). It replaces
nothing in the order above; the next charter chooses.
