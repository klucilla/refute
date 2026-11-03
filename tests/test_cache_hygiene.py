"""Work folders under .cache/ are removed after each test (#197; v0.5 acceptance, case 8.5)."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest

from conftest import CACHE, cache_test_dir, remove_cache_test_dir

_LEFT: list[Path] = []


def test_the_path_is_a_fresh_uuid_folder_under_cache():
    path = cache_test_dir("hygiene")
    assert path.parent == CACHE / "test-hygiene"
    assert len(path.name) == 32 and all(c in "0123456789abcdef" for c in path.name)
    assert not path.exists()
    assert cache_test_dir("hygiene") != path


@pytest.mark.parametrize("name", ["", "../x", "a/b", "a\\b", ".hidden", "x y"])
def test_an_unsafe_name_is_refused(name):
    with pytest.raises(ValueError):
        cache_test_dir(name)


@pytest.mark.parametrize(
    "path",
    [
        CACHE,
        CACHE / "v05",
        CACHE / "test-hygiene",
        CACHE / "test-hygiene" / "not-a-uuid",
        CACHE / "v05" / ("a" * 32),
        CACHE.parent / "test-hygiene" / ("a" * 32),
        CACHE / "test-hygiene" / ("A" * 32),
    ],
)
def test_the_guard_refuses_any_other_path(path):
    with pytest.raises(RuntimeError, match="refusing to remove"):
        remove_cache_test_dir(path)


def test_a_folder_with_a_read_only_file_is_created_here():
    path = cache_test_dir("hygiene")
    (path / "sub").mkdir(parents=True)
    locked = path / "sub" / "locked.txt"
    locked.write_text("x", encoding="utf-8")
    os.chmod(locked, stat.S_IREAD)
    _LEFT.append(path)
    assert locked.exists()


def test_the_folder_of_the_previous_test_is_gone():
    # the autouse fixture of conftest removed it after the previous test, and the empty
    # test-hygiene folder with it
    assert _LEFT, "runs after the previous test"
    assert not _LEFT[0].exists()
    assert not _LEFT[0].parent.exists()
