# Specification A: the weakened scenario, under the definition "presence of the signal"

The maintainer's decision of 2026-10-21, item A, after the diagnosis of the R_min study. A
specification only: no lot, no code. It is fixed **before any new data**.

## A0. A change of objective, decided after a negative result

The R_min study's criterion 5, "Power, incompatible weakening" (map Amendment 19: the lower bound
of the FAIL fraction of the qualified weakened targets ≥ 0.50, a target qualifying when its
last-year round passes decisions 1 and 2 and `0.3 · S_pred,2 ≤ 3`), **was not met**: it could not be
evaluated (n = 0 in every group and R; [../rmin-study/study/README.md](../rmin-study/study/README.md)).
It is **withdrawn**, not met, and not renamed. The objective of the weakened scenario changes, by
the maintainer's decision of 2026-10-21, **after** that negative result: from "a FAIL is expected
when the depth no longer matches" to "detection at reduced depth, and abstention when evidence
lacks". Every record that cites the weakened scenario says this. The old requirement of FAIL is not
kept under another name; nothing here presents it as fulfilled.

## A1. What the blind holdout by year tests (the temporal definition)

For a target and one of its **necessary years** (specification B, B1), the round that hides that
year tests whether the signal **predicted from the other years** (their train candidate's ephemeris
and duration) is **detected in the predicted windows of that hidden year**: `S_meas ≥ min_snr` at
those windows. It does not require the hidden depth to equal the train depth. A PASS says "the
predicted signal was detected where and when it was predicted, in each necessary year"; it does not
show that the depth is stable. **The stability of the depth is outside this test**: it needs a
specification of its own (dilution, aperture, contamination), not part of v0.2.1's current work.

## A2. The weakened scenario's truth, on the evaluator's side only

As built (`rmin_study.SCENARIOS`, `alter_last_year`): the last observing year's transits keep the
fraction `s = 0.3` of their depth; the other years are unchanged; the noise is untouched. The
engine never receives `s`, the scenario or any class below.

For the target's **last-year round** the evaluator computes `ρ = s · S_pred,2` (the **predicted**
SNR of the weakened signal in that year, from the engine's pre-measurement quantity `S_pred,2` and
the known `s`) and puts the target in one class, fixed before the outcome is read. `ρ` rests on the
engine's own error model, whose agreement with the observed scatter is not established (experiment
plan, X2): the classes are **operational classes of predicted detectability**, declared before, not
an established detectability.

| Class | Rule | What the presence test should do |
|---|---|---|
| **D**, predicted detectable | `S_pred,2` finite and `ρ ≥ 8` | detect it: PASS |
| **M**, predicted marginal | `S_pred,2` finite and `3 < ρ < 8` | either; no error label |
| **U**, predicted undetectable | `S_pred,2` finite and `ρ ≤ 3` (zero and negative values included) | not detect it: FAIL or INCONCLUSIVE |
| **N**, not classifiable | `S_pred,2` missing (the round stopped before the hidden noise was estimated) **or non-finite** (`NaN`, `±inf`, as `predicted_error` can give) | the last-year round abstains by construction; the target can still FAIL through another year |

Boundary examples, fixed now: `ρ` = 8 exactly is D; `ρ` = 3 exactly is U; `S_pred,2` = 0 is U;
`S_pred,2` = `NaN` or absent is N.

The bounds 3 and 8 are fixed now, before any data: 3 is the old filter's "an expected hidden SNR
at most 3"; 8 is `min_snr` (5) plus three units of a unit-variance SNR, so that a detection is
expected. They are not to be tuned on any lot.

## A3. The outcomes and their labels (the target's final outcome under specification B)

| Class | PASS | FAIL | INCONCLUSIVE |
|---|---|---|---|
| D | correct detection at reduced depth | **error**: a detectable, present signal declared not detected and inconsistent (a false FAIL at reduced depth) | abstention (a loss of utility, not an error) |
| M | reported, no label | reported, no label | abstention |
| U | reported (a detection beyond expectation), not an error | consistent with the definition (the predicted signal was not detectable and the depth is inconsistent), not an error | abstention |
| N | not expected from the last-year round (would be reported) | reported (through another year) | abstention |

## A4. The metrics, defined now

Per group (and per the scope fixed by the scope rule) and per R:
- **W1, detection at reduced depth:** in D, PASS / all D targets (utility) and PASS / decided D
  targets.
- **W1e, false FAIL at reduced depth:** in D, FAIL / decided D targets, with its one-sided
  Clopper-Pearson upper bound at the study's level.
- **W2, abstention when evidence lacks:** in U and N, INCONCLUSIVE / targets, reported; in M and U
  the PASS, FAIL and INCONCLUSIVE fractions reported, no label.
- **Utility over all weakened targets:** decided / total, beside the error fractions; never
  replacing them.

**The roles, fixed now, before the pilot:** **W1e is an acceptance criterion**: its upper bound ≤
**0.02** (the false-FAIL limit of the constant scenario; proposed, for the maintainer to confirm
before the pilot), with a minimum of decided D targets that the sizing derives from the pilot's
yields. **W1 and W2 are reported, not acceptance criteria**: no pass limit is set for them, so no
limit is chosen from any lot's numbers; the pilot's yields serve only the feasibility and the size
of W1e. Changing a role or a limit needs the maintainer's decision before the pilot is run.

## A5. The compatibility check this needs

Class D needs `S_pred,2 ≥ 8/0.3 ≈ 26.7`; class U needs `S_pred,2 ≤ 10`. The classes do **not**
require the decisions to pass (a stop at decision 2 is an abstention, counted in the class), so they
cannot become empty by a gate as the old filter did. The mandatory check after the b/s calibration
(experiment plan, X4) verifies, with the calibrated `(b, s)`: that the D class's interval is
compatible with decision 2 (`S_pred,2 ≥ 26.7` is above every threshold seen, 9.9 to 13.1). That is
**algebraic** compatibility only: it does not establish a positive yield of decided D targets
through the other gates (timing, replicas, decision 1, the hidden noise), which only the pilot (X5)
can measure. It also records whether a U target's last-year round can be decided at all: with a threshold above
10 it cannot (decision 2 stops it, an abstention), so a U target is then INCONCLUSIVE unless another
year's round FAILs; W2 is then read as abstention only, said so before the lot.

## A6. What this specification does not do

It does not change the engine, the FAIL rule or any threshold. It does not evaluate any data. It
does not define a depth-stability test.
