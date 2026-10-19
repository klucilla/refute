from pathlib import Path

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


def test_ml_pack_is_discovered_and_locks_through_its_schema():
    from refute.packs.ml.schema import MlClaimSchema

    assert available_packs()["ml"] == "refute.packs.ml:PACK"
    pack = load_pack("ml")
    assert pack.name == "ml" and isinstance(pack.schema, MlClaimSchema)
    assert isinstance(pack.schema, ClaimSchema)


@pytest.mark.parametrize(
    "call",
    [
        lambda p: p.adapter.fetch({}, {}, None),
        lambda p: p.adapter.load({}, {}, None),
        lambda p: p.search.run(None, {}),
        lambda p: p.analyzer.analyze({}, None, {}, {}, None),
        lambda p: p.exporter.export({}, None),
        lambda p: p.calibrator.evaluate(None, [], True),
    ],
)
def test_ml_pack_runs_no_paper_through_the_core(call):
    with pytest.raises(NotImplementedError, match="refute.packs.ml.production"):
        call(load_pack("ml"))


def test_an_ml_claim_locks_and_verifies_through_the_registered_pack(tmp_path):
    """The core loads an ML claim by its pack name (no pack passed), locks it and verifies
    it: the path of the main sample's locks (a synthetic claim of the schema tests)."""
    from refute.core.lock import VerifyStatus, create_lock, verify_claim
    from test_ml_schema import build_claim

    path = build_claim(tmp_path)
    record = create_lock(path, code_root=Path(__file__).resolve().parents[1])
    assert len(record["claim_sha256"]) == 64
    result = verify_claim(path, code_root=Path(__file__).resolve().parents[1])
    assert result.status == VerifyStatus.PASS, result.messages
