"""The SHA-256 of every record file of X2's lot, and copies of its manifest and run reports, for the
results record: python x2_lot_digests.py <run folder> <out folder>."""

import json
import shutil
import sys
from pathlib import Path

POP = Path(__file__).resolve().parents[4] / "population"
sys.path.insert(0, str(POP))
import x2_study as x2  # noqa: E402

run, out = Path(sys.argv[1]), Path(sys.argv[2])
data = x2.load_x2_lot(run)
(out / "lot-record-digests.json").write_text(
    json.dumps(data["files"], indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
)
shutil.copyfile(run / "manifest.json", out / "lot-manifest.json")
for p in sorted(run.glob("run-report-*.json")):
    shutil.copyfile(p, out / f"lot-{p.name}")
print(len(data["files"]), "records;", len(data["leftovers"]), "leftovers")
