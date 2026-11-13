"""v0.5.4, second half, step 4: B0's oracle with stellar errors of 1, 2 and 3 % (#217; the
maintainer's decision of 2026-11-12, night, item 4c; the frozen design is
``docs/plans/v0.5.4-h2-step4-b0-errors.md``). ``method_status: not_validated``.

B0's eligible binaries (its own records, read through its reviewed reader), each regenerated, and
B0's oracle (``d1_routes.nearest_with_bounds`` and ``forecast.mahalanobis2``, unchanged) at
radius and mass errors of 1, 2 and 3 %, with a 5 % check against B0's recorded distances.
Part ``h2_step4`` under ``budgeted_v3``.

Usage (from the project root, launched through ``launch_detached.py``):
``.venv/Scripts/python.exe -B docs/validation/v0.5.4/step4_b0_errors.py run``, then ``summarize``.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from pathlib import Path
from statistics import NormalDist

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import i4_bound as i4  # noqa: E402,I001  (stage A's and B's modules, then ledger_i, last)
from i4_bound import ROOT, ledger_b  # noqa: E402
import i4_rest as r1  # noqa: E402
import ledger_i  # noqa: E402
import budgeted  # noqa: E402
import budgeted_v3  # noqa: E402

sys.path.insert(0, str(i4.STAGE_B))
import d1_bound as b0  # noqa: E402  (ledger_b is already imported: no rebinding)

PART = "h2_step4"
ALLOCATION = 3.0
OUT = ROOT / ".cache/v054/step4"
OUT_FILE = HERE / "h2-step4-b0-errors.json"
DESIGN = ROOT / "docs/plans/v0.5.4-h2-step4-b0-errors.md"
B0_RECORD = i4.STAGE_B / "d1-bound.json"
SETTINGS = (0.01, 0.02, 0.03)
CHECK = 0.05
CHECK_PER_FAMILY = 10
ELIGIBLE = {"EB1": 381, "EB2": 373}
WORKERS = 12
PIN = tuple(range(8, 32, 2))
MAX_SHARD_SECONDS = 1200.0
PER_SHARD = 10
RESERVE_TOKENS = 600_000
PRIMARY_ALPHA = b0.PRIMARY_ALPHA
REASON = ("the maintainer's decision of 2026-11-12 (night), item 4c (#217): step 4, B0's oracle at "
          "1, 2 and 3 % (h2_step4, budgeted_v3)")  # fmt: skip


def b0_records() -> list[dict]:
    """B0's records, through its own reviewed reader on v0.5.3's ledger."""
    rows = b0.schedule()
    # B0's fingerprint as its committed record states it: recomputing it today would hash today's
    # code; the driver checks every shard's sidecar against this one
    fp = json.loads(B0_RECORD.read_text("utf-8"))["fingerprint"]
    with i4._ledger(ledger_b):
        data = budgeted.assembled(
            ledger_b.SECTION, b0.PART, b0.OUT / fp, b0.shard, rows, fp, b0.WORKERS, pin=b0.PIN,
            max_shard_seconds=b0.MAX_SHARD_SECONDS,
        )  # fmt: skip
    return [json.loads(x) for x in data.decode().splitlines() if x.strip()]


def schedule(recs: list[dict]) -> list:
    elig = {f: [r for r in recs if r["family"] == f and r.get("status") == "OK"
                and r.get("eligible") and "catalog" in r] for f in b0.FAMILIES}  # fmt: skip
    if {f: len(v) for f, v in elig.items()} != ELIGIBLE:
        raise SystemExit(f"B0's eligible counts are {[len(v) for v in elig.values()]}: STOP")
    checks = {f: {r["index"] for r in elig[f][:CHECK_PER_FAMILY]} for f in b0.FAMILIES}
    rows = []
    chunks = {f: [elig[f][k : k + PER_SHARD] for k in range(0, len(elig[f]), PER_SHARD)]
              for f in b0.FAMILIES}  # fmt: skip
    for j in range(max(len(c) for c in chunks.values())):
        for f in b0.FAMILIES:
            if j < len(chunks[f]):
                items = [{"index": r["index"], "seed": r["seed"], "found": r["found"],
                          "check": r["index"] in checks[f],
                          "b0_catalog_distance": r["catalog"]["distance"]}
                         for r in chunks[f][j]]  # fmt: skip
                rows.append((f"{f}-{j:03d}", {"family": f, "items": items}))
    probe = {arg["family"] for _, arg in budgeted.checkpoint(rows)}
    if probe != set(b0.FAMILIES):
        raise SystemExit(f"the checkpoint does not cover both families: {sorted(probe)}")
    return rows


def distance(family: str, item: dict, error: float) -> dict:
    from refute.packs.tess.calib05 import c1

    s = int(item["seed"])
    data, truth = c1.generate(family, s)
    t, sector = data.lc.time, data.lc.sector
    factor = b0.trend_factor(family, s, t)
    sigma_w = truth["sigma_white_ppm"] * 1e-6
    sigma_r = sigma_w / 2.0 if truth["correlated"] else 0.0
    bounds = b0.d1_routes.effective_bounds(error, error)
    radius, r, at_bound = b0.d1_routes.nearest_with_bounds(
        b0.forecast, t, truth, item["found"], error, bounds
    )
    d = math.sqrt(b0.forecast.mahalanobis2(t, sector, r * factor, sigma_w, sigma_r))
    return {"distance": d, "effective_radius": radius, "at_bound": bool(at_bound)}


def shard(arg: dict) -> bytes:
    lines = []
    for item in arg["items"]:
        rec: dict = {"family": arg["family"], "index": item["index"]}
        try:
            for e in SETTINGS:
                rec[f"{e:g}"] = distance(arg["family"], item, e)
            if item["check"]:
                d5 = distance(arg["family"], item, CHECK)["distance"]
                rec["check_5pct"] = {"distance": d5, "b0": item["b0_catalog_distance"]}
            rec["status"] = "OK"
        except Exception as exc:  # noqa: BLE001 - recorded, a stop at the summary
            rec.update(status="ERROR", reason=repr(exc))
        lines.append(json.dumps(rec, sort_keys=True))
    return ("\n".join(lines) + "\n").encode()


def fingerprint(rows: list) -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    for path in (Path(__file__), DESIGN, HERE / "ledger_i.py", HERE / "budgeted_v3.py",
                 i4.STAGE_B / "d1_bound.py", B0_RECORD,
                 b0.FEAS / "d1_routes.py", b0.FEAS / "forecast.py"):  # fmt: skip
        h.update(hashlib.sha256(path.read_bytes()).digest())
    h.update(json.loads(B0_RECORD.read_text("utf-8"))["fingerprint"].encode())
    h.update(json.dumps(rows, sort_keys=True).encode())
    return h.hexdigest()[:16]


def run() -> None:
    ledger_i.assert_bound()
    rows = schedule(b0_records())
    fp = fingerprint(rows)
    if PART not in ledger_i._rows():
        with ledger_i.Exclusive("step4 transfer"):
            ledger_i._transfer("h2_unallocated", PART, ALLOCATION, REASON)
    ledger_i.refuse_new_identity(PART, fp, rows)
    ledger_i.check_caps("step4 run", reserve_days=0.3, reserve_tokens=RESERVE_TOKENS,
                        in_h1=False, reserve_bytes=len(rows) * 20_000 + 50_000_000)  # fmt: skip
    cap = ledger_i.hard_cap(PART, WORKERS, MAX_SHARD_SECONDS)
    print(f"{PART}: {len(rows)} shards; hard cap {cap:.3f} CPU-h; {WORKERS} workers; fp {fp}",
          flush=True)  # fmt: skip
    with ledger_i.Exclusive("step4 run"):
        state = budgeted_v3.execute(
            ledger_i.SECTION, PART, OUT / fp, shard, rows, fp, WORKERS, pin=PIN,
            max_shard_seconds=MAX_SHARD_SECONDS, hard_cap_hours=cap, pause_at=r1.PAUSE_AT,
            units=lambda arg: len(arg["items"]),
        )  # fmt: skip
    print(state, flush=True)
    ledger_i.check_caps("step4 after the run", 0.0, 0, in_h1=False)
    if state != "complete":
        raise SystemExit(f"STOP for the maintainer: {state}")


SUMMARY_RESERVE_HOURS = 0.03  # the summary's estimated cost (about a processor-minute), doubled


def summarize() -> None:
    """The caps, and the charges' room for the summary's reserve, are checked first (a stop there
    ends before any record). The summary's own processor time, mostly the bootstrap, is charged in
    a ``finally`` under a name unique to this invocation; the record is written only after that
    charge succeeded (B0's protection)."""
    import time

    ledger_i.assert_bound()
    ledger_i.check_caps("step4 summarize", reserve_days=0.05, reserve_tokens=0, in_h1=False)
    room = ledger_i.CHARGES_ROOM - ledger_i._charges()
    if room < SUMMARY_RESERVE_HOURS:
        raise SystemExit(f"the charges' room ({room:.3f} CPU-h) cannot hold the summary: STOP")
    started = time.process_time()
    import uuid

    stamp = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime()) + "-" + uuid.uuid4().hex[:12]
    try:
        result = _summarize()
    finally:
        hours = (time.process_time() - started) / 3600.0
        ledger_i.charge(f"{PART}_summarize_{stamp}", hours,
                        "the summary's own CPU, outside the driver")  # fmt: skip
    _write(*result)
    stops = result[-1]
    print(json.dumps(result[2], indent=1))
    if stops:
        raise SystemExit("STOP for the maintainer: " + "; ".join(stops))


def _summarize() -> tuple:
    b0recs = b0_records()
    rows = schedule(b0recs)
    fp = fingerprint(rows)
    data = budgeted.assembled(ledger_i.SECTION, PART, OUT / fp, shard, rows, fp, WORKERS, pin=PIN,
                              max_shard_seconds=MAX_SHARD_SECONDS)  # fmt: skip
    recs = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
    nd = NormalDist()
    rng = np.random.default_rng(b0.BOOTSTRAP_SEED)
    stops = []
    errors = [f"{r['family']}-{r['index']}" for r in recs if r.get("status") != "OK"]
    if errors:
        stops.append(f"{len(errors)} binaries raised an error")

    def finite_positive(x) -> bool:
        return isinstance(x, (int, float)) and math.isfinite(x) and x > 0

    bad_check = [
        f"{r['family']}-{r['index']}"
        for r in recs
        if "check_5pct" in r
        and not (
            finite_positive(r["check_5pct"]["distance"])
            and finite_positive(r["check_5pct"]["b0"])
            and abs(r["check_5pct"]["distance"] / r["check_5pct"]["b0"] - 1.0) <= 1e-6
        )
    ]
    checked = sum("check_5pct" in r for r in recs)
    if bad_check or checked != CHECK_PER_FAMILY * len(b0.FAMILIES):
        stops.append(f"the 5 % check: {checked} checked, {len(bad_check)} differ")
    for r in recs:  # every distance is checked before any aggregate
        for e in SETTINGS:
            if r.get("status") == "OK" and not finite_positive(r[f"{e:g}"]["distance"]):
                stops.append(f"{r['family']}-{r['index']} {e:g}: a non-finite distance")
    out: dict = {}
    if stops:  # no aggregate, and so no favourable outcome, is computed under a stop
        outcomes = {f"{e:g}": "INCONCLUSIVE (a stop)" for e in SETTINGS}
        return fp, out, outcomes, errors, checked, bad_check, stops
    for f in b0.FAMILIES:
        attempted = sum(r["family"] == f for r in b0recs)
        ok = [r for r in recs if r["family"] == f and r.get("status") == "OK"]
        n_proj = round(b0.C1_PRIME_PER_FAMILY * len(ok) / attempted) if attempted else 0
        k = b0.forecast.max_count(n_proj)
        fam: dict = {"attempted": attempted, "eligible": len(ok), "c1_prime_projection": n_proj,
                     "d1_allowance": k, "settings": {}}  # fmt: skip
        for e in SETTINGS:
            d = np.array([r[f"{e:g}"]["distance"] for r in ok])
            block: dict = {
                "median_distance": float(np.median(d)),
                "at_bound": sum(r[f"{e:g}"]["at_bound"] for r in ok),
                "alphas": {},
            }
            for alpha in b0.ALPHAS:
                z = nd.inv_cdf(1.0 - alpha)
                p = np.array([nd.cdf(z - x) for x in d])
                probs = [
                    b0.forecast.poisson_binomial_cdf(rng.choice(p, size=n_proj, replace=True), k)
                    for _ in range(b0.BOOTSTRAP)
                ]
                block["alphas"][str(alpha)] = {
                    "non_rejection_fraction": float(p.mean()),
                    "expected_non_rejected_at_projection": float(p.mean() * n_proj),
                    "pass_probability_median": float(np.median(probs)),
                    "pass_probability_p95": float(np.percentile(probs, 95)),
                }
            fam["settings"][f"{e:g}"] = block
        out[f] = fam
    outcomes = {}
    a = str(PRIMARY_ALPHA)
    for e in SETTINGS:
        key = f"{e:g}"
        blocks = [out[f]["settings"].get(key, {}).get("alphas", {}).get(a) for f in b0.FAMILIES]
        if any(b is None for b in blocks) or stops:
            outcomes[key] = "INCONCLUSIVE"
            continue
        ks = [out[f]["d1_allowance"] for f in b0.FAMILIES]
        if all(b["expected_non_rejected_at_projection"] <= k and b["pass_probability_median"]
               >= 0.5 for b, k in zip(blocks, ks, strict=True)):  # fmt: skip
            outcomes[key] = "the scenario leaves a margin (under B0's per-planet assumptions)"
        elif any(b["expected_non_rejected_at_projection"] > k and b["pass_probability_median"]
                 < 0.05 for b, k in zip(blocks, ks, strict=True)):  # fmt: skip
            outcomes[key] = "the scenario leaves none (under B0's per-planet assumptions)"
        else:
            outcomes[key] = "INCONCLUSIVE"
    return fp, out, outcomes, errors, checked, bad_check, stops


def _write(fp, out, outcomes, errors, checked, bad_check, stops) -> None:
    doc = {
        "label": "v0.5.4 step 4: B0's oracle at stellar errors of 1, 2 and 3 % (a diagnostic under "
        "B0's per-planet assumptions; never a D1 draft)",
        "method_status": "not_validated", "fingerprint": fp,
        "decision": "the maintainer's decision of 2026-11-12 (night), item 4c (#217)",
        "design": "docs/plans/v0.5.4-h2-step4-b0-errors.md",
        "families": out, "outcomes_at_alpha_0.0027": outcomes, "errors": errors,
        "five_percent_check": {"checked": checked, "differ_or_invalid": bad_check},
        "stops": stops,
        "pass_probability_note": "the median and p95 over bootstrap cohorts are a forecast by "
        "resampling, not a confidence interval (B0's design)",
        "cpu_hours": round(ledger_i.part_consumption(PART), 4),
    }  # fmt: skip
    text = json.dumps(doc, indent=1, sort_keys=True) + chr(10)
    OUT_FILE.write_text(text, "utf-8", newline=chr(10))


if __name__ == "__main__":
    if budgeted.LEDGER != ledger_i.HERE / "ledger.json":
        raise SystemExit("budgeted is not pointed at v0.5.4's ledger: refused")
    {"run": run, "summarize": summarize}[sys.argv[1]]()
