**REFUTED (`36e3270`).**

1. **A failed adequacy evaluation does not enforce the scientific STOP.** [adequacy.py:254](C:/Projetos/refute/docs/validation/v0.5.2/stage2/adequacy.py:254), [adequacy.py:262](C:/Projetos/refute/docs/validation/v0.5.2/stage2/adequacy.py:262)  
   With 200 non-certified dataset records, `evaluate()` writes `passes: false` and returns normally. The CLI consequently exits successfully, without a persistent scientific stop blocking subsequent work.  
   **Smallest correction:** persist the failed gate, exit unsuccessfully, and require that unresolved gate to block subsequent workloads. Preserve the failed assessment when a redesign starts.

2. **The evaluation fingerprint does not verify the reference bytes actually loaded.** [adequacy.py:168](C:/Projetos/refute/docs/validation/v0.5.2/stage2/adequacy.py:168), [adequacy.py:231](C:/Projetos/refute/docs/validation/v0.5.2/stage2/adequacy.py:231)  
   Replacing `components-v4.pkl` after building leaves the saved `table_sha256` unchanged. Evaluation derives its fingerprint from that saved string, while workers load the replacement file. Changed members or `min_g` can therefore be evaluated under the original reference identity. The version-3 source table is also absent from `fingerprint()`.  
   **Smallest correction:** pin the version-3 table to the sizing reference, verify the rebuilt table’s actual digest before evaluation, and have workers load those same verified bytes.

3. **Every twentieth shard is not representative of these ordered parts.** [budgeted.py:89](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:89), [adequacy.py:98](C:/Projetos/refute/docs/validation/v0.5.2/stage2/adequacy.py:98)  
   A0.7 has 17 shards; its probe selects only the first 128 two-sector curves, omitting all three- and four-sector curves. A0.1’s probe contains only white and trend noise, omitting correlated, long and correlated-trend noise. Their costs are extrapolated across the omitted regimes.  
   **Smallest correction:** interleave or stratify constructions before selecting the checkpoint sample, and weight the projection by scheduled units, including partial shards.

4. **Unregistered parts lose their budget reservation.** [budgeted.py:99](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:99)  
   Parts register only when execution reaches them. For adequacy’s 95-hour line, a first part allocated 25 hours but projected at 30 leaves the section projection at 95, rather than reserving the other 70 hours and projecting 100. In a fixture starting at 3,099 globally, execution proceeds although the corrected projection is 3,104.  
   **Smallest correction:** register every part and allocation before dispatch, or retain the unregistered remainder when replacing allocations with measured projections.

5. **The execution cap remains based on the allocation, not the checkpoint projection.** [budgeted.py:76](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:76), [budgeted.py:107](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:107)  
   If a 95-hour allocation projects to 50 hours at the checkpoint, the full run still receives a 142.5-hour cap. Consumption of 80 hours therefore passes the implemented cap despite exceeding 1.5 times the measured projection, 75 hours.  
   **Smallest correction:** freeze the checkpoint-derived section projection and enforce its 1.5-times consumption limit, alongside the global maximum.

6. **Checkpoint reuse can bypass a rejected projection across changed code and allocations.** [budgeted.py:73](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:73), [budgeted.py:90](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:90), [budgeted.py:103](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:103)  
   Reproduced in memory: a part allocated one hour stops after projecting two hours. Calling it again with a new fingerprint and a two-hour allocation skips sampling and completes, reusing the rejected checkpoint. These preflight stops are returned as strings rather than persisted as driver stops.  
   **Smallest correction:** bind checkpoints to the fingerprint, schedule and allocation; persist preflight stops; retain previous attempts’ consumption; require recorded reconciliation before passing a stop.

7. **The global limit is not checked after the final batch.** [budgeted.py:108](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:108), [budgeted.py:115](C:/Projetos/refute/docs/validation/v0.5.2/stage2/budgeted.py:115)  
   A fixture admitted at a total projection of 3,099 hours returns `complete` after final consumption raises the ledger total to 3,104, while remaining below its local cap. The final ledger update performs no global check, and assembly supplies no budget guard.  
   **Smallest correction:** recheck and persist the global stop after final accounting, before returning completion or permitting assembly.

