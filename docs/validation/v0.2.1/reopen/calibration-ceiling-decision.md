# The ceiling of execution and the timing lot of the calibration population (2026-10-17)

Status: **the maintainer's decision**, taken on 2026-10-17 on the sizing of revision 4
(`calc/calibration_sizing_rev4.py`, `calc/calibration-sizing-rev4.json`, commit `f4d0037`), before
any case of the calibration population of the estimators is generated.

## The decision

1. **Ceiling of execution: 397 hours** of machine time (the sizing's worst case, about 317 h, times
   1.25), for everything the calibration population of revision 4 needs: the generation and the
   evaluations of the selection part (with its one enlargement), the reserve R4 and, if M5 is
   measured, R5. It is counted on logical processors 0 to 7 with 6 workers while v0.3 is not sealed;
   a wider affinity, when the maintainer releases it, counts its machine hours the same way.
2. **Reaching the ceiling stops the work** and goes to the maintainer as a package (where it stands,
   what is left, the measured rates). Nothing is cut, enlarged or skipped to stay under it; no
   criterion, size or limit changes because of it.
3. **A timing lot first.** Before the calibration population is generated, and after the M4 code
   exists, the real cost per case is measured on a small lot, so that the declared factor of the new
   methods (2, in the sizing) is replaced by a measurement before the ceiling is relied on.

## The timing lot (declared now, before it exists)

- **What it measures:** only time: seconds per light curve and worker, for the M4 candidate code,
  under the same plan as the calibration evaluations, on logical processors 0 to 7 with 6 workers.
  No condition, pull, rate or verdict of the lot is examined or recorded beyond the timing, and no
  setting is chosen with it.
- **Cases:** 60 light curves, 10 for each pair of family (planets without variability, planets with
  variability, null) and noise model (white, correlated), from the generator of the population
  harness, under the seed prefix `refute-v0.2.1-timing`, distinct from the development
  (`refute-v0.2.1-population-dev`), confirmation and calibration prefixes; never reused for anything
  else.
- **Record:** a dated file with the code commit, the plan, the per-case times and their median, and
  the recomputed worst case with the measured rate in place of the factor 2.
- **Rule:** if the recomputed worst case exceeds 397 hours, the work stops and goes to the maintainer
  before any calibration case is generated.
