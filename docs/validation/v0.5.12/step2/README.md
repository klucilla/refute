# v0.5.12 step 2 (#223): the inventory, the cases and the probe

The charter's step 2, in the order of Codex's consensus (#218 comment 7197519001, item 3). Labels:
`exploratory`, `method_status: not_validated`.

1. **The inventory** (`inventory.py`, `inventory.json`, run at `00404cb` on the approval code
   `f18d6f8`): 69 entries.
   - **Read with two notes,** with no rerun:
     - B01 and B02 are the same branch, the `except` of `f1_box` (lines 205 to 206), so the
       entries name 68 distinct sites;
     - B10 and B11 are the parity templates of `_f1_box` (lines 239 to 240 and 244 to 245), whose
       reason is a variable, so each stands for two branches, odd and even.
   - This gives **70 branches**.
2. **The case record** (`cases.json`, built by `cases_build.py`) is committed before the first
   probe. For each case it gives:
   - the recipe and whether it is a natural witness or a fault injection;
   - the expected state and reason of each asserted record, and F2's flags where applicable;
   - each asserted value with its source (the generating model, or a deterministic independent
     oracle frozen on the realized fixture) and its `atol` and `rtol`.
3. **The probe** (`probe.py`) evaluates every case on the approval code and writes each
   assertion's outcome. A failure is documented only if `cases.json` names it before the probe.
4. **The suites** are pushed before any `src/` change:
   - `tests/test_v0512_223_cases.py`, #223's suite;
   - `tests/test_v0512_correction2.py`, correction 2's section 7.

**Expectations.** F1's expectations are those of correction 2 revision 1 (adopted, SHA-256
`c24e7fd9…`): Codex's round 1, item 4, "use corrected F1 expectations and existing MES
expectations".
- Where the approval code differs, the difference is a documented failure, for its own case and
  assertion.
- The report-only expectations are those of the frozen §5 (they do not change).

**Fixtures** (`tests/v0512_fixtures.py`, independent of `src/`):
- **One sector:** 10-minute cadence from t = 1325.0 for 27 days (3,888 cadences).
- **The candidate:** P = 3.7 d, t0 = 1326.3, T = 2.5/24 d.
- **The flux:** a box, a trapezoid or a null, plus a white Gaussian noise from
  `default_rng([seed, 223])`, then the named modifications.

## How each branch is reached

The kinds are:
- **N:** a natural witness;
- **F:** a fault injection, where a module helper is replaced by `monkeypatch` in the probe and the
  suite;
- **U:** unreachable in the approval code, with a written proof, a GitHub issue, and no count as
  tested.

| Branches | Kind | Witness |
|---|---|---|
| B01 = B02, F1 numerical failure | N | t0 shifted by 1e16·P: the epoch index is not exactly representable (ValueError) |
| B03 | N | period NaN |
| B04 | N | one σ = 2e3 |
| B05 | N | 15 cadences |
| B06, noise | N | baseline < 10 (T = 3.5 d); fewer than 3 bins (a 2.7·T window); non-finite (one baseline flux 1e300 at σ = 1e-12); and, corrected, `s² ≤ 0` (constant baseline; the approval code gives B11 there, a documented failure) |
| B07 | U | `_noise` returned `sigma_w` only if `_wmean(f[base], w[base])` is not None, the same deterministic call that line 231 repeats |
| B08 | N, corrected | flux 0 except one baseline point 3e-162, σ = 1e-12: `s²/W` and `σ_r²` round to 0. The approval code gives B11 (`sigma_w` = 0), a documented failure; its own route to B08 is an overflow of `s_odd² + s_even²`, not constructed |
| B09 | N | odd in-transit flux −1.6e308 and even +1.6e308 at σ = 1e3: the difference overflows |
| B10 odd, B10 even | N | the odd (even) in-transit cadences removed |
| B11 odd, B11 even | N | the odd (even) in-transit flux 1e300 at σ = 1e-12: the weighted sum overflows |
| B12, B13 | N | baseline < 10 |
| B14, B15 | N | 400 cadences and T = 0.03 d: 4P/T > N |
| B16, B17 | N | T = P/3.5: no cell is 2T from the primary |
| B18, B19 | U | FA1 and FA2 are finite for 0 < T/P < 2. T/P ≥ 2 leaves no cell 2T from the primary, so line 378 returns first |
| B20 | N | T = 0.371 d (T/P just above 0.1), a primary box and a secondary box 1.0 d away |
| B21, B25, B28 | N | every cadence within 2T of a transit removed |
| B22 | N | three odd fit cadences |
| B23 | U, and F | `_uncertainties` returns σ > 0 with `var` ≥ the smallest subnormal, so `sdo² + sde²` > 0 and the sum is never NaN. Fault: `_parity_fit` returns zero σ |
| B24 | F | `_parity_fit` returns t0 = ±1e308. A natural route needs T > 5e146 d, not constructed |
| B26 | N | no star record |
| B27 | N | stellar radius 1.7e308 R☉ (rel. error 0.01): Rp overflows |
| B29 to B33 | F | `_trapezoid` returns a chosen fit: q_in = 0.5; a flat interval between cadences; q = 1e-320 on a cadence; q_in = 0; dF = 0.25 with q_in = 0.1 |
| B34, B35 | F | `_noise` raises ValueError |
| B36, B57, B58 | F | `_trapezoid` raises ValueError |
| B37, B38 | F | `_mes` raises ValueError |
| B39 | F | `_parity_fit` raises ValueError |
| B40 | F | `_reliable_radius` raises ValueError |
| B41 | F | `_trapezoid` returns q_in = None: TypeError in F4 only |
| B42 to B46 | N | period NaN |
| B47 to B51 | N | one σ = 2e3 |
| B52 to B56 | N | 15 cadences |
| B59 to B64 | N | `compute_screen` with no flattened curve |
| B65 to B69 | N | `compute_screen` with a flux that holds a string: F1 contains it, and `report_only` raises outside its guards |

**Added or changed by the correction:**
- **`C ≤ 0`:** a new guard, defensive and unreachable (revision 1, section 4, and its bound in
  section 6).
- **B08:** naturally reachable through underflow.
- **The constant baseline:** it moves from B11 to B06.

**The charter's cases** (v0.5.11 charter, step 1):
- a planet;
- a binary with unequal depths at half the period;
- a binary with a secondary away from phase 0.5;
- an occultation that meets F2's exception;
- a grazing binary (F4) and a giant (F3, with a star record);
- a null.

Each report-only record has one `computed` witness with numeric assertions. The giant's
Rp > 22 R⊕ is the genuine paper-threshold crossing. Its isolation is asserted by comparing its
core and outcome with the same case without a star record.
