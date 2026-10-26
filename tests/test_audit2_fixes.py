"""Two fixes of Codex's audit of 2026-10-26 (on ab4c233), decided by the maintainer the same day:
R1 (an archive never writes into the tree it archives, nor over an existing archive) and R4 (a
claim that lists one attachment twice, also after normalizing the path, is refused at its
validation, before any dossier). Written before the code. Synthetic files only; no network."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from conftest import replicate_claim, target_entry, write_yaml
from refute.cli import app
from refute.core.claim import ClaimError, load_claim
from refute.core.dossier import write_archive
from refute.core.hashing import sha256_file


def _run_dir(tmp_path: Path) -> Path:
    run = tmp_path / "run"
    (run / "TIC-1").mkdir(parents=True)
    (run / "TIC-1" / "verdict.json").write_bytes(b'{"verdict": "SURVIVED"}\n')
    (run / "a.txt").write_bytes(b"a\n")
    return run


def _hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha256_file(p) for p in root.rglob("*") if p.is_file()}


# --- R1 ------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "target", ["inside.zip", "TIC-1/inside.zip", "a.txt", "TIC-1/verdict.json"]
)
def test_r1_a_destination_inside_the_tree_is_refused_before_any_write(tmp_path, target):
    run = _run_dir(tmp_path)
    before = _hashes(run)
    with pytest.raises(ValueError, match="inside"):
        write_archive(run, run / target)
    assert _hashes(run) == before


def test_r1_an_existing_archive_or_digest_is_never_overwritten(tmp_path):
    run = _run_dir(tmp_path)
    out = tmp_path / "out" / "run.zip"
    out.parent.mkdir()
    out.write_bytes(b"an earlier archive")
    with pytest.raises(FileExistsError):
        write_archive(run, out)
    assert out.read_bytes() == b"an earlier archive"
    out.unlink()
    sidecar = out.with_name(out.name + ".sha256")
    sidecar.write_bytes(b"an earlier digest\n")
    with pytest.raises(FileExistsError):
        write_archive(run, out)
    assert sidecar.read_bytes() == b"an earlier digest\n" and not out.exists()


def test_r1_an_archive_outside_the_tree_is_written(tmp_path):
    run = _run_dir(tmp_path)
    before = _hashes(run)
    path, digest = write_archive(run, tmp_path / "out" / "run.zip")
    assert path.is_file() and sha256_file(path) == digest
    assert _hashes(run) == before


def test_r1_a_destination_through_a_link_into_the_tree_is_refused(tmp_path):
    import os

    run = _run_dir(tmp_path)
    before = _hashes(run)
    link = tmp_path / "out"
    try:
        os.symlink(run / "TIC-1", link, target_is_directory=True)
    except OSError:
        pytest.skip("this account cannot create symbolic links")
    with pytest.raises(ValueError, match="inside"):
        write_archive(run, link / "run.zip")
    assert _hashes(run) == before


def test_r1_a_relative_root_names_the_entries_by_the_folder(tmp_path, monkeypatch):
    import zipfile

    run = _run_dir(tmp_path)
    monkeypatch.chdir(run)
    path, _ = write_archive(Path("."), tmp_path / "dot.zip")
    names = zipfile.ZipFile(path).namelist()
    assert names and all(n.startswith("run/") for n in names), names
    monkeypatch.chdir(run / "TIC-1")
    path, _ = write_archive(Path(".."), tmp_path / "up.zip")
    assert all(n.startswith("run/") for n in zipfile.ZipFile(path).namelist())


def test_r4_the_ml_production_refuses_a_repeated_attachment(tmp_path, monkeypatch):
    import json

    from refute.packs.ml import production

    class ReachedError(Exception):
        pass

    def first_effect():
        raise ReachedError

    monkeypatch.setattr(production, "refute_checkout", first_effect)
    argv = ["--paper", "p", "--root", str(tmp_path / "root"), "--out", str(tmp_path / "out"),
            "--cache", str(tmp_path / "cache")]  # fmt: skip
    for attachments, refused in (
        ([{"path": "count.json"}, {"path": "./count.json"}], True),
        ([{"path": "count.json"}, {"path": "COUNT.json"}], True),
        ([{"path": "count.json"}, {"path": "other.json"}], False),  # the control
    ):
        claim = tmp_path / "claim.json"
        claim.write_text(
            json.dumps({"targets": [{"key": "c1"}], "attachments": attachments, "test_plan": {}}),
            encoding="utf-8",
        )
        expected = production.ProductionError if refused else ReachedError
        with pytest.raises(expected):
            production.main(["--claim", str(claim), *argv])


def test_r1_the_cli_refuses_with_exit_1(tmp_path):
    run = _run_dir(tmp_path)
    before = _hashes(run)
    result = CliRunner().invoke(app, ["archive", str(run), "--out", str(run / "x.zip")])
    assert result.exit_code == 1 and _hashes(run) == before


# --- R4 ------------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("first", "second"),
    [
        ("data/a.csv", "data/a.csv"),
        ("data/a.csv", "./data/a.csv"),
        ("data/a.csv", "data//a.csv"),
        ("data/a.csv", "data/./a.csv"),
        ("data/a.csv", "Data/A.csv"),  # one file on a case-insensitive file system
    ],
)
def test_r4_a_repeated_attachment_is_refused_at_validation(tmp_path, first, second):
    claims = tmp_path / "claims"
    (claims / "data").mkdir(parents=True)
    (claims / "data" / "a.csv").write_bytes(b"x\n")
    claim = write_yaml(
        claims / "claim.yaml",
        replicate_claim(
            [target_entry(1, "planet", 3.7)],
            attachments=[{"path": first, "role": "one"}, {"path": second, "role": "two"}],
        ),
    )
    with pytest.raises(ClaimError, match="attachment"):
        load_claim(claim)
    result = CliRunner().invoke(app, ["lock", str(claim)])
    assert result.exit_code != 0
    assert not (claims / "claim.lock.json").exists()


def test_r4_distinct_attachments_still_load(tmp_path):
    claims = tmp_path / "claims"
    (claims / "data").mkdir(parents=True)
    for name in ("a.csv", "b.csv"):
        (claims / "data" / name).write_bytes(b"x\n")
    claim = write_yaml(
        claims / "claim.yaml",
        replicate_claim(
            [target_entry(1, "planet", 3.7)],
            attachments=[{"path": "data/a.csv", "role": "one"}, {"path": "data/b.csv"}],
        ),
    )
    assert [a.path for a in load_claim(claim).claim.attachments] == ["data/a.csv", "data/b.csv"]
