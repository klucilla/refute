# v0.5 closing record: the second gate's minor findings (2026-11-05)

The second gate review (`calibration/v0.5/gate/gate-2-report.md`, verdict WEAKENED) listed five
minor findings, to be answered in the closing record as new records, never as edits of a
published one (the maintainer's decision 1(b) of 2026-11-05, #199). This file is that record.

1. **The reopened scope issue on reproduction (#195): its state after the reopen.** Saved from
   the GitHub API on 2026-11-05 after the dispositions: state `OPEN`, no milestone. Its last
   events: `demilestoned` 2026-11-05T19:19:07Z, `reopened` 2026-11-05T19:19:47Z, `referenced`
   2026-11-05T19:20:49Z (commit `88cc530`, which names it without a closing word). It had been
   shut by GitHub at 19:08:47Z because commit `f895f9c`'s message quoted a closing word next to
   its number; `calibration/v0.5/results/criterion7.md` records that. It stays open for item 4.
   The saved state and events (event names, times and commit SHAs only):
   [issue-195-after-reopen.json](issue-195-after-reopen.json).
2. **Correction of `calibration/v0.5/reviews/objections-map.md`, row "TIC-17746821, 3"**: the
   issue is **#191 (kept open)**, not "#191 (moved)". The map was committed (`1c6c66b`) before
   Codex's second round changed #191's disposition from move to keep open; the applied
   disposition is in `criterion7.md` (kept open, the whole of optional WP5 as the part left). The
   map itself is not edited.
3. **The trade-off summary** (the second gate dossier, section 3, finding 3), corrected:
   *fewer spurious signals survive*: D1 PASS for NR, SE, ER, V1, V2; T2b (inverted and rotated
   curves, surviving detections 8 and 9 → 0); *fewer original candidates survive (truth
   unknown)*: T2c (2 → 0); *more planets end INCONCLUSIVE*: D2, D4, T2a FAIL; *planets not
   refuted*: D3 PASS, T3a PASS; *false positives*: T3b PASS (0 of 8 SURVIVED) **with C3's false
   positives REFUTED 2 → 1** (v0.4 against v0.5, without the catalog test; TIC-233681149 went
   from REFUTED to INCONCLUSIVE) and 3 INCONCLUSIVE; *spurious signals that still survive*: D1
   FAIL for EB1 and EB2.
4. **Codex's third round on the criterion-7 list** returned `DISAGREEMENT`, on the wording of
   #190's evidence only (the holdout columns appear in the reports that have a holdout table;
   the C3 reserve TIC-184679932, whose analysis did not run, has none); the fix was adopted in
   full before the dispositions were applied (`.cache/v05/codex-c7-answer-3.md`;
   `criterion7.md` says "validated with Codex in 3 rounds", which this item makes precise).
5. **The saved thread of #199 had 32 comments**, not 31 as the second gate dossier said
   (section 2, row M7).
