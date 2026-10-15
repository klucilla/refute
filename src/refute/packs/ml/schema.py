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
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator, model_validator

from refute.core.canonical import canonical_bytes
from refute.core.hashing import sha256_bytes
from refute.core.paper import BASE_GATES, BASE_REPRODUCTION, METRIC_RECOMPUTE, prerequisite_names
from refute.packs.ml import recompute, rules, seeds
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
# 1.0.11 (maintainer, 2026-10-15): the bounded rates that may use percent or fraction
BOUNDED_RATES = ("accuracy", "error_rate", "precision", "recall", "f1", "auroc")
INVENTORY_ROLE = "claim-inventory"
DRAW_ROLE = "claim-draw"
PATCH_ROLE = "allowed-patch"
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


def _finite(value: float | None, what: str) -> None:
    if value is not None and not math.isfinite(value):
        raise ValueError(f"{what} must be finite")


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
        return _text(value, "split source")


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


class Dataset(Artifact):
    splits: dict[str, Split] = Field(min_length=1)
    size_tolerance: int = Field(default=0, ge=0)


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
    datasets: list[Dataset] = Field(min_length=1)
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


class Extraction(_Model):
    from_: Literal["file", "log"] = Field(alias="from")
    file: str | None = None
    json_path: str | None = None
    csv: CsvExtraction | None = None
    regex: RegexExtraction | None = None
    unit: Literal["percent", "fraction", "native"]

    @model_validator(mode="after")
    def _check(self) -> Extraction:
        if self.from_ == "file":
            _relative(self.file or "", "metric_extraction.file", ("seed",))
        elif self.file is not None:
            raise ValueError("metric_extraction.file is only for 'from: file'")
        ways = [w for w in (self.json_path, self.csv, self.regex) if w is not None]
        if len(ways) != 1:
            raise ValueError("metric_extraction takes exactly one of json_path, csv, regex")
        return self


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
        for name in ("reported_full", "reported_ablated", "g_abl"):
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
    approvals: Approvals

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
        names = self.coverage_names()
        unknown = sorted(set(self.coverage_minimum) - set(names))
        if unknown:
            raise ValueError(f"coverage_minimum names checks WP2 refuses for this claim: {unknown}")
        coverage = self.coverage_defaults()
        for name, given in self.coverage_minimum.items():
            coverage[name] = given.model_dump(mode="json")
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
        for target in targets:
            self._check_target(plan, target)
        inventory = _attachment_record(loaded, INVENTORY_ROLE)
        draw_record = _attachment_record(loaded, DRAW_ROLE)
        inventory_hash = self._check_inventory(plan, targets, inventory)
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
    def _check_inventory(
        plan: MlTestPlan, targets: list[MlTarget], inventory: dict[str, Any]
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
            if candidate["transcription"] != t.inventory.transcription.model_dump(mode="json"):
                raise ValueError(f"{t.key}: the transcription differs from the inventory's")
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
        return digest

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
        split = dataset.splits.get(t.metric.split)
        if split is None:
            raise ValueError(f"{t.key}: split {t.metric.split} is not declared for {t.dataset}")
        if t.metric.n_examples != split.expected_examples:
            raise ValueError(
                f"{t.key}: metric.n_examples differs from the split's expected_examples"
            )
        if t.weights is not None and t.weights not in {w.name for w in plan.weights}:
            raise ValueError(f"{t.key}: weights {t.weights} is not declared in test_plan")
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
        holdout = t.attack("holdout")
        if holdout.applies:
            dataset = next(d for d in plan.datasets if d.name == t.dataset)
            m = rules.holdout_size(dataset.splits["train"].expected_examples)
            entry = next(a for a in out["attacks"] if a["name"] == "holdout")
            entry["params"].update(
                fraction=rules.HOLDOUT_FRACTION,
                m=m,
                factor=rules.holdout_factor(t.metric.n_examples, m),
            )
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
        total = Decimal(0)
        for part in text.lstrip("+-").split(":"):
            total = total * 60 + Decimal(part)
        return sign * total
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
