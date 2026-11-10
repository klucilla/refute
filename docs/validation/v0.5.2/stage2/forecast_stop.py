"""v0.5.2 stage 2: the maintainer's rule for the forecast (2026-11-10, #216, item 1): a planet
target failing in the forecast with version 4 is a STOP. Reads ``forecast-v4.json`` (D2, D4, by
the frozen rules) and ``forecast-t2a.json`` (T2a, version 4 as built); a FAIL is written to the
budget ledger as the failed gate ``planet_forecast``, which blocks every later part. It decides
nothing else. ``method_status: not_validated``.

Usage: ``.venv/Scripts/python.exe <this file>`` after both summaries.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import budgeted  # noqa: E402


def main() -> None:
    failed = {}
    d = json.loads((HERE / "forecast-v4.json").read_text("utf-8"))["batteries"]["v4"]
    for target in ("D2", "D4"):
        if d[target] == "FAIL":
            failed[target] = "forecast-v4.json"
    t2a = HERE / "forecast-t2a.json"
    t = {"forecast": "not run"}
    if t2a.exists():
        t = json.loads(t2a.read_text("utf-8"))["batteries"]["v4A"]
        if t["forecast"] == "FAIL":
            failed["T2a"] = "forecast-t2a.json"
    print({"failed": failed, "D2": d["D2"], "D4": d["D4"], "T2a": t["forecast"]}, flush=True)
    if failed:
        budgeted.fail_gate("planet_forecast", failed)
        raise SystemExit(f"{sorted(failed)} fail in the forecast with version 4: a STOP")


if __name__ == "__main__":
    main()
