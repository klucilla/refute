"""v0.5.2 stage 2: a development forecast of T2a with battery version 4, paired with v0.4 and
version 3 on the same injections (the maintainer's decisions of 2026-11-09, item 2, and
2026-11-10, items 1 and 2; #216; Codex's round 1 on this forecast). **A forecast; it decides
nothing.** ``method_status: not_validated``. The v0.5 C2 records are development data
(``docs/plans/v0.5.1-plan.md``); nothing here touches them, and no result clears the adequacy
gate.

**The estimand, frozen.** T2a's own denominator in v0.5's C2 records (``c2.summarize``): the
injections into hosts whose original curve did not pass the v0.4 gate, recovered by the v0.4
battery, 615 injections in 84 hosts; its v0.4 kept fraction, 613/615, fixes the minimum at
613/615 - 0.10. **The sample, frozen before any outcome:** seeded
(``refute-v052-dev:forecast-t2a``), without replacement, stratified by the host's number of
120-s light-curve files (2 to 4, 5 to 20, above 20: the selector's two refusals), 40, 40 and 30
injections; each stratum is weighted back by its population count. Unavailable outcomes (a
changed input, a failed download, an error, a reconstruction that does not match v0.4) stay in
the sample as unknown, bounded pessimistically and optimistically; they are never replaced.

**The inputs, authenticated.** The v0.4 stage-1 dossiers (sealed; ``c2.references`` refuses them
unless their recorded SHA-256 hold) give each host's light-curve files, stellar parameters and
neighbours. The FITS files are downloaded again by their recorded URLs into
``.cache/v052/s2/t2a-cache`` (transient rule: 5 attempts, 120 s) and each must have its recorded
SHA-256; the cache manifest is the dossier's, so no catalogue is queried again.
``t2a-fetch.json`` records the URLs, sizes, SHA-256 and retrieval times.

**Each injection.** Rebuilt with ``c2.tasks_for`` (the v0.4 R_inj seeds); the candidate is
generated once, as ``paired.paired_chain`` does, and each battery attacks it through
``paired._outcome`` at stage 1 with the v0.4 claim's catalogs. The v0.4 battery's record is
compared with its v0.4 measurement by ``c2.compat_problems`` (candidate, tests, verdicts, gate,
injection, recovery); a difference makes the injection unknown. Then version 3, and version 4
twice: **A** as built (the selector not certified; the refusal above 20 sectors), **C** a
counterfactual with the selector treated as certified and the refusal lifted (no certification
evidence is implied). **B**, certified with the refusal, equals C for hosts of at most 20 loaded
sectors and A above 20, since the refusal is checked first and acts the same way; for at most 4
sectors A equals C. Every battery must attack the same final candidate.

**The decision rule of the forecast, frozen.** With the stratified finite-population interval
(simultaneous two-sided hypergeometric intervals per stratum at 0.05/3, combined by population
counts, unknowns pessimistic for the lower end and optimistic for the upper end): FAIL when the
point estimate (unknowns left out) is below the minimum, PASS only when the lower end reaches
it, otherwise UNRESOLVED. A FAIL of the production configuration (A) is a STOP, written to the
budget ledger as the failed gate ``planet_forecast``; a favourable C or B does not override A.

Usage: ``fetch`` (network, one process, logged), then ``run`` through
``scripts/launch_affinity.ps1`` after the D2/D4 part, then ``summarize``
(``forecast-t2a.json``).
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
import urllib.request
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(HERE))
import budgeted  # noqa: E402

LABEL = "refute-v052-dev:forecast-t2a"
OUT = ROOT / ".cache/v052/s2/forecast-t2a"
CACHE = ROOT / ".cache/v052/s2/t2a-cache"
C2_RECORDS = ROOT / ".cache/v05/calibration/c2/records.jsonl"
C2_FETCH = ROOT / ".cache/v05/calibration/c2-fetch.json"
V04_STEP = ROOT / "calibration/v0.4"
STRATA = ("2_to_4", "5_to_20", "above_20")
SAMPLE = {"2_to_4": 40, "5_to_20": 40, "above_20": 30}
WORKERS = 12
PIN = tuple(range(8, 32, 2))
SECTION, PART = "remaining_work_packages", "forecast_t2a"
FORECAST_CAP_HOURS = 25.0  # the maintainer, 2026-11-10 (second set): the whole forecast
D2D4_PART = "forecast_d2_d4"
DIAGNOSIS_PART = "forecast_diagnosis"
MAX_SHARD_SECONDS = 1700.0  # inside the 30-minute batch; a 20-sector host takes about 25 minutes
# Decided after one smoke injection (31 sectors: 2,364 CPU-seconds, 39 minutes) and before any
# outcome of the run: an injection above 20 sectors outlasts the maintainer's 30-minute batch, so
# that stratum is not run; its A and B follow from the refusal rule, its v3 and C stay unknown
MEASURED_STRATA = ("2_to_4", "5_to_20")
ATTEMPTS, WAIT_SECONDS = 5, 120.0
ALPHA = 0.05
KEPT = ("SURVIVED", "WEAKENED")


def stratum(n_files: int) -> str:
    return "above_20" if n_files > 20 else "5_to_20" if n_files >= 5 else "2_to_4"


def population() -> list[dict]:
    """T2a's denominator, as ``c2.summarize`` counts it."""
    recs = [json.loads(x) for x in C2_RECORDS.read_text("utf-8").splitlines() if x.strip()]
    own = {
        r["target_key"]
        for r in recs
        if r["kind"] == "original" and r.get("status") == "OK" and r["chain"]["v04"]["gate_passed"]
    }
    files = json.loads(C2_FETCH.read_text("utf-8"))["files"]
    rows = []
    for r in recs:
        if r["kind"] != "injection" or r.get("status") != "OK" or r["target_key"] in own:
            continue
        if not (r.get("recovery") or {}).get("recovered"):
            continue
        n = len(files.get(r["target_key"]) or [])
        rows.append(
            {
                "key": r["target_key"],
                "slot": int(r["slot"]),
                "stratum": stratum(n),
                "v04_stage": r["chain"]["v04"]["stage_verdict"],
            }
        )
    return sorted(rows, key=lambda x: (x["key"], x["slot"]))


def sample(rows: list[dict]) -> list[dict]:
    out = []
    for s in STRATA:
        members = [r for r in rows if r["stratum"] == s]
        seed = int(hashlib.sha256(f"{LABEL}:sample:{s}".encode()).hexdigest()[:16], 16)
        pick = np.random.default_rng(seed).choice(
            len(members), size=min(SAMPLE[s], len(members)), replace=False
        )
        out += [members[i] for i in sorted(pick.tolist())]
    return out


def targets() -> dict[str, dict]:
    from refute.packs.tess.calib05.steps import c2_targets

    return {t["key"]: t for t in c2_targets(ROOT)}


def _download(url: str, dest: Path) -> str | None:
    """One file by its recorded URL, atomically; the transient rule; returns an error or None."""
    error = None
    for attempt in range(ATTEMPTS):
        try:
            part = dest.with_suffix(dest.suffix + ".part")
            with urllib.request.urlopen(url, timeout=300) as response:  # noqa: S310 - MAST URL
                part.write_bytes(response.read())
            part.replace(dest)
            return None
        except Exception as exc:  # noqa: BLE001 - transient: retried, then recorded
            error = f"{type(exc).__name__}: {exc}"
            if attempt + 1 < ATTEMPTS:
                time.sleep(WAIT_SECONDS)
    return error


def fetch() -> None:
    """The sampled hosts' FITS files again, checked against the sealed v0.4 dossiers."""
    from refute.core.hashing import sha256_file
    from refute.packs.tess.calib05 import c2
    from refute.packs.tess.discover.claim import TESS_EB_CACHE_PATH
    from refute.packs.tess.discover.pilot import TESS_EB_STATIC, static_tess_eb

    dossiers, _ = c2.references(ROOT)  # refused unless the sealed SHA-256 hold
    eb = CACHE / TESS_EB_CACHE_PATH
    if not eb.exists():
        eb.parent.mkdir(parents=True, exist_ok=True)
        eb.write_bytes(static_tess_eb(ROOT / TESS_EB_STATIC["path"], TESS_EB_STATIC))
    hosts = sorted({r["key"] for r in sample(population())})
    report: dict = {"source": "the sealed v0.4 stage-1 dossiers' data manifests", "hosts": {},
                    "changed": {}, "failed": {}}  # fmt: skip
    folder = CACHE / "files"
    folder.mkdir(parents=True, exist_ok=True)
    for key in hosts:
        manifest = json.loads(json.dumps(dossiers[key]["manifest"]))
        records, problems = [], []
        for f in manifest["files"]:
            dest = folder / f["name"]
            if not dest.exists() or sha256_file(dest) != f["sha256"]:
                error = _download(f["url"], dest)
                if error:
                    problems.append(f"{f['name']}: {error}")
                    continue
            got = sha256_file(dest)
            if got != f["sha256"]:
                problems.append(f"{f['name']}: other bytes")
            records.append(
                {"name": f["name"], "url": f["url"], "bytes": dest.stat().st_size, "sha256": got,
                 "retrieved_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
            )  # fmt: skip
            f["path"] = dest.relative_to(CACHE).as_posix()
            f["format"] = "spoc-fits"
        report["hosts"][key] = records
        if any("other bytes" in p for p in problems):
            report["changed"][key] = problems
        elif problems:
            report["failed"][key] = problems
        print(key, len(records), "ok" if not problems else "problem", flush=True)
    report["bytes"] = sum(f["bytes"] for files in report["hosts"].values() for f in files)
    (HERE / "t2a-fetch.json").write_text(
        json.dumps(report, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    manifests()


def manifests() -> None:
    """The cache manifests of the authenticated hosts, built from the sealed dossiers' manifests
    in the adapter's cache format (``refute-tess-fetch-2``; the dossier's own schema is a report
    format the loader refuses). No network: the files are the ones ``fetch`` checked."""
    from refute.core.io import write_json
    from refute.packs.tess.adapter import FETCH_SCHEMA, manifest_path
    from refute.packs.tess.calib05 import c2

    dossiers, _ = c2.references(ROOT)
    fetched = json.loads((HERE / "t2a-fetch.json").read_text("utf-8"))
    excluded = set(fetched["changed"]) | set(fetched["failed"])
    by_key = targets()
    for key in sorted(set(fetched["hosts"]) - excluded):
        manifest = json.loads(json.dumps(dossiers[key]["manifest"]))
        tic = int(by_key[key]["tic_id"])
        for f in manifest["files"]:
            f["path"] = f"files/{f['name']}"
            f["format"] = "spoc-fits"
        manifest.update(schema=FETCH_SCHEMA, tic_id=tic, target_key=f"TIC-{tic}", pixel_files=[])
        path = manifest_path(CACHE, tic)
        path.parent.mkdir(parents=True, exist_ok=True)
        write_json(path, manifest)


def _plans():
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.calib051.plans import pair, v051_plan
    from refute.packs.tess.discover.measure import stage_plan
    from refute.packs.tess.params import TessTestPlan

    raw = v04_test_plan(ROOT)
    staged = stage_plan(raw, 1)
    p04, p3 = pair(staged)
    out = {"v04": p04, "v3": p3}
    for name, certified in (("v4A", False), ("v4C", True)):
        d = v051_plan(staged)
        d["discovery"]["version"] = 4
        d["v052"] = {"selector_certified": certified}
        out[name] = TessTestPlan.model_validate(d)
    return raw, staged, out


def _outcome(data, cand, plan, catalogs, scan, pw) -> tuple[dict, dict | None]:
    """``paired._outcome`` at stage 1, and the version-4 sector selection of its gauntlet."""
    from refute.packs.tess.discover import paired

    seen = []
    original = paired.attack_candidate

    def spy(*args, **kwargs):
        g = original(*args, **kwargs)
        seen.append(g)
        return g

    paired.attack_candidate = spy
    try:
        out = paired._outcome(data, cand, plan, 1, catalogs, scan, pw)
    finally:
        paired.attack_candidate = original
    selection = None
    for t in seen[0].tests:
        sel = t.metrics.get("sector_selection")
        if sel:
            selection = {k: sel.get(k) for k in ("original", "chosen", "contributing", "refused")}
            break
    return out, selection


def _brief(out: dict, selection: dict | None, plan) -> dict:
    from refute.packs.tess.pipeline import expected_by_role

    decisive, _ = expected_by_role(plan, True)
    return {
        "stage_verdict": out["stage_verdict"],
        "candidate": out["candidate"],
        "tests": out["tests"],
        "deferred": out["deferred"],
        "decisive": sorted(decisive),
        "selection": selection,
    }


def one(row: dict) -> dict:
    from refute.packs.tess import battery_v52
    from refute.packs.tess.adapter import TessAdapter
    from refute.packs.tess.calib05 import c2
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.discover import injection as inj
    from refute.packs.tess.discover.measure import load_catalogs
    from refute.packs.tess.pipeline import global_prewhitening
    from refute.packs.tess.search import search_period

    started = time.process_time()
    rec: dict = {"key": row["key"], "slot": row["slot"], "stratum": row["stratum"]}
    target = targets()[row["key"]]
    raw, staged, plans = _plans()
    randomness = json.loads((V04_STEP / "runs" / "r_inj.json").read_text("utf-8"))["beacon"][
        "randomness"
    ]
    catalog = ((V04_STEP / "eb_catalog.csv").as_posix(),)
    scan_path = (V04_STEP / "eb_catalog_scan.json").as_posix()
    tasks = c2.tasks_for(target, raw, CACHE, randomness, catalog, scan_path)
    task = next(t for t in tasks if t.kind == "injection" and t.slot == row["slot"])
    base = TessAdapter().load(target, staged, CACHE)
    star = base.star
    drawn = inj.draw_injections(
        task.seed, task.k, inj.first_time(base),
        star.radius_rsun if star else None, star.logg_cgs if star else None,
    )[task.slot]  # fmt: skip
    data = inj.inject(base, drawn)
    rec["sectors"] = int(np.unique(data.lc.sector).size)
    catalogs, scan = load_catalogs(catalog, scan_path, CACHE)
    p04 = plans["v04"]
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    v04, _ = _outcome(data, cand, p04, catalogs, scan, pw)
    _, references = c2.references(ROOT)
    mine = {
        "kind": "injection", "status": "OK", "chain": {"v04": v04},
        "injection": drawn.to_dict(),
        "recovery": inj.recovery(drawn, v04["candidate"], v04["gate_passed"]),
    }  # fmt: skip
    rec["compat_problems"] = c2.compat_problems(
        mine, references[f"{row['key']}/injection/{row['slot']}"]
    )
    rec["v04"] = _brief(v04, None, p04)
    for name in ("v3", "v4A"):
        out, sel = _outcome(data, cand, plans[name], catalogs, scan, pw)
        rec[name] = _brief(out, sel, plans[name])
    if rec["sectors"] <= battery_v52.MAX_SELECTED_SECTORS:
        rec["v4C"] = rec["v4A"]
    else:
        saved = battery_v52.MAX_ORIGINAL_SECTORS
        battery_v52.MAX_ORIGINAL_SECTORS = 10**6  # this forecast only: the refusal lifted
        try:
            out, sel = _outcome(data, cand, plans["v4C"], catalogs, scan, pw)
        finally:
            battery_v52.MAX_ORIGINAL_SECTORS = saved
        rec["v4C"] = _brief(out, sel, plans["v4C"])
    rec["v4B"] = rec["v4C"] if rec["sectors"] <= battery_v52.MAX_ORIGINAL_SECTORS else rec["v4A"]
    if any(rec[b]["candidate"] != rec["v04"]["candidate"] for b in ("v3", "v4A", "v4C")):
        raise ValueError("the batteries did not attack the same final candidate")
    rec["status"] = "OK"
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def shard(row: dict) -> bytes:
    try:
        rec = one(row)
    except Exception as exc:  # noqa: BLE001 - recorded as unknown, never dropped
        rec = {**{k: row[k] for k in ("key", "slot", "stratum")}, "status": "ERROR",
               "reason": repr(exc)}  # fmt: skip
    return json.dumps(rec, sort_keys=True).encode() + b"\n"


def shards() -> list:
    fetched = json.loads((HERE / "t2a-fetch.json").read_text("utf-8"))
    excluded = set(fetched["changed"]) | set(fetched["failed"])
    return [
        (f"t-{r['key']}-{r['slot']:02d}", r)
        for r in sample(population())
        if r["key"] not in excluded and r["stratum"] in MEASURED_STRATA
    ]


def fingerprint() -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    for path in (Path(__file__), HERE / "t2a-fetch.json", HERE / "budgeted.py", HERE / "driver.py"):
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()[:16]


def _forecast_used() -> float:
    """Everything the forecast has consumed: its parts, every attempt, and its charged smokes."""
    book = budgeted.load()
    parts = book["sections"][SECTION]["parts"]
    total = sum(c["hours"] for c in book.get("charges", []) if c["name"].startswith("forecast"))
    for part in (D2D4_PART, DIAGNOSIS_PART, PART):
        row = parts.get(part, {})
        total += row.get("spent_hours", 0.0) + sum(
            a["spent_hours"] for a in row.get("attempts", [])
        )
    return total


def run() -> None:
    parts = budgeted.load()["sections"][SECTION]["parts"]
    if "projection_hours" not in parts.get(D2D4_PART, {}) or parts[D2D4_PART].get(
        "unresolved_stop"
    ):
        raise SystemExit("the D2/D4 part has not completed: the forecast's parts run in turn")
    fp = fingerprint()
    cap = FORECAST_CAP_HOURS - _forecast_used() + parts.get(PART, {}).get("spent_hours", 0.0)
    print("hard cap", round(cap, 2), "CPU-h", flush=True)
    state = budgeted.execute(
        SECTION, PART, OUT / fp, shard, shards(), fp, WORKERS, pin=PIN,
        max_shard_seconds=MAX_SHARD_SECONDS, hard_cap_hours=cap,
    )  # fmt: skip
    print(state, flush=True)
    if state != "complete":
        raise SystemExit(state)


def _hypergeometric(k: int, n: int, big_n: int, alpha: float) -> tuple[int, int]:
    """Two-sided exact interval for the population count of kept injections in one stratum."""
    from scipy import stats

    low = min(
        (K for K in range(big_n + 1) if stats.hypergeom.sf(k - 1, big_n, K, n) > alpha / 2),
        default=0,
    )
    high = max(
        (K for K in range(big_n + 1) if stats.hypergeom.cdf(k, big_n, K, n) > alpha / 2),
        default=big_n,
    )
    return low, high


def summarize() -> None:
    fp = fingerprint()
    data = budgeted.assembled(
        SECTION, PART, OUT / fp, shard, shards(), fp, WORKERS, pin=PIN,
        max_shard_seconds=MAX_SHARD_SECONDS,
    )  # fmt: skip
    got = {(r["key"], r["slot"]): r for r in map(json.loads, data.decode().splitlines()) if r}
    rows = population()
    drawn = sample(rows)
    counts = {s: sum(r["stratum"] == s for r in rows) for s in STRATA}
    v04_population = sum(r["v04_stage"] in KEPT for r in rows)
    minimum = v04_population / len(rows) - 0.10
    known, unknown = {}, Counter()
    for r in drawn:
        rec = got.get((r["key"], r["slot"]))
        if r["stratum"] not in MEASURED_STRATA:
            unknown[f"{r['stratum']}: not run (an injection outlasts a 30-minute batch)"] += 1
            continue
        if rec is None or rec.get("status") != "OK" or rec.get("compat_problems"):
            reason = "not run (input)" if rec is None else (
                "error" if rec.get("status") != "OK" else "v0.4 does not reproduce"
            )  # fmt: skip
            unknown[f"{r['stratum']}: {reason}"] += 1
            continue
        known[(r["key"], r["slot"])] = rec
    out: dict = {
        "label": "forecast, decides nothing (#216): T2a with battery version 4",
        "method_status": "not_validated",
        "population": len(rows),
        "strata_population": counts,
        "sample": {s: sum(r["stratum"] == s for r in drawn) for s in STRATA},
        "unknown": dict(unknown),
        "v04_kept_population": f"{v04_population}/{len(rows)}",
        "minimum": minimum,
        "rule": "FAIL if the point estimate is below the minimum; PASS only if the interval's "
        "lower end reaches it; otherwise UNRESOLVED. A's FAIL is a STOP.",
        "batteries": {},
    }

    def outcome(r: dict, b: str) -> bool | None:
        """Kept or not; None when unknown. Above 20 sectors (not run, see MEASURED_STRATA): v0.4
        from its record, A and B by the refusal rule (A0's tests refused, odd_even decisive and
        INCONCLUSIVE), version 3 and C unknown."""
        rec = known.get((r["key"], r["slot"]))
        if rec is not None:
            return rec[b]["stage_verdict"] in KEPT
        if r["stratum"] not in MEASURED_STRATA:
            if b == "v04":
                return r["v04_stage"] in KEPT
            if b in ("v4A", "v4B"):
                return False
        return None

    for b in ("v04", "v3", "v4A", "v4B", "v4C"):
        point, low, high, per = 0.0, 0, 0, {}
        for s in STRATA:
            members = [r for r in drawn if r["stratum"] == s]
            seen = [o for o in (outcome(r, b) for r in members) if o is not None]
            k = sum(seen)
            missing = len(members) - len(seen)
            done = seen
            lo, _ = _hypergeometric(k, len(members), counts[s], ALPHA / len(STRATA))
            _, hi = _hypergeometric(k + missing, len(members), counts[s], ALPHA / len(STRATA))
            low, high = low + lo, high + hi
            point += counts[s] * (k / len(done) if done else 0.0)
            per[s] = {"kept": k, "known": len(done), "unknown": missing}
        block = {
            "strata": per,
            "point": point / len(rows),
            "interval": [low / len(rows), high / len(rows)],
        }
        if b != "v04":
            block["forecast"] = (
                "FAIL" if block["point"] < minimum else "PASS" if low / len(rows) >= minimum
                else "UNRESOLVED"
            )  # fmt: skip
        out["batteries"][b] = block
    # the losses against v0.4, every blocker listed (they overlap), and the paired transitions
    for b in ("v4A", "v4B", "v4C"):
        blockers: Counter = Counter()
        for rec in known.values():
            if rec["v04"]["stage_verdict"] not in KEPT or rec[b]["stage_verdict"] in KEPT:
                continue
            refused = (rec[b]["selection"] or {}).get("refused") or ""
            if "not certified" in refused:
                blockers[f"{rec['stratum']}: refused, the selector not certified"] += 1
            if "above the supported" in refused:
                blockers[f"{rec['stratum']}: refused above 20 sectors"] += 1
            if "outside the grid" in refused:
                blockers[f"{rec['stratum']}: refused, measured events outside 2 to 4 sectors"] += 1
            for t in rec[b]["decisive"]:
                st = rec[b]["tests"].get(t, {}).get("status")
                if t not in rec[b]["deferred"] and st in ("FAIL", "INCONCLUSIVE"):
                    blockers[f"{rec['stratum']}: {t} {st}"] += 1
        out["batteries"][b]["blockers_of_losses_overlapping"] = dict(blockers)
    for a, c in (("v4A", "v4B"), ("v4B", "v4C"), ("v3", "v4A")):
        out[f"transitions_{a}_to_{c}"] = dict(
            Counter(f"{x[a]['stage_verdict']} -> {x[c]['stage_verdict']}" for x in known.values()
                    if x[a]["stage_verdict"] != x[c]["stage_verdict"])
        )  # fmt: skip
    out["cpu_hours"] = round(sum(float(r.get("cpu_seconds", 0.0)) for r in got.values()) / 3600, 3)
    (HERE / "forecast-t2a.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps(out, indent=1, sort_keys=True))
    if out["batteries"]["v4A"]["forecast"] == "FAIL":
        budgeted.fail_gate("planet_forecast", {"target": "T2a", "forecast": "forecast-t2a.json"})
        raise SystemExit("T2a fails in the forecast with version 4 as built: a STOP")


if __name__ == "__main__":
    {"fetch": fetch, "manifests": manifests, "run": run, "summarize": summarize}[sys.argv[1]]()
