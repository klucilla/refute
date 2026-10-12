"""v0.2.1 synthetic population study harness.

Protocol: docs/validation/v0.2.1/population-study.md, with its Amendment 1 (inputs are
regenerated and checked by hash). This file is outside ``src/``: it is not part of the
code hash of Refute, and it is never edited after the first generation (a change is a
new file with a new name).

Modes (``python population.py <mode> --help``):

- ``generate``: only in the environment of tag v0.2.0 (commit f479823). Builds every case
  of a population from its seed, writes its canonical serialization to a cache folder,
  and writes the manifest (or, with ``--check``, compares with a frozen manifest). It
  analyzes nothing.
- ``analyze``: in the environment of a measurement point. Reads only cases whose bytes
  match the manifest, runs catalog conditions (i) and (ii), and writes one result file
  per case. Results are never overwritten; an interrupted run is resumed by running the
  same command again (only cases without a result are analyzed).
- ``metrics``: criteria C1-C6 with one-sided 95% Clopper-Pearson bounds, results by
  mechanism, and paired comparisons between runs.
- ``orchestrate``: the cycle by lot (regenerate, check, analyze at every point, check the
  results on disk, then delete the lot's inputs from the cache).

Only the interfaces listed in section 7 of the protocol are used. ``matching_factor``
and ``conclude_analysis`` are not used: signal identity is computed here.
"""

from __future__ import annotations

import argparse
import ctypes
import hashlib
import json
import math
import os
import platform
import subprocess
import sys
import time
import traceback
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

SERIALIZATION = "refute-population-serialization/1"
MAGIC = (SERIALIZATION + "\n").encode("ascii")
MANIFEST_FORMAT = "refute-population-manifest/1"
RESULT_FORMAT = "refute-population-result/1"
GENERATOR_COMMIT = "f4798230f1bca607bcc0e98fe47711a26ec4ee59"
GENERATOR_SYNTHETIC_SHA256 = "b1d9518ea96ee3fd91b861c33601d57742ad96520b15079d97bd217f391fc50d"
HARNESS_PATH = Path(__file__).resolve()

# --- protocol constants (population-study.md, sections 3 and 4) ------------------------

NOISE_PPM = 600.0
AR_PPM = 600.0
AR_TAU_DAYS = 1.0 / 24.0
TREND_AMPLITUDE = 0.002
TREND_PERIOD_DAYS = 6.0
RSUN_AU = 0.00465047
TARGET_TIC = 1
FAST_PLAN = {"search": {"period_max_days": 6.0, "durations_hours": [1.0, 2.0, 3.0, 4.0]}}
PERIOD_TOLERANCE = 0.001
IDENTITY_FACTORS = (1.0, 2.0, 0.5)
BANDS = {
    "below": (0.5, 1.0, "uniform"),
    "near": (1.0, 1.5, "uniform"),
    "measurable": (1.5, 6.0, "log-uniform"),
}
DEPTH_LIMITS = {"planet": 0.03, "eclipse": 0.5, "neighbor": 1.0}
MAX_ATTEMPTS = 1000
SECTOR_STARTS = {2018: 1325.0, 2019: 1700.0, 2020: 2061.0}
FEW_TRAIN_STARTS = {1: 1690.25, 2: 2055.5, 3: 2420.75}
CATALOG_HEADER = "catalog,source_id,tic_id,ra_deg,dec_deg,period_days"
NEIGHBOR_TIC = 2

PLANET_MECHANISMS = ("two_years", "three_years", "few_train", "variability_some_years")
FP_MECHANISMS = ("eb_secondary", "eb_odd_even", "blend", "variability_masked")
NOTRANSIT_MECHANISMS = ("pure_noise", "trend", "trend_variability")
CATALOG_VARIANTS = ("own", "own", "own", "neighbor", "independent")

DEV_PREFIX = "refute-v0.2.1-population-dev"
SELFTEST_PREFIX = "refute-v0.2.1-population-selftest"

# The order of the random calls, recorded in the manifest (Amendment 1, item c).
CALL_SEQUENCE = [
    "parameters: numpy.random.default_rng(seed_k) (PCG64); seed_k = case seed for the "
    "first attempt, sub_seed(seed, 'redraw', k) for attempt k; draws in the order of "
    "draw_parameters() for the case's class and mechanism",
    "noise: numpy.random.default_rng(sub_seed(seed_k, 'noise')); per sector in time "
    "order: white normal(0, 600 ppm, n); for correlated noise, then normal(0, 600 ppm) "
    "for the first AR(1) value and normal(0, 1, n) for the innovations",
    "pixels and auxiliary data: refute.packs.tess.synthetic.make_aux(lc, "
    "seed=sub_seed(seed_k, 'aux')) at v0.2.0; for a blend, "
    "numpy.random.default_rng(sub_seed(seed_k, 'aux')) passed to render_pixels for each "
    "sector in order, then to make_sector_aux",
]


def sub_seed(seed: int, *parts: object) -> int:
    text = "|".join([str(seed), *(str(p) for p in parts)])
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


def case_seed(prefix: str, cls: str, band: str, noise: str, index: int) -> int:
    text = f"{prefix}|{cls}|{band}|{noise}|{index}"
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


# --- populations ------------------------------------------------------------------------


def _planet_mechanism(i: int) -> str:
    return PLANET_MECHANISMS[0 if i < 100 else 1 if i < 150 else 2 if i < 200 else 3]


def _fp_mechanism(i: int, n: int) -> str:
    if n == 250:
        return FP_MECHANISMS[0 if i < 63 else 1 if i < 126 else 2 if i < 188 else 3]
    return FP_MECHANISMS[i // (n // 4)]


def _notransit_mechanism(i: int, n: int) -> str:
    pure, trend = round(0.4 * n), round(0.3 * n)
    return NOTRANSIT_MECHANISMS[0 if i < pure else 1 if i < pure + trend else 2]


def _case(prefix, cls, band, noise, index, mechanism, variant, extra=None) -> dict:
    band_tag = band or "none"
    return {
        "id": f"{cls}-{band_tag}-{noise}-{index:04d}",
        "class": cls,
        "band": band,
        "noise": noise,
        "index": index,
        "mechanism": mechanism,
        "catalog_variant": variant,
        "seed": str(case_seed(prefix, cls, band_tag, noise, index)),
        "extra": extra or {},
    }


def _few_train_extra(j: int, n: int) -> dict:
    third = math.ceil(n / 3)
    distance = 1 + min(2, j // third) if n >= 3 else 1 + j
    return {"train_transits": 3 if j % 2 == 0 else 4, "distance_years": distance}


def population_cases(population: str) -> list[dict]:
    """Every case of a population, in a fixed order."""
    if population == "selftest":
        return _selftest_cases()
    if population == "dev":
        prefix = DEV_PREFIX
    elif population.startswith("confirm:"):
        prefix = population.split(":", 1)[1]
    else:
        raise SystemExit(f"unknown population {population}")
    cases = []
    for noise in ("white", "correlated"):
        for band in ("below", "near", "measurable"):
            for i in range(250):
                mech = _planet_mechanism(i)
                extra = _few_train_extra(i - 150, 50) if mech == "few_train" else None
                cases.append(
                    _case(prefix, "planet", band, noise, i, mech, CATALOG_VARIANTS[i % 5], extra)
                )
        for band, n in (("below", 100), ("near", 100), ("measurable", 250)):
            for i in range(n):
                cases.append(
                    _case(
                        prefix,
                        "false_positive",
                        band,
                        noise,
                        i,
                        _fp_mechanism(i, n),
                        CATALOG_VARIANTS[i % 5],
                    )
                )
        n = 2200 if noise == "white" else 600
        for i in range(n):
            cases.append(
                _case(prefix, "no_transit", None, noise, i, _notransit_mechanism(i, n), None)
            )
    return cases


def _selftest_cases() -> list[dict]:
    """At most 2 cases per class and mechanism, in both noise models (self-test only)."""
    cases, counter = [], 0
    variants = ("own", "neighbor", "independent")
    for noise in ("white", "correlated"):
        for m, mech in enumerate(PLANET_MECHANISMS):
            for t, band in enumerate(("measurable", "near")):
                extra = _few_train_extra(t, 2) if mech == "few_train" else None
                cases.append(
                    _case(
                        SELFTEST_PREFIX,
                        "planet",
                        band,
                        noise,
                        2 * m + t,
                        mech,
                        variants[counter % 3],
                        extra,
                    )
                )
                counter += 1
        for m, mech in enumerate(FP_MECHANISMS):
            for t, band in enumerate(("measurable", "below")):
                cases.append(
                    _case(
                        SELFTEST_PREFIX,
                        "false_positive",
                        band,
                        noise,
                        2 * m + t,
                        mech,
                        variants[counter % 3],
                    )
                )
                counter += 1
        for m, mech in enumerate(NOTRANSIT_MECHANISMS):
            for t in range(2):
                cases.append(
                    _case(SELFTEST_PREFIX, "no_transit", None, noise, 2 * m + t, mech, None)
                )
    return cases


# --- canonical serialization (Amendment 1, item b) --------------------------------------


def plain(value):
    """Plain JSON values: numpy scalars to Python, tuples to lists; no NaN or infinity."""
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [plain(v) for v in value]
    if isinstance(value, np.generic):
        value = value.item()
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite float in canonical metadata")
    return value


def canonical_json(obj) -> bytes:
    """UTF-8, sorted keys, no spaces, floats as Python's shortest round-trip repr."""
    text = json.dumps(
        plain(obj), sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    )
    return text.encode("utf-8")


def serialize(meta: dict, arrays: list[tuple[str, np.ndarray, str]]) -> bytes:
    """MAGIC, 8-byte little-endian length of the metadata JSON, the metadata JSON, then
    every array's bytes in the listed order, C-order, in its declared dtype."""
    index = [[name, dtype, list(np.shape(a))] for name, a, dtype in arrays]
    head = canonical_json({**meta, "arrays": index})
    body = b"".join(
        np.ascontiguousarray(a, dtype=np.dtype(d)).tobytes(order="C") for _, a, d in arrays
    )
    return MAGIC + len(head).to_bytes(8, "little") + head + body


def deserialize(blob: bytes) -> tuple[dict, dict[str, np.ndarray]]:
    if not blob.startswith(MAGIC):
        raise ValueError("not a refute-population-serialization/1 file")
    pos = len(MAGIC)
    size = int.from_bytes(blob[pos : pos + 8], "little")
    pos += 8
    meta = json.loads(blob[pos : pos + size].decode("utf-8"))
    pos += size
    arrays = {}
    for name, dtype, shape in meta["arrays"]:
        dt = np.dtype(dtype)
        count = int(np.prod(shape)) if shape else 1
        n = count * dt.itemsize
        arrays[name] = np.frombuffer(blob[pos : pos + n], dtype=dt).reshape(shape).copy()
        pos += n
    if pos != len(blob):
        raise ValueError("trailing bytes after the last array")
    return meta, arrays


def data_to_parts(data) -> tuple[dict, list[tuple[str, np.ndarray, str]]]:
    lc = data.lc
    arrays = [
        ("lc/time", lc.time, "<f8"),
        ("lc/flux", lc.flux, "<f8"),
        ("lc/flux_err", lc.flux_err, "<f8"),
        ("lc/sector", lc.sector, "<i8"),
        ("lc/year", lc.year, "<i8"),
    ]
    aux = data.aux
    aux_sectors, pixels = [], []
    for k, s in enumerate(aux.sectors):
        for field in ("time", "pdcsap_flux", "sap_flux", "sap_bkg", "dump_times"):
            arrays.append((f"aux/sectors/{k}/{field}", getattr(s, field), "<f8"))
        aux_sectors.append({"sector": s.sector, "crowdsap": s.crowdsap, "flfrcsap": s.flfrcsap})
    for k, p in enumerate(aux.pixels):
        arrays += [
            (f"aux/pixels/{k}/time", p.time, "<f8"),
            (f"aux/pixels/{k}/flux", p.flux, "<f8"),
            (f"aux/pixels/{k}/flux_err", p.flux_err, "<f8"),
            (f"aux/pixels/{k}/aperture", p.aperture, "|b1"),
        ]
        pixels.append(
            {
                "sector": p.sector,
                "target_xy": list(p.target_xy) if p.target_xy is not None else None,
                "filename": p.filename,
                "sha256": p.sha256,
                "n_dropped_cadences": p.n_dropped_cadences,
            }
        )
    meta = {
        "target_key": data.target_key,
        "tic_id": data.tic_id,
        "sectors": [asdict(s) for s in data.sectors],
        "star": asdict(data.star) if data.star is not None else None,
        "product": asdict(data.product),
        "data_manifest": data.manifest,
        "aux": {
            "sectors": aux_sectors,
            "pixels": pixels,
            "neighbors": [asdict(n) for n in (aux.neighbors or [])],
            "neighbor_radius_arcsec": aux.neighbor_radius_arcsec,
        },
    }
    return meta, arrays


def parts_to_data(meta: dict, arrays: dict[str, np.ndarray]):
    """TessData from a deserialized case, with the types of the code being measured."""
    from refute.packs.tess.types import (
        AuxData,
        LightCurveData,
        Neighbor,
        PixelData,
        ProductInfo,
        SectorAux,
        SectorInfo,
        StarInfo,
        TessData,
    )

    d = meta["data"]
    lc = LightCurveData(
        arrays["lc/time"],
        arrays["lc/flux"],
        arrays["lc/flux_err"],
        arrays["lc/sector"],
        arrays["lc/year"],
    )
    aux_meta = d["aux"]
    sectors_aux = [
        SectorAux(
            sector=s["sector"],
            time=arrays[f"aux/sectors/{k}/time"],
            pdcsap_flux=arrays[f"aux/sectors/{k}/pdcsap_flux"],
            sap_flux=arrays[f"aux/sectors/{k}/sap_flux"],
            sap_bkg=arrays[f"aux/sectors/{k}/sap_bkg"],
            dump_times=arrays[f"aux/sectors/{k}/dump_times"],
            crowdsap=s["crowdsap"],
            flfrcsap=s["flfrcsap"],
        )
        for k, s in enumerate(aux_meta["sectors"])
    ]
    pixels = [
        PixelData(
            sector=p["sector"],
            time=arrays[f"aux/pixels/{k}/time"],
            flux=arrays[f"aux/pixels/{k}/flux"],
            flux_err=arrays[f"aux/pixels/{k}/flux_err"],
            aperture=arrays[f"aux/pixels/{k}/aperture"],
            target_xy=tuple(p["target_xy"]) if p["target_xy"] is not None else None,
            filename=p["filename"],
            sha256=p["sha256"],
            n_dropped_cadences=p["n_dropped_cadences"],
        )
        for k, p in enumerate(aux_meta["pixels"])
    ]
    aux = AuxData(
        sectors=sectors_aux,
        pixels=pixels,
        neighbors=[Neighbor(**n) for n in aux_meta["neighbors"]],
        neighbor_radius_arcsec=aux_meta["neighbor_radius_arcsec"],
    )
    return TessData(
        target_key=d["target_key"],
        tic_id=d["tic_id"],
        lc=lc,
        sectors=[SectorInfo(**s) for s in d["sectors"]],
        star=StarInfo(**d["star"]) if d["star"] is not None else None,
        product=ProductInfo(**d["product"]),
        manifest=d["data_manifest"],
        aux=aux,
    )


# --- expected SNR (population-study.md, section 3) --------------------------------------


def _transit_groups(time: np.ndarray, period: float, t0: float, duration: float):
    epoch = np.round((time - t0) / period)
    inside = np.abs(time - (t0 + epoch * period)) <= duration / 2.0
    return epoch, inside


def unit_snr(time, unit_deficit, epoch, inside, select, noise: str) -> float:
    """SNR per unit depth of the in-transit mean over the selected cadences."""
    mask = inside & select
    if not mask.any():
        return 0.0
    s2 = (NOISE_PPM * 1e-6) ** 2
    a2 = (AR_PPM * 1e-6) ** 2
    total_var = 0.0
    for e in np.unique(epoch[mask]):
        t = time[mask & (epoch == e)]
        var = s2 * t.size
        if noise == "correlated":
            var += a2 * float(np.exp(-np.abs(t[:, None] - t[None, :]) / AR_TAU_DAYS).sum())
        total_var += var
    return float(unit_deficit[mask].sum() / math.sqrt(total_var))


def snr_profile(time, years, unit_deficit, epoch, inside, noise, gate, hidden_min) -> dict:
    out = {
        "global": unit_snr(time, unit_deficit, epoch, inside, np.ones(time.size, bool), noise),
        "train": {},
        "hidden": {},
    }
    for y in sorted({int(v) for v in years}):
        out["train"][str(y)] = unit_snr(time, unit_deficit, epoch, inside, years != y, noise)
        out["hidden"][str(y)] = unit_snr(time, unit_deficit, epoch, inside, years == y, noise)
    ratios = [out["global"] / gate]
    ratios += [v / gate for v in out["train"].values()]
    ratios += [v / hidden_min for v in out["hidden"].values()]
    out["min_unit_ratio"] = min(ratios)
    return out


# --- generation (only in the v0.2.0 environment) ----------------------------------------


def _layout(mech: str, extra: dict) -> list[tuple[int, float, bool]]:
    """(sector number, start, first orbit only) for each sector, in time order."""
    if mech in ("three_years", "variability_some_years"):
        starts = [SECTOR_STARTS[2018], SECTOR_STARTS[2019], SECTOR_STARTS[2020]]
        return [(k + 1, s, False) for k, s in enumerate(starts)]
    if mech == "few_train":
        return [
            (1, SECTOR_STARTS[2018], True),
            (2, FEW_TRAIN_STARTS[extra["distance_years"]], False),
        ]
    return [(1, SECTOR_STARTS[2018], False), (2, SECTOR_STARTS[2020], False)]


def _sector_cadences(synthetic, layout):
    out = []
    for number, start, first_only in layout:
        t = synthetic.sector_times(start)
        if first_only:
            t = t[t < start + 13.0]
        out.append((number, t))
    return out


def _planet_duration(period: float, k: float, b: float) -> float:
    a_au = (period / 365.25) ** (2.0 / 3.0)  # one solar mass
    x = (RSUN_AU / a_au) * math.sqrt(max((1.0 + k) ** 2 - b * b, 1e-12))
    t14 = period / math.pi * math.asin(min(1.0, x))
    return min(max(t14, 1.0 / 24.0), 4.0 / 24.0)


def _commensurate(p1: float, p2: float) -> bool:
    ratio = p1 / p2
    return any(abs(ratio - p / q) <= 0.01 for q in range(1, 5) for p in range(1, 81))


def draw_parameters(case: dict, rng: np.random.Generator, t_first: float) -> dict:
    """Random parameters of a case, drawn in a fixed order (CALL_SEQUENCE)."""
    cls, mech = case["class"], case["mechanism"]
    p: dict = {}
    if cls != "no_transit":
        lo, hi, kind = BANDS[case["band"]]
        u = rng.uniform()
        p["r_target"] = lo * (hi / lo) ** u if kind == "log-uniform" else lo + (hi - lo) * u
    if cls == "planet":
        p["period"] = rng.uniform(3.0, 5.5) if mech == "few_train" else rng.uniform(1.5, 5.5)
        p["t0"] = t_first + rng.uniform(0.0, p["period"])
        p["impact"] = rng.uniform(0.0, 0.7)
        if mech == "variability_some_years":
            p["var_period"] = rng.uniform(0.3, 1.0)
            p["var_phase"] = rng.uniform(0.0, p["var_period"])
            p["var_amplitude_factor"] = rng.uniform(2.0, 4.0)
            p["var_absent_year"] = int(rng.choice([2018, 2019, 2020]))
    elif cls == "false_positive":
        p["period"] = rng.uniform(1.0, 5.5)
        p["t0"] = t_first + rng.uniform(0.0, p["period"])
        p["duration"] = rng.uniform(1.5, 4.0) / 24.0
        if mech == "blend":
            p["ingress_fraction"] = 0.15
            p["neighbor_distance_px"] = rng.uniform(1.5, 4.0)
            p["neighbor_angle"] = rng.uniform(0.0, 2.0 * math.pi)
            p["neighbor_ratio"] = rng.uniform(0.1, 0.5)
        else:
            p["ingress_fraction"] = rng.uniform(0.2, 0.5)
        if mech == "eb_secondary":
            p["secondary_fraction"] = rng.uniform(0.2, 0.4)
        if mech == "eb_odd_even":
            p["odd_factor"] = rng.uniform(0.6, 0.85)
        if mech == "variability_masked":
            p["var_period"] = rng.uniform(0.3, 1.0)
            p["var_phase"] = rng.uniform(0.0, p["var_period"])
            p["var_amplitude_factor"] = rng.uniform(2.0, 4.0)
    else:
        if mech == "trend_variability":
            p["var_period"] = rng.uniform(0.3, 5.0)
            p["var_phase"] = rng.uniform(0.0, p["var_period"])
            p["var_amplitude"] = rng.uniform(1000e-6, 4000e-6)
    if cls != "no_transit":
        variant = case["catalog_variant"]
        if variant == "neighbor":
            p["catalog_sep_arcsec"] = rng.uniform(5.0, 20.0)
            p["catalog_angle"] = rng.uniform(0.0, 2.0 * math.pi)
        elif variant == "independent":
            p["catalog_sep_arcsec"] = rng.uniform(0.0, 2.0)
            p["catalog_angle"] = rng.uniform(0.0, 2.0 * math.pi)
    return p


def _scene(synthetic, p):
    cx, cy = 5.0, 5.0
    d, a = p["neighbor_distance_px"], p["neighbor_angle"]
    return synthetic.Scene(
        neighbor_xy=(cx + d * math.cos(a), cy + d * math.sin(a)), neighbor_ratio=p["neighbor_ratio"]
    )


def _signal_spec(synthetic, case, p, depth):
    mech = case["mechanism"]
    return synthetic.SignalSpec(
        period=p["period"],
        t0=p["t0"],
        depth=depth,
        duration=p["duration"],
        ingress_fraction=p["ingress_fraction"],
        secondary_depth=depth * p["secondary_fraction"] if mech == "eb_secondary" else 0.0,
        odd_depth_factor=p["odd_factor"] if mech == "eb_odd_even" else 1.0,
    )


def _unit_deficit(synthetic, case, p, time, dilution):
    """Deficit of the catalogued signal on the target for depth 1 (secondary excluded)."""
    unit = synthetic.trapezoid(
        time, p["period"], p["t0"], 1.0, p["duration"], p["ingress_fraction"]
    )
    if case["mechanism"] == "eb_odd_even":
        epoch = np.round((time - p["t0"]) / p["period"]).astype(int)
        unit = np.where(epoch % 2 != 0, unit * p["odd_factor"], unit)
    return unit * dilution


def _place_in_band(synthetic, case, p, time, years, gate, hidden_min) -> tuple[str | None, dict]:
    """Depth from r (and, for planets, the geometry). Returns (redraw reason or None, SNR)."""
    dilution = 1.0
    if case["mechanism"] == "blend":
        c = synthetic.crowding(_scene(synthetic, p))
        dilution = (1.0 - c) / c
        p["dilution"] = dilution
    passes = 3 if case["class"] == "planet" else 1
    depth = 0.0
    profile: dict = {}
    for _ in range(passes):
        if case["class"] == "planet":
            k = math.sqrt(depth)
            p["duration"] = _planet_duration(p["period"], k, p["impact"])
            p["ingress_fraction"] = min(max(k / (1.0 - p["impact"] ** 2), 0.05), 0.5)
        epoch, inside = _transit_groups(time, p["period"], p["t0"], p["duration"])
        unit = _unit_deficit(synthetic, case, p, time, dilution)
        profile = snr_profile(time, years, unit, epoch, inside, case["noise"], gate, hidden_min)
        if profile["min_unit_ratio"] <= 0.0:
            return "no_transit_in_a_year", profile
        depth = p["r_target"] / profile["min_unit_ratio"]
    p["depth"] = depth
    r_actual = depth * profile["min_unit_ratio"]
    p["r_actual"] = r_actual
    lo, hi, _ = BANDS[case["band"]]
    if not (lo <= r_actual < hi or (case["band"] == "measurable" and r_actual >= lo)):
        return "band", profile
    limit = {"planet": DEPTH_LIMITS["planet"]}.get(case["class"], DEPTH_LIMITS["eclipse"])
    if case["mechanism"] == "blend":
        limit = DEPTH_LIMITS["neighbor"]
    if depth > limit:
        return "depth_limit", profile
    return None, profile


def _mechanism_condition(case, p, cadences) -> str | None:
    if case["mechanism"] == "few_train":
        t = cadences[0][1]
        n0 = math.ceil((t.min() - p["t0"]) / p["period"])
        n1 = math.floor((t.max() - p["t0"]) / p["period"])
        if n1 - n0 + 1 != case["extra"]["train_transits"]:
            return "train_transit_count"
    if case["mechanism"] == "variability_masked" and _commensurate(p["period"], p["var_period"]):
        return "commensurate_periods"
    return None


def _noise(rng, time_sector, noise):
    n = time_sector.size
    out = rng.normal(0.0, NOISE_PPM * 1e-6, n)
    if noise == "correlated":
        a = AR_PPM * 1e-6
        x0 = rng.normal(0.0, a)
        innov = rng.normal(0.0, 1.0, n)
        ar = np.empty(n)
        ar[0] = x0
        dt = np.diff(time_sector)
        phi = np.exp(-dt / AR_TAU_DAYS)
        scale = a * np.sqrt(1.0 - phi**2)
        for i in range(1, n):
            ar[i] = phi[i - 1] * ar[i - 1] + scale[i - 1] * innov[i]
        out = out + ar
    return out


def build_case(case: dict) -> tuple[bytes, dict]:
    """The canonical bytes of a case and its manifest entry (v0.2.0 helpers only)."""
    from refute.packs.tess import synthetic
    from refute.packs.tess.params import HoldoutParams, SnrParams
    from refute.packs.tess.types import (
        AuxData,
        LightCurveData,
        Neighbor,
        SectorInfo,
        btjd_to_year,
    )

    gate, hidden_min = SnrParams().min_snr, HoldoutParams().min_snr
    seed = int(case["seed"])
    redraws: dict[str, int] = {}
    layout = _layout(case["mechanism"], case["extra"])
    cadences = _sector_cadences(synthetic, layout)
    time = np.concatenate([t for _, t in cadences])
    years = np.concatenate([np.full(t.size, btjd_to_year(float(t.min()))) for _, t in cadences])
    profile: dict = {}
    for attempt in range(MAX_ATTEMPTS):
        seed_k = seed if attempt == 0 else sub_seed(seed, "redraw", attempt)
        p = draw_parameters(case, np.random.default_rng(seed_k), float(time.min()))
        reason = None
        if case["class"] != "no_transit":
            reason = _mechanism_condition(case, p, cadences)
            if reason is None:
                reason, profile = _place_in_band(synthetic, case, p, time, years, gate, hidden_min)
        if reason is None:
            break
        redraws[reason] = redraws.get(reason, 0) + 1
    else:
        raise RuntimeError(f"{case['id']}: no valid draw in {MAX_ATTEMPTS} attempts")
    if case["class"] != "no_transit" and "var_amplitude_factor" in p:
        p["var_amplitude"] = p["var_amplitude_factor"] * p["depth"]

    rng_noise = np.random.default_rng(sub_seed(seed_k, "noise"))
    star = synthetic.make_star(tic_id=TARGET_TIC)
    blend = case["mechanism"] == "blend"
    times, fluxes, errors, numbers, yrs, infos = [], [], [], [], [], []
    for number, t in cadences:
        year = btjd_to_year(float(t.min()))
        model = np.ones(t.size)
        if case["class"] != "no_transit" and not blend:
            model = synthetic.signal_model(t, _signal_spec(synthetic, case, p, p["depth"]))
        if case["mechanism"] != "pure_noise":
            model = model * (1.0 + TREND_AMPLITUDE * np.sin(2 * np.pi * t / TREND_PERIOD_DAYS))
        if "var_amplitude" in p and year != p.get("var_absent_year"):
            model = model + p["var_amplitude"] * np.sin(
                2 * np.pi * (t - p["var_phase"]) / p["var_period"]
            )
        flux = model + _noise(rng_noise, t, case["noise"])
        times.append(t)
        fluxes.append(flux)
        errors.append(np.full(t.size, NOISE_PPM * 1e-6))
        numbers.append(np.full(t.size, number))
        yrs.append(np.full(t.size, year))
        infos.append(
            SectorInfo(
                sector=number,
                year=year,
                t_start=float(t.min()),
                t_end=float(t.max()),
                n_points=int(t.size),
                filename=f"synthetic_sector_{number:02d}.npz",
            )
        )
    lc = LightCurveData(*(np.concatenate(x) for x in (times, fluxes, errors, numbers, yrs)))
    aux_seed = sub_seed(seed_k, "aux")
    if blend:
        scene = _scene(synthetic, p)
        rng_aux = np.random.default_rng(aux_seed)
        aperture = synthetic.scene_aperture(scene)
        c = synthetic.crowding(scene)
        neighbor_spec = synthetic.SignalSpec(
            period=p["period"],
            t0=p["t0"],
            depth=p["depth"],
            duration=p["duration"],
            ingress_fraction=0.15,
        )
        flux = np.empty(len(lc))
        pixels = []
        for sector in lc.sectors:
            sel = lc.sector == sector
            t = lc.time[sel]
            px = synthetic.render_pixels(
                int(sector),
                t,
                lc.flux[sel],
                scene,
                rng_aux,
                synthetic.signal_model(t, neighbor_spec),
            )
            ap = px.flux[:, aperture].sum(axis=1)
            ap = ap / np.median(ap)
            flux[sel] = (ap - (1.0 - c)) / c
            pixels.append(px)
        lc = LightCurveData(lc.time, flux, lc.flux_err, lc.sector, lc.year)
        sep = math.dist(scene.target_xy, scene.neighbor_xy) * synthetic.PIXEL_SCALE_ARCSEC
        aux = AuxData(
            sectors=synthetic.make_sector_aux(lc, c, rng_aux),
            pixels=pixels,
            neighbors=[
                Neighbor(
                    tic_id=NEIGHBOR_TIC,
                    tmag=10.0 - 2.5 * math.log10(p["neighbor_ratio"]),
                    separation_arcsec=sep,
                )
            ],
            neighbor_radius_arcsec=120.0,
        )
    else:
        aux = synthetic.make_aux(lc, seed=aux_seed)
    data = synthetic.make_data(lc, infos, star, tic_id=TARGET_TIC, aux=aux)

    catalog = None
    if case["class"] != "no_transit":
        catalog = _catalog(case, p, star)
    data_meta, arrays = data_to_parts(data)
    meta = {
        "serialization": SERIALIZATION,
        "case": {
            k: case[k]
            for k in (
                "id",
                "class",
                "band",
                "noise",
                "index",
                "mechanism",
                "catalog_variant",
                "seed",
                "extra",
            )
        },
        "attempt_seed": str(seed_k),
        "redraws": redraws,
        "parameters": p,
        "expected_snr": profile,
        "catalog": catalog,
        "data": data_meta,
    }
    blob = serialize(meta, arrays)
    entry = {
        **meta["case"],
        "attempt_seed": str(seed_k),
        "redraws": redraws,
        "parameters": plain(p),
        "expected_snr": plain(profile),
        "sha256": hashlib.sha256(blob).hexdigest(),
        "bytes": len(blob),
    }
    return blob, entry


def _catalog(case, p, star) -> dict:
    ra, dec = star.ra_deg, star.dec_deg
    period = p["period"]
    variant = case["catalog_variant"]
    if variant == "own":
        row = f"TESS-EB,TIC {TARGET_TIC} (1),{TARGET_TIC},{ra!r},{dec!r},{period!r}"
    else:
        sep, ang = p["catalog_sep_arcsec"], p["catalog_angle"]
        dec2 = dec + sep * math.cos(ang) / 3600.0
        ra2 = ra + sep * math.sin(ang) / 3600.0 / math.cos(math.radians(dec))
        if variant == "neighbor":
            row = f"TESS-EB,TIC {NEIGHBOR_TIC} (1),{NEIGHBOR_TIC},{ra2!r},{dec2!r},{period!r}"
        else:
            row = f"Gaia-DR3-EB,population {case['id']},,{ra2!r},{dec2!r},{period!r}"
    text = CATALOG_HEADER + "\n" + row + "\n"
    scan = {
        "format": "refute-eb-catalog-scan-1",
        "radius_arcsec": 120.0,
        "snapshots": [
            {
                "file": "population-catalog.csv",
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "rows": 1,
            }
        ],
        "per_target": {f"TIC-{TARGET_TIC}": {}},
    }
    return {"text": text, "scan": scan}


def generate_one(task: tuple[dict, str | None]) -> dict:
    """Build one case; write it to the cache unless ``cache`` is None (hash only)."""
    case, cache = task
    start = time.perf_counter()
    blob, entry = build_case(case)
    if cache is not None:
        path = Path(cache) / f"{case['id']}.rpc"
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(blob)
        os.replace(tmp, path)
    # Popped by mode_generate before the manifest is built: not part of the manifest.
    entry["_seconds"] = time.perf_counter() - start
    entry["_peak_memory_mb"] = peak_memory_mb()
    return entry


# --- environment ------------------------------------------------------------------------


def set_affinity(cpus: str | None) -> str:
    if not cpus:
        return "not set"
    lo, hi = (int(x) for x in cpus.split("-"))
    mask = sum(1 << i for i in range(lo, hi + 1))
    if sys.platform == "win32":
        k = ctypes.windll.kernel32
        k.GetCurrentProcess.restype = ctypes.c_void_p
        if not k.SetProcessAffinityMask(
            ctypes.c_void_p(k.GetCurrentProcess()), ctypes.c_size_t(mask)
        ):
            raise SystemExit(f"SetProcessAffinityMask failed: {ctypes.GetLastError()}")
    else:
        os.sched_setaffinity(0, set(range(lo, hi + 1)))
    return f"logical processors {lo}-{hi} (mask {mask:#x})"


def peak_memory_mb() -> float | None:
    if sys.platform == "win32":

        class Counters(ctypes.Structure):
            _fields_ = [
                (n, ctypes.c_size_t)
                for n in (
                    "cb",
                    "PageFaultCount",
                    "PeakWorkingSetSize",
                    "WorkingSetSize",
                    "QuotaPeakPagedPoolUsage",
                    "QuotaPagedPoolUsage",
                    "QuotaPeakNonPagedPoolUsage",
                    "QuotaNonPagedPoolUsage",
                    "PagefileUsage",
                    "PeakPagefileUsage",
                )
            ]

        c = Counters()
        c.cb = ctypes.sizeof(c)
        proc = ctypes.windll.kernel32.GetCurrentProcess()
        ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.c_void_p(proc), ctypes.byref(c), c.cb)
        return round(c.PeakWorkingSetSize / 1e6, 1)
    try:
        import resource

        return round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e3, 1)
    except ImportError:
        return None


def numeric_environment() -> dict:
    import numpy

    info = {
        "python": sys.version,
        "platform": platform.platform(),
        "numpy": numpy.__version__,
        "random_generator": "numpy.random.default_rng (PCG64)",
    }
    try:
        cfg = numpy.show_config(mode="dicts")
        info["numpy_blas"] = cfg["Build Dependencies"]["blas"]
    except Exception as exc:  # noqa: BLE001 - recorded, not hidden
        info["numpy_blas"] = f"unavailable: {exc}"
    try:
        from threadpoolctl import threadpool_info

        info["threadpools"] = [
            {k: t.get(k) for k in ("user_api", "internal_api", "version", "num_threads")}
            for t in threadpool_info()
        ]
    except ImportError:
        info["threadpools"] = "threadpoolctl unavailable"
    info["thread_env"] = {
        v: os.environ.get(v)
        for v in (
            "OMP_NUM_THREADS",
            "OPENBLAS_NUM_THREADS",
            "MKL_NUM_THREADS",
            "NUMEXPR_NUM_THREADS",
        )
    }
    return info


def refute_checkout() -> dict:
    import refute

    root = Path(refute.__file__).resolve().parents[2]
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True
    ).stdout.strip()
    dirty = subprocess.run(
        ["git", "-C", str(root), "status", "--porcelain", "--", "src"],
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {"refute_version": refute.__version__, "commit": head, "src_dirty": bool(dirty)}


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_new(path: Path, data: bytes) -> None:
    """Write a file that must not exist yet (results are never overwritten)."""
    with open(path, "xb") as fh:
        fh.write(data)


def _selected(cases: list[dict], cases_from: str | None) -> list[dict]:
    if not cases_from:
        return cases
    wanted = Path(cases_from).read_text(encoding="utf-8").split()
    by_id = {c["id"]: c for c in cases}
    missing = [w for w in wanted if w not in by_id]
    if missing:
        raise SystemExit(f"unknown case ids: {missing[:5]}")
    return [by_id[w] for w in wanted]


def _ordered(cases: list[dict], order: str) -> list[dict]:
    if order == "index":
        return cases
    if order == "reverse":
        return list(reversed(cases))
    if order.startswith("shuffle:"):
        rng = np.random.default_rng(int(order.split(":", 1)[1]))
        return [cases[i] for i in rng.permutation(len(cases))]
    raise SystemExit(f"unknown order {order}")


# --- modes ------------------------------------------------------------------------------


def mode_generate(args) -> int:
    from refute.core.runner import run_processes
    from refute.packs.tess import synthetic

    checkout = refute_checkout()
    # Recorded before run_processes: with one worker, init_worker() sets the thread
    # variables in this process, which would make the manifest depend on --workers.
    environment = numeric_environment()
    synth = Path(synthetic.__file__)
    if checkout["commit"] != GENERATOR_COMMIT or checkout["src_dirty"]:
        raise SystemExit(f"generate runs only at {GENERATOR_COMMIT} (clean src): {checkout}")
    if file_sha256(synth) != GENERATOR_SYNTHETIC_SHA256:
        raise SystemExit("synthetic.py is not the file of tag v0.2.0")
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    cases = _ordered(_selected(population_cases(args.population), args.cases_from), args.order)
    target = None if args.no_store else str(cache)
    started = time.perf_counter()
    entries = run_processes(generate_one, [(c, target) for c in cases], args.workers)
    wall = time.perf_counter() - started
    peaks = [e.pop("_peak_memory_mb") for e in entries]
    seconds = [e.pop("_seconds") for e in entries]
    entries = sorted(entries, key=lambda e: e["id"])
    manifest = {
        "format": MANIFEST_FORMAT,
        "serialization": SERIALIZATION,
        "population": args.population,
        "harness_sha256": file_sha256(HARNESS_PATH),
        "generator": {**checkout, "synthetic_py_sha256": GENERATOR_SYNTHETIC_SHA256},
        "environment": environment,
        "thresholds": {"snr_gate": 7.1, "hidden_min_snr": 5.0},
        "call_sequence": CALL_SEQUENCE,
        "cases": entries,
    }
    blob = canonical_json(manifest) + b"\n"
    print(
        f"cases generated: {len(entries)} ({'hash only' if args.no_store else 'stored'}); "
        f"wall {wall:.1f} s; per case {sum(seconds) / len(seconds):.2f} s mean, "
        f"{max(seconds):.2f} s max; peak worker memory {max(peaks)} MB; "
        f"bytes {sum(e['bytes'] for e in entries)}"
    )
    if args.check:
        frozen = json.loads(Path(args.check).read_text(encoding="utf-8"))
        frozen_by_id = {e["id"]: e for e in frozen["cases"]}
        diverged = [
            e["id"]
            for e in entries
            if canonical_json(e) != canonical_json(frozen_by_id.get(e["id"], {}))
        ]
        print(
            f"checked against {args.check}: {len(entries) - len(diverged)} identical, "
            f"{len(diverged)} diverged"
        )
        for d in diverged:
            print("  DIVERGED", d)
        return 2 if diverged else 0
    write_new(Path(args.manifest), blob)
    print(f"manifest {args.manifest}: SHA-256 {hashlib.sha256(blob).hexdigest()}")
    return 0


def _plan():
    from refute.packs.tess.params import TessTestPlan

    return TessTestPlan.model_validate(FAST_PLAN)


def _identity(found: float | None, injected: float) -> tuple[bool, float | None]:
    if found is None:
        return False, None
    for f in IDENTITY_FACTORS:
        if abs(found - f * injected) / (f * injected) <= PERIOD_TOLERANCE:
            return True, f
    return False, None


def _outcome(data, plan, entry, catalogs, scan) -> dict:
    from refute.packs.tess.calibration import signal_verdict
    from refute.packs.tess.pipeline import analyze_data, build_result

    try:
        analysis = analyze_data(data, plan, catalogs=catalogs, catalog_scan=scan)
        candidate = analysis.gauntlet.candidate
        period = entry["parameters"].get("period")
        target = {
            "key": data.target_key,
            "tic_id": data.tic_id,
            "kind": entry["class"],
            "name": entry["id"],
            "published": {"period_days": period},
            "source": {"name": "synthetic population"},
        }
        result = build_result(
            target, data, plan, analysis, {"pass_criteria": {"period_tolerance": PERIOD_TOLERANCE}}
        )
        identity, factor = (False, None)
        if period is not None:
            identity, factor = _identity(candidate.period if candidate else None, period)
        return {
            "status": "analyzed",
            "verdict": analysis.verdict,
            "verdict_reason": analysis.verdict_reason,
            "tests": [
                {"name": t.name, "status": t.status.value, "severity": t.severity.value}
                for t in analysis.tests
            ],
            "fatal": [
                t.name
                for t in analysis.tests
                if t.status.value == "FAIL" and t.severity.value == "fatal"
            ],
            "candidate_period": candidate.period if candidate else None,
            "signal_verdict_without_eb_catalog": signal_verdict(result, ["eb_catalog"]),
            "signal_identity": identity,
            "identity_factor": factor,
        }
    except Exception:  # noqa: BLE001 - an analysis error is a result, recorded in full
        return {"status": "error", "traceback": traceback.format_exc()}


def analyze_one(task: tuple[dict, str, str]) -> str:
    entry, cache, run_dir = task
    from refute.core.io import dumps_json

    start = time.perf_counter()

    out = Path(run_dir) / "cases" / f"{entry['id']}.json"
    if out.exists():
        return "kept"
    path = Path(cache) / f"{entry['id']}.rpc"
    record: dict = {
        "format": RESULT_FORMAT,
        "case": entry["id"],
        "expected_sha256": entry["sha256"],
    }
    if not path.is_file():
        record.update(status="refused", reason="input file missing from the cache")
    else:
        blob = path.read_bytes()
        digest = hashlib.sha256(blob).hexdigest()
        record["input_sha256"] = digest
        if digest != entry["sha256"]:
            record.update(
                status="refused", reason="input SHA-256 does not match the manifest; not analyzed"
            )
        else:
            meta, arrays = deserialize(blob)
            data = parts_to_data(meta, arrays)
            plan = _plan()
            conditions = {"i": _outcome(data, plan, entry, None, None)}
            if meta["catalog"] is not None:
                from refute.packs.tess.ebcatalog import parse_catalog

                entries = parse_catalog(meta["catalog"]["text"], "population-catalog.csv")
                conditions["ii"] = _outcome(data, plan, entry, entries, meta["catalog"]["scan"])
            record.update(status="analyzed", conditions=conditions)
    record["seconds"] = round(time.perf_counter() - start, 3)
    record["peak_memory_mb"] = peak_memory_mb()
    write_new(out, dumps_json(record).encode("utf-8"))
    return record["status"]


def mode_analyze(args) -> int:
    from refute.core.io import dumps_json
    from refute.core.runner import run_processes

    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_dir = Path(args.out)
    (run_dir / "cases").mkdir(parents=True, exist_ok=True)
    run = {
        "format": RESULT_FORMAT,
        "point": args.point,
        "checkout": refute_checkout(),
        "harness_sha256": file_sha256(HARNESS_PATH),
        "manifest_sha256": file_sha256(manifest_path),
        "plan": _plan().model_dump(mode="json"),
        "environment": numeric_environment(),
    }
    run_file = run_dir / "run.json"
    if run_file.exists():
        previous = json.loads(run_file.read_text(encoding="utf-8"))
        for key in ("point", "checkout", "harness_sha256", "manifest_sha256", "plan"):
            if previous[key] != json.loads(dumps_json(run[key])):
                raise SystemExit(f"resume refused: {key} differs from {run_file}")
    else:
        run["started_utc"] = datetime.now(UTC).isoformat(timespec="seconds")
        write_new(run_file, dumps_json(run).encode("utf-8"))
    entries = _selected(manifest["cases"], args.cases_from)
    todo = [e for e in entries if not (run_dir / "cases" / f"{e['id']}.json").exists()]
    print(
        f"{args.point}: {len(entries)} cases, {len(entries) - len(todo)} already done, "
        f"{len(todo)} to analyze"
    )
    statuses = run_processes(
        analyze_one, [(e, args.cache, str(run_dir)) for e in todo], args.workers
    )
    counts = {s: statuses.count(s) for s in sorted(set(statuses))}
    print(f"{args.point}: {counts}")
    return 0


# --- metrics ----------------------------------------------------------------------------


def cp_upper(k: int, n: int) -> float:
    from scipy.stats import beta

    return 1.0 if k >= n else float(beta.ppf(0.95, k + 1, n - k))


def cp_lower(k: int, n: int) -> float:
    from scipy.stats import beta

    return 0.0 if k <= 0 else float(beta.ppf(0.05, k, n - k + 1))


def _load_run(run_dir: Path) -> tuple[dict, dict[str, dict]]:
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    cases = {}
    for f in sorted((run_dir / "cases").glob("*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        cases[rec["case"]] = rec
    return run, cases


def _cond(rec: dict | None, condition: str) -> dict:
    if rec is None:
        return {"status": "missing"}
    if rec["status"] != "analyzed":
        return {"status": rec["status"]}
    return rec["conditions"].get(condition, {"status": "missing"})


def _outcomes(entry: dict, rec: dict | None, condition: str = "i") -> dict:
    o = _cond(rec, condition)
    ok = o.get("status") == "analyzed"
    verdict = o.get("verdict") if ok else None
    return {
        "error": not ok,
        "refuted": verdict == "REFUTED",
        "inconclusive": (verdict == "INCONCLUSIVE") or not ok,
        "false_alarm": verdict in ("SURVIVED", "WEAKENED"),
        "flagged_identity": ok
        and o.get("signal_verdict_without_eb_catalog") == "REFUTED"
        and bool(o.get("signal_identity")),
        "flagged_old": ok and o.get("signal_verdict_without_eb_catalog") == "REFUTED",
        "refuted_only_by_eb_catalog": ok
        and verdict == "REFUTED"
        and o.get("fatal") == ["eb_catalog"],
    }


def _rate(entries, key, recs, condition="i", kind="upper") -> dict:
    n = len(entries)
    k = sum(_outcomes(e, recs.get(e["id"]), condition)[key] for e in entries)
    out = {"k": k, "n": n, "rate": k / n if n else None}
    if n:
        out["bound"] = cp_upper(k, n) if kind == "upper" else cp_lower(k, n)
    return out


def run_metrics(manifest: dict, recs: dict[str, dict]) -> dict:
    cases = manifest["cases"]

    def sel(**kw):
        return [c for c in cases if all(c[k] == v for k, v in kw.items())]

    m: dict = {"criteria": {}, "by_mechanism": {}, "errors": {}}
    for noise in ("white", "correlated"):
        for band in ("below", "near", "measurable"):
            r = _rate(sel(**{"class": "planet", "band": band, "noise": noise}), "refuted", recs)
            r["passes"] = r["n"] > 0 and r["bound"] <= 0.10
            m["criteria"][f"C1 refuted planets, {band}, {noise}"] = r
        r = _rate(
            sel(**{"class": "false_positive", "band": "measurable", "noise": noise}),
            "flagged_identity",
            recs,
            kind="lower",
        )
        r["passes"] = r["n"] > 0 and r["bound"] >= 0.60
        m["criteria"][f"C2 flagged false positives, measurable, {noise}"] = r
        for cls in ("planet", "false_positive"):
            r = _rate(
                sel(**{"class": cls, "band": "measurable", "noise": noise}), "inconclusive", recs
            )
            r["passes"] = r["n"] > 0 and r["bound"] <= 0.20
            m["criteria"][f"C3 INCONCLUSIVE, {cls}, measurable, {noise}"] = r
        group = sel(**{"class": "no_transit", "noise": noise})
        r = _rate(group, "false_alarm", recs)
        r["passes"] = r["n"] > 0 and r["bound"] <= (0.01 if noise == "white" else 0.05)
        m["criteria"][f"C4 false alarm, {noise}"] = r
        own = [
            c for c in sel(**{"class": "planet", "noise": noise}) if c["catalog_variant"] == "own"
        ]
        k = sum(_outcomes(c, recs.get(c["id"]), "ii")["refuted_only_by_eb_catalog"] for c in own)
        m["criteria"][f"C5 planets refuted only by own-TIC eb_catalog, {noise}"] = {
            "k": k,
            "n": len(own),
            "passes": k == 0,
        }
    errors = [
        c["id"]
        for c in cases
        if any(
            _outcomes(c, recs.get(c["id"]), cond)["error"]
            for cond in (("i", "ii") if c["class"] != "no_transit" else ("i",))
        )
    ]
    m["criteria"]["C6 analysis errors and refused inputs"] = {
        "k": len(errors),
        "passes": not errors,
    }
    m["errors"] = errors
    for c in cases:
        key = f"{c['class']}|{c['band']}|{c['noise']}|{c['mechanism']}"
        o = _outcomes(c, recs.get(c["id"]))
        slot = m["by_mechanism"].setdefault(key, {"n": 0})
        slot["n"] += 1
        for name in ("refuted", "inconclusive", "false_alarm", "flagged_identity", "flagged_old"):
            slot[name] = slot.get(name, 0) + int(o[name])
    for slot in m["by_mechanism"].values():
        for name in ("refuted", "inconclusive", "false_alarm", "flagged_identity", "flagged_old"):
            slot[f"{name}_upper"] = cp_upper(slot[name], slot["n"])
            slot[f"{name}_lower"] = cp_lower(slot[name], slot["n"])
    return m


def paired(manifest: dict, a: dict[str, dict], b: dict[str, dict]) -> dict:
    from scipy.stats import binomtest

    out = {}
    for key, cls in (
        ("refuted", "planet"),
        ("flagged_identity", "false_positive"),
        ("inconclusive", None),
        ("false_alarm", "no_transit"),
    ):
        cases = [c for c in manifest["cases"] if cls is None or c["class"] == cls]
        changed_up, changed_down = [], []
        for c in cases:
            x = _outcomes(c, a.get(c["id"]))[key]
            y = _outcomes(c, b.get(c["id"]))[key]
            if x and not y:
                changed_down.append(c["id"])
            elif y and not x:
                changed_up.append(c["id"])
        n = len(cases)
        ka = sum(_outcomes(c, a.get(c["id"]))[key] for c in cases)
        kb = sum(_outcomes(c, b.get(c["id"]))[key] for c in cases)
        discordant = len(changed_up) + len(changed_down)
        p = binomtest(len(changed_up), discordant, 0.5).pvalue if discordant else 1.0
        out[key] = {
            "n": n,
            "rate_before": ka / n if n else None,
            "rate_after": kb / n if n else None,
            "difference": (kb - ka) / n if n else None,
            "became_true": changed_up,
            "became_false": changed_down,
            "mcnemar_exact_p": p,
        }
    return out


def mode_metrics(args) -> int:
    from refute.core.io import dumps_json

    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    runs = [_load_run(Path(r)) for r in args.runs]
    out = {
        "format": "refute-population-metrics/1",
        "manifest_sha256": file_sha256(Path(args.manifest)),
        "harness_sha256": file_sha256(HARNESS_PATH),
        "points": [],
        "paired": [],
    }
    for (run, recs), path in zip(runs, args.runs, strict=True):
        out["points"].append(
            {
                "point": run["point"],
                "run": Path(path).name,
                "checkout": run["checkout"],
                "metrics": run_metrics(manifest, recs),
            }
        )
    for (ra, a), (rb, b) in zip(runs, runs[1:], strict=False):
        out["paired"].append(
            {"from": ra["point"], "to": rb["point"], "comparisons": paired(manifest, a, b)}
        )
    target = Path(args.out)
    write_new(target, dumps_json(out).encode("utf-8"))
    lines = [f"# Population metrics ({Path(args.manifest).name})", ""]
    for point in out["points"]:
        lines += [
            f"## {point['point']} ({point['checkout']['commit'][:7]})",
            "",
            "| Criterion | k | n | bound | passes |",
            "|---|---|---|---|---|",
        ]
        for name, r in point["metrics"]["criteria"].items():
            bound = f"{r['bound']:.4f}" if "bound" in r else "-"
            lines.append(f"| {name} | {r['k']} | {r.get('n', '-')} | {bound} | {r['passes']} |")
        lines.append("")
    write_new(target.with_suffix(".md"), ("\n".join(lines) + "\n").encode("utf-8"))
    print(f"metrics written to {target} and {target.with_suffix('.md')}")
    return 0


# --- orchestration ----------------------------------------------------------------------


def mode_orchestrate(args) -> int:
    """Lots: regenerate and check, analyze at every point, check results, delete inputs."""
    project_cache = (Path(args.project) / ".cache" / "population").resolve()
    cache = Path(args.cache).resolve()
    if project_cache not in (cache, *cache.parents):
        raise SystemExit(f"the cache must be inside {project_cache}")
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    points = [p.split("=", 2) for p in args.point]  # name=python=run_dir
    ids = [c["id"] for c in manifest["cases"]]
    lots = [ids[i : i + args.lot_size] for i in range(0, len(ids), args.lot_size)]
    cache.mkdir(parents=True, exist_ok=True)
    log = Path(args.log)
    for n, lot in enumerate(lots):
        done = all((Path(r) / "cases" / f"{i}.json").exists() for _, _, r in points for i in lot)
        if done:
            continue
        lot_file = cache / f"lot-{n:04d}.txt"
        lot_file.write_text("\n".join(lot) + "\n", encoding="utf-8")
        gen = subprocess.run(
            [
                args.generator_python,
                str(HARNESS_PATH),
                "generate",
                "--population",
                manifest["population"],
                "--cache",
                str(cache),
                "--cases-from",
                str(lot_file),
                "--check",
                args.manifest,
                "--workers",
                str(args.workers),
                "--cpus",
                args.cpus or "",
            ]
        )
        if gen.returncode != 0:
            raise SystemExit(
                f"lot {n}: regeneration diverged or failed; stopped for "
                "investigation (nothing deleted)"
            )
        for name, python, run_dir in points:
            res = subprocess.run(
                [
                    python,
                    str(HARNESS_PATH),
                    "analyze",
                    "--manifest",
                    args.manifest,
                    "--cache",
                    str(cache),
                    "--out",
                    run_dir,
                    "--point",
                    name,
                    "--cases-from",
                    str(lot_file),
                    "--workers",
                    str(args.workers),
                    "--cpus",
                    args.cpus or "",
                ]
            )
            if res.returncode != 0:
                raise SystemExit(f"lot {n}: analyze failed at {name}; stopped")
        for _, _, run_dir in points:
            for i in lot:
                json.loads((Path(run_dir) / "cases" / f"{i}.json").read_text(encoding="utf-8"))
        for i in lot:
            f = (cache / f"{i}.rpc").resolve()
            if project_cache in f.parents and f.is_file():
                f.unlink()
        lot_file.unlink()
        with open(log, "a", encoding="utf-8") as fh:
            fh.write(
                f"{datetime.now(UTC).isoformat(timespec='seconds')} lot {n} done "
                f"({len(lot)} cases)\n"
            )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--population", required=True)
    g.add_argument("--cache", required=True)
    g.add_argument("--manifest")
    g.add_argument("--check")
    g.add_argument("--cases-from")
    g.add_argument("--order", default="index")
    g.add_argument("--no-store", action="store_true", help="hash only; write no case file")
    a = sub.add_parser("analyze")
    a.add_argument("--manifest", required=True)
    a.add_argument("--cache", required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--point", required=True)
    a.add_argument("--cases-from")
    m = sub.add_parser("metrics")
    m.add_argument("--manifest", required=True)
    m.add_argument("--runs", nargs="+", required=True)
    m.add_argument("--out", required=True)
    o = sub.add_parser("orchestrate")
    o.add_argument("--manifest", required=True)
    o.add_argument("--project", required=True)
    o.add_argument("--cache", required=True)
    o.add_argument("--generator-python", required=True)
    o.add_argument("--point", action="append", required=True)
    o.add_argument("--lot-size", type=int, default=50)
    o.add_argument("--log", required=True)
    for p in (g, a, o):
        p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 8))
    for p in (g, a, m, o):
        p.add_argument("--cpus", default="8-31")
    args = parser.parse_args(argv)
    if args.mode == "generate" and bool(args.manifest) == bool(args.check):
        parser.error("generate needs exactly one of --manifest (write) or --check (compare)")
    print(f"affinity: {set_affinity(args.cpus)}", flush=True)
    return {
        "generate": mode_generate,
        "analyze": mode_analyze,
        "metrics": mode_metrics,
        "orchestrate": mode_orchestrate,
    }[args.mode](args)


if __name__ == "__main__":
    sys.exit(main())
