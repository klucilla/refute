"""v0.5.3 stage B, B0b: D1's pre-registered infeasibility test for EB1 and EB2 (#217; the
maintainer's decision of 2026-11-11, comment 6804003610; `docs/plans/v0.5.3-stageB0b-design.md`).
**Development seeds only; a diagnostic under B0's stated assumptions, never a verdict.**
``method_status: not_validated``.

B0's bound (``d1_bound.py``, imported unchanged) on new seeds ``refute-v053-b0b:<family>:<i>``,
i in 0 to 399, EB1 and EB2: the same generator, candidate generation, eligibility, oracle, stars
and summary. Only the seeds, the bootstrap seed, the output folder and the reading change.

**The reading** (fixed before the run; the design's section 2): (I) when, for EB1 or EB2, with the
catalog star at both levels 0.0027 and 0.05, the expected non-rejected count at the C1'
projection is above D1's allowance and the median cohort's pass probability is below 0.05;
(D) no conclusion when a record is an ERROR or a family is not ``valid`` (B0's rule); (N)
otherwise.

Usage: ``smoke``, ``run`` (through ``scripts/launch_affinity.ps1``), then ``summarize``
(``d1-infeasibility.json``).
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import d1_bound  # noqa: E402,I001  (imports ledger_b first, which points budgeted at stage B's)
from d1_bound import budgeted, ledger_b  # noqa: E402

DESIGN = ledger_b.ROOT / "docs/plans/v0.5.3-stageB0b-design.md"
PART = "b0_infeasibility"
SOURCE_PART = "b0_reserve"
ALLOCATION = 4.0
OUT = ledger_b.ROOT / ".cache/v053/stageB/d1-infeasibility"
BOOTSTRAP_SEED = 20261112
LEVELS = (0.0027, 0.05)  # the criterion must hold at both
PASS_PROBABILITY = 0.05
SMOKE_INDEX = 100000

_B0_SEED = d1_bound.seed


def seed(family: str, i: int) -> int:
    return int(hashlib.sha256(f"refute-v053-b0b:{family}:{i}".encode()).hexdigest()[:16], 16)


# B0's ``bound_one`` reads the module's ``seed``: pointed at B0b's seeds here, in this process and
# in every worker, which imports this module to run ``shard``
d1_bound.seed = seed


def check_seeds() -> None:
    """None of B0b's seeds is one of B0's (both families, both index ranges)."""
    ours = {seed(f, i) for f in d1_bound.FAMILIES for i in range(d1_bound.SIZE)}
    theirs = {_B0_SEED(f, i) for f in d1_bound.FAMILIES for i in range(d1_bound.SIZE)}
    theirs |= {_B0_SEED(f, SMOKE_INDEX) for f in d1_bound.FAMILIES}
    if len(ours) != len(d1_bound.FAMILIES) * d1_bound.SIZE or ours & theirs:
        raise SystemExit("B0b's seeds are not new and distinct: refused")


def shard(arg: dict) -> bytes:
    return d1_bound.shard(arg)


def fingerprint() -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    for path in (
        Path(__file__),
        HERE / "d1_bound.py",
        HERE / "ledger_b.py",
        DESIGN,
        d1_bound.FEAS / "d1_routes.py",
        d1_bound.FEAS / "forecast.py",
        ledger_b.V052 / "budgeted.py",
        ledger_b.V052 / "driver.py",
        ledger_b.ROOT / "calibration/v0.4/claim.yaml",
    ):
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()[:16]


def ensure_part() -> None:
    """The design's section 4: 4 CPU-h from ``b0_reserve`` to ``b0_infeasibility``, once."""
    if PART not in ledger_b._rows():
        ledger_b.transfer(SOURCE_PART, PART, ALLOCATION, "B0b (#217, comment 6804003610)")
    ledger_b.declare()


def smoke() -> None:
    """One binary outside the measured range, charged by its processor time."""
    check_seeds()
    ledger_b.check_caps("b0b smoke", reserve_days=0.05, reserve_tokens=0)
    if ledger_b.charges_left() < 0.01:
        raise SystemExit("too little of the charges' room left for the smoke: a STOP")
    started = time.process_time()
    try:
        print(shard({"family": "EB1", "indices": [SMOKE_INDEX]}).decode(), flush=True)
    finally:
        used = time.process_time() - started
        ledger_b.charge(
            f"b0_b0b_smoke_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
            used / 3600.0,
            f"d1_infeasibility.smoke: EB1 index {SMOKE_INDEX}, outside the measured 0 to 399; "
            f"process time {used:.1f} s",
        )


def run() -> None:
    check_seeds()
    before = ledger_b.v052_ledger_sha256()
    try:
        ledger_b.check_caps("b0b run", reserve_days=0.3, reserve_tokens=0)
        ensure_part()
        fp = fingerprint()
        rows = d1_bound.schedule()
        ledger_b.refuse_new_identity(PART, fp, rows)
        cap = ledger_b.hard_cap(PART, d1_bound.WORKERS, d1_bound.MAX_SHARD_SECONDS)
        print(len(rows), "shards; hard cap", round(cap, 2), "CPU-h", flush=True)
        state = budgeted.execute(
            ledger_b.SECTION,
            PART,
            OUT / fp,
            shard,
            rows,
            fp,
            d1_bound.WORKERS,
            pin=d1_bound.PIN,
            max_shard_seconds=d1_bound.MAX_SHARD_SECONDS,
            hard_cap_hours=cap,
            units=lambda arg: len(arg["indices"]),
        )
        print(state, flush=True)
    finally:
        if ledger_b.v052_ledger_sha256() != before:
            raise SystemExit("the v0.5.2 ledger changed: refused")
    if state != "complete":
        raise SystemExit(state)


def criterion(fam: dict) -> dict:
    """The design's section 2, for one valid family: the catalog star at both levels."""
    k = fam["d1_allowance"]
    per = {}
    for alpha in LEVELS:
        a = fam["stars"]["catalog"]["alphas"][str(alpha)]
        per[str(alpha)] = {
            "expected_above_allowance": a["expected_non_rejected_at_projection"] > k,
            "median_pass_probability_below": a["pass_probability_median"] < PASS_PROBABILITY,
        }
    met = all(all(v.values()) for v in per.values())
    return {"levels": per, "met": met}


def outcome(recs: list[dict], fams: dict) -> str:
    if any(r.get("status") == "ERROR" for r in recs) or not all(f["valid"] for f in fams.values()):
        return "D"
    return "I" if any(f["criterion"]["met"] for f in fams.values()) else "N"


def summarize() -> None:
    ledger_b.check_caps("b0b summarize", reserve_days=0.05, reserve_tokens=0)
    if ledger_b.charges_left() < d1_bound.SUMMARIZE_RESERVE_HOURS:
        raise SystemExit("too little of the charges' room left for the summary: a STOP")
    started = time.process_time()
    try:
        _summarize()
    finally:
        used = time.process_time() - started
        ledger_b.charge(
            f"b0_b0b_summarize_{time.strftime('%Y%m%dT%H%M%SZ', time.gmtime())}",
            used / 3600.0,
            f"d1_infeasibility.summarize: process time {used:.1f} s",
        )


def _summarize() -> None:
    check_seeds()
    fp = fingerprint()
    rows = d1_bound.schedule()
    data = budgeted.assembled(
        ledger_b.SECTION, PART, OUT / fp, shard, rows, fp, d1_bound.WORKERS,
        pin=d1_bound.PIN, max_shard_seconds=d1_bound.MAX_SHARD_SECONDS,
    )  # fmt: skip
    recs = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    fams = {f: d1_bound._family_summary(recs, f, rng) for f in d1_bound.FAMILIES}
    for f in fams.values():
        # B0's own A/B/C fields are B0's reading, not B0b's: removed to avoid a second reading
        f.pop("no_room_star_known", None)
        f.pop("room_catalog", None)
        if f["valid"]:
            f["criterion"] = criterion(f)
    out = {
        "label": "D1's pre-registered infeasibility test for EB1 and EB2 on new development "
        "seeds, a diagnostic under B0's stated assumptions (#217, stage B, B0b); the reading "
        "fixed in docs/plans/v0.5.3-stageB0b-design.md, section 2",
        "method_status": "not_validated",
        "fingerprint": fp,
        "levels": list(LEVELS),
        "errors": sum(r.get("status") == "ERROR" for r in recs),
        "families": fams,
        "outcome": outcome(recs, fams),
        "cpu_seconds_of_the_records": sum(r.get("cpu_seconds", 0.0) for r in recs),
    }
    path = HERE / "d1-infeasibility.json"
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8")
    print(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    # every ledger writer holds the ledger for its whole run (Codex's round 1 of B0b)
    with ledger_b.Exclusive(f"d1_infeasibility {sys.argv[1]}"):
        {"smoke": smoke, "run": run, "summarize": summarize}[sys.argv[1]]()
