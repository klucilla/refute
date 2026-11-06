"""v0.5.1 WP3 (c) development check: does ``period_alias`` prefer a box on pure sinusoids?

Development data only. Two synthetic sectors (``synthetic.sector_times`` at 2000.0 and 2027.4
BTJD), white noise of 300 or 1000 ppm, a pure sinusoid at the candidate's period with peak to
trough equal to the depth (the v0.5 sensitivity alternative), 40 realizations per setting (seed 1),
periods 1.5, 3.3 and 7.0 d; the frozen ``battery.check_period_alias`` with the v0.4 claim's plan,
with the detrending's transit mask as coded and with it replaced by an empty mask. Counts the
realizations that do **not** FAIL (the box preferred). Result of 2026-11-06: 0 of 240 in both
variants ("the hypothesized failure was not reproduced in these tested settings").

Usage: .venv/Scripts/python.exe docs/validation/v0.5.1/feasibility/alias_synthetic_check.py
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def main() -> dict:
    from refute.packs.tess import battery
    from refute.packs.tess import synthetic as syn
    from refute.packs.tess.calib05.plans import pair
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.types import Candidate, LightCurveData

    p04, _ = pair(v04_test_plan(ROOT))
    t = np.concatenate([syn.sector_times(2000.0), syn.sector_times(2027.4)])
    sector = np.where(t < 2027, 1, 2)
    year = np.full(t.size, 2020)
    rows = []
    original = battery.transit_mask
    for period, duration in ((1.5, 0.08), (3.3, 0.12), (7.0, 0.16)):
        for sigma in (300e-6, 1000e-6):
            depth = 2000e-6 if sigma > 500e-6 else 800e-6
            cand = Candidate(
                period=period,
                t0=2001.1,
                duration=duration,
                depth=depth,
                depth_err=depth / 10,
                snr=10.0,
                sde=10.0,
                log_likelihood=0.0,
                n_transits=10,
            )
            rng = np.random.default_rng(1)
            counts = {"mask": 0, "no_mask": 0}
            gains = []
            for _ in range(40):
                phase = rng.uniform(0.0, 2.0 * math.pi)
                flux = 1.0 + depth / 2.0 * np.cos(2 * math.pi * (t - cand.t0) / period + phase)
                flux = flux + sigma * rng.standard_normal(t.size)
                lc = LightCurveData(t, flux, np.full(t.size, sigma), sector, year)
                r = battery.check_period_alias(lc, cand, p04)
                gains.append(float(r.metrics.get("box_delta_bic")))
                counts["mask"] += r.status.value != "FAIL"
                battery.transit_mask = lambda *a, **k: np.zeros(t.size, bool)
                try:
                    r2 = battery.check_period_alias(lc, cand, p04)
                finally:
                    battery.transit_mask = original
                counts["no_mask"] += r2.status.value != "FAIL"
            rows.append(
                {
                    "period_days": period,
                    "sigma_ppm": sigma * 1e6,
                    "realizations": 40,
                    "not_fail_with_mask": counts["mask"],
                    "not_fail_without_mask": counts["no_mask"],
                    "max_box_delta_bic": max(gains),
                }
            )
    return {"label": "development check (v0.5.1 WP3 (c)); it decides nothing", "rows": rows}


if __name__ == "__main__":
    doc = main()
    (HERE / "alias-synthetic-check.json").write_text(
        json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(doc, indent=1, sort_keys=True))
