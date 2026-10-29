"""Sampling frame, exclusions, domain and walk of the v0.4 pilot (protocol sections 3 and 4;
issues #22, #27 and #172).

The frame and every catalog are read from files frozen and hashed before the selection round
(protocol section 4.0). Only the per-star checks of the domain (the TIC fields and the MAST
listings) are live queries, passed in by the caller, retried on transient errors by
``refute.selection.walk.with_retries``; when the retries are exhausted the walk stops for the
maintainer and no star is skipped (#22). A star is never rejected by a test that depends on a
signal: the domain uses metadata and the existence of products only (#159).
"""

from __future__ import annotations

import csv
import io
import math
import re
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np

from refute.packs.tess.discover.protocol import CONTROLS, DOMAIN, SELECTION, Domain
from refute.selection.walk import RetriesExhaustedError, RetryPolicy, TransientError, with_retries

# --- the frame -------------------------------------------------------------------------------

TARGET_LIST_LINK = re.compile(r"target_lists/2m/(all_targets_S(\d{3})_v(\d+)\.csv)")
TARGET_LIST_BASE = "https://tess.mit.edu/public/target_lists/2m/"
TARGET_LIST_HEADER = ["TICID", "Camera", "CCD", "Tmag", "RA", "Dec"]


class SelectionError(Exception):
    """An input does not have the expected form; the selection stops."""


def list_urls(page_html: str, s_max: int) -> dict[int, str]:
    """The URL of the all-targets two-minute list of each sector 1 to ``s_max`` on the target
    lists page. A sector with no list, or with two different lists, stops the selection."""
    found: dict[int, set[str]] = {}
    for name, sector, _version in TARGET_LIST_LINK.findall(page_html):
        found.setdefault(int(sector), set()).add(name)
    out = {}
    for sector in range(1, s_max + 1):
        names = found.get(sector, set())
        if len(names) != 1:
            raise SelectionError(f"sector {sector}: {len(names)} all-targets lists on the page")
        out[sector] = TARGET_LIST_BASE + names.pop()
    return out


@dataclass(frozen=True)
class ListRow:
    tic_id: int
    tmag: float | None
    ra_deg: float
    dec_deg: float


def parse_target_list(text: str) -> list[ListRow]:
    """One all-targets list: comment lines start with '#', then the header
    ``TICID,Camera,CCD,Tmag,RA,Dec``."""
    lines = [line for line in text.splitlines() if line.strip() and not line.startswith("#")]
    if not lines:
        raise SelectionError("an empty target list")
    header = [h.strip() for h in lines[0].split(",")]
    if header != TARGET_LIST_HEADER:
        raise SelectionError(f"unexpected target list header {header}")
    rows = []
    for record in csv.reader(lines[1:]):
        tmag = _float(record[3])
        rows.append(ListRow(int(record[0]), tmag, float(record[4]), float(record[5])))
    return rows


@dataclass(frozen=True)
class FrameStar:
    tic_id: int
    sectors: tuple[int, ...]
    tmag: float | None
    ra_deg: float
    dec_deg: float


def build_frame(lists: dict[int, str], min_sectors: int = DOMAIN.min_sectors) -> list[FrameStar]:
    """The union of the TIC IDs of the lists, with the sectors each appears in; kept: stars
    listed in at least ``min_sectors`` sectors. Tmag and position are those of the star's
    lowest sector. Sorted by TIC ID."""
    seen: dict[int, list[tuple[int, ListRow]]] = {}
    for sector in sorted(lists):
        for row in parse_target_list(lists[sector]):
            seen.setdefault(row.tic_id, []).append((sector, row))
    frame = []
    for tic, items in sorted(seen.items()):
        sectors = tuple(sorted({s for s, _ in items}))
        if len(sectors) < min_sectors:
            continue
        first = min(items, key=lambda item: item[0])[1]
        frame.append(FrameStar(tic, sectors, first.tmag, first.ra_deg, first.dec_deg))
    return frame


FRAME_HEADER = "tic_id,n_sectors,sectors,tmag,ra_deg,dec_deg"


def frame_csv(frame: Sequence[FrameStar]) -> bytes:
    """The frame file (LF line endings), whose SHA-256 is written into the protocol commit."""
    lines = [FRAME_HEADER]
    for star in frame:
        tmag = "" if star.tmag is None else repr(star.tmag)
        sectors = " ".join(str(s) for s in star.sectors)
        lines.append(
            f"{star.tic_id},{len(star.sectors)},{sectors},{tmag},{star.ra_deg!r},{star.dec_deg!r}"
        )
    return ("\n".join(lines) + "\n").encode("utf-8")


def read_frame_csv(data: bytes) -> list[FrameStar]:
    rows = list(csv.DictReader(io.StringIO(data.decode("utf-8"))))
    return [
        FrameStar(
            int(r["tic_id"]),
            tuple(int(s) for s in r["sectors"].split()),
            _float(r["tmag"]),
            float(r["ra_deg"]),
            float(r["dec_deg"]),
        )
        for r in rows
    ]


# --- catalogs and exclusions -----------------------------------------------------------------


def read_csv_rows(data: bytes) -> list[dict[str, str]]:
    text = data.decode("utf-8-sig")
    lines = [line for line in text.splitlines() if not line.startswith("#")]
    return list(csv.DictReader(io.StringIO("\n".join(lines))))


def parse_tic(value: str | None) -> int | None:
    match = re.search(r"(\d+)", value or "")
    return int(match.group(1)) if match else None


def toi_rows(data: bytes) -> list[dict[str, str]]:
    """The ExoFOP TOI table (CSV); every row must have a ``TIC ID``."""
    rows = read_csv_rows(data)
    if not rows or "TIC ID" not in rows[0]:
        raise SelectionError("the TOI snapshot has no 'TIC ID' column")
    return rows


def ctoi_tics(data: bytes) -> set[int]:
    """TIC IDs of the ExoFOP CTOI table (CSV, column ``TIC ID``)."""
    rows = read_csv_rows(data)
    if not rows or "TIC ID" not in rows[0]:
        raise SelectionError("the CTOI snapshot has no 'TIC ID' column")
    return {t for t in (parse_tic(r["TIC ID"]) for r in rows) if t is not None}


def pscomppars_rows(data: bytes) -> list[dict[str, str]]:
    rows = read_csv_rows(data)
    if not rows or "tic_id" not in rows[0]:
        raise SelectionError("the pscomppars snapshot has no 'tic_id' column")
    return rows


def tess_eb_tics(data: bytes) -> set[int]:
    """TIC IDs of the TESS-EB VizieR TSV (columns ``TIC``, ...; three header lines: names,
    units, dashes)."""
    lines = [
        line
        for line in data.decode("utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]
    header = [h.strip() for h in lines[0].split("\t")]
    if "TIC" not in header:
        raise SelectionError("the TESS-EB snapshot has no 'TIC' column")
    index = header.index("TIC")
    out = set()
    for line in lines[3:]:
        cell = line.split("\t")[index].strip()
        if cell.isdigit():
            out.add(int(cell))
    return out


def gaia_eb_positions(data: bytes) -> np.ndarray:
    """(n, 2) array of RA and Dec in degrees from the Gaia DR3 EB snapshot (``source_id,ra,
    dec,frequency``)."""
    text = data.decode("utf-8")
    header, _, body = text.partition("\n")
    if header.strip() != "source_id,ra,dec,frequency":
        raise SelectionError(f"unexpected Gaia EB header {header.strip()!r}")
    values = np.loadtxt(io.StringIO(body), delimiter=",", usecols=(1, 2), ndmin=2)
    return values


def _unit(ra_deg: np.ndarray, dec_deg: np.ndarray) -> np.ndarray:
    ra, dec = np.radians(ra_deg), np.radians(dec_deg)
    return np.column_stack([np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)])


def within_radius(
    stars: Sequence[tuple[float, float]], catalog: np.ndarray, radius_arcsec: float
) -> list[bool]:
    """For each (RA, Dec) of ``stars``, whether a catalog position lies within the radius."""
    from scipy.spatial import cKDTree

    if len(stars) == 0:
        return []
    if catalog.size == 0:
        return [False] * len(stars)
    tree = cKDTree(_unit(catalog[:, 0], catalog[:, 1]))
    chord = 2.0 * math.sin(math.radians(radius_arcsec / 3600.0) / 2.0)
    points = np.array(stars, dtype=float)
    hits = tree.query_ball_point(_unit(points[:, 0], points[:, 1]), r=chord)
    return [bool(h) for h in hits]


EXCLUSION_ORDER = ("known_target", "TOI", "CTOI", "pscomppars", "TESS-EB", "Gaia-DR3-EB")


@dataclass
class Exclusions:
    kept: list[FrameStar]
    reasons: dict[int, list[str]]  # excluded TIC -> every reason that applies

    def counts(self) -> dict[str, int]:
        """Each excluded star counted once, by its first reason in ``EXCLUSION_ORDER``; and
        separately the number of stars each reason applies to."""
        first = {r: 0 for r in EXCLUSION_ORDER}
        every = {r: 0 for r in EXCLUSION_ORDER}
        for reasons in self.reasons.values():
            first[min(reasons, key=EXCLUSION_ORDER.index)] += 1
            for reason in reasons:
                every[reason] += 1
        return {
            **{f"first:{k}": v for k, v in first.items()},
            **{f"any:{k}": v for k, v in every.items()},
        }


def apply_exclusions(
    frame: Sequence[FrameStar],
    known: set[int],
    tic_sets: dict[str, set[int]],
    gaia_positions: np.ndarray,
    radius_arcsec: float = SELECTION.match_radius_arcsec,
) -> Exclusions:
    """Remove known targets, stars with a TOI, CTOI or ``pscomppars`` planet or a TESS-EB entry
    (by TIC ID), and stars with a Gaia DR3 EB within ``radius_arcsec`` (by position)."""
    for name in ("TOI", "CTOI", "pscomppars", "TESS-EB"):
        if name not in tic_sets:
            raise SelectionError(f"the {name} snapshot is missing")
    gaia = within_radius([(s.ra_deg, s.dec_deg) for s in frame], gaia_positions, radius_arcsec)
    kept, reasons = [], {}
    for star, gaia_hit in zip(frame, gaia, strict=True):
        why = []
        if star.tic_id in known:
            why.append("known_target")
        for name in ("TOI", "CTOI", "pscomppars", "TESS-EB"):
            if star.tic_id in tic_sets[name]:
                why.append(name)
        if gaia_hit:
            why.append("Gaia-DR3-EB")
        if why:
            reasons[star.tic_id] = why
        else:
            kept.append(star)
    return Exclusions(kept, reasons)


def known_targets(root: Path) -> dict[int, str]:
    """Targets of earlier phases, read from their files (protocol section 4.1): v0.1 and v0.2
    target files (development targets included) and the planets eligible in the v0.2.1 gate-3b
    screening. The pre-document runs of v0.2.1 used synthetic data only (their record says so),
    so they add none."""
    import yaml

    out: dict[int, str] = {}
    for path, label in (
        ("calibration/targets.yaml", "v0.1"),
        ("calibration/v0.2/targets.yaml", "v0.2"),
    ):
        data = yaml.safe_load((root / path).read_text(encoding="utf-8"))
        for target in data["targets"]:
            out.setdefault(int(target["tic_id"]), f"{label} {target['kind']}")
    import json

    gate = json.loads(
        (root / "docs/validation/v0.2.1/reopen/stage-1/real-controls/result.json").read_text(
            encoding="utf-8"
        )
    )
    for cls in ("planets", "false_positives"):
        for row in gate["pools"][cls]["eligible"]:
            out.setdefault(int(row["tic_id"]), f"v0.2.1 gate-3b {cls}")
    return out


# --- the domain ------------------------------------------------------------------------------


def mjd_year(mjd: float) -> int:
    return (datetime(1858, 11, 17, tzinfo=UTC) + timedelta(days=float(mjd))).year


@dataclass(frozen=True)
class Listing:
    """What MAST lists for a star (SPOC 120-s): the sector and start (MJD) of each product."""

    light_curves: tuple[tuple[int, float], ...]
    pixel_files: tuple[tuple[int, float], ...]


TIC_FIELDS = ("logg", "rad", "e_rad", "Teff", "Tmag", "contratio", "ra", "dec")


def domain_check(
    tic: dict[str, float | None], listing: Listing, domain: Domain = DOMAIN
) -> tuple[bool, str, dict[str, Any]]:
    """Section 3 of the protocol, on metadata only. Returns (in domain, reason, evidence); the
    reason names the first rule that fails, in the order D-1 to D-8."""
    missing = [f for f in TIC_FIELDS if f not in tic]
    if missing:
        raise SelectionError("the TIC answer lacks the field(s): " + ", ".join(missing))
    lc_sectors = sorted({s for s, _ in listing.light_curves})
    starts = sorted(t for _, t in listing.light_curves)
    years = sorted({mjd_year(t) for t in starts})
    span = (starts[-1] - starts[0]) if starts else 0.0
    px_sectors = sorted({s for s, _ in listing.pixel_files})
    evidence: dict[str, Any] = {
        "light_curve_sectors": lc_sectors,
        "light_curve_years": years,
        "light_curve_span_days": round(span, 3),
        "pixel_file_sectors": px_sectors,
        **{f"tic_{k}": tic[k] for k in TIC_FIELDS},
    }
    rad, e_rad = tic["rad"], tic["e_rad"]
    rules = [
        ("D-1", len(lc_sectors) >= domain.min_sectors, f"fewer than {domain.min_sectors} sectors"),
        (
            "D-2",
            len(years) >= domain.min_years and span >= domain.min_span_days,
            f"fewer than {domain.min_years} years or a span under {domain.min_span_days:g} d",
        ),
        (
            "D-3",
            (not domain.pixel_files_every_sector) or set(lc_sectors) <= set(px_sectors),
            "a sector without a target pixel file",
        ),
        ("D-4", _ge(tic["logg"], domain.min_logg), f"logg missing or < {domain.min_logg:g}"),
        (
            "D-5",
            _ok(rad) and rad > 0 and _ok(e_rad) and e_rad / rad <= domain.max_radius_rel_err,
            f"radius or its error missing, or error / radius > {domain.max_radius_rel_err:g}",
        ),
        (
            "D-6",
            _ok(tic["Teff"]) and domain.teff_min_k <= tic["Teff"] <= domain.teff_max_k,
            f"Teff missing or outside {domain.teff_min_k:g} to {domain.teff_max_k:g} K",
        ),
        (
            "D-7",
            _ok(tic["Tmag"]) and domain.tmag_min <= tic["Tmag"] <= domain.tmag_max,
            f"Tmag missing or outside {domain.tmag_min:g} to {domain.tmag_max:g}",
        ),
        (
            "D-8",
            _ok(tic["contratio"]) and tic["contratio"] <= domain.max_contamination,
            f"contamination ratio missing or > {domain.max_contamination:g}",
        ),
    ]
    for rule, ok, why in rules:
        if not ok:
            return False, f"{rule}: {why}", evidence
    return True, "accepted", evidence


# --- the walk --------------------------------------------------------------------------------

ACCEPTED = "accepted"
REJECTED = "rejected"
STOPPED = "stopped_transient"


@dataclass
class Decision:
    position: int
    tic_id: int
    decision: str
    reason: str
    evidence: dict[str, Any] = field(default_factory=dict)
    transient_attempts: list[dict[str, str]] = field(default_factory=list)


@dataclass
class Walk:
    label: str
    needed: int
    decisions: list[Decision]
    stopped: bool

    @property
    def accepted(self) -> list[int]:
        return [d.tic_id for d in self.decisions if d.decision == ACCEPTED]

    @property
    def outcome(self) -> str:
        if self.stopped:
            return STOPPED
        return "sample_filled" if len(self.accepted) == self.needed else "input_exhausted"

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "needed": self.needed,
            "outcome": self.outcome,
            "accepted": self.accepted,
            "decisions": [d.__dict__ for d in self.decisions],
        }


def walk(
    label: str,
    ordered: Iterable[int],
    triage: Callable[[int], tuple[bool, str, dict[str, Any]]],
    needed: int,
    policy: RetryPolicy,
    sleep: Callable[[float], None],
) -> Walk:
    """Walk ``ordered`` until ``needed`` stars are accepted. ``triage`` may raise
    ``TransientError``; after the retries the walk stops at that star, for the maintainer.
    Any other error propagates (the selection stops; no star is rejected by an error)."""
    decisions: list[Decision] = []
    for position, tic in enumerate(ordered, start=1):
        try:
            (ok, reason, evidence), failures = with_retries(lambda t=tic: triage(t), policy, sleep)
        except RetriesExhaustedError as exc:
            attempts = [{"utc": a.utc, "error": a.error} for a in exc.attempts]
            decisions.append(Decision(position, tic, STOPPED, "transient errors", {}, attempts))
            return Walk(label, needed, decisions, stopped=True)
        attempts = [{"utc": a.utc, "error": a.error} for a in failures]
        decisions.append(
            Decision(position, tic, ACCEPTED if ok else REJECTED, reason, evidence, attempts)
        )
        if ok and sum(d.decision == ACCEPTED for d in decisions) == needed:
            break
    return Walk(label, needed, decisions, stopped=False)


def policy() -> RetryPolicy:
    return RetryPolicy(SELECTION.retry_attempts, SELECTION.retry_backoff_seconds)


TRANSIENT_HTTP = range(500, 600)


def transient(call: Callable[[], Any], context: str) -> Any:
    """Run a MAST or catalog query; a failure that may pass (a connection error, a timeout, an
    HTTP 5xx answer) becomes ``TransientError``. Anything else propagates unchanged."""
    try:
        return call()
    except (TimeoutError, ConnectionError) as exc:
        raise TransientError(f"{context}: {type(exc).__name__}") from exc
    except Exception as exc:
        try:
            import requests
        except ImportError:  # pragma: no cover - requests comes with astroquery
            raise exc from None
        if isinstance(exc, requests.exceptions.HTTPError):
            status = getattr(exc.response, "status_code", None)
            if status in TRANSIENT_HTTP:
                raise TransientError(f"{context}: HTTP {status}") from exc
            raise
        if isinstance(exc, (requests.exceptions.ConnectionError, requests.exceptions.Timeout)):
            raise TransientError(f"{context}: {type(exc).__name__}") from exc
        raise


# --- control pools ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PoolRow:
    tic_id: int
    name: str
    period_days: float
    depth: float  # percent for planets, ppm for false positives
    row: dict[str, str]


def planet_pool(rows: Sequence[dict[str, str]], min_depth_percent: float) -> list[PoolRow]:
    """``pscomppars`` rows with ``tran_flag = 1``, ``sy_pnum = 1``, a TIC, the period range of
    the protocol and ``pl_trandep`` at least ``min_depth_percent``. One row per TIC."""
    out: dict[int, PoolRow] = {}
    for r in rows:
        tic = parse_tic(r.get("tic_id"))
        period, depth = _float(r.get("pl_orbper")), _float(r.get("pl_trandep"))
        if (
            tic is None
            or r.get("tran_flag") != "1"
            or r.get("sy_pnum") != "1"
            or period is None
            or depth is None
            or not CONTROLS.period_min_days < period < CONTROLS.period_max_days
            or depth < min_depth_percent
        ):
            continue
        out.setdefault(tic, PoolRow(tic, r.get("pl_name", ""), period, depth, dict(r)))
    return [out[t] for t in sorted(out)]


def fp_pool(
    rows: Sequence[dict[str, str]], planet_tics: set[int], min_depth_ppm: float
) -> list[PoolRow]:
    """TOI rows with TFOPWG disposition ``FP``, the period range, depth at least
    ``min_depth_ppm``, exactly one TOI for the TIC and no ``pscomppars`` planet."""
    per_tic: dict[int, int] = {}
    for r in rows:
        tic = parse_tic(r.get("TIC ID"))
        if tic is not None:
            per_tic[tic] = per_tic.get(tic, 0) + 1
    out = []
    for r in rows:
        tic = parse_tic(r.get("TIC ID"))
        period, depth = _float(r.get("Period (days)")), _float(r.get("Depth (ppm)"))
        if (
            tic is None
            or (r.get("TFOPWG Disposition") or "").strip() != "FP"
            or period is None
            or depth is None
            or not CONTROLS.period_min_days < period < CONTROLS.period_max_days
            or depth < min_depth_ppm
            or per_tic.get(tic) != 1
            or tic in planet_tics
        ):
            continue
        out.append(PoolRow(tic, f"TOI-{r.get('TOI', '')}", period, depth, dict(r)))
    return sorted(out, key=lambda p: p.tic_id)


# --- helpers ---------------------------------------------------------------------------------


def _float(value: str | None) -> float | None:
    try:
        number = float(value) if value not in (None, "") else None
    except ValueError:
        return None
    return number if number is not None and math.isfinite(number) else None


def _ok(value: float | None) -> bool:
    return value is not None and math.isfinite(value)


def _ge(value: float | None, limit: float) -> bool:
    return _ok(value) and value >= limit
