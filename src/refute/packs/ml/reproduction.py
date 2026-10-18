"""The base reproduction check of an ML claim (fatal; WP3 design 1.0.4, 1.0.5 and 1.0.7).

docs/validation/v0.3/wp3-acceptance.md:

- **1.0.4, base value:** "The reproduced value ``x_rep`` is the arithmetic mean of the
  ``n_base`` extracted values. With ``n_base`` < ``reported_n_seeds``, the dossier says
  the mean is over fewer seeds than the paper's."
- **1.0.5, pairing:** both methods of a comparison run with the same seeds; "``d`` is
  computed for each seed and ``d_rep`` is the mean of the per-seed differences", oriented
  so that a positive ``d`` is an advantage in the claimed sense.
- **1.0.7, coverage:** ``base_reproduction`` has positive and negative minimums of
  ``n_base`` (the compared value is the mean of the base runs).

The check applies the claim's predicate (predicates.py: a value mode, or a comparison mode
with its tolerance) to the mean. It needs every base run: with a run missing, the mean is
not the one the claim fixed, and the check is ``INCONCLUSIVE`` (never a failure), with the
valid runs as its coverage.

**The mean is exact.** The values and their differences are summed as fractions, with no
rounding; a sequential sum in 50-digit decimals could cancel a small advantage (1 + 1e-50
- 1 gives 0) and turn it into a tie (Codex review). A mean that is a finite decimal goes to
the predicate exactly; any other mean is decided from its 50-digit roundings down and up,
and only when no rounding can change the answer (``decide_on_mean``); otherwise the check
is ``INCONCLUSIVE``, never a conclusion. A value at the limit stays at the limit.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from decimal import ROUND_CEILING, ROUND_FLOOR, Decimal, Inexact, localcontext
from fractions import Fraction

from refute.core.paper import BASE_REPRODUCTION
from refute.core.verdict import Severity, TestResult, TestStatus
from refute.packs.ml import predicates as pr

Predicate = Callable[[Decimal], pr.Outcome]
ORIENTATIONS = ("method_minus_reference", "reference_minus_method")
UNDECIDABLE_MEAN = "the exact mean is too close to a limit to decide at 50 digits"


def exact_mean(values: Sequence[Decimal]) -> Fraction:
    """The mean of decimal values as an exact fraction."""
    if not values:
        raise ValueError("a mean needs at least one value")
    return sum((Fraction(v) for v in values), Fraction(0)) / len(values)


def _rounded(value: Fraction, rounding: str) -> Decimal:
    with localcontext() as ctx:
        ctx.prec = pr.PRECISION
        ctx.rounding = rounding
        return Decimal(value.numerator) / Decimal(value.denominator)


def _finite_decimal(value: Fraction) -> Decimal | None:
    """``value`` as an exact Decimal when it is a finite decimal (its reduced
    denominator has no prime factor but 2 and 5), whatever its number of digits."""
    den, twos, fives = value.denominator, 0, 0
    while den % 2 == 0:
        den, twos = den // 2, twos + 1
    while den % 5 == 0:
        den, fives = den // 5, fives + 1
    if den != 1:
        return None
    k = max(twos, fives)
    scaled = value * 10**k  # an integer
    return Decimal(f"{scaled.numerator}E-{k}")  # built from text: exact at any length


def decide_on_mean(values: Sequence[Decimal], predicate: Predicate) -> tuple[pr.Outcome, Fraction]:
    """The predicate on the exact mean of ``values``.

    A mean that is a finite decimal (the usual case: a sum of decimals divided by a power
    of 2 or 5, or by 1) is given to the predicate exactly. Otherwise the mean lies
    strictly between its 50-digit roundings down and up, and the decision uses that every
    predicate of predicates.py passes on a convex set (an interval or a half-line):

    - PASS at both roundings is PASS (the whole bracket is inside the convex set);
    - different answers, or any INCONCLUSIVE, give INCONCLUSIVE;
    - FAIL at both roundings is FAIL unless the passing set could lie entirely between
      them: a bounded passing set has the width ``2 x tolerance`` (``two_sided``,
      ``magnitude``), so when the outcome reports a tolerance whose double is below the
      bracket, the answer is INCONCLUSIVE (Codex review).
    """
    mean = exact_mean(values)
    exact = _finite_decimal(mean)
    if exact is not None:
        return predicate(exact), mean
    low, high = _rounded(mean, ROUND_FLOOR), _rounded(mean, ROUND_CEILING)
    first, second = predicate(low), predicate(high)
    undecided = pr.Outcome(TestStatus.INCONCLUSIVE, UNDECIDABLE_MEAN)
    if first.status is not second.status or first.status is TestStatus.INCONCLUSIVE:
        return undecided, mean
    if first.status is TestStatus.PASS:
        return first, mean
    bracket = Fraction(high) - Fraction(low)
    for outcome in (first, second):
        # a square-root tolerance by its exact square, never by its rounded record
        if outcome.squared is not None:
            narrow = 4 * outcome.squared < bracket * bracket
        else:
            narrow = outcome.tolerance is not None and 2 * Fraction(outcome.tolerance) < bracket
        if narrow:
            return undecided, mean
    return first, mean


def mean_text(mean: Fraction) -> str:
    """The mean for the record: the exact decimal when it is a finite decimal, otherwise
    the fraction itself."""
    exact = _finite_decimal(mean)
    return str(exact) if exact is not None else f"{mean.numerator}/{mean.denominator}"


def oriented_differences(
    method: Sequence[pr.Number | None],
    reference: Sequence[pr.Number | None],
    orientation: str,
) -> list[Decimal | None]:
    """The per-seed differences of a comparison, oriented (1.0.5). A seed with either
    value missing has no difference."""
    if orientation not in ORIENTATIONS:
        raise ValueError(f"orientation is one of {ORIENTATIONS}")
    if len(method) != len(reference):
        raise ValueError("the method and the reference run with the same seeds")
    out: list[Decimal | None] = []
    for m, r in zip(method, reference, strict=True):
        if m is None or r is None:
            out.append(None)
            continue
        a, b = pr.dec(m, "a method value"), pr.dec(r, "a reference value")
        with localcontext() as ctx:
            # exact: the precision spans from the highest digit to the lowest exponent of
            # the two operands, and any rounding would raise (Inexact is trapped)
            low = min(a.as_tuple().exponent, b.as_tuple().exponent)
            ctx.prec = max(pr.PRECISION, max(a.adjusted(), b.adjusted()) - low + 2)
            ctx.traps[Inexact] = True
            out.append(a - b if orientation == "method_minus_reference" else b - a)
    return out


def base_reproduction(
    values: Sequence[pr.Number | None],
    predicate: Predicate,
    reported_n_seeds: int | None = None,
) -> TestResult:
    """The fatal check ``base_reproduction``: the claim's predicate on the mean of the
    ``n_base`` base values (``x`` for a value claim, the oriented ``d`` for a
    comparison). ``None`` marks a run that is missing, interrupted or invalid."""
    n_base = len(values)
    if n_base < 1:
        raise ValueError("a base reproduction has at least one run")
    xs = [None if v is None else pr.dec(v, "a base value") for v in values]
    valid = [x for x in xs if x is not None]
    notes = []
    if reported_n_seeds is not None and n_base < reported_n_seeds:
        notes.append(f"the mean is over {n_base} seeds, fewer than the paper's {reported_n_seeds}")
    metrics: dict[str, object] = {"n_base": n_base, "valid_runs": len(valid)}
    if len(valid) < n_base:
        message = f"{len(valid)} valid base runs of {n_base}: the mean needs every run"
        status = TestStatus.INCONCLUSIVE
    else:
        outcome, mean = decide_on_mean(valid, predicate)
        metrics["mean"] = mean_text(mean)
        status, message = outcome.status, outcome.reason
    return TestResult(
        BASE_REPRODUCTION,
        status,
        Severity.FATAL,
        "; ".join([message, *notes]),
        metrics=metrics,
        coverage=len(valid),
        coverage_unit="base runs",
    )
