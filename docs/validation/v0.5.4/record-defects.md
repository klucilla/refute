# v0.5.4: four record defects, as new records (#217, #59)

**The decision.** The maintainer's decision of 2026-11-12 (night), item 7d: the record defects the
audit points out become new records and items of #59, and nothing in `src/` changes without a
stop.

The facts below were checked by Codex against the files at `9742a96`
([`docs/plans/v0.5.4-audit-check.md`](../../plans/v0.5.4-audit-check.md), points 11, 13, 14 and
17). **No earlier record, verdict, lock or `src/` file is edited**; each correction is this record.

## 1. The ambiguous-sinusoid branch carries the class `insufficient_sensitivity`

- **The fact.** `src/refute/packs/tess/battery_v52.py:420-428` returns INCONCLUSIVE with
  `inconclusive_class = "insufficient_sensitivity"` and
  `inconclusive_detail = AMBIGUOUS_SINUSOID`, with the message "significant sinusoid at …: it does
  not establish the dip's cause".
  - The code's comment says why: the closed set of classes is not extended, so that earlier
    tallies keep their bytes; the detail carries the design's name.
  - The case is an ambiguous cause, not a lack of sensitivity: a significant sinusoid was
    detected.
- **What it does to the records.** A tally by `inconclusive_class` alone reads these cases as
  sensitivity losses.
  - [`b1-stop-report-addendum.md:124`](../v0.5.3/stageB/b1-stop-report-addendum.md) states D2's
    `sinusoid` losses as "17 with no class recorded, 8 insufficient sensitivity". **Read: the 8
    are the ambiguous-cause branch.** I1 classifies them as class (ii), and the 18 cases of
    insufficient sensitivity as class (i)
    ([`i1-diagnosis.json`](i1-diagnosis.json), `class_table.d2.sinusoid`).
  - The same label may also enter other tallies by class, for example the addendum's T2a line
    "`sinusoid` 95, all insufficient sensitivity" (`:69`). **Not checked** here: it is a #59 item.
- **Correct reading from now on:** tally the sinusoid's INCONCLUSIVE cases by
  `inconclusive_detail` as well as by class.

## 2. I1's counts of 27 and 26 against the addendum's 26 and 25 (not a defect)

- **The fact.** I1 classifies 27 `odd_even` and 26 `sinusoid` cases among D2's losses; the
  addendum counts 26 and 25.
- **Why they differ** (Codex, the audit's point 14, rejected as an inconsistency). The two count
  different things:
  - for D2, I1 classifies the `odd_even` and `sinusoid` tests found INCONCLUSIVE or FAIL in each
    loss, including those hidden behind a fatal FAIL
    ([`i1_diagnose.py:367-371`](i1_diagnose.py));
  - B1 counts the blockers of the branch that decided the verdict
    ([`b1_blockers_decisive.py:110-126`](../v0.5.3/stageB/b1_blockers_decisive.py)).
  - That explains one more per test; there is no reproduction error.
- **No defect in the records.** The addendum defines its unit, the decisive blockers and the
  fatal precedence ([`b1-stop-report-addendum.md:73`](../v0.5.3/stageB/b1-stop-report-addendum.md)),
  and I1's script defines its own. The audit compared counts of two different units. This record
  keeps the comparison and its explanation; a reader comparing the two takes each count's unit
  from its own record.

## 3. I4's 15 convergence failures

- **The fact.** E = 15 in both of I4's sets ([`i4-bound.json`](i4-bound.json)):
  - in the fresh set, 15 convergence failures;
  - in the v0.5.2 set, 14 convergence failures and 1 ill-conditioned case.
  - They are counted conservatively, apart from L, and do not change the outcome:
    L + E = 17 < 23.
- **The cause is not established.**
  - The bound already uses analytic derivatives of the trapezoid; central differences are only
    the convergence check against them ([`i4_bound.py:119-165`](i4_bound.py)).
  - The audit's hypothesis is that the check fails at the trapezoid's kinks (ingress and egress).
    It is plausible and **not confirmed**.
  - These planets' power was not summarized.
- **The open item:** the check may fail for a numerical reason that is no property of the planet.
  Any later use of this bound establishes why these 15 fail before relying on them, or reports
  their power apart. No specific fix is prescribed here.

## 4. The decision page's prices against the designs

- **The fact.**
  - [`v0.5.3-after-round3-decision.md:100, 135`](../../plans/v0.5.3-after-round3-decision.md)
    priced I2 at 3 to 12 CPU-h and I3 at 5 to 8.
  - The frozen paper designs estimate 95 to 380 CPU-h and about 860
    ([`v0.5.4-I2-I3-designs.md`](../../plans/v0.5.4-I2-I3-designs.md)).
  - v0.5.4's caps (ROADMAP) were set on the former.
- **The reading.** The large figures were extrapolations, disclosed before any run and recorded as
  impediments. Nothing ran on the wrong price.
- **The defect.** The decision page's I3 price did cite a measurement: B0b's 2.45 CPU-h. The
  defect was the extrapolation from that measurement to a design whose work differs (per-curve
  Monte Carlo, an envelope), which the later design priced at about 860 CPU-h.
- From now on, a price on a decision page cites the design it applies to and the measurement it
  comes from, and says how it is extrapolated.

`method_status: not_validated`. These records correct readings; they change no verdict.
