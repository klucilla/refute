"""v0.5.4, second half, step 5: the decomposition of E2's distance to the information bound
(#217; the maintainer's decision of 2026-11-12, night, item 4d; the frozen design is
``docs/plans/v0.5.4-h2-step5-gap.md``). ``method_status: not_validated``.

For each of D2 version 5's 178 eligible fresh planets, the odd-even contrast's Fisher bound under
the generator's model in six variants (V0 known, V_trend, V_win, V_box, V_win+box, V_all), compared
with E2's own error as I4 recorded it. One planet per shard, part ``h2_step5`` under
``budgeted_v3``.

Usage (from the project root, launched through ``launch_detached.py``):
``.venv/Scripts/python.exe -B docs/validation/v0.5.4/step5_gap.py run``, then ``summarize``.
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
import i4_bound as i4  # noqa: E402,I001  (stage A's and B's modules, then ledger_i, last)
from i4_bound import ROOT, sa, b1_b14  # noqa: E402
import i4_rest as r1  # noqa: E402
import i4_rest2  # noqa: E402
import ledger_i  # noqa: E402
import budgeted  # noqa: E402
import budgeted_v3  # noqa: E402

PART = "h2_step5"
ALLOCATION = 0.5
OUT = ROOT / ".cache/v054/step5"
OUT_FILE = HERE / "h2-step5-gap.json"
DESIGN = ROOT / "docs/plans/v0.5.4-h2-step5-gap.md"
STEP1 = HERE / "h2-step1-floor.json"
STEP1_CASES = ROOT / ".cache/v054/step1/cases.json"
WORKERS = 12
PIN = tuple(range(8, 32, 2))
MAX_SHARD_SECONDS = 600.0
REQUIRED = 0.95
OUTER = 1.5  # A0's baseline_outer_durations
COND_MAX = 1e12
RESERVE_TOKENS = 750_000  # the rest of the plan's reviews, reserved before the run
VARIANTS = ("V0", "V_trend", "V_win", "V_box", "V_win+box", "V_all")
TRAPEZOID = ("V0", "V_trend", "V_win")
REASON = ("the maintainer's decision of 2026-11-12 (night), item 4d (#217): step 5, E2's gap "
          "decomposition (h2_step5, budgeted_v3)")  # fmt: skip


def precision_apply(t, sector, x, sigma_w, sigma_r) -> np.ndarray:
    """``Sigma^-1 X`` for Sigma = sigma_w^2 I + sigma_r^2 K, K exponential per sector (the same
    banded solve as ``forecast.mahalanobis2``, for a matrix)."""
    from scipy.linalg import solve_banded

    if sigma_r <= 0:
        return x / sigma_w**2
    out = np.zeros_like(x)
    pou = sa._wp1()._precision_ou
    for n in np.unique(sector):
        sel = sector == n
        ts, xs = t[sel], x[sel]
        diag, off = pou(ts)
        ax = diag[:, None] * xs
        ax[:-1] += off[:, None] * xs[1:]
        ax[1:] += off[:, None] * xs[:-1]
        ab = np.zeros((3, ts.size))
        ab[0, 1:] = sigma_w**2 * off
        ab[1] = sigma_w**2 * diag + sigma_r**2
        ab[2, :-1] = sigma_w**2 * off
        out[sel] = solve_banded((1, 1), ab, ax)
    return out


def _sigma(t, sector, cols, sigma_w, sigma_r, target=None):
    """The contrast's σ (first two columns) in the target's units, its scaled condition, the raw
    σ and the response ``r`` to ``target`` columns (1 without a target)."""
    x = np.column_stack(cols)
    px = precision_apply(t, sector, x, sigma_w, sigma_r)
    g = x.T @ px
    d = np.sqrt(np.clip(np.diag(g), 0.0, None))
    if np.any(d <= 0) or not np.all(np.isfinite(g)):
        return None, float("nan"), None, None
    gs = g / np.outer(d, d)
    try:
        np.linalg.cholesky(gs)
    except np.linalg.LinAlgError:
        return None, float("nan"), None, None
    cond = float(np.linalg.cond(gs))
    if not math.isfinite(cond) or cond > COND_MAX:
        return None, cond, None, None
    c = np.zeros(x.shape[1])
    c[0], c[1] = 1.0, -1.0
    var = float(c @ np.linalg.solve(g, c))
    if not (math.isfinite(var) and var > 0):
        return None, cond, None, None
    sigma = math.sqrt(var)
    if target is None:
        return sigma, cond, sigma, 1.0
    xt = np.column_stack(target)
    gbt = px.T @ xt  # X_b^T Sigma^-1 X_t
    ct = np.array([1.0, -1.0])
    r = float(c @ np.linalg.solve(g, gbt @ ct)) / 2.0
    if not (math.isfinite(r) and r > 0):
        return None, cond, sigma, None
    return sigma / r, cond, sigma, r


def one(index: int) -> dict:
    from refute.packs.tess.calib05 import c1

    data, truth = c1.generate("P", c1.development_seed("P", index))
    t, sector = data.lc.time, data.lc.sector
    sigma_w = truth["sigma_white_ppm"] * 1e-6
    sigma_r = sigma_w / 2.0 if truth["correlated"] else 0.0
    shape, _, _ = i4.shape_and_derivatives(t, truth)
    trend = sa.trend_multiplier(t, truth)
    p, t0, dur = truth["period_days"], truth["t0_btjd"], truth["duration_days"]
    epoch = np.round((t - t0) / p).astype(int)
    odd, even = epoch % 2 != 0, epoch % 2 == 0
    dt = np.abs(np.mod(t - t0 + 0.5 * p, p) - 0.5 * p)
    box = (dt <= dur / 2.0).astype(float)

    def contrast(unit):
        return [np.where(odd, -unit, 0.0), np.where(even, -unit, 0.0)]

    def offsets(mask):
        return [((sector == s) & mask).astype(float) for s in np.unique(sector[mask])]

    def quadratics(mask):
        out = []
        for s in np.unique(sector[mask]):
            sel = (sector == s) & mask
            tc = np.where(sel, t - np.mean(t[sel]), 0.0)
            out += [sel.astype(float), tc, tc**2]
        return out

    def trend_derivs():
        tr = truth.get("trend")
        if not tr:
            return []
        arg = 2 * np.pi * t / tr["period_days"] + tr["phase"]
        a = tr["amplitude"]
        # the generator's flux is (1 - D shape) x trend: each trend derivative carries the transit
        transit = 1.0 - truth["depth"] * shape
        return [
            transit * np.sin(arg),
            transit * a * np.cos(arg),
            transit * a * np.cos(arg) * (-2 * np.pi * t / tr["period_days"] ** 2),
        ]

    win = dt <= dur / 2.0 + OUTER * dur
    wid = np.round((t - t0) / p).astype(int)

    def windows():
        out = []
        for s in np.unique(sector[win]):
            for e in np.unique(wid[win & (sector == s)]):
                sel = win & (sector == s) & (wid == e)
                if sel.sum() < 3:
                    continue
                tc = np.where(sel, t - np.mean(t[sel]), 0.0)
                out += [sel.astype(float), tc]
        return out

    # E2 measures a box on a trapezoid: its response to a unit trapezoid depth is the shape's mean
    # over the box, so its error is converted to trapezoid units by the same rule as the box's
    r_e2 = float(np.mean(shape[box > 0])) if np.any(box > 0) else float("nan")
    rec: dict = {"index": index, "status": "OK", "sigma": {}, "condition": {}, "raw_sigma": {},
                 "response": {}, "r_e2": r_e2}  # fmt: skip
    full = np.ones_like(t, dtype=bool)
    specs = {
        "V0": (full, contrast(shape * trend) + offsets(full), None),
        "V_trend": (full, contrast(shape * trend) + quadratics(full) + trend_derivs(), None),
        "V_win": (win, contrast(shape * trend) + windows(), None),
        "V_box": (full, contrast(box * trend) + offsets(full), contrast(shape * trend)),
        "V_win+box": (win, contrast(box * trend) + windows(), contrast(shape * trend)),
        "V_all": (win, contrast(box * trend) + windows() + trend_derivs(), contrast(shape * trend)),
    }
    for name, (mask, cols, target) in specs.items():
        tgt = None if target is None else [c[mask] for c in target]
        s, cond, raw, r = _sigma(
            t[mask], sector[mask], [c[mask] for c in cols], sigma_w, sigma_r, tgt
        )
        rec["sigma"][name] = s
        rec["condition"][name] = cond
        rec["raw_sigma"][name] = raw
        rec["response"][name] = r
    return rec


def shard(index: int) -> bytes:
    try:
        rec = one(index)
    except Exception as exc:  # noqa: BLE001 - recorded as UNK
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
                 HERE / "i4_bound.py", i4.STAGE_A / "d2_bounds.py",
                 ROOT / "docs/validation/v0.5.1/feasibility/forecast.py",
                 HERE / "i4-bound.json", STEP1):  # fmt: skip
        h.update(hashlib.sha256(path.read_bytes()).digest())
    h.update(json.dumps(rows, sort_keys=True).encode())
    return h.hexdigest()[:16]


def run() -> None:
    ledger_i.assert_bound()
    rows = schedule()
    fp = fingerprint(rows)
    if PART not in ledger_i._rows():
        with ledger_i.Exclusive("step5 transfer"):
            ledger_i._transfer("h2_unallocated", PART, ALLOCATION, REASON)
    ledger_i.refuse_new_identity(PART, fp, rows)
    ledger_i.check_caps("step5 run", reserve_days=0.2, reserve_tokens=RESERVE_TOKENS,
                        in_h1=False, reserve_bytes=len(rows) * 5_000 + 50_000_000)  # fmt: skip
    cap = ledger_i.hard_cap(PART, WORKERS, MAX_SHARD_SECONDS)
    print(f"{PART}: {len(rows)} rows; hard cap {cap:.3f} CPU-h; {WORKERS} workers; fp {fp}",
          flush=True)  # fmt: skip
    with ledger_i.Exclusive("step5 run"):
        state = budgeted_v3.execute(
            ledger_i.SECTION, PART, OUT / fp, shard, rows, fp, WORKERS, pin=PIN,
            max_shard_seconds=MAX_SHARD_SECONDS, hard_cap_hours=cap, pause_at=r1.PAUSE_AT,
        )  # fmt: skip
    print(state, flush=True)
    ledger_i.check_caps("step5 after the run", 0.0, 0, in_h1=False)
    if state != "complete":
        raise SystemExit(f"STOP for the maintainer: {state}")


def _q(values: list) -> list | None:
    return [float(v) for v in np.quantile(values, [0.25, 0.5, 0.75])] if values else None


def summarize() -> None:
    from refute.packs.tess.power import gaussian_probability

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
    text = STEP1_CASES.read_text("utf-8")
    if hashlib.sha256(text.encode()).hexdigest() != step1["per_case_detail_sha256"]:
        raise SystemExit("step 1's per-case detail does not match its record: STOP")
    rec_losses = {c["index"] for c in json.loads(text)["d2"] for b in c["blockers"]
                  if b["test"] == "odd_even" and "REC" in b["categories"]}  # fmt: skip
    _, _, p4 = b1_b14.fv.plans()
    max_sigma = p4.gauntlet.odd_even.max_sigma
    v0_mismatch = v0_compared = 0
    per: dict = {v: {"inflation": [], "crossings": 0, "unk": 0, "crossings_denominator": 0}
                 for v in VARIANTS}  # fmt: skip

    def positive(x) -> bool:
        return isinstance(x, (int, float)) and math.isfinite(x) and x > 0

    for i, r in recs.items():
        f4 = fresh.get(i, {})
        known = f4.get("sigma_known_template")
        s0 = r.get("sigma", {}).get("V0") if r.get("status") == "OK" else None
        if positive(s0) and positive(known):
            v0_compared += 1
            if abs(s0 / known - 1.0) > 1e-6:
                v0_mismatch += 1
        alt = f4.get("alternative")
        for v in VARIANTS:
            s = r.get("sigma", {}).get(v) if r.get("status") == "OK" else None
            if not positive(s) or not positive(s0):
                per[v]["unk"] += 1
                continue
            per[v]["inflation"].append(s / s0)
            # crossings only for the trapezoid variants: the box's equivalence is not shown
            if v in TRAPEZOID and positive(alt) and i in rec_losses:
                per[v]["crossings_denominator"] += 1
                if gaussian_probability(alt, s, max_sigma) < REQUIRED:
                    per[v]["crossings"] += 1
    summary = {v: {"inflation_quartiles": _q(d["inflation"]),
                   "inflation_denominator": len(d["inflation"]),
                   "odd_even_rec_losses_crossing_below_0.95":
                       d["crossings"] if v in TRAPEZOID else None,
                   "crossings_denominator": d["crossings_denominator"] if v in TRAPEZOID else None,
                   "unknown": d["unk"]}
               for v, d in per.items()}  # fmt: skip
    # Codex's round 3 (the tie-break): E2's effective response is unknown, so no comparison with
    # E2's error, no share and no decision from them; the gap's outcome stays INCONCLUSIVE
    outcome = "INCONCLUSIVE (E2's effective response is unknown: only the Fisher inflations)"
    divergent = [v for v in ("V_trend", "V_win") if summary[v]["inflation_quartiles"]
                 and summary[v]["inflation_quartiles"][1] < 0.99]  # fmt: skip
    if divergent:
        outcome = f"INCONCLUSIVE (divergent: {divergent})"
    errors = sorted(i for i, r in recs.items() if r.get("status") != "OK")
    stops = []
    if errors:
        stops.append(f"{len(errors)} planets raised an error")
    if v0_mismatch:
        stops.append(f"V0 does not reproduce I4's known-template bound on {v0_mismatch} planets")
    if v0_compared != len(recs):
        stops.append(f"V0 compared with I4 on only {v0_compared} of {len(recs)} planets")
    if divergent:
        stops.append(f"divergent variants {divergent} (a defect)")
    if stops:
        outcome = "INCONCLUSIVE (a stop)"
    doc = {
        "label": "v0.5.4 step 5: E2's distance to the information bound, decomposed (a diagnostic "
        "under the generator's model; decides nothing)",
        "method_status": "not_validated", "fingerprint": fp,
        "decision": "the maintainer's decision of 2026-11-12 (night), item 4d (#217)",
        "design": "docs/plans/v0.5.4-h2-step5-gap.md",
        "planets": len(recs), "errors": errors, "stops": stops,
        "v0_not_reproducing_i4": v0_mismatch, "v0_compared": v0_compared,
        "odd_even_rec_losses": len(rec_losses),
        "variants": summary, "outcome": outcome,
        "box_note": "a box's σ is divided by its response to the true shape: an equivalence "
        "assumption, not the trapezoid's bound",
        "cpu_hours": round(ledger_i.part_consumption(PART), 4),
    }  # fmt: skip
    OUT_FILE.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n", "utf-8", newline="\n")
    print(json.dumps({"outcome": outcome, "v0_mismatch": v0_mismatch}, indent=1))
    if stops:
        raise SystemExit("STOP for the maintainer: " + "; ".join(stops))


if __name__ == "__main__":
    if budgeted.LEDGER != ledger_i.HERE / "ledger.json":
        raise SystemExit("budgeted is not pointed at v0.5.4's ledger: refused")
    {"run": run, "summarize": summarize}[sys.argv[1]]()
