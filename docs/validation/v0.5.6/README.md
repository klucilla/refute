# v0.5.6 Apply with declared limits: records

Plan: [docs/plans/v0.5.6-plan.md](../../plans/v0.5.6-plan.md). Tracking: #218.

**Every output here is exploratory** unless a part B record says otherwise. Outputs are never
verdicts on a TOI, and never candidates in a public claim. Every result that uses the v0.5
battery carries its limits label, **"WEAKENED; does not meet D1, D2, D4, T2a"**.
`method_status: not_validated`.

| File | What it is |
|---|---|
| `part_a_frame.py` | Builds part A's frame, the split by TIC and the draw, before any light curve is read. |
| `part-a-frame.csv`, `part-a-frame.json` | The frame (one row per single-TOI star) and its record: sources, rules, exclusions, counts and SHA-256. |
| `part-a-exposure.json` | The prior-exposure scan at a fixed commit, with first evidence per TIC. It is a superset; part B fixes which evidence counts before its drand draw. |
| `part-a-draw.json` | The draw, from MAST metadata only: the 120 TICs per arm and the ordered trail of every TIC checked. |
| `part_a_run.py`, `part-a-ledger.json` | The labelled v0.5 battery on the drawn TICs (the pilot first), and the caps ledger (50 CPU-h). |
| `t3b_updated_count.py` | T3b's count of the updated frame (the addendum of 22:45, item 2): metadata only, counts only. |
| `codex_tokens.py` | The per-thread count of Codex review tokens (the decision of 22:30, item 1). |
| `part-a-records.json`, `part_a_report.py`, `part-a-report.json`, `part-a-report.md` | Part A's 240 records and TPF deletion records (unchanged, with SHA-256), and the exploratory door report. |
| `part_b_prep.py`, `part-b-prep.json`, `part-b-prep.md` | Part B's exploratory step: the REFUTED cases one by one and identity against outcome. Its prior-exposure section is superseded by `part-b-exposure.*`. |
| `part_b_exposure.py`, `part-b-exposure.json`, `part-b-exposure.md` | The prior-exposure scan, second version: all evidence per TIC, catalogue copies excluded by a written list. |
| `part-b-records.json`, `part-b-tpf-deletions.json` | Part B's 300 confirmatory records and 300 TPF deletion records (unchanged, each with the SHA-256 of its file); two files, so that each stays under 5 MB. Per-target outputs are never verdicts on a TOI. |
| `part_b_strata.py`, `part-b-strata.json` | Part B's two strata described: median and quartiles of the drawn TOIs' depth and period, from the draw (descriptive only; the maintainer's decision of 2026-11-23, item 1 (c)). |
| `verify_part_b_draw.py` | Checks part B's draw from public sources: the BLS signature, the order rebuilt from the randomness, the drawn TOIs, and (with the network) the round against the lock's time on GitHub and the drand network. |

**The phase's public report:** [docs/reports/v0.5.6-report.md](../../reports/v0.5.6-report.md)
(approved by the maintainer on 2026-11-23, #218).

**Its dated addendum:**
[docs/reports/v0.5.6-report-addendum-2026-11-23.md](../../reports/v0.5.6-report-addendum-2026-11-23.md).
- It is a new file of 2026-11-23, from v0.5.8 (exploratory). The report is not edited.
- It records how part B's events moved when the same TOIs were refitted from the TOI's ephemeris.
- The locked verdict stands as recorded.

## Part B

- The design is [amendment 1](../../plans/v0.5.6-plan-amendment-1.md), and the steps are in
  [the lock plan](../../plans/v0.5.6-part-b-lock-plan.md).
- The claim, its pool and its scripts are in
  [`calibration/v0.5.6/`](../../../calibration/v0.5.6/), with the draw (`part-b-draw.json`), the
  ledger (`part-b-ledger.json`) and the claim's verdict (`part-b-verdict.json`, `.md`).
- **The Codex review of part B** (conversation `partb`) and the independent review of its options
  are stored, with unchanged bytes, in the consensus record
  [`docs/plans/v0.5.5-consensus/`](../../plans/v0.5.5-consensus/README.md):
  - `partb-independent-review.md`;
  - `partb-round-1-answer.md` to `partb-round-3-answer.md`, and any later round;
  - see the README's sections "v0.5.6 part B". They are not moved, since their bytes are recorded.

## Data and acknowledgments

- **Sources:**
  - the TOI table and PSCompPars come from the NASA Exoplanet Archive
    ([sources](../../plans/sources/v0.5.6-toi-ephemerides-2026-11-21.md));
  - the light curves come from MAST (SPOC).
- **The TFOPWG disposition** is a descriptive column only. NExScI's answer on its use is in
  [the NExScI answer record](../../plans/sources/v0.5.6-nexsci-answer-2026-11-22.md).
- **The ExoFOP acknowledgment**, given in NExScI's answer:

  > This research has made use of the Exoplanet Follow-up Observation Program (ExoFOP; DOI:
  > 10.26134/ExoFOP5) website, which is operated by the California Institute of Technology, under
  > contract with the National Aeronautics and Space Administration under the Exoplanet
  > Exploration Program.

- **The NASA Exoplanet Archive** asks for its standard acknowledgment in published material
  ([its page](https://exoplanetarchive.ipac.caltech.edu/docs/acknowledge.html), read 2026-11-21).
- **TESS-EB rows** (T3b) are under a restricted licence (#33), so they never enter this folder;
  only counts do.
