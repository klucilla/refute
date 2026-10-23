"""v0.2.1 synthetic population generator, version 4 (plan B; the profile three-observing-years/1).

Acceptance record: ``population-v4-acceptance.md`` next to this file (committed before its
tests, which were committed before this code). Plan B:
docs/validation/v0.2.1/reopen/stage-1/plan-b/README.md, section 3; the population study's
Amendment B (docs/validation/v0.2.1/population-study.md).

What is new is only the time layout of each case and the mapping of the variability-free year:

- the **geometry** is allocated by the case's position in its group (class, noise model, band,
  mechanism): G-a (both separations about one year) at even positions, G-b (one about one year,
  one about two years) at odd ones, "short then long" and "long then short" alternating;
- the **layout** is drawn from its own stream, ``sub_seed(seed, "layout", a)``: the first start,
  the separations, and per sector the orbits, the orbit gap, the loss blocks, the single-cadence
  losses and the jitter; it is drawn again (``a + 1``) only when the domain function
  (``refute.packs.tess.domain``) rejects it, the reason recorded as ``layout:D<n>``;
- ``var_absent_year`` is drawn by ``population_v2`` from (2018, 2019, 2020); its position in
  that tuple names the curve's own label at that position.

Everything else (the parameters and their redraws, the bands, the depth limits, the noise, the
trend, the variability, the pixel and auxiliary data, the catalog, the serialization) is
``population_v2``'s (frozen; loaded by path after its SHA-256 is checked), in the same order.
This file is outside ``src/``; it never imports an engine module and runs no analysis.
"""

from __future__ import annotations

import hashlib
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np

from refute.packs.tess import domain

HERE = Path(__file__).resolve().parent
V2_PATH = HERE / "population_v2.py"
# The frozen version 2 (its last commit 37c92c9617fb4077b7ec6f3c31c0972193ff0702).
V2_SHA256 = "8b3b6ad6aca6e713636b04e40db5a7d253c05458c8b143c38d984100072c1f82"


def _load_v2():
    if hashlib.sha256(V2_PATH.read_bytes()).hexdigest() != V2_SHA256:
        raise SystemExit("population_v2.py is not the frozen version 2 (SHA-256)")
    if "population_v2" in sys.modules:
        return sys.modules["population_v2"]
    spec = importlib.util.spec_from_file_location("population_v2", V2_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["population_v2"] = module
    spec.loader.exec_module(module)
    return module


pv2 = _load_v2()

# population_v2's objects, reused as they are.
draw_parameters = pv2.draw_parameters
_place_in_band = pv2._place_in_band
_mechanism_condition = pv2._mechanism_condition
_noise = pv2._noise
sub_seed = pv2.sub_seed
BANDS = pv2.BANDS
DEPTH_LIMITS = pv2.DEPTH_LIMITS
MAX_ATTEMPTS = pv2.MAX_ATTEMPTS

GENERATOR = "refute-population-v4/1"
ACCEPTANCE_PREFIX = "refute-v0.2.1-population-v4-acceptance"
SELFTEST_PREFIX = "refute-v0.2.1-population-v4-selftest"
LAYOUT_STREAM = "layout"
PLANET_REGIMES = ("three_years", "variability_some_years")
PLANETS_PER_REGIME = 180

FIRST_START = 1325.0
ONE_YEAR_DAYS = 365.25
SHORT_SEPARATION = (345.0, 385.0)
LONG_SEPARATION = (710.0, 750.0)
ORBIT_DAYS = (12.5, 14.0)
ORBIT_GAP_DAYS = (0.5, 2.0)
MAX_BLOCKS = 4
BLOCK_SECONDS = (600.0, 21600.0)
LOSS_RATE = (0.0, 0.05)
JITTER_S = 0.25
CADENCE_S = 120.0
DT = CADENCE_S / 86400.0
ABSENT_YEARS = (2018, 2019, 2020)
REDRAW_REASONS = (
    "layout:D1",
    "layout:D2",
    "layout:D3",
    "layout:D4",
    "layout:D5",
    "band",
    "depth_limit",
    "no_transit_in_a_year",
    "commensurate_periods",
)


# --- the population -----------------------------------------------------------------------------


def geometry_of(j: int) -> dict:
    """The geometry of the case at position ``j`` of its group (section 2.2)."""
    if j % 2 == 0:
        return {"geometry": "G-a"}
    return {"geometry": "G-b", "order": "short-long" if j % 4 == 1 else "long-short"}


def _b2(prefix: str) -> list[tuple[dict, int]]:
    """Every case of the B2 structure with its position in its group, in a fixed order."""
    out = []
    for noise in ("white", "correlated"):
        for band in ("below", "near", "measurable"):
            for i in range(2 * PLANETS_PER_REGIME):
                regime, j = divmod(i, PLANETS_PER_REGIME)
                case = pv2._case(
                    prefix,
                    "planet",
                    band,
                    noise,
                    i,
                    PLANET_REGIMES[regime],
                    pv2.CATALOG_VARIANTS[i % 5],
                    geometry_of(j),
                )
                out.append((case, j))
        for band, n in (("below", 100), ("near", 100), ("measurable", 250)):
            seen: dict[str, int] = {}
            for i in range(n):
                mech = pv2._fp_mechanism(i, n)
                j = seen.get(mech, 0)
                seen[mech] = j + 1
                case = pv2._case(
                    prefix,
                    "false_positive",
                    band,
                    noise,
                    i,
                    mech,
                    pv2.CATALOG_VARIANTS[i % 5],
                    geometry_of(j),
                )
                out.append((case, j))
        n = 2200 if noise == "white" else 600
        seen = {}
        for i in range(n):
            mech = pv2._notransit_mechanism(i, n)
            j = seen.get(mech, 0)
            seen[mech] = j + 1
            out.append(
                (pv2._case(prefix, "no_transit", None, noise, i, mech, None, geometry_of(j)), j)
            )
    return out


def population_cases(population: str) -> list[dict]:
    """``acceptance`` (B2 under the acceptance prefix), ``selftest`` (the first four positions of
    every group under its own prefix) or ``prefix:<text>`` (B2 under that prefix)."""
    if population == "acceptance":
        return [c for c, _ in _b2(ACCEPTANCE_PREFIX)]
    if population == "selftest":
        return [c for c, j in _b2(SELFTEST_PREFIX) if j < 4]
    if population.startswith("prefix:") and len(population) > len("prefix:"):
        return [c for c, _ in _b2(population.split(":", 1)[1])]
    raise SystemExit(f"unknown population {population}")


# --- the layout ---------------------------------------------------------------------------------


def _sector(
    start, orbit_days, gap, blocks, rho, losses, jitter
) -> tuple[np.ndarray, np.ndarray, dict]:
    """The kept time stamps of one sector from its draws (section 2.2, steps 1 to 4)."""
    n1, n2 = round(orbit_days[0] / DT), round(orbit_days[1] / DT)
    n = n1 + n2
    first = start + DT * np.arange(n1)
    nominal = np.concatenate([first, (first[-1] + gap) + DT * np.arange(n2)])

    removed = np.zeros(n, bool)
    placed = []
    for b in blocks:
        m = math.floor(b["seconds"] / CADENCE_S)
        a1, a2 = max(n1 - m - 1, 0), max(n2 - m - 1, 0)
        p = math.floor(b["place"] * (a1 + a2))
        orbit, anchor = (1, p) if p < a1 else (2, n1 + (p - a1))
        removed[anchor + 1 : anchor + m + 1] = True
        placed.append({**b, "removed": m, "orbit": orbit, "anchor": anchor})

    eligible = ~removed
    eligible[[0, n1 - 1, n1, n - 1]] = False
    eligible[:-1] &= ~removed[1:]
    eligible[1:] &= ~removed[:-1]
    lost = eligible & (losses < rho)
    run, prev = 0, -2
    for i in np.flatnonzero(lost):
        run = run + 1 if i == prev + 1 else 1
        prev = i
        if run % 4 == 0:
            lost[i] = False

    kept = ~(removed | lost)
    jit = jitter[kept]
    times = nominal[kept] + jit / 86400.0
    record = {
        "start": float(start),
        "orbit_days": [float(orbit_days[0]), float(orbit_days[1])],
        "orbit_gap_days": float(gap),
        "blocks": placed,
        "loss_rate": float(rho),
        "n_nominal": int(n),
        "n_lost_blocks": int(removed.sum()),
        "n_eligible": int(eligible.sum()),
        "n_lost_single": int(lost.sum()),
    }
    return times, jit, record


def _separation_kinds(case: dict) -> tuple[str, str]:
    g = case["extra"]
    if g["geometry"] == "G-a":
        return ("short", "short")
    return ("short", "long") if g["order"] == "short-long" else ("long", "short")


def _draw(case: dict, rng: np.random.Generator) -> dict:
    """One layout attempt: the draws in their declared order, then the time stamps."""
    first_start = FIRST_START + ONE_YEAR_DAYS * rng.uniform()
    separations = []
    for kind in _separation_kinds(case):
        separations.append(
            float(rng.uniform(*(SHORT_SEPARATION if kind == "short" else LONG_SEPARATION)))
        )
    starts = [
        first_start,
        first_start + separations[0],
        first_start + separations[0] + separations[1],
    ]
    times, jitters, records = [], [], []
    for start in starts:
        l1 = rng.uniform(*ORBIT_DAYS)
        gap = rng.uniform(*ORBIT_GAP_DAYS)
        l2 = rng.uniform(*ORBIT_DAYS)
        blocks = []
        for _ in range(int(rng.integers(0, MAX_BLOCKS + 1))):
            seconds = float(rng.uniform(*BLOCK_SECONDS))
            blocks.append({"seconds": seconds, "place": float(rng.uniform())})
        rho = rng.uniform(*LOSS_RATE)
        n = round(l1 / DT) + round(l2 / DT)
        losses = rng.uniform(size=n)
        jitter = rng.uniform(-JITTER_S, JITTER_S, size=n)
        t, jit, record = _sector(start, (l1, l2), gap, blocks, rho, losses, jitter)
        times.append(t)
        jitters.append(jit)
        records.append(record)
    draws = {"first_start": float(first_start), "separations": separations, "sectors": records}
    return {"times": times, "jitter_s": jitters, "draws": draws}


def layout_from_draws(*, first_start, separations, sectors, seed: int) -> dict:
    """A layout from given primitive draws (tests and sabotages): the per-cadence uniform numbers
    and jitters from ``default_rng(seed)``, per sector in time order."""
    rng = np.random.default_rng(seed)
    starts = [
        first_start,
        first_start + separations[0],
        first_start + separations[0] + separations[1],
    ]
    times, jitters, records = [], [], []
    for start, s in zip(starts, sectors, strict=True):
        n = round(s["orbit_days"][0] / DT) + round(s["orbit_days"][1] / DT)
        losses = rng.uniform(size=n)
        jitter = rng.uniform(-JITTER_S, JITTER_S, size=n)
        t, jit, record = _sector(
            start, s["orbit_days"], s["orbit_gap_days"], s["blocks"], s["loss_rate"], losses, jitter
        )
        times.append(t)
        jitters.append(jit)
        records.append(record)
    draws = {
        "first_start": float(first_start),
        "separations": list(separations),
        "sectors": records,
    }
    return {"times": times, "jitter_s": jitters, "draws": draws}


def draw_layout(case: dict) -> dict:
    """The case's accepted layout: attempts ``a = 0, 1, ...`` until the domain accepts one."""
    seed = int(case["seed"])
    redraws: dict[str, int] = {}
    for attempt in range(MAX_ATTEMPTS):
        lay = _draw(case, np.random.default_rng(sub_seed(seed, LAYOUT_STREAM, attempt)))
        result = domain.check_domain(lay["times"])
        if result.inside:
            return {**lay, "attempt": attempt, "redraws": redraws, "domain": result}
        key = f"layout:{result.failed}"
        redraws[key] = redraws.get(key, 0) + 1
    raise RuntimeError(f"{case['id']}: no layout inside the domain in {MAX_ATTEMPTS} attempts")


def map_absent_year(p: dict, labels: list[int]) -> None:
    """``var_absent_year`` drawn from (2018, 2019, 2020) names the curve's label at its position."""
    if "var_absent_year" in p:
        position = ABSENT_YEARS.index(p["var_absent_year"])
        p["var_absent_position"] = position
        p["var_absent_year"] = int(labels[position])


# --- the case -----------------------------------------------------------------------------------


def build_case(case: dict) -> tuple[bytes, dict]:
    """The canonical bytes of a case and its manifest entry without the hashes: population_v2's
    ``build_case`` on the case's own layout (the same operations in the same order)."""
    from refute.packs.tess import synthetic
    from refute.packs.tess.params import HoldoutParams, SnrParams
    from refute.packs.tess.types import AuxData, LightCurveData, Neighbor, SectorInfo

    gate, hidden_min = SnrParams().min_snr, HoldoutParams().min_snr
    seed = int(case["seed"])
    lay = draw_layout(case)
    redraws = dict(lay["redraws"])
    labels = [s.label for s in lay["domain"].sectors]
    cadences = [(k + 1, t) for k, t in enumerate(lay["times"])]
    time = np.concatenate([t for _, t in cadences])
    years = np.concatenate([np.full(t.size, y) for (_, t), y in zip(cadences, labels, strict=True)])
    profile: dict = {}
    for attempt in range(MAX_ATTEMPTS):
        seed_k = seed if attempt == 0 else sub_seed(seed, "redraw", attempt)
        p = draw_parameters(case, np.random.default_rng(seed_k), float(time.min()))
        map_absent_year(p, labels)
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
    star = synthetic.make_star(tic_id=pv2.TARGET_TIC)
    blend = case["mechanism"] == "blend"
    times, fluxes, errors, numbers, yrs, infos = [], [], [], [], [], []
    for (number, t), year in zip(cadences, labels, strict=True):
        model = np.ones(t.size)
        if case["class"] != "no_transit" and not blend:
            model = synthetic.signal_model(t, pv2._signal_spec(synthetic, case, p, p["depth"]))
        if case["mechanism"] != "pure_noise":
            model = model * (
                1.0 + pv2.TREND_AMPLITUDE * np.sin(2 * np.pi * t / pv2.TREND_PERIOD_DAYS)
            )
        if "var_amplitude" in p and year != p.get("var_absent_year"):
            model = model + p["var_amplitude"] * np.sin(
                2 * np.pi * (t - p["var_phase"]) / p["var_period"]
            )
        flux = model + _noise(rng_noise, t, case["noise"])
        times.append(t)
        fluxes.append(flux)
        errors.append(np.full(t.size, pv2.NOISE_PPM * 1e-6))
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
        scene = pv2._scene(synthetic, p)
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
                    tic_id=pv2.NEIGHBOR_TIC,
                    tmag=10.0 - 2.5 * math.log10(p["neighbor_ratio"]),
                    separation_arcsec=sep,
                )
            ],
            neighbor_radius_arcsec=120.0,
        )
    else:
        aux = synthetic.make_aux(lc, seed=aux_seed)
    data = synthetic.make_data(lc, infos, star, tic_id=pv2.TARGET_TIC, aux=aux)

    catalog = None
    if case["class"] != "no_transit":
        catalog = pv2._catalog(case, p, star)
    data_meta, arrays = pv2.data_to_parts(data)
    meta = {
        "serialization": pv2.SERIALIZATION,
        "generator": GENERATOR,
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
        "layout": {"attempt": lay["attempt"], **lay["draws"]},
        "domain": lay["domain"].summary(),
        "parameters": p,
        "expected_snr": profile,
        "catalog": catalog,
        "data": data_meta,
    }
    blob = pv2.serialize(meta, arrays)
    entry = {
        **meta["case"],
        "attempt_seed": str(seed_k),
        "layout_attempt": lay["attempt"],
        "redraws": redraws,
        "parameters": pv2.plain(p),
        "expected_snr": pv2.plain(profile),
        "bytes": len(blob),
    }
    return blob, entry


def case_digest(case: dict) -> tuple[str, int]:
    """The SHA-256 of a case's bytes and their length (the case built and discarded)."""
    blob, _ = build_case(case)
    return hashlib.sha256(blob).hexdigest(), len(blob)
