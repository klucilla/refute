"""TESS exoplanet-transit domain pack (gauntlet v0.1).

Exposed to the engine through the ``refute.packs`` entry point as ``PACK``.
Importing this module does not import lightkurve; the adapter imports it only
when data are fetched or read.
"""

from __future__ import annotations

from refute.core.pack import DomainPack
from refute.packs.tess.adapter import TessAdapter
from refute.packs.tess.calibration import TessCalibrator
from refute.packs.tess.exporter import CtoiExporter
from refute.packs.tess.pipeline import TessAnalyzer, TessGauntlet, TessHoldout, TessSearch
from refute.packs.tess.schema import TessClaimSchema

__all__ = ["PACK"]

PACK = DomainPack(
    name="tess",
    version="0.1.0",
    description="TESS SPOC 2-min transits: BLS search, gauntlet v0.1, blind holdout by year",
    schema=TessClaimSchema(),
    adapter=TessAdapter(),
    search=TessSearch(),
    gauntlet=TessGauntlet(),
    holdout=TessHoldout(),
    exporter=CtoiExporter(),
    analyzer=TessAnalyzer(),
    calibrator=TessCalibrator(),
)
