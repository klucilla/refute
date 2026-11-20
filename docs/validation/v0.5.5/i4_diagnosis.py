"""v0.5.5: a diagnosis of I4's convergence failures (#218; the maintainer's decision of 2026-11-20,
night, item 3a; ``docs/validation/v0.5.4/record-defects.md``, section 3). **A diagnosis only: no
conclusion on D2.** ``method_status: not_validated``. Development records only.

On I4's two sets, already read (the fresh 178 of round 3 and v0.5.2's 112), every planet I4 marked
invalid is listed with its reasons. For each one whose reasons include "the convergence check
failed":
1. the curve is rebuilt (C1 version 1 and I4's development seed: ``c1.generate("P",
   c1.development_seed("P", i))``, exactly as I4);
2. I4's own check is recomputed (``i4_bound.shape_and_derivatives`` and ``i4_bound._numeric``),
   and each derivative's relative L2 difference must equal I4's recorded one to 1e-9 relative
   (the reproduction check; otherwise the planet is "not reproduced");
3. the same difference over the cadences that straddle no corner of the trapezoid
   (``i4_fix.masked_convergence``), with the guard of ``i4_fix``;
4. the cause is **confirmed** for the planet if the masked check passes I4's tolerance while the
   full one fails; **not confirmed** otherwise;
5. if confirmed and the planet has no other invalid reason, its power is computed from I4's
   recorded σ and alternative (``power.gaussian_probability``, unchanged): reported apart, with
   no reading against D2.

I4's records are located under the code hash they were written with (``pinned_hash``) and read
by I4's own reader with ``budgeted`` bound to v0.5.4's ledger for the read only.

Usage (from the project root): ``.venv/Scripts/python.exe -B .cache/v054/tools/pin.py
"import runpy; runpy.run_path('docs/validation/v0.5.5/i4_diagnosis.py', run_name='__main__')"``
"""

from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
V054 = ROOT / "docs/validation/v0.5.4"
for p in (str(V054), str(HERE)):
    if p not in sys.path:
        sys.path.insert(0, p)
import i4_bound as i4  # noqa: E402,I001  (stage A's and B's modules, then ledger_i)
import i4_rest2  # noqa: E402
import ledger_i  # noqa: E402,F401  (imported before ledger_v055, which binds last)
import historical_read  # noqa: E402
import i4_fix  # noqa: E402
import pinned_hash  # noqa: E402
import ledger_v055 as lv  # noqa: E402  (last: it binds budgeted to v0.5.5's ledger)

OUT_FILE = HERE / "i4-convergence-diagnosis.json"
CONVERGENCE_REASON = "the convergence check failed"
REPRO_TOL = 1e-9


def i4_records() -> list:
    with pinned_hash.pinned():
        rows = i4.schedule()
        with historical_read.v054_read():
            fp = i4.fingerprint(rows)
            recs, refusal, _ = i4_rest2._records(rows, fp)
    if refusal:
        raise SystemExit(f"I4's reader: {refusal}: STOP")
    return recs


def diagnose(rec: dict) -> dict:
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.power import gaussian_probability

    i = rec["index"]
    data, truth = c1.generate("P", c1.development_seed("P", i))
    t = data.lc.time
    _, deriv, n = i4.shape_and_derivatives(t, truth)
    conv = i4_fix.masked_convergence(
        t, truth, deriv, n, lambda name, h: i4._numeric(t, truth, name, h)
    )
    recorded = rec["nuisance"].get("convergence", {})
    reproduced = all(
        name in recorded
        and math.isfinite(recorded[name])
        and abs(conv[name]["full"] - recorded[name]) <= REPRO_TOL * max(abs(recorded[name]), 1e-300)
        for name in i4_fix.NAMES
    )
    full_fails = any(c["full"] > i4_fix.CONVERGENCE_TOL for c in conv.values())
    ok = i4_fix.passes(conv)
    out = {
        "set": rec["set"],
        "index": i,
        "reproduced": reproduced,
        "convergence": conv,
        "masked_check": {True: "passes", False: "fails", None: "not covered"}[ok],
        "cause_confirmed": bool(reproduced and full_fails and ok is True),
        "other_invalid_reasons": [r for r in rec["nuisance"]["invalid"] if r != CONVERGENCE_REASON],
    }
    if out["cause_confirmed"] and not out["other_invalid_reasons"] and "sigma" in rec["nuisance"]:
        _, _, p4 = i4.fv.plans()
        power = gaussian_probability(
            rec["alternative"], rec["nuisance"]["sigma"], p4.gauntlet.odd_even.max_sigma
        )
        out["power_after_fix"] = float(power)
    return out


def main() -> None:
    if OUT_FILE.exists():
        raise SystemExit(f"{OUT_FILE.name} exists: the record is written once")
    started = time.process_time()
    recs = i4_records()
    by_set: dict = {}
    rows = []
    for rec in recs:
        if rec.get("status") != "OK" or rec.get("mismatch") or "nuisance" not in rec:
            continue
        invalid = rec["nuisance"].get("invalid") or []
        if not invalid:
            continue
        s = by_set.setdefault(rec["set"], {"invalid": 0, "reasons": {}, "convergence": 0})
        s["invalid"] += 1
        for r in invalid:
            s["reasons"][r] = s["reasons"].get(r, 0) + 1
        if CONVERGENCE_REASON in invalid:
            s["convergence"] += 1
            rows.append(diagnose(rec))
    for name, s in by_set.items():
        mine = [r for r in rows if r["set"] == name]
        s.update(
            not_reproduced=sum(not r["reproduced"] for r in mine),
            cause_confirmed=sum(r["cause_confirmed"] for r in mine),
            masked_check={
                k: sum(r["masked_check"] == k for r in mine)
                for k in ("passes", "fails", "not covered")
            },
            valid_after_fix=sum("power_after_fix" in r for r in mine),
        )
    used = time.process_time() - started
    doc = {
        "label": "v0.5.5: a diagnosis of I4's convergence failures on I4's two sets "
        "(development; a diagnosis only, no conclusion on D2)",
        "method_status": "not_validated",
        "decision": "the maintainer's decision of 2026-11-20 (night), item 3a (#218)",
        "fix": "docs/validation/v0.5.5/i4_fix.py: I4's check restricted to the cadences that "
        "straddle no corner of the trapezoid, with a coverage guard",
        "tolerance": i4_fix.CONVERGENCE_TOL,
        "max_masked_fraction": i4_fix.MAX_MASKED_FRACTION,
        "sets": by_set,
        "planets": rows,
        "cpu_hours": round(used / 3600.0, 4),
    }
    OUT_FILE.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    lv.declare()
    lv.charge(
        f"i4_diagnosis_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
        used / 3600.0,
        f"i4_diagnosis.py: process time {used:.1f} s",
    )
    print(json.dumps(by_set, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
