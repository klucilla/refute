"""Injection-recovery of the v0.4 pilot (protocol section 9; issue #175).

Each injection is drawn from the star's injection stream (protocol section 8): draw ``i`` is
the same for any ``K``, so the measurement prefix of the controls counts inside the final ``K``.
Parameters: period log-uniform in [0.5, 13] d; flat-bottom depth log-uniform in [100, 10000]
ppm; impact parameter uniform in [0, 0.8]; the duration of a circular orbit from the period, the
TIC radius, the mass from logg and radius, and the impact parameter; the epoch uniform over one
period from the first cadence. The model is a trapezoid with ingress and egress of 15 % of the
duration each (``refute.packs.tess.synthetic.trapezoid``).

The signal multiplies the normalized PDCSAP flux **before detrending**, so the whole chain runs
on it. The same fractional dip, scaled by the sector's CROWDSAP, multiplies the normalized SAP
flux, so that the systematics test sees the injected transit in both fluxes as a real one on
the target would be; the background is unchanged. No pixel file is injected: injections run the
stage-1 chain only.

Recovery: a period within 1 % of the injected one, an epoch within half the injected duration
(modulo the period), and the gate passes. A period at 2x, 1/2x, 3x or 1/3x is counted apart as
a declared alias.
"""

from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass, replace
from typing import Any

import numpy as np

from refute.packs.tess.discover.protocol import INJECTION
from refute.packs.tess.gauntlet import G_SI, M_SUN_KG, R_SUN_M
from refute.packs.tess.synthetic import trapezoid
from refute.packs.tess.types import LightCurveData, TessData

INGRESS_FRACTION = 0.15


class InjectionError(Exception):
    """The star lacks what the injection needs (radius, logg); its injections are not run."""


def _uniform(seed: int, index: int, name: str) -> float:
    """A uniform number in [0, 1) for draw ``index`` and parameter ``name``: fixed per draw."""
    digest = hashlib.sha256(f"{seed}|injection-{index}|{name}".encode()).digest()
    return int.from_bytes(digest[:8], "big") / 2.0**64


def stellar_mass_from_logg(logg_cgs: float, radius_rsun: float) -> float:
    g_si = 10.0**logg_cgs / 100.0
    return g_si * (radius_rsun * R_SUN_M) ** 2 / G_SI / M_SUN_KG


def duration_days(
    period: float, radius_rsun: float, mass_msun: float, depth: float, impact: float
) -> float:
    """Total duration of a circular orbit: P/pi * asin(R*/a * sqrt((1 + k)^2 - b^2)), with
    sin(i) taken as 1 (b < 1 + k keeps the argument real)."""
    a = (G_SI * mass_msun * M_SUN_KG * (period * 86400.0) ** 2 / (4.0 * math.pi**2)) ** (1 / 3)
    k = math.sqrt(depth)
    chord = math.sqrt(max(0.0, (1.0 + k) ** 2 - impact**2))
    return period / math.pi * math.asin(min(1.0, radius_rsun * R_SUN_M / a * chord))


@dataclass(frozen=True)
class Injection:
    index: int
    period_days: float
    depth: float  # fraction
    impact: float
    duration_days: float
    t0_btjd: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "period_days": self.period_days,
            "depth_ppm": self.depth * 1e6,
            "impact": self.impact,
            "duration_hours": self.duration_days * 24.0,
            "t0_btjd": self.t0_btjd,
        }


def draw_injections(
    seed: int, k: int, first_time: float, radius_rsun: float | None, logg_cgs: float | None
) -> list[Injection]:
    """The first ``k`` injections of the star's stream."""
    if radius_rsun is None or not radius_rsun > 0 or logg_cgs is None:
        raise InjectionError("the injection needs the TIC radius and logg")
    mass = stellar_mass_from_logg(logg_cgs, radius_rsun)
    p_lo, p_hi = math.log(INJECTION.period_min_days), math.log(INJECTION.period_max_days)
    d_lo, d_hi = math.log(INJECTION.depth_min_ppm), math.log(INJECTION.depth_max_ppm)
    out = []
    for i in range(k):
        period = math.exp(p_lo + (p_hi - p_lo) * _uniform(seed, i, "period"))
        depth = math.exp(d_lo + (d_hi - d_lo) * _uniform(seed, i, "depth")) / 1e6
        impact = INJECTION.impact_max * _uniform(seed, i, "impact")
        t0 = first_time + period * _uniform(seed, i, "epoch")
        duration = duration_days(period, radius_rsun, mass, depth, impact)
        out.append(Injection(i, period, depth, impact, duration, t0))
    return out


def inject(data: TessData, injection: Injection) -> TessData:
    """``data`` with the injection multiplied into the normalized PDCSAP flux, and into the
    normalized SAP flux scaled by each sector's CROWDSAP. Pixels are not changed."""
    deficit = trapezoid(
        data.lc.time,
        injection.period_days,
        injection.t0_btjd,
        injection.depth,
        injection.duration_days,
        INGRESS_FRACTION,
    )
    lc = data.lc
    flux = lc.flux * (1.0 - deficit)
    new_lc = LightCurveData(lc.time, flux, lc.flux_err, lc.sector, lc.year)
    aux = data.aux
    if aux is not None:
        sectors = []
        for sector in aux.sectors:
            sector_deficit = trapezoid(
                sector.time,
                injection.period_days,
                injection.t0_btjd,
                injection.depth,
                injection.duration_days,
                INGRESS_FRACTION,
            )
            crowd = sector.crowdsap if sector.crowdsap is not None else 1.0
            sectors.append(
                replace(
                    sector,
                    pdcsap_flux=sector.pdcsap_flux * (1.0 - sector_deficit),
                    sap_flux=sector.sap_flux * (1.0 - crowd * sector_deficit),
                )
            )
        aux = replace(aux, sectors=sectors)
    return replace(data, lc=new_lc, aux=aux)


def recovery(
    injection: Injection, found: dict[str, Any] | None, gate_passed: bool
) -> dict[str, Any]:
    """Whether the found candidate (``period_days``, ``t0_btjd``) is the injected signal."""
    out: dict[str, Any] = {
        "recovered": False,
        "alias": None,
        "gate_passed": gate_passed,
        "period_relative_error": None,
        "epoch_offset_durations": None,
    }
    if not found or found.get("period_days") is None:
        return out
    period = float(found["period_days"])
    error = abs(period - injection.period_days) / injection.period_days
    out["period_relative_error"] = error
    if error <= INJECTION.period_tolerance:
        phase = (float(found["t0_btjd"]) - injection.t0_btjd) / injection.period_days
        offset = abs(phase - round(phase)) * injection.period_days
        out["epoch_offset_durations"] = offset / injection.duration_days
        epoch_ok = offset <= INJECTION.epoch_tolerance_durations * injection.duration_days
        out["recovered"] = bool(epoch_ok and gate_passed)
        return out
    for factor in INJECTION.alias_factors:
        if (
            abs(period - factor * injection.period_days) / (factor * injection.period_days)
            <= INJECTION.period_tolerance
        ):
            out["alias"] = factor
            break
    return out


def wilson_interval(successes: int, trials: int, z: float = 1.959963984540054) -> list[float]:
    """The 95 % Wilson score interval of a proportion (empty trials give [0, 1])."""
    if trials <= 0:
        return [0.0, 1.0]
    p = successes / trials
    denominator = 1.0 + z * z / trials
    centre = (p + z * z / (2 * trials)) / denominator
    half = z * math.sqrt(p * (1 - p) / trials + z * z / (4 * trials * trials)) / denominator
    return [max(0.0, centre - half), min(1.0, centre + half)]


def summarize(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Per-curve counts: injections, recovered (period, epoch and gate), declared aliases, gate
    passes; the recovery rate with its 95 % Wilson interval. The sampling unit is one injection
    into this curve; injections into the same curve are treated as independent, which is an
    approximation."""
    n = len(records)
    recovered = sum(1 for r in records if r["recovery"]["recovered"])
    aliases = sum(1 for r in records if r["recovery"]["alias"] is not None)
    gates = sum(1 for r in records if r["recovery"]["gate_passed"])
    return {
        "sampling_unit": "one injection into this curve",
        "independence": "approximate: injections into the same curve are not independent stars",
        "injections": n,
        "recovered": recovered,
        "declared_aliases": aliases,
        "gate_passed": gates,
        "recovery_rate": recovered / n if n else None,
        "recovery_wilson_95": wilson_interval(recovered, n),
    }


def stage1_chain_seed(randomness_hex: str, tic_id: int) -> int:
    """The injection stream of a star (protocol section 8)."""
    digest = hashlib.sha256(f"{randomness_hex}|v0.4|injection|{tic_id}".encode()).hexdigest()
    return int(digest, 16)


def first_time(data: TessData) -> float:
    return float(np.min(data.lc.time))
