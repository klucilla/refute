"""Published uncertainty of a value or a difference (WP3 design, section 1.0.9).

A record states what the paper printed: an SD, an SE, a confidence interval, or
nothing. Every number comes from the paper, with its location and quote; none comes
from Refute's runs, so a tolerance never depends on a result of the sample.

Resolution converts the record to the standard deviation the tolerance uses, in the
claim's unit, and writes out how:

- ``converted``: ``sd`` given, ``se · sqrt(n)``, or a symmetric ``t`` or ``normal`` CI with
  ``n``: ``se = (upper − lower) / (2 · q)`` with ``q = t(1 − (1 − level)/2, n − 1)`` or
  ``z(1 − (1 − level)/2)``, then ``se · sqrt(n)``;
- ``none``: the paper reports no uncertainty (no ``k_sd`` term);
- ``not_convertible``: reported, but not invertible here (``se`` or ``ci`` without ``n``, a
  CI of method ``other_or_unknown``, or a CI whose half-widths around the published
  value differ by more than 1% of its width). Never treated as "no uncertainty".

Sources (retrieved 2026-10-15): Cochrane Handbook 6.5.2.2; NIST/SEMATECH e-Handbook
1.3.5.2; NIST Dataplot "T TEST" (cited in docs/validation/v0.3/wp3-acceptance.md).
"""

from __future__ import annotations

import math
from typing import Any, Literal

from pydantic import Field, model_validator

from refute.core.claim import StrictModel

UNITS = ("percent", "fraction", "native")
# A CI is symmetric when its two half-widths around the published value differ by at
# most this fraction of its width.
SYMMETRY_TOLERANCE = 0.01
DERIVED = ("status", "sd", "quantile")


class Uncertainty(StrictModel):
    """One published uncertainty record, as printed."""

    kind: Literal["sd", "se", "ci", "none"]
    value: float | None = None
    lower: float | None = None
    upper: float | None = None
    level: float | None = None
    method: Literal["t", "normal", "other_or_unknown"] | None = None
    n: int | None = Field(default=None, ge=2)
    unit: Literal["percent", "fraction", "native"] | None = None
    location: str | None = None
    quote: str | None = None
    # written out by the resolution, never given by hand
    status: Literal["converted", "none", "not_convertible"] | None = None
    sd: float | None = None
    quantile: float | None = None

    @model_validator(mode="after")
    def _check(self) -> Uncertainty:
        given = [name for name in DERIVED if getattr(self, name) is not None]
        if given:
            raise ValueError(f"uncertainty: {', '.join(given)} are derived, never given by hand")
        numbers = {"value": self.value, "lower": self.lower, "upper": self.upper}
        if self.kind == "none":
            extra = [
                k
                for k in ("value", "lower", "upper", "level", "method", "n", "unit")
                if getattr(self, k) is not None
            ]
            if extra:
                raise ValueError(f"uncertainty 'none' takes no {', '.join(extra)}")
            return self
        if not (self.location and self.location.strip() and self.quote and self.quote.strip()):
            raise ValueError("an uncertainty record needs its location and quote in the paper")
        if self.unit is None:
            raise ValueError("an uncertainty record needs the unit it is printed in")
        for name, number in numbers.items():
            if number is not None and not math.isfinite(number):
                raise ValueError(f"uncertainty {name} must be finite")
        if self.kind in ("sd", "se"):
            if self.value is None or self.value < 0:
                raise ValueError(f"uncertainty '{self.kind}' needs a value of at least 0")
            if any(v is not None for v in (self.lower, self.upper, self.level, self.method)):
                raise ValueError(
                    f"uncertainty '{self.kind}' takes no lower, upper, level or method"
                )
            return self
        if self.value is not None:
            raise ValueError("a CI takes lower and upper, not value")
        if self.lower is None or self.upper is None or self.lower >= self.upper:
            raise ValueError("a CI needs lower < upper")
        if self.level is None or not 0 < self.level < 1:
            raise ValueError("a CI needs a level in (0, 1)")
        if self.method is None:
            raise ValueError("a CI needs its method: t, normal or other_or_unknown")
        return self


def unit_factor(from_unit: str, to_unit: str) -> float:
    """× 100 from fraction to percent, ÷ 100 back; ``native`` converts only to itself."""
    if from_unit == to_unit:
        return 1.0
    if "native" in (from_unit, to_unit):
        raise ValueError(f"an uncertainty in {from_unit} cannot be converted to {to_unit}")
    return 100.0 if (from_unit, to_unit) == ("fraction", "percent") else 0.01


def _quantile(method: str, level: float, n: int) -> float:
    from scipy import stats

    q = 1 - (1 - level) / 2
    if method == "t":
        return float(stats.t.ppf(q, n - 1))
    return float(stats.norm.ppf(q))


def resolve_uncertainty(
    record: Uncertainty, metric_unit: str, center: float | None
) -> dict[str, Any]:
    """The record as written in the resolved claim, with ``status``, ``sd`` (in
    ``metric_unit``) and, for a converted CI, the ``quantile`` used. ``center`` is the
    published value the CI is around (in ``metric_unit``), used for its symmetry; with no
    published value the symmetry cannot be checked and the CI is not convertible."""
    out = record.model_dump(mode="json")
    if record.kind == "none":
        out.update(status="none", sd=None, quantile=None)
        return out
    factor = unit_factor(record.unit or "", metric_unit)
    if record.kind == "sd":
        out.update(status="converted", sd=record.value * factor, quantile=None)
        return out
    if record.n is None:
        out.update(status="not_convertible", sd=None, quantile=None)
        return out
    if record.kind == "se":
        out.update(
            status="converted", sd=record.value * factor * math.sqrt(record.n), quantile=None
        )
        return out
    lower, upper = record.lower * factor, record.upper * factor
    width = upper - lower
    symmetric = center is not None and abs((center - lower) - (upper - center)) <= (
        SYMMETRY_TOLERANCE * width
    )
    if record.method == "other_or_unknown" or not symmetric:
        out.update(status="not_convertible", sd=None, quantile=None)
        return out
    q = _quantile(record.method, record.level, record.n)
    se = width / (2 * q)
    out.update(status="converted", sd=se * math.sqrt(record.n), quantile=q)
    return out
