"""Reproduction predicates of ML claims (plan section 6.2; WP3 design, sections 1.0.5,
1.0.6, 1.0.9 and 1.0.10 of docs/validation/v0.3/wp3-acceptance.md).

The base reproduction compares the runs with **the claim published in the paper**;
``metric_recompute`` (recompute.py) is a different check and never reads the paper.

**One-number tolerance.** ``max(abs_floor, rel_tol · |x|, k_sd · sd)``, where ``sd``
comes from the published uncertainty of ``x`` (1.0.9): with status ``converted`` the
``k_sd`` term uses it; with ``none`` there is no ``k_sd`` term; with
``not_convertible`` the true tolerance is unknown and only known to be **at least**
the tolerance without the ``k_sd`` term (a lower bound).

**Lower bounds.** A conclusion stands only if it holds for every tolerance at or above
the lower bound; otherwise the check is INCONCLUSIVE with the reason "reported
uncertainty not convertible". For a predicate that a larger tolerance makes easier to
pass (the value modes, ``magnitude``, the tolerance part of ``margin`` and ablation
``margin``), a PASS at the lower bound stands and a FAIL does not, except a FAIL that
holds for every tolerance (``d ≤ 0`` in ``margin``). For a predicate that a larger
tolerance makes harder to pass (``trivial_baseline``), a FAIL at the lower bound stands
and a PASS does not. ``direction`` uses no tolerance.

Equality at the limit counts as reproduced for the value modes and ``magnitude``; never
for ``direction`` or for the ``d > 0`` part of ``margin`` (plan section 6.2).

**Exact decimal arithmetic.** Published values, tolerances and reproduced values are
decimal numbers; in binary floats ``61.2 − 60`` is ``1.2000000000000028``, which would
move a value at the limit across it (Codex review). Every number is therefore taken as
a ``Decimal``: a ``Decimal`` or a decimal text as given, an int exactly, and a float by
its shortest representation (``repr``, which reads back as the same float). The
predicates decide **exactly**, whatever the number of digits (a token read from a binary
float has up to hundreds, wp3-tensorboard-acceptance.md): comparisons on exact
fractions, tolerances as exact sums, products and maxima, and a square-root tolerance
kept as its exact square and compared by squares; only the record shows a square root
rounded down to 50 digits. The runner passes the reproduced value as the exact decimal
mean of the extracted tokens.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal, Inexact, localcontext
from fractions import Fraction
from typing import Literal

from refute.core.verdict import TestStatus

Status = Literal["converted", "none", "not_convertible"]
Number = Decimal | float | int | str
NOT_CONVERTIBLE = "reported uncertainty not convertible"
PRECISION = 50
_DECIMAL = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


def dec(value: Number, what: str = "a value") -> Decimal:
    """``value`` as an exact finite Decimal (floats by their shortest representation)."""
    if isinstance(value, bool):
        raise ValueError(f"{what} is a boolean, not a number")
    if isinstance(value, Decimal):
        out = value
    elif isinstance(value, int):
        out = Decimal(value)
    elif isinstance(value, float):
        out = Decimal(repr(value)) if value == value and abs(value) != float("inf") else None
    elif isinstance(value, str) and _DECIMAL.match(value.strip()):
        out = Decimal(value.strip())
    else:
        out = None
    if out is None or not out.is_finite():
        raise ValueError(f"{what} must be a finite number")
    return out


@dataclass(frozen=True)
class ToleranceParams:
    rel_tol: Decimal
    k_sd: Decimal
    abs_floor: Decimal

    def __init__(self, rel_tol: Number, k_sd: Number, abs_floor: Number):
        for name, value in (("rel_tol", rel_tol), ("k_sd", k_sd), ("abs_floor", abs_floor)):
            number = dec(value, name)
            if number < 0:
                raise ValueError(f"{name} must be at least 0")
            object.__setattr__(self, name, number)


@dataclass(frozen=True)
class PublishedUncertainty:
    """The resolved uncertainty record of 1.0.9: its status and, when converted, the SD
    in the claim's unit."""

    status: Status
    sd: Decimal | None = None

    def __init__(self, status: Status, sd: Number | None = None):
        if status not in ("converted", "none", "not_convertible"):
            raise ValueError(f"unknown uncertainty status {status!r}")
        if status == "converted":
            if sd is None or dec(sd, "sd") < 0:
                raise ValueError("a converted uncertainty has a finite sd of at least 0")
            sd = dec(sd, "sd")
        elif sd is not None:
            raise ValueError(f"an uncertainty with status {status} has no sd")
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "sd", sd)


NONE = PublishedUncertainty("none")


@dataclass(frozen=True)
class Tolerance:
    """A tolerance, or only its lower bound when an uncertainty was not convertible.

    A tolerance that is a square root (``sqrt(a² + b²)``) keeps its exact square in
    ``squared``: the predicates then decide by comparing squares, and ``value`` is only its
    50-digit approximation for the record (wp3-tensorboard-acceptance.md, Codex review)."""

    value: Decimal
    lower_bound: bool = False
    squared: Fraction | None = None

    def __init__(self, value: Number, lower_bound: bool = False, squared: Fraction | None = None):
        number = dec(value, "a tolerance")
        if number < 0 or (squared is not None and squared < 0):
            raise ValueError("a tolerance is at least 0")
        object.__setattr__(self, "value", number)
        object.__setattr__(self, "lower_bound", lower_bound)
        object.__setattr__(self, "squared", squared)


def _within(lhs: Fraction, tol: Tolerance) -> bool:
    """``lhs <= tol``, exactly (by squares for a square-root tolerance)."""
    if tol.squared is not None:
        return lhs <= 0 or lhs * lhs <= tol.squared
    return lhs <= Fraction(tol.value)


def _exact(a: Decimal, b: Decimal, op: str) -> Decimal:
    """``a + b``, ``a - b`` or ``a * b`` with no rounding: the precision covers every digit
    of the result, and any rounding would raise (Inexact is trapped)."""
    with localcontext() as ctx:
        ctx.traps[Inexact] = True
        if op == "*":
            ctx.prec = max(PRECISION, len(a.as_tuple().digits) + len(b.as_tuple().digits) + 1)
            return a * b
        low = min(a.as_tuple().exponent, b.as_tuple().exponent)
        ctx.prec = max(PRECISION, max(a.adjusted(), b.adjusted()) - int(low) + 2)
        return a + b if op == "+" else a - b


@dataclass(frozen=True)
class Outcome:
    status: TestStatus
    reason: str
    tolerance: Decimal | None = None


def one_number(x: Number, params: ToleranceParams, uncertainty: PublishedUncertainty) -> Tolerance:
    """``max(abs_floor, rel_tol · |x|, k_sd · sd)`` (plan line 415; 1.0.9), exactly."""
    # copy_abs, not abs(): abs() rounds to the context's precision
    relative = _exact(params.rel_tol, dec(x, "the published value").copy_abs(), "*")
    base = max(params.abs_floor, relative)
    if uncertainty.status == "converted":
        return Tolerance(max(base, _exact(params.k_sd, uncertainty.sd, "*")))
    return Tolerance(base, lower_bound=uncertainty.status == "not_convertible")


def difference_tolerance(
    p: Number,
    params: ToleranceParams,
    reported_method: Number,
    reported_reference: Number,
    uncertainty_method: PublishedUncertainty,
    uncertainty_reference: PublishedUncertainty,
    paired: PublishedUncertainty,
) -> Tolerance:
    """``tol_d`` of a comparison (1.0.5, 1.0.9). With a paired uncertainty reported
    (converted or not), the one-number tolerance of the published difference ``p``
    (``d_pub`` or ``g_pub``) is used, keeping the paired structure; only when the paper
    reports no paired uncertainty, ``sqrt(tol_m² + tol_b²)``."""
    if paired.status != "none":
        return one_number(p, params, paired)
    tol_m = one_number(reported_method, params, uncertainty_method)
    tol_b = one_number(reported_reference, params, uncertainty_reference)
    return _hypot(tol_m.value, tol_b.value, tol_m.lower_bound or tol_b.lower_bound)


def _root(squared: Fraction) -> Decimal:
    """The 50-digit square root of an exact square, rounded down (for the record only)."""
    with localcontext() as ctx:
        ctx.prec = PRECISION + 10
        root = (Decimal(squared.numerator) / Decimal(squared.denominator)).sqrt()
        ctx.prec, ctx.rounding = PRECISION, ROUND_FLOOR
        return ctx.plus(root)


def _hypot(a: Decimal, b: Decimal, lower_bound: bool = False) -> Tolerance:
    """``sqrt(a² + b²)``, kept as its exact square (``Tolerance.squared``)."""
    squared = Fraction(a) ** 2 + Fraction(b) ** 2
    return Tolerance(_root(squared), lower_bound, squared)


def _easier(
    holds: bool, tol: Tolerance, what: str, fails_for_every_tolerance: bool = False
) -> Outcome:
    """A predicate that a larger tolerance makes easier to pass."""
    if holds:
        return Outcome(TestStatus.PASS, f"{what} holds", tol.value)
    if tol.lower_bound and not fails_for_every_tolerance:
        return Outcome(
            TestStatus.INCONCLUSIVE,
            f"{what} fails only under the lower tolerance: {NOT_CONVERTIBLE}",
            tol.value,
        )
    return Outcome(TestStatus.FAIL, f"{what} does not hold", tol.value)


def value_predicate(
    x_rep: Number,
    reported: Number,
    mode: Literal["two_sided", "one_sided_at_least", "one_sided_at_most"],
    tol: Tolerance,
) -> Outcome:
    """The value modes (plan section 6.2)."""
    x, r, t = dec(x_rep, "the reproduced value"), dec(reported, "the published value"), tol.value
    fx, fr = Fraction(x), Fraction(r)
    if mode == "two_sided":
        holds, what = _within(abs(fx - fr), tol), f"|{x} - {r}| <= {t}"
    elif mode == "one_sided_at_least":
        holds, what = _within(fr - fx, tol), f"{x} >= {r} - {t}"
    elif mode == "one_sided_at_most":
        holds, what = _within(fx - fr, tol), f"{x} <= {r} + {t}"
    else:
        raise ValueError(f"unknown value mode {mode!r}")
    return _easier(holds, tol, what)


def comparison_predicate(
    d_rep: Number,
    mode: Literal["direction", "margin", "magnitude"],
    tol: Tolerance | None = None,
    g_pub: Number | None = None,
    d_pub: Number | None = None,
) -> Outcome:
    """The comparison modes; ``d_rep`` is oriented so that positive is an advantage in
    the claimed sense."""
    d = dec(d_rep, "the reproduced difference")
    if mode == "direction":
        if d > 0:
            return Outcome(TestStatus.PASS, f"d_rep = {d} > 0")
        return Outcome(
            TestStatus.FAIL, f"d_rep = {d} is not > 0 (a tie does not keep the direction)"
        )
    if tol is None:
        raise ValueError(f"{mode} needs tol_d")
    if mode == "margin":
        if g_pub is None:
            raise ValueError("margin needs g_pub")
        g = dec(g_pub, "g_pub")
        return _easier(
            _within(Fraction(g) - Fraction(d), tol) and d > 0,
            tol,
            f"d_rep = {d} >= {g} - {tol.value} and d_rep > 0",
            fails_for_every_tolerance=d <= 0,
        )
    if mode == "magnitude":
        if d_pub is None:
            raise ValueError("magnitude needs d_pub")
        p = dec(d_pub, "d_pub")
        return _easier(
            _within(abs(Fraction(d) - Fraction(p)), tol), tol, f"|{d} - {p}| <= {tol.value}"
        )
    raise ValueError(f"unknown comparison mode {mode!r}")


def ablation_predicate(
    d_abl: Number,
    mode: Literal["direction", "margin"],
    tol_abl: Tolerance | None = None,
    g_abl: Number | None = None,
) -> Outcome:
    """The ablation attack (1.0.6): ``direction`` is ``d_abl > 0``; ``margin`` is
    ``d_abl ≥ g_abl − tol_abl`` and ``d_abl > 0``."""
    if mode == "direction":
        return comparison_predicate(d_abl, "direction")
    if mode == "margin":
        return comparison_predicate(d_abl, "margin", tol_abl, g_pub=g_abl)
    raise ValueError(f"unknown ablation mode {mode!r}")


def ablation_tolerance(
    reported_full: Number,
    reported_ablated: Number,
    params: ToleranceParams,
    sd_full: Number | None,
    sd_ablated: Number | None,
) -> Tolerance:
    """``tol_abl = sqrt(tol_full² + tol_ablated²)``, each with its published SD (or no
    ``k_sd`` term without one)."""
    full = one_number(reported_full, params, _sd(sd_full))
    ablated = one_number(reported_ablated, params, _sd(sd_ablated))
    return _hypot(full.value, ablated.value)


def _sd(value: Number | None) -> PublishedUncertainty:
    return NONE if value is None else PublishedUncertainty("converted", value)


def trivial_baseline_predicate(
    x_rep: Number,
    baseline: Number,
    higher_is_better: bool,
    tol: Tolerance,
) -> Outcome:
    """The claim must beat the baseline by more than its tolerance (1.0.6). A larger
    tolerance makes it harder to pass: under a lower bound a FAIL stands and a PASS
    becomes INCONCLUSIVE."""
    x, b = dec(x_rep, "the reproduced value"), dec(baseline, "the baseline")
    advantage = _exact(x, b, "-") if higher_is_better else _exact(b, x, "-")
    what = f"advantage {advantage} over the baseline > {tol.value}"
    if _within(Fraction(advantage), tol):
        return Outcome(TestStatus.FAIL, f"{what} does not hold", tol.value)
    if tol.lower_bound:
        return Outcome(
            TestStatus.INCONCLUSIVE,
            f"{what} holds only under the lower tolerance: {NOT_CONVERTIBLE}",
            tol.value,
        )
    return Outcome(TestStatus.PASS, f"{what} holds", tol.value)


def widen(tol: Tolerance, factor: Number) -> Tolerance:
    """The holdout's wider tolerance (1.0.10): the claim's tolerance times
    ``factor`` (≥ 1). A lower bound stays a lower bound."""
    f = dec(factor, "the holdout factor")
    if f < 1:
        raise ValueError("the holdout factor is at least 1")
    if tol.squared is not None:
        squared = tol.squared * Fraction(f) ** 2
        return Tolerance(_root(squared), tol.lower_bound, squared)
    return Tolerance(_exact(tol.value, f, "*"), tol.lower_bound)
