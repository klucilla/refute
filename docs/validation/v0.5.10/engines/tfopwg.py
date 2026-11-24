"""Read the TFOPWG disposition of the 24 TOIs from the NASA Exoplanet Archive (description only).

Part (f) of the charter: the table of results sits beside the TFOPWG disposition, with its source
and date, for description only (G3), never as a verdict. Metadata only (the archive's TOI table,
column tfopwg_disp), in the project's environment. Output: tfopwg.json.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from census_common import tap  # noqa: E402

SET = HERE.parents[1] / "v0.5.9/prototype-set.json"


def main() -> int:
    s = json.loads(SET.read_text(encoding="utf-8"))
    tois = s["tois"]
    names = ",".join(f"'{t}'" for t in sorted(set(tois.values())))
    rows, meta = tap(
        "tfopwg-24",
        f"select toi, tid, tfopwg_disp, rowupdate from toi where toi in ({names})",
    )
    by_toi = {f"{float(r['toi']):.2f}": r for r in rows}
    out = {}
    for key, toi in tois.items():
        r = by_toi.get(f"{float(toi):.2f}")
        out[key] = {
            "toi": toi,
            "tfopwg_disp": None if r is None else r.get("tfopwg_disp"),
            "rowupdate": None if r is None else r.get("rowupdate"),
            "tid_matches": None if r is None else int(r["tid"]) == int(key.split("-")[1]),
        }
    doc = {
        "schema": "refute-v0510-tfopwg-1",
        "mode": "exploratory",
        "use": "description only (G3); never a verdict, never a label for a TOI in Refute's terms",
        "source": meta,
        "targets": out,
    }
    (HERE / "tfopwg.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    counts: dict = {}
    for v in out.values():
        counts[v["tfopwg_disp"]] = counts.get(v["tfopwg_disp"], 0) + 1
    print(counts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
