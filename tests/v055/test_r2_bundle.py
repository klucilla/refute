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
    return b


def _arguments(root, body, disclosure="the numbers: 98 against 97"):
    text = f"# A\n\n{body}\n\n## Disclosure: results known when this was written\n\n{disclosure}\n"
    (root / "docs/plans/v0.5.5-r2-arguments.md").write_text(text, "utf-8")


def test_the_bundle_is_cut_at_the_disclosure_and_hashed_first(bundle, tmp_path):
    manifest = bundle.build()
    cut = (tmp_path / "bundle/arguments.md").read_text("utf-8")
    assert "the arguments" in cut and "Disclosure" not in cut and "98" not in cut
    assert set(manifest["files"]) == {"arguments.md", "frozen-rules/src/rule.py"}
    assert (tmp_path / "bundle/MANIFEST.json").read_bytes() == (
        tmp_path / "manifest.json"
    ).read_bytes()
    assert bundle.check() == {"files": 2, "ok": True}
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


@pytest.mark.parametrize(
    "body",
    ["as d2f-A.json showed", "T2a-E read it", "the forecasts say", "14 against 13 in each"],
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
