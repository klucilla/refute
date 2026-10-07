from typer.testing import CliRunner

import refute
from conftest import replicate_claim, target_entry, write_yaml
from refute.cli import app
from refute.core.dossier import write_manifest

runner = CliRunner()


def test_version_and_packs():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert refute.__version__ in result.output
    result = runner.invoke(app, ["packs"])
    assert result.exit_code == 0
    assert "tess" in result.output


def test_lock_and_verify_exit_codes(tmp_path):
    claim = write_yaml(tmp_path / "claim.yaml", replicate_claim([target_entry(1, "planet", 3.7)]))
    assert runner.invoke(app, ["verify", str(claim)]).exit_code == 1
    result = runner.invoke(app, ["lock", str(claim)])
    assert result.exit_code == 0, result.output
    assert "claim_sha256" in result.output
    assert runner.invoke(app, ["lock", str(claim)]).exit_code == 1
    verify = runner.invoke(app, ["verify", str(claim)])
    assert verify.exit_code == 0
    assert "PASS" in verify.output
    claim.write_text(claim.read_text(encoding="utf-8").replace("3.7", "3.9"), encoding="utf-8")
    tampered = runner.invoke(app, ["verify", str(claim), "--json"])
    assert tampered.exit_code == 2
    assert '"TAMPERED"' in tampered.output
    forced = runner.invoke(app, ["lock", str(claim), "--force"])
    assert forced.exit_code == 1
    forced = runner.invoke(app, ["lock", str(claim), "--force", "--reason", "new period"])
    assert forced.exit_code == 0
    assert runner.invoke(app, ["verify", str(claim)]).exit_code == 0


def test_check_dossier_and_archive(tmp_path):
    dossier = tmp_path / "run" / "TIC-1"
    dossier.mkdir(parents=True)
    (dossier / "verdict.json").write_text('{"verdict": "SURVIVED"}\n', encoding="utf-8")
    write_manifest(dossier)
    assert runner.invoke(app, ["check-dossier", str(dossier)]).exit_code == 0
    (dossier / "verdict.json").write_text('{"verdict": "REFUTED"}\n', encoding="utf-8")
    result = runner.invoke(app, ["check-dossier", str(dossier)])
    assert result.exit_code == 1
    assert "modified file: verdict.json" in result.output
    archive = runner.invoke(app, ["archive", str(tmp_path / "run")])
    assert archive.exit_code == 0
    assert (tmp_path / "run.zip").is_file()
    assert (tmp_path / "run.zip.sha256").is_file()


def test_run_commands_refuse_unlocked_claims(tmp_path):
    claim = write_yaml(tmp_path / "claim.yaml", replicate_claim([target_entry(1, "planet", 3.7)]))
    result = runner.invoke(app, ["replicate", str(claim), "--offline", "--out", str(tmp_path)])
    assert result.exit_code == 1
    result = runner.invoke(app, ["calibrate", "--claim", str(claim), "--offline"])
    assert result.exit_code == 1
