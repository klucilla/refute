"""ML pack (v0.3, WP3): reproduce and attack claims of machine-learning papers.

docs/validation/v0.3/wp3-acceptance.md is the design. Exposed to the engine through the
``refute.packs`` entry point as ``PACK`` (``ml``), so the core loads, resolves and locks an
ML claim (``refute lock``) with this pack's claim schema. A paper is run by
``refute.packs.ml.production`` on the VM (the docker backend, the ladder and the
orchestrator), never by the core's ``refute run``: the pack's other components refuse with
that reason.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from refute.core.pack import DomainPack
from refute.packs.ml.schema import MlClaimSchema

__all__ = ["PACK"]

NOT_THIS_PATH = (
    "the ML pack runs a paper with refute.packs.ml.production on the VM "
    "(scripts/vm/launch-paper.sh), not through the core's refute run"
)


class _ProductionOnly:
    """The core's search, gauntlet, holdout, adapter, exporter, analyzer and calibrator
    roles: an ML paper is run by the production module, so each refuses with the reason."""

    def fetch(self, target: dict[str, Any], test_plan: dict[str, Any], cache_dir: Path) -> dict:
        raise NotImplementedError(NOT_THIS_PATH)

    def load(self, target: dict[str, Any], test_plan: dict[str, Any], cache_dir: Path) -> Any:
        raise NotImplementedError(NOT_THIS_PATH)

    def run(self, *args: Any, **kwargs: Any) -> Any:
        raise NotImplementedError(NOT_THIS_PATH)

    def export(self, result: dict[str, Any], out_dir: Path) -> list[Path]:
        raise NotImplementedError(NOT_THIS_PATH)

    def analyze(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError(NOT_THIS_PATH)

    def error_result(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError(NOT_THIS_PATH)

    def report(self, *args: Any, **kwargs: Any) -> str:
        raise NotImplementedError(NOT_THIS_PATH)

    def evaluate(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        raise NotImplementedError(NOT_THIS_PATH)

    def summary_markdown(self, summary: dict[str, Any]) -> str:
        raise NotImplementedError(NOT_THIS_PATH)


_ONLY = _ProductionOnly()

PACK = DomainPack(
    name="ml",
    version="0.3.0.dev0",
    description=(
        "ML papers: drawn claims reproduced from the repository at the pinned commit on the "
        "VM (docker backend, build ladder, budget), then attacked; verdicts per claim"
    ),
    schema=MlClaimSchema(),
    adapter=_ONLY,
    search=_ONLY,
    gauntlet=_ONLY,
    holdout=_ONLY,
    exporter=_ONLY,
    analyzer=_ONLY,
    calibrator=_ONLY,
)
