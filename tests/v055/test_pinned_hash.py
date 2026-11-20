"""v0.5.5: the pinned code hash's manifest check and its restoration
(``docs/validation/v0.5.5/pinned_hash.py``), on hand-made manifests; no network."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parents[2] / "docs/validation/v0.5.5"
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

import pinned_hash as ph  # noqa: E402

EXPECTED = {"src/a.py": "1", "pyproject.toml": "2", "uv.lock": "old"}


def test_the_manifest_accepts_the_pinned_or_the_approved_lock_only():
    approved = {"old", "approved"}
    assert ph.check_manifest(dict(EXPECTED), EXPECTED, approved) is None
    assert ph.check_manifest({**EXPECTED, "uv.lock": "approved"}, EXPECTED, approved) is None
    assert "uv.lock" in ph.check_manifest({**EXPECTED, "uv.lock": "other"}, EXPECTED, approved)


def test_the_manifest_refuses_a_source_change_or_an_extra_covered_file():
    approved = {"old"}
    assert "changed" in ph.check_manifest({**EXPECTED, "src/a.py": "9"}, EXPECTED, approved)
    extra = {**EXPECTED, "src/ignored_by_git.py": "3"}
    assert "added" in ph.check_manifest(extra, EXPECTED, approved)
    missing = {k: v for k, v in EXPECTED.items() if k != "pyproject.toml"}
    assert "missing" in ph.check_manifest(missing, EXPECTED, approved)


def test_pinned_restores_the_function_also_on_an_error():
    from refute.core import codehash

    original = codehash.compute_code_hash
    marker = object()
    with pytest.raises(RuntimeError), ph.pinned(marker):
        assert codehash.compute_code_hash() is marker
        raise RuntimeError("inside")
    assert codehash.compute_code_hash is original


def test_ls_tree_paths_keep_spaces_and_unicode():
    out = "src/a b.py\0src/\u00e7.py\0src/c.py\0".encode()
    assert ph.ls_tree_paths(out) == ["src/a b.py", "src/\u00e7.py", "src/c.py"]
    assert ph.ls_tree_paths(b"") == []
