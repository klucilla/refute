import pytest

from refute.core.pack import (
    Analyzer,
    Calibrator,
    ClaimSchema,
    DataAdapter,
    DomainPack,
    Exporter,
    Gauntlet,
    HoldoutStrategy,
    PackError,
    Search,
    available_packs,
    load_pack,
)


def test_tess_pack_is_discovered_through_entry_points():
    assert available_packs()["tess"] == "refute.packs.tess:PACK"
    pack = load_pack("tess")
    assert isinstance(pack, DomainPack)
    assert pack.name == "tess"


def test_tess_pack_implements_every_interface():
    pack = load_pack("tess")
    assert isinstance(pack.schema, ClaimSchema)
    assert isinstance(pack.adapter, DataAdapter)
    assert isinstance(pack.search, Search)
    assert isinstance(pack.gauntlet, Gauntlet)
    assert isinstance(pack.holdout, HoldoutStrategy)
    assert isinstance(pack.exporter, Exporter)
    assert isinstance(pack.analyzer, Analyzer)
    assert isinstance(pack.calibrator, Calibrator)


def test_unknown_pack():
    with pytest.raises(PackError, match="unknown domain pack"):
        load_pack("does-not-exist")


def test_engine_core_does_not_import_astronomy_code():
    import subprocess
    import sys

    code = (
        "import sys, refute.core.claim, refute.core.lock, refute.core.run, refute.core.dossier;"
        "bad=[m for m in ('astropy','lightkurve','refute.packs.tess') if m in sys.modules];"
        "print(','.join(bad))"
    )
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True)
    assert out.stdout.strip() == ""
