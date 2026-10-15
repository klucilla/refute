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
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from refute.core.verdict import TestStatus

Status = Literal["converted", "none", "not_convertible"]
NOT_CONVERTIBLE = "reported uncertainty not convertible"


@dataclass(frozen=True)
class ToleranceParams:
    rel_tol: float
    k_sd: float
    abs_floor: float

    def __post_init__(self) -> None:
        for name in ("rel_tol", "k_sd", "abs_floor"):
            value = getattr(self, name)
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be finite and at least 0")


@dataclass(frozen=True)
class PublishedUncertainty:
    """The resolved uncertainty record of 1.0.9: its status and, when converted, the SD
    in the claim's unit."""

    status: Status
    sd: float | None = None

    def __post_init__(self) -> None:
        if self.status == "converted":
            if self.sd is None or not math.isfinite(self.sd) or self.sd < 0:
                raise ValueError("a converted uncertainty has a finite sd of at least 0")
        elif self.sd is not None:
            raise ValueError(f"an uncertainty with status {self.status} has no sd")


NONE = PublishedUncertainty("none")


@dataclass(frozen=True)
class Tolerance:
    """A tolerance, or only its lower bound when an uncertainty was not convertible."""

    value: float
    lower_bound: bool = False


@dataclass(frozen=True)
class Outcome:
    status: TestStatus
    reason: str
    tolerance: float | None = None


def one_number(x: float, params: ToleranceParams, uncertainty: PublishedUncertainty) -> Tolerance:
    """``max(abs_floor, rel_tol · |x|, k_sd · sd)`` (plan line 415; 1.0.9)."""
    _finite(x, "the published value")
    base = max(params.abs_floor, params.rel_tol * abs(x))
    if uncertainty.status == "converted":
        return Tolerance(max(base, params.k_sd * uncertainty.sd))
    return Tolerance(base, lower_bound=uncertainty.status == "not_convertible")


def difference_tolerance(
    p: float,
    params: ToleranceParams,
    reported_method: float,
    reported_reference: float,
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
    return Tolerance(
        math.sqrt(tol_m.value**2 + tol_b.value**2),
        lower_bound=tol_m.lower_bound or tol_b.lower_bound,
    )


def _finite(value: float, what: str) -> None:
    if not math.isfinite(value):
        raise ValueError(f"{what} must be finite")


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
    x_rep: float,
    reported: float,
    mode: Literal["two_sided", "one_sided_at_least", "one_sided_at_most"],
    tol: Tolerance,
) -> Outcome:
    """The value modes (plan section 6.2)."""
    _finite(x_rep, "the reproduced value")
    _finite(reported, "the published value")
    if mode == "two_sided":
        holds = abs(x_rep - reported) <= tol.value
        what = f"|{x_rep} - {reported}| <= {tol.value}"
    elif mode == "one_sided_at_least":
        holds = x_rep >= reported - tol.value
        what = f"{x_rep} >= {reported} - {tol.value}"
    elif mode == "one_sided_at_most":
        holds = x_rep <= reported + tol.value
        what = f"{x_rep} <= {reported} + {tol.value}"
    else:
        raise ValueError(f"unknown value mode {mode!r}")
    return _easier(holds, tol, what)


def comparison_predicate(
    d_rep: float,
    mode: Literal["direction", "margin", "magnitude"],
    tol: Tolerance | None = None,
    g_pub: float | None = None,
    d_pub: float | None = None,
) -> Outcome:
    """The comparison modes; ``d_rep`` is oriented so that positive is an advantage in
    the claimed sense."""
    _finite(d_rep, "the reproduced difference")
    if mode == "direction":
        if d_rep > 0:
            return Outcome(TestStatus.PASS, f"d_rep = {d_rep} > 0")
        return Outcome(
            TestStatus.FAIL, f"d_rep = {d_rep} is not > 0 (a tie does not keep the direction)"
        )
    if tol is None:
        raise ValueError(f"{mode} needs tol_d")
    if mode == "margin":
        if g_pub is None:
            raise ValueError("margin needs g_pub")
        holds = d_rep >= g_pub - tol.value and d_rep > 0
        return _easier(
            holds,
            tol,
            f"d_rep = {d_rep} >= {g_pub} - {tol.value} and d_rep > 0",
            fails_for_every_tolerance=d_rep <= 0,
        )
    if mode == "magnitude":
        if d_pub is None:
            raise ValueError("magnitude needs d_pub")
        return _easier(abs(d_rep - d_pub) <= tol.value, tol, f"|{d_rep} - {d_pub}| <= {tol.value}")
    raise ValueError(f"unknown comparison mode {mode!r}")


def ablation_predicate(
    d_abl: float,
    mode: Literal["direction", "margin"],
    tol_abl: Tolerance | None = None,
    g_abl: float | None = None,
) -> Outcome:
    """The ablation attack (1.0.6): ``direction`` is ``d_abl > 0``; ``margin`` is
    ``d_abl ≥ g_abl − tol_abl`` and ``d_abl > 0``."""
    if mode == "direction":
        return comparison_predicate(d_abl, "direction")
    if mode == "margin":
        return comparison_predicate(d_abl, "margin", tol_abl, g_pub=g_abl)
    raise ValueError(f"unknown ablation mode {mode!r}")


def ablation_tolerance(
    reported_full: float,
    reported_ablated: float,
    params: ToleranceParams,
    sd_full: float | None,
    sd_ablated: float | None,
) -> Tolerance:
    """``tol_abl = sqrt(tol_full² + tol_ablated²)``, each with its published SD (or no
    ``k_sd`` term without one)."""
    full = one_number(reported_full, params, _sd(sd_full))
    ablated = one_number(reported_ablated, params, _sd(sd_ablated))
    return Tolerance(math.sqrt(full.value**2 + ablated.value**2))


def _sd(value: float | None) -> PublishedUncertainty:
    return NONE if value is None else PublishedUncertainty("converted", value)


def trivial_baseline_predicate(
    x_rep: float,
    baseline: float,
    higher_is_better: bool,
    tol: Tolerance,
) -> Outcome:
    """The claim must beat the baseline by more than its tolerance (1.0.6). A larger
    tolerance makes it harder to pass: under a lower bound a FAIL stands and a PASS
    becomes INCONCLUSIVE."""
    _finite(x_rep, "the reproduced value")
    _finite(baseline, "the baseline")
    advantage = x_rep - baseline if higher_is_better else baseline - x_rep
    what = f"advantage {advantage} over the baseline > {tol.value}"
    if advantage <= tol.value:
        return Outcome(TestStatus.FAIL, f"{what} does not hold", tol.value)
    if tol.lower_bound:
        return Outcome(
            TestStatus.INCONCLUSIVE,
            f"{what} holds only under the lower tolerance: {NOT_CONVERTIBLE}",
            tol.value,
        )
    return Outcome(TestStatus.PASS, f"{what} holds", tol.value)


def widen(tol: Tolerance, factor: float) -> Tolerance:
    """The holdout's wider tolerance (1.0.10): the claim's tolerance times
    ``factor`` (≥ 1). A lower bound stays a lower bound."""
    if not math.isfinite(factor) or factor < 1:
        raise ValueError("the holdout factor is at least 1")
    return Tolerance(tol.value * factor, tol.lower_bound)
