"""The values of the v0.4 pilot protocol, approved by the maintainer at P1 on 2026-10-29
(calibration/v0.4/PROTOCOL.md). They are code, so the lock's code hash covers them; the
protocol text states the same values, and a test checks that the two agree."""

from __future__ import annotations

from dataclasses import dataclass

PROTOCOL_ID = "refute-tess-discover-v0.4"


@dataclass(frozen=True)
class Domain:
    """Section 3 of the protocol: a star is in the domain when every rule holds."""

    min_sectors: int = 3  # D-1: sectors with SPOC 120-s light curves
    min_years: int = 2  # D-2: calendar years of those sectors' starts
    min_span_days: float = 300.0  # D-2: first to last sector start
    pixel_files_every_sector: bool = True  # D-3: a target pixel file listed for each sector
    min_logg: float = 4.0  # D-4
    max_radius_rel_err: float = 0.25  # D-5
    teff_min_k: float = 3200.0  # D-6
    teff_max_k: float = 7000.0  # D-6
    tmag_min: float = 8.0  # D-7
    tmag_max: float = 12.0  # D-7
    max_contamination: float = 0.10  # D-8


@dataclass(frozen=True)
class Selection:
    """Sections 4.2 and 4.3: how many stars are accepted and how queries are retried."""

    funnel_accepted: int = 100  # N = 50 run, the next 50 the reserve of the N rule
    controls_per_pool: int = 1
    retry_attempts: int = 5
    retry_backoff_seconds: float = 120.0
    # Frame and deduplication radius around a star, in arcsec (one TESS pixel; the
    # eb_catalog match_radius_arcsec of the v0.2 parameters).
    match_radius_arcsec: float = 21.0


@dataclass(frozen=True)
class ControlPools:
    """Section 4.3: the planet and false-positive pools."""

    period_min_days: float = 0.5
    period_max_days: float = 13.0
    planet_min_depth_percent: float = 0.1
    fp_min_depth_ppm: float = 1000.0
    # The ladder for an empty pool, each step at most once, in this order.
    ladder_tmag_max: float = 13.0
    ladder_planet_min_depth_percent: float = 0.05
    ladder_fp_min_depth_ppm: float = 500.0
    identity_period_tolerance: float = 0.001
    fp_identity_factors: tuple[float, ...] = (1.0, 2.0, 0.5)


@dataclass(frozen=True)
class Dedup:
    """Section 6: period equal within the tolerance, or at one of the alias factors."""

    period_tolerance: float = 0.01
    factors: tuple[float, ...] = (1.0, 2.0, 0.5, 3.0, 1.0 / 3.0)
    catalogs: tuple[str, ...] = ("TOI", "CTOI", "pscomppars", "TESS-EB", "Gaia-DR3-EB")


@dataclass(frozen=True)
class Promotion:
    """Section 7: at most this many funnel stars reach stage 2."""

    cap: int = 3


@dataclass(frozen=True)
class Injection:
    """Section 9 (the depth floor of 100 ppm set at P1)."""

    period_min_days: float = 0.5
    period_max_days: float = 13.0
    depth_min_ppm: float = 100.0
    depth_max_ppm: float = 10000.0
    impact_max: float = 0.8
    period_tolerance: float = 0.01
    epoch_tolerance_durations: float = 0.5
    alias_factors: tuple[float, ...] = (2.0, 0.5, 3.0, 1.0 / 3.0)
    measurement_prefix: int = 5


@dataclass(frozen=True)
class Transforms:
    """Section 10: one inverted curve and two per-sector cyclic rotations."""

    rotations: int = 2
    offset_min_fraction: float = 0.1
    offset_max_fraction: float = 0.9
    min_sector_cadences: int = 100
    max_redraws: int = 100


@dataclass(frozen=True)
class Budget:
    """Sections 4.4 and 11: the caps and the (N, K) sequence."""

    max_logical_processor_hours: float = 100.0
    max_cache_bytes: int = 10 * 1000**3
    margin: float = 1.5
    share_of_remaining: float = 0.5
    sequence: tuple[tuple[int, int], ...] = ((100, 20), (50, 20), (50, 10), (50, 5))


DOMAIN = Domain()
SELECTION = Selection()
CONTROLS = ControlPools()
DEDUP = Dedup()
PROMOTION = Promotion()
INJECTION = Injection()
TRANSFORMS = Transforms()
BUDGET = Budget()

SURVIVED_MEANING = (
    "the signal survived the declared decisive battery; temporal confirmation was not "
    "required; the method is not validated"
)
