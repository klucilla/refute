"""Seal of the experimental core and annexes (docs/validation/v0.3/wp2-acceptance.md,
W2.11-W2.12). Synthetic dossiers in tmp_path, offline."""

import io
import json
import zipfile

import pytest
from typer.testing import CliRunner

from refute.cli import app
from refute.core.dossier import DossierWriter, check_dossier, verify_manifest
from refute.core.hashing import sha256_file
from refute.core.seal import (
    ANNEX_MANIFEST,
    SEAL_NAME,
    SealError,
    add_annex,
    check_sealed,
    combined_sha256,
    core_archive,
    core_sha256,
    read_seal,
    seal,
    verify_seal,
)

BINARY = b"\x00\x01\r\n\x02 binary with CRLF bytes"


def make_dossier(root, newline="\n"):
    w = DossierWriter(root)
    w.write_text("claim.yaml", f"id: c1{newline}kind: replicate{newline}")
    w.write_json("verdict.json", {"verdict": "REPRODUCED", "tests": []})
    w.write_text("logs/run.log", f"line 1{newline}line 2{newline}")
    w.write_bytes("outputs/predictions.bin", BINARY)
    w.finalize()
    return root


def annex_source(root, text="Reviewer report: no objection.\n"):
    root.mkdir(parents=True, exist_ok=True)
    (root / "report.md").write_text(text, encoding="utf-8", newline="\n")
    return root


# W2.11 ------------------------------------------------------------------------------------


def test_seal_writes_the_core_hash_and_the_core_is_intact(tmp_path):
    d = make_dossier(tmp_path / "D1")
    record = seal(d)
    assert record == read_seal(d)
    assert record["core_sha256"] == core_sha256(d)
    assert [f["path"] for f in record["files"]] == [
        "MANIFEST.sha256",
        "claim.yaml",
        "logs/run.log",
        "outputs/predictions.bin",
        "verdict.json",
    ]
    assert verify_seal(d) == []
    assert verify_manifest(d) == []  # SEAL.json is not a core file


def test_archive_is_deterministic_stored_and_sorted(tmp_path):
    a = make_dossier(tmp_path / "A")
    b = make_dossier(tmp_path / "B")
    assert core_archive(a) == core_archive(b)
    with zipfile.ZipFile(io.BytesIO(core_archive(a))) as z:
        infos = z.infolist()
    assert [i.filename for i in infos] == sorted(i.filename for i in infos)
    assert all(i.compress_type == zipfile.ZIP_STORED for i in infos)
    assert all(i.date_time == (1980, 1, 1, 0, 0, 0) for i in infos)
    assert all(i.external_attr == 0o644 << 16 and i.create_system == 3 for i in infos)


def test_the_archive_holds_the_raw_bytes_so_a_line_ending_change_is_detected(tmp_path):
    """The archive stores raw bytes, consistent with MANIFEST.sha256; the repository's
    .gitattributes keeps text LF on every checkout. A change of terminators only is a
    change of the core."""
    d = make_dossier(tmp_path / "D1")
    seal(d)
    with zipfile.ZipFile(io.BytesIO(core_archive(d))) as z:
        assert z.read("claim.yaml") == (d / "claim.yaml").read_bytes()
    raw = (d / "logs/run.log").read_bytes()
    (d / "logs/run.log").write_bytes(raw.replace(b"\n", b"\r\n"))
    assert any("core file modified: logs/run.log" in p for p in verify_seal(d))


def test_binary_content_is_hashed_as_it_is(tmp_path):
    a = make_dossier(tmp_path / "A")
    b = make_dossier(tmp_path / "B")
    (b / "outputs/predictions.bin").write_bytes(BINARY.replace(b"\r\n", b"\n"))
    assert core_sha256(a) != core_sha256(b)


def test_a_dossier_is_sealed_once(tmp_path):
    d = make_dossier(tmp_path / "D1")
    seal(d)
    with pytest.raises(SealError, match="already sealed"):
        seal(d)


def test_seal_refuses_a_broken_manifest(tmp_path):
    d = make_dossier(tmp_path / "D1")
    (d / "verdict.json").write_text("{}", encoding="utf-8")
    with pytest.raises(SealError, match="manifest is not intact"):
        seal(d)
    assert not (d / SEAL_NAME).exists()


def test_combined_hash_of_a_set(tmp_path):
    cores = {"D2": "b" * 64, "D1": "a" * 64}
    assert combined_sha256(cores) == combined_sha256(dict(sorted(cores.items())))
    assert combined_sha256(cores) != combined_sha256({**cores, "D2": "c" * 64})


# W2.12 ------------------------------------------------------------------------------------


def test_annex_added_after_the_seal_leaves_the_core_intact(tmp_path):
    d = make_dossier(tmp_path / "D1")
    before = seal(d)["core_sha256"]
    record = add_annex(d, "review-claude", annex_source(tmp_path / "src"))
    assert record["core_sha256"] == before
    assert core_sha256(d) == before  # adding an annex never changes the core hash
    check = check_sealed(d)
    assert check.core_problems == [] and check.annexes == {"review-claude": []}
    assert verify_manifest(d) == []
    assert check_dossier(d).ok


def test_changed_byte_in_the_core_is_reported_as_core_not_intact(tmp_path):
    d = make_dossier(tmp_path / "D1")
    seal(d)
    add_annex(d, "reply", annex_source(tmp_path / "src"))
    data = bytearray((d / "outputs/predictions.bin").read_bytes())
    data[3] ^= 1
    (d / "outputs/predictions.bin").write_bytes(bytes(data))
    check = check_sealed(d)
    assert any("core file modified: outputs/predictions.bin" in p for p in check.core_problems)
    assert not check_dossier(d).ok


def test_changed_annex_is_not_intact_while_the_core_stays_intact(tmp_path):
    d = make_dossier(tmp_path / "D1")
    seal(d)
    add_annex(d, "reply", annex_source(tmp_path / "src"))
    (d / "annexes/reply/report.md").write_text("edited\n", encoding="utf-8")
    check = check_sealed(d)
    assert check.core_problems == []
    assert check.annexes["reply"] == ["annex file modified: report.md"]


@pytest.mark.parametrize("change", ["extra", "missing", "cites-other-core"])
def test_other_annex_changes_are_detected(tmp_path, change):
    d = make_dossier(tmp_path / "D1")
    seal(d)
    add_annex(d, "reply", annex_source(tmp_path / "src"))
    annex = d / "annexes" / "reply"
    if change == "extra":
        (annex / "late.md").write_text("added later\n", encoding="utf-8")
    elif change == "missing":
        (annex / "report.md").unlink()
    else:
        record = json.loads((annex / ANNEX_MANIFEST).read_text(encoding="utf-8"))
        record["core_sha256"] = "0" * 64
        (annex / ANNEX_MANIFEST).write_text(json.dumps(record), encoding="utf-8")
    problems = check_sealed(d).annexes["reply"]
    assert problems
    assert check_sealed(d).core_problems == []


def test_annex_needs_a_sealed_intact_core(tmp_path):
    d = make_dossier(tmp_path / "D1")
    with pytest.raises(SealError, match="sealed, intact core"):
        add_annex(d, "reply", annex_source(tmp_path / "src"))
    seal(d)
    (d / "claim.yaml").write_text("id: other\n", encoding="utf-8")
    with pytest.raises(SealError, match="sealed, intact core"):
        add_annex(d, "reply", annex_source(tmp_path / "src"))


def test_annex_names_and_rewrites_are_refused(tmp_path):
    d = make_dossier(tmp_path / "D1")
    seal(d)
    src = annex_source(tmp_path / "src")
    for bad in ("Reply", "../x", "", "a/b", "-x"):
        with pytest.raises(SealError, match="invalid annex name"):
            add_annex(d, bad, src)
    add_annex(d, "reply", src)
    with pytest.raises(SealError, match="never rewritten"):
        add_annex(d, "reply", src)


def test_seal_refuses_annexes_before_the_seal(tmp_path):
    d = make_dossier(tmp_path / "D1")
    (d / "annexes" / "early").mkdir(parents=True)
    with pytest.raises(SealError, match="annexes before its seal"):
        seal(d)


# CLI --------------------------------------------------------------------------------------


def test_cli_seal_annex_and_check_report_core_and_annexes_separately(tmp_path):
    runner = CliRunner()
    d1 = make_dossier(tmp_path / "D1")
    d2 = make_dossier(tmp_path / "D2")
    out = runner.invoke(app, ["seal", str(d1), str(d2)])
    assert out.exit_code == 0, out.output
    expected = combined_sha256({"D1": core_sha256(d1), "D2": core_sha256(d2)})
    assert f"{expected}  combined (2 dossier(s))" in out.output
    out = runner.invoke(app, ["annex", str(d1), "reply", str(annex_source(tmp_path / "src"))])
    assert out.exit_code == 0, out.output
    out = runner.invoke(app, ["check-dossier", str(d1)])
    assert out.exit_code == 0, out.output
    assert "core: intact against its seal" in out.output
    assert "annex reply: intact against its manifest" in out.output
    (d1 / "annexes/reply/report.md").write_text("edited\n", encoding="utf-8")
    out = runner.invoke(app, ["check-dossier", str(d1)])
    assert out.exit_code == 1
    assert "core: intact against its seal" in out.output
    assert "annex reply: NOT intact" in out.output


def test_cli_seal_refuses_duplicate_names_before_sealing(tmp_path):
    runner = CliRunner()
    a = make_dossier(tmp_path / "x" / "D1")
    b = make_dossier(tmp_path / "y" / "D1")
    out = runner.invoke(app, ["seal", str(a), str(b)])
    assert out.exit_code == 1
    assert not (a / SEAL_NAME).exists() and not (b / SEAL_NAME).exists()


# Codex round 1 ------------------------------------------------------------------------------


def test_annex_line_ending_change_is_detected(tmp_path):
    d = make_dossier(tmp_path / "D1")
    seal(d)
    add_annex(d, "reply", annex_source(tmp_path / "src", "line 1\nline 2\n"))
    path = d / "annexes/reply/report.md"
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    assert check_sealed(d).annexes["reply"] == ["annex file modified: report.md"]


@pytest.mark.parametrize("bad", ["D1\n" + "b" * 64 + "  D2", "a/b", "a\b", "", "tab\there"])
def test_combined_hash_refuses_ambiguous_names(bad):
    with pytest.raises(ValueError):
        combined_sha256({"D1": "a" * 64, bad: "b" * 64})


def test_combined_hash_refuses_invalid_core_hashes():
    with pytest.raises(ValueError):
        combined_sha256({"D1": "not-a-hash"})


@pytest.mark.parametrize("bad", ["reply\n", "con", "nul", "com1", "lpt9", "aux"])
def test_annex_names_must_be_portable(tmp_path, bad):
    d = make_dossier(tmp_path / "D1")
    seal(d)
    with pytest.raises(SealError, match="invalid annex name"):
        add_annex(d, bad, annex_source(tmp_path / "src"))


@pytest.mark.parametrize("files", [["annex.json"], ["Report.md", "report.md"], ["con.txt"]])
def test_annex_file_names_must_be_portable(tmp_path, files):
    d = make_dossier(tmp_path / "D1")
    seal(d)
    src = tmp_path / "src"
    src.mkdir()
    try:
        for name in files:
            (src / name).write_text("x\n", encoding="utf-8")
    except OSError:
        pytest.skip("this file system cannot even create these names")
    if len(list(src.iterdir())) < len(files):
        pytest.skip("this file system folds the case of names")
    with pytest.raises(SealError):
        add_annex(d, "reply", src)
    assert not (d / "annexes" / "reply").exists()


@pytest.mark.parametrize("content", ["[]", '{"annex_version": 1, "name": "reply", "files": [1]}'])
def test_malformed_annex_manifest_is_reported_for_that_annex_only(tmp_path, content):
    d = make_dossier(tmp_path / "D1")
    seal(d)
    add_annex(d, "reply", annex_source(tmp_path / "src"))
    (d / "annexes/reply" / ANNEX_MANIFEST).write_text(content, encoding="utf-8")
    check = check_sealed(d)
    assert check.core_problems == []
    assert check.annexes["reply"]
    out = CliRunner().invoke(app, ["check-dossier", str(d)])
    assert "core: intact against its seal" in out.output
    assert "annex reply: NOT intact" in out.output


def _link_dir(link, target):
    """A directory link: a junction on Windows, a symbolic link elsewhere."""
    import os
    import sys

    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
    else:
        os.symlink(target, link, target_is_directory=True)


def test_annexes_as_a_link_into_the_core_is_refused(tmp_path):
    d = make_dossier(tmp_path / "D1")
    seal(d)
    _link_dir(d / "annexes", d / "outputs")
    before = core_sha256(d)
    with pytest.raises(SealError):
        add_annex(d, "reply", annex_source(tmp_path / "src"))
    assert core_sha256(d) == before
    assert not (d / "outputs" / "reply").exists()
    assert check_sealed(d).annex_problems


def test_link_inside_an_annex_does_not_mark_the_core(tmp_path):
    d = make_dossier(tmp_path / "D1")
    seal(d)
    add_annex(d, "reply", annex_source(tmp_path / "src"))
    _link_dir(d / "annexes/reply/inner", tmp_path)
    check = check_sealed(d)
    assert check.core_problems == []
    assert any("not allowed" in p for p in check.annexes["reply"])


def test_link_in_an_annex_source_is_refused(tmp_path):
    d = make_dossier(tmp_path / "D1")
    seal(d)
    src = annex_source(tmp_path / "src")
    _link_dir(src / "inner", tmp_path / "D1")
    with pytest.raises(SealError, match="not allowed"):
        add_annex(d, "reply", src)


def test_older_manifest_listing_seal_or_annex_paths_keeps_covering_them(tmp_path):
    """A manifest written before v0.3 that lists SEAL.json or annexes/ files keeps its
    meaning: those files stay covered and a change is still detected."""
    root = tmp_path / "legacy"
    w = DossierWriter(root)
    w.write_text("verdict.json", "{}\n")
    w.write_text("SEAL.json", "legacy content\n")
    w.write_text("annexes/note.txt", "legacy note\n")
    lines = [
        f"{sha256_file(root / rel)}  {rel}\n"
        for rel in ("SEAL.json", "annexes/note.txt", "verdict.json")
    ]
    (root / "MANIFEST.sha256").write_text("".join(lines), encoding="utf-8", newline="\n")
    assert verify_manifest(root) == []
    (root / "annexes/note.txt").write_text("changed\n", encoding="utf-8")
    assert verify_manifest(root) == ["modified file: annexes/note.txt"]


def test_against_checks_the_seal_of_the_original(tmp_path):
    original = make_dossier(tmp_path / "orig" / "D1")
    seal(original)
    add_annex(original, "reply", annex_source(tmp_path / "src"))
    (original / "annexes/reply/report.md").write_text("tampered\n", encoding="utf-8")
    copy = make_dossier(tmp_path / "new" / "D1")
    result = check_dossier(copy, against=original)
    assert any(p.startswith("original: annex reply:") for p in result.integrity_problems)
    assert not result.ok


# Codex round 2 ------------------------------------------------------------------------------


def test_unlistable_directory_stops_the_check(tmp_path, monkeypatch):
    import os

    d = make_dossier(tmp_path / "D1")
    seal(d)
    add_annex(d, "reply", annex_source(tmp_path / "src"))
    hidden = d / "annexes" / "reply" / "hidden"
    hidden.mkdir()
    (hidden / "extra.md").write_text("not in the manifest\n", encoding="utf-8")
    real = os.scandir

    def refusing(path="."):
        if os.fspath(path).endswith("hidden"):
            raise PermissionError(13, "Permission denied", os.fspath(path))
        return real(path)

    monkeypatch.setattr(os, "scandir", refusing)
    problems = check_sealed(d).annexes["reply"]
    assert problems and "cannot list" in problems[0]


@pytest.mark.parametrize(
    "rels",
    [
        ["a:b.md"],
        ["a\x01b.md"],
        ["dir|x/a.md"],
        ["A/x.txt", "a/y.txt"],
        ["sub/CON.md"],
        ["trailing./a.md"],
        ["Annex.json"],
    ],
)
def test_annex_path_components_must_be_portable(rels):
    from refute.core.seal import _check_annex_files

    with pytest.raises(SealError):
        _check_annex_files(rels)


def test_portable_annex_paths_are_accepted():
    from refute.core.seal import _check_annex_files

    _check_annex_files(["report.md", "data/table.csv", "data/notes.txt", "a-b/c_d.json"])


def test_legacy_dossier_is_checked_by_its_manifest_only(tmp_path):
    root = tmp_path / "legacy"
    w = DossierWriter(root)
    w.write_text("verdict.json", "{}\n")
    w.write_text("SEAL.json", "legacy content\n")
    w.write_text("annexes/note.txt", "legacy note\n")
    w.finalize()  # a manifest that lists SEAL.json and annexes/note.txt, as before v0.3
    from refute.core.dossier import read_manifest

    assert "SEAL.json" not in read_manifest(root)  # finalize() writes the v0.3 form
    lines = [
        f"{sha256_file(root / rel)}  {rel}\n"
        for rel in ("SEAL.json", "annexes/note.txt", "verdict.json")
    ]
    (root / "MANIFEST.sha256").write_text("".join(lines), encoding="utf-8", newline="\n")
    result = check_dossier(root)
    assert result.ok and result.seal is None
    out = CliRunner().invoke(app, ["check-dossier", str(root)])
    assert out.exit_code == 0 and "core:" not in out.output
    copy = tmp_path / "copy"
    w2 = DossierWriter(copy)
    w2.write_text("verdict.json", "{}\n")
    w2.finalize()
    assert not any("original" in p for p in check_dossier(copy, against=root).integrity_problems)


def test_cli_shows_problems_of_the_annexes_directory(tmp_path):
    d = make_dossier(tmp_path / "D1")
    seal(d)
    _link_dir(d / "annexes", d / "outputs")
    out = CliRunner().invoke(app, ["check-dossier", str(d)])
    assert out.exit_code == 1
    assert "core: intact against its seal" in out.output
    assert "annexes: annexes/ is a link" in out.output
