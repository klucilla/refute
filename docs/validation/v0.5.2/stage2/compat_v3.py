"""v0.5.2 stage 2: a compatibility check of versions 2 and 3 (design, section 9, step 3).

Each scenario goes through ``analyze_data`` under the plans of discovery versions 2 and 3, and the
canonical JSON of the plan's dump, every test, the final candidate, the flattened curve, the event
depths, the timing, the ephemeris, the markers, the roles and the prewhitening is hashed. Run
against an archive of the source at a commit before version 4 (``--src <folder>``) and against the
working tree; the two outputs must be identical. **What it shows:** those projections are unchanged
on these scenarios, with the corrections off and on and with the auxiliary data absent; it is not
a proof for every input, and the persisted dossier's other fields are not hashed.

Usage (from the project root): ``.venv/Scripts/python.exe <this file> --src <folder> --out <file>``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict, is_dataclass, replace
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--src", required=True)
parser.add_argument("--out", required=True)
args = parser.parse_args()
sys.path.insert(0, str(Path(args.src).resolve()))

import numpy as np  # noqa: E402

from refute.packs.tess import synthetic as syn  # noqa: E402
from refute.packs.tess.params import TessTestPlan  # noqa: E402
from refute.packs.tess.pipeline import analyze_data  # noqa: E402

SCENARIOS = ("planet", "planet_three_years", "noise", "eb_secondary", "eb_odd_even", "sinusoid")


def plain(value):
    if is_dataclass(value):
        return plain(asdict(value))
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]
    if isinstance(value, np.ndarray):
        return plain(value.tolist())
    if isinstance(value, np.generic):
        return plain(value.item())
    if isinstance(value, float) and not math.isfinite(value):
        return repr(value)
    if hasattr(value, "value") and not isinstance(value, (int, float, str)):
        return plain(value.value)
    return value


def record(analysis, plan) -> str:
    g = analysis.gauntlet
    doc = {
        "plan": plan.model_dump(mode="json"),
        "verdict": analysis.verdict,
        "reason": analysis.verdict_reason,
        "tests": [plain(t) for t in analysis.tests],
        "final": plain(g.final),
        "flat": hashlib.sha256(np.asarray(g.flat.flux).tobytes()).hexdigest() if g.flat else None,
        "primary": plain(g.primary),
        "secondary": plain(g.secondary),
        "ephemeris": plain(g.ephemeris),
        "timing": plain(g.timing),
        "executed": plain(g.executed),
        "prewhitening": plain(g.prewhitening),
        "roles": plain(analysis.roles),
        "stage": analysis.stage,
    }
    text = json.dumps(doc, sort_keys=True, allow_nan=False)
    return hashlib.sha256(text.encode()).hexdigest()


def corrected(raw: dict) -> dict:
    return {**raw, "gauntlet": {"corrections": {"enabled": True, "version": 2}}}


def main() -> None:
    out = {"records": {}}
    plans = {
        "v2": syn.discovery_v05_plan_dict(),
        "v3": syn.discovery_v051_plan_dict(),
        "v3-corrections": corrected(syn.discovery_v051_plan_dict()),
    }
    for label, raw in plans.items():
        plan = TessTestPlan.model_validate(raw)
        for name in SCENARIOS:
            analysis = analyze_data(syn.scenario_data(name), plan)
            out["records"][f"{label}/{name}"] = record(analysis, plan)
        data = replace(syn.scenario_data("planet"), aux=None)
        out["records"][f"{label}/planet-no-aux"] = record(analyze_data(data, plan), plan)
    Path(args.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8")
    print(json.dumps(out["records"], indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
