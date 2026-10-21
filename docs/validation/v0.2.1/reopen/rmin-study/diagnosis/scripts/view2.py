"""Read only: the disappearing scenario's evaluation-qualified set in safety-utility.json."""

import json
import sys
from pathlib import Path

su = json.loads((Path(sys.argv[1]) / "safety-utility.json").read_text("utf-8"))
for r, cells in su.items():
    for cell, e in cells.items():
        if cell.endswith("disappearing"):
            print(
                r,
                cell,
                "PASS",
                e["PASS"],
                "decided",
                e["decided"],
                "qualified",
                e["evaluation_qualified_set"],
            )
