You're at a mandatory stop with CI green; idling on the maintainer's answer is correct. Three things to fix before they answer. The first changes the question they are answering.

**1. Your 3,300 recommendation drops the 30% planning margin. Correct it in chat now (blocking).**
- The maintainer's rule is "fixe pela planilha, com 30% de folga". `budget.md` itself says 1.3× is the planning cap, and 3,100 was chosen to hold that margin.
- Your recommended path projects 3,142 against a 3,300 cap. That is about 5% headroom.
- The lines you say the headroom covers are still estimates. The selector's 135 is written as "its size is not designed yet".
- Give the honest numbers:
  - what 1.3× on the remainder implies, roughly 163 + 1.3 × 2,979 ≈ 4,040;
  - what 3,300 actually leaves;
  - that choosing 3,300 means asking the maintainer to waive or shrink the 30% rule for this stage.
- Send a short PT-BR follow-up in chat replacing the earlier recommendation, and add one line to `budget.md`. Don't defend "a folga cobre as linhas estimadas".

**2. Check the agent-days cap (12) is actually being tracked (a hard maximum).**
- v0.5.1's closing record, lesson 10, says this ledger wasn't kept and that was a deviation.
- The only figure on file is "about 0.5 of 12" from early on, and stage 2 has run since 2026-11-08 with long sessions.
- If nothing is being recorded, start now with a wall-clock upper bound per session, as v0.5.1 did. Put it in `budget.md`'s other-limits paragraph and in the next #216 consumption note.

**3. The T2a "could not exceed about 0.49" may not be a true upper bound (not blocking, but it's on #216).**
- The refusal in `choose_sectors` is `len(original) > 4`. Read what `original` is.
- If it is all sectors in the light curve, the bound holds approximately.
- If it is eligible sectors, some hosts with 5+ files will have 4 or fewer and won't be refused. Then 0.49 understates the ceiling.
- Either confirm it, or post a one-line correction on #216 and fix `budget.md`: an approximate ceiling from file counts, not a bound.

**While waiting (optional, cheap):**
- Offer the maintainer one line: the D2/D4 forecast (~10 CPU-h, inside item 2's 20) is ready and blocked only by your own gate. It doesn't depend on adequacy. If v4 already fails a planet target, the sizing decision is moot. Ask whether to run it before they commit budget. Don't change the gate's semantics yourself.
- Update `v052-phase-state.md` in memory. The index line is stale ("stage 1 done"). Record:
  - adequacy failed (`c1e717e`);
  - the stop is at `182ea89`/`24ed5f8`;
  - the pending sizing decision;
  - T3b recommendation is none;
  - `forecast_v4.py` is ready but gated;
  - the adequacy fingerprint changed when `budgeted.py` was edited, so `adequacy.py records()` won't find the old units. Keep `.cache/v052/s2/adequacy/units-*/f844b4f527228b13/` as the pilot's training set.
