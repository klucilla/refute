"""Worker of part (f): exoVetter 0.0.16 (BSD-3-Clause) on the catalog ephemeris.

Runs only in the AppContainer, with the engines' Python (``-I``). Reads one job JSON, writes one
result JSON. The light curves and pixel files are read from the verified local files; no
Lightkurve search or download is called. LPP is not run: its map is a remote file that was not
staged (Codex's blocking item 3), so it is recorded as unavailable.

The flux given to the vetters is the job's light curves (SPOC PDCSAP, quality 0, each sector
divided by its median) detrended by wotan with the same settings as the TLS worker.
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
import traceback

# -I leaves the script's folder off the path; the workers' folder is added explicitly.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import worker_tls as common  # noqa: E402


def to_float(x):
    try:
        v = float(x)
    except Exception:
        return None
    return v if math.isfinite(v) else None


def main() -> int:
    job = json.loads(open(sys.argv[1], encoding="utf-8").read())
    s = job["settings"]
    cat = job["catalog"]
    res = {"engine": "exovetter", "mode": "exploratory", "metrics": {}, "vetters": {}}
    t0 = time.process_time()
    try:
        import astropy.units as u
        import exovetter
        import lightkurve as lk
        import numpy as np
        from astropy.time import Time
        from exovetter import const, vetters
        from exovetter.tce import Tce
        from wotan import flatten

        res["versions"] = {"exovetter": exovetter.__version__, "lightkurve": lk.__version__}
        if "synthetic" in job:
            lc = common.synthetic_curve(job["synthetic"])
        else:
            lc = common.load_light_curves(job["light_curves"])
        if lc is None:
            res["status"] = "unavailable"
            res["reason"] = "no usable cadence"
            return common.finish(job, res, t0)
        t, f, e, sectors = lc
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
        res["coverage"] = {"cadences": int(ok.sum()), "sectors": sectors}
        curve = lk.LightCurve(
            time=Time(t[ok], format="btjd", scale="tdb"), flux=flat[ok], flux_err=e[ok]
        )
        tce = Tce(
            period=cat["period_days"] * u.day,
            epoch=cat["epoch_btjd"] * u.day,
            epoch_offset=const.btjd,
            duration=cat["duration_hours"] * u.hour,
            depth=cat["depth_ppm"] * const.ppm,
            snr=10.0,
        )

        def vet(name, fn):
            try:
                out = fn()
                res["vetters"][name] = {"status": "ok", "native": out}
            except Exception as exc:  # recorded per vetter (G5)
                res["vetters"][name] = {
                    "status": "failed",
                    "error": f"{type(exc).__name__}: {exc}"[:600],
                }

        def modshift():
            m = vetters.ModShift().run(tce, curve, plot=False)
            return {k: to_float(v) for k, v in m.items() if not isinstance(v, (list, dict))}

        def oddeven():
            m = vetters.OddEven().run(tce, curve, plot=False)
            odd = [to_float(x) for x in np.atleast_1d(m["odd_depth"])]
            even = [to_float(x) for x in np.atleast_1d(m["even_depth"])]
            return {"oe_sigma": to_float(m["oe_sigma"]), "odd_depth": odd, "even_depth": even}

        def coverage():
            m = vetters.TransitPhaseCoverage().run(tce, curve, plot=False)
            return {"transit_phase_coverage": to_float(m["transit_phase_coverage"])}

        def sweet():
            m = vetters.Sweet().run(tce, curve, plot=False)
            amp = np.asarray(m["amp"], float)
            return {
                "msg": m["msg"],
                "amp_half_period": [to_float(x) for x in amp[0]],
                "amp_period": [to_float(x) for x in amp[1]],
                "amp_twice_period": [to_float(x) for x in amp[2]],
            }

        vet("ModShift", modshift)
        vet("OddEven", oddeven)
        vet("TransitPhaseCoverage", coverage)
        vet("Sweet", sweet)
        res["vetters"]["Lpp"] = {
            "status": "unavailable",
            "reason": "its map file is remote and was not staged as a verified local input",
        }
        cents = []
        for path in job.get("pixel_files", []):
            rec = {"file": path.replace("\\", "/").rsplit("/", 1)[-1]}
            try:
                tpf = lk.read(path, quality_bitmask="hardest")
                m = vetters.Centroid().run(tce, tpf, plot=False)
                rec.update(
                    {
                        "status": "ok",
                        "offset_pix": to_float(m["offset"]),
                        "significance": to_float(m["significance"]),
                    }
                )
            except Exception as exc:
                rec.update({"status": "failed", "error": f"{type(exc).__name__}: {exc}"[:600]})
            cents.append(rec)
        res["vetters"]["Centroid"] = {"status": "per_sector", "sectors": cents}
        res["status"] = "ok"
    except Exception as exc:  # recorded, never hidden
        res["status"] = "failed"
        res["error"] = f"{type(exc).__name__}: {exc}"
        res["traceback"] = traceback.format_exc()[-4000:]
    return common.finish(job, res, t0)


if __name__ == "__main__":
    raise SystemExit(main())
