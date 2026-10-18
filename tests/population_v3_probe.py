"""A probe for tests/test_population_v3.py, run in its own process (the harness version 3 replaces
functions in the loaded version 2, which must not leak into the test process).

Usage: ``python tests/population_v3_probe.py <mode> <work folder>``; prints one JSON object.
Modes: ``v3`` (the harness version 3, with REFUTE_M4_CONFIGURATION set by the caller: one
synthetic case analyzed by a spawned worker of version 2's pool), ``v2`` (version 2 alone: its
plan), ``import`` (only import version 3).
"""

import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POPULATION = ROOT / "docs" / "validation" / "v0.2.1" / "population"


def _import(name):
    sys.path.insert(0, str(POPULATION))
    return importlib.import_module(name)


def main() -> None:
    mode, work = sys.argv[1], Path(sys.argv[2])
    if mode == "import":
        _import("population_v3")
        print(json.dumps({"imported": True}))
        return
    if mode == "v2":
        pv2 = _import("population_v2")
        print(json.dumps({"active": pv2._plan().gauntlet.corrections.active}))
        return
    v3 = _import("population_v3")
    pv2 = v3.pv2
    case = next(c for c in pv2.population_cases("selftest") if c["class"] == "planet")
    blob, entry, _, _ = pv2.built_case(case)
    cache = work / "cache"
    run_dir = work / "run"
    (run_dir / "cases").mkdir(parents=True)
    cache.mkdir()
    (cache / f"{entry['id']}.rpc").write_bytes(blob)
    identity = {"probe": True}
    declared = {
        "environment": {pv2.DISPATCH_VARIABLE: os.environ.get(pv2.DISPATCH_VARIABLE)},
        "table": pv2.dispatch_table(),
    }
    outcome = pv2.run_pool(
        pv2.analyze_task,
        [(entry, str(cache), str(run_dir), identity)],
        1,
        declared,
        on_worker=lambda report: None,
        on_result=lambda i, r: None,
    )
    if not outcome.results:
        print(json.dumps({"error": outcome.error, "stopped": outcome.stopped, "results": None}))
        raise SystemExit(1)
    result = next(iter(outcome.results.values()))
    record = json.loads((run_dir / "cases" / f"{entry['id']}.json").read_text(encoding="utf-8"))
    scientific = record["conditions"]["i"]["scientific"]
    print(
        json.dumps(
            {
                "error": outcome.error,
                "status": record["status"],
                "main_pid": os.getpid(),
                "worker_pid": result.get("pid"),
                "marker": scientific.get("corrections"),
                "block": scientific["test_plan"]["gauntlet"]["corrections"],
                "harness_sha256": pv2.HARNESS_SHA256,
                "v3_sha256": v3.V3_SHA256,
            }
        )
    )


if __name__ == "__main__":
    main()
