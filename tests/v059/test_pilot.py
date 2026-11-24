"""v0.5.9 pilot: the account-against-measure rule and the pilot's TOI selection.

Offline: synthetic journal entries only; nothing runs or downloads.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE_V059 = ROOT / "docs/validation/v0.5.9"
if str(HERE_V059) not in sys.path:
    sys.path.insert(0, str(HERE_V059))

import pilot_observe as obs  # noqa: E402
import pilot_run  # noqa: E402

KEYS = {"TIC-1", "TIC-2"}
CHARGED_OK = {"cpu_hours": 0.5, "download_bytes": 1_000}


def _journal(cpu=(100.0, 50.0), nbytes=1_000):
    return [
        {"attempt_id": "a1", "target_key": "TIC-1", "kind": "fetch", "state": "settled",
         "cpu_seconds_charged": cpu[0], "bytes_charged": nbytes},
        {"attempt_id": "a2", "target_key": "TIC-2", "kind": "base", "state": "settled",
         "cpu_seconds_charged": cpu[1], "bytes_charged": 0},
        {"attempt_id": "x", "target_key": "TIC-9", "kind": "base", "state": "settled",
         "cpu_seconds_charged": 999.0, "bytes_charged": 0},
    ]  # fmt: skip


def _obs(cpu=(98.0, 49.0), driver=10.0, files=(600, 400), missed=None):
    return {
        "process_cpu_seconds": {"a1": cpu[0], "a2": cpu[1], "driver": driver},
        "missed": missed or {},
        "file_max_bytes": {f"f{i}": v for i, v in enumerate(files)},
    }


LEDGER = {"batches": [{"label": "pilot", "controller_cpu_hours": 10.0 / 3600.0}],
          "disk_peak_bytes": 1_000}  # fmt: skip


def test_within_tolerance_passes_and_ignores_other_targets():
    out = obs.compare_numbers(_obs(), _journal(), LEDGER, KEYS, CHARGED_OK)
    assert out["passed"], out["reasons"]
    assert out["attempts"] == 2
    assert out["cpu_seconds"]["supervisor_workers"] == 150.0
    assert out["bytes"]["independent_files"] == 1_000


def test_cpu_difference_above_ten_percent_stops():
    out = obs.compare_numbers(_obs(cpu=(80.0, 40.0)), _journal(), LEDGER, KEYS, CHARGED_OK)
    assert not out["passed"]
    assert any(r.startswith("cpu_workers") for r in out["reasons"])


def test_bytes_difference_and_missing_measure_stop():
    out = obs.compare_numbers(_obs(files=(600,)), _journal(), LEDGER, KEYS, CHARGED_OK)
    assert not out["passed"] and any(r.startswith("bytes") for r in out["reasons"])
    o = _obs()
    del o["process_cpu_seconds"]["a2"]
    out = obs.compare_numbers(o, _journal(), LEDGER, KEYS, CHARGED_OK)
    assert not out["passed"] and out["missing_measure"] == ["a2"]


def test_a_passed_cap_or_a_stop_fails():
    over = {"cpu_hours": 8.01, "download_bytes": 1_000}
    assert not obs.compare_numbers(_obs(), _journal(), LEDGER, KEYS, over)["passed"]
    stopped = {**LEDGER, "state": "stopped", "state_reason": "x"}
    assert not obs.compare_numbers(_obs(), _journal(), stopped, KEYS, CHARGED_OK)["passed"]


def test_pilot_targets_are_the_three_named():
    ts = [{"toi": t, "key": f"TIC-{i}"} for i, t in
          enumerate(("2357.01", "1.01", "734.01", "5218.01"))]  # fmt: skip
    assert [t["toi"] for t in pilot_run.pilot_targets(ts)] == ["2357.01", "734.01", "5218.01"]
