"""``metric_recompute`` (WP3; docs/validation/v0.3/wp3-acceptance.md, section 1.7).

**What this check is, and what it is not.** It checks the chain inside one run: it
recomputes the metric from the predictions the run saved and compares the result with
the value **that same run printed**. It never reads the paper. Comparing the runs with
the claim published in the paper is the base reproduction, a separate check
(``base_reproduction``), which this module does not compute.

Two independent implementations compute each metric: Refute's own (numpy, below) and
scikit-learn, with every convention passed explicitly. A run is decided only when the
two agree with each other (``|a - b| <= 1e-9 * max(1, |a|)``):

- both inside the printed interval (widened by that epsilon): PASS;
- both outside it, on the same side: FAIL (a valid failure), unless the rounding of
  the printed value is ``unknown``;
- anything else, including an implementation that cannot compute: INCONCLUSIVE.

A limitation of Refute (an unsupported case, an unreadable file, a zero denominator
under ``zero_division: undefined``) is always INCONCLUSIVE, never a failure.
"""

from __future__ import annotations

import csv
import json
import math
import re
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from decimal import Decimal, localcontext
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np

from refute.core.paper import EXPECTED_COVERAGE, FAILURE_ESTABLISHED, METRIC_RECOMPUTE
from refute.core.verdict import Severity, TestResult, TestStatus

CLASSIFICATION = ("accuracy", "error_rate", "precision", "recall", "f1", "auroc")
REGRESSION = ("mae", "mse", "rmse", "r2")
SUPPORTED_METRICS = CLASSIFICATION + REGRESSION
AVERAGES = ("binary", "macro", "micro", "weighted")
ZERO_DIVISION = ("0", "1", "undefined")
UNITS = ("percent", "fraction", "native")
ROUNDINGS = ("nearest", "truncate", "unknown")
FORMATS = ("npy", "csv", "jsonl")

_NUMBER = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


class RecomputeError(Exception):
    """The recomputation cannot be done (a Refute-side limitation): INCONCLUSIVE."""


class UndefinedMetricError(RecomputeError):
    """The metric is undefined under the declared convention (for example a zero
    denominator under ``zero_division: undefined``): INCONCLUSIVE."""


# ---- conventions ---------------------------------------------------------------------


@dataclass(frozen=True)
class Convention:
    """The conventions of one metric, fixed in the claim before the lock (W3.15)."""

    metric: str
    scale: str
    labels: tuple[Any, ...] | None = None
    average: str | None = None
    pos_label: Any = None
    zero_division: str | None = None

    def validate(self) -> None:
        """Raises ValueError for a metric or convention outside W3.15."""
        if self.metric not in SUPPORTED_METRICS:
            raise ValueError(f"unsupported metric: {self.metric!r}")
        if self.metric in REGRESSION:
            if self.scale != "native":
                raise ValueError(f"{self.metric} takes scale 'native'")
            if self.labels is not None or self.average or self.pos_label is not None:
                raise ValueError(f"{self.metric} takes no labels, average or pos_label")
            if self.zero_division is not None:
                raise ValueError(f"{self.metric} takes no zero_division")
            return
        if self.scale not in ("percent", "fraction"):
            raise ValueError(f"{self.metric} takes scale 'percent' or 'fraction'")
        labels = self.labels or ()
        if len(labels) < 2 or len({_key(v) for v in labels}) != len(labels):
            raise ValueError("labels must be at least 2 distinct classes")
        if any(isinstance(v, bool | float) for v in labels):
            raise ValueError("labels must be integers or strings")
        if self.metric in ("accuracy", "error_rate"):
            if self.average or self.pos_label is not None or self.zero_division is not None:
                raise ValueError(f"{self.metric} takes no average, pos_label or zero_division")
        elif self.metric == "auroc":
            if len(labels) != 2 or _key(self.pos_label) not in {_key(v) for v in labels}:
                raise ValueError("auroc needs exactly 2 labels and a pos_label among them")
            if self.average or self.zero_division is not None:
                raise ValueError("auroc takes no average or zero_division")
        else:
            if self.average not in AVERAGES:
                raise ValueError(f"average must be one of {AVERAGES}")
            if self.zero_division not in ZERO_DIVISION:
                raise ValueError(f"zero_division must be one of {ZERO_DIVISION}")
            if self.average == "binary":
                if len(labels) != 2 or _key(self.pos_label) not in {_key(v) for v in labels}:
                    raise ValueError("binary averaging needs 2 labels and a pos_label among them")
            elif self.pos_label is not None:
                raise ValueError("pos_label is only for binary averaging")


def _key(value: Any) -> str:
    """Labels are matched by their text, so 1 in a npy file and "1" in a CSV are the same
    class, and 1.0 is not."""
    return str(value)


# ---- readers (W3.18: they execute no stored object) ----------------------------------


def read_predictions(path: Path, fmt: str, fields: dict[str, str]) -> dict[str, np.ndarray]:
    """The declared fields of a predictions file, as arrays of equal length.

    ``fields`` maps a role (``y_true``, and ``y_pred`` or ``y_score``) to the field,
    column or key name in the file. ``npy`` is a structured array read with
    ``allow_pickle=False``; ``csv`` is read with the standard library; ``jsonl`` with the
    standard JSON parser, refusing NaN and infinities.
    """
    if fmt not in FORMATS:
        raise RecomputeError(f"unsupported predictions format: {fmt!r}")
    try:
        if fmt == "npy":
            data = np.load(path, allow_pickle=False)
            names = data.dtype.names or ()
            out = {}
            for role, name in fields.items():
                if name not in names:
                    raise RecomputeError(f"field {name!r} not in {path.name}")
                column = data[name]
                if column.dtype.kind not in "biuUf":
                    raise RecomputeError(f"field {name!r} has an unsupported dtype {column.dtype}")
                out[role] = np.asarray(column).ravel()
            return _equal_lengths(out)
        if fmt == "csv":
            with path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                header = reader.fieldnames or []
                for name in fields.values():
                    if name not in header:
                        raise RecomputeError(f"column {name!r} not in {path.name}")
                rows = list(reader)
            return _equal_lengths(
                {
                    role: np.array([r[name] for r in rows], dtype=object)
                    for role, name in fields.items()
                }
            )
        rows = []
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if line.strip():
                    # numbers keep their text (Decimal), so a lossy conversion is seen
                    rows.append(
                        json.loads(line, parse_constant=_refuse_constant, parse_float=Decimal)
                    )
        out = {}
        for role, name in fields.items():
            if any(not isinstance(r, dict) or name not in r for r in rows):
                raise RecomputeError(f"key {name!r} missing in {path.name}")
            out[role] = np.array([r[name] for r in rows], dtype=object)
        return _equal_lengths(out)
    except RecomputeError:
        raise
    except (OSError, ValueError, UnicodeDecodeError, csv.Error) as exc:
        raise RecomputeError(f"cannot read {path.name}: {type(exc).__name__}: {exc}") from None


def _refuse_constant(name: str) -> Any:
    raise ValueError(f"non-finite JSON constant {name}")


def _equal_lengths(arrays: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    lengths = {len(a) for a in arrays.values()}
    if len(lengths) != 1:
        raise RecomputeError("the prediction fields have different lengths")
    return arrays


def _encode(values: np.ndarray, labels: Sequence[Any]) -> np.ndarray:
    index = {_key(v): i for i, v in enumerate(labels)}
    out = np.empty(len(values), dtype=np.int64)
    for i, v in enumerate(values):
        if isinstance(v, bool | float | Decimal | np.floating | np.bool_):
            raise RecomputeError(f"label value {v!r} is not an integer or a string")
        k = _key(v.item() if isinstance(v, np.generic) else v)
        if k not in index:
            raise RecomputeError(f"label {k!r} is not among the declared labels")
        out[i] = index[k]
    return out


def _exact(value: Any, what: str) -> int | float | Decimal:
    """The exact number a file holds: a Python int, a float (a value already stored as
    a float is exact as such), or the Decimal of a text."""
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, bool):
        raise RecomputeError(f"{what} holds a boolean, not a number")
    if isinstance(value, int | float):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not _NUMBER.match(text):
            raise RecomputeError(f"{what} holds a value that is not a number")
        value = Decimal(text)
    if not isinstance(value, Decimal):
        raise RecomputeError(f"{what} holds a value that is not a number")
    return value


def _floats(
    arrays: Sequence[tuple[np.ndarray, str]],
) -> tuple[list[np.ndarray], list[list[Fraction]]]:
    """The arrays as 64-bit floats, and the exact values of the file (Codex review of
    PR #81, rounds 1 to 4).

    Over the values of all the arrays compared with each other: a non-zero value must
    not become zero, and the conversion must keep their strict order, so two distinct
    values never become one float and no tie is created (2**53 against 2**53 + 1,
    1e-400 against 2e-400, 0.1 against 0.10000000000000001). That is all a rank metric
    (AUROC) needs. A metric of distances also depends on how far each value moved and
    on the rounding of the arithmetic itself (the mean in r2), so for those the exact
    values go to ``exact_regression_metric``."""
    pairs: list[tuple[int | float | Decimal, float]] = []
    out = []
    exacts: list[list[Fraction]] = []
    for values, what in arrays:
        floats = np.empty(len(values), dtype=np.float64)
        column: list[Fraction] = []
        for i, v in enumerate(values):
            exact = _exact(v, what)
            try:
                f = float(exact)
            except OverflowError:
                raise RecomputeError(f"{what} holds a value beyond the float range") from None
            if not math.isfinite(f):
                raise RecomputeError(f"{what} holds a non-finite value")
            if f == 0 and exact != 0:
                raise RecomputeError(f"{what} holds {exact}, which underflows to zero")
            floats[i] = f
            column.append(Fraction(exact))
            pairs.append((exact, f))
        out.append(floats)
        exacts.append(column)
    pairs.sort(key=lambda p: p[0])
    for (e1, f1), (e2, f2) in zip(pairs, pairs[1:], strict=False):
        if e1 != e2 and not f1 < f2:
            raise RecomputeError(
                f"the distinct values {e1} and {e2} become the same float: the conversion "
                "would change the metric"
            )
    return out, exacts


def exact_regression_metric(
    metric: str, y_true: Sequence[Fraction], y_pred: Sequence[Fraction]
) -> float:
    """MAE, MSE, RMSE or r2 computed in exact rational arithmetic from the values the
    file holds (RMSE: the square root of the exact MSE, to 40 digits). Every regression
    run checks the float result against it: the conversion and the float arithmetic can
    both move a metric of distances."""
    n = len(y_true)
    errors = [p - t for t, p in zip(y_true, y_pred, strict=True)]
    if metric == "mae":
        return float(sum((abs(e) for e in errors), Fraction(0)) / n)
    squares = sum((e * e for e in errors), Fraction(0))
    if metric == "mse":
        return float(squares / n)
    if metric == "rmse":
        mse = squares / n
        with localcontext() as ctx:
            ctx.prec = 40
            return float((Decimal(mse.numerator) / Decimal(mse.denominator)).sqrt())
    mean = sum(y_true, Fraction(0)) / n
    total = sum(((t - mean) * (t - mean) for t in y_true), Fraction(0))
    if total == 0:
        raise UndefinedMetricError("r2 of a constant y_true")
    return float(1 - squares / total)


@dataclass(frozen=True)
class Prepared:
    """The arrays both implementations receive (same reader, same encoding)."""

    y_true: np.ndarray
    y_other: np.ndarray  # predicted class indices, scores, or predicted values
    n_labels: int = 0
    pos_index: int = -1
    # regression only: the exact values of the file (y_true, y_pred)
    exact: tuple[list[Fraction], list[Fraction]] | None = None


def prepare(conv: Convention, data: dict[str, np.ndarray]) -> Prepared:
    if conv.metric in REGRESSION:
        (y_true, y_pred), exacts = _floats([(data["y_true"], "y_true"), (data["y_pred"], "y_pred")])
        return Prepared(y_true, y_pred, exact=(exacts[0], exacts[1]))
    labels = list(conv.labels or ())
    y_true = _encode(data["y_true"], labels)
    pos = -1
    if conv.pos_label is not None:
        pos = [_key(v) for v in labels].index(_key(conv.pos_label))
    if conv.metric == "auroc":
        (y_score,), _ = _floats([(data["y_score"], "y_score")])  # AUROC needs only the order
        return Prepared(y_true, y_score, len(labels), pos)
    return Prepared(y_true, _encode(data["y_pred"], labels), len(labels), pos)


# ---- Refute's own implementation (numpy) ----------------------------------------------


def _div(num: float, den: float, zero_division: str | None) -> float:
    if den != 0:
        return num / den
    if zero_division == "undefined" or zero_division is None:
        raise UndefinedMetricError("zero denominator")
    return float(zero_division)


def own_metric(conv: Convention, p: Prepared) -> float:
    """The metric as a plain number (rates as fractions)."""
    n = len(p.y_true)
    if n == 0:
        raise RecomputeError("no examples")
    m = conv.metric
    if m in ("accuracy", "error_rate"):
        acc = float(np.mean(p.y_true == p.y_other))
        return acc if m == "accuracy" else 1.0 - acc
    if m in ("precision", "recall", "f1"):
        classes = [p.pos_index] if conv.average == "binary" else list(range(p.n_labels))
        tp = np.array([np.sum((p.y_true == c) & (p.y_other == c)) for c in classes], dtype=float)
        fp = np.array([np.sum((p.y_true != c) & (p.y_other == c)) for c in classes], dtype=float)
        fn = np.array([np.sum((p.y_true == c) & (p.y_other != c)) for c in classes], dtype=float)

        def per(t: float, f_p: float, f_n: float) -> float:
            if m == "precision":
                return _div(t, t + f_p, conv.zero_division)
            if m == "recall":
                return _div(t, t + f_n, conv.zero_division)
            return _div(2 * t, 2 * t + f_p + f_n, conv.zero_division)

        if conv.average == "micro":
            return per(tp.sum(), fp.sum(), fn.sum())
        values = [per(tp[i], fp[i], fn[i]) for i in range(len(classes))]
        if conv.average in ("binary", "macro"):
            return float(np.mean(values))
        support = tp + fn
        return _div(float(np.dot(support, values)), float(support.sum()), conv.zero_division)
    if m == "auroc":
        positive = p.y_true == p.pos_index
        n_pos, n_neg = int(positive.sum()), int((~positive).sum())
        if n_pos == 0 or n_neg == 0:
            raise UndefinedMetricError("auroc needs both classes")
        ranks = _average_ranks(p.y_other)
        u = float(ranks[positive].sum()) - n_pos * (n_pos + 1) / 2.0
        return u / (n_pos * n_neg)  # Mann-Whitney: ties count one half
    err = p.y_other - p.y_true
    if m == "mae":
        return float(np.mean(np.abs(err)))
    if m == "mse":
        return float(np.mean(err**2))
    if m == "rmse":
        return math.sqrt(float(np.mean(err**2)))
    _refuse_constant_target(p)
    ss_tot = float(np.sum((p.y_true - np.mean(p.y_true)) ** 2))
    return 1.0 - float(np.sum(err**2)) / ss_tot


def _refuse_constant_target(p: Prepared) -> None:
    """r2 is undefined for a constant ``y_true``. The values are compared directly: a
    variance computed from a rounded mean can be a tiny positive number for equal
    values (Codex review of PR #81)."""
    if np.all(p.y_true == p.y_true[0]):
        raise UndefinedMetricError("r2 of a constant y_true")


def _average_ranks(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    sorted_values = values[order]
    ranks = np.empty(len(values), dtype=float)
    i = 0
    while i < len(values):
        j = i
        while j + 1 < len(values) and sorted_values[j + 1] == sorted_values[i]:
            j += 1
        ranks[order[i : j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


# ---- scikit-learn, with every convention explicit -------------------------------------


def sklearn_metric(conv: Convention, p: Prepared) -> float:
    from sklearn import metrics as skm

    m = conv.metric
    if m in ("accuracy", "error_rate"):
        acc = float(skm.accuracy_score(p.y_true, p.y_other))
        return acc if m == "accuracy" else 1.0 - acc
    if m in ("precision", "recall", "f1"):
        _check_denominators(conv, p)  # Refute decides zero denominators before scikit-learn
        fn = {"precision": skm.precision_score, "recall": skm.recall_score, "f1": skm.f1_score}[m]
        kwargs: dict[str, Any] = {
            "labels": list(range(p.n_labels)),
            "average": conv.average,
            "zero_division": 0 if conv.zero_division == "undefined" else int(conv.zero_division),
        }
        if conv.average == "binary":
            kwargs["pos_label"] = p.pos_index
        return float(fn(p.y_true, p.y_other, **kwargs))
    if m == "auroc":
        y = (p.y_true == p.pos_index).astype(int)
        if y.min() == y.max():
            raise UndefinedMetricError("auroc needs both classes")
        return float(skm.roc_auc_score(y, p.y_other))
    if m == "mae":
        return float(skm.mean_absolute_error(p.y_true, p.y_other))
    if m == "mse":
        return float(skm.mean_squared_error(p.y_true, p.y_other))
    if m == "rmse":
        return float(skm.root_mean_squared_error(p.y_true, p.y_other))
    _refuse_constant_target(p)
    return float(skm.r2_score(p.y_true, p.y_other, force_finite=False))


def _check_denominators(conv: Convention, p: Prepared) -> None:
    """Raises UndefinedMetricError when ``zero_division`` is ``undefined`` and a denominator the
    metric uses is zero; the own implementation raises in the same cases."""
    if conv.zero_division != "undefined":
        return
    own_metric(conv, p)


# ---- the printed interval --------------------------------------------------------------


@dataclass(frozen=True)
class PrintedInterval:
    """True values that print as the token, in the token's unit."""

    value: Decimal
    lower: Decimal
    upper: Decimal


def printed_interval(token: str, rounding: str) -> PrintedInterval:
    """``q = 10^(e - d)`` from the token's text (d decimals, exponent e); nearest:
    ``[v - q/2, v + q/2]``; truncate: ``[v, v + q)``, or ``(v - q, v]`` when the text has a
    leading ``-`` (``-0.0`` included), or ``(-q, q)`` for a zero with no sign (``+0.0``
    has one: ``[0, q)``); unknown:
    ``[v - q, v + q]``. Open and closed ends are treated alike: the decision widens the
    interval by an epsilon anyway."""
    text = token.strip()
    if not _NUMBER.match(text):
        raise RecomputeError(f"the printed value {token!r} is not a decimal number")
    if rounding not in ROUNDINGS:
        raise RecomputeError(f"unsupported printed_rounding {rounding!r}")
    value = Decimal(text)
    q = Decimal(1).scaleb(value.as_tuple().exponent)
    if rounding == "nearest":
        return PrintedInterval(value, value - q / 2, value + q / 2)
    if rounding == "unknown":
        return PrintedInterval(value, value - q, value + q)
    if text.startswith("-"):
        return PrintedInterval(value, value - q, value)
    if value == 0 and not text.startswith("+"):
        return PrintedInterval(value, -q, q)  # an unsigned zero: either sign was truncated
    return PrintedInterval(value, value, value + q)


def unit_factor(from_unit: str, to_unit: str) -> Decimal:
    if from_unit not in UNITS or to_unit not in UNITS:
        raise RecomputeError(f"unknown unit {from_unit!r} or {to_unit!r}")
    if from_unit == to_unit:
        return Decimal(1)
    if "native" in (from_unit, to_unit):
        raise RecomputeError("a native unit cannot be converted")
    return Decimal(100) if (from_unit, to_unit) == ("fraction", "percent") else Decimal("0.01")


# ---- one run ---------------------------------------------------------------------------


@dataclass
class RunOutcome:
    label: str
    status: TestStatus
    reason: str
    recomputed_in_full: bool = False
    details: dict[str, Any] = field(default_factory=dict)


def decide(a: float, b: float, interval: PrintedInterval, rounding: str) -> tuple[TestStatus, str]:
    """The decision table of section 1.7 (values in the claim's unit)."""
    eps = 1e-9 * max(1.0, abs(a))
    if abs(a - b) > eps:
        return TestStatus.INCONCLUSIVE, "the two implementations disagree"
    lo, hi = float(interval.lower) - eps, float(interval.upper) + eps
    inside = [lo <= x <= hi for x in (a, b)]
    if all(inside):
        return TestStatus.PASS, "both implementations give a value inside the printed interval"
    below = all(x < lo for x in (a, b))
    above = all(x > hi for x in (a, b))
    if below or above:
        if rounding == "unknown":
            return (
                TestStatus.INCONCLUSIVE,
                "outside the interval, but the printed rounding is unknown",
            )
        return TestStatus.FAIL, "both implementations give a value outside the printed interval"
    return TestStatus.INCONCLUSIVE, "boundary case: one value inside, one outside"


def recompute_run(
    label: str,
    conv: Convention,
    printed_token: str,
    channel_unit: str,
    metric_unit: str,
    rounding: str,
    data: dict[str, np.ndarray],
    n_examples: int,
    second: Callable[[Convention, Prepared], float] = sklearn_metric,
) -> RunOutcome:
    """Recompute one run and compare it with what that run printed."""
    details: dict[str, Any] = {"printed": printed_token}
    try:
        conv.validate()
        if metric_unit != conv.scale:
            raise RecomputeError("the convention's scale differs from the metric's unit")
        lengths = {len(v) for v in data.values()}
        if lengths != {n_examples}:
            raise RecomputeError(f"{sorted(lengths)} examples, expected {n_examples}")
        prepared = prepare(conv, data)
        interval = printed_interval(printed_token, rounding)
        factor = unit_factor(channel_unit, metric_unit)
        interval = PrintedInterval(
            interval.value * factor, interval.lower * factor, interval.upper * factor
        )
        to_claim = 100.0 if metric_unit == "percent" else 1.0
        own_raw = own_metric(conv, prepared)
        if prepared.exact is not None:
            # the float result must be the exact metric of the values in the file: the
            # conversion and the float arithmetic can both move it (Codex review of PR #81,
            # rounds 3 and 4)
            exact = exact_regression_metric(conv.metric, *prepared.exact)
            if abs(own_raw - exact) > 1e-9 * max(1.0, abs(exact)):
                raise RecomputeError(
                    f"floating-point rounding moves {conv.metric} from its exact value "
                    f"{exact!r} to {own_raw!r}"
                )
            details["exact"] = exact
        own = own_raw * to_claim
        other = second(conv, prepared) * to_claim
    except RecomputeError as exc:
        return RunOutcome(label, TestStatus.INCONCLUSIVE, str(exc), False, details)
    except Exception as exc:  # noqa: BLE001 - any failure of an implementation is Refute-side
        reason = f"an implementation failed: {type(exc).__name__}: {exc}"
        return RunOutcome(label, TestStatus.INCONCLUSIVE, reason, False, details)
    if not (math.isfinite(own) and math.isfinite(other)):
        return RunOutcome(label, TestStatus.INCONCLUSIVE, "a non-finite value", False, details)
    details.update(
        own=own,
        sklearn=other,
        interval=[str(interval.lower), str(interval.upper)],
        unit=metric_unit,
    )
    status, reason = decide(own, other, interval, rounding)
    return RunOutcome(label, status, reason, True, details)


# ---- the check over every base run ------------------------------------------------------


def metric_recompute_result(
    outcomes: Sequence[RunOutcome], expected_labels: Sequence[str]
) -> TestResult:
    """The ``metric_recompute`` check of one claim over its base runs, named by
    ``expected_labels`` (for example ``seed=1``, or ``method:seed=1`` for a comparison).

    Each outcome must name a distinct expected run, and a decided outcome (PASS or
    FAIL) must have been recomputed in full; anything else is an input error
    (``ValueError``), so a repeated or foreign outcome can neither fill a PASS nor
    establish a failure. One valid failure establishes the failure; every expected run
    must pass for a PASS; anything else is INCONCLUSIVE. Coverage: runs recomputed in
    full."""
    expected = list(expected_labels)
    if not expected or len(set(expected)) != len(expected):
        raise ValueError("expected_labels must be a non-empty list of distinct run labels")
    labels = [o.label for o in outcomes]
    if len(set(labels)) != len(labels):
        raise ValueError("two outcomes name the same run")
    foreign = sorted(set(labels) - set(expected))
    if foreign:
        raise ValueError("outcomes for runs that are not expected: " + ", ".join(foreign))
    for o in outcomes:
        if o.status in (TestStatus.PASS, TestStatus.FAIL) and not o.recomputed_in_full:
            raise ValueError(f"run {o.label} is {o.status} but was not recomputed in full")
    failed = [o for o in outcomes if o.status is TestStatus.FAIL]
    passed = {o.label for o in outcomes if o.status is TestStatus.PASS}
    coverage = sum(1 for o in outcomes if o.recomputed_in_full)
    if failed:
        status, message = (
            TestStatus.FAIL,
            f"{len(failed)} run(s) printed a value their predictions do not give",
        )
    elif passed == set(expected):
        status, message = TestStatus.PASS, "every run printed the value its predictions give"
    else:
        status, message = TestStatus.INCONCLUSIVE, "not every run could be decided"
    return TestResult(
        name=METRIC_RECOMPUTE,
        status=status,
        severity=Severity.FATAL,
        message=message,
        metrics={
            EXPECTED_COVERAGE: len(expected),
            FAILURE_ESTABLISHED: bool(failed),
            "runs": [
                {"label": o.label, "status": str(o.status), "reason": o.reason, **o.details}
                for o in outcomes
            ],
        },
        coverage=coverage,
        coverage_unit="runs recomputed in full",
    )
