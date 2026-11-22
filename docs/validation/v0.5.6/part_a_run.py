"""v0.5.6 part A (exploratory): the labelled v0.5 battery on the drawn TOIs, the pilot first
(docs/plans/v0.5.6-plan.md; the maintainer's decision of 2026-11-21, 22:30, item 3; #218).

**What runs:** for each drawn TIC, the TESS adapter's download (SPOC 120-s light curves and pixel
files up to sector 107, into ``.cache/v056/data``), then the v0.5 battery unchanged: the C3
claim's test plan (``calibration/v0.5/claim.yaml``, its SHA-256 checked), stage 2, **without the
catalog test**, by the same calls as ``refute.packs.tess.discover.measure.chain`` (detrending,
prewhitening, search, ``attack_candidate``, coverage, the sensitivity rule, deferral, the
decisive aggregate). The chain is reproduced here, not changed, so that each test's message,
coverage and sensitivity are kept (``measure.chain`` keeps only status and severity). No code in
``src/`` changes.

**Every record** carries ``mode: exploratory`` and the limits label; outputs are never verdicts on
any TOI, never candidates in a public claim. ``method_status: not_validated``. Zero coverage stays
INCONCLUSIVE (``enforce_coverage``).

**Signal identity** (recorded, never a replacement): the found period against the TOI's at the
factors 1, 2 and 0.5 within 0.1 % (C3's tolerance), and the found epoch's offset from the TOI's
predicted transit, in hours.

**Caps** (the decision): 50 CPU-h for everything of part A, the pilot, attempts and reruns
included, in ``part-a-ledger.json``. The pilot is the first 5 TICs of each arm in draw order; its
projection to the 240 stops the run if it exceeds 50 CPU-h or 20 GB. Workers: at most 10 on
weekdays 08:00 to 18:00, else up to 20; BelowNormal priority and CPUs 8 to 31 (``pinrun``);
batches of at most 30 minutes; every target is one record file, so the run resumes.

Usage: ``part_a_run.py pilot`` then ``part_a_run.py rest``.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import math
import os
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
CLAIM = ROOT / "calibration/v0.5/claim.yaml"
DRAW = HERE / "part-a-draw.json"
LEDGER = HERE / "part-a-ledger.json"
DATA = ROOT / ".cache/v056/data"
RECORDS = ROOT / ".cache/v056/run/records"
LABEL = "WEAKENED; does not meet D1, D2, D4, T2a"
CAP_CPU_HOURS = 50.0
CAP_DISK_BYTES = 20e9
PILOT_PER_ARM = 5
BATCH_SECONDS = 30 * 60
BTJD = 2457000.0
IDENTITY_TOLERANCE = 0.001
FACTORS = (1.0, 2.0, 0.5)


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def workers() -> int:
    now = dt.datetime.now()
    business = now.weekday() < 5 and 8 <= now.hour < 18
    return 10 if business else 20


def targets() -> list[dict]:
    draw = json.loads(DRAW.read_text("utf-8"))
    if draw.get("status") != "complete":
        raise SystemExit("the draw is not complete")
    out = []
    for arm in ("planet", "open"):
        for rank, c in enumerate(draw["arms"][arm]["chosen"]):
            out.append({**c, "arm": arm, "rank": rank, "key": f"TIC-{c['tic_id']}"})
    return out


def pilot_set(all_targets: list[dict]) -> list[dict]:
    return [t for t in all_targets if t["rank"] < PILOT_PER_ARM]


def _bytes(manifest: dict) -> int:
    total = 0
    for rec in [*manifest.get("files", []), *manifest.get("pixel_files", [])]:
        path = DATA / rec["path"]
        if path.exists():
            total += path.stat().st_size
    return total


def _test(t) -> dict:
    return {
        "status": t.status.value,
        "severity": t.severity.value,
        "message": (t.message or "")[:400],
        "coverage": t.coverage,
        "coverage_unit": t.coverage_unit,
        "sensitivity": t.sensitivity,
    }


def run_one(target: dict, test_plan: dict) -> dict:
    """One TIC: download, the battery, the identity. Any failure is recorded, never hidden."""
    from refute.core.io import read_json
    from refute.core.sensitivity import enforce_sensitivity
    from refute.core.verdict import aggregate, defer_tests, enforce_coverage
    from refute.packs.tess.adapter import NoProductsError, TessAdapter, manifest_path
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.discover.measure import stage_plan
    from refute.packs.tess.params import TessTestPlan
    from refute.packs.tess.pipeline import (
        attack_candidate,
        expected_by_role,
        global_prewhitening,
        matching_factor,
    )
    from refute.packs.tess.power import registry_for
    from refute.packs.tess.search import search_period

    started, wall = time.process_time(), time.time()
    rec = {
        "target_key": target["key"],
        "tic_id": target["tic_id"],
        "toi": target["toi"],
        "arm": target["arm"],
        "rank": target["rank"],
        "mode": "exploratory",
        "limits_label": LABEL,
        "method_status": "not_validated",
    }
    try:
        plan_dict = stage_plan(test_plan, 2)
        plan = TessTestPlan.model_validate(plan_dict)
        tgt = {"key": target["key"], "tic_id": int(target["tic_id"])}
        try:
            TessAdapter().fetch(tgt, plan_dict, DATA)
        except NoProductsError as exc:
            rec.update({"status": "MISSING_PRODUCTS", "reason": str(exc)})
            return rec
        manifest = read_json(manifest_path(DATA, int(target["tic_id"])))
        rec["bytes"] = _bytes(manifest)
        rec["light_curve_sectors"] = sorted({int(f["sector"]) for f in manifest["files"]})
        rec["pixel_file_sectors"] = sorted({int(f["sector"]) for f in manifest["pixel_files"]})
        rec["listed_sectors"] = target["sectors"]
        data = TessAdapter().load(tgt, plan_dict, DATA)
        flat = detrend(data.lc, plan.detrend)
        pw, searched = global_prewhitening(data, plan, flat)
        search = search_period(searched, plan.search)
        gauntlet = attack_candidate(data, search.candidate, plan, None, None, pw)
        tests = enforce_coverage(gauntlet.tests)
        tests = enforce_sensitivity(tests, registry_for(plan))
        tests, deferred = defer_tests(tests, dict(plan.discovery.stages), 2)
        decisive, _ = expected_by_role(plan, False)
        verdict, reason = aggregate([t for t in tests if t.name in decisive], expected=decisive)
        cand = gauntlet.candidate
        found = None if cand is None else float(cand.period)
        published = float(target["period_days"])
        factor = matching_factor(published, found, FACTORS, IDENTITY_TOLERANCE)
        offset_hours = None
        if cand is not None:
            epoch = float(target["epoch_bjd"]) - BTJD
            phase = ((float(cand.t0) - epoch) / published) % 1.0
            offset_hours = (min(phase, 1.0 - phase)) * published * 24.0
        rec.update(
            {
                "status": "OK",
                "candidate": None
                if cand is None
                else {"period_days": found, "t0_btjd": float(cand.t0), "snr": float(cand.snr)},
                "tests": {t.name: _test(t) for t in tests},
                "decisive": list(decisive),
                "deferred": deferred,
                "outcome": verdict.value,
                "outcome_reason": reason,
                "identity": {
                    "toi_period_days": published,
                    "found_period_days": found,
                    "factor": factor,
                    "epoch_offset_hours": offset_hours,
                    "toi_duration_hours": float(target["duration_hours"]),
                    "matched": factor == 1.0
                    and offset_hours is not None
                    and offset_hours <= float(target["duration_hours"]) / 2.0,
                },
            }
        )
    except Exception as exc:  # noqa: BLE001 - recorded, never hidden
        rec.update({"status": "ERROR", "reason": f"{type(exc).__name__}: {exc}",
                    "trace": traceback.format_exc()[-1500:]})  # fmt: skip
    finally:
        rec["cpu_seconds"] = time.process_time() - started
        rec["wall_seconds"] = time.time() - wall
    return rec


def _plain(value):
    """numpy scalars and other objects in a JSON record."""
    return value.item() if hasattr(value, "item") else str(value)


def _ledger() -> dict:
    if LEDGER.exists():
        return json.loads(LEDGER.read_text("utf-8"))
    return {"cap_cpu_hours": CAP_CPU_HOURS, "cap_disk_bytes": CAP_DISK_BYTES, "batches": []}


def _spent() -> tuple[float, int, int]:
    cpu, nbytes, n = 0.0, 0, 0
    for f in RECORDS.glob("*.json"):
        r = json.loads(f.read_text("utf-8"))
        cpu += r.get("cpu_seconds", 0.0)
        nbytes += r.get("bytes", 0)
        n += 1
    return cpu / 3600.0, nbytes, n


def run(selection: list[dict], label: str) -> None:
    claim_text = CLAIM.read_bytes()
    import yaml

    test_plan = yaml.safe_load(claim_text.decode("utf-8"))["test_plan"]
    RECORDS.mkdir(parents=True, exist_ok=True)
    DATA.mkdir(parents=True, exist_ok=True)
    todo = [t for t in selection if not (RECORDS / f"{t['key']}.json").exists()]
    ledger = _ledger()
    spent, _, done = _spent()
    if spent >= CAP_CPU_HOURS:
        raise SystemExit(f"the cap of {CAP_CPU_HOURS} CPU-h is reached: STOP")
    n = workers()
    batch_start = time.time()
    with ProcessPoolExecutor(max_workers=n) as pool:
        futures = {pool.submit(run_one, t, test_plan): t for t in todo}
        for fut in as_completed(futures):
            rec = fut.result()
            path = RECORDS / f"{rec['target_key']}.json"
            tmp = path.with_name(path.name + ".tmp")
            tmp.write_text(json.dumps(rec, indent=1, default=_plain), "utf-8")
            os.replace(tmp, path)
            spent, nbytes, done = _spent()
            print(rec["target_key"], rec["status"], rec.get("outcome"), round(rec["cpu_seconds"]),
                  f"spent {spent:.2f} CPU-h", flush=True)  # fmt: skip
            if spent >= CAP_CPU_HOURS or time.time() - batch_start > BATCH_SECONDS:
                for f in futures:
                    f.cancel()
                break
    spent, nbytes, done = _spent()
    ledger["batches"].append(
        {
            "label": label,
            "ended_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "workers": n,
            "claim_sha256": sha256(claim_text),
            "code_sha256": sha256(Path(__file__).read_bytes()),
            "records": done,
            "cpu_hours_spent": round(spent, 4),
            "bytes": nbytes,
        }
    )
    tmp = LEDGER.with_name(LEDGER.name + ".tmp")
    tmp.write_text(json.dumps(ledger, indent=1) + "\n", "utf-8", newline="\n")
    os.replace(tmp, LEDGER)


def projection(total: int) -> dict:
    recs = [json.loads(f.read_text("utf-8")) for f in RECORDS.glob("*.json")]
    cpu = sum(r.get("cpu_seconds", 0.0) for r in recs) / 3600.0
    nbytes = sum(r.get("bytes", 0) for r in recs)
    k = len(recs)
    per_cpu, per_bytes = (cpu / k, nbytes / k) if k else (math.nan, math.nan)
    return {
        "records": k,
        "cpu_hours": cpu,
        "bytes": nbytes,
        "cpu_hours_per_target": per_cpu,
        "bytes_per_target": per_bytes,
        "projected_cpu_hours": per_cpu * total,
        "projected_bytes": per_bytes * total,
        "stop": per_cpu * total > CAP_CPU_HOURS or per_bytes * total > CAP_DISK_BYTES,
    }


def main(step: str) -> None:
    all_targets = targets()
    if step == "pilot":
        run(pilot_set(all_targets), "pilot")
        p = projection(len(all_targets))
        ledger = _ledger()
        ledger["pilot_projection"] = p
        tmp = LEDGER.with_name(LEDGER.name + ".tmp")
        tmp.write_text(json.dumps(ledger, indent=1) + "\n", "utf-8", newline="\n")
        os.replace(tmp, LEDGER)
        print(json.dumps(p, indent=1))
    elif step == "rest":
        p = _ledger().get("pilot_projection")
        if p is None or p["stop"]:
            raise SystemExit("no pilot projection, or it said STOP")
        run(all_targets, "rest")
    else:
        raise SystemExit("usage: part_a_run.py pilot|rest")


if __name__ == "__main__":
    main(sys.argv[1])
