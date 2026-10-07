"""Claim specification (``claim.yaml``): schema, loading and resolution.

The core schema is domain-agnostic. The domain pack named in ``pack`` validates
its own sections (``test_plan``, ``targets``, ``pass_criteria``) and fills in
every default, so the *resolved* claim contains every threshold explicitly.
The lock hashes the resolved claim: changing a code default later cannot
silently change a locked claim, because the locked value is written out.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

from refute.core.canonical import canonical_sha256

if TYPE_CHECKING:
    from refute.core.pack import DomainPack

SCHEMA_VERSION = 1


class ClaimError(Exception):
    """The claim file is unreadable or does not match the schema."""


class StrictModel(BaseModel):
    """Base model that rejects unknown fields, so typos are errors, not silent defaults."""

    model_config = ConfigDict(extra="forbid")


class DataSource(StrictModel):
    name: str
    url: str
    retrieved: str = Field(description="UTC date or timestamp of retrieval (ISO 8601)")
    notes: str | None = None


class Attachment(StrictModel):
    """An external file covered by the lock. ``path`` is relative to the claim's directory."""

    path: str
    role: str | None = None
    sha256: str | None = Field(
        default=None, description="Optional expected hash; the lock records the actual hash."
    )

    @field_validator("path")
    @classmethod
    def _relative_posix(cls, value: str) -> str:
        if "\\" in value:
            raise ValueError("attachment paths must use '/' separators")
        posix = PurePosixPath(value)
        if posix.is_absolute() or ":" in value:
            raise ValueError("attachment paths must be relative to the claim's directory")
        if any(part == ".." for part in posix.parts):
            raise ValueError("attachment paths must not contain '..'")
        return posix.as_posix()


class Claim(StrictModel):
    schema_version: Literal[1] = SCHEMA_VERSION
    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
    kind: Literal["replicate", "calibration"]
    pack: str
    title: str
    hypothesis: str
    created: dt.date
    authors: list[str] = Field(min_length=1)
    definitions: dict[str, str] = Field(default_factory=dict)
    data_sources: list[DataSource] = Field(default_factory=list)
    attachments: list[Attachment] = Field(default_factory=list)
    targets: list[dict[str, Any]] = Field(default_factory=list)
    test_plan: dict[str, Any] = Field(default_factory=dict)
    pass_criteria: dict[str, Any] | None = None


def format_validation_error(error: ValidationError, prefix: str = "") -> str:
    lines = []
    for item in error.errors():
        location = ".".join(str(part) for part in item["loc"])
        if prefix:
            location = f"{prefix}.{location}" if location else prefix
        lines.append(f"{location or '<root>'}: {item['msg']}")
    return "; ".join(lines)


@dataclass
class LoadedClaim:
    """A claim file after validation and resolution by its domain pack."""

    path: Path
    raw: dict[str, Any]
    claim: Claim
    pack: DomainPack

    @property
    def directory(self) -> Path:
        return self.path.parent

    def canonical(self) -> dict[str, Any]:
        """The resolved claim as plain JSON values (what the lock hashes)."""
        return self.claim.model_dump(mode="json")

    def sha256(self) -> str:
        return canonical_sha256(self.canonical())

    def attachment_path(self, attachment: Attachment) -> Path:
        return self.directory / Path(*PurePosixPath(attachment.path).parts)

    def attachment_by_role(self, role: str) -> Attachment | None:
        matches = [a for a in self.claim.attachments if a.role == role]
        if len(matches) > 1:
            raise ClaimError(f"more than one attachment with role '{role}'")
        return matches[0] if matches else None


def read_claim_file(path: Path | str) -> dict[str, Any]:
    claim_path = Path(path)
    if not claim_path.is_file():
        raise ClaimError(f"claim file not found: {claim_path}")
    try:
        data = yaml.safe_load(claim_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ClaimError(f"cannot read claim file {claim_path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ClaimError(f"claim file {claim_path} must contain a YAML mapping")
    return data


def load_claim(path: Path | str, pack: DomainPack | None = None) -> LoadedClaim:
    """Read, validate and resolve a claim. Raises :class:`ClaimError` on any problem."""
    from refute.core.pack import PackError, load_pack

    claim_path = Path(path).resolve()
    raw = read_claim_file(claim_path)
    try:
        base = Claim.model_validate(raw)
    except ValidationError as exc:
        raise ClaimError(f"invalid claim: {format_validation_error(exc)}") from exc

    if pack is None:
        try:
            pack = load_pack(base.pack)
        except PackError as exc:
            raise ClaimError(str(exc)) from exc
    elif pack.name != base.pack:
        raise ClaimError(f"claim names pack '{base.pack}' but pack '{pack.name}' was given")

    if base.kind == "calibration" and base.pass_criteria is None:
        raise ClaimError("calibration claims must define pass_criteria")

    try:
        resolved = base.model_copy(
            update={
                "test_plan": pack.schema.resolve_test_plan(base.test_plan),
                "targets": pack.schema.resolve_targets(base.targets),
                "pass_criteria": pack.schema.resolve_pass_criteria(base.pass_criteria, base.kind),
            }
        )
    except ValidationError as exc:
        raise ClaimError(f"invalid claim: {format_validation_error(exc)}") from exc
    except ValueError as exc:
        raise ClaimError(f"invalid claim: {exc}") from exc

    loaded = LoadedClaim(path=claim_path, raw=raw, claim=resolved, pack=pack)
    try:
        pack.schema.validate_claim(loaded)
    except ValidationError as exc:
        raise ClaimError(f"invalid claim: {format_validation_error(exc)}") from exc
    except ValueError as exc:
        raise ClaimError(f"invalid claim: {exc}") from exc
    return loaded
