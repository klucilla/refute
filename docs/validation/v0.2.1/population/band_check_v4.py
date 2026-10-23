"""The independent band check of population_v4 (acceptance criterion 5).

Acceptance record: ``population-v4-acceptance.md`` next to this file, section 3, criterion 5.
This file imports only the standard library and NumPy: not ``refute``, not ``population_v2``,
not ``population_v4``. Everything it needs is written here from the protocol's text
(docs/validation/v0.2.1/population-study.md, section 3, the expected SNR and the bands;
section 4, the noise models, the trend, the variability, the shapes and the blend's scene) and
from ``population_v2``'s declared call sequence (``CALL_SEQUENCE``: the noise stream).

For a serialized case (``refute-population-serialization/1``) it checks:

- with an injected transit: the per-unit-depth expected SNRs recorded in ``expected_snr``
  (global, each label's train and hidden ones, and ``min_unit_ratio``) recomputed from the
  stored time stamps, labels and parameters, within a relative tolerance of 1e-9; ``r_actual``
  and the band; for a blend, the crowding recomputed from the recorded scene;
- except for blends: the flux rebuilt from the parameters, the model and the noise stream,
  equal to the stored flux within 1e-12; for a curve without a transit, no transit parameter;
- for a ``variability_some_years`` planet: the variability-free year one of the curve's labels.

``python band_check_v4.py <case files...>`` prints one JSON report per file.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

MAGIC = b"refute-population-serialization/1\n"
# Section 3: the thresholds; section 4: the noise, the trend.
GATE_SNR = 7.1
HIDDEN_SNR = 5.0
WHITE = 600e-6
AR_SIGMA = 600e-6
AR_TAU_DAYS = 1.0 / 24.0
TREND_AMPLITUDE = 0.002
TREND_PERIOD_DAYS = 6.0
# Section 3: the bands of the minimum ratio r.
BAND_LIMITS = {"below": (0.5, 1.0), "near": (1.0, 1.5), "measurable": (1.5, math.inf)}
# Section 4.4 (the blend's scene, as make_blend): 11 x 11 pixels, the target at the centre,
# a Gaussian PSF of 0.9 pixel, the aperture the pixels holding at least 2% of the target.
SCENE_SHAPE = (11, 11)
TARGET_XY = (5.0, 5.0)
PSF_SIGMA = 0.9
APERTURE_MIN_FRACTION = 0.02
SNR_RTOL = 1e-9
FLUX_ATOL = 1e-12
TRANSIT_KEYS = ("period", "t0", "depth", "duration")


def read(blob: bytes) -> tuple[dict, dict[str, np.ndarray]]:
    """The metadata and the arrays of a serialized case."""
    if not blob.startswith(MAGIC):
        raise ValueError("not a refute-population-serialization/1 case")
    pos = len(MAGIC)
    size = int.from_bytes(blob[pos : pos + 8], "little")
    pos += 8
    meta = json.loads(blob[pos : pos + size].decode("utf-8"))
    pos += size
    arrays = {}
    for name, dtype, shape in meta["arrays"]:
        dt = np.dtype(dtype)
        count = 1
        for s in shape:
            count *= s
        arrays[name] = np.frombuffer(blob, dtype=dt, count=count, offset=pos).reshape(shape)
        pos += count * dt.itemsize
    if pos != len(blob):
        raise ValueError("trailing bytes")
    return meta, arrays


def sub_seed(seed: int, *parts) -> int:
    text = "|".join([str(seed), *(str(p) for p in parts)])
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:8], "big")


def trapezoid(t, period, t0, depth, duration, ingress_fraction, phase=0.0):
    """The deficit of a trapezoid centred on ``t0 + (n + phase) period``."""
    offset = np.mod(t - t0 - phase * period + 0.5 * period, period) - 0.5 * period
    ramp = max(ingress_fraction * duration, 1e-6)
    return depth * np.clip((duration / 2.0 - np.abs(offset)) / ramp, 0.0, 1.0)


def _pixel_fractions(xy):
    scale = math.sqrt(2.0) * PSF_SIGMA

    def axis(n, centre):
        cdf = [0.5 * (1.0 + math.erf((b - 0.5 - centre) / scale)) for b in range(n + 1)]
        return np.diff(np.array(cdf))

    return np.outer(axis(SCENE_SHAPE[0], xy[1]), axis(SCENE_SHAPE[1], xy[0]))


def crowding(p: dict) -> float:
    d, a = p["neighbor_distance_px"], p["neighbor_angle"]
    neighbor = (TARGET_XY[0] + d * math.cos(a), TARGET_XY[1] + d * math.sin(a))
    target = _pixel_fractions(TARGET_XY)
    aperture = target >= APERTURE_MIN_FRACTION
    own = float(target[aperture].sum())
    other = p["neighbor_ratio"] * float(_pixel_fractions(neighbor)[aperture].sum())
    return own / (own + other)


def _unit_deficit(case: dict, p: dict, t, dilution: float):
    unit = trapezoid(t, p["period"], p["t0"], 1.0, p["duration"], p["ingress_fraction"])
    if case["mechanism"] == "eb_odd_even":
        odd = np.round((t - p["t0"]) / p["period"]).astype(int) % 2 != 0
        unit = np.where(odd, unit * p["odd_factor"], unit)
    return unit * dilution


def _snr(t, deficit, epoch, inside, select, noise: str) -> float:
    """Section 3: the in-transit mean deficit over the square root of its variance."""
    mask = inside & select
    if not mask.any():
        return 0.0
    variance = 0.0
    for e in np.unique(epoch[mask]):
        te = t[mask & (epoch == e)]
        variance += WHITE**2 * te.size
        if noise == "correlated":
            variance += AR_SIGMA**2 * float(
                np.exp(-np.abs(te[:, None] - te[None, :]) / AR_TAU_DAYS).sum()
            )
    return float(deficit[mask].sum() / math.sqrt(variance))


def _close(a: float, b: float) -> bool:
    return abs(a - b) <= SNR_RTOL * max(abs(a), abs(b), 1e-300)


def _snr_problems(meta, case, p, t, labels) -> tuple[list[str], int]:
    problems, checked = [], 0
    dilution = 1.0
    if case["mechanism"] == "blend":
        c = crowding(p)
        dilution = (1.0 - c) / c
        if not _close(dilution, p["dilution"]):
            problems.append(f"dilution {p['dilution']!r} but the scene gives {dilution!r}")
    epoch = np.round((t - p["t0"]) / p["period"])
    inside = np.abs(t - (p["t0"] + epoch * p["period"])) <= p["duration"] / 2.0
    deficit = _unit_deficit(case, p, t, dilution)
    rec = meta["expected_snr"]
    mine = {"global": _snr(t, deficit, epoch, inside, np.ones(t.size, bool), case["noise"])}
    ratios = [mine["global"] / GATE_SNR]
    for y in sorted(set(labels.tolist())):
        train = _snr(t, deficit, epoch, inside, labels != y, case["noise"])
        hidden = _snr(t, deficit, epoch, inside, labels == y, case["noise"])
        mine[f"train/{y}"], mine[f"hidden/{y}"] = train, hidden
        ratios += [train / GATE_SNR, hidden / HIDDEN_SNR]
    recorded = {"global": rec["global"]}
    for y in sorted(set(labels.tolist())):
        recorded[f"train/{y}"] = rec["train"].get(str(y))
        recorded[f"hidden/{y}"] = rec["hidden"].get(str(y))
    if set(rec["train"]) != {str(y) for y in set(labels.tolist())}:
        problems.append(f"expected_snr years {sorted(rec['train'])} are not the labels")
    for key, value in mine.items():
        checked += 1
        if recorded.get(key) is None or not _close(value, recorded[key]):
            problems.append(
                f"expected SNR {key}: recorded {recorded.get(key)!r}, recomputed {value!r}"
            )
    ratio = min(ratios)
    checked += 1
    if not _close(ratio, rec["min_unit_ratio"]):
        problems.append(f"min_unit_ratio {rec['min_unit_ratio']!r}, recomputed {ratio!r}")
    r = p["depth"] * ratio
    if not _close(r, p["r_actual"]):
        problems.append(f"r_actual {p['r_actual']!r}, recomputed {r!r}")
    lo, hi = BAND_LIMITS[case["band"]]
    if not lo <= r < hi:
        problems.append(f"r {r!r} outside the band {case['band']}")
    return problems, checked


def _model(case, p, t, label):
    model = np.ones(t.size)
    if case["class"] != "no_transit":
        deficit = trapezoid(
            t, p["period"], p["t0"], p["depth"], p["duration"], p["ingress_fraction"]
        )
        if case["mechanism"] == "eb_odd_even":
            odd = np.round((t - p["t0"]) / p["period"]).astype(int) % 2 != 0
            deficit = np.where(odd, deficit * p["odd_factor"], deficit)
        if case["mechanism"] == "eb_secondary":
            secondary = p["depth"] * p["secondary_fraction"]
            if secondary > 0:
                deficit = deficit + trapezoid(
                    t,
                    p["period"],
                    p["t0"],
                    secondary,
                    p["duration"],
                    p["ingress_fraction"],
                    phase=0.5,
                )
        model = 1.0 - deficit
    if case["mechanism"] != "pure_noise":
        model = model * (1.0 + TREND_AMPLITUDE * np.sin(2 * np.pi * t / TREND_PERIOD_DAYS))
    if "var_amplitude" in p and label != p.get("var_absent_year"):
        model = model + p["var_amplitude"] * np.sin(
            2 * np.pi * (t - p["var_phase"]) / p["var_period"]
        )
    return model


def _noise(rng, t, noise: str):
    out = rng.normal(0.0, WHITE, t.size)
    if noise == "correlated":
        x = np.empty(t.size)
        x[0] = rng.normal(0.0, AR_SIGMA)
        innov = rng.normal(0.0, 1.0, t.size)
        phi = np.exp(-np.diff(t) / AR_TAU_DAYS)
        scale = AR_SIGMA * np.sqrt(1.0 - phi**2)
        for i in range(1, t.size):
            x[i] = phi[i - 1] * x[i - 1] + scale[i - 1] * innov[i]
        out = out + x
    return out


def check(blob: bytes) -> dict:
    meta, arrays = read(blob)
    case, p = meta["case"], meta["parameters"]
    t, flux = arrays["lc/time"], arrays["lc/flux"]
    sector, labels = arrays["lc/sector"], arrays["lc/year"]
    problems: list[str] = []
    snr_checked = flux_checked = 0
    distinct = sorted(set(labels.tolist()))
    if case["mechanism"] == "variability_some_years":
        if p.get("var_absent_year") not in distinct:
            problems.append(f"var_absent_year {p.get('var_absent_year')} is not a label {distinct}")
        elif sum(y != p["var_absent_year"] for y in distinct) != 2:
            problems.append("not exactly two labels with variability")
    if case["class"] == "no_transit":
        present = [k for k in TRANSIT_KEYS if k in p]
        if present:
            problems.append(f"a curve without a transit has transit parameters {present}")
    else:
        found, snr_checked = _snr_problems(meta, case, p, t, labels)
        problems += found
    if case["mechanism"] != "blend":
        rng = np.random.default_rng(sub_seed(int(meta["attempt_seed"]), "noise"))
        for number in sorted(set(sector.tolist())):
            sel = sector == number
            ts = t[sel]
            label = int(labels[sel][0])
            rebuilt = _model(case, p, ts, label) + _noise(rng, ts, case["noise"])
            worst = float(np.max(np.abs(rebuilt - flux[sel]))) if ts.size else 0.0
            flux_checked += int(ts.size)
            if not worst <= FLUX_ATOL:
                problems.append(f"sector {number}: the rebuilt flux differs by {worst:.3e}")
    if snr_checked == 0 and flux_checked == 0:
        problems.append("nothing checked")
    return {
        "id": case["id"],
        "problems": problems,
        "snr_checked": snr_checked,
        "flux_checked": flux_checked,
    }


def main(argv: list[str]) -> int:
    bad = 0
    for name in argv:
        report = check(Path(name).read_bytes())
        print(json.dumps(report, sort_keys=True))
        bad += bool(report["problems"])
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
