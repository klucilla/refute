Opened on the maintainer's decision of #218 comment 7198110621, item 3 (the v0.5.12 charter, step 2: "An unreachable branch needs a written proof and a GitHub issue. It is not counted as tested"). Labels of the work: `exploratory`, `method_status: not_validated`.

**Four branches of version 5's screen are unreachable in the approval code** (`src/refute/packs/tess/screen_d5.py` at `f18d6f8`; inventory `docs/validation/v0.5.12/step2/inventory.json`, run at `00404cb`). **They are not counted as tested.**

| Branch | Site | Written proof |
|---|---|---|
| B07 | `_f1_box`, line 233: F1 `not_assessed`, "baseline mean unavailable" | [cases.json, `unreachable.B07`](https://github.com/klucilla/refute/blob/6f9925e/docs/validation/v0.5.12/step2/cases.json); [README, the B07 row](https://github.com/klucilla/refute/blob/6f9925e/docs/validation/v0.5.12/step2/README.md) |
| B18 | `_f2_u1`, line 383: F2 `unavailable`, "FA1 or FA2 not finite" | [cases.json, `unreachable["B18 B19"]`](https://github.com/klucilla/refute/blob/6f9925e/docs/validation/v0.5.12/step2/cases.json); [README](https://github.com/klucilla/refute/blob/6f9925e/docs/validation/v0.5.12/step2/README.md) |
| B19 | `_f2_u1`, line 383: U1 `unavailable`, the same reason | the same proof as B18 |
| B23 | `_f1_trap`, line 575: F1_trap `unavailable`, "a denominator is not positive" | [cases.json, `unreachable.B23`](https://github.com/klucilla/refute/blob/6f9925e/docs/validation/v0.5.12/step2/cases.json); [README](https://github.com/klucilla/refute/blob/6f9925e/docs/validation/v0.5.12/step2/README.md) |

**The proofs, in short:**
- **B07.** Line 231 repeats `_wmean(f[base], w[base])`. `_noise` returned `sigma_w` only after `_wstd`'s own call of `_wmean` on the same arrays was not None (lines 89 to 91 and 149), and `_wmean` is deterministic.
- **B18 and B19.** `erfcinv(T/P)` is finite for 0 < T/P < 2. When T/P ≥ 2, no MES cell is 2T from the primary, because `_cell_distance` ≤ P/2 < 2T. Line 378 then returns first.
- **B23.** `_uncertainties` returns `sqrt(var)` with a finite `var` > 0. Each σ is then at least `sqrt(4.9e-324)`, its square is not 0, and the sum is never NaN. B23 is also witnessed by fault injection (case R23), but that witness is not counted as natural.

**Also unreachable, in the corrected F1** (correction 2 revision 1, adopted at SHA-256 `c24e7fd9…`): the `C ≤ 0` guard is defensive, by revision 1's section 4 and its bound in section 6.

**What this asks.** Nothing is changed now. A future change of `screen_d5.py` either keeps these as guards declared unreachable, or removes them behind the phase's stops.
