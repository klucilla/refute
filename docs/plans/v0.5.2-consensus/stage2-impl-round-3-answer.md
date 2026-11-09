**REFUTED**

1. **A0.8’s optimized truth changes availability, not merely rounding.** [a0v4.py:276](C:/Projetos/refute/docs/validation/v0.5.2/stage2/a0v4.py:276)  
   Reproduced with `('group', 'correlated_trend', 'minimal', 4, 4.0, 23, 523)`. At centre `2086.034196442714`, production-default preprocessing gives no measurable truth box; `rounding_fallback=False` returns depth `0.0004558557867`, coverage `0.59722`. Compared with the pre-optimization runner, `box_even` and `box_diff` change from NaN to finite pulls `0.99510` and `-0.30429`.  
   **Smallest correction:** restore production-default preprocessing for the truth, add this regression, and reprice A0 before relying on the 1,048 CPU-hour projection.

2. **The known byte-test gap extends to an actual runner/production-construction mismatch.** [a0v4.py:262](C:/Projetos/refute/docs/validation/v0.5.2/stage2/a0v4.py:262), [detrend_fast.py:186](C:/Projetos/refute/src/refute/packs/tess/detrend_fast.py:186)  
   For `('event', 'white', 'full', 2, 2.5, 0, 600)`, the runner’s reused construction differs from a fresh `a0_v4.prepare`, as production uses, by up to `1.11e-15` in flux. The real series and all four comb series differ in bytes. No material decision difference was established. [fast_identity.py:58](C:/Projetos/refute/docs/validation/v0.5.2/stage2/fast_identity.py:58) exercises neither reuse nor disabled rounding fallback.  
   **Smallest correction:** make batching/padding independent of which knots are reused, then add the missing integration byte test for the real series and all combs.

3. **The first-5% projection and global budget conditions are not enforced by the reviewed dispatcher.** [budget.md:44](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budget.md:44), [driver.py:319](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:319), [driver.py:509](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:509)  
   A `Run` can dispatch its entire schedule using a caller-supplied cap without recording a 5% projection or consulting other sections’ consumption and remaining projections. Separate runs can therefore satisfy their local limits while exceeding 3,100 CPU-hours collectively.  
   **Smallest correction:** require a persisted 5% checkpoint before further dispatch, freeze its section projection, and bind dispatch to a shared stage-budget ledger.

4. **Crossing a cap can still produce an unrestricted completed result.** [driver.py:568](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:568), [driver.py:596](C:/Projetos/refute/docs/validation/v0.5.2/stage2/driver.py:596)  
   An in-memory completed-shard fixture with `cap_hours=1.5` and charged consumption `1.6` returns `state="complete"`. Empty `todo` is checked before consumption; this overrun also remains below the watchdog’s `1.65` threshold. Without `stop.json`, assembly does not reject it. This can bypass the section’s 1.5-times stop when its last shard crosses the limit.  
   **Smallest correction:** check consumption before declaring completion and after the final batch, persist the applicable stop, and refuse assembly until it is resolved.

5. **The budget omits an identifiable allowance for the mandatory comb reference study.** [budget.md:14](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budget.md:14), [v0.5.2-stage2-design.md:122](C:/Projetos/refute/docs/plans/v0.5.2-stage2-design.md:122)  
   The required comparison against masking individual windows, 200 curves per required construction, has no explicit allocation or priced schedule. The A0 projection counts the ordinary acceptance units, not these additional refits. The stated planning calculation already reaches `70 + 1.3 × 2329 = 3097.7` CPU-hours.  
   **Smallest correction:** explicitly allocate and price this study, or identify its reserved allocation within an existing row, then recompute admission against the maximum.

6. **The deletion guard accepts paths escaping its declared base through `..`.** [dispose_t10k.py:29](C:/Projetos/refute/docs/validation/v0.5.2/stage2/dispose_t10k.py:29)  
   Reproduced without deletion: `guarded(BASE / '..' / 'outside-t10k.txt')` succeeds, although its resolved target is `.cache/v052/outside-t10k.txt`. Lexical ancestry does not establish containment. The current hardcoded entries do not exploit this, so this does not establish an escaped deletion occurred.  
   **Smallest correction:** reject parent traversal and validate resolved containment after checking links and junctions, while retaining the original literal path as the deletion operand.

