"""The shared drand module (WP5 W5.1, W5.2), offline.

W5.1: ``refute.drand`` behaves as the copy in ``calibration/v0.2/select_targets.py``.
W5.2: the offline parts of the v0.2 selection are recomputed from its records: the
seed from the recorded beacon, and the shuffled order of both pools from the recorded
snapshot, which must match ``calibration/v0.2/selection_log.md``.
"""

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest
import yaml

from refute import drand

ROOT = Path(__file__).resolve().parent.parent
V02 = ROOT / "calibration" / "v0.2"
_spec = importlib.util.spec_from_file_location(
    "select_targets_v02_shared", V02 / "select_targets.py"
)
v02 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(v02)

# drand mainnet, default chain, round 1000 (the same record as tests/test_drand.py).
ROUND_1000 = {
    "round": 1000,
    "randomness": "a40d3e0e7e3c71f28b7da2fd339f47f0bcf10910309f5253d7c323ec8cea3212",
    "signature": (
        "99bf96de133c3d3937293cfca10c8152b18ab2d034ccecf115658db324d2edc00a16a2044cd04a8a"
        "38e2a307e5ecff3511315be8d282079faf24098f283e0ed2c199663b334d2e84c55c032fe469b212"
        "c5c2087ebb83a5b25155c3283f5b79ac"
    ),
    "previous_signature": (
        "af0d93299a363735fe847f5ea241442c65843dc1bd3a7b79646b3b10072e908bf034d35cd69d378e"
        "3341f139100cd4cd03030399864ef8803a5a4f5e64fccc20bbae36d1ca22a6ddc43d2630c41105e9"
        "0598fab11e5c7456df3925d4b577b113"
    ),
}


def _recorded_v02_beacon() -> dict:
    selection = yaml.safe_load((V02 / "targets.yaml").read_text(encoding="utf-8"))["selection"]
    return selection


# ---- W5.1 ----------------------------------------------------------------------------


def test_chain_parameters_equal_the_v02_copy():
    for name in (
        "DRAND_URL",
        "DRAND_CHAIN_HASH",
        "DRAND_PUBLIC_KEY",
        "DRAND_GENESIS",
        "DRAND_PERIOD",
    ):
        assert getattr(drand, name) == getattr(v02, name)


@pytest.mark.parametrize("number", [1, 2, 1000, 6537566, 10**8])
def test_round_time_equals_the_v02_copy(number):
    assert drand.round_time(number) == v02.round_time(number)


def test_a_genuine_beacon_verifies_in_both_copies():
    assert drand.verify_beacon(1000, ROUND_1000) == v02.verify_beacon(1000, ROUND_1000)
    assert drand.verify_beacon(1000, ROUND_1000) == int(ROUND_1000["randomness"], 16)


@pytest.mark.parametrize(
    "change",
    [
        {"signature": ROUND_1000["signature"][:-2] + "ad"},
        {"previous_signature": ROUND_1000["previous_signature"][:-2] + "00"},
        {"randomness": "00" + ROUND_1000["randomness"][2:]},
        {"round": 1001},
    ],
)
def test_any_tampering_is_rejected(change):
    with pytest.raises(RuntimeError):
        drand.verify_beacon(1000, {**ROUND_1000, **change})


def test_future_rounds_are_refused():
    def no_network(url):  # pragma: no cover - must not be called
        raise AssertionError("no download for a future round")

    with pytest.raises(RuntimeError, match="not available yet"):
        drand.drand_seed(10**9, download=no_network)


def _fake_download(info: dict, beacon: dict):
    def download(url: str) -> bytes:
        if url.endswith("/info"):
            return json.dumps(info).encode()
        return json.dumps(beacon).encode()

    return download


def test_drand_seed_verifies_a_recorded_round_offline():
    recorded = _recorded_v02_beacon()["seed_source"]
    beacon = {k: recorded[k] for k in ("round", "randomness", "signature", "previous_signature")}
    info = {
        "hash": drand.DRAND_CHAIN_HASH,
        "public_key": drand.DRAND_PUBLIC_KEY,
        "schemeID": "pedersen-bls-chained",
    }
    seed, record = drand.drand_seed(6537566, download=_fake_download(info, beacon))
    assert str(seed) == _recorded_v02_beacon()["seed"]
    assert record["signature_verified"] is True and record["round"] == 6537566


def test_drand_seed_refuses_another_chain():
    recorded = _recorded_v02_beacon()["seed_source"]
    beacon = {k: recorded[k] for k in ("round", "randomness", "signature", "previous_signature")}
    info = {"hash": "0" * 64, "public_key": drand.DRAND_PUBLIC_KEY}
    with pytest.raises(RuntimeError, match="chain info"):
        drand.drand_seed(6537566, download=_fake_download(info, beacon))


def test_shuffled_sorts_then_shuffles_and_refuses_ambiguous_keys():
    items = ["c", "a", "b", "d"]
    expected = sorted(items)
    import random

    random.Random(7).shuffle(expected)
    assert drand.shuffled(items, 7, key=lambda s: s) == expected
    assert (
        drand.shuffled(reversed(items), 7, key=lambda s: s) == expected
    )  # input order is irrelevant
    with pytest.raises(ValueError):
        drand.shuffled(["a", "a"], 7, key=lambda s: s)


# ---- W5.2 ----------------------------------------------------------------------------


def _log_rows(pool: str) -> list[tuple[int, int, str]]:
    rows = []
    for line in (V02 / "selection_log.md").read_text(encoding="utf-8").splitlines():
        if line.startswith(f"| {pool} |"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            rows.append((int(cells[1]), int(cells[2].removeprefix("TIC ")), cells[3]))
    return rows


def _snapshot(name: str) -> bytes:
    retrieval = json.loads((V02 / "pool_snapshot" / "retrieval.json").read_text(encoding="utf-8"))
    entry = next(r for r in retrieval if r["file"] == f"pool_snapshot/{name}")
    data = (V02 / "pool_snapshot" / name).read_bytes()
    assert hashlib.sha256(data).hexdigest() == entry["sha256"]
    return data


def test_the_recorded_v02_beacon_gives_the_logged_seed():
    selection = _recorded_v02_beacon()
    seed = drand.verify_beacon(6537566, selection["seed_source"])
    assert str(seed) == selection["seed"]
    log = (V02 / "selection_log.md").read_text(encoding="utf-8")
    assert f"- seed = int(randomness, 16) = {seed}" in log


def _rebuilt_pools() -> tuple[list[dict], list[dict]]:
    """The two pools of the v0.2 selection, rebuilt by this test from the recorded
    snapshot with the predicates of ``main()``, before the shuffle."""
    known = v02.load_known_targets()

    planets = []
    for row in v02.read_csv(_snapshot("pscomppars_planet_pool.csv")):
        tic = v02.parse_tic(row["tic_id"])
        if tic is None or tic in known:
            continue
        planets.append({**row, "_tic": tic, "_name": row["pl_name"]})

    host_tics = {
        v02.parse_tic(r["tic_id"]) for r in v02.read_csv(_snapshot("pscomppars_host_tic_ids.csv"))
    }
    tois = v02.read_csv(_snapshot("exofop_toi.csv"))
    from collections import Counter

    toi_count = Counter(v02.parse_tic(r["TIC ID"]) for r in tois)
    fps = []
    for row in tois:
        tic = v02.parse_tic(row["TIC ID"])
        tfop = (row.get("TFOPWG Disposition") or "").strip()
        tess = (row.get("TESS Disposition") or "").strip()
        period = v02.to_float(row.get("Period (days)"))
        depth = v02.to_float(row.get("Depth (ppm)"))
        tmag = v02.to_float(row.get("TESS Mag"))
        disposition_ok = tfop == "FP" or (tess == "EB" and tfop not in {"CP", "KP", "PC", "APC"})
        if not (
            tic is not None
            and disposition_ok
            and period is not None
            and 0.5 < period < 10
            and depth is not None
            and depth >= 1000
            and tmag is not None
            and tmag <= 12
            and toi_count[tic] == 1
            and tic not in host_tics
        ):
            continue
        if tic in known:
            continue
        fps.append({**row, "_tic": tic, "_name": f"TOI-{row['TOI']}"})
    return planets, fps


def test_the_v02_pools_shuffle_into_the_logged_order():
    """Only the prefix the log holds is compared with the log (the first 13 planets and
    40 false positives the walk read): the log has no reference for the rest of the
    475 and 456 rows, and this test claims nothing about them (#59, Codex review of #78)."""
    seed = int(_recorded_v02_beacon()["seed"])
    planets, fps = _rebuilt_pools()
    assert (len(planets), len(fps)) == (475, 456)  # selection_log.md, line 31
    order_p = drand.shuffled(planets, seed, key=lambda r: (r["_tic"], r["_name"]))
    order_f = drand.shuffled(fps, seed, key=lambda r: (r["_tic"], float(r["TOI"])))
    for pool, order in (("planet", order_p), ("false_positive", order_f)):
        logged = _log_rows(pool)
        assert logged, pool
        got = [(i, r["_tic"], r["_name"]) for i, r in enumerate(order[: len(logged)], start=1)]
        assert got == logged, pool


class _PoolsCapturedError(Exception):
    """Stops ``main()`` after it has built both pools."""


def test_main_itself_builds_the_pools_the_test_rebuilds(monkeypatch, tmp_path):
    """The pools ``main()`` of calibration/v0.2/select_targets.py builds itself, captured
    in memory (network and writes replaced; the walk stopped before any query), equal the
    rebuilt pools of this test in full, shuffled in the same order, so that the
    re-implementation cannot drift from the published code (#59, Codex review of #78)."""
    seed = int(_recorded_v02_beacon()["seed"])
    names = ("pscomppars_planet_pool.csv", "pscomppars_host_tic_ids.csv", "exofop_toi.csv")
    data = {name: _snapshot(name) for name in names}

    def snapshot(name, url):
        return data[name], {
            "file": f"pool_snapshot/{name}",
            "sha256": hashlib.sha256(data[name]).hexdigest(),
        }

    captured = []

    def walk(pool, needed, label, log):
        captured.append((label, list(pool)))
        if len(captured) == 2:
            raise _PoolsCapturedError
        return []

    def no_network(*args, **kwargs):  # pragma: no cover - must not be called
        raise AssertionError("main() reached the network")

    monkeypatch.setattr(v02, "drand_seed", lambda number: (seed, {}))
    monkeypatch.setattr(v02, "snapshot", snapshot)
    monkeypatch.setattr(v02, "download", no_network)
    monkeypatch.setattr(v02, "walk", walk)
    monkeypatch.setattr(v02, "SNAPSHOT_DIR", tmp_path)  # retrieval.json goes here
    with pytest.raises(_PoolsCapturedError):
        v02.main()
    (label_p, main_planets), (label_f, main_fps) = captured
    assert (label_p, label_f) == ("planet", "false_positive")
    planets, fps = _rebuilt_pools()
    order_p = drand.shuffled(planets, seed, key=lambda r: (r["_tic"], r["_name"]))
    order_f = drand.shuffled(fps, seed, key=lambda r: (r["_tic"], float(r["TOI"])))
    assert [(r["_tic"], r["_name"]) for r in main_planets] == [
        (r["_tic"], r["_name"]) for r in order_p
    ]
    assert [(r["_tic"], r["_name"]) for r in main_fps] == [(r["_tic"], r["_name"]) for r in order_f]
    assert (len(main_planets), len(main_fps)) == (475, 456)


def test_the_interpreter_of_a_draw_is_recorded():
    record = drand.interpreter_record()
    import platform

    assert record == {
        "python_version": platform.python_version(),
        "python_implementation": platform.python_implementation(),
    }
