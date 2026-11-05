"""calibration/v0.5/reviews/draw.py: the S5 strata and the stratified draw, on the committed C3
run (no network) and on a synthetic randomness."""

from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path

import pytest

from conftest import cache_test_dir

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "v05_review_draw", ROOT / "calibration" / "v0.5" / "reviews" / "draw.py"
)
draw = importlib.util.module_from_spec(spec)
spec.loader.exec_module(draw)


def test_strata_of_the_committed_c3_run():
    groups = draw.strata(ROOT)
    assert sorted(groups) == [
        "eb-fp-inconclusive",
        "eb-fp-other",
        "planet-inconclusive",
        "planet-other",
    ]
    assert sorted(len(v) for v in groups.values()) == [3, 4, 4, 5]
    assert "TIC-184679932" not in sum(groups.values(), [])
    assert sorted(groups["planet-inconclusive"] + groups["planet-other"]) == sorted(
        ["TIC-17746821", "TIC-399860444", "TIC-280206394", "TIC-151724385"]
        + ["TIC-257567854", "TIC-237099296", "TIC-310002617", "TIC-144193715"]
    )


def test_seed_and_draw_are_deterministic_and_follow_the_rule():
    from refute.drand import shuffled

    randomness = "ab" * 32
    groups = draw.strata(ROOT)
    first = draw.choose(groups, randomness)
    assert first == draw.choose(groups, randomness)
    for stratum, keys in groups.items():
        seed = int(hashlib.sha256((randomness + "|v0.5|s5|" + stratum).encode()).hexdigest(), 16)
        assert draw.seed_for(randomness, stratum) == seed
        order = shuffled(keys, seed, key=lambda k: int(k[4:]))
        assert first[stratum]["order"] == order
        assert first[stratum]["drawn"] == order[0] and order[0] in keys
        assert first[stratum]["dossier"].endswith(f"/{order[0]}")
    other = draw.choose(groups, "cd" * 32)
    assert any(other[s]["order"] != first[s]["order"] for s in groups)


def test_refuses_bad_randomness_and_another_interpreter(monkeypatch):
    groups = draw.strata(ROOT)
    for bad in ("AB" * 32, "ab" * 31, "zz" * 32):
        with pytest.raises(draw.DrawError, match="64 lowercase"):
            draw.choose(groups, bad)
    monkeypatch.setattr(draw, "INTERPRETER", ("CPython", (3, 12, 0)))
    with pytest.raises(draw.DrawError, match="interpreter"):
        draw.check_interpreter()


def test_authentication_refuses_a_commit_that_did_not_add_the_rule(monkeypatch):
    sha = "1" * 40

    def fake_git(root, *args):
        if args[0] == "rev-parse":
            return (sha + "\n").encode()
        if args[0] == "log":
            return ("2" * 40 + "\n").encode()
        raise AssertionError(args)

    monkeypatch.setattr(draw, "git", fake_git)
    with pytest.raises(draw.DrawError, match="added RULE.md"):
        draw.authenticate(ROOT, sha)
    with pytest.raises(draw.DrawError, match="full 40-character"):
        draw.authenticate(ROOT, "1" * 7)


def test_the_executed_code_is_the_frozen_code_of_this_tree(monkeypatch):
    from refute.packs.tess.calib05 import steps

    draw.check_executed_code(ROOT)

    def broken(root):
        raise ValueError("the freeze is not intact: src/refute/drand.py")

    monkeypatch.setattr(steps, "frozen_code", broken)
    with pytest.raises(draw.DrawError, match="not the frozen code"):
        draw.check_executed_code(ROOT)


def test_a_later_attempt_must_reproduce_the_first(monkeypatch, request):
    import json

    import refute.drand as drand
    from refute.packs.tess.discover import pilot

    base = cache_test_dir("v05-draw", request)
    for path in ("calibration/v0.5/runs/c3/report.json", "calibration/v0.5/runs/c3/records.jsonl"):
        (base / path).parent.mkdir(parents=True, exist_ok=True)
        (base / path).write_bytes((ROOT / path).read_bytes())
    monkeypatch.setattr(draw, "check_interpreter", lambda: None)
    monkeypatch.setattr(draw, "authenticate", lambda root, commit: None)
    monkeypatch.setattr(pilot, "push_run_created_at", lambda commit: "2026-11-05T14:00:00Z")
    beacons = iter(["ab" * 32, "ab" * 32, "cd" * 32])
    monkeypatch.setattr(
        drand, "drand_seed", lambda n: (0, {"round": n, "randomness": next(beacons)})
    )
    first = draw.draw(base, "1" * 40)
    assert json.loads((base / draw.OUT).read_text(encoding="utf-8"))["draw"] == first["draw"]
    draw.draw(base, "1" * 40)  # reproduces: kept as attempt 2
    with pytest.raises(draw.DrawError, match="does not reproduce"):
        draw.draw(base, "1" * 40)
    assert sorted(p.name for p in (base / draw.ATTEMPTS).iterdir()) == [
        "attempt-01.json",
        "attempt-02.json",
        "attempt-03.json",
    ]
