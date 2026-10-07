import zipfile

from refute.core.dossier import write_archive
from refute.core.hashing import sha256_file


def _run_dir(root):
    run = root / "run-1"
    (run / "TIC-1" / "plots").mkdir(parents=True)
    (run / "TIC-1" / "verdict.json").write_text('{"verdict": "SURVIVED"}\n', encoding="utf-8")
    (run / "TIC-1" / "plots" / "a.png").write_bytes(b"\x89PNG fake")
    (run / "summary.md").write_text("# summary\n", encoding="utf-8")
    return run


def test_archive_is_byte_identical_and_hash_matches(tmp_path):
    run = _run_dir(tmp_path)
    first, digest1 = write_archive(run, tmp_path / "a" / "run.zip")
    second, digest2 = write_archive(run, tmp_path / "b" / "run.zip")
    assert first.read_bytes() == second.read_bytes()
    assert digest1 == digest2 == sha256_file(first)
    sidecar = (tmp_path / "a" / "run.zip.sha256").read_text(encoding="utf-8")
    assert sidecar == f"{digest1}  run.zip\n"
    with zipfile.ZipFile(first) as archive:
        names = archive.namelist()
        assert names == sorted(names)
        assert names == ["run-1/TIC-1/plots/a.png", "run-1/TIC-1/verdict.json", "run-1/summary.md"]
        assert all(info.date_time == (1980, 1, 1, 0, 0, 0) for info in archive.infolist())
