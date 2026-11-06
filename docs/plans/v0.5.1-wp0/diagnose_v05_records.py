"""WP0 of v0.5.1: the numbers of section 2 of docs/plans/v0.5.1-plan.md, from the v0.5 records.

Development use only (v0.5.1 plan, section 5). Reads the v0.5 C1 confirmation and C2 records,
checks the C1 records against the SHA-256 of their Drive manifest, and prints one JSON document.

Usage: .venv/Scripts/python.exe docs/plans/v0.5.1-wp0/diagnose_v05_records.py > out.json
"""

from __future__ import annotations

import collections
import hashlib
import json
import math
import sys
from pathlib import Path
from statistics import NormalDist, median

ROOT = Path(__file__).resolve().parents[3]
C1 = ROOT / ".cache/v05/calibration/c1-confirmation/records.jsonl"
C1_SHA256 = "538382d0b973ed02b061a0e97d4d7485ff5f88afc824928f40b13fdcc62bc5e7"
C2 = ROOT / ".cache/v05/calibration/c2/records.jsonl"

PLANETS = ("P", "PG", "PV", "PA")
G, M_SUN, R_SUN = 6.674e-11, 1.989e30, 6.957e8


def load(path: Path, sha256: str | None = None) -> list[dict]:
    data = path.read_bytes()
    if sha256 is not None and hashlib.sha256(data).hexdigest() != sha256:
        raise SystemExit(f"{path.name}: SHA-256 differs from its manifest")
    return [json.loads(line) for line in data.splitlines() if line.strip()]


def eligible(record: dict) -> bool:
    if record.get("status") != "OK" or not record["chain"]["v05"]["gate_passed"]:
        return False
    return record["family"] not in PLANETS or bool(record.get("identity"))


def inconclusive_tests(battery: dict) -> tuple[str, ...]:
    return tuple(
        t for t in battery["stage_tests"] if battery["tests"][t]["status"] == "INCONCLUSIVE"
    )


def max_duration(period_days: float, k: float, radius: float) -> float:
    """The circular-orbit duration of a central transit for a 1 M_sun star of ``radius``."""
    p = period_days * 86400.0
    a = (G * M_SUN * p**2 / (4 * math.pi**2)) ** (1 / 3) / (radius * R_SUN)
    return period_days / math.pi * math.asin(min(1.0, (1 + k) / a))


def c1_section(records: list[dict]) -> dict:
    out: dict = {}
    by_family = collections.defaultdict(list)
    for r in records:
        if eligible(r):
            by_family[r["family"]].append(r)
    # 2.1: which decisive tests refused a PASS, per family
    refused = {}
    for fam in ("P", "PG", "PV", "PA", "EB1", "EB2"):
        inc = [r for r in by_family[fam] if r["chain"]["v05"]["verdict"] == "INCONCLUSIVE"]
        tally = collections.Counter(t for r in inc for t in inconclusive_tests(r["chain"]["v05"]))
        refused[fam] = {"eligible": len(by_family[fam]), "inconclusive": len(inc), "tests": tally}
    out["inconclusive_by_test"] = refused
    # 2.4: INCONCLUSIVE with no decisive FAIL, per spurious family
    held = {}
    for fam in ("SE", "V1", "V2", "ER", "NR", "NW", "EB1", "EB2", "PX"):
        rows = by_family[fam]
        inc = [r for r in rows if r["chain"]["v05"]["verdict"] == "INCONCLUSIVE"]
        no_fail = [
            r
            for r in inc
            if "FAIL"
            not in [
                r["chain"]["v05"]["tests"][t]["status"]
                for t in r["chain"]["v05"]["stage_tests"]
                if t != "snr"
            ]
        ]
        single = collections.Counter(
            r["chain"]["v05"]["tests"]["single_event"]["status"] for r in inc
        )
        held[fam] = {
            "eligible": len(rows),
            "verdicts": collections.Counter(r["chain"]["v05"]["verdict"] for r in rows),
            "inconclusive_without_decisive_fail": len(no_fail),
            "single_event_among_inconclusive": single,
        }
    out["held_by_inconclusive"] = held
    # 2.5: the surviving binaries
    nd = NormalDist()
    binaries = {}
    for fam in ("EB1", "EB2"):
        rows = by_family[fam]
        survivors = [r for r in rows if r["chain"]["v05"]["verdict"] == "SURVIVED"]
        others = [r for r in rows if r["chain"]["v05"]["verdict"] != "SURVIVED"]

        def folded(r: dict) -> bool:
            true_p = r["truth"].get("true_period_days", r["truth"]["period_days"])
            return abs(r["chain"]["v05"]["candidate"]["period_days"] / true_p - 0.5) < 0.02

        expected = 0.0
        for r in rows:
            t = r["truth"]
            snr, ratio = t["target_snr"], t["secondary_ratio"]
            if folded(r):
                p_survive = nd.cdf(3.0 - (1.0 - ratio) * snr / math.sqrt(2.0))
                found = r["chain"]["v05"]["candidate"]["period_days"]
                too_long = t["duration_days"] / max_duration(found, math.sqrt(t["depth"]), 1.05)
                expected += 0.0 if too_long > 1.0 else p_survive
            else:
                expected += nd.cdf(3.0 - ratio * snr)
        binaries[fam] = {
            "eligible": len(rows),
            "survivors": len(survivors),
            "survivors_folded_at_half": sum(folded(r) for r in survivors),
            "median_ratio_survivors": median(r["truth"]["secondary_ratio"] for r in survivors),
            "median_ratio_others": median(r["truth"]["secondary_ratio"] for r in others),
            "rough_bound_expected_survivors": round(expected, 1),
        }
    out["binaries"] = binaries
    return out


def c2_section(records: list[dict]) -> dict:
    injections = [r for r in records if r["kind"] == "injection" and r["status"] == "OK"]
    inc = [
        r
        for r in injections
        if (r["chain"].get("v05") or {}).get("stage_verdict") == "INCONCLUSIVE"
    ]
    tally = collections.Counter(t for r in inc for t in inconclusive_tests(r["chain"]["v05"]))
    return {"injections_inconclusive": len(inc), "tests": tally}


def main() -> None:
    doc = {
        "note": "v0.5 records, development use only (v0.5.1 plan, section 5)",
        "c1": c1_section(load(C1, C1_SHA256)),
        "c2": c2_section(load(C2)),
    }
    json.dump(doc, sys.stdout, indent=1, sort_keys=True, default=dict)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
