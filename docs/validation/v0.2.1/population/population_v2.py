"""v0.2.1 synthetic population study harness, version 2.

Protocol: docs/validation/v0.2.1/population-study.md, with Amendments 1 to 3 and Amendment 4
(the rules of this version). Specification: harness-v2-spec.md, revision 6, and
D6-proposta.md, revision 4 (both recorded with Amendment 4). The v1 harness
(``population.py``, SHA-256 ``408020676340322f4728ce3a8b4eecae505bfbec7ec34643ad9afed0e5a76225``)
is left as it is. This file and its comparator (``population_compare.py``, next to it) are
outside ``src/``: they are not part of the code hash of Refute, and they are never edited
after the first campaign generation (a change is a new file with a new name).

The case bytes do not change: a case is built and serialized exactly as by v1
(``refute-population-serialization/1``).

Campaign modes (``python population_v2.py <mode> --help``). Each works on one campaign,
named by ``--campaign`` and found under ``--root`` (by default ``campaigns/`` next to this
file); the journal, the lock markers and the resolutions live in the campaign's directory,
whatever run directories are used:

- ``generate``: one generation (1..K) of one set (1..N) of the campaign's population, in the
  v0.2.0 environment, hash only (or stored with ``--cache``). Writes the scientific manifest
  (``refute-population-manifest/2``), its block index (``refute-population-blocks/1``) and the
  execution record (``refute-population-execution/1``). A generation that differs from an
  earlier generation of its set writes a lock.
- ``check-set``: the K generations of a set: byte-identical manifests and block indexes, every
  execution closed, and the blocking comparisons (other sets; for the development
  population, manifest B). Accepts the set (journal entry ``accepted``) or writes a lock.
- ``regenerate``: the inputs of a lot, written to the cache and checked against the accepted
  manifest and block index (any difference writes a lock).
- ``analyze``: one slot (1 or 2) of one lot at one measurement point; the complete scientific
  record (``refute-population-result/3``) of every case. Resumed per slot after an
  infrastructure failure only.
- ``compare-slots``: the two slots of a lot at a point, with the comparator's profile
  ``slots`` (record 3c); a difference writes a lock.
- ``orchestrate``: the cycle by lot (regenerate, both slots at every point, records 3 per slot,
  the comparison 3c, then the inputs are deleted and record 4 is written).
- ``metrics``: reconciliation, then criteria C1 to C6 as in v1; ``--integrity-report`` writes
  the integrity-failure report of a locked campaign instead.
- ``reconcile``: the maintainer's record of an execution whose closure cannot be shown.
- ``status``: read-only state of a campaign.
- ``dispatch-table`` and ``compare``: helpers (the effective NumPy dispatch table; an offline
  comparison of two files). They write nothing into a campaign.

Eligibility: a campaign under the default root has ``eligibility`` ``campaign`` and every
check is enforced (this file and the comparator are the files of HEAD, R2; the declaration
and the resolutions are committed). Under any other root the campaign is a **diagnostic**:
its declaration must say ``"eligibility": "diagnostic"``, every artifact is ``diagnostic``,
the git checks are recorded but not enforced, and nothing it writes can be accepted by a
campaign. The harness never runs a git command that writes.
"""

from __future__ import annotations

import os

# Amendment 2, N1: one thread in every numeric library, set before NumPy (or Refute, which
# imports it) is imported in this process. Spawned workers import this file first and
# inherit the environment; threadpoolctl confirms it at run time (single_thread_problems).
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
import concurrent.futures as cf  # noqa: E402
import ctypes  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import multiprocessing  # noqa: E402
import platform  # noqa: E402
import queue as queue_module  # noqa: E402
import re  # noqa: E402
import secrets  # noqa: E402
import struct  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402
import traceback  # noqa: E402
from dataclasses import asdict, dataclass, field  # noqa: E402
from datetime import UTC, datetime  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402

SERIALIZATION = "refute-population-serialization/1"
MAGIC = (SERIALIZATION + "\n").encode("ascii")
MANIFEST_FORMAT = "refute-population-manifest/2"
BLOCKS_FORMAT = "refute-population-blocks/1"
EXECUTION_FORMAT = "refute-population-execution/1"
RESULT_FORMAT = "refute-population-result/3"
DECLARATION_FORMAT = "refute-population-campaign/1"
JOURNAL_FORMAT = "refute-population-journal/1"
LOCK_FORMAT = "refute-population-lock/1"
RESOLUTION_FORMAT = "refute-population-resolution/1"
SET_REPORT_FORMAT = "refute-population-set-check/1"
SLOTS_REPORT_FORMAT = "refute-population-slots/1"
LOT_RECORD_FORMAT = "refute-population-lot-record/2"
POINTS_FORMAT = "refute-population-points/1"
METRICS_FORMAT = "refute-population-metrics/3"
INTEGRITY_REPORT_FORMAT = "refute-population-integrity-report/1"
GENERATOR_COMMIT = "f4798230f1bca607bcc0e98fe47711a26ec4ee59"
GENERATOR_SYNTHETIC_SHA256 = "b1d9518ea96ee3fd91b861c33601d57742ad96520b15079d97bd217f391fc50d"
BLOCK_SIZE = 1 << 20
HARNESS_PATH = Path(__file__).resolve()
# The bytes of the harness and of the comparator this process runs, read once at start (R2:
# they must be the files of the repository's HEAD commit in a campaign).
HARNESS_BYTES = HARNESS_PATH.read_bytes()
HARNESS_SHA256 = hashlib.sha256(HARNESS_BYTES).hexdigest()
COMPARATOR_PATH = HARNESS_PATH.parent / "population_compare.py"
COMPARATOR_BYTES = COMPARATOR_PATH.read_bytes()
COMPARATOR_SHA256_AT_START = hashlib.sha256(COMPARATOR_BYTES).hexdigest()
POINTS_PATH = HARNESS_PATH.parent / "points.json"
DEFAULT_ROOT = HARNESS_PATH.parent / "campaigns"
# The project folder (the top of the repository): every path the harness writes must be
# inside it.
PROJECT_ROOT = HARNESS_PATH.parents[4]
# Manifest B: the value repeated by the v1 generations B, A2, A3, B2 and D of the development
# population (Amendment 4, item 6), the reference of every development campaign.
MANIFEST_B_SHA256 = "4073d96a0bce901a31241d5c2dd3d7b46192a4731a4ec3996ea1077039b833e9"
VERDICTS = ("SURVIVED", "WEAKENED", "REFUTED", "INCONCLUSIVE")
CAMPAIGN_ID_CHARS = frozenset("abcdefghijklmnopqrstuvwxyz0123456789.-")


def inside_project(path, what: str) -> Path:
    """The resolved path, which must be the project folder or inside it."""
    p = Path(path).resolve()
    if p != PROJECT_ROOT and PROJECT_ROOT not in p.parents:
        raise SystemExit(f"refused: {what} {p} is not inside the project folder {PROJECT_ROOT}")
    return p


def _user_path_pattern():
    name = os.environ.get("USERNAME") or os.environ.get("USER") or ""
    if len(name) < 2:
        return None
    return re.compile(
        r"([\\/]+)(Users|home)([\\/]+)" + re.escape(name) + r"(?=[\\/]|$)", re.IGNORECASE
    )


_USER_PATH = _user_path_pattern()


def home_problems() -> list[str]:
    """The project must not be inside the user's home directory: the masking of the records
    would then also change the paths the harness reads back."""
    home = Path.home().resolve()
    if PROJECT_ROOT == home or home in PROJECT_ROOT.parents:
        return [f"the project folder is inside the user's home directory ({PROJECT_ROOT})"]
    return []


def mask_user(value):
    """The value with the user's home directory replaced by ``Users/<user>`` (or
    ``home/<user>``) in every string, dictionary keys included (records, tracebacks and
    machine records never carry the user name)."""
    if _USER_PATH is None:
        return value
    if isinstance(value, str):
        return _USER_PATH.sub(lambda m: f"{m.group(1)}{m.group(2)}{m.group(3)}<user>", value)
    if isinstance(value, dict):
        return {mask_user(k): mask_user(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [mask_user(v) for v in value]
    return value


def _load_comparator():
    spec = importlib.util.spec_from_file_location("population_compare", COMPARATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["population_compare"] = module
    spec.loader.exec_module(module)
    return module


CMP = _load_comparator()

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
DETERMINISM_PREFIX = "refute-v0.2.1-population-determinism"

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
    if population == "determinism":
        return _determinism_cases()
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


def _determinism_cases() -> list[dict]:
    """The determinism and measurement population (Amendment 4): the cases of the
    development structure with the prefix ``refute-v0.2.1-population-determinism`` whose
    index is ``10 j + (j mod 5)``, one per ten consecutive indexes of every class, band and
    noise model. That keeps 10 % of every block (520 cases), with the same mix of classes,
    bands, noise models, mechanisms and catalog variants. v1 builds the same cases with
    ``--population confirm:refute-v0.2.1-population-determinism`` and ``--cases-from``."""
    full = population_cases("confirm:" + DETERMINISM_PREFIX)
    return [c for c in full if c["index"] % 10 == (c["index"] // 10) % 5]


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
        for field_name in ("time", "pdcsap_flux", "sap_flux", "sap_bkg", "dump_times"):
            arrays.append((f"aux/sectors/{k}/{field_name}", getattr(s, field_name), "<f8"))
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


# --- segments, blocks and the double hash (specification, section 3) -------------------


def case_hashes(blob: bytes) -> tuple[str, dict, dict, list[str]]:
    """The whole-blob SHA-256, the layout (header length and every segment with its
    SHA-256), the SHA-256 of every block of 1 MiB of every segment, and the integrity
    problems. Every hash is computed over a slice of the final ``bytes`` object. The whole
    hash is computed twice with two fresh hashlib objects; unequal digests are an integrity
    problem (a detector of transient errors, not independent of a systematic defect)."""
    problems = []
    first = hashlib.sha256(blob).hexdigest()
    second = hashlib.sha256(blob).hexdigest()
    if first != second:
        problems.append(f"double hash: {first} then {second}")
    try:
        parsed = CMP.parse_layout(blob)
    except CMP.LayoutError as exc:
        return first, {}, {}, [*problems, f"layout: {exc}"]
    problems += [f"coverage: {p}" for p in CMP.coverage_problems(parsed["segments"], len(blob))]
    view = memoryview(blob)
    segments, blocks = [], {}
    for s in parsed["segments"]:
        part = view[s["offset"] : s["offset"] + s["length"]]
        segments.append({**s, "sha256": hashlib.sha256(part).hexdigest()})
        blocks[s["name"]] = [
            hashlib.sha256(part[i : i + BLOCK_SIZE]).hexdigest()
            for i in range(0, s["length"], BLOCK_SIZE)
        ]
    if len(blocks) != len(segments):
        problems.append("two segments have the same name")
    layout = {"header_length": parsed["header_length"], "segments": segments}
    return first, layout, blocks, problems


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
    """The canonical bytes of a case and its manifest entry without the hashes (v0.2.0
    helpers only; the bytes are those of v1)."""
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


def built_case(case: dict) -> tuple[bytes, dict, dict, list[str]]:
    """A case's bytes, its complete manifest entry (whole SHA-256, layout with the hash of
    every segment, the SHA-256 of its block list), its blocks and the integrity problems."""
    blob, entry = build_case(case)
    digest, layout, blocks, problems = case_hashes(blob)
    entry["sha256"] = digest
    entry["layout"] = layout
    entry["blocks_sha256"] = hashlib.sha256(canonical_json(blocks)).hexdigest()
    return blob, entry, blocks, problems


def store_case(cache: Path, case_id: str, blob: bytes, digest: str) -> tuple[str, str | None]:
    """Write a case to the cache without ever replacing a different file (section 6): an
    existing file with the same bytes is kept; an existing file with other bytes is left
    untouched, the new bytes are written beside it as ``<case>.<sha256>.rpc``, and the
    divergence is returned."""
    path = cache / f"{case_id}.rpc"
    if path.exists():
        existing = path.read_bytes()
        if existing == blob:
            return "kept", None
        side = cache / f"{case_id}.{digest}.rpc"
        note = ""
        if not side.exists():
            write_atomic(side, blob)
        elif side.read_bytes() != blob:
            note = f"; {side.name} already existed with other bytes (left untouched)"
        return "diverged", (
            f"cache: {path.name} exists with SHA-256 {hashlib.sha256(existing).hexdigest()}{note}; "
            f"the new bytes ({digest}) are in {side.name}"
        )
    write_atomic(path, blob)
    return "written", None


# Sequence number of the cases a worker process has handled (0 for its first case).
_SEQUENCE = 0


def _next_position() -> int:
    global _SEQUENCE
    position = _SEQUENCE
    _SEQUENCE += 1
    return position


def generate_task(task: tuple[dict, str | None, dict | None]) -> dict:
    """Build one case in a worker; store it unless ``cache`` is None (hash only); with a
    frozen entry (``regenerate``), compare the entry and its blocks with it."""
    case, cache, frozen = task
    position = _next_position()
    started = utc_now()
    start = time.perf_counter()
    blob, entry, blocks, problems = built_case(case)
    stored = None
    if frozen is not None:
        if canonical_json(entry) != canonical_json(frozen["entry"]):
            problems.append("regeneration: the case entry differs from the frozen manifest")
        if canonical_json(blocks) != canonical_json(frozen["blocks"]):
            problems.append("regeneration: the case blocks differ from the frozen block index")
    if cache is not None:
        stored, problem = store_case(Path(cache), case["id"], blob, entry["sha256"])
        if problem:
            problems.append(problem)
    return {
        "case": case["id"],
        "entry": entry,
        "blocks": blocks,
        "problems": problems,
        "stored": stored,
        "operational": {
            "pid": os.getpid(),
            "sequence_position": position,
            "seconds": round(time.perf_counter() - start, 3),
            "peak_memory_mb": peak_memory_mb(),
            "started_utc": started,
            "ended_utc": utc_now(),
        },
    }


# --- environment ------------------------------------------------------------------------


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="microseconds")


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


def affinity_mask() -> str | None:
    """The affinity mask of this process, read back from the operating system."""
    if sys.platform == "win32":
        k = ctypes.windll.kernel32
        k.GetCurrentProcess.restype = ctypes.c_void_p
        proc, system = ctypes.c_size_t(), ctypes.c_size_t()
        if k.GetProcessAffinityMask(
            ctypes.c_void_p(k.GetCurrentProcess()), ctypes.byref(proc), ctypes.byref(system)
        ):
            return f"{proc.value:#x}"
        return None
    return f"{sum(1 << c for c in os.sched_getaffinity(0)):#x}"


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


def pid_running(pid: int) -> bool:
    """Whether a process with this PID is still running."""
    if sys.platform == "win32":
        k = ctypes.windll.kernel32
        k.OpenProcess.restype = ctypes.c_void_p
        handle = k.OpenProcess(0x00100000 | 0x1000, False, int(pid))  # SYNCHRONIZE, QUERY
        if not handle:
            return ctypes.GetLastError() != 87  # ERROR_INVALID_PARAMETER: no such process
        try:
            return k.WaitForSingleObject(ctypes.c_void_p(handle), 0) != 0  # WAIT_OBJECT_0
        finally:
            k.CloseHandle(ctypes.c_void_p(handle))
    try:
        os.kill(int(pid), 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


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


# --- dispatch (specification, section 5) ------------------------------------------------

DISPATCH_VARIABLE = "NPY_DISABLE_CPU_FEATURES"


def dispatch_table() -> dict:
    """The effective NumPy dispatch table: every function and signature with its
    ``current`` target, as ``numpy.lib.introspect.opt_func_info()`` reports it."""
    from numpy.lib.introspect import opt_func_info

    return {
        func: {sig: info.get("current") for sig, info in sorted(sigs.items())}
        for func, sigs in sorted(opt_func_info().items())
    }


def dispatch_problems(declared: dict) -> tuple[dict | None, str | None, list[str]]:
    """The effective table, its SHA-256, and every difference from the declared inventory
    (the dispatch variable, every entry; a missing, extra or different entry, or a table that
    cannot be read, is a problem)."""
    problems = []
    want_env = (declared.get("environment") or {}).get(DISPATCH_VARIABLE)
    if os.environ.get(DISPATCH_VARIABLE) != want_env:
        problems.append(
            f"{DISPATCH_VARIABLE} is {os.environ.get(DISPATCH_VARIABLE)!r}, declared {want_env!r}"
        )
    try:
        table = dispatch_table()
    except Exception as exc:  # noqa: BLE001 - a table that cannot be read is a problem
        return None, None, [*problems, f"dispatch table not readable: {exc}"]
    digest = hashlib.sha256(canonical_json(table)).hexdigest()
    want = declared.get("table") or {}
    for func in sorted(set(want) | set(table)):
        a, b = want.get(func), table.get(func)
        if a is None or b is None:
            problems.append(f"dispatch {func}: {'missing' if b is None else 'not declared'}")
            continue
        for sig in sorted(set(a) | set(b)):
            if a.get(sig) != b.get(sig):
                problems.append(f"dispatch {func}[{sig}]: {b.get(sig)!r}, declared {a.get(sig)!r}")
    return table, digest, problems


# --- machine record (specification, section 8.1) ----------------------------------------

_CIM_SCRIPT = """
$ErrorActionPreference = 'Stop'
$bios = Get-CimInstance Win32_BIOS
$board = Get-CimInstance Win32_BaseBoard
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$mem = @(Get-CimInstance Win32_PhysicalMemory | ForEach-Object {
    [pscustomobject]@{ bank = $_.BankLabel; locator = $_.DeviceLocator;
        manufacturer = $_.Manufacturer; part = "$($_.PartNumber)".Trim();
        capacity = [string]$_.Capacity; speed = $_.Speed; configured = $_.ConfiguredClockSpeed;
        configured_voltage_mv = $_.ConfiguredVoltage }
})
$ecc = (Get-CimInstance Win32_PhysicalMemoryArray | Select-Object -First 1).MemoryErrorCorrection
$svc = Get-CimInstance Win32_Service -Filter "Name='EasyTuneEngineService'"
[pscustomobject]@{
    cpu = @{ name = "$($cpu.Name)".Trim(); processor_id = $cpu.ProcessorId }
    bios = @{ manufacturer = $bios.Manufacturer; version = $bios.SMBIOSBIOSVersion;
              date = $bios.ReleaseDate.ToString('yyyy-MM-dd') }
    board = @{ manufacturer = $board.Manufacturer; product = $board.Product }
    memory = $mem
    memory_error_correction = $ecc
    easytune = if ($svc) { @{ state = $svc.State; start_mode = $svc.StartMode } } else { $null }
} | ConvertTo-Json -Depth 5 -Compress
"""


def _cim_record() -> dict:
    """BIOS, board, memory, ECC and the EasyTune service (Windows only; read-only)."""
    if sys.platform != "win32":
        return {"unavailable": "not Windows"}
    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", _CIM_SCRIPT],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if res.returncode != 0:
            return {"unavailable": res.stderr.strip()[-500:]}
        return json.loads(res.stdout)
    except Exception as exc:  # noqa: BLE001 - recorded, not hidden
        return {"unavailable": f"{type(exc).__name__}: {exc}"}


def _file_version(path: Path) -> str | None:
    """The file version of a Windows binary (for the UCRT)."""
    if sys.platform != "win32" or not path.is_file():
        return None
    v = ctypes.windll.version
    size = v.GetFileVersionInfoSizeW(str(path), None)
    if not size:
        return None
    buf = ctypes.create_string_buffer(size)
    if not v.GetFileVersionInfoW(str(path), 0, size, buf):
        return None
    ptr, n = ctypes.c_void_p(), ctypes.c_uint()
    if not v.VerQueryValueW(buf, "\\", ctypes.byref(ptr), ctypes.byref(n)):
        return None
    ms, ls = struct.unpack_from("<II", ctypes.string_at(ptr.value + 8, 8))
    return f"{ms >> 16}.{ms & 0xFFFF}.{ls >> 16}.{ls & 0xFFFF}"


def _registry_cpu() -> dict:
    if sys.platform != "win32":
        return {}
    import winreg

    out = {}
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
        )
        with key:
            out["name"] = str(winreg.QueryValueEx(key, "ProcessorNameString")[0]).strip()
            raw = winreg.QueryValueEx(key, "Update Revision")[0]
            if isinstance(raw, bytes):
                # Read as a little-endian number (8 bytes: the revision is the upper half).
                out["microcode_raw_hex"] = raw[::-1].hex()
                value = raw[4:8] if len(raw) == 8 else raw
                out["microcode_revision"] = f"{int.from_bytes(value, 'little'):#010x}"
    except OSError as exc:
        out["unavailable"] = str(exc)
    return out


def _lock_wheels(root: Path) -> dict:
    """The wheels of NumPy (which bundles scipy-openblas) for this interpreter and platform,
    with their hashes, from the ``uv.lock`` of the installed Refute's worktree."""
    import tomllib

    lock = root / "uv.lock"
    if not lock.is_file():
        return {"unavailable": f"{lock} not found"}
    data = tomllib.loads(lock.read_text(encoding="utf-8"))
    tag = f"cp{sys.version_info.major}{sys.version_info.minor}"
    plat = "win_amd64" if sys.platform == "win32" else platform.machine()
    out = {"uv_lock_sha256": file_sha256(lock)}
    for pkg in data.get("package", []):
        if pkg.get("name") in ("numpy", "scipy", "scipy-openblas32", "scipy-openblas64"):
            wheels = [
                {"file": w["url"].rsplit("/", 1)[-1], "hash": w.get("hash")}
                for w in pkg.get("wheels", [])
                if f"-{tag}-" in w["url"] and plat in w["url"]
            ]
            out[pkg["name"]] = {"version": pkg.get("version"), "wheels": wheels}
    return out


def _bundled_libraries() -> list[dict]:
    """The DLLs bundled with NumPy (OpenBLAS among them), with their SHA-256."""
    import numpy

    folder = Path(numpy.__file__).resolve().parents[1] / "numpy.libs"
    if not folder.is_dir():
        return []
    return [{"file": f.name, "sha256": file_sha256(f)} for f in sorted(folder.iterdir())]


class MachineRecord:
    """The machine record of section 8.1, collected once per execution; the slow part (CIM)
    runs in a background thread while the execution proceeds."""

    def __init__(self, declared: dict) -> None:
        self.declared = declared
        self._cim: dict = {}
        self._thread = threading.Thread(target=self._collect, daemon=True)
        self._thread.start()

    def _collect(self) -> None:
        self._cim = _cim_record()

    def result(self, refute_root: str | None) -> dict:
        self._thread.join(timeout=180)
        system = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "ucrtbase.dll"
        return {
            "python": sys.version,
            "executable": sys.executable,
            "numpy": np.__version__,
            "numpy_blas": numeric_environment().get("numpy_blas"),
            "lock_wheels": _lock_wheels(Path(refute_root)) if refute_root else None,
            "bundled_libraries": _bundled_libraries(),
            "os": {
                "platform": platform.platform(),
                "version": platform.version(),
                "ucrt": _file_version(system),
            },
            "cpu_registry": _registry_cpu(),
            "affinity_mask": affinity_mask(),
            "thread_env": {v: os.environ.get(v) for v in THREAD_VARIABLES},
            "threadpools": thread_pools(),
            "cim": self._cim if not self._thread.is_alive() else {"unavailable": "timeout"},
            "declared": self.declared,
        }


# --- git, the installed Refute, points --------------------------------------------------


def git(cwd: Path, *args: str) -> str:
    """Output of a read-only git command (empty if git fails)."""
    res = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    return res.stdout.strip() if res.returncode == 0 else ""


def git_blob(cwd: Path, spec: str) -> bytes | None:
    """The bytes of ``<commit>:<path>``, or None if it does not exist."""
    res = subprocess.run(["git", "-C", str(cwd), "show", spec], capture_output=True)
    return res.stdout if res.returncode == 0 else None


def committed_problems(path: Path, sha256: str | None = None) -> list[str]:
    """Why ``path`` is not, byte for byte, the file of HEAD of its repository (tracked,
    no change against HEAD, and the bytes of ``git show HEAD:<path>``)."""
    folder = path.parent
    rel = git(folder, "ls-files", "--full-name", "--", path.name)
    head = git(folder, "rev-parse", "HEAD")
    if not rel or not head:
        return [f"{path.name} is not tracked in a git repository"]
    problems = []
    diff = subprocess.run(["git", "-C", str(folder), "diff", "--quiet", "HEAD", "--", path.name])
    if diff.returncode != 0:
        problems.append(f"{rel} has changes that are not committed (git diff HEAD)")
    blob = git_blob(folder, f"{head}:{rel}")
    want = sha256 or file_sha256(path)
    if blob is None or hashlib.sha256(blob).hexdigest() != want:
        problems.append(f"{rel} is not the file of commit {head} (SHA-256)")
    return problems


def harness_problems() -> tuple[str, list[str]]:
    """The HEAD commit, and why the running harness or comparator is not byte for byte the
    file of that commit, or changed on disk since this process started (R2, extended)."""
    head = git(HARNESS_PATH.parent, "rev-parse", "HEAD")
    problems = committed_problems(HARNESS_PATH, HARNESS_SHA256)
    problems += committed_problems(COMPARATOR_PATH, COMPARATOR_SHA256_AT_START)
    if file_sha256(HARNESS_PATH) != HARNESS_SHA256:
        problems.append("the harness file changed on disk after this process started")
    if file_sha256(COMPARATOR_PATH) != COMPARATOR_SHA256_AT_START:
        problems.append("the comparator file changed on disk after this process started")
    if CMP.COMPARATOR_SHA256 != COMPARATOR_SHA256_AT_START:
        problems.append("the comparator module loaded is not the file read at start")
    return head, problems


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


def generator_problems(checkout: dict) -> list[str]:
    """The generator runs only at tag v0.2.0 (Amendment 1, item c)."""
    from refute.packs.tess import synthetic

    problems = []
    if checkout["commit"] != GENERATOR_COMMIT:
        problems.append(f"generation runs only at {GENERATOR_COMMIT}, not {checkout['commit']}")
    problems += install_problems(checkout)
    if file_sha256(Path(synthetic.__file__)) != GENERATOR_SYNTHETIC_SHA256:
        problems.append("synthetic.py is not the file of tag v0.2.0")
    return problems


def file_sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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


def run_provenance_problems(camp, point: str, runs: list[str]) -> list[str]:
    """The provenance of the two slot runs of a point (Amendment 2, C1 and N8, per slot):
    each run's binding is the point's line in points.json, the recorded points.json is in
    git, the installed Refute was clean and editable, and both slots ran the same checkout,
    environment fingerprint, plan, harness and manifest."""
    points = load_points()
    problems, runs_seen = [], []
    for s, run in enumerate(runs, start=1):
        f = Path(run) / "run.json"
        if not f.is_file():
            problems.append(f"{point} slot {s}: no run.json")
            continue
        r = read_json(f)
        runs_seen.append(r)
        entry = point_entry(points, point)
        b = r.get("binding") or {}
        if r.get("point") != point or r.get("slot") != s or b.get("point") != point:
            problems.append(f"{point} slot {s}: run.json names another point or slot")
        if entry is None or b.get("commit") != entry["commit"]:
            problems.append(f"{point} slot {s}: the binding is not the point's line in points.json")
        if (r.get("checkout") or {}).get("commit") != b.get("commit"):
            problems.append(f"{point} slot {s}: the checkout commit is not the binding's")
        if r.get("campaign_id") != camp.campaign_id or (
            r.get("campaign_declaration_sha256") != camp.declaration_sha256
        ):
            problems.append(f"{point} slot {s}: run.json belongs to another campaign")
        problems += [f"{point} slot {s}: {p}" for p in install_problems(r.get("checkout") or {})]
        problems += [
            f"{point} slot {s}: {p}"
            for p in recorded_points_problems(r.get("points_at_start") or {}, b, points)
        ]
    if len(runs_seen) == 2:
        for key in ("checkout", "fingerprint", "plan", "harness_sha256", "manifest_sha256"):
            if runs_seen[0].get(key) != runs_seen[1].get(key):
                problems.append(f"{point}: the two slots differ in {key}")
    return problems


def write_atomic(path: Path, data: bytes, *, exclusive: bool = True) -> None:
    """Write ``data`` to a temporary file in the same folder and move it into place, so that
    no final file is ever written in parts; only inside the project. With ``exclusive`` (the
    default) an existing final file is never replaced: the final name is created by a hard
    link, which fails if the name exists (no window between a test and a rename)."""
    path = inside_project(path, "the file")
    if exclusive and path.exists():
        raise FileExistsError(f"{path} exists; it is never overwritten")
    tmp = path.with_name(f".{path.name}.tmp-{os.getpid()}-{secrets.token_hex(3)}")
    with open(tmp, "wb") as fh:
        fh.write(data)
        fh.flush()
        os.fsync(fh.fileno())
    if not exclusive:
        os.replace(tmp, path)
        return
    try:
        os.link(tmp, path)
    except FileExistsError:
        raise FileExistsError(f"{path} appeared while writing; left {tmp.name} in place") from None
    os.unlink(tmp)  # the temporary name of this process only; the final name stays


def write_json(path: Path, obj) -> str:
    """Write canonical JSON (plus a newline) exclusively, with the user's home directory
    masked, inside the project only; returns its SHA-256."""
    path = inside_project(path, "the file")
    data = canonical_json(mask_user(obj)) + b"\n"
    write_atomic(path, data)
    return hashlib.sha256(data).hexdigest()


def read_json(path: Path):
    return json.loads(Path(path).read_bytes())


def _ordered(cases: list, order: str) -> list:
    if order == "index":
        return list(cases)
    if order == "reverse":
        return list(reversed(cases))
    if order.startswith("shuffle:"):
        rng = np.random.default_rng(int(order.split(":", 1)[1]))
        return [cases[i] for i in rng.permutation(len(cases))]
    raise SystemExit(f"unknown order {order}")


def order_sha256(ids: list[str]) -> str:
    return hashlib.sha256(canonical_json(ids)).hexdigest()


# --- typed contract (specification, section 10) -----------------------------------------

INT64_MIN, INT64_MAX = -(1 << 63), (1 << 63) - 1


class ContractError(TypeError):
    """A value outside the closed list of the typed contract."""


def typed_float(value) -> dict:
    """``{"f64": <16 hex digits, big-endian binary64>, "dec": <repr>}``, the bits captured
    from the original value; non-finite values keep their bits and have ``dec`` ``nan``,
    ``inf`` or ``-inf``; a finite ``dec`` must parse back to the same bits."""
    if isinstance(value, np.float64):
        bits = value.tobytes()[::-1].hex() if sys.byteorder == "little" else value.tobytes().hex()
    else:
        bits = struct.pack(">d", value).hex()
    x = float(value)
    if math.isnan(x):
        dec = "nan"
    elif math.isinf(x):
        dec = "inf" if x > 0 else "-inf"
    else:
        dec = repr(x)
        if struct.pack(">d", float(dec)).hex() != bits:
            raise ContractError(f"float {dec} does not round-trip to its bits {bits}")
    return {"f64": bits, "dec": dec}


def typed(value, path: str = ""):
    """The typed encoding of a value (closed list; anything else is a ContractError)."""
    if value is None or isinstance(value, bool):
        return value
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, np.floating) and not isinstance(value, np.float64):
        raise ContractError(f"{path or '/'}: {type(value).__name__} is not supported")
    if isinstance(value, float):
        return typed_float(value)
    if isinstance(value, int | np.integer):
        v = int(value)
        if not INT64_MIN <= v <= INT64_MAX:
            raise ContractError(f"{path or '/'}: integer {v} outside the int64 range")
        return v
    if isinstance(value, str):
        return str.__str__(value)  # the string's content, also for a str subclass
    if isinstance(value, list | tuple):
        return [typed(v, f"{path}/{i}") for i, v in enumerate(value)]
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if not isinstance(k, str):
                raise ContractError(f"{path or '/'}: key {k!r} is not a string")
            out[str(k)] = typed(v, f"{path}/{CMP.pointer([k])[1:]}")
        return out
    raise ContractError(f"{path or '/'}: {type(value).__name__} is not supported")


def record_bytes(record: dict) -> bytes:
    """A record already typed: UTF-8 JSON, keys sorted, no spaces, the user's home directory
    masked (in a traceback, for example)."""
    return (
        json.dumps(
            mask_user(record),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
        + b"\n"
    )


# --- campaign: declaration, journal, locks, resolutions (sections 1, 7, 8) --------------


@dataclass
class Campaign:
    root: Path
    campaign_id: str
    strict: bool
    declaration: dict = field(default_factory=dict)
    declaration_sha256: str = ""
    problems: list = field(default_factory=list)
    superseded: bool = False

    @property
    def dir(self) -> Path:
        return self.root / self.campaign_id

    @property
    def journal(self) -> Path:
        return self.dir / "journal.jsonl"

    @property
    def locks(self) -> Path:
        return self.dir / "locks"

    @property
    def resolutions(self) -> Path:
        return self.dir / "resolutions"

    @property
    def eligibility(self) -> str:
        return "campaign" if self.strict else "diagnostic"

    def common_identity(self, set_number: int | None) -> dict:
        return {
            "campaign_id": self.campaign_id,
            "campaign_declaration_sha256": self.declaration_sha256,
            "chain": self.declaration.get("chain"),
            "set": set_number,
        }

    def cases(self) -> list[dict]:
        """The campaign's population (a diagnostic declaration may restrict it to a closed
        list of case ids, in population order)."""
        cases = population_cases(self.declaration["population"])
        wanted = self.declaration.get("cases")
        if wanted is None:
            return cases
        keep = set(wanted)
        chosen = [c for c in cases if c["id"] in keep]
        if len(chosen) != len(keep):
            raise SystemExit("the declaration names case ids that are not in the population")
        return chosen


def campaign_id_problems(campaign_id: str) -> list[str]:
    """A campaign id is a single folder name: lowercase letters, digits, dots and hyphens,
    starting with a letter or digit, at most 64 characters, never ``..``."""
    ok = (
        isinstance(campaign_id, str)
        and 0 < len(campaign_id) <= 64
        and campaign_id[0] in CAMPAIGN_ID_CHARS - {".", "-"}
        and set(campaign_id) <= CAMPAIGN_ID_CHARS
        and ".." not in campaign_id
    )
    return [] if ok else [f"campaign id {campaign_id!r} is not a plain folder name"]


def strict_declaration_problems(decl: dict) -> list[str]:
    """The rules a campaign declaration must meet under the default root (Amendment 4,
    clarifications of 2026-10-13): the whole population, no case list; the chain of the
    population; manifest B as the reference of the development population and no reference
    for any other; the qualification and the full D6 named with their SHA-256."""
    problems = []
    pop = decl.get("population")
    if "cases" in decl:
        problems.append("a campaign declaration cannot restrict the population to a case list")
    chain = (
        "development"
        if pop == "dev"
        else "confirmation"
        if str(pop).startswith("confirm:")
        else None
    )
    if chain is None:
        problems.append(f"population {pop!r} is not a campaign population (dev or confirm:...)")
    elif decl.get("chain") != chain:
        problems.append(
            f"population {pop!r} belongs to the {chain} chain, not {decl.get('chain')!r}"
        )
    ref = decl.get("reference_manifest")
    if pop == "dev":
        if not ref or ref.get("sha256") != MANIFEST_B_SHA256:
            problems.append(f"the development population needs manifest B ({MANIFEST_B_SHA256})")
    elif ref:
        problems.append("only the development population has a reference manifest")
    for key in ("qualification", "d6"):
        item = decl.get(key) or {}
        if not item.get("path") or not item.get("sha256"):
            problems.append(f"the declaration does not name the {key} record (path and SHA-256)")
    return problems


QUALIFICATION_FORMAT = "refute-machine-qualification/1"
D6_PROFILES = ("d6-science", "d6-control")


def machine_snapshot() -> dict:
    """The validity conditions of the qualification that this process can read without
    elevation: CPU, microcode, BIOS, board and memory modules (CIM and registry)."""
    cim = _cim_record()
    reg = _registry_cpu()
    modules = [
        {
            k: m.get(k)
            for k in ("bank", "locator", "part", "capacity", "configured", "configured_voltage_mv")
        }
        for m in cim.get("memory") or []
    ]
    return {
        "cpu_name": (cim.get("cpu") or {}).get("name"),
        "cpu_processor_id": (cim.get("cpu") or {}).get("processor_id"),
        "microcode_revision": reg.get("microcode_revision"),
        "bios_version": (cim.get("bios") or {}).get("version"),
        "bios_date": (cim.get("bios") or {}).get("date"),
        "board_product": (cim.get("board") or {}).get("product"),
        "memory_modules": sorted(modules, key=lambda m: (str(m["bank"]), str(m["locator"]))),
        "unavailable": cim.get("unavailable"),
    }


QUALIFICATION_CONDITIONS = (
    "cpu_name",
    "cpu_processor_id",
    "microcode_revision",
    "bios_version",
    "bios_date",
    "board_product",
    "memory_modules",
)
MEMORY_MODULE_KEYS = ("bank", "locator", "part", "capacity", "configured", "configured_voltage_mv")


def _absent(value) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def qualification_condition_problems(want) -> list[str]:
    """The machine-checked validity conditions must all be present, with values: the seven
    conditions, and at least one memory module with every field. An incomplete record is
    refused before any comparison (a condition left out would otherwise never be compared)."""
    if not isinstance(want, dict):
        return ["the qualification record has no machine-checked validity conditions"]
    problems = []
    missing = [k for k in QUALIFICATION_CONDITIONS if k not in want or _absent(want[k])]
    if missing:
        problems.append(f"the qualification record lacks the conditions {missing}")
    unknown = sorted(set(want) - set(QUALIFICATION_CONDITIONS) - {"note"})
    if unknown:
        problems.append(f"the qualification record has unknown conditions {unknown}")
    modules = want.get("memory_modules")
    if "memory_modules" not in missing:
        if not isinstance(modules, list) or not modules:
            problems.append("the qualification record lists no memory module")
        else:
            for i, m in enumerate(modules):
                if not isinstance(m, dict):
                    problems.append(f"memory module {i}: not an object")
                    continue
                lacks = [k for k in MEMORY_MODULE_KEYS if k not in m or _absent(m[k])]
                if lacks or set(m) - set(MEMORY_MODULE_KEYS):
                    problems.append(
                        f"memory module {i}: fields missing {lacks} or unknown "
                        f"{sorted(set(m) - set(MEMORY_MODULE_KEYS))}"
                    )
    return problems


def qualification_problems(qual: dict, snapshot: dict) -> list[str]:
    """The structured qualification record: result PASS, the seven machine-checked validity
    conditions present with values, and each equal to this machine now. An incomplete PASS
    record is refused. The conditions that need elevation (the BCD badmemorylist entry) are
    attested by the maintainer and not compared."""
    problems = []
    if not isinstance(qual, dict) or qual.get("format") != QUALIFICATION_FORMAT:
        return [f"the qualification record is not {QUALIFICATION_FORMAT}"]
    if qual.get("result") != "PASS":
        problems.append(f"the machine qualification record says {qual.get('result')!r}, not PASS")
    want = qual.get("validity_conditions_machine_checked")
    incomplete = qualification_condition_problems(want)
    if incomplete:
        return problems + incomplete
    if snapshot.get("unavailable"):
        problems.append(f"the machine record cannot be read: {snapshot['unavailable']}")
    for key in QUALIFICATION_CONDITIONS:
        value = want[key]
        got = snapshot.get(key)
        if key == "memory_modules":
            value = sorted(value, key=lambda m: (str(m["bank"]), str(m["locator"])))
        if got != value:
            problems.append(
                f"qualification condition {key}: the machine has {got!r}, qualified {value!r}"
            )
    return problems


def prerequisite_problems(decl: dict, snapshot: dict | None = None) -> list[str]:
    """Section 8.2 and 17: a campaign generation starts only after the machine qualification
    and the full D6, both named by path and SHA-256 in the declaration. The qualification's
    result and validity conditions are read from its structured record (never from the
    declaration) and compared with this machine; the D6 report must be a PASS of the full
    matrix produced by the current d6.py, harness and comparator profiles."""
    problems = []
    for key in ("qualification", "d6"):
        item = decl.get(key) or {}
        try:
            path = inside_project(PROJECT_ROOT / str(item.get("path", "")), f"the {key} record")
        except SystemExit as exc:
            problems.append(str(exc))
            continue
        if not path.is_file() or file_sha256(path) != item.get("sha256"):
            problems.append(f"the {key} record is missing or differs from its SHA-256")
            continue
        try:
            doc = read_json(path)
        except ValueError:
            problems.append(f"the {key} record is not valid JSON")
            continue
        if key == "qualification":
            problems += qualification_problems(
                doc, snapshot if snapshot is not None else machine_snapshot()
            )
            continue
        if doc.get("format") != "refute-population-d6-report/1":
            problems.append("the D6 record is not a D6 report")
            continue
        if doc.get("result") != "PASS" or not doc.get("counts_as_d6"):
            problems.append(
                f"the D6 report is {doc.get('result')!r}, counts as the D6: "
                f"{doc.get('counts_as_d6')!r} (a PASS of the full matrix is required)"
            )
        d6_path = HARNESS_PATH.parent / "d6.py"
        current = {
            "d6_sha256": file_sha256(d6_path) if d6_path.is_file() else None,
            "harness_sha256": HARNESS_SHA256,
            "profiles": {n: CMP.profile_sha256(n) for n in D6_PROFILES},
        }
        for k, v in current.items():
            if doc.get(k) != v:
                problems.append(f"the D6 report is of another version ({k} differs)")
    return problems


def _declarations(root: Path) -> dict[str, tuple[dict, str]]:
    out = {}
    if root.is_dir():
        for d in sorted(root.iterdir()):
            f = d / "declaration.json"
            if f.is_file():
                data = f.read_bytes()
                try:
                    out[d.name] = (json.loads(data), hashlib.sha256(data).hexdigest())
                except ValueError:
                    out[d.name] = ({}, hashlib.sha256(data).hexdigest())
    return out


def chain_problems(camp: Campaign, root: Path | None = None) -> list[str]:
    """Section 1 and 8.5: the chain's counter is never reset. The declared predecessor must
    exist under the same root with the declared declaration SHA-256, have no unreconciled
    execution, and the sets it consumed plus its own count before must equal this
    declaration's count before; every other campaign of the chain must be an ancestor (one
    line per chain). The first campaign of the development chain names the v1 generations as
    its diagnostic predecessor and counts 0."""
    root = (root or DEFAULT_ROOT).resolve()
    decl = camp.declaration
    chain = decl.get("chain")
    pred = decl.get("predecessor") or {}
    before = decl.get("chain_sets_consumed_before")
    problems = []
    others = {k: v for k, v in _declarations(root).items() if k != camp.campaign_id}
    ancestors: set[str] = set()
    cur = pred.get("campaign_id")
    if cur is None:
        want = "v1-diagnostic" if chain == "development" else "none"
        if pred.get("kind") != want:
            problems.append(
                f"the first campaign of the {chain} chain names predecessor kind {want!r}"
            )
        if before != 0:
            problems.append("the first campaign of a chain counts 0 sets consumed before it")
    else:
        if cur not in others:
            problems.append(f"the predecessor {cur!r} is not a campaign under {root}")
        else:
            pdecl, psha = others[cur]
            if psha != pred.get("campaign_declaration_sha256"):
                problems.append("the predecessor's declaration differs from its declared SHA-256")
            if pdecl.get("chain") != chain:
                problems.append("the predecessor belongs to another chain")
            pcamp = Campaign(root, cur, camp.strict, pdecl, psha)
            entries, jp = read_journal(pcamp)
            problems += [f"predecessor journal: {p}" for p in jp]
            for ex, st in executions(entries).items():
                if "started" in st and "closed" not in st and "reconciled" not in st:
                    problems.append(f"the predecessor's execution {ex} has no closure")
            consumed = budget_state(pcamp, entries)["chain_sets_consumed"]
            if before != consumed:
                problems.append(
                    f"the declaration counts {before} sets consumed before it; the predecessor "
                    f"line consumed {consumed}"
                )
        seen = cur
        while seen in others and seen not in ancestors:
            ancestors.add(seen)
            seen = (others[seen][0].get("predecessor") or {}).get("campaign_id")

    def line_of(cid: str) -> set[str]:
        """The predecessors of a campaign under the root, following its declarations."""
        line, seen = set(), (others[cid][0].get("predecessor") or {}).get("campaign_id")
        while seen is not None and seen not in line:
            line.add(seen)
            nxt = others.get(seen)
            seen = (nxt[0].get("predecessor") or {}).get("campaign_id") if nxt else None
        return line

    for other, (odecl, _) in others.items():
        if odecl.get("chain") != chain or other in ancestors:
            continue
        if camp.campaign_id in line_of(other):
            # A successor exists: no new set starts here; reconciliation, metrics and the
            # integrity report of this campaign still work.
            camp.superseded = True
        else:
            problems.append(
                f"campaign {other!r} of the same chain is neither a predecessor nor a successor"
            )
    return problems


def open_campaign(root: str | None, campaign_id: str) -> Campaign:
    """Load and check a campaign declaration. Under the default root the campaign is
    strict (eligibility ``campaign``); under any other root, inside the project, it is a
    diagnostic."""
    problems = campaign_id_problems(campaign_id)
    if problems:
        refuse("no campaign", problems)
    default = inside_project(DEFAULT_ROOT, "the default campaigns root")
    r = inside_project(root, "the campaigns root") if root else default
    strict = r == default
    if not strict and (default == r or default in r.parents):
        raise SystemExit("a diagnostic root cannot be inside the campaigns directory")
    camp = Campaign(r, campaign_id, strict)
    if camp.dir.resolve().parent != r:
        refuse("no campaign", [f"the campaign folder {camp.dir} is not directly under {r}"])
    path = camp.dir / "declaration.json"
    if not path.is_file():
        raise SystemExit(f"no declaration at {path}")
    data = path.read_bytes()
    camp.declaration_sha256 = hashlib.sha256(data).hexdigest()
    decl = json.loads(data)
    camp.declaration = decl
    p = camp.problems
    if decl.get("format") != DECLARATION_FORMAT:
        p.append(f"declaration format {decl.get('format')!r}")
    if decl.get("campaign_id") != campaign_id:
        p.append(f"declaration campaign_id {decl.get('campaign_id')!r} is not {campaign_id!r}")
    if decl.get("eligibility") != camp.eligibility:
        p.append(
            f"declaration eligibility {decl.get('eligibility')!r}, but this root gives "
            f"{camp.eligibility!r}"
        )
    if decl.get("chain") not in ("development", "confirmation"):
        p.append(f"declaration chain {decl.get('chain')!r}")
    if decl.get("harness_sha256") != HARNESS_SHA256:
        p.append("the declaration names another harness (SHA-256)")
    if decl.get("comparator") != CMP.identity():
        p.append(
            "the declaration's comparator (SHA-256, schema, version, profiles) is not this one"
        )
    budget = decl.get("budget") or {}
    k, n, ceiling = budget.get("K"), budget.get("N"), budget.get("chain_ceiling")
    if strict and (k, n, ceiling) != (3, 3, 6):
        p.append(f"budget K={k}, N={n}, chain ceiling={ceiling} is not 3, 3, 6 (Amendment 4)")
    if len(decl.get("generation_configurations") or []) != k:
        p.append("the declaration does not have K generation configurations")
    try:
        ids = [c["id"] for c in camp.cases()]
        for s in ("1", "2"):
            slot = ((decl.get("analysis") or {}).get("slots") or {}).get(s) or {}
            if order_sha256([c for c in _ordered(ids, slot.get("order", "index"))]) != slot.get(
                "order_sha256"
            ):
                p.append(f"slot {s}: the permutation does not match its declared SHA-256")
    except (KeyError, SystemExit) as exc:
        p.append(f"declaration population: {exc}")
    if not isinstance(decl.get("affinity"), str) or "-" not in decl.get("affinity", ""):
        p.append("the declaration does not declare the affinity of its executions (e.g. 8-31)")
    if (decl.get("overhead") or {}).get("double_hash") is not True:
        p.append("the declaration does not record the overhead decision (double hash kept)")
    if strict:
        p += [f"declaration: {x}" for x in committed_problems(path)]
        p += strict_declaration_problems(decl)
        p += chain_problems(camp)
    return camp


def affinity_problems(camp: Campaign, cpus: str) -> list[str]:
    """Every execution of a campaign runs with the declared affinity (Amendment 4,
    clarifications: the two slots share one configuration, affinity included)."""
    want = camp.declaration.get("affinity")
    return [] if cpus == want else [f"affinity {cpus!r} is not the declared {want!r}"]


def refuse(message: str, details: list[str] | None = None) -> None:
    for d in (details or [])[:40]:
        print("  REFUSED", d, flush=True)
    raise SystemExit(f"refused: {message}")


class _FileLock:
    """An operating-system lock on a small file next to the journal, so that two
    processes never append at the same time (released when the process ends)."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fh = open(self.path, "a+b")
        for _ in range(100):
            try:
                if sys.platform == "win32":
                    import msvcrt

                    self.fh.seek(0)
                    msvcrt.locking(self.fh.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl

                    fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except OSError:
                time.sleep(0.1)
        self.fh.close()
        raise SystemExit(f"the journal lock {self.path} is held by another process")

    def __exit__(self, *exc):
        if sys.platform == "win32":
            import msvcrt

            self.fh.seek(0)
            msvcrt.locking(self.fh.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
        self.fh.close()


def read_journal(camp: Campaign) -> tuple[list[dict], list[str]]:
    """The journal's entries and the problems of its hash chain."""
    if not camp.journal.exists():
        return [], []
    entries, problems = [], []
    prev = "0" * 64
    for n, line in enumerate(camp.journal.read_bytes().split(b"\n")):
        if not line:
            continue
        try:
            e = json.loads(line)
        except ValueError:
            problems.append(f"journal line {n + 1} is not valid JSON")
            break
        if e.get("format") != JOURNAL_FORMAT or e.get("seq") != len(entries):
            problems.append(f"journal line {n + 1}: format or sequence number is wrong")
        if e.get("prev_sha256") != prev:
            problems.append(f"journal line {n + 1}: the hash chain is broken")
        if (e.get("identity") or {}).get("campaign_id") != camp.campaign_id:
            problems.append(f"journal line {n + 1}: another campaign")
        prev = hashlib.sha256(line).hexdigest()
        e["_sha256"] = prev
        entries.append(e)
    return entries, problems


def append_journal(camp: Campaign, kind: str, identity: dict, payload: dict, *, check=None) -> str:
    """Append one entry (hash-chained); returns its SHA-256. With ``check``, a function of
    the journal's entries returning refusals, the check and the append happen under the same
    lock, so that two executions of one unit can never both start."""
    with _FileLock(camp.dir / "journal.lock"):
        entries, problems = read_journal(camp)
        if problems:
            raise SystemExit(f"journal integrity: {problems[:3]}; nothing appended")
        if check is not None:
            refused = check(entries)
            if refused:
                refuse(f"{kind} not written", refused)
        entry = {
            "format": JOURNAL_FORMAT,
            "seq": len(entries),
            "prev_sha256": entries[-1]["_sha256"] if entries else "0" * 64,
            "utc": utc_now(),
            "kind": kind,
            "identity": identity,
            "payload": payload,
        }
        line = canonical_json(mask_user(entry))
        with open(camp.journal, "ab") as fh:
            fh.write(line + b"\n")
            fh.flush()
            os.fsync(fh.fileno())
        return hashlib.sha256(line).hexdigest()


def write_lock(camp: Campaign, identity: dict, unit: dict, reason: str, evidence: list) -> str:
    """The lock marker of a divergence, keyed by the campaign, and its journal entry."""
    camp.locks.mkdir(parents=True, exist_ok=True)
    entries, _ = read_journal(camp)
    marker = {
        "format": LOCK_FORMAT,
        "campaign_id": camp.campaign_id,
        "campaign_declaration_sha256": camp.declaration_sha256,
        "identity": identity,
        "unit": unit,
        "reason": reason,
        "evidence": evidence,
        "budget": budget_state(camp, entries),
        "utc": utc_now(),
        "accepted_risk": (
            "Until the maintainer commits this marker and the journal, they exist only on "
            "disk and could be deleted or altered by hand; only the commit makes that visible."
        ),
    }
    name = f"lock-{datetime.now(UTC).strftime('%Y%m%dT%H%M%S%fZ')}-{identity['execution_id']}.json"
    sha = write_json(camp.locks / name, marker)
    append_journal(
        camp,
        "divergence",
        identity,
        {"lock": f"locks/{name}", "lock_sha256": sha, "unit": unit, "reason": reason},
    )
    print(f"LOCK written: {camp.locks / name} (SHA-256 {sha}); the campaign is blocked", flush=True)
    return sha


def resolutions(camp: Campaign) -> tuple[set[str], list[str]]:
    """The lock hashes named by valid resolution records, and the problems found. In a
    strict campaign a resolution counts only if it is committed unchanged and applies a rule
    registered in the declaration."""
    named, problems = set(), []
    rules = {r.get("id") for r in (camp.declaration.get("rules") or {}).get("resolution", [])}
    if not camp.resolutions.is_dir():
        return named, problems
    for f in sorted(camp.resolutions.glob("*.json")):
        try:
            r = read_json(f)
        except ValueError:
            problems.append(f"{f.name}: not valid JSON")
            continue
        if r.get("format") != RESOLUTION_FORMAT or r.get("campaign_id") != camp.campaign_id:
            problems.append(f"{f.name}: not a resolution of this campaign")
            continue
        if r.get("rule") not in rules:
            problems.append(f"{f.name}: rule {r.get('rule')!r} is not registered")
            continue
        if camp.strict:
            found = committed_problems(f)
            if found:
                problems.append(f"{f.name}: {found}")
                continue
        named.add(r.get("lock_sha256"))
    return named, problems


def deleted_locks(camp: Campaign) -> list[tuple[str, str]]:
    """Lock markers that were committed and later deleted: (path, SHA-256 of the deleted
    bytes). Only in a strict campaign (the campaign directory is in git)."""
    if not camp.strict:
        return []
    out = []
    names = git(camp.dir, "log", "--diff-filter=D", "--name-only", "--format=", "--", "locks")
    top = Path(git(camp.dir, "rev-parse", "--show-toplevel") or ".")
    for rel in sorted(set(names.split())):
        commit = git(top, "log", "-1", "--diff-filter=D", "--format=%H", "--", rel)
        blob = git_blob(top, f"{commit}^:{rel}") if commit else None
        out.append((rel, hashlib.sha256(blob).hexdigest() if blob else "unknown"))
    return out


def executions(entries: list[dict]) -> dict[str, dict]:
    """The state of every execution in the journal: its started, closed, interrupted and
    reconciled entries."""
    out: dict[str, dict] = {}
    for e in entries:
        ex = (e.get("identity") or {}).get("execution_id")
        if not ex:
            continue
        st = out.setdefault(ex, {"identity": e["identity"]})
        if e["kind"] in ("started", "closed", "interrupted", "reconciled", "process"):
            st.setdefault(e["kind"], []).append(e)
    return out


def blocking_problems(camp: Campaign) -> list[str]:
    """Why every campaign mode must refuse now: a broken journal, a lock marker or a
    divergence without a committed resolution, a deleted lock, or a started execution
    without a closure."""
    entries, problems = read_journal(camp)
    named, res_problems = resolutions(camp)
    problems += [f"resolution: {p}" for p in res_problems]
    if camp.locks.is_dir():
        for f in sorted(camp.locks.glob("lock-*.json")):
            if file_sha256(f) not in named:
                problems.append(f"lock marker {f.name} has no committed resolution")
    for e in entries:
        if e["kind"] == "divergence" and e["payload"].get("lock_sha256") not in named:
            problems.append(f"journal entry {e['seq']}: divergence without a resolution")
    for rel, sha in deleted_locks(camp):
        if sha not in named:
            problems.append(f"lock marker {rel} was deleted from git without a resolution")
    for ex, st in executions(entries).items():
        if "started" in st and "closed" not in st and "reconciled" not in st:
            problems.append(f"execution {ex} started and has no verified closure")
    return problems


def budget_state(camp: Campaign, entries: list[dict]) -> dict:
    """Sets consumed (a set consumes budget when its first generation starts)."""
    started = sorted(
        {
            e["identity"]["set"]
            for e in entries
            if e["kind"] == "started" and e["identity"].get("generation") is not None
        }
    )
    budget = camp.declaration.get("budget") or {}
    before = int(camp.declaration.get("chain_sets_consumed_before", 0))
    return {
        "sets_started_in_campaign": started,
        "chain_sets_consumed_before": before,
        "chain_sets_consumed": before + len(started),
        "chain_ceiling": budget.get("chain_ceiling"),
        "campaign_N": budget.get("N"),
    }


def accepted_set(entries: list[dict]) -> dict | None:
    return next((e for e in entries if e["kind"] == "accepted"), None)


def new_execution_identity(camp: Campaign, mode: str, set_number, attempt: int, **unit) -> dict:
    head = git(HARNESS_PATH.parent, "rev-parse", "HEAD")
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    return {
        **camp.common_identity(set_number),
        **unit,
        "execution_id": f"{stamp}-{os.getpid()}-{secrets.token_hex(4)}",
        "attempt": attempt,
        "eligibility": camp.eligibility,
        "origin": {"mode": mode, "harness_sha256": HARNESS_SHA256, "harness_commit": head},
    }


def campaign_refusals(camp: Campaign) -> list[str]:
    """The refusals every campaign mode applies: the declaration, R2 in a strict campaign,
    and the blocking state."""
    problems = list(camp.problems)
    _, harness = harness_problems()
    if camp.strict:
        problems += [f"harness: {p}" for p in harness]
    elif harness:
        print(f"diagnostic: R2 not enforced ({len(harness)} finding(s) recorded)", flush=True)
    problems += blocking_problems(camp)
    return problems


# --- the pool (PIDs recorded as they start, dispatch checked in every worker) -----------


def _worker_init(reports, declared_dispatch: dict) -> None:
    """Worker initializer: the same setup as ``refute.core.runner.init_worker`` (one BLAS
    thread, the Agg backend), then the thread-pool and dispatch checks before the first
    task. The worker reports its PID, its table's SHA-256 and its problems; a problem stops
    the worker (the pool breaks and the execution ends)."""
    from refute.core.runner import init_worker

    init_worker()
    table, digest, problems = dispatch_problems(declared_dispatch)
    problems = [*problems, *single_thread_problems()]
    reports.put(
        {
            "pid": os.getpid(),
            "utc": utc_now(),
            "dispatch_table_sha256": digest,
            "dispatch_table": table if problems else None,
            "threadpools": thread_pools(),
            "thread_env": {v: os.environ.get(v) for v in THREAD_VARIABLES},
            "affinity_mask": affinity_mask(),
            "problems": problems,
        }
    )
    if problems:
        raise RuntimeError(f"worker {os.getpid()}: {problems[:3]}")


@dataclass
class PoolOutcome:
    results: dict = field(default_factory=dict)
    workers: dict = field(default_factory=dict)
    error: str | None = None
    stopped: str | None = None


def run_pool(fn, tasks: list, workers: int, declared_dispatch: dict, *, on_worker, on_result):
    """Run ``fn`` over ``tasks`` in new spawned worker processes, dispatching the tasks in
    the given order, at most two per worker in flight. ``on_worker(report)`` is called when a
    worker reports its start; ``on_result(index, result)`` for every result, and a non-empty
    return value stops the dispatch (no further task is submitted; the pending ones are
    cancelled; the running ones finish). Returns a PoolOutcome."""
    out = PoolOutcome()
    if not tasks:
        return out
    context = multiprocessing.get_context("spawn")
    reports = context.Queue()

    def drain():
        while True:
            try:
                r = reports.get_nowait()
            except queue_module.Empty:
                return
            out.workers[r["pid"]] = r
            on_worker(r)

    pool = cf.ProcessPoolExecutor(
        max_workers=min(workers, len(tasks)),
        mp_context=context,
        initializer=_worker_init,
        initargs=(reports, declared_dispatch),
    )
    pending: dict = {}
    nxt = 0
    try:
        while nxt < len(tasks) or pending:
            while out.stopped is None and nxt < len(tasks) and len(pending) < 2 * workers:
                pending[pool.submit(fn, tasks[nxt])] = nxt
                nxt += 1
            if not pending:
                break
            done, _ = cf.wait(pending, timeout=5, return_when=cf.FIRST_COMPLETED)
            drain()
            for fut in done:
                i = pending.pop(fut)
                if fut.cancelled():
                    continue
                exc = fut.exception()
                if exc is not None:
                    out.error = out.error or f"{type(exc).__name__}: {exc}"
                    out.stopped = out.stopped or "error"
                    continue
                out.results[i] = fut.result()
                stop = on_result(i, out.results[i])
                if stop and out.stopped is None:
                    out.stopped = stop
            if out.stopped is not None:
                for fut in list(pending):
                    if fut.cancel():
                        pending.pop(fut)
    except BaseException as exc:
        out.error = out.error or f"{type(exc).__name__}: {exc}"
        out.stopped = out.stopped or "interrupted"
        for fut in list(pending):
            fut.cancel()
        raise
    finally:
        pool.shutdown(wait=True, cancel_futures=True)
        time.sleep(0.2)
        drain()
    return out


def verify_closed(pids: list[int], timeout: float = 60.0) -> list[int]:
    """The recorded PIDs still running after waiting up to ``timeout`` seconds."""
    deadline = time.monotonic() + timeout
    alive = [p for p in pids if pid_running(p)]
    while alive and time.monotonic() < deadline:
        time.sleep(0.5)
        alive = [p for p in alive if pid_running(p)]
    return alive


class Execution:
    """One execution of a campaign mode that starts processes: ``started`` before the first
    dispatch, a ``process`` entry for every worker as it reports, then ``interrupted`` (if
    it ended by an exception) and ``closed`` once every recorded process has ended."""

    def __init__(self, camp: Campaign, identity: dict, payload: dict, unit: dict, check) -> None:
        """``check(entries)``: the refusals of this unit, evaluated under the journal lock
        together with the blocking state, immediately before ``started`` is appended."""
        self.camp, self.identity, self.unit = camp, identity, unit
        self.pids: list[int] = []
        self.lock_sha256: str | None = None
        self.later_events: list = []

        def full_check(entries):
            return blocking_problems(camp) + check(entries)

        append_journal(
            camp,
            "started",
            identity,
            {**payload, "unit": unit, "main_pid": os.getpid()},
            check=full_check,
        )

    def lock(self, reason: str, evidence: list) -> None:
        """A divergence, written at the instant it is detected: the first one writes the
        lock marker and the journal entry; every later one is written to the journal at
        once (kind ``event``) and listed again in the closure record."""
        if self.lock_sha256 is None:
            self.lock_sha256 = write_lock(self.camp, self.identity, self.unit, reason, evidence)
        else:
            self.later_events.append({"reason": reason, "evidence": evidence})
            append_journal(
                self.camp,
                "event",
                self.identity,
                {"reason": reason, "evidence": evidence, "lock_sha256": self.lock_sha256},
            )

    def worker(self, report: dict) -> None:
        self.pids.append(report["pid"])
        append_journal(
            self.camp,
            "process",
            self.identity,
            {"pid": report["pid"], "problems": report["problems"]},
        )
        if report["problems"]:
            # A worker whose dispatch or thread pools differ from the declaration is an
            # integrity divergence, never an infrastructure failure (section 5).
            self.lock("a worker's dispatch or thread pools differ from the declaration", [report])

    def interrupted(self, reason: str, details: dict) -> None:
        append_journal(self.camp, "interrupted", self.identity, {"reason": reason, **details})

    def close(self, payload: dict) -> bool:
        alive = verify_closed(self.pids)
        if alive:
            print(
                f"processes {alive} still running: no closure written; the execution stays "
                "unreconciled and blocks the campaign",
                flush=True,
            )
            return False
        # N-c: the harness and the comparator on disk at the end of the execution.
        on_disk = {
            "harness_sha256": file_sha256(HARNESS_PATH),
            "comparator_sha256": file_sha256(COMPARATOR_PATH),
        }
        unchanged = on_disk == {
            "harness_sha256": HARNESS_SHA256,
            "comparator_sha256": COMPARATOR_SHA256_AT_START,
        }
        append_journal(
            self.camp,
            "closed",
            self.identity,
            {
                **payload,
                "pids_verified_ended": sorted(self.pids),
                "files_on_disk_at_close": on_disk,
                "files_unchanged": unchanged,
                "lock_sha256": self.lock_sha256,
                "later_divergence_events": self.later_events,
            },
        )
        if not unchanged:
            write_lock(
                self.camp,
                self.identity,
                {"kind": "harness", "execution_id": self.identity["execution_id"]},
                "the harness or the comparator changed on disk during the execution",
                [on_disk],
            )
        return unchanged


class ObservationLog:
    """Every result of an execution as it arrives, one JSON line per case (masked, flushed
    to the operating system at once; synchronized to disk at a divergence and at the end):
    an interruption after a detection keeps every observation made until then."""

    def __init__(self, path: Path) -> None:
        self.path = inside_project(path, "the observations file")
        self.fh = open(self.path, "xb")

    def append(self, obj, *, sync: bool = False) -> None:
        self.fh.write(canonical_json(mask_user(obj)) + b"\n")
        self.fh.flush()
        if sync:
            os.fsync(self.fh.fileno())

    def close(self) -> str:
        self.fh.flush()
        os.fsync(self.fh.fileno())
        self.fh.close()
        return file_sha256(self.path)


# --- generation modes -------------------------------------------------------------------


def _set_generation_lists(entries: list[dict], set_number: int) -> dict[int, list[dict]]:
    """Every execution of every generation of a set, in journal order."""
    out: dict[int, list[dict]] = {}
    for ex, st in executions(entries).items():
        ident = st["identity"]
        if ident.get("set") == set_number and ident.get("generation") is not None:
            if ident["origin"]["mode"] == "generate" and "started" in st:
                out.setdefault(ident["generation"], []).append({"execution_id": ex, **st})
    return out


def _set_generations(entries: list[dict], set_number: int) -> dict[int, dict]:
    """The generations of a set: generation -> its (first) execution. Two executions of one
    generation are refused at their start and found by duplicate_generations."""
    return {g: lst[0] for g, lst in _set_generation_lists(entries, set_number).items()}


def duplicate_generations(entries: list[dict], set_number: int) -> list[str]:
    return [
        f"generation {g} of set {set_number} has {len(lst)} executions"
        for g, lst in sorted(_set_generation_lists(entries, set_number).items())
        if len(lst) > 1
    ]


def generation_refusals(camp: Campaign, entries: list[dict], s: int, g: int) -> list[str]:
    """The set and generation rules of section 8 (budget, order, no completion of an
    interrupted set, nothing after an accepted set, one execution per generation)."""
    problems = duplicate_generations(entries, s)
    if camp.superseded:
        problems.append("a successor campaign of the chain exists; no generation starts here")
    budget = camp.declaration["budget"]
    if accepted_set(entries) is not None:
        problems.append("the campaign already has an accepted set; no new generation starts")
    gens = _set_generations(entries, s)
    started_sets = budget_state(camp, entries)["sets_started_in_campaign"]
    if not gens:
        if g != 1:
            problems.append(f"a new set starts with generation 1, not {g}")
        if s != (max(started_sets) + 1 if started_sets else 1):
            problems.append(f"set {s} is not the next set (sets started: {started_sets})")
        if s > budget["N"]:
            problems.append(f"set {s} is beyond the campaign's N = {budget['N']}")
        state = budget_state(camp, entries)
        if state["chain_sets_consumed"] + 1 > budget["chain_ceiling"]:
            problems.append(
                f"the chain's ceiling of {budget['chain_ceiling']} sets is reached "
                f"({state['chain_sets_consumed']} consumed): no new set starts"
            )
        for earlier in started_sets:
            eg = _set_generations(entries, earlier)
            done = all("closed" in eg.get(k, {}) for k in range(1, budget["K"] + 1))
            broken = any("interrupted" in x or "reconciled" in x for x in eg.values())
            if not done and not broken:
                problems.append(f"set {earlier} has not ended (neither complete nor interrupted)")
    else:
        if any("interrupted" in x or "reconciled" in x for x in gens.values()):
            problems.append(
                f"set {s} has an interrupted generation: it is consumed, never completed"
            )
        if g != len(gens) + 1:
            problems.append(f"generation {g} is not the next generation of set {s}")
    if not 1 <= g <= budget["K"]:
        problems.append(f"generation {g} is outside 1..{budget['K']}")
    return problems


def mode_generate(args) -> int:
    camp = open_campaign(args.root, args.campaign)
    checkout = refute_checkout()
    problems = campaign_refusals(camp)
    problems += generator_problems(checkout)
    problems += [f"thread pools: {p}" for p in single_thread_problems()]
    declared = camp.declaration["dispatch"]
    main_table, main_digest, dproblems = dispatch_problems(declared)
    problems += dproblems
    entries, _ = read_journal(camp)
    problems += generation_refusals(camp, entries, args.set, args.generation)
    problems += affinity_problems(camp, args.cpus)
    if camp.strict:
        problems += prerequisite_problems(camp.declaration)
    if problems:
        refuse(f"generation {args.set}.{args.generation} not started", problems)
    config = camp.declaration["generation_configurations"][args.generation - 1]
    out_dir = inside_project(args.out, "--out")
    if args.cache:
        inside_project(args.cache, "--cache")
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = f"set{args.set}-gen{args.generation}"
    paths = {
        "manifest": out_dir / f"manifest-{stem}.json",
        "block_index": out_dir / f"blocks-{stem}.json",
        "execution": out_dir / f"execution-{stem}.json",
    }
    existing = [str(p) for p in paths.values() if p.exists()]
    if existing:
        refuse("output files exist; nothing is ever replaced", existing)
    cache = Path(args.cache) if args.cache else None
    if cache is not None:
        cache.mkdir(parents=True, exist_ok=True)
    cases = _ordered(camp.cases(), config["order"])
    identity = new_execution_identity(camp, "generate", args.set, 1, generation=args.generation)
    machine = MachineRecord(camp.declaration.get("machine_declared") or {})
    started_utc = utc_now()
    t0 = time.perf_counter()
    unit = {"kind": "generation", "set": args.set, "generation": args.generation}
    obs_path = out_dir / f"observations-{stem}-{identity['execution_id']}.jsonl"
    ex = Execution(
        camp,
        identity,
        {
            "configuration": config,
            "cases": len(cases),
            "store": cache is not None,
            "out": str(out_dir),
            "observations": str(obs_path),
        },
        unit,
        lambda entries: generation_refusals(camp, entries, args.set, args.generation),
    )
    obs = ObservationLog(obs_path)
    print(
        f"generate {camp.campaign_id} set {args.set} generation {args.generation}: "
        f"{len(cases)} cases, {config['workers']} workers, order {config['order']}",
        flush=True,
    )
    events: list[dict] = []

    def on_result(i, r):
        obs.append(r, sync=bool(r["problems"]))  # before the lock: the observation is kept
        if r["problems"]:
            events.append({"case": r["case"], "problems": r["problems"]})
            ex.lock(
                "integrity problem while building cases",
                [{**events[-1], "observations": str(obs_path)}],
            )
            return "integrity"
        return None

    def write_evidence(results: dict, workers: dict) -> str:
        """Everything observed before an integrity stop: the entries, blocks, problems and
        operational data of every case built (the bytes are not kept, section 3)."""
        path = out_dir / f"evidence-{stem}-{identity['execution_id']}.json"
        write_json(
            path,
            {
                "identity": identity,
                "events": events,
                "workers": {str(k): v for k, v in sorted(workers.items())},
                "cases": [results[i] for i in sorted(results)],
            },
        )
        return str(path)

    tasks = [(c, str(cache) if cache else None, None) for c in cases]
    try:
        outcome = run_pool(
            generate_task,
            tasks,
            config["workers"],
            declared,
            on_worker=ex.worker,
            on_result=on_result,
        )
    except BaseException as exc:
        obs_sha = obs.close()
        ex.interrupted("exception", {"exception": f"{type(exc).__name__}: {exc}"})
        ex.close(
            {"result": "interrupted", "observations": str(obs_path), "observations_sha256": obs_sha}
        )
        raise SystemExit(f"interrupted: {exc}; the set is incomplete and consumed") from None
    wall = time.perf_counter() - t0
    obs_sha = obs.close()
    kept = {"observations": str(obs_path), "observations_sha256": obs_sha}
    if ex.lock_sha256 is not None:
        evidence = write_evidence(outcome.results, outcome.workers)
        ex.close({"result": "divergence", "evidence": evidence, **kept})
        return 2
    if outcome.error or len(outcome.results) != len(tasks):
        ex.interrupted(
            "error",
            {"error": outcome.error, "results": len(outcome.results), "tasks": len(tasks)},
        )
        ex.close({"result": "interrupted", **kept})
        print(f"generation interrupted: {outcome.error}; the set is incomplete and consumed")
        return 3
    results = [outcome.results[i] for i in range(len(tasks))]
    common = camp.common_identity(args.set)
    blocks_doc = {
        "format": BLOCKS_FORMAT,
        "identity": common,
        "block_size": BLOCK_SIZE,
        "cases": {r["case"]: r["blocks"] for r in sorted(results, key=lambda r: r["case"])},
    }
    blocks_sha = write_json(paths["block_index"], blocks_doc)
    manifest = {
        "format": MANIFEST_FORMAT,
        "serialization": SERIALIZATION,
        "population": camp.declaration["population"],
        "harness_sha256": HARNESS_SHA256,
        "generator": {
            "commit": GENERATOR_COMMIT,
            "synthetic_py_sha256": GENERATOR_SYNTHETIC_SHA256,
        },
        "thresholds": {"snr_gate": 7.1, "hidden_min_snr": 5.0},
        "call_sequence": CALL_SEQUENCE,
        "identity": common,
        "block_size": BLOCK_SIZE,
        "block_index_sha256": blocks_sha,
        "cases": [r["entry"] for r in sorted(results, key=lambda r: r["case"])],
    }
    manifest_sha = write_json(paths["manifest"], manifest)
    seconds = [r["operational"]["seconds"] for r in results]
    record = {
        "format": EXECUTION_FORMAT,
        "identity": identity,
        "configuration": {
            **config,
            "affinity": args.cpus,
            "affinity_mask": affinity_mask(),
            "random_generator": "numpy.random.default_rng (PCG64)",
            "thread_env_inherited": INHERITED_THREAD_ENV,
            "thread_env": {v: os.environ.get(v) for v in THREAD_VARIABLES},
            "threadpools_main": thread_pools(),
            "dispatch": {
                "declared_environment": declared.get("environment"),
                "main_table_sha256": main_digest,
                "main_table": main_table,
                "workers": {
                    str(pid): {
                        k: w[k]
                        for k in (
                            "dispatch_table_sha256",
                            "threadpools",
                            "thread_env",
                            "affinity_mask",
                        )
                    }
                    for pid, w in sorted(outcome.workers.items())
                },
            },
            "store": cache is not None,
        },
        "checkout": checkout,
        "machine": machine.result(checkout["refute_root"]),
        "timings": {
            "started_utc": started_utc,
            "ended_utc": utc_now(),
            "wall_seconds": round(wall, 3),
            "per_case_mean_seconds": round(sum(seconds) / len(seconds), 3),
            "per_case_max_seconds": max(seconds),
        },
        "manifest_sha256": manifest_sha,
        "block_index_sha256": blocks_sha,
        "artifacts": {k: str(v) for k, v in paths.items() if k != "execution"},
        "cases": {r["case"]: r["operational"] for r in results},
        "sequence": [
            [r["operational"]["pid"], r["operational"]["sequence_position"], r["case"]]
            for r in sorted(results, key=lambda r: r["operational"]["started_utc"])
        ],
    }
    execution_sha = write_json(paths["execution"], record)
    closed = ex.close(
        {
            "result": "generated",
            **kept,
            "manifest": str(paths["manifest"]),
            "manifest_sha256": manifest_sha,
            "block_index": str(paths["block_index"]),
            "block_index_sha256": blocks_sha,
            "execution_record": str(paths["execution"]),
            "execution_record_sha256": execution_sha,
            "wall_seconds": round(wall, 3),
        }
    )
    print(
        f"generated {len(results)} cases in {wall:.1f} s; manifest {manifest_sha}; "
        f"block index {blocks_sha}",
        flush=True,
    )
    if not closed:
        return 3
    return _compare_with_set(camp, identity, args.set, args.generation)


def _closed_generation(camp: Campaign, st: dict) -> tuple[dict | None, list[str]]:
    """The artifacts of a closed generation, re-read and checked by hash."""
    if "closed" not in st or st["closed"][0]["payload"].get("result") != "generated":
        return None, ["not closed as generated"]
    pay = st["closed"][0]["payload"]
    problems = []
    for key in ("manifest", "block_index", "execution_record"):
        p = Path(pay[key])
        if not p.is_file():
            problems.append(f"{key} {p} is missing")
        elif file_sha256(p) != pay[f"{key}_sha256"]:
            problems.append(f"{key} {p}: SHA-256 differs from the journal")
    if problems:
        return None, problems
    rec = read_json(Path(pay["execution_record"]))
    man = read_json(Path(pay["manifest"]))
    if man.get("identity") != camp.common_identity(st["identity"]["set"]):
        problems.append("the manifest's common identity is not the campaign's")
    if man.get("block_index_sha256") != pay["block_index_sha256"]:
        problems.append("the manifest points to another block index")
    if rec.get("identity") != st["identity"]:
        problems.append("the execution record's identity is not the journal's")
    if rec.get("identity", {}).get("eligibility") != camp.eligibility:
        problems.append("the execution record's eligibility is not the campaign's")
    if rec.get("manifest_sha256") != pay["manifest_sha256"]:
        problems.append("the execution record points to another manifest")
    return pay, problems


def _compare_with_set(camp: Campaign, identity: dict, s: int, g: int) -> int:
    """After a generation: its manifest and block index must be byte-identical to those of
    the earlier generations of its set; otherwise the divergence is located and locked."""
    entries, _ = read_journal(camp)
    gens = _set_generations(entries, s)
    mine, problems = _closed_generation(camp, gens[g])
    if problems:
        write_lock(
            camp, identity, {"kind": "generation", "set": s, "generation": g}, "artifacts", problems
        )
        return 2
    for k in sorted(gens):
        if k == g:
            continue
        other, problems = _closed_generation(camp, gens[k])
        if problems == ["not closed as generated"]:
            continue  # an interrupted generation: its set is consumed and never accepted
        if problems:
            write_lock(
                camp,
                identity,
                {"kind": "generation", "set": s, "generation": k},
                "the artifacts of an earlier generation are missing or differ from the journal",
                problems,
            )
            return 2
        if (other["manifest_sha256"], other["block_index_sha256"]) == (
            mine["manifest_sha256"],
            mine["block_index_sha256"],
        ):
            continue
        report = CMP.compare_manifests(
            read_json(Path(other["manifest"])),
            read_json(Path(mine["manifest"])),
            read_json(Path(other["block_index"])),
            read_json(Path(mine["block_index"])),
        )
        rpath = Path(mine["manifest"]).with_name(f"divergence-set{s}-gen{k}-gen{g}.json")
        rsha = write_json(rpath, report)
        write_lock(
            camp,
            identity,
            {"kind": "generation", "set": s, "generation": g, "against": k},
            "the generation differs from an earlier generation of its set",
            [
                {"manifest": other["manifest"], "sha256": other["manifest_sha256"]},
                {"manifest": mine["manifest"], "sha256": mine["manifest_sha256"]},
                {
                    "report": str(rpath),
                    "sha256": rsha,
                    "cases_differing": report["cases_differing"],
                },
            ],
        )
        return 2
    earlier = sorted(k for k in gens if k != g)
    if earlier:
        print(f"set {s}: generation {g} is byte-identical to generations {earlier}", flush=True)
    else:
        print(f"set {s}: generation {g} is the first of its set", flush=True)
    return 0


def mode_check_set(args) -> int:
    camp = open_campaign(args.root, args.campaign)
    problems = campaign_refusals(camp)
    if problems:
        refuse(f"set {args.set} not checked", problems)
    entries, _ = read_journal(camp)
    k = camp.declaration["budget"]["K"]
    gens = _set_generations(entries, args.set)
    identity = new_execution_identity(camp, "check-set", args.set, 1)
    unit = {"kind": "set", "set": args.set}
    duplicates = duplicate_generations(entries, args.set)
    if duplicates:
        write_lock(camp, identity, unit, "a generation has more than one execution", duplicates)
        return 2
    found, damaged = [], []
    pays = {}
    for g in range(1, k + 1):
        if g not in gens:
            found.append(f"generation {g} has not run")
            continue
        pay, p = _closed_generation(camp, gens[g])
        if p and p != ["not closed as generated"]:
            damaged += [f"generation {g}: {x}" for x in p]
        found += [f"generation {g}: {x}" for x in p]
        pays[g] = pay
    if damaged:
        write_lock(camp, identity, unit, "generation artifacts missing or changed", damaged)
        return 2
    if found:
        refuse(f"set {args.set} is not complete", found)
    manifests = {pays[g]["manifest_sha256"] for g in pays}
    blocks = {pays[g]["block_index_sha256"] for g in pays}
    if len(manifests) != 1 or len(blocks) != 1:
        write_lock(
            camp, identity, unit, "the K generations are not byte-identical", list(pays.values())
        )
        return 2
    candidate = read_json(Path(pays[1]["manifest"]))
    cand = {e["id"]: e["sha256"] for e in candidate["cases"]}
    blocking = []
    for other in budget_state(camp, entries)["sets_started_in_campaign"]:
        if other == args.set:
            continue
        values: dict[str, dict[str, int]] = {}
        for st in _set_generations(entries, other).values():
            pay, p = _closed_generation(camp, st)
            if p == ["not closed as generated"]:
                continue
            if p:
                write_lock(
                    camp, identity, unit, "the artifacts of another set are missing or changed", p
                )
                return 2
            for e in read_json(Path(pay["manifest"]))["cases"]:
                values.setdefault(e["id"], {}).setdefault(e["sha256"], 0)
                values[e["id"]][e["sha256"]] += 1
        for cid, counts in values.items():
            for sha, n in counts.items():
                if n >= 2 and cand.get(cid) != sha:
                    blocking.append(
                        {
                            "case": cid,
                            "set": other,
                            "value_in_2_or_more": sha,
                            "candidate": cand.get(cid),
                        }
                    )
    ref = camp.declaration.get("reference_manifest")
    if ref:
        rpath = Path(ref["path"])
        if not rpath.is_absolute():
            rpath = HARNESS_PATH.parent / rpath
        if not rpath.is_file() or file_sha256(rpath) != ref["sha256"]:
            refuse(
                "the reference manifest is missing or differs from its declared SHA-256",
                [str(rpath)],
            )
        reference = {e["id"]: e["sha256"] for e in read_json(rpath)["cases"]}
        for cid, sha in cand.items():
            if reference.get(cid) != sha:
                blocking.append({"case": cid, "reference": reference.get(cid), "candidate": sha})
        if set(reference) != set(cand):
            blocking.append({"reference_cases": len(reference), "candidate_cases": len(cand)})
    report = {
        "format": SET_REPORT_FORMAT,
        "identity": identity,
        "set": args.set,
        "generations": pays,
        "manifest_sha256": pays[1]["manifest_sha256"],
        "block_index_sha256": pays[1]["block_index_sha256"],
        "blocking_comparisons": blocking,
        "reference_manifest": ref,
    }
    rfile = camp.dir / f"set-{args.set}-check-{identity['execution_id']}.json"
    rsha = write_json(rfile, report)
    if blocking:
        write_lock(
            camp,
            identity,
            unit,
            "a blocking comparison found a difference",
            [{"report": str(rfile), "sha256": rsha, "differences": len(blocking)}],
        )
        return 2
    append_journal(
        camp,
        "accepted",
        identity,
        {
            "set": args.set,
            "manifest": pays[1]["manifest"],
            "manifest_sha256": pays[1]["manifest_sha256"],
            "block_index": pays[1]["block_index"],
            "block_index_sha256": pays[1]["block_index_sha256"],
            "report": str(rfile),
            "report_sha256": rsha,
        },
    )
    print(
        f"set {args.set} accepted: manifest {pays[1]['manifest_sha256']} (commit and freeze it "
        "manually, with the journal)",
        flush=True,
    )
    return 0


def _accepted_inputs(camp: Campaign, manifest_path: str) -> tuple[dict, dict, dict, int]:
    """The accepted set's manifest (it must be the file given) and block index."""
    entries, _ = read_journal(camp)
    acc = accepted_set(entries)
    if acc is None:
        refuse("the campaign has no accepted set")
    pay = acc["payload"]
    if file_sha256(Path(manifest_path)) != pay["manifest_sha256"]:
        refuse("the manifest given is not the accepted set's manifest", [manifest_path])
    blocks_path = Path(manifest_path).with_name(Path(pay["block_index"]).name)
    if not blocks_path.is_file():
        blocks_path = Path(pay["block_index"])
    if not blocks_path.is_file() or file_sha256(blocks_path) != pay["block_index_sha256"]:
        refuse("the accepted block index is missing or differs", [str(blocks_path)])
    manifest, blocks = read_json(Path(manifest_path)), read_json(blocks_path)
    set_number = acc["identity"]["set"]
    if manifest.get("identity") != camp.common_identity(set_number) or blocks.get(
        "identity"
    ) != camp.common_identity(set_number):
        refuse("the accepted manifest or block index carries another common identity")
    return manifest, blocks, pay, set_number


def analysis_units(entries: list[dict]) -> dict[tuple, dict]:
    """Every analysis unit (point, lot, slot) in the journal: the run directory fixed by its
    first execution, and its executions in order. A unit has exactly one run directory, so
    a case has at most one record per slot (the first valid observation; records are never
    replaced), and a second analysis of a unit in another folder is refused."""
    units: dict[tuple, dict] = {}
    for e in entries:
        ident = e.get("identity") or {}
        if e["kind"] != "started" or (ident.get("origin") or {}).get("mode") != "analyze":
            continue
        key = (ident.get("point"), ident.get("lot"), ident.get("slot"))
        unit = units.setdefault(key, {"run_dir": e["payload"].get("run_dir"), "executions": []})
        unit["executions"].append(ident["execution_id"])
    return units


def analysis_unit_refusals(entries: list[dict], key: tuple, run_dir: str) -> list[str]:
    unit = analysis_units(entries).get(key)
    if unit is not None and unit["run_dir"] != run_dir:
        return [
            f"the unit point {key[0]}, lot {key[1]}, slot {key[2]} is bound to "
            f"{unit['run_dir']}; it is never analyzed again in another folder"
        ]
    return []


def accepted_record_executions(camp: Campaign) -> dict[str, tuple]:
    """execution id -> (point, lot, slot, run directory) for the analysis executions that
    started and were closed (or reconciled) in the journal: the only executions whose
    records a campaign mode accepts, and only in their unit's run directory."""
    entries, _ = read_journal(camp)
    states = executions(entries)
    out = {}
    for key, unit in analysis_units(entries).items():
        for ex in unit["executions"]:
            st = states.get(ex, {})
            if "closed" in st or "reconciled" in st:
                out[ex] = (*key, unit["run_dir"])
    return out


def bound_run_dir(camp: Campaign, point: str, lot: int, slot: int) -> str | None:
    entries, _ = read_journal(camp)
    unit = analysis_units(entries).get((point, lot, slot))
    return unit["run_dir"] if unit else None


def lots_of(manifest: dict, size: int) -> list[list[str]]:
    ids = [c["id"] for c in manifest["cases"]]
    return [ids[i : i + size] for i in range(0, len(ids), size)]


def mode_regenerate(args) -> int:
    camp = open_campaign(args.root, args.campaign)
    checkout = refute_checkout()
    problems = campaign_refusals(camp) + generator_problems(checkout)
    problems += [f"thread pools: {p}" for p in single_thread_problems()]
    declared = camp.declaration["dispatch"]
    problems += dispatch_problems(declared)[2]
    problems += affinity_problems(camp, args.cpus)
    if problems:
        refuse(f"lot {args.lot} not regenerated", problems)
    manifest, blocks, _, set_number = _accepted_inputs(camp, args.manifest)
    lot = lots_of(manifest, camp.declaration["analysis"]["lot_size"])[args.lot]
    by_id = {c["id"]: c for c in camp.cases()}
    frozen = {e["id"]: e for e in manifest["cases"]}
    cache = inside_project(args.cache, "--cache")
    cache.mkdir(parents=True, exist_ok=True)
    identity = new_execution_identity(camp, "regenerate", set_number, 1, lot=args.lot)
    obs_path = cache / f"observations-lot{args.lot:04d}-{identity['execution_id']}.jsonl"
    ex = Execution(
        camp,
        identity,
        {"lot": args.lot, "cases": len(lot), "cache": str(cache), "observations": str(obs_path)},
        {"kind": "regeneration", "lot": args.lot},
        lambda entries: [],
    )
    obs = ObservationLog(obs_path)
    events: list[dict] = []

    def on_result(i, r):
        obs.append(r, sync=bool(r["problems"]))
        if r["problems"]:
            events.append({"case": r["case"], "problems": r["problems"]})
            ex.lock("regenerated inputs differ", [{**events[-1], "observations": str(obs_path)}])
            return "integrity"
        return None

    tasks = [
        (by_id[c], str(cache), {"entry": frozen[c], "blocks": blocks["cases"][c]}) for c in lot
    ]
    workers = camp.declaration["generation_configurations"][0]["workers"]
    try:
        outcome = run_pool(
            generate_task, tasks, workers, declared, on_worker=ex.worker, on_result=on_result
        )
    except BaseException as exc:
        kept = {"observations": str(obs_path), "observations_sha256": obs.close()}
        ex.interrupted("exception", {"exception": f"{type(exc).__name__}: {exc}"})
        ex.close({"result": "interrupted", **kept})
        raise SystemExit(f"regeneration interrupted: {exc}") from None
    kept = {"observations": str(obs_path), "observations_sha256": obs.close()}
    if ex.lock_sha256 is not None:
        ex.close({"result": "divergence", "events": events, **kept})
        return 2
    if outcome.error or len(outcome.results) != len(tasks):
        ex.interrupted("error", {"error": outcome.error})
        ex.close({"result": "interrupted", **kept})
        return 3
    stored = {r["case"]: r["stored"] for r in outcome.results.values()}
    if not ex.close({"result": "regenerated", "lot": args.lot, "stored": stored, **kept}):
        return 2
    print(
        f"lot {args.lot}: {len(lot)} inputs regenerated and checked "
        f"({sorted(set(stored.values()))})"
    )
    return 0


# --- analysis (sections 9 and 10) -------------------------------------------------------


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
    """An input missing from the cache, or a failure of the machine: the run stops and no
    result is written for the case (Amendment 2, N10)."""


class IntegrityEventError(RuntimeError):
    """An observed divergence (an input whose SHA-256 differs from the manifest): never an
    infrastructure failure; it writes a lock (section 12)."""


INFRASTRUCTURE = (InfrastructureError, MemoryError, OSError)


def condition_outcome(data, plan, entry, catalogs, scan) -> dict:
    """The complete scientific record of one condition (the typed ``build_result``) and the
    harness's own outcomes. An exception propagates: the case's record has status
    ``error``."""
    from refute.packs.tess.calibration import signal_verdict
    from refute.packs.tess.pipeline import analyze_data, build_result

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
        "scientific": typed(result, "/scientific"),
        "harness_outcomes": typed(
            {
                "signal_identity": identity,
                "identity_factor": factor,
                "signal_verdict_without_eb_catalog": signal_verdict(result, ["eb_catalog"]),
            },
            "/harness_outcomes",
        ),
    }


def worker_configuration() -> dict:
    table = dispatch_table()
    return {
        "thread_env": {v: os.environ.get(v) for v in THREAD_VARIABLES},
        "threadpools": thread_pools(),
        "dispatch_table_sha256": hashlib.sha256(canonical_json(table)).hexdigest(),
    }


def analysis_record(entry: dict, blob: bytes, identity: dict, position: int) -> dict:
    """The complete result record of one case (``refute-population-result/3``), typed. The
    caller has checked the input's SHA-256."""
    started = utc_now()
    start = time.perf_counter()
    record: dict = {
        "format": RESULT_FORMAT,
        "identity": identity,
        "case": entry["id"],
        "input": {
            "sha256": hashlib.sha256(blob).hexdigest(),
            "manifest_entry_sha256": hashlib.sha256(canonical_json(entry)).hexdigest(),
        },
    }
    try:
        meta, arrays = deserialize(blob)
        data = parts_to_data(meta, arrays)
        plan = _plan()
        conditions = {"i": condition_outcome(data, plan, entry, None, None)}
        if meta["catalog"] is not None:
            from refute.packs.tess.ebcatalog import parse_catalog

            entries = parse_catalog(meta["catalog"]["text"], "population-catalog.csv")
            conditions["ii"] = condition_outcome(
                data, plan, entry, entries, meta["catalog"]["scan"]
            )
        record.update(status="analyzed", conditions=conditions)
    except INFRASTRUCTURE:
        raise
    except Exception:  # noqa: BLE001 - a permanent result with status "error", in full
        record.update(status="error", traceback=traceback.format_exc())
    record["configuration"] = worker_configuration()
    record["operational"] = typed(
        {
            "pid": os.getpid(),
            "seconds": round(time.perf_counter() - start, 3),
            "peak_memory_mb": peak_memory_mb(),
            "started_utc": started,
            "ended_utc": utc_now(),
            "sequence_position": position,
        },
        "/operational",
    )
    record["comparison"] = {"status": "pending", "report_sha256": None}
    record["integrity"] = "ok"
    return record


def read_input(cache: Path, entry: dict) -> bytes:
    path = cache / f"{entry['id']}.rpc"
    if not path.is_file():
        raise InfrastructureError("input file missing from the cache")
    blob = path.read_bytes()
    digest = hashlib.sha256(blob).hexdigest()
    if digest != entry["sha256"]:
        raise IntegrityEventError(
            f"input SHA-256 {digest} differs from the manifest {entry['sha256']}"
        )
    return blob


def analyze_task(task: tuple[dict, str, str, dict]) -> dict:
    """Analyze one case and write its record; an integrity event or an infrastructure
    failure writes nothing and is returned."""
    entry, cache, run_dir, identity = task
    position = _next_position()
    out = Path(run_dir) / "cases" / f"{entry['id']}.json"
    try:
        if out.exists():
            raise InfrastructureError("a result appeared after dispatch; it is never overwritten")
        blob = read_input(Path(cache), entry)
        record = analysis_record(entry, blob, identity, position)
        data = record_bytes(record)
        write_atomic(out, data)
        return {
            "case": entry["id"],
            "status": record["status"],
            "sha256": hashlib.sha256(data).hexdigest(),
            "pid": os.getpid(),
            "sequence_position": position,
        }
    except IntegrityEventError as exc:
        return {"case": entry["id"], "integrity": str(exc)}
    except INFRASTRUCTURE as exc:
        return {"case": entry["id"], "infrastructure": f"{type(exc).__name__}: {exc}"}


IDENTITY_KEYS = {
    "campaign_id",
    "campaign_declaration_sha256",
    "chain",
    "set",
    "point",
    "lot",
    "slot",
    "execution_id",
    "attempt",
    "eligibility",
    "origin",
}
ORIGIN_KEYS = {"mode", "harness_sha256", "harness_commit"}
CONDITION_KEYS = {"scientific", "harness_outcomes"}
OUTCOME_KEYS = {"signal_identity", "identity_factor", "signal_verdict_without_eb_catalog"}
CONFIGURATION_KEYS = {"thread_env", "threadpools", "dispatch_table_sha256"}
OPERATIONAL_KEYS = {
    "pid",
    "seconds",
    "peak_memory_mb",
    "started_utc",
    "ended_utc",
    "sequence_position",
}


SCIENTIFIC_KEYS = (
    "schema",
    "status",
    "verdict",
    "verdict_reason",
    "candidate",
    "tests",
    "expected_tests",
    "test_plan",
    "key_values",
    "holdout_rounds",
)


def scientific_problems(sci) -> list[str]:
    """The minimal content of a complete scientific record (the output of ``build_result``
    at the four points): an analysis whose record lacks it is not a successful analysis
    (Amendment 4, clarifications of 2026-10-13)."""
    if not isinstance(sci, dict):
        return ["the scientific record is not an object"]
    problems = [f"scientific record without {k!r}" for k in SCIENTIFIC_KEYS if k not in sci]
    if sci.get("schema") != "refute-tess-verdict-1":
        problems.append(f"scientific schema {sci.get('schema')!r}")
    if sci.get("status") != "OK":
        problems.append(f"scientific status {sci.get('status')!r}")
    if sci.get("verdict") not in VERDICTS:
        problems.append(f"verdict {sci.get('verdict')!r} is not one of {VERDICTS}")
    tests = sci.get("tests")
    if not isinstance(tests, list) or not tests:
        problems.append("the scientific record has no tests")
    else:
        for t in tests:
            if not isinstance(t, dict) or not all(
                isinstance(t.get(k), str) for k in ("name", "status", "severity")
            ):
                problems.append("a test without a name, status or severity")
                break
    exp = sci.get("expected_tests")
    if not isinstance(exp, list) or not all(isinstance(x, str) for x in exp):
        problems.append("expected_tests is not a list of names")
    return problems


def validate_record(
    rec, entry: dict, expect: dict, *, extra_top: frozenset = frozenset()
) -> list[str]:
    """Problems of a result record against the closed schema of ``refute-population-result/3``
    (``expect``: identity values that must match, e.g. campaign, point, lot, slot)."""
    name = entry["id"]
    if not isinstance(rec, dict):
        return [f"{name}: not a JSON object"]
    problems = []
    status = rec.get("status")
    top = {"format", "identity", "case", "input", "status", "configuration", "operational"}
    top |= {"comparison", "integrity"} | set(extra_top)
    if status == "analyzed":
        top.add("conditions")
    elif status == "error":
        top.add("traceback")
    else:
        problems.append(f"{name}: status {status!r}")
    if set(rec) != top:
        problems.append(f"{name}: members {sorted(set(rec) ^ top)} differ from the schema")
    if rec.get("format") != RESULT_FORMAT:
        problems.append(f"{name}: format {rec.get('format')!r}")
    if rec.get("case") != entry["id"]:
        problems.append(f"{name}: case {rec.get('case')!r}")
    ident = rec.get("identity") or {}
    if set(ident) != IDENTITY_KEYS or set(ident.get("origin") or {}) != ORIGIN_KEYS:
        problems.append(f"{name}: identity members differ from the schema")
    for k, v in expect.items():
        if ident.get(k) != v:
            problems.append(f"{name}: identity {k} {ident.get(k)!r} is not {v!r}")
    inp = rec.get("input") or {}
    if inp.get("sha256") != entry["sha256"]:
        problems.append(f"{name}: input SHA-256 differs from the manifest")
    if inp.get("manifest_entry_sha256") != hashlib.sha256(canonical_json(entry)).hexdigest():
        problems.append(f"{name}: manifest entry SHA-256 differs")
    if status == "analyzed":
        conds = rec.get("conditions") or {}
        want = {"i", "ii"} if entry["class"] != "no_transit" else {"i"}
        if set(conds) != want:
            problems.append(f"{name}: conditions {sorted(conds)} are not {sorted(want)}")
        for c, o in conds.items():
            if not isinstance(o, dict) or set(o) != CONDITION_KEYS:
                problems.append(f"{name}: condition {c} members differ from the schema")
                continue
            if set(o["harness_outcomes"] or {}) != OUTCOME_KEYS:
                problems.append(f"{name}: condition {c} harness outcomes differ from the schema")
            problems += [
                f"{name}: condition {c}: {p}" for p in scientific_problems(o["scientific"])
            ]
    if set(rec.get("configuration") or {}) != CONFIGURATION_KEYS:
        problems.append(f"{name}: configuration members differ from the schema")
    if set(rec.get("operational") or {}) != OPERATIONAL_KEYS:
        problems.append(f"{name}: operational members differ from the schema")
    if rec.get("comparison") is None or set(rec["comparison"]) != {"status", "report_sha256"}:
        problems.append(f"{name}: comparison members differ from the schema")
    if rec.get("integrity") not in ("ok", "blocked"):
        problems.append(f"{name}: integrity {rec.get('integrity')!r}")
    problems += CMP.record_problems(rec, f"{name}:")
    return problems


def analysis_environment(point: str) -> tuple[dict, dict, dict, list[str]]:
    checkout = refute_checkout()
    binding, state, problems = binding_problems(point, checkout)
    return checkout, binding, state, problems


RUN_KEYS = (
    "campaign_id",
    "campaign_declaration_sha256",
    "point",
    "slot",
    "affinity",
    "binding",
    "checkout",
    "harness_sha256",
    "manifest_sha256",
    "plan",
    "fingerprint",
)


def _fingerprint(checkout: dict) -> dict:
    import refute

    env = numeric_environment()
    return {
        "python": env["python"],
        "numpy": env["numpy"],
        "numpy_blas": env["numpy_blas"],
        "threadpools": env["threadpools"],
        "thread_env": env["thread_env"],
        "affinity_mask": affinity_mask(),
        "commit": checkout["commit"],
        "refute_file": str(Path(refute.__file__).resolve()),
    }


def mode_analyze(args) -> int:
    camp = open_campaign(args.root, args.campaign)
    checkout, binding, state, problems = analysis_environment(args.point)
    problems = campaign_refusals(camp) + problems
    declared = camp.declaration["dispatch"]
    problems += dispatch_problems(declared)[2]
    if args.slot not in (1, 2):
        problems.append(f"slot {args.slot} is not 1 or 2")
    problems += affinity_problems(camp, args.cpus)
    run_dir = inside_project(args.out, "--out")
    inside_project(args.cache, "--cache")
    unit_key = (args.point, args.lot, args.slot)
    problems += analysis_unit_refusals(read_journal(camp)[0], unit_key, str(run_dir))
    if problems:
        refuse(f"{args.point} lot {args.lot} slot {args.slot} not analyzed", problems)
    manifest, _, _, set_number = _accepted_inputs(camp, args.manifest)
    manifest_sha = file_sha256(Path(args.manifest))
    lots = lots_of(manifest, camp.declaration["analysis"]["lot_size"])
    lot = set(lots[args.lot])
    slot_order = _ordered(
        [c["id"] for c in camp.cases()],
        camp.declaration["analysis"]["slots"][str(args.slot)]["order"],
    )
    order = [c for c in slot_order if c in lot]
    by_id = {e["id"]: e for e in manifest["cases"]}
    (run_dir / "cases").mkdir(parents=True, exist_ok=True)
    run = {
        "format": RESULT_FORMAT,
        "campaign_id": camp.campaign_id,
        "campaign_declaration_sha256": camp.declaration_sha256,
        "point": args.point,
        "slot": args.slot,
        "affinity": args.cpus,
        "binding": binding,
        "points_at_start": state,
        "checkout": checkout,
        "harness_sha256": HARNESS_SHA256,
        "manifest_sha256": manifest_sha,
        "plan": _plan().model_dump(mode="json"),
        "fingerprint": _fingerprint(checkout),
    }
    run_file = run_dir / "run.json"
    if run_file.exists():
        previous = read_json(run_file)
        differ = [k for k in RUN_KEYS if previous.get(k) != json.loads(canonical_json(run[k]))]
        if differ:
            refuse("resume with a different run", [f"{k} differs from {run_file}" for k in differ])
    else:
        write_json(run_file, run)
    entries, _ = read_journal(camp)
    attempts = [
        st
        for st in executions(entries).values()
        if st["identity"].get("point") == args.point
        and st["identity"].get("lot") == args.lot
        and st["identity"].get("slot") == args.slot
        and "started" in st
    ]
    identity = new_execution_identity(
        camp,
        "analyze",
        set_number,
        len(attempts) + 1,
        point=args.point,
        lot=args.lot,
        slot=args.slot,
    )
    unit = {"kind": "analysis", "point": args.point, "lot": args.lot, "slot": args.slot}
    expect = {
        "campaign_id": camp.campaign_id,
        "campaign_declaration_sha256": camp.declaration_sha256,
        "set": set_number,
        "point": args.point,
        "lot": args.lot,
        "slot": args.slot,
        "eligibility": camp.eligibility,
    }
    existing = [c for c in order if (run_dir / "cases" / f"{c}.json").exists()]
    invalid = []
    for c in existing:
        try:
            rec = read_json(run_dir / "cases" / f"{c}.json")
        except ValueError:
            invalid.append(f"{c}: not valid JSON")
            continue
        invalid += validate_record(rec, by_id[c], expect)
    if existing:
        _, _, foreign = slot_records(
            run_dir, existing, by_id, expect, accepted_record_executions(camp)
        )
        invalid += [p for p in foreign if "not an execution of this unit" in p]
    if invalid:
        write_lock(camp, identity, unit, "invalid existing results", invalid[:200])
        return 2
    todo = [c for c in order if c not in existing]
    cache = inside_project(args.cache, "--cache")
    missing = [c for c in todo if not (cache / f"{c}.rpc").is_file()]
    if missing:
        refuse("inputs missing from the cache; no result written", missing)
    diverged = [
        f"{c}: input {file_sha256(cache / f'{c}.rpc')}, manifest {by_id[c]['sha256']}"
        for c in todo
        if file_sha256(cache / f"{c}.rpc") != by_id[c]["sha256"]
    ]
    if diverged:
        write_lock(camp, identity, unit, "input SHA-256 differs from the manifest", diverged)
        return 2
    if not todo:
        print(f"{args.point} lot {args.lot} slot {args.slot}: every result exists and is valid")
        return 0
    ex = Execution(
        camp,
        identity,
        {"cases": len(todo), "already_valid": len(existing), "run_dir": str(run_dir)},
        unit,
        lambda entries: analysis_unit_refusals(entries, unit_key, str(run_dir)),
    )
    events: list[dict] = []
    infra: list[dict] = []

    def on_result(i, r):
        if "integrity" in r:
            events.append(r)
            ex.lock("input SHA-256 differs from the manifest at read", [r])
            return "integrity"
        if "infrastructure" in r:
            infra.append(r)
            return "infrastructure"
        return None

    tasks = [(by_id[c], str(cache), str(run_dir), identity) for c in todo]
    workers = camp.declaration["analysis"]["workers"]
    try:
        outcome = run_pool(
            analyze_task, tasks, workers, declared, on_worker=ex.worker, on_result=on_result
        )
    except BaseException as exc:
        ex.interrupted("exception", {"exception": f"{type(exc).__name__}: {exc}"})
        ex.close({"result": "interrupted"})
        raise SystemExit(
            f"interrupted: {exc}; resume only this slot's cases without a result"
        ) from None
    if ex.lock_sha256 is not None:
        ex.close({"result": "divergence", "events": events})
        return 2
    if infra or outcome.error or len(outcome.results) != len(tasks):
        ex.interrupted("infrastructure", {"failures": infra, "error": outcome.error})
        ex.close({"result": "interrupted"})
        print(f"interrupted by infrastructure: {infra[:3]} {outcome.error}; resume this slot only")
        return 3
    statuses = [r["status"] for r in outcome.results.values()]
    counts = {s: statuses.count(s) for s in sorted(set(statuses))}
    sequence = sorted(
        [r["pid"], r["sequence_position"], r["case"]] for r in outcome.results.values()
    )
    if not ex.close({"result": "analyzed", "counts": counts, "sequence": sequence}):
        return 2
    print(f"{args.point} lot {args.lot} slot {args.slot}: {counts}", flush=True)
    return 0


def slot_records(
    run_dir: Path, lot: list[str], by_id: dict, expect: dict, allowed: dict | None = None
) -> tuple[dict, dict, list[str]]:
    """The records of a lot in one slot's run directory: case -> record, case -> SHA-256 of
    the file, and the problems (missing or invalid, or written by an execution that is not
    in ``allowed`` for this unit and this directory: ``accepted_record_executions``)."""
    recs, hashes, problems = {}, {}, []
    here = str(Path(run_dir).resolve())
    for c in lot:
        f = Path(run_dir) / "cases" / f"{c}.json"
        if not f.is_file():
            problems.append(f"{c}: missing")
            continue
        data = f.read_bytes()
        try:
            rec = json.loads(data)
        except ValueError:
            problems.append(f"{c}: not valid JSON")
            continue
        problems += validate_record(rec, by_id[c], expect)
        ex = (rec.get("identity") or {}).get("execution_id") if isinstance(rec, dict) else None
        want = (expect.get("point"), expect.get("lot"), expect.get("slot"), here)
        if allowed is not None and allowed.get(ex) != want:
            problems.append(
                f"{c}: written by execution {ex!r}, which is not an execution of this unit "
                "and this run directory, started and closed in the journal"
            )
        recs[c] = rec
        hashes[c] = hashlib.sha256(data).hexdigest()
    return recs, hashes, problems


def compare_lot_slots(
    camp: Campaign,
    manifest: dict,
    set_number: int,
    point: str,
    lot_n: int,
    runs: list[str],
    records: Path,
) -> tuple[int, str | None]:
    """Record 3c: the two slots of a lot at a point compared with the profile ``slots``.
    A difference (or a missing or invalid record) writes a lock. One comparison per lot and
    point, whatever the records folder: an already registered comparison refuses a new one,
    and a registered comparison that is missing, altered or repeated writes a lock."""
    lot = lots_of(manifest, camp.declaration["analysis"]["lot_size"])[lot_n]
    by_id = {e["id"]: e for e in manifest["cases"]}
    identity = new_execution_identity(camp, "compare-slots", set_number, 1, point=point, lot=lot_n)
    unit = {"kind": "slots", "point": point, "lot": lot_n}
    registered, why, damaged = registered_comparison(camp, point, lot_n)
    if damaged:
        write_lock(camp, identity, unit, why, [why])
        return 2, None
    if registered is not None:
        refuse(
            f"{point} lot {lot_n} is already compared (one comparison per lot and point)",
            [f"registered report: {journal_comparisons(camp)[(point, lot_n)][0]['report']}"],
        )
    base = {
        "campaign_id": camp.campaign_id,
        "campaign_declaration_sha256": camp.declaration_sha256,
        "set": set_number,
        "point": point,
        "lot": lot_n,
        "eligibility": camp.eligibility,
    }
    bound = [bound_run_dir(camp, point, lot_n, s) for s in (1, 2)]
    given = [str(inside_project(r, "--runs")) for r in runs]
    if bound != given:
        refuse(
            "the runs given are not the run directories bound to this lot",
            [
                f"slot {s}: given {g}, bound {b}"
                for s, (g, b) in enumerate(zip(given, bound, strict=True), 1)
            ],
        )
    allowed = accepted_record_executions(camp)
    r1, h1, p1 = slot_records(Path(runs[0]), lot, by_id, {**base, "slot": 1}, allowed)
    r2, h2, p2 = slot_records(Path(runs[1]), lot, by_id, {**base, "slot": 2}, allowed)
    if p1 or p2:
        write_lock(
            camp, identity, unit, "records missing or invalid at the comparison", [*p1, *p2][:200]
        )
        return 2, None
    cases, divergent = {}, []
    records.mkdir(parents=True, exist_ok=True)
    for c in lot:
        rep = CMP.compare_records(r1[c], r2[c], "slots", labels=("slot1", "slot2"))
        cases[c] = {
            "status": rep["status"],
            "slot1_sha256": h1[c],
            "slot2_sha256": h2[c],
            "report_sha256": hashlib.sha256(canonical_json(rep)).hexdigest(),
        }
        if rep["status"] != "identical":
            path = records / f"slots-{point}-lot{lot_n:04d}-{c}-{identity['execution_id']}.json"
            write_json(path, rep)
            divergent.append(
                {
                    "case": c,
                    "report": str(path),
                    "status": rep["status"],
                    "slot1": str(Path(runs[0]) / "cases" / f"{c}.json"),
                    "slot1_sha256": h1[c],
                    "slot2": str(Path(runs[1]) / "cases" / f"{c}.json"),
                    "slot2_sha256": h2[c],
                }
            )
    report = {
        "format": SLOTS_REPORT_FORMAT,
        "identity": identity,
        "point": point,
        "lot": lot_n,
        "profile": "slots",
        "profile_sha256": CMP.profile_sha256("slots"),
        "comparator_sha256": CMP.COMPARATOR_SHA256,
        "runs": runs,
        "cases": cases,
        "all_identical": not divergent,
    }
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    rfile = records / f"lot-{lot_n:04d}-{stamp}-3c-{point}-comparison.json"
    rsha = write_json(rfile, report)
    if divergent:
        write_lock(
            camp,
            identity,
            unit,
            "the two slots differ",
            [{"report": str(rfile), "sha256": rsha}, *divergent],
        )
        return 2, str(rfile)

    def no_comparison_yet(entries):
        same = [
            e
            for e in entries
            if e["kind"] == "compared"
            and (e["payload"].get("point"), e["payload"].get("lot")) == (point, lot_n)
        ]
        if same:
            return [f"{point} lot {lot_n} was compared meanwhile ({same[0]['payload']['report']})"]
        return []

    append_journal(
        camp,
        "compared",
        identity,
        {**unit, "report": str(rfile), "report_sha256": rsha},
        check=no_comparison_yet,
    )
    return 0, str(rfile)


def journal_comparisons(camp: Campaign) -> dict[tuple, list[dict]]:
    """(point, lot) -> the comparisons 3c registered in the journal (report path and SHA-256),
    in journal order. A comparison report counts only if the journal names it; more than one
    for a lot and point is a divergence."""
    entries, _ = read_journal(camp)
    out: dict[tuple, list[dict]] = {}
    for e in entries:
        if e["kind"] == "compared":
            out.setdefault((e["payload"]["point"], e["payload"]["lot"]), []).append(e["payload"])
    return out


def registered_comparison(camp: Campaign, point: str, lot: int) -> tuple[dict | None, str, bool]:
    """The comparison report of a lot at a point, re-read and checked against the journal:
    (the report, "", False); (None, why not, False) when no comparison is registered yet (the
    lot is not finished); (None, why, True) when two comparisons are registered for the lot
    and point, or the registered report is missing, altered or not an identical comparison of
    this lot: damaged evidence, a divergence (lock)."""
    regs = journal_comparisons(camp).get((point, lot), [])
    if not regs:
        return None, "no comparison registered in the journal", False
    if len(regs) > 1:
        return (
            None,
            f"{len(regs)} comparisons are registered for {point} lot {lot} (one is allowed): "
            + ", ".join(r["report"] for r in regs),
            True,
        )
    pay = regs[0]
    path = Path(pay["report"])
    if not path.is_file() or file_sha256(path) != pay["report_sha256"]:
        return None, f"the registered comparison report {path} is missing or altered", True
    report = read_json(path)
    if (
        report.get("format") != SLOTS_REPORT_FORMAT
        or report.get("point") != point
        or report.get("lot") != lot
        or not report.get("all_identical")
        or (report.get("identity") or {}).get("campaign_declaration_sha256")
        != camp.declaration_sha256
    ):
        return (
            None,
            f"the comparison report {path} is not an identical comparison of this lot",
            True,
        )
    return report, "", False


def mode_compare_slots(args) -> int:
    camp = open_campaign(args.root, args.campaign)
    problems = campaign_refusals(camp)
    if problems:
        refuse("slots not compared", problems)
    manifest, _, _, set_number = _accepted_inputs(camp, args.manifest)
    records = inside_project(args.records, "--records")
    code, rfile = compare_lot_slots(
        camp, manifest, set_number, args.point, args.lot, args.runs, records
    )
    print(
        f"{args.point} lot {args.lot}: comparison "
        f"{'identical' if code == 0 else 'DIVERGENT or invalid'} ({rfile})"
    )
    return code


# --- orchestration (R1 extended) --------------------------------------------------------


def _slot_dirs(prefix: str) -> list[str]:
    return [f"{prefix}-slot1", f"{prefix}-slot2"]


def _lot_kinds(records: Path, n: int) -> dict[str, list[Path]]:
    """Lot records by kind ("1", "2", "3", "3c", "4") for lot ``n``."""
    out: dict[str, list[Path]] = {}
    for f in sorted(records.glob(f"lot-{n:04d}-*.json")):
        parts = f.stem.split("-")  # lot, nnnn, stamp, kind, ...
        if len(parts) > 3:
            out.setdefault(parts[3], []).append(f)
    return out


def mode_orchestrate(args) -> int:
    """Lots: regenerate (checked against the accepted manifest and block index), analyze both
    slots at every point, re-read the results (record 3 per point and slot), compare the
    slots (record 3c per point), then delete the lot's inputs (record 4, only inside
    .cache/population/ of the harness's repository)."""
    camp = open_campaign(args.root, args.campaign)
    problems = campaign_refusals(camp) + affinity_problems(camp, args.cpus)
    if problems:
        refuse("orchestrate not started", problems)
    project = Path(args.project).resolve()
    top = Path(git(HARNESS_PATH.parent, "rev-parse", "--show-toplevel") or "/").resolve()
    if project != top:
        raise SystemExit(f"--project must be the top of the harness's repository ({top})")
    project_cache = (project / ".cache" / "population").resolve()
    cache = Path(args.cache).resolve()
    if project_cache not in (cache, *cache.parents):
        raise SystemExit(f"the cache must be inside {project_cache}")
    manifest, _, _, set_number = _accepted_inputs(camp, args.manifest)
    by_id = {e["id"]: e for e in manifest["cases"]}
    points = [p.split("=", 2) for p in args.point]  # name=python=run_dir_prefix
    for _, _, prefix in points:
        for run in _slot_dirs(prefix):
            inside_project(run, "a run directory")
    lots = lots_of(manifest, camp.declaration["analysis"]["lot_size"])
    records = inside_project(args.records, "--records")
    records.mkdir(parents=True, exist_ok=True)
    child_env = {**os.environ, "PYTHONUNBUFFERED": "1"}
    common = ["--root", str(camp.root), "--campaign", camp.campaign_id, "--cpus", args.cpus or ""]

    def record(name: str, payload: dict) -> str:
        return write_json(records / name, {"format": LOT_RECORD_FORMAT, **payload})

    def reread(n: int, lot: list[str]) -> tuple[bool, dict, list[str]]:
        complete, hashes, problems = True, {}, []
        allowed = accepted_record_executions(camp)
        for name, _, prefix in points:
            for s, run in enumerate(_slot_dirs(prefix), start=1):
                expect = {
                    "campaign_id": camp.campaign_id,
                    "set": set_number,
                    "point": name,
                    "lot": n,
                    "slot": s,
                }
                _, h, p = slot_records(Path(run), lot, by_id, expect, allowed)
                missing = [x for x in p if x.endswith(": missing")]
                complete = complete and not missing
                problems += [f"{name} slot {s}: {x}" for x in p if not x.endswith(": missing")]
                hashes[f"{name}/slot{s}"] = h
        return complete, hashes, problems

    def remove(f: Path) -> str | None:
        if f.is_symlink():
            return None
        f = f.resolve()
        if project_cache in f.parents and f.is_file():
            f.unlink()
            return f.name
        return None

    def finish(n: int, lot: list[str], prefix: str, extra: dict) -> None:
        deleted = [d for d in (remove(cache / f"{i}.rpc") for i in lot) if d]
        record(
            f"{prefix}-4-inputs-deleted.json",
            {"lot": n, "utc": utc_now(), "deleted": deleted, **extra},
        )

    for n, lot in enumerate(lots):
        complete, hashes, problems = reread(n, lot)
        if problems:
            ident = new_execution_identity(camp, "orchestrate", set_number, 1, lot=n)
            write_lock(camp, ident, {"kind": "lot", "lot": n}, "invalid results", problems[:200])
            return 2
        # The registered comparisons are checked first, whatever the records folder (B2): a
        # missing, altered or repeated one locks; one registered elsewhere refuses a new run.
        registered = {}
        for name, _, _ in points:
            report, why, damaged = registered_comparison(camp, name, n)
            if damaged:
                ident = new_execution_identity(camp, "orchestrate", set_number, 1, lot=n)
                write_lock(camp, ident, {"kind": "slots", "point": name, "lot": n}, why, [why])
                return 2
            if report is not None:
                registered[name] = journal_comparisons(camp)[(name, n)][0]["report"]
        kinds = _lot_kinds(records, n)
        if "3" not in kinds and registered:
            refuse(
                f"lot {n} is already compared; it is resumed only with the records folder of "
                "that comparison",
                [f"{k}: {v}" for k, v in registered.items()],
            )
        if "3" in kinds:
            recorded = {}
            for f in kinds["3"]:
                r = read_json(f)
                recorded[r["run"]] = r["results_sha256"]
            # A record 3 that exists must equal the results; a missing one (a stop while the
            # records 3 were written) is rebuilt from complete, valid results (N5).
            if not complete or any(hashes.get(k) != v for k, v in recorded.items()):
                ident = new_execution_identity(camp, "orchestrate", set_number, 1, lot=n)
                write_lock(
                    camp,
                    ident,
                    {"kind": "lot", "lot": n},
                    "records 3 and the results on disk diverge",
                    [str(f) for f in kinds["3"]],
                )
                return 2
            prefix = "-".join(kinds["3"][0].stem.split("-")[:3])
            for name, _, _ in points:
                for s in (1, 2):
                    key = f"{name}/slot{s}"
                    if key not in recorded:
                        record(
                            f"{prefix}-3-{name}-slot{s}-results-reread.json",
                            {
                                "lot": n,
                                "utc": utc_now(),
                                "point": name,
                                "slot": s,
                                "run": key,
                                "results_sha256": hashes[key],
                                "written_on_resume": True,
                            },
                        )
            for name, _, run_prefix in points:
                if name not in registered:
                    code, _ = compare_lot_slots(
                        camp, manifest, set_number, name, n, _slot_dirs(run_prefix), records
                    )
                    if code:
                        return code
            if "4" in kinds:
                print(
                    f"lot {n}: results valid and equal to records 3, comparisons and record 4 "
                    "present; skipped"
                )
                continue
            finish(n, lot, prefix, {"completed_on_resume": True})
            print(f"lot {n}: records checked, record 4 written")
            continue
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        prefix = f"lot-{n:04d}-{stamp}"
        if not complete:
            record(f"{prefix}-1-started.json", {"lot": n, "cases": lot, "utc": utc_now()})
            gen = subprocess.run(
                [
                    args.generator_python,
                    str(HARNESS_PATH),
                    "regenerate",
                    *common,
                    "--manifest",
                    args.manifest,
                    "--cache",
                    str(cache),
                    "--lot",
                    str(n),
                ],
                env=child_env,
            )
            record(
                f"{prefix}-2-regenerated.json",
                {"lot": n, "utc": utc_now(), "returncode": gen.returncode},
            )
            if gen.returncode != 0:
                raise SystemExit(
                    f"lot {n}: regeneration diverged or failed; stopped (nothing deleted)"
                )
            for name, python, run_prefix in points:
                for s, run in enumerate(_slot_dirs(run_prefix), start=1):
                    res = subprocess.run(
                        [
                            python,
                            str(HARNESS_PATH),
                            "analyze",
                            *common,
                            "--manifest",
                            args.manifest,
                            "--cache",
                            str(cache),
                            "--out",
                            run,
                            "--point",
                            name,
                            "--lot",
                            str(n),
                            "--slot",
                            str(s),
                        ],
                        env=child_env,
                    )
                    if res.returncode != 0:
                        raise SystemExit(
                            f"lot {n}: analyze stopped at {name} slot {s}; stopped "
                            "(nothing deleted)"
                        )
            complete, hashes, problems = reread(n, lot)
            if problems or not complete:
                raise SystemExit(f"lot {n}: results incomplete or invalid after analysis; stopped")
        for name, _, _ in points:
            for s in (1, 2):
                key = f"{name}/slot{s}"
                record(
                    f"{prefix}-3-{name}-slot{s}-results-reread.json",
                    {
                        "lot": n,
                        "utc": utc_now(),
                        "point": name,
                        "slot": s,
                        "run": key,
                        "results_sha256": hashes[key],
                    },
                )
        for name, _, run_prefix in points:
            code, _ = compare_lot_slots(
                camp, manifest, set_number, name, n, _slot_dirs(run_prefix), records
            )
            if code:
                return code
        finish(n, lot, prefix, {})
        print(f"lot {n}: done ({len(lot)} cases)", flush=True)
    return 0


# --- metrics (section 13) ---------------------------------------------------------------


def cp_upper(k: int, n: int) -> float:
    from scipy.stats import beta

    return 1.0 if k >= n else float(beta.ppf(0.95, k + 1, n - k))


def cp_lower(k: int, n: int) -> float:
    from scipy.stats import beta

    return 0.0 if k <= 0 else float(beta.ppf(0.05, k, n - k + 1))


def _decoded(value):
    """A typed value with its floats back as Python floats (for the criteria only)."""
    if CMP.is_typed_float(value):
        return struct.unpack(">d", bytes.fromhex(value["f64"]))[0]
    if isinstance(value, dict):
        return {k: _decoded(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_decoded(v) for v in value]
    return value


def condition_view(rec: dict | None, condition: str, effective: str) -> dict:
    """The fields the criteria read from one condition of a record, with the effective
    state of the record (``ok``, or why it counts as an integrity error in C6)."""
    if rec is None:
        return {"status": "missing"}
    if effective != "ok":
        return {"status": effective}
    if rec["status"] != "analyzed":
        return {"status": rec["status"]}
    c = rec["conditions"].get(condition)
    if c is None:
        return {"status": "missing"}
    sci, out = _decoded(c["scientific"]), _decoded(c["harness_outcomes"])
    if scientific_problems(sci):
        # An analysis without its complete scientific record (no valid verdict, no tests)
        # counts as an error in C6, never as a successful analysis.
        return {"status": "error"}
    return {
        "status": "analyzed",
        "verdict": sci.get("verdict"),
        "fatal": [
            t["name"]
            for t in sci.get("tests", [])
            if t.get("status") == "FAIL" and t.get("severity") == "fatal"
        ],
        "signal_verdict_without_eb_catalog": out.get("signal_verdict_without_eb_catalog"),
        "signal_identity": out.get("signal_identity"),
    }


def _outcomes(o: dict) -> dict:
    """Outcomes of one case and condition. An error, missing or blocked result is never a
    successful analysis: it stays in every denominator, counts as an error (C6) and as
    INCONCLUSIVE (C3), and never as refuted, flagged or a false alarm."""
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


def run_metrics(cases: list[dict], views: dict[tuple[str, str], dict]) -> dict:
    """Criteria C1 to C6 as in v1 (unchanged limits and bounds), from the condition views."""

    def out(c, cond):
        return _outcomes(views.get((c["id"], cond), {"status": "missing"}))

    def sel(**kw):
        return [c for c in cases if all(c[k] == v for k, v in kw.items())]

    def rate(group, key, cond="i", kind="upper"):
        n = len(group)
        k = sum(out(c, cond)[key] for c in group)
        r = {"k": k, "n": n, "rate": k / n if n else None}
        if n:
            r["bound"] = cp_upper(k, n) if kind == "upper" else cp_lower(k, n)
        return r

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
            s = out(c, cond)["status"]
            m["status_counts"][s] = m["status_counts"].get(s, 0) + 1
    for noise in ("white", "correlated"):
        for band in ("below", "near", "measurable"):
            r = rate(sel(**{"class": "planet", "band": band, "noise": noise}), "refuted")
            r["passes"] = r["n"] > 0 and r["bound"] <= 0.10
            m["criteria"][f"C1 refuted planets, {band}, {noise}"] = r
        r = rate(
            sel(**{"class": "false_positive", "band": "measurable", "noise": noise}),
            "flagged_identity",
            kind="lower",
        )
        r["passes"] = r["n"] > 0 and r["bound"] >= 0.60
        m["criteria"][f"C2 flagged false positives, measurable, {noise}"] = r
        for cls in ("planet", "false_positive"):
            r = rate(sel(**{"class": cls, "band": "measurable", "noise": noise}), "inconclusive")
            r["passes"] = r["n"] > 0 and r["bound"] <= 0.20
            m["criteria"][f"C3 INCONCLUSIVE, {cls}, measurable, {noise}"] = r
        r = rate(sel(**{"class": "no_transit", "noise": noise}), "false_alarm")
        r["passes"] = r["n"] > 0 and r["bound"] <= (0.01 if noise == "white" else 0.05)
        m["criteria"][f"C4 false alarm, {noise}"] = r
        own = [
            c for c in sel(**{"class": "planet", "noise": noise}) if c["catalog_variant"] == "own"
        ]
        k = sum(out(c, "ii")["refuted_only_by_eb_catalog"] for c in own)
        m["criteria"][f"C5 planets refuted only by own-TIC eb_catalog, {noise}"] = {
            "k": k,
            "n": len(own),
            "passes": k == 0,
        }
    errors = [c["id"] for c in cases if any(out(c, cond)["error"] for cond in _conditions(c))]
    m["criteria"]["C6 analysis errors, missing results and integrity errors"] = {
        "k": len(errors),
        "passes": not errors,
    }
    m["errors"] = errors
    failed = [name for name, r in m["criteria"].items() if not r["passes"]]
    m["approval"] = {
        "passes": not failed,
        "failed": failed,
        "rule": "The study is approved only if every criterion passes, C6 included. A rate "
        "can meet its limit while the study fails.",
    }
    for c in cases:
        for cond in _conditions(c):
            key = f"{c['class']}|{c['band']}|{c['noise']}|{c['mechanism']}"
            if cond == "ii":
                key += f"|{c['catalog_variant']}"
            o = out(c, cond)
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


def _gather_point(
    camp, manifest, set_number, point, prefix, records, lot_size
) -> tuple[dict, list[str]]:
    """Reconciliation of one point (R1 extended): for every lot, both slots' records in the
    run directories bound to the lot, written by executions of the unit closed in the
    journal; the records 3 of both slots equal to the files; the comparison 3c registered in
    the journal, identical, naming the same files; and record 4. Returns the effective
    views, the problems of content (a divergence) and the lots not finished."""
    by_id = {e["id"]: e for e in manifest["cases"]}
    problems: list[str] = []
    unfinished: list[str] = []
    recs: dict[int, dict] = {1: {}, 2: {}}
    hashes: dict[int, dict] = {1: {}, 2: {}}
    compared: set[str] = set()
    entries, _ = read_journal(camp)
    units = analysis_units(entries)
    allowed = accepted_record_executions(camp)
    given = [str(Path(r).resolve()) for r in _slot_dirs(prefix)]
    problems += run_provenance_problems(camp, point, _slot_dirs(prefix))
    for s, run in enumerate(given, start=1):
        found = {f.stem for f in (Path(run) / "cases").glob("*.json")}
        problems += [
            f"{point} slot {s}: {x} is not in the manifest" for x in sorted(found - set(by_id))
        ]
    for n, lot in enumerate(lots_of(manifest, lot_size)):
        kinds = _lot_kinds(Path(records), n)
        reread = {}
        for f in kinds.get("3", []):
            r = read_json(f)
            if r.get("point") == point:
                reread[r.get("slot")] = r.get("results_sha256")
        for s in (1, 2):
            unit = units.get((point, n, s))
            if unit is None or unit["run_dir"] != given[s - 1]:
                unfinished.append(f"{point} lot {n} slot {s}: not analyzed in the run given")
                continue
            expect = {
                "campaign_id": camp.campaign_id,
                "campaign_declaration_sha256": camp.declaration_sha256,
                "set": set_number,
                "point": point,
                "lot": n,
                "slot": s,
                "eligibility": camp.eligibility,
            }
            r, h, p = slot_records(Path(given[s - 1]), lot, by_id, expect, allowed)
            recs[s].update(r)
            hashes[s].update(h)
            unfinished += [f"{point} slot {s} lot {n}: {x}" for x in p if x.endswith(": missing")]
            problems += [f"{point} slot {s} lot {n}: {x}" for x in p if not x.endswith(": missing")]
            if s not in reread:
                unfinished.append(f"{point} lot {n} slot {s}: no record 3")
            elif reread[s] != h:
                problems.append(f"{point} lot {n} slot {s}: the files differ from record 3")
        report, why, damaged = registered_comparison(camp, point, n)
        if damaged:
            problems.append(f"{point} lot {n}: {why}")
        elif report is None:
            unfinished.append(f"{point} lot {n}: {why}")
        else:
            for c in lot:
                v = report["cases"].get(c) or {}
                if v.get("status") != "identical" or (
                    v.get("slot1_sha256"),
                    v.get("slot2_sha256"),
                ) != (
                    hashes[1].get(c),
                    hashes[2].get(c),
                ):
                    problems.append(f"{point} {c}: the registered comparison names other files")
                else:
                    compared.add(c)
        if "4" not in kinds:
            unfinished.append(f"lot {n}: no record 4")
    views = {}
    for c, e in by_id.items():
        if c not in recs[1] or c not in recs[2]:
            effective = "missing"
        elif c not in compared:
            effective = "blocked"
        else:
            effective = "ok"
        for cond in _conditions(e):
            views[(c, cond)] = condition_view(recs[1].get(c), cond, effective)
    return views, problems, unfinished


def mode_metrics(args) -> int:
    camp = open_campaign(args.root, args.campaign)
    if args.integrity_report:
        return integrity_report(camp, args)
    problems = campaign_refusals(camp)
    if problems:
        refuse("metrics not computed (use --integrity-report for a locked campaign)", problems)
    if not args.manifest or not args.records or not args.point:
        raise SystemExit("metrics needs --manifest, --records and at least one --point")
    target = inside_project(args.out, "--out")
    records = inside_project(args.records, "--records")
    if target.exists() or target.with_suffix(".md").exists():
        raise SystemExit(f"{target} (or its .md) exists; nothing computed")
    manifest, _, _, set_number = _accepted_inputs(camp, args.manifest)
    lot_size = camp.declaration["analysis"]["lot_size"]
    points = [p.split("=", 1) for p in args.point]  # name=run_dir_prefix
    for _, prefix in points:
        for run in _slot_dirs(prefix):
            inside_project(run, "a run directory")
    identity = new_execution_identity(camp, "metrics", set_number, 1)
    out = {
        "format": METRICS_FORMAT,
        "identity": identity,
        "eligibility": camp.eligibility,
        "approval_status": (
            "computed from eligible campaign evidence"
            if camp.strict
            else "DIAGNOSTIC: not an approval"
        ),
        "campaign_id": camp.campaign_id,
        "campaign_declaration_sha256": camp.declaration_sha256,
        "manifest_sha256": file_sha256(Path(args.manifest)),
        "harness_sha256": HARNESS_SHA256,
        "comparator_sha256": CMP.COMPARATOR_SHA256,
        "accepted_risk": (
            "Between a detection and the manual commit, the lock marker and the journal exist "
            "only on disk and could be deleted or altered by hand; only the commit makes such "
            "an action visible."
        ),
        "points": [],
    }
    all_problems = []
    counts = {}
    for c in manifest["cases"]:
        key = f"{c['class']}|{c['band']}|{c['noise']}"
        counts[key] = counts.get(key, 0) + 1
    expected_counts = {}
    for c in camp.cases():
        key = f"{c['class']}|{c['band']}|{c['noise']}"
        expected_counts[key] = expected_counts.get(key, 0) + 1
    if counts != expected_counts:
        all_problems.append("the manifest's denominators per stratum differ from the population")
    out["redraws"] = redraw_summary(manifest)
    by_point: dict[str, dict] = {}
    unfinished: list[str] = []
    for name, prefix in points:
        views, p, u = _gather_point(camp, manifest, set_number, name, prefix, records, lot_size)
        all_problems += p
        unfinished += u
        by_point[name] = views
        out["points"].append({"point": name, "metrics": run_metrics(manifest["cases"], views)})
    names = [name for name, _ in points]
    out["paired"] = [
        {"from": a, "to": b, "comparisons": paired(manifest, by_point[a], by_point[b])}
        for a, b in zip(names, names[1:], strict=False)
    ]
    if args.check_against:
        previous = read_json(Path(args.check_against))
        if canonical_json(previous.get("points")) != canonical_json(
            json.loads(canonical_json(out["points"]))
        ):
            all_problems.append(f"the recomputed metrics differ from {args.check_against}")
    if all_problems:
        write_lock(camp, identity, {"kind": "metrics"}, "reconciliation failed", all_problems[:300])
        return 2
    if unfinished:
        refuse("metrics not computed: lots are not finished (R1)", unfinished[:60])
    target.parent.mkdir(parents=True, exist_ok=True)
    write_json(target, out)
    write_atomic(target.with_suffix(".md"), metrics_markdown(out).encode("utf-8"))
    print(f"metrics written to {target}")
    return 0


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


def _paired_group(cases, a: dict, b: dict, key: str, cond: str) -> dict:
    """McNemar comparison of one outcome between two points (as v1, on the views)."""
    from scipy.stats import binomtest

    def out(views, c):
        return _outcomes(views.get((c["id"], cond), {"status": "missing"}))[key]

    up = [c["id"] for c in cases if out(b, c) and not out(a, c)]
    down = [c["id"] for c in cases if out(a, c) and not out(b, c)]
    n = len(cases)
    ka = sum(out(a, c) for c in cases)
    kb = sum(out(b, c) for c in cases)
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


def paired(manifest: dict, a: dict, b: dict) -> dict:
    """McNemar comparisons by band and noise model in conditions (i) and (ii), and in (ii)
    also by catalog variant; the aggregates are additional information only (as v1)."""
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


def _fmt(x) -> str:
    return "-" if x is None else f"{x:.4f}"


def metrics_markdown(out: dict) -> str:
    diagnostic = out.get("eligibility") != "campaign"
    lines = [
        (
            f"# DIAGNOSTIC: not an approval. Population metrics of the diagnostic "
            f"{out['campaign_id']}"
            if diagnostic
            else f"# Population metrics, campaign {out['campaign_id']}"
        ),
        "",
        f"Eligibility: {out.get('eligibility')}. {out.get('approval_status')}.",
        "",
        f"Accepted risk: {out.get('accepted_risk')}",
        "",
        "Every point uses the fast plan of the test suite (section 7); false-alarm rates under "
        "the calibration plan could be higher. The SNR bands of blends use the expected SNR "
        "without the noise of the pixel data (Amendment 2, N2). Every case was analyzed in two "
        "slots whose records are identical (Amendment 4); the values are those of slot 1.",
        "",
    ]
    for point in out["points"]:
        m = point["metrics"]
        a = m["approval"]
        lines += [
            f"## {point['point']}",
            "",
            (
                "**DIAGNOSTIC: not an approval.** Criteria computed on diagnostic evidence "
                f"(they would {'pass' if a['passes'] else 'fail'}). {a['rule']}"
                if diagnostic
                else f"**Overall approval: {'PASSES' if a['passes'] else 'FAILS'}.** {a['rule']}"
            )
            + (f" Failed: {', '.join(a['failed'])}." if a["failed"] else ""),
            "",
            f"Statuses (per condition): {m['status_counts']}",
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
        lines.append("")
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


def integrity_report(camp: Campaign, args) -> int:
    """The integrity-failure report: reads every lock, divergence, resolution and execution
    (eligible and diagnostic, each labelled), never lifts or requires lifting a lock, never
    computes an approval."""
    target = Path(args.out)
    if target.exists():
        raise SystemExit(f"{target} exists; nothing written")
    entries, journal_problems = read_journal(camp)
    named, res_problems = resolutions(camp)
    locks = []
    if camp.locks.is_dir():
        for f in sorted(camp.locks.glob("lock-*.json")):
            sha = file_sha256(f)
            locks.append(
                {"file": f.name, "sha256": sha, "resolved": sha in named, "marker": read_json(f)}
            )
    report = {
        "format": INTEGRITY_REPORT_FORMAT,
        "campaign_id": camp.campaign_id,
        "campaign_declaration_sha256": camp.declaration_sha256,
        "approval": "BLOCKED: integrity failure",
        "eligibility_of_this_campaign": camp.eligibility,
        "journal_problems": journal_problems,
        "blocking": blocking_problems(camp),
        "locks": locks,
        "divergences": [
            {k: e[k] for k in ("seq", "utc", "identity", "payload")}
            for e in entries
            if e["kind"] == "divergence"
        ],
        "resolutions": {"named_locks": sorted(named), "problems": res_problems},
        "executions": {
            ex: {"identity": st["identity"], "kinds": sorted(k for k in st if k != "identity")}
            for ex, st in executions(entries).items()
        },
        "budget": budget_state(camp, entries),
        "accepted_risk": "Between the detection and the manual commit, the local marker and "
        "the journal exist only on disk and could be deleted or altered by hand; only the "
        "commit makes such an action visible.",
    }
    write_json(target, report)
    print(
        f"integrity report written to {target}: BLOCKED: integrity failure ({len(locks)} lock(s))"
    )
    return 0


# --- maintainer and helper modes --------------------------------------------------------


def mode_reconcile(args) -> int:
    camp = open_campaign(args.root, args.campaign)
    if camp.problems:
        refuse("no reconciliation", camp.problems)
    if camp.strict and harness_problems()[1]:
        refuse("no reconciliation (R2)", harness_problems()[1])
    entries, problems = read_journal(camp)
    if problems:
        refuse("journal integrity", problems)
    st = executions(entries).get(args.execution_id)
    if st is None or "started" not in st:
        refuse(f"execution {args.execution_id} did not start")
    if "closed" in st or "reconciled" in st:
        refuse(f"execution {args.execution_id} is already closed or reconciled")
    pids = [st["started"][0]["payload"].get("main_pid")] + [
        e["payload"]["pid"] for e in st.get("process", [])
    ]
    alive = [p for p in pids if p and pid_running(p)]
    if alive and not args.processes_checked_by_hand:
        refuse(f"recorded processes {alive} are still running")
    append_journal(
        camp,
        "reconciled",
        st["identity"],
        {
            "classified_as": "interrupted",
            "reason": args.reason,
            "pids": pids,
            "pids_running": alive,
            "by": "maintainer",
        },
    )
    print(f"execution {args.execution_id} reconciled as interrupted (its set, if any, is consumed)")
    return 0


def mode_status(args) -> int:
    camp = open_campaign(args.root, args.campaign)
    entries, problems = read_journal(camp)
    acc = accepted_set(entries)
    print(
        json.dumps(
            {
                "campaign_id": camp.campaign_id,
                "eligibility": camp.eligibility,
                "declaration_sha256": camp.declaration_sha256,
                "declaration_problems": camp.problems,
                "journal_entries": len(entries),
                "journal_problems": problems,
                "blocking": blocking_problems(camp),
                "budget": budget_state(camp, entries),
                "accepted_set": acc["payload"] if acc else None,
            },
            indent=1,
        )
    )
    return 0


def mode_dispatch_table(args) -> int:
    table = dispatch_table()
    doc = {
        "environment": {DISPATCH_VARIABLE: os.environ.get(DISPATCH_VARIABLE)},
        "table": table,
        "sha256": hashlib.sha256(canonical_json(table)).hexdigest(),
    }
    text = json.dumps(doc, indent=1, sort_keys=True)
    if args.out:
        write_atomic(Path(args.out), text.encode("utf-8") + b"\n")
    print(text if not args.out else f"written to {args.out} (SHA-256 of the table {doc['sha256']})")
    return 0


def mode_compare(args) -> int:
    a, b = Path(args.left).read_bytes(), Path(args.right).read_bytes()
    if args.kind == "blob":
        rep = CMP.compare_blobs(a, b)
    elif args.kind == "record":
        rep = CMP.compare_records(json.loads(a), json.loads(b), args.profile)
    else:
        rep = CMP.compare_manifests(
            json.loads(a),
            json.loads(b),
            read_json(Path(args.left_blocks)),
            read_json(Path(args.right_blocks)),
        )
    text = json.dumps(rep, indent=1, sort_keys=True)
    if args.out:
        write_atomic(Path(args.out), text.encode("utf-8") + b"\n")
    print(text[:20000])
    return 0


def main(argv: list[str] | None = None) -> int:
    sys.stdout.reconfigure(line_buffering=True)
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="mode", required=True)

    def campaign(p):
        p.add_argument("--root", help="campaigns root (default: campaigns/ next to this file)")
        p.add_argument("--campaign", required=True)
        return p

    g = campaign(sub.add_parser("generate"))
    g.add_argument("--set", type=int, required=True)
    g.add_argument("--generation", type=int, required=True)
    g.add_argument("--out", required=True)
    g.add_argument("--cache", help="store the cases (default: hash only)")
    cs = campaign(sub.add_parser("check-set"))
    cs.add_argument("--set", type=int, required=True)
    rg = campaign(sub.add_parser("regenerate"))
    rg.add_argument("--manifest", required=True)
    rg.add_argument("--cache", required=True)
    rg.add_argument("--lot", type=int, required=True)
    a = campaign(sub.add_parser("analyze"))
    a.add_argument("--manifest", required=True)
    a.add_argument("--cache", required=True)
    a.add_argument("--out", required=True)
    a.add_argument("--point", required=True)
    a.add_argument("--lot", type=int, required=True)
    a.add_argument("--slot", type=int, required=True)
    c = campaign(sub.add_parser("compare-slots"))
    c.add_argument("--manifest", required=True)
    c.add_argument("--point", required=True)
    c.add_argument("--lot", type=int, required=True)
    c.add_argument("--runs", nargs=2, required=True)
    c.add_argument("--records", required=True)
    o = campaign(sub.add_parser("orchestrate"))
    o.add_argument("--manifest", required=True)
    o.add_argument("--project", required=True)
    o.add_argument("--cache", required=True)
    o.add_argument("--generator-python", required=True)
    o.add_argument("--point", action="append", required=True, help="name=python=run_dir_prefix")
    o.add_argument("--records", required=True)
    m = campaign(sub.add_parser("metrics"))
    m.add_argument("--manifest")
    m.add_argument("--point", action="append", default=[], help="name=run_dir_prefix")
    m.add_argument("--records")
    m.add_argument("--out", required=True)
    m.add_argument("--check-against")
    m.add_argument("--integrity-report", action="store_true")
    r = campaign(sub.add_parser("reconcile"))
    r.add_argument("--execution-id", required=True)
    r.add_argument("--reason", required=True)
    r.add_argument("--processes-checked-by-hand", action="store_true")
    campaign(sub.add_parser("status"))
    d = sub.add_parser("dispatch-table")
    d.add_argument("--out")
    cp = sub.add_parser("compare")
    cp.add_argument("--kind", choices=("blob", "record", "manifest"), required=True)
    cp.add_argument("--profile")
    cp.add_argument("--left", required=True)
    cp.add_argument("--right", required=True)
    cp.add_argument("--left-blocks")
    cp.add_argument("--right-blocks")
    cp.add_argument("--out")
    for p in sub.choices.values():
        p.add_argument("--cpus", default="8-31")
    args = parser.parse_args(argv)
    print(f"affinity: {set_affinity(args.cpus)}", flush=True)
    if home_problems():
        refuse("the harness does not run here", home_problems())
    return {
        "generate": mode_generate,
        "check-set": mode_check_set,
        "regenerate": mode_regenerate,
        "analyze": mode_analyze,
        "compare-slots": mode_compare_slots,
        "orchestrate": mode_orchestrate,
        "metrics": mode_metrics,
        "reconcile": mode_reconcile,
        "status": mode_status,
        "dispatch-table": mode_dispatch_table,
        "compare": mode_compare,
    }[args.mode](args)


if __name__ == "__main__":
    sys.exit(main())
