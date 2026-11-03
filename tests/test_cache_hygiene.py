"""Work folders under .cache/ are removed when their owner ends, and nothing else is ever
removed (#197; v0.5 acceptance, case 8.5; Codex's end-of-round review of 2026-11-03)."""

from __future__ import annotations

import os
import stat
import subprocess
import sys
from pathlib import Path

import pytest

import conftest
from conftest import CACHE, cache_test_dir, remove_cache_test_dir

_LEFT: list[Path] = []


def _forget(path: Path) -> None:
    # a test that makes the guard refuse an allocation takes it off the books itself
    conftest._owned.discard(path)
    if path in conftest._by_test:
        conftest._by_test.remove(path)


def _link(link: Path, target: Path) -> str | None:
    """A directory symlink, or else a junction (Windows); None when neither can be made."""
    try:
        os.symlink(target, link, target_is_directory=True)
        return None
    except OSError as error:
        if sys.platform != "win32":
            return str(error)
    done = subprocess.run(
        ["cmd", "/c", "mklink", "/J", str(link), str(target)], capture_output=True, text=True
    )
    return None if done.returncode == 0 else done.stdout + done.stderr


def _unlink(link: Path) -> None:
    # removes the link itself, never what it points to
    if link.is_junction() or (sys.platform == "win32" and link.is_symlink()):
        os.rmdir(link)
    else:
        link.unlink()


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
        CACHE / "test-hygiene" / ("a" * 32),  # the right form, but never allocated
        CACHE.parent / "test-hygiene" / ("a" * 32),
        Path(".cache") / "test-hygiene" / ("a" * 32),  # relative
    ],
)
def test_the_guard_refuses_a_path_it_did_not_allocate(path):
    with pytest.raises(RuntimeError, match="refusing to remove"):
        remove_cache_test_dir(path)


def test_a_relative_spelling_of_an_allocation_is_refused():
    path = cache_test_dir("hygiene")
    relative = Path(os.path.relpath(path, Path.cwd()))
    with pytest.raises(RuntimeError, match="not allocated"):
        remove_cache_test_dir(relative)


def test_a_link_in_place_of_the_folder_is_refused_and_its_target_kept(tmp_path):
    target = tmp_path / "outside"
    (target / "keep").mkdir(parents=True)
    (target / "keep" / "file.txt").write_text("x", encoding="utf-8")
    path = cache_test_dir("hygiene")
    path.parent.mkdir(parents=True, exist_ok=True)
    why = _link(path, target)
    if why is not None:
        _forget(path)
        pytest.skip(f"this machine cannot create a directory link: {why}")
    try:
        with pytest.raises(RuntimeError, match="link or a junction"):
            remove_cache_test_dir(path)
        assert (target / "keep" / "file.txt").exists()
    finally:
        _unlink(path)
        _forget(path)
        try:
            path.parent.rmdir()
        except OSError:
            pass


def test_a_redirected_cache_is_refused(tmp_path, monkeypatch):
    # the critical finding: if .cache itself pointed outside the project, its test-*/<uuid>
    # descendants would pass a guard based on resolved paths
    root = tmp_path / "project"
    root.mkdir()
    outside = tmp_path / "outside"
    allocated_outside = outside / "test-hygiene"
    allocated_outside.mkdir(parents=True)
    why = _link(root / ".cache", outside)
    if why is not None:
        pytest.skip(f"this machine cannot create a directory link: {why}")
    monkeypatch.setattr(conftest, "ROOT", root)
    monkeypatch.setattr(conftest, "CACHE", root / ".cache")
    path = conftest.cache_test_dir("hygiene")
    (outside / "test-hygiene" / path.name / "keep").mkdir(parents=True)
    try:
        with pytest.raises(RuntimeError, match="link or a junction"):
            conftest.remove_cache_test_dir(path)
        assert (outside / "test-hygiene" / path.name / "keep").exists()
    finally:
        _forget(path)
        _unlink(root / ".cache")


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
    assert _LEFT[0] not in conftest._owned


@pytest.fixture(scope="module")
def module_folder(request):
    path = cache_test_dir("hygiene-module", request)
    path.mkdir(parents=True)
    return path


def test_a_module_fixture_folder_outlives_the_first_test(module_folder):
    assert module_folder.exists()


def test_a_module_fixture_folder_is_still_there_for_the_second(module_folder):
    # removed by the fixture's finalizer at the end of the module, not after a test
    assert module_folder.exists()
