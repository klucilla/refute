"""The comparative viability package C/D (docs/validation/v0.2.1/reopen/stage-1/viability-cd/
README.md; its acceptance record ``viability-cd-acceptance.md`` next to this file, committed before
its tests, which were committed before this code): the geometries derived from gate 3b's saved
metadata, the cases and their seeds, their layouts on the real sector dates, their generation,
their records and the resumable runner of the two sub-lots. Nothing here runs a lot by itself; the
lot runs only with the maintainer's authorization 2.

- ``geometry_list``: the eligible geometries of C (exactly three observing years) and D (four or
  more), every sector with its target pixel file and a span of 25.5 to 30.0 d, unique by their
  sector numbers (the lowest eligible TIC supplies the dates), shuffled by a fixed seed, the first
  24 and 12 (G1 to G8);
- ``lot_cases``: the planets of the measurable band, their seeds and geometries, in the interleaved
  task order (K1 to K6);
- ``draw_layout`` and ``build_curve``: the cadences of each real sector (``population_v4._sector``
  on the drawn orbits), checked by the domain function, then ``population_v2``'s parameters, band
  placement, model and noise (L1 to L4, P1 to P5);
- ``record_target``: every round by ``calibration_measurement`` with the noiseless twin; the
  identity flag and the evaluator's oracle computed after the engine calls (R1 to R6);
- ``run_lot``: ``x2_study``'s runner pattern with the sub-lot's ceiling and its 10% cost check
  (X1 to X8).

``population_v2.py`` (frozen), ``population_v3.py``, ``population_v4.py``, ``rmin_study.py`` and
``x2_study.py`` are reused, never edited; the engine is never edited.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import population_v4 as v4  # noqa: E402
import x2_study as x2  # noqa: E402

rs, v3, pv2 = x2.rs, x2.v3, x2.pv2
domain = v4.domain

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
MAST_ROWS = REPO / ".cache" / "real-controls" / "mast-rows.json"
MAST_ROWS_SHA256 = "57fb8a014e8aacc5c0de5fc30dcbf46f6bd8315b30c5642281381fdfd46567c2"
GEOMETRY_LIST = REPO / "docs/validation/v0.2.1/reopen/stage-1/viability-cd/geometry-list.json"
GEOMETRY_FORMAT = "refute-v0.2.1-viability-cd-geometries/1"
MJD0 = datetime(1858, 11, 17, tzinfo=UTC)
MJD_BTJD_OFFSET = 56999.5
SPAN_DAYS = (25.5, 30.0)
N_SELECTED = {"C": 24, "D": 12}
GEOMETRY_SEED_ROOT = "refute/v0.2.1/viability-cd/geometries"

PREFIX = "refute-v0.2.1-viability-cd-1"
SEED_ROOT = "refute/v0.2.1/viability-cd"
TEST_PREFIX = "refute-v0.2.1-viability-cd-test"
TEST_SEED_ROOT = "refute/v0.2.1/viability-cd-test"
NOISES = ("white", "correlated")
NOISE_TAGS = {"white": "white", "correlated": "AR(1)"}
REGIMES = {
    "C": (("three_years", 180), ("variability_some_years", 180)),
    "D": (("three_years", 120),),
}
ABSENT_YEARS = v4.ABSENT_YEARS
MAX_ATTEMPTS = v4.MAX_ATTEMPTS
ORBIT_GAP_DAYS = v4.ORBIT_GAP_DAYS
ORBIT_DAYS = v4.ORBIT_DAYS
DELTA_DAYS = (-0.5, 0.5)
IDENTITY_TOLERANCE = 0.01
ORACLE_MIN_IN, ORACLE_MIN_SIDE = 5, 10
LOT_AFFINITY = x2.LOT_AFFINITY
WORKERS = 22
RECORD_FORMAT = "refute-v0.2.1-viability-cd-record/1"
LOT_FORMAT = "refute-v0.2.1-viability-cd-lot/1"
COST_CHECK_FRACTION = 0.1


@dataclass(frozen=True)
class SubLot:
    """A sub-lot: its name, alternative, submission ceiling (hours), LP-h ceiling, prefix and seed
    root (the tests use their own)."""

    name: str
    alternative: str
    deadline_hours: float
    lp_hours: float
    prefix: str = PREFIX
    seed_root: str = SEED_ROOT


SUBLOTS = {
    "viability-c": SubLot("viability-c", "C", 1.70, 37.0),
    "viability-d": SubLot("viability-d", "D", 1.40, 30.8),
}
SUBLOT_ORDER = ("viability-c", "viability-d")


# --- the geometries (G1 to G8) ------------------------------------------------------------------


def load_mast_rows(path: Path = MAST_ROWS) -> tuple[dict, str]:
    """Gate 3b's saved MAST rows, read once, and their SHA-256 (refused if not the recorded one)."""
    data = Path(path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != MAST_ROWS_SHA256:
        raise SystemExit(f"mast-rows.json: SHA-256 {digest} is not gate 3b's {MAST_ROWS_SHA256}")
    return json.loads(data.decode("utf-8")), digest


def utc_year(mjd: float) -> int:
    return (MJD0 + timedelta(days=float(mjd))).year


def consolidate(found: dict) -> tuple[dict[int, float], dict[int, float], set[int]]:
    """Per sector, the earliest ``t_min`` and the latest ``t_max`` of its light-curve rows (MJD),
    and the sectors of the target pixel files (viability-3b's ``sectors_of``)."""
    starts: dict[int, float] = {}
    ends: dict[int, float] = {}
    for row in found["light_curves"]:
        s, t0 = int(row["sequence_number"]), float(row["t_min"])
        t1 = float(row["t_max"]) if row.get("t_max") is not None else t0
        if not (math.isfinite(t0) and math.isfinite(t1)) or t1 < t0:
            raise ValueError(f"invalid t_min/t_max {row.get('t_min')!r}/{row.get('t_max')!r}")
        starts[s] = min(t0, starts.get(s, t0))
        ends[s] = max(t1, ends.get(s, t1))
    tpfs = {int(row["sequence_number"]) for row in found.get("pixel_files", [])}
    return starts, ends, tpfs


def tic_geometry(tic: int, found: dict) -> dict:
    """One TIC's geometry and its eligibility (``alternative`` C, D or None, with every reason)."""
    starts, ends, tpfs = consolidate(found)
    order = sorted(starts)
    years = sorted({utc_year(starts[s]) for s in order})
    sectors = [
        {
            "sector": s,
            "t_min_mjd": starts[s],
            "t_max_mjd": ends[s],
            "span_days": ends[s] - starts[s],
            "year": utc_year(starts[s]),
        }
        for s in order
    ]
    reasons = []
    if len(years) < 3:
        reasons.append(f"years: {len(years)}")
    missing = [s for s in order if s not in tpfs]
    if missing:
        reasons.append(f"no target pixel file: {missing}")
    for x in sectors:
        if not (SPAN_DAYS[0] <= x["span_days"] <= SPAN_DAYS[1]):
            reasons.append(f"span outside 25.5 to 30.0 d: {x['sector']} {x['span_days']:.4f}")
    alternative = None
    if not reasons:
        alternative = "C" if len(years) == 3 else "D"
    return {
        "tic": int(tic),
        "alternative": alternative,
        "reasons": reasons,
        "years": years,
        "sectors": sectors,
    }


def geometry_seed(alternative: str) -> int:
    text = f"{GEOMETRY_SEED_ROOT}/{alternative}"
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


def orbit_acceptance(span: float, steps: int = 20001) -> float:
    """The probability that one draw of ``g`` U(0.5, 2) and ``delta`` U(-0.5, 0.5) gives two orbits
    in [12.5, 14] for a sector of real span ``span`` (the trapezoid rule over ``g``)."""
    g = np.linspace(ORBIT_GAP_DAYS[0], ORBIT_GAP_DAYS[1], steps)
    half = (span - g) / 2.0
    room = np.minimum(half - ORBIT_DAYS[0], ORBIT_DAYS[1] - half)
    width = np.clip(2.0 * room, 0.0, DELTA_DAYS[1] - DELTA_DAYS[0])
    p = np.trapezoid(width, g) / (ORBIT_GAP_DAYS[1] - ORBIT_GAP_DAYS[0])
    return float(p / (DELTA_DAYS[1] - DELTA_DAYS[0]))


def _btjd_sectors(geometry: dict) -> list[dict]:
    return [
        {
            "sector": int(x["sector"]),
            "year": int(x["year"]),
            "t_min_btjd": float(x["t_min_mjd"]) - MJD_BTJD_OFFSET,
            "t_max_btjd": float(x["t_max_mjd"]) - MJD_BTJD_OFFSET,
            "span_days": float(x["span_days"]),
        }
        for x in geometry["sectors"]
    ]


def geometry_list(rows: dict, digest: str | None = None) -> dict:
    """The eligible geometries, their unique keys and the selections (the declaration's
    section 1)."""
    tics = [tic_geometry(int(t), rows[t]) for t in sorted(rows, key=int)]
    retrieved = sorted({str(v["retrieved_utc"]) for v in rows.values() if v.get("retrieved_utc")})
    out: dict = {
        "format": GEOMETRY_FORMAT,
        "source": {
            "file": ".cache/real-controls/mast-rows.json",
            "sha256": digest,
            "origin": "MAST (SPOC 120-s light curves and target pixel files), saved by gate 3b",
            "retrieved_utc_first_last": [retrieved[0], retrieved[-1]] if retrieved else [],
        },
        "rule": {
            "span_days": list(SPAN_DAYS),
            "mjd_btjd_offset": MJD_BTJD_OFFSET,
            "n_selected": dict(N_SELECTED),
            "seed_texts": {a: f"{GEOMETRY_SEED_ROOT}/{a}" for a in N_SELECTED},
            "max_attempts": MAX_ATTEMPTS,
        },
        "tics": [{k: t[k] for k in ("tic", "alternative", "reasons", "years")} for t in tics],
        "alternatives": {},
    }
    for a in ("C", "D"):
        unique: dict[tuple, dict] = {}
        for t in tics:  # in TIC order, so the first of a key is its lowest eligible TIC
            if t["alternative"] != a:
                continue
            key = tuple(x["sector"] for x in t["sectors"])
            if key in unique:
                unique[key]["other_tics"].append(t["tic"])
                continue
            unique[key] = {
                "key": list(key),
                "tic": t["tic"],
                "other_tics": [],
                "years": t["years"],
                "sectors": _btjd_sectors(t),
            }
        ordered = [unique[k] for k in sorted(unique)]
        perm = np.random.default_rng(geometry_seed(a)).permutation(len(ordered))
        selected = [ordered[int(i)] for i in perm][: N_SELECTED[a]]
        out["alternatives"][a] = {
            "eligible": ordered,
            "permutation": [int(i) for i in perm],
            "selected": selected,
        }
    out["acceptance"] = acceptance_summary(out)
    return out


def acceptance_summary(listing: dict) -> dict:
    """Per selected sector, the per-attempt acceptance of the orbit draw (a numerical integral,
    ``orbit_acceptance``), and the nominal expected number of exhausted draws over the lot,
    counting **one pass** per sector and case (the layout redraws, which draw the sectors again, are
    not counted, so the figure is a lower bound): a disclosed risk, computed without any of the
    lot's seeds."""
    out = {}
    for a, part in listing["alternatives"].items():
        selected = part["selected"]
        g = len(selected)
        expected = 0.0
        rows = []
        for pos, geo in enumerate(selected):
            uses = len(NOISES) * sum(
                sum(1 for i in range(n) if i % g == pos) for _, n in REGIMES[a]
            )
            for x in geo["sectors"]:
                p = orbit_acceptance(x["span_days"])
                exhaust = (1.0 - p) ** MAX_ATTEMPTS
                expected += uses * exhaust
                rows.append(
                    {
                        "position": pos,
                        "sector": x["sector"],
                        "span_days": x["span_days"],
                        "acceptance": p,
                        "exhaustion": exhaust,
                    }
                )
        out[a] = {"sectors": rows, "expected_exhausted_draws": expected}
    return out


def selected_geometries(alternative: str, listing: dict | None = None) -> list[dict]:
    if listing is None:
        listing = json.loads(GEOMETRY_LIST.read_text(encoding="utf-8"))
    if listing.get("format") != GEOMETRY_FORMAT:
        raise SystemExit("the geometry list's format is not this module's")
    return listing["alternatives"][alternative]["selected"]


# --- the cases (K1 to K6) -----------------------------------------------------------------------


def case_seed(seed_root: str, alternative: str, noise: str, regime: str, i: int) -> int:
    text = f"{seed_root}/{alternative}/{NOISE_TAGS[noise]}/{regime}/{int(i)}"
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


def make_case(seed_root: str, alternative: str, noise: str, regime: str, i: int, g: int) -> dict:
    return {
        "id": f"{alternative}-{noise}-{regime}-{int(i):04d}",
        "class": "planet",
        "band": "measurable",
        "noise": noise,
        "index": int(i),
        "mechanism": regime,
        "catalog_variant": "own",
        "seed": str(case_seed(seed_root, alternative, noise, regime, i)),
        "extra": {"alternative": alternative, "geometry": int(g)},
    }


def lot_cases(
    alternative: str,
    n_geometries: int,
    seed_root: str = SEED_ROOT,
    sizes: dict[str, int] | None = None,
) -> list[dict]:
    """The cases of an alternative in the interleaved task order (K5); ``sizes`` (tests) replaces
    the regimes' sizes."""
    if n_geometries < 1:
        raise ValueError("no geometry")
    regimes = [(r, (sizes or {}).get(r, n)) for r, n in REGIMES[alternative]]
    groups = [(noise, r, n) for noise in NOISES for r, n in regimes]
    out = []
    for i in range(max(n for _, _, n in groups)):
        for noise, regime, n in groups:
            if i < n:
                out.append(make_case(seed_root, alternative, noise, regime, i, i % n_geometries))
    return out


# --- the layouts (L1 to L4) ---------------------------------------------------------------------


class GenerationDefectError(RuntimeError):
    """An orbit draw, a layout or a parameter draw exhausted ``MAX_ATTEMPTS``: a defect that stops
    the lot (L2, L3, X9), never a silent replacement and never a scientific outcome."""


def _orbits(rng: np.random.Generator, span: float) -> tuple[float, float, float, int]:
    """``(l1, l2, g, draws)``: the orbit gap and the orbits of a sector of real span ``span``."""
    for k in range(MAX_ATTEMPTS):
        g = float(rng.uniform(*ORBIT_GAP_DAYS))
        delta = float(rng.uniform(*DELTA_DAYS))
        l1 = (span - g) / 2.0 + delta
        l2 = span - g - l1
        if ORBIT_DAYS[0] <= l1 <= ORBIT_DAYS[1] and ORBIT_DAYS[0] <= l2 <= ORBIT_DAYS[1]:
            return l1, l2, g, k + 1
    raise GenerationDefectError(
        f"no orbit draw within 12.5 to 14.0 d in {MAX_ATTEMPTS} draws (span {span})"
    )


def _draw(geometry: dict, rng: np.random.Generator) -> dict:
    times, jitters, records = [], [], []
    for x in sorted(geometry["sectors"], key=lambda s: s["t_min_btjd"]):
        l1, l2, g, draws = _orbits(rng, float(x["span_days"]))
        blocks = []
        for _ in range(int(rng.integers(0, v4.MAX_BLOCKS + 1))):
            seconds = float(rng.uniform(*v4.BLOCK_SECONDS))
            blocks.append({"seconds": seconds, "place": float(rng.uniform())})
        rho = rng.uniform(*v4.LOSS_RATE)
        n = round(l1 / v4.DT) + round(l2 / v4.DT)
        losses = rng.uniform(size=n)
        jitter = rng.uniform(-v4.JITTER_S, v4.JITTER_S, size=n)
        t, jit, record = v4._sector(x["t_min_btjd"], (l1, l2), g, blocks, rho, losses, jitter)
        times.append(t)
        jitters.append(jit)
        records.append({**record, "sector": int(x["sector"]), "orbit_draws": draws})
    return {"times": times, "jitter_s": jitters, "sectors": records}


def layout_failure(alternative: str, result) -> str | None:
    """The layout's first failing check (L3), or None."""
    if not result.conditions["D3"]:
        return "layout:D3"
    if not result.conditions["D4"]:
        return "layout:D4"
    if alternative == "C" and not result.conditions["D1"]:
        return "layout:D1"
    if alternative == "D":
        labels = [s.label for s in result.sectors]
        if any(x is None for x in labels) or len(set(labels)) < 4:
            return "layout:labels"
    return None


def draw_layout(case: dict, geometry: dict) -> dict:
    """The case's accepted layout: attempts ``a = 0, 1, ...`` until the checks accept one."""
    seed = int(case["seed"])
    alternative = case["extra"]["alternative"]
    redraws: dict[str, int] = {}
    for attempt in range(MAX_ATTEMPTS):
        lay = _draw(geometry, np.random.default_rng(pv2.sub_seed(seed, v4.LAYOUT_STREAM, attempt)))
        result = domain.check_domain(lay["times"])
        failed = layout_failure(alternative, result)
        if failed is None:
            return {**lay, "attempt": attempt, "redraws": redraws, "domain": result}
        redraws[failed] = redraws.get(failed, 0) + 1
    raise GenerationDefectError(f"{case['id']}: no layout accepted in {MAX_ATTEMPTS} attempts")


def map_absent_year(p: dict, labels: list[int]) -> None:
    """``var_absent_year`` drawn from (2018, 2019, 2020) names the curve's sorted distinct label at
    its position (P2)."""
    if "var_absent_year" in p:
        distinct = sorted(set(int(x) for x in labels))
        position = ABSENT_YEARS.index(p["var_absent_year"])
        p["var_absent_position"] = position
        p["var_absent_year"] = int(distinct[position])


# --- the generation (P1 to P5) ------------------------------------------------------------------


def curve_digest(lc, sectors) -> str:
    h = hashlib.sha256()
    for name in ("time", "flux", "flux_err", "sector", "year"):
        a = np.ascontiguousarray(getattr(lc, name))
        h.update(name.encode() + b"\0" + str(a.dtype).encode() + b"\0" + a.tobytes())
    for s in sectors:
        h.update(json.dumps([s.sector, s.year, s.t_start, s.t_end, s.n_points]).encode())
    return h.hexdigest()


def build_curve(case: dict, geometry: dict) -> dict:
    """The case's light curve on its geometry (P1 to P5): ``lc``, ``sectors``, ``parameters``,
    ``model`` (the twin), ``layout``, ``redraws``, ``attempt_seed``, ``profile`` and ``digest``."""
    from refute.packs.tess import synthetic
    from refute.packs.tess.params import HoldoutParams, SnrParams
    from refute.packs.tess.types import LightCurveData, SectorInfo

    if case["class"] != "planet" or case["mechanism"] not in (
        "three_years",
        "variability_some_years",
    ):
        raise ValueError(f"{case['id']}: not a planet of this package's regimes")
    gate, hidden_min = SnrParams().min_snr, HoldoutParams().min_snr
    seed = int(case["seed"])
    lay = draw_layout(case, geometry)
    redraws = dict(lay["redraws"])
    labels = [int(s.label) for s in lay["domain"].sectors]
    numbers = [int(r["sector"]) for r in lay["sectors"]]
    cadences = list(zip(numbers, lay["times"], strict=True))
    time = np.concatenate([t for _, t in cadences])
    years = np.concatenate([np.full(t.size, y) for (_, t), y in zip(cadences, labels, strict=True)])
    profile: dict = {}
    for attempt in range(MAX_ATTEMPTS):
        seed_k = seed if attempt == 0 else pv2.sub_seed(seed, "redraw", attempt)
        p = pv2.draw_parameters(case, np.random.default_rng(seed_k), float(time.min()))
        map_absent_year(p, labels)
        reason = pv2._mechanism_condition(case, p, cadences)
        if reason is None:
            reason, profile = pv2._place_in_band(synthetic, case, p, time, years, gate, hidden_min)
        if reason is None:
            break
        redraws[reason] = redraws.get(reason, 0) + 1
    else:
        raise GenerationDefectError(f"{case['id']}: no valid draw in {MAX_ATTEMPTS} attempts")
    if "var_amplitude_factor" in p:
        p["var_amplitude"] = p["var_amplitude_factor"] * p["depth"]
    rng_noise = np.random.default_rng(pv2.sub_seed(seed_k, "noise"))
    times, fluxes, errors, nums, yrs, infos = [], [], [], [], [], []
    for (number, t), year in zip(cadences, labels, strict=True):
        model = synthetic.signal_model(t, pv2._signal_spec(synthetic, case, p, p["depth"]))
        model = model * (1.0 + pv2.TREND_AMPLITUDE * np.sin(2 * np.pi * t / pv2.TREND_PERIOD_DAYS))
        if "var_amplitude" in p and year != p.get("var_absent_year"):
            model = model + p["var_amplitude"] * np.sin(
                2 * np.pi * (t - p["var_phase"]) / p["var_period"]
            )
        flux = model + pv2._noise(rng_noise, t, case["noise"])
        times.append(t)
        fluxes.append(flux)
        errors.append(np.full(t.size, pv2.NOISE_PPM * 1e-6))
        nums.append(np.full(t.size, number))
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
    lc = LightCurveData(*(np.concatenate(x) for x in (times, fluxes, errors, nums, yrs)))
    twin = rs.noiseless_model(case, p, lc.time, lc.year, 1.0)
    return {
        "lc": lc,
        "sectors": infos,
        "parameters": p,
        "model": twin,
        "layout": {"attempt": lay["attempt"], "redraws": lay["redraws"], "sectors": lay["sectors"]},
        "redraws": redraws,
        "attempt_seed": str(seed_k),
        "profile": profile,
        "digest": curve_digest(lc, infos),
    }


def case_digest(case: dict, geometry: dict) -> str:
    """The curve's SHA-256 (P5; the determinism check runs it in several processes)."""
    return build_curve(case, geometry)["digest"]


# --- the record (R1 to R6) ----------------------------------------------------------------------


def identity_flag(round_record: dict, period: float) -> dict:
    """R3: the train ephemeris' period against the injected one (after the engine calls)."""
    eph = round_record.get("train_ephemeris")
    if not isinstance(eph, dict) or eph.get("period") is None:
        return {"identifiable": False, "period_ratio": None, "flag": None}
    ratio = float(eph["period"]) / float(period)
    return {
        "identifiable": True,
        "period_ratio": ratio,
        "flag": bool(abs(ratio - 1.0) > IDENTITY_TOLERANCE),
    }


def oracle_year(time, flux, spans, truth: dict, min_snr: float) -> dict:
    """R4: the evaluator's diagnostic oracle of one hidden year (the declaration, section 5, R3).
    ``time`` and ``flux`` are the whole curve's; ``spans`` the year's sectors (closed)."""
    order = np.argsort(np.asarray(time, dtype=float), kind="stable")
    t = np.asarray(time, dtype=float)[order]
    f = np.asarray(flux, dtype=float)[order]
    period, t0, t14 = float(truth["period"]), float(truth["t0"]), float(truth["duration"])
    epochs = []
    for lo, hi in spans:
        epochs += range(math.ceil((lo - t0) / period), math.floor((hi - t0) / period) + 1)
    epochs = sorted(set(epochs))
    reach = 4.0 * t14  # another centre farther than this cannot touch the window's cadences
    k_max = max(1, math.ceil(reach / period))
    kept, skipped = 0, 0
    deficits, residuals, n_base = [], [], 0
    for n in epochs:
        tc = t0 + n * period
        lo_i = int(np.searchsorted(t, tc - 3.0 * t14, side="left"))
        hi_i = int(np.searchsorted(t, tc + 3.0 * t14, side="right"))
        tt, ff = t[lo_i:hi_i], f[lo_i:hi_i]
        near_other = np.zeros(tt.size, bool)
        for k in range(1, k_max + 1):  # every other injected centre that can reach the window
            for to in (t0 + (n - k) * period, t0 + (n + k) * period):
                near_other |= np.abs(tt - to) <= t14
        dt = tt - tc
        inside = (np.abs(dt) <= t14 / 2.0) & ~near_other
        base = (np.abs(dt) >= t14) & (np.abs(dt) <= 3.0 * t14) & ~near_other
        left, right = int(np.sum(base & (dt < 0))), int(np.sum(base & (dt > 0)))
        if int(inside.sum()) < ORACLE_MIN_IN or left < ORACLE_MIN_SIDE or right < ORACLE_MIN_SIDE:
            skipped += 1
            continue
        kept += 1
        coef = np.polyfit(dt[base], ff[base], 1)
        deficits.append(np.polyval(coef, dt[inside]) - ff[inside])
        residuals.append(ff[base] - np.polyval(coef, dt[base]))
        n_base += int(base.sum())
    out = {
        "n_centres": len(epochs),
        "kept": kept,
        "skipped": skipped,
        "depth": None,
        "error": None,
        "snr": None,
        "detectable": False,
        "reason": None,
    }
    if kept == 0:
        out["reason"] = "no kept transit"
        return out
    d = np.concatenate(deficits)
    r = np.concatenate(residuals)
    dof = n_base - 2 * kept
    sigma = math.sqrt(float(np.sum(r * r)) / dof) if dof > 0 else float("nan")
    depth = float(np.mean(d))
    error = sigma / math.sqrt(d.size)
    out.update(depth=depth, error=error)
    if not (math.isfinite(error) and error > 0 and math.isfinite(depth)):
        out["reason"] = "non-finite or zero error"
        return out
    out["snr"] = depth / error
    out["detectable"] = bool(out["snr"] >= min_snr)
    if not out["detectable"]:
        out["reason"] = "below min_snr"
    return out


def record_target(
    case: dict, geometry: dict, expected: dict | None, spec: SubLot = SUBLOTS["viability-c"]
) -> dict:
    """One target's record (R1 to R5): its rounds with the twin, then, after the engine calls, its
    identity flags and its oracle."""
    from refute.packs.tess.holdout import calibration_measurement

    if v3.STATE["problem"] is not None:
        raise RuntimeError(f"the M4 configuration is not loaded: {v3.STATE['problem']}")
    plan = v3._plan()
    problems = rs.study_configuration_problems(v3.STATE["identity"], plan)
    if problems:
        raise RuntimeError("the configuration is not the study's: " + "; ".join(problems))
    if expected is None or v3.STATE["identity"] != expected:
        raise RuntimeError("this worker's configuration has another identity than the main one")
    built = build_curve(case, geometry)
    lc, sectors, p = built["lc"], built["sectors"], built["parameters"]
    years = sorted({int(s.year) for s in sectors})
    truth = rs.EvaluatorTruth(rs.truth_of(case, p, 1.0))  # made before, read only after the calls
    with rs.engine_call():
        rounds = [
            calibration_measurement(
                lc, sectors, y, plan, identity=rs.calibration_identity(), twin_model=built["model"]
            )
            for y in years
        ]
    min_snr = plan.gauntlet.holdout_by_year.min_snr
    plain_truth = {k: truth[k] for k in truth}
    identity = {str(r["hidden_year"]): identity_flag(r, plain_truth["period"]) for r in rounds}
    oracle = {
        str(y): oracle_year(
            lc.time,
            lc.flux,
            [(s.t_start, s.t_end) for s in sectors if s.year == y],
            plain_truth,
            min_snr,
        )
        for y in years
    }
    return {
        "format": RECORD_FORMAT,
        "target": f"{spec.prefix}/{case['id']}",
        "case_id": case["id"],
        "alternative": case["extra"]["alternative"],
        "noise": case["noise"],
        "regime": case["mechanism"],
        "index": case["index"],
        "geometry": {
            "position": case["extra"]["geometry"],
            "key": list(geometry["key"]),
            "tic": geometry["tic"],
        },
        "seed": case["seed"],
        "attempt_seed": built["attempt_seed"],
        "layout": built["layout"],
        "redraws": built["redraws"],
        "years": years,
        "sectors": [
            {
                "sector": int(s.sector),
                "year": int(s.year),
                "t_start": s.t_start,
                "t_end": s.t_end,
                "n_points": int(s.n_points),
            }
            for s in sectors
        ],
        "curve_sha256": built["digest"],
        "configuration": v3.STATE["identity"],
        "rounds": rounds,
        "identity": identity,
        "oracle": oracle,
        "truth": plain_truth,
    }


ORACLE_FIELDS = ("n_centres", "kept", "skipped", "depth", "error", "snr", "detectable", "reason")
IDENTITY_FIELDS = ("identifiable", "period_ratio", "flag")
STAMP_TOLERANCE_DAYS = 1.0 / 86400.0  # the first time stamp is t_min' plus at most 0.25 s jitter


def _sector_problems(key: str, sectors, order: list[dict], alternative: str) -> list[str]:
    """R6: the record's sectors are the geometry's, in time order, each starting at its real date
    (within the jitter), ending before its real end, labelled by the year of its first time stamp;
    three labels for C, four or more for D."""
    from refute.packs.tess.types import btjd_to_year

    fields = ("sector", "year", "t_start", "t_end", "n_points")
    if not (
        isinstance(sectors, list)
        and len(sectors) == len(order)
        and all(isinstance(x, dict) and all(f in x for f in fields) for x in sectors)
    ):
        return [f"{key}: sectors are not the geometry's"]
    out = []
    for x, g in zip(sectors, order, strict=True):
        try:
            start, end, n = float(x["t_start"]), float(x["t_end"]), int(x["n_points"])
            label = btjd_to_year(start)
        except (TypeError, ValueError, OverflowError):
            out.append(f"{key}: sector {x.get('sector')} has invalid dates")
            continue
        if int(x["sector"]) != int(g["sector"]):
            out.append(f"{key}: sector {x['sector']} is not the geometry's {g['sector']}")
        elif abs(start - g["t_min_btjd"]) > STAMP_TOLERANCE_DAYS or not (
            start < end <= g["t_max_btjd"] + STAMP_TOLERANCE_DAYS
        ):
            out.append(f"{key}: sector {x['sector']} is not at its real dates")
        elif x["year"] != label or n < 1:
            out.append(f"{key}: sector {x['sector']} label {x['year']!r} or cadences {n}")
    labels = {x.get("year") for x in sectors}
    if (alternative == "C" and len(labels) != 3) or (alternative == "D" and len(labels) < 4):
        out.append(f"{key}: {len(labels)} labels for {alternative}")
    return out


def record_problems(
    rec, case: dict, geometry: dict, configuration: dict, spec: SubLot = SUBLOTS["viability-c"]
) -> list[str]:
    """R6: why a record file is not a complete record of its task."""
    key = case["id"]
    if not isinstance(rec, dict):
        return [f"{key}: not a record"]
    out = []
    for field, value in (
        ("format", RECORD_FORMAT),
        ("target", f"{spec.prefix}/{case['id']}"),
        ("case_id", case["id"]),
        ("alternative", case["extra"]["alternative"]),
        ("noise", case["noise"]),
        ("regime", case["mechanism"]),
        ("index", case["index"]),
        ("seed", case["seed"]),
    ):
        if rec.get(field) != value:
            out.append(f"{key}: {field} {rec.get(field)!r} is not {value!r}")
    want_geo = {
        "position": case["extra"]["geometry"],
        "key": list(geometry["key"]),
        "tic": geometry["tic"],
    }
    if rec.get("geometry") != want_geo:
        out.append(f"{key}: geometry {rec.get('geometry')!r} is not the case's {want_geo!r}")
    if rec.get("configuration") != configuration:
        out.append(f"{key}: another configuration")
    order = sorted(geometry["sectors"], key=lambda s: s["t_min_btjd"])
    numbers_want = [int(x["sector"]) for x in order]
    seed = rec.get("attempt_seed")
    if not (isinstance(seed, str) and seed.isdigit()):
        out.append(f"{key}: attempt_seed {seed!r}")
    digest = rec.get("curve_sha256")
    if not (
        isinstance(digest, str) and len(digest) == 64 and set(digest) <= set("0123456789abcdef")
    ):
        out.append(f"{key}: curve_sha256 {digest!r}")
    if not isinstance(rec.get("redraws"), dict):
        out.append(f"{key}: redraws {rec.get('redraws')!r}")
    lay = rec.get("layout")
    if not (
        isinstance(lay, dict)
        and isinstance(lay.get("attempt"), int)
        and isinstance(lay.get("redraws"), dict)
        and isinstance(lay.get("sectors"), list)
        and [x.get("sector") if isinstance(x, dict) else None for x in lay["sectors"]]
        == numbers_want
    ):
        out.append(f"{key}: layout is not one entry per geometry sector")
    out += _sector_problems(key, rec.get("sectors"), order, case["extra"]["alternative"])
    sectors = rec.get("sectors")
    ok = isinstance(sectors, list) and all(isinstance(x, dict) for x in sectors)
    years = rec.get("years")
    labels = sorted({x.get("year") for x in sectors}) if ok else None
    if years != labels:
        out.append(f"{key}: years {years} are not the sectors' labels {labels}")
    rounds = rec.get("rounds")
    hidden = (
        sorted(r.get("hidden_year") for r in rounds if isinstance(r, dict))
        if isinstance(rounds, list)
        else None
    )
    if hidden != years or len(rounds or []) != len(years or []):
        out.append(f"{key}: rounds {hidden} for years {years}")
    for r in rounds if isinstance(rounds, list) else []:
        missing = [k for k in x2.ROUND_FIELDS if not isinstance(r, dict) or k not in r]
        if missing:
            out.append(f"{key}: a round lacks {missing[:4]}")
            break
    for name, fields in (("identity", IDENTITY_FIELDS), ("oracle", ORACLE_FIELDS)):
        part = rec.get(name)
        if not isinstance(part, dict) or sorted(part) != sorted(str(y) for y in years or []):
            out.append(f"{key}: {name} not one entry per year")
        elif any(not isinstance(v, dict) or set(v) != set(fields) for v in part.values()):
            out.append(f"{key}: an entry of {name} lacks its fields")
    truth = rec.get("truth")
    if not isinstance(truth, dict) or set(truth) != set(x2.TRUTH_FIELDS):
        out.append(f"{key}: truth {sorted(truth) if isinstance(truth, dict) else truth}")
    return out


# --- the runner (X1 to X8) ----------------------------------------------------------------------

CODE_FILES = (
    "pyproject.toml",
    "uv.lock",
    "docs/validation/v0.2.1/population/viability_cd.py",
    "docs/validation/v0.2.1/population/population_v4.py",
    "docs/validation/v0.2.1/population/x2_study.py",
    "docs/validation/v0.2.1/population/rmin_study.py",
    "docs/validation/v0.2.1/population/population_v3.py",
    "docs/validation/v0.2.1/population/population_v2.py",
)


def code_digest() -> str:
    """SHA-256 over the engine (``src/refute/**/*.py``), the lock files and the modules used."""
    files = sorted(
        [p.relative_to(REPO).as_posix() for p in (REPO / "src" / "refute").rglob("*.py")]
        + list(CODE_FILES)
    )
    h = hashlib.sha256()
    for rel in files:
        h.update(rel.encode() + b"\0" + (REPO / rel).read_bytes() + b"\0")
    return h.hexdigest()


def record_path(run_dir: Path, case_id: str) -> Path:
    return x2.record_path(run_dir, case_id, 0)


def timing_path(run_dir: Path, case_id: str) -> Path:
    return Path(run_dir) / "timings" / f"{case_id}.json"


def manifest_payload(
    spec: SubLot, tasks: list[dict], configuration: dict, geometry_sha256: str
) -> dict:
    from refute.core.canonical import canonical_sha256

    return rs._canonical(
        {
            "format": LOT_FORMAT,
            "lot": spec.name,
            "alternative": spec.alternative,
            "prefix": spec.prefix,
            "seed_root": spec.seed_root,
            "deadline_hours": spec.deadline_hours,
            "lp_hours": spec.lp_hours,
            "geometry_sha256": geometry_sha256,
            "configuration": configuration,
            "plan_sha256": canonical_sha256(v3._plan().model_dump(mode="json")),
            "code_sha256": code_digest(),
            "environment": x2.environment(),
            "expected": [[c["id"], c["seed"], c["extra"]["geometry"]] for c in tasks],
        }
    )


def _task(task: tuple) -> tuple[dict, float]:
    """A worker's task: the record and its wall seconds (kept outside the record)."""
    import time

    case, geometry, expected, spec = task
    start = time.perf_counter()
    record = record_target(case, geometry, expected, spec)
    return record, time.perf_counter() - start


def cost_projection(seconds: list[float], n_tasks: int, workers: int) -> dict:
    """X5: the mean task seconds and the sub-lot's projected LP-h and hours."""
    m = float(np.mean(seconds))
    return {
        "mean_task_seconds": m,
        "projected_lp_hours": m * n_tasks / 3600.0,
        "projected_hours": m * n_tasks / workers / 3600.0,
    }


def lot_problems(
    run_dir: Path,
    spec: SubLot,
    geometries: list[dict],
    tasks: list[dict] | None = None,
    full: bool = False,
) -> list[str]:
    """X8: every task one complete record at its own path; no record outside the tasks; with
    ``full`` the manifest's tasks are exactly the declared sub-lot's. Never raises on a damaged
    file: each is a problem (Codex's review)."""
    run_dir = Path(run_dir)
    try:
        manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
        expected = {c: (s, g) for c, s, g in manifest["expected"]}
        configuration = manifest["configuration"]
    except (OSError, ValueError, KeyError, TypeError) as exc:
        return [f"the manifest is not readable: {type(exc).__name__}"]
    canonical = {f"records/{c}/000.json" for c in expected}
    problems = [
        f"{r}: a record file not at a task's own path"
        for r in record_files(run_dir)
        if r not in canonical
    ]
    declared = (
        tasks if tasks is not None else lot_cases(spec.alternative, len(geometries), spec.seed_root)
    )
    by_id = {c["id"]: c for c in declared}
    if full:
        listed = [[c, s, g] for c, s, g in manifest["expected"]]
        want = [[c["id"], c["seed"], c["extra"]["geometry"]] for c in declared]
        if listed != want:
            problems.append(
                f"the manifest's {len(listed)} tasks are not the declared sub-lot's {len(want)}"
            )
    for case_id in expected:
        path = record_path(run_dir, case_id)
        if not path.exists():
            problems.append(f"{case_id}: no record")
            continue
        try:
            rec = json.loads(path.read_bytes())
        except (OSError, ValueError):
            problems.append(f"{case_id}: not JSON")
            continue
        case = by_id.get(case_id)
        if case is None or not (0 <= case["extra"]["geometry"] < len(geometries)):
            problems.append(f"{case_id}: not one of the sub-lot's cases")
            continue
        geometry = geometries[case["extra"]["geometry"]]
        problems += record_problems(rec, case, geometry, configuration, spec)
    return problems


def record_files(run_dir: Path) -> list[str]:
    """The record files of a run folder (relative paths); leftover temporary files are not
    records."""
    root = Path(run_dir) / "records"
    if not root.exists():
        return []
    return sorted(
        p.relative_to(run_dir).as_posix()
        for p in root.rglob("*.json")
        if not p.name.startswith(".")
    )


def load_records(run_dir: Path) -> tuple[list[dict], list[str]]:
    """The records that parse, and the files that do not (each a problem, never an exception)."""
    good, bad = [], []
    for rel in record_files(run_dir):
        try:
            rec = json.loads((Path(run_dir) / rel).read_bytes())
        except (OSError, ValueError):
            bad.append(rel)
            continue
        (good if isinstance(rec, dict) else bad).append(rec if isinstance(rec, dict) else rel)
    return good, bad


def run_lot(
    spec: SubLot,
    run_dir: Path,
    geometries: list[dict],
    geometry_sha256: str,
    tasks: list[dict] | None = None,
    workers: int = WORKERS,
    executor=None,
    clock=None,
) -> dict:
    """Generate and record a sub-lot (X1 to X7), resumable, on ``workers`` spawned workers on
    logical processors 8 to 31; ``x2_study.run_x2_lot``'s pattern with the sub-lot's ceiling and its
    cost check. ``tasks`` (tests) replaces the sub-lot's cases."""
    import time
    from concurrent.futures import FIRST_COMPLETED, wait

    if v3.STATE["problem"] is not None:
        raise SystemExit(f"the M4 configuration is not loaded: {v3.STATE['problem']}")
    problems = rs.study_configuration_problems(v3.STATE["identity"], v3._plan())
    if problems:
        raise SystemExit("the configuration is not the study's: " + "; ".join(problems))
    affinity = pv2.affinity_mask()
    if executor is None and affinity != LOT_AFFINITY:
        raise SystemExit(f"the affinity is {affinity}, not {LOT_AFFINITY} (processors 8 to 31)")
    workers = int(workers)
    if workers < 1:
        raise SystemExit(f"workers must be positive, got {workers}")
    os.environ.update(rs.THREAD_ENV)
    run_dir = Path(run_dir)
    configuration = v3.STATE["identity"]
    if tasks is None:
        tasks = lot_cases(spec.alternative, len(geometries), spec.seed_root)
    payload = manifest_payload(spec, tasks, configuration, geometry_sha256)
    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        try:
            stored = json.loads(manifest_path.read_text(encoding="utf-8"))
        except ValueError as exc:
            raise SystemExit(f"the run folder's manifest is not readable: {exc}") from exc
        if stored != payload:
            raise SystemExit(
                "the run folder's manifest is another sub-lot's, geometry list's, configuration's, "
                "plan's, code's or environment's"
            )
    else:
        x2.write_record_atomic(manifest_path, json.dumps(payload, indent=1) + "\n")
    consumed_before = x2.consumed_hours(run_dir)
    blocked_keys, retry_keys = x2.task_states(run_dir)
    todo, terminal_failures, retried = [], [], []
    for c in tasks:
        path = record_path(run_dir, c["id"])
        geometry = geometries[c["extra"]["geometry"]]
        if not path.exists():
            key = (c["id"], 0)
            if key in blocked_keys:
                terminal_failures.append({"case_id": c["id"], "state": blocked_keys[key]})
                continue
            if key in retry_keys:
                retried.append({"case_id": c["id"]})
            todo.append((c, geometry, configuration, spec))
            continue
        try:
            existing = json.loads(path.read_bytes())
        except ValueError:
            existing = None
        bad = record_problems(existing, c, geometry, configuration, spec)
        if bad:
            raise SystemExit("an existing record is incomplete (never replaced): " + "; ".join(bad))
    check_path = run_dir / "cost-check.json"
    n_check = max(1, math.ceil(COST_CHECK_FRACTION * len(tasks)))
    check_ids = [c["id"] for c in tasks[:n_check]]
    cost_stop = False
    if check_path.exists():
        cost_stop = json.loads(check_path.read_text(encoding="utf-8")).get("stop") is True
    defect_path = run_dir / "defect.json"
    defect = defect_path.exists()  # X9: a generation defect stops the lot for good
    started = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    # an invocation's stamp names its consumption record and its markers: never an earlier one's
    # (two invocations within one tick of the system clock would otherwise share it)
    while (run_dir / "consumption" / f"{started}.json").exists():
        time.sleep(0.001)
        started = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
    failures: list[dict] = []
    dispatch_error = None
    submitted = 0
    clock = time.monotonic if clock is None else clock
    t0 = clock()
    x2._write_consumption(run_dir, started, 0.0, closed=False)
    deadline_reached = False
    futures: dict = {}

    def cost_check() -> None:
        nonlocal cost_stop
        if check_path.exists():
            return
        seconds = []
        for case_id in check_ids:
            tp = timing_path(run_dir, case_id)
            if not (record_path(run_dir, case_id).exists() and tp.exists()):
                return
            seconds.append(float(json.loads(tp.read_text(encoding="utf-8"))["seconds"]))
        projection = cost_projection(seconds, len(tasks), workers)
        stop = (
            projection["projected_lp_hours"] > spec.lp_hours
            or projection["projected_hours"] > spec.deadline_hours
        )
        x2.write_record_atomic(
            check_path,
            json.dumps(
                {
                    "tasks_checked": len(check_ids),
                    "tasks": len(tasks),
                    "workers": workers,
                    **projection,
                    "lp_hours_ceiling": spec.lp_hours,
                    "hours_ceiling": spec.deadline_hours,
                    "stop": stop,
                    "run_started_utc": started,
                },
                indent=1,
            )
            + "\n",
        )
        cost_stop = stop

    def collect(done) -> None:
        nonlocal defect
        for fut in done:
            case = futures.pop(fut)[0]
            try:
                record, seconds = fut.result()
            except Exception as exc:  # noqa: BLE001 - every failure is recorded, none retried
                failure = {"case_id": case["id"], "error": repr(exc)}
                failures.append(failure)
                x2.write_record_atomic(
                    x2.failure_path(run_dir, case["id"], 0, started),
                    json.dumps({**failure, "run_started_utc": started}, indent=1) + "\n",
                )
                if isinstance(exc, GenerationDefectError):
                    defect = True
                    if not defect_path.exists():
                        x2.write_record_atomic(
                            defect_path,
                            json.dumps({**failure, "run_started_utc": started}, indent=1) + "\n",
                        )
            else:
                # the timing first: a run cut between the two writes leaves a task without its
                # record (blocked until a decision), never a record the cost check cannot read
                tp = timing_path(run_dir, case["id"])
                if not tp.exists():
                    x2.write_record_atomic(tp, json.dumps({"seconds": seconds}) + "\n")
                path = record_path(run_dir, case["id"])
                if not path.exists():
                    x2.write_record_atomic(path, x2.record_text(record))
            x2._write_consumption(run_dir, started, (clock() - t0) / 3600.0, closed=False)
        cost_check()

    try:
        pool = rs._spawn_pool(workers) if executor is None else executor
        with pool:
            try:
                cost_check()
                for task in todo:
                    while len(futures) >= 4 * workers:
                        done, _ = wait(futures, return_when=FIRST_COMPLETED)
                        collect(done)
                    if cost_stop or defect:
                        break
                    case_id = task[0]["id"]
                    x2.write_record_atomic(
                        x2.attempt_path(run_dir, case_id, 0, started),
                        json.dumps({"run_started_utc": started}) + "\n",
                    )
                    elapsed = (clock() - t0) / 3600.0
                    if consumed_before + elapsed >= spec.deadline_hours:
                        x2.write_record_atomic(
                            x2.not_submitted_path(run_dir, case_id, 0, started),
                            json.dumps({"run_started_utc": started}) + "\n",
                        )
                        deadline_reached = True
                        break
                    futures[pool.submit(_task, task)] = task
                    submitted += 1
                    x2._write_consumption(run_dir, started, elapsed, closed=False)
            except Exception as exc:  # noqa: BLE001 - the dispatch stops, reported, not retried
                dispatch_error = f"submission: {exc!r}"
            while futures:
                done, _ = wait(futures, return_when=FIRST_COMPLETED)
                collect(done)
    except Exception as exc:  # noqa: BLE001 - the pool itself failed: reported, not retried
        dispatch_error = (dispatch_error or "") + f" pool: {exc!r}"
    elapsed_hours = (clock() - t0) / 3600.0
    x2._write_consumption(run_dir, started, elapsed_hours, closed=True)
    integrity = lot_problems(run_dir, spec, geometries, tasks)
    report = {
        "format": LOT_FORMAT,
        "lot": spec.name,
        "run": str(run_dir),
        "started_utc": started,
        "workers": workers,
        "affinity": affinity,
        "tasks": len(tasks),
        "dispatched": len(todo),
        "submitted": submitted,
        "dispatch_error": dispatch_error,
        "deadline_hours": spec.deadline_hours,
        "deadline_reached": deadline_reached,
        "cost_stop": cost_stop,
        "defect": defect,
        "elapsed_hours": elapsed_hours,
        "consumed_before_hours": consumed_before,
        "consumed_total_hours": consumed_before + elapsed_hours,
        "failures": failures,
        "terminal_failures": terminal_failures,
        "retried": retried,
        "leftover_temporary_files": sorted(
            p.relative_to(run_dir).as_posix() for p in (run_dir / "records").rglob(".*.tmp")
        )
        if (run_dir / "records").exists()
        else [],
        "integrity_problems": integrity,
        "complete": (
            dispatch_error is None
            and not deadline_reached
            and not cost_stop
            and not defect
            and not failures
            and not terminal_failures
            and not integrity
        ),
    }
    with open(run_dir / f"run-report-{started}.json", "x", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(report, indent=1) + "\n")
    return report


def determinism(spec: SubLot, geometries: list[dict], n: int, workers: int = WORKERS) -> dict:
    """The generation's determinism check (the declaration, section 7): the curves of the first
    ``n`` tasks built three times, in this process, on one spawned worker and on ``workers``
    spawned workers; every digest must agree. Builds curves of the lot: authorization 2 only."""
    tasks = lot_cases(spec.alternative, len(geometries), spec.seed_root)[:n]
    args = [(c, geometries[c["extra"]["geometry"]]) for c in tasks]
    runs = [[case_digest(c, g) for c, g in args]]
    for w in (1, workers):
        with rs._spawn_pool(w) as pool:
            runs.append(list(pool.map(case_digest, *zip(*args, strict=True))))
    return {
        "lot": spec.name,
        "tasks": [c["id"] for c in tasks],
        "workers": [0, 1, workers],
        "digests": runs[0],
        "agree": runs[0] == runs[1] == runs[2],
    }


def main(argv: list[str]) -> int:
    """``geometries <out>`` (the list, from gate 3b's saved metadata; written once),
    ``determinism <out> --lot <name> --n <k>`` and ``run <run_dir> --lot viability-c|viability-d``
    (authorization 2 only), or ``check <run_dir> --lot <name> [--full]``."""
    command = argv[0]
    if command == "determinism":
        spec = SUBLOTS[argv[argv.index("--lot") + 1]]
        n = int(argv[argv.index("--n") + 1])
        result = determinism(spec, selected_geometries(spec.alternative), n)
        with open(Path(argv[1]), "x", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(result, indent=1) + "\n")
        print(json.dumps({"agree": result["agree"], "tasks": len(result["tasks"])}))
        return 0 if result["agree"] else 1
    if command == "geometries":
        rows, digest = load_mast_rows()
        listing = geometry_list(rows, digest)
        out = Path(argv[1])
        with open(out, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(listing, indent=1) + "\n")
        summary = {
            a: {
                "eligible": len(part["eligible"]),
                "selected": len(part["selected"]),
                "expected_exhausted_draws": listing["acceptance"][a]["expected_exhausted_draws"],
            }
            for a, part in listing["alternatives"].items()
        }
        print(json.dumps(summary, indent=1))
        return 0
    if command not in ("run", "check") or "--lot" not in argv:
        raise SystemExit(f"unknown command {argv!r}")
    spec = SUBLOTS[argv[argv.index("--lot") + 1]]
    run_dir = Path(argv[1])
    geometries = selected_geometries(spec.alternative)
    if command == "check":
        problems = lot_problems(run_dir, spec, geometries, full="--full" in argv)
        print(json.dumps({"problems": problems}, indent=1))
        return 1 if problems else 0
    geometry_sha256 = hashlib.sha256(GEOMETRY_LIST.read_bytes()).hexdigest()
    report = run_lot(spec, run_dir, geometries, geometry_sha256)
    print(json.dumps({k: report[k] for k in ("tasks", "dispatched", "complete")}))
    return 0 if report["complete"] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
