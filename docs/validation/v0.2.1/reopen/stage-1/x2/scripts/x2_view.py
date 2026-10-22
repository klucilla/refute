"""Print X2's evaluation tables (no per-round rows):
python x2_view.py <x2-evaluation.json> <x2-intervals.json>."""

# ruff: noqa: E501  (the printed lines are kept as run)

import json
import sys
from collections import Counter
from pathlib import Path

d = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
iv = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))


def f(x, p=3):
    return "-" if x is None else (f"{x:.{p}g}" if isinstance(x, float) else str(x))


print("rounds", d["rounds"], "code", d["manifest_code_sha256"][:12], "m_beta", iv["m_beta"])
print("\n== X2-B")
for g, e in d["x2b"].items():
    print(f"\n{g}: case-years {e['case_years']}, excluded {e['excluded']}")
    for name, r in iv["cells"][g].items():
        sd, mad = r["sd_interval"], r["mad_interval"]
        sub = e["subset_same_and_placed"][name]
        print(
            f"  {name} (D={f(r['design'])}): SD {f(sd['value'])} [{f(sd['lo'])}, {f(sd['hi'])}] n={sd['cases']} "
            f"-> {r['sd_verdict']}; MAD {f(mad['value'])} [{f(mad['lo'])}, {f(mad['hi'])}] -> {r['mad_verdict']}; "
            f"FINAL {r['verdict']} | subset {f(sub['value'])} [{f(sub['lo'])}, {f(sub['hi'])}] n={sub['cases']}"
        )
    ex = Counter()
    for s in e["case_year_stats"].values():
        if s.get("excluded"):
            ex[s.get("measured")] += 1
    print("  excluded case-years by measured count:", dict(sorted(ex.items())))
print("\n== X2-A by cell")
for g, c in d["x2a"]["by_cell"].items():
    print(f"\n{g}")
    for k in ("all", "z_train_ge_3", "fail"):
        print(f"  {k}: n={c[k]['n']} {json.dumps(c[k]['counts'])}")
print("\n== X2-A by cell and mechanism")
for g, c in d["x2a"]["by_cell_and_mechanism"].items():
    print(
        f"  {g}: all {json.dumps(c['all'])}\n      z>=3 {json.dumps(c['z_train_ge_3'])}\n      fail {json.dumps(c['fail'])}"
    )
print("\n== descriptive")
for g, c in d["descriptive"].items():
    print(f"  {g}: {json.dumps(c)}")
ident = Counter()
for r in d["rows"]:
    ident[(r["group"], r.get("identity", "no ephemeris"))] += 1
print("\n== identity by cell:", {f"{k[0]}|{k[1]}": v for k, v in sorted(ident.items())})
fails = [r for r in d["rows"] if r.get("fail")]
print("\n== FAIL rounds:", len(fails))
for r in fails[:40]:
    print(
        f"  {r['group']} {r['case_id']} j{r['realization']} y{r['year']} id={r.get('identity')} "
        f"I={f(r.get('I'))} L={f(r.get('L'))} A={f(r.get('A'))} off={f(r.get('offset_max_durations'))}D "
        f"outmask={f(r.get('outside_masks'))} cause={r['cause']}"
    )
