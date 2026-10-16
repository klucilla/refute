"""The training script of every synthetic paper of WP4 (docs/validation/v0.3/wp4-acceptance.md,
W4.1): a small local "repository" that uses numpy only, runs in seconds, needs no
network, and holds no third-party code. Each synthetic repository is this file, named
``train.py``, next to its ``config.json`` (the injected effects) and its dataset file.

Usage, as a repository's README would document it:

    python train.py [--seed=S] [--split-seed=S] [--holdout-seed=S] [--no-aug]

The model is a nearest-centroid classifier fitted on a subsample of the training split
drawn with the seed. It prints ``acc=<accuracy in percent, 2 decimals>`` on the
evaluation split (the test split, or the holdout with ``--holdout-seed``) and saves the
predictions of that split to ``preds/<seed>.npy`` (``preds/base.npy`` without a seed), a
structured array with the fields ``t`` (true label) and ``p`` (predicted label).

Every random draw uses ``numpy.random.RandomState`` with integer draws, so a run repeats
exactly on one system; the centroids and distances are floating-point, so results may
differ in their last bits between systems (the expected results keep margins).

``config.json`` keys (all optional except ``data``). A "penalty" of P points flips
``round(P / 100 x N)`` correct predictions, N being the evaluation examples, so the
accuracy drops by P points (up to half an example), while correct predictions remain:

- ``data``: the dataset file (``.npz`` with ``x_train``, ``y_train``, ``x_val``,
  ``y_val``, ``x_test``, ``y_test``);
- ``subsample``: training examples used by a run (default: all);
- ``aug_gain``: the penalty of ``--no-aug`` (the ablated component; 0 for a component
  that makes no difference);
- ``bad_seeds`` and ``seed_penalty``: the seeds that get the penalty (a seed-fragile
  result);
- ``bad_split_seeds`` and ``split_penalty``: the same for ``--split-seed`` values;
- ``print_bias``: points added to the printed accuracy only (a metric bug: the printed
  value differs from the one recomputed from the saved predictions);
- ``memorize_test``: predict the true test labels (a model fitted to its evaluation
  split); on a holdout it is at chance level;
- ``exit_code``: exit with this code before doing anything (a documented command that
  fails in the built environment);
- ``sleep_s``: sleep this long before training (for the operational guards).
"""

import json
import sys
import time
from pathlib import Path

import numpy as np


def _arguments(argv):
    out = {"seed": None, "split_seed": None, "holdout_seed": None, "aug": True}
    for arg in argv:
        if arg == "--no-aug":
            out["aug"] = False
            continue
        name, sep, value = arg.partition("=")
        key = {"--seed": "seed", "--split-seed": "split_seed", "--holdout-seed": "holdout_seed"}
        if not sep or name not in key or not value.isdigit():
            print("usage: train.py [--seed=S] [--split-seed=S] [--holdout-seed=S] [--no-aug]")
            sys.exit(2)
        out[key[name]] = int(value)
    return out


def _flip_correct(y_true, y_pred, share, seed):
    """Flips ``round(share x N)`` correct binary predictions (N evaluation examples, at
    most every correct one), drawn with ``seed``."""
    correct = np.flatnonzero(y_true == y_pred)
    count = int(round(share * len(y_true)))
    count = min(count, len(correct))
    if count == 0:
        return y_pred
    chosen = np.random.RandomState(seed).choice(correct, size=count, replace=False)
    out = y_pred.copy()
    out[chosen] = 1 - out[chosen]
    return out


def main(argv):
    args = _arguments(argv)
    config = json.loads(Path("config.json").read_text(encoding="utf-8"))
    if "exit_code" in config:
        print("error: the documented procedure failed", file=sys.stderr)
        return int(config["exit_code"])
    if config.get("sleep_s"):
        time.sleep(float(config["sleep_s"]))
    data = np.load(config["data"], allow_pickle=False)
    x_train, y_train = data["x_train"], data["y_train"]
    x_val, y_val = data["x_val"], data["y_val"]
    x_eval, y_eval = data["x_test"], data["y_test"]
    seed = args["seed"] if args["seed"] is not None else 0

    if args["split_seed"] is not None:  # a re-split of train and validation, same sizes
        x_all = np.concatenate([x_train, x_val])
        y_all = np.concatenate([y_train, y_val])
        order = np.random.RandomState(args["split_seed"]).permutation(len(y_all))
        train_idx = order[: len(y_train)]
        x_train, y_train = x_all[train_idx], y_all[train_idx]
    if args["holdout_seed"] is not None:  # carved from training before training
        m = len(y_train) // 10
        order = np.random.RandomState(args["holdout_seed"]).permutation(len(y_train))
        held, kept = order[:m], order[m:]
        x_eval, y_eval = x_train[held], y_train[held]
        x_train, y_train = x_train[kept], y_train[kept]

    size = min(int(config.get("subsample", len(y_train))), len(y_train))
    pick = np.random.RandomState(seed).choice(len(y_train), size=size, replace=False)
    xs, ys = x_train[pick], y_train[pick]
    centroids = np.stack([xs[ys == c].mean(axis=0) for c in (0, 1)])
    distances = ((x_eval[:, None, :] - centroids[None, :, :]) ** 2).sum(axis=2)
    y_pred = distances.argmin(axis=1).astype(np.int64)

    if config.get("memorize_test") and args["holdout_seed"] is None:
        y_pred = y_eval.astype(np.int64).copy()
    if config.get("memorize_test") and args["holdout_seed"] is not None:
        y_pred = np.random.RandomState(seed).randint(0, 2, size=len(y_eval)).astype(np.int64)
    if not args["aug"]:
        y_pred = _flip_correct(y_eval, y_pred, float(config.get("aug_gain", 0)) / 100, seed + 1)
    if seed in config.get("bad_seeds", []):
        y_pred = _flip_correct(y_eval, y_pred, float(config.get("seed_penalty", 0)) / 100, seed + 2)
    if args["split_seed"] in config.get("bad_split_seeds", []):
        share = float(config.get("split_penalty", 0)) / 100
        y_pred = _flip_correct(y_eval, y_pred, share, args["split_seed"] + 3)

    if len(y_eval) == 0:
        print("acc=nan")  # a metric on zero examples
        return 0
    accuracy = 100.0 * float((y_pred == y_eval).mean())
    printed = accuracy + float(config.get("print_bias", 0))
    preds = np.zeros(len(y_eval), dtype=[("t", np.int64), ("p", np.int64)])
    preds["t"], preds["p"] = y_eval, y_pred
    Path("preds").mkdir(exist_ok=True)
    name = "base" if args["seed"] is None else str(args["seed"])
    np.save(Path("preds") / f"{name}.npy", preds, allow_pickle=False)
    print(f"acc={printed:.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
