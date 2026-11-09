"""v0.5.2 stage 2: the frozen adequacy check of the design's section 1, on development seeds.

Version 4 runs the **whole A0 round 2 schedule** (425,400 curves: the cells and counts of
``docs/validation/v0.5.1/acceptance/a0.py``, ``schedule``, for the sections of the plasmode), on the
seed label ``refute-v052-dev:adequacy``. The reference is rebuilt from these records with **version
3's family, components and per-component factor kept frozen** (``components.pkl``): the same curves
per run and no rescaling to version 4's availability, so a member of the family that version 4
fails to deliver is a member not measured, and the family fails. Each member is standardized on
version 4's own pulls. A member priced only under version 4 is counted and stays out of the family.
The complete evaluation of ``plasmode.py`` is then repeated at ``T`` = 9,000, on the new seed label
``adequacy``, under the same bound (200 datasets; one-sided Clopper-Pearson at level ``1 - 0.05/4``
reaching 0.90).

**A failure, or a run that cannot be completed, is a STOP and a prospective redesign**, recorded; it
never changes ``T``, the schedule or the reference. It certifies nothing about any target, and
pooled moments are diagnostics only. ``method_status: not_validated``.

Usage: ``scripts/launch_affinity.ps1 -Script <this file> -Arguments units|build|evaluate``.
"""

from __future__ import annotations

import hashlib
import json
import math
import pickle
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import a0v4  # noqa: E402
import budgeted  # noqa: E402
import plasmode as pm  # noqa: E402

LABEL = "refute-v052-dev:adequacy"
OUT = ROOT / ".cache/v052/s2/adequacy"
V3_TABLE = ROOT / ".cache/v052/s2/plasmode/components.pkl"
V4_TABLE = OUT / "components-v4.pkl"
TARGET = 9000
WORKERS = 12
PIN = tuple(range(8, 32, 2))
SECTIONS = ("a01", "a02", "a04", "a05", "a07", "a08")
PER_SHARD = {"a01": 96, "a02": 40, "a04": 128, "a05": 128, "a07": 128, "a08": 96}
UNITS_PART_HOURS = 75.0
EVALUATE_PART_HOURS = 20.0
V3_TABLE_SHA256 = "6d91a7616a54f4293adb165ebff5c94542917db62b26d46fe15c21ef6db1c68b"
pm.TABLE = V4_TABLE


def _dev_seed(case: str, i: int, label: str | None = None) -> int:
    return int(hashlib.sha256(f"{LABEL}:{case}:{i}".encode()).hexdigest()[:16], 16)


def schedule(section: str) -> list:
    """``v3.schedule`` with this run's seeds; the acceptance's own seeds are never made here."""
    original = a0v4.v3.c.accept_seed
    a0v4.v3.c.accept_seed = _dev_seed
    try:
        return a0v4.v3.schedule(section)
    finally:
        a0v4.v3.c.accept_seed = original


def identity(section: str, arg) -> dict:
    """The record's cell, so that a curve that gave nothing stays in its run's denominator."""
    if section == "a01":
        return {"noise": arg[0], "kind": arg[1]}
    if section in ("a02", "a04", "a07"):
        return {"noise": arg[1], "kind": arg[2], "sectors": arg[3]}
    if section == "a05":
        return dict(
            zip(("pattern", "spacing", "combo", "noise", "kind", "sectors"), arg, strict=False)
        )
    return {
        "shape": arg[0], "noise": arg[1], "kind": arg[2], "sectors": arg[3], "multiple": arg[4],
        "branch": "included",
    }  # fmt: skip


def shard_units(spec) -> bytes:
    section, args = spec
    fn = a0v4.UNIT_OF[section]
    lines = []
    for arg in args:
        try:
            rec = {**identity(section, arg), **fn(arg)}
            rec.setdefault("status", "OK")
        except Exception as exc:  # noqa: BLE001 - a failure stays in its denominator, as v0.5.1's
            rec = {**identity(section, arg), "status": "ERROR", "reason": repr(exc)[:400]}
        lines.append(json.dumps(rec, sort_keys=True))
    return ("\n".join(lines) + "\n").encode()


def shards_of(section: str) -> list:
    # shuffled by hash into the shards, so that the first 5 % sample every construction
    args = sorted(
        (arg for _, arg in schedule(section)),
        key=lambda a: hashlib.sha256(repr(a).encode()).hexdigest(),
    )
    step = PER_SHARD[section]
    return [
        (f"{section}-{i:06d}", (section, args[i : i + step])) for i in range(0, len(args), step)
    ]


def fingerprint() -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    for path in (
        Path(__file__), HERE / "a0v4.py", HERE / "driver.py", HERE / "budgeted.py",
        HERE / "plasmode.py", ROOT / "docs/validation/v0.5.1/acceptance/a0.py",
        ROOT / "docs/validation/v0.5.1/acceptance/common.py",
    ):  # fmt: skip
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()[:16]


def units() -> None:
    fp = fingerprint()
    every = {section: shards_of(section) for section in SECTIONS}
    total = sum(len(arg[1]) for shards in every.values() for _, arg in shards)
    print("curves", total, "fingerprint", fp, flush=True)
    if total != 425400:
        raise SystemExit(f"the schedule has {total} curves, not 425,400")
    weight = {s: sum(len(a[1]) for _, a in every[s]) / total for s in SECTIONS}
    budgeted.declare(
        "adequacy",
        {**{f"units-{s}": UNITS_PART_HOURS * w for s, w in weight.items()},
         "evaluate": EVALUATE_PART_HOURS},
    )  # fmt: skip
    for section, shards in every.items():
        state = budgeted.execute(
            "adequacy", f"units-{section}", OUT / f"units-{section}" / fp, shard_units, shards, fp,
            WORKERS, units=lambda a: len(a[1]), pin=PIN, max_shard_seconds=900.0,
        )  # fmt: skip
        print(section, state, flush=True)
        if state != "complete":
            raise SystemExit(f"{section}: {state}")


def records(section: str, fp: str):
    data = budgeted.assembled(
        "adequacy", f"units-{section}", OUT / f"units-{section}" / fp, shard_units,
        shards_of(section), fp, WORKERS, pin=PIN,
    )  # fmt: skip
    return [json.loads(line) for line in data.splitlines()]


def build() -> None:
    """Version 3's family and factors; version 4's pulls."""
    fp = fingerprint()
    curves: dict = {}
    not_ok = dict.fromkeys(SECTIONS, 0)
    for section in SECTIONS:
        for r in records(section, fp):
            run, parts = pm._contributions(section, r)
            row: dict = {}
            if r.get("status") == "OK":
                for member, p in parts:
                    if p is not None and math.isfinite(p):
                        row.setdefault(member, []).append(float(p))
            else:
                not_ok[section] += 1
            curves.setdefault(run, []).append(row)
    short = {repr(run): len(rows) for run, rows in curves.items() if len(rows) != pm._units(run)}
    if short:
        raise SystemExit(f"runs whose curves differ from the schedule: {short}")
    pulls: dict = {}
    for rows in curves.values():
        for row in rows:
            for member, values in row.items():
                pulls.setdefault(member, []).extend(values)
    raw = V3_TABLE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != V3_TABLE_SHA256:
        raise SystemExit("the version 3 table is not the sizing reference")
    v3_table = pickle.loads(raw)  # noqa: S301 - written by plasmode.py, in the local cache
    family = {m for comp in v3_table for m in comp["members"]}
    table, absent = [], 0
    for comp in v3_table:
        members = comp["members"]
        scale = {}
        for m in members:
            values = pulls.get(m, [])
            if len(values) > 2 and np.std(values) > 0:
                scale[m] = (float(np.mean(values)), float(np.std(values)))
            else:
                absent += 1
        index = {m: j for j, m in enumerate(members)}
        runs = []
        for run in comp["runs"]:
            rows = curves[run["key"]]
            n = np.zeros((len(rows), len(members)), dtype=np.int32)
            s1, s2 = np.zeros_like(n, dtype=float), np.zeros_like(n, dtype=float)
            for i, row in enumerate(rows):
                for m, values in row.items():
                    j = index.get(m)
                    if j is None or m not in scale:
                        continue
                    z = (np.asarray(values) - scale[m][0]) / scale[m][1]
                    n[i, j], s1[i, j], s2[i, j] = z.size, float(z.sum()), float(np.sum(z * z))
            runs.append({"key": run["key"], "n": n, "s1": s1, "s2": s2})
        table.append({"members": members, "runs": runs, "min_g": comp["min_g"]})  # v3's factor
    with V4_TABLE.open("wb") as fh:
        pickle.dump(table, fh, protocol=5)
    moments = {
        "mean_of_member_means": float(np.mean([np.mean(pulls[m]) for m in family if m in pulls])),
        "mean_of_member_sds": float(np.mean([np.std(pulls[m]) for m in family if m in pulls])),
    }
    doc = {
        "family_members": len(family),
        "family_members_without_pulls": absent,
        "priced_only_under_version_4": sum(
            1 for m in pulls if m not in family and len(pulls[m]) > 2 and "matched" not in repr(m)
        ),
        "records_not_ok": not_ok,
        "diagnostic_pooled_moments_certify_nothing": moments,
        "table_sha256": hashlib.sha256(V4_TABLE.read_bytes()).hexdigest(),
        "version_3_table_sha256": V3_TABLE_SHA256,
        "fingerprint": fp,
    }
    (OUT / "build.json").write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8")
    print(doc, flush=True)


def load_verified() -> None:
    """The rebuilt table, in each worker, only if its bytes are the recorded ones."""
    expected = json.loads((OUT / "build.json").read_text("utf-8"))["table_sha256"]
    raw = V4_TABLE.read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected:
        raise SystemExit("the rebuilt table is not the recorded one")
    pm._TABLE = pickle.loads(raw)  # noqa: S301 - written by build, verified just above


def shard_evaluate(arg) -> bytes:
    target, rep = arg
    row = pm.complete_procedure(target, rep, "adequacy")
    return json.dumps(row, sort_keys=True).encode() + b"\n"


def evaluate() -> None:
    from scipy import stats

    fp = fingerprint()
    build_doc = json.loads((OUT / "build.json").read_text("utf-8"))
    if build_doc["fingerprint"] != fp:
        raise SystemExit("the build is from other code")
    load_verified()
    shards = [(f"e-{r:03d}", (TARGET, r)) for r in range(pm.EVAL_REPS)]
    table_fp = hashlib.sha256((fp + build_doc["table_sha256"]).encode()).hexdigest()[:16]
    kwargs = {
        "pin": PIN,
        "initializer": load_verified,
        "max_shard_seconds": pm.EVAL_MAX_SHARD_SECONDS,
    }
    state = budgeted.execute(
        "adequacy", "evaluate", OUT / "evaluate" / table_fp, shard_evaluate, shards, table_fp,
        WORKERS, **kwargs,
    )  # fmt: skip
    print(state, flush=True)
    if state != "complete":
        raise SystemExit(state)
    data = budgeted.assembled(
        "adequacy", "evaluate", OUT / "evaluate" / table_fp, shard_evaluate, shards, table_fp,
        WORKERS, **kwargs,
    )  # fmt: skip
    rows = [json.loads(line) for line in data.splitlines()]
    k = sum(r["certified"] for r in rows)
    lower = float(stats.beta.ppf(1.0 - pm.EVAL_LEVEL, k, pm.EVAL_REPS - k + 1)) if k else 0.0
    doc = {
        "label": "the frozen adequacy check of version 4 (design, section 1); certifies no target",
        "method_status": "not_validated",
        "target": TARGET,
        "datasets": pm.EVAL_REPS,
        "certified": k,
        "one_sided_level": pm.EVAL_LEVEL,
        "lower_bound": lower,
        "passes": lower >= pm.EVAL_FLOOR,
        "q_min_max": [min(r["q"] for r in rows), max(r["q"] for r in rows)],
        "not_measured_datasets": sum(r["not_measured"] > 0 for r in rows),
        "failed_member_datasets": sum(r["failed_members"] > 0 for r in rows),
        "failed_aggregate_datasets": sum(r["failed_aggregate"] > 0 for r in rows),
        "degenerate_datasets": sum(r["degenerate_replicates"] >= pm.DEGENERATE_LIMIT for r in rows),
        "build": build_doc,
    }
    # one file per reference, so that a failed assessment survives a redesign
    path = HERE / f"adequacy-result-{table_fp}.json"
    path.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8")
    print(doc, flush=True)
    summary = {"certified": k, "lower_bound": lower, "file": path.name}
    if not doc["passes"]:
        budgeted.fail_gate("adequacy", summary)
        raise SystemExit("the adequacy check failed: a STOP and a prospective redesign")
    budgeted.pass_gate("adequacy", summary)


if __name__ == "__main__":
    {"units": units, "build": build, "evaluate": evaluate}[sys.argv[1]]()
