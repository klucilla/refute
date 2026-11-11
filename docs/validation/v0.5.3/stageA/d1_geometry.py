"""v0.5.3 stage A, item (d): D1's geometric route, measured as a diagnostic (#217;
`docs/plans/v0.5.3-stageA-design.md`, section (d); #215). **Development data and development seeds
only; it decides nothing and no test is built from it.** ``method_status: not_validated``.

**The statistic** is v0.5.1's transit-geometry consistency (``d1_routes.geometry_dchi2``, imported
unchanged from `docs/validation/v0.5.1/feasibility/d1_routes.py`): on the curve flattened with the
candidate's transits masked, a free trapezoid against a physical planet at the found period with
the star's radius and mass under Gaussian priors from the catalogue star; ``dchi2`` (white weights)
and ``dchi2_cov`` (the generator's covariance). Each curve is ``d1_routes.route_one``: C1's
generator at the development seed ``refute-v051-dev:route-<family>:<i>``, the frozen v0.4
candidate generation, eligibility (the SNR gate; for planets, the identity with the truth).

**The sample.** v0.5.1 measured indices 0 to 149 of each family (`.cache/v051/d1routes/route.jsonl`,
summarized in `docs/validation/v0.5.1/feasibility/d1-routes.json`); its planets' 99.73 % quantile
rested on about one tail observation. Here, new development seeds: indices 150 to 949 of P and PG
(800 each) and 150 to 299 of EB1 and EB2 (150 each), so that, with v0.5.1's, about 1,900 planet
curves fix the threshold.

**The reading, fixed before the measurement.** For each statistic: the threshold is the larger of
the 99.73 % quantiles of the eligible P and of the eligible PG values (so that each family's
false-failure fraction in this calibration sample is at most 0.0027; noise types pooled within a
family, as C1's population mixes them), with each family's count strictly above it stated; at that
threshold, the fraction of eligible EB1 and EB2 flagged (overall and among the folded EB1), and of
eligible P and PG flagged, per noise type (white, correlated). These are calibration-sample
fractions, with no population guarantee; nothing here sets a rule. **Cost**, revised before the run
from v0.5.1's records (a mean of 14.75 CPU-seconds per curve): about 7.7 CPU-h, inside the part's
cap of 1.5 times its 6 CPU-h; it runs only after (a), (b), (c1), (c2) are done and (c3) is done or
cut, with at least 6 CPU-h left under stage A's cap.

Usage: ``run`` through ``scripts/launch_affinity.ps1``, then ``summarize`` (``d1-geometry.json``).
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ledger_a  # noqa: E402,I001  (before budgeted: it points the ledger at stage A's)
import budgeted  # noqa: E402

FEAS = ledger_a.ROOT / "docs/validation/v0.5.1/feasibility"
sys.path.insert(0, str(FEAS))
import d1_routes  # noqa: E402

PART = "d_geometry"
OUT = ledger_a.ROOT / ".cache/v053/stageA/d1-geometry"
OLD = ledger_a.ROOT / ".cache/v051/d1routes/route.jsonl"
WORKERS = 12
PIN = tuple(range(8, 32, 2))
MAX_SHARD_SECONDS = 1200.0
PER_SHARD = 20
NEW = {"P": range(150, 950), "PG": range(150, 950), "EB1": range(150, 300), "EB2": range(150, 300)}
QUANTILE = 1.0 - 0.0027


def schedule() -> list:
    """The families' chunks ordered so that the 5 % checkpoint (``budgeted.checkpoint``'s evenly
    spaced shards) holds one chunk of each family in turn; the rest follow in family order;
    checked."""
    chunks = {}
    for family, indices in NEW.items():
        idx = list(indices)
        chunks[family] = [idx[k : k + PER_SHARD] for k in range(0, len(idx), PER_SHARD)]
    n = sum(len(c) for c in chunks.values())
    probe_positions = [i for i, _ in budgeted.checkpoint(list(enumerate(range(n))))]
    slots: list = [None] * n
    families = list(NEW)
    for j, pos in enumerate(probe_positions):
        slots[pos] = (families[j % len(families)], chunks[families[j % len(families)]].pop(0))
    rest = [(f, c) for f in families for c in chunks[f]]
    for i in range(n):
        if slots[i] is None:
            slots[i] = rest.pop(0)
    rows = [(f"{f}-{c[0]:04d}", {"family": f, "indices": c}) for f, c in slots]
    probe = {arg["family"] for _, arg in budgeted.checkpoint(rows)}
    if probe != set(NEW):
        raise SystemExit(f"the checkpoint does not cover every family: {sorted(probe)}")
    return rows


def shard(arg: dict) -> bytes:
    lines = []
    for i in arg["indices"]:
        try:
            rec = d1_routes.route_one(arg["family"], i)
        except Exception as exc:  # noqa: BLE001 - recorded, never dropped
            rec = {"family": arg["family"], "index": i, "status": "ERROR", "reason": repr(exc)}
        lines.append(json.dumps(rec, sort_keys=True, default=str))
    return ("\n".join(lines) + "\n").encode()


def fingerprint() -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    for path in (
        Path(__file__),
        HERE / "ledger_a.py",
        FEAS / "d1_routes.py",
        FEAS / "forecast.py",
        ledger_a.V052 / "budgeted.py",
        ledger_a.V052 / "driver.py",
        OLD,
        ledger_a.ROOT / "calibration/v0.4/claim.yaml",
    ):
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()[:16]


def run() -> None:
    before = ledger_a.v052_ledger_sha256()
    try:
        ledger_a.check_caps(reserve_days=0.3, reserve_tokens=0)
        ledger_a.declare()
        fp = fingerprint()
        rows = schedule()
        cap = ledger_a.hard_cap(PART, WORKERS, MAX_SHARD_SECONDS)
        print(len(rows), "shards; hard cap", round(cap, 2), "CPU-h", flush=True)
        state = budgeted.execute(
            ledger_a.SECTION,
            PART,
            OUT / fp,
            shard,
            rows,
            fp,
            WORKERS,
            pin=PIN,
            max_shard_seconds=MAX_SHARD_SECONDS,
            hard_cap_hours=cap,
            units=lambda arg: len(arg["indices"]),
        )
        print(state, flush=True)
    finally:
        if ledger_a.v052_ledger_sha256() != before:
            raise SystemExit("the v0.5.2 ledger changed: refused")
    if state != "complete":
        raise SystemExit(state)


def _quantile_threshold(values: list[float]) -> tuple[float, int]:
    """The empirical 99.73 % quantile (the order statistic ceil(q n)) and how many values lie
    strictly above it."""
    v = sorted(values)
    k = min(len(v) - 1, max(0, math.ceil(QUANTILE * len(v)) - 1))
    return v[k], sum(x > v[k] for x in v)


def summarize() -> None:
    fp = fingerprint()
    rows = schedule()
    data = budgeted.assembled(
        ledger_a.SECTION,
        PART,
        OUT / fp,
        shard,
        rows,
        fp,
        WORKERS,
        pin=PIN,
        max_shard_seconds=MAX_SHARD_SECONDS,
    )
    new = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    old = [json.loads(x) for x in OLD.read_text("utf-8").splitlines() if x.strip()]
    recs = [r for r in old + new if r.get("status") == "OK" and r.get("eligible") and "dchi2" in r]
    out: dict = {
        "label": "D1's geometric route on development curves; a diagnostic, decides nothing "
        "(#217, stage A (d); #215)",
        "method_status": "not_validated",
        "fingerprint": fp,
        "curves": {"v0.5.1": len(old), "new": len(new)},
        "errors": sum(r.get("status") == "ERROR" for r in new),
        "eligible": {f: sum(r["family"] == f for r in recs) for f in ("P", "PG", "EB1", "EB2")},
        "statistics": {},
    }
    for stat in ("dchi2", "dchi2_cov"):
        per = {
            fam: [r[stat] for r in recs if r["family"] == fam and r.get(stat) is not None]
            for fam in ("P", "PG")
        }
        if not all(per.values()):
            continue
        quantiles = {fam: _quantile_threshold(v)[0] for fam, v in per.items()}
        thr = max(quantiles.values())
        block: dict = {
            "threshold": thr,
            "rule": "the larger of the P and PG 99.73 % quantiles (calibration-sample fractions)",
            "quantile_99.73": quantiles,
            "strictly_above_threshold": {fam: sum(x > thr for x in v) for fam, v in per.items()},
            "planets": {fam: len(v) for fam, v in per.items()},
        }
        for noise in ("white", "correlated", "all"):
            sel = [
                r
                for r in recs
                if r.get(stat) is not None
                and (noise == "all" or r["correlated"] == (noise == "correlated"))
            ]
            row = {}
            for fam in ("P", "PG", "EB1", "EB2"):
                vals = [r[stat] for r in sel if r["family"] == fam]
                row[fam] = {
                    "n": len(vals),
                    "flagged": sum(v > thr for v in vals),
                    "fraction": (sum(v > thr for v in vals) / len(vals)) if vals else None,
                }
            folded = [r[stat] for r in sel if r["family"] == "EB1" and r.get("folded")]
            row["EB1_folded"] = {
                "n": len(folded),
                "flagged": sum(v > thr for v in folded),
                "fraction": (sum(v > thr for v in folded) / len(folded)) if folded else None,
            }
            block[noise] = row
        block["quantiles"] = {
            fam: [
                float(
                    np.quantile(
                        [r[stat] for r in recs if r["family"] == fam and r.get(stat) is not None], q
                    )
                )
                for q in (0.5, 0.9, 0.99)
            ]
            for fam in ("P", "PG", "EB1", "EB2")
        }
        out["statistics"][stat] = block
    (HERE / "d1-geometry.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    {"run": run, "summarize": summarize}[sys.argv[1]]()
