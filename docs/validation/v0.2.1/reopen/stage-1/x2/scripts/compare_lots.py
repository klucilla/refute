"""Compare two X2 run folders' records byte for byte and write the resumption check's result.
python compare_lots.py <continuous> <interrupted> <out.json> <records at the stop> <pids>
<seconds> (this copy's docstring wrapped for the line limit; otherwise as run)."""

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
    "continuous": str(a),
    "interrupted": str(b),
    "records_continuous": len(fa),
    "records_interrupted": len(fb),
    "records_at_the_stop": int(sys.argv[4]),
    "stopped_pids": sys.argv[5],
    "continuous_seconds": float(sys.argv[6]),
    "same_names": sorted(fa) == sorted(fb),
    "byte_identical": fa == fb,
    "differing": sorted(k for k in fa if fb.get(k) != fa[k]),
    "problems_continuous": x2.x2_lot_problems(a),
    "problems_interrupted": x2.x2_lot_problems(b),
    "leftovers_interrupted": x2.load_x2_lot(b)["leftovers"],
    "reports_interrupted": sorted(p.name for p in b.glob("run-report-*.json")),
    "digests": {k: hashlib.sha256(v).hexdigest() for k, v in sorted(fa.items())},
}
out.write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
print(json.dumps({k: result[k] for k in list(result)[:12]}, indent=1))
