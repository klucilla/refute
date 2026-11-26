"""Item 6a of the maintainer's decisions of 2026-11-26 (#218, comment 7204660147): the type
composition of the 307 usable KELT-FP false positives, from catalogue labels only.

The question (logged in log.jsonl before this ran): of the KELT-FP TICs that v0.5.10's census
found usable (SPOC 2-minute data, not exposed), how many carry each KELT-FP type label (NEB, SB1,
SB2, EB1, EB2, BEB, Giant, others)?

- **The unit is the distinct TIC** (the census's 307 usable TICs; the table has 308 usable rows,
  so one TIC has two rows). A TIC whose rows carry one type counts once under it; a TIC whose rows
  carry different types counts under "multiple types", with its types listed.
- **The only input** is the census table archived on the Drive on 2026-11-24
  (census-d1-targets.json), checked against its SHA-256 in
  docs/validation/v0.5.10/cleanup/manifest.json before use. Its `type` field is the catalogue's
  label (KELT_False_Positive_Catalog_20180531.csv, as v0.5.10 read it).
- **Nothing else is read:** no light curve, no pixel file, no battery output. No KELT-FP battery
  result exists.

Output: type-count.json next to this file. Labels: exploratory, method_status not_validated; the
counts come from v0.5.10's census and carry its limits label.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ARCHIVE = Path(
    "K:/Meu Drive/Pessoal/Projetos/refute/cache-archive-2026-11-24-v0510/v0510/census"
    "/census-d1-targets.json"
)
EXPECTED = "f7d89ce7e1affe8d3b4e0899a1b88a80398b76acb66ccb6572ec915040739a0f"
NAMED = ("NEB", "SB1", "SB2", "EB1", "EB2", "BEB", "Giant")


def main() -> int:
    data = ARCHIVE.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED:
        raise SystemExit(f"census-d1-targets.json: SHA-256 {digest} differs from the manifest")
    rows = json.loads(data.decode("utf-8"))
    usable = [
        r for r in rows if r["arm"] == "kelt_fp" and r.get("spoc_2min") and not r.get("exposed")
    ]
    by_tic: dict[int, set[str]] = {}
    for r in usable:
        by_tic.setdefault(r["tic"], set()).add(str(r.get("type") or "(none)"))
    single = Counter(next(iter(t)) for t in by_tic.values() if len(t) == 1)
    multiple = {str(tic): sorted(t) for tic, t in by_tic.items() if len(t) > 1}
    counts = {name: single.get(name, 0) for name in NAMED}
    others = {k: v for k, v in sorted(single.items()) if k not in NAMED}
    doc = {
        "schema": "refute-v0513-amendment1-type-count-1",
        "mode": "exploratory",
        "method_status": "not_validated",
        "limits_label_of_the_counts": (
            "v0.5.10: closed with declared limits (gate REFUTED); does not meet criteria 1, 2, 3, "
            "4, 5, 7, 8, 9, 10"
        ),
        "input": {"file": "census-d1-targets.json (Drive archive of 2026-11-24)", "sha256": digest},
        "usable_rows": len(usable),
        "usable_distinct_tics": len(by_tic),
        "unit": "distinct TIC",
        "by_type": counts,
        "others": others,
        "others_total": sum(others.values()),
        "multiple_types": multiple,
        "check_sum": sum(counts.values()) + sum(others.values()) + len(multiple),
    }
    (HERE / "type-count.json").write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    keys = ("usable_rows", "usable_distinct_tics", "by_type", "others", "multiple_types")
    print(json.dumps({k: doc[k] for k in (*keys, "check_sum")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
