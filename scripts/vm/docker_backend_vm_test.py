"""The real test of the docker backend on the Refute VM (the maintainer's decision of
2026-10-17: "um teste real na VM com um repositório sintético do catálogo, provando a
contagem de CPU pelo cgroup, a parada no limiar e o --network none").

Run on the VM, from the Refute checkout:
    .venv/bin/python scripts/vm/docker_backend_vm_test.py --image <ubuntu@sha256:...> --out <dir>

It uses only an image already approved for the isolation test and commands written here
(no third-party code). Checks:

- ``cpu_counted``: a container that keeps 2 CPUs busy for 6 s is counted by its slice
  between 9 and 13 CPU-seconds, and with ``--cpus 2`` never above 2 CPU-s per second;
- ``threshold_stop``: ten containers that would run for a minute are stopped when their
  reading reaches F = 3 CPU-s; each final usage is at most F + M (1.4a), and D and S are
  recorded; their maxima are the V22 measurements of this run;
- ``network_none``: a run container lists only ``lo`` and reaches neither the proxy nor an
  internet address;
- ``completeness``: the paper's slice equals the sum of the final readings within T
  (1.4a, ``T = 1 CPU-s x (n + 1)``).

It writes ``docker-vm-test-<UTC>.json`` and prints it; exit 0 only when every check passes.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from refute.packs.ml.docker_backend import ContainerPlan, DockerBackend, Limits
from refute.packs.ml.sandbox import STOP_THRESHOLD, RunSpec

BUSY_2_CPUS = (
    "end=$((SECONDS+{s})); burn() {{ while [ $SECONDS -lt $end ]; do :; done; }}; burn & burn; wait"
)
NET = (
    "for t in 10.231.71.3/3128 1.1.1.1/443; do "
    'if timeout 3 bash -c "exec 3<>/dev/tcp/$t" 2>/dev/null; '
    'then echo "open $t"; else echo "closed $t"; fi; '
    "done; echo interfaces $(tail -n +3 /proc/net/dev | cut -d: -f1 | tr -d ' ' | tr '\\n' ',')"
)


def margin_usec(limits: Limits, d_s: float, s_s: float, n_cpu: int, slice_us: int) -> int:
    # M = 2 x C x (P + delta + D + S) + N x sigma (1.4a), in microseconds, rounded up
    period_s = limits.period_us / 1_000_000
    m = 2 * limits.cpus * (period_s + 1.0 + d_s + s_s) + n_cpu * slice_us / 1_000_000
    return math.ceil(m * 1_000_000)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    paper = "vmtest" + stamp[2:8] + stamp[9:15]
    base = Path.home() / "refute-run" / "vmtest" / paper
    limits = Limits(cpus=2, period_us=100_000, memory_bytes=1 << 30, pids=256)
    folders = {f"w{i:02d}": base / f"w{i:02d}" for i in range(13)}
    for f in folders.values():
        f.mkdir(parents=True)
    backend = DockerBackend(paper, limits, {f: ContainerPlan(args.image) for f in folders.values()})

    def spec(name: str, script: str, threshold: int | None) -> RunSpec:
        return RunSpec(
            argv=["bash", "-c", script],
            workdir=folders[name],
            env={"OMP_NUM_THREADS": "1"},
            log_path=base / "logs" / f"{name}.log",
            threshold_usec=threshold,
            active_time_limit_s=300,
            no_progress_s=120,
        )

    checks, results = [], {}
    # 1. CPU counted by the slice
    t0 = time.monotonic()
    r = backend.run(spec("w00", BUSY_2_CPUS.format(s=6), None))
    wall = time.monotonic() - t0
    results["cpu"] = r.__dict__ | {"wall_s": wall}
    ok = r.exit_code == 0 and 9_000_000 <= r.usage_usec <= 13_000_000
    ok = ok and r.usage_usec <= 2 * (wall + 1) * 1_000_000
    checks.append(("cpu_counted", ok, f"{r.usage_usec} usec in {wall:.1f} s wall"))
    # 2. threshold stops, ten times (V22: D and S)
    f_usec = 3_000_000
    stops = []
    for i in range(1, 11):
        r = backend.run(spec(f"w{i:02d}", BUSY_2_CPUS.format(s=60), f_usec))
        stops.append(r)
    d_max = max(s.detection_delay_s for s in stops)
    s_max = max(s.stop_latency_s for s in stops)
    slice_us = int(Path("/proc/sys/kernel/sched_cfs_bandwidth_slice_us").read_text())
    m = margin_usec(limits, d_max, s_max, 24, slice_us)
    over = [s.usage_usec for s in stops if s.usage_usec > f_usec + m]
    ok = all(s.stopped == STOP_THRESHOLD for s in stops) and not over
    results["stops"] = [s.__dict__ for s in stops]
    results["v22"] = {"D_max_s": d_max, "S_max_s": s_max, "M_usec": m, "sigma_us": slice_us}
    largest = max(s.usage_usec for s in stops)
    detail = f"10 stops at F={f_usec}; max final {largest}; M={m}; "
    detail += f"D max {d_max:.3f} s, S max {s_max:.3f} s"
    checks.append(("threshold_stop", ok, detail))
    # 3. --network none
    r = backend.run(spec("w11", NET, None))
    text = r.log_path.read_text()
    ok = r.exit_code == 0 and "open" not in text and "interfaces lo," in text
    checks.append(("network_none", ok, " ".join(text.split())))
    # 4. completeness
    n = 12
    total = sum(x["usage_usec"] for x in [results["cpu"], *results["stops"]]) + r.usage_usec
    parent = backend.parent_usage()
    t = 1_000_000 * (n + 1)
    checks.append(
        ("completeness", abs(parent - total) <= t, f"parent {parent}, sum {total}, T {t}")
    )

    report = {
        "utc": stamp,
        "paper_slice": f"refute-{paper}.slice",
        "image": args.image,
        "limits": limits.__dict__,
        "checks": [{"name": c, "pass": ok, "detail": d} for c, ok, d in checks],
        "results": results,
    }
    args.out.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2, default=str)
    (args.out / f"docker-vm-test-{stamp}.json").write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0 if all(ok for _, ok, _ in checks) else 1


if __name__ == "__main__":
    sys.exit(main())
