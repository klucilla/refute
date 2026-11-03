# #188 study: deviations from its specification

Recorded on 2026-11-03, after Codex's end-of-round review of the second v0.5 work round. The
study (`study_188.py`, run once; `study-188.json` and `study-188.md`, unchanged) is kept as it
ran. No rerun was made: any further computation needs its approval recorded in an issue first
(the repository's rerun rule), and would be a separate record.

1. **The quantity recorded at the true period.** The specification (docs/plans/v0.5-acceptance.md,
   WP7) asks for "the BLS power at the true period". The script records the SNR of a box
   finalized by `search.finalize_candidate` from the true period and duration, and
   `finalize_candidate` refines the period in a local neighbourhood: it is not an evaluation at
   the exact true period, and not the BLS power. The column "Median box SNR at the true period"
   of `study-188.md` is that quantity, not the specified one.
2. **What is unaffected.** The gate counts and whether the search candidate falls at the true
   period or an alias come from the search itself, as specified; Codex recomputed them from the
   committed record and found the Markdown table accurate. The descriptive conclusion (a
   reflected curve of a star with a strong signal of its own can pass the gate at the real
   period, as #188 describes) rests on those counts.
3. **Execution.** The 40 searches ran in one process (0.028 processor-hours), not spread over
   workers as CLAUDE.md asks for CPU-heavy work. The study is not rerun to repair this; future
   studies use worker processes.

The study's result changes no reporting category of the calibration (fixed in the plan), so these
deviations do not affect any decision of the phase.
