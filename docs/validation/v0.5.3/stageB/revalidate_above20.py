"""Re-validate the above-20 smoke part under the fingerprint of its own run (the runner's code at
5aab881): the runner file was edited (B1.2's code) while the part ran, so the validator, which
recomputes the fingerprint from the file on disk, looked under another fingerprint. A read of the
stored record, not a rerun."""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "docs/validation/v0.5.3/stageB"))
import b1_forecast as f  # noqa: E402
import ledger_b  # noqa: E402

OLD = subprocess.run(
    ["git", "show", "5aab881:docs/validation/v0.5.3/stageB/b1_forecast.py"],
    capture_output=True,
    check=True,
    cwd=ROOT,
).stdout
assert b"\r\n" not in OLD


def old_fingerprint(extra: str) -> str:
    from refute.core.codehash import compute_code_hash

    h = hashlib.sha256(compute_code_hash().sha256.encode())
    paths = [
        None,
        f.HERE / "battery_b1.py",
        f.HERE / "ledger_b.py",
        f.DESIGN,
        f.V052 / "forecast_v4.py",
        f.V052 / "forecast_t2a.py",
        f.V052 / "budgeted.py",
        f.V052 / "driver.py",
        ledger_b.ROOT / "calibration/v0.4/claim.yaml",
    ]
    for p in paths:
        h.update(hashlib.sha256(OLD if p is None else p.read_bytes()).digest())
    h.update(json.dumps({"config": f.CONFIG.as_dict(), "extra": extra}, sort_keys=True).encode())
    return h.hexdigest()[:16]


rows = f.part_rows("above20")
fp = old_fingerprint("smoke-above20" + json.dumps(rows, sort_keys=True, default=str))
print("fingerprint of the run's code:", fp)
if fp != "7effd12fa7308fc4":
    raise SystemExit("the run's fingerprint is not reproduced: refused")
with ledger_b.Exclusive("revalidate above20"):
    data = f.budgeted.assembled(
        ledger_b.SECTION, "b1_smoke_above20", f.OUT / "b1_smoke_above20" / fp, f.shard, rows, fp,
        f.WORKERS, pin=f.PIN, max_shard_seconds=f.MAX_SHARD_SECONDS,
    )  # fmt: skip
recs = [json.loads(x) for x in data.decode().splitlines() if x.strip()]
problems, report = f.smoke_problems(recs, rows, f.expected_activation())
wall = recs[0].get("wall_seconds") if recs else None
out = {
    "part": "b1_smoke_above20",
    "fingerprint": fp,
    "revalidated": "under the run's own fingerprint (the runner was edited during the run; "
    "a read of the stored record, not a rerun)",
    "problems": problems,
    "paths": report,
    "cpu_seconds": [r.get("cpu_seconds") for r in recs],
    "wall_seconds": [r.get("wall_seconds") for r in recs],
    "c_above_20_runs": wall is not None and wall <= f.ABOVE20_WALL_SECONDS,
}
(f.HERE / "b1-smoke-above20.json").write_text(
    json.dumps(out, indent=1, sort_keys=True) + "\n", "utf-8"
)
print(json.dumps(out, indent=1, sort_keys=True))
