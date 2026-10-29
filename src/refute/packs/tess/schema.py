"""TESS pack claim schema: resolves ``test_plan``, ``targets`` and ``pass_criteria``."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from refute.packs.tess.params import CalibrationCriteria, TargetsFile, TessTarget, TessTestPlan
from refute.packs.tess.pipeline import expected_tests

if TYPE_CHECKING:
    from refute.core.claim import LoadedClaim


def load_targets_file(path: Path) -> TargetsFile:
    with Path(path).open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle)
    return TargetsFile.model_validate(raw)


class TessClaimSchema:
    def resolve_test_plan(self, raw: dict[str, Any]) -> dict[str, Any]:
        return TessTestPlan.model_validate(raw or {}).model_dump(mode="json")

    def resolve_targets(self, raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [TessTarget.model_validate(item).model_dump(mode="json") for item in raw]

    def resolve_pass_criteria(self, raw: dict[str, Any] | None, kind: str) -> dict[str, Any] | None:
        if kind == "calibration":
            if raw is None:
                raise ValueError("calibration claims must define pass_criteria")
            return CalibrationCriteria.model_validate(raw).model_dump(mode="json")
        if raw is not None:
            raise ValueError(f"{kind} claims do not use pass_criteria")
        return None

    def validate_claim(self, loaded: LoadedClaim) -> None:
        claim = loaded.claim
        discovery = claim.test_plan.get("discovery")
        if claim.kind != "discover" and discovery is not None:
            raise ValueError("only discover claims have a test_plan.discovery section")
        if claim.kind == "discover":
            self._validate_discover(loaded, discovery)
            return
        if claim.kind == "calibration":
            if claim.targets:
                raise ValueError("calibration claims list targets in the 'targets' attachment")
            attachment = loaded.attachment_by_role("targets")
            if attachment is None:
                raise ValueError("calibration claims need an attachment with role 'targets'")
            path = loaded.attachment_path(attachment)
            if not path.is_file():
                raise ValueError(f"targets attachment not found: {attachment.path}")
            targets = load_targets_file(path)
            criteria = claim.pass_criteria or {}
            planets = sum(1 for t in targets.targets if t.kind == "planet")
            fps = sum(1 for t in targets.targets if t.kind == "false_positive")
            if (
                planets != criteria["expected_planets"]
                or fps != criteria["expected_false_positives"]
            ):
                raise ValueError(
                    f"targets file has {planets} planets and {fps} false positives; pass_criteria "
                    f"expects {criteria['expected_planets']} and "
                    f"{criteria['expected_false_positives']}"
                )
            keys = [t.key for t in targets.targets]
            if len(keys) != len(set(keys)):
                raise ValueError("duplicate target keys in the targets file")
        else:
            if not claim.targets:
                raise ValueError("replicate claims must list at least one target")
            if any(t["kind"] == "development" for t in claim.targets):
                raise ValueError("development targets belong only in calibration target files")

    def _validate_discover(self, loaded: LoadedClaim, discovery: dict[str, Any] | None) -> None:
        """A v0.4 discover claim: the discovery section, every test with exactly one role,
        targets in a ``targets`` attachment (controls and funnel stars only)."""
        if discovery is None:
            raise ValueError("discover claims need a test_plan.discovery section (roles)")
        claim = loaded.claim
        catalogs = loaded.attachment_by_role("eb-catalog") is not None
        expected = set(expected_tests(catalogs))
        roles = set(discovery["decisive"]) | set(discovery["diagnostic"])
        if roles != expected:
            missing = sorted(expected - roles)
            extra = sorted(roles - expected)
            raise ValueError(
                "every test of the analysis needs exactly one role"
                + (f"; without a role: {', '.join(missing)}" if missing else "")
                + (f"; not part of this analysis: {', '.join(extra)}" if extra else "")
            )
        if claim.targets:
            raise ValueError("discover claims list targets in the 'targets' attachment")
        attachment = loaded.attachment_by_role("targets")
        if attachment is None:
            raise ValueError("discover claims need an attachment with role 'targets'")
        path = loaded.attachment_path(attachment)
        if not path.is_file():
            raise ValueError(f"targets attachment not found: {attachment.path}")
        targets = load_targets_file(path).targets
        if any(t.kind == "development" for t in targets):
            raise ValueError("discover claims have no development targets")
        keys = [t.key for t in targets]
        if len(keys) != len(set(keys)):
            raise ValueError("duplicate target keys in the targets file")

    def plan_for_stage(self, test_plan: dict[str, Any], stage: int | None) -> dict[str, Any]:
        """The test plan a run of ``stage`` uses: before the last stage of a discover claim no
        target pixel file is downloaded or read (the v0.4 funnel, stage 1). Otherwise the plan
        is returned unchanged."""
        discovery = test_plan.get("discovery")
        if stage is None or discovery is None:
            return test_plan
        last = max([1, *(int(s) for s in (discovery.get("stages") or {}).values())])
        if stage >= last:
            return test_plan
        plan = TessTestPlan.model_validate(test_plan)
        plan.data.target_pixel_files = False
        return plan.model_dump(mode="json")

    def targets_for_run(self, loaded: LoadedClaim) -> list[dict[str, Any]]:
        if loaded.claim.kind == "discover":
            attachment = loaded.attachment_by_role("targets")
            assert attachment is not None
            targets = load_targets_file(loaded.attachment_path(attachment)).targets
            return [t.model_dump(mode="json") for t in targets]
        if loaded.claim.kind == "calibration":
            attachment = loaded.attachment_by_role("targets")
            assert attachment is not None
            targets = load_targets_file(loaded.attachment_path(attachment)).targets
            return [t.model_dump(mode="json") for t in targets if t.kind != "development"]
        return list(loaded.claim.targets)

    def verify_promotion(
        self, record: dict[str, Any], loaded: LoadedClaim, offline: bool = False
    ) -> list[str]:
        """Problems of a v0.4 promotion record against the claim (protocol section 7): the run
        set is the first ``n_chosen`` funnel stars in the targets file's order (the walk's)."""
        from refute.core.codehash import git_state
        from refute.packs.tess.discover.protocol import BUDGET
        from refute.packs.tess.discover.steps import promotion_problems

        n = record.get("n_chosen")
        allowed = sorted({pair[0] for pair in BUDGET.sequence})
        if n not in allowed:
            return [f"n_chosen must be one of {allowed}"]
        from refute.core.io import read_json
        from refute.core.lock import lock_path_for

        all_targets = self.targets_for_run(loaded)
        funnel = [t for t in all_targets if t.get("kind") == "exploration"]
        run_set = [self.target_key(t) for t in funnel[:n]]
        state = git_state(loaded.directory)
        if not state.is_repo or state.toplevel is None:
            return ["the promotion is verified inside the claim's git repository"]
        lock = read_json(lock_path_for(loaded.path))
        identity = {
            "claim_id": loaded.claim.id,
            "claim_sha256": loaded.sha256(),
            "code_sha256": (lock.get("code") or {}).get("sha256"),
        }
        discovery = loaded.claim.test_plan.get("discovery") or {}
        return promotion_problems(
            record,
            Path(state.toplevel),
            identity,
            run_set,
            {self.target_key(t): t for t in all_targets},
            (discovery.get("inputs") or {}).get("inputs_json"),
            offline=offline,
        )

    def is_control(self, target: dict[str, Any]) -> bool:
        """A known control of a discover claim (it runs every stage without promotion)."""
        return target.get("kind") in ("planet", "false_positive")

    def target_key(self, target: dict[str, Any]) -> str:
        return str(target["key"])
