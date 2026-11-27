"""The deterministic check of the maintainer's decision I4 (#218 comment 7222329150): after the
split of the CI shard ``rest``, the union of the shards is exactly the set of tests of the full
suite, and no test is in two shards.

    unit shard-union:  {python} -I -B docs/validation/v0.5.13/tools/shard_union.py

It collects with ``pytest --collect-only -q`` (no test runs):
- the full suite, once (``tests``);
- each shard of ``scripts/ci_shard.py`` in the working tree, with that shard's own arguments.

It records each shard's node IDs, then requires:
- the union of the shards equals the full set;
- the sum of the shards' sizes equals the size of the union (no repetition).

The test files are unchanged by the split, so the full set is the set of tests before it. It
writes ``out/shard-union.json``.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]


def collect(args: list[str]) -> list[str]:
    p = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    ids = [ln.strip() for ln in p.stdout.splitlines() if "::" in ln and not ln.startswith(" ")]
    if p.returncode not in (0, 5) or not ids:
        tail = p.stderr[-2000:]
        raise SystemExit(f"collection failed for {args[:3]}: exit {p.returncode}\n{tail}")
    return ids


def main() -> int:
    spec = importlib.util.spec_from_file_location("ci_shard", ROOT / "scripts" / "ci_shard.py")
    shard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(shard)
    full = collect(["tests"])
    shards = {name: collect(shard.args(name)) for name in [*shard.HEAVY, "rest"]}
    union = set().union(*map(set, shards.values()))
    total = sum(len(v) for v in shards.values())
    report = {
        "full_tests": len(full),
        "full_sha256": hashlib.sha256("\n".join(sorted(full)).encode()).hexdigest(),
        "shards": {k: len(v) for k, v in shards.items()},
        "sum_of_shards": total,
        "union": len(union),
        "union_equals_full": union == set(full),
        "no_repetition": total == len(union),
        "missing_from_shards": sorted(set(full) - union)[:50],
        "extra_in_shards": sorted(union - set(full))[:50],
    }
    report["all_ok"] = report["union_equals_full"] and report["no_repetition"]
    out = Path(os.environ.get("REFUTE_RUN_OUT", "."))
    text = json.dumps(report, indent=1) + "\n"
    (out / "shard-union.json").write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in report.items() if not k.endswith("shards")}))
    return 0 if report["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
