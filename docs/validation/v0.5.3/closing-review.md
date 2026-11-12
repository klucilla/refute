# The independent review of the v0.5.3 closing record

The maintainer's decision of 2026-11-12 (#217, item 4): one independent review session, a new
Claude Opus session, read only. It received the record and its annexes, plus the rule files it
needs, listed in the brief and disclosed below. Its limit was 350,000 tokens, counted in stage B's
4.5 M. The maintainer's question was "Com os limites da etapa A e os resultados de B0, B0b e B1,
alguma meta tem base para um registro de inviabilidade? D2 e T2a são alcançáveis por uma bateria
que só passa com evidência, e o que uma mudança de abordagem deveria tentar primeiro?". The report
enters as it came out.

**The session.**
- **Type:** a Claude Code subagent of type Explore (no write or edit tools), model Opus.
- **When:** launched on 2026-11-12 after commit `40aa485`, the record as reviewed. Its brief is in
  the session.
- **The brief:**
  - it forbade writing, running anything that writes, and opening the maintainer's security folder;
  - it set a target of about 300,000 tokens and the hard limit of 350,000;
  - it asked for a report in English with a fixed structure.
- **The files the brief listed.** The record's annexes:
  - `stageA/README.md`, `d2-bounds.json`, `t2a-bounds.json`, `d1-geometry.json`;
  - `stageB/README.md`, `d1-bound.json`, `b0b-record.md`, `d1-infeasibility.json`;
  - `b1-stop-report.md` and its addendum, `b1-forecast.json`, `b1-forecast-d2d4-complete.json`,
    `b1-blockers-decisive.json`, `b1-recal.json`;
  - `docs/plans/v0.5.3-design-questions.md`, `docs/plans/v0.5.3-stageB1-design.md`;
  - `docs/validation/v0.5.2/closing-record.md`.
- **The rule files the brief listed:** `CLAUDE.md`, `ROADMAP.md` (the advance rule),
  `src/refute/core/verdict.py`, `src/refute/packs/tess/calib05/values.py`,
  `src/refute/packs/tess/calib051/values.py` and `src/refute/packs/tess/calib05/c1.py`.
- **Tokens:** 220,574, as counted by the session tool. The reviewer's own estimate, at the end of its
  report, is about 130,000. It made 41 tool calls in 10min39.
- **Read outside the list, disclosed:** the report cites `b1-screen.json` and `battery_v5.py`
  (lines 58 and 377, for the severities of `secondary_eclipse`, `systematics` and `sinusoid`). Both
  are committed files, and neither carries the record's authors' reasoning.
- **Transcription:** the report below was transcribed from the session's hand-back message. The
  harness indents each line; the indentation was removed. It was not copied from a file.

The report, unchanged:

---

# Independent review of `docs/validation/v0.5.3/closing-record.md` (commit 40aa485)

Read-only review. I read the record, its annexes and the rule files named in the request. Line references are to the files as they stand. No file was written and no program was run.

## 1. Summary answer

**Does any target have a basis for an infeasibility record?** No. I agree with the record (closing-record.md:226-234). D1 is the only target that came near one. B0b's pre-registered criterion returned **N** on fresh seeds (b0b-record.md:36-42; d1-infeasibility.json:259), and B0 gave **C** on other seeds. Those results settle the question for now. The record's reasons are sound for D2 and D4. They are weaker than they look for T2a, where stage A's "bound" counts recoverable blockers; it is not an information bound. For D1 they are incomplete: the binary-side bound alone cannot ground a D1 record. T3b is missing from the record's table. Details in §2.

**Are D2 and T2a reachable by a battery that only passes with evidence?** The evidence does not establish it either way. Neither target is shown unreachable, and neither is shown reachable.
- **D2.** It has a model-based room: 108 evidence-qualified planets against 97 needed, on v0.5.2's 112 planets. But the attained `odd_even` error stays about 1.1 to 2.1 times stage A's Fisher bound, nearly unchanged by E2. E3 is available on 15 % of curves. Version 5 does not move D2 on fresh planets (141 against 142).
- **T2a.** There is no information bound for its dominant blocker, the `systematics` background sub-check. If the selector's refusal above 20 sectors is kept, the margin is almost nil: with the 5 fatal FAILs kept, at most 2 of 223 INCONCLUSIVE losses may stay lost. If the selector is certified above 20 sectors, about 49 losses on 2 to 20 sectors are allowed. The record understates this second case.

**What should a change of approach try first?** Cheap information checks before any new estimator, each with a pre-registered rule that can end in either a route or a draft infeasibility record:
1. The `systematics` sub-check diagnosis, and a per-host bound on the background-rise error under a model of the series' slow variability.
2. A D1 test that includes the planet side.
3. D2's `odd_even` bound with the transit shape as a nuisance.

Estimators come only where those bounds leave room. The certification above 20 sectors should be priced as T2a's margin lever, not as "nothing". My order differs from the record's (§4).

## 2. Infeasibility, target by target

The general test (ROADMAP.md:17-26) is evidence that the target cannot be met with the available data, reviewed by Codex and an independent review, and approved by the maintainer.

**D1, EB1.** No basis.
- B0, catalog star, primary level 0.0027: an expected 29.2 binaries are not rejected, against an allowance of 10 (stageB/README.md:67). B0b: 26.4 against 11 (b0b-record.md:29).
- At 0.05, B0b gives 12.0 > 11, but the median probability of meeting the allowance is 0.452. The pre-registered criterion needed both levels, so it is not met (b0b-record.md:41).
- A structural reason, beyond the criterion: D1 counts **SURVIVED only**, not WEAKENED and not INCONCLUSIVE (c1.py:641-649). `secondary_eclipse` is a warning test (battery_v5.py:58), so a warning FAIL already keeps a binary out of the count. The planet-side price of failing or holding binaries depends on the severity:
  - a fatal FAIL costs REFUTED, bounded by D2 (c1.py:668-669) and D3 (c1.py:682);
  - a warning FAIL costs WEAKENED, which D2 counts as kept (c1.py:654) and which no rule D1 to D5 bounds;
  - an INCONCLUSIVE costs D2 and D4 (c1.py:654, 686-690).
- B0 and B0b measured only the binary side, at fixed levels up to 0.05. A D1 infeasibility record would therefore need a **joint** pre-registered test: binaries SURVIVED within the allowance, together with the planet-side rules, for any severity. No number on file addresses that.
- Unchecked: D1's second clause, no more SURVIVED than v0.4 (c1.py:649), does not appear in the B0 or B0b allowance (d1-bound.json has no v0.4 term).

**D1, EB2.** No basis, for the same reasons.
- B0: 35.5 against 10 at 0.0027. B0b: 36.1 against 9.
- At 0.05, 13.1 > 9 with a median probability of 0.102, not below 0.05 (b0b-record.md:30, 42).
- The families' order reverses between seed sets (b0b-record.md:53-56). The margin at 0.05 is seed-sensitive and was not quantified.

**D2.** No basis. This is the clearest case.
- On the forecast sample, a record would need at least 23 of 178 planets shown unreachable by any evidence-only battery: 178 eligible, 156 needed, so 22 losses allowed (b1-forecast-d2d4-complete.json:8, 52, 63).
- Stage A's evidence-qualified bound loses 4 of 112 (d2-bounds.json:8). That was on a different sample, and the bound was not recomputed on the 178.
- Under stage A's model, `odd_even`'s power at the bound is 0.97 to 1.0 where version 4 was INCONCLUSIVE (stageA/README.md:50-52).

**D4.** Nothing to record. It PASSes in the forecast: 7 of 122 INCONCLUSIVE, 0.057 (b1-forecast-d2d4-complete.json:42). A forecast is not an acceptance, as the record says (:53).

**T2a.** No basis, but not because a bound shows room.
- Stage A's "upper bound" (0.909 to 1.0) is a recoverability count: "every blocker of the 51 losses is recoverable" (t2a-bounds.json:26-31). It was computed on v0.5.2's 51 losses, not on the census's 228. The background audit is marked `not_a_bound` (t2a-bounds.json:11).
- The basis is missing because no bound exists for the dominant blocker.
- The stratum above 20 sectors is procedural, so it cannot count as lost in a record unless its information is bounded (v0.5.2 closing-record.md:207-209).
- So a T2a record would need about 64 of 615 injections shown unreachable: 552 needed (b1-forecast.json:122-123), so 63 losses allowed. "7 injections of room" is the margin under the refusal rule, not the infeasibility threshold.
- T2a is the target where a future record is most plausible, because A0's background-rise error is a median 23.2 times the white error (t2a-bounds.json:6). The 0.17-of-depth requirement against a median of 0.41 (v0.5.2 closing-record.md:238-241) comes from a selected subset.

**T3b** (not asked by name, but a declared target). The record lists it (:55) but leaves it out of the infeasibility table (:229-234). It was not measured in round 3, and its population is "none as written". That is a problem of definition, not an information limit, so there is no basis.

## 3. Reachability of D2 and T2a with evidence-only passing

**D2: undetermined. A model-based room exists; attainment is far from it.**
- **Shown.**
  - D2 FAILs on fresh planets with version 5: 141 of 178 kept against 156 needed. Version 4 keeps 142 (b1-forecast-d2d4-complete.json:35, 52).
  - The what-if needs both `odd_even` and `sinusoid` resolved: 9 alone, 8 alone, 33 together (addendum:138-143).
  - On v0.5.2's 112 planets, version 5's `odd_even` error over stage A's Fisher bound sits mostly between 1.3 and 1.9 (range 0.82 to 2.12). It is almost the same as version 4's where both exist (b1-screen.json `error_ratios`, e.g. :277-281, :399-403, :646-650). The B1 design said B1 would not claim to reach the bound, because the bound uses the true template, not boxes (v0.5.3-stageB1-design.md:153-155).
  - On the D2 losses, E2 operated in 22 and `odd_even` stayed INCONCLUSIVE in 21 (addendum:178-179).
  - E3's availability is 51 of 339, 15 %, against the 80 % rule. Its SD is 1.35 [1.045, 1.87] (b1-recal.json:127-135).
  - Stage A's oracle leaves 3 of 112 planets below 0.95 on the sinusoid, which bounds that route (stageA/README.md:47-49).
- **Not shown.**
  - Whether an estimator using the transit shape, with its parameters estimated rather than known, can approach the bound. Stage A's bound assumes the true template (stageA/README.md:53-55).
  - Why 24 of 26 `odd_even` and 17 of 25 `sinusoid` D2 losses are INCONCLUSIVE: no class was recorded (addendum:123-124).
- B1.2's gain on the 112 planets (81 to 86 kept, b1-screen.json:28-29) did not carry over to the fresh 178.

**T2a: undetermined. No information bound exists; the margin is extremely narrow unless the selector is certified above 20 sectors.**
- **Configuration B** (refusal above 20 kept as a rule):
  - 331 kept. Of the 228 losses, 223 are INCONCLUSIVE and 5 REFUTED (b1-blockers-decisive.json:478-481, 580-583).
  - If the fatal FAILs stay, the most B can keep is 554 against 552, so at most 2 INCONCLUSIVE losses may stay lost, with no new false FAIL.
  - Recovery by blocker class, INCONCLUSIVE losses only, from the loss sets at :482-493 and :584-594:
    - `systematics` alone: 72;
    - adding `sinusoid`: 124;
    - adding `odd_even`: 207;
    - adding `period_alias`: 223.
  - So all four classes must be resolved almost completely.
- **Configuration C** (selector treated as certified):
  - 42 of 56 kept above 20 sectors. The 14 losses there are all INCONCLUSIVE: `systematics` 9, `odd_even` 8 (b1-blockers-decisive.json:915-926; addendum:96-98).
  - The need on 2 to 20 sectors drops to 510, which means 179 recovered, against the 207 that three classes give. `period_alias` is then not required, and about 28 losses of slack exist.
  - Two classes (124) are still not enough.
- **Dominant unknown.** E4 measured in 110 of the 169 `systematics` losses, and `systematics` stayed INCONCLUSIVE in each. The records do not say which sub-check held it (addendum:166-170). Whether any estimator can certify the 0.8-depth alternative against the background's slow variability is not established (stageA/README.md:74-77).
- **A fact, not advocacy.** `systematics` and `sinusoid` are warning tests (design-questions.md:88; battery_v5.py:377). Design questions 1 to 3 would change how their INCONCLUSIVE counts. That lies outside the maintainer's premise of a battery that only passes with evidence, so I do not count it as a reachability route.

## 4. What a change of approach should try first, in order

1. **Fix what the records cannot tell (near zero CPU; the T2a cache is kept, record:244).**
   - Rerun the `systematics` losses with each sub-check's status, message and inputs logged, to find which sub-check held the 110 cases where E4 measured.
   - Recover the missing INCONCLUSIVE classes of D2's losses.
   - Reason: v0.5.2's lesson 2 (v0.5.2 closing-record.md:225-227) recurred (addendum:123-124). Every later bound must aim at the sub-check that actually blocks.
2. **T2a: a per-host bound on the background-rise error** under a fitted model of the background series' variability (a state-space or celerite-type likelihood, as the record proposes, :178-182). Pre-register the rule before the run: about 64 of 615 shown unreachable means a draft infeasibility record; otherwise an estimator target.
   - Reason: this is the only step that can end in either a route or a T2a record. It is lesson 5 (v0.5.2 closing-record.md:238). It is cheap: 2 to 10 CPU-h, an estimate the record (:184) carries over from v0.5.2 and that has not been measured.
3. **D1: a joint pre-registered test.** Reuse B0's oracle and add the planet side (P and PG under D2, D3 and D4), for both fatal and warning severity.
   - Reason: D1 gates closing item 1 (stageA/README.md:201-204), whatever D2 and T2a do. The record lists it last and with no route (:215-217). B0 and B0b measured only the binary side. The oracle costs about 2.5 CPU-h per 800 binaries (b0b-record.md:60).
4. **D2's `odd_even`: the Fisher bound with the transit shape as a nuisance parameter.** If room remains, build a contrast fitted on the transit shape, not a box GLS.
   - Reason: E2's error stays 1.1 to 2.1 times the known-template bound (b1-screen.json), so "use E2's joint contrast where it applies" (record:201) would not close the gap on this evidence.
5. **The sinusoid residual by exact likelihood on gapped data**, with availability gated at 80 % before any calibration (record:188-194).
   - Reason: it is needed by both D2 and T2a. E3's moment estimates are unavailable on 85 % of curves.
6. **Coverage:**
   - A0's grid, for the 42 refusals;
   - the selector's certification up to 20 sectors (about 135 CPU-h);
   - the certification above 20 sectors (about 380 CPU-h, an estimate), priced as T2a's margin lever. It changes the T2a need from four classes and a margin of about 2 to three classes and a margin of about 28.
7. **`period_alias`'s diagnosis**, needed only if the stratum above 20 sectors stays refused.

## 5. Errors or overstatements found in the record

1. **closing-record.md:152** "(it buys nothing for T2a)", repeated at :54, and item 3 at :195-198, which prices only certification up to 20. This is true for version 5's forecast (373 < 552). It is an overstatement for a change of approach: C's 42 of 56 kept above 20 sectors raises the allowed 2-to-20 losses from 7 to about 49 (b1-blockers-decisive.json:915-926, 939-940). Stage A named exactly this path (stageA/README.md:92-93).
2. **closing-record.md:64-67, :234.** T2a's "upper bound" is presented like D2's but without its assumptions. It is a recoverability count by rule (t2a-bounds.json:26-31), on v0.5.2's 51 losses, not an information bound. The "room" is therefore weaker than D2's.
3. **closing-record.md:97-103.** The what-if recovers the 5 REFUTED losses (fatal FAILs) along with the INCONCLUSIVE ones, without saying so. With those FAILs kept, B tops out at 554 against 552.
4. **closing-record.md:139-143, :199-201.** The record omits B1.2's per-planet `error_ratios` (E2 at about 1.1 to 2.1 times the Fisher bound, almost equal to version 4's), which the B1 design promised as information (v0.5.3-stageB1-design.md:153-155). It also omits B1.2's 81-to-86 gain, which did not carry over. Both bear on recommendation 4.
5. **closing-record.md:232.** "Version 5's shortfall shows no information limit" uses a bound computed on a different sample (112) from the FAIL (178). It should be stated as such.
6. **closing-record.md:105-117, :187-201.** The record does not say that 24 of 26 `odd_even` and 17 of 25 `sinusoid` D2 losses have no INCONCLUSIVE class recorded (addendum:123-124). The "what to try" items assume a sensitivity cause that those records do not show.
7. **closing-record.md:229-234.** T3b is listed at :55 but missing from the infeasibility table.
8. **closing-record.md:231, :216-217.** The D1 reasoning is right but incomplete. D1 counts SURVIVED only, and warning-severity routes exist (battery_v5.py:58), so the missing quantity is the planet-side cost. "A route would need information beyond the light curve … or a test whose power survives them" omits the severity dimension.
9. **closing-record.md:133.** E4's null screen was "empty": b1-recal.json:141-152 shows 2 eligible, 1 contrast, availability 0.0. "Carried no information" (b1-stop-report.md:136) is the accurate wording. This is trivial.

I recomputed or traced the following and they match the annexes: D2's 141/178, 0.792 [0.727, 0.845], 3 REFUTED with a Wilson upper end of 0.048, and the minimum 0.872 (156); D4's 7/122; T2a's 551.5, 331, 373 and 228; every blocker count and sole-blocker count in :88-117; E2, E3 and E4's operated, fell-back and not-reached counts; B0 and B0b's figures; the CPU arithmetic at :157-158 and :255.

## 6. Limits of this review

- Issue #217 is not visible to me. I could not check the maintainer's decision applying closing item 3 to a part-level cap. The record says no stage cap was reached (:255), and item 2 applies regardless.
- I did not check "the 135 [CPU-h] already inside v0.5.2's inherited schedule" (:157), v0.5.2's budget figures, the ledgers, or caps.json.
- I did not read d1-bound.json or d1-geometry.json in detail, the scripts (b1_*.py, battery_b1.py, d1_*.py), b1-fetch-*.json, or most of b1-screen.json. The E2 error ratios above are the values printed in that file, not a full distribution.
- The planet-side arithmetic for D1 and the C-configuration what-if are my own readings of committed counts. They are what-ifs, not forecasts, and they design nothing.
- Everything here is development data. No statement above is about a real target.

Overall: WEAKENED (the closing outcome and "no infeasibility basis now" hold; the change-of-approach guidance overstates that certification above 20 sectors "buys nothing", presents T2a's recoverability count as a bound, omits E2's distance to the Fisher bound and the unrecorded D2 INCONCLUSIVE classes, and leaves T3b out of the infeasibility table; items 1 to 9 of §5) — tokens used: about 130,000 (estimate: about 50,000 of files read, about 35,000 of system prompt and tool definitions, about 45,000 of reasoning and this report; cumulative re-sent context across turns is not counted).
