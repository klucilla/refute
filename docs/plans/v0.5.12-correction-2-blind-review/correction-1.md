# v0.5.11 specification, correction 1: the input range of σ (2026-11-25)

> **Status:** a dated correction to the frozen specification
> [v0.5.11-spec.md](v0.5.11-spec.md) (frozen at `ab828ce`, SHA-256
> `d498a82ada2e31a5b47768d58d6af2e19af0a3c5e35364693f04886068612f15`). That file is **not
> edited**; this file adds to it. Exploratory, `method_status: not_validated`.
>
> **Decided by** the maintainer on 2026-11-25 (received at 09:34 local, 12:34Z), reviewed by the
> adviser, recorded before any action in #218, comment 7162573384, item 1.

## 1. Why

The weights w = 1/σ² of section 5 are finite for every finite σ > 0 down to about 1e-154, but
their sums are not. Two fixes by arithmetic failed review:
- **The common-scale fallback** committed at `a896c49` (errata 12). With equal errors of 1e-154,
  every weight is finite, yet the sums overflow, so F1 abstains on a curve it should assess.
- **E1**, a preflight bound (never committed; errata 13). Codex's last round gave two witnesses:
  - with equal errors of 4.5e-153, the bound overflows where the actual reductions do not, and
    a `pass` becomes a `fail`;
  - in a 20-point case, the total weight is finite but the sum of the red-noise bin totals
    overflows, and the bound misses it.

This correction removes the cause instead: σ values that no TESS light curve in the normalized
flow can carry are refused before any arithmetic.

## 2. The rule (normative)

**In the normalized flow** (the version-2 gauntlet's flattened curve, with flux normalized to
about 1, section 1), consider the cadences whose time t and flux f are finite.

- **Every σ of those cadences must be finite and lie in [1e-12, 1e3]** (both ends included).
- **Otherwise:**
  - **F1** is `not_assessed`, with the reason `invalid_uncertainty`, and records the counts
    `dropped` and `valid` of the frozen predicate. The screen's outcome is then `unassessed`
    (section 3, rule 3).
  - **Each report-only quantity** is `unavailable`, with the reason `invalid_uncertainty`
    (section 7: a value outside a stated range gives `unavailable`).
- **The reference implementation** (`tests/screen_reference.py`) applies the same rule.
- **Order:** the candidate check comes first, as before; then this rule; then the frozen
  predicate and the 20-point minimum of section 5.

**Unchanged:**
- The weight is w = 1/σ², **unscaled**, as section 5 says. There is no common scale and no
  fallback: the weights adjustment of `a896c49` is withdrawn.
- Every other choice of the specification.

**The reading the agent made** (for the gate to check): "every σ" is read as the σ of the
cadences with finite t and f.
- A cadence whose time or flux is not finite is dropped by the frozen predicate, whatever its σ.
- On a cadence with finite t and f, a σ that is not finite, zero or negative is no longer
  dropped: it makes F1 `not_assessed`. That is stricter than section 5's predicate, and it is the
  more conservative reading: it can only turn an assessment into an abstention, never the
  reverse.

## 3. The floor and the ceiling

**Typical TESS errors in normalized flux.** Source: NASA HEASARC, TESS Science Support Center,
"TESS Telescope Information", https://heasarc.gsfc.nasa.gov/docs/tess/telescope_information.html,
retrieved 2026-11-25; record with the literal excerpts:
[sources/v0.5.11-tess-noise-2026-11-25.md](sources/v0.5.11-tess-noise-2026-11-25.md).
- The page gives 60 ppm on hourly timescales, and about 1% for Tmag = 16.
- Scaled to one cadence under white noise (the agent's arithmetic, an assumption): about 3.3e-4
  to 5.5e-2 at 2 minutes, and about 0.13 for Tmag = 16 at 20 seconds.
- So typical per-cadence σ lie roughly between 1e-4 and 1e-1.

**The floor, 1e-12**, is about eight orders of magnitude below the smallest of those values. It
refuses nothing a TESS curve can carry. It refuses the values that break the arithmetic: both of
Codex's witnesses (about 1e-153) and the case of errata 12 (1e-154).

**The ceiling, 1e3**, is about four orders of magnitude above the largest typical value, and
three above the normalized flux itself. A σ of 1e3 in a flux of about 1 carries no information
about a transit of a fraction of a percent. Larger values are not TESS uncertainties in this
flow; they are unit or column errors.

## 4. No overflow up to 1e7 points (the bound)

Let N ≤ 1e7 be the number of cadences, and every σ ∈ [1e-12, 1e3]. Then every weight satisfies
w = 1/σ² ∈ [1e-6, 1e24]. Let X bound |f|; in the normalized flow f is about 1, and the bound
below holds for any X ≤ 1e100.

1. **Every sum of weights** is a sum of non-negative terms:
   - the valid set, the baseline, a bin, a parity, a MES cell, and the sum of the bin totals;
   - each is at most N·1e24 ≤ 1e31;
   - every partial sum, in **any** order of summation, is at most the same total, so no
     reduction order can overflow.
   - A non-empty set's sum is at least 1e-6, so it never underflows to 0 (the smallest normal
     float64 is about 2.2e-308), and the division of a weighted mean is defined.
2. **Σw·x**, for x a flux or a bin's weighted mean (|x| ≤ X): every partial sum is at most
   1e31·X. A weighted mean is a convex combination, so |x̄| ≤ X up to rounding.
3. **Σw·(x − x̄)²**: every term is at most 1e24·(2X)², and every partial sum at most
   4e31·X².
4. **Red noise:** σ_bin uses the bins' weighted means (bounded by X) and the bins' total weights
   (whose sum is at most 1e31), so items 1 to 3 apply. σ_w², σ_bin² and σ_r² are at most
   (2X)². The pink noise σ_tr is at most 2X·√2.

With X ≤ 1e100, every intermediate is at most 4e31·1e200 = 4e231. That is far below the float64
maximum of about 1.797e308. **So the sums and the weighted means cannot overflow for up to 1e7
points.**
- In particular, the second witness cannot occur: its weights were about 9e306 each, outside the
  range.
- An underflow of a product w·(x − x̄)² to a subnormal or 0 changes a sum by less than
  N·2.3e-308. That is negligible against any σ the rule admits.

**Beyond the bound:** a flux above 1e100 in absolute value is outside the normalized flow.
- If an overflow happens there, the existing guards catch it: a non-finite sum makes the
  quantity unavailable and F1 `not_assessed`.
- It never gives a `pass` or a `fail` from a non-finite value.
- No rescaled second path exists, so no decision can flip between paths.

A test exercises the bound at the floor with 1e7 points (section 5).

## 5. Tests (written and pushed before the code, strict expected failures on `a896c49`)

**Given `unassessed` with the reason `invalid_uncertainty`** (strict expected failures on
`a896c49`):
- Codex's first witness: equal σ = 4.5e-153.
- Codex's second witness: the 20-point case. The test asserts its own precondition, that the
  flat total weight is finite while the sum of the three bin totals overflows.
- The case of errata 12: equal σ = 1e-154. Through `compute_screen`, the outcome is `unassessed`
  and every report-only quantity is `unavailable`, all with that reason.
- Just outside the range: σ = 9.99e-13 and σ = 1.001e3.

**Unchanged by the rule** (they pass before and after):
- **Ordinary errors:** the same state and OE_box as the reviewed path (`a896c49`), at a relative
  tolerance of 1e-9. The values were recorded from `a896c49`:
  - the synthetic planet, seed 3: `pass`, OE_box 2.507454281461856;
  - the binary at half the period, seed 3: `fail`, OE_box 43.09203063661559.
- **The ends of the range** (σ = 1e-12 and σ = 1e3, equal errors): assessed, with the same state
  and OE_box as ordinary errors.
- **The bound of section 4:** the weighted mean and standard deviation of 1e7 points at the floor
  are finite, with fluxes up to 1e100 in absolute value.
- **The reference implementation** gives the same reason.

**The test withdrawn:** the E1 regression test committed at `912087a` required σ = 1e-154 to
give the same assessed F1 as ordinary errors. This rule decides the opposite, so the test is
replaced by the case of errata 12 above.

## 6. What was known when this correction was adopted

- The results of `a896c49` on the synthetic fixtures of step 1:
  - its tests unit step2-c: 171 tests, 0 failures; 22 of 22 expected IDs;
  - proofs (i) to (iii) held.
- E1's tests unit: 172 tests, 0 failures. Its refutation, and both witnesses, are in
  [v0.5.11-consensus/all-commits-r2-codex-answer.md](v0.5.11-consensus/all-commits-r2-codex-answer.md).
- No screen of version 5 has run on real data: this phase is specification and software only.

## 7. Review

- **No Codex round reviews this correction:** the rounds are over (the decision, item 2).
- **Recorded as a deviation:** its review is left to the independent gate, which sees the whole
  phase.
