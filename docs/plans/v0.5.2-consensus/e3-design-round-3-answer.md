**Verdict: WEAKENED. Final review, round 3 of 3.**

Round-2 objections **1, 4, 5 and 6 are correctly answered**: the adverse endpoint includes final INCONCLUSIVE, paired intervals retain boundary uncertainty, every alternative requires adequate baseline recovery, and full sensitivity blocks are stored. With 100 identical pairs, the conservative interval is approximately **[−0.04287, +0.04287]**, allowing the specified non-regression check.

Three objections remain, including a new blocking defect in `runlib.py`. Checks used isolated in-memory fixtures. No E3 units ran, no files were written, and the prohibited directory was not accessed.

1. **HIGH, blocking: The process-pool callable cannot be serialized.**

   **Evidence:** [runlib.py:89](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/runlib.py:89) constructs:

   ```python
   guarded = Guarded(fn, lambda a: uid(a), fingerprint)
   ```

   `Guarded` stores that local lambda. Serializing the actual dispatch callable reproduced:

   ```text
   AttributeError: Can't get local object 'bounded_run.<locals>.<lambda>'
   ```

   Consequently, `pool.map` fails before executing a unit; the exception occurs outside `Guarded.__call__`.

   **Exact change:** Replace that line with:

   ```python
   guarded = Guarded(fn, uid, fingerprint)
   ```

   Ensure both supplied callables remain module-level, picklable functions.

2. **HIGH: Record validation still accepts incomplete or invalid scientific fields and can crash on missing fields.**

   **Evidence:** [Validation](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3_sinusoid.py:228) accepted a record containing empty fits, empty sensitivity blocks, an incomplete applicable-harmonic set, and string `"false"` detectability values. Those strings subsequently count as true. Removing `depth` raised `KeyError` rather than producing NOT ESTABLISHED.

   The validator checks fit fields only **if present**, and sensitivity blocks only for key presence. It does not establish their required contents or consistency.

   **Exact change:** Complete validation before any indexed access or aggregation:

   - Check required fields and container types, returning named reasons for missing or malformed values.
   - Require the expected harmonic keys and actual Boolean detectability values.
   - Require finite fit values and positive fitted errors wherever the fit is required.
   - Validate full sensitivity-block fields, probability ranges, rule identity, and consistency between probability, required probability and detectability.
   - Validate finite, nonnegative CPU accounting.

   Structural failures must produce **NOT ESTABLISHED with null recommendations**, without raising during validation.

3. **HIGH: The budget remains an estimate-based stop, not the frozen hard cap.**

   **Evidence:** [Batch sizing](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/runlib.py:98) uses historical mean cost. There is no enforcement during the initial probe or an executing batch. A mocked case with a 2.5-second budget, one second already spent, and a two-second final unit finished at **three seconds and returned `"complete"`**.

   The final batch can therefore exceed the cap without entering another pre-dispatch check. [Summarization](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e3_sinusoid.py:386) also has no over-budget gate.

   **Exact change:** Add aggregate CPU enforcement for executing workers, with a reserved allowance for monitoring and termination latency. Persist the capped/over-budget state, check actual spending after every batch including the last, and make summarization return **NOT ESTABLISHED** when the cap was reached or exceeded. Historical-mean projections alone cannot enforce the stated maximum.

Per the agreed three-round limit, these remaining divergences go to the maintainer.