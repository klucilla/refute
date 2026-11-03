# v0.5 scope consensus: Codex's answers

The maintainer delegated, on 2026-11-03, the scope of v0.5 and the renumbering of the later
phases to a consensus between Claude and Codex. Codex ran read-only (sandbox `read-only`,
logical processors 8 to 31) on the drafts in three rounds on 2026-11-03. Its answers are kept
here unchanged; the prompts stay local because they name a private folder the session was told
not to open.

| Round | What Codex reviewed | Verdict | File | SHA-256 |
|---|---|---|---|---|
| 1 | the first draft of the plan | `WEAKENED` | [codex-round-1.md](codex-round-1.md) | `dce41662fcaafbfc36e7fd98556d22737fda2a3863cfd953d23022b4b8e4ed61` |
| 2 | the plan with the round-1 changes | `WEAKENED` | [codex-round-2.md](codex-round-2.md) | `d23e39cf74033a3f6576592b9fb447277e2cbc9038648185b3d140ade86e7b3f` |
| 3 | the plan with the round-2 changes and the first acceptance text | scope and budget accepted; acceptance text `WEAKENED` (corrections A to H) | [codex-round-3.md](codex-round-3.md) | `1860479b637c16f32216d3bdca5b56bdd5425869de15e386bfdfe1db4960158d` |

**How each round was treated.**
- Round 1: every required change adopted in [../v0.5-plan.md](../v0.5-plan.md).
- Round 2: every remaining point fixed (the severity table, infrastructure failures that cannot
  be downgraded, the agent-day accounting, the reserve invariant, the development processor-hour
  limit, the week-4 trigger); the acceptance documents written.
- Round 3: corrections A to H applied to [../v0.5-acceptance.md](../v0.5-acceptance.md)
  (revision 1), the single revision before code that the plan's stop rule allows. Claude agreed
  with every correction, so no disagreement went to the maintainer.
- Codex's end-of-round review of the first work round ([codex-end-of-round-1.md](codex-end-of-round-1.md),
  `WEAKENED`) found A to F and H applied and G only in part (the C1 generator was not yet
  deterministic). Revision 2 of the acceptance documents completes G in section C1 only, before
  any C1 code; the review's other findings (the cleanup guard, the sensitivity validation) were
  fixed in code. Recorded in the tracking issue.

**Round 2 of the work** (the TESS wiring, WP2 to WP4, WP6, WP7):
- [codex-design-round-2.md](codex-design-round-2.md) (SHA-256
  `dcbb8514ae5a7ced108054f2b9cc6ba5f37002ac474f3092b65bdfd299de0aa9`): the wiring design,
  `WEAKENED`; every change adopted (the rule on every fatal or warning test, version-aware
  expected tests, conditional sub-checks, the registered 0.9 requirement of `period_alias`).
- [codex-end-of-round-2.md](codex-end-of-round-2.md) (SHA-256
  `e75b7b579a07f32cd2f2600431ba82ebd46f98828245716d300af3c5919698ee`): `WEAKENED`, 1 critical
  (the measurement chain without the rule) and 8 important findings. All fixed by bounded
  repairs to the frozen specification, except the #188 study's measured quantity, recorded as
  a deviation without a rerun (docs/validation/v0.5/study-188-deviation.md).
