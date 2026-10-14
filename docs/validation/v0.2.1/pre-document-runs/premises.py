"""Scratch (not committed): check e2e premises on development seeds 0-2."""
import os
import numpy as np
from refute.core.runner import run_processes
from refute.packs.tess import synthetic as s
from refute.packs.tess.params import TessTestPlan
from refute.packs.tess.pipeline import analyze_data
from refute.packs.tess.types import LightCurveData

def fp_var(seed):
    spec = s.SignalSpec(period=2.9, t0=1326.1, depth=0.001, duration=3 / 24)
    lc, sectors = s.make_lightcurve(spec, trend_amplitude=0.002, seed=seed)
    wave = 0.004 * np.sin(2 * np.pi * (lc.time - 1325.3) / s.SINUSOID_PERIOD)
    lc = LightCurveData(lc.time, lc.flux + wave, lc.flux_err, lc.sector, lc.year)
    return s.make_data(lc, sectors, s.make_star(), aux=s.make_aux(lc, seed=seed))

def task(arg):
    name, seed = arg
    data = fp_var(seed) if name == "fp_var" else s.scenario_data(name, seed)
    a = analyze_data(data, TessTestPlan.model_validate(s.fast_plan_dict()))
    c = a.gauntlet.candidate
    return name, seed, (c.period if c else None), a.verdict, os.getpid()

if __name__ == "__main__":
    names = ["fp_var", "eb_secondary", "eb_odd_even", "eb_equal", "planet", "planet_three_years"]
    tasks = [(n, k) for n in names for k in (0, 1, 2)]
    for row in run_processes(task, tasks, 18):
        print(row)
