"""Fixed rules of the ML pack that the claim schema writes out (WP3 design).

- Holdout (1.0.10): ``m = floor(0.1 · n_train)`` training examples are carved out; with
  ``m < 100`` the attack is not applicable; the claim's tolerance is widened by
  ``factor = max(1, sqrt(n_examples / m))``. An operational convention, fixed before the
  lock and never adjusted because of results.
- Random baseline (1.0.6): on a single-label classification task with ``K`` declared
  classes, a uniform guess has accuracy ``1/K`` and error rate ``1 − 1/K``, whatever the
  class frequencies. Known limitation (maintainer, 2026-10-15): on imbalanced data it is
  more lenient than the majority class; deliberate, so the attack never fails falsely.
"""

from __future__ import annotations

import math

HOLDOUT_FRACTION = 0.1
HOLDOUT_MIN_EXAMPLES = 100
HOLDOUT_METRICS = ("accuracy", "error_rate", "mae", "mse")
BASELINE_METRICS = ("accuracy", "error_rate")


def holdout_size(n_train: int) -> int:
    """``m = floor(0.1 · n_train)``, in integer arithmetic."""
    if n_train < 0:
        raise ValueError("n_train cannot be negative")
    return n_train // 10


def holdout_factor(n_examples: int, m: int) -> float:
    """``max(1, sqrt(n_examples / m))``; ``m`` must be at least the minimum."""
    if m < HOLDOUT_MIN_EXAMPLES:
        raise ValueError(f"a holdout of {m} examples is below {HOLDOUT_MIN_EXAMPLES}")
    if n_examples < 1:
        raise ValueError("n_examples must be at least 1")
    return max(1.0, math.sqrt(n_examples / m))


def random_baseline(metric: str, n_classes: int) -> float:
    """The expected value of a uniform random guess (no random draw)."""
    if metric not in BASELINE_METRICS:
        raise ValueError(f"the random baseline is defined only for {BASELINE_METRICS}")
    if n_classes < 2:
        raise ValueError("a classification task has at least 2 classes")
    accuracy = 1.0 / n_classes
    return accuracy if metric == "accuracy" else 1.0 - accuracy
