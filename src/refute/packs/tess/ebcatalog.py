"""Cross-match with eclipsing-binary catalogs (gauntlet v0.2, test ``eb_catalog``).

Catalogs are not downloaded at run time. Each catalog is a snapshot attached to
the claim with role ``eb-catalog`` (so the lock covers it), in the normalized
format ``refute-eb-catalog-1``: a CSV file with the header

    catalog,source_id,tic_id,ra_deg,dec_deg,period_days

``tic_id`` and ``period_days`` may be empty. The script that builds a snapshot
records the source URL, retrieval time and SHA-256 of the raw catalog next to it.

Because an extraction around the targets can legitimately be empty, the proof that
the catalogs were examined comes from a second attachment, role ``eb-catalog-scan``
(JSON, format ``refute-eb-catalog-scan-1``): the snapshots scanned (file, SHA-256,
rows), the extraction radius and the targets the extraction was made for. Without
it, or if the target was not part of the extraction, or if the extraction radius is
smaller than the match radius, the test is INCONCLUSIVE: an empty answer is a PASS
only when the catalogs were really searched around this target.

Decision: a catalog entry matches the target when it has the target's TIC ID or
lies within ``match_radius_arcsec``. A match whose period equals the found period
times one of ``period_factors`` (within ``period_tolerance``) is a fatal failure;
a match by position or ID only is a warning; no match passes.
"""

from __future__ import annotations

import csv
import io
import json
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


def load_scan(path: Path) -> dict:
    scan = json.loads(Path(path).read_text(encoding="utf-8"))
    if scan.get("format") != "refute-eb-catalog-scan-1":
        raise CatalogError(f"{Path(path).name}: not a refute-eb-catalog-scan-1 file")
    return scan


def separation_arcsec(ra1: float, dec1: float, ra2: float, dec2: float) -> float:
    """Angular separation (haversine), in arcseconds."""
    r1, d1, r2, d2 = map(math.radians, (ra1, dec1, ra2, dec2))
    h = math.sin((d2 - d1) / 2) ** 2 + math.cos(d1) * math.cos(d2) * math.sin((r2 - r1) / 2) ** 2
    return math.degrees(2 * math.asin(min(1.0, math.sqrt(h)))) * 3600.0


def _inconclusive(reason: str, thresholds: dict) -> TestResult:
    return TestResult(
        "eb_catalog",
        TestStatus.INCONCLUSIVE,
        Severity.FATAL,
        reason,
        thresholds=thresholds,
        coverage=0,
        coverage_unit="catalog rows scanned",
    )


def check_eb_catalog(
    entries: list[EbEntry],
    scan: dict | None,
    target_key: str,
    star: StarInfo | None,
    period: float,
    params: EbCatalogParams,
) -> TestResult:
    thresholds = params.model_dump(mode="json")
    if star is None or star.ra_deg is None or star.dec_deg is None:
        return _inconclusive("no target coordinates for the catalog cross-match", thresholds)
    if not scan or not scan.get("snapshots"):
        return _inconclusive("no record of which catalogs were scanned", thresholds)
    if target_key not in (scan.get("per_target") or {}):
        return _inconclusive(
            f"the catalogs were not scanned around {target_key} (not in the extraction)",
            thresholds,
        )
    if float(scan.get("radius_arcsec", 0)) < params.match_radius_arcsec:
        return _inconclusive(
            f"extraction radius {scan.get('radius_arcsec')} arcsec is smaller than the match "
            f"radius {params.match_radius_arcsec:g} arcsec",
            thresholds,
        )
    scanned = sum(int(s["rows"]) for s in scan["snapshots"])
    names = ", ".join(Path(s["file"]).name for s in scan["snapshots"])
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
    metrics = {
        "n_catalog_entries": len(entries),
        "catalog_rows_scanned": scanned,
        "snapshots": scan["snapshots"],
        "matches": matches,
        "found_period_days": period,
    }
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
            coverage=scanned,
            coverage_unit="catalog rows scanned",
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
            coverage=scanned,
            coverage_unit="catalog rows scanned",
        )
    return TestResult(
        "eb_catalog",
        TestStatus.PASS,
        Severity.FATAL,
        f"no eclipsing binary within {params.match_radius_arcsec:g} arcsec: {scanned} catalog "
        f"rows scanned ({names}), {len(entries)} extracted near the targets",
        metrics=metrics,
        thresholds=thresholds,
        coverage=scanned,
        coverage_unit="catalog rows scanned",
    )
