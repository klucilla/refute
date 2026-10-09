"""Cross-match with eclipsing-binary catalogs (gauntlet v0.2, test ``eb_catalog``).

Catalogs are not downloaded at run time. Each catalog is a snapshot attached to
the claim with role ``eb-catalog`` (so the lock covers it), in the normalized
format ``refute-eb-catalog-1``: a CSV file with the header

    catalog,source_id,tic_id,ra_deg,dec_deg,period_days

``tic_id`` and ``period_days`` may be empty. The script that builds a snapshot
records the source URL, retrieval time and SHA-256 of the raw catalog next to it.

Some catalogs may not be redistributed (v0.2: TESS-EB, because its terms differ
between the publisher and the CDS). Their entries appear in the attachment only as
*reference rows*: catalog and source identifier, with empty coordinates and period.
The scan record lists such a catalog as an external snapshot (``redistributed:
false``) with its source URL, its local cache path and the SHA-256 of its canonical
content. Before any analysis, :func:`prepare_external_snapshots` downloads the file
if it is missing and checks that hash; if it does not match, the run stops. The
analyzer then resolves the reference rows from that verified local copy
(:func:`resolve_references`).

The canonical content of a VizieR ASU response is every non-empty line that does not
start with ``#``, joined with LF and ending with LF: VizieR writes the query date in
comment lines, so the raw file changes at every download while its content does not.

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
import hashlib
import io
import json
import math
import urllib.request
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
    ra_deg: float | None  # None for a reference row (resolved from an external snapshot)
    dec_deg: float | None
    period_days: float | None

    @property
    def is_reference(self) -> bool:
        return self.ra_deg is None or self.dec_deg is None


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
            entry = EbEntry(
                catalog=row[0],
                source_id=row[1],
                tic_id=_optional(row[2], int),
                ra_deg=_optional(row[3], float),
                dec_deg=_optional(row[4], float),
                period_days=_optional(row[5], float),
            )
        except ValueError as exc:
            raise CatalogError(f"{name}: line {line}: {exc}") from exc
        if (entry.ra_deg is None) != (entry.dec_deg is None):
            raise CatalogError(f"{name}: line {line}: give both coordinates or neither")
        if entry.is_reference and entry.period_days is not None:
            raise CatalogError(f"{name}: line {line}: a reference row carries no catalog values")
        entries.append(entry)
    return entries


# --- external (not redistributed) snapshots -----------------------------------------


def vizier_content(data: bytes) -> bytes:
    """Canonical content of a VizieR ASU response (comment lines removed, LF endings)."""
    text = data.decode("utf-8").replace("\r\n", "\n")
    lines = [ln for ln in text.split("\n") if ln and not ln.startswith("#")]
    return ("\n".join(lines) + "\n").encode("utf-8")


def content_sha256(data: bytes) -> str:
    return hashlib.sha256(vizier_content(data)).hexdigest()


def parse_tess_eb(data: bytes) -> dict[str, tuple[float, float, float | None]]:
    """TESS-EB VizieR TSV (TIC, m_TIC, RAJ2000, DEJ2000, Per) keyed by 'TIC <tic> (<m>)'."""
    lines = vizier_content(data).decode("utf-8").splitlines()
    if not lines or lines[0].split("\t")[:5] != ["TIC", "m_TIC", "RAJ2000", "DEJ2000", "Per"]:
        raise CatalogError("unexpected TESS-EB snapshot header")
    rows = {}
    for line in lines[3:]:  # header, units, dashes
        tic, m_tic, ra, dec, per = (f.strip() for f in line.split("\t"))
        rows[f"TIC {int(tic)} ({m_tic})"] = (float(ra), float(dec), _optional(per, float))
    return rows


EXTERNAL_PARSERS = {"tess-eb-vizier-tsv": parse_tess_eb}


def external_snapshots(scan: dict | None) -> list[dict]:
    return [s for s in (scan or {}).get("snapshots", []) if s.get("redistributed") is False]


def prepare_external_snapshots(
    scan: dict | None, cache_dir: Path, offline: bool, download=None
) -> list[str]:
    """Make sure every external snapshot is in the cache with the recorded content hash.

    Downloads a missing file from its recorded URL (unless ``offline``). Raises
    :class:`CatalogError` if a file is missing offline or its content hash differs:
    the run must stop before any analysis. Returns one message per snapshot.
    """
    fetch = download or _download
    messages = []
    for snap in external_snapshots(scan):
        path = Path(cache_dir) / snap["cache_path"]
        if not path.is_file():
            if offline:
                raise CatalogError(
                    f"{snap['catalog_name']} snapshot not in the cache ({snap['cache_path']}); "
                    "run without --offline to download it"
                )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(fetch(snap["url"]))
        digest = content_sha256(path.read_bytes())
        if digest != snap["content_sha256"]:
            raise CatalogError(
                f"{snap['catalog_name']} snapshot content SHA-256 is {digest}, the claim records "
                f"{snap['content_sha256']}: STOP (the source changed or the file is corrupt)"
            )
        messages.append(f"{snap['catalog_name']}: content SHA-256 verified ({digest})")
    return messages


def _download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "refute"})
    with urllib.request.urlopen(request, timeout=180) as response:  # noqa: S310 - recorded URL
        return response.read()


def resolve_references(entries: list[EbEntry], scan: dict | None, cache_dir: Path) -> list[EbEntry]:
    """Fill reference rows from the verified external snapshots (offline)."""
    if not any(e.is_reference for e in entries):
        return entries
    tables: dict[str, dict] = {}
    for snap in external_snapshots(scan):
        data = (Path(cache_dir) / snap["cache_path"]).read_bytes()
        if content_sha256(data) != snap["content_sha256"]:
            raise CatalogError(f"{snap['catalog_name']} snapshot hash mismatch: STOP")
        tables[snap["catalog_name"]] = EXTERNAL_PARSERS[snap["parser"]](data)
    resolved = []
    for entry in entries:
        if entry.is_reference:
            table = tables.get(entry.catalog)
            if table is None or entry.source_id not in table:
                raise CatalogError(f"reference row {entry.catalog} {entry.source_id} not found")
            ra, dec, per = table[entry.source_id]
            entry = EbEntry(entry.catalog, entry.source_id, entry.tic_id, ra, dec, per)
        resolved.append(entry)
    return resolved


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
    if any(e.is_reference for e in entries):
        raise CatalogError("unresolved reference rows: resolve them before the cross-match")
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
