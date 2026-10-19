"""ML pack claim schema (WP3 design, docs/validation/v0.3/wp3-acceptance.md, section 1.0).

One ``claim.yaml`` per paper, ``kind: replicate``, ``pack: ml`` (D-S1): the settings shared
by the paper are in ``test_plan``, the ML claims are the entries of ``targets`` in the
drawn order, and ``pass_criteria`` is null. The core schema is unchanged.

Resolution happens in two steps, both before the lock hashes the claim:

1. ``resolve_test_plan`` and ``resolve_targets`` validate each section on its own and
   write out every default (tolerances, coverage minimums, the build ladder, the
   budget of the profile, the converted uncertainties).
2. ``validate_claim`` checks everything that relates the sections and the attachments
   (identity, datasets and splits, the inventory and the draw, the allowed patches),
   and writes out the values that need both a target and ``test_plan``: the derived
   seed lists (1.0.4) and the holdout size and factor (1.0.10). Derived seed lists may
   be given and must then equal the derivation; the holdout size and factor are never
   given by hand.

Every model is strict: an unknown field is an error.
"""

from __future__ import annotations

import json
import math
import re
from decimal import Context, Decimal, Inexact, InvalidOperation, Rounded
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Annotated, Any, Literal

import yaml
from pydantic import (
    BaseModel,
    ConfigDict,
    Discriminator,
    Field,
    StrictInt,
    Tag,
    ValidationError,
    field_validator,
    model_serializer,
    model_validator,
)

from refute.core.canonical import canonical_bytes
from refute.core.hashing import sha256_bytes
from refute.core.paper import BASE_GATES, BASE_REPRODUCTION, METRIC_RECOMPUTE, prerequisite_names
from refute.packs.ml import readers, recompute, rules, seeds
from refute.packs.ml.extract import ExtractionError, check_pattern, parse_json_path
from refute.packs.ml.uncertainty import Uncertainty, resolve_uncertainty
from refute.selection import inventory as inv

if TYPE_CHECKING:
    from refute.core.claim import LoadedClaim

ARXIV_ID = r"^\d{4}\.\d{4,5}$"
HEX40 = r"^[0-9a-f]{40}$"
HEX64 = r"^[0-9a-f]{64}$"
UTC_TIMESTAMP = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
BUDGET_PROFILES = {"main": (384.0, 192.0, 192.0), "development": (96.0, 48.0, 48.0)}
BUILD_LADDER = ("own_environment", "requirements_compiled", "requirements_compiled_next_python")
STAGES = ("build", "data", "base_run", "metric_recompute", "attack_run")
ATTACKS = ("seeds", "data_split", "ablation", "holdout", "leakage", "trivial_baseline")
VALUE_MODES = ("two_sided", "one_sided_at_least", "one_sided_at_most")
COMPARISON_MODES = ("direction", "margin", "magnitude")
DEFAULT_REL_TOL = 0.02
DEFAULT_K_SD = 2.0
DEFAULT_ABS_FLOOR = {"percent": 0.5, "fraction": 0.005}
# the engine's single base image of the requirements_compiled rungs
# (wp3-run-resources-acceptance.md, section 3): python:3.12-slim-bookworm, glibc 2.36,
# pushed 2026-10-06 (Docker Hub API, read 2026-10-18); never a choice per paper
ENGINE_BASE_IMAGE = "python@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258"
# 1.0.11 (maintainer, 2026-10-15): the bounded rates that may use percent or fraction
BOUNDED_RATES = ("accuracy", "error_rate", "precision", "recall", "f1", "auroc")
INVENTORY_ROLE = "claim-inventory"
DRAW_ROLE = "claim-draw"
PATCH_ROLE = "allowed-patch"
# an approved errata of the frozen inventory (wp3-population-count-acceptance.md, section 2)
ERRATA_ROLE = "inventory-errata"
ERRATA_FORMAT = "refute-ml-inventory-errata-1"
ERRATA_FIELDS = ("command",)  # the closed list of fields an errata may change
# a population counted before the lock (wp3-population-count-acceptance.md, section 1)
POPULATION_SCRIPT_ROLE = "population-count"
POPULATION_RECORD_ROLE = "population-count-record"
POPULATION_RECORD_FORMAT = "refute-ml-population-count-1"
# the ladder's rungs that write a resolved lock (ladder.RUNGS[1:])
COUNTED_RUNGS = ("requirements_compiled", "requirements_compiled_next_python")
_DECIMAL_TEXT = re.compile(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$")


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


def _text(value: str, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be non-empty text")
    return value


def _relative(value: str, what: str, placeholders: tuple[str, ...] = ()) -> str:
    """A relative path with '/' separators, no '..', and no placeholder other than those
    listed."""
    _text(value, what)
    if "\\" in value or ":" in value:
        raise ValueError(f"{what} must use '/' separators and no drive")
    posix = PurePosixPath(value)
    if posix.is_absolute() or any(part == ".." for part in posix.parts):
        raise ValueError(f"{what} must be relative, without '..'")
    for name in re.findall(r"\{([^}]*)\}", value):
        if name not in placeholders:
            raise ValueError(f"{what} has an unknown placeholder {{{name}}}")
    return value


def _file_pattern(value: str, what: str) -> None:
    """At most one path component that is exactly '*' (wp3-extraction-pattern-acceptance.md,
    W3.11a); no other pattern."""
    try:
        check_pattern(value)
    except ValueError as exc:
        raise ValueError(f"{what}: {exc}") from None


def _json_path(value: str | None, what: str) -> None:
    """A json_path in the grammar the extractor reads (extract.parse_json_path): '$' then
    '.name' or '[index]' steps, naming one value (Codex review of #120)."""
    if value is None:
        return
    try:
        parse_json_path(value)
    except ExtractionError as exc:
        raise ValueError(f"{what}: {exc}") from None


def _finite(value: float | None, what: str) -> None:
    if value is not None and not math.isfinite(value):
        raise ValueError(f"{what} must be finite")


def _finite_tree(value: Any, what: str) -> None:
    """``value`` is JSON data: null, a boolean, a finite number, a text, a list, or a map
    with text keys, recursively. A non-finite float would be serialized as null, a set or
    a non-text key changed silently (#59, Codex review of the #85 items)."""
    if value is None or isinstance(value, bool | int | str):
        return
    if isinstance(value, float):
        _finite(value, what)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _finite_tree(item, f"{what}[{index}]")
    elif isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError(f"{what}: every map key must be text")
            _finite_tree(item, f"{what}.{key}")
    else:
        raise ValueError(f"{what} must be JSON data, not {type(value).__name__}")


# ---- test_plan (1.0.2) -------------------------------------------------------------------


class Paper(_Model):
    arxiv_id: str = Field(pattern=ARXIV_ID)
    version: int = Field(ge=1)
    run_seed_sha256: str = Field(pattern=HEX64)


class Budget(_Model):
    profile: Literal["main", "development"]
    paper_cpu_hours: float | None = None
    base_cpu_hours: float | None = None
    attacks_cpu_hours: float | None = None

    @model_validator(mode="after")
    def _profile(self) -> Budget:
        expected = BUDGET_PROFILES[self.profile]
        given = (self.paper_cpu_hours, self.base_cpu_hours, self.attacks_cpu_hours)
        for value, want in zip(given, expected, strict=True):
            if value is not None and value != want:
                raise ValueError(
                    f"budget {self.profile} is {expected[0]:g} / {expected[1]:g} / "
                    f"{expected[2]:g} CPU-hours; no other value is accepted"
                )
        self.paper_cpu_hours, self.base_cpu_hours, self.attacks_cpu_hours = expected
        return self


class Repository(_Model):
    url: str = Field(pattern=r"^https://\S+$")
    commit: str = Field(pattern=HEX40)
    latest_commit_at_draw: str = Field(pattern=HEX40)
    version_basis: Literal["named_in_paper", "named_in_readme", "latest_at_draw"]
    named_ref: str | None = None
    named_ref_location: str | None = None

    @model_validator(mode="after")
    def _named(self) -> Repository:
        named = (self.named_ref, self.named_ref_location)
        if self.version_basis == "latest_at_draw":
            if any(v is not None for v in named):
                raise ValueError("latest_at_draw takes no named_ref or named_ref_location")
        else:
            _text(self.named_ref or "", "repository.named_ref")
            _text(self.named_ref_location or "", "repository.named_ref_location")
        return self


class AllowedPatch(_Model):
    attachment: str
    reason: str

    @field_validator("attachment")
    @classmethod
    def _path(cls, value: str) -> str:
        return _relative(value, "allowed patch attachment")

    @field_validator("reason")
    @classmethod
    def _reason(cls, value: str) -> str:
        return _text(value, "allowed patch reason")


class Build(_Model):
    ladder: list[str] | None = None
    python_ladder: list[str] = Field(min_length=1)
    exclude_newer: str = Field(pattern=r"^\d{4}-\d{2}-\d{2}(T\d{2}:\d{2}:\d{2}Z)?$")
    base_image: str = Field(pattern=r"^[^@\s]+@sha256:[0-9a-f]{64}$")
    allowed_patches: list[AllowedPatch]

    @model_validator(mode="after")
    def _check(self) -> Build:
        if self.ladder is not None:
            raise ValueError("build.ladder is fixed and is never given (plan lines 392-399)")
        if self.base_image != ENGINE_BASE_IMAGE:
            raise ValueError(
                f"build.base_image is the engine's pinned image {ENGINE_BASE_IMAGE}, "
                "never a choice of the claim (wp3-run-resources-acceptance.md, section 3)"
            )
        self.ladder = list(BUILD_LADDER)
        versions = []
        for v in self.python_ladder:
            if not re.fullmatch(r"3\.\d{1,2}", v):
                raise ValueError(f"python_ladder holds {v!r}, not a Python version like '3.10'")
            versions.append(int(v.split(".")[1]))
        if versions != sorted(set(versions)):
            raise ValueError("python_ladder must be distinct versions in increasing order")
        names = [p.attachment for p in self.allowed_patches]
        if len(set(names)) != len(names):
            raise ValueError("an allowed patch is listed twice")
        return self


class Split(_Model):
    expected_examples: int = Field(ge=1)
    source: str

    @field_validator("source")
    @classmethod
    def _source(cls, value: str) -> str:
        _text(value, "split source")
        if readers.is_container_source(value):
            readers.container_place(value)  # an unknown reader or a bad selector is refused
        return value


class Artifact(_Model):
    name: str
    url: str = Field(pattern=r"^https://\S+$")
    reference: str
    version: str
    license: str
    retrieved_utc: str = Field(pattern=UTC_TIMESTAMP)
    sha256: str = Field(pattern=HEX64)
    size_bytes: int = Field(ge=1)
    local_copy_allowed: bool

    @field_validator("name", "reference", "version", "license")
    @classmethod
    def _texts(cls, value: str) -> str:
        return _text(value, "artifact field")


class CodeCitation(_Model):
    """A place in the paper's repository at ``source.repository_commit``: a relative file,
    an inclusive range of 1-based lines, and what that code does (for coverage: in the
    chain from the counter, or the call, to the value ``metric_extraction`` reads)."""

    file: str
    lines: list[int] = Field(min_length=2, max_length=2)
    role: str

    @model_validator(mode="after")
    def _check(self) -> CodeCitation:
        _relative(self.file, "citation file")
        first, last = self.lines
        if not 1 <= first <= last:
            raise ValueError("citation lines are [first, last], 1-based, first <= last")
        _text(self.role, "citation role")
        return self


# The origins of a dataset (docs/validation/v0.3/wp3-data-sources-acceptance.md, section 1).
DOWNLOADED, REPOSITORY_FILE, GENERATED = "downloaded", "repository_file", "generated"
# the reason the resolution writes for a claim on generated data (section 3)
GENERATED_REASON = "generated_by_repository_code"


class CountedBeforeLock(_Model):
    """The attachments of a population counted before the lock (W3.12f): the Refute script
    and its output record (wp3-population-count-acceptance.md, section 1)."""

    script: str
    record: str

    @field_validator("script", "record")
    @classmethod
    def _paths(cls, value: str) -> str:
        return _relative(value, "counted_before_lock attachment")


class DerivedSplit(_Model):
    """A population the repository's code derives from splits of the file (section 2):
    ``data_present`` counts the file's splits; this one is checked by the coverage routes
    against ``expected_examples``. When the repository's own computation decides its
    membership, it may be ``counted_before_lock`` (W3.12f); an absent one is not written."""

    expected_examples: int = Field(ge=1)
    derived_from: list[str] = Field(min_length=1)
    rule: str
    code: list[CodeCitation] = Field(min_length=1)
    counted_before_lock: CountedBeforeLock | None = None

    @model_serializer(mode="wrap")
    def _omit_absent(self, handler: Any) -> dict[str, Any]:
        out = handler(self)
        if out.get("counted_before_lock") is None:
            out.pop("counted_before_lock", None)
        return out

    @model_validator(mode="after")
    def _check(self) -> DerivedSplit:
        _text(self.rule, "derived split rule")
        if len(set(self.derived_from)) != len(self.derived_from):
            raise ValueError("derived_from names a split twice")
        return self


def _check_derived(splits: dict[str, Any], derived: dict[str, DerivedSplit] | None) -> None:
    for name, d in (derived or {}).items():
        if name in splits:
            raise ValueError(f"derived split {name} repeats a split name")
        unknown = sorted(set(d.derived_from) - set(splits))
        if unknown:
            raise ValueError(f"derived split {name} derives from undeclared splits {unknown}")


class Dataset(Artifact):
    """A dataset Refute fetches (``origin`` absent or ``downloaded``). An absent ``origin``
    and absent ``derived_splits`` are not written by the resolution, so an existing claim
    resolves to the same hash."""

    origin: Literal["downloaded"] | None = None
    splits: dict[str, Split] = Field(min_length=1)
    size_tolerance: int = Field(default=0, ge=0)
    derived_splits: dict[str, DerivedSplit] | None = None

    @model_validator(mode="after")
    def _derived(self) -> Dataset:
        _check_derived(self.splits, self.derived_splits)
        return self

    @model_serializer(mode="wrap")
    def _omit_absent(self, handler: Any) -> dict[str, Any]:
        out = handler(self)
        for key in ("origin", "derived_splits"):
            if out.get(key) is None:
                out.pop(key, None)
        return out


class RepositoryFileDataset(_Model):
    """A dataset that is a file of the repository at the pinned commit (section 1)."""

    name: str
    origin: Literal["repository_file"]
    path: str
    sha256: str = Field(pattern=HEX64)
    size_bytes: int = Field(ge=1)
    splits: dict[str, Split] = Field(min_length=1)
    size_tolerance: int = Field(default=0, ge=0)
    derived_splits: dict[str, DerivedSplit] | None = None

    @model_validator(mode="after")
    def _check(self) -> RepositoryFileDataset:
        _text(self.name, "dataset name")
        _relative(self.path, "repository_file path")
        _check_derived(self.splits, self.derived_splits)
        return self


class GeneratedSplit(_Model):
    """A population of data the repository's code generates: its size, what one example is
    (``unit``), and where the paper or the repository states the number (``source``)."""

    expected_examples: int = Field(ge=1)
    unit: str
    source: str

    @model_validator(mode="after")
    def _check(self) -> GeneratedSplit:
        _text(self.unit, "generated split unit")
        _text(self.source, "generated split source")
        return self


class GeneratedDataset(_Model):
    """Data the repository's code creates from its configuration, its seeds and the
    declared ``inputs`` only (section 1); ``data_present`` does not apply (section 3)."""

    name: str
    origin: Literal["generated"]
    generator: list[CodeCitation] = Field(min_length=1)
    configuration: str
    inputs: list[str]
    splits: dict[str, GeneratedSplit] = Field(min_length=1)

    @model_validator(mode="after")
    def _check(self) -> GeneratedDataset:
        _text(self.name, "dataset name")
        _text(self.configuration, "generated dataset configuration")
        if len(set(self.inputs)) != len(self.inputs):
            raise ValueError("generated dataset inputs name a weights entry twice")
        return self


def _origin_of(value: Any) -> str:
    if isinstance(value, dict):
        return value.get("origin") or DOWNLOADED
    return getattr(value, "origin", None) or DOWNLOADED


AnyDataset = Annotated[
    Annotated[Dataset, Tag(DOWNLOADED)]
    | Annotated[RepositoryFileDataset, Tag(REPOSITORY_FILE)]
    | Annotated[GeneratedDataset, Tag(GENERATED)],
    Discriminator(_origin_of),
]


def dataset_origin(dataset: Any) -> str:
    """The origin of a dataset entry (a model or its resolved dict)."""
    return _origin_of(dataset)


REPOSITORY_URL_PREFIX = "repository:"


def artifact_identity(dataset: dict[str, Any]) -> tuple[str, str, str, int]:
    """(name, url, sha256, size) of a resolved dataset entry Refute reads from a file: the
    fetched artifact, or a file of the repository, named ``repository:<path>``."""
    origin = dataset_origin(dataset)
    if origin == GENERATED:
        raise ValueError(f"dataset {dataset['name']} is generated: there is no file")
    url = REPOSITORY_URL_PREFIX + dataset["path"] if origin == REPOSITORY_FILE else dataset["url"]
    return dataset["name"], url, dataset["sha256"], int(dataset["size_bytes"])


def populations(dataset: Any) -> dict[str, int]:
    """Every population a claim on this dataset may name: its splits and its derived
    splits, with their expected sizes (a model or its resolved dict)."""
    if isinstance(dataset, dict):
        splits = dataset["splits"]
        derived = dataset.get("derived_splits") or {}
        out = {k: v["expected_examples"] for k, v in splits.items()}
        out.update({k: v["expected_examples"] for k, v in derived.items()})
        return out
    out = {k: v.expected_examples for k, v in dataset.splits.items()}
    out.update(
        {
            k: v.expected_examples
            for k, v in (getattr(dataset, "derived_splits", None) or {}).items()
        }
    )
    return out


class Stage(_Model):
    active_time_limit_hours: float = Field(gt=0)
    no_progress_hours: float = Field(default=2.0, gt=0)
    progress_signal: Literal["cpu_or_output"] = "cpu_or_output"
    retries: int = Field(ge=0)

    @model_validator(mode="after")
    def _limits(self) -> Stage:
        _finite(self.active_time_limit_hours, "active_time_limit_hours")
        if self.no_progress_hours > self.active_time_limit_hours:
            raise ValueError("no_progress_hours cannot exceed the stage's active limit")
        return self


class Stages(_Model):
    build: Stage
    data: Stage
    base_run: Stage
    metric_recompute: Stage
    attack_run: Stage


class AbsentArtifact(_Model):
    attempts: int = Field(ge=1)
    interval_minutes: float = Field(gt=0)

    @model_validator(mode="after")
    def _finite_interval(self) -> AbsentArtifact:
        # refused at validation, not first at canonicalization (#59, Codex review of #85)
        _finite(self.interval_minutes, "absent_artifact.interval_minutes")
        return self


class Threads(_Model):
    OMP_NUM_THREADS: int = Field(ge=1)
    MKL_NUM_THREADS: int = Field(ge=1)
    OPENBLAS_NUM_THREADS: int = Field(ge=1)
    NUMEXPR_NUM_THREADS: int = Field(ge=1)


class MlTestPlan(_Model):
    paper: Paper
    budget: Budget
    repository: Repository
    build: Build
    datasets: list[AnyDataset] = Field(min_length=1)
    weights: list[Artifact] = Field(default_factory=list)
    stages: Stages
    absent_artifact: AbsentArtifact
    threads: Threads

    @model_validator(mode="after")
    def _names(self) -> MlTestPlan:
        for what, items in (("dataset", self.datasets), ("weights", self.weights)):
            names = [i.name for i in items]
            if len(set(names)) != len(names):
                raise ValueError(f"two {what} entries share a name")
        weights = {w.name for w in self.weights}
        for d in self.datasets:
            if isinstance(d, GeneratedDataset):
                unknown = sorted(set(d.inputs) - weights)
                if unknown:
                    raise ValueError(
                        f"generated dataset {d.name} names inputs that are not weights: {unknown}"
                    )
        return self


# ---- one ML claim (1.0.3 to 1.0.7) ------------------------------------------------------------


class Source(_Model):
    arxiv_id: str = Field(pattern=ARXIV_ID)
    version: int = Field(ge=1)
    location: str
    quote: str
    retrieved_utc: str = Field(pattern=UTC_TIMESTAMP)
    repository_url: str
    repository_commit: str = Field(pattern=HEX40)

    @field_validator("location", "quote")
    @classmethod
    def _texts(cls, value: str) -> str:
        return _text(value, "source location and quote")


class Transcription(_Model):
    value: str
    location: str
    metric: str
    split: str
    command: str


class InventoryRef(_Model):
    candidate_id: str
    position: int = Field(ge=1)
    transcription: Transcription


class Metric(_Model):
    name: str
    split: str
    unit: Literal["percent", "fraction", "native"]
    higher_is_better: bool
    reported: float | None = None
    reported_uncertainty: Uncertainty | None = None
    reported_n_seeds: int | None = Field(default=None, ge=1)
    n_examples: int = Field(ge=1)


class CsvExtraction(_Model):
    column: str
    row: dict[str, str]

    @field_validator("row")
    @classmethod
    def _row(cls, value: dict[str, str]) -> dict[str, str]:
        if sorted(value) != ["column", "equals"]:
            raise ValueError("csv.row is {column, equals}")
        return value


class RegexExtraction(_Model):
    pattern: str
    group: int | str

    @field_validator("pattern")
    @classmethod
    def _compiles(cls, value: str) -> str:
        try:
            re.compile(value)
        except re.error as exc:
            raise ValueError(f"regex does not compile: {exc}") from None
        return value

    @model_validator(mode="after")
    def _group_exists(self) -> RegexExtraction:
        # a group the pattern does not have can never extract anything (Codex review of
        # #120): refused before the lock rather than found by the gate
        compiled = re.compile(self.pattern)
        if isinstance(self.group, int):
            if not 0 <= self.group <= compiled.groups:
                raise ValueError(f"regex has no group {self.group}")
        elif self.group not in compiled.groupindex:
            raise ValueError(f"regex has no group named {self.group!r}")
        return self


class TensorBoardExtraction(_Model):
    """The one scalar of ``tag`` at ``step`` (or ``"last"``, the greatest step) of a
    TensorBoard event file (W3.11b, wp3-tensorboard-acceptance.md)."""

    tag: str = Field(min_length=1)
    step: Annotated[StrictInt, Field(ge=0)] | Literal["last"]


class Extraction(_Model):
    from_: Literal["file", "log"] = Field(alias="from")
    file: str | None = None
    json_path: str | None = None
    csv: CsvExtraction | None = None
    regex: RegexExtraction | None = None
    tensorboard: TensorBoardExtraction | None = None
    unit: Literal["percent", "fraction", "native"]

    @model_validator(mode="after")
    def _check(self) -> Extraction:
        if self.from_ == "file":
            _relative(self.file or "", "metric_extraction.file", ("seed",))
            _file_pattern(self.file or "", "metric_extraction.file")
        elif self.file is not None:
            raise ValueError("metric_extraction.file is only for 'from: file'")
        if self.tensorboard is not None and self.from_ != "file":
            raise ValueError("metric_extraction.tensorboard is only for 'from: file'")
        ways = [
            w for w in (self.json_path, self.csv, self.regex, self.tensorboard) if w is not None
        ]
        if len(ways) != 1:
            raise ValueError(
                "metric_extraction takes exactly one of json_path, csv, regex, tensorboard"
            )
        _json_path(self.json_path, "metric_extraction.json_path")
        return self

    @model_serializer(mode="wrap")
    def _omit_absent(self, handler: Any) -> dict[str, Any]:
        # an absent tensorboard is not written, so an existing claim resolves to the same
        # hash (wp3-tensorboard-acceptance.md)
        out = handler(self)
        if out.get("tensorboard") is None:
            out.pop("tensorboard", None)
        return out


class Run(_Model):
    argv: list[str] = Field(min_length=1)
    workdir: str
    seed_argument: str | None
    metric_extraction: Extraction

    @field_validator("workdir")
    @classmethod
    def _workdir(cls, value: str) -> str:
        if value == ".":
            return value
        return _relative(value, "run.workdir")

    @field_validator("seed_argument")
    @classmethod
    def _seed(cls, value: str | None) -> str | None:
        if value is not None and value.count("{seed}") != 1:
            raise ValueError("seed_argument holds exactly one {seed}")
        return value


class SameRuns(_Model):
    """``reference_run`` when the reference value comes from the same runs, read by its
    own extraction (1.0.5)."""

    same: Literal[True]
    metric_extraction: Extraction


class Comparison(_Model):
    method: str
    reference: str
    orientation: Literal["method_minus_reference", "reference_minus_method"]
    reported_method: float
    reported_reference: float
    uncertainty_method: Uncertainty
    uncertainty_reference: Uncertainty
    g_pub: float | None = None
    d_pub: float | None = None
    paired_uncertainty: Uncertainty
    reference_run: SameRuns | Run

    @model_validator(mode="after")
    def _finite_values(self) -> Comparison:
        for name in ("reported_method", "reported_reference", "g_pub", "d_pub"):
            _finite(getattr(self, name), f"comparison.{name}")
        return self


class Seeds(_Model):
    base: list[int] = Field(min_length=1)
    base_cap: int = Field(ge=1)
    base_source: Literal["documented", "derived"]
    attack: list[int] | None = None
    data_split: list[int] | None = None
    holdout: list[int] | None = None

    @model_validator(mode="after")
    def _range(self) -> Seeds:
        for name in ("base", "attack", "data_split", "holdout"):
            values = getattr(self, name) or []
            if any(not 0 <= v < seeds.SEED_LIMIT for v in values):
                raise ValueError(f"seeds.{name} must lie in [0, 2**31)")
            if len(set(values)) != len(values):
                raise ValueError(f"seeds.{name} repeats a seed")
        return self


class Tolerance(_Model):
    rel_tol: float = DEFAULT_REL_TOL
    k_sd: float = DEFAULT_K_SD
    abs_floor: float | None = None
    override_reason: str | None = None


class CoverageMin(_Model):
    positive: int = Field(ge=1)
    negative: int = Field(ge=1)


class ArgvDisable(_Model):
    argv: list[str] = Field(min_length=1)


class ConfigDisable(_Model):
    config_file: str
    key: str
    value: Any

    @field_validator("config_file")
    @classmethod
    def _file(cls, value: str) -> str:
        return _relative(value, "ablation.disable.config_file")

    @field_validator("value")
    @classmethod
    def _finite_value(cls, value: Any) -> Any:
        _finite_tree(value, "ablation.disable.value")
        return value


class DataSplitParams(_Model):
    original_proportions: list[float] = Field(min_length=2)
    proportions: list[float] = Field(min_length=2)
    split_argument: str

    @model_validator(mode="after")
    def _check(self) -> DataSplitParams:
        for name in ("original_proportions", "proportions"):
            values = getattr(self, name)
            if any(not math.isfinite(v) or not 0 < v < 1 for v in values):
                raise ValueError(f"data_split.{name} must be numbers in (0, 1)")
            if abs(sum(values) - 1) > 1e-9:
                raise ValueError(f"data_split.{name} must sum to 1")
        if self.proportions != self.original_proportions:
            raise ValueError("data_split.proportions must equal original_proportions")
        _text(self.split_argument, "data_split.split_argument")
        return self


class AblationParams(_Model):
    disable: ArgvDisable | ConfigDisable
    orientation: Literal["full_minus_ablated", "ablated_minus_full"]
    mode: Literal["direction", "margin"]
    reported_full: float | None = None
    reported_ablated: float | None = None
    reported_sd_full: float | None = Field(default=None, ge=0)
    reported_sd_ablated: float | None = Field(default=None, ge=0)
    g_abl: float | None = None

    @model_validator(mode="after")
    def _margin(self) -> AblationParams:
        published = (self.reported_full, self.reported_ablated, self.g_abl)
        # the published standard deviations too (#59, Codex review of #85)
        for name in (
            "reported_full",
            "reported_ablated",
            "g_abl",
            "reported_sd_full",
            "reported_sd_ablated",
        ):
            _finite(getattr(self, name), f"ablation.{name}")
        if self.mode == "direction":
            if (
                any(v is not None for v in published)
                or self.reported_sd_full is not None
                or (self.reported_sd_ablated is not None)
            ):
                raise ValueError("ablation in direction mode takes no published values")
            return self
        if any(v is None for v in published):
            raise ValueError("ablation in margin mode needs reported_full, reported_ablated, g_abl")
        full, ablated = self.reported_full, self.reported_ablated
        oriented = full - ablated if self.orientation == "full_minus_ablated" else ablated - full
        if not math.isclose(self.g_abl, oriented, rel_tol=1e-12, abs_tol=1e-12):
            raise ValueError(
                "ablation.g_abl must be the oriented difference of the published values"
            )
        return self


class HoldoutParams(_Model):
    split_argument: str
    # written out by validate_claim (1.0.10), never given by hand
    fraction: float | None = None
    m: int | None = None
    factor: float | None = None

    @model_validator(mode="after")
    def _by_rule(self) -> HoldoutParams:
        _text(self.split_argument, "holdout.split_argument")
        if any(v is not None for v in (self.fraction, self.m, self.factor)):
            raise ValueError("the holdout fraction, size and factor follow 1.0.10; never by hand")
        return self


class LeakageParams(_Model):
    max_overlap_fraction: float = Field(ge=0, lt=1)


class TrivialBaselineParams(_Model):
    kind: Literal["majority", "random"]
    labels: list[int | str] = Field(min_length=2)
    task: Literal["single_label_classification"]

    @field_validator("labels")
    @classmethod
    def _distinct(cls, value: list[int | str]) -> list[int | str]:
        if any(isinstance(v, bool) for v in value) or len({str(v) for v in value}) != len(value):
            raise ValueError("trivial_baseline.labels must be distinct classes")
        return value


PARAMS: dict[str, type[_Model] | None] = {
    "seeds": None,
    "data_split": DataSplitParams,
    "ablation": AblationParams,
    "holdout": HoldoutParams,
    "leakage": LeakageParams,
    "trivial_baseline": TrivialBaselineParams,
}


class AttackEntry(_Model):
    name: Literal["seeds", "data_split", "ablation", "holdout", "leakage", "trivial_baseline"]
    applies: bool
    reason: str
    params: dict[str, Any] | None = None

    @model_validator(mode="after")
    def _params(self) -> AttackEntry:
        _text(self.reason, f"attack {self.name} reason")
        if not self.applies:
            if self.params is not None:
                raise ValueError(f"attack {self.name} does not apply and takes no params")
            return self
        if self.params is None:
            raise ValueError(f"attack {self.name} applies and needs params")
        model = PARAMS[self.name]
        if model is None:
            if self.params:
                raise ValueError(f"attack {self.name} takes empty params")
        else:
            self.params = model.model_validate(self.params).model_dump(mode="json")
        return self


class Predictions(_Model):
    file: str
    format: Literal["npy", "csv", "jsonl"]
    fields: dict[str, str]

    @field_validator("file")
    @classmethod
    def _file(cls, value: str) -> str:
        if any(c in value for c in "*?[]"):
            # a predictions file is a fixed path (wp3-extraction-pattern-acceptance.md)
            raise ValueError("metric_recompute.predictions.file holds no pattern")
        return _relative(value, "metric_recompute.predictions.file", ("seed", "method"))


class MetricRecompute(_Model):
    applies: bool
    reason: str
    predictions: Predictions | None = None
    convention: dict[str, Any] | None = None
    printed_rounding: Literal["nearest", "truncate", "unknown"] | None = None

    @model_validator(mode="after")
    def _check(self) -> MetricRecompute:
        _text(self.reason, "metric_recompute.reason")
        parts = (self.predictions, self.convention, self.printed_rounding)
        if not self.applies:
            if any(p is not None for p in parts):
                raise ValueError("metric_recompute does not apply and takes no other field")
            return self
        if self.predictions is None or self.convention is None:
            raise ValueError("metric_recompute applies and needs predictions and convention")
        if self.printed_rounding is None:
            self.printed_rounding = "nearest"
        conv = _convention(self.convention)
        roles = sorted(self.predictions.fields)
        want = ["y_score", "y_true"] if conv.metric == "auroc" else ["y_pred", "y_true"]
        if roles != want:
            raise ValueError(f"predictions.fields for {conv.metric} are exactly {want}")
        return self


# ---- coverage of metric_extracted (1.5a; the maintainer's design direction of 2026-10-16) ------

# The routes in the order a claim must list them: first the native evidence the run already
# produces, (c) saved predictions, (d) sufficient statistics, (a) a printed count with its
# cited link; then (b) the hook, fixed in the hashed list of allowed patches. With no route
# that closes the chain, metric_extracted is INCONCLUSIVE. (e), an observer of a specific
# evaluator, is out of v0.3; (f), a trace of the dataset reads, is complementary only.
NATIVE_ROUTES = ("saved_predictions", "sufficient_statistics", "printed_count")
COVERAGE_ROUTES = (*NATIVE_ROUTES, "hook")
# (b): the one metric function a hook may observe for each metric; nothing else in v0.3
HOOK_FUNCTIONS = {
    "accuracy": "sklearn.metrics.accuracy_score",
    "precision": "sklearn.metrics.precision_score",
    "recall": "sklearn.metrics.recall_score",
    "f1": "sklearn.metrics.f1_score",
    "auroc": "sklearn.metrics.roc_auc_score",
}
# (d): a count of correctly classified examples and the total, for these metrics only
STATISTICS_METRICS = ("accuracy", "error_rate")
# every route cites the code from its evidence to the value metric_extraction reads (link)
_ROUTE_FIELDS = {
    "saved_predictions": ("link",),
    "sufficient_statistics": ("correct", "total", "link"),
    "printed_count": ("count", "link"),
    "hook": ("patch", "function", "call_site", "link"),
}
# the routes whose evidence holds the labels, which identify the split (W3.12d)
LABEL_ROUTES = ("saved_predictions", "hook")


class CountSelector(_Model):
    """A deterministic reader of one integer count, as ``metric_extraction`` reads a value
    (W3.11): a JSON path, a CSV cell or a regular expression, on a file or the log."""

    from_: Literal["file", "log"] = Field(alias="from")
    file: str | None = None
    json_path: str | None = None
    csv: CsvExtraction | None = None
    regex: RegexExtraction | None = None

    @model_validator(mode="after")
    def _check(self) -> CountSelector:
        if self.from_ == "file":
            _relative(self.file or "", "coverage count file", ("seed",))
            _file_pattern(self.file or "", "coverage count file")
        elif self.file is not None:
            raise ValueError("a coverage count file is only for 'from: file'")
        ways = [w for w in (self.json_path, self.csv, self.regex) if w is not None]
        if len(ways) != 1:
            raise ValueError("a coverage count takes exactly one of json_path, csv, regex")
        _json_path(self.json_path, "coverage count json_path")
        return self


class SelectedEvaluation(_Model):
    """The evaluation whose value ``metric_extraction`` reads (W3.12a): the final one of the
    run, an epoch, or a checkpoint file. Every route's evidence must come from it."""

    kind: Literal["final", "epoch", "checkpoint"]
    value: int | str | None = None

    @model_validator(mode="after")
    def _check(self) -> SelectedEvaluation:
        if self.kind == "final" and self.value is not None:
            raise ValueError("selected_evaluation 'final' takes no value")
        if self.kind == "epoch" and not (isinstance(self.value, int) and self.value >= 0):
            raise ValueError("selected_evaluation 'epoch' takes a value that is an epoch number")
        if self.kind == "checkpoint":
            if not isinstance(self.value, str):
                raise ValueError("selected_evaluation 'checkpoint' takes the checkpoint's path")
            _relative(self.value, "selected_evaluation checkpoint", ("seed",))
        return self


class OtherSplit(_Model):
    name: str
    labels_sha256: str = Field(pattern=HEX64)

    @field_validator("name")
    @classmethod
    def _name(cls, value: str) -> str:
        return _text(value, "split_identity.other_splits name")


class SplitIdentity(_Model):
    """How the routes that see labels tell the claim's split from the others (W3.12d):
    the SHA-256 of the canonical JSON array of its labels in example order; every other
    split of the dataset the repository can evaluate, by name, with the same hash; and the
    cited code where the repository defines the splits it can evaluate, which justifies the
    list (empty only when that code evaluates the claim's split alone). Every split the
    claim's dataset declares in test_plan, except the claim's own, must be in the list
    (checked across sections). A
    split whose labels equal another's cannot be identified by its labels: the routes that
    see labels do not apply to it."""

    labels_sha256: str = Field(pattern=HEX64)
    other_splits: list[OtherSplit]
    splits_evidence: list[CodeCitation] = Field(min_length=1)

    @model_validator(mode="after")
    def _check(self) -> SplitIdentity:
        names = [s.name for s in self.other_splits]
        if len(set(names)) != len(names):
            raise ValueError("split_identity.other_splits names a split twice")
        if self.labels_sha256 in {s.labels_sha256 for s in self.other_splits}:
            raise ValueError(
                "the split's labels equal another split's: the routes that see labels cannot "
                "identify it"
            )
        return self


class CoverageRoute(_Model):
    route: Literal["saved_predictions", "sufficient_statistics", "printed_count", "hook"]
    count: CountSelector | None = None
    correct: CountSelector | None = None
    total: CountSelector | None = None
    link: list[CodeCitation] | None = None
    patch: str | None = None
    function: str | None = None
    call_site: CodeCitation | None = None

    @model_validator(mode="after")
    def _check(self) -> CoverageRoute:
        want = set(_ROUTE_FIELDS[self.route])
        given = {
            name
            for name in ("count", "correct", "total", "link", "patch", "function", "call_site")
            if getattr(self, name) is not None
        }
        if given != want:
            raise ValueError(
                f"coverage route {self.route} takes exactly {sorted(want)} (given {sorted(given)})"
            )
        if self.link is not None and not self.link:
            raise ValueError(f"coverage route {self.route} cites at least one place in the code")
        if self.patch is not None:
            _relative(self.patch, "coverage hook patch")
        return self


class CoverageEvidence(_Model):
    """How the coverage of ``metric_extracted`` is shown for one method, for every base seed
    (1.5a): the selected evaluation, the routes in the fixed order, the split's identity
    when a route sees labels, the rule for conflicting evidence, and complementary evidence
    that never decides."""

    selected_evaluation: SelectedEvaluation
    routes: list[CoverageRoute] = Field(min_length=1)
    split_identity: SplitIdentity | None = None
    conflict_rule: Literal["all_must_agree"] = "all_must_agree"
    complementary: list[Literal["dataset_read_trace"]] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check(self) -> CoverageEvidence:
        names = [r.route for r in self.routes]
        if len(set(names)) != len(names):
            raise ValueError("a coverage route is listed twice")
        order = [COVERAGE_ROUTES.index(n) for n in names]
        if order != sorted(order):
            raise ValueError(f"coverage routes are listed in the order {COVERAGE_ROUTES}")
        if bool(set(LABEL_ROUTES) & set(names)) != (self.split_identity is not None):
            raise ValueError(
                "split_identity is required with the saved_predictions or hook route, "
                "and absent otherwise"
            )
        if len(set(self.complementary)) != len(self.complementary):
            raise ValueError("complementary evidence is listed twice")
        return self

    def route(self, name: str) -> CoverageRoute | None:
        return next((r for r in self.routes if r.route == name), None)


def _evidence_key(route: CoverageRoute, evaluation: SelectedEvaluation) -> str:
    """What a route reads, without the text of its citations: its selectors, or the hook's
    patch, function, call site (file and lines) and selected evaluation (one call site can
    evaluate two checkpoints: two events, Codex review of #120)."""
    data = route.model_dump(mode="json", by_alias=True, exclude={"link"})
    if data.get("call_site") is not None:
        data["call_site"] = {k: data["call_site"][k] for k in ("file", "lines")}
        data["selected_evaluation"] = evaluation.model_dump(mode="json")
    return json.dumps(data, sort_keys=True)


class Coverage(_Model):
    method: CoverageEvidence
    reference: CoverageEvidence | None = None


def _convention(raw: dict[str, Any]) -> recompute.Convention:
    allowed = {"metric", "scale", "labels", "average", "pos_label", "zero_division"}
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise ValueError(f"convention: unknown fields {unknown} (W3.15 supports no other)")
    labels = raw.get("labels")
    conv = recompute.Convention(
        metric=raw.get("metric", ""),
        scale=raw.get("scale", ""),
        labels=tuple(labels) if isinstance(labels, list) else labels,
        average=raw.get("average"),
        pos_label=raw.get("pos_label"),
        zero_division=raw.get("zero_division"),
    )
    conv.validate()
    return conv


class TranscriptionApproval(_Model):
    approved_by: str
    approved_utc: str = Field(pattern=UTC_TIMESTAMP)
    approved_commit: str = Field(pattern=HEX40)
    inventory_sha256: str = Field(pattern=HEX64)


class ClaimApproval(_Model):
    approved_by: str
    approved_utc: str = Field(pattern=UTC_TIMESTAMP)
    approved_commit: str = Field(pattern=HEX40)


class Approvals(_Model):
    transcription: TranscriptionApproval
    claim: ClaimApproval


class MlTarget(_Model):
    key: str
    type: Literal["value", "comparison"]
    statement: str
    source: Source
    inventory: InventoryRef
    dataset: str
    metric: Metric
    comparison_mode: Literal[
        "two_sided", "one_sided_at_least", "one_sided_at_most", "direction", "margin", "magnitude"
    ]
    comparison: Comparison | None = None
    scope: Literal["full_training", "checkpoint_evaluation"]
    weights: str | None = None
    run: Run
    seeds: Seeds
    tolerance: Tolerance = Field(default_factory=Tolerance)
    coverage_minimum: dict[str, CoverageMin] = Field(default_factory=dict)
    attacks: list[AttackEntry]
    metric_recompute: MetricRecompute
    coverage_evidence: Coverage
    approvals: Approvals
    # written by the resolution only, for a claim on generated data (wp3-data-sources-
    # acceptance.md, section 3); absent otherwise, and then not written
    not_applicable: dict[str, str] | None = None

    @model_serializer(mode="wrap")
    def _omit_absent(self, handler: Any) -> dict[str, Any]:
        out = handler(self)
        if out.get("not_applicable") is None:
            out.pop("not_applicable", None)
        return out

    @model_validator(mode="after")
    def _check(self) -> MlTarget:
        _text(self.statement, "statement")
        self._identity()
        self._type_and_mode()
        self._units()
        self._tolerance()
        self._seeds()
        self._attacks()
        self._metric_recompute()
        self._coverage()
        return self

    @property
    def n_base(self) -> int:
        reported = self.metric.reported_n_seeds
        return 1 if reported is None else min(reported, self.seeds.base_cap)

    def attack(self, name: str) -> AttackEntry:
        return next(a for a in self.attacks if a.name == name)

    def _identity(self) -> None:
        want = f"arXiv-{self.source.arxiv_id}v{self.source.version}-C"
        if not re.fullmatch(re.escape(want) + r"[1-9]\d*", self.key):
            raise ValueError(f"key {self.key!r} must be {want}<n>, matching its source")

    def _type_and_mode(self) -> None:
        if self.type == "value":
            if self.comparison_mode not in VALUE_MODES:
                raise ValueError(f"a value claim takes comparison_mode in {VALUE_MODES}")
            if self.comparison is not None:
                raise ValueError("a value claim has no comparison block")
            if self.metric.reported is None or not math.isfinite(self.metric.reported):
                raise ValueError("a value claim needs a finite metric.reported")
            if self.metric.reported_uncertainty is None:
                raise ValueError(
                    "a value claim needs metric.reported_uncertainty (kind none allowed)"
                )
        else:
            if self.comparison_mode not in COMPARISON_MODES:
                raise ValueError(f"a comparison claim takes comparison_mode in {COMPARISON_MODES}")
            if self.comparison is None:
                raise ValueError("a comparison claim needs its comparison block")
            if self.metric.reported is not None or self.metric.reported_uncertainty is not None:
                raise ValueError("a comparison claim keeps its published values in comparison")
            c = self.comparison
            if (c.g_pub is not None) != (self.comparison_mode == "margin"):
                raise ValueError("g_pub is required in margin mode and absent otherwise")
            if (c.d_pub is not None) != (self.comparison_mode == "magnitude"):
                raise ValueError("d_pub is required in magnitude mode and absent otherwise")
        if (self.weights is not None) != (self.scope == "checkpoint_evaluation"):
            raise ValueError("weights is required for checkpoint_evaluation and absent otherwise")

    def _units(self) -> None:
        extractions = [self.run.metric_extraction]
        if self.comparison is not None:
            extractions.append(self.comparison.reference_run.metric_extraction)
        for extraction in extractions:
            unit = extraction.unit
            if (unit == "native") != (self.metric.unit == "native"):
                raise ValueError(
                    f"metric_extraction.unit {unit} cannot be converted to metric.unit "
                    f"{self.metric.unit}"
                )
        # 1.0.8 and 1.0.11: percent and fraction (with their default floors) are for the
        # closed list of bounded rates; any other metric is native
        if self.metric.name not in BOUNDED_RATES and self.metric.unit != "native":
            raise ValueError(
                f"{self.metric.name} is not a bounded rate {BOUNDED_RATES}: its unit is native"
            )

    def _tolerance(self) -> None:
        t, unit = self.tolerance, self.metric.unit
        default_floor = DEFAULT_ABS_FLOOR.get(unit)
        if t.abs_floor is None:
            if default_floor is None:
                raise ValueError("a native metric states its abs_floor, with a reason")
            t.abs_floor = default_floor
        for name in ("rel_tol", "k_sd", "abs_floor"):
            value = getattr(t, name)
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"tolerance.{name} must be finite and at least 0")
        overridden = (
            t.rel_tol != DEFAULT_REL_TOL
            or t.k_sd != DEFAULT_K_SD
            or t.abs_floor != default_floor
            or unit == "native"
        )
        if overridden and not (t.override_reason and t.override_reason.strip()):
            raise ValueError("a tolerance other than the default, or a native unit, needs a reason")

    def _seeds(self) -> None:
        n_base = self.n_base
        if len(self.seeds.base) != n_base:
            raise ValueError(
                f"seeds.base must hold n_base = {n_base} seeds (reported_n_seeds capped by "
                "base_cap, 1 when not reported)"
            )
        if self.run.seed_argument is None:
            if n_base != 1:
                raise ValueError("with no seed argument, n_base must be 1")
            if self.attack("seeds").applies if self._has_attacks() else False:
                raise ValueError("with no seed argument, the seeds attack does not apply")
        reference = self.comparison.reference_run if self.comparison is not None else None
        if isinstance(reference, Run) and (reference.seed_argument is None) != (
            self.run.seed_argument is None
        ):
            # 1.0.5: both methods run with the same seeds (Codex review)
            raise ValueError(
                "a separate reference run takes a seed argument exactly when the method's "
                "run does, so both run with the same seeds"
            )
        base = set(self.seeds.base)
        for name in ("attack", "data_split", "holdout"):
            if base & set(getattr(self.seeds, name) or []):
                raise ValueError(f"seeds.{name} overlaps the base seeds")

    def _has_attacks(self) -> bool:
        return sorted(a.name for a in self.attacks) == sorted(ATTACKS)

    def _attacks(self) -> None:
        names = [a.name for a in self.attacks]
        if sorted(names) != sorted(ATTACKS):
            raise ValueError(f"attacks lists each of {ATTACKS} exactly once")
        if self.run.seed_argument is None and self.attack("seeds").applies:
            raise ValueError("with no seed argument, the seeds attack does not apply")
        holdout = self.attack("holdout")
        if holdout.applies:
            if self.metric.name not in rules.HOLDOUT_METRICS:
                raise ValueError(f"holdout applies only to {rules.HOLDOUT_METRICS} (1.0.10)")
            if self.comparison_mode == "direction":
                raise ValueError("holdout does not apply to a direction claim (1.0.10)")
        baseline = self.attack("trivial_baseline")
        if baseline.applies and self.metric.name not in rules.BASELINE_METRICS:
            raise ValueError(f"trivial_baseline applies only to {rules.BASELINE_METRICS}")
        # the baseline is computed in percent or fraction (attacks.trivial_baseline_value):
        # a claim in another unit could pass the schema with an attack that cannot run
        # (issue #59; the maintainer's approval of 2026-10-17)
        if baseline.applies and self.metric.unit not in ("percent", "fraction"):
            raise ValueError("trivial_baseline needs a claim in percent or fraction")

    def _metric_recompute(self) -> None:
        mr = self.metric_recompute
        if not mr.applies:
            return
        conv = _convention(mr.convention or {})
        if conv.metric != self.metric.name:
            raise ValueError("metric_recompute.convention.metric must be the claim's metric")
        if conv.scale != self.metric.unit:
            raise ValueError("metric_recompute.convention.scale must equal metric.unit")
        file = mr.predictions.file if mr.predictions else ""
        if self.n_base > 1 and "{seed}" not in file:
            raise ValueError("with several base runs the predictions file names {seed}")
        if self.type == "comparison" and "{method}" not in file:
            raise ValueError(
                "a comparison recomputes the predictions of both methods: the file names "
                "{method}; otherwise metric_recompute does not apply"
            )

    def _coverage(self) -> None:
        """1.5a: each method has its own coverage evidence, for every base seed."""
        cov = self.coverage_evidence
        if (cov.reference is not None) != (self.type == "comparison"):
            raise ValueError(
                "coverage_evidence.reference is required for a comparison claim and absent "
                "otherwise (each method has its own evidence)"
            )
        for side, evidence in (("method", cov.method), ("reference", cov.reference)):
            if evidence is None:
                continue
            where = f"coverage_evidence.{side}"
            if evidence.route("saved_predictions") and not self.metric_recompute.applies:
                raise ValueError(
                    f"{where}: the saved_predictions route reads the predictions of "
                    "metric_recompute, which must apply"
                )
            if (
                evidence.route("sufficient_statistics")
                and self.metric.name not in STATISTICS_METRICS
            ):
                raise ValueError(
                    f"{where}: sufficient_statistics applies only to {STATISTICS_METRICS}"
                )
            hook = evidence.route("hook")
            if hook is not None and hook.function != HOOK_FUNCTIONS.get(self.metric.name):
                raise ValueError(
                    f"{where}: the hook observes {HOOK_FUNCTIONS.get(self.metric.name)} for "
                    f"{self.metric.name}, no other function"
                )
            counts = [
                c
                for r in evidence.routes
                for c in (r.count, r.correct, r.total)
                if c is not None and c.from_ == "file"
            ]
            if self.n_base > 1 and any("{seed}" not in (c.file or "") for c in counts):
                raise ValueError(f"{where}: with several base runs a count file names {{seed}}")
        # each method has its own evidence (W3.12a). When the reference value comes from the
        # same runs, a route declared alike for both (same selectors, or the same hook call)
        # would read one piece of evidence twice. This is a necessary check only: two
        # different selectors can still read the same token, which the gate checks on the
        # resolved file, token or event. Separate runs may use the same selector on their
        # own logs and files.
        if cov.reference is not None and isinstance(self.comparison.reference_run, SameRuns):
            keys = {
                _evidence_key(r, cov.method.selected_evaluation)
                for r in cov.method.routes
                if r.route != "saved_predictions"
            }
            if keys & {
                _evidence_key(r, cov.reference.selected_evaluation)
                for r in cov.reference.routes
                if r.route != "saved_predictions"
            }:
                raise ValueError(
                    "coverage_evidence.method and .reference read the same evidence of the same "
                    "runs; each method has its own"
                )

    def coverage_names(self) -> list[str]:
        """The names WP2 accepts for this claim (1.0.7), in a fixed order."""
        names = [*BASE_GATES, BASE_REPRODUCTION]
        if self.metric_recompute.applies:
            names.append(METRIC_RECOMPUTE)
        for a in self.attacks:
            if a.applies:
                names.extend([a.name, *prerequisite_names(a.name)])
        return names

    def coverage_defaults(self) -> dict[str, dict[str, int]]:
        out = {}
        for name in self.coverage_names():
            if name == BASE_REPRODUCTION:
                out[name] = {"positive": self.n_base, "negative": self.n_base}
            elif name == METRIC_RECOMPUTE:
                runs = self.n_base * (2 if self.type == "comparison" else 1)
                out[name] = {"positive": runs, "negative": 1}
            else:
                out[name] = {"positive": 1, "negative": 1}
        return out

    def resolved(self) -> dict[str, Any]:
        """The claim with every default written out (step 1 of the module docstring)."""
        if self.not_applicable is not None:
            raise ValueError(
                "not_applicable is written by the resolution for generated data, never by hand"
            )
        names = self.coverage_names()
        unknown = sorted(set(self.coverage_minimum) - set(names))
        if unknown:
            raise ValueError(f"coverage_minimum names checks WP2 refuses for this claim: {unknown}")
        coverage = self.coverage_defaults()
        for name, given in self.coverage_minimum.items():
            value = given.model_dump(mode="json")
            # a claim may raise a minimum, never lower it below 1.0.7 (the maintainer,
            # 2026-10-16): the written value never contradicts the design
            low = sorted(k for k in ("positive", "negative") if value[k] < coverage[name][k])
            if low:
                raise ValueError(
                    f"coverage_minimum.{name}: {', '.join(low)} below the 1.0.7 default "
                    f"{coverage[name]}"
                )
            coverage[name] = value
        out = self.model_dump(mode="json", by_alias=True)
        out["coverage_minimum"] = {name: coverage[name] for name in names}
        unit = self.metric.unit
        if self.metric.reported_uncertainty is not None:
            out["metric"]["reported_uncertainty"] = resolve_uncertainty(
                self.metric.reported_uncertainty, unit, self.metric.reported
            )
        if self.comparison is not None:
            c, oc = self.comparison, out["comparison"]
            center = c.d_pub if c.d_pub is not None else c.g_pub
            oc["uncertainty_method"] = resolve_uncertainty(
                c.uncertainty_method, unit, c.reported_method
            )
            oc["uncertainty_reference"] = resolve_uncertainty(
                c.uncertainty_reference, unit, c.reported_reference
            )
            oc["paired_uncertainty"] = resolve_uncertainty(c.paired_uncertainty, unit, center)
        return out


# ---- the schema object ---------------------------------------------------------------------


def _attachment_record(loaded: LoadedClaim, role: str) -> dict[str, Any]:
    """The JSON record of the single attachment with ``role``, stored in canonical JSON so
    that the hash of its bytes is the hash of its content."""
    matches = [a for a in loaded.claim.attachments if a.role == role]
    if len(matches) != 1:
        raise ValueError(f"the claim needs exactly one attachment with role '{role}'")
    attachment = matches[0]
    if attachment.sha256 is None or not re.fullmatch(HEX64, attachment.sha256):
        raise ValueError(f"the '{role}' attachment needs its sha256")
    path = loaded.attachment_path(attachment)
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read the '{role}' attachment: {exc}") from None
    if sha256_bytes(data) != attachment.sha256:
        raise ValueError(f"the '{role}' attachment differs from its sha256")
    try:
        record = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"the '{role}' attachment is not JSON: {exc}") from None
    if canonical_bytes(record) != data:
        raise ValueError(f"the '{role}' attachment must be stored in canonical JSON")
    return record


def _configuration_ok(items: Any) -> bool:
    """A count record's configuration: a list of {path, sha256}, each path relative, without
    '..', listed once (the files the selection reads, checked again in the run's tree)."""
    if not isinstance(items, list):
        return False
    seen = set()
    for item in items:
        if not isinstance(item, dict) or set(item) != {"path", "sha256"}:
            return False
        path, digest = item["path"], item["sha256"]
        if not isinstance(path, str) or not isinstance(digest, str) or path in seen:
            return False
        posix = PurePosixPath(path)
        if posix.is_absolute() or ".." in posix.parts or "\\" in path or not posix.parts:
            return False
        if not re.fullmatch(HEX64, digest):
            return False
        seen.add(path)
    return True


def _record_at(loaded: LoadedClaim, attachment: Any) -> dict[str, Any]:
    """The canonical JSON record of one attachment, checked against its sha256."""
    if attachment.sha256 is None or not re.fullmatch(HEX64, attachment.sha256):
        raise ValueError(f"the attachment {attachment.path} needs its sha256")
    try:
        data = loaded.attachment_path(attachment).read_bytes()
    except OSError as exc:
        raise ValueError(f"cannot read the attachment {attachment.path}: {exc}") from None
    if sha256_bytes(data) != attachment.sha256:
        raise ValueError(f"the attachment {attachment.path} differs from its sha256")
    try:
        record = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"the attachment {attachment.path} is not JSON: {exc}") from None
    if canonical_bytes(record) != data:
        raise ValueError(f"the attachment {attachment.path} must be stored in canonical JSON")
    if not isinstance(record, dict):
        raise ValueError(f"the attachment {attachment.path} is not a JSON object")
    return record


def _attachment_records(loaded: LoadedClaim, role: str) -> list[dict[str, Any]]:
    """The JSON records of every attachment with ``role`` (possibly none), each checked
    like ``_attachment_record``."""
    out = []
    for attachment in [a for a in loaded.claim.attachments if a.role == role]:
        if attachment.sha256 is None or not re.fullmatch(HEX64, attachment.sha256):
            raise ValueError(f"the '{role}' attachment {attachment.path} needs its sha256")
        try:
            data = loaded.attachment_path(attachment).read_bytes()
        except OSError as exc:
            raise ValueError(f"cannot read the '{role}' attachment: {exc}") from None
        if sha256_bytes(data) != attachment.sha256:
            raise ValueError(f"the '{role}' attachment {attachment.path} differs from its sha256")
        try:
            record = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ValueError(f"the '{role}' attachment is not JSON: {exc}") from None
        if canonical_bytes(record) != data:
            raise ValueError(f"the '{role}' attachment must be stored in canonical JSON")
        out.append(record)
    return out


def errata_corrections(
    erratas: list[dict[str, Any]], inventory: dict[str, Any], inventory_hash: str
) -> tuple[dict[str, dict[str, str]], dict[str, list[str]]]:
    """The approved corrections of the inventory, by candidate: {candidate: {field: new}},
    and the comparisons each corrected candidate is the reference of (``also_used_by``).
    Only ``ERRATA_FIELDS`` may change; each entry's ``old`` must be the inventory's; a
    candidate is corrected once (wp3-population-count-acceptance.md, section 2)."""
    by_id = {c["candidate_id"]: c for c in inventory["candidates"]}
    corrections: dict[str, dict[str, str]] = {}
    uses: dict[str, list[str]] = {}
    for errata in erratas:
        if errata.get("format") != ERRATA_FORMAT:
            raise ValueError(f"an inventory errata has the format {ERRATA_FORMAT}")
        if (errata.get("inventory") or {}).get("sha256") != inventory_hash:
            raise ValueError("an inventory errata names another inventory")
        approval = errata.get("approval") or {}
        for key in ("approved_by", "approved_utc", "approval_record"):
            if not isinstance(approval.get(key), str) or not approval[key].strip():
                raise ValueError(f"an inventory errata needs approval.{key}")
        if not inv.APPROVAL_URL.fullmatch(approval["approval_record"]):
            raise ValueError("an errata's approval_record is a GitHub issue or PR comment URL")
        entries = errata.get("entries")
        if not isinstance(entries, list) or not entries:
            raise ValueError("an inventory errata lists at least one entry")
        for entry in entries:
            cid, field = entry.get("candidate_id"), entry.get("field")
            if cid not in by_id:
                raise ValueError(f"an errata corrects candidate {cid!r}, not in the inventory")
            if field not in ERRATA_FIELDS:
                raise ValueError(f"an errata may change only {ERRATA_FIELDS}, not {field!r}")
            if cid in corrections:
                raise ValueError(f"candidate {cid} is corrected twice")
            if by_id[cid]["transcription"].get(field) != entry.get("old"):
                raise ValueError(f"{cid}: the errata's old {field} is not the inventory's")
            if not isinstance(entry.get("new"), str) or not entry["new"]:
                raise ValueError(f"{cid}: the errata's new {field} is empty")
            corrections[cid] = {field: entry["new"]}
        for comparison in errata.get("also_used_by") or {}:
            uses.setdefault(comparison, [])
            for cid in corrections:
                uses[comparison].append(cid)
    return corrections, uses


class MlClaimSchema:
    """The ``ClaimSchema`` of the ML pack."""

    def resolve_test_plan(self, raw: dict[str, Any]) -> dict[str, Any]:
        return MlTestPlan.model_validate(raw or {}).model_dump(mode="json", by_alias=True)

    def resolve_targets(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out = []
        for i, item in enumerate(raw):
            try:
                out.append(MlTarget.model_validate(item).resolved())
            except ValidationError as exc:
                raise ValueError(f"targets[{i}]: {_errors(exc)}") from None
            except ValueError as exc:
                raise ValueError(f"targets[{i}]: {exc}") from None
        return out

    def resolve_pass_criteria(self, raw: dict[str, Any] | None, kind: str) -> dict[str, Any] | None:
        if kind != "replicate":
            raise ValueError("the ml pack has replicate claims only")
        if raw is not None:
            raise ValueError("ML claims use no pass_criteria: each claim carries its own rule")
        return None

    def validate_claim(self, loaded: LoadedClaim) -> None:
        claim = loaded.claim
        if claim.kind != "replicate":
            raise ValueError("the ml pack has replicate claims only")
        if not claim.targets:
            raise ValueError("an ML claim file lists at least one claim in targets")
        plan = MlTestPlan.model_validate(_input_form(claim.test_plan))
        targets = [MlTarget.model_validate(_target_input(t)) for t in claim.targets]
        keys = [t.key for t in targets]
        if len(set(keys)) != len(keys):
            raise ValueError("two claims share a key")
        self._check_patches(loaded, plan)
        self._check_population_counts(loaded, plan)
        for target in targets:
            self._check_target(plan, target)
        self._check_exempt_minimums(loaded, plan, targets)
        inventory = _attachment_record(loaded, INVENTORY_ROLE)
        draw_record = _attachment_record(loaded, DRAW_ROLE)
        try:
            inventory_hash = inv.inventory_sha256(inventory)
        except inv.InventoryError as exc:
            raise ValueError(f"claim inventory: {exc}") from None
        corrections, uses = errata_corrections(
            _attachment_records(loaded, ERRATA_ROLE), inventory, inventory_hash
        )
        self._check_inventory(plan, targets, inventory, corrections, uses)
        self._check_draw(targets, draw_record, inventory, inventory_hash)
        self._check_transcribed_numbers(loaded, targets)
        resolved = [
            self._derive(plan, target, raw_target)
            for raw_target, target in zip(claim.targets, targets, strict=True)
        ]
        loaded.claim = claim.model_copy(update={"targets": resolved})
        # the written derived values must equal a fresh derivation (maintainer's
        # condition on item e, 2026-10-15)
        verify_derived(loaded.canonical())

    @staticmethod
    def _check_exempt_minimums(
        loaded: LoadedClaim, plan: MlTestPlan, targets: list[MlTarget]
    ) -> None:
        """A minimum coverage of data_present written by hand for generated data is refused,
        whatever its value (wp3-data-sources-acceptance.md, section 3): read in the claim
        file as written, before the resolution fills the defaults (Codex review)."""
        raw_targets = _read_decimal_claim(loaded.path).get("targets") or []
        if len(raw_targets) != len(targets):
            raise ValueError("the claim file changed while it was being read")
        origins = {d.name: dataset_origin(d) for d in plan.datasets}
        for t, raw in zip(targets, raw_targets, strict=True):
            given = raw.get("coverage_minimum") or {}
            if origins[t.dataset] == GENERATED and BASE_GATES[1] in given:
                raise ValueError(
                    f"{t.key}: a minimum coverage of data_present is given for generated data, "
                    "where the gate does not apply"
                )

    @staticmethod
    def _check_transcribed_numbers(loaded: LoadedClaim, targets: list[MlTarget]) -> None:
        """The approved transcription's value and command are the claim's (maintainer's
        decision 1, 2026-10-15). Numbers are compared as the decimals written in the claim
        file, read again without passing through a float; commands as argument lists."""
        raw_targets = _read_decimal_claim(loaded.path).get("targets") or []
        if len(raw_targets) != len(targets):
            raise ValueError("the claim file changed while it was being read")
        for t, raw in zip(targets, raw_targets, strict=True):
            text = t.inventory.transcription
            if t.type == "value":
                written = [_decimal(text.value, f"{t.key}: transcription.value")]
                claimed = [raw["metric"]["reported"]]
            else:
                parts = text.value.split(" vs ")
                if len(parts) != 2:
                    raise ValueError(
                        f"{t.key}: a comparison's transcribed value is '<method> vs <reference>'"
                    )
                written = [_decimal(p, f"{t.key}: transcription.value") for p in parts]
                comparison = raw["comparison"]
                claimed = [comparison["reported_method"], comparison["reported_reference"]]
            decimals = [_claimed_decimal(c) for c in claimed]
            if any(d is None for d in decimals):
                raise ValueError(f"{t.key}: the published values must be decimal numbers")
            if decimals != written:
                raise ValueError(f"{t.key}: the transcribed value differs from the claim's")
            try:
                command = json.loads(text.command)
            except json.JSONDecodeError:
                command = None
            if not isinstance(command, list) or any(not isinstance(a, str) for a in command):
                raise ValueError(
                    f"{t.key}: the transcribed command is a JSON array of argument strings"
                )
            argv = list(t.run.argv) + ([t.run.seed_argument] if t.run.seed_argument else [])
            if command != argv:
                raise ValueError(f"{t.key}: the transcribed command differs from the claim's")

    def targets_for_run(self, loaded: LoadedClaim) -> list[dict[str, Any]]:
        return list(loaded.claim.targets)

    def target_key(self, target: dict[str, Any]) -> str:
        return str(target["key"])

    # -- checks across sections

    @staticmethod
    def _check_patches(loaded: LoadedClaim, plan: MlTestPlan) -> None:
        patches = {a.path for a in loaded.claim.attachments if a.role == PATCH_ROLE}
        for patch in plan.build.allowed_patches:
            if patch.attachment not in patches:
                raise ValueError(
                    f"allowed patch {patch.attachment} is not an attachment with role "
                    f"'{PATCH_ROLE}'"
                )

    @staticmethod
    def _check_population_counts(loaded: LoadedClaim, plan: MlTestPlan) -> None:
        """Each population counted before the lock is bound to its claim (W3.12f): the
        script and record attachments by path and role, the record's dataset, split, count
        (an int of at least 1, equal to expected_examples), script hash, commit, patches in
        order, base image and exit 0 (wp3-population-count-acceptance.md, section 1)."""
        by_path = {a.path: a for a in loaded.claim.attachments}
        used: set[str] = set()
        patches = []
        for patch in plan.build.allowed_patches:
            attachment = by_path.get(patch.attachment)
            patches.append(attachment.sha256 if attachment is not None else None)
        for dataset in plan.datasets:
            for name, split in (getattr(dataset, "derived_splits", None) or {}).items():
                counted = split.counted_before_lock
                if counted is None:
                    continue
                where = f"{dataset.name}/{name}"
                script = by_path.get(counted.script)
                record_attachment = by_path.get(counted.record)
                if script is None or script.role != POPULATION_SCRIPT_ROLE:
                    raise ValueError(f"{where}: the count script is not an attachment with role "
                                     f"'{POPULATION_SCRIPT_ROLE}'")  # fmt: skip
                if record_attachment is None or record_attachment.role != POPULATION_RECORD_ROLE:
                    raise ValueError(f"{where}: the count record is not an attachment with role "
                                     f"'{POPULATION_RECORD_ROLE}'")  # fmt: skip
                for path in (counted.script, counted.record):
                    if path in used:
                        raise ValueError(f"{where}: {path} serves another counted population")
                    used.add(path)
                if script.sha256 is None or not re.fullmatch(HEX64, script.sha256):
                    raise ValueError(f"{where}: the count script needs its sha256")
                record = _record_at(loaded, record_attachment)
                count = record.get("count")
                checks = (
                    (record.get("format") == POPULATION_RECORD_FORMAT, "format"),
                    (record.get("dataset") == dataset.name, "dataset"),
                    (record.get("split") == name, "split"),
                    (type(count) is int and count >= 1, "count (an int of at least 1)"),
                    (count == split.expected_examples, "count equal to expected_examples"),
                    (record.get("script_sha256") == script.sha256, "script's sha256"),
                    (record.get("commit") == plan.repository.commit, "repository commit"),
                    (record.get("patches") == patches, "allowed patches in order"),
                    (
                        (record.get("environment") or {}).get("base_image")
                        == plan.build.base_image,
                        "base image",
                    ),
                    (
                        re.fullmatch(HEX64, str((record.get("environment") or {}).get(
                            "lock_sha256", ""))) is not None,
                        "resolved lock's sha256",
                    ),
                    (
                        re.fullmatch(HEX64, str((record.get("environment") or {}).get(
                            "pyvenv_sha256", ""))) is not None,
                        "interpreter's pyvenv.cfg sha256",
                    ),
                    (
                        (record.get("environment") or {}).get("rung")
                        in COUNTED_RUNGS,
                        "rung (one with a resolved lock)",
                    ),
                    (_configuration_ok(record.get("configuration")), "configuration"),
                    (record.get("exit_code") == 0, "exit code 0"),
                )  # fmt: skip
                for ok, what in checks:
                    if not ok:
                        raise ValueError(f"{where}: the count record's {what} does not hold")

    @staticmethod
    def _check_inventory(
        plan: MlTestPlan,
        targets: list[MlTarget],
        inventory: dict[str, Any],
        corrections: dict[str, dict[str, str]] | None = None,
        uses: dict[str, list[str]] | None = None,
    ) -> str:
        try:
            digest = inv.inventory_sha256(inventory)
        except inv.InventoryError as exc:
            raise ValueError(f"claim inventory: {exc}") from None
        paper = inventory["paper"]
        if (paper["arxiv_id"], paper["version"]) != (plan.paper.arxiv_id, plan.paper.version):
            raise ValueError("the claim inventory is for another paper")
        by_id = {c["candidate_id"]: c for c in inventory["candidates"]}
        for t in targets:
            if t.approvals.transcription.inventory_sha256 != digest:
                raise ValueError(f"{t.key}: the transcription approval names another inventory")
            candidate = by_id.get(t.inventory.candidate_id)
            if candidate is None:
                raise ValueError(
                    f"{t.key}: candidate {t.inventory.candidate_id} is not in the inventory"
                )
            if candidate["type"] != t.type:
                raise ValueError(
                    f"{t.key}: the inventory lists this candidate as {candidate['type']}"
                )
            # the inventory's transcription, with an approved errata's correction (the
            # approval and the draw stay bound to the original inventory)
            expected = {
                **candidate["transcription"],
                **(corrections or {}).get(t.inventory.candidate_id, {}),
            }
            if expected != t.inventory.transcription.model_dump(mode="json"):
                raise ValueError(f"{t.key}: the transcription differs from the inventory's")
            if t.type == "comparison" and isinstance(t.comparison.reference_run, Run):
                MlClaimSchema._check_reference_command(t, candidate, by_id, corrections, uses)
            text = t.inventory.transcription
            pairs = (
                (text.location, t.source.location, "location"),
                (text.metric, t.metric.name, "metric"),
                (text.split, t.metric.split, "split"),
            )
            for written, structured, what in pairs:
                if written != structured:
                    raise ValueError(f"{t.key}: the transcribed {what} differs from the claim's")
            if t.type == "comparison" and candidate.get("reference") != t.comparison.reference:
                raise ValueError(f"{t.key}: the inventory names another reference method")
            # the identity of the candidate (#59, Codex review of the WP5 hardening): the
            # dataset by the identifier the claim uses, and for a comparison its method;
            # the execution conditions are text the maintainer approves with the inventory
            if candidate.get("dataset") != t.dataset:
                raise ValueError(f"{t.key}: the inventory names another dataset")
            if t.type == "comparison" and candidate.get("method") != t.comparison.method:
                raise ValueError(f"{t.key}: the inventory names another method")
        return digest

    @staticmethod
    def _check_reference_command(
        t: MlTarget,
        candidate: dict[str, Any],
        by_id: dict[str, dict[str, Any]],
        corrections: dict[str, dict[str, str]] | None,
        uses: dict[str, list[str]] | None,
    ) -> None:
        """A comparison whose reference method is a candidate an errata corrects runs the
        reference with the corrected command: the value candidate of the same table and row
        named by the reference, listed in the errata's ``also_used_by`` for this comparison
        (wp3-population-count-acceptance.md, section 2)."""
        prefix = candidate["candidate_id"].rsplit("/", 1)[0]
        reference_id = f"{prefix}/{candidate.get('reference')}"
        fix = (corrections or {}).get(reference_id)
        if fix is None or "command" not in fix:
            return
        if reference_id not in (uses or {}).get(candidate["candidate_id"], []):
            raise ValueError(f"{t.key}: the errata of {reference_id} does not list this comparison")
        run = t.comparison.reference_run
        argv = list(run.argv) + ([run.seed_argument] if run.seed_argument else [])
        if json.loads(fix["command"]) != argv:
            raise ValueError(
                f"{t.key}: the reference run's command is not the errata's corrected command"
            )
        if reference_id not in by_id:
            raise ValueError(f"{t.key}: {reference_id} is not in the inventory")

    @staticmethod
    def _check_draw(
        targets: list[MlTarget],
        record: dict[str, Any],
        inventory: dict[str, Any],
        inventory_hash: str,
    ) -> None:
        try:
            draw = inv.read_draw_record(record)
        except inv.InventoryError as exc:
            raise ValueError(f"claim draw: {exc}") from None
        if draw.inventory_sha256 != inventory_hash:
            raise ValueError("the claim draw used another inventory")
        # the record must agree with the inventory it names (Codex review); whether its
        # order comes from the drand round is the provenance check of WP5/WP7
        if draw.arxiv_id != inventory["paper"]["arxiv_id"]:
            raise ValueError("the claim draw is for another paper")
        required = inv.has_eligible_comparison(inventory)
        if draw.comparison_required != required:
            raise ValueError("the claim draw states the comparison requirement wrongly")
        drawable = sorted(
            c["candidate_id"]
            for c in inventory["candidates"]
            if c["type"] == "value" or (required and c["eligible_comparison"])
        )
        if sorted(draw.shuffled) != drawable:
            raise ValueError("the claim draw did not shuffle exactly the drawable candidates")
        by_id = {c["candidate_id"]: c for c in inventory["candidates"]}
        if required and not any(by_id[i]["type"] == "comparison" for i in draw.drawn):
            raise ValueError("the claim draw holds no comparison although one is required")
        if [t.inventory.candidate_id for t in targets] != draw.drawn:
            raise ValueError("the claims in targets are not the drawn claims in the drawn order")
        for i, t in enumerate(targets, start=1):
            if t.inventory.position != i:
                raise ValueError(f"{t.key}: inventory.position must be {i}, its place in the draw")

    @staticmethod
    def _check_target(plan: MlTestPlan, t: MlTarget) -> None:
        if (t.source.arxiv_id, t.source.version) != (plan.paper.arxiv_id, plan.paper.version):
            raise ValueError(f"{t.key}: source names another paper than test_plan.paper")
        if (t.source.repository_url, t.source.repository_commit) != (
            plan.repository.url,
            plan.repository.commit,
        ):
            raise ValueError(f"{t.key}: source names another repository or commit")
        datasets = {d.name: d for d in plan.datasets}
        dataset = datasets.get(t.dataset)
        if dataset is None:
            raise ValueError(f"{t.key}: dataset {t.dataset} is not declared in test_plan")
        # a split of the file or a derived split (wp3-data-sources-acceptance.md, section 2)
        sizes = populations(dataset)
        if t.metric.split not in sizes:
            raise ValueError(f"{t.key}: split {t.metric.split} is not declared for {t.dataset}")
        if t.metric.n_examples != sizes[t.metric.split]:
            raise ValueError(
                f"{t.key}: metric.n_examples differs from the split's expected_examples"
            )
        if t.weights is not None and t.weights not in {w.name for w in plan.weights}:
            raise ValueError(f"{t.key}: weights {t.weights} is not declared in test_plan")
        # 1.5a: the hook is an allowed patch, fixed and hashed before the lock; the split's
        # identity names every other split the dataset declares
        patches = {p.attachment for p in plan.build.allowed_patches}
        for evidence in (t.coverage_evidence.method, t.coverage_evidence.reference):
            if evidence is None:
                continue
            hook = evidence.route("hook")
            if hook is not None and hook.patch not in patches:
                raise ValueError(
                    f"{t.key}: the coverage hook {hook.patch} is not in test_plan.build."
                    "allowed_patches"
                )
            identity = evidence.split_identity
            if identity is not None:
                others = {s.name for s in identity.other_splits}
                if t.metric.split in others:
                    raise ValueError(
                        f"{t.key}: split_identity.other_splits names the claim's own split"
                    )
                # every split and derived split but the claim's own (section 2)
                missing = sorted(set(sizes) - {t.metric.split} - others)
                if missing:
                    raise ValueError(
                        f"{t.key}: split_identity.other_splits leaves out the declared "
                        f"splits {missing}"
                    )
        holdout = t.attack("holdout")
        if holdout.applies:
            train = dataset.splits.get("train")
            if train is None:
                raise ValueError(f"{t.key}: holdout needs a declared train split (1.0.10)")
            if rules.holdout_size(train.expected_examples) < rules.HOLDOUT_MIN_EXAMPLES:
                raise ValueError(
                    f"{t.key}: a holdout of floor(0.1 * {train.expected_examples}) examples is "
                    f"below {rules.HOLDOUT_MIN_EXAMPLES}; the attack does not apply (1.0.10)"
                )

    @staticmethod
    def _derive(plan: MlTestPlan, t: MlTarget, raw: dict[str, Any]) -> dict[str, Any]:
        """Writes out the derived seed lists and the holdout size and factor."""
        out = json.loads(json.dumps(raw))
        run_seed = plan.paper.run_seed_sha256
        base = list(t.seeds.base)
        if t.seeds.base_source == "derived":
            want = seeds.derived_seeds(run_seed, "base", t.n_base)
            if base != want:
                raise ValueError(f"{t.key}: seeds.base differs from the derivation of 1.0.4")
        derived = {
            "attack": seeds.derived_seeds(run_seed, "seeds", seeds.ATTACK_SEEDS, base),
            "data_split": seeds.derived_seeds(run_seed, "data_split", seeds.DATA_SPLIT_SEEDS, base),
            "holdout": seeds.derived_seeds(run_seed, "holdout", seeds.HOLDOUT_SEEDS, base),
        }
        for name, want in derived.items():
            given = getattr(t.seeds, name)
            if given is not None and given != want:
                raise ValueError(f"{t.key}: seeds.{name} differs from the derivation of 1.0.4")
            out["seeds"][name] = want
        dataset = next(d for d in plan.datasets if d.name == t.dataset)
        holdout = t.attack("holdout")
        if holdout.applies:
            m = rules.holdout_size(dataset.splits["train"].expected_examples)
            entry = next(a for a in out["attacks"] if a["name"] == "holdout")
            entry["params"].update(
                fraction=rules.HOLDOUT_FRACTION,
                m=m,
                factor=rules.holdout_factor(t.metric.n_examples, m),
            )
        # data_present is not applicable for generated data, and only then (wp3-data-
        # sources-acceptance.md, section 3): the map is written here, and the gate's
        # minimum is not written; one given by hand (other than the default) is refused
        if dataset_origin(dataset) == GENERATED:
            given = out.get("coverage_minimum", {}).get(BASE_GATES[1])
            if given is not None and given != {"positive": 1, "negative": 1}:
                raise ValueError(
                    f"{t.key}: a minimum coverage of data_present is given for generated data, "
                    "where the gate does not apply"
                )
            out.get("coverage_minimum", {}).pop(BASE_GATES[1], None)
            out["not_applicable"] = {BASE_GATES[1]: GENERATED_REASON}
        elif raw.get("not_applicable") is not None:
            raise ValueError(f"{t.key}: not_applicable is only for generated data")
        return out


class _DecimalLoader(yaml.SafeLoader):
    """A YAML loader whose floats are Decimals of their written text: the same numbers
    the SafeLoader reads (YAML 1.1 floats, with "_" separators and base-60 forms), never
    passed through a binary float. ``.inf`` and ``.nan`` stay their text, so a comparison
    with them refuses instead of the whole file failing to load."""


def _construct_decimal(loader: yaml.SafeLoader, node: yaml.Node) -> Decimal | str:
    text = str(loader.construct_scalar(node)).replace("_", "")
    if ":" in text:  # YAML 1.1 base 60, for example 1:30.5 = 90.5
        sign = -1 if text.startswith("-") else 1
        parts = text.lstrip("+-").split(":")
        # exact arithmetic, independent of the caller's decimal context: enough digits
        # for every term, and any rounding raises instead of passing (Codex review)
        exact = Context(prec=len(text) * 4 + 50, traps=[Inexact, Rounded, InvalidOperation])
        try:
            total = Decimal(0)
            for part in parts:
                total = exact.add(exact.multiply(total, Decimal(60)), Decimal(part))
            return exact.multiply(Decimal(sign), total)
        except (Inexact, Rounded, InvalidOperation):
            return text
    try:
        value = Decimal(text)
    except InvalidOperation:
        return text
    return value if value.is_finite() else text


def _claimed_decimal(value: Any) -> Decimal | None:
    """A published value of the claim file as an exact Decimal: a YAML float (Decimal), an
    int, or a numeric string that the schema's float fields also accept (``"9.12e1"``,
    which YAML 1.1 reads as a string). Anything else is None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return value if value.is_finite() else None
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, str) and _DECIMAL_TEXT.match(value.strip()):
        return Decimal(value.strip())
    return None


_DecimalLoader.add_constructor("tag:yaml.org,2002:float", _construct_decimal)


def _read_decimal_claim(path: Path) -> dict[str, Any]:
    try:
        data = yaml.load(path.read_text(encoding="utf-8"), Loader=_DecimalLoader)  # noqa: S506
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as exc:
        raise ValueError(f"cannot read the claim file again: {exc}") from None
    if not isinstance(data, dict):
        raise ValueError("the claim file must hold a mapping")
    return data


def _decimal(text: str, what: str) -> Decimal:
    if not _DECIMAL_TEXT.match(text.strip()):
        raise ValueError(f"{what} must be a decimal number as printed, got {text!r}")
    return Decimal(text.strip())


# ---- derived values: written once, recomputed at every validation ---------------------------


def verify_derived(claim: dict[str, Any]) -> None:
    """Recomputes every value the resolution derives and requires equality with the
    written one (maintainer's condition on item e, 2026-10-15): the build ladder and the
    budget of the profile, the derived seed lists, the holdout fraction, size and factor,
    and each uncertainty's status, sd and quantile. Raises ValueError on any difference
    or missing value. The derivations depend only on the claim's own values: no clock,
    no platform-specific digits (quantiles and SDs are rounded to 12 significant digits),
    no dictionary order."""
    plan = claim["test_plan"]
    if "ladder" not in plan["build"] or plan["build"]["ladder"] != list(BUILD_LADDER):
        raise ValueError("derived value differs: test_plan.build.ladder")
    budget = plan["budget"]
    want = BUDGET_PROFILES[budget["profile"]]
    names = ("paper_cpu_hours", "base_cpu_hours", "attacks_cpu_hours")
    if any(n not in budget for n in names) or tuple(budget[n] for n in names) != want:
        raise ValueError("derived value differs: test_plan.budget")
    run_seed = plan["paper"]["run_seed_sha256"]
    datasets = {d["name"]: d for d in plan["datasets"]}
    for t in claim["targets"]:
        key, s = t["key"], t["seeds"]
        base = list(s["base"])
        # n_base by its rule (1.0.4), never from the written list (Codex review)
        reported = t["metric"].get("reported_n_seeds")
        n_base = 1 if reported is None else min(reported, s["base_cap"])
        if len(base) != n_base:
            raise ValueError(f"derived value differs: {key} seeds.base holds {len(base)} seeds")
        if s["base_source"] == "derived" and base != seeds.derived_seeds(run_seed, "base", n_base):
            raise ValueError(f"derived value differs: {key} seeds.base")
        for name, domain, count in (
            ("attack", "seeds", seeds.ATTACK_SEEDS),
            ("data_split", "data_split", seeds.DATA_SPLIT_SEEDS),
            ("holdout", "holdout", seeds.HOLDOUT_SEEDS),
        ):
            if name not in s or s[name] != seeds.derived_seeds(run_seed, domain, count, base):
                raise ValueError(f"derived value differs: {key} seeds.{name}")
        # the exemption of data_present iff the data are generated (wp3-data-sources-
        # acceptance.md, section 3): the map and the absent minimum, nothing else
        generated = dataset_origin(datasets[t["dataset"]]) == GENERATED
        want_map = {BASE_GATES[1]: GENERATED_REASON} if generated else None
        if t.get("not_applicable") != want_map:
            raise ValueError(f"derived value differs: {key} not_applicable")
        if (BASE_GATES[1] in t.get("coverage_minimum", {})) == generated:
            raise ValueError(f"derived value differs: {key} coverage_minimum.data_present")
        holdout = next(a for a in t["attacks"] if a["name"] == "holdout")
        if holdout["applies"]:
            n_train = datasets[t["dataset"]]["splits"]["train"]["expected_examples"]
            m = rules.holdout_size(n_train)
            p = holdout["params"]
            for name, value in (
                ("fraction", rules.HOLDOUT_FRACTION),
                ("m", m),
                ("factor", rules.holdout_factor(t["metric"]["n_examples"], m)),
            ):
                if name not in p or p[name] != value:
                    raise ValueError(f"derived value differs: {key} holdout.{name}")
        unit = t["metric"]["unit"]
        comparison = t.get("comparison")
        records = []
        if t["metric"].get("reported_uncertainty") is not None:
            records.append(
                (
                    "metric.reported_uncertainty",
                    t["metric"]["reported_uncertainty"],
                    t["metric"].get("reported"),
                )
            )
        if comparison:
            center = (
                comparison.get("d_pub")
                if comparison.get("d_pub") is not None
                else comparison.get("g_pub")
            )
            records += [
                (
                    "comparison.uncertainty_method",
                    comparison["uncertainty_method"],
                    comparison["reported_method"],
                ),
                (
                    "comparison.uncertainty_reference",
                    comparison["uncertainty_reference"],
                    comparison["reported_reference"],
                ),
                ("comparison.paired_uncertainty", comparison["paired_uncertainty"], center),
            ]
        for where, record, center in records:
            inputs = {k: v for k, v in record.items() if k not in ("status", "sd", "quantile")}
            fresh = resolve_uncertainty(Uncertainty.model_validate(inputs), unit, center)
            for name in ("status", "sd", "quantile"):
                # a missing key is refused even when the expected value is None
                if name not in record or record[name] != fresh[name]:
                    raise ValueError(f"derived value differs: {key} {where}.{name}")


def _errors(exc: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(p) for p in e['loc']) or '<root>'}: {e['msg']}" for e in exc.errors()
    )


def _input_form(test_plan: dict[str, Any]) -> dict[str, Any]:
    """The resolved test_plan back in input form (the fixed ladder is not an input)."""
    out = json.loads(json.dumps(test_plan))
    out["build"].pop("ladder", None)
    return out


def _target_input(target: dict[str, Any]) -> dict[str, Any]:
    """A resolved target back in input form: the values resolution writes out are
    removed, so the model checks them again from the inputs."""
    out = json.loads(json.dumps(target))
    for record in _uncertainty_records(out):
        for key in ("status", "sd", "quantile"):
            record.pop(key, None)
    out.pop("not_applicable", None)  # written again by _derive from the dataset's origin
    return out


def _uncertainty_records(target: dict[str, Any]) -> list[dict[str, Any]]:
    records = []
    if target.get("metric", {}).get("reported_uncertainty") is not None:
        records.append(target["metric"]["reported_uncertainty"])
    comparison = target.get("comparison")
    if comparison:
        for key in ("uncertainty_method", "uncertainty_reference", "paired_uncertainty"):
            records.append(comparison[key])
    return records
