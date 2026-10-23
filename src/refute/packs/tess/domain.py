"""The operational domain of the profile ``three-observing-years/1``.

Amendment B of docs/validation/v0.2.1/population-study.md and its acceptance record
(docs/validation/v0.2.1/population/population-v4-acceptance.md, section 2.1). The input is, per
sector, the array of its kept cadence time stamps (BTJD days), before any filter that reads a
flux value: the generated time stamps in the synthetic harness, the cadences kept by the plan's
quality mask for a real product. Nothing here reads a flux.

The conditions, in order (the result names the first that fails):

- D1: every sector labelled (the year of its first kept time stamp), exactly three labels;
- D2: exactly three sectors;
- D3: the two-minute cadence: every interval of at most 600 s is ``k x 120 s`` within 0.5 s,
  ``k`` from 1 to 4, and every time stamp finite;
- D4: per sector, the orbit gap (the longest interval above 600 s) 0.5 to 2.0 d, both orbits
  12.5 to 14.0 d, at most four other internal gaps of at most 6 h, coverage at least 0.84;
- D5: the two separations between consecutive sectors' first time stamps, each about one year
  (345 to 385 d) or about two years (710 to 750 d), at most one about two years.

Every condition is computed on every input; a quantity that cannot be computed is ``None`` and
fails its condition. Nothing in the engine imports this module before the profile O2.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np

from refute.packs.tess.types import btjd_to_year

PROFILE = "three-observing-years/1"
CONDITIONS = ("D1", "D2", "D3", "D4", "D5")

CADENCE_S = 120.0
TIMING_TOLERANCE_S = 0.5
MAX_STEP = 4
INTERNAL_GAP_S = 600.0
ORBIT_DAYS = (12.5, 14.0)
ORBIT_GAP_DAYS = (0.5, 2.0)
MAX_OTHER_GAPS = 4
MAX_OTHER_GAP_S = 21600.0
MIN_COVERAGE = 0.84
ONE_YEAR_DAYS = (345.0, 385.0)
TWO_YEARS_DAYS = (710.0, 750.0)
DAY_S = 86400.0


@dataclass(frozen=True)
class SectorTiming:
    """The measured timing of one sector (``None``: not computable)."""

    label: int | None
    n_kept: int
    first: float | None
    last: float | None
    span_days: float | None
    coverage: float | None
    orbit_days: tuple[float, float] | None
    orbit_gap_days: float | None
    other_gaps_seconds: tuple[float, ...]
    k_counts: dict[int, int]
    residual_min_s: float | None
    residual_max_s: float | None
    d3_problem: str | None
    d4_problem: str | None

    def summary(self) -> dict:
        return {
            "label": self.label,
            "n_kept": self.n_kept,
            "first": self.first,
            "last": self.last,
            "span_days": self.span_days,
            "coverage": self.coverage,
            "orbit_days": list(self.orbit_days) if self.orbit_days is not None else None,
            "orbit_gap_days": self.orbit_gap_days,
            "other_gaps_seconds": list(self.other_gaps_seconds),
            "k_counts": {str(k): v for k, v in self.k_counts.items()},
            "residual_min_s": self.residual_min_s,
            "residual_max_s": self.residual_max_s,
            "d3_problem": self.d3_problem,
            "d4_problem": self.d4_problem,
        }


@dataclass(frozen=True)
class DomainResult:
    inside: bool
    failed: str | None
    reason: str | None
    conditions: dict[str, bool]
    sectors: tuple[SectorTiming, ...]
    separations_days: tuple[float, ...]

    def summary(self) -> dict:
        """Plain JSON values."""
        return {
            "profile": PROFILE,
            "inside": self.inside,
            "failed": self.failed,
            "reason": self.reason,
            "conditions": dict(self.conditions),
            "separations_days": list(self.separations_days),
            "sectors": [s.summary() for s in self.sectors],
        }


def _within(value: float, bounds: tuple[float, float]) -> bool:
    return bounds[0] <= value <= bounds[1]


def sector_timing(times) -> SectorTiming:
    """The timing of one sector's kept time stamps, read in the order given."""
    t = np.asarray(times, dtype=float)
    n = int(t.size)
    zero = {k: 0 for k in range(1, MAX_STEP + 1)}
    first = float(t[0]) if n else None
    last = float(t[-1]) if n else None
    label = btjd_to_year(first) if first is not None and np.isfinite(first) else None
    if not np.all(np.isfinite(t)):
        return SectorTiming(
            label, n, first, last, None, None, None, None, (), zero, None, None,
            "a time stamp is not finite", "not computable: a time stamp is not finite",
        )  # fmt: skip
    dt = np.diff(t) * DAY_S
    span_s = (t[-1] - t[0]) * DAY_S + CADENCE_S
    coverage = n * CADENCE_S / span_s

    gap = dt > INTERNAL_GAP_S
    steps = dt[~gap]
    k = np.rint(steps / CADENCE_S)
    residual = steps - k * CADENCE_S
    bad = (k < 1) | (k > MAX_STEP) | (np.abs(residual) > TIMING_TOLERANCE_S)
    d3 = None
    if bad.any():
        i = int(np.flatnonzero(~gap)[np.flatnonzero(bad)[0]])
        d3 = f"interval {i} of {dt[i]:.3f} s is not 1 to 4 cadences of 120 s within 0.5 s"
    k_counts = {j: int(np.count_nonzero(k == j)) for j in range(1, MAX_STEP + 1)}
    good = residual[~bad]
    r_min = float(good.min()) if good.size else None
    r_max = float(good.max()) if good.size else None

    gaps = np.flatnonzero(gap)
    if gaps.size == 0:
        return SectorTiming(
            label, n, first, last, span_s / DAY_S, float(coverage), None, None, (), k_counts,
            r_min, r_max, d3, "no internal gap: no orbit gap",
        )  # fmt: skip
    og = int(gaps[np.argmax(dt[gaps])])
    orbits = (
        float((t[og] - t[0]) * DAY_S + CADENCE_S) / DAY_S,
        float((t[-1] - t[og + 1]) * DAY_S + CADENCE_S) / DAY_S,
    )
    orbit_gap = float(dt[og]) / DAY_S
    others = tuple(float(dt[i]) for i in gaps if i != og)

    d4 = None
    if not _within(orbit_gap, ORBIT_GAP_DAYS):
        d4 = f"orbit gap of {orbit_gap:.4f} d outside 0.5 to 2.0 d"
    elif not all(_within(x, ORBIT_DAYS) for x in orbits):
        d4 = f"orbits of {orbits[0]:.4f} and {orbits[1]:.4f} d, each must be 12.5 to 14.0 d"
    elif len(others) > MAX_OTHER_GAPS:
        d4 = f"{len(others)} other internal gaps, at most 4"
    elif any(x > MAX_OTHER_GAP_S for x in others):
        d4 = f"another internal gap of {max(others):.1f} s, longer than 6 h"
    elif coverage < MIN_COVERAGE:
        d4 = f"coverage {coverage:.4f} below 0.84"
    return SectorTiming(
        label, n, first, last, span_s / DAY_S, float(coverage), orbits, orbit_gap, others,
        k_counts, r_min, r_max, d3, d4,
    )  # fmt: skip


def check_domain(sectors: Sequence) -> DomainResult:
    """D1 to D5 on the kept time stamps of each sector (a sector without one is left out)."""
    timings = tuple(sector_timing(t) for t in sectors if np.asarray(t).size > 0)
    labels = [s.label for s in timings]
    problems: dict[str, str | None] = {}

    if any(x is None for x in labels):
        problems["D1"] = "a sector has no label (its first time stamp is not finite)"
    elif len(set(labels)) != 3:
        problems["D1"] = f"{len(set(labels))} observing years {sorted(set(labels))}, three required"
    else:
        problems["D1"] = None
    problems["D2"] = None if len(timings) == 3 else f"{len(timings)} sectors, three required"
    d3 = [(i, s.d3_problem) for i, s in enumerate(timings) if s.d3_problem]
    problems["D3"] = f"sector {d3[0][0]}: {d3[0][1]}" if d3 else None
    d4 = [(i, s.d4_problem) for i, s in enumerate(timings) if s.d4_problem]
    problems["D4"] = f"sector {d4[0][0]}: {d4[0][1]}" if d4 else None

    separations: tuple[float, ...] = ()
    if any(x is None for x in labels) or any(not np.isfinite(s.first) for s in timings):
        problems["D5"] = "a sector has no finite first time stamp"
    else:
        firsts = sorted(s.first for s in timings)
        separations = tuple(float(b - a) for a, b in zip(firsts[:-1], firsts[1:], strict=True))
        long_ = [_within(x, TWO_YEARS_DAYS) for x in separations]
        short = [_within(x, ONE_YEAR_DAYS) for x in separations]
        if len(separations) != 2:
            problems["D5"] = f"{len(separations)} separations, two required"
        elif not all(a or b for a, b in zip(long_, short, strict=True)):
            problems["D5"] = (
                f"separations {separations[0]:.3f} and {separations[1]:.3f} d, each must be "
                "about one year (345 to 385 d) or about two years (710 to 750 d)"
            )
        elif sum(long_) > 1:
            problems["D5"] = "both separations about two years, at most one allowed"
        else:
            problems["D5"] = None

    conditions = {c: problems[c] is None for c in CONDITIONS}
    failed = next((c for c in CONDITIONS if problems[c] is not None), None)
    return DomainResult(
        inside=failed is None,
        failed=failed,
        reason=f"{failed}: {problems[failed]}" if failed else None,
        conditions=conditions,
        sectors=timings,
        separations_days=separations,
    )
