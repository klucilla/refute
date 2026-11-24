BLOCKS: 5

### (a) Round-2 items

Paths below are relative to `docs/validation/v0.5.9/`.

1. **NOT RESOLVED.** The download meter still admits a whole product before checking its size, and the supervisor samples files after transfer. `prototype_run.py:795–809, 1300–1319, 1591–1611`
2. **NOT RESOLVED.** Process termination replaces the interrupt watchdog, but current-batch settlements disappear from the live charge, and CPU and disk limits are still checked after consumption. `prototype_run.py:1065–1075, 1549–1559, 1583–1642`
3. **NOT RESOLVED.** Pre-dispatch fingerprinting and exact-byte manifest loading hold. A `launching` journal has no PID, and stop paths can discard a written result. `prototype_run.py:917–947, 1351–1379, 1505–1520, 1561–1565, 1713–1718`
4. **NOT RESOLVED.** Q1–Q4 correctly withhold affected marks. The all-24 agreement summary still includes incomplete pairs in its denominator. `prototype_report.py:120–131, 262–284, 314–328, 432–439`
5. **RESOLVED.** The symmetry tolerance scales to the covariance itself before Cholesky. `prototype_run.py:456–468`
6. **NOT RESOLVED.** Cache-root and distinct-destination checks hold. Cleanup accepts a `match: true` receipt without checking it against the current staged bundle. `prototype_run.py:1103–1120, 1868–1888, 1908–1915`

### (b) Run blockers

1. **New: a batch forgets settled charges during admission.** `settled_charge` is read once. When a worker is removed from `running`, its CPU and download bytes disappear from `live()` until drain. An in-memory test admitted two 0.6 CPU-h units against a 1 CPU-h cap and detected 1.2 only after drain. Add each durable settlement to the live total before freeing its reservation or admitting another unit. `prototype_run.py:1549–1559, 1607–1634, 1673–1688`
2. **Still open: the limits can be exceeded before enforcement.** Product-level checks and file snapshots cannot bound transfer bytes. The snapshot ignores baseline replacements and repeated partial transfers under the same name. Polling also allows CPU and disk overshoot. Enforce transfer allowances at the stream boundary, reserve storage before writes, and use enforceable worker CPU limits. Include startup and final resource usage in settlement. `prototype_run.py:795–809, 1065–1075, 1300–1319, 1583–1642`
3. **New: interrupted launch breaks recovery.** I reproduced `KeyError('pid')` for the journal state written before `proc.start()`. A controller failure just after spawn can also leave a child outside the tracked set. Handle the PID-less state explicitly and prevent the child from working until its identity is durably registered. `prototype_run.py:1351–1379, 1505–1520, 1577–1578`
4. **New: a stop can discard a completed result.** Both stop paths call `settle(..., None)` even when the child has already written its result. Recovery then skips the settled attempt. Confirm worker exit, prefer any valid result for that attempt, and synthesize a stop record only when no result exists. Keep the worker tracked until settlement succeeds. `prototype_run.py:1357–1372, 1523–1527, 1561–1565, 1607–1624`
5. **The report can still count resource losses against agreement.** The descriptive all-24 rate divides by 24 even when pairs were never evaluated because of a cap. Compute agreement over complete pairs and print the incomplete count separately. Preserve the Q1–Q4 withholding rule. `prototype_report.py:134–152, 262–284, 314–328, 432–439`

### Non-blocking

- Bind the archive receipt to the current staged SHA-256. The runner’s cleanup removes FITS inputs and leaves the staged unit records in place.
- Reviewed `521fcff7` offline with static inspection and in-memory checks. The pilot and CI suite were not rerun.

