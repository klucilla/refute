## Verdict: WEAKENED

Round 1’s A1 and A2 objections are resolved:

- **A1:** Row 5.2 now states the processor-time and task-identity exception and requires reporting `check-dossier --against`.
- **A2:** The plan and row 5.2 use the same locked-tag and `REPRODUCE.md` wording.
- The revised issue #213 also addresses the round 1 scope objections by separating result-changing defaults from bytes-only additions, recording the sampled result separately from general risk, and limiting the v0.4/v0.5 finding to what was checked.

1. **Minor.** The plan still describes the superseded acceptance criterion as current. Its opening says row 5.2 asks v0.1 through v0.5 to preserve outputs with v0.5.1 code, while the amended row gates only v0.2, v0.4, and v0.5, and reports v0.1 separately. The acceptance overview also says all v0.1-to-v0.5 claims “give exactly their recorded outputs,” which overstates the v0.1 result: its locked-tag `verdict.json` differs in retrieval times and run identity.  
   **Evidence:** [v0.5.1 plan, amendment 7](C:\Projetos\refute\docs\plans\v0.5.1-plan.md), lines 547–550; [v0.5.1 acceptance](C:\Projetos\refute\docs\plans\v0.5.1-acceptance.md), lines 71–72 and row 5.2; [v0.1 locked-tag reproduction record](C:\Projetos\refute\docs\validation\v0.5.1\wp5\reproduce-v0.1-at-tag.json), which reports `check-dossier --against` passing and lists the four `verdict.json` differences.  
   **Required change:** In the plan, change “Row 5.2 … asks” to **“Before amendment 7, row 5.2 asked…”**. In the acceptance overview, qualify the v0.1 statement to say it is reported and reproduced at its locked tag; reserve the v0.2/v0.4/v0.5 preservation criterion for row 5.2.

**Row 5.2 itself needs no further change.** Its current scope and comparison-reporting requirements are clear. The v0.1 record supports the separate locked-tag report.

