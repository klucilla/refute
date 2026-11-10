**Verdict:** recommending path (ii) is sound and nothing below changes it. Fix items 1–4 before the push; 5–7 are about how you close the stop.

1. **The 0.902 sentence mixes two kinds of number.** The table's ranges are point estimates, but "an upper end of about 0.902" is Codex's sampling-interval endpoint, and no script in the repo reproduces it. Add the scenario "every INCONCLUSIVE except `systematics`'s `not_enough_data`" to the T2a what-if. From your own counts (8 and 11 such losses) I expect a point of about 0.70 to 0.79; check it. Then state both: the point fails by 0.11 to 0.20, and only the upper sampling bound of an 80-injection sample touches the minimum.

2. **`forecast-t2a-paths.json` still contradicts the corrected record.** It emits "only if the stratum above 20 is mostly kept", which the record now gives as 14 % and 25 %. `forecast_t2a_paths.py` is not in any fingerprint, so fix it and regenerate in a follow-up commit.

3. **Two literature statements came from Codex's answer, not from your reading.** These are LEO-Vetter's unavailable fit uncertainties and Carter and Winn's simulation evidence. Read them yourself and add them to the sources file with URL and date, or mark them "per Codex, not confirmed".

4. **The memory files are stale.** `v052-phase-state.md` and the `MEMORY.md` line still say there is no information limit and that the coverage rule blocks T2a. Codex refuted both and the record no longer says them. Rewrite them, or they come back as fact after the next compaction.

5. **Path (i)'s risks omit two things the maintainer needs.**
   - **Agent-days:** the cap is 12 and the wall-clock bound is already 6.1 after two days. Weeks more would pass it on either measure, which is another non-delegated stop.
   - **Budget:** the open budget options are not tied to the path. At 3,474 to 4,110 total, 3,300 does not cover path (i) and about 4,036 covers only part of the range. Under path (ii) the budget decision is moot.

6. **Codex has not seen what you wrote after its review.** That covers `forecast_v4_paths_r2.py`, the rewritten record, and the end-of-round review of d9b5cad..HEAD. Run that review before the push, or say in the #216 comment that it is pending. Do not write "all applied" as if it were verified.

7. **No tests ran for 81252a2.** Grep `tests/` for what reads the consensus folder or lints the docs (README hashes, links). Run those through `run_tests_affinity.ps1` with JUnit counts before pushing.

**Closing sequence:**
- Store this answer unchanged, with the model and date; one consultation is left.
- Run the privacy check on it and on the Codex answer file.
- Make one further commit and a single push, with the SHA before and after and CI in the background.
- Post the #216 comment with the consumption note.
- Stop in Portuguese with the two open decisions.

In the stop question, you may offer the `systematics`-cause diagnosis as an option (about 80 injections rerun keeping the messages, within the 25 CPU-h). It is a rerun outside the plan, so do not run it without approval on the issue.
