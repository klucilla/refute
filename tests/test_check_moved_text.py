"""scripts/check_moved_text.py: a literal move loses nothing and changes nothing (#218,
the maintainer's decisions of 2026-11-26, items A1 to A3). Synthetic texts only."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "check_moved_text", ROOT / "scripts" / "check_moved_text.py"
)
cmt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cmt)

OLD = """# Title

## Rules

- First rule. It holds always.
- Second rule: it holds
  in every session.

## Records

A record line.
---
---
"""
HEAD = "# Title\n\n## Rules\n\n"
RULE_1 = "- First rule. It holds always.\n"
RULE_2 = "- Second rule: it holds\n  in every session.\n"
MOVED = "## Records\n\nA record line.\n---\n---\n"


def test_a_literal_split_passes_and_reports_additions():
    main = HEAD + RULE_1 + RULE_2 + "\nBefore X, read records.md.\n"
    for unit in ("lines", "sentences"):
        result = cmt.compare(OLD, {"main.md": main, "records.md": MOVED}, unit)
        assert result["passed"], result
        assert result["missing_count"] == 0
        assert result["added_by_file"] == {"main.md": ["Before X, read records.md."]}


def test_a_changed_word_fails_in_both_units():
    main = HEAD + RULE_1.replace("always", "often") + RULE_2
    for unit in ("lines", "sentences"):
        result = cmt.compare(OLD, {"main.md": main, "records.md": MOVED}, unit)
        assert not result["passed"]
        assert any("always" in m for m in result["missing"])


def test_a_dropped_repeat_is_missing():
    moved = "## Records\n\nA record line.\n---\n"  # one "---" of two
    result = cmt.compare(OLD, {"main.md": HEAD + RULE_1 + RULE_2, "records.md": moved}, "lines")
    assert result["missing"] == ["---"]


def test_rewrapping_passes_only_in_the_sentence_unit():
    main = HEAD + RULE_1 + "- Second rule: it holds in every session.\n"
    assert not cmt.compare(OLD, {"m": main, "r": MOVED}, "lines")["passed"]
    assert cmt.compare(OLD, {"m": main, "r": MOVED}, "sentences")["passed"]


def test_main_reads_files_and_writes_a_report(tmp_path):
    old = tmp_path / "old.md"
    old.write_text(OLD, encoding="utf-8")
    a = tmp_path / "a.md"
    a.write_text(OLD, encoding="utf-8")
    report = tmp_path / "r.json"
    code = cmt.main(["--old-file", str(old), "--new", str(a), "--report", str(report)])
    assert code == 0
    assert '"passed": true' in report.read_text(encoding="utf-8")
    b = tmp_path / "b.md"
    b.write_text("# Title\n", encoding="utf-8")
    assert cmt.main(["--old-file", str(old), "--new", str(b)]) == 1
