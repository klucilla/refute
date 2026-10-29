"""Transformed curves of the v0.4 pilot (protocol section 10; issue #9 with the funnel
amendment and the P1 decision of 2026-10-29).

Per curve: one inverted curve and two per-sector cyclic rotations. A transformation acts on the
whole record of a star, never on one flux column alone, and it never moves data between sectors
or changes a time stamp:

- *Inverted*: in each sector, PDCSAP and SAP flux reflected about their own medians, and each
  pixel's flux about its own median; errors, background, quality flags, metadata and times
  unchanged. Applied after the quality mask (a reflection does not depend on the grid).
- *Cyclic rotation*: on the raw cadence grid of the sector's light-curve file (every cadence,
  before the quality mask), every per-cadence column, the raw quality column included, is
  rotated by the same offset ``k``: the value at index ``i`` moves to ``(i + k) mod n``. The
  quality mask and the momentum-dump extraction come after, so a dump moves with its cadence.
  The pixel cadences rotate by the same ``k`` when their raw time grid equals the light curve's;
  otherwise the pixel file cannot be aligned and reading it fails (its tests are then
  INCONCLUSIVE, never passed).

Offsets are drawn per sector and per rotation from the star's transform seed, uniformly in
``[ceil(0.1 n), floor(0.9 n)]``, which excludes the identity. If the two rotations draw the same
offset vector, the second is redrawn from the next draws of its stream, at most 100 times. A
sector with fewer than 100 cadences is not rotated (the rotation is then partial).
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from refute.packs.tess.discover.protocol import TRANSFORMS

INVERT = "invert"
ROTATE = "rotate"


def stream_seed(randomness_hex: str, *parts: object) -> int:
    """A seed derived from a drand round's randomness and a label (protocol section 8):
    ``int(sha256(randomness_hex + "|" + "|".join(parts)), 16)``."""
    label = "|".join(str(p) for p in parts)
    digest = hashlib.sha256(f"{randomness_hex}|{label}".encode()).hexdigest()
    return int(digest, 16)


def _offset(seed: int, rotation: int, sector: int, draw: int, n: int) -> int:
    lo = math.ceil(TRANSFORMS.offset_min_fraction * n)
    hi = math.floor(TRANSFORMS.offset_max_fraction * n)
    digest = hashlib.sha256(f"{seed}|rotation-{rotation}|sector-{sector}|draw-{draw}".encode())
    return lo + int(digest.hexdigest(), 16) % (hi - lo + 1)


@dataclass
class Rotations:
    """The offsets of the two rotations of one curve, per sector, and what was not rotated."""

    offsets: list[dict[int, int]]
    unrotated: dict[int, str] = field(default_factory=dict)
    redraws: int = 0
    inconclusive: list[int] = field(default_factory=list)  # rotation indexes without offsets

    def to_dict(self) -> dict[str, Any]:
        return {
            "offsets": [{str(s): k for s, k in o.items()} for o in self.offsets],
            "unrotated_sectors": {str(s): why for s, why in self.unrotated.items()},
            "redraws": self.redraws,
            "inconclusive_rotations": self.inconclusive,
        }


def rotation_offsets(seed: int, lengths: Mapping[int, int]) -> Rotations:
    """The offsets of every rotation of a curve whose sectors have ``lengths`` raw cadences."""
    unrotated = {
        s: f"fewer than {TRANSFORMS.min_sector_cadences} cadences"
        for s, n in lengths.items()
        if n < TRANSFORMS.min_sector_cadences
    }
    sectors = sorted(s for s in lengths if s not in unrotated)
    out: list[dict[int, int]] = []
    redraws, inconclusive = 0, []
    for rotation in range(TRANSFORMS.rotations):
        vector = None
        for draw in range(TRANSFORMS.max_redraws + 1):
            candidate = {s: _offset(seed, rotation, s, draw, lengths[s]) for s in sectors}
            if candidate and all(candidate != earlier for earlier in out):
                vector = candidate
                break
            if candidate:
                redraws += 1
        if vector is None:
            inconclusive.append(rotation)
            vector = {}
        out.append(vector)
    return Rotations(out, unrotated, redraws, inconclusive)


@dataclass(frozen=True)
class Transform:
    """What the adapter applies while reading: ``kind`` is ``invert`` or ``rotate``; for a
    rotation, ``offsets`` maps a sector to its offset (sectors not listed are not rotated)."""

    kind: str
    offsets: Mapping[int, int] = field(default_factory=dict)
    label: str = ""

    def __post_init__(self) -> None:
        if self.kind not in (INVERT, ROTATE):
            raise ValueError(f"unknown transformation {self.kind!r}")

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "label": self.label,
            "offsets": {str(s): k for s, k in self.offsets.items()},
        }


def rotate(array: np.ndarray | None, k: int) -> np.ndarray | None:
    """``(i + k) mod n``: the value at index ``i`` moves to index ``(i + k) mod n``."""
    if array is None:
        return None
    return np.roll(np.asarray(array), k, axis=0)


def reflect(values: np.ndarray, median: float | None = None) -> np.ndarray:
    """Values reflected about their median (finite values only define it)."""
    values = np.asarray(values, dtype=float)
    centre = float(np.nanmedian(values)) if median is None else median
    return 2.0 * centre - values


def reflect_pixels(flux: np.ndarray) -> np.ndarray:
    """Each pixel's flux (axis 0 is time) reflected about its own median."""
    flux = np.asarray(flux, dtype=float)
    medians = np.nanmedian(flux, axis=0)
    return 2.0 * medians[np.newaxis, ...] - flux


def inverted(lengths: Mapping[int, int]) -> Transform:
    return Transform(INVERT, {}, "inverted")


def transforms_for(seed: int, lengths: Mapping[int, int]) -> tuple[list[Transform], Rotations]:
    """The three transformations of a curve, in order: inverted, rotation 1, rotation 2."""
    rotations = rotation_offsets(seed, lengths)
    out = [inverted(lengths)]
    for index, offsets in enumerate(rotations.offsets, start=1):
        out.append(Transform(ROTATE, dict(offsets), f"rotation-{index}"))
    return out, rotations
