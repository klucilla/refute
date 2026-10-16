"""scripts/check_interpreter.py: the CI fails unless the interpreter has the pinned exact
version and is a uv-managed build (WP0, docs/validation/v0.3/wp0-acceptance.md 3.5)."""

import os
import platform
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "check_interpreter.py"
sys.path.insert(0, str(ROOT / "scripts"))

from check_interpreter import problems  # noqa: E402


def test_the_pinned_managed_interpreter_passes(tmp_path):
    managed = tmp_path / "uv-python" / "cpython-3.13.16-windows-x86_64-none"
    managed.mkdir(parents=True)
    assert problems("3.13.16", str(managed), str(tmp_path / "uv-python"), "3.13.16") == []


def test_another_patch_version_fails(tmp_path):
    managed = tmp_path / "uv-python" / "cpython-3.13.15"
    managed.mkdir(parents=True)
    found = problems("3.13.15", str(managed), str(tmp_path / "uv-python"), "3.13.16")
    assert found == ["version 3.13.15, expected exactly 3.13.16"]


def test_a_system_interpreter_fails(tmp_path):
    system = tmp_path / "usr"
    system.mkdir()
    (tmp_path / "uv-python").mkdir()
    found = problems("3.12.15", str(system), str(tmp_path / "uv-python"), "3.12.15")
    assert len(found) == 1 and "is not inside" in found[0]


def test_a_sibling_folder_with_the_same_prefix_is_not_inside(tmp_path):
    """'uv-python-evil' starts with 'uv-python' but is not inside it."""
    sibling = tmp_path / "uv-python-evil" / "cpython-3.12.15"
    sibling.mkdir(parents=True)
    (tmp_path / "uv-python").mkdir()
    found = problems("3.12.15", str(sibling), str(tmp_path / "uv-python"), "3.12.15")
    assert len(found) == 1 and "is not inside" in found[0]


def test_the_install_directory_itself_is_not_an_installation(tmp_path):
    root = tmp_path / "uv-python"
    root.mkdir()
    found = problems("3.12.15", str(root), str(root), "3.12.15")
    assert len(found) == 1 and "is not inside" in found[0]


def test_no_install_directory_fails():
    found = problems("3.12.15", "/somewhere", "", "3.12.15")
    assert found == ["no uv Python install directory given (UV_PYTHON_INSTALL_DIR)"]


def test_another_implementation_fails(tmp_path):
    managed = tmp_path / "uv-python" / "pypy-3.12.15"
    managed.mkdir(parents=True)
    found = problems("3.12.15", str(managed), str(tmp_path / "uv-python"), "3.12.15", "PyPy")
    assert found == ["implementation PyPy, expected CPython"]


def _symlink(link: Path, target: Path) -> None:
    try:
        os.symlink(target, link, target_is_directory=True)
    except (OSError, NotImplementedError) as exc:  # Windows without the symlink privilege
        pytest.skip(f"cannot create a directory symlink here: {exc}")


def test_a_link_inside_the_install_directory_to_a_folder_outside_is_not_inside(tmp_path):
    """The base installation is resolved before the comparison: a link placed inside the
    install directory that points outside it does not count as inside."""
    outside = tmp_path / "elsewhere" / "cpython-3.12.15"
    outside.mkdir(parents=True)
    root = tmp_path / "uv-python"
    root.mkdir()
    _symlink(root / "cpython-3.12.15", outside)
    found = problems("3.12.15", str(root / "cpython-3.12.15"), str(root), "3.12.15")
    assert len(found) == 1 and "is not inside" in found[0]


def test_an_install_directory_given_through_a_link_is_resolved_too(tmp_path):
    real = tmp_path / "real-uv-python"
    (real / "cpython-3.12.15").mkdir(parents=True)
    _symlink(tmp_path / "uv-python", real)
    found = problems(
        "3.12.15", str(real / "cpython-3.12.15"), str(tmp_path / "uv-python"), "3.12.15"
    )
    assert found == []


@pytest.mark.skipif(sys.platform != "win32", reason="paths are case-insensitive on Windows")
def test_on_windows_the_case_of_a_path_does_not_matter(tmp_path):
    managed = tmp_path / "uv-python" / "cpython-3.12.15"
    managed.mkdir(parents=True)
    root = str(tmp_path / "uv-python")
    assert problems("3.12.15", str(managed).upper(), root.lower(), "3.12.15") == []


@pytest.mark.skipif(sys.platform != "win32", reason="drive letters exist on Windows only")
def test_on_windows_a_base_on_another_drive_is_not_inside(tmp_path):
    drive = os.path.splitdrive(str(tmp_path))[0].upper()
    other = "Y:" if drive != "Y:" else "Z:"
    found = problems("3.12.15", other + "\\uv-python\\cpython-3.12.15", str(tmp_path), "3.12.15")
    assert len(found) == 1 and "is not inside" in found[0]


def test_the_script_passes_for_this_interpreter_in_its_own_install_directory():
    """Run as a script, with the install directory from UV_PYTHON_INSTALL_DIR: the folder
    holding this interpreter's base installation, and this interpreter's own version, so
    the script must pass (the positive path of the CLI)."""
    env = dict(os.environ, UV_PYTHON_INSTALL_DIR=str(Path(sys.base_prefix).resolve().parent))
    out = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), platform.python_version()],
        capture_output=True,
        text=True,
        check=False,
        env=env,
    )
    assert out.returncode == 0, out.stdout + out.stderr
    assert "OK: CPython" in out.stdout


def test_the_script_reports_and_fails_for_this_interpreter(tmp_path):
    """Run as a script against an empty install directory: this interpreter is not inside
    it, so the script exits 1 and says why."""
    empty = tmp_path / "uv-python"
    empty.mkdir()
    out = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), "0.0.0", str(empty)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert out.returncode == 1
    assert "FAIL: version" in out.stdout and "is not inside" in out.stdout


def test_usage_errors():
    out = subprocess.run(
        [sys.executable, "-I", str(SCRIPT)], capture_output=True, text=True, check=False
    )
    assert out.returncode == 2
