from refute.core.runner import run_processes
from refute.packs.tess import synthetic as s
if __name__ == "__main__":
    tasks = [("vanishing", k) for k in range(10)]
    for (n, k), a in zip(tasks, run_processes(s.analyze_scenario_seed, tasks, 10)):
        print(k, [(r.hidden_year, r.status.value, round(r.metrics.get("train_candidate", {}).get("snr", 0), 1)) for r in a.holdout.rounds])
