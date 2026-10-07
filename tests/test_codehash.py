from pathlib import Path

from conftest import replicate_claim, target_entry, write_yaml
from refute.core.codehash import compute_code_hash, diff_code_files, project_root
from refute.core.lock import VerifyStatus, create_lock, verify_claim
from refute.core.run import execute_run


def _tree(root: Path, newline: bytes = b"\n") -> Path:
    (root / "src" / "refute" / "core").mkdir(parents=True)
    (root / "src" / "refute" / "__init__.py").write_bytes(b'__version__ = "0"' + newline)
    (root / "src" / "refute" / "core" / "a.py").write_bytes(b"x = 1" + newline + b"y = 2" + newline)
    (root / "pyproject.toml").write_bytes(b"[project]" + newline + b'name = "refute"' + newline)
    (root / "uv.lock").write_bytes(b"version = 1" + newline)
    return root


def test_code_hash_is_deterministic_and_covers_expected_files(tmp_path):
    root = _tree(tmp_path / "a")
    first, second = compute_code_hash(root), compute_code_hash(root)
    assert first == second
    paths = [p for p, _ in first.files]
    assert paths == sorted(paths)
    assert set(paths) == {
        "pyproject.toml",
        "src/refute/__init__.py",
        "src/refute/core/a.py",
        "uv.lock",
    }


def test_code_hash_ignores_line_endings_and_bytecode(tmp_path):
    lf = compute_code_hash(_tree(tmp_path / "lf"))
    crlf_root = _tree(tmp_path / "crlf", newline=b"\r\n")
    cache = crlf_root / "src" / "refute" / "__pycache__"
    cache.mkdir()
    (cache / "a.cpython-313.pyc").write_bytes(b"\x00\x01binary")
    assert compute_code_hash(crlf_root).sha256 == lf.sha256


def test_one_byte_edit_changes_hash_and_is_named(tmp_path):
    root = _tree(tmp_path / "a")
    before = compute_code_hash(root)
    target = root / "src" / "refute" / "core" / "a.py"
    target.write_bytes(target.read_bytes().replace(b"x = 1", b"x = 2"))
    after = compute_code_hash(root)
    assert after.sha256 != before.sha256
    assert diff_code_files(before.to_dict()["files"], after) == ["modified: src/refute/core/a.py"]


def test_verify_reports_code_tampering_and_runs_abort(tmp_path):
    root = _tree(tmp_path / "code")
    claim = write_yaml(
        tmp_path / "claims" / "claim.yaml", replicate_claim([target_entry(1, "planet", 3.7)])
    )
    create_lock(claim, code_root=root)
    assert verify_claim(claim, code_root=root).status is VerifyStatus.PASS
    (root / "src" / "refute" / "core" / "new.py").write_text("z = 3\n", encoding="utf-8")
    result = verify_claim(claim, code_root=root)
    assert result.status is VerifyStatus.TAMPERED
    assert "code" in result.tampered
    assert "added: src/refute/core/new.py" in result.changed_files
    outcome = execute_run(
        claim, mode="replicate", out_dir=tmp_path / "out", offline=True, code_root=root
    )
    assert outcome.exit_code == 2
    assert not (tmp_path / "out").exists()


def test_project_root_is_this_checkout():
    root = project_root()
    assert (root / "pyproject.toml").is_file()
    assert (root / "src" / "refute" / "__init__.py").is_file()
