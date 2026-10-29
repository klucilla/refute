"""Deduplication of a stage-1 signal against the frozen catalogs (protocol section 6; #27).

Every signal that passes the gate is compared with each catalog on its own: the same TIC, or a
catalogued object within the match radius, and a period equal within the tolerance at one of
the alias factors (the alias is named). Each catalog has its own state and coverage: ``match``,
``no_match`` (rows scanned > 0 and every comparison decidable) or ``INCONCLUSIVE`` (no snapshot,
nothing scanned, the star without a position, or a nearby entry without a period, so a match
cannot be excluded). One catalog never stands in for another: the overall result is ``no_match``
only when every catalog is ``no_match``.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from refute.packs.tess.discover.protocol import DEDUP, SELECTION

MATCH = "match"
NO_MATCH = "no_match"
INCONCLUSIVE = "INCONCLUSIVE"


@dataclass(frozen=True)
class CatalogEntry:
    """One catalogued object: an identifier, its TIC (None when the catalog has none), its
    position (degrees, None when unknown) and its period in days (None when unknown)."""

    identifier: str
    tic_id: int | None
    ra_deg: float | None
    dec_deg: float | None
    period_days: float | None


@dataclass
class CatalogResult:
    catalog: str
    state: str
    coverage: int
    matches: list[dict[str, Any]] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "catalog": self.catalog,
            "state": self.state,
            "coverage": self.coverage,
            "coverage_unit": "catalog rows scanned",
            "matches": self.matches,
            "reason": self.reason,
        }


def separation_arcsec(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    """Great-circle separation (haversine), in arcsec."""
    r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    h = math.sin((d2 - d1) / 2) ** 2 + math.cos(d1) * math.cos(d2) * math.sin((r2 - r1) / 2) ** 2
    return math.degrees(2 * math.asin(min(1.0, math.sqrt(h)))) * 3600.0


def alias_factor(
    found: float, catalogued: float, factors: Sequence[float], tolerance: float
) -> float | None:
    """The first factor ``f`` with ``|found - f * catalogued| / (f * catalogued) <= tolerance``."""
    if not (catalogued and catalogued > 0 and found and found > 0):
        return None
    for factor in factors:
        if abs(found - factor * catalogued) / (factor * catalogued) <= tolerance:
            return factor
    return None


class CatalogIndex:
    """A catalog snapshot indexed by TIC and by position, so that the entries near a star are
    found without a linear scan; every row of the snapshot counts as scanned."""

    def __init__(self, entries: Sequence[CatalogEntry]):
        import numpy as np
        from scipy.spatial import cKDTree

        self.entries = list(entries)
        self.size = len(self.entries)
        self.by_tic: dict[int, list[int]] = {}
        positioned = []
        for i, entry in enumerate(self.entries):
            if entry.tic_id is not None:
                self.by_tic.setdefault(entry.tic_id, []).append(i)
            if entry.ra_deg is not None and entry.dec_deg is not None:
                positioned.append(i)
        self._positioned = np.array(positioned, dtype=int)
        self._tree = None
        if positioned:
            ra = np.radians([self.entries[i].ra_deg for i in positioned])
            dec = np.radians([self.entries[i].dec_deg for i in positioned])
            xyz = np.column_stack([np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)])
            self._tree = cKDTree(xyz)

    def near(
        self, tic_id: int, ra_deg: float | None, dec_deg: float | None, radius_arcsec: float
    ) -> list[CatalogEntry]:
        found = set(self.by_tic.get(tic_id, []))
        if self._tree is not None and ra_deg is not None and dec_deg is not None:
            ra, dec = math.radians(ra_deg), math.radians(dec_deg)
            point = [math.cos(dec) * math.cos(ra), math.cos(dec) * math.sin(ra), math.sin(dec)]
            # a slightly larger chord, then the exact separation decides
            chord = 2.0 * math.sin(math.radians(1.01 * radius_arcsec / 3600.0) / 2.0)
            for j in self._tree.query_ball_point(point, r=chord):
                found.add(int(self._positioned[j]))
        return [self.entries[i] for i in sorted(found)]


def match_catalog(
    name: str,
    index: CatalogIndex | None,
    tic_id: int,
    ra_deg: float | None,
    dec_deg: float | None,
    period_days: float,
    radius_arcsec: float = SELECTION.match_radius_arcsec,
    tolerance: float = DEDUP.period_tolerance,
    factors: Sequence[float] = DEDUP.factors,
) -> CatalogResult:
    """One catalog. An entry is near the star when it has the star's TIC, or its position is
    within ``radius_arcsec``; a near entry matches when its period is at an alias factor."""
    if index is None:
        return CatalogResult(name, INCONCLUSIVE, 0, reason="no snapshot")
    if index.size == 0:
        return CatalogResult(name, INCONCLUSIVE, 0, reason="the snapshot has no rows")
    matches, undecided = [], []
    for entry in index.near(tic_id, ra_deg, dec_deg, radius_arcsec):
        same_tic = entry.tic_id is not None and entry.tic_id == tic_id
        separation = None
        if None not in (entry.ra_deg, entry.dec_deg, ra_deg, dec_deg):
            separation = separation_arcsec(ra_deg, dec_deg, entry.ra_deg, entry.dec_deg)
        near = same_tic or (separation is not None and separation <= radius_arcsec)
        if not near:
            continue
        if entry.period_days is None:
            # a nearby entry without a period cannot be excluded as the same signal
            undecided.append(entry.identifier)
            continue
        factor = alias_factor(period_days, entry.period_days, factors, tolerance)
        if factor is not None:
            matches.append(
                {
                    "identifier": entry.identifier,
                    "tic_id": entry.tic_id,
                    "separation_arcsec": separation,
                    "catalogued_period_days": entry.period_days,
                    "alias_factor": factor,
                    "same_tic": same_tic,
                }
            )
    if matches:
        return CatalogResult(name, MATCH, index.size, matches)
    if ra_deg is None or dec_deg is None:
        # without the star's position the nearby objects were not searched
        return CatalogResult(name, INCONCLUSIVE, index.size, reason="the star has no position")
    if undecided:
        return CatalogResult(
            name,
            INCONCLUSIVE,
            index.size,
            reason="nearby entries without a period: " + ", ".join(undecided),
        )
    return CatalogResult(name, NO_MATCH, index.size)


def deduplicate(
    catalogs: dict[str, CatalogIndex | None],
    tic_id: int,
    ra_deg: float | None,
    dec_deg: float | None,
    period_days: float,
    required: Sequence[str] = DEDUP.catalogs,
) -> dict[str, Any]:
    """Every required catalog, each with its own state. ``overall`` is ``match`` if any catalog
    matches, ``no_match`` only if every one is ``no_match``, else ``INCONCLUSIVE``."""
    results = [
        match_catalog(name, catalogs.get(name), tic_id, ra_deg, dec_deg, period_days)
        for name in required
    ]
    states = {r.state for r in results}
    if MATCH in states:
        overall = MATCH
    elif states == {NO_MATCH}:
        overall = NO_MATCH
    else:
        overall = INCONCLUSIVE
    return {
        "overall": overall,
        "period_days": period_days,
        "catalogs": [r.to_dict() for r in results],
    }
