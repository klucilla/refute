"""Pydantic models for the TESS pack's sections of ``claim.yaml`` and ``targets.yaml``.

Every threshold has an explicit default here, and the resolved values are written
into the locked claim. See ``docs/gauntlet-tess-v0.1.md`` for what each one means.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_serializer,
    model_validator,
)


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid")


class DataParams(_Model):
    mission: Literal["TESS"] = "TESS"
    author: Literal["SPOC"] = "SPOC"
    exptime_seconds: Literal[120] = 120
    flux_column: Literal["pdcsap_flux"] = "pdcsap_flux"
    quality_bitmask: Literal["default"] = "default"
    # v0.2: SPOC 2-min target pixel files and TIC sources around the target.
    target_pixel_files: bool = True
    neighbor_radius_arcsec: float = Field(120.0, gt=0)


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
    # v0.2 (issue #3): TIC rows with these dispositions do not describe one real star.
    unreliable_tic_dispositions: list[str] = Field(
        default_factory=lambda: ["SPLIT", "DUPLICATE", "ARTIFACT"]
    )
    # Data-quality warning (report only, not a test): TIC Tmag vs the target's catalog Tmag.
    max_tmag_mismatch: float = Field(1.0, gt=0)


class CentroidParams(_Model):
    """Flux-weighted centroid in the SPOC aperture of the target pixel files."""

    max_sigma: float = Field(3.0, gt=0)
    min_offset_pixels: float = Field(0.5, ge=0)
    min_sectors: int = Field(1, ge=1)


class ApertureParams(_Model):
    """Transit depth in a core aperture versus a dilated aperture."""

    core_radius_pixels: float = Field(1.5, gt=0)
    dilation_pixels: int = Field(1, ge=1)
    max_sigma: float = Field(3.0, gt=0)
    min_depth_ratio: float = Field(1.2, gt=1)


class ContaminationParams(_Model):
    """Unresolved TIC neighbors that could produce the signal."""

    max_separation_arcsec: float = Field(21.0, gt=0)
    max_eclipse_depth: float = Field(1.0, gt=0, le=1)
    min_crowdsap: float = Field(0.8, gt=0, le=1)
    ignored_dispositions: list[str] = Field(
        default_factory=lambda: ["SPLIT", "DUPLICATE", "ARTIFACT"]
    )


class AliasParams(_Model):
    """Does a box add to a sinusoid at the found period? And known systematic periods."""

    min_box_delta_bic: float = Field(10.0, gt=0)
    sine_harmonics: int = Field(2, ge=1, le=4)
    detrend_window_periods: float = Field(3.0, gt=0)
    systematic_periods_days: list[float] = Field(
        default_factory=lambda: [13.7, 13.7 / 2, 13.7 / 3, 13.7 / 4, 1.0]
    )
    systematic_tolerance: float = Field(0.01, gt=0)


class SystematicsParams(_Model):
    """Momentum dumps, SAP versus PDCSAP depth, and background at transit times."""

    dump_margin_hours: float = Field(1.0, ge=0)
    max_dump_fraction: float = Field(0.5, gt=0, le=1)
    min_events_for_dumps: int = Field(3, ge=1)
    max_sap_sigma: float = Field(3.0, gt=0)
    max_sap_rel_diff: float = Field(0.5, gt=0)
    max_background_sigma: float = Field(3.0, gt=0)
    max_background_fraction: float = Field(0.5, gt=0)


class EbCatalogParams(_Model):
    """Cross-match with eclipsing-binary catalogs given as claim attachments.

    The test runs only if the claim has attachments with role ``eb-catalog``.
    """

    match_radius_arcsec: float = Field(21.0, gt=0)
    period_tolerance: float = Field(0.01, gt=0)
    period_factors: list[float] = Field(default_factory=lambda: [1.0, 2.0, 0.5])
    # v0.2.1 (H9a): catalogs built from the same photometry as the light curve. A
    # period match under the target's own TIC in one of them is a warning, not a fatal
    # failure (it is not independent evidence). An empty list restores v0.2.
    same_photometry_catalogs: list[str] = Field(default_factory=lambda: ["TESS-EB"])

    @field_validator("same_photometry_catalogs")
    @classmethod
    def _named(cls, names: list[str]) -> list[str]:
        if any(not name.strip() for name in names):
            raise ValueError("catalog names must not be empty")
        return names


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
    # v0.2 (issue #2): the hidden year is detrended with a window at least this many
    # times the widest masked span, and a round is INCONCLUSIVE when the train-only
    # timing uncertainty in the hidden year exceeds this many transit durations.
    hidden_detrend_window_factor: float = Field(3.0, gt=0)
    max_timing_sigma_durations: float = Field(1.0, gt=0)
    # v0.2.1 (H4): a round whose train-only candidate fails the SNR gate, has a box
    # longer than this fraction of its period, or predicts transit windows covering
    # more than this fraction of the hidden year is INCONCLUSIVE before the hidden year
    # is read. Both limits follow from the window geometry (docs/gauntlet-tess-v0.2.1.md).
    # require_valid_train: false reports the rules without applying them.
    require_valid_train: bool = True
    max_train_duration_period_ratio: float = Field(0.2, gt=0, le=1)
    max_hidden_window_fraction: float = Field(0.5, gt=0, le=1)


# Revision 3, 5: the declared order of the (z_F*, f*) pairs of period_alias.
ALIAS_PAIRS = ((18.47, 0.5), (18.47, 0.7), (30.0, 0.5), (30.0, 0.7), (50.0, 0.5), (50.0, 0.7))


class CorrectionsParams(_Model):
    """M4 of v0.2.1: the TESS corrections of revision 4 of the corrections plan
    (docs/validation/v0.2.1/reopen/corrections-plan-rev4.md; the map of the code,
    m4-implementation-map.md). ``enabled: false`` is the M3 code path; the settings are those of
    a configuration (revision 3, 9.2; the defaults are M4-c1's until the M4 freeze)."""

    # The version rule (map Amendment 17, the maintainer's decision of 2026-10-18): 1 is the
    # legacy block (always the M3 path, whatever ``enabled`` says); 2 is M4 of revision 4. A claim
    # without the block, or with version 1, resolves on the M3 path. New claims write version 2,
    # enabled true and the chosen configuration explicitly. No default here ever changes.
    version: int = Field(1, ge=1, le=2)
    enabled: bool = False
    b_min: int = Field(20, ge=1)
    gap_split: float = Field(5.0, gt=0)
    fap_max: float = Field(1e-4, gt=0, lt=1)
    max_components: int = Field(3, ge=0)
    k_clip: float = Field(2.5, gt=0)
    h_min: float = Field(0.90, gt=0, le=1)
    m_beta: float = Field(1.2, ge=1)
    r_min: int = Field(20, ge=1)
    # M4 piece 6 (map Amendment 21; revision 3, 5): the thresholds (z_F*, f*) of period_alias,
    # chosen per configuration on the selection part among the six declared pairs; the default is
    # the first pair of the declared order.
    alias_z_f: float = 18.47
    alias_f: float = 0.5
    # Package 25 (map Amendment 25, approved 2026-10-18): b and s of the capacity rule (revision
    # 4, 2: one pair, pooled over both noise models, estimated on the selection part). The
    # defaults reproduce the threshold min_snr; they are not a calibration.
    capacity_b: float = Field(0.0, allow_inf_nan=False)
    capacity_s: float = Field(0.0, ge=0, allow_inf_nan=False)

    @model_validator(mode="after")
    def _alias_pair(self) -> CorrectionsParams:
        if (self.alias_z_f, self.alias_f) not in ALIAS_PAIRS:
            raise ValueError(f"(alias_z_f, alias_f) must be a declared pair: {ALIAS_PAIRS}")
        return self

    @property
    def active(self) -> bool:
        """The M4 path runs only with version 2 and enabled true (map Amendment 17)."""
        return self.version == 2 and self.enabled


class GauntletParams(_Model):
    snr: SnrParams = Field(default_factory=SnrParams)
    odd_even: OddEvenParams = Field(default_factory=OddEvenParams)
    secondary_eclipse: SecondaryParams = Field(default_factory=SecondaryParams)
    plausibility: PlausibilityParams = Field(default_factory=PlausibilityParams)
    holdout_by_year: HoldoutParams = Field(default_factory=HoldoutParams)
    events: EventParams = Field(default_factory=EventParams)
    centroid_shift: CentroidParams = Field(default_factory=CentroidParams)
    aperture_depth: ApertureParams = Field(default_factory=ApertureParams)
    nearby_contamination: ContaminationParams = Field(default_factory=ContaminationParams)
    period_alias: AliasParams = Field(default_factory=AliasParams)
    systematics: SystematicsParams = Field(default_factory=SystematicsParams)
    eb_catalog: EbCatalogParams = Field(default_factory=EbCatalogParams)
    corrections: CorrectionsParams = Field(default_factory=CorrectionsParams)


# v0.4 (issue #174): every test a TESS analysis can contain, in the order of expected_tests.
DISCOVERY_TESTS = (
    "snr",
    "odd_even",
    "secondary_eclipse",
    "plausibility",
    "centroid_shift",
    "aperture_depth",
    "nearby_contamination",
    "period_alias",
    "systematics",
    "eb_catalog",
    "holdout_by_year",
)
# v0.5 (docs/plans/v0.5-plan.md): the tests that exist only in a claim with discovery version 2,
# in the order of expected_tests. Only implemented tests are listed, so a claim cannot give a
# role to a test the pipeline does not run (the optional WP5 tests enter when they exist).
V05_TESTS = (
    "single_event",
    "event_consistency",
    "edge_events",
    "sinusoid",
    "duty_cycle",
)
# v0.5.1 (discovery version 3): the EB route's diagnostic (plan, amendments 4 and 9)
V051_TESTS = ("duration_excess",)
GATE_TEST = "snr"
METHOD_STATUS_REFERENCE = "docs/validation/v0.2.1/closing-2026-10-27.md"


class StrongerParams(_Model):
    """The v0.5 section of a test plan (docs/plans/v0.5-acceptance.md): the sensitivity rule's
    alternatives and the parameters of the v0.5 tests. Present only with discovery version 2;
    a plan without it dumps exactly as before (issue #30). The provenance of each default (a
    cited source or a Refute convention) is in the acceptance documents' provenance table.
    """

    # WP1: alternatives strictly beyond each rejection boundary (#185 examples; conventions)
    odd_even_alternative_depth_fraction: float = Field(1.0, gt=0)
    secondary_alternative_depth_fraction: float = Field(1.0, gt=0)
    aperture_alternative_ratio_increment: float = Field(0.3, gt=0)
    centroid_alternative_offset_factor: float = Field(2.0, gt=1)
    sap_alternative_increment: float = Field(0.3, gt=0)
    background_alternative_increment: float = Field(0.3, gt=0)
    period_alias_realizations: int = Field(50, ge=10)
    period_alias_required_failures: int = Field(45, ge=1)
    # WP2: signal versus noise
    single_event_max_ratio: float = Field(0.88, gt=0, lt=1)
    min_measured_events: int = Field(3, ge=2)
    chi2_alpha: float = Field(0.00135, gt=0, lt=1)
    edge_gap_days: float = Field(0.3, gt=0)
    edge_reach_durations: float = Field(2.0, gt=0)
    edge_min_fraction: float = Field(0.5, gt=0, le=1)
    edge_alternative_depth_fraction: float = Field(0.5, gt=0)
    # WP3: variability
    brightening_min_depth_ratio: float = Field(0.1, gt=0)
    sinusoid_min_significance: float = Field(15.0, gt=0)
    sinusoid_max_period_days: float = Field(10.0, gt=0)
    sinusoid_min_amplitude_ratio: float = Field(0.5, gt=0)
    sinusoid_mask_durations: float = Field(1.0, ge=0)
    max_duty_cycle: float = Field(0.5, gt=0, le=1)
    # WP4: centroid per sector
    centroid_control_epochs: int = Field(20, ge=1)
    centroid_min_controls: int = Field(10, ge=1)
    centroid_min_sectors: int = Field(2, ge=2)
    centroid_qualification_sigma: float = Field(3.0, gt=0)
    centroid_max_unqualified_fraction: float = Field(0.5, gt=0, le=1)
    # WP5 (optional): shape and depth stability
    shape_max_ingress_fraction: float = Field(0.45, gt=0, lt=0.5)
    shape_alternative_ingress_fraction: float = Field(0.5, gt=0, le=0.5)
    depth_stability_alternative_fraction: float = Field(0.5, gt=0)

    @model_validator(mode="after")
    def _consistent(self) -> StrongerParams:
        if self.period_alias_required_failures > self.period_alias_realizations:
            raise ValueError("period_alias_required_failures exceeds the realizations")
        if self.centroid_min_controls > self.centroid_control_epochs:
            raise ValueError("centroid_min_controls exceeds centroid_control_epochs")
        if self.shape_alternative_ingress_fraction <= self.shape_max_ingress_fraction:
            raise ValueError("the shape alternative must lie beyond the shape bound")
        return self


class V051Params(_Model):
    """The v0.5.1 section ``v051`` of a test plan (docs/plans/v0.5.1-acceptance.md): the
    parameters of the corrected tests. Present only with discovery version 3, which also needs
    ``stronger``; a plan without it dumps exactly as before (issue #30). The provenance of each
    default is in the acceptance documents' provenance table."""

    # WP3 (b): the sinusoid per harmonic, with the star's other variability modelled
    sinusoid_harmonic_max_period_days: float = Field(20.0, gt=0)
    sinusoid_extra_frequencies: int = Field(3, ge=0)
    sinusoid_extra_min_snr: float = Field(4.0, gt=0)
    # WP3 (c): period_alias with more harmonics; its sensitivity with an exact lower bound
    period_alias_harmonics: int = Field(4, ge=1)
    period_alias_realizations: int = Field(100, ge=10)
    period_alias_required_lower_bound: float = Field(0.9, gt=0, lt=1)


class V052Params(_Model):
    """The v0.5.2 section ``v052`` of a test plan (docs/plans/v0.5.2-stage2-design.md): present only
    with discovery version 4; a plan without it dumps exactly as before (issue #30).

    ``sinusoid_fail_allowed``: withdrawn (false) when any per-cell evaluation of section 5 has a
    false FAIL. ``selector_certified``: true only when the sector selector's own family passes
    (section 2); otherwise a target of five or more sectors stays INCONCLUSIVE in the A0-dependent
    tests."""

    sinusoid_fail_allowed: bool = True
    selector_certified: bool = False


class DiscoveryParams(_Model):
    """The v0.4 section of a discovery claim's test plan (issue #174).

    It exists only in claims of kind ``discover``: a test plan without it resolves exactly as
    before (``TessTestPlan`` leaves the key out), so the resolved hash of every earlier claim
    is unchanged (issue #30).

    - ``decisive`` and ``diagnostic``: the role of every test the analysis contains, as two
      lists, so a test given both roles is caught. The verdict aggregates the decisive tests
      only.
    - ``stages``: the stage at which a test runs (1 or 2; 1 when not listed). In a run of an
      earlier stage the test is reported INCONCLUSIVE with zero coverage, never PASS.
    - ``required_diagnostics``: diagnostics whose absence makes the case incomplete.
    - ``method_status``: always ``not_validated`` in v0.4, with its reference.
    - ``survived_meaning``: what SURVIVED means in this claim, fixed before the lock.
    - ``inputs``: SHA-256 of the files the claim depends on outside the code (protocol,
      frame, catalog snapshots). They are part of the resolved claim, so the lock covers
      them; the selection and promotion steps check their files against them.
    """

    # 1: v0.4. 2: v0.5, the sensitivity rule and the v0.5 tests (needs the plan's `stronger`).
    # 3: v0.5.1, the corrected battery (needs `stronger` and `v051`).
    # 4: v0.5.2, battery version 4 (needs `stronger`, `v051` and `v052`).
    version: Literal[1, 2, 3, 4] = 1
    decisive: list[str] = Field(min_length=1)
    diagnostic: list[str] = Field(default_factory=list)
    stages: dict[str, Literal[1, 2]] = Field(default_factory=dict)
    required_diagnostics: list[str] = Field(default_factory=list)
    method_status: Literal["not_validated"] = "not_validated"
    method_status_reference: str = METHOD_STATUS_REFERENCE
    survived_meaning: str = Field(min_length=1)
    inputs: dict[str, str] = Field(default_factory=dict)
    # S_max (protocol D-9): no product of a later sector is downloaded or read.
    max_sector: int | None = Field(None, ge=1)

    @model_validator(mode="after")
    def _consistent(self) -> DiscoveryParams:
        for label, names in (("decisive", self.decisive), ("diagnostic", self.diagnostic)):
            if len(set(names)) != len(names):
                raise ValueError(f"the {label} list names a test twice")
        both = sorted(set(self.decisive) & set(self.diagnostic))
        if both:
            raise ValueError("a test cannot be both decisive and diagnostic: " + ", ".join(both))
        known = set(DISCOVERY_TESTS) | (set(V05_TESTS) if self.version >= 2 else set())
        if self.version >= 3:
            known |= set(V051_TESTS)  # the version-3 diagnostic of the EB route (amendment 9)
        unknown = sorted(set(self.roles) - known)
        if unknown:
            raise ValueError("roles name unknown tests: " + ", ".join(unknown))
        if self.roles.get(GATE_TEST) != "decisive":
            raise ValueError(f"the gate test '{GATE_TEST}' must have the role 'decisive'")
        if int(self.stages.get(GATE_TEST, 1)) != 1:
            raise ValueError(f"the gate test '{GATE_TEST}' must run at stage 1")
        unstaged = sorted(set(self.stages) - set(self.roles))
        if unstaged:
            raise ValueError("stages name tests without a role: " + ", ".join(unstaged))
        for name in self.required_diagnostics:
            if name not in self.roles:
                raise ValueError(f"required diagnostic '{name}' is not among the claim's tests")
            if self.roles[name] != "diagnostic":
                raise ValueError(
                    f"required diagnostic '{name}' does not have the role 'diagnostic'"
                )
        if len(set(self.required_diagnostics)) != len(self.required_diagnostics):
            raise ValueError("required_diagnostics lists a test twice")
        for name, digest in self.inputs.items():
            if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
                raise ValueError(f"inputs.{name} must be a lowercase SHA-256 hex digest")
        return self

    @property
    def roles(self) -> dict[str, str]:
        """Test name -> ``decisive`` or ``diagnostic``."""
        return {
            **{name: "decisive" for name in self.decisive},
            **{name: "diagnostic" for name in self.diagnostic},
        }

    def stage_of(self, name: str) -> int:
        return int(self.stages.get(name, 1))

    @property
    def last_stage(self) -> int:
        return max([1, *(int(s) for s in self.stages.values())])


class ReproductionInput(_Model):
    """One input a clone lacks (v0.5 WP8; ``refute.core.reproduce``)."""

    name: str = Field(min_length=1)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    url: str = Field(min_length=1)
    dest: str = Field(min_length=1)


class ReproductionParams(_Model):
    """v0.5 (#189, #195): the inputs a clone lacks, each with its SHA-256, URL and destination
    under ``.cache/frozen/``. Only with discovery version 2; absent from the dump otherwise."""

    inputs: list[ReproductionInput] = Field(min_length=1)

    @model_validator(mode="after")
    def _safe(self) -> ReproductionParams:
        from refute.core.reproduce import InputSpec, specs_problems

        problems = specs_problems([InputSpec(**i.model_dump()) for i in self.inputs])
        if problems:
            raise ValueError("; ".join(problems))
        return self


class TessTestPlan(_Model):
    data: DataParams = Field(default_factory=DataParams)
    detrend: DetrendParams = Field(default_factory=DetrendParams)
    search: SearchParams = Field(default_factory=SearchParams)
    gauntlet: GauntletParams = Field(default_factory=GauntletParams)
    discovery: DiscoveryParams | None = None
    stronger: StrongerParams | None = None
    reproduction: ReproductionParams | None = None
    v051: V051Params | None = None
    v052: V052Params | None = None

    @model_serializer(mode="wrap")
    def _without_absent_discovery(self, handler: Any) -> dict[str, Any]:
        """A plan without the v0.4 or the v0.5 sections dumps exactly as before they existed
        (issue #30)."""
        out = handler(self)
        for key in ("discovery", "stronger", "reproduction", "v051", "v052"):
            if out.get(key, 0) is None:
                del out[key]
        return out

    @model_validator(mode="after")
    def _v05_section(self) -> TessTestPlan:
        """Discovery version 2 needs the `stronger` section and a registered sensitivity rule
        or category for every decisive fatal or warning test (v0.5 acceptance, case 1.5); any
        other plan must not have the section."""
        version = self.discovery.version if self.discovery is not None else 1
        version2 = version >= 2
        if version2 != (self.stronger is not None):
            raise ValueError(
                "the `stronger` section goes with discovery version 2 or 3, and only with them"
            )
        if (version >= 3) != (self.v051 is not None):
            raise ValueError("the `v051` section goes with discovery version 3, and only with it")
        if (version == 4) != (self.v052 is not None):
            raise ValueError("the `v052` section goes with discovery version 4, and only with it")
        if self.reproduction is not None and not version2:
            raise ValueError("the `reproduction` section goes only with discovery version 2 or 3")
        if version2:
            from refute.core.sensitivity import registry_problems
            from refute.packs.tess.power import registry_for

            problems = registry_problems(self.discovery.decisive, registry_for(self), [GATE_TEST])
            if problems:
                raise ValueError(
                    "decisive tests without a sensitivity rule: " + "; ".join(problems)
                )
        if version >= 3:
            # v0.5.1 WP5 (row 5.1): version 3 corrects the v0.5 battery and drops none of its
            # tests; every decisive or diagnostic test of v0.5 keeps a role
            from refute.packs.tess.calib05.values import V05_DECISIVE, V05_DIAGNOSTIC

            missing = [n for n in (*V05_DECISIVE, *V05_DIAGNOSTIC) if n not in self.discovery.roles]
            if missing:
                raise ValueError(
                    "version 3 keeps every test of the v0.5 battery; without a role: "
                    + ", ".join(missing)
                )
        return self

    @property
    def v05(self) -> bool:
        """True for a v0.5 or v0.5.1 claim (discovery version 2 or 3): the sensitivity rule
        applies."""
        return self.stronger is not None

    @property
    def is_v052(self) -> bool:
        """True for a v0.5.2 claim (discovery version 4): battery version 4."""
        return self.v052 is not None

    @property
    def is_v051(self) -> bool:
        """True for a v0.5.1 claim (discovery version 3): the corrected battery."""
        return self.v051 is not None


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
    # "exploration": a v0.4 funnel star (no TOI, CTOI or confirmed planet when selected).
    kind: Literal["planet", "false_positive", "development", "exploration"]
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


# P, 2P and P/2: the periods at which a found signal is the catalogued one (v0.2.1).
DEFAULT_SIGNAL_PERIOD_FACTORS = (1.0, 2.0, 0.5)


class CalibrationCriteria(_Model):
    period_tolerance: float = Field(gt=0)
    expected_planets: int = Field(ge=1)
    min_recovered_planets: int = Field(ge=0)
    expected_false_positives: int = Field(ge=0)
    min_flagged_false_positives: int = Field(ge=0)
    max_refuted_planets: int = Field(ge=0)
    # v0.2: tests whose failures do not count when deciding whether a false positive
    # is "flagged" (for example eb_catalog, whose catalogs may share sources with the
    # dispositions used to select the false positives). The degeneracy guard always
    # uses the full verdict.
    flag_excluded_tests: list[str] = Field(default_factory=list)
    # v0.2.1: a false positive counts as "flagged" only if the analyzed period matches
    # the catalogued period at one of these factors (within period_tolerance). Opt-in:
    # false keeps the v0.2 definition.
    flag_requires_signal_recovery: bool = False
    flag_signal_period_factors: list[float] = Field(
        default_factory=lambda: list(DEFAULT_SIGNAL_PERIOD_FACTORS), min_length=1
    )

    @field_validator("flag_signal_period_factors")
    @classmethod
    def _positive_factors(cls, factors: list[float]) -> list[float]:
        if any(f <= 0 for f in factors):
            raise ValueError("every period factor must be > 0")
        return factors

    @model_validator(mode="after")
    def _consistent(self) -> CalibrationCriteria:
        if self.min_recovered_planets > self.expected_planets:
            raise ValueError("min_recovered_planets cannot exceed expected_planets")
        if self.min_flagged_false_positives > self.expected_false_positives:
            raise ValueError("min_flagged_false_positives cannot exceed expected_false_positives")
        return self
