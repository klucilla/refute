"""Compare the X2 subset run in the updated environment with the same subset in the frozen one,
record by record, byte for byte (modelled on x2/scripts/compare_lots.py).
compare_subsets.py <updated run> <frozen run> <out.json>"""

import hashlib
import json
import sys
from pathlib import Path

POP = Path("C:/Projetos/refute/.cache/wt-merge-check/docs/validation/v0.2.1/population")
sys.path.insert(0, str(POP))
import x2_study as x2  # noqa: E402

a, b, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])


def files(run):
    root = run / "records"
    return {
        p.relative_to(run).as_posix(): p.read_bytes()
        for p in root.rglob("*.json")
        if not p.name.startswith(".")
    }


fa, fb = files(a), files(b)
result = {
    "updated": str(a),
    "frozen": str(b),
    "records_updated": len(fa),
    "records_frozen": len(fb),
    "same_names": sorted(fa) == sorted(fb),
    "byte_identical": fa == fb,
    "differing": sorted(k for k in set(fa) | set(fb) if fa.get(k) != fb.get(k)),
    "problems_updated": x2.x2_lot_problems(a),
    "problems_frozen": x2.x2_lot_problems(b),
    "digests": {k: hashlib.sha256(v).hexdigest() for k, v in sorted(fa.items())},
}
out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
print(json.dumps({k: result[k] for k in list(result)[:9]}, indent=1))
