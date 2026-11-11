1. **Applied, partially correct.** Atomic ledger saving and recovery across fingerprints are present. However, [above20.py:296](C:/Projetos/refute/docs/validation/v0.5.3/stageA/above20.py:296) skips any existing charge, even when recovery requires a larger reservation. An in-memory check retained 0.1 CPU-h against a 0.433 CPU-h reservation. This does not implement the stated full-reservation policy. **Correction:** reconcile the amount idempotently, rather than checking existence alone.

2. **Applied, partially correct.** Cleanup now isolates each child’s exceptions. **Remaining blocker:** [above20.py:400](C:/Projetos/refute/docs/validation/v0.5.3/stageA/above20.py:400) removes the open attempt before its accounting-failure stop is persisted at [:459](C:/Projetos/refute/docs/validation/v0.5.3/stageA/above20.py:459). A crash between them loses the binding stop. **Correction:** persist that stop before closing the attempt.

3. **Applied and correct.** [above20.py:53](C:/Projetos/refute/docs/validation/v0.5.3/stageA/above20.py:53), [:272](C:/Projetos/refute/docs/validation/v0.5.3/stageA/above20.py:272). Early child pinning, exact-mask verification, and `SUBSET_AFFINITY` address the previous defects.

4. **Applied, partially correct.** The watchdog starts before dispatch and remains active through child completion. **Remaining blocker:** [above20.py:446](C:/Projetos/refute/docs/validation/v0.5.3/stageA/above20.py:446) merely appends a watchdog failure; [:583](C:/Projetos/refute/docs/validation/v0.5.3/stageA/above20.py:583) returns its message without persisting a stop. An in-memory reproduction wrote zero binding stops. **Correction:** persist the watchdog stop before settlement and prevent further dispatch once it fails.

5. **Applied and correct.** [above20.py:504](C:/Projetos/refute/docs/validation/v0.5.3/stageA/above20.py:504). Acceptance reuse, terminal-unknown refusal, result validation, authoritative markers, and the explicit 1,200-second acceptance limit are present.

6. **Applied and correct.** [above20.py:390](C:/Projetos/refute/docs/validation/v0.5.3/stageA/above20.py:390), [:596](C:/Projetos/refute/docs/validation/v0.5.3/stageA/above20.py:596). Publication follows measured charging; timeout markers remain authoritative.

7. **Applied and correct.** [above20.py:149](C:/Projetos/refute/docs/validation/v0.5.3/stageA/above20.py:149), [:605](C:/Projetos/refute/docs/validation/v0.5.3/stageA/above20.py:605). Partial evidence survives, and failed instrumentation stays unknown.

8. **Applied and correct.** [above20.py:333](C:/Projetos/refute/docs/validation/v0.5.3/stageA/above20.py:333), [:487](C:/Projetos/refute/docs/validation/v0.5.3/stageA/above20.py:487). Numeric thread limits and controller-placement checks remain present.

9. **Applied, partially correct.** Cross-fingerprint stops and the [design qualification](C:/Projetos/refute/docs/plans/v0.5.3-stageA-design.md:159) are restored. **Remaining blocker:** [above20.py:540](C:/Projetos/refute/docs/validation/v0.5.3/stageA/above20.py:540) ignores an existing checkpoint’s `passes` value. A crash after writing `passes: false` but before writing the stop permits dispatch on restart, reproduced in memory. **Correction:** read and enforce the persisted decision, recreating its binding stop when failed.

10. **Applied and correct.** [above20.py:213](C:/Projetos/refute/docs/validation/v0.5.3/stageA/above20.py:213). Native declarations remain correct. No historical-code edits or historical-ledger write paths were found.

**Verdict: REFUTED. Do not run the smoke or subsequent (c3) run; keep the above-20 stratum bounded both ways.**