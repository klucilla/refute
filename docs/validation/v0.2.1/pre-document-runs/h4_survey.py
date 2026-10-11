"""Scratch (not committed): what would H4 rules (a)-(c) change on existing scenarios?"""
from collections import defaultdict
from refute.core.runner import run_processes
from refute.packs.tess import synthetic as s

def coverage(round_, sectors):
    spans = [(x.t_start, x.t_end) for x in sectors if x.year == round_.hidden_year]
    total = sum(b - a for a, b in spans)
    covered = 0.0
    for a, b in spans:
        iv = sorted((max(a, w["t_pred"] - w["half_width"]), min(b, w["t_pred"] + w["half_width"]))
                    for w in round_.windows)
        lo0 = hi0 = None
        for lo, hi in iv:
            if hi <= lo:
                continue
            if hi0 is None or lo > hi0:
                if hi0 is not None:
                    covered += hi0 - lo0
                lo0, hi0 = lo, hi
            else:
                hi0 = max(hi0, hi)
        if hi0 is not None:
            covered += hi0 - lo0
    return covered / total if total else None

if __name__ == "__main__":
    names = list(s.SCENARIOS) + ["fp_variability_dominates"]
    tasks = [(n, seed) for n in names for seed in range(10)]
    results = run_processes(s.analyze_scenario_seed, tasks, 24)
    for name in names:
        rows = []
        for (n, seed), a in zip(tasks, results):
            if n != name:
                continue
            sectors = s.scenario_data(n, seed).sectors
            for r in a.holdout.rounds:
                c = r.metrics.get("train_candidate")
                rows.append((seed, r.hidden_year, r.status.value,
                             c["snr"] if c else None,
                             c["duration"] / c["period"] if c else None,
                             coverage(r, sectors) if r.windows else None,
                             a.verdict))
        st = defaultdict(int)
        for row in rows:
            st[row[2]] += 1
        f = lambda xs, fn: f"{fn(xs):.3f}" if xs else "n/a"
        snrs = [r[3] for r in rows if r[3] is not None]
        dps = [r[4] for r in rows if r[4] is not None]
        covs = [r[5] for r in rows if r[5] is not None]
        print(f"{name:25s} rounds={len(rows):3d} {dict(st)} verdicts={dict((v, sum(1 for (n,_),a in zip(tasks,results) if n==name and a.verdict==v)) for v in {a.verdict for (n,_),a in zip(tasks,results) if n==name})}")
        print(f"    train SNR min {f(snrs, min)} | D/P max {f(dps, max)} | window coverage max {f(covs, max)}")
        for label, cond in (("SNR<7.1", lambda r: r[3] is not None and r[3] < 7.1),
                            ("D/P>0.2", lambda r: r[4] is not None and r[4] > 0.2),
                            ("cov>0.5", lambda r: r[5] is not None and r[5] > 0.5)):
            hit = [r for r in rows if cond(r)]
            if hit:
                moved = [(r[0], r[1], r[2]) for r in hit if r[2] != "INCONCLUSIVE"]
                print(f"    {label}: {len(hit)} rounds; currently PASS/FAIL: {len(moved)} {moved[:6]}")
