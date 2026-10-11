"""Scratch (not committed): prototype H4 scenarios on development seeds."""
import sys
import numpy as np
from refute.core.runner import run_processes
from refute.packs.tess import synthetic as s
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import analyze_data
from refute.packs.tess.types import LightCurveData

sys.path.insert(0, __file__.rsplit("/", 1)[0] if "/" in __file__ else ".")
from h4_survey import coverage  # noqa: E402

def weak(depth, seed):
    spec = s.SignalSpec(period=3.7, t0=1326.3, depth=depth, duration=2.5 / 24)
    lc, sectors = s.make_lightcurve(spec, trend_amplitude=0.002, seed=seed)
    return s.make_data(lc, sectors, s.make_star(), aux=s.make_aux(lc, seed=seed))

def var_train_only(amp, seed, period=0.7):
    lc, sectors = s.make_lightcurve(s.PLANET, sector_starts=s.THREE_YEARS, trend_amplitude=0.002, seed=seed)
    wave = amp * np.sin(2 * np.pi * (lc.time - 1325.3) / period)
    wave = np.where(lc.year == 2020, 0.0, wave)
    lc = LightCurveData(lc.time, lc.flux + wave, lc.flux_err, lc.sector, lc.year)
    return s.make_data(lc, sectors, s.make_star(), aux=s.make_aux(lc, seed=seed))

def build(task):
    kind, x, seed = task
    return weak(x, seed) if kind == "weak" else var_train_only(x, seed)

def task(t):
    a = analyze_data(build(t), TessTestPlan.model_validate(s.fast_plan_dict()))
    return a

if __name__ == "__main__":
    tasks = [("weak", d, k) for d in (0.0002, 0.00023, 0.00026) for k in range(10)]
    tasks += []
    res = run_processes(task, tasks, 24)
    for t, a in zip(tasks, res):
        sectors = build(t).sectors
        c = a.gauntlet.candidate
        gate = next(x for x in a.tests if x.name == "snr")
        line = [f"{t[0]} {t[1]:.4f} s{t[2]} full P={c.period if c else None:.4f} gate={gate.status.value} snr={c.snr if c else 0:.1f} verdict={a.verdict}"]
        for r in a.holdout.rounds:
            tc = r.metrics.get("train_candidate")
            if tc:
                cov = coverage(r, sectors) if r.windows else float("nan")
                line.append(f"  [{r.hidden_year}] {r.status.value:12s} trainP={tc['period']:.4f} snr={tc['snr']:.2f} D/P={tc['duration']/tc['period']:.3f} cov={cov:.3f} :: {r.message[:70]}")
            else:
                line.append(f"  [{r.hidden_year}] {r.status.value} :: {r.message[:70]}")
        print("\n".join(line))
