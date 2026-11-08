"""The common machinery of the v0.5.1 acceptance runs (docs/plans/v0.5.1-acceptance.md).

- **The freeze.** Every acceptance run reads acceptance seeds only on frozen code: the tree's code
  hash (``refute-code-1``: ``src/``, ``pyproject.toml``, ``uv.lock``) must equal ``FROZEN_CODE``,
  the hash of commit ``063ac1f`` (the last change to the code before the acceptance; recorded on
  #208 before the first run). A run on another hash refuses to start.
- **Seeds.** ``int(SHA-256("refute-v051-accept:<case>:<i>")[:16], 16)`` (the conventions).
- **Binomial bands** (the conventions): "at least at rate p" over N is a count at or above the
  lower 2.5 % quantile of Binomial(N, p); "at most a" a count at or below the upper 97.5 %
  quantile of Binomial(N, a).
- **Pull bands** (A0, WP2, WP3): standard deviation in [0.9, 1.1], absolute mean at most 0.1.
- **Noise models.** white; correlated (AR(1) of ``synthetic.ar1_series``, half the white level,
  tau one hour); long (AR(1), half the white level, tau 0.5 day; A0's strata); trend (a sinusoid of
  amplitude uniform in [0, 2000] ppm, period uniform in [3, 10] d, random phase, multiplicative);
  correlated_trend.
- **Runs.** Each section's units are run once, in parallel processes (the CPUs this process may
  use, minus 2), their records appended to ``.cache/v051/accept/<section>/records.jsonl`` with the
  processor time; a run resumes by skipping done units, never repeats one. **The 5 % projection
  (amendment 10):** a section first runs its first 5 % of units (in its scheduled order), projects
  its total cost from their processor time, records the projection, and continues only when the
  phase's development projection stays within the cap; past 1.5 times its own projection it stops.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
from collections.abc import Callable, Sequence
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
OUT = ROOT / ".cache" / "v051" / "accept"
FROZEN_COMMIT = "06da162c5f7d082bc191f560290411a7ee1cb266"
FROZEN_CODE = "dc73db1ce7ba9fff0fd3395c86e2348adc3a87b40d461fca42006e22a87349ce"
DEV_CAP_HOURS = 200.0
STOP_FACTOR = 1.5
PROBE_FRACTION = 0.05
NOISES_A0 = ("white", "correlated", "long", "trend", "correlated_trend")
NOISES = ("white", "correlated", "trend", "correlated_trend")
CADENCE = 2.0 / 1440.0
SECTOR_STEP = 27.4


_FREEZE_CHECKED = False


def accept_seed(case: str, i: int) -> int:
    """An acceptance seed; refused unless this process has checked the freeze first (Codex's
    review of the A0 runner design, objection 1)."""
    if not _FREEZE_CHECKED:
        raise SystemExit("an acceptance seed before the freeze check: refused")
    text = f"refute-v051-accept:{case}:{i}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def check_freeze() -> str:
    """The tree's code hash, refused unless it is the frozen one. Every runner calls it before it
    builds any unit (so before any acceptance seed exists)."""
    global _FREEZE_CHECKED
    sys.path.insert(0, str(ROOT / "src"))
    from refute.core.codehash import compute_code_hash

    code = compute_code_hash(ROOT).sha256
    if code != FROZEN_CODE:
        raise SystemExit(f"the code hash is {code}, not the frozen {FROZEN_CODE}: no run")
    _FREEZE_CHECKED = True
    return code


# --- bands ------------------------------------------------------------------------------------


def binom_lower(n: int, p: float) -> int:
    """The lower 2.5 % quantile of Binomial(n, p)."""
    from scipy.stats import binom

    return int(binom.ppf(0.025, n, p))


def binom_upper(n: int, a: float) -> int:
    """The upper 97.5 % quantile of Binomial(n, a)."""
    from scipy.stats import binom

    return int(binom.ppf(0.975, n, a))


def at_least(count: int, n: int, p: float) -> dict[str, Any]:
    bound = binom_lower(n, p)
    return {
        "count": count,
        "n": n,
        "rate": p,
        "bound": bound,
        "pass": bool(n > 0 and count >= bound),
    }


def at_most(count: int, n: int, a: float) -> dict[str, Any]:
    bound = binom_upper(n, a)
    return {
        "count": count,
        "n": n,
        "rate": a,
        "bound": bound,
        "pass": bool(n > 0 and count <= bound),
    }


def pull_band(pulls: Sequence[float], n_required: int | None = None) -> dict[str, Any]:
    """Pull standard deviation in [0.9, 1.1] and absolute mean at most 0.1; with
    ``n_required``, fewer finite pulls make the stratum NOT DECIDABLE."""
    x = np.asarray([p for p in pulls if p is not None and math.isfinite(p)], dtype=float)
    out: dict[str, Any] = {"n": int(x.size)}
    if x.size < 2 or (n_required is not None and x.size < n_required):
        out.update(result="NOT DECIDABLE", sd=None, mean=None)
        return out
    sd, mean = float(np.std(x, ddof=1)), float(np.mean(x))
    out.update(sd=sd, mean=mean, result="PASS" if 0.9 <= sd <= 1.1 and abs(mean) <= 0.1 else "FAIL")
    return out


# --- curves -----------------------------------------------------------------------------------


def sector_starts(n: int, first: float = 2000.0) -> tuple[float, ...]:
    return tuple(first + SECTOR_STEP * j for j in range(n))


def noise_curve(
    seed: int,
    noise: str,
    sectors: int,
    sigma_ppm: float = 1000.0,
    model=None,
    trend_sectors: Sequence[int] | None = None,
):
    """A light curve (``LightCurveData``) of ``sectors`` TESS-like sectors, two-minute cadence,
    the white level ``sigma_ppm`` and the noise model; ``model(t)`` (a multiplicative flux model,
    default 1) is applied before the noise. ``trend_sectors`` (1-based sector numbers): a stellar
    trend in those sectors only, whatever the noise model (row A0.4, "a trend in one sector
    only"); by default the trend is in every sector of the trend models and in none otherwise.
    Returns the curve and the trend's parameters."""
    from refute.packs.tess import synthetic as syn
    from refute.packs.tess.types import LightCurveData, btjd_to_year

    rng = np.random.default_rng([seed, 7])
    sigma = sigma_ppm * 1e-6
    ts, fs, es, ss, ys = [], [], [], [], []
    trend = None
    if trend_sectors is not None or noise in ("trend", "correlated_trend"):
        trend = {
            "amplitude": float(rng.uniform(0.0, 2000e-6)),
            "period": float(rng.uniform(3.0, 10.0)),
            "phase": float(rng.uniform(0.0, 2 * math.pi)),
        }
    with_trend = set(range(1, sectors + 1)) if trend_sectors is None else set(trend_sectors)
    for j, start in enumerate(sector_starts(sectors)):
        t = syn.sector_times(start)
        f = np.ones_like(t) if model is None else np.asarray(model(t), dtype=float)
        if trend is not None and (j + 1) in with_trend:
            f = f * (
                1.0 + trend["amplitude"] * np.sin(2 * np.pi * t / trend["period"] + trend["phase"])
            )
        f = f + rng.normal(0.0, sigma, t.size)
        if noise in ("correlated", "correlated_trend"):
            f = f + syn.ar1_series(t, sigma / 2.0, 1.0 / 24.0, rng)
        elif noise == "long":
            f = f + syn.ar1_series(t, sigma / 2.0, 0.5, rng)
        ts.append(t)
        fs.append(f)
        es.append(np.full(t.size, sigma))
        ss.append(np.full(t.size, j + 1))
        ys.append(np.full(t.size, btjd_to_year(float(t.min()))))
    lc = LightCurveData(
        np.concatenate(ts),
        np.concatenate(fs),
        np.concatenate(es),
        np.concatenate(ss),
        np.concatenate(ys),
    )
    return lc, trend


# --- running ----------------------------------------------------------------------------------


def _workers() -> int:
    sys.path.insert(0, str(ROOT / "src"))
    from refute.core.runner import default_workers

    return default_workers()


def _records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def run_section(
    section: str,
    units: Sequence[tuple[str, Any]],
    fn: Callable[[Any], dict],
    used_dev_hours: float,
    other_projected_hours: float,
) -> list[dict]:
    """Run ``units`` (``(unit_id, argument)``, in order) once, with the 5 % projection first."""
    check_freeze()
    folder = OUT / section
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "records.jsonl"
    proj_path = folder / "projection.json"
    done = {r["unit"] for r in _records(path)}
    ids = [u for u, _ in units]
    if len(set(ids)) != len(ids):
        raise SystemExit("two units share an identity")
    n_probe = max(1, int(math.ceil(PROBE_FRACTION * len(units))))

    def dispatch(batch):
        with ProcessPoolExecutor(max_workers=_workers()) as pool:
            futures = {pool.submit(_timed, fn, arg): uid for uid, arg in batch if uid not in done}
            for fut in as_completed(futures):
                uid = futures[fut]
                try:
                    rec = fut.result()
                except Exception as exc:  # noqa: BLE001 - recorded; the unit stays in its denominator
                    rec = {"status": "ERROR", "reason": repr(exc)[:400], "cpu_seconds": 0.0}
                rec["unit"] = uid
                with path.open("a", encoding="utf-8") as fh:
                    fh.write(json.dumps(rec, sort_keys=True, default=_json) + "\n")
                done.add(uid)

    if not proj_path.exists():
        dispatch(units[:n_probe])
        probe = [r for r in _records(path) if r["unit"] in set(ids[:n_probe])]
        mean = sum(float(r.get("cpu_seconds", 0.0)) for r in probe) / max(1, len(probe))
        projected = mean * len(units) / 3600.0
        total = used_dev_hours + other_projected_hours + projected
        record = {
            "section": section,
            "units": len(units),
            "probe_units": n_probe,
            "mean_cpu_seconds": mean,
            "projected_hours": projected,
            "phase_projection_hours": total,
            "cap_hours": DEV_CAP_HOURS,
            "code_sha256": FROZEN_CODE,
            "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        with open(proj_path, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps(record, indent=1) + "\n")
        if total > DEV_CAP_HOURS:
            raise SystemExit(f"STOP: the development projection {total:.1f} h passes the cap")
    projection = json.loads(proj_path.read_text(encoding="utf-8"))
    rest = [u for u in units if u[0] not in done]
    # in chunks, so that the 1.5-times stop is checked along the way
    chunk = max(_workers() * 4, 1)
    for start in range(0, len(rest), chunk):
        dispatch(rest[start : start + chunk])
        spent = sum(float(r.get("cpu_seconds", 0.0)) for r in _records(path)) / 3600.0
        if spent > STOP_FACTOR * projection["projected_hours"]:
            raise SystemExit(
                f"STOP: {section} spent {spent:.2f} h, past 1.5 times its projection "
                f"{projection['projected_hours']:.2f} h"
            )
    return [r for r in _records(path) if r["unit"] in set(ids)]


def _timed(fn, arg) -> dict:
    """One unit with its processor time, also when it fails (Codex's objection 6): a failure is
    recorded as an ERROR with the time it used, and stays in its denominator."""
    started = time.process_time()
    try:
        rec = fn(arg)
        rec.setdefault("status", "OK")
    except Exception as exc:  # noqa: BLE001 - recorded with its processor time
        rec = {"status": "ERROR", "reason": f"{type(exc).__name__}: {exc}"[:400]}
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def _json(value):
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return str(value)


def write_result(section: str, result: dict) -> Path:
    """The section's result next to the runner, written once."""
    out = HERE / f"{section}-result.json"
    with open(out, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(result, indent=1, sort_keys=True, default=_json) + "\n")
    return out


def env_threads() -> None:
    for name in (
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        os.environ.setdefault(name, "1")
