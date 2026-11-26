**The versions' bytes depend on the BLAS thread count**

This comes from the v0.5.12 gate review, important finding 3. The review is stored unchanged in [`docs/gates/v0.5.12-review.md`](https://github.com/klucilla/refute/blob/main/docs/gates/v0.5.12-review.md), section 3, row 3. The maintainer's decision is #218 comment 7202383280, item 1(a).

**The finding** (an English rendering of the review's Portuguese text):

> "F-1 found" is right by the letter of the charter. What was shown, though, is a **sufficient** factor: the BLAS thread count changes the last digits. It is not the mechanism of what was seen in CI (a pytest process against a fresh subprocess).
> - The factor analogous to the phenomenon, `workload`, changed nothing, and it is one module of 16 tests, not "thousands of tests".
> - It used one machine and one system.
> - The "field signature" reduced to `amplitude_snr`, with no comparison against the fields that differed in run 45514526728.
>
> The consequence has no issue and is not in the v0.5.13 proposal, which holds only the old note about F-1: version 3's bytes depend on the thread count, and so on the machine.
>
> Why it matters: F-1 "needs its cause identified before any lock" (the v0.5.11 report). Sealing "found" without the limit could close the item. The thread dependence touches the reproducibility of any future lock (a relative of #212).

**What was recorded:**
- `docs/validation/v0.5.12/step3/f1-cause.md`, whose section "What it does not establish" gives the limit;
- `step3/f1-result.json`: the factor `threads1` changes `amplitude_snr` in all three pairs, and the first differing operation is `battery_v51._wls`, line 45, `normal = (x.T * w) @ x`.

**Open:**
- **The declared limit of F-1's cause.** It is a sufficient factor on one machine, not the mechanism of the CI difference. The origin of the configuration difference in the historical CI is still open, as Codex's second opinion also notes.
- **The decision on pinning the BLAS threads,** or on another correction. It is the maintainer's (the charter, stop 4). Nothing is corrected in `src/` by this issue.

**Status:** this issue is a **precondition before any lock**, and it is cited as such in the v0.5.13 proposal.

Labels: `exploratory`, `method_status: not_validated`.
