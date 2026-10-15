"""Seal of the experimental core and annexes (docs/validation/v0.3/wp2-acceptance.md,
W2.11-W2.12). Synthetic dossiers in tmp_path, offline."""

import io
import json
import zipfile

import pytest
from typer.testing import CliRunner

from refute.cli import app
from refute.core.dossier import DossierWriter, check_dossier, verify_manifest
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


def test_text_line_endings_do_not_change_the_core_hash(tmp_path):
    lf = make_dossier(tmp_path / "LF")
    crlf = tmp_path / "CRLF"
    w = DossierWriter(crlf)
    for rel in ("claim.yaml", "logs/run.log"):
        w.write_bytes(rel, (lf / rel).read_bytes().replace(b"\n", b"\r\n"))
    w.write_bytes("verdict.json", (lf / "verdict.json").read_bytes())
    w.write_bytes("outputs/predictions.bin", BINARY)
    w.write_bytes("MANIFEST.sha256", (lf / "MANIFEST.sha256").read_bytes().replace(b"\n", b"\r\n"))
    assert core_sha256(lf) == core_sha256(crlf)


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
