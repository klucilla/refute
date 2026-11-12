**The corrections mostly hold, but two stop-related defects remain.** Static, read-only review only.

1. **I4 can pass a mandatory stop.** At [i4_bound.py:304](C:/Projetos/refute/docs/validation/v0.5.4/i4_bound.py:304), exceptions become ERROR without `_raise_stop()`. The oversized-record branch also omits it ([i4_bound.py:310](C:/Projetos/refute/docs/validation/v0.5.4/i4_bound.py:310)). These records enter E, while the summary can report `route` and exit successfully.

   **Conservative option:** unexpected execution errors and oversized records must create the binding stop and force a failing summary. Keep the explicitly enumerated numerical invalidities in E and isolated sinusoid errors separate. This resolves the tension between “E includes errors” and the stricter stop rule at [design:233](C:/Projetos/refute/docs/plans/v0.5.4-h1-design.md:233).

2. **`i1_verified()` does not verify I1’s execution.** [i4_bound.py:316](C:/Projetos/refute/docs/validation/v0.5.4/i4_bound.py:316) accepts any JSON object whose three optional fields are absent or empty, including `{}`. It does not check I1’s current fingerprint, complete population, skipped count, binding-stop file, ledger state or verified shards. Hashing that document pins its bytes, without establishing provenance.

   **Conservative option:** refuse I4 unless the report matches the current I1 fingerprint and completed, verified records, contains all 206 cases with zero skips, and has no report, ledger or binding-file stop. Perform this prerequisite before I4’s scheduling and mutations.

3. **A stopped run is not guaranteed to produce its promised report.** Both summaries call `budgeted.assembled()` before examining the binding stop ([i1_diagnose.py:494](C:/Projetos/refute/docs/validation/v0.5.4/i1_diagnose.py:494), [i4_bound.py:370](C:/Projetos/refute/docs/validation/v0.5.4/i4_bound.py:370)). Assembly refuses unresolved budget stops and incomplete shards, so a scientific stop followed by a driver stop can prevent report creation.

   **Conservative option:** write a diagnostic stop report even when assembly is refused, leave unprocessed cases unknown, and exit unsuccessfully. Do not reconcile or resume merely to obtain the report.

**Confirmed corrections:** supplied-block validation and classification precedence are corrected; replay messages and bounded records are retained; I1’s stop file makes subsequent workers skip; non-finite convergence residuals are rejected; sinusoid exceptions preserve the odd/even result; and `_atomic_save()` now checks the ledger binding ([ledger_i.py:72](C:/Projetos/refute/docs/validation/v0.5.4/ledger_i.py:72)). I4’s draft correctly causes a failing summary exit. I found no new stage A/B ledger write or adaptive rule selection in the reviewed paths.

WEAKENED, with mandatory corrections to I4’s stop handling, I1 provenance verification, and reporting when assembly is refused.