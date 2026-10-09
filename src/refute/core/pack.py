"""Domain pack interface and discovery through Python entry points.

The engine knows nothing about any science. A domain pack provides five pieces
(data adapter, search, gauntlet, holdout strategy, exporter), a claim schema for
its sections of ``claim.yaml``, an analyzer that wires the pieces together for one
target, and a calibrator that evaluates calibration claims.

Packs are discovered through the ``refute.packs`` entry-point group, so they can
live in other repositories::

    [project.entry-points."refute.packs"]
    tess = "refute.packs.tess:PACK"
"""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import entry_points
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from refute.core.claim import LoadedClaim
    from refute.core.dossier import DossierWriter
    from refute.core.verdict import TestResult

ENTRY_POINT_GROUP = "refute.packs"


class PackError(Exception):
    """A pack cannot be found or is invalid."""


@runtime_checkable
class DataAdapter(Protocol):
    """Fetches and loads data. Optionally it may also define

    ``prepare_claim_data(loaded, cache_dir, offline) -> list[str]``: claim-level data
    every target needs (for example a reference catalog that may not be
    redistributed). The engine calls it once, before any analysis; it must download
    what is missing (unless offline), verify recorded hashes and raise on any
    problem, which stops the run.
    """

    def fetch(self, target: dict[str, Any], test_plan: dict[str, Any], cache_dir: Path) -> dict:
        """Download and cache the target's public data (network). Returns a fetch record."""

    def load(self, target: dict[str, Any], test_plan: dict[str, Any], cache_dir: Path) -> Any:
        """Load cached data (offline), verifying recorded hashes."""


@runtime_checkable
class Search(Protocol):
    def run(self, data: Any, params: dict[str, Any]) -> Any:
        """Find the best candidate signal in the data."""


@runtime_checkable
class Gauntlet(Protocol):
    def run(
        self, data: Any, candidate: Any, target: dict[str, Any], params: dict[str, Any]
    ) -> list[TestResult]:
        """Run the falsification tests against a candidate."""


@runtime_checkable
class HoldoutStrategy(Protocol):
    def run(self, data: Any, params: dict[str, Any]) -> Any:
        """Blind holdout. Receives raw data only: never the candidate found on all data."""


@runtime_checkable
class Exporter(Protocol):
    def export(self, result: dict[str, Any], out_dir: Path) -> list[Path]:
        """Write submission-oriented files for a human. Must never submit anything."""


@runtime_checkable
class ClaimSchema(Protocol):
    def resolve_test_plan(self, raw: dict[str, Any]) -> dict[str, Any]: ...

    def resolve_targets(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]: ...

    def resolve_pass_criteria(
        self, raw: dict[str, Any] | None, kind: str
    ) -> dict[str, Any] | None: ...

    def validate_claim(self, loaded: LoadedClaim) -> None: ...

    def targets_for_run(self, loaded: LoadedClaim) -> list[dict[str, Any]]:
        """Targets a run analyzes (for calibration: from the targets attachment)."""

    def target_key(self, target: dict[str, Any]) -> str:
        """Filesystem-safe identifier, used as the dossier directory name."""


@runtime_checkable
class Analyzer(Protocol):
    def analyze(
        self,
        target: dict[str, Any],
        data: Any,
        test_plan: dict[str, Any],
        context: dict[str, Any],
        writer: DossierWriter,
    ) -> dict[str, Any]:
        """Search, gauntlet and holdout for one target. Writes plots; returns the result."""

    def error_result(
        self, target: dict[str, Any], error: str, context: dict[str, Any]
    ) -> dict[str, Any]:
        """Result for a target whose analysis raised an exception."""

    def report(self, result: dict[str, Any], context: dict[str, Any]) -> str:
        """Markdown report for one dossier."""


@runtime_checkable
class Calibrator(Protocol):
    def evaluate(
        self, loaded: LoadedClaim, results: list[dict[str, Any]], complete: bool
    ) -> dict[str, Any]:
        """Evaluate a calibration claim from per-target results."""

    def summary_markdown(self, summary: dict[str, Any]) -> str: ...


@dataclass(frozen=True)
class DomainPack:
    name: str
    version: str
    description: str
    schema: ClaimSchema
    adapter: DataAdapter
    search: Search
    gauntlet: Gauntlet
    holdout: HoldoutStrategy
    exporter: Exporter
    analyzer: Analyzer
    calibrator: Calibrator


def available_packs() -> dict[str, str]:
    """Map of pack name to entry-point target, without importing the packs."""
    return {ep.name: ep.value for ep in entry_points(group=ENTRY_POINT_GROUP)}


def load_pack(name: str) -> DomainPack:
    matches = [ep for ep in entry_points(group=ENTRY_POINT_GROUP) if ep.name == name]
    if not matches:
        known = ", ".join(sorted(available_packs())) or "none"
        raise PackError(f"unknown domain pack '{name}' (installed packs: {known})")
    try:
        pack = matches[0].load()
    except Exception as exc:  # pragma: no cover - depends on third-party packs
        raise PackError(f"cannot load domain pack '{name}': {exc}") from exc
    if not isinstance(pack, DomainPack):
        raise PackError(f"entry point '{name}' does not provide a DomainPack")
    if pack.name != name:
        raise PackError(f"entry point '{name}' provides a pack named '{pack.name}'")
    return pack
