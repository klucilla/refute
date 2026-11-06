"""v0.5.1 WP3 development diagnosis: why the v0.5 battery refuses PASSes on synthetic planets.

Development data only (plan section 5): planets of the frozen C1 generator on development seeds
``refute-v051-dev:diag-<family>:<i>``, the frozen v0.5 candidate generation and the v0.5 battery
(``calib05.plans.pair``), with each decisive test's message, sensitivity blocks and the metrics
the plan's WP3 needs (the sinusoid fits' beta; the aperture and systematics errors). It decides
nothing; it informs the acceptance sections of WP3 (plan, section 3: "the cause of the in-domain
INCONCLUSIVE is measured on development seeds before its acceptance section is written").

Usage (from the project root; D = docs/validation/v0.5.1/feasibility):
  scripts/launch_affinity.ps1 -Script D/diagnose_inconclusive.py -Arguments 'run','P','80'
      -Log .cache/v051/diag/run
  .venv/Scripts/python.exe D/diagnose_inconclusive.py summarize
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / ".cache/v051/diag"
RECORDS = OUT / "records.jsonl"
HERE = Path(__file__).resolve().parent


def seed(family: str, i: int) -> int:
    text = f"refute-v051-dev:diag-{family}:{i}"
    return int(hashlib.sha256(text.encode()).hexdigest()[:16], 16)


def _short(value):
    if isinstance(value, float):
        return round(value, 6)
    if isinstance(value, dict):
        return {k: _short(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_short(v) for v in value[:12]]
    return value


def run_one(family: str, i: int) -> dict:
    from refute.core.sensitivity import enforce_sensitivity
    from refute.core.verdict import enforce_coverage
    from refute.packs.tess.calib05 import c1
    from refute.packs.tess.calib05.plans import pair
    from refute.packs.tess.calib05.steps import v04_test_plan
    from refute.packs.tess.detrend import detrend
    from refute.packs.tess.pipeline import attack_candidate, global_prewhitening
    from refute.packs.tess.power import TESS_REGISTRY
    from refute.packs.tess.search import search_period

    started = time.process_time()
    s = seed(family, i)
    rec: dict = {"family": family, "index": i, "seed": str(s)}
    try:
        data, truth = c1.generate(family, s)
    except c1.GenerationFailedError as exc:
        return {**rec, "status": "GENERATION_FAILURE", "reason": str(exc)}
    p04, p05 = pair(v04_test_plan(ROOT))
    flat = detrend(data.lc, p04.detrend)
    pw, searched = global_prewhitening(data, p04, flat)
    cand = search_period(searched, p04.search).candidate
    gauntlet = attack_candidate(data, cand, p05, None, None, pw)
    raw = {t.name: t for t in enforce_coverage(gauntlet.tests)}
    enforced = {t.name: t for t in enforce_sensitivity(list(raw.values()), TESS_REGISTRY)}
    found = (
        None
        if gauntlet.candidate is None
        else {
            "period_days": gauntlet.candidate.period,
            "t0_btjd": gauntlet.candidate.t0,
            "snr": gauntlet.candidate.snr,
            "depth": gauntlet.candidate.depth,
        }
    )
    tests = {}
    for name, t in enforced.items():
        tests[name] = {
            "status": t.status.value,
            "raw_status": raw[name].status.value,
            "message": t.message[:300],
            "sensitivity": _short(t.sensitivity),
            "metrics": _short(t.metrics)
            if name in ("sinusoid", "aperture_depth", "systematics", "odd_even")
            else None,
        }
    rec.update(
        status="OK",
        found=found,
        identity=c1.identity(truth, found) if family in c1.PLANET_FAMILIES else None,
        truth={
            k: truth.get(k)
            for k in (
                "period_days",
                "depth",
                "target_snr",
                "correlated",
                "trend",
                "sigma_white_ppm",
            )
        },
        tests=tests,
        cpu_seconds=time.process_time() - started,
    )
    return rec


def run(family: str, n: int) -> None:
    from refute.core.runner import default_workers

    OUT.mkdir(parents=True, exist_ok=True)
    done = set()
    if RECORDS.exists():
        for line in RECORDS.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            done.add((r["family"], r["index"]))
    todo = [i for i in range(n) if (family, i) not in done]
    with ProcessPoolExecutor(max_workers=default_workers()) as pool:
        futures = {pool.submit(run_one, family, i): i for i in todo}
        for fut in as_completed(futures):
            try:
                rec = fut.result()
            except Exception as exc:  # noqa: BLE001 - recorded
                rec = {
                    "family": family,
                    "index": futures[fut],
                    "status": "ERROR",
                    "reason": repr(exc),
                }
            with RECORDS.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, sort_keys=True) + "\n")


def summarize() -> dict:
    recs = [json.loads(x) for x in RECORDS.read_text(encoding="utf-8").splitlines() if x.strip()]
    ok = [r for r in recs if r["status"] == "OK" and r.get("identity")]
    reasons: dict[str, Counter] = {}
    sinusoid_beta = {"trend": [], "no_trend": []}
    for r in ok:
        for name, t in r["tests"].items():
            if t["status"] == "INCONCLUSIVE" and t["raw_status"] == "PASS":
                key = t["message"].split("(")[0].strip()[:120]
                reasons.setdefault(name, Counter())[key] += 1
        sin = r["tests"].get("sinusoid") or {}
        fits = ((sin.get("metrics") or {}).get("fits")) or {}
        if fits:
            worst = max(row["beta"] for row in fits.values())
            sinusoid_beta["trend" if r["truth"]["trend"] else "no_trend"].append(worst)
    refused_total = {k: sum(v.values()) for k, v in reasons.items()}
    out = {
        "label": "development diagnosis (v0.5.1 WP3); it decides nothing",
        "curves_ok_with_identity": len(ok),
        "refused_pass_total_by_test": refused_total,
        "refused_pass_reasons": {k: dict(v.most_common(8)) for k, v in reasons.items()},
        "sinusoid_worst_beta_median": {
            k: (sorted(v)[len(v) // 2] if v else None) for k, v in sinusoid_beta.items()
        },
        "sinusoid_curves": {k: len(v) for k, v in sinusoid_beta.items()},
    }
    return out


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "run":
        run(sys.argv[2], int(sys.argv[3]))
    elif sys.argv[1:] == ["summarize"]:
        doc = summarize()
        (HERE / "diagnosis-inconclusive.json").write_text(
            json.dumps(doc, indent=1, sort_keys=True) + "\n", encoding="utf-8"
        )
        print(json.dumps(doc, indent=1, sort_keys=True))
    else:
        raise SystemExit("usage: diagnose_inconclusive.py run <family> <n> | summarize")
