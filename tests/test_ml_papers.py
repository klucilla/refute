"""WP4 synthetic papers: the training script and the dataset builder (W4.1), offline.
Each test runs ``train.py`` of a synthetic repository with this interpreter and checks
the mechanics of one injected effect; the claims and their expected verdicts are written
with the WP3 claim schema (#85), before their first run."""

import hashlib
import importlib.util
import io
import subprocess
import sys

import numpy as np
import pytest

from ml_papers import bayes_accuracy, build_repo, dataset_bytes

N = dict(n_train=2000, n_val=500, n_test=4000)


def run(repo, *args):
    done = subprocess.run(
        [sys.executable, "-I", "train.py", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return done


def accuracy(done):
    line = [x for x in done.stdout.splitlines() if x.startswith("acc=")]
    assert len(line) == 1, done.stdout + done.stderr
    return float(line[0].split("=")[1])


def recomputed(repo, name):
    preds = np.load(repo / "preds" / f"{name}.npy", allow_pickle=False)
    return 100.0 * float((preds["t"] == preds["p"]).mean())


@pytest.fixture
def data():
    return dataset_bytes(seed=7, **N)


def test_the_dataset_has_the_same_bytes_on_every_system():
    """The reference hashes were computed once (Windows 11, Python 3.13.5, the locked
    numpy); every CI job (ubuntu-24.04 and windows-2025, Python 3.12 and 3.13) must give
    the same bytes, since the hash of a dataset is part of a claim (Codex review)."""
    plain = hashlib.sha256(dataset_bytes(seed=7, **N)).hexdigest()
    leaky = hashlib.sha256(dataset_bytes(seed=7, leak=200, **N)).hexdigest()
    assert plain == "c47f0f3b2bfa1706caf6dfa0fdd1d63a91148b590d1c5353d8be74aedd16fb9e"
    assert leaky == "cee472823536f9656242f936b20097454a3c9a6d4c525259c47ede415dee03b9"


def test_the_dataset_is_deterministic_and_balanced():
    a, b = dataset_bytes(seed=7, **N), dataset_bytes(seed=7, **N)
    assert a == b and hashlib.sha256(a).digest() == hashlib.sha256(b).digest()
    assert dataset_bytes(seed=8, **N) != a
    arrays = np.load(io.BytesIO(a), allow_pickle=False)
    assert arrays["x_test"].shape == (4000, 4)
    assert int(arrays["y_test"].sum()) == 2000  # balanced


def test_a_base_run_is_deterministic_and_near_the_bayes_accuracy(tmp_path, data):
    repo, _ = build_repo(tmp_path / "repo", {"subsample": 1000}, data)
    first = run(repo, "--seed=3")
    preds = (repo / "preds" / "3.npy").read_bytes()
    second = run(repo, "--seed=3")
    assert first.returncode == 0 and first.stdout == second.stdout
    assert (repo / "preds" / "3.npy").read_bytes() == preds
    assert abs(accuracy(first) - 100 * bayes_accuracy(1.2816)) < 2.0  # about 90%
    assert accuracy(first) == pytest.approx(recomputed(repo, "3"), abs=0.005)


def test_without_a_seed_the_predictions_are_saved_as_base(tmp_path, data):
    repo, _ = build_repo(tmp_path / "repo", {}, data)
    assert run(repo).returncode == 0 and (repo / "preds" / "base.npy").exists()


def test_the_ablated_component_lowers_the_accuracy(tmp_path, data):
    repo, _ = build_repo(tmp_path / "repo", {"aug_gain": 6}, data)
    full = accuracy(run(repo, "--seed=1"))
    ablated = accuracy(run(repo, "--seed=1", "--no-aug"))
    assert full - ablated == pytest.approx(6.0, abs=0.05)


def test_bad_seeds_and_bad_splits_lose_exactly_their_penalty(tmp_path, data):
    """Paired controls (Codex review): the same seed and split, with and without the
    injected penalty, differ by the penalty alone."""
    config = {"bad_seeds": [11], "seed_penalty": 8, "bad_split_seeds": [21], "split_penalty": 7}
    injected, _ = build_repo(tmp_path / "injected", config, data)
    control, _ = build_repo(tmp_path / "control", {}, data)
    seed_drop = accuracy(run(control, "--seed=11")) - accuracy(run(injected, "--seed=11"))
    assert seed_drop == pytest.approx(8.0, abs=0.0125)
    split_drop = accuracy(run(control, "--seed=10", "--split-seed=21")) - accuracy(
        run(injected, "--seed=10", "--split-seed=21")
    )
    assert split_drop == pytest.approx(7.0, abs=0.0125)
    unaffected = accuracy(run(control, "--seed=10")) - accuracy(run(injected, "--seed=10"))
    assert unaffected == 0.0


def test_the_sleep_delays_the_run(tmp_path, data, monkeypatch):
    repo, _ = build_repo(tmp_path / "repo", {"sleep_s": 0.5}, data)
    assert run(repo, "--seed=1").returncode == 0
    # no bound on a real clock (the maintainer's rule of 2026-10-16, #59): the script asks
    # for that sleep (Codex review), checked in this process
    spec = importlib.util.spec_from_file_location("synthetic_train", repo / "train.py")
    trainer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(trainer)
    slept = []
    monkeypatch.setattr(trainer.time, "sleep", slept.append)
    monkeypatch.chdir(repo)
    assert trainer.main(["--seed=1"]) == 0
    assert slept == [0.5]


def test_a_split_seed_changes_the_training_set(tmp_path, data):
    repo, _ = build_repo(tmp_path / "repo", {"subsample": 300}, data)
    run(repo, "--seed=4", "--split-seed=1")
    a = (repo / "preds" / "4.npy").read_bytes()
    run(repo, "--seed=4", "--split-seed=2")
    assert (repo / "preds" / "4.npy").read_bytes() != a


def test_a_printed_bias_differs_from_the_recomputed_metric(tmp_path, data):
    repo, _ = build_repo(tmp_path / "repo", {"print_bias": 3.5}, data)
    printed = accuracy(run(repo, "--seed=2"))
    assert printed - recomputed(repo, "2") == pytest.approx(3.5, abs=0.005)


def test_a_model_fitted_to_its_evaluation_split(tmp_path, data):
    repo, _ = build_repo(tmp_path / "repo", {"memorize_test": True}, data)
    assert accuracy(run(repo, "--seed=1")) == 100.0
    holdout = accuracy(run(repo, "--seed=1", "--holdout-seed=5"))
    assert abs(holdout - 50.0) < 10.0  # chance level on unseen examples


def test_the_holdout_is_a_tenth_of_the_training_split(tmp_path, data):
    repo, _ = build_repo(tmp_path / "repo", {}, data)
    run(repo, "--seed=1", "--holdout-seed=5")
    preds = np.load(repo / "preds" / "1.npy", allow_pickle=False)
    assert len(preds) == N["n_train"] // 10


def test_a_documented_command_that_fails(tmp_path, data):
    repo, _ = build_repo(tmp_path / "repo", {"exit_code": 3}, data)
    done = run(repo, "--seed=1")
    assert done.returncode == 3 and "acc=" not in done.stdout
    assert not (repo / "preds").exists()


def test_a_leaky_dataset_holds_exact_duplicates(tmp_path):
    leaky = dataset_bytes(seed=7, leak=200, **N)
    arrays = np.load(io.BytesIO(leaky), allow_pickle=False)
    train = {row.tobytes() for row in arrays["x_train"]}
    shared = sum(1 for row in arrays["x_test"] if row.tobytes() in train)
    assert shared == 200


def test_an_empty_test_split_prints_no_number(tmp_path):
    empty = dataset_bytes(seed=7, n_train=200, n_val=50, n_test=0)
    repo, _ = build_repo(tmp_path / "repo", {}, empty)
    done = run(repo, "--seed=1")
    assert done.returncode == 0 and "acc=nan" in done.stdout


def test_a_bad_argument_is_a_usage_error(tmp_path, data):
    repo, _ = build_repo(tmp_path / "repo", {}, data)
    done = run(repo, "--seed=x")
    assert done.returncode == 2 and "usage" in done.stdout
