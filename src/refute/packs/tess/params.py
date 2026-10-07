"""Pydantic models for the TESS pack's sections of ``claim.yaml`` and ``targets.yaml``.

Every threshold has an explicit default here, and the resolved values are written
into the locked claim. See ``docs/gauntlet-tess-v0.1.md`` for what each one means.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DataParams(_Model):
    mission: Literal["TESS"] = "TESS"
    author: Literal["SPOC"] = "SPOC"
    exptime_seconds: Literal[120] = 120
    flux_column: Literal["pdcsap_flux"] = "pdcsap_flux"
    quality_bitmask: Literal["default"] = "default"


class DetrendParams(_Model):
    method: Literal["robust-local-quadratic"] = "robust-local-quadratic"
    window_days: float = Field(1.0, gt=0)
    knot_spacing_days: float = Field(0.1, gt=0)
    segment_gap_days: float = Field(0.5, gt=0)
    min_points_per_knot: int = Field(30, ge=3)
    clip_sigma: float = Field(3.0, gt=0)
    clip_iterations: int = Field(2, ge=0)
    upper_clip_sigma: float = Field(5.0, gt=0)
    transit_mask_half_width_durations: float = Field(1.0, gt=0)


class SearchParams(_Model):
    method: Literal["bls-two-stage"] = "bls-two-stage"
    objective: Literal["likelihood"] = "likelihood"
    period_min_days: float = Field(0.5, gt=0)
    period_max_days: float = Field(20.0, gt=0)
    durations_hours: list[float] = Field(
        default_factory=lambda: [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0]
    )
    bin_minutes: float = Field(10.0, gt=0)
    frequency_factor: float = Field(1.0, gt=0)
    peaks_per_sector: int = Field(5, ge=1)
    max_clusters: int = Field(5, ge=1)
    cluster_tolerance: float = Field(0.01, gt=0)
    block_gap_days: float = Field(10.0, gt=0)
    refine_samples_per_width: float = Field(6.0, gt=0)
    refine_width_factor: float = Field(1.5, gt=0)
    final_duration_steps: int = Field(21, ge=3)
    final_oversample: int = Field(20, ge=1)

    @model_validator(mode="after")
    def _check(self) -> SearchParams:
        if self.period_min_days >= self.period_max_days:
            raise ValueError("period_min_days must be smaller than period_max_days")
        if not self.durations_hours or any(d <= 0 for d in self.durations_hours):
            raise ValueError("durations_hours must be a non-empty list of positive numbers")
        if max(self.durations_hours) / 24.0 >= self.period_min_days:
            raise ValueError("the longest duration must be shorter than period_min_days")
        return self


class SnrParams(_Model):
    min_snr: float = Field(7.1, gt=0)


class OddEvenParams(_Model):
    max_sigma: float = Field(3.0, gt=0)
    min_transits_each: int = Field(2, ge=1)


class SecondaryParams(_Model):
    max_sigma: float = Field(3.0, gt=0)
    fatal_depth_ratio: float = Field(0.10, gt=0)


class PlausibilityParams(_Model):
    max_duration_ratio: float = Field(1.5, gt=0)
    max_companion_radius_rjup: float = Field(2.5, gt=0)
    max_stellar_radius_rel_err: float = Field(0.3, gt=0)


class EventParams(_Model):
    """How per-event depths (each transit, or each phase-0.5 window) are measured."""

    min_coverage: float = Field(0.5, gt=0, le=1)
    baseline_gap_durations: float = Field(0.25, ge=0)
    baseline_outer_durations: float = Field(1.5, gt=0)


class HoldoutParams(_Model):
    min_snr: float = Field(5.0, gt=0)
    timing_sigma: float = Field(3.0, gt=0)
    min_predicted_transits: int = Field(2, ge=1)
    min_train_transits: int = Field(3, ge=2)
    min_window_coverage: float = Field(0.5, gt=0, le=1)
    baseline_gap_durations: float = Field(0.25, ge=0)
    baseline_outer_durations: float = Field(1.5, gt=0)
    timing_step_minutes: float = Field(1.0, gt=0)
    timing_scan_half_width_durations: float = Field(0.5, gt=0)


class GauntletParams(_Model):
    snr: SnrParams = Field(default_factory=SnrParams)
    odd_even: OddEvenParams = Field(default_factory=OddEvenParams)
    secondary_eclipse: SecondaryParams = Field(default_factory=SecondaryParams)
    plausibility: PlausibilityParams = Field(default_factory=PlausibilityParams)
    holdout_by_year: HoldoutParams = Field(default_factory=HoldoutParams)
    events: EventParams = Field(default_factory=EventParams)


class TessTestPlan(_Model):
    data: DataParams = Field(default_factory=DataParams)
    detrend: DetrendParams = Field(default_factory=DetrendParams)
    search: SearchParams = Field(default_factory=SearchParams)
    gauntlet: GauntletParams = Field(default_factory=GauntletParams)


class PublishedParams(_Model):
    period_days: float | None = None
    period_err_days: float | None = None
    t0_bjd: float | None = None
    depth_ppm: float | None = None
    duration_hours: float | None = None


class TargetSource(_Model):
    name: str
    url: str
    retrieved_utc: str
    reference: str | None = None


class TessTarget(_Model):
    key: str = Field(pattern=r"^TIC-[0-9]+$")
    tic_id: int = Field(gt=0)
    kind: Literal["planet", "false_positive", "development"]
    name: str | None = None
    published: PublishedParams = Field(default_factory=PublishedParams)
    source: TargetSource
    catalog: dict[str, Any] = Field(default_factory=dict)
    mast: dict[str, Any] = Field(default_factory=dict)
    fp_reason: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def _key_matches(self) -> TessTarget:
        if self.key != f"TIC-{self.tic_id}":
            raise ValueError(f"target key {self.key} does not match tic_id {self.tic_id}")
        return self


class TargetsFile(_Model):
    schema_id: Literal["refute-tess-targets-1"] = Field(alias="schema")
    generated_utc: str
    generator: str
    selection: dict[str, Any] = Field(default_factory=dict)
    targets: list[TessTarget]

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class CalibrationCriteria(_Model):
    period_tolerance: float = Field(gt=0)
    expected_planets: int = Field(ge=1)
    min_recovered_planets: int = Field(ge=0)
    expected_false_positives: int = Field(ge=0)
    min_flagged_false_positives: int = Field(ge=0)
    max_refuted_planets: int = Field(ge=0)

    @model_validator(mode="after")
    def _consistent(self) -> CalibrationCriteria:
        if self.min_recovered_planets > self.expected_planets:
            raise ValueError("min_recovered_planets cannot exceed expected_planets")
        if self.min_flagged_false_positives > self.expected_false_positives:
            raise ValueError("min_flagged_false_positives cannot exceed expected_false_positives")
        return self
