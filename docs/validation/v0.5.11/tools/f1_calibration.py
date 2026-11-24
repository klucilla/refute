"""v0.5.11 step 1: the record of the F1 calibration rule (docs/plans/v0.5.11-spec.md, section 4),
by the test-only reference evaluator, before any `src/` change.

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.11/tools/f1_calibration.py

It writes docs/validation/v0.5.11/step1/f1-calibration.json: per family (white, correlated), the
assessed, unavailable and OE_box > 3 counts over seeds 1 to 200, the OE_box values, and whether
the rule holds. Exploratory: a software check on two fixed noise families, not a population error
rate.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "tests"))

from refute.packs.tess.synthetic import (  # noqa: E402
    CORRELATED_PROFILE,
    PLANET,
    make_lightcurve,
)
from screen_reference import f1_reference  # noqa: E402

OUT = ROOT / "docs" / "validation" / "v0.5.11" / "step1" / "f1-calibration.json"
SPEC = ROOT / "docs" / "plans" / "v0.5.11-spec.md"
REF = ROOT / "tests" / "screen_reference.py"


def main() -> int:
    doc = {
        "labels": ["exploratory", "method_status: not_validated", "software check"],
        "spec_sha256": hashlib.sha256(SPEC.read_bytes()).hexdigest(),
        "reference_sha256": hashlib.sha256(REF.read_bytes()).hexdigest(),
        "rule": "each family: 200 of 200 assessed and at most 4 with OE_box > 3",
        "families": {},
    }
    holds = True
    for name, kwargs in (("white", {}), ("correlated", dict(CORRELATED_PROFILE))):
        values, states = [], []
        for seed in range(1, 201):
            lc, _ = make_lightcurve(PLANET, seed=seed, **kwargs)
            r = f1_reference(
                lc.time, lc.flux, lc.flux_err, PLANET.period, PLANET.t0, PLANET.duration
            )
            states.append(r.state)
            values.append(r.metrics.get("oe_box"))
        assessed = sum(s != "not_assessed" for s in states)
        exceed = sum(1 for v in values if v is not None and v > 3.0)
        ok = assessed == 200 and exceed <= 4
        holds = holds and ok
        doc["families"][name] = {
            "assessed": assessed,
            "unavailable": 200 - assessed,
            "exceedances": exceed,
            "rule_holds": ok,
            "oe_box": [None if v is None else round(v, 6) for v in values],
        }
    doc["rule_holds"] = holds
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    summary = {"rule_holds": holds}
    for k, v in doc["families"].items():
        summary[k] = {x: v[x] for x in ("assessed", "exceedances")}
    print(json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
