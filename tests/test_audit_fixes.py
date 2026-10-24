"""The four safety fixes of the external audits of 2026-10-24 (Codex and Gemini, on c83cdf7),
decided by the maintainer the same day: A1 (the TESS adapter refuses a manifest of another
target), A4 (a run directory is reserved exclusively and a dossier file is never overwritten),
A5 (an executable claim with duplicate target keys is refused before any download or dossier)
and A6 (a reviewer report is never attached to a sealed dossier). Written before the code.
Synthetic data only; no network."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest
from typer.testing import CliRunner

from conftest import replicate_claim, target_entry, write_yaml
from refute.cli import app
from refute.core.dossier import DossierWriter, verify_manifest
from refute.core.io import read_json
from refute.core.lock import create_lock
from refute.core.review import ReviewError, attach_review
from refute.core.run import execute_run
from refute.core.seal import SEAL_NAME, seal, verify_seal
from refute.packs.tess.adapter import DataError, TessAdapter, manifest_path
from refute.packs.tess.synthetic import fast_plan_dict, scenario_data, write_synthetic_cache


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


# --- A1: the manifest must be the requested target's -------------------------------------------


def _cache_with_b_at_a(tmp_path: Path) -> Path:
    """An intact manifest of TIC 2 (target B) at the path of TIC 1 (target A)."""
    cache = tmp_path / "cache"
    data = scenario_data("planet")
    write_synthetic_cache(cache, 2, data.lc, data.star, aux=data.aux)
    shutil.copyfile(manifest_path(cache, 2), manifest_path(cache, 1))
    return cache


def test_a1_the_adapter_refuses_another_targets_manifest(tmp_path):
    cache = _cache_with_b_at_a(tmp_path)
    target = target_entry(1, "planet", 3.7)
    with pytest.raises(DataError, match="TIC-2|tic_id 2"):
        TessAdapter().load(target, fast_plan_dict(), cache)


def test_a1_a_wrong_target_key_alone_is_refused(tmp_path):
    cache = tmp_path / "cache"
    data = scenario_data("planet")
    write_synthetic_cache(cache, 1, data.lc, data.star, aux=data.aux)
    manifest = read_json(manifest_path(cache, 1))
    manifest["target_key"] = "TIC-2"
    manifest_path(cache, 1).write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(DataError, match="target_key"):
        TessAdapter().load(target_entry(1, "planet", 3.7), fast_plan_dict(), cache)


def test_a1_the_matching_manifest_still_loads(tmp_path):
    cache = tmp_path / "cache"
    data = scenario_data("planet")
    write_synthetic_cache(cache, 1, data.lc, data.star, aux=data.aux)
    loaded = TessAdapter().load(target_entry(1, "planet", 3.7), fast_plan_dict(), cache)
    assert loaded.tic_id == 1 and loaded.target_key == "TIC-1"


def test_a1_a_run_on_another_targets_data_gives_no_verdict(tmp_path):
    cache = _cache_with_b_at_a(tmp_path)
    claim = write_yaml(
        tmp_path / "claims" / "claim.yaml", replicate_claim([target_entry(1, "planet", 3.7)])
    )
    create_lock(claim)
    outcome = execute_run(
        claim, mode="replicate", out_dir=tmp_path / "out", workers=1, offline=True,
        run_id="a1", cache_dir=cache,
    )  # fmt: skip
    verdict = read_json(outcome.run_dir / "TIC-1" / "verdict.json")
    assert verdict["status"] == "ERROR" and verdict["tests"] == []
    assert verdict["verdict"] == "INCONCLUSIVE"
    assert "TIC-2" in verdict["error"] or "tic_id" in verdict["error"]


# --- A4: an exclusive run directory; no file overwritten ---------------------------------------


@pytest.fixture
def planet_claim(tmp_path):
    cache = tmp_path / "cache"
    data = scenario_data("planet")
    write_synthetic_cache(cache, 1, data.lc, data.star, aux=data.aux)
    claim = write_yaml(
        tmp_path / "claims" / "claim.yaml", replicate_claim([target_entry(1, "planet", 3.7)])
    )
    create_lock(claim)
    return claim, cache


def test_a4_a_repeated_run_id_is_refused_and_the_first_run_is_intact(tmp_path, planet_claim):
    claim, cache = planet_claim
    kw = {"mode": "replicate", "out_dir": tmp_path / "out", "workers": 1, "offline": True,
          "run_id": "same", "cache_dir": cache}  # fmt: skip
    first = execute_run(claim, **kw)
    assert first.exit_code == 0, first.messages
    before = _tree_bytes(first.run_dir)
    second = execute_run(claim, **kw)
    assert second.exit_code != 0
    assert any("exists" in m for m in second.messages), second.messages
    assert _tree_bytes(first.run_dir) == before
    assert verify_manifest(first.run_dir / "TIC-1") == []


def test_a4_the_dossier_writer_never_overwrites(tmp_path):
    writer = DossierWriter(tmp_path / "D")
    writer.write_text("report.md", "first\n")
    for write in (
        lambda: writer.write_text("report.md", "second\n"),
        lambda: writer.write_json("report.md", {"x": 1}),
        lambda: writer.write_bytes("report.md", b"third"),
    ):
        with pytest.raises(FileExistsError):
            write()
    assert (tmp_path / "D" / "report.md").read_text(encoding="utf-8") == "first\n"


# --- A5: duplicate target keys -----------------------------------------------------------------


def test_a5_duplicate_target_keys_are_refused_before_any_download(tmp_path, monkeypatch):
    # The TESS schema already ties the key to the tic_id (^TIC-[0-9]+$, equal to TIC-<tic_id>),
    # so the only duplicate that reaches a TESS run is the same target twice; the shared check
    # below covers case and spacing variants for every pack.
    calls = []
    monkeypatch.setattr(TessAdapter, "fetch", lambda self, *a, **k: calls.append(a))
    claim = write_yaml(
        tmp_path / "claims" / "claim.yaml",
        replicate_claim([target_entry(1, "planet", 3.7), target_entry(1, "planet", 3.7)]),
    )
    create_lock(claim)
    out = tmp_path / "out"
    outcome = execute_run(
        claim, mode="replicate", out_dir=out, workers=1, offline=False, run_id="dup",
        cache_dir=tmp_path / "cache",
    )  # fmt: skip
    assert outcome.exit_code != 0
    assert any("duplicate" in m for m in outcome.messages), outcome.messages
    assert calls == []
    assert not (out / "dup").exists()


def test_a5_fetch_refuses_duplicate_keys(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(TessAdapter, "fetch", lambda self, *a, **k: calls.append(a))
    claim = write_yaml(
        tmp_path / "claims" / "claim.yaml",
        replicate_claim([target_entry(1, "planet", 3.7), target_entry(1, "planet", 3.7)]),
    )
    result = CliRunner().invoke(app, ["fetch", str(claim), "--cache-dir", str(tmp_path / "cache")])
    assert result.exit_code != 0
    assert "duplicate" in result.output
    assert calls == []


def test_a5_the_ml_production_refuses_duplicate_keys(tmp_path):
    from refute.packs.ml import production

    claim = tmp_path / "claim.json"
    claim.write_text(
        json.dumps({"targets": [{"key": "c1"}, {"key": "C1"}], "test_plan": {}}),
        encoding="utf-8",
    )
    with pytest.raises(production.ProductionError, match="duplicate"):
        production.main(
            ["--claim", str(claim), "--paper", "p", "--root", str(tmp_path / "root"),
             "--out", str(tmp_path / "out"), "--cache", str(tmp_path / "cache")]
        )  # fmt: skip
    assert not (tmp_path / "root").exists() and not (tmp_path / "out").exists()


def test_a5_the_shared_check():
    from refute.core.pack import duplicate_target_keys

    assert duplicate_target_keys(["TIC-1", "TIC-2"]) == []
    assert duplicate_target_keys(["TIC-1", "tic-1", "TIC-2", "TIC 2"]) == ["TIC-1", "TIC-2"]


# --- the cases added after Codex's review of the fixes (round 1) -------------------------------


class _ReachedError(Exception):
    """Raised by a patched first effect: the check under test let the input through."""


def test_a1_a_wrong_tic_id_alone_is_refused(tmp_path):
    cache = tmp_path / "cache"
    data = scenario_data("planet")
    write_synthetic_cache(cache, 1, data.lc, data.star, aux=data.aux)
    manifest = read_json(manifest_path(cache, 1))
    manifest["tic_id"] = 2  # target_key stays TIC-1
    manifest_path(cache, 1).write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(DataError, match="tic_id 2"):
        TessAdapter().load(target_entry(1, "planet", 3.7), fast_plan_dict(), cache)


def test_a4_a_path_is_reserved_once(tmp_path):
    writer = DossierWriter(tmp_path / "D")
    first = writer.path("plots/full.png")  # reserved for a producer such as savefig
    with pytest.raises(FileExistsError):
        writer.path("plots/full.png")
    with pytest.raises(FileExistsError):
        writer.write_bytes("plots/full.png", b"other")
    first.write_bytes(b"the plot")
    assert first.read_bytes() == b"the plot"


def test_a4_a_run_that_loses_the_directory_is_refused(tmp_path, planet_claim, monkeypatch):
    import refute.core.run as run_module

    claim, cache = planet_claim
    other = tmp_path / "out" / "race"

    def another_run_wins(pack, loaded, cache_dir, offline):
        other.mkdir(parents=True)
        (other / "theirs.txt").write_bytes(b"the other run\n")
        return []

    monkeypatch.setattr(run_module, "prepare_claim_data", another_run_wins)
    outcome = execute_run(
        claim, mode="replicate", out_dir=tmp_path / "out", workers=1, offline=True,
        run_id="race", cache_dir=cache,
    )  # fmt: skip
    assert outcome.exit_code != 0 and any("exists" in m for m in outcome.messages)
    assert _tree_bytes(other) == {"theirs.txt": b"the other run\n"}


def _ml_claim(tmp_path: Path, keys: list[str]) -> Path:
    claim = tmp_path / "claim.json"
    claim.write_text(
        json.dumps({"targets": [{"key": k} for k in keys], "test_plan": {}}), encoding="utf-8"
    )
    return claim


def test_a5_the_ml_main_checks_before_any_effect_and_lets_a_valid_claim_through(
    tmp_path, monkeypatch
):
    from refute.packs.ml import production

    def first_effect():
        raise _ReachedError

    monkeypatch.setattr(production, "refute_checkout", first_effect)
    argv = ["--paper", "p", "--root", str(tmp_path / "root"), "--out", str(tmp_path / "out"),
            "--cache", str(tmp_path / "cache")]  # fmt: skip
    with pytest.raises(production.ProductionError, match="duplicate"):
        production.main(["--claim", str(_ml_claim(tmp_path, ["c1", "C1"])), *argv])
    with pytest.raises(_ReachedError):  # the control: no duplicate, the run goes on
        production.main(["--claim", str(_ml_claim(tmp_path, ["c1", "c2"])), *argv])


def test_a5_the_ml_entries_refuse_duplicates_before_any_effect(tmp_path, monkeypatch):
    from refute.packs.ml import integration, production

    def first_effect(*args, **kwargs):
        raise _ReachedError

    monkeypatch.setattr(production.repository, "clone", first_effect)
    duplicate = {"targets": [{"key": "c1"}, {"key": "C1"}], "test_plan": {}}
    with pytest.raises(production.ProductionError, match="duplicate"):
        production.prepare_inputs(duplicate, tmp_path / "root", tmp_path / "cache")
    with pytest.raises(production.ProductionError, match="duplicate"):
        production.build_harness(None, duplicate)
    with pytest.raises(production.ProductionError, match="duplicate"):
        production.run_production(None, duplicate, tmp_path / "out", {})
    with pytest.raises(ValueError, match="duplicate"):
        integration.PaperIntegration(duplicate, None)
    valid = {"targets": [{"key": "c1"}], "test_plan": {"repository": {"url": "u", "commit": "c"}}}
    with pytest.raises(_ReachedError):  # the control
        production.prepare_inputs(valid, tmp_path / "root", tmp_path / "cache")
    assert not (tmp_path / "root").exists() and not (tmp_path / "out").exists()


def test_a6_a_legacy_dossier_is_not_sealed_and_still_takes_a_review(tmp_path):
    from refute.core.dossier import read_manifest
    from refute.core.hashing import sha256_file

    root = tmp_path / "legacy"
    w = DossierWriter(root)
    w.write_text("verdict.json", "{}\n")
    w.write_text("SEAL.json", "legacy content\n")
    w.write_text("annexes/note.txt", "legacy note\n")
    w.finalize()
    lines = [
        f"{sha256_file(root / rel)}  {rel}\n"
        for rel in ("SEAL.json", "annexes/note.txt", "verdict.json")
    ]  # the manifest of a dossier written before v0.3, which lists those names
    (root / "MANIFEST.sha256").write_text("".join(lines), encoding="utf-8", newline="\n")
    assert "SEAL.json" in read_manifest(root)
    report = tmp_path / "review.md"
    report.write_text("No objection.\n", encoding="utf-8")
    entry = attach_review(root, report, reviewer="opus-1", model="m")
    assert entry["file"] == "review/opus-1.md"
    # the legacy names stay covered: the dossier stays intact and legacy (Codex, round 2)
    from refute.core.dossier import check_dossier

    after = read_manifest(root)
    assert {"SEAL.json", "annexes/note.txt", "review/opus-1.md"} <= set(after)
    assert verify_manifest(root) == []
    result = check_dossier(root)
    assert result.ok and result.seal is None


def test_a6_a_modern_seal_listed_in_the_manifest_is_still_a_seal(tmp_path):
    from refute.core.hashing import sha256_file

    root = _sealed(tmp_path)
    with (root / "MANIFEST.sha256").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(f"{sha256_file(root / SEAL_NAME)}  {SEAL_NAME}\n")
    before = _tree_bytes(root)
    report = tmp_path / "review.md"
    report.write_text("No objection.\n", encoding="utf-8")
    with pytest.raises(ReviewError, match="sealed"):
        attach_review(root, report, reviewer="opus-1", model="m")
    assert _tree_bytes(root) == before and not (root / "review").exists()


def test_a6_an_annex_without_a_seal_is_refused_too(tmp_path):
    root = tmp_path / "D"
    w = DossierWriter(root)
    w.write_json("verdict.json", {"verdict": "REPRODUCED"})
    w.finalize()
    (root / "annexes" / "x").mkdir(parents=True)
    (root / "annexes" / "x" / "a.md").write_text("a\n", encoding="utf-8")
    report = tmp_path / "review.md"
    report.write_text("No objection.\n", encoding="utf-8")
    with pytest.raises(ReviewError, match="sealed"):
        attach_review(root, report, reviewer="opus-1", model="m")


# --- A6: no review attached to a sealed dossier ------------------------------------------------


def _sealed(tmp_path: Path) -> Path:
    root = tmp_path / "D"
    w = DossierWriter(root)
    w.write_text("claim.yaml", "id: c1\nkind: replicate\n")
    w.write_json("verdict.json", {"verdict": "REPRODUCED", "tests": []})
    w.write_text("report.md", "# report\n")
    w.finalize()
    seal(root)
    return root


def test_a6_attach_refuses_a_sealed_dossier(tmp_path):
    root = _sealed(tmp_path)
    before = _tree_bytes(root)
    report = tmp_path / "review.md"
    report.write_text("No objection.\n", encoding="utf-8")
    with pytest.raises(ReviewError, match="sealed"):
        attach_review(root, report, reviewer="opus-1", model="m")
    assert _tree_bytes(root) == before
    assert verify_seal(root) == []
    assert not (root / "review").exists()


def test_a6_the_cli_refuses_too(tmp_path):
    root = _sealed(tmp_path)
    before = _tree_bytes(root)
    report = tmp_path / "review.md"
    report.write_text("No objection.\n", encoding="utf-8")
    result = CliRunner().invoke(
        app, ["review", "attach", str(root), str(report), "--reviewer", "opus-1", "--model", "m"]
    )
    assert result.exit_code == 1 and "sealed" in result.output
    assert _tree_bytes(root) == before and (root / SEAL_NAME).is_file()
