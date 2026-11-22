# Independent review of v0.5.6 part B options

**Provenance (written by the maintainer's adviser, not by the reviewer).**
- Reviewer: one session of Claude Fable 5.2, launched by the maintainer's adviser on 2026-11-22 at the maintainer's request (12:08), read only.
- Input: a git worktree of klucilla/refute at `2e734b53` and the adviser's proposed part-B decisions (summarized in the review's section 5). Not a blind review: the reviewer saw part A's results by design.
- Rules given: read only, no writes, no network, cite file:line for every fact.
- The reviewer's use: 176,190 tokens, 19 tool calls, about 3.6 minutes.
- The text below the line is the reviewer's report, unchanged.

---

# Independent review of v0.5.6 part B options

Read-only review of `/home/claude/wt-b` at 2e734b53 and `/home/claude/fable-b/proposed-block.md`. All counts below were recomputed from `docs/validation/v0.5.6/part-a-records.json`, `part-a-frame.csv` and `part-a-draw.json`. No file was changed, no network was used, and nothing here came from memory.

**Bottom line:** do not spend the first lock on door 3. It is close to tautological and repeats what v0.5 already recorded. The FP discrimination finding is the better first claim, but only through a dated plan amendment and with the signal-identity problem handled in the endpoint.

## 1) What door 3 would establish

**The door is near-certain by construction.**
- A "cause" is the test's message with numbers replaced by `#` (`part_a_report.py:112-113`). The number of possible causes per test is therefore the number of message templates in the code.
- In the planet arm, the distinct causes per test are: `edge_events` 1, `single_event` 1, `period_alias` 1, `aperture_depth` 2, `event_consistency` 2, `odd_even` 2, `secondary_eclipse` 2, `plausibility` 2, `sinusoid` 3, `centroid_shift` 4, `systematics` 4.
- With one or two templates, "more than half from one cause" holds whenever there is no exact tie (`part_a_report.py:206`). Seven of the eleven tests are in that position.
- The door is "found" if any single test qualifies (`part_a_report.py:210`). Nine qualified.

**"Insufficient sensitivity" is a designed default, not a discovery.**
- Every fatal or warning PASS is converted to INCONCLUSIVE unless the test shows at least 0.95 probability of detecting its declared alternative (`src/refute/core/sensitivity.py:56`, `:184-197`).
- The refusal message is one fixed template per sub-check (`sensitivity.py:173-178`).
- The refusal names the first non-detectable sub-check in registry order and stops (`sensitivity.py:163-178`). For `systematics` the order is dumps, sap, background (`src/refute/packs/tess/power.py:42`). The split 41 "background" versus 34 "SAP" is therefore partly an ordering artifact.
- The classifier also makes it the residual class: any `PASS refused:` prefix, and the fallback with nonzero coverage, map to `insufficient_sensitivity` (`src/refute/core/inconclusive.py:75-76`, `:80-81`, `:37-39`).

**The proposed block's summary of door 3 is inaccurate.**
- Only 3 of the 9 qualifying tests have a sensitivity refusal as top cause: `aperture_depth` 35/57, `event_consistency` 39/58, `systematics` 41/80.
- The other six are structural: "not enough transits", "no measured event", "no data covers phase", "only # measured event(s)", "period outside the test's domain", "qualification failed".
- Three of the qualifying tests (`centroid_shift`, `single_event`, `event_consistency`) are not in the records' `decisive` list, so they never enter the outcome.
- `systematics` qualifies at 41/80 (51 %). It could flip in a confirmation sample for no meaningful reason.

**What a verdict would tell anyone.**
- SURVIVED: "the battery's INCONCLUSIVE messages come from few templates". That is known from the code.
- REFUTED: a near-tie between two templates in some test. It carries no scientific or engineering consequence.
- The substantive fact is already on record without a lock: v0.5 fails D4 (decidability) and T2a because planets are lost to INCONCLUSIVE (`ROADMAP.md:711-712`), and v0.5.4's I1 already diagnosed the `systematics` losses (`ROADMAP.md:74`, `:819-820`).
- Part A's own numbers repeat it: 72 of the 82 INCONCLUSIVE planet-arm outcomes have `systematics` INCONCLUSIVE, and 18 have it as the only undecided test.
- The open arm already reproduces the same top cause for every test, so the prediction carries little risk of failing.

## 2) The FP discrimination finding and the honest route to a claim

**The signal is stronger than the report shows, once signal identity is taken into account.**

| Group (exploration half) | n | REFUTED | REFUTED on the TOI's own signal (`identity.matched`) |
|---|---|---|---|
| Open arm, disposition FP | 21 | 5 (24 %) | 5 |
| Planet arm | 120 | 9 (7.5 %) | 1 (TOI-251.01, `period_alias`) |

- REFUTED, FP against planet arm, all records: Fisher one-sided p = 0.037.
- "Matched and REFUTED" over all records: 5/21 against 1/120, one-sided p = 0.0003.
- SURVIVED, 0/21 against 13/120: p = 0.11 one-sided. This is not significant, and the Wilson upper bound for the FP survival rate is 15.5 %.
- Kept (SURVIVED or WEAKENED), 2/21 against 29/120: p = 0.11.
- These are post-hoc numbers, picked after seeing the table. Expect shrinkage.

**Caveats that belong in any claim.**
- **Not independent evidence.** TFOPWG dispositions rest partly on the same TESS photometry and similar diagnostics; the plan already says agreement is not independence. The claim is "agreement with TFOPWG dispositions", never "detects false positives".
- **Populations differ.** Median TOI depth is 3621 ppm for FPs against 2277 ppm for the planet arm; median period is 2.5 d against 5.0 d. A difference in REFUTED rates may partly reflect depth and period.
- **Low sensitivity either way.** 14 of the 21 FPs were INCONCLUSIVE. Even a SURVIVED discrimination claim would say the battery refutes a minority of FPs.
- **The open arm is not "non-planets".** The frame's open arm holds KP and CP rows (confirmation half: 295 KP, 29 CP).

**The honest procedure.** The plan allows only a door to become a claim (`v0.5.6-plan.md:106`) and requires a new dated record for any comparison by disposition (`:140`).
1. Report door 3 as found and not pursued, with the reason. This is a deviation from "the first proceeds" (`:101`), so the maintainer decides it and it is recorded on #218.
2. Commit a dated plan amendment before any confirmation light curve is read. It states that the hypothesis is not a pre-written door, that part A's descriptive table suggested it, and gives part A's numbers.
3. Record that NExScI's answer covers this use. The sources record quotes "This column is fine to use in your project" (`docs/plans/sources/v0.5.6-nexsci-answer-2026-11-22.md`); the maintainer should confirm that reading, since the addendum set the column as "descriptive only".
4. Take the disposition from the already committed frame (`part-a-frame.csv`, SHA in `part-a-frame.json`), not from a fresh query. Later disposition changes then cannot leak in.
5. Freeze before the lock: strata, sample sizes, the primary endpoint, the test, alpha, the verdict mapping, the missing-data and ERROR policy, and the prior-exposure rule.
6. Then follow the plan's order: lock, drand round, one run, verdict as it comes with the limits label.

**Suggested design.**
- **Strata:** confirmation half, open arm with disposition FP, against confirmation half, planet arm. FA is excluded and that is stated. KP and CP rows of the open arm are a descriptive secondary.
- **Primary endpoint:** "REFUTED and `identity.matched`", with all drawn records with nonzero coverage as the denominator. This avoids conditioning on a variable that depends on the photometry, and does not count refutations of another signal.
- **Co-primary guard:** the same event in the planet arm stays at or below a fixed bound, in the style of D2 (REFUTED at most 0.05, `docs/plans/v0.5-acceptance.md:423-424`).
- **Secondary endpoints:** plain REFUTED, and SURVIVED.
- **Test:** Fisher one-sided, alpha 0.05, fixed in the claim.

**Sample sizes.** FPs are not scarce: the confirmation half holds 646 FP rows in the open arm and 313 planet-arm rows before eligibility and prior-exposure exclusions. Part A's eligibility rates were 120 of 140 checked (open) and 120 of 123 (planet).

Rough power, Fisher one-sided at alpha 0.05, by simulation with 1,500 draws per cell:

| True rates (FP against planet) | n = 60 per group | 80 | 120 | 150 |
|---|---|---|---|---|
| 24 % against 7.5 % (part A, all REFUTED) | 0.77 | 0.87 | 0.97 | 0.99 |
| 20 % against 7.5 % | 0.57 | 0.67 | 0.85 | 0.92 |
| 15 % against 5 % | 0.47 | 0.61 | 0.79 | 0.87 |
| 12 % against 2 % (shrunk matched endpoint) | 0.58 | 0.76 | 0.91 | 0.97 |
| 15 % against 7.5 % | 0.28 | 0.36 | 0.50 | 0.60 |

- 120 per group gives about 0.8 to 0.9 power for a shrunk but real effect. 150 per group is the safer choice.
- Cost by part A's actuals (5.49 CPU-h and 81.75 GB for 240 targets): about 5.5 CPU-h for 120 + 120, about 7 CPU-h for 150 + 150. Downloads would be roughly 80 to 100 GB.

## 3) Pitfalls to fix or state

| Pitfall | Evidence | Fix or state |
|---|---|---|
| Identity mismatch | 33 of 120 planet-arm records are unmatched, and 8 of the 9 REFUTED planets are among them. The runner attacks its own search result (`part_a_run.py:285`). | **Must fix in the endpoint**, as in section 2. Attacking at the TOI ephemeris would need an adapter in `src/`, which is a maintainer stop. |
| The 9 REFUTED planets | Factor 0.5 with `odd_even` fatal (TOI-1824.01, 2338.01); unrelated short periods with `period_alias` and `duty_cycle` (TOI-199.01, 2049.01); only TOI-251.01 is matched. | **State.** Read TOI-251.01 one by one before the lock. The half-period case is a search and alias defect to log, not evidence against the planets. |
| Prior exposure | 7,480 of 7,482 frame rows are flagged. The scan keeps only the first evidence per TIC (`part_a_frame.py:207`, `:220`), and 7,461 first hits are `calibration/pool_snapshot/exofop_toi.csv`. | **Must fix before the draw.** The current record cannot separate catalogue mentions from real use, because the snapshot masks later files. A new scan must exclude catalogue snapshots or record all evidence. |
| The one ERROR | TIC 219108677: `OverflowError` at `battery.py:123`, reached from `centroid_v5.py:328`. | **Must be decided before the lock.** A fix changes the code hash, so it goes in before the lock or the bug is locked in. The claim needs an ERROR policy: counted as a non-event in the denominator, with a cap on the loss rate. |
| Single-TOI stars | 263 TICs with several TOIs are excluded (`part-a-frame.json`, `excluded_counts`). | **State.** It is already in `biases_declared`; the claim's scope is single-TOI stars. |
| Planet arm by PSCompPars match | In the planet arm sample, dispositions are CP 93, PC 25, KP 1, APC 1. Pre-TESS planets sit in the open arm. | **State.** The arm definition stays frozen as it is; "confirmed" means the PSCompPars match of the frame date. |
| Disk cap | Part A fetched 0.34 GB per target on average; TIC 219108677 alone was 0.62 GB. | **Check.** The proposed 20 GB peak holds only if pixel files are released per target as in part A and the worker count is bounded. |

## 4) Recommendation with risks

**Recommendation: (b), a discrimination claim instead of door 3, preceded by one short exploratory step on data already in hand.** That makes it (d) then (b), with no new photometry before the lock.

**The step before the lock** (read-only on part A's records, about a day):
- TOI-251.01 and the 8 unmatched REFUTED planets, one by one.
- The 5 REFUTED FPs, by test: `aperture_depth` 3, `odd_even` 2, `plausibility` 1, with one record failing two.
- The corrected prior-exposure scan and the resulting sizes of the confirmation strata.
- The OverflowError fix, planned before the lock.

**Reasons.**
- Door 3 would give the relaunch a first verdict that tests nothing, and its informative content is already recorded as D4 and T2a.
- The discrimination claim is falsifiable, and addresses the real-TOI counterpart of the question D1 asks on synthetic eclipsing binaries.
- The confirmation half is large enough (646 FP, 313 planet-arm rows) for a properly powered test at about the cost of part A.

**Main risk.** The exploratory effect comes from 21 FPs and 5 events, found after looking. A real but smaller effect could end REFUTED or INCONCLUSIVE at 120 per group. If it SURVIVES, a reader may take it as independent validation. The claim's text must say that it measures agreement with TFOPWG dispositions on overlapping photometry, with the limits label, and that most FPs were not refuted.

**Second risk.** Departing from "the first door proceeds" can look like outcome switching. The dated amendment and the explicit "door 3 found, not pursued, because" record are what keep it honest. If the maintainer prefers strict adherence to the plan, the fallback is (c): lock both in one lock, with door 3 labelled as a low-information claim and the discrimination claim as primary.

**I do not recommend (a).** If door 3 is locked anyway, it needs at minimum: decisive tests only, a pre-listed set of tests and expected top causes, sensitivity refusals collapsed to one cause per test, and a margin above 50 %.

## 5) Concrete edits to the proposed block

1. **Replace item 1's claim.** New text: "Part B approved for a discrimination claim, by a dated plan amendment committed before any confirmation light curve is read. Door 3 is recorded as found and not pursued: near-tautological (one to four message templates per test) and already known (D4, T2a, I1)."
2. **Add the disclosure.** "The hypothesis was suggested by part A's descriptive table (FP 0/2/5/14 of 21; planet arm 13/16/9/82 of 120) and was not a pre-written door."
3. **Add the frozen design.** Strata from the committed frame's `tfopwg_disp_descriptive` (FP of the open arm against the planet arm; FA excluded); 150 per stratum (120 at minimum); primary endpoint "REFUTED and identity matched" over all drawn records with nonzero coverage; Fisher one-sided at alpha 0.05; the planet-arm guard; the verdict mapping; ERROR and missing-products policy.
4. **Rewrite the prior-exposure line.** "Rerun the scan recording all evidence per TIC and excluding catalogue snapshots (`calibration/pool_snapshot/`, catalogue CSVs); exclude only TICs with records, light curves or results from v0.1 to v0.5.5. Commit it before the draw."
5. **Move item 3 before the lock.** The OverflowError of TIC 219108677 is fixed (with a unit test on synthetic input) before the code hash is locked, or the lock records it as a known defect with the ERROR policy.
6. **Make item 2 a precondition, not a parallel task.** Its results (the 9 REFUTED planets, identity against outcome) feed the endpoint definition and must be committed before the claim is written.
7. **Correct the wording** "mostly 'PASS refused: insufficient sensitivity'": it is the top cause in 3 of 9 qualifying tests.
8. **Caps.** CPU 15 CPU-h is adequate for 300 targets (about 7 CPU-h expected). Add a download estimate of about 100 GB next to the 20 GB peak-disk cap.
9. **Keep as proposed:** lock before any confirmation target is read; disjointness by TIC and product; the drand round named in the claim before the lock; one run with part A's runner; Codex up to three rounds.

**Uncertainties.** The power figures are simulations at assumed rates, not estimates of the true rates. The stratum sizes are frame counts before eligibility and the corrected exposure rule. I did not verify outside the repository that no confirmation-half photometry was ever read; the commit order (frame 099c67c6, draw 2f0d95e9, records 2e734b53) is consistent with the plan.
