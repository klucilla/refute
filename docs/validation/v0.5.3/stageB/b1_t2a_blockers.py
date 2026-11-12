"""v0.5.3 stage B, B1.4: what blocks T2a's injections under version 5, read from the census's
verified records (#217). ``method_status: not_validated``. A diagnostic that decides nothing.

``b1_b14.t2a_summary`` counted its blockers by comparing each test's entry, a dict, with a status
string, so its ``blockers`` came out empty; the answer, ``K_B`` and ``U_B`` read the stage verdict
and are not affected. ``b1_b14.py`` is in the census's fingerprint and stays unchanged; this script
reads the same records through ``b1_b14._records_or_partial`` (each shard checked against its
sidecar: fingerprint, argument and SHA-256) and counts, per stratum and per configuration, the
kept and lost injections, the tests that are INCONCLUSIVE or FAIL among the lost, their
inconclusive classes, and the selection's refusals. It writes ``b1-t2a-blockers.json``.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b1_b14  # noqa: E402,I001
from b1_b14 import KEPT, ft, ledger_b  # noqa: E402

STRATA = ("2_to_4", "5_to_20", "above_20")


def config_of(rec: dict, b: str) -> str:
    """B is C up to 20 sectors and A above (the design's derivation)."""
    if b == "v5B":
        return "v5C" if rec["sectors"] <= 20 else "v5A"
    return b


def stratum_view(recs: list, b: str) -> dict:
    out = {"injections": len(recs), "not_ok": 0, "missing": 0, "kept": 0, "lost": 0,
           "lost_v04_kept": 0, "verdicts": Counter(), "blockers": Counter(),
           "sole_blocker": Counter(), "inconclusive_classes": Counter(),
           "selection_refusals": Counter()}  # fmt: skip
    for rec in recs:
        if rec.get("status") != "OK" or rec.get("compat_problems"):
            out["not_ok"] += 1
            continue
        res = rec.get(config_of(rec, b))
        if res is None:
            out["missing"] += 1
            continue
        verdict = res["stage_verdict"]
        out["verdicts"][verdict] += 1
        if verdict in KEPT:
            out["kept"] += 1
            continue
        out["lost"] += 1
        out["lost_v04_kept"] += rec["v04"]["stage_verdict"] in KEPT
        # the stage's deferred tests (aperture_depth, centroid_shift: INCONCLUSIVE in every record,
        # kept or lost, v0.4 included) never block the stage verdict and are left out
        deferred = set(res.get("deferred") or [])
        bad = [
            f"{t}: {d['status']}"
            for t, d in sorted((res.get("tests") or {}).items())
            if t not in deferred and d.get("status") in ("INCONCLUSIVE", "FAIL")
        ]
        out["blockers"].update(bad)
        if len(bad) == 1:
            out["sole_blocker"][bad[0]] += 1
        for t, d in (res.get("tests") or {}).items():
            if t in deferred:
                continue
            if d.get("status") == "INCONCLUSIVE" and d.get("inconclusive_class"):
                out["inconclusive_classes"][f"{t}: {d['inconclusive_class']}"] += 1
        refused = (res.get("selection") or {}).get("refused")
        if refused:
            out["selection_refusals"][refused.split(":", 1)[-1].strip()] += 1
    for key in ("verdicts", "blockers", "sole_blocker", "inconclusive_classes",
                "selection_refusals"):  # fmt: skip
        out[key] = dict(out[key].most_common())
    return out


def main() -> None:
    by_stratum, states = {}, {}
    for s in STRATA:
        by_stratum[s], note = b1_b14._records_or_partial(s)
        states[s] = note or "complete"
    out: dict = {
        "label": "B1.4 T2a census: blockers by stratum and configuration (diagnostic; decides "
        "nothing)",
        "method_status": "not_validated",
        "part_states": states,
        "population": len(ft.population()),
        "configurations": {},
    }  # fmt: skip
    for b in ("v5A", "v5B", "v5C"):
        out["configurations"][b] = {
            s: stratum_view(by_stratum[s], b)
            for s in STRATA
            if not (b != "v5C" and s == "above_20")
        }
    out["v04_by_stratum"] = {
        s: dict(Counter(r["v04"]["stage_verdict"] for r in by_stratum[s] if "v04" in r))
        for s in STRATA
    }
    (HERE / "b1-t2a-blockers.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n"
    )
    print(json.dumps(out, indent=1, sort_keys=True)[:12000])


if __name__ == "__main__":
    with ledger_b.Exclusive("b1_t2a_blockers"):
        main()
