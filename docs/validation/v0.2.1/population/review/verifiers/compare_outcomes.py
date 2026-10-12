"""Compare the analysis outcomes (conditions i and ii, every field the metrics use) of the
same cases across run folders. Written by the Phase G reviewer; reads JSON only.
Usage: compare_outcomes.py <runs dir A> <runs dir B> [<point folder pairs ...>]
with pairs given as A_sub=B_sub (e.g. M0-f479823=M0)."""

import glob
import json
import os
import sys

KEYS = ("status", "verdict", "verdict_reason", "tests", "fatal", "candidate_period",
        "signal_verdict_without_eb_catalog", "signal_identity", "identity_factor")


def outcomes(folder):
    out = {}
    for f in sorted(glob.glob(os.path.join(folder, "cases", "*.json"))):
        r = json.load(open(f, encoding="utf-8"))
        conds = r.get("conditions") or {}
        out[r["case"]] = (r["status"], {c: {k: o.get(k) for k in KEYS} for c, o in conds.items()})
    return out


a_root, b_root = sys.argv[1], sys.argv[2]
for pair in sys.argv[3:]:
    a_sub, b_sub = pair.split("=")
    a, b = outcomes(os.path.join(a_root, a_sub)), outcomes(os.path.join(b_root, b_sub))
    common = sorted(set(a) & set(b))
    differ = [c for c in common if a[c] != b[c]]
    print(f"{a_sub} vs {b_sub}: {len(a)} and {len(b)} results, {len(common)} common, "
          f"{len(differ)} with different outcomes {differ[:5]}")
