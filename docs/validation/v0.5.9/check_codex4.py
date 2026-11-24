"""Check Codex's round-4 numbers: identity-qualified flips (block 6) and power at 320 pairs
(block 7)."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from yield_model import power  # noqa: E402

D = ("SURVIVED", "WEAKENED", "REFUTED")
recs = json.loads((ROOT / "docs/validation/v0.5.9/prototype-records.json").read_text("utf-8"))[
    "records"
]
by = {}
for r in recs:
    by.setdefault(r["target_key"], {})[r["entry_mode"]] = r


def dec(r, cons):
    if r.get("status") != "OK":
        return None
    on = (r.get("identity") or {}).get("stayed_on_toi_ephemeris")
    out = (
        (r.get("consensus") or {}).get("outcome") if cons else (r.get("base") or {}).get("outcome")
    )
    return out if (out in D and on) else None


for cons in (False, True):
    inf = flips = 0
    raw_inf = raw_flips = 0
    for m in by.values():
        e, s = dec(m["E"], cons), dec(m["S"], cons)
        if e or s:
            inf += 1
            flips += (e is None) != (s is None) or (e and s and e != s)
        eo = (
            (m["E"].get("consensus") or {}).get("outcome")
            if cons
            else (m["E"].get("base") or {}).get("outcome")
        )
        so = (
            (m["S"].get("consensus") or {}).get("outcome")
            if cons
            else (m["S"].get("base") or {}).get("outcome")
        )
        if eo in D or so in D:
            raw_inf += 1
            raw_flips += (eo in D) != (so in D) or (eo in D and so in D and eo != so)
    print(
        "consensus" if cons else "base",
        "identity-qualified",
        flips,
        "/",
        inf,
        "raw",
        raw_flips,
        "/",
        raw_inf,
    )
print("power 320 at 0.05", power(320, 0.05), "300", power(300, 0.05))
