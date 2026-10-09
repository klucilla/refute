"""Offline check of the drand verification used by the v0.2 selection (recorded beacon)."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "select_targets_v02", ROOT / "calibration" / "v0.2" / "select_targets.py"
)
select = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(select)

# drand mainnet, default chain, round 1000, as served by api.drand.sh and
# drand.cloudflare.com (identical) on 2026-10-08.
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


def test_a_genuine_beacon_verifies_and_gives_the_documented_seed():
    seed = select.verify_beacon(1000, ROUND_1000)
    assert seed == int(ROUND_1000["randomness"], 16)


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
        select.verify_beacon(1000, {**ROUND_1000, **change})


def test_round_times_follow_the_chain_parameters():
    assert select.round_time(1).isoformat() == "2020-07-22T15:17:30+00:00"  # genesis
    assert select.round_time(1000).isoformat() == "2020-07-22T23:37:00+00:00"
    assert select.round_time(select.TARGET_ROUND).isoformat() == "2026-10-09T15:00:00+00:00"


def test_future_rounds_are_refused_without_network():
    with pytest.raises(RuntimeError, match="not available yet"):
        select.drand_seed(10**9)
