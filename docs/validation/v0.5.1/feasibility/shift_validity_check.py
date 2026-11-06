"""v0.5.1 A0 development check: how many phase-shifted ephemerides are valid under each rule?

Development data only: 60 planets of the frozen C1 generator (family P, seeds
``refute-v051-dev:shiftcheck:<i>``), the event coverage of ``events.per_event_depths`` with the
v0.4 claim's event parameters at the true ephemeris and at shifted phases. Three rules:

- ``r1_exact``: revision 1's text: 20 seeded shifts in [0.15, 0.35] and [0.65, 0.85] (seed 0), a
  shift valid when each group (odd, even) has exactly the real ephemeris's number of measured
  events;
- ``r1_ten_percent``: the same shifts, each group within max(1, 10 %) of the real count;
- ``r2_grid_half``: a grid of 40 shifts (20 evenly in each range), at least 1.5 durations (in
  phase) from 0 and 0.5, overlap between shifts allowed, a shift valid when each group has at
  least max(1, half) the real count.

For each rule: the median number of valid shifts and the fraction of curves with fewer than 10.
It decides nothing; it is the evidence behind revision 2 of A0 (acceptance documents).

Usage: .venv/Scripts/python.exe docs/validation/v0.5.1/feasibility/shift_validity_check.py
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def main() -> dict:
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.calib05.plans import pair
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.events import per_event_depths

    p04, _ = pair(v04_test_plan(ROOT))
    ev = p04.gauntlet.events
    cadence = 2.0 / 1440.0
    rng = np.random.default_rng(0)
    grid = np.concatenate([np.linspace(0.15, 0.35, 20), np.linspace(0.65, 0.85, 20)])
    rows = {"r1_exact": [], "r1_ten_percent": [], "r2_grid_half": []}
    for i in range(60):
        text = f"refute-v051-dev:shiftcheck:{i}"
        seed = int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)
        data, truth = c1.generate("P", seed)
        period, t0, dur = truth["period_days"], truth["t0_btjd"], truth["duration_days"]

        def counts(phase, period=period, t0=t0, dur=dur, data=data):
            e = per_event_depths(data.lc, period, t0, dur, cadence, ev, phase=phase)
            return int(np.sum(e.epochs % 2 == 1)), int(np.sum(e.epochs % 2 == 0))

        ro, re_ = counts(0.0)
        seeded = np.concatenate([rng.uniform(0.15, 0.35, 10), rng.uniform(0.65, 0.85, 10)])
        if min(ro, re_) < 1:
            continue
        shifted = [counts(f) for f in seeded]
        rows["r1_exact"].append(sum(c == (ro, re_) for c in shifted))

        def tol(n):
            return max(1, round(0.1 * n))

        rows["r1_ten_percent"].append(
            sum(abs(a - ro) <= tol(ro) and abs(b - re_) <= tol(re_) for a, b in shifted)
        )
        sep = dur / period
        phis = [f for f in grid if min(abs(f - 0.5), f, 1 - f) >= 1.5 * sep]
        rows["r2_grid_half"].append(
            sum(
                a >= max(1, 0.5 * ro) and b >= max(1, 0.5 * re_)
                for a, b in (counts(f) for f in phis)
            )
        )
    out = {"label": "development check (v0.5.1 A0); it decides nothing", "curves": {}}
    for name, valid in rows.items():
        v = np.asarray(valid)
        out["curves"][name] = {
            "n": int(v.size),
            "median_valid": float(np.median(v)),
            "fraction_below_10": float(np.mean(v < 10)),
        }
    return out


if __name__ == "__main__":
    doc = main()
    (HERE / "shift-validity-check.json").write_text(
        json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(doc, indent=1, sort_keys=True))
