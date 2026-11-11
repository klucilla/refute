"""v0.5.3 stage B, B1.4: the development forecast of D2, D4 and T2a with the candidate version 5
(#217; ``docs/plans/v0.5.3-stageB1-design.md``, section 3, B1.4). **A forecast; it decides
nothing.** ``method_status: not_validated``.

Version 5 runs with the composition B1.3 froze (``b1-composition.json``), around its own attacks
only (``b1_forecast.Version5``).

- **D2 and D4** (part ``b1_forecast_d2d4``): 200 new C1 planets, family P, seeds
  ``c1.development_seed("P", i)`` for i in 3000 to 3199, attacked by v0.4, version 4 and version 5
  on the same candidate. The frozen rules (``calib05.c1.decision_rules`` wording) are the
  forecast; the Wilson intervals are a diagnostic apart.
- **T2a, a census** (parts ``b1_t2a_2to4``, ``b1_t2a_5to20``, ``b1_t2a_above20``): every injection
  of T2a's population (615 in 84 hosts), each rebuilt by ``c2.tasks_for`` from B1's cache. v0.4
  must reproduce its v0.4 record, then version 5 runs as built (A) and with the selector treated
  as certified and the refusal lifted (C); B equals C up to 20 sectors and A above. Above 20
  sectors only v0.4 and C run (the smoke took 600.8 s, under the design's 20 minutes).

``summarize`` gives D2, D4, and T2a's explicit answer from ``K_B`` and ``U_B`` among the 559 of 2
to 20 sectors: yes if ``K_B >= 552``, no if ``K_B + U_B <= 551``, unresolved otherwise; and C's
upper end for the rescue above 20 sectors.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import b1_forecast as bf  # noqa: E402,I001
from b1_forecast import battery_b1, budgeted, ft, fv, ledger_b  # noqa: E402
import b1_data  # noqa: E402

COMPOSITION = HERE / "b1-composition.json"
OUT = ledger_b.ROOT / ".cache/v053/stageB/b1"
KEPT = ("SURVIVED", "WEAKENED")
D2_FIRST, D2_N = 3000, 200
# allocations from the measured smokes and screening (about 145 CPU-s per curve and battery
# pair; 252 s per injection of 5 to 20 sectors with v0.4, A and C; 595 s above 20 with v0.4 and C)
PARTS = {
    "d2d4": ("b1_forecast_d2d4", 14.0),
    "2_to_4": ("b1_t2a_2to4", 18.0),
    "5_to_20": ("b1_t2a_5to20", 24.0),
    "above_20": ("b1_t2a_above20", 12.0),
}
V04_INPUTS = (
    "runs/r_inj.json",
    "selection/targets.yaml",
    "runs/funnel_run_set.json",
    "eb_catalog.csv",
    "eb_catalog_scan.json",
)
T2A_MIN_KEPT_559 = 552  # the design: ceil(551.5), the 56 above 20 lost in B


def config() -> battery_b1.Config:
    """The composition frozen by B1.3 (refused if absent)."""
    if not COMPOSITION.exists():
        raise SystemExit("B1.3's composition is not frozen yet: refused")
    c = json.loads(COMPOSITION.read_text("utf-8"))["composition"]
    return battery_b1.Config(e1=c["e1"], e2=c["e2"], e3=c["e3"], e4=c["e4"])


def d2_one(i: int) -> dict:
    """``b1_forecast.d2_one`` with the frozen composition."""
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
    with bf.Version5(config()) as v5:
        g = attack_candidate(data, cand, p4, None, None, pw)
        rec["v5"], rec["v5_tests"] = fv._verdict(g.tests, p4)
    rec["v5_activation"], rec["v5_counts"] = v5.activation, v5.counts
    rec["status"] = "OK"
    rec["cpu_seconds"] = time.process_time() - started
    return rec


def t2a_one(row: dict) -> dict:
    """``b1_forecast.t2a_one`` from B1's cache, with the frozen composition; above 20 sectors only
    v0.4 and C."""
    from refute.packs.tess import battery_v52
    from refute.packs.tess.adapter import TessAdapter
    from refute.packs.tess.calib05 import c2
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.discover import injection as inj
    from refute.packs.tess.discover.measure import load_catalogs
    from refute.packs.tess.pipeline import global_prewhitening
    from refute.packs.tess.search import search_period

    cache = b1_data.CACHE
    only_c = row["stratum"] == "above_20"
    started, wall = time.process_time(), time.perf_counter()
    rec: dict = {"key": row["key"], "slot": row["slot"], "stratum": row["stratum"]}
    target = ft.targets()[row["key"]]
    raw, staged, plans = ft._plans()
    randomness = json.loads((ft.V04_STEP / "runs" / "r_inj.json").read_text("utf-8"))["beacon"][
        "randomness"
    ]
    catalog = ((ft.V04_STEP / "eb_catalog.csv").as_posix(),)
    scan_path = (ft.V04_STEP / "eb_catalog_scan.json").as_posix()
    tasks = c2.tasks_for(target, raw, cache, randomness, catalog, scan_path)
    task = next(t for t in tasks if t.kind == "injection" and t.slot == row["slot"])
    base = TessAdapter().load(target, staged, cache)
    star = base.star
    drawn = inj.draw_injections(
        task.seed, task.k, inj.first_time(base),
        star.radius_rsun if star else None, star.logg_cgs if star else None,
    )[task.slot]  # fmt: skip
    data = inj.inject(base, drawn)
    rec["sectors"] = int(len(set(data.lc.sector.tolist())))
    catalogs, scan = load_catalogs(catalog, scan_path, cache)
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
    cfg = config()
    if not only_c:
        with bf.Version5(cfg) as v:
            out, sel = ft._outcome(data, cand, plans["v4A"], catalogs, scan, pw)
        rec["v5A"], rec["v5A_counts"] = ft._brief(out, sel, plans["v4A"]), v.counts
        rec["v5_activation"] = v.activation
    if not only_c and rec["sectors"] <= battery_v52.MAX_SELECTED_SECTORS:
        rec["v5C"], rec["v5C_counts"] = rec["v5A"], "same as v5A (at most 4 sectors)"
    else:
        saved = battery_v52.MAX_ORIGINAL_SECTORS
        battery_v52.MAX_ORIGINAL_SECTORS = 10**6  # configuration C only: the refusal lifted
        try:
            with bf.Version5(cfg) as v:
                out, sel = ft._outcome(data, cand, plans["v4C"], catalogs, scan, pw)
        finally:
            battery_v52.MAX_ORIGINAL_SECTORS = saved
        rec["v5C"], rec["v5C_counts"] = ft._brief(out, sel, plans["v4C"]), v.counts
        rec["v5_activation"] = v.activation
    attacked = ("v5C",) if only_c else ("v5A", "v5C")
    if any(rec[b]["candidate"] != rec["v04"]["candidate"] for b in attacked):
        raise ValueError("the batteries did not attack the same final candidate")
    rec["status"] = "OK"
    rec["cpu_seconds"] = time.process_time() - started
    rec["wall_seconds"] = time.perf_counter() - wall
    return rec


def shard(arg: dict) -> bytes:
    key = {k: arg[k] for k in ("kind", "index", "key", "slot") if k in arg}
    try:
        rec = d2_one(arg["index"]) if arg["kind"] == "d2" else t2a_one(arg["row"])
        rec = {**key, **rec}
    except Exception as exc:  # noqa: BLE001 - recorded as unknown, never dropped
        rec = {**key, "status": "ERROR", "reason": repr(exc)}
    return bf._bounded(rec, key)


USED_DEVELOPMENT_INDICES = {
    "v0.5.1 forecast": range(0, 100),
    "v0.5.2 forecast, stage A (b), B1.2": range(1000, 1120),
    "B1.3": range(4000, 4450),
}
# Disclosed, not changed (Codex's review of B1.4, round 1): B1.1's D2 smoke used index 3000, the
# first of the frozen 3000 to 3199. Its record (version 4 and version 5 INCONCLUSIVE, the selector
# refused) chose nothing; the interval stays as the design froze it.
SMOKE_INDICES = {3000}


def check_d2_indices() -> None:
    mine = set(range(D2_FIRST, D2_FIRST + D2_N))
    for label, used in USED_DEVELOPMENT_INDICES.items():
        if mine & set(used):
            raise SystemExit(f"the forecast's indices meet {label}'s: refused")


def rows(name: str) -> list:
    if name == "d2d4":
        check_d2_indices()
        return [(f"d{i:05d}", {"kind": "d2", "index": i}) for i in range(D2_FIRST, D2_FIRST + D2_N)]
    return [
        (f"t-{r['key']}-{r['slot']:02d}", {"kind": "t2a", "key": r["key"], "slot": r["slot"],
                                            "row": r})
        for r in ft.population()
        if r["stratum"] == name
    ]  # fmt: skip


def fingerprint(name: str, rws: list) -> str:
    """Code, configuration and rows (``bf.fingerprint``), this script, ``b1_data.py``, the frozen
    composition, and for T2a the C2 records, the C2 fetch record and B1's fetch report."""
    h = hashlib.sha256(bf.fingerprint(name + json.dumps(rws, sort_keys=True)).encode())
    paths = [Path(__file__), HERE / "b1_data.py", COMPOSITION]
    if name != "d2d4":
        paths += [ft.C2_RECORDS, ft.C2_FETCH, HERE / "b1-fetch-t2a.json"]
        # v0.4's inputs read by c2.tasks_for, c2.references and the catalogs (Codex, round 1)
        paths += [ft.V04_STEP / rel for rel in V04_INPUTS]
    for path in paths:
        h.update(hashlib.sha256(path.read_bytes()).digest())
    return h.hexdigest()[:16]


def run(name: str) -> None:
    part, hours = PARTS[name]
    before = ledger_b.v052_ledger_sha256()
    try:
        ledger_b.check_caps(f"b1 forecast {name}", reserve_days=0.3, reserve_tokens=0, in_b0=False)
        config()
        rws = rows(name)
        if name != "d2d4":
            fetched = json.loads((HERE / "b1-fetch-t2a.json").read_text("utf-8"))
            if fetched["changed"] or fetched["failed"]:
                raise SystemExit("hosts changed or failed in B1's fetch: their injections would "
                                 "be unknown; brought to the maintainer first")  # fmt: skip
        bf.disk_check(len(rws))
        bf._part(part, hours, f"B1.4's forecast, {name} (#217)")
        fp = fingerprint(name, rws)
        ledger_b.refuse_new_identity(part, fp, rws)
        cap = ledger_b.hard_cap(part, bf.WORKERS, bf.MAX_SHARD_SECONDS)
        print(len(rws), "shards; hard cap", round(cap, 2), "CPU-h; fingerprint", fp, flush=True)
        state = budgeted.execute(
            ledger_b.SECTION, part, OUT / part / fp, shard, rws, fp, bf.WORKERS, pin=bf.PIN,
            max_shard_seconds=bf.MAX_SHARD_SECONDS, hard_cap_hours=cap,
        )  # fmt: skip
        print(state, flush=True)
        print("disk used by B1 so far:", bf.disk_after(), "bytes", flush=True)
    finally:
        if ledger_b.v052_ledger_sha256() != before:
            raise SystemExit("the v0.5.2 ledger changed: refused")
    if state != "complete":
        raise SystemExit(state)


def _records(name: str) -> list:
    part, _ = PARTS[name]
    rws = rows(name)
    fp = fingerprint(name, rws)
    data = budgeted.assembled(
        ledger_b.SECTION, part, OUT / part / fp, shard, rws, fp, bf.WORKERS, pin=bf.PIN,
        max_shard_seconds=bf.MAX_SHARD_SECONDS,
    )  # fmt: skip
    return [json.loads(x) for x in data.decode().splitlines() if x.strip()]


def _records_or_partial(name: str) -> tuple[list, str | None]:
    """The part's records; if it stopped, the shards it completed, each checked against its
    sidecar (fingerprint, argument and SHA-256), the stop kept and the rest unknown (Codex's
    review of B1.4, round 1). Never a reconciliation or a resume."""
    import driver

    try:
        return _records(name), None
    except SystemExit as exc:
        # only a stop or missing shards allow the partial read; any integrity refusal stands
        # (Codex's review of B1.4, round 2)
        part, _ = PARTS[name]
        # the persisted state decides, not the message (Codex's review of B1.4, round 3): a
        # failed gate is propagated even with a stop; a partial read only for a proven stop or
        # missing shards
        book = budgeted.load()
        row = book.get("sections", {}).get(ledger_b.SECTION, {}).get("parts", {}).get(part, {})
        if budgeted._open_gates(book, ledger_b.SECTION, part):
            raise
        stopped = "unresolved_stop" in row
        if not stopped and "shards are not done" not in str(exc):
            raise
        rws = rows(name)
        fp = fingerprint(name, rws)
        run_dir = OUT / part / fp
        known = {sid for sid, _ in rws}
        if (run_dir / "sidecars").exists():
            for side_p in (run_dir / "sidecars").glob("*.json"):
                if side_p.stem not in known:
                    raise SystemExit(
                        f"shard {side_p.stem}: not in this schedule: refused"
                    ) from None
        recs = []
        for sid, arg in rws:
            data_p, side_p = run_dir / "shards" / f"{sid}.bin", run_dir / "sidecars" / f"{sid}.json"
            if not side_p.exists():
                continue
            side = json.loads(side_p.read_text("utf-8"))
            if side["fingerprint"] != fp or side["arg_sha256"] != driver._arg_hash(arg):
                raise SystemExit(f"{sid}: a record of another run: refused") from None
            if (
                not data_p.exists()
                or hashlib.sha256(data_p.read_bytes()).hexdigest() != side["sha256"]
            ):
                raise SystemExit(f"{sid}: its file does not match its sidecar: refused") from None
            recs += [json.loads(x) for x in data_p.read_text("utf-8").splitlines() if x.strip()]
        return recs, f"stopped ({exc}); {len(recs)} of {len(rws)} records read, the rest unknown"


def d2d4_summary(recs: list) -> dict:
    from refute.packs.tess.calib05.c1 import wilson
    from refute.packs.tess.calib05.values import C1

    ok = [r for r in recs if r.get("status") == "OK"]
    eligible = [r for r in ok if r["gate_passed"] and r["identity"]]
    subset = [r for r in eligible if r["target_snr"] >= 15.0]
    n, m = len(eligible), len(subset)
    floor = C1.not_decidable_below
    v04_kept = sum(r["v04"] in KEPT for r in eligible)
    out: dict = {
        "curves": len(recs), "errors": sum(r.get("status") == "ERROR" for r in recs),
        "generation_failures": sum(r.get("status") == "GENERATION_FAILURE" for r in recs),
        "eligible": n, "d4_subset": m, "floor": floor, "batteries": {},
    }  # fmt: skip
    for b in ("v04", "v4", "v5"):
        kept = sum(r[b] in KEPT for r in eligible)
        refuted = sum(r[b] == "REFUTED" for r in eligible)
        inconc = sum(r[b] == "INCONCLUSIVE" for r in subset)
        d2_min = v04_kept / n - 0.10 if n else None
        upper = wilson(refuted, n)[1] if n else None
        d2 = fv._decision(
            n >= floor, kept / n >= d2_min and refuted / n <= 0.05 and upper <= 0.10
        ) if n else "NOT DECIDABLE"  # fmt: skip
        d4 = fv._decision(m >= floor, inconc / m <= 0.30) if m else "NOT DECIDABLE"
        out["batteries"][b] = {
            "kept": kept, "refuted": refuted, "d4_inconclusive": inconc,
            "d2_minimum": d2_min, "refuted_wilson_upper": upper, "D2": d2, "D4": d4,
            "diagnostic_kept_wilson": wilson(kept, n) if n else None,
            "diagnostic_d4_wilson": wilson(inconc, m) if m else None,
        }  # fmt: skip
    out["v5_blockers"] = dict(Counter(
        f"{t}: {d['status']}" for r in eligible if r["v5"] not in KEPT
        for t, d in r["v5_tests"].items() if d["status"] in ("INCONCLUSIVE", "FAIL")
    ).most_common())  # fmt: skip
    return out


def t2a_summary(by_stratum: dict) -> dict:
    """The census's answer (the design's B1.4): ``K_B`` and ``U_B`` among the 559 of 2 to 20
    sectors; A over the same; C over all 615 when the stratum above 20 ran."""
    pop = ft.population()
    v04_pop = sum(r["v04_stage"] in KEPT for r in pop)
    minimum = v04_pop / len(pop) - 0.10
    got = {(r["key"], r["slot"]): r for recs in by_stratum.values() for r in recs}

    def outcome(row: dict, b: str) -> bool | None:
        rec = got.get((row["key"], row["slot"]))
        if rec is None or rec.get("status") != "OK" or rec.get("compat_problems"):
            return None
        if b == "v5B":
            b = "v5C" if rec["sectors"] <= 20 else "v5A"
        if b not in rec:
            return False if b == "v5A" and row["stratum"] == "above_20" else None
        return rec[b]["stage_verdict"] in KEPT

    out: dict = {"population": len(pop), "v04_kept_population": v04_pop, "minimum": minimum,
                 "minimum_count": minimum * len(pop), "configurations": {}}  # fmt: skip
    measured = [r for r in pop if r["stratum"] != "above_20"]
    above = [r for r in pop if r["stratum"] == "above_20"]
    for b in ("v5A", "v5B", "v5C"):
        k = sum(outcome(r, b) is True for r in measured)
        u = sum(outcome(r, b) is None for r in measured)
        ka = sum(outcome(r, b) is True for r in above) if b == "v5C" else 0
        ua = sum(outcome(r, b) is None for r in above) if b == "v5C" else 0
        out["configurations"][b] = {
            "kept_2_to_20": k, "unknown_2_to_20": u, "kept_above_20": ka, "unknown_above_20": ua,
            "lower_615": k + ka, "upper_615": k + u + ka + ua,
            "blockers": dict(Counter(
                f"{t}: {d}" for r in measured if outcome(r, b) is False
                for t, d in ((got[(r["key"], r["slot"])].get(b if b != "v5B" else (
                    "v5C" if got[(r["key"], r["slot"])]["sectors"] <= 20 else "v5A")) or {}
                ).get("tests") or {}).items() if d in ("INCONCLUSIVE", "FAIL")
            ).most_common(20)),
        }  # fmt: skip
    kb, ub = (
        out["configurations"]["v5B"]["kept_2_to_20"],
        out["configurations"]["v5B"]["unknown_2_to_20"],
    )
    out["answer_without_certification_above_20"] = (
        "yes"
        if kb >= T2A_MIN_KEPT_559
        else "no"
        if kb + ub <= T2A_MIN_KEPT_559 - 1
        else "unresolved"
    )
    c = out["configurations"]["v5C"]
    out["certification_above_20_cannot_rescue"] = c["upper_615"] <= T2A_MIN_KEPT_559 - 1
    return out


def summarize() -> None:
    out: dict = {"label": "B1.4 development forecast with the candidate version 5 (decides "
                 "nothing)", "method_status": "not_validated",
                 "composition": json.loads(COMPOSITION.read_text("utf-8"))}  # fmt: skip
    recs, note = _records_or_partial("d2d4")
    out["d2_d4"] = d2d4_summary(recs)
    out["d2_d4"]["part_state"] = note or "complete"
    if note:  # an incomplete part gives counts only, never the forecast's decision (round 2)
        for b in out["d2_d4"]["batteries"].values():
            b["D2"] = b["D4"] = "NOT DECIDED: the part did not complete"
    out["d2_d4"]["smoke_index_disclosed"] = sorted(SMOKE_INDICES)
    strata, notes = {}, {}
    for s_ in ("2_to_4", "5_to_20", "above_20"):
        strata[s_], notes[s_] = _records_or_partial(s_)
    out["t2a"] = t2a_summary(strata)
    out["t2a"]["part_states"] = {k: v or "complete" for k, v in notes.items()}
    (HERE / "b1-forecast.json").write_text(
        json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
    )
    print(json.dumps(out, indent=1, sort_keys=True, default=str)[:8000])


if __name__ == "__main__":
    with ledger_b.Exclusive(f"b1_b14 {' '.join(sys.argv[1:])}"):
        {"run": lambda: run(sys.argv[2]), "summarize": summarize}[sys.argv[1]]()
