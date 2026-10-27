# Gate 3b: the recorded result

**Recorded by the maintainer's decision of 2026-10-27**, on the check's result (`320ab8b`,
[result.md](result.md)).

**The result of gate 3b:** in the metadata screening, **11 confirmed planets and 0 known false
positives** are candidates inside D1 to D5, against the minimum of 20 + 20. **The minimum is not
reached.**

**Its qualifications:**

- It is a **screening by metadata**, not a complete check of D1 to D5: D3's measured intervals and
  D4 need the products' time stamps, and `t_min` approximates the first kept cadence, which can
  classify some cases differently (D1's year labels, D5's separations near a bound).
- The 911 targets are **known controls already filtered** by period, depth, magnitude and
  multiplicity (v0.2's pools), **not a sample of the stars Refute could search**. The result says
  how many calibration controls the domain admits; it says nothing about the domain's reach for
  `refute discover`.

**What follows from it (plan B, sections 5 and 8):**

- **X2f stays blocked**; no lot runs.
- **The domain does not change**, and **plan B stays frozen**.
- Any new domain needs an explicit decision of the maintainer to end or replace this attempt, the
  preservation of this result, and a new declared plan.

A diagnosis of viability from the saved metadata (no new download) was requested on the same day;
it informs a proposal and does not choose a domain or authorize a lot:
[../viability-3b/README.md](../viability-3b/README.md).
