"""v0.5.12 step 3 (F-1): ONE fresh-process evaluation of a pre-logged intermediate diagnostic,
under one condition. Run only by ``f1_driver.py``. Exploratory and post hoc; it replaces no
record (charter, section 4: a new fixture and a new quantity, no recorded case recomputed).

    {python} -I -B docs/validation/v0.5.12/step3/f1_probe.py <condition> <out.json>

**The fixture (new):** ``scenario_data("planet_three_years", seed=2026112601)`` (the seed is
checked absent from the repository by ``f1_seed_check.py`` before the first run), with the
candidate of ``synthetic.PLANET`` (P = 3.7 d, t0 = 1326.3, T = 2.5/24 d).

**The quantity (new, absent from every record):** version 3's sinusoid test's first
prewhitening step, recomputed stage by stage with ``battery_v51``'s own helpers, the SHA-256 of
each stage's float64 bytes, in order: (1) the prepared arrays t, f, e, sector; (2) the design
``x``; (3) ``normal = (x.T * w) @ x``; (4) ``cov = inv(normal)``; (5) ``coef``; (6) ``resid``;
(7) the Lomb-Scargle power; (8) the peak (frequency, ``amplitude_snr``) with ``repr`` digits.
It also records the SHA-256 of the full ``check_sinusoid`` result's metrics (repr).

**The conditions** (one factor at a time; ``none`` is the reference):
- ``none``: a fresh process, default environment;
- ``workload``: ``pytest.main`` on ``tests/test_v0512_correction2.py`` in-process first;
- ``threads1``: ``OMP_NUM_THREADS``, ``OPENBLAS_NUM_THREADS`` and ``MKL_NUM_THREADS`` = 1, set
  before numpy is imported;
- ``import_order``: astropy's LombScargle and scipy imported before numpy and refute;
- ``misalign``: the stage inputs (t, f, e, the design) copied into buffers offset by 8 bytes from
  a 64-byte boundary (the reference copies them to a 64-byte boundary);
- ``random_state``: the global ``numpy.random`` state seeded and consumed first;
- the floating-point control state is not settable from Python without third-party code: it is
  excluded, and the record says so.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys

COND = sys.argv[1]
if COND == "threads1":
    for var in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[var] = "1"
if COND == "import_order":
    import scipy.linalg  # noqa: F401
    from astropy.timeseries import LombScargle  # noqa: F401

import numpy as np  # noqa: E402

SEED = 2026112601


def _aligned(a: np.ndarray, offset: int) -> np.ndarray:
    a = np.ascontiguousarray(a)
    buf = np.empty(a.nbytes + 128, dtype=np.uint8)
    start = (-buf.ctypes.data) % 64 + offset
    out = buf[start : start + a.nbytes].view(a.dtype).reshape(a.shape)
    out[...] = a
    return out


def _sha(*arrays) -> str:
    h = hashlib.sha256()
    for a in arrays:
        h.update(np.ascontiguousarray(a, dtype="<f8").tobytes())
    return h.hexdigest()


def main() -> int:
    if COND == "workload":
        import pytest

        pytest.main(["-q", "-p", "no:cacheprovider", "tests/test_v0512_correction2.py"])
    if COND == "random_state":
        np.random.seed(12345)
        np.random.standard_normal(1000)
    from refute.packs.tess import battery_v51 as b
    from refute.packs.tess.params import StrongerParams, V051Params
    from refute.packs.tess.synthetic import PLANET, scenario_data
    from refute.packs.tess.types import Candidate

    sp, cp = StrongerParams(), V051Params()
    data = scenario_data("planet_three_years", seed=SEED)
    raw = data.lc
    spec = {"period": PLANET.period, "t0": PLANET.t0, "duration": PLANET.duration}
    spec.update({"depth": PLANET.depth, "depth_err": PLANET.depth / 20, "snr": 20.0})
    cand = Candidate(**spec, log_likelihood=0.0, sde=20.0, n_transits=10)
    good = np.isfinite(raw.flux) & np.isfinite(raw.flux_err) & (raw.flux_err > 0)
    lc = raw.select(good)
    flux, err = lc.flux.copy(), lc.flux_err.copy()
    for s in np.unique(lc.sector):
        sel = lc.sector == s
        med = float(np.median(flux[sel]))
        flux[sel] /= med
        err[sel] /= med
    half = cand.duration / 2.0 + sp.sinusoid_mask_durations * cand.duration
    dt = np.abs(np.mod(lc.time - cand.t0 + 0.5 * cand.period, cand.period) - 0.5 * cand.period)
    keep = dt > half
    offset = 8 if COND == "misalign" else 0
    t, f, e = (_aligned(np.asarray(a, dtype=float)[keep], offset) for a in (lc.time, flux, err))
    sec = np.asarray(lc.sector)[keep]
    span = float(t.max() - t.min())
    applicable = [
        q for _, q in b.HARMONICS if cand.period * q < cp.sinusoid_harmonic_max_period_days
    ]
    tested = [1.0 / (cand.period * q) for q in applicable]
    x = _aligned(b._design(t, sec, [1.0 / q for q in tested]), offset)
    w = 1.0 / np.square(e)
    xtw = x.T * w
    normal = xtw @ x
    cov = np.linalg.inv(normal)
    coef = cov @ (xtw @ f)
    resid = f - x @ coef
    from astropy.timeseries import LombScargle

    freqs = np.arange(2.0 / span, b.EXTRA_MAX_FREQUENCY, 1.0 / (5.0 * span))
    power = LombScargle(t, resid, e).power(freqs, normalization="psd")
    peak = b._ls_peak(t, resid, e, 2.0 / span, b.EXTRA_MAX_FREQUENCY, tested, 1.0 / span)
    full = b.check_sinusoid(raw, cand, sp, cp, seed=SEED)
    stages = {
        "1_prepared": _sha(t, f, e, sec.astype(float)),
        "2_design": _sha(x),
        "3_normal": _sha(normal),
        "4_cov": _sha(cov),
        "5_coef": _sha(coef),
        "6_resid": _sha(resid),
        "7_power": _sha(power),
        "8_peak": repr(peak),
    }
    doc = {
        "condition": COND,
        "stages": stages,
        "amplitude_snr": None if peak is None else repr(peak[1]),
        "check_sinusoid_repr_sha256": hashlib.sha256(repr(full).encode()).hexdigest(),
        "threads_env": {v: os.environ.get(v) for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS")},
        "x_address_mod_64": int(x.ctypes.data % 64),
    }
    with open(sys.argv[2], "w", encoding="utf-8") as fh:
        json.dump(doc, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
