"""The two batteries of the v0.5 calibration (docs/plans/v0.5-plan.md, section 4): the v0.4
compatibility plan is the v0.4 claim's plan unchanged; the v0.5 plan is the same plan (every
parameter of the candidate generation shared, ``paired.check_pairing``) with discovery version 2,
the ``stronger`` section at its defaults, and the roles of the S2 decisions (values.py)."""

from __future__ import annotations

import copy
from typing import Any

from refute.packs.tess.calib05.values import V05_DECISIVE, V05_DIAGNOSTIC
from refute.packs.tess.params import TessTestPlan


def v05_plan(test_plan_v04: dict[str, Any]) -> dict[str, Any]:
    """The v0.5 plan paired with a v0.4 discover plan (a dict, as in a claim)."""
    plan = copy.deepcopy(test_plan_v04)
    discovery = plan.get("discovery")
    if not discovery or int(discovery.get("version", 1)) != 1:
        raise ValueError("the v0.5 plan is built from a v0.4 discover plan (discovery version 1)")
    discovery["version"] = 2
    discovery["decisive"] = list(V05_DECISIVE)
    discovery["diagnostic"] = list(V05_DIAGNOSTIC)
    plan["stronger"] = {}
    return TessTestPlan.model_validate(plan).model_dump(mode="json")


def pair(test_plan_v04: dict[str, Any]) -> tuple[TessTestPlan, TessTestPlan]:
    """The two validated plans of a pair, checked to share the candidate generation."""
    from refute.packs.tess.discover.paired import check_pairing

    p04 = TessTestPlan.model_validate(test_plan_v04)
    p05 = TessTestPlan.model_validate(v05_plan(test_plan_v04))
    check_pairing(p04, p05)
    return p04, p05
