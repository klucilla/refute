"""The distributions of the environment records compared: the frozen environment against the
committed reference of the earlier lock, and the updated environment against the frozen one.
env_compare.py <reference> <frozen> <updated> <out.json>"""

import json
import sys
from pathlib import Path


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def diff(a, b):
    da, db = a["distributions"], b["distributions"]
    return {
        k: {"before": da.get(k), "after": db.get(k)}
        for k in sorted(set(da) | set(db))
        if da.get(k) != db.get(k)
    }


ref, frozen, updated = (load(p) for p in sys.argv[1:4])
out = {
    "lock_files": {
        "reference": ref["lock_files"],
        "frozen": frozen["lock_files"],
        "updated": updated["lock_files"],
    },
    "distributions": {
        "reference": len(ref["distributions"]),
        "frozen": len(frozen["distributions"]),
        "updated": len(updated["distributions"]),
    },
    "frozen_vs_reference": diff(ref, frozen),
    "updated_vs_frozen": diff(frozen, updated),
}
Path(sys.argv[4]).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(out, indent=1))
