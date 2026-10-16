"""scripts/check_interpreter.py: the CI fails unless the interpreter has the pinned exact
version and is a uv-managed build (WP0, docs/validation/v0.3/wp0-acceptance.md 3.5)."""

import subprocess
import sys
from pathlib import Path

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
