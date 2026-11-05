"""calibration/v0.5/archive_run.py: archiving a collected run's large files to the Drive with a
checked SHA-256 manifest, on synthetic files only (a test folder stands in for the Drive)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from conftest import cache_test_dir

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "calibration" / "v0.5" / "archive_run.py"

spec = importlib.util.spec_from_file_location("v05_archive_run", SCRIPT)
archive = importlib.util.module_from_spec(spec)
spec.loader.exec_module(archive)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _setup(base: Path) -> tuple[Path, Path, bytes]:
    root = base / "repo"
    run = root / ".cache/v05/calibration/step"
    run.mkdir(parents=True)
    big = b"record\n" * 1000
    small = b"{}\n"
    (run / "records.jsonl").write_bytes(big)
    (run / "report.json").write_bytes(small)
    out = root / "calibration/v0.5/runs/step"
    out.mkdir(parents=True)
    listing = {
        "run_folder": ".cache/v05/calibration/step",
        "files": [
            {"path": "records.jsonl", "bytes": len(big), "sha256": _sha(big), "in_git": False},
            {"path": "report.json", "bytes": len(small), "sha256": _sha(small), "in_git": True},
        ],
    }
    (out / "files.json").write_text(json.dumps(listing), encoding="utf-8")
    return root, base / "drive", big


def test_archives_only_files_outside_git_with_a_checked_manifest(request):
    root, drive, big = _setup(cache_test_dir("v05-archive", request))
    result = archive.archive_run(root, "step", drive)
    assert result["problems"] == []
    assert [f["path"] for f in result["files"]] == ["records.jsonl"]
    assert (drive / "step/records.jsonl").read_bytes() == big
    assert not (drive / "step/report.json").exists()
    manifest = (root / "calibration/v0.5/runs/step/drive-manifest.sha256").read_bytes()
    assert manifest == f"{_sha(big)}  records.jsonl\n".encode()
    assert (drive / "step/MANIFEST.sha256").read_bytes() == manifest
    assert (drive / "step/archive_run.py").read_bytes() == SCRIPT.read_bytes()


DOSSIER_SCRIPT = ROOT / "calibration" / "v0.5" / "archive_dossiers.py"
spec_d = importlib.util.spec_from_file_location("v05_archive_dossiers", DOSSIER_SCRIPT)
archive_d = importlib.util.module_from_spec(spec_d)
spec_d.loader.exec_module(archive_d)


def test_dossiers_archived_as_one_checked_zip(request):
    import zipfile

    base = cache_test_dir("v05-archive", request)
    root = base / "repo"
    source = root / "dossiers/run"
    (source / "TIC-1").mkdir(parents=True)
    (source / "TIC-1/verdict.json").write_bytes(b'{"v": 1}\n')
    (source / "summary.json").write_bytes(b"{}\n")
    (source / "summary.md").write_bytes(b"# s\n")
    result = archive_d.archive(root, Path("dossiers/run"), "c3-dossiers", base / "drive")
    assert result["problems"] == [] and result["members"] == 3
    with zipfile.ZipFile(base / "drive/c3-dossiers/c3-dossiers.zip") as zf:
        assert zf.namelist() == ["TIC-1/verdict.json", "summary.json", "summary.md"]
        assert zf.read("TIC-1/verdict.json") == b'{"v": 1}\n'
    out = root / "calibration/v0.5/runs/c3-dossiers"
    manifest = (out / "drive-manifest.sha256").read_bytes()
    assert manifest == (base / "drive/c3-dossiers/MANIFEST.sha256").read_bytes()
    assert f"{_sha(b'{}' + bytes([10]))}  summary.json".encode() in manifest
    assert (out / "summary.md").read_bytes() == b"# s\n"
    with pytest.raises(ValueError, match="not replaced"):
        archive_d.archive(root, Path("dossiers/run"), "c3-dossiers", base / "drive")


def test_refuses_a_changed_source_and_an_existing_drive_folder(request):
    root, drive, _ = _setup(cache_test_dir("v05-archive", request))
    (root / ".cache/v05/calibration/step/records.jsonl").write_bytes(b"changed\n")
    with pytest.raises(ValueError, match="changed since files.json"):
        archive.archive_run(root, "step", drive)
    root, drive, _ = _setup(cache_test_dir("v05-archive", request))
    (drive / "step").mkdir(parents=True)
    with pytest.raises(ValueError, match="not replaced"):
        archive.archive_run(root, "step", drive)
