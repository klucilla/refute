**Process: order proofs, the record of repetitions, and the origin of decision records**

This comes from the v0.5.12 gate:
- Fable's review, important findings 1 and 2 and minor finding 13, stored unchanged in [`docs/gates/v0.5.12-review.md`](https://github.com/klucilla/refute/blob/main/docs/gates/v0.5.12-review.md);
- Codex's second opinion, important findings 1 and 2, in [`docs/gates/v0.5.12-review-codex.md`](https://github.com/klucilla/refute/blob/main/docs/gates/v0.5.12-review-codex.md).

The maintainer's decision is #218 comment 7202383280, item 1(c). This issue is an **input to the v0.5.13 charter**.

**1. The order proof by push before the probe** (Fable 1, Codex 1).
- `step2/inventory.json` entered git at `e1834c1`, after the first probe. The probe is journal line 375, 16:40:23Z, HEAD `6f9925e`; Codex adds that that tree has no `inventory.json`.
- No step-2 commit before the probe was pushed before it. The push after 16:17Z is 16:41:26Z (run 723).
- The order "case record before the probe" therefore rests on local commits and on the `head` written in the journal.
- The journal hash of the inventory's run (`f95be285…`) equals the committed file's.
- Suggested: in later phases, a push with the trailer `CI: order-proof` between the case record and the probe. The probe's start also checks that the inventory is in the commit.

**2. The record of repetitions** (Fable 2, Codex 2).
- The deviations were incomplete. `commit-check` was refused and repeated with no approval reference 8 times in the phase journal and 3 times in the outer meter. `inspect` was repeated as `sddl-from-dll`, then `sddl-from-dll-2`.
- They are now recorded in the report as deviations, marked not approved.
- Codex adds that a repetition was admitted whenever the unit's key changed, and that amendment 1 removed the network barrier from the descendant processes.
- Suggested:
  - decide in the next charter whether a commit refused by the checker counts as a repetition;
  - use a repetition identity that keeps the approval requirement when paths or the tree state change;
  - demonstrate metering of the whole path.

**3. The origin and time of decision records** (Fable 13).
- The "maintainer's decisions" in #218 are posted by the building session through the launcher's `gh` unit, on the maintainer's account. The gate cannot tell, from the repository and GitHub, the maintainer's decision from the agent's text.
- Two records declared an hour later than their own timestamp: comments 7174740316 and 7176253382. They are corrected by a dated comment in #218; the originals are not edited.
- From the maintainer's decision of 2026-11-26 (item 3), a decision recorded in #218 cites the pasted block and declares no hour; the comment's timestamp is its time.
- Suggested: consider having the approvals of mandatory stops posted by the maintainer.

Labels: `exploratory`, `method_status: not_validated`.
