# v0.5.12, #222: M1's result (2026-11-26)

Exploratory, `method_status: not_validated`. A software check of F1 on synthetic curves, never a
scientific result.

**The measurement** ran through `launch_v3.py` (charter amendment 1, outside the AppContainer),
with the recipe, families and seeds pre-registered in the charter's step 1 (`7df389c`). Every one
of the 21,000 cases' inputs was rebuilt and matched its frozen hash in `m1-inputs.json` before F1
ran: `m1.py` refuses a mismatch, and it ran to the end with exit 0. F1 is the project's code,
`refute.packs.tess.screen_d5.f1_box`, at the approval commit's `src/`.

**The rule** (fixed before the run): a family passes with 0 `not_assessed` and at most 19 `fail`
of 3,000, that is, a 95 % Wilson upper bound of the fail rate of at most 1 %. M1 passes if every
family passes.

| Family | σ | pass | fail | not_assessed | OE_box > 2 | Wilson upper (95 %) | Family |
|---|---|---|---|---|---|---|---|
| U | uniform | 2,992 | 8 | 0 | 133 | 0.525 % | passes |
| S9.5 | 9.5× in the second sector | 2,986 | 14 | 0 | 136 | 0.782 % | passes |
| P2.4 | 2.4× on odd epochs | 2,909 | **91** | 0 | 464 | **3.71 %** | **fails** |
| P9.5 | 9.5× on odd epochs | 1,389 | **1,611** | 0 | 2,047 | **55.5 %** | **fails** |
| T2 | one in-transit cadence at σ0/100 | 3,000 | 0 | 0 | 20 | 0.128 % | passes |
| T6 | the same cadence at σ0/10⁶ | 3,000 | 0 | 0 | 18 | 0.128 % | passes |
| B6 | one baseline cadence at σ0/10⁶ | 1 | **2,999** | 0 | 3,000 | **99.99 %** | **fails** |

**M1 does not pass:** three of the seven families fail the pre-registered rule. #222's finding
is shown with the project's code. A noise that differs by parity, and a single very precise
baseline cadence, make F1 reject equal-depth curves far above the nominal rate (0.27 % at the
benchmark). The cadence inside the transit (T2, T6), and a noise change by sector with the same
mix in both parities (S9.5), do not.

**What follows, by the charter:** step 4 (a dated specification correction of F1's noise, a
blind review before its adoption, tests before code, then M2 and the sensitivity control). Each of
those has its own stop. Nothing of step 4 has started. M1's records stay as they are and are
never replaced.

The records:
- `m1-summary.json`;
- `m1-<family>.json`, the state and OE_box per seed;
- the journal entry of the unit `m1`.
