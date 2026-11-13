# The v0.5 line, paused: the record per target (#217)

**The decision.** The maintainer's decision of 2026-11-13 (#217), items 1 and 3:
- "Escolho pausar a linha da v0.5, depois dos itens 2 e 3 abaixo. Nenhuma meta é afrouxada,
  nenhuma é declarada inviável e nenhum veredito muda; a v0.5 segue WEAKENED."
- "Escreva docs/validation/v0.5.4/pause-record.md: por meta (D1, D2, D4, T2a, T3b), o que se sabe
  com as referências, o que NÃO foi mostrado, e o que reabriria a meta (gatilhos concretos e
  verificáveis [...])."

**What this record is.** It is a record of state, not a verdict.
- No target is relaxed, none is declared infeasible, and no verdict changes. v0.5 stays
  `WEAKENED`.
- `method_status: not_validated` throughout.
- Every number below comes from a committed record, which is cited. The exceptions are step
  3's Clopper-Pearson examples, which are derived here from scipy's beta quantile and are
  marked as derived.
- The rules of the targets are v0.5's frozen rules (`src/refute/packs/tess/calib05/c1.py:633-702`
  for D1 to D4, and v0.5's T2a rule).
- The "what would warrant reconsideration" items name evidence that can be checked: what would
  have to be observed. Each is evidence that would motivate reconsidering the target. None
  authorizes a run, a new design, a rule change, an amendment or step 8, which are all the
  maintainer's, and none decides anything.

## The state at the pause

| Target | Frozen rule | State | Where it stands |
|---|---|---|---|
| D1 (EB1, EB2) | SURVIVED fraction's Wilson 95 % upper end ≤ 0.10, and no more SURVIVED than v0.4 | FAIL in v0.5's confirmation | no route |
| D2 | kept ≥ v0.4's − 0.10; REFUTED ≤ 0.05, with its Wilson upper end ≤ 0.10 | FAIL | 141 of 178 kept against 156 in round 3's forecast |
| D4 | INCONCLUSIVE fraction at target SNR ≥ 15 ≤ 0.30 | FAIL in v0.5's confirmation | PASS in two development forecasts, not accepted |
| T2a | kept ≥ v0.4's − 0.10 (0.897 of 615) | FAIL | `K_B` 331 against 552 in round 3's forecast |
| T3b | the EB truth population | "none as written" (v0.5.2) | the frame's count is short by 9 |

Sources: [`calibration/v0.5/results/closing-record.md`](../../../calibration/v0.5/results/closing-record.md)
and [`docs/validation/v0.5.3/closing-record.md`](../v0.5.3/closing-record.md) (its target table).

## D1, EB1 and EB2

**What is known:**
- **B0, D1's information bound** (round 3; [`stageB/README.md`](../v0.5.3/stageB/README.md)):
  outcome C.
  - Under the catalog star, the oracle leaves an expected 29.2 (EB1) and 35.5 (EB2) non-rejected
    at the primary level, against an allowance of 10.
  - With the star known, it leaves 11.9 and 11.2.
- **B0b** ([`stageB/b0b-record.md`](../v0.5.3/stageB/b0b-record.md)): outcome N. The
  pre-registered infeasibility criterion is not met (median pass probabilities 0.452 and 0.102).
- **Stage A's geometric route** did not separate the binaries: at most 2 of 279 EB2 flagged.
- **Step 3 of v0.5.4** ([`h2-step3-i3.json`](h2-step3-i3.json)): `INCONCLUSIVE`.
  - At τ* = 124.80, EB1 keeps 275 of 381 binaries not rejected and EB2 332 of 373.
  - D1 is not met by that test alone.
  - The test's limits are in the next list.
- **Step 4 of v0.5.4** ([`h2-step4-b0-errors.json`](h2-step4-b0-errors.json)): B0's oracle
  with stellar errors of 1, 2 and 3 %, at the primary α of 0.0027, against D1's allowance of 10:

  | Stellar error | EB1 expected non-rejected | EB2 expected non-rejected | Outcome |
  |---|---|---|---|
  | 3 % | 19.1 | 21.0 | the scenario leaves none |
  | 2 % | 16.8 | 16.4 | the scenario leaves none |
  | 1 % | 13.8 | 13.7 | `INCONCLUSIVE` (pass medians 0.081 and 0.100) |

  The projections are 190 (EB1) and 186 (EB2). All three outcomes are under B0's per-planet
  assumptions.
  - So none of 1, 2 or 3 % is shown to be enough. B0's oracle with the star known exactly gives
    11.9 and 11.2, also above 10.
  - Step 4 was completed with the maintainer's second completion, under a fixed cap of 1.0 CPU-h
    (`step4_rest2.py`, 0.109 CPU-h), after two stops by the driver's mechanics.

**Step 3's limits** (the maintainer's item 3):
- **The calibration's size.** The eligible planet curves per family were:
  - calibration: P 141, PG 141, PV 146, PA 147;
  - evaluation: P 141, PG 140, PV 141, PA 147.

  τ* was calibrated on the calibration set at point values. The bands were applied on the
  disjoint evaluation set, each limit a one-sided Clopper-Pearson end at 1 − 0.05/8.
  - Derived here: at n = 141, the upper end is 0.0354 with 0 failures, 0.0498 with 1 and 0.0846
    with 4. So P's strict REFUTED budget (an upper end ≤ 0.05) holds only with at most 1 FAIL in
    141.
  - That strict budget is I3's design (step 2), not a frozen target rule. D2's frozen rule asks
    REFUTED ≤ 0.05 with a Wilson upper end ≤ 0.10 (`c1.py:664-669`).
  - Within I3's design, any test at this size is held to that band. So the band's width, not only
    the test, makes the strict budgets hard to meet.
- **τ* = 124.80 as a sign of model misfit on the planets.** Λ = χ²_planet − χ²_binary is a
  likelihood-ratio statistic under a white-noise approximation. A threshold that large on the
  calibration planets means the binary family fits many true planets much better than the planet
  family does.
  - This is a sign of this test's misfit on the planets: possibly the planet model, its noise
    weights, or both. It is a diagnostic only, and no cause is established.
  - So the result is evidence against this test, under this design. It is not evidence against D1.

**What was not shown:**
- That D1 cannot be met. No infeasibility basis exists (the v0.5.3 closing record, its table
  "Record infeasibility").
- That the star's density, with any catalog precision, separates the binaries within the allowance
  together with the planet side. B0 and B0b measured the binary side only.
- That a binary held INCONCLUSIVE, or FAILed by a warning test, costs nothing on the planet side.
  D1 counts SURVIVED only, and D2 counts WEAKENED as kept.
- What step 3 says about the battery as a whole.
  - It assumes the other tests reject nothing.
  - It models no sensitivity block for the new test, so its INCONCLUSIVE is understated
    ([`h2-step3-i3.json`](h2-step3-i3.json), `scope`).
  - Its failure bounds that test only.

**What would warrant reconsidering D1** (evidence, any one):
1. A D1 test with its planet side whose development forecast, under a rule frozen before its data,
   gives both EB1 and EB2 a Wilson upper end ≤ 0.10 and no more SURVIVED than v0.4. D2, D3 and D4
   must hold on the same planets. This covers any redesign of step 3's test; such a design is the
   maintainer's.
2. Information beyond the star's density, or a different model or population, under which an
   oracle run like step 4, frozen before its data, gives "the scenario leaves a margin" for both
   EB1 and EB2. It also needs a documented source of that information for the binaries' host
   population, with its URL and retrieval date.
   - Under B0's model and population, a finer stellar precision alone would not do: even the
     star known exactly leaves expectations of 11.9 and 11.2, above 10.
   - Those expectations are not SURVIVED counts, and they show no impossibility.

## D2

**What is known:**
- **Round 3's forecast** (version 5): 141 of 178 kept against at least 156, so at most 22 losses.
  There are 3 REFUTED (Wilson upper end 0.048).
  - Version 4 keeps 142.
  - Source: [`b1-forecast-d2d4-complete.json`](../v0.5.3/stageB/b1-forecast-d2d4-complete.json).
- **Stage A's bound** leaves room on v0.5.2's 112 planets (111 and 108 against 97), under Gaussian
  noise with the generator's covariance. It was not recomputed on the 178.
- **I4** ([`i4-bound.json`](i4-bound.json)): `route`. `odd_even`'s loss is not explained by the
  transit shape as a nuisance: L = 2, E = 15 against 23.
- **Step 1** ([`h2-step1-floor.json`](h2-step1-floor.json)): the joint floor, from existing records
  under stated categories, is `F_strict` 8, `F_rule` 16 and `F_upper` 21, against 22 allowed.
- **Step 7** ([`h2-step7-sinusoid.json`](h2-step7-sinusoid.json)): the sinusoid's Fréchet
  certificate at the oracle gives a floor of 11 and an upper count of 27. This is the battery's own
  rule under the generator's model.
- **Step 5** ([`h2-step5-gap.json`](h2-step5-gap.json)): `INCONCLUSIVE` by design. Only the Fisher
  inflations exist (windows about 1.15, box about 1.02), and E2's effective response is unknown.

**What was not shown:**
- An unavoidable floor of 23 or more. `F_upper` and step 7's upper count carry explicit limits, and
  the strict and rule floors (8, 16, 11) are below 22.
- That any estimator reaches the bound. The four estimators of version 5 did not move D2 (142 and
  141).
- Attainability on the 178 fresh planets.

**What would warrant reconsidering D2** (evidence):
1. A battery version whose development forecast on fresh planets keeps at least v0.4's kept
   fraction minus 0.10 (156 of 178 on round 3's set), with REFUTED ≤ 0.05 and its Wilson upper end
   ≤ 0.10, under a rule frozen before the run.
2. Or a recount of the joint floor by step 1's method, with its categories unchanged, in a new
   script frozen before its data, on the records of a new forecast population. It would have to
   give `F_strict` above that population's allowance (22 on round 3's 178).
   - `step1_floor.py` itself fixes round 3's populations and refuses to overwrite its output, so it
     does not rerun as is.
   - Such a count would be a basis for the maintainer's infeasibility stop, never a record by
     itself.

## D4

**What is known:**
- PASS in both development forecasts: version 5 has 7 of 122 INCONCLUSIVE (0.057), and v0.5.2's
  forecast had 0.122, against ≤ 0.30. Source: the v0.5.3 closing record, its target table.
- It failed in v0.5's confirmation run.

**What was not shown:** a PASS in an acceptance or a confirmation. A forecast is not an
acceptance.
- v0.5.4 made no new acceptance or confirmation of D4.
- Step 3 examined only its incremental budget `i_P(≥15)` at its upper end, inside I3's design
  ([`v0.5.4-h2-step3-i3-population.md`](../../plans/v0.5.4-h2-step3-i3-population.md)).

**What would warrant reconsidering D4:** an acceptance run of a battery version for the other
targets, where D4 is measured with them under its frozen rule. D4 is not reconsidered alone.

## T2a

**What is known:**
- **Round 3's forecast** (version 5): `K_B` 331 and `U_B` 0 of 559, against at least 552, so 7
  injections of room under the selector's refusal above 20 sectors (rule B).
  - Under C (the selector treated as certified above 20), 373 of 615 are kept, and about 49 losses
    are allowed on 2 to 20 sectors.
  - Source: [`b1-forecast.json`](../v0.5.3/stageB/b1-forecast.json) and
    [`b1-blockers-decisive.json`](../v0.5.3/stageB/b1-blockers-decisive.json).
- **I1** ([`i1-diagnosis.json`](i1-diagnosis.json)): of the 169 `systematics` losses, 103 are in
  class (i) (insufficient sensitivity; 102 in the `background` block) and 66 in class (ii) (a
  refusal or a procedure). None is a code defect.
- **Step 1:** 20 losses that no procedure fixes (`F_strict`), against B's 7. That would be 2 if
  the 5 REFUTED stay, and 49 under C. The marginals were known before this reading.
- **Step 6** ([`h2-step6-i2.json`](h2-step6-i2.json)): `INCONCLUSIVE (too many unknown)`. All 102
  class-(i) injections are UNK: 96 because the fitted noise model is inadequate at the transit's
  scale (Box-Pierce), and 6 because their OU τ is below three bins. None is freed.
  - The margins stay at −221 under B and −179 under C.
  - Only 56 of the 102 have `systematics` as their only blocker.
- **Step 7:** T2a `INCONCLUSIVE` by design (no true covariance for real hosts).

**What was not shown:**
- An information bound for T2a's dominant blocker. None exists; stage A's figure is a
  recoverability count by rule.
- That the 20 non-fixable losses cannot be fixed by new data. They are non-fixable under the
  stated categories and the current data.
- That the background step's error cannot be estimated. Step 6 found no adequate model of this
  class, which bounds nothing.

**What would warrant reconsidering T2a** (evidence, any one):
1. A noise model of the background series, in a new design frozen before its data, under which at
   least 82 of the 102 class-(i) injections are **valid** by all of step 6's requirements.
   - Those requirements are adequacy at the transit's scale (Box-Pierce, at least 30 pairs per
     lag), the unit response, the replay's reproduction and numerical validity
     ([`v0.5.4-h2-step6-i2-staged.md`](../../plans/v0.5.4-h2-step6-i2-staged.md)).
   - That is step 6's own limit of at most 20 UNK. Adequacy alone is not validity.
   - Such a design is the maintainer's.
2. New data for the T2a hosts, such as more TESS sectors, or a measured background or SAP series
   where none was, under which a recount by step 1's method gives `F_strict` ≤ 7 under B. The
   recount uses step 1's categories unchanged, in a new script frozen before its data.
3. A battery version whose development forecast keeps at least 552 of the 559 under B, under a rule
   frozen before the run.

## T3b

**What is known:**
- v0.5.2: the EB truth population is "none as written", a problem of definition, not an
  information limit (the v0.5.3 closing record).
- **The count of v0.5.4** ([`t3b-count.json`](t3b-count.json); metadata only, under v0.4's
  domain D-1 to D-9, unchanged): 2 of the frame's 22 unwalked stars are domain-eligible. That makes
  13 of 63 in all, with v0.5's 11. The 13 joins v0.5's queries of 2026-11 with this count's
  queries, so it is not one simultaneous recount of the 63.
  - A new confirmation sample needs 11 more, so the shortage is 9.
  - Rejections by clause: D-1 6, D-4 8, D-6 3, D-7 3.

**What was not shown:**
- Any adjudication. The count selects and confirms nothing.
- That the frame cannot grow. A shortage is a counted fact, not an infeasibility record.

**What would warrant reconsidering T3b:** the frame's domain-eligible count of new stars reaching
11, with new TOIs.
The check is `t3b_count.py`'s method, re-run on a later TOI table under v0.4's domain unchanged,
with the table's URL, retrieval date and SHA-256 recorded. Any change of the frame is an amendment,
and amendments are the maintainer's.

## What the pause leaves

**Open items:**
- #59's items from [`record-defects.md`](record-defects.md);
- I4's 15 convergence failures, whose cause is not established;
- the T2a cache and v0.5.4's caches, kept until the maintainer decides (item 4).

**Consumption of v0.5.4** (from [`ledger.json`](ledger.json) and [`caps.json`](caps.json)):
- CPU: 29.15 CPU-h of 50 (first half 17.17; second half, with step 4's completion and its
  summary, 11.98).
- Review tokens: Codex 2,134,118 before this record's own review, plus the independent review's
  266,456, counted apart (cap 3.5 M; stop at 2.8 M). The final figure is in the closing report on
  #217.
- Agent-days: 1.39 by wall clock (0.82 active) at step 4's summary, of 10.

**Lessons of v0.5.4, for whoever reopens:**
- A checkpoint of a few heterogeneous shards underestimates the rest. One item per shard, or a
  fixed cap, avoids it (step 4).
- Pilots disclosed before a freeze (step 6's three UNK) foretell the outcome. A cheap adequacy
  pilot before the design is frozen saves a run.
- A calibration of about 141 curves per family cannot show a strict 0.05 upper end with more than
  one failure, at a Bonferroni level over eight limits. Size the calibration from the band before
  the design.
