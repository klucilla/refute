"""v0.2.1 synthetic population study harness.

Protocol: docs/validation/v0.2.1/population-study.md, with its Amendment 1 (inputs are
regenerated and checked by hash) and Amendment 2 (independent harness review). This
file is outside ``src/``: it is not part of the code hash of Refute, and it is never
edited after the first generation (a change is a new file with a new name).

Modes (``python population.py <mode> --help``):

- ``generate``: only in the environment of tag v0.2.0 (commit f479823). Builds every case
  of a population from its seed, writes its canonical serialization to a cache folder,
  and writes the manifest (or, with ``--check``, compares with a frozen manifest). It
  analyzes nothing.
- ``analyze``: in the environment of a measurement point named in ``points.json`` (next
  to this file). Refuses an unknown point, an installed Refute at another commit, a
  dirty ``src/``, a Refute that is not the editable install of the point's worktree,
  thread pools with more than one thread, and inputs missing from the cache or whose
  SHA-256 differs from the manifest; every refusal happens before any case is dispatched
  and is recorded as an attempt without results. Runs catalog conditions (i) and (ii)
  and writes one result file per case. Results are never overwritten; an interrupted run
  is resumed by running the same command again (only cases without a result are
  analyzed, with the same inputs, environment and harness).
- ``check-point``: the refusals of ``analyze`` that depend on the environment only (used
  by ``orchestrate`` before the first lot).
- ``metrics``: criteria C1-C6 with one-sided 95% Clopper-Pearson bounds and the overall
  approval, results by mechanism in both catalog conditions, redraws, the families whose
  point estimate is worse than their limit, and paired comparisons between points.
  Refuses runs whose provenance or integrity does not check.
- ``orchestrate``: the cycle by lot (regenerate, check, analyze at every point, check the
  results on disk, then delete the lot's inputs and lot files from the cache).

Errors (Amendment 2, N10): an exception of the analysis of a case is a permanent result
with status ``error``; it is published and investigated, and correcting it needs a new
attempt (a new harness or new code), never a replacement of the result. An
infrastructure failure (memory, operating system, interruption, an input missing from
the cache or with a different SHA-256) stops the run without writing a result for the
case; the attempt is recorded and may be resumed only for the cases without a result.

Only the interfaces listed in section 7 of the protocol are used. ``matching_factor``
and ``conclude_analysis`` are not used: signal identity is computed here.
"""

from __future__ import annotations

import os

# Amendment 2, N1: one thread in every numeric library, set before NumPy (or Refute, which
# imports it) is imported in this process. Spawned workers import this file first and
# inherit the environment, so the generator, every point and every worker run with
# single-threaded pools; threadpoolctl confirms it at run time (single_thread_problems).
THREAD_VARIABLES = (
    "OMP_NUM_THREADS",
    "OPENBLAS_NUM_THREADS",
    "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS",
)
INHERITED_THREAD_ENV = {_name: os.environ.get(_name) for _name in THREAD_VARIABLES}
for _name in THREAD_VARIABLES:
    os.environ[_name] = "1"

import argparse  # noqa: E402
import ctypes  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import platform  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import traceback  # noqa: E402
from dataclasses import asdict  # noqa: E402
from datetime import UTC, datetime  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

SERIALIZATION = "refute-population-serialization/1"
MAGIC = (SERIALIZATION + "\n").encode("ascii")
MANIFEST_FORMAT = "refute-population-manifest/1"
RESULT_FORMAT = "refute-population-result/2"
ATTEMPT_FORMAT = "refute-population-attempt/1"
POINTS_FORMAT = "refute-population-points/1"
METRICS_FORMAT = "refute-population-metrics/2"
GENERATOR_COMMIT = "f4798230f1bca607bcc0e98fe47711a26ec4ee59"
GENERATOR_SYNTHETIC_SHA256 = "b1d9518ea96ee3fd91b861c33601d57742ad96520b15079d97bd217f391fc50d"
HARNESS_PATH = Path(__file__).resolve()
POINTS_PATH = HARNESS_PATH.parent / "points.json"

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
    problems = single_thread_problems()
    if problems:
        raise RuntimeError(f"infrastructure: worker thread pools {problems}")
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
    entry["_worker"] = {"pid": os.getpid(), "threadpools": thread_pools()}
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


def thread_pools() -> list[dict] | str:
    """The thread pools of the loaded numeric libraries, as threadpoolctl reports them."""
    try:
        from threadpoolctl import threadpool_info
    except ImportError:
        return "threadpoolctl unavailable"
    return [
        {k: t.get(k) for k in ("user_api", "internal_api", "version", "num_threads")}
        for t in threadpool_info()
    ]


def single_thread_problems() -> list[str]:
    """Why this process does not run with single-threaded numeric pools (Amendment 2, N1);
    an empty list means every variable is 1 and every pool reported has 1 thread."""
    pools = thread_pools()
    if isinstance(pools, str):
        return [pools]
    problems = [f"{v}={os.environ.get(v)!r}" for v in THREAD_VARIABLES if os.environ.get(v) != "1"]
    if not pools:
        problems.append("threadpoolctl reports no thread pool")
    problems += [
        f"{p['internal_api']} pool has {p['num_threads']} threads"
        for p in pools
        if p.get("num_threads") != 1
    ]
    return problems


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
    info["threadpools"] = thread_pools()
    info["thread_env"] = {v: os.environ.get(v) for v in THREAD_VARIABLES}
    return info


def git(cwd: Path, *args: str) -> str:
    """Output of a read-only git command (empty if git fails)."""
    res = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else ""


def git_blob(cwd: Path, spec: str) -> bytes | None:
    """The bytes of ``<commit>:<path>``, or None if it does not exist."""
    res = subprocess.run(["git", "-C", str(cwd), "show", spec], capture_output=True)
    return res.stdout if res.returncode == 0 else None


def refute_checkout() -> dict:
    """The installed Refute: its commit, whether its ``src/`` is clean (tracked changes and
    untracked files both count), and whether it is the editable install of its worktree."""
    from importlib.metadata import distribution
    from urllib.parse import urlparse
    from urllib.request import url2pathname

    import refute

    root = Path(refute.__file__).resolve().parents[2]
    status = git(root, "status", "--porcelain", "--untracked-files=all", "--", "src")
    try:
        direct = json.loads(distribution("refute").read_text("direct_url.json") or "null")
    except Exception:  # noqa: BLE001 - recorded as "not an editable install"
        direct = None
    editable_root = None
    if isinstance(direct, dict) and (direct.get("dir_info") or {}).get("editable"):
        editable_root = str(Path(url2pathname(urlparse(direct["url"]).path)).resolve())
    return {
        "refute_version": refute.__version__,
        "commit": git(root, "rev-parse", "HEAD"),
        "src_dirty": bool(status),
        "src_status": status.splitlines(),
        "refute_root": str(root),
        "worktree_toplevel": str(Path(git(root, "rev-parse", "--show-toplevel")).resolve()),
        "editable_root": editable_root,
    }


def install_problems(checkout: dict) -> list[str]:
    """Refute must be the editable install of the worktree it is imported from, with a
    clean ``src/`` (Amendment 2, C1 and N10)."""
    problems = []
    if checkout["src_dirty"]:
        problems.append(f"src/ of the installed Refute is not clean: {checkout['src_status']}")
    if checkout["editable_root"] is None:
        problems.append("the installed Refute is not an editable install")
    elif checkout["editable_root"] != checkout["refute_root"]:
        problems.append(
            f"the editable install points to {checkout['editable_root']}, but Refute is "
            f"imported from {checkout['refute_root']}"
        )
    if checkout["worktree_toplevel"] != checkout["refute_root"]:
        problems.append(f"{checkout['refute_root']} is not the top of a git worktree")
    return problems


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def environment_fingerprint(checkout: dict) -> dict:
    """What must be identical between the start of a run and every resumption."""
    import refute

    env = numeric_environment()
    return {
        "python": env["python"],
        "numpy": env["numpy"],
        "numpy_blas": env["numpy_blas"],
        "threadpools": env["threadpools"],
        "thread_env": env["thread_env"],
        "commit": checkout["commit"],
        "refute_file": str(Path(refute.__file__).resolve()),
    }


# --- measurement points (Amendment 2, C1) -----------------------------------------------


def load_points(blob: bytes | None = None) -> list[dict]:
    """The entries of points.json (or of its bytes at some commit), checked."""
    data = json.loads(POINTS_PATH.read_bytes() if blob is None else blob)
    if data.get("format") != POINTS_FORMAT:
        raise SystemExit(f"points.json: format {data.get('format')!r}")
    points = data.get("points")
    if not isinstance(points, list):
        raise SystemExit("points.json: no list of points")
    names = [p.get("point") for p in points]
    if len(set(names)) != len(names):
        raise SystemExit("points.json: a point name appears twice")
    for p in points:
        c = p.get("commit", "")
        if not (isinstance(c, str) and len(c) == 40 and all(x in "0123456789abcdef" for x in c)):
            raise SystemExit(f"points.json: {p.get('point')} has no full commit hash")
    return points


def point_entry(points: list[dict], name: str) -> dict | None:
    return next((p for p in points if p["point"] == name), None)


def points_state() -> dict:
    """points.json now: its path in its repository, SHA-256, the repository's commit, and
    whether the file is committed there unchanged."""
    folder = POINTS_PATH.parent
    rel = git(folder, "ls-files", "--full-name", "--", POINTS_PATH.name)
    head = git(folder, "rev-parse", "HEAD")
    changed = git(folder, "status", "--porcelain", "--", POINTS_PATH.name)
    sha = file_sha256(POINTS_PATH)
    blob = git_blob(folder, f"{head}:{rel}") if rel and head else None
    committed = bool(rel) and not changed and blob is not None
    committed = committed and hashlib.sha256(blob).hexdigest() == sha
    return {"path": rel, "sha256": sha, "repository_commit": head, "committed": committed}


def binding_problems(name: str, checkout: dict) -> tuple[dict, dict, list[str]]:
    """The association used by a run (point and full commit), the state of points.json,
    and the reasons to refuse the point in this environment."""
    state = points_state()
    entry = point_entry(load_points(), name)
    problems = []
    if not state["committed"]:
        problems.append(
            "points.json is not committed unchanged in its repository (a point is "
            "committed before its measurement)"
        )
    if entry is None:
        problems.append(f"unknown point {name!r}: it is not in points.json")
    elif checkout["commit"] != entry["commit"]:
        problems.append(
            f"point {name} is commit {entry['commit']}, but the installed Refute is at "
            f"{checkout['commit']}"
        )
    problems += install_problems(checkout)
    problems += [f"thread pools: {p}" for p in single_thread_problems()]
    binding = {"point": name, "commit": entry["commit"] if entry else None}
    return binding, state, problems


def recorded_points_problems(state: dict, binding: dict, current: list[dict]) -> list[str]:
    """Checks a run's recorded points.json against git and the current file: the recorded
    bytes exist at the recorded commit, hold the run's association, and every recorded
    entry is unchanged in the current file (it only receives new points)."""
    blob = git_blob(POINTS_PATH.parent, f"{state.get('repository_commit')}:{state.get('path')}")
    if blob is None:
        return ["the recorded points.json is not found at the recorded repository commit"]
    if hashlib.sha256(blob).hexdigest() != state.get("sha256"):
        return ["the recorded points.json SHA-256 differs from the file at that commit"]
    recorded = load_points(blob)
    problems = []
    entry = point_entry(recorded, binding.get("point"))
    if entry is None or entry["commit"] != binding.get("commit"):
        problems.append("the recorded points.json does not hold the run's association")
    if current[: len(recorded)] != recorded:
        problems.append("points.json changed an entry that was already recorded")
    return problems


def write_atomic(path: Path, data: bytes, *, exclusive: bool = True) -> None:
    """Write ``data`` to a temporary file in the same folder and move it into place with
    ``os.replace``, so that no final file is ever written in parts. With ``exclusive``
    (the default) an existing final file is never replaced (results are never
    overwritten)."""
    path = Path(path)
    if exclusive and path.exists():
        raise FileExistsError(f"{path} exists; it is never overwritten")
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    if exclusive and path.exists():
        raise FileExistsError(f"{path} appeared while writing; left {tmp.name} in place")
    os.replace(tmp, path)


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
    environment = numeric_environment()
    synth = Path(synthetic.__file__)
    if checkout["commit"] != GENERATOR_COMMIT or install_problems(checkout):
        raise SystemExit(
            f"generate runs only at {GENERATOR_COMMIT} (clean src, editable install): "
            f"{checkout['commit']} {install_problems(checkout)}"
        )
    if file_sha256(synth) != GENERATOR_SYNTHETIC_SHA256:
        raise SystemExit("synthetic.py is not the file of tag v0.2.0")
    if single_thread_problems():
        raise SystemExit(f"thread pools are not single-threaded: {single_thread_problems()}")
    print(
        f"thread variables inherited {INHERITED_THREAD_ENV}, set to 1; main process pools "
        f"{[(p['internal_api'], p['num_threads']) for p in thread_pools()]}",
        flush=True,
    )
    cache = Path(args.cache)
    cache.mkdir(parents=True, exist_ok=True)
    cases = _ordered(_selected(population_cases(args.population), args.cases_from), args.order)
    target = None if args.no_store else str(cache)
    started = time.perf_counter()
    entries = run_processes(generate_one, [(c, target) for c in cases], args.workers)
    wall = time.perf_counter() - started
    peaks = [e.pop("_peak_memory_mb") for e in entries]
    seconds = [e.pop("_seconds") for e in entries]
    workers = {}
    for e in entries:
        w = e.pop("_worker")
        workers[w["pid"]] = sorted(
            {(p["internal_api"], p["num_threads"]) for p in w["threadpools"]}
        )
    print(
        f"worker thread pools: {len(workers)} process(es) "
        f"({'the main process' if set(workers) == {os.getpid()} else 'spawned'}), "
        f"pools {sorted({str(v) for v in workers.values()})}",
        flush=True,
    )
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
        if args.check_report:
            report = {
                "checked_against": args.check,
                "frozen_manifest_sha256": file_sha256(Path(args.check)),
                "cases": len(entries),
                "identical": len(entries) - len(diverged),
                "diverged": diverged,
                "stored": not args.no_store,
                "bytes": sum(e["bytes"] for e in entries),
            }
            write_atomic(Path(args.check_report), canonical_json(report) + b"\n")
        return 2 if diverged else 0
    write_atomic(Path(args.manifest), blob)
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


class InfrastructureError(RuntimeError):
    """An input missing from the cache or with a different SHA-256, or a failure of the
    machine: the run stops and no result is written for the case (Amendment 2, N10)."""


# Exceptions that stop a run instead of becoming a result (KeyboardInterrupt is not an
# Exception and always propagates).
INFRASTRUCTURE = (InfrastructureError, MemoryError, OSError)

CONDITION_KEYS = {
    "analyzed": (
        "verdict",
        "verdict_reason",
        "tests",
        "fatal",
        "candidate_period",
        "signal_verdict_without_eb_catalog",
        "signal_identity",
        "identity_factor",
    ),
    "error": ("traceback",),
}
RECORD_KEYS = ("attempt", "input_sha256", "seconds", "peak_memory_mb", "worker_environment")
CONTEXT_KEYS = ("point", "commit", "harness_sha256", "manifest_sha256")


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
    except INFRASTRUCTURE:
        raise
    except Exception:  # noqa: BLE001 - an analysis error is a permanent result, in full
        return {"status": "error", "traceback": traceback.format_exc()}


def validate_result(path: Path, entry: dict, ctx: dict) -> list[str]:
    """Problems of an existing result file; an empty list means it is valid and complete."""
    name = Path(path).name
    try:
        rec = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - any unreadable file is a problem to report
        return [f"{name}: not valid JSON ({type(exc).__name__}: {exc})"]
    problems = []
    if not isinstance(rec, dict):
        return [f"{name}: not a JSON object"]
    if rec.get("format") != RESULT_FORMAT:
        problems.append(f"{name}: format {rec.get('format')!r}")
    if rec.get("case") != entry["id"]:
        problems.append(f"{name}: case {rec.get('case')!r} is not {entry['id']}")
    if Path(path).stem != rec.get("case"):
        problems.append(f"{name}: the file name is not its case {rec.get('case')!r}")
    if rec.get("expected_sha256") != entry["sha256"]:
        problems.append(f"{name}: expected_sha256 differs from the manifest")
    if rec.get("input_sha256") != entry["sha256"]:
        problems.append(f"{name}: input_sha256 differs from the manifest")
    for key in CONTEXT_KEYS:
        if rec.get(key) != ctx[key]:
            problems.append(f"{name}: {key} {rec.get(key)!r} is not {ctx[key]!r}")
    for key in RECORD_KEYS:
        if key not in rec:
            problems.append(f"{name}: missing {key}")
    status = rec.get("status")
    if status == "analyzed":
        expected = {"i", "ii"} if entry["class"] != "no_transit" else {"i"}
        conditions = rec.get("conditions") or {}
        if set(conditions) != expected:
            problems.append(f"{name}: conditions {sorted(conditions)} are not {sorted(expected)}")
        for cond, o in conditions.items():
            keys = CONDITION_KEYS.get(o.get("status") if isinstance(o, dict) else None)
            if keys is None:
                problems.append(f"{name}: condition {cond} has status {o!r}")
            elif any(k not in o for k in keys):
                problems.append(f"{name}: condition {cond} is incomplete")
    elif status == "error":
        if "traceback" not in rec:
            problems.append(f"{name}: error without a traceback")
    else:
        problems.append(f"{name}: status {status!r}")
    return problems


def _worker_environment() -> dict:
    env = numeric_environment()
    return {"pid": os.getpid(), "threadpools": env["threadpools"], "thread_env": env["thread_env"]}


def analyze_one(task: tuple[dict, str, str, dict, str]) -> str:
    """Analyze one case and write its result. An infrastructure failure writes nothing and
    is raised as a RuntimeError (a built-in type, so it crosses the process boundary)."""
    entry, cache, run_dir, ctx, attempt_id = task
    try:
        return _analyze_one(entry, cache, run_dir, ctx, attempt_id)
    except INFRASTRUCTURE as exc:
        raise RuntimeError(
            f"infrastructure, {entry['id']}: {type(exc).__name__}: {exc}; no result written"
        ) from None


def _analyze_one(entry: dict, cache: str, run_dir: str, ctx: dict, attempt_id: str) -> str:
    from refute.core.io import dumps_json

    problems = single_thread_problems()
    if problems:
        raise InfrastructureError(f"worker thread pools {problems}")
    start = time.perf_counter()
    out = Path(run_dir) / "cases" / f"{entry['id']}.json"
    if out.exists():
        raise InfrastructureError("a result appeared after dispatch; it is never overwritten")
    path = Path(cache) / f"{entry['id']}.rpc"
    if not path.is_file():
        raise InfrastructureError("input file missing from the cache")
    blob = path.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != entry["sha256"]:
        raise InfrastructureError(
            f"input SHA-256 {digest} differs from the manifest {entry['sha256']}; "
            "stopped for investigation"
        )
    record: dict = {
        "format": RESULT_FORMAT,
        "case": entry["id"],
        "attempt": attempt_id,
        "expected_sha256": entry["sha256"],
        "input_sha256": digest,
        **{k: ctx[k] for k in CONTEXT_KEYS},
    }
    try:
        meta, arrays = deserialize(blob)
        data = parts_to_data(meta, arrays)
        plan = _plan()
        conditions = {"i": _outcome(data, plan, entry, None, None)}
        if meta["catalog"] is not None:
            from refute.packs.tess.ebcatalog import parse_catalog

            entries = parse_catalog(meta["catalog"]["text"], "population-catalog.csv")
            conditions["ii"] = _outcome(data, plan, entry, entries, meta["catalog"]["scan"])
        record.update(status="analyzed", conditions=conditions)
    except INFRASTRUCTURE:
        raise
    except Exception:  # noqa: BLE001 - a permanent result with status "error"
        record.update(status="error", traceback=traceback.format_exc())
    record["seconds"] = round(time.perf_counter() - start, 3)
    record["peak_memory_mb"] = peak_memory_mb()
    record["worker_environment"] = _worker_environment()
    write_atomic(out, dumps_json(record).encode("utf-8"))
    return record["status"]


def _attempt(run_dir: Path, attempt_id: str, kind: str, payload: dict) -> None:
    from refute.core.io import dumps_json

    folder = run_dir / "attempts"
    folder.mkdir(parents=True, exist_ok=True)
    record = {"format": ATTEMPT_FORMAT, "attempt": attempt_id, "kind": kind, **payload}
    write_atomic(folder / f"attempt-{attempt_id}-{kind}.json", dumps_json(record).encode("utf-8"))


def _run_context(run: dict) -> dict:
    return {
        "point": run["point"],
        "commit": run["checkout"]["commit"],
        "harness_sha256": run["harness_sha256"],
        "manifest_sha256": run["manifest_sha256"],
    }


RESUME_KEYS = (
    "point",
    "binding",
    "checkout",
    "harness_sha256",
    "manifest_sha256",
    "plan",
    "fingerprint",
)


def mode_check_point(args) -> int:
    checkout = refute_checkout()
    binding, state, problems = binding_problems(args.point, checkout)
    print(
        json.dumps(
            {"point": args.point, "installed_commit": checkout["commit"], "problems": problems}
        ),
        flush=True,
    )
    return 2 if problems else 0


def mode_analyze(args) -> int:
    from refute.core.io import dumps_json
    from refute.core.runner import run_processes

    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    attempt_id = f"{stamp}-{os.getpid()}"
    manifest_path = Path(args.manifest)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    run_dir = Path(args.out)
    cache = Path(args.cache)
    checkout = refute_checkout()
    fingerprint = environment_fingerprint(checkout)
    binding, state, problems = binding_problems(args.point, checkout)
    harness_sha = file_sha256(HARNESS_PATH)
    manifest_sha = file_sha256(manifest_path)
    attempt = {
        "started_utc": stamp,
        "argv": sys.argv[1:],
        "harness_sha256": harness_sha,
        "manifest_sha256": manifest_sha,
        "binding": binding,
        "points": state,
        "checkout": checkout,
        "fingerprint": fingerprint,
        "thread_env_inherited": INHERITED_THREAD_ENV,
    }

    def refuse(reason: str, details: list) -> None:
        """A refusal before dispatch: recorded for audit, with no results (C2)."""
        _attempt(
            run_dir,
            attempt_id,
            "refused",
            {
                **attempt,
                "dispatched": False,
                "results": "none",
                "reason": reason,
                "details": details,
            },
        )
        for d in details[:30]:
            print("  REFUSED", d, flush=True)
        raise SystemExit(f"{args.point}: refused before dispatch: {reason} (nothing analyzed)")

    if problems:
        refuse("the point cannot be measured in this environment", problems)
    (run_dir / "cases").mkdir(parents=True, exist_ok=True)
    run = {
        "format": RESULT_FORMAT,
        "point": args.point,
        "binding": binding,
        "points_at_start": state,
        "checkout": checkout,
        "harness_sha256": harness_sha,
        "manifest_sha256": manifest_sha,
        "plan": _plan().model_dump(mode="json"),
        "fingerprint": fingerprint,
        "environment": numeric_environment(),
    }
    run_file = run_dir / "run.json"
    if run_file.exists():
        previous = json.loads(run_file.read_text(encoding="utf-8"))
        differ = [k for k in RESUME_KEYS if previous.get(k) != json.loads(dumps_json(run[k]))]
        if differ:
            refuse("resume with a different run", [f"{k} differs from {run_file}" for k in differ])
        run = previous
    else:
        run["started_utc"] = stamp
        write_atomic(run_file, dumps_json(run).encode("utf-8"))
    ctx = _run_context(run)
    entries = _selected(manifest["cases"], args.cases_from)
    existing = [e for e in entries if (run_dir / "cases" / f"{e['id']}.json").exists()]
    invalid = [
        p for e in existing for p in validate_result(run_dir / "cases" / f"{e['id']}.json", e, ctx)
    ]
    if invalid:
        refuse("invalid existing results; stopped for investigation", invalid)
    todo = [e for e in entries if e not in existing]
    # C3: every pending input must exist and match the manifest before any dispatch.
    missing = [e["id"] for e in todo if not (cache / f"{e['id']}.rpc").is_file()]
    if missing:
        refuse("inputs missing from the cache; no result written", missing)
    diverged = []
    for e in todo:
        digest = file_sha256(cache / f"{e['id']}.rpc")
        if digest != e["sha256"]:
            diverged.append(f"{e['id']}: input {digest}, manifest {e['sha256']}")
    if diverged:
        refuse("input SHA-256 differs from the manifest; stopped for investigation", diverged)
    _attempt(
        run_dir,
        attempt_id,
        "started",
        {
            **attempt,
            "dispatched": True,
            "cases": len(entries),
            "already_valid": len(existing),
            "to_analyze": len(todo),
            "inputs_checked": len(todo),
        },
    )
    print(
        f"{args.point}: {len(entries)} cases, {len(existing)} already valid, {len(todo)} to "
        f"analyze (inputs present and checked by SHA-256)",
        flush=True,
    )
    try:
        statuses = run_processes(
            analyze_one,
            [(e, str(cache), str(run_dir), ctx, attempt_id) for e in todo],
            args.workers,
        )
    except BaseException as exc:
        written = []
        for f in sorted((run_dir / "cases").glob("*.json")):
            try:
                if json.loads(f.read_text(encoding="utf-8")).get("attempt") == attempt_id:
                    written.append(f.stem)
            except Exception:  # noqa: BLE001 - listed by the next validation, not here
                pass
        _attempt(
            run_dir,
            attempt_id,
            "interrupted",
            {
                "exception": f"{type(exc).__name__}: {exc}",
                "traceback": traceback.format_exc(),
                "results_written": written,
            },
        )
        raise SystemExit(
            f"{args.point}: interrupted ({type(exc).__name__}: {exc}); {len(written)} results "
            "written by this attempt are kept; resume only the cases without a result"
        ) from None
    counts = {s: statuses.count(s) for s in sorted(set(statuses))}
    _attempt(run_dir, attempt_id, "finished", {"counts": counts})
    print(f"{args.point}: {counts}", flush=True)
    return 0


# --- metrics ----------------------------------------------------------------------------


def cp_upper(k: int, n: int) -> float:
    from scipy.stats import beta

    return 1.0 if k >= n else float(beta.ppf(0.95, k + 1, n - k))


def cp_lower(k: int, n: int) -> float:
    from scipy.stats import beta

    return 0.0 if k <= 0 else float(beta.ppf(0.05, k, n - k + 1))


def _load_run(run_dir: Path, by_id: dict, points: list[dict]) -> dict:
    """A run with its case records, its attempts, and every provenance or integrity problem
    found in it (Amendment 2, C1, C2 and N8)."""
    name = run_dir.name
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    ctx = _run_context(run)
    problems = []
    binding = run.get("binding") or {}
    entry = point_entry(points, run.get("point"))
    if binding.get("point") != run.get("point"):
        problems.append(f"{name}: the binding's point is not the run's point")
    if entry is None:
        problems.append(f"{name}: point {run.get('point')!r} is not in points.json")
    elif binding.get("commit") != entry["commit"] or ctx["commit"] != entry["commit"]:
        problems.append(
            f"{name}: point {run.get('point')} is {entry['commit']} in points.json, but the "
            f"run's binding is {binding.get('commit')} and its checkout {ctx['commit']}"
        )
    problems += [f"{name}: {p}" for p in install_problems(run["checkout"])]
    if run.get("fingerprint", {}).get("commit") != ctx["commit"]:
        problems.append(f"{name}: fingerprint commit differs from the checkout commit")
    problems += [
        f"{name}: {p}"
        for p in recorded_points_problems(run.get("points_at_start") or {}, binding, points)
    ]
    attempts: dict[str, list[dict]] = {}
    for f in sorted((run_dir / "attempts").glob("attempt-*.json")):
        a = json.loads(f.read_text(encoding="utf-8"))
        attempts.setdefault(a.get("attempt"), []).append(a)
    dispatched, refused = set(), []
    for attempt_id, recs in sorted(attempts.items()):
        kinds = sorted(a["kind"] for a in recs)
        if "started" in kinds:
            dispatched.add(attempt_id)
            start = next(a for a in recs if a["kind"] == "started")
            for key, want in (
                ("fingerprint", run["fingerprint"]),
                ("binding", binding),
                ("checkout", run["checkout"]),
                ("harness_sha256", run["harness_sha256"]),
                ("manifest_sha256", run["manifest_sha256"]),
            ):
                if start.get(key) != want:
                    problems.append(f"{name}/attempt {attempt_id}: {key} differs from the run")
        elif kinds == ["refused"]:
            a = recs[0]
            refused.append(
                {
                    "attempt": attempt_id,
                    "results": a.get("results"),
                    "reason": a.get("reason"),
                    "installed_commit": (a.get("checkout") or {}).get("commit"),
                    "point_requested": (a.get("binding") or {}).get("point"),
                }
            )
        else:
            problems.append(f"{name}/attempt {attempt_id}: records {kinds} without a start")
    cases: dict[str, dict] = {}
    files: dict[str, str] = {}
    for f in sorted((run_dir / "cases").glob("*.json")):
        try:
            rec = json.loads(f.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - reported as a problem
            problems.append(f"{name}/{f.name}: not valid JSON ({type(exc).__name__})")
            continue
        case = rec.get("case") if isinstance(rec, dict) else None
        if case not in by_id:
            problems.append(f"{name}/{f.name}: case {case!r} is not in the manifest")
            continue
        problems += [f"{name}/{p}" for p in validate_result(f, by_id[case], ctx)]
        if rec.get("attempt") not in dispatched:
            problems.append(f"{name}/{f.name}: attempt {rec.get('attempt')!r} was not dispatched")
        if case in cases:
            problems.append(f"{name}/{f.name}: case id {case} appears twice in the run")
        cases[case] = rec
        files[case] = file_sha256(f)
    return {
        "path": run_dir,
        "run": run,
        "cases": cases,
        "files": files,
        "refused_attempts": refused,
        "dispatched_attempts": sorted(dispatched),
        "problems": problems,
    }


def _cond(rec: dict | None, condition: str) -> dict:
    if rec is None:
        return {"status": "missing"}
    if rec["status"] != "analyzed":
        return {"status": rec["status"]}
    return rec["conditions"].get(condition, {"status": "missing"})


def _outcomes(entry: dict, rec: dict | None, condition: str = "i") -> dict:
    """Outcomes of one case. An error or missing result is never a successful analysis: it
    stays in every denominator, counts as an error (C6) and as INCONCLUSIVE (C3), and never
    as refuted, flagged or a false alarm."""
    o = _cond(rec, condition)
    ok = o.get("status") == "analyzed"
    verdict = o.get("verdict") if ok else None
    return {
        "status": o.get("status"),
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


OUTCOME_NAMES = (
    "refuted",
    "inconclusive",
    "false_alarm",
    "flagged_identity",
    "flagged_old",
    "refuted_only_by_eb_catalog",
)


def _conditions(case: dict) -> tuple[str, ...]:
    return ("i", "ii") if case["class"] != "no_transit" else ("i",)


def _family_limits(cls: str, band: str | None, noise: str) -> list[tuple[str, str, str, float]]:
    """(criterion, outcome, direction, limit) of the criteria a family of condition (i)
    falls under; the families of the other bands of C2 have no limit."""
    out = []
    if cls == "planet":
        out.append(("C1", "refuted", "above", 0.10))
    if cls == "false_positive" and band == "measurable":
        out.append(("C2", "flagged_identity", "below", 0.60))
    if cls in ("planet", "false_positive") and band == "measurable":
        out.append(("C3", "inconclusive", "above", 0.20))
    if cls == "no_transit":
        out.append(("C4", "false_alarm", "above", 0.01 if noise == "white" else 0.05))
    return out


def run_metrics(manifest: dict, recs: dict[str, dict]) -> dict:
    cases = manifest["cases"]

    def sel(**kw):
        return [c for c in cases if all(c[k] == v for k, v in kw.items())]

    m: dict = {
        "criteria": {},
        "approval": {},
        "by_mechanism": {"i": {}, "ii": {}},
        "named_families": [],
        "errors": [],
        "status_counts": {},
    }
    for c in cases:
        for cond in _conditions(c):
            s = _outcomes(c, recs.get(c["id"]), cond)["status"]
            m["status_counts"][s] = m["status_counts"].get(s, 0) + 1
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
        if any(_outcomes(c, recs.get(c["id"]), cond)["error"] for cond in _conditions(c))
    ]
    m["criteria"]["C6 analysis errors and missing results"] = {
        "k": len(errors),
        "passes": not errors,
    }
    m["errors"] = errors
    failed = [name for name, r in m["criteria"].items() if not r["passes"]]
    m["approval"] = {
        "passes": not failed,
        "failed": failed,
        "rule": "The study is approved only if every criterion passes, C6 included. A "
        "rate can meet its limit while the study fails.",
    }
    for c in cases:
        for cond in _conditions(c):
            key = f"{c['class']}|{c['band']}|{c['noise']}|{c['mechanism']}"
            if cond == "ii":
                key += f"|{c['catalog_variant']}"
            o = _outcomes(c, recs.get(c["id"]), cond)
            slot = m["by_mechanism"][cond].setdefault(key, {"n": 0})
            slot["n"] += 1
            for name in OUTCOME_NAMES:
                slot[name] = slot.get(name, 0) + int(o[name])
    for cond, slots in m["by_mechanism"].items():
        for key, slot in slots.items():
            for name in OUTCOME_NAMES:
                slot[f"{name}_upper"] = cp_upper(slot[name], slot["n"])
                slot[f"{name}_lower"] = cp_lower(slot[name], slot["n"])
            cls, band, noise = key.split("|")[:3]
            band = None if band == "None" else band
            limits = _family_limits(cls, band, noise) if cond == "i" else []
            if cond == "ii" and cls == "planet" and key.endswith("|own"):
                limits = [("C5", "refuted_only_by_eb_catalog", "above", 0.0)]
            for criterion, outcome, direction, limit in limits:
                estimate = slot[outcome] / slot["n"]
                worse = estimate > limit if direction == "above" else estimate < limit
                if worse:
                    m["named_families"].append(
                        {
                            "condition": cond,
                            "family": key,
                            "criterion": criterion,
                            "outcome": outcome,
                            "estimate": estimate,
                            "k": slot[outcome],
                            "n": slot["n"],
                            "limit": limit,
                        }
                    )
    return m


def redraw_summary(manifest: dict) -> dict:
    """Redraws aggregated by class, band and mechanism (both noise models together)."""
    out: dict = {}
    for c in manifest["cases"]:
        key = f"{c['class']}|{c['band'] or 'none'}|{c['mechanism']}"
        slot = out.setdefault(key, {"cases": 0, "cases_redrawn": 0, "redraws": {}})
        slot["cases"] += 1
        slot["cases_redrawn"] += int(bool(c["redraws"]))
        for reason, n in c["redraws"].items():
            slot["redraws"][reason] = slot["redraws"].get(reason, 0) + n
    return out


PAIRED = (
    ("refuted", "planet"),
    ("flagged_identity", "false_positive"),
    ("flagged_old", "false_positive"),
    ("inconclusive", "planet"),
    ("inconclusive", "false_positive"),
    ("inconclusive", "no_transit"),
    ("false_alarm", "no_transit"),
)


def _paired_group(cases, a, b, key, cond) -> dict:
    from scipy.stats import binomtest

    up, down = [], []
    for c in cases:
        x = _outcomes(c, a.get(c["id"]), cond)[key]
        y = _outcomes(c, b.get(c["id"]), cond)[key]
        if x and not y:
            down.append(c["id"])
        elif y and not x:
            up.append(c["id"])
    n = len(cases)
    ka = sum(_outcomes(c, a.get(c["id"]), cond)[key] for c in cases)
    kb = sum(_outcomes(c, b.get(c["id"]), cond)[key] for c in cases)
    discordant = len(up) + len(down)
    return {
        "n": n,
        "rate_before": ka / n if n else None,
        "rate_after": kb / n if n else None,
        "difference": (kb - ka) / n if n else None,
        "became_true": up,
        "became_false": down,
        "mcnemar_exact_p": binomtest(len(up), discordant, 0.5).pvalue if discordant else 1.0,
    }


def paired(manifest: dict, a: dict[str, dict], b: dict[str, dict]) -> dict:
    """McNemar comparisons by band and noise model in conditions (i) and (ii), and in (ii)
    also by catalog variant; the aggregates are additional information only."""
    out: dict = {"i": {}, "ii": {}, "ii_by_catalog_variant": {}, "aggregate": {"i": {}, "ii": {}}}
    for cond in ("i", "ii"):
        for key, cls in PAIRED:
            if cond == "ii" and cls == "no_transit":
                continue
            label = f"{key} | {cls}"
            group = [c for c in manifest["cases"] if c["class"] == cls]
            out["aggregate"][cond][label] = _paired_group(group, a, b, key, cond)
            by: dict[str, list] = {}
            by_variant: dict[str, list] = {}
            for c in group:
                by.setdefault(f"{c['noise']}|{c['band'] or 'none'}", []).append(c)
                v = f"{c['noise']}|{c['band'] or 'none'}|{c['catalog_variant']}"
                by_variant.setdefault(v, []).append(c)
            out[cond][label] = {g: _paired_group(cs, a, b, key, cond) for g, cs in by.items()}
            if cond == "ii":
                out["ii_by_catalog_variant"][label] = {
                    g: _paired_group(cs, a, b, key, cond) for g, cs in by_variant.items()
                }
    return out


def _reread_records(folders: list[str]) -> tuple[dict[str, str], list[str], list[str]]:
    """``run/case -> SHA-256`` from the results-reread records of orchestrate."""
    hashes: dict[str, str] = {}
    files, problems = [], []
    for folder in folders:
        for f in sorted(Path(folder).glob("lot-*-3-results-reread.json")):
            files.append(str(f))
            for key, sha in json.loads(f.read_text(encoding="utf-8"))["results_sha256"].items():
                if hashes.get(key, sha) != sha:
                    problems.append(f"{key}: two records give different SHA-256")
                hashes[key] = sha
    return hashes, files, problems


def _fmt(x) -> str:
    return "-" if x is None else f"{x:.4f}"


def mode_metrics(args) -> int:
    from refute.core.io import dumps_json

    target = Path(args.out)
    if target.exists() or target.with_suffix(".md").exists():
        raise SystemExit(f"{target} (or its .md) exists; nothing computed")
    target.parent.mkdir(parents=True, exist_ok=True)
    manifest_sha = file_sha256(Path(args.manifest))
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in manifest["cases"]}
    points = load_points()
    names = [Path(r).name for r in args.runs]
    if len(set(names)) != len(names):
        raise SystemExit("two runs have the same folder name; nothing computed")
    loaded = [_load_run(Path(r), by_id, points) for r in args.runs]
    problems = [p for x in loaded for p in x["problems"]]
    for x in loaded:
        if x["run"]["manifest_sha256"] != manifest_sha:
            problems.append(
                f"{x['path'].name}: manifest {x['run']['manifest_sha256'][:12]} is not "
                f"{manifest_sha[:12]}"
            )
    harnesses = {x["run"]["harness_sha256"] for x in loaded}
    if len(harnesses) > 1:
        problems.append(
            f"runs come from {len(harnesses)} different harnesses: "
            f"{sorted(h[:12] for h in harnesses)}"
        )
    record_hashes, record_files, record_problems = _reread_records(args.records or [])
    problems += record_problems
    if args.records:
        for x in loaded:
            for case, sha in x["files"].items():
                key = f"{x['path'].name}/{case}"
                if key not in record_hashes:
                    problems.append(f"{key}: not in any results-reread record")
                elif record_hashes[key] != sha:
                    problems.append(f"{key}: SHA-256 differs from the results-reread record")
    by_point: dict[str, dict[str, dict]] = {}
    order: list[str] = []
    for x in loaded:
        point = x["run"]["point"]
        if point not in order:
            order.append(point)
        merged = by_point.setdefault(point, {})
        repeated = sorted(set(merged) & set(x["cases"]))
        if repeated:
            problems.append(
                f"{x['path'].name}: {len(repeated)} case ids repeated within point {point}"
            )
        merged.update(x["cases"])
    for point in order:
        group = [x for x in loaded if x["run"]["point"] == point]
        for key in ("checkout", "manifest_sha256", "harness_sha256", "plan", "fingerprint"):
            if any(x["run"][key] != group[0]["run"][key] for x in group[1:]):
                problems.append(f"runs of point {point} are not compatible: {key} differs")
    if problems:
        for p in problems[:30]:
            print("  REFUSED", p)
        print(f"metrics refused: {len(problems)} provenance problem(s); nothing computed")
        return 2
    out = {
        "format": METRICS_FORMAT,
        "manifest_sha256": manifest_sha,
        "harness_sha256": file_sha256(HARNESS_PATH),
        "run_harness_sha256": sorted(harnesses)[0],
        "points_sha256": file_sha256(POINTS_PATH),
        "results_checked_against_records": bool(args.records),
        "records": record_files,
        "redraws": redraw_summary(manifest),
        "points": [],
        "paired": [],
    }
    for point in order:
        group = [x for x in loaded if x["run"]["point"] == point]
        out["points"].append(
            {
                "point": point,
                "binding": group[0]["run"]["binding"],
                "runs": [x["path"].name for x in group],
                "checkout": group[0]["run"]["checkout"],
                "refused_attempts": {x["path"].name: x["refused_attempts"] for x in group},
                "metrics": run_metrics(manifest, by_point[point]),
            }
        )
    for pa, pb in zip(order, order[1:], strict=False):
        out["paired"].append(
            {"from": pa, "to": pb, "comparisons": paired(manifest, by_point[pa], by_point[pb])}
        )
    write_atomic(target, dumps_json(out).encode("utf-8"))
    write_atomic(target.with_suffix(".md"), metrics_markdown(out, args.manifest).encode("utf-8"))
    print(f"metrics written to {target} and {target.with_suffix('.md')}")
    return 0


def metrics_markdown(out: dict, manifest_name: str) -> str:
    lines = [
        f"# Population metrics ({Path(manifest_name).name})",
        "",
        "Results checked against the orchestrate records: "
        f"{out['results_checked_against_records']}.",
        "",
        "Every point uses the fast plan of the test suite (section 7); false-alarm rates "
        "under the calibration plan could be higher. The SNR bands of blends use the "
        "expected SNR without the noise of the pixel data, which lowers the SNR of the "
        "analyzed light curve (Amendment 2, N2).",
        "",
    ]
    for point in out["points"]:
        m = point["metrics"]
        a = m["approval"]
        lines += [
            f"## {point['point']} ({point['binding']['commit']})",
            "",
            f"**Overall approval: {'PASSES' if a['passes'] else 'FAILS'}.** {a['rule']}"
            + (f" Failed: {', '.join(a['failed'])}." if a["failed"] else ""),
            "",
            f"Result statuses (per condition): {m['status_counts']}",
            "",
            "| Criterion | k | n | rate | bound | passes |",
            "|---|---|---|---|---|---|",
        ]
        for name, r in m["criteria"].items():
            lines.append(
                f"| {name} | {r['k']} | {r.get('n', '-')} | {_fmt(r.get('rate'))} | "
                f"{_fmt(r.get('bound'))} | {r['passes']} |"
            )
        lines += ["", "Families whose point estimate is worse than their limit:", ""]
        if m["named_families"]:
            lines += ["| Condition | Family | Criterion | k / n | estimate | limit |"]
            lines += ["|---|---|---|---|---|---|"]
            for f in m["named_families"]:
                lines.append(
                    f"| {f['condition']} | {f['family']} | {f['criterion']} ({f['outcome']}) | "
                    f"{f['k']} / {f['n']} | {f['estimate']:.4f} | {f['limit']} |"
                )
        else:
            lines.append("none")
        for cond in ("i", "ii"):
            lines += [
                "",
                f"Results by mechanism, condition ({cond}):",
                "",
                "| Family | n | refuted | inconclusive | false alarm | flagged (identity) | "
                "flagged (old) | refuted only by eb_catalog |",
                "|---|---|---|---|---|---|---|---|",
            ]
            for key, s in sorted(m["by_mechanism"][cond].items()):
                lines.append(
                    f"| {key} | {s['n']} | {s['refuted']} | {s['inconclusive']} | "
                    f"{s['false_alarm']} | {s['flagged_identity']} | {s['flagged_old']} | "
                    f"{s['refuted_only_by_eb_catalog']} |"
                )
        refused = {k: v for k, v in point["refused_attempts"].items() if v}
        lines += ["", f"Attempts refused before dispatch (no results): {refused or 'none'}", ""]
    lines += [
        "## Redraws by class, band and mechanism",
        "",
        "| Family | cases | redrawn | redraws |",
    ]
    lines += ["|---|---|---|---|"]
    for key, s in sorted(out["redraws"].items()):
        lines.append(f"| {key} | {s['cases']} | {s['cases_redrawn']} | {s['redraws']} |")
    for p in out["paired"]:
        lines += [
            "",
            f"## Paired comparisons {p['from']} -> {p['to']}",
            "",
            "| Condition | Outcome | Group | n | before | after | difference | up | down | "
            "McNemar p |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ]
        c = p["comparisons"]
        sections = [("i", c["i"]), ("ii", c["ii"]), ("ii by variant", c["ii_by_catalog_variant"])]
        sections += [(f"{k} (aggregate, additional)", v) for k, v in c["aggregate"].items()]
        for cond, block in sections:
            for label, groups in block.items():
                items = groups.items() if "n" not in groups else [("all", groups)]
                for g, r in sorted(items):
                    lines.append(
                        f"| {cond} | {label} | {g} | {r['n']} | {_fmt(r['rate_before'])} | "
                        f"{_fmt(r['rate_after'])} | {_fmt(r['difference'])} | "
                        f"{len(r['became_true'])} | {len(r['became_false'])} | "
                        f"{r['mcnemar_exact_p']:.4g} |"
                    )
    return "\n".join(lines) + "\n"


# --- orchestration ----------------------------------------------------------------------


def _lot_results(points, lot, by_id) -> tuple[bool, list[str], dict]:
    """Whether every case of a lot has a valid result at every point, the problems of the
    results that exist, and the SHA-256 of every result file read."""
    complete, problems, hashes = True, [], {}
    for _, _, run_dir in points:
        run_file = Path(run_dir) / "run.json"
        if not run_file.exists():
            complete = False
            continue
        ctx = _run_context(json.loads(run_file.read_text(encoding="utf-8")))
        for i in lot:
            f = Path(run_dir) / "cases" / f"{i}.json"
            if not f.exists():
                complete = False
                continue
            found = validate_result(f, by_id[i], ctx)
            problems += [f"{Path(run_dir).name}: {p}" for p in found]
            hashes[f"{Path(run_dir).name}/{i}"] = file_sha256(f)
    return complete and not problems, problems, hashes


def mode_orchestrate(args) -> int:
    """Lots: regenerate and check, analyze at every point, re-read and validate the results
    on disk, record that, then delete the lot's inputs and lot files (only inside
    .cache/population/ of the harness's repository)."""
    from refute.core.io import dumps_json

    project = Path(args.project).resolve()
    top = Path(git(HARNESS_PATH.parent, "rev-parse", "--show-toplevel") or "/").resolve()
    if project != top:
        raise SystemExit(f"--project must be the top of the harness's repository ({top})")
    project_cache = (project / ".cache" / "population").resolve()
    cache = Path(args.cache).resolve()
    if project_cache not in (cache, *cache.parents):
        raise SystemExit(f"the cache must be inside {project_cache}")
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    by_id = {c["id"]: c for c in manifest["cases"]}
    points = [p.split("=", 2) for p in args.point]  # name=python=run_dir
    ids = [c["id"] for c in manifest["cases"]]
    lots = [ids[i : i + args.lot_size] for i in range(0, len(ids), args.lot_size)]
    child_env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    for name, python, _ in points:
        res = subprocess.run(
            [python, str(HARNESS_PATH), "check-point", "--point", name, "--cpus", args.cpus or ""],
            env=child_env,
        )
        if res.returncode != 0:
            raise SystemExit(f"point {name} refused before the first lot; nothing ran")
    cache.mkdir(parents=True, exist_ok=True)
    records = Path(args.records)
    records.mkdir(parents=True, exist_ok=True)

    def now():
        return datetime.now(UTC).isoformat(timespec="microseconds")

    def record(name, payload):
        write_atomic(records / name, dumps_json(payload).encode("utf-8"))

    def remove(f: Path) -> str | None:
        if f.is_symlink():
            return None
        f = f.resolve()
        if project_cache in f.parents and f.is_file():
            f.unlink()
            return f.name
        return None

    for n, lot in enumerate(lots):
        complete, problems, _ = _lot_results(points, lot, by_id)
        if problems:
            for p in problems[:20]:
                print("  INVALID", p, flush=True)
            raise SystemExit(
                f"lot {n}: invalid results; stopped for investigation "
                "(nothing overwritten, deleted or redone)"
            )
        if complete:
            print(f"lot {n}: every result present and valid at every point; skipped", flush=True)
            continue
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        prefix = f"lot-{n:04d}-{stamp}"
        lot_file = cache / f"{prefix}.txt"
        report_file = cache / f"{prefix}-check.json"
        write_atomic(lot_file, ("\n".join(lot) + "\n").encode("utf-8"))
        record(f"{prefix}-1-started.json", {"lot": n, "cases": lot, "utc": now()})
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
                "--check-report",
                str(report_file),
                "--workers",
                str(args.workers),
                "--cpus",
                args.cpus or "",
            ],
            env=child_env,
        )
        check = json.loads(report_file.read_text("utf-8")) if report_file.is_file() else None
        if gen.returncode != 0:
            record(
                f"{prefix}-2-regeneration-stopped.json",
                {"lot": n, "utc": now(), "returncode": gen.returncode, "check": check},
            )
            raise SystemExit(
                f"lot {n}: regeneration diverged or failed; stopped for "
                "investigation (nothing deleted)"
            )
        record(f"{prefix}-2-regenerated.json", {"lot": n, "utc": now(), "check": check})
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
                ],
                env=child_env,
            )
            if res.returncode != 0:
                record(
                    f"{prefix}-analysis-stopped.json",
                    {"lot": n, "utc": now(), "point": name, "returncode": res.returncode},
                )
                raise SystemExit(f"lot {n}: analyze stopped at {name}; stopped (nothing deleted)")
        complete, problems, hashes = _lot_results(points, lot, by_id)
        if problems or not complete:
            raise SystemExit(
                f"lot {n}: results incomplete or invalid after analysis; stopped (nothing deleted)"
            )
        record(
            f"{prefix}-3-results-reread.json", {"lot": n, "utc": now(), "results_sha256": hashes}
        )
        deleted = [d for d in (remove(cache / f"{i}.rpc") for i in lot) if d]
        # This lot's list and check report, and those left by its interrupted attempts.
        own = {*cache.glob(f"lot-{n:04d}-*.txt"), *cache.glob(f"lot-{n:04d}-*-check.json")}
        lot_files = [d for d in (remove(f) for f in sorted(own | {lot_file, report_file})) if d]
        record(
            f"{prefix}-4-inputs-deleted.json",
            {"lot": n, "utc": now(), "deleted": deleted, "lot_files_deleted": lot_files},
        )
        print(f"lot {n}: done ({len(lot)} cases)", flush=True)
    return 0


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)
    g = sub.add_parser("generate")
    g.add_argument("--population", required=True)
    g.add_argument("--cache", required=True)
    g.add_argument("--manifest")
    g.add_argument("--check")
    g.add_argument("--check-report", help="with --check: write the counts as JSON")
    g.add_argument("--cases-from")
    g.add_argument("--order", default="index")
    g.add_argument("--no-store", action="store_true", help="hash only; write no case file")
    a = sub.add_parser("analyze")
    a.add_argument("--manifest", required=True)
    a.add_argument("--cache", required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--point", required=True)
    a.add_argument("--cases-from")
    c = sub.add_parser("check-point")
    c.add_argument("--point", required=True)
    m = sub.add_parser("metrics")
    m.add_argument("--manifest", required=True)
    m.add_argument("--runs", nargs="+", required=True)
    m.add_argument("--records", nargs="*", help="orchestrate record folders to check against")
    m.add_argument("--out", required=True)
    o = sub.add_parser("orchestrate")
    o.add_argument("--manifest", required=True)
    o.add_argument("--project", required=True)
    o.add_argument("--cache", required=True)
    o.add_argument("--generator-python", required=True)
    o.add_argument("--point", action="append", required=True)
    o.add_argument("--lot-size", type=int, default=50)
    o.add_argument("--records", required=True, help="folder for the lot records")
    for p in (g, a, o):
        p.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 8))
    for p in (g, a, c, m, o):
        p.add_argument("--cpus", default="8-31")
    args = parser.parse_args(argv)
    if args.mode == "generate" and bool(args.manifest) == bool(args.check):
        parser.error("generate needs exactly one of --manifest (write) or --check (compare)")
    print(f"affinity: {set_affinity(args.cpus)}", flush=True)
    return {
        "generate": mode_generate,
        "analyze": mode_analyze,
        "check-point": mode_check_point,
        "metrics": mode_metrics,
        "orchestrate": mode_orchestrate,
    }[args.mode](args)


if __name__ == "__main__":
    sys.exit(main())
