"""The test harness side of the synthetic catalog (src/refute/packs/ml/synthetic.py): the
sources of each cataloged fixture's code files, and a helper that writes a fixture into a
new folder. The tests build every subprocess backend with these authorizations only."""

from __future__ import annotations

from pathlib import Path

from refute.packs.ml import synthetic

FIXTURES = Path(__file__).parent / "fixtures"
HOOK = Path(__file__).parent.parent / "src" / "refute" / "packs" / "ml" / "coverage_hook.py"
READER = Path(__file__).parent.parent / "src" / "refute" / "packs" / "ml" / "container_reader.py"
SOURCES = {
    "sandbox-probe": {"probe.py": FIXTURES / "sandbox" / "probe.py"},
    "ml-paper": {"train.py": FIXTURES / "ml_papers" / "trainer.py", "coverage_hook.py": HOOK},
    "ladder-build": {"build.py": FIXTURES / "ladder" / "build.py"},
    "data-reader": {"reader.py": READER},
}


def fixture(name: str, root: Path, data: dict[str, bytes] | None = None) -> synthetic.Authorization:
    """Writes the cataloged fixture ``name`` into ``root`` with its code files read from
    tests/fixtures and the given data files."""
    code = {path: source.read_bytes() for path, source in SOURCES[name].items()}
    return synthetic.materialize(name, root, code, data)
