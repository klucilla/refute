"""TESS pack claim schema: resolves ``test_plan``, ``targets`` and ``pass_criteria``."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

from refute.packs.tess.params import CalibrationCriteria, TargetsFile, TessTarget, TessTestPlan

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
            raise ValueError("replicate claims do not use pass_criteria in v0.1")
        return None

    def validate_claim(self, loaded: LoadedClaim) -> None:
        claim = loaded.claim
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

    def targets_for_run(self, loaded: LoadedClaim) -> list[dict[str, Any]]:
        if loaded.claim.kind == "calibration":
            attachment = loaded.attachment_by_role("targets")
            assert attachment is not None
            targets = load_targets_file(loaded.attachment_path(attachment)).targets
            return [t.model_dump(mode="json") for t in targets if t.kind != "development"]
        return list(loaded.claim.targets)

    def target_key(self, target: dict[str, Any]) -> str:
        return str(target["key"])
