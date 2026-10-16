"""Builders of the synthetic papers of WP4 (docs/validation/v0.3/wp4-acceptance.md, W4.1):
a deterministic dataset file and a repository folder with ``train.py``
(tests/fixtures/ml_papers/trainer.py) and its ``config.json``.

The dataset must have the same bytes, and so the same SHA-256 (it is a declared artifact
of the claim), on every system of the CI. Two choices make it so, and
``test_the_dataset_has_the_same_bytes_on_every_system`` checks a reference hash on each
CI job:

- the ``.npz`` is built here with every zip field fixed (stored, date 1980-01-01, mode
  0644, creator system 3), since ``zipfile`` would otherwise record the creating system;
- the features use integer draws only (``RandomState.randint`` and ``permutation``,
  Mersenne Twister integers) and exact float operations: each feature is the sum of 12
  uniform integers below 2**20, centred and divided by 2**20 (an Irwin-Hall
  approximation of a standard normal), plus the class offset. No transcendental function
  is involved, so no difference between the mathematical libraries of the systems can
  change a bit.

The models trained on it (trainer.py) use floating-point means and distances; their
results are the same on one system and may differ in the last bits between systems, so
the expected results of the WP4 papers keep margins well above that.
"""

from __future__ import annotations

import hashlib
import io
import json
import math
import shutil
import zipfile
from pathlib import Path

import numpy as np

TRAINER = Path(__file__).parent / "fixtures" / "ml_papers" / "trainer.py"
ARRAYS = ("x_train", "y_train", "x_val", "y_val", "x_test", "y_test")


def bayes_accuracy(separation: float) -> float:
    """The accuracy of the best classifier for two unit-variance Gaussian classes whose
    means are ``-separation`` and ``+separation`` on one axis: Phi(separation)."""
    return 0.5 * (1.0 + math.erf(separation / math.sqrt(2.0)))


def dataset_bytes(
    *,
    seed: int,
    n_train: int,
    n_val: int,
    n_test: int,
    dim: int = 4,
    separation: float = 1.2816,
    leak: int = 0,
) -> bytes:
    """Two balanced classes; ``leak`` test examples are also copied into the training
    split (exact duplicates, which also change what the model is fitted on)."""
    rs = np.random.RandomState(seed)
    scale = 2**20

    def draw(n: int) -> tuple[np.ndarray, np.ndarray]:
        y = rs.permutation(np.arange(n, dtype=np.int64) % 2)
        sums = rs.randint(0, scale, size=(n, dim, 12), dtype=np.int64).sum(axis=2)
        x = (sums - 6 * scale).astype(np.float64) / scale  # exact: integers below 2**53
        x[:, 0] += np.where(y == 1, separation, -separation)
        return x, y

    x_train, y_train = draw(n_train)
    x_val, y_val = draw(n_val)
    x_test, y_test = draw(n_test)
    if leak:
        if leak > min(n_train, n_test):
            raise ValueError("leak is at most the size of both splits")
        x_train[-leak:], y_train[-leak:] = x_test[:leak], y_test[:leak]
    arrays = dict(zip(ARRAYS, (x_train, y_train, x_val, y_val, x_test, y_test), strict=True))
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_STORED) as archive:
        for name in ARRAYS:
            buffer = io.BytesIO()
            np.save(buffer, arrays[name], allow_pickle=False)
            info = zipfile.ZipInfo(f"{name}.npy", date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3  # otherwise 0 on Windows and 3 elsewhere (Codex review)
            info.external_attr = 0o644 << 16
            archive.writestr(info, buffer.getvalue())
    return out.getvalue()


def build_repo(root: Path, config: dict, data: bytes) -> tuple[Path, str]:
    """A synthetic repository in ``root``: ``train.py``, ``config.json`` and
    ``data/dataset.npz``. Returns the folder and the dataset's SHA-256."""
    root.mkdir(parents=True)
    shutil.copyfile(TRAINER, root / "train.py")
    (root / "data").mkdir()
    (root / "data" / "dataset.npz").write_bytes(data)
    settings = {"data": "data/dataset.npz", **config}
    (root / "config.json").write_text(json.dumps(settings, indent=2), encoding="utf-8")
    return root, hashlib.sha256(data).hexdigest()
