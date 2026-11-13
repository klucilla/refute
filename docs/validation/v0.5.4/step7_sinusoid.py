"""v0.5.4, second half, step 7: ``sinusoid``'s joint limit in D2 (the flag's power and the
residual, at the information bound), and T2a's feasibility reading (#217; the maintainer's
decision of 2026-11-12, night, item 4f; the frozen design is
``docs/plans/v0.5.4-h2-step7-sinusoid.md``). ``method_status: not_validated``.

For each of D2 version 5's 178 eligible fresh planets, at the generator's oracle:
- ``p_small``, stage A's residual formula at the true ephemeris;
- each applicable harmonic's ``p_flag``, the battery's own ``_sinusoid_power`` on the oracle
  covariance of its (cos, sin) on the out-of-transit cadences;
- the Fréchet block ``max(0, p_flag + p_small - 1)``.

A planet is ``sinusoid``-limited when its smallest block is below 0.95. Runs as part ``h2_step7``
under ``budgeted_v3``, one planet per shard.

Usage (from the project root, launched through ``launch_detached.py``):
``.venv/Scripts/python.exe -B docs/validation/v0.5.4/step7_sinusoid.py run``, then ``summarize``.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import types
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import i4_bound as i4  # noqa: E402,I001  (stage A's and B's modules, then ledger_i, last)
from i4_bound import ROOT, sa, b1_b14  # noqa: E402
import i4_rest as r1  # noqa: E402
import i4_rest2  # noqa: E402
import ledger_i  # noqa: E402
import budgeted  # noqa: E402
import budgeted_v3  # noqa: E402

PART = "h2_step7"
ALLOCATION = 0.5
OUT = ROOT / ".cache/v054/step7"
OUT_FILE = HERE / "h2-step7-sinusoid.json"
DESIGN = ROOT / "docs/plans/v0.5.4-h2-step7-sinusoid.md"
STEP1 = HERE / "h2-step1-floor.json"
STEP1_CASES = ROOT / ".cache/v054/step1/cases.json"
WORKERS = 12
PIN = tuple(range(8, 32, 2))
MAX_SHARD_SECONDS = 600.0
REQUIRED = 0.95
BAND = 0.02  # about 4 Monte Carlo standard errors of a 2,000-draw power near 0.95: uncertain
COND_MAX = 1e12
D2_ALLOWED = 22
RESERVE_TOKENS = 750_000  # the rest of the plan's reviews, reserved before the run
REASON = ("the maintainer's decision of 2026-11-12 (night), item 4f (#217): step 7, sinusoid's "
          "joint limit in D2 (h2_step7, budgeted_v3)")  # fmt: skip


def _seed(index: int, label: str) -> int:
    text = f"refute-v054-step7:{index}:{label}"
    return int(hashlib.sha256(text.encode()).hexdigest(), 16) % (2**32)


def one(index: int) -> dict:
    from refute.packs.tess.battery_v5 import _sinusoid_power
    from refute.packs.tess.battery_v52 import HARMONICS
    from refute.packs.tess.calib05 import c1

    data, truth = c1.generate("P", c1.development_seed("P", index))
    _, _, p4 = b1_b14.fv.plans()
    sp, domain = p4.stronger, p4.v051.sinusoid_harmonic_max_period_days
    t, sector = data.lc.time, data.lc.sector
    sigma_w = truth["sigma_white_ppm"] * 1e-6
    sigma_r = sigma_w / 2.0 if truth["correlated"] else 0.0
    scale = sa.sector_scale(sector, data.lc.flux)
    cand = types.SimpleNamespace(
        period=truth["period_days"],
        t0=truth["t0_btjd"],
        duration=truth["duration_days"],
        depth=float(truth["depth"]),
    )
    applicable = [(lab, f) for lab, f in HARMONICS if cand.period * f < domain]
    rec: dict = {"index": index, "applicable": [lab for lab, _ in applicable]}
    if ("P/2", 0.5) not in applicable:
        rec["status"] = "OUTSIDE_DOMAIN"
        return rec
    periods = [cand.period * f for _, f in applicable]
    # stage A's sinusoid_bound, its Gram matrix validated first (Codex, h2-step7 round 2)
    dtb = np.abs(np.mod(t - cand.t0 + 0.5 * cand.period, cand.period) - 0.5 * cand.period)
    rcols = [-(dtb <= cand.duration / 2.0).astype(float)]
    rcols += [(sector == s).astype(float) for s in np.unique(sector)]
    for period in periods:
        ph = 2.0 * math.pi * t / period
        rcols += [np.cos(ph), np.sin(ph)]
    rgram = sa.gram(t, sector, [c * scale for c in rcols], sigma_w, sigma_r)
    why = _invalid_matrix(rgram)
    if why:
        rec.update({"status": "UNK", "reason": f"the residual Gram matrix: {why}"})
        return rec
    s_box = float(math.sqrt(np.linalg.inv(rgram)[0, 0]))
    reference = sa.sinusoid_bound(t, sector, cand, periods, sigma_w, sigma_r, scale)
    if not (math.isfinite(s_box) and s_box > 0) or abs(s_box / reference - 1.0) > 1e-9:
        rec.update({"status": "UNK", "reason": f"sigma_box {s_box} against stage A's {reference}"})
        return rec
    p_small = 0.5 * math.erfc(
        -((sa.SMALL_FRACTION * cand.depth / s_box) - sa.SMALL_Z) / math.sqrt(2.0)
    )
    half = cand.duration / 2.0 + sp.sinusoid_mask_durations * cand.duration
    dt = np.abs(np.mod(t - cand.t0 + 0.5 * cand.period, cand.period) - 0.5 * cand.period)
    keep = dt > half
    tk, sk, scl = t[keep], sector[keep], scale[keep]
    cols = [(sk == s).astype(float) for s in np.unique(sk)]
    n_off = len(cols)
    for period in periods:
        phase = 2.0 * math.pi * tk / period
        cols += [np.cos(phase), np.sin(phase)]
    gram = sa.gram(tk, sk, [c * scl for c in cols], sigma_w, sigma_r)
    why = _invalid_matrix(gram)
    if why or not _probability(p_small):
        rec.update({"status": "UNK", "reason": why or f"p_small not a probability: {p_small}"})
        return rec
    inv = np.linalg.inv(gram)
    blocks, flags = {}, {}
    for j, (label, _) in enumerate(applicable):
        cov = inv[n_off + 2 * j : n_off + 2 * j + 2, n_off + 2 * j : n_off + 2 * j + 2]
        why = _invalid_matrix(cov)
        if why:  # _sinusoid_power would return 0 on a failed Cholesky: UNK, never a power
            rec.update({"status": "UNK", "reason": f"{label}: {why}"})
            return rec
        flags[label] = float(_sinusoid_power(cov, cand.depth, cand.depth, sp, _seed(index, label)))
        if not _probability(flags[label]):
            rec.update({"status": "UNK", "reason": f"{label}: p_flag {flags[label]}"})
            return rec
        blocks[label] = max(0.0, flags[label] + p_small - 1.0)
    low = min(blocks.values())
    # below the band: the certificate fails; above it: it holds; inside it: uncertain (UNK)
    limited = True if low < REQUIRED - BAND else False if low >= REQUIRED + BAND else None
    rec.update({"status": "OK", "p_small_true": p_small, "sigma_box": s_box, "p_flag": flags,
                "blocks": blocks, "min_block": low, "limited": limited,
                "out_of_transit_cadences": int(keep.sum())})  # fmt: skip
    return rec


def _probability(p) -> bool:
    return isinstance(p, float) and math.isfinite(p) and 0.0 <= p <= 1.0


def _invalid_matrix(m) -> str | None:
    """A symmetric matrix that is finite, positive definite and not ill-conditioned (scaled), or
    the reason it is not."""
    if not np.all(np.isfinite(m)):
        return "a non-finite entry"
    d = np.sqrt(np.clip(np.diag(m), 0.0, None))
    if np.any(d <= 0):
        return "a zero diagonal"
    ms = m / np.outer(d, d)
    try:
        np.linalg.cholesky(ms)
    except np.linalg.LinAlgError:
        return "not positive definite"
    cond = float(np.linalg.cond(ms))
    return None if math.isfinite(cond) and cond <= COND_MAX else f"ill-conditioned ({cond:.3g})"


def shard(index: int) -> bytes:
    try:
        rec = one(index)
    except Exception as exc:  # noqa: BLE001 - a failed computation is UNK, recorded
        rec = {"index": index, "status": "ERROR", "reason": repr(exc)}
    return (json.dumps(rec, sort_keys=True) + "\n").encode()


def schedule() -> list:
    rows = [(sid, a["index"]) for sid, a in i4.schedule() if a["set"] == "fresh"]
    if len(rows) != 178:
        raise SystemExit(f"{len(rows)} fresh planets, not 178: STOP")
    return rows


def fingerprint(rows: list) -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    for path in (Path(__file__), DESIGN, HERE / "ledger_i.py", HERE / "budgeted_v3.py",
                 i4.STAGE_A / "d2_bounds.py", i4.STAGE_B / "b1_b14.py",
                 ROOT / "docs/validation/v0.5.1/feasibility/forecast.py",
                 HERE / "i4-bound.json", STEP1):  # fmt: skip
        h.update(hashlib.sha256(path.read_bytes()).digest())
    h.update(json.dumps(rows, sort_keys=True).encode())
    return h.hexdigest()[:16]


def run() -> None:
    ledger_i.assert_bound()
    rows = schedule()
    fp = fingerprint(rows)
    book = ledger_i._rows()
    if PART not in book:
        with ledger_i.Exclusive("step7 transfer"):
            ledger_i._transfer("h2_unallocated", PART, ALLOCATION, REASON)
    ledger_i.refuse_new_identity(PART, fp, rows)
    ledger_i.check_caps("step7 run", reserve_days=0.2, reserve_tokens=RESERVE_TOKENS,
                        in_h1=False, reserve_bytes=len(rows) * 5_000 + 50_000_000)  # fmt: skip
    cap = ledger_i.hard_cap(PART, WORKERS, MAX_SHARD_SECONDS)
    print(f"{PART}: {len(rows)} rows; hard cap {cap:.3f} CPU-h; {WORKERS} workers; fp {fp}",
          flush=True)  # fmt: skip
    with ledger_i.Exclusive("step7 run"):
        state = budgeted_v3.execute(
            ledger_i.SECTION, PART, OUT / fp, shard, rows, fp, WORKERS, pin=PIN,
            max_shard_seconds=MAX_SHARD_SECONDS, hard_cap_hours=cap, pause_at=r1.PAUSE_AT,
        )  # fmt: skip
    print(state, flush=True)
    ledger_i.check_caps("step7 after the run", 0.0, 0, in_h1=False)
    if state != "complete":
        raise SystemExit(f"STOP for the maintainer: {state}")


def summarize() -> None:
    ledger_i.assert_bound()
    rows = schedule()
    fp = fingerprint(rows)
    data = budgeted.assembled(ledger_i.SECTION, PART, OUT / fp, shard, rows, fp, WORKERS, pin=PIN,
                              max_shard_seconds=MAX_SHARD_SECONDS)  # fmt: skip
    recs = {r["index"]: r for r in (json.loads(x) for x in data.decode().splitlines() if x)}
    rows4 = i4.schedule()
    i4recs, refusal, _ = i4_rest2._records(rows4, i4.fingerprint(rows4))
    if refusal:
        raise SystemExit(f"I4: {refusal}: STOP")
    fresh = {r["index"]: r for r in i4recs if r.get("set") == "fresh"}
    step1 = json.loads(STEP1.read_text("utf-8"))
    cases_text = STEP1_CASES.read_text("utf-8")
    if hashlib.sha256(cases_text.encode()).hexdigest() != step1["per_case_detail_sha256"]:
        raise SystemExit("step 1's per-case detail does not match its record: STOP")
    cases = json.loads(cases_text)
    data_losses = {c["index"] for c in cases["d2"]
                   if any("DATA" in b["categories"] for b in c["blockers"])}  # fmt: skip
    ok = {i: r for i, r in recs.items() if r.get("status") == "OK"}
    l_sin = {i for i, r in ok.items() if r["limited"] is True}
    uncertain = {i for i, r in ok.items() if r["limited"] is None}
    unk_sin = {i for i, r in recs.items() if r.get("status") in ("UNK", "ERROR")}
    errors = sorted(i for i, r in recs.items() if r.get("status") == "ERROR")
    outside = {i for i, r in recs.items() if r.get("status") == "OUTSIDE_DOMAIN"}
    valid4 = {i: r for i, r in fresh.items() if r.get("status") == "OK" and not r.get("mismatch")
              and not r["nuisance"]["invalid"] and "power_nuisance" in r}  # fmt: skip
    l_oe = {i for i, r in valid4.items() if r["power_nuisance"] < REQUIRED}
    e4 = set(recs) - set(valid4)
    # the recorded sinusoid status of each planet (D2 version 5): a warning FAIL keeps retention
    with i4._ledger(i4.ledger_b):
        d2recs, _, _, _ = i4.b1_d2d4_rest.complete_records()
    status = {r["index"]: (r.get("v5_tests") or {}).get("sinusoid", {}).get("status")
              for r in d2recs if r.get("status") == "OK"}  # fmt: skip

    def kind(i):
        if i in l_sin:
            return "certificate fails"
        if i in uncertain:
            return "uncertain"
        return "unknown" if i in unk_sin else "certificate holds"

    overlap = Counter(f"{kind(i)} / recorded {status.get(i)}" for i in recs)
    warned = {i for i in l_sin if status.get(i) == "FAIL"}  # a warning FAIL keeps the planet
    floor = data_losses | l_oe | (l_sin - warned)
    upper = data_losses | l_oe | l_sin | uncertain | e4 | unk_sin
    if len(upper) <= D2_ALLOWED:
        outcome = (
            "a conditional margin (the generator's model, the battery's own Fréchet "
            "certificate at the bound, every other loss recovered)"
        )
    else:
        outcome = "INCONCLUSIVE"
    agree = [abs(r["p_small_true"] - fresh[i]["sinusoid_small_at_bound"])
             for i, r in ok.items() if "sinusoid_small_at_bound" in fresh.get(i, {})]  # fmt: skip
    far = sum(d > 0.05 for d in agree)
    stops = []
    if errors:
        stops.append(f"{len(errors)} planets raised an error")
    if len(agree) < 0.9 * len(ok):
        stops.append(f"p_small compared with I4's on only {len(agree)} of {len(ok)} planets")
    if agree and far > 0.10 * len(agree):
        stops.append("p_small disagrees with I4's on more than 10 % of the planets")
    if stops:  # a result with a stop is never a margin
        outcome = "INCONCLUSIVE (a stop)"
    t2a_sin = Counter("+".join(b["categories"]) for c in cases["t2a"] for b in c["blockers"]
                      if b["test"] == "sinusoid")  # fmt: skip
    doc = {
        "label": "v0.5.4 step 7: sinusoid's Fréchet certificate at the information bound (the "
        "battery's own rule under the generator's model; not a universal impossibility; decides "
        "nothing by itself)",
        "method_status": "not_validated", "fingerprint": fp,
        "decision": "the maintainer's decision of 2026-11-12 (night), item 4f (#217)",
        "design": "docs/plans/v0.5.4-h2-step7-sinusoid.md",
        "d2": {
            "planets": len(recs), "certificate_fails": len(l_sin),
            "certificate_fails_planets": sorted(l_sin),
            "certificate_fails_with_a_recorded_warning_fail": len(warned),
            "uncertain_within_the_band": sorted(uncertain), "unknown": sorted(unk_sin),
            "outside_domain": sorted(outside), "odd_even_limited (I4)": len(l_oe),
            "i4_invalid (E)": len(e4), "data_losses (step 1)": len(data_losses),
            "overlap_with_the_recorded_status": dict(sorted(overlap.items())),
            "floor": len(floor), "floor_upper": len(upper), "allowed": D2_ALLOWED,
            "margin_under_the_floor": D2_ALLOWED - len(floor), "outcome": outcome,
            "min_block_quantiles": [float(q) for q in np.quantile(
                [r["min_block"] for r in ok.values()], [0.0, 0.1, 0.5, 0.9, 1.0])]
            if ok else None,
            "p_small_vs_i4": {"compared": len(agree), "differ_by_more_than_0.05": far},
        },
        "t2a": {"outcome": "INCONCLUSIVE (by design: no true covariance for real hosts)",
                "sinusoid_blockers_by_category_set (step 1)": dict(t2a_sin)},
        "stops": stops,
        "cpu_hours": round(ledger_i.part_consumption(PART), 4),
    }  # fmt: skip
    text = json.dumps(doc, indent=1, sort_keys=True) + chr(10)
    OUT_FILE.write_text(text, "utf-8", newline=chr(10))
    print(json.dumps({k: doc["d2"][k] for k in ("certificate_fails", "floor", "floor_upper",
                                                "outcome")}, indent=1))  # fmt: skip
    if stops:
        raise SystemExit("STOP for the maintainer: " + "; ".join(stops))


if __name__ == "__main__":
    if budgeted.LEDGER != ledger_i.HERE / "ledger.json":
        raise SystemExit("budgeted is not pointed at v0.5.4's ledger: refused")
    {"run": run, "summarize": summarize}[sys.argv[1]]()
