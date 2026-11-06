"""v0.5.1 A0 development check: how many events A0's pseudo-event windows can measure.

Development data only: 200 planets of the frozen C1 generator (family P, seeds
``refute-v051-dev:a0avail:<i>``), detrended by the frozen v0.4 plan, the truth's ephemeris as the
candidate, the event parameters of the v0.4 claim. For each planet: the kept pseudo-windows per
sector and stratum, the effective count of the ``full`` stratum, the fraction of the planet's
events A0 measures (``n_eff >= 10`` in its sector and stratum), and whether at least 3 events are
measured (the per-event tests' domain) and at least 2 in each of the odd and even groups. Reported
by period band. It decides nothing.

Usage: .venv/Scripts/python.exe docs/validation/v0.5.1/feasibility/a0_window_availability.py
"""

from __future__ import annotations

import hashlib
import json
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


VARIANT = "as_adopted"


def one(i: int, variant: str = "as_adopted") -> dict | None:
    from refute.packs.tess import a0
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.calib05.plans import pair
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.events import per_event_depths, transit_mask
    from refute.packs.tess.rednoise import event_noise
    from refute.packs.tess.types import Candidate

    s = int(hashlib.sha256(f"refute-v051-dev:a0avail:{i}".encode()).hexdigest()[:16], 16)
    try:
        data, truth = c1.generate("P", s)
    except c1.GenerationFailedError:
        return None
    p04, _ = pair(v04_test_plan(ROOT))
    cand = Candidate(period=truth["period_days"], t0=truth["t0_btjd"],
                     duration=truth["duration_days"], depth=truth["depth"], depth_err=1e-5,
                     snr=20.0, log_likelihood=0.0, sde=10.0, n_transits=10)  # fmt: skip
    mask = transit_mask(data.lc.time, cand.period, cand.t0, cand.duration)
    flat = detrend(data.lc, p04.detrend, mask=mask)
    cadence = p04.data.exptime_seconds / 86400.0
    ev = p04.gauntlet.events
    noise = event_noise(flat, None, cand.period, cand.t0, cand.duration, p04)
    events = per_event_depths(
        flat, cand.period, cand.t0, cand.duration, cadence, ev, 0.0, None, noise
    )
    if variant == "no_phase_half_exclusion" and not getattr(a0, "_dev_patched", False):
        # option (a) of the finding (development only): the phase-0.5 exclusion dropped,
        # patched once per worker process
        original = a0.pseudo_windows

        def patched(*args, **kwargs):
            kwargs["exclude_phase_half"] = False
            return original(*args, **kwargs)

        a0.pseudo_windows = patched
        a0._dev_patched = True
    out, windows, details = a0.empirical_events(flat, cand, events, ev, cadence)
    odd = int(np.sum(out.epochs % 2 == 1))
    even = int(np.sum(out.epochs % 2 == 0))
    full_neff = [d["n_eff"] for k, d in details.items() if k.endswith(":full")]
    return {
        "period": cand.period,
        "duration": cand.duration,
        "events": len(events),
        "measured": len(out),
        "odd": odd,
        "even": even,
        "windows": len(windows),
        "full_neff_min": min(full_neff) if full_neff else 0.0,
    }


def main() -> dict:
    import sys

    from refute.core.runner import default_workers

    variant = sys.argv[1] if len(sys.argv) > 1 else "as_adopted"
    with ProcessPoolExecutor(max_workers=default_workers()) as pool:
        rows = [r for r in pool.map(one, range(200), [variant] * 200) if r is not None]
    bands = {}
    for lo, hi in ((0.7, 1.5), (1.5, 3.0), (3.0, 6.0), (6.0, 12.0)):
        g = [r for r in rows if lo <= r["period"] < hi]
        if not g:
            continue
        bands[f"{lo}-{hi} d"] = {
            "planets": len(g),
            "events_measured_fraction": sum(r["measured"] for r in g)
            / max(1, sum(r["events"] for r in g)),
            "domain_3_events": sum(r["measured"] >= 3 for r in g) / len(g),
            "two_per_parity": sum(r["odd"] >= 2 and r["even"] >= 2 for r in g) / len(g),
            "median_windows": float(np.median([r["windows"] for r in g])),
        }
    return {
        "label": "development check (v0.5.1 A0 window availability); it decides nothing",
        "variant": variant,
        "planets": len(rows),
        "all": {
            "domain_3_events": sum(r["measured"] >= 3 for r in rows) / len(rows),
            "two_per_parity": sum(r["odd"] >= 2 and r["even"] >= 2 for r in rows) / len(rows),
            "events_measured_fraction": sum(r["measured"] for r in rows)
            / sum(r["events"] for r in rows),
        },
        "by_period": bands,
    }


if __name__ == "__main__":
    doc = main()
    name = "a0-window-availability" + (
        "" if doc["variant"] == "as_adopted" else "-" + doc["variant"]
    )
    (HERE / f"{name}.json").write_text(
        json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(doc, indent=1, sort_keys=True))
