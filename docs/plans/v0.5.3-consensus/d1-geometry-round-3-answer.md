1. **Round-2 blocker fixed:** [d1_geometry.py:72](/C:/Projetos/refute/docs/validation/v0.5.3/stageA/d1_geometry.py:72). Verified 96 unique shards, exactly 1,900 unique scheduled curves, deterministic ordering, and checkpoint `P-0150, PG-0150, EB1-0150, EB2-0150, P-0170`. The coverage refusal is correct.

2. **No other blocking defect found.** [d1_geometry.py:124](/C:/Projetos/refute/docs/validation/v0.5.3/stageA/d1_geometry.py:124) computes an **8.182 CPU-h** hard cap from the current ledger, above the **7.71 CPU-h** estimate. The checkpoint and all binding stops remain active.

**Verdict: Acceptable to run under the stated completed/cut prerequisites and existing caps. No measurement was run during this review.**