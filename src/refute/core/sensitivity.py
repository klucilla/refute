"""The sensitivity rule (v0.5, issue #185): no PASS without the power to fail.

The coverage rule (``refute.core.verdict.enforce_coverage``) refuses a PASS from a check that
examined no data. This rule refuses a PASS from a check that examined too little data to
decide: a fatal or warning test PASSes only when it could have detected its declared
alternative. Otherwise the PASS becomes INCONCLUSIVE, with the reason. A FAIL is never changed:
a detected failure stands. The gate is exempt (it is a positive detection test). The
aggregation rules of ``docs/verdicts.md`` do not change.

Every test of a claim that uses this rule declares, in a registry kept by its domain pack, its
sub-checks and, for each, whether it is a statistical **rule** or an applicability
**category** (a check that is not a statistical test). A result carries one block per
sub-check in ``TestResult.sensitivity``:

- a rule block: ``effect``, ``alternative``, ``unit``, ``rule_id``, ``probability`` (of
  rejecting under the alternative), ``required_probability`` and ``detectable``
  (``probability >= required_probability``);
- a category block: ``category`` and ``reason``.

A statistical test cannot PASS by declaring a category: the registry fixes which applies. A
PASS still needs positive coverage. The acceptance cases are in
``docs/plans/v0.5-acceptance.md`` (WP1).
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from typing import Any

import numpy as np

from refute.core.verdict import Severity, TestResult, TestStatus

RULE = "rule"
CATEGORIES = frozenset({"deterministic-bound", "catalog-lookup", "fraction"})
RULE_KEYS = (
    "effect",
    "alternative",
    "unit",
    "rule_id",
    "probability",
    "required_probability",
    "detectable",
)
CATEGORY_KEYS = ("category", "reason")
REQUIRED_PROBABILITY = 0.95
Z_POWER = 1.645
DRAWS = 2000

# test name -> sub-check name -> RULE or a category
Registry = Mapping[str, Mapping[str, str]]


def _finite(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def _text(value: Any) -> bool:
    return isinstance(value, str) and value.strip() != ""


def block_problem(block: Any, expected: str) -> str | None:
    """Why ``block`` is not a valid block of the kind ``expected`` (None when it is).

    The required probability is the engine's (:data:`REQUIRED_PROBABILITY`): a result cannot
    lower it. Descriptive fields must be non-empty strings."""
    if not isinstance(block, Mapping):
        return "not a mapping"
    if expected == RULE:
        missing = [key for key in RULE_KEYS if key not in block]
        if missing:
            return "missing " + ", ".join(missing)
        for key in ("effect", "unit", "rule_id"):
            if not _text(block[key]):
                return f"{key} is not a non-empty string"
        if not isinstance(block["detectable"], bool):
            return "detectable is not a boolean"
        for key in ("alternative", "probability", "required_probability"):
            if not _finite(block[key]):
                return f"{key} is not a finite number"
        if block["required_probability"] != REQUIRED_PROBABILITY:
            return f"required_probability is not the engine's {REQUIRED_PROBABILITY}"
        if not 0.0 <= block["probability"] <= 1.0:
            return "probability outside [0, 1]"
        if block["detectable"] != (block["probability"] >= REQUIRED_PROBABILITY):
            return "detectable disagrees with the probabilities"
        return None
    if expected not in CATEGORIES:
        return f"unknown category {expected!r} in the registry"
    if "category" not in block or "reason" not in block:
        return "missing category or reason"
    if block["category"] != expected:
        return f"category {block['category']!r}, registered {expected!r}"
    if not _text(block["reason"]):
        return "reason is not a non-empty string"
    return None


def _refusal(result: TestResult, registry: Registry) -> str | None:
    """Why a PASS of ``result`` is refused by the rule (None when it stands)."""
    entries = registry.get(result.name)
    if not isinstance(entries, Mapping) or not entries:
        return "no sensitivity rule or category registered"
    blocks = result.sensitivity
    if blocks is None:
        blocks = {}
    if not isinstance(blocks, Mapping):
        return "invalid sensitivity: not a mapping of sub-checks"
    for sub, expected in entries.items():
        block = blocks.get(sub)
        if block is None:
            return "no sensitivity declared" + ("" if sub == "main" else f" for {sub}")
        problem = block_problem(block, expected)
        if problem:
            return f"invalid sensitivity block for {sub}: {problem}"
        if expected == RULE and not block["detectable"]:
            return (
                f"insufficient sensitivity: {block['effect']} {block['alternative']:g} "
                f"{block['unit']} not detectable ({block['probability']:.3f} < "
                f"{block['required_probability']:.2f})"
            )
    return None


def enforce_sensitivity(results: Sequence[TestResult], registry: Registry) -> list[TestResult]:
    """Turn every fatal or warning PASS without the declared sensitivity into INCONCLUSIVE."""
    out = []
    for result in results:
        if result.status is TestStatus.PASS and result.severity is not Severity.GATE:
            why = _refusal(result, registry)
            if why is not None:
                result = replace(
                    result,
                    status=TestStatus.INCONCLUSIVE,
                    message=f"PASS refused: {why} ({result.message})",
                )
        out.append(result)
    return out


def registry_problems(tests: Sequence[str], registry: Registry, exempt: Sequence[str]) -> list[str]:
    """The problems of a claim's decisive tests against the registry (refused at load time)."""
    problems = []
    for name in tests:
        if name in exempt:
            continue
        entries = registry.get(name)
        if not isinstance(entries, Mapping) or not entries:
            problems.append(f"{name}: no sensitivity rule or category registered")
            continue
        for sub, kind in entries.items():
            if kind != RULE and kind not in CATEGORIES:
                problems.append(f"{name}.{sub}: unknown kind {kind!r}")
    return problems


def seed_for(*parts: object) -> int:
    """A deterministic seed from the parts (test name, candidate values...)."""
    text = "|".join(repr(p) for p in parts)
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:16], 16)


def rule_block(
    effect: str, alternative: float, unit: str, rule_id: str, probability: float
) -> dict[str, Any]:
    return {
        "effect": effect,
        "alternative": float(alternative),
        "unit": unit,
        "rule_id": rule_id,
        "probability": float(probability),
        "required_probability": REQUIRED_PROBABILITY,
        "detectable": bool(probability >= REQUIRED_PROBABILITY),
    }


def category_block(category: str, reason: str) -> dict[str, Any]:
    if category not in CATEGORIES:
        raise ValueError(f"unknown category {category!r}")
    return {"category": category, "reason": reason}


def gaussian_probability(alternative: float, sigma: float, threshold: float) -> float:
    """P(alternative + sigma Z >= threshold sigma), Z standard normal: the probability that a
    one-sided Gaussian statistic reaches its threshold (in sigmas) under the alternative.

    ``probability >= 0.95`` is, to the rounding of 1.645, the closed form
    ``alternative / sigma >= threshold + 1.645``. Any non-finite input, or a sigma that is not
    positive, gives 0 (not detectable): a rule never becomes detectable by a bad input.
    """
    values = (alternative, sigma, threshold)
    if not all(_finite(v) for v in values) or not sigma > 0:
        return 0.0
    z = alternative / sigma - threshold
    return 0.5 * math.erfc(-z / math.sqrt(2.0))


def simulated_probability(
    draw: Callable[[np.random.Generator, int], Any],
    reject: Callable[[Any], np.ndarray],
    seed: int,
    draws: int = DRAWS,
) -> float:
    """The fraction of ``draws`` simulated statistics, under the alternative, that the test's
    full rejection rule rejects. ``draw(rng, n)`` returns the statistics for ``n`` draws and
    ``reject`` must return a NumPy boolean array of shape ``(n,)``; anything else (NaN, numbers,
    another shape) is refused, never cast to a detection. Deterministic for a given seed."""
    if isinstance(draws, bool) or not isinstance(draws, int) or draws < 1:
        raise ValueError("draws must be a positive integer")
    rng = np.random.default_rng(seed)
    rejected = reject(draw(rng, draws))
    if not isinstance(rejected, np.ndarray) or rejected.dtype != np.bool_:
        raise ValueError("reject() must return a NumPy boolean array")
    if rejected.shape != (draws,):
        raise ValueError("reject() must return one boolean per draw")
    return float(rejected.mean())
