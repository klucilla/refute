"""Worker of part (f): wotan detrending, then a transitleastsquares search (MIT and MIT).

Runs only in the AppContainer, with the engines' Python (``-I``). Reads one job JSON, writes one
result JSON. No network, no catalog helper (TLS's ``catalog_info`` is never called), no
Lightkurve search or download: the light curves are read with astropy from the verified files.

Job keys: ``out`` (result path), ``light_curves`` (FITS paths) or ``synthetic`` (a dict that
asks for an injected curve, for cost and launcher checks only), ``catalog`` (period_days,
epoch_btjd, duration_hours, depth_ppm) and ``settings`` (from engines/settings.json).
"""

from __future__ import annotations

import json
import sys
import time
import traceback


def appcontainer_pipes() -> None:
    """Name multiprocessing's pipes under the LOCAL namespace an AppContainer may create."""
    import itertools
    import multiprocessing.connection as mc
    import os

    original = mc.arbitrary_address
    counter = itertools.count()

    def address(family):
        if family == "AF_PIPE":
            return f"\\\\.\\pipe\\LOCAL\\pyc-{os.getpid()}-{next(counter)}"
        return original(family)

    mc.arbitrary_address = address


appcontainer_pipes()


def load_light_curves(paths, quality_zero=True):
    import numpy as np
    from astropy.io import fits

    ts, fs, es, sectors = [], [], [], []
    for p in paths:
        with fits.open(p, memmap=False) as h:
            d = h[1].data
            sector = int(h[0].header.get("SECTOR", -1))
            t = np.asarray(d["TIME"], float)
            f = np.asarray(d["PDCSAP_FLUX"], float)
            e = np.asarray(d["PDCSAP_FLUX_ERR"], float)
            q = np.asarray(d["QUALITY"], int)
        ok = np.isfinite(t) & np.isfinite(f) & np.isfinite(e)
        if quality_zero:
            ok &= q == 0
        if ok.sum() < 10:
            continue
        med = np.nanmedian(f[ok])
        ts.append(t[ok])
        fs.append(f[ok] / med)
        es.append(e[ok] / med)
        sectors.append(sector)
    if not ts:
        return None
    t = np.concatenate(ts)
    order = np.argsort(t)
    return t[order], np.concatenate(fs)[order], np.concatenate(es)[order], sectors


def synthetic_curve(spec):
    import numpy as np

    rng = np.random.default_rng(int(spec.get("seed", 1)))
    cadence = 2.0 / 1440.0
    t = []
    start = 0.0
    for _ in range(int(spec["sectors"])):
        t.append(np.arange(start, start + 27.0, cadence))
        start += float(spec.get("sector_gap_days", 110.0))
    t = np.concatenate(t) + 1500.0
    f = 1.0 + rng.normal(0.0, float(spec["noise"]), t.size)
    phase = ((t - spec["epoch"] + 0.5 * spec["period"]) % spec["period"]) - 0.5 * spec["period"]
    f[np.abs(phase) < 0.5 * spec["duration_hours"] / 24.0] -= spec["depth_ppm"] * 1e-6
    e = np.full_like(f, float(spec["noise"]))
    return t, f, e, list(range(int(spec["sectors"])))


def bin_curve(t, f, e, width_days):
    import numpy as np

    if not width_days:
        return t, f, e
    k = np.floor((t - t[0]) / width_days).astype(np.int64)
    uniq, inv, cnt = np.unique(k, return_inverse=True, return_counts=True)
    tb = np.bincount(inv, t) / cnt
    fb = np.bincount(inv, f) / cnt
    eb = np.sqrt(np.bincount(inv, e**2)) / cnt
    return tb, fb, eb


def main() -> int:
    job = json.loads(open(sys.argv[1], encoding="utf-8").read())
    s = job["settings"]
    cat = job["catalog"]
    res = {"engine": "wotan+transitleastsquares", "mode": "exploratory", "metrics": {}}
    t0 = time.process_time()
    try:
        import numpy as np
        import transitleastsquares
        import wotan
        from transitleastsquares import transitleastsquares as tls_model
        from wotan import flatten

        res["versions"] = {
            "wotan": getattr(wotan, "__version__", "2.1 (pinned)"),
            "transitleastsquares": getattr(transitleastsquares, "tls_constants", None)
            and transitleastsquares.tls_constants.TLS_VERSION,
            "numpy": np.__version__,
        }
        if "synthetic" in job:
            lc = synthetic_curve(job["synthetic"])
        else:
            lc = load_light_curves(job["light_curves"])
        if lc is None:
            res["status"] = "unavailable"
            res["reason"] = "no usable cadence (quality 0, finite flux)"
            return finish(job, res, t0)
        t, f, e, sectors = lc
        res["coverage"] = {"cadences": int(t.size), "sectors": sectors}
        window = max(
            s["wotan_window_min_days"], s["wotan_window_durations"] * cat["duration_hours"] / 24.0
        )
        flat = flatten(
            t,
            f,
            method="biweight",
            window_length=window,
            edge_cutoff=0.0,
            break_tolerance=s["wotan_break_tolerance_days"],
        )
        ok = np.isfinite(flat)
        t, f, e = t[ok], flat[ok], e[ok]
        tb, fb, eb = bin_curve(t, f, e, s["tls_bin_minutes"] / 1440.0)
        res["coverage"]["points_searched"] = int(tb.size)
        res["coverage"]["span_days"] = float(tb[-1] - tb[0])
        model = tls_model(tb, fb, eb)
        r = model.power(
            period_min=s["tls_period_min_days"],
            period_max=s["tls_period_max_days"],
            oversampling_factor=s["tls_oversampling_factor"],
            use_threads=int(job.get("threads", 1)),
            show_progress_bar=False,
        )
        sde = float(r.SDE) if np.isfinite(r.SDE) else None
        res["metrics"] = {
            "window_length_days": window,
            "periods_tested": int(len(r.periods)),
            "period_days": float(r.period),
            "t0_btjd": float(r.T0),
            "duration_hours": float(r.duration) * 24.0,
            "depth_fraction": float(1.0 - r.depth) if np.isfinite(r.depth) else None,
            "sde": sde,
            "snr": float(r.snr) if np.isfinite(r.snr) else None,
            "transit_count": int(r.transit_count),
            "distinct_transit_count": int(r.distinct_transit_count),
            "odd_even_mismatch_sigma": float(r.odd_even_mismatch)
            if np.isfinite(r.odd_even_mismatch)
            else None,
        }
        res["status"] = "ok"
    except Exception as exc:  # recorded, never hidden
        res["status"] = "failed"
        res["error"] = f"{type(exc).__name__}: {exc}"
        res["traceback"] = traceback.format_exc()[-4000:]
    return finish(job, res, t0)


def finish(job, res, t0) -> int:
    res["worker_process_cpu_seconds"] = time.process_time() - t0
    with open(job["out"], "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
