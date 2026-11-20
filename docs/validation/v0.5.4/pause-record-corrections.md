# Corrections to the pause record and the v0.5.4 stop report (#218)

**The decision.** The maintainer's decision of 2026-11-20 (15:40), part 2, item 3 (#218):
corrections as **new records, never by editing the old ones**, with the points of Fable 5.2's
proposal ([`docs/plans/v0.5.5-fable-core-plan.md`](../../plans/v0.5.5-fable-core-plan.md)) that
Codex accepted when it checked their facts
([`docs/plans/v0.5.5-consensus/facts-round-1-answer.md`](../../plans/v0.5.5-consensus/facts-round-1-answer.md),
stored unchanged).

**What this record is.** A record of corrected statements. [`pause-record.md`](pause-record.md)
and [`h2-stop-report.md`](h2-stop-report.md) keep their bytes; [`ROADMAP.md`](../../../ROADMAP.md)'s
v0.5.4 paragraph keeps its sentence, with only a pointer to this record added (the maintainer's
approval of 2026-11-20). Where they differ from this record, this record holds.
- **No verdict, target, frozen rule or number of any run changes.** v0.5 stays `WEAKENED`;
  `method_status: not_validated`.
- **No outcome changes.** Step 4's frozen outcome stays as recorded: it was frozen at α = 0.0027
  ([`v0.5.4-h2-step4-b0-errors.md`](../../plans/v0.5.4-h2-step4-b0-errors.md), "The outcomes"),
  and at that level its outcomes are as reported. What is corrected is the **generality** of the
  sentences that report it.
- The corrected texts are Codex's, as written in its check, translated only where the record is
  in English already; each cites its evidence there.

## 1. "No stellar precision is enough" holds at α = 0.0027 only

**Why.** α = 0.0027 is B0's convention and the level at which step 4 froze its outcome. It is not
a frozen target rule. The frozen rule of D2 is a REFUTED fraction of P at most 0.05, with its
Wilson upper end at most 0.10, together with retention relative to v0.4 (`c1.py:664-669`;
`docs/plans/v0.5-acceptance.md:423-424`). At α = 0.05, step 4's own record leaves expected
non-rejected counts from **4.9 to 8.6**, all below D1's allowance of 10.

**Step 4's exact numbers by level** (`h2-step4-b0-errors.json`, the field
`expected_non_rejected_at_projection`; projections EB1 190, EB2 186; allowance 10 for both):

| Family | Stellar error (radius and mass) | α = 0.0027 | α = 0.01 | α = 0.05 |
|---|---|---|---|---|
| EB1 | 1 % | 13.83 | 10.00 | 5.36 |
| EB1 | 2 % | 16.84 | 12.61 | 7.25 |
| EB1 | 3 % | 19.07 | 14.41 | 8.58 |
| EB2 | 1 % | 13.67 | 9.55 | 4.91 |
| EB2 | 2 % | 16.38 | 11.26 | 5.66 |
| EB2 | 3 % | 20.95 | 14.40 | 7.16 |

These are oracle forecasts of non-rejection under B0's per-planet assumptions. **They are not
battery PASS results**, and α = 0.05 at the oracle does not show that the joint REFUTED rule is
met.

**The corrected statements:**

| Record and sentence | Correct text |
|---|---|
| `pause-record.md:63-64`: "So none of 1, 2 or 3 % is shown to be enough. B0's oracle with the star known exactly gives 11.9 and 11.2, also above 10." | At α = 0.0027, under B0's assumptions, none of the three settings meets the frozen step-4 margin criterion. The star-known expectations 11.9 and 11.2 also refer to α = 0.0027. At α = 0.05, the three settings give expectations below 10 in both families; B0's star-known expectations are 4.6 and 4.1. These are oracle non-rejection forecasts, not battery PASS results. |
| `pause-record.md:112-113`: "Under B0's model and population, a finer stellar precision alone would not do: even the star known exactly leaves expectations of 11.9 and 11.2, above 10." | At α = 0.0027, B0's star-known expectations are 11.9 and 11.2, above 10. This does not extend to α = 0.05, where they are 4.6 and 4.1, or establish a general impossibility. |
| `ROADMAP.md:66-67`: "Step 4 found that no stellar precision of 1, 2 or 3 % is shown to be enough for D1 under B0's oracle." | At its frozen outcome level α = 0.0027, step 4 found no margin under B0's criterion for the 1, 2 or 3 % settings. At α = 0.05, all six expected non-rejection counts are below 10; no battery PASS was demonstrated. |

**A related precision** (Codex, point 8.1): B0b's star-known reading (EB1 9.3, pass median
0.915; `docs/validation/v0.5.3/stageB/b0b-record.md:31-32`) is **at α = 0.0027**, not at 0.05.

## 2. The generator's true star is the catalog's centre

**Why.** In C1 the durations come from a star of exactly 1.0 M_sun and 1.0 R_sun
(`src/refute/packs/tess/calib05/c1.py:48-49, 77-92`), and every target carries the catalog star
1.0 ± 0.05 in radius and mass (`c1.py:366`, `synthetic.py:203-217`; also PX, `c1.py:531`). The
true star therefore sits at the catalog's centre in every curve. The acceptance document already
states the solar star (`docs/plans/v0.5-acceptance.md:344-348`); what the pause record lacked is
its consequence for "stellar precision".

| Record and sentence | Correct text (added to the sentence, which stays) |
|---|---|
| `pause-record.md:110-111`: "It also needs a documented source of that information for the binaries' host population, with its URL and retrieval date." | C1's binary hosts are synthetic: the duration generator uses exactly 1 M_sun and 1 R_sun, while the catalog declares 5 % errors centred on those same values. A real-host source concerns an additional population assumption. |

So "a stellar precision of p %" in B0 and step 4 is the **width of the box a test may use**, not
an error the true star was drawn with. The charter's decision (b) addresses this for new draws
([`docs/plans/v0.5.5-charter.md`](../../plans/v0.5.5-charter.md)); old records and draws do not
change.

## 3. T2a's step-1 floor depends on the current battery

| Record and sentence | Correct text |
|---|---|
| `pause-record.md:182`: "20 losses that no procedure fixes (`F_strict`), against B's 7." | 20 recorded losses classified as DATA under the current battery's `not_enough_data` results, against B's allowance of 7. This classification is not an estimator-independent information bound. |
| `h2-stop-report.md:81-83`: "20 losses that no procedure fixes, under the stated rules and assumptions, against a margin of 7." | 20 recorded losses fall in step 1's DATA category, against B's margin of 7. Their classification depends on the current battery's results and does not demonstrate that every procedure must lose them. |

## 4. The stop report is stale on step 4

| Record and sentence | Correct text |
|---|---|
| `h2-stop-report.md:22`: "There is no summary." | Step 4 was subsequently completed; the summary is `h2-step4-b0-errors.json`, recording 1.5179 CPU-h for the computation and no stops in the completed record. |
| `h2-stop-report.md:52`: "29.04 CPU-h (first half 17.17; second half 11.87)" | 29.15 CPU-h (first half 17.17; second half 11.98), including step 4's completion and the recorded summary charges. |
| `h2-stop-report.md:101-102`: "Open for the maintainer: step 4's stop (63 of 77 shards), and the decision between going on and pausing." | The historical step-4 stops were followed by an approved completion. The completed summary is `h2-step4-b0-errors.json`; the maintainer subsequently paused the line, as recorded in `pause-record.md`. |

## 5. T3b's row omits its pass in v0.5

| Record and sentence | Correct text |
|---|---|
| `pause-record.md:32`, T3b's state: "\"none as written\" (v0.5.2)" | PASS in v0.5: 0 of 8 SURVIVED (`calibration/v0.5/results/closing-record.md:24-26`). For a new confirmation, the later frame count leaves 2 domain-eligible unused stars against 11 needed, a shortage of 9. |

## 6. Points accepted with a caveat that ask for context, not a numeric correction

Codex accepted these with caveats; they are recorded here as context for any reader of the pause
record, and they change no number and no trigger:

- **8.4 to 8.6, step 3.** Step 3 required D1 from its test alone on all eligible binaries, not
  among the battery's survivors (`v0.5.4-h2-step2-i3-increment.md:36-46`), and spent 6.55 CPU-h.
  Its calibration allowed about three P failures in 141 while the evaluation band passed with at
  most one (Clopper-Pearson upper end 0.0498 with one FAIL, 0.0622 with two); the calibrated P
  had two. It had no sensitivity block, which its design stated.
- **8.8, the floors.** Step 7 already joins step 1's DATA with `odd_even` and its sinusoid
  certificate; it does not include step 1's full F_rule. The union of step 1's F_rule with step
  7's certificate failures is 20, or 22 with the uncertain planets (Codex's count on the per-case
  file whose hash matches step 1's record); it is a conditional union of classifications.
- **8.9.** One planet's sinusoid certificate fails at the oracle while the battery recorded a
  PASS (`h2-step7-sinusoid.json:33-42`). No cause is established.
- **8.10.** In step 5, three of the 21 REC losses fall below 0.95 with windows alone; the null
  combined crossings are deliberate (the box's equivalence and E2's response were not shown).
- **8.13.** D1's trigger 1 requires D2 to hold on the same planets, which fails today for other
  reasons. That does not make the trigger unreachable; it restricts it to a battery with those
  problems resolved.
- **8.14.** T2a's trigger 1 concerns the validity of a noise model (82 of 102 valid). Meeting it
  alone shows no recovery and changes no counted margin.

## What Codex rejected (no correction made from these)

From the proposal, Codex rejected: the claim that a Gaussian-prior reading would lie between 4.6
and 14.1 (those are other treatments of the star); the claim that D2 caps INCONCLUSIVE at an
absolute 0.10 (D2's rule is relative to v0.4's retention, with 22 losses allowed on the 178); the
claim that the `odd_even` arithmetic is a rigorous lemma against D2; the claim of two strict D2
floors of 8 and 11 (11 is step 7's floor conditional on the recorded statuses); and the claim that
T3b's frame grows only by new false-positive dispositions. None of these is in a project record,
so none is corrected; they are noted so that the proposal is not read as checked where it was not.
