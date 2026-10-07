"""Plain data types for the TESS pack (numpy arrays, no lightkurve objects).

Times are BTJD: BJD_TDB - 2457000, as in TESS SPOC products.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

import numpy as np

BTJD_OFFSET = 2457000.0
_JD_J2000 = 2451545.0
_J2000 = datetime(2000, 1, 1, 12, 0, 0, tzinfo=UTC)


def btjd_to_datetime(btjd: float) -> datetime:
    """Calendar date of a BTJD time.

    TDB is treated as UTC: the difference (about 69 s) is irrelevant for assigning
    observing years. No leap-second table is needed, so this never uses the network.
    """
    return _J2000 + timedelta(days=float(btjd) + BTJD_OFFSET - _JD_J2000)


def btjd_to_year(btjd: float) -> int:
    return btjd_to_datetime(btjd).year


def year_start_btjd(year: int) -> float:
    start = datetime(year, 1, 1, tzinfo=UTC)
    return (start - _J2000).total_seconds() / 86400.0 + _JD_J2000 - BTJD_OFFSET


@dataclass(frozen=True)
class SectorInfo:
    """Metadata of one sector's light curve. Contains no flux values."""

    sector: int
    year: int
    t_start: float
    t_end: float
    n_points: int
    camera: int | None = None
    ccd: int | None = None
    filename: str = ""
    sha256: str = ""
    url: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StarInfo:
    """Stellar parameters from the TESS Input Catalog (TIC), with provenance."""

    tic_id: int
    radius_rsun: float | None
    radius_err_rsun: float | None
    mass_msun: float | None
    mass_err_msun: float | None
    teff_k: float | None
    logg_cgs: float | None
    tmag: float | None
    tic_version: str | None
    source: str
    retrieved_utc: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProductInfo:
    product: str
    author: str
    exptime_seconds: int
    flux_column: str
    quality_bitmask: str
    quality_bitmask_value: int | None
    reader: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class LightCurveData:
    """Time series as numpy arrays, sorted by time."""

    time: np.ndarray
    flux: np.ndarray
    flux_err: np.ndarray
    sector: np.ndarray
    year: np.ndarray

    def __post_init__(self) -> None:
        self.time = np.asarray(self.time, dtype=float)
        self.flux = np.asarray(self.flux, dtype=float)
        self.flux_err = np.asarray(self.flux_err, dtype=float)
        self.sector = np.asarray(self.sector, dtype=int)
        self.year = np.asarray(self.year, dtype=int)
        n = self.time.size
        for name in ("flux", "flux_err", "sector", "year"):
            if getattr(self, name).shape != (n,):
                raise ValueError(f"{name} must have the same length as time")
        if n > 1 and np.any(np.diff(self.time) < 0):
            order = np.argsort(self.time, kind="stable")
            self.time = self.time[order]
            self.flux = self.flux[order]
            self.flux_err = self.flux_err[order]
            self.sector = self.sector[order]
            self.year = self.year[order]

    def __len__(self) -> int:
        return int(self.time.size)

    def select(self, mask: np.ndarray) -> LightCurveData:
        mask = np.asarray(mask, dtype=bool)
        return LightCurveData(
            self.time[mask],
            self.flux[mask],
            self.flux_err[mask],
            self.sector[mask],
            self.year[mask],
        )

    @property
    def years(self) -> list[int]:
        return sorted(int(y) for y in np.unique(self.year))

    @property
    def sectors(self) -> list[int]:
        return sorted(int(s) for s in np.unique(self.sector))

    @property
    def span(self) -> float:
        return float(self.time[-1] - self.time[0]) if len(self) > 1 else 0.0


@dataclass
class TessData:
    """Everything loaded for one target: raw normalized light curve plus metadata."""

    target_key: str
    tic_id: int
    lc: LightCurveData
    sectors: list[SectorInfo]
    star: StarInfo | None
    product: ProductInfo
    manifest: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Candidate:
    """A periodic box-shaped signal: the output of the period search."""

    period: float
    t0: float
    duration: float
    depth: float
    depth_err: float
    snr: float
    log_likelihood: float
    sde: float
    n_transits: int

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["duration_hours"] = self.duration * 24.0
        out["depth_ppm"] = self.depth * 1e6
        out["t0_bjd"] = self.t0 + BTJD_OFFSET
        return out
