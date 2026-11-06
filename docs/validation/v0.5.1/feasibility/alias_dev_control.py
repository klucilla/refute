"""v0.5.1 WP3 (c) development diagnosis of #204 on the development control TIC-101395259.

Development data only: the control's light curves fetched by ``fetch_dev_control.py`` (equal to
the v0.5 dossier's SHA-256), the candidate of the v0.5 dossier (period 7.574684 d, t0 1523.941968
BTJD, duration 0.095833 d, depth 5554.02 ppm), the v0.5 C3 claim's test plan. The v0.5
sensitivity simulation of ``period_alias`` (``power.period_alias_blocks``: 50 seeded sinusoids at
the candidate's period, peak to trough equal to the depth, on the candidate's times and errors)
is repeated with the same seed under variants, to find which step makes the test prefer a box on
a pure sinusoid (7 of 50 in v0.5):

- ``as_is``: the frozen test;
- ``no_detrend``: the detrending of the test replaced by the identity (the simulated flux is
  already flat around the sinusoid);
- ``harmonics_4``: four harmonics in the Fourier model instead of two;
- ``window_1_period``: the test's detrending window of one period instead of three.

For each: the failures out of 50 (a FAIL means the sinusoid was recognized) and the box gains.
It decides nothing; it informs the acceptance section of WP3 (c).

Usage: .venv/Scripts/python.exe docs/validation/v0.5.1/feasibility/alias_dev_control.py
"""

from __future__ import annotations

import json
import math
from dataclasses import replace
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
CACHE = ROOT / ".cache/v051/dev"


def main() -> dict:
    import yaml

    from refute.packs.tess import battery
    from refute.packs.tess.adapter import TessAdapter
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.power import candidate_seed
    from refute.packs.tess.types import Candidate

    claim = yaml.safe_load((ROOT / "calibration/v0.5/claim.yaml").read_text(encoding="utf-8"))
    raw = claim["test_plan"]
    raw["data"]["target_pixel_files"] = False
    plan = TessTestPlan.model_validate(raw)
    data = TessAdapter().load({"tic_id": 101395259}, raw, CACHE)
    lc = data.lc
    cand = Candidate(period=7.574683911754836, t0=1523.9419679015348, duration=0.09583333333333333,
                     depth=0.005554021405985093, depth_err=3.39e-05, snr=163.8, sde=21.3,
                     log_likelihood=0.0, n_transits=16)  # fmt: skip
    seed = candidate_seed("period_alias", cand)
    errors = np.where(
        np.isfinite(lc.flux_err) & (lc.flux_err > 0), lc.flux_err, np.nanmedian(lc.flux_err)
    )
    original_detrend = battery.detrend
    variants = {}
    for name in ("as_is", "no_detrend", "harmonics_4", "window_1_period"):
        p = plan
        if name == "harmonics_4":
            alias = plan.gauntlet.period_alias.model_copy(update={"sine_harmonics": 4})
            p = plan.model_copy(
                update={"gauntlet": plan.gauntlet.model_copy(update={"period_alias": alias})}
            )
        if name == "window_1_period":
            alias = plan.gauntlet.period_alias.model_copy(update={"detrend_window_periods": 1.0})
            p = plan.model_copy(
                update={"gauntlet": plan.gauntlet.model_copy(update={"period_alias": alias})}
            )
        if name == "no_detrend":
            battery.detrend = lambda lc_, params, mask=None: lc_
        rng = np.random.default_rng(seed)
        fails, gains, near_edge = 0, [], []
        try:
            for _ in range(50):
                phase = rng.uniform(0.0, 2.0 * math.pi)
                model = 1.0 + cand.depth / 2.0 * np.cos(
                    2.0 * math.pi * (lc.time - cand.t0) / cand.period + phase
                )
                flux = model + errors * rng.standard_normal(lc.time.size)
                r = battery.check_period_alias(replace(lc, flux=flux), cand, p)
                fails += r.status.value == "FAIL"
                gains.append(round(float(r.metrics.get("box_delta_bic", float("nan"))), 1))
                near_edge.append(round(float(math.cos(phase)), 2))
        finally:
            battery.detrend = original_detrend
        variants[name] = {
            "failures_of_50": fails,
            "box_gains": gains,
            "cos_phase_at_transit": near_edge,
        }
    return {
        "label": "development diagnosis (v0.5.1 WP3 (c), #204); it decides nothing",
        "target": "TIC-101395259",
        "cadences": int(lc.time.size),
        "sectors": sorted(int(s) for s in np.unique(lc.sector)),
        "variants": variants,
    }


if __name__ == "__main__":
    doc = main()
    (HERE / "alias-dev-control.json").write_text(
        json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v["failures_of_50"] for k, v in doc["variants"].items()}))
