# Refute v0.4 pilot: report (draft for the maintainer, not published)

`method_status: not_validated`. No result here establishes a new astrophysical object;
no signal is called a planet. Verdicts come only from the locked code (claim
`d2ce83808eb0…`, lock commit B `65e4363`).
Prepared at P5; publication is the maintainer's (P7).

## Rounds and decisions

| Item | Value | Record |
|---|---|---|
| R_sel | round 6598335 | `selection/selection.json` |
| R_inj | round 6600947 (2026-10-31T15:10:30Z) | `runs/r_inj.json` |
| (N, K) | {'K': 20, 'N': 100} | `runs/n_k.json` |
| R_prom | round 6601360 | `runs/promotion.json` |

## Controls

| Control | Kind | Identity (factor) | Stage-2 verdict | Temporal diagnostic | Review |
|---|---|---|---|---|---|
| TIC-86396382 | planet | yes (1.0) | WEAKENED | pass | OBJECTIONS |
| TIC-393911494 | false_positive | yes (1.0) | REFUTED | pass | OBJECTIONS |

## Funnel stage 1 (denominators)

- Run: 100 stars (N = 100); gate passed: 13.
- Eligible: 5; promoted by the cap (3, R_prom draw): TIC-88096786, TIC-286480954, TIC-406413408; not evaluated past stage 1 (cap): TIC-44743595, TIC-146613141.
- Eligibility reasons (funnel.stage1_eligibility):

  - 5: eligible
  - 2: insufficient data to decide: odd_even
  - 1: insufficient data to decide: systematics
  - 87: no significant signal in these data
  - 5: signal with a likely alternative explanation, by the test(s) period_alias

## Promoted stars, stage 2

| Star | Stage-2 verdict | Reason | Temporal diagnostic | Review |
|---|---|---|---|---|
| TIC-88096786 | REFUTED | fatal failure in: centroid_shift | fail | SERIOUS OBJECTIONS |
| TIC-286480954 | WEAKENED | warning failure in: plausibility | inconclusive | SERIOUS OBJECTIONS |
| TIC-406413408 | SURVIVED (not support for the candidate: by the independent review, fatal tests without the power to fail and a signal not distinguished from noise; #185, #184) | every test passed | inconclusive | SERIOUS OBJECTIONS |

## Conclusions (approved by the maintainer on 2026-11-01)

The verdicts above come from the locked code and no review changes them. The
conclusions below are the human reading of each case (closed vocabulary, protocol
section 1), drafted by the agent, checked with Codex and approved by the maintainer,
with the caveats given; TIC-88096786's was set by the maintainer.

- **TIC-86396382**: signal matches a known object: WASP-12 b (the planet control); signal identity recovered at factor 1.
  Caveat: the WEAKENED comes from warnings that do not discriminate the signal; 0 of 20 injections were recovered on this curve, which does not measure sensitivity; factor 1 identifies the catalogued signal and is not a new confirmation.
- **TIC-393911494**: signal matches a known object: TOI-2106.01 (the false-positive control); signal identity recovered at factor 1.
  Caveat: factor 1 recovers the catalogued signal; it does not settle whether the signal is on the target or on the neighbor 2.84 arcsec away, nor the physical orbital period; the REFUTED (odd_even) stands.
- **TIC-88096786**: insufficient data to decide: the astrophysical origin of the signal is unresolved, because the only fatal failure (centroid_shift) comes from a sector whose measurement may be artifact-dominated.
  The deterministic verdict stays REFUTED, the label of the locked battery (the maintainer's decision of 2026-11-01). The conclusion is the human reading of the case: the battery's only fatal failure does not settle where the signal comes from.
- **TIC-286480954**: insufficient data to decide: stellar variability is a plausible alternative supported by independent review; the locked battery does not distinguish it adequately from a transit.
  The deterministic verdict stays WEAKENED (the plausibility warning). The conclusion is the human reading of the case.
  Caveat: stellar variability is a hypothesis supported by the independent review, with no stellar classification established; the deterministic verdict stays WEAKENED.
- **TIC-406413408**: signal survived the declared decisive battery; temporal diagnostic: inconclusive; method not validated.
  This SURVIVED is not support for the candidate. It means only that no decisive test failed. By the independent review's estimates (no validated power rule; #185), several fatal tests (aperture_depth, centroid_shift, secondary_eclipse, odd_even) lacked the power to fail, and the review found the signal not distinguished from this light curve's noise or systematics (#184).

## Reproduction (acceptance criterion 2)

Criterion 2 is met here through the approved substitution of the instructions (the maintainer's Option 1 of 2026-11-01): its text names REPRODUCE.md, and the five stage-2 dossiers were re-run by following literally the instructions of the annex `reproduce-2` (REPRODUCE-2.md, which supersedes the core's REPRODUCE.md without amending the criterion, because that file is written by the locked run.py; #189), in a clean clone from GitHub at commit 95cd7d9 (CI green), with a fresh data cache. Every input a clone lacks was fetched and checked by SHA-256 by `calibration/v0.4/reproduce_inputs.py prepare`, and nothing was placed by hand. The TESS-EB table was downloaded afresh from the VizieR CfA mirror (Strasbourg being unreachable); its content matched the frozen edition, and its four header metadata lines (server, two dates, request URL) were restored to the frozen values recorded in inputs.json before the raw hash was checked, as the approved design specifies. Each result is attached to its original dossier as the annex `reproduction-2`. The first attempt (annex `reproduction`) does not count for criterion 2: files were placed by hand.

| Dossier | check-dossier --against |
|---|---|
| TIC-286480954 | OK: manifest intact; key results reproduced |
| TIC-393911494 | OK: manifest intact; key results reproduced |
| TIC-406413408 | OK: manifest intact; key results reproduced |
| TIC-86396382 | OK: manifest intact; key results reproduced |
| TIC-88096786 | OK: manifest intact; key results reproduced |

Before P7 the two zips the instructions fetch (the 100 stage-1 verdicts and the five original stage-2 dossiers) are in the maintainer's private archive. How they are made available, and under which terms, waits for the maintainer's decision: the stage-2 originals hold third-party catalog values (Gaia DR3 rows, one TESS-EB record, TOI periods from ExoFOP). Until then a third party cannot run the instructions.

## Injection-recovery per curve (stage 1)

Sampling unit: one injection into that curve; injections into one curve are not
independent stars. Across curves the numbers are descriptive only. A curve whose own
signal passes the gate (marked *) measures whether an injection outranks that signal,
not sensitivity (#180): the search keeps one candidate.

| Curve | Recovered / injections | Rate | Wilson 95 % | Declared aliases | CROWDSAP missing |
|---|---|---|---|---|---|
| TIC-86396382* | 0 / 20 | 0 % | [0 %, 16 %] | 1 | 0 |
| TIC-393911494* | 7 / 20 | 35 % | [18 %, 57 %] | 0 | 0 |
| TIC-100610422* | 15 / 20 | 75 % | [53 %, 89 %] | 0 | 0 |
| TIC-120900130 | 6 / 20 | 30 % | [15 %, 52 %] | 0 | 0 |
| TIC-122616851 | 19 / 20 | 95 % | [76 %, 99 %] | 0 | 0 |
| TIC-138651299 | 19 / 20 | 95 % | [76 %, 99 %] | 0 | 0 |
| TIC-140123544 | 19 / 20 | 95 % | [76 %, 99 %] | 0 | 0 |
| TIC-140867523 | 16 / 20 | 80 % | [58 %, 92 %] | 0 | 0 |
| TIC-140899383 | 18 / 20 | 90 % | [70 %, 97 %] | 0 | 0 |
| TIC-141121044 | 15 / 20 | 75 % | [53 %, 89 %] | 0 | 0 |
| TIC-141944911 | 16 / 20 | 80 % | [58 %, 92 %] | 0 | 0 |
| TIC-142440081 | 14 / 20 | 70 % | [48 %, 85 %] | 0 | 0 |
| TIC-142727252 | 11 / 20 | 55 % | [34 %, 74 %] | 1 | 0 |
| TIC-146613141* | 17 / 20 | 85 % | [64 %, 95 %] | 0 | 0 |
| TIC-147617419 | 10 / 20 | 50 % | [30 %, 70 %] | 0 | 0 |
| TIC-148002142 | 14 / 20 | 70 % | [48 %, 85 %] | 0 | 0 |
| TIC-14802455 | 16 / 20 | 80 % | [58 %, 92 %] | 0 | 0 |
| TIC-149968737 | 13 / 20 | 65 % | [43 %, 82 %] | 0 | 0 |
| TIC-150249543 | 12 / 20 | 60 % | [39 %, 78 %] | 1 | 0 |
| TIC-150250788* | 11 / 20 | 55 % | [34 %, 74 %] | 1 | 0 |
| TIC-154257406 | 20 / 20 | 100 % | [84 %, 100 %] | 0 | 0 |
| TIC-156118042 | 16 / 20 | 80 % | [58 %, 92 %] | 0 | 0 |
| TIC-158175179* | 16 / 20 | 80 % | [58 %, 92 %] | 0 | 0 |
| TIC-158461758 | 14 / 20 | 70 % | [48 %, 85 %] | 0 | 0 |
| TIC-158636944 | 10 / 20 | 50 % | [30 %, 70 %] | 0 | 0 |
| TIC-162582602 | 8 / 20 | 40 % | [22 %, 61 %] | 0 | 0 |
| TIC-166087356 | 18 / 20 | 90 % | [70 %, 97 %] | 0 | 0 |
| TIC-166151416 | 16 / 20 | 80 % | [58 %, 92 %] | 0 | 0 |
| TIC-166761808 | 17 / 20 | 85 % | [64 %, 95 %] | 0 | 0 |
| TIC-167755099 | 18 / 20 | 90 % | [70 %, 97 %] | 1 | 0 |
| TIC-198407396 | 19 / 20 | 95 % | [76 %, 99 %] | 0 | 0 |
| TIC-202295593 | 17 / 20 | 85 % | [64 %, 95 %] | 0 | 0 |
| TIC-210464356 | 14 / 20 | 70 % | [48 %, 85 %] | 1 | 0 |
| TIC-219404837 | 14 / 20 | 70 % | [48 %, 85 %] | 0 | 0 |
| TIC-219407250 | 12 / 20 | 60 % | [39 %, 78 %] | 0 | 0 |
| TIC-229943561 | 8 / 20 | 40 % | [22 %, 61 %] | 0 | 0 |
| TIC-230068646 | 13 / 20 | 65 % | [43 %, 82 %] | 1 | 0 |
| TIC-232623880 | 18 / 20 | 90 % | [70 %, 97 %] | 0 | 0 |
| TIC-232966887 | 13 / 20 | 65 % | [43 %, 82 %] | 0 | 0 |
| TIC-233045207 | 19 / 20 | 95 % | [76 %, 99 %] | 0 | 0 |
| TIC-233231885 | 11 / 20 | 55 % | [34 %, 74 %] | 0 | 0 |
| TIC-233747343 | 12 / 20 | 60 % | [39 %, 78 %] | 0 | 0 |
| TIC-236778955* | 1 / 20 | 5 % | [1 %, 24 %] | 0 | 0 |
| TIC-23708215 | 12 / 20 | 60 % | [39 %, 78 %] | 0 | 0 |
| TIC-240171830 | 17 / 20 | 85 % | [64 %, 95 %] | 0 | 0 |
| TIC-24607925 | 17 / 20 | 85 % | [64 %, 95 %] | 0 | 0 |
| TIC-248356317 | 13 / 20 | 65 % | [43 %, 82 %] | 1 | 0 |
| TIC-25155713 | 12 / 20 | 60 % | [39 %, 78 %] | 0 | 0 |
| TIC-25382939 | 13 / 20 | 65 % | [43 %, 82 %] | 0 | 0 |
| TIC-255927008 | 12 / 20 | 60 % | [39 %, 78 %] | 0 | 0 |
| TIC-258827696 | 13 / 20 | 65 % | [43 %, 82 %] | 0 | 0 |
| TIC-264252839 | 11 / 20 | 55 % | [34 %, 74 %] | 0 | 0 |
| TIC-267039954 | 18 / 20 | 90 % | [70 %, 97 %] | 2 | 0 |
| TIC-269533563 | 12 / 20 | 60 % | [39 %, 78 %] | 0 | 0 |
| TIC-281426580* | 10 / 20 | 50 % | [30 %, 70 %] | 2 | 0 |
| TIC-281574170 | 16 / 20 | 80 % | [58 %, 92 %] | 0 | 0 |
| TIC-281709735 | 20 / 20 | 100 % | [84 %, 100 %] | 0 | 0 |
| TIC-28289264 | 12 / 20 | 60 % | [39 %, 78 %] | 0 | 0 |
| TIC-286480954* | 4 / 20 | 20 % | [8 %, 42 %] | 0 | 0 |
| TIC-29267852 | 10 / 20 | 50 % | [30 %, 70 %] | 0 | 0 |
| TIC-298001089 | 17 / 20 | 85 % | [64 %, 95 %] | 0 | 0 |
| TIC-300142911 | 15 / 20 | 75 % | [53 %, 89 %] | 0 | 0 |
| TIC-321476318* | 12 / 20 | 60 % | [39 %, 78 %] | 0 | 0 |
| TIC-323296004 | 16 / 20 | 80 % | [58 %, 92 %] | 0 | 0 |
| TIC-326209514 | 12 / 20 | 60 % | [39 %, 78 %] | 0 | 0 |
| TIC-334900819 | 15 / 20 | 75 % | [53 %, 89 %] | 0 | 0 |
| TIC-336265633 | 9 / 20 | 45 % | [26 %, 66 %] | 1 | 0 |
| TIC-349577085 | 17 / 20 | 85 % | [64 %, 95 %] | 0 | 0 |
| TIC-349682621 | 13 / 20 | 65 % | [43 %, 82 %] | 0 | 0 |
| TIC-354822931 | 12 / 20 | 60 % | [39 %, 78 %] | 0 | 0 |
| TIC-356241506 | 14 / 20 | 70 % | [48 %, 85 %] | 0 | 0 |
| TIC-356683052 | 20 / 20 | 100 % | [84 %, 100 %] | 0 | 0 |
| TIC-358713436 | 15 / 20 | 75 % | [53 %, 89 %] | 0 | 0 |
| TIC-364129259 | 19 / 20 | 95 % | [76 %, 99 %] | 0 | 0 |
| TIC-372045060 | 18 / 20 | 90 % | [70 %, 97 %] | 0 | 0 |
| TIC-37774136 | 18 / 20 | 90 % | [70 %, 97 %] | 0 | 0 |
| TIC-380039482 | 13 / 20 | 65 % | [43 %, 82 %] | 0 | 0 |
| TIC-381981543 | 17 / 20 | 85 % | [64 %, 95 %] | 0 | 0 |
| TIC-383646543 | 11 / 20 | 55 % | [34 %, 74 %] | 0 | 0 |
| TIC-387512509 | 13 / 20 | 65 % | [43 %, 82 %] | 1 | 0 |
| TIC-388198210 | 15 / 20 | 75 % | [53 %, 89 %] | 0 | 0 |
| TIC-394103866 | 13 / 20 | 65 % | [43 %, 82 %] | 0 | 0 |
| TIC-396607112 | 9 / 20 | 45 % | [26 %, 66 %] | 0 | 0 |
| TIC-397000139 | 20 / 20 | 100 % | [84 %, 100 %] | 0 | 0 |
| TIC-405483372 | 14 / 20 | 70 % | [48 %, 85 %] | 0 | 0 |
| TIC-406413408* | 10 / 20 | 50 % | [30 %, 70 %] | 0 | 0 |
| TIC-416715793 | 11 / 20 | 55 % | [34 %, 74 %] | 0 | 0 |
| TIC-421801900 | 16 / 20 | 80 % | [58 %, 92 %] | 0 | 0 |
| TIC-441633615 | 19 / 20 | 95 % | [76 %, 99 %] | 0 | 0 |
| TIC-441728473 | 14 / 20 | 70 % | [48 %, 85 %] | 0 | 0 |
| TIC-441803025 | 15 / 20 | 75 % | [53 %, 89 %] | 0 | 0 |
| TIC-44743595* | 16 / 20 | 80 % | [58 %, 92 %] | 0 | 0 |
| TIC-453467954* | 11 / 20 | 55 % | [34 %, 74 %] | 1 | 0 |
| TIC-456894260 | 12 / 20 | 60 % | [39 %, 78 %] | 0 | 0 |
| TIC-458358301* | 7 / 20 | 35 % | [18 %, 57 %] | 0 | 0 |
| TIC-468978941 | 16 / 20 | 80 % | [58 %, 92 %] | 0 | 0 |
| TIC-62815027 | 19 / 20 | 95 % | [76 %, 99 %] | 0 | 0 |
| TIC-75628092 | 19 / 20 | 95 % | [76 %, 99 %] | 0 | 0 |
| TIC-79569472 | 14 / 20 | 70 % | [48 %, 85 %] | 0 | 0 |
| TIC-88096786* | 16 / 20 | 80 % | [58 %, 92 %] | 0 | 0 |
| TIC-95860790 | 14 / 20 | 70 % | [48 %, 85 %] | 0 | 0 |
| TIC-97814880 | 16 / 20 | 80 % | [58 %, 92 %] | 0 | 0 |

Descriptive, over the 87 curves without a gate-passing signal of their own: median rate 70 %, range 30 % to 100 %.

## Detections on transformed curves (not a false-alarm rate)

Per star: 3 transformed curves (1 inverted, 2 per-sector cyclic rotations), stage-1
tests for the funnel; the full battery (stage 2) for the controls and the promoted.

- Funnel, stage 1: 300 transformed curves; 64 pass the gate; 17 survive the stage-1 decisive tests.
- TIC-86396382, stage 2: 3 curves; 3 pass the gate; 1 survive the stage's tests.
- TIC-393911494, stage 2: 3 curves; 3 pass the gate; 2 survive the stage's tests.
- TIC-88096786, stage 1: 3 curves; 2 pass the gate; 0 survive the stage's tests.
- TIC-88096786, stage 2: 3 curves; 2 pass the gate; 0 survive the stage's tests.
- TIC-286480954, stage 1: 3 curves; 3 pass the gate; 0 survive the stage's tests.
- TIC-286480954, stage 2: 3 curves; 3 pass the gate; 0 survive the stage's tests.
- TIC-406413408, stage 1: 3 curves; 2 pass the gate; 1 survive the stage's tests.
- TIC-406413408, stage 2: 3 curves; 2 pass the gate; 0 survive the stage's tests.

## Exporter

Defect in the locked exporter (#179, classified by the maintainer on 2026-11-01): the
sheet's `duration_hours` is the BLS grid value next to `duration_method:
trapezoid-least-squares-1`, and the .md says "not estimable" where the method was not
accepted. It touches no verdict. Fixed, with #194 (the controls' catalogued period
uncertainty), by sheet version 2 (`calibration/v0.4/reexport.py`): re-exported
deterministically from the 107 sealed dossiers as the annex `export-2`, with no analysis
re-run (`runs/reexport.json`); read the sheet there, not in the core's `export/`. The
locked exporter is fixed in the v0.5 code. Period and epoch from two fits: #186.

## Reviews (P4)

One independent session per stage-2 dossier. The objections are tracked in public
issues in generic form (#179 to #188; no star, verdict or result; details at P7); the
objections the first gate review (P6) found untracked are #190 to #194; the full
drafts stay private until P7. None changes a verdict.
Opened later, both prospective for v0.5: #195 (a reproduction criterion with complete, verifiable inputs) and #196 (a dedicated frozen folder for the TESS-EB edition).

## Use of the caps

- Logical-processor hours counted since the lock: 27.92 (measured CPU and, for parallel runs, wall x workers + the parent's CPU; of which 0.27 for the reproductions, counted from their wall time (sequential steps, single-threaded numerical libraries; an approximation, not a measured CPU time)); before the lock: 3.94 estimated, never metered.
- Bytes in the phase's .cache folders, largest recorded measurement: 6.42 GB (2026-11-01T13:19:11Z: the pilot's folder, with two reproduction worktrees, and the lightkurve cache); 3.14 GB later that day; 1.04 GB after the cleanup of 2026-11-01. These are point measurements, not a monitored peak.
- Reviewer tokens: 1807636 (seven sessions: five dossier reviews (P4) 1092544, the first gate review 344434, the second gate review 370658; cap 2000000. The 80 % warning was passed without a stop, a deviation recorded in #177).

## Limits

- The method is not validated; SURVIVED means the declared decisive battery was
  survived, without requiring the temporal diagnostic to pass. It is not support for a
  candidate: a fatal test can PASS without the power to fail (no validated power rule;
  #185), and a surviving signal can be indistinguishable from the curve's noise (#184).
- A PASS from the pixel tests does not exclude unresolved blends (#187).
- No decisive test models stellar variability (#182); centroid_shift can be decided by
  one sector (#183); a gate-passing signal can be indistinguishable from the curve's
  noise (#184).
- Injection-recovery uses a trapezoid model, injected before detrending, into the
  pilot's curves only; the numbers are about these curves and this code.
- The exclusions use catalog snapshots of 2026-10-29.
- The case ledger was assembled at P5 (2026-11-01) from dated records: each event's utc
  comes from its source record, and the ledger's first anchor is of 2026-11-01. The hash
  chain shows the order in which the events were written at P5, not that they were
  recorded live. The approvals of 2026-11-01 are later events that point to the drafts.
