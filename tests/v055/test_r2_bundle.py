"""v0.5.5 R2: the blind review's bundle builder (``docs/validation/v0.5.5/r2_bundle.py``; the
maintainer's decisions of 2026-11-21, 13:30, item 4). Offline, on a temporary project tree."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "docs/validation/v0.5.5/r2_bundle.py"


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    spec = importlib.util.spec_from_file_location("r2_bundle_under_test", SRC)
    b = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b)
    monkeypatch.setattr(b, "ROOT", tmp_path)
    monkeypatch.setattr(b, "OUT", tmp_path / "bundle")
    monkeypatch.setattr(b, "MANIFEST", tmp_path / "manifest.json")
    monkeypatch.setattr(b, "FROZEN_RULES", ("src/rule.py",))
    (tmp_path / "src").mkdir()
    (tmp_path / "src/rule.py").write_text("def rule():\n    return 1\n", "utf-8")
    (tmp_path / "docs/plans").mkdir(parents=True)
    _arguments(tmp_path, "the arguments")
    (tmp_path / "docs/plans/v0.5.5-r2-code-semantics.md").write_text("the semantics\n", "utf-8")
    (tmp_path / "docs/plans/v0.5.5-r2-targets.md").write_text("the targets\n", "utf-8")
    return b


def _arguments(root, body, disclosure="the numbers: 98 against 97"):
    text = f"# A\n\n{body}\n\n## Disclosure: results known when this was written\n\n{disclosure}\n"
    (root / "docs/plans/v0.5.5-r2-arguments.md").write_text(text, "utf-8")


def test_the_bundle_is_cut_at_the_disclosure_and_hashed_first(bundle, tmp_path):
    manifest = bundle.build()
    cut = (tmp_path / "bundle/arguments.md").read_text("utf-8")
    assert "the arguments" in cut and "Disclosure" not in cut and "98" not in cut
    assert set(manifest["files"]) == {
        "arguments.md",
        "code-semantics.md",
        "targets.md",
        "frozen-rules/src/rule.py",
    }
    assert (tmp_path / "bundle/MANIFEST.json").read_bytes() == (
        tmp_path / "manifest.json"
    ).read_bytes()
    assert bundle.check() == {"files": 4, "ok": True}
    with pytest.raises(SystemExit, match="built once"):
        bundle.build()


def test_a_changed_bundle_fails_its_check(bundle, tmp_path):
    bundle.build()
    (tmp_path / "bundle/arguments.md").write_text("changed", "utf-8")
    with pytest.raises(SystemExit, match="differs"):
        bundle.check()
    (tmp_path / "bundle/extra.md").write_text("x", "utf-8")
    with pytest.raises(SystemExit, match="differs"):
        bundle.check()


def test_a_nested_manifest_name_is_not_hidden_and_the_delivered_manifest_is_checked(
    bundle, tmp_path
):
    # Codex, r2args round 1: only the exact path of the delivered manifest is left out
    bundle.build()
    (tmp_path / "bundle/sub").mkdir()
    (tmp_path / "bundle/sub/MANIFEST.json").write_text("extra content", "utf-8")
    with pytest.raises(SystemExit, match="differs from its manifest"):
        bundle.check()
    (tmp_path / "bundle/sub/MANIFEST.json").unlink()
    assert bundle.check()["ok"]
    (tmp_path / "bundle/MANIFEST.json").write_text("{}", "utf-8")
    with pytest.raises(SystemExit, match="delivered manifest differs"):
        bundle.check()


def test_a_leak_in_the_semantics_refuses_the_build(bundle, tmp_path):
    (tmp_path / "docs/plans/v0.5.5-r2-code-semantics.md").write_text(
        "where Frechet was the limit", "utf-8"
    )
    with pytest.raises(SystemExit, match="would leak"):
        bundle.build()


@pytest.mark.parametrize(
    "body",
    [
        "as d2f-A.json showed",
        "T2a-E read it",
        "the forecasts say",
        "14 against 13 in each",
        "where the sub-check lacked power",
        "the objections in the record",
        "| Helps | D2 |",
        "it serves D2 and T2a",
        "which is the purpose and also the risk",
    ],
)
def test_a_leak_before_the_disclosure_refuses_the_build(bundle, tmp_path, body):
    _arguments(tmp_path, body)
    with pytest.raises(SystemExit, match="would leak"):
        bundle.build()
    assert not (tmp_path / "manifest.json").exists() and not (tmp_path / "bundle").exists()


def test_a_leak_in_a_frozen_rule_refuses_the_build(bundle, tmp_path):
    (tmp_path / "src/rule.py").write_text("# see the closing-record\n", "utf-8")
    with pytest.raises(SystemExit, match="would leak"):
        bundle.build()


def test_a_review_copy_replaces_its_text_and_is_declared(bundle, tmp_path, monkeypatch):
    # Codex, r2rev round 1: a comment stating a historical outcome is replaced in the copy only
    monkeypatch.setattr(bundle, "REVIEW_COPIES", {"src/rule.py": ("return 1", "return 2")})
    manifest = bundle.build()
    assert (tmp_path / "bundle/frozen-rules/src/rule.py").read_text("utf-8") == (
        "def rule():\n    return 2\n"
    )
    assert (tmp_path / "src/rule.py").read_text("utf-8") == "def rule():\n    return 1\n"
    src = manifest["sources"]["frozen-rules/src/rule.py"]
    assert src["replaced"] == "return 1" and src["by"] == "return 2" and "review_copy" in src
    assert bundle.check()["ok"]


def test_a_review_copy_whose_text_is_missing_is_refused(bundle, monkeypatch):
    monkeypatch.setattr(bundle, "REVIEW_COPIES", {"src/rule.py": ("absent text", "x")})
    with pytest.raises(SystemExit, match="not found once"):
        bundle.build()


def test_two_disclosure_headings_are_refused(bundle, tmp_path):
    text = "# A\n\n## Disclosure: results known when this was written\n\nx\n" * 2
    (tmp_path / "docs/plans/v0.5.5-r2-arguments.md").write_text(text, "utf-8")
    with pytest.raises(SystemExit, match="exactly one"):
        bundle.build()


def test_the_manifest_records_the_sources(bundle, tmp_path):
    manifest = bundle.build()
    src = manifest["sources"]["arguments.md"]
    assert src["from"] == "docs/plans/v0.5.5-r2-arguments.md" and src["cut_at"].startswith(
        "## Disc"
    )
    assert json.loads((tmp_path / "manifest.json").read_text("utf-8"))["files"] == manifest["files"]
