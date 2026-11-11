"""v0.5.3 stage B, B1: the runner of the candidate battery version 5 on development data (#217;
``docs/plans/v0.5.3-stageB1-design.md``). **Development; it decides nothing.**
``method_status: not_validated``.

Version 5 is ``battery_b1`` activated around its own attacks only: the comparators (v0.4 and
version 4) always run with version 4's functions, checked by ``battery_b1.check_active``. Every
record stores the activation record (the configuration and each replaced function's source hash)
and the execution counters of each version-5 attack.

- ``d2_one(i)``: C1 family P, ``c1.development_seed("P", i)``, as v0.5.2's ``forecast_v4.one``:
  the shared candidate generation, then v0.4, version 4 and version 5 (stage 2).
- ``t2a_one(row, cache)``: a T2a injection, as v0.5.2's ``forecast_t2a.one``: v0.4 reproduces its
  v0.4 record (``c2.compat_problems``), then version 5 as built (A) and with the selector treated
  as certified and the refusal lifted (C); B follows by v0.5.2's rule.

Usage (B1.1): ``smoke`` through ``scripts/launch_affinity.ps1``.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ledger_b  # noqa: E402,I001  (before budgeted: it points the ledger at stage B's)
import budgeted  # noqa: E402

V052 = ledger_b.V052
sys.path.insert(0, str(V052))
import battery_b1  # noqa: E402
import forecast_t2a as ft  # noqa: E402
import forecast_v4 as fv  # noqa: E402

DESIGN = ledger_b.ROOT / "docs/plans/v0.5.3-stageB1-design.md"
CONFIG = battery_b1.Config()  # the composition before B1.3 (every estimator on)
OUT = ledger_b.ROOT / ".cache/v053/stageB/b1"
WORKERS = 12
PIN = tuple(range(8, 32, 2))
MAX_SHARD_SECONDS = 1700.0
MAX_RECORD_BYTES = 200_000
DISK_QUOTA = 5 * 1024**3
DISK_BASELINE = ledger_b.ROOT / ".cache/v053/stageB/b1-disk-baseline.json"
SMOKE_PART, SMOKE_HOURS = "b1_smoke", 1.0
SMOKE_D2_INDEX = 3000


# --- version 5 around one attack ---------------------------------------------------------------


class Version5:
    """Activate version 5 for one attack and restore version 4 after it; the counters of that
    attack are returned in ``self.counts``."""

    def __init__(self, config: battery_b1.Config = CONFIG) -> None:
        self.config = config

    def __enter__(self):
        battery_b1.check_active(None)
        battery_b1.reset_counts()
        self.activation = battery_b1.activate(self.config)
        battery_b1.check_active(self.config)
        return self

    def __exit__(self, *exc) -> None:
        self.counts = battery_b1.counts()
        battery_b1.deactivate()
        battery_b1.check_active(None)


def d2_one(i: int) -> dict:
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.discover.paired import _outcome as paired_outcome
    from refute.packs.tess.pipeline import attack_candidate, global_prewhitening
    from refute.packs.tess.search import search_period

    started = time.process_time()
    rec: dict = {"index": i}
    try:
        data, truth = c1.generate("P", c1.development_seed("P", i))
    except c1.GenerationFailedError as exc:
        return {**rec, "status": "GENERATION_FAILURE", "reason": str(exc)}
    rec["target_snr"] = truth["target_snr"]
    p04, _, p4 = fv.plans()
    battery_b1.check_active(None)
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    v04 = paired_outcome(data, cand, p04, 2, None, None, pw)
    rec["gate_passed"] = v04["gate_passed"]
    rec["identity"] = c1.identity(truth, v04["candidate"])
    rec["v04"] = v04["verdict"]
    rec["sectors"] = len(set(data.lc.sector.tolist()))
    g = attack_candidate(data, cand, p4, None, None, pw)
    rec["v4"], rec["v4_tests"] = fv._verdict(g.tests, p4)
    with Version5() as v5:
        g = attack_candidate(data, cand, p4, None, None, pw)
        rec["v5"], rec["v5_tests"] = fv._verdict(g.tests, p4)
    rec["v5_activation"], rec["v5_counts"] = v5.activation, v5.counts
    rec["status"] = "OK"
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def t2a_one(row: dict) -> dict:
    """v0.5.2's ``forecast_t2a.one`` with version 5 in place of version 3 and 4 (the cache is
    v0.5.2's, ``ft.CACHE``, for the hosts it holds)."""
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
    target = ft.targets()[row["key"]]
    raw, staged, plans = ft._plans()
    randomness = json.loads((ft.V04_STEP / "runs" / "r_inj.json").read_text("utf-8"))["beacon"][
        "randomness"
    ]
    catalog = ((ft.V04_STEP / "eb_catalog.csv").as_posix(),)
    scan_path = (ft.V04_STEP / "eb_catalog_scan.json").as_posix()
    tasks = c2.tasks_for(target, raw, ft.CACHE, randomness, catalog, scan_path)
    task = next(t for t in tasks if t.kind == "injection" and t.slot == row["slot"])
    base = TessAdapter().load(target, staged, ft.CACHE)
    star = base.star
    drawn = inj.draw_injections(
        task.seed, task.k, inj.first_time(base),
        star.radius_rsun if star else None, star.logg_cgs if star else None,
    )[task.slot]  # fmt: skip
    data = inj.inject(base, drawn)
    rec["sectors"] = int(len(set(data.lc.sector.tolist())))
    catalogs, scan = load_catalogs(catalog, scan_path, ft.CACHE)
    p04 = plans["v04"]
    battery_b1.check_active(None)
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    v04, _ = ft._outcome(data, cand, p04, catalogs, scan, pw)
    _, references = c2.references(ledger_b.ROOT)
    mine = {
        "kind": "injection", "status": "OK", "chain": {"v04": v04},
        "injection": drawn.to_dict(),
        "recovery": inj.recovery(drawn, v04["candidate"], v04["gate_passed"]),
    }  # fmt: skip
    rec["compat_problems"] = c2.compat_problems(
        mine, references[f"{row['key']}/injection/{row['slot']}"]
    )
    rec["v04"] = ft._brief(v04, None, p04)
    with Version5() as v5a:
        out, sel = ft._outcome(data, cand, plans["v4A"], catalogs, scan, pw)
    rec["v5A"] = ft._brief(out, sel, plans["v4A"])
    rec["v5A_counts"] = v5a.counts
    if rec["sectors"] <= battery_v52.MAX_SELECTED_SECTORS:
        rec["v5C"], rec["v5C_counts"] = rec["v5A"], "same as v5A (at most 4 sectors)"
    else:
        saved = battery_v52.MAX_ORIGINAL_SECTORS
        battery_v52.MAX_ORIGINAL_SECTORS = 10**6  # configuration C only: the refusal lifted
        try:
            with Version5() as v5c:
                out, sel = ft._outcome(data, cand, plans["v4C"], catalogs, scan, pw)
        finally:
            battery_v52.MAX_ORIGINAL_SECTORS = saved
        rec["v5C"], rec["v5C_counts"] = ft._brief(out, sel, plans["v4C"]), v5c.counts
    rec["v5B"] = rec["v5C"] if rec["sectors"] <= battery_v52.MAX_ORIGINAL_SECTORS else rec["v5A"]
    rec["v5_activation"] = v5a.activation
    if any(rec[b]["candidate"] != rec["v04"]["candidate"] for b in ("v5A", "v5C")):
        raise ValueError("the batteries did not attack the same final candidate")
    rec["status"] = "OK"
    rec["cpu_seconds"] = time.process_time() - started
    return rec


# --- shards, disk and the fingerprint ---------------------------------------------------------


def _bounded(rec: dict, key: dict) -> bytes:
    line = json.dumps(rec, sort_keys=True, default=str).encode()
    if len(line) + 1 > MAX_RECORD_BYTES:  # the final bytes, newline included (Codex's code r1)
        line = json.dumps(
            {**key, "status": "ERROR", "reason": f"record of {len(line)} bytes above the bound"},
            sort_keys=True,
        ).encode()
    return line + b"\n"


def shard(arg: dict) -> bytes:
    key = {k: arg[k] for k in ("kind", "index", "key", "slot") if k in arg}
    try:
        rec = d2_one(arg["index"]) if arg["kind"] == "d2" else t2a_one(arg["row"])
        rec = {**key, **rec}
    except Exception as exc:  # noqa: BLE001 - recorded, never dropped
        rec = {**key, "status": "ERROR", "reason": repr(exc)}
    return _bounded(rec, key)


def disk_used() -> int:
    root = ledger_b.ROOT / ".cache/v053/stageB"
    return sum(p.stat().st_size for p in root.rglob("*") if p.is_file())


RUN_OVERHEAD_BYTES = 4 * 1024**2  # the driver's state, progress and charges files of one run


def _baseline() -> int:
    if not DISK_BASELINE.exists():
        DISK_BASELINE.write_text(json.dumps({"bytes": disk_used()}) + "\n", "utf-8")
    return json.loads(DISK_BASELINE.read_text("utf-8"))["bytes"]


def disk_check(records: int) -> None:
    """The design's section 4: the quota before any write, from a bound, not a projection: each
    record and its sidecar at most ``MAX_RECORD_BYTES``, and a fixed bound for the driver's other
    files (Codex's code review, round 1)."""
    need = 2 * records * MAX_RECORD_BYTES + RUN_OVERHEAD_BYTES
    if disk_used() - _baseline() + need > DISK_QUOTA:
        raise SystemExit("the disk quota of 5 GB would be passed: a STOP")


def disk_after() -> int:
    """The usage after a run or a download, checked against the quota (a STOP past it)."""
    used = disk_used() - _baseline()
    if used > DISK_QUOTA:
        raise SystemExit(f"the disk quota of 5 GB is passed ({used} bytes): a STOP")
    return used


def fingerprint(extra: str) -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    for path in (
        Path(__file__),
        HERE / "battery_b1.py",
        HERE / "ledger_b.py",
        DESIGN,
        V052 / "forecast_v4.py",
        V052 / "forecast_t2a.py",
        V052 / "budgeted.py",
        V052 / "driver.py",
        ledger_b.ROOT / "calibration/v0.4/claim.yaml",
    ):
        h.update(hashlib.sha256(path.read_bytes()).digest())
    h.update(json.dumps({"config": CONFIG.as_dict(), "extra": extra}, sort_keys=True).encode())
    return h.hexdigest()[:16]


def _part(part: str, hours: float, reason: str) -> None:
    if part not in ledger_b._rows():
        ledger_b.transfer("b1_unallocated", part, hours, reason)
    ledger_b.declare()


def _execute(part: str, rows: list, extra: str) -> str:
    # the sample itself enters the fingerprint (Codex's code review, round 1)
    fp = fingerprint(extra + json.dumps(rows, sort_keys=True, default=str))
    ledger_b.refuse_new_identity(part, fp, rows)
    cap = ledger_b.hard_cap(part, WORKERS, MAX_SHARD_SECONDS)
    print(len(rows), "shards; hard cap", round(cap, 2), "CPU-h; fingerprint", fp, flush=True)
    return budgeted.execute(
        ledger_b.SECTION, part, OUT / part / fp, shard, rows, fp, WORKERS, pin=PIN,
        max_shard_seconds=MAX_SHARD_SECONDS, hard_cap_hours=cap,
    )  # fmt: skip


# --- B1.1: the smoke ---------------------------------------------------------------------------


def smoke_rows() -> list:
    """One D2 planet (index 3000, the forecast's first) and the first injection of v0.5.2's
    sample with 5 to 20 sectors, whose host is cached (so that A and C differ)."""
    rows = [("d2-03000", {"kind": "d2", "index": SMOKE_D2_INDEX})]
    sample = ft.sample(ft.population())
    first = next(r for r in sample if r["stratum"] == "5_to_20")
    rows.append(
        (f"t2a-{first['key']}-{first['slot']}",
         {"kind": "t2a", "key": first["key"], "slot": first["slot"], "row": first})
    )  # fmt: skip
    return rows


def smoke() -> None:
    before = ledger_b.v052_ledger_sha256()
    try:
        ledger_b.check_caps("b1 smoke", reserve_days=0.1, reserve_tokens=0, in_b0=False)
        rows = smoke_rows()
        disk_check(len(rows))
        _part(SMOKE_PART, SMOKE_HOURS, "B1.1's smoke (#217, comment 6805071179)")
        state = _execute(SMOKE_PART, rows, "smoke")
        print(state, flush=True)
        print("disk used by B1 so far:", disk_after(), "bytes", flush=True)
    finally:
        if ledger_b.v052_ledger_sha256() != before:
            raise SystemExit("the v0.5.2 ledger changed: refused")
    if state != "complete":
        raise SystemExit(state)
    validate_smoke(rows)


ALWAYS = ("e3.sinusoid_calls", "e4.systematics_calls")  # these tests run in every attack
UNLESS_REFUSED = ("e2.calls",)  # odd_even reaches E2 unless the A0 tests are refused
EFFECTIVE = {
    "e1": ("e1.v4_finite", "e1.completion_missing", "e1.completion_nonpsd"),
    "e2": ("e2.gls",),
    "e3": ("e3.gls",),
    "e4": ("e4.window_quadratic",),
}


def _refused(rec: dict, attack: str) -> bool:
    """Whether the attack's A0-dependent tests were refused by the selector (a structural
    refusal: ``pipeline_v52`` then never calls E2)."""
    if attack == "v5_counts":  # D2: the selection is in the odd_even row of the version-5 tests
        return bool(((rec.get("v5_tests") or {}).get("odd_even") or {}).get("refused"))
    brief = rec.get("v5A" if attack == "v5A_counts" else "v5C") or {}
    return bool((brief.get("selection") or {}).get("refused"))


def smoke_problems(recs: list, rows: list, expected_activation: dict) -> tuple[list, list]:
    """The smoke's checks (Codex's code review, rounds 1 and 2): exactly the expected records in
    order; each OK; v0.4 reproducing its record; the full activation record equal to the
    configuration's; the counters integer and positive where the attack reaches them, and E2's
    counter zero where the selector refused. Returns (problems, the paths report)."""
    problems, report = [], []
    keys = [{k: arg[k] for k in ("kind", "index", "key", "slot") if k in arg} for _, arg in rows]
    got = [{k: r[k] for k in ("kind", "index", "key", "slot") if k in r} for r in recs]
    if got != keys:
        problems.append(f"records {got} are not the expected {keys}")
    attacks = {"d2": ("v5_counts",), "t2a": ("v5A_counts", "v5C_counts")}
    for rec in recs:
        kind = rec.get("kind")
        if rec.get("status") != "OK":
            problems.append(f"{kind}: status {rec.get('status')}: {rec.get('reason')}")
            continue
        if kind == "t2a" and rec.get("compat_problems") != []:
            problems.append(
                f"t2a: v0.4 does not reproduce its record: {rec.get('compat_problems')}"
            )
        if rec.get("v5_activation") != expected_activation:
            problems.append(f"{kind}: the activation record is not the configuration's")
        for attack in attacks.get(kind, ()):
            c = rec.get(attack)
            if attack == "v5C_counts" and isinstance(c, str) and rec.get("sectors", 99) <= 4:
                continue  # C is A at four sectors or fewer
            if not isinstance(c, dict) or not all(isinstance(v, int) for v in c.values()):
                problems.append(f"{kind} {attack}: counters missing or not integers")
                continue
            refused = _refused(rec, attack)
            need = ALWAYS if refused else ALWAYS + UNLESS_REFUSED
            missing = [k for k in need if c.get(k, 0) <= 0]
            if missing:
                problems.append(f"{kind} {attack}: counters not positive: {missing}")
            if refused and c.get("e2.calls", 0) != 0:
                problems.append(f"{kind} {attack}: E2 ran although the selector refused")
            report.append(
                {
                    "record": kind,
                    "attack": attack,
                    "selector_refused": refused,
                    "effective": {e: {k: c.get(k, 0) for k in ks} for e, ks in EFFECTIVE.items()},
                    "fallbacks": {k: v for k, v in c.items() if "fallback" in k or "v4_path" in k},
                }
            )
    return problems, report


def expected_activation() -> dict:
    record = battery_b1.activate(CONFIG)
    battery_b1.deactivate()
    battery_b1.check_active(None)
    return record


def validate_smoke(rows: list) -> None:
    """The smoke succeeds only if ``smoke_problems`` finds nothing; the report is written to
    ``b1-smoke.json`` either way."""
    fp = fingerprint("smoke" + json.dumps(rows, sort_keys=True, default=str))
    data = budgeted.assembled(
        ledger_b.SECTION, SMOKE_PART, OUT / SMOKE_PART / fp, shard, rows, fp, WORKERS, pin=PIN,
        max_shard_seconds=MAX_SHARD_SECONDS,
    )  # fmt: skip
    recs = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    problems, report = smoke_problems(recs, rows, expected_activation())
    out = {"problems": problems, "paths": report,
           "cpu_seconds": [r.get("cpu_seconds") for r in recs]}  # fmt: skip
    (HERE / "b1-smoke.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8")
    print(json.dumps(out, indent=1, sort_keys=True), flush=True)
    if problems:
        raise SystemExit("the smoke did not pass its checks: " + "; ".join(problems))


if __name__ == "__main__":
    with ledger_b.Exclusive(f"b1_forecast {sys.argv[1]}"):
        {"smoke": smoke}[sys.argv[1]]()
