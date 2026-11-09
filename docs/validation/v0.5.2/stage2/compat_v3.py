"""v0.5.2 stage 2: the byte-compatibility check of versions 2 and 3 (design, section 9, step 3).

Each scenario goes through ``analyze_data`` under the plans of discovery versions 2 and 3, and the
canonical JSON of every test (status, message, metrics, thresholds, coverage, sensitivity), with
the plan's dump, is hashed. Run against an archive of the source at a commit before version 4
(argument ``--src <folder>``) and against the working tree; the two outputs must be identical.

Usage (from the project root): ``.venv/Scripts/python.exe <this file> --src <folder> --out <file>``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
from dataclasses import asdict, is_dataclass
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


def main() -> None:
    out = {"source": str(Path(args.src).name) and "see the command line", "records": {}}
    plans = {"v2": syn.discovery_v05_plan_dict(), "v3": syn.discovery_v051_plan_dict()}
    for label, raw in plans.items():
        plan = TessTestPlan.model_validate(raw)
        for name in SCENARIOS:
            analysis = analyze_data(syn.scenario_data(name), plan)
            doc = {
                "plan": plan.model_dump(mode="json"),
                "verdict": analysis.verdict,
                "reason": analysis.verdict_reason,
                "tests": [plain(t) for t in analysis.tests],
            }
            text = json.dumps(doc, sort_keys=True, allow_nan=False)
            out["records"][f"{label}/{name}"] = hashlib.sha256(text.encode()).hexdigest()
    Path(args.out).write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8")
    print(json.dumps(out["records"], indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
