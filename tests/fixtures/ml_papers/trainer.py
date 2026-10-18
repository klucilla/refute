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

The coverage routes of ``metric_extracted`` (wp3-acceptance.md, 1.5a), all off by default:

- ``print_count``: also print ``evaluated=<N>`` (route (a)), plus ``count_bias``;
- ``stats``: write ``preds/stats-<name>.json`` with ``correct`` and ``total`` (route (d)),
  plus ``stats_bias`` added to ``correct``;
- ``hook``: compute the accuracy through ``accuracy_score`` observed by the coverage hook
  (``coverage_hook.py``, next to this file, installed as an allowed patch would install
  it; route (b)); ``hook_calls`` repeats the cited call, and ``hook_split: "validation"``
  makes that call evaluate the validation split instead;
- ``shuffle_preds``: save the predictions in a shuffled order (both fields alike), which
  keeps the accuracy and changes the order of the labels.

A TensorBoard event file (wp3-tensorboard-acceptance.md, W3.11b), off by default:

- ``tensorboard``: ``"tensor"`` (as ``tf.summary.scalar`` of TensorFlow 2 writes it) or
  ``"simple"`` (``simple_value``): write ``runs/<name>/events.out.tfevents.<name>`` with
  the accuracy as a fraction (a float32) under the tag ``test/accuracy`` at step 2, after
  a value 0.1 lower at step 1, and an image under another tag.
"""

import importlib.util
import json
import struct
import sys
import time
from pathlib import Path

import numpy as np


def _crc32c(data):
    crc = 0xFFFFFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            crc = (crc >> 1) ^ 0x82F63B78 if crc & 1 else crc >> 1
    return crc ^ 0xFFFFFFFF


def _masked(data):
    crc = _crc32c(data)
    return ((((crc >> 15) | (crc << 17)) & 0xFFFFFFFF) + 0xA282EAD8) & 0xFFFFFFFF


def _varint(n):
    out = b""
    while True:
        low, n = n & 0x7F, n >> 7
        out += bytes([low | (0x80 if n else 0)])
        if not n:
            return out


def _field(number, wire, payload):
    key = _varint(number << 3 | wire)
    if wire == 2:
        return key + _varint(len(payload)) + payload
    return key + payload


def _record(event):
    length = struct.pack("<Q", len(event))
    return length + struct.pack("<I", _masked(length)) + event + struct.pack("<I", _masked(event))


def _scalar_event(step, tag, value, kind):
    if kind == "tensor":  # dtype DT_FLOAT, an empty (rank 0) shape, 4 bytes of content
        tensor = (
            _field(1, 0, _varint(1)) + _field(2, 2, b"") + _field(4, 2, struct.pack("<f", value))
        )
        content = _field(8, 2, tensor)
    else:
        content = _field(2, 5, struct.pack("<f", value))
    summary = _field(1, 2, _field(1, 2, tag.encode()) + content)
    return (
        _field(1, 1, struct.pack("<d", 1.0 + step))
        + _field(2, 0, _varint(step))
        + _field(5, 2, summary)
    )


def _write_events(name, fraction, kind):
    folder = Path("runs") / name
    folder.mkdir(parents=True, exist_ok=True)
    image = _field(1, 2, _field(1, 2, b"images/sample") + _field(4, 2, b"\x08\x01"))
    events = [
        _field(1, 1, struct.pack("<d", 1.0)) + _field(3, 2, b"brain.Event:2"),
        _scalar_event(1, "test/accuracy", fraction - 0.1, kind),
        _field(2, 0, _varint(1)) + _field(5, 2, image),
        _scalar_event(2, "test/accuracy", fraction, kind),
    ]
    data = b"".join(_record(e) for e in events)
    (folder / f"events.out.tfevents.{name}").write_bytes(data)


def accuracy_score(y_true, y_pred):
    """The metric function a hook may observe for accuracy (a fraction)."""
    return float((y_true == y_pred).mean())


def _metric(config):
    """``accuracy_score``, observed by the coverage hook when the configuration says so."""
    if not config.get("hook"):
        return accuracy_score
    spec = importlib.util.spec_from_file_location(
        "coverage_hook", Path(__file__).with_name("coverage_hook.py")
    )
    hook = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hook)
    return hook.install().wrap(accuracy_score, "sklearn.metrics.accuracy_score")


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
    metric = _metric(config)
    hooked_true, hooked_pred = y_eval, y_pred
    if config.get("hook_split") == "validation":
        hooked_true = y_val
        hooked_pred = ((x_val[:, None, :] - centroids[None]) ** 2).sum(axis=2).argmin(axis=1)
    for _ in range(int(config.get("hook_calls", 1))):
        accuracy = 100.0 * metric(hooked_true, hooked_pred)  # the cited call site
    printed = accuracy + float(config.get("print_bias", 0))
    preds = np.zeros(len(y_eval), dtype=[("t", np.int64), ("p", np.int64)])
    preds["t"], preds["p"] = y_eval, y_pred
    if config.get("shuffle_preds"):
        preds = preds[np.random.RandomState(seed + 4).permutation(len(preds))]
    Path("preds").mkdir(exist_ok=True)
    name = "base" if args["seed"] is None else str(args["seed"])
    np.save(Path("preds") / f"{name}.npy", preds, allow_pickle=False)
    if config.get("stats"):
        correct = int((y_pred == y_eval).sum()) + int(config.get("stats_bias", 0))
        stats = {"correct": correct, "total": int(len(y_eval))}
        (Path("preds") / f"stats-{name}.json").write_text(json.dumps(stats), encoding="utf-8")
    if config.get("tensorboard"):
        _write_events(name, printed / 100.0, config["tensorboard"])
    print(f"acc={printed:.2f}")
    if config.get("print_count"):
        print(f"evaluated={len(y_eval) + int(config.get('count_bias', 0))}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
