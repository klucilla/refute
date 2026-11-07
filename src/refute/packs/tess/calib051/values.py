"""The values of the v0.5.1 calibration that the plan fixes before the protocol
(docs/plans/v0.5.1-plan.md, sections 5 and 6: "fixed now as minimums, with no cost-based
fallback"). They are code, so the lock's code hash covers them. The protocol's own values (pools,
rounds, replacement and corrupted-run rules) are added after its approval."""

from __future__ import annotations

from dataclasses import dataclass, field

from refute.packs.tess.calib05.values import C1 as C1_V05
from refute.packs.tess.calib05.values import V05_DECISIVE, V05_DIAGNOSTIC
from refute.packs.tess.calib05.values import C3Values as C3ValuesV05

PROTOCOL_ID = "refute-tess-v0.5.1-calibration"
STEP_DIR = "calibration/v0.5.1"


@dataclass(frozen=True)
class C1Values:
    """C1': the v0.5 generator, families and sizes (200 per family, 100 for PA and PX: 2,400
    curves); the v0.5 halving rule is not used (plan, section 6)."""

    sizes: dict[str, int] = field(default_factory=lambda: dict(C1_V05.sizes))
    seed_prefix: str = "refute-v051-c1"
    development_prefix: str = "refute-v051-c1-dev"
    not_decidable_below: int = C1_V05.not_decidable_below


@dataclass(frozen=True)
class C2Values:
    """C2': 50 new stars, 3 transformed curves per star, 10 injections per curve (the v0.4
    grid); T2a, T2b, T2c with their v0.5 definitions (plan, sections 5 and 6)."""

    stars: int = 50
    transformed_per_star: int = 3
    injections_per_curve: int = 10
    t2a_margin: float = 0.10
    not_decidable_below: int = 20


# C3': 8 confirmed planets and 8 TESS-EB false positives, 3 ordered reserves per pool, as in v0.5
# (plan, section 6), with v0.5's identity tolerances and retry rule; T3a and T3b as in v0.5.
C3Values = C3ValuesV05

C1 = C1Values()
C2 = C2Values()
C3 = C3Values()

# The roles of the version-3 battery: every test of the v0.5 battery keeps its role (acceptance
# row 5.1). The diagnostic `duration_excess` (plan, amendment 4) gets its role when it is built,
# before the freeze; the rehearsal runs again then.
V051_DECISIVE = tuple(V05_DECISIVE)
V051_DIAGNOSTIC = tuple(V05_DIAGNOSTIC)

if sum(C1.sizes.values()) != 2400:
    raise ValueError("plan, section 6: C1' has 2,400 curves")
