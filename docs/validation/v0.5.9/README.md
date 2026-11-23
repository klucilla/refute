# v0.5.9 Ephemeris entry: exploratory prototype (records)

Plan: [docs/plans/v0.5.9-plan.md](../../plans/v0.5.9-plan.md). Tracking: #218.

**Everything here is exploratory:**
- an output is never a verdict on a TOI, a candidate or a disposition;
- every record carries the limits label **"WEAKENED; does not meet D1, D2, D4, T2a"** and
  `method_status: not_validated`;
- nothing here changes `src/`, the v0.5 battery's tests, thresholds or rules, or any verdict.

| File | What it is |
|---|---|
| `prototype_run.py` | The prototype: the set's draw, the two entry modes, the fixed evaluation, the six probes, the consensus rule and the centroid guard, with the run's caps. It imports v0.5.7's `seeded_run.py`, v0.5.8's `stability_report.py` and the battery without editing them. Steps: `draw`, `run`, `bundle`, `clean`. |
| `prototype_report.py` | The five questions and their counting rules, fixed before any result. |
| `prototype-set.json` | The 24 TOIs, written once by `draw` after the seed was committed. *(Added by the draw.)* |
| `prototype-ledger.json`, `prototype-records.json`, `prototype-units.json`, `prototype-report.json`, `prototype-report.md` | The run's ledger, the 48 mode records, the unit records and the report. *(Written by the run, after the maintainer's approval.)* |

The tests are in `tests/v059/`.

**The Codex rounds** are in the consensus record
[docs/plans/v0.5.9-consensus/](../../plans/v0.5.9-consensus/README.md).

## Data and acknowledgments

- **TOIs and their ephemerides:** v0.5.6's frozen frame, from the NASA Exoplanet Archive's TOI
  table.
- **Light curves and pixel files:** SPOC products at MAST. None is kept here.
- **The acknowledgments** (ExoFOP, the NASA Exoplanet Archive and MAST) are given in full in
  [the v0.5.8 report](../../reports/v0.5.8-report.md#data-and-acknowledgments).
