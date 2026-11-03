"""The values of the v0.5 calibration protocol (calibration/v0.5/PROTOCOL.md), approved by the
maintainer at S2 on 2026-11-03 (docs/plans/v0.5-plan.md, section 9a). They are code, so the
lock's code hash covers them; the protocol states the same values in its section 11, and a test
checks that the two agree."""

from __future__ import annotations

from dataclasses import dataclass, field

PROTOCOL_ID = "refute-tess-v0.5-calibration"
STEP_DIR = "calibration/v0.5"


@dataclass(frozen=True)
class C3Values:
    """Section 5: 8 confirmed planets and 8 eclipsing-binary false positives, newly drawn."""

    planets: int = 8
    false_positives: int = 8
    reserves: int = 3  # per pool, in order, at most 3 replacements in total per pool
    period_min_days: float = 0.5
    period_max_days: float = 13.0
    planet_min_depth_percent: float = 0.1
    fp_min_depth_ppm: float = 1000.0
    identity_period_tolerance: float = 0.001
    fp_identity_factors: tuple[float, ...] = (1.0, 2.0, 0.5)
    max_planets_refuted: int = 1  # T3a
    max_fp_survived: int = 2  # T3b
    retry_attempts: int = 5
    retry_backoff_seconds: float = 120.0


@dataclass(frozen=True)
class C1Values:
    """Section 3 (the acceptance document, C1): sizes and the cost rule."""

    sizes: dict[str, int] = field(
        default_factory=lambda: {
            "P": 200,
            "PG": 200,
            "PV": 200,
            "PA": 100,
            "EB1": 200,
            "EB2": 200,
            "V1": 200,
            "V2": 200,
            "SE": 200,
            "ER": 200,
            "NW": 200,
            "NR": 200,
            "PX": 100,
        }
    )
    development_prefix: int = 20
    max_processor_hours: float = 30.0
    not_decidable_below: int = 20
    seed_prefix: str = "refute-v05-c1"


@dataclass(frozen=True)
class C2Values:
    """Section 4: the reused v0.4 benchmark."""

    stars: int = 100
    injections_per_curve: int = 20
    injections_fallback: int = 10
    transformed_per_star: int = 3
    float_rel_tolerance: float = 1e-9
    not_decidable_below: int = 20
    t2a_margin: float = 0.10


@dataclass(frozen=True)
class BudgetValues:
    """Section 8: inside the plan's caps."""

    reserve_processor_hours: float = 100.0
    reserve_agent_days: float = 5.0
    reserve_reviewer_tokens: int = 1_500_000
    disk_bytes: int = 15 * 1000**3


C3 = C3Values()
C1 = C1Values()
C2 = C2Values()
BUDGET = BudgetValues()

# The roles of the v0.5 battery (the acceptance README and the S2 decisions): every v0.4 decisive
# test except centroid_shift (in a v0.5 plan it is the per-sector centroid, not accepted), plus the
# accepted v0.5 tests; diagnostic: the tests whose acceptance failed, and the holdout.
V05_DECISIVE = (
    "snr",
    "odd_even",
    "secondary_eclipse",
    "plausibility",
    "aperture_depth",
    "nearby_contamination",
    "period_alias",
    "systematics",
    "eb_catalog",
    "edge_events",
    "sinusoid",
    "duty_cycle",
)
V05_DIAGNOSTIC = ("holdout_by_year", "single_event", "event_consistency", "centroid_shift")
