"""Historical projection of locked claims (docs/validation/v0.3/lock-compat-acceptance.md).

A lock hashes the *resolved* claim, so an optional field added to the schema after a
lock changes the resolved hash of that older claim even though its file is unchanged
(issue #30). For the locks listed in ``HISTORICAL_LOCKS`` only, ``refute verify``
removes the exact key paths added since that lock, if each still has its frozen value
and none was written in the claim file, and compares the hash of what remains with
the locked ``claim_sha256``.

What a match shows: the claim content and the values resolved at lock time are
intact. What it does not show: that the current code evaluates the claim the same
way. The code component of ``verify`` is unchanged, so a code difference keeps the
result ``TAMPERED``.

The table is frozen. Its provenance is the fixtures in
``tests/fixtures/locked_canonical/`` (built by ``scripts/lock_compat_snapshot.py`` from
each lock commit's own code; each hashes to its locked ``claim_sha256``). Extending it
changes lock verification and needs the maintainer's approval (CLAUDE.md).
"""

from __future__ import annotations

import copy
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from refute.core.canonical import canonical_bytes, canonical_sha256

Path = tuple[str, ...]

# The lock fields that identify a table entry; every one must be equal (L1).
IDENTITY_FIELDS = (
    "lock_version",
    "canonicalization",
    "claim_id",
    "claim_kind",
    "claim_path_in_repo",
    "claim_sha256",
    "code_sha256",
    "git_commit",
    "locked_at_utc",
)

_SYSTEMATIC_PERIODS = [13.7, 6.85, 4.566666666666666, 3.425, 1.0]
_UNRELIABLE = ["SPLIT", "DUPLICATE", "ARTIFACT"]


@dataclass(frozen=True)
class HistoricalLock:
    name: str
    identity: Mapping[str, Any]
    added: Mapping[Path, Any]  # key path added after the lock -> frozen value


HISTORICAL_LOCKS: tuple[HistoricalLock, ...] = (
    HistoricalLock(
        name="tess-calibration-v0.1@5214f2e",
        identity={
            "lock_version": 1,
            "canonicalization": "refute-cjson-1",
            "claim_id": "tess-calibration-v0.1",
            "claim_kind": "calibration",
            "claim_path_in_repo": "calibration/self_claim.yaml",
            "claim_sha256": "5701c54cb088f1d33895f73d98244d0ea214ddb3f861340d8261b817e189a53f",
            "code_sha256": "624f5f900334abcdc614a679a3fdc4ce9c9e8a465f2d3e553d71b24c199f4cfa",
            "git_commit": "5214f2e29de98803aafff3094733ca424ae3dbde",
            "locked_at_utc": "2026-10-07T21:42:15Z",
        },
        added={
            ("pass_criteria", "flag_excluded_tests"): [],
            ("pass_criteria", "flag_requires_signal_recovery"): False,
            ("pass_criteria", "flag_signal_period_factors"): [1.0, 2.0, 0.5],
            ("test_plan", "data", "neighbor_radius_arcsec"): 120.0,
            ("test_plan", "data", "target_pixel_files"): True,
            ("test_plan", "gauntlet", "aperture_depth"): {
                "core_radius_pixels": 1.5,
                "dilation_pixels": 1,
                "max_sigma": 3.0,
                "min_depth_ratio": 1.2,
            },
            ("test_plan", "gauntlet", "centroid_shift"): {
                "max_sigma": 3.0,
                "min_offset_pixels": 0.5,
                "min_sectors": 1,
            },
            ("test_plan", "gauntlet", "eb_catalog"): {
                "match_radius_arcsec": 21.0,
                "period_factors": [1.0, 2.0, 0.5],
                "period_tolerance": 0.01,
                "same_photometry_catalogs": ["TESS-EB"],
            },
            ("test_plan", "gauntlet", "holdout_by_year", "hidden_detrend_window_factor"): 3.0,
            ("test_plan", "gauntlet", "holdout_by_year", "max_hidden_window_fraction"): 0.5,
            ("test_plan", "gauntlet", "holdout_by_year", "max_timing_sigma_durations"): 1.0,
            ("test_plan", "gauntlet", "holdout_by_year", "max_train_duration_period_ratio"): 0.2,
            ("test_plan", "gauntlet", "holdout_by_year", "require_valid_train"): True,
            ("test_plan", "gauntlet", "nearby_contamination"): {
                "ignored_dispositions": _UNRELIABLE,
                "max_eclipse_depth": 1.0,
                "max_separation_arcsec": 21.0,
                "min_crowdsap": 0.8,
            },
            ("test_plan", "gauntlet", "period_alias"): {
                "detrend_window_periods": 3.0,
                "min_box_delta_bic": 10.0,
                "sine_harmonics": 2,
                "systematic_periods_days": _SYSTEMATIC_PERIODS,
                "systematic_tolerance": 0.01,
            },
            ("test_plan", "gauntlet", "plausibility", "max_tmag_mismatch"): 1.0,
            ("test_plan", "gauntlet", "plausibility", "unreliable_tic_dispositions"): _UNRELIABLE,
            ("test_plan", "gauntlet", "systematics"): {
                "dump_margin_hours": 1.0,
                "max_background_fraction": 0.5,
                "max_background_sigma": 3.0,
                "max_dump_fraction": 0.5,
                "max_sap_rel_diff": 0.5,
                "max_sap_sigma": 3.0,
                "min_events_for_dumps": 3,
            },
        },
    ),
    HistoricalLock(
        name="tess-calibration-v0.2@e176ac3",
        identity={
            "lock_version": 1,
            "canonicalization": "refute-cjson-1",
            "claim_id": "tess-calibration-v0.2",
            "claim_kind": "calibration",
            "claim_path_in_repo": "calibration/v0.2/self_claim.yaml",
            "claim_sha256": "c9f341d29bea4ec0d125adf3f0822fae4b593beabbdd19aeb339613e7a6b34a8",
            "code_sha256": "2cd8b5c16c9ded3e32335cd95d8b68f46e0676d5183f3129a6cef4e8dfbd1752",
            "git_commit": "e176ac3d21ca6e2efeb5085a8acb44d69624d520",
            "locked_at_utc": "2026-10-09T15:29:55Z",
        },
        added={
            ("pass_criteria", "flag_requires_signal_recovery"): False,
            ("pass_criteria", "flag_signal_period_factors"): [1.0, 2.0, 0.5],
            ("test_plan", "gauntlet", "eb_catalog", "same_photometry_catalogs"): ["TESS-EB"],
            ("test_plan", "gauntlet", "holdout_by_year", "max_hidden_window_fraction"): 0.5,
            ("test_plan", "gauntlet", "holdout_by_year", "max_train_duration_period_ratio"): 0.2,
            ("test_plan", "gauntlet", "holdout_by_year", "require_valid_train"): True,
        },
    ),
)

LIMIT = (
    "the projection shows that the claim content and the values resolved at lock time "
    "are intact; it does not show that the current code evaluates the claim the same way"
)


@dataclass
class Projection:
    """Outcome of a historical projection attempt."""

    entry: str | None  # name of the table entry, None when the lock is not listed
    applied: bool
    sha256: str | None = None
    reason: str = ""


def lock_identity(lock: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "lock_version": lock.get("lock_version"),
        "canonicalization": lock.get("canonicalization"),
        "claim_id": lock.get("claim_id"),
        "claim_kind": lock.get("claim_kind"),
        "claim_path_in_repo": lock.get("claim_path_in_repo"),
        "claim_sha256": lock.get("claim_sha256"),
        "code_sha256": (lock.get("code") or {}).get("sha256"),
        "git_commit": lock.get("git_commit"),
        "locked_at_utc": lock.get("locked_at_utc"),
    }


def find_entry(
    lock: Mapping[str, Any], table: tuple[HistoricalLock, ...] = HISTORICAL_LOCKS
) -> HistoricalLock | None:
    """The table entry whose identity equals the lock's, field by field (L1)."""
    identity = lock_identity(lock)
    for entry in table:
        if all(entry.identity.get(f) == identity[f] for f in IDENTITY_FIELDS) and set(
            entry.identity
        ) == set(IDENTITY_FIELDS):
            return entry
    return None


_MISSING = object()


def _get(tree: Any, path: Path) -> Any:
    node = tree
    for key in path:
        if not isinstance(node, Mapping) or key not in node:
            return _MISSING
        node = node[key]
    return node


def project(
    canonical: Mapping[str, Any],
    raw: Mapping[str, Any],
    lock: Mapping[str, Any],
    table: tuple[HistoricalLock, ...] = HISTORICAL_LOCKS,
) -> Projection:
    """Remove exactly the listed paths and hash the rest (L1-L4).

    ``canonical`` is the resolved claim, ``raw`` the claim file as written. Returns an
    unapplied projection, with the reason, whenever a safeguard is not met.
    """
    entry = find_entry(lock, table)
    if entry is None:
        return Projection(entry=None, applied=False, reason="lock not in the table")
    for path in entry.added:
        if _get(raw, path) is not _MISSING:
            return Projection(
                entry.name,
                False,
                reason=f"field {'.'.join(path)} is written in the claim file",
            )
        value = _get(canonical, path)
        if value is _MISSING:
            return Projection(entry.name, False, reason=f"field {'.'.join(path)} is absent")
        if canonical_bytes(value) != canonical_bytes(entry.added[path]):
            return Projection(
                entry.name,
                False,
                reason=f"field {'.'.join(path)} differs from its frozen value",
            )
    projected = copy.deepcopy(dict(canonical))
    for path in entry.added:
        parent = _get(projected, path[:-1]) if len(path) > 1 else projected
        del parent[path[-1]]
    return Projection(entry.name, True, sha256=canonical_sha256(projected))
