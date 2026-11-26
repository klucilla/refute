"""scripts/md_links.py and check_moved_text.py --normalize-links (the maintainer's decision of
2026-11-26, item M2): re-prefixing a moved link changes only its target. Synthetic texts only."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import md_links  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "check_moved_text", ROOT / "scripts" / "check_moved_text.py"
)
cmt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cmt)

OLD = (
    "See [the report](docs/reports/r.md#top) and [ROADMAP](ROADMAP.md#current-phase).\n"
    '<img src="docs/assets/a.svg" alt="x"> <a href="LICENSE">L</a>\n'
    "[web](https://example.org/x) [here](#local) [dir](calibration/v0.5/gate/)\n"
    "```\n[code](docs/not-a-link.md)\n```\n"
)


def test_targets_finds_relative_targets_only():
    found = [t for _, t in md_links.targets(OLD)]
    assert found == [
        "docs/reports/r.md#top",
        "ROADMAP.md#current-phase",
        "docs/assets/a.svg",
        "LICENSE",
        "calibration/v0.5/gate/",
    ]


def test_reprefix_round_trip_from_the_root_to_docs():
    moved = md_links.map_targets(OLD, lambda t: md_links.from_root(md_links.to_root(t, ""), "docs"))
    assert "](reports/r.md#top)" in moved
    assert "](../ROADMAP.md#current-phase)" in moved
    assert 'src="assets/a.svg"' in moved and 'href="../LICENSE"' in moved
    assert "](../calibration/v0.5/gate/)" in moved
    assert "](https://example.org/x)" in moved and "](#local)" in moved
    assert "[code](docs/not-a-link.md)" in moved  # fenced code is left alone
    assert md_links.normalize(moved, "docs") == md_links.normalize(OLD, "")


def test_start_line_leaves_the_header_alone():
    text = "[h](reports/x.md)\nMARK\n[m](docs/reports/x.md)\n"
    out = md_links.map_targets(text, lambda t: md_links.from_root(t, "docs"), start_line=2)
    assert out == "[h](reports/x.md)\nMARK\n[m](reports/x.md)\n"


def test_checker_passes_a_reprefixed_move_and_fails_a_word_change():
    moved = md_links.map_targets(OLD, lambda t: md_links.from_root(md_links.to_root(t, ""), "docs"))
    old_n = cmt.normalized(OLD, "")
    assert cmt.compare(old_n, {"d": cmt.normalized(moved, "docs")}, "lines")["passed"]
    assert not cmt.compare(OLD, {"d": moved}, "lines")["passed"]
    changed = moved.replace("the report", "a report")
    assert not cmt.compare(old_n, {"d": cmt.normalized(changed, "docs")}, "lines")["passed"]
