"""v0.5.4, I1: what the records cannot tell (#217; ``docs/plans/v0.5.4-h1-design.md``, section I1).
**A diagnostic; it decides nothing about any target.** ``method_status: not_validated``.

For T2a, the 169 losses of configuration B whose decisive blockers include ``systematics``; for
D2, the 37 eligible planets version 5 loses. Each is rebuilt exactly as B1.4 did (``b1_b14``'s
``t2a_one`` and ``d2_one``) and attacked again by version 5 only (for T2a, configuration B's
attack), with a spy that keeps the raw ``TestResult`` of the blocking tests: status, message,
metrics and every sensitivity block. A rerun must reproduce its B1 record (the verdict and every
decisive test's status) before it is classified; one that does not stops the run for the
maintainer. Each blocking test is classified by the design's frozen table: (iii) a code defect,
(ii) a refusal or procedure, (i) insufficient sensitivity.

Usage, through ``scripts/launch_affinity.ps1``: ``run``, then ``summarize`` (``i1-diagnosis.json``).
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import math
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
STAGE_B = ROOT / "docs/validation/v0.5.3/stageB"
sys.path.insert(0, str(STAGE_B))
import b1_b14  # noqa: E402,I001  (stage B's modules first: they point budgeted at stage B)
import b1_blockers_decisive as bd  # noqa: E402
import b1_d2d4_rest  # noqa: E402
import ledger_b  # noqa: E402
from b1_b14 import bf, ft, fv  # noqa: E402

sys.path.insert(0, str(HERE))
import ledger_i  # noqa: E402,I001  (last: it points budgeted at v0.5.4's ledger)
import budgeted  # noqa: E402

PART = "h1_i1"
OUT = ROOT / ".cache/v054/i1"
OUT_FILE = HERE / "i1-diagnosis.json"
DESIGN = ROOT / "docs/plans/v0.5.4-h1-design.md"
WORKERS = 12
PIN = tuple(range(8, 32, 2))
MAX_SHARD_SECONDS = 1700.0
KEPT = ("SURVIVED", "WEAKENED")
T2A_TEST = "systematics"
D2_TESTS = ("odd_even", "sinusoid")
EXPECTED_T2A, EXPECTED_D2 = 169, 37
MAX_RECORD_BYTES = 200_000  # a record (at most half) and its sidecar, for the disk reservation
RUN_OVERHEAD_BYTES = 50_000_000


@contextlib.contextmanager
def _stage_b_ledger():
    """Read stage B's records through its own reviewed readers: ``budgeted`` pointed at stage B's
    ledger for the duration of the read, then back at v0.5.4's. Reads only."""
    saved = (budgeted.LEDGER, budgeted.LINES, budgeted.HARD_MAXIMUM, budgeted.SPENT_BEFORE,
             budgeted.save)  # fmt: skip
    budgeted.LEDGER = ledger_b.HERE / "ledger.json"
    budgeted.LINES = {ledger_b.SECTION: ledger_b.CAP_HOURS - ledger_b.CHARGES_ROOM}
    budgeted.HARD_MAXIMUM, budgeted.SPENT_BEFORE = ledger_b.CAP_HOURS, 0.0
    budgeted.save = None  # a write here would be a defect
    try:
        yield
    finally:
        (budgeted.LEDGER, budgeted.LINES, budgeted.HARD_MAXIMUM, budgeted.SPENT_BEFORE,
         budgeted.save) = saved  # fmt: skip


def _statuses(tests: dict) -> dict:
    return {k: (v.get("status") if isinstance(v, dict) else v) for k, v in tests.items()}


def schedule() -> list:
    """The two populations from B1's committed records: T2a B's ``systematics`` losses and D2's
    version-5 losses, each with the expected verdict and test statuses for the reproduction."""
    with _stage_b_ledger():
        got = {}
        for s in ("2_to_4", "5_to_20"):
            for r in b1_b14._records(s):
                got[(r["key"], r["slot"])] = r
        d2_recs, _, _, _ = b1_d2d4_rest.complete_records()
    rows = []
    for row in ft.population():
        rec = got.get((row["key"], row["slot"]))
        if rec is None or row["stratum"] == "above_20":
            continue
        if rec.get("status") != "OK" or rec.get("compat_problems"):
            continue
        b = "v5C" if rec["sectors"] <= 20 else "v5A"
        brief = rec[b]
        if brief["stage_verdict"] in KEPT:
            continue
        blockers, _, _ = bd.t2a_blockers(brief)
        if not any(x.split(" ")[0] == T2A_TEST for x in blockers):
            continue
        rows.append((f"t-{row['key']}-{row['slot']:02d}", {
            "kind": "t2a", "row": row, "sectors": rec["sectors"],
            "expected_verdict": brief["stage_verdict"],
            "expected_tests": _statuses(brief["tests"]),
            "expected_candidate": brief["candidate"],
            "expected_decisive": sorted(brief["decisive"]),
            "expected_deferred": sorted(brief["deferred"]),
        }))  # fmt: skip
    for r in d2_recs:
        if r.get("status") != "OK" or not (r["gate_passed"] and r["identity"]):
            continue
        if r["v5"] in KEPT:
            continue
        rows.append((f"d{r['index']:05d}", {
            "kind": "d2", "index": r["index"], "expected_verdict": r["v5"],
            "expected_tests": _statuses(r["v5_tests"]),
        }))  # fmt: skip
    n_t = sum(a["kind"] == "t2a" for _, a in rows)
    n_d = sum(a["kind"] == "d2" for _, a in rows)
    if (n_t, n_d) != (EXPECTED_T2A, EXPECTED_D2):
        raise SystemExit(f"the populations are {n_t} and {n_d}, not 169 and 37: refused")
    return rows


def _finite(x) -> bool:
    return isinstance(x, (int, float)) and math.isfinite(x)


def classify(raw, enforced_status: str, registry: dict, stages: dict, stage: int) -> dict:
    """The design's frozen table for one blocking test: its raw result replayed through the
    complete pipeline (coverage, sensitivity, the stage's deferral), against the enforced status
    the attack produced."""
    from collections.abc import Mapping

    from refute.core.sensitivity import _refusal, block_problem, enforce_sensitivity
    from refute.core.verdict import defer_tests, enforce_coverage

    kinds = registry.get(raw.name) or {}
    invalid = []
    if raw.sensitivity is None:
        blocks = {}  # absent: the rule refuses a PASS for it (class (ii)), not a defect
    elif isinstance(raw.sensitivity, Mapping):
        blocks = dict(raw.sensitivity)
    else:
        blocks = {}
        invalid.append("the sensitivity container is not a mapping")
    out: dict = {
        "raw_status": raw.status.value, "raw_message": raw.message,
        "enforced_status": enforced_status, "coverage": raw.coverage,
        "blocks": {}, "non_detectable": [],
        "metrics": {k: raw.metrics.get(k) for k in (
            "sub_checks_run", "sub_checks_not_run", "sub_checks_not_applicable",
            "inconclusive_class", "background_rise_sigma", "background_rise_err",
            "background_rise_fraction_of_depth", "fraction_near_dumps",
            "sap_difference_sigma", "sap_relative_difference") if k in raw.metrics},
    }  # fmt: skip
    for sub, block in blocks.items():  # every supplied block, "not applicable" ones included
        if sub not in kinds:
            invalid.append(f"{sub}: a block the registry does not declare")
            continue
        problem = block_problem(block, kinds[sub])
        if problem is not None:
            invalid.append(f"{sub}: {problem}")
        if not isinstance(block, Mapping):
            continue
        keep = {k: block.get(k) for k in ("detectable", "probability", "required_probability",
                                          "effect", "alternative", "unit", "applicable",
                                          "reason", "category")}  # fmt: skip
        out["blocks"][sub] = {k: v for k, v in keep.items() if v is not None}
        if "probability" in block and not _finite(block["probability"]):
            invalid.append(f"{sub}: probability not finite")
        # only statistical (rule) blocks carry ``detectable``; a categorical block never does
        if "detectable" in block and not block["detectable"]:
            out["non_detectable"].append(sub)
    covered = enforce_coverage([raw])[0]
    sensed = enforce_sensitivity([covered], registry)[0]
    deferred, _ = defer_tests([sensed], stages, stage)
    recomputed = deferred[0].status.value
    out["replay"] = {
        "coverage": [covered.status.value, covered.message],
        "sensitivity": [sensed.status.value, sensed.message],
        "deferral": [recomputed, deferred[0].message],
    }
    if invalid:
        out["class"], out["why"] = "iii", "invalid sensitivity block: " + "; ".join(invalid)
    elif recomputed != enforced_status:
        out["class"] = "iii"
        out["why"] = f"enforced {enforced_status}, recomputed {recomputed}"
    elif raw.status.value == "INCONCLUSIVE":
        out["class"], out["why"] = "ii", "raw INCONCLUSIVE: " + raw.message
    elif raw.status.value == "PASS" and covered.status.value == "INCONCLUSIVE":
        out["class"], out["why"] = "ii", "the coverage rule: " + covered.message
    elif raw.status.value == "PASS" and sensed.status.value == "INCONCLUSIVE":
        why = _refusal(raw, registry) or ""
        out["class"] = "i" if why.startswith("insufficient sensitivity") else "ii"
        out["why"] = why
    else:
        out["class"], out["why"] = "unresolved", f"raw {raw.status.value}, enforced {recomputed}"
    return out


def _outcome_raw(data, cand, plan, catalogs, scan, pw):
    """``forecast_t2a._outcome`` with the spy keeping the gauntlet's raw results."""
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
    return out, selection, seen[0]


def _replay_all(tests, registry: dict, stages: dict, stage: int, decisive) -> dict:
    """Every decisive test's raw and replayed status and message (the design's record)."""
    from refute.core.sensitivity import enforce_sensitivity
    from refute.core.verdict import defer_tests, enforce_coverage

    raw = [t for t in tests if t.name in decisive]
    done, _ = defer_tests(enforce_sensitivity(enforce_coverage(raw), registry), stages, stage)
    return {
        a.name: {"raw": [a.status.value, a.message[:400]], "enforced": [b.status.value,
                                                                     b.message[:400]]}
        for a, b in zip(raw, done, strict=True)
    }  # fmt: skip


STOP_FILE = OUT / "binding-stop.json"


def _raise_stop(why: str) -> None:
    """A binding stop, written once by the first worker that finds it: every later shard skips its
    work (the driver itself only knows spending)."""
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        with STOP_FILE.open("x", encoding="utf-8") as fh:
            fh.write(json.dumps({"why": why}) + "\n")
    except FileExistsError:
        pass


def t2a_one(arg: dict) -> dict:
    """``b1_b14.t2a_one``'s rebuild, then configuration B's attack only."""
    from refute.packs.tess import battery_v52
    from refute.packs.tess.adapter import TessAdapter
    from refute.packs.tess.calib05 import c2
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.discover import injection as inj
    from refute.packs.tess.discover.measure import load_catalogs
    from refute.packs.tess.pipeline import global_prewhitening
    from refute.packs.tess.power import registry_for
    from refute.packs.tess.search import search_period

    row = arg["row"]
    cache = b1_b14.b1_data.CACHE
    target = ft.targets()[row["key"]]
    raw_plan, staged, plans = ft._plans()
    randomness = json.loads((ft.V04_STEP / "runs" / "r_inj.json").read_text("utf-8"))["beacon"][
        "randomness"
    ]
    catalog = ((ft.V04_STEP / "eb_catalog.csv").as_posix(),)
    scan_path = (ft.V04_STEP / "eb_catalog_scan.json").as_posix()
    tasks = c2.tasks_for(target, raw_plan, cache, randomness, catalog, scan_path)
    task = next(t for t in tasks if t.kind == "injection" and t.slot == row["slot"])
    base = TessAdapter().load(target, staged, cache)
    star = base.star
    drawn = inj.draw_injections(
        task.seed, task.k, inj.first_time(base),
        star.radius_rsun if star else None, star.logg_cgs if star else None,
    )[task.slot]  # fmt: skip
    data = inj.inject(base, drawn)
    sectors = int(len(set(data.lc.sector.tolist())))
    catalogs, scan = load_catalogs(catalog, scan_path, cache)
    p04 = plans["v04"]
    b1_b14.battery_b1.check_active(None)
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    # v0.4 must reproduce its C2 record (B1's input check)
    v04, _ = ft._outcome(data, cand, p04, catalogs, scan, pw)
    _, references = c2.references(ledger_i.ROOT)
    mine = {
        "kind": "injection", "status": "OK", "chain": {"v04": v04},
        "injection": drawn.to_dict(),
        "recovery": inj.recovery(drawn, v04["candidate"], v04["gate_passed"]),
    }  # fmt: skip
    compat = c2.compat_problems(mine, references[f"{row['key']}/injection/{row['slot']}"])
    cfg = b1_b14.config()
    if sectors <= battery_v52.MAX_SELECTED_SECTORS:
        plan, lift = plans["v4A"], False
    else:
        plan, lift = plans["v4C"], True
    saved = battery_v52.MAX_ORIGINAL_SECTORS
    if lift:
        battery_v52.MAX_ORIGINAL_SECTORS = 10**6  # configuration C, as B1.4 ran it
    try:
        with bf.Version5(cfg) as v:
            out, sel, gauntlet = _outcome_raw(data, cand, plan, catalogs, scan, pw)
    finally:
        battery_v52.MAX_ORIGINAL_SECTORS = saved
    brief = ft._brief(out, sel, plan)
    rec: dict = {"sectors": sectors, "plan": "v4A" if not lift else "v4C (refusal lifted)",
                 "stage_verdict": brief["stage_verdict"], "counts": v.counts}  # fmt: skip
    got = _statuses(brief["tests"])
    rec["mismatch"] = _mismatch(arg, brief["stage_verdict"], got, sectors)
    if compat:
        rec["mismatch"].append(f"v0.4 does not reproduce its C2 record: {compat}")
    if brief["candidate"] != v04["candidate"]:
        rec["mismatch"].append("version 5 did not attack v0.4's final candidate")
    if brief["candidate"] != arg["expected_candidate"]:
        rec["mismatch"].append("the final candidate differs from B1's record")
    if sorted(brief["decisive"]) != arg["expected_decisive"]:
        rec["mismatch"].append("the decisive tests differ from B1's record")
    if sorted(brief["deferred"]) != arg["expected_deferred"]:
        rec["mismatch"].append("the deferred tests differ from B1's record")
    if not rec["mismatch"]:
        raw = next(t for t in gauntlet.tests if t.name == T2A_TEST)
        rec["tests"] = {T2A_TEST: classify(raw, got[T2A_TEST], registry_for(plan),
                                           dict(plan.discovery.stages), 1)}  # fmt: skip
        rec["decisive_replay"] = _replay_all(
            gauntlet.tests, registry_for(plan), dict(plan.discovery.stages), 1, brief["decisive"]
        )
    return rec


def d2_one(arg: dict) -> dict:
    """``b1_b14.d2_one``'s rebuild, then version 5's attack only."""
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.pipeline import attack_candidate, global_prewhitening
    from refute.packs.tess.power import registry_for
    from refute.packs.tess.search import search_period

    i = arg["index"]
    data, truth = c1.generate("P", c1.development_seed("P", i))
    p04, _, p4 = fv.plans()
    b1_b14.battery_b1.check_active(None)
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    with bf.Version5(b1_b14.config()) as v:
        g = attack_candidate(data, cand, p4, None, None, pw)
    verdict, detail = fv._verdict(g.tests, p4)
    rec: dict = {"stage_verdict": verdict, "counts": v.counts}
    got = _statuses(detail)
    rec["mismatch"] = _mismatch(arg, verdict, got, None)
    if not rec["mismatch"]:
        from refute.packs.tess.pipeline import expected_by_role

        decisive, _ = expected_by_role(p4, False)
        rec["decisive_replay"] = _replay_all(g.tests, registry_for(p4),
                                             dict(p4.discovery.stages), 2, decisive)  # fmt: skip
        rec["tests"] = {}
        for name in D2_TESTS:
            raw = next((t for t in g.tests if t.name == name), None)
            if raw is not None and got.get(name) in ("INCONCLUSIVE", "FAIL"):
                rec["tests"][name] = classify(raw, got[name], registry_for(p4),
                                              dict(p4.discovery.stages), 2)  # fmt: skip
    return rec


def _mismatch(arg: dict, verdict: str, got: dict, sectors) -> list:
    out = []
    if verdict != arg["expected_verdict"]:
        out.append(f"verdict {verdict}, B1 {arg['expected_verdict']}")
    if got != arg["expected_tests"]:
        diff = sorted(k for k in set(got) | set(arg["expected_tests"])
                      if got.get(k) != arg["expected_tests"].get(k))  # fmt: skip
        out.append("tests differ: " + ", ".join(diff))
    if sectors is not None and sectors != arg["sectors"]:
        out.append(f"sectors {sectors}, B1 {arg['sectors']}")
    return out


def shard(arg: dict) -> bytes:
    key = {k: arg[k] for k in ("kind", "index") if k in arg}
    if arg["kind"] == "t2a":
        key.update(key=arg["row"]["key"], slot=arg["row"]["slot"], stratum=arg["row"]["stratum"])
    started = time.process_time()
    if STOP_FILE.exists():
        rec = {**key, "status": "SKIPPED", "reason": "a binding stop was raised"}
    else:
        try:
            rec = {**key, **(t2a_one(arg) if arg["kind"] == "t2a" else d2_one(arg)),
                   "status": "OK"}  # fmt: skip
        except Exception as exc:  # noqa: BLE001 - a class (iii) case, recorded, never dropped
            rec = {**key, "status": "ERROR", "reason": repr(exc)}
        if rec["status"] == "ERROR":
            _raise_stop(f"class (iii): an error in {key}")
        elif rec["mismatch"]:
            _raise_stop(f"a rerun did not reproduce its B1 record: {key}")
        elif any(c["class"] == "iii" for c in rec["tests"].values()):
            _raise_stop(f"class (iii) in {key}")
    rec["cpu_seconds"] = time.process_time() - started
    line = (json.dumps(rec, sort_keys=True, default=str) + "\n").encode()
    if len(line) > MAX_RECORD_BYTES // 2:  # the record and its sidecar within the reservation
        line = (json.dumps({**key, "status": "ERROR", "reason": f"a record of {len(line)} bytes "
                            "above its bound"}, sort_keys=True) + "\n").encode()  # fmt: skip
        _raise_stop(f"class (iii): an oversized record in {key}")
    return line


def fingerprint(rows: list) -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    h.update(bf.fingerprint("i1").encode())  # version 5's code and configuration, as B1 ran it
    paths = [Path(__file__), HERE / "ledger_i.py", DESIGN, STAGE_B / "b1_b14.py",
             STAGE_B / "b1_blockers_decisive.py", STAGE_B / "b1_d2d4_rest.py",
             STAGE_B / "b1-composition.json", STAGE_B / "b1_data.py",
             ft.C2_RECORDS, ft.C2_FETCH, STAGE_B / "b1-fetch-t2a.json"]  # fmt: skip
    paths += [ft.V04_STEP / rel for rel in b1_b14.V04_INPUTS]  # as b1_b14.fingerprint
    for path in paths:
        h.update(hashlib.sha256(path.read_bytes()).digest())
    h.update(json.dumps(rows, sort_keys=True, default=str).encode())
    return h.hexdigest()[:16]


def run() -> None:
    ledger_i.assert_bound()
    before = ledger_i.v052_ledger_sha256()
    try:
        rows = schedule()
        reserve = len(rows) * MAX_RECORD_BYTES + RUN_OVERHEAD_BYTES
        ledger_i.check_caps("i1 run", reserve_days=0.3, reserve_tokens=0, reserve_bytes=reserve)
        ledger_i.declare()
        fp = fingerprint(rows)
        ledger_i.refuse_new_identity(PART, fp, rows)
        cap = ledger_i.hard_cap(PART, WORKERS, MAX_SHARD_SECONDS)
        print(len(rows), "rows; hard cap", round(cap, 2), "CPU-h; fingerprint", fp, flush=True)
        state = budgeted.execute(
            ledger_i.SECTION, PART, OUT / fp, shard, rows, fp, WORKERS, pin=PIN,
            max_shard_seconds=MAX_SHARD_SECONDS, hard_cap_hours=cap,
        )  # fmt: skip
        print(state, flush=True)
        ledger_i.check_caps("i1 after the run", 0.0, 0)  # the disk used, after
    finally:
        if ledger_i.v052_ledger_sha256() != before:
            raise SystemExit("the v0.5.2 ledger changed: refused")
    if state != "complete":
        raise SystemExit(state)


def _probabilities(ok: list) -> dict:
    """For each test and sub-check of class (i): the distribution of its blocks' probabilities."""
    import numpy as np

    vals: dict = {}
    for r in ok:
        for name, c in r["tests"].items():
            if c["class"] != "i":
                continue
            for sub, b in c["blocks"].items():
                if "probability" in b:
                    vals.setdefault(f"{r['kind']} {name}.{sub}", []).append(b["probability"])
    return {
        k: {"n": len(v), "min": min(v), "median": float(np.median(v)), "max": max(v),
            "below_0.95": sum(x < 0.95 for x in v)}
        for k, v in sorted(vals.items())
    }  # fmt: skip


def _estimators(ok: list) -> dict:
    """E2's and E4's operation per class, from each record's counters (the design's report)."""
    out: dict = {}
    for r in ok:
        counts = r.get("counts") if isinstance(r.get("counts"), dict) else {}
        for name, c in r["tests"].items():
            for e, own, calls in (("E2", "e2.gls", "e2.calls"), ("E4", "e4.measured", "e4.calls")):
                state = ("not reached" if not counts.get(calls) else "operated"
                         if counts.get(own) else "called, no completion")  # fmt: skip
                key = f"{r['kind']} {name} class {c['class']}: {e}"
                out.setdefault(key, Counter())[state] += 1
    return {k: dict(v) for k, v in sorted(out.items())}


def _read(rows: list, fp: str) -> tuple[list, str | None]:
    """The part's records; if ``budgeted.assembled`` refuses (a driver stop, missing shards), the
    verified shards only, read by the driver's own sidecar check, and the refusal (Codex's round 3:
    a stopped run still writes its report; nothing is reconciled or resumed to get it)."""
    import driver

    try:
        data = budgeted.assembled(
            ledger_i.SECTION, PART, OUT / fp, shard, rows, fp, WORKERS, pin=PIN,
            max_shard_seconds=MAX_SHARD_SECONDS,
        )  # fmt: skip
        return [json.loads(x) for x in data.decode().splitlines() if x.strip()], None
    except SystemExit as exc:
        run_ = driver.Run(OUT / fp, shard, rows, fp, 1.0, 1, pin=PIN,
                          max_shard_seconds=MAX_SHARD_SECONDS)  # fmt: skip
        recs = []
        for sid in run_._done():
            data_p = run_._paths(sid)[0]
            recs += [json.loads(x) for x in data_p.read_text("utf-8").splitlines() if x.strip()]
        return recs, f"the assembly was refused ({exc}); {len(recs)} of {len(rows)} verified"


def summarize() -> None:
    ledger_i.assert_bound()
    rows = schedule()
    fp = fingerprint(rows)
    recs, refusal = _read(rows, fp)
    skipped = [r for r in recs if r["status"] == "SKIPPED"]
    errors = [r for r in recs if r["status"] == "ERROR"]
    mismatched = [r for r in recs if r["status"] == "OK" and r["mismatch"]]
    ok = [r for r in recs if r["status"] == "OK" and not r["mismatch"]]
    table: dict = {"t2a": {}, "d2": {}}
    i2_population = []
    for r in recs:
        if r["status"] != "OK" or r["mismatch"]:
            continue
        for name, c in r["tests"].items():
            if r["kind"] == "t2a":
                slot = table["t2a"].setdefault(r["stratum"], Counter())
            else:
                slot = table["d2"].setdefault(name, Counter())
            slot[c["class"]] += 1
            if r["kind"] == "t2a" and c["class"] == "i" and "background" in c["non_detectable"]:
                i2_population.append(f"{r['key']}/{r['slot']}")
    sys_i = [c for r in recs if r["status"] == "OK" and not r["mismatch"] and r["kind"] == "t2a"
             for n, c in r["tests"].items() if c["class"] == "i"]  # fmt: skip
    stop = []
    if refusal:
        stop.append(refusal)
    if STOP_FILE.exists():
        stop.append("a binding stop: " + json.loads(STOP_FILE.read_text("utf-8"))["why"])
    if errors or any(c["class"] == "iii" for r in recs if r["status"] == "OK" and not r["mismatch"]
                     for c in r["tests"].values()):  # fmt: skip
        stop.append("class (iii): a code defect")
    if mismatched:
        stop.append("a rerun did not reproduce its B1 record")
    out = {
        "label": "v0.5.4 I1: what the records cannot tell (a diagnostic; decides nothing)",
        "method_status": "not_validated", "fingerprint": fp,
        "decision": "the maintainer's decision of 2026-11-12, 14:00, item 3 (#217)",
        "records": len(recs), "errors": [{k: r.get(k) for k in ("kind", "key", "slot", "index",
                                                               "reason")} for r in errors],
        "not_reproduced": [{k: r.get(k) for k in ("kind", "key", "slot", "index", "mismatch")}
                           for r in mismatched],
        "class_table": {k: {s: dict(c) for s, c in v.items()} for k, v in table.items()},
        "t2a_class_i_non_detectable_sets": dict(Counter(
            "+".join(sorted(c["non_detectable"])) for c in sys_i).most_common()),
        "t2a_class_ii_reasons": dict(Counter(
            c["why"][:160] for r in recs if r["status"] == "OK" and not r["mismatch"]
            and r["kind"] == "t2a" for c in r["tests"].values() if c["class"] == "ii"
        ).most_common()),
        "d2_reasons": {name: dict(Counter(
            f"{r['tests'][name]['class']}: {r['tests'][name]['why'][:160]}" for r in recs
            if r["status"] == "OK" and not r["mismatch"] and r["kind"] == "d2"
            and name in r["tests"]).most_common()) for name in D2_TESTS},
        "i2_population": sorted(i2_population),
        "skipped_after_a_stop": len(skipped),
        "unresolved": [f"{r.get('key', r.get('index'))}/{n}" for r in ok for n, c in
                       r["tests"].items() if c["class"] == "unresolved"],
        "class_i_probabilities": _probabilities(ok),
        "estimators": _estimators(ok),
        "stop": stop,
        "cpu_hours": round(ledger_i.part_consumption(PART), 4),
    }  # fmt: skip
    OUT_FILE.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in ("class_table", "stop", "records")}, indent=1))
    if stop:
        raise SystemExit("STOP for the maintainer: " + "; ".join(stop))


if __name__ == "__main__":
    if budgeted.LEDGER != ledger_i.HERE / "ledger.json":
        raise SystemExit("budgeted is not pointed at v0.5.4's ledger: refused")
    with ledger_i.Exclusive(f"i1 {' '.join(sys.argv[1:])}"):
        {"run": run, "summarize": summarize}[sys.argv[1]]()
