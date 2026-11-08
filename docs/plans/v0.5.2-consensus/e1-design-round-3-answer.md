## Verdict: SURVIVED, round 3 of 3

**Both remaining objections are answered. No further changes required within this review’s scope.**

- **Availability intervals:** Numerators and denominators use the same curve-bootstrap draws across arms. Both availability and its paired difference against A receive intervals. Zero denominators remain undefined. See [_cell](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e1_mask.py:359).
- **Undefined statistics:** Guards, the 100-contributing-curve minimum, interval checks, null serialization and `allow_nan=False` are implemented. Undefined `rho` or its interval produces **NOT ESTABLISHED**, with the arm and cell identified. See [decision guards](/C:/Projetos/refute/docs/validation/v0.5.2/stage1/e1_mask.py:512).

In-memory checks confirmed:

- Empty cells return NOT ESTABLISHED, with null statistics.
- 99 contributing curves fail the minimum; 100 satisfy it.
- Exactly 5 undefined replicates out of 500 are permitted; 6 make the interval undefined.
- Outputs serialize successfully as strict JSON.

No E1 units executed, no files changed, and the prohibited directory was not accessed. This verdict covers the two requested fixes, not experimental results.

