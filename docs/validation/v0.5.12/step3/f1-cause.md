# v0.5.12 step 3: F-1, the cause of version 3's process-state dependence

Exploratory and post hoc (the charter, step 3; #218 comment 7199932177, item 1). Labels:
`exploratory`, `method_status: not_validated`. It replaces no record, and no correction was made.

**The record:** `step3/f1-result.json`, from the unit `f1`, repeated once with the approval above.
- Code: `f1_driver.py` and `f1_probe.py`, frozen before the first attempt.
- The only change for the repetition: the seed check runs at the parent of the freeze commit,
  through `f1_seed_check_parent.py`.
- Cost: 83.6 CPU-s, within the 0.8 CPU-h cap.

**The outcome: found, the BLAS thread count (`threads1`).**
- **In all three fresh-process A/B pairs,** the default threads against `OMP_NUM_THREADS`,
  `OPENBLAS_NUM_THREADS` and `MKL_NUM_THREADS` = 1 changed `amplitude_snr` in its last digits.
  - Pair 1: `92.9434937093231` against `92.94349370932503`.
  - The record holds all three pairs.
- **The first differing operation is the same in all three pairs:** stage 3,
  `normal = (x.T * w) @ x`.
  - It is the matrix product of `_wls`, `src/refute/packs/tess/battery_v51.py`, line 45, a
    BLAS call whose summation order depends on the thread count.
  - Every later stage differs after it: `inv`, `coef`, the residuals, the Lomb-Scargle power and
    the peak.
  - Stages 1 and 2 (the prepared arrays and the design) are identical.
- **Not the cause, here:** the conditioning workload, the import order, the memory alignment
  (an offset of 8 bytes from a 64-byte boundary) and the global random state changed nothing in
  any pair.
  - The fifteen reference runs were identical byte for byte.
- **Excluded:** the floating-point control state, which is not settable from Python without
  third-party code.

**What it does not establish.**
- Why the pytest process of CI run 45514526728 ran version 3 with another thread count than a
  fresh subprocess. One possibility is a library or test that limits BLAS threads in-process, but
  it is not traced here.
- The finding is on a new fixture (`planet_three_years`, seed 2026112601) and a new diagnostic
  quantity. It is not a recomputation of `verdict-v3.txt`.

**No correction.** Fixing the thread count, or replacing the BLAS product, could change an output
byte of versions 1 to 4. The charter stops before such a change (section 2.2).
