# Verdicts

A claim is never "proven". It survives the attacks, or it does not. There is no
`TRUE`.

## Discovery verdicts (signals)

| Verdict | Meaning |
|---|---|
| `SURVIVED` | The signal is significant and every test passed. |
| `WEAKENED` | No fatal failure, but at least one warning-level failure. |
| `REFUTED` | At least one fatal failure. |
| `INCONCLUSIVE` | The signal is not significant (gate failed), or a required test could not be decided. |

## Paper verdicts (from v0.3)

`REPRODUCED`, `FRAGILE`, `NOT_REPRODUCED`, `NOT_REPRODUCIBLE`. Defined in the
code, not used in v0.1.

## Test results

Every test returns `PASS`, `FAIL` or `INCONCLUSIVE` (never a silent skip), with a
severity that says what a failure means:

- `gate`: the signal itself is not significant, so nothing can be attacked;
- `fatal`: the failure refutes the claim;
- `warning`: the failure weakens the claim.

A test may report a different severity for different outcomes. For example the
secondary-eclipse test is fatal for a deep eclipse at phase 0.5 and a warning for a
shallow one.

## Aggregation (deterministic)

Rules are applied in order; the first that matches decides:

1. a gate test that did not `PASS` -> `INCONCLUSIVE`;
2. any fatal `FAIL` -> `REFUTED`;
3. any `INCONCLUSIVE` test -> `INCONCLUSIVE`;
4. any warning `FAIL` -> `WEAKENED`;
5. otherwise -> `SURVIVED`.

A fatal failure refutes even when another test is inconclusive. A missing stellar
radius can never turn into a pass: the plausibility test is then `INCONCLUSIVE`,
and so is the verdict unless something else already refuted the signal.

## Calibration claims

For a calibration claim, per-target verdicts feed the claim's pass criteria. A
known planet *recovered* means its period was found within the tolerance. A known
false positive *flagged* means its verdict is `REFUTED`. The degeneracy guard caps
how many known planets may be `REFUTED`, so a gauntlet that refutes everything
fails the claim. Analysis errors count against the claim.

Verdicts are about claims, never about the people who made them.
