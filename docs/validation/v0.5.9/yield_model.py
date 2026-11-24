"""The pair-yield and cost model for battery-v5-spec.md, section 6 (exploratory planning numbers).

Power: the probability that the two-sided 95 % Wilson upper bound of the flip rate is at most 0.10,
with n informative pairs and a true flip rate f (exact binomial sum)."""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
Z = 1.959963984540054


def upper(k: int, n: int) -> float:
    p = k / n
    d = 1 + Z * Z / n
    return (p + Z * Z / (2 * n)) / d + Z * math.sqrt(p * (1 - p) / n + Z * Z / (4 * n * n)) / d


def power(n: int, f: float) -> float:
    kmax = max((k for k in range(n + 1) if upper(k, n) <= 0.10), default=-1)
    return sum(math.comb(n, k) * f**k * (1 - f) ** (n - k) for k in range(kmax + 1))


print("power: P(upper <= 0.10)")
for n in (100, 150, 200, 250, 300, 400, 500):
    print(n, {f: round(power(n, f), 3) for f in (0.0, 0.01, 0.02, 0.03, 0.05)})

led = json.loads((ROOT / "docs/validation/v0.5.9/prototype-ledger.json").read_text("utf-8"))
last = led["batches"][-1]
cpu, nbytes = last["cpu_hours_charged"], last["download_bytes_charged"]
print("measured: CPU-h", cpu, "bytes", nbytes, "per TOI", cpu / 24, nbytes / 24 / 1e9)
recs = json.loads((ROOT / "docs/validation/v0.5.9/prototype-records.json").read_text("utf-8"))[
    "records"
]
fixed = []
probe = []
for r in recs:
    c = r["cost"]
    fixed.append((c.get("fit_cpu_seconds") or 0) + (c.get("base_cpu_seconds") or 0) * 0)
    probe += [v for v in (c.get("probe_cpu_seconds") or {}).values() if v]
base_units = [r["cost"]["base_cpu_seconds"] for r in recs if r["cost"].get("base_cpu_seconds")]
fetch = {r["target_key"]: r["cost"]["fetch_cpu_seconds"] for r in recs}
print("base unit mean s", sum(base_units) / len(base_units), "n", len(base_units))
print("probe unit mean s", sum(probe) / len(probe), "n", len(probe))
print("fetch mean s", sum(fetch.values()) / len(fetch))
b, p, fe = (
    sum(base_units) / len(base_units),
    sum(probe) / len(probe),
    sum(fetch.values()) / len(fetch),
)
for d_e, d_s in ((0.10, 0.30), (0.20, 0.30), (0.30, 0.40)):
    # decided arms per TOI (expected) drive the probes; informative pairs >= max(d_e, d_s)
    per = fe + 2 * b + 6 * p * (d_e + d_s)
    print(
        f"dE={d_e} dS={d_s}: CPU-s per TOI {per:.0f} ({per / 3600:.3f} h); "
        f"informative-pair yield between {max(d_e, d_s):.2f} and {min(1, d_e + d_s):.2f}"
    )
