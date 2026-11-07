"""The two batteries of the v0.5.1 calibration (plan, section 6): the v0.4 compatibility plan is
the v0.4 claim's plan unchanged; the version-3 plan is the same plan (every parameter of the
candidate generation shared, ``paired.check_pairing``) with discovery version 3, the roles of
``values.py``, the ``stronger`` section and the ``v051`` section at their defaults."""

from __future__ import annotations

import copy
from typing import Any

from refute.packs.tess.calib051.values import V051_DECISIVE, V051_DIAGNOSTIC
from refute.packs.tess.params import TessTestPlan


def v051_plan(test_plan_v04: dict[str, Any]) -> dict[str, Any]:
    """The version-3 plan paired with a v0.4 discover plan (a dict, as in a claim)."""
    plan = copy.deepcopy(test_plan_v04)
    discovery = plan.get("discovery")
    if not discovery or int(discovery.get("version", 1)) != 1:
        raise ValueError("the version-3 plan is built from a v0.4 discover plan (version 1)")
    discovery["version"] = 3
    discovery["decisive"] = list(V051_DECISIVE)
    discovery["diagnostic"] = list(V051_DIAGNOSTIC)
    plan["stronger"] = {}
    plan["v051"] = {}
    return TessTestPlan.model_validate(plan).model_dump(mode="json")


def pair(test_plan_v04: dict[str, Any]) -> tuple[TessTestPlan, TessTestPlan]:
    """The two validated plans of a pair, checked to share the candidate generation."""
    from refute.packs.tess.discover.paired import check_pairing

    p04 = TessTestPlan.model_validate(test_plan_v04)
    p51 = TessTestPlan.model_validate(v051_plan(test_plan_v04))
    if not p51.is_v051:
        raise ValueError("the paired plan is not a version-3 plan")
    check_pairing(p04, p51)
    return p04, p51
