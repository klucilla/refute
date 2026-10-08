"""Cross-match with eclipsing-binary catalogs (gauntlet v0.2, test ``eb_catalog``).

Catalogs are not downloaded at run time. Each catalog is a snapshot attached to
the claim with role ``eb-catalog`` (so the lock covers it), in the normalized
format ``refute-eb-catalog-1``: a CSV file with the header

    catalog,source_id,tic_id,ra_deg,dec_deg,period_days

``tic_id`` and ``period_days`` may be empty. The script that builds a snapshot
records the source URL, retrieval time and SHA-256 of the raw catalog next to it.

Decision: a catalog entry matches the target when it has the target's TIC ID or
lies within ``match_radius_arcsec``. A match whose period equals the found period
times one of ``period_factors`` (within ``period_tolerance``) is a fatal failure;
a match by position or ID only is a warning; no match passes.
"""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass
from pathlib import Path

from refute.core.verdict import Severity, TestResult, TestStatus
from refute.packs.tess.params import EbCatalogParams
from refute.packs.tess.types import StarInfo

CATALOG_FORMAT = "refute-eb-catalog-1"
COLUMNS = ["catalog", "source_id", "tic_id", "ra_deg", "dec_deg", "period_days"]


class CatalogError(ValueError):
    """A catalog snapshot does not follow the refute-eb-catalog-1 format."""


@dataclass(frozen=True)
class EbEntry:
    catalog: str
    source_id: str
    tic_id: int | None
    ra_deg: float
    dec_deg: float
    period_days: float | None


def _optional(value: str, kind: type) -> int | float | None:
    value = value.strip()
    return kind(value) if value else None


def parse_catalog(text: str, name: str = "catalog") -> list[EbEntry]:
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    if header != COLUMNS:
        raise CatalogError(f"{name}: header must be {','.join(COLUMNS)}")
    entries = []
    for line, row in enumerate(reader, start=2):
        if not row:
            continue
        if len(row) != len(COLUMNS):
            raise CatalogError(f"{name}: line {line} has {len(row)} fields")
        try:
            entries.append(
                EbEntry(
                    catalog=row[0],
                    source_id=row[1],
                    tic_id=_optional(row[2], int),
                    ra_deg=float(row[3]),
                    dec_deg=float(row[4]),
                    period_days=_optional(row[5], float),
                )
            )
        except ValueError as exc:
            raise CatalogError(f"{name}: line {line}: {exc}") from exc
    return entries


def load_catalogs(paths: list[Path]) -> list[EbEntry]:
    entries: list[EbEntry] = []
    for path in paths:
        entries.extend(parse_catalog(Path(path).read_text(encoding="utf-8"), Path(path).name))
    return entries


def separation_arcsec(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    """Angular separation (haversine), in arcseconds."""
    r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    h = math.sin((d2 - d1) / 2) ** 2 + math.cos(d1) * math.cos(d2) * math.sin((r2 - r1) / 2) ** 2
    return math.degrees(2 * math.asin(min(1.0, math.sqrt(h)))) * 3600.0


def check_eb_catalog(
    entries: list[EbEntry], star: StarInfo | None, period: float, params: EbCatalogParams
) -> TestResult:
    thresholds = params.model_dump(mode="json")
    if star is None or star.ra_deg is None or star.dec_deg is None:
        return TestResult(
            "eb_catalog",
            TestStatus.INCONCLUSIVE,
            Severity.FATAL,
            "no target coordinates for the catalog cross-match",
            thresholds=thresholds,
        )
    matches = []
    for entry in entries:
        sep = separation_arcsec(star.ra_deg, star.dec_deg, entry.ra_deg, entry.dec_deg)
        by_id = entry.tic_id is not None and entry.tic_id == star.tic_id
        if not by_id and sep > params.match_radius_arcsec:
            continue
        factor = None
        if entry.period_days:
            for f in params.period_factors:
                if abs(entry.period_days - f * period) / (f * period) <= params.period_tolerance:
                    factor = f
                    break
        matches.append(
            {
                "catalog": entry.catalog,
                "source_id": entry.source_id,
                "tic_id": entry.tic_id,
                "separation_arcsec": sep,
                "period_days": entry.period_days,
                "period_factor": factor,
                "matched_by": "tic_id" if by_id else "position",
            }
        )
    metrics = {"n_catalog_entries": len(entries), "matches": matches, "found_period_days": period}
    with_period = [m for m in matches if m["period_factor"] is not None]
    if with_period:
        m = with_period[0]
        return TestResult(
            "eb_catalog",
            TestStatus.FAIL,
            Severity.FATAL,
            f"listed as an eclipsing binary in {m['catalog']} ({m['source_id']}) with period "
            f"{m['period_days']:.6g} d = {m['period_factor']:g} x the found period",
            metrics=metrics,
            thresholds=thresholds,
        )
    if matches:
        m = matches[0]
        return TestResult(
            "eb_catalog",
            TestStatus.FAIL,
            Severity.WARNING,
            f"an eclipsing binary in {m['catalog']} ({m['source_id']}) lies "
            f"{m['separation_arcsec']:.1f} arcsec away, with a different or unknown period",
            metrics=metrics,
            thresholds=thresholds,
        )
    return TestResult(
        "eb_catalog",
        TestStatus.PASS,
        Severity.FATAL,
        f"no eclipsing binary within {params.match_radius_arcsec:g} arcsec in "
        f"{len(entries)} catalog entries",
        metrics=metrics,
        thresholds=thresholds,
    )
