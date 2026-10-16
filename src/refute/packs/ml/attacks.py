"""Evaluation of the robustness attacks of an ML claim (WP3 W3.13).

Plan section 6.3 (docs/plans/v0.3-plan.md, lines 468-493) and the WP3 design, sections
1.0.6 and 1.0.10 of docs/validation/v0.3/wp3-acceptance.md. Each function turns the
values obtained by an attack's runs into the attack's own ``TestResult`` for the WP2
core (``aggregate_claim``); the prerequisites of each attack (its runs and its metric)
are recorded separately by the runner.

General rules (plan lines 474-483):

- a missing, interrupted or invalid run (``None`` here) never counts as a scientific
  failure;
- a valid failure (a run that completed and fails the attack's predicate) can establish
  ``FRAGILE``;
- with no valid failure and incomplete coverage, the attack is ``INCONCLUSIVE``;
- ``seeds`` and ``data_split`` use the claim's own predicate (``Predicate``: the value
  mode or the comparison mode, with the claim's tolerance), so one-sided modes stay
  one-sided; the others keep their own predicates.

A predicate that cannot decide (``INCONCLUSIVE``, for example under a lower tolerance
bound when the published uncertainty is not convertible) is never a valid failure.

These functions decide nothing about the base reproduction and read no claim file: the
caller builds the predicate and the parameters from the resolved claim.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Callable, Hashable, Sequence
from decimal import Decimal, localcontext
from fractions import Fraction

from refute.core.paper import (
    EXPECTED_COVERAGE,
    FAILURE_ESTABLISHED,
    attack_result,
    data_split_attack,
    seeds_attack,
)
from refute.core.verdict import TestResult, TestStatus
from refute.packs.ml import predicates as pr
from refute.packs.ml.reproduction import decide_on_mean

Predicate = Callable[[Decimal], pr.Outcome]

SEED_RUNS = 5
SPLIT_RUNS = 3


def _holds(outcome: pr.Outcome) -> bool | None:
    """PASS holds, FAIL is a valid failure, anything else decides nothing."""
    if outcome.status is TestStatus.PASS:
        return True
    if outcome.status is TestStatus.FAIL:
        return False
    return None


def _values(values: Sequence[pr.Number | None], expected: int, what: str) -> list[Decimal | None]:
    if len(values) != expected:
        raise ValueError(f"{what} expects {expected} run slots, got {len(values)}")
    return [None if v is None else pr.dec(v, f"a {what} value") for v in values]


def seeds(values: Sequence[pr.Number | None], predicate: Predicate) -> TestResult:
    """5 extra seeds: the claim's predicate on each run (at least 4 of 5) and on the
    mean of the 5 runs (only when all 5 are valid). Two valid failures establish the
    failure (WP2 ``seeds_attack``)."""
    xs = _values(values, SEED_RUNS, "seeds")
    runs = [None if x is None else _holds(predicate(x)) for x in xs]
    mean_holds = None
    if all(x is not None for x in xs):
        mean, _ = decide_on_mean(xs, predicate)  # exact mean (reproduction.py)
        mean_holds = _holds(mean)
        if mean_holds is False:
            # the 5 runs exist and the predicate fails conclusively on their mean: a
            # valid failure, also when a single run's predicate could not decide (the
            # WP2 rule would otherwise count that run as missing; Codex review)
            failed = sum(1 for r in runs if r is False)
            result = attack_result(
                "seeds",
                TestStatus.FAIL,
                SEED_RUNS,
                f"the predicate fails on the mean of the 5 runs ({mean.reason}); "
                f"{failed} valid failures in the runs",
            )
            result.metrics = {
                EXPECTED_COVERAGE: SEED_RUNS,
                "valid_runs": SEED_RUNS,
                "valid_failures": failed,
                FAILURE_ESTABLISHED: True,
            }
            return result
    return seeds_attack(runs, mean_holds)


def data_split(values: Sequence[pr.Number | None], predicate: Predicate) -> TestResult:
    """3 re-splits with the same proportions; the claim's predicate must hold in 3 of 3
    (WP2 ``data_split_attack``)."""
    xs = _values(values, SPLIT_RUNS, "data_split")
    return data_split_attack([None if x is None else _holds(predicate(x)) for x in xs])


def _runs_result(name: str, status: TestStatus, valid: int, expected: int, message: str):
    result = attack_result(name, status, valid, message)
    result.metrics = {EXPECTED_COVERAGE: expected, "valid_runs": valid}
    return result


def ablation(
    d_values: Sequence[pr.Number | None],
    mode: str,
    tol_abl: pr.Tolerance | None = None,
    g_abl: pr.Number | None = None,
) -> TestResult:
    """``d_abl`` is the mean over the attack's runs (one per base seed), oriented so that
    a positive value means the component helps in the claimed sense (1.0.6). The mean
    needs every run: with a run missing the attack is INCONCLUSIVE."""
    if not d_values:
        raise ValueError("ablation needs at least one run slot")
    ds = [None if d is None else pr.dec(d, "an ablation difference") for d in d_values]
    valid = [d for d in ds if d is not None]
    if len(valid) < len(ds):
        return _runs_result(
            "ablation",
            TestStatus.INCONCLUSIVE,
            len(valid),
            len(ds),
            f"{len(valid)} valid runs of {len(ds)}: d_abl needs every run",
        )
    outcome, _ = decide_on_mean(valid, lambda d: pr.ablation_predicate(d, mode, tol_abl, g_abl))
    return _runs_result("ablation", outcome.status, len(valid), len(ds), outcome.reason)


def holdout(value: pr.Number | None, predicate: Predicate, factor: pr.Number) -> TestResult:
    """The claim's predicate with its tolerance widened by ``factor`` (1.0.10), applied
    to the value measured on the holdout. ``predicate`` must already use the widened
    tolerance; ``factor`` is recorded."""
    f = pr.dec(factor, "the holdout factor")
    if f < 1:
        raise ValueError("the holdout factor is at least 1")
    if value is None:
        result = _runs_result("holdout", TestStatus.INCONCLUSIVE, 0, 1, "no valid holdout run")
    else:
        outcome = predicate(pr.dec(value, "the holdout value"))
        result = _runs_result("holdout", outcome.status, 1, 1, outcome.reason)
    result.metrics["factor"] = str(f)
    return result


def leakage(
    train_hashes: Sequence[str] | None,
    test_hashes: Sequence[str] | None,
    max_overlap_fraction: pr.Number,
) -> TestResult:
    """Exact duplicates between train and test (plan line 492): the fraction of test
    examples whose hash appears in train. Above ``max_overlap_fraction`` is a valid
    failure. Empty or missing splits examine nothing: INCONCLUSIVE, never PASS."""
    limit = pr.dec(max_overlap_fraction, "max_overlap_fraction")
    if not 0 <= limit < 1:
        raise ValueError("max_overlap_fraction must be in [0, 1)")
    if not train_hashes or not test_hashes:
        result = attack_result(
            "leakage", TestStatus.INCONCLUSIVE, 0, "a split to compare is empty or missing"
        )
        result.coverage_unit = "test examples"
        return result
    train = set(train_hashes)
    overlap = sum(1 for h in test_hashes if h in train)
    fraction = Fraction(overlap, len(test_hashes))
    above = fraction > Fraction(limit)
    message = (
        f"{overlap} of {len(test_hashes)} test examples also in train "
        f"(fraction {float(fraction):.6g}; limit {limit})"
    )
    result = attack_result(
        "leakage", TestStatus.FAIL if above else TestStatus.PASS, len(test_hashes), message
    )
    result.coverage_unit = "test examples"
    result.metrics = {
        "overlap": overlap,
        "test_examples": len(test_hashes),
        "fraction": f"{fraction.numerator}/{fraction.denominator}",
    }
    return result


def trivial_baseline_value(
    kind: str,
    labels: Sequence[Hashable],
    metric: str,
    unit: str,
    train_labels: Sequence[Hashable] | None = None,
    test_labels: Sequence[Hashable] | None = None,
) -> Decimal:
    """The baseline of 1.0.6 in the claim's unit (``percent`` or ``fraction``):

    - ``random``: the expected value of a uniform guess among the ``K`` declared labels,
      computed exactly: accuracy ``1/K``, error rate ``1 - 1/K``;
    - ``majority``: the most frequent class of the training labels predicted for every
      test example. When several classes tie for the most frequent, the tied class with
      the lowest accuracy on the test labels is used, the weakest baseline, so that a tie
      never produces a failure the data do not force. The concession: a PASS then means
      beating the weakest of the tied classes, not every one of them (a provisional
      decision of 2026-10-16 under the maintainer's night delegation, waiting for
      ratification).
    """
    if metric not in ("accuracy", "error_rate"):
        raise ValueError("trivial_baseline applies only to accuracy and error_rate")
    declared = list(labels)
    if len(declared) < 2 or len(set(declared)) != len(declared):
        raise ValueError("trivial_baseline needs at least 2 distinct declared labels")
    if kind == "random":
        accuracy = Fraction(1, len(declared))
    elif kind == "majority":
        if not train_labels or not test_labels:
            raise ValueError("the majority baseline needs the training and test labels")
        unknown = (set(train_labels) | set(test_labels)) - set(declared)
        if unknown:
            raise ValueError(f"labels outside the declared classes: {sorted(map(str, unknown))}")
        counts = Counter(train_labels)
        top = max(counts.values())
        tied = [c for c in declared if counts.get(c, 0) == top]
        test_counts = Counter(test_labels)
        accuracy = min(Fraction(test_counts.get(c, 0), len(test_labels)) for c in tied)
    else:
        raise ValueError(f"unknown baseline kind {kind!r}")
    value = accuracy if metric == "accuracy" else 1 - accuracy
    scale = {"percent": 100, "fraction": 1}.get(unit)
    if scale is None:
        raise ValueError("trivial_baseline needs a claim in percent or fraction")
    with localcontext() as ctx:
        ctx.prec = pr.PRECISION
        return Decimal(value.numerator * scale) / Decimal(value.denominator)


def trivial_baseline(
    x_rep: pr.Number,
    baseline: pr.Number,
    higher_is_better: bool,
    tol: pr.Tolerance,
    coverage: int,
) -> TestResult:
    """The claim must beat the baseline by more than its tolerance (1.0.6).
    ``coverage`` is the number of test labels examined (majority) or 1 (random, an exact
    expectation)."""
    if coverage < 1:
        return attack_result(
            "trivial_baseline", TestStatus.INCONCLUSIVE, 0, "no test label was examined"
        )
    outcome = pr.trivial_baseline_predicate(x_rep, baseline, higher_is_better, tol)
    result = attack_result("trivial_baseline", outcome.status, coverage, outcome.reason)
    result.metrics = {"baseline": str(pr.dec(baseline, "the baseline"))}
    return result
