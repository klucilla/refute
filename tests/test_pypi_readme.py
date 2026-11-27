"""README-pypi.md, the README shown on the package index, is what scripts/make_pypi_readme.py
writes from README.md (the maintainer's decisions D5 and F2, #218). No network."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import md_links  # noqa: E402


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module  # dataclasses need the module registered (as test_ci_plan.py)
    spec.loader.exec_module(module)
    return module


make_pypi_readme = load("make_pypi_readme")
ci_plan = load("ci_plan")


def test_the_index_readme_is_up_to_date():
    written = (ROOT / "README-pypi.md").read_text(encoding="utf-8")
    assert written == make_pypi_readme.render(), "run scripts/make_pypi_readme.py"


def test_the_index_readme_has_no_relative_target():
    assert md_links.targets((ROOT / "README-pypi.md").read_text(encoding="utf-8")) == []


def test_targets_become_absolute_on_github():
    assert make_pypi_readme.absolute("ROADMAP.md") == make_pypi_readme.BLOB + "ROADMAP.md"
    assert make_pypi_readme.absolute("docs/") == make_pypi_readme.TREE + "docs"
    assert make_pypi_readme.absolute("docs/assets/x.svg") == (
        make_pypi_readme.RAW + "docs/assets/x.svg"
    )
    assert make_pypi_readme.absolute("LICENSE#l1") == make_pypi_readme.BLOB + "LICENSE#l1"


def test_a_readme_change_runs_the_tests():
    # README.md is not documentation-only for the CI plan, so a change to it runs this test
    assert not ci_plan.docs_only(["README.md"])
    assert ci_plan.touches_full(["pyproject.toml"])
