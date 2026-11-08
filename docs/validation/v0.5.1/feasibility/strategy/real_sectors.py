"""Item 3 (a): the number of sectors of the real stars of v0.5 (C2's 100 stars, C3's 22 targets),
from the local fetch records of v0.5. Only counts leave this script; it decides nothing.

Usage (from the project root): ``.venv/Scripts/python.exe <this file>``; writes
``real-sectors.json``.
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent
FETCH = ROOT / ".cache/v05/calibration"


def bucket(n: int) -> str:
    return str(n) if n in (1, 2, 3, 4) else ("0" if n == 0 else "5 or more")


def main():
    c2 = json.loads((FETCH / "c2-fetch.json").read_text("utf-8"))
    counts = Counter()
    for files in c2["files"].values():
        n = len(files) if isinstance(files, (list, dict)) else 0
        counts[bucket(n)] += 1
    c3 = json.loads((FETCH / "c3-fetch.json").read_text("utf-8"))
    c3_counts = Counter(
        bucket(len(s.get("light_curve_sectors") or [])) for s in c3["states"].values()
    )
    out = {
        "label": "development reading; it decides nothing",
        "c2_stars_by_number_of_light_curve_files": dict(sorted(counts.items())),
        "c3_targets_by_number_of_light_curve_sectors": dict(sorted(c3_counts.items())),
        "note": "A0's group rows are calibrated for 2, 3 and 4 sectors only; a star's sectors with "
        "measured events can be fewer than its light-curve sectors",
    }
    (HERE / "real-sectors.json").write_text(json.dumps(out, indent=1) + "\n", "utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
