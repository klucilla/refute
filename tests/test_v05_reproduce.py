"""v0.5 WP8: the inputs a clone lacks (docs/plans/v0.5-acceptance.md, cases 8.1 and 8.2; #189,
#195). The core rules of refute.core.reproduce, and an offline empty-checkout reproduction of a
synthetic stage-2 dossier with every fetch served from local fixtures."""

from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from conftest import git, target_entry, targets_file, write_yaml
from refute.core.dossier import check_dossier
from refute.core.lock import create_lock
from refute.core.reproduce import (
    InputError,
    InputSpec,
    check,
    dest_problem,
    fetch_bytes,
    prepare,
    specs_problems,
)
from refute.core.run import execute_run
from refute.packs.tess.synthetic import (
    discovery_v05_plan_dict,
    scenario_data,
    write_synthetic_cache,
)

DATA = b"a frozen input of the synthetic claim\n"
SHA = hashlib.sha256(DATA).hexdigest()
DEST = f".cache/frozen/synthetic/{SHA}/frozen.txt"


# --- the destination and fetching rules ------------------------------------------------------


@pytest.mark.parametrize(
    "dest",
    [
        "",
        "/abs/.cache/frozen/x",
        ".cache/frozen",
        ".cache/frozen/../../x",
        ".cache/frozen/./x",
        ".cache\\frozen\\x",
        "C:/x",
        "//server/share/.cache/frozen/x",
        ".cache/frozen/x:stream",
        ".cache/frozen/CON.txt",
        ".cache/frozen/a b",
        "inputs/x",
    ],
)
def test_an_unsafe_destination_is_refused(dest):
    assert dest_problem(dest) is not None


def test_a_destination_inside_the_frozen_area_is_accepted():
    assert dest_problem(DEST) is None


def test_a_duplicate_destination_is_refused_whatever_its_case():
    a = InputSpec("a", SHA, "https://x", DEST)
    b = InputSpec("b", SHA, "https://x", DEST.upper().replace(".CACHE/FROZEN", ".cache/frozen"))
    assert any("duplicate" in p for p in specs_problems([a, b]))


def test_file_urls_only_under_a_fixture_root(tmp_path):
    fixture = tmp_path / "fixtures" / "f.txt"
    fixture.parent.mkdir()
    fixture.write_bytes(DATA)
    with pytest.raises(InputError, match="fixture root"):
        fetch_bytes(fixture.as_uri())
    assert fetch_bytes(fixture.as_uri(), file_root=fixture.parent) == DATA
    outside = tmp_path / "outside.txt"
    outside.write_bytes(b"x")
    with pytest.raises(InputError, match="inside the fixture root"):
        fetch_bytes(outside.as_uri(), file_root=fixture.parent)
    with pytest.raises(InputError, match="https"):
        fetch_bytes("http://example.invalid/x")


def test_prepare_installs_verified_bytes_and_never_replaces(tmp_path):
    spec = InputSpec("frozen", SHA, "fixture", DEST)
    assert check([spec], tmp_path)[0].endswith("run `refute prepare-inputs`")
    assert prepare([spec], tmp_path, fetch=lambda url: DATA) == [
        {"name": "frozen", "state": "installed"}
    ]
    assert check([spec], tmp_path) == []
    assert prepare([spec], tmp_path, fetch=lambda url: b"never read")[0]["state"] == "present"
    with pytest.raises(InputError, match="declared SHA-256"):
        prepare([InputSpec("x", SHA, "f", DEST.replace("frozen.txt", "other.txt"))], tmp_path,
                fetch=lambda url: b"wrong")  # fmt: skip
    (tmp_path / DEST).write_bytes(b"tampered")
    assert "other bytes" in check([spec], tmp_path)[0]
    with pytest.raises(InputError, match="other bytes"):
        prepare([spec], tmp_path, fetch=lambda url: DATA)


# --- 8.1 and 8.2: a stage-2 dossier reproduced in an empty checkout ---------------------------


def _claim(url: str) -> dict:
    plan = discovery_v05_plan_dict()
    plan["reproduction"] = {
        "inputs": [{"name": "synthetic frozen input", "sha256": SHA, "url": url, "dest": DEST}]
    }
    return {
        "schema_version": 1,
        "id": "synthetic-v05",
        "kind": "discover",
        "pack": "tess",
        "title": "Synthetic v0.5 claim with a declared input",
        "hypothesis": "The declared inputs make the dossier reproducible from a clone.",
        "created": "2026-11-03",
        "authors": ["Refute test suite"],
        "attachments": [{"path": "targets.yaml", "role": "targets"}],
        "test_plan": plan,
    }


@pytest.fixture
def original(git_repo: Path, tmp_path: Path):
    fixtures = tmp_path / "fixtures"
    fixtures.mkdir()
    (fixtures / "frozen.txt").write_bytes(DATA)
    url = (fixtures / "frozen.txt").as_uri()
    (git_repo / ".gitignore").write_text(".cache/\n", encoding="utf-8")
    claim_dir = git_repo / "claims"
    write_yaml(claim_dir / "targets.yaml", targets_file([target_entry(1, "planet", 3.7)]))
    claim = write_yaml(claim_dir / "claim.yaml", _claim(url))
    git(git_repo, "add", "-A")
    git(git_repo, "commit", "-q", "-m", "claim")
    create_lock(claim)
    git(git_repo, "add", "-A")
    git(git_repo, "commit", "-q", "-m", "lock")
    cache = tmp_path / "cache"
    data = scenario_data("planet")
    write_synthetic_cache(cache, 1, data.lc, data.star, aux=data.aux)
    return git_repo, claim, cache, fixtures


def _run(claim, cache, out, run_id):
    return execute_run(
        claim, mode="discover", out_dir=out, workers=1, offline=True, cache_dir=cache,
        stage=2, targets=["TIC-1"], run_id=run_id,
    )  # fmt: skip


def test_8_2_a_run_without_its_declared_input_is_refused(original, tmp_path):
    _repo, claim, cache, _fixtures = original
    refused = _run(claim, cache, tmp_path / "out", "missing")
    assert refused.exit_code == 1
    assert any("declared inputs" in m and "prepare-inputs" in m for m in refused.messages)
    assert not (tmp_path / "out" / "missing").exists()


def test_8_1_and_8_2_the_dossier_is_reproduced_in_an_empty_checkout(original, tmp_path):
    repo, claim, cache, fixtures = original
    from_fixtures = lambda url: fetch_bytes(url, file_root=fixtures)  # noqa: E731
    spec = [InputSpec("synthetic frozen input", SHA, (fixtures / "frozen.txt").as_uri(), DEST)]
    prepare(spec, repo, fetch=from_fixtures)
    first = _run(claim, cache, tmp_path / "out", "original")
    assert first.exit_code == 0, first.messages
    dossier = first.run_dir / "TIC-1"
    reproduce = (dossier / "REPRODUCE.md").read_text(encoding="utf-8")
    # 8.1: every input a clone lacks, with its fetch-and-verify step
    assert "Inputs this clone lacks" in reproduce
    assert SHA in reproduce and DEST in reproduce and "frozen.txt" in reproduce
    assert "uv run refute prepare-inputs" in reproduce
    assert reproduce.index("uv run refute prepare-inputs") < reproduce.index("uv run refute verify")

    # 8.2: an empty checkout, the instructions followed with the fixtures only
    clone = tmp_path / "clone"
    subprocess.run(["git", "clone", "-q", str(repo), str(clone)], check=True)
    cloned_claim = clone / "claims" / "claim.yaml"
    assert not (clone / ".cache").exists()
    refused = _run(cloned_claim, cache, tmp_path / "repro", "refused")
    assert refused.exit_code == 1
    prepare(spec, clone, fetch=from_fixtures)
    again = _run(cloned_claim, cache, tmp_path / "repro", "repro")
    assert again.exit_code == 0, again.messages
    result = check_dossier(again.run_dir / "TIC-1", against=dossier)
    assert result.integrity_problems == [] and result.differences == []


def test_8_1_a_claim_without_inputs_keeps_its_reproduce_text():
    from refute.core.run import TargetTask, reproduce_markdown

    context = {
        "mode": "replicate",
        "claim_id": "c",
        "claim_sha256": "a" * 64,
        "code_sha256": "b" * 64,
        "run_git_commit": "abc",
    }
    task = TargetTask("tess", {}, "TIC-1", {}, context, "", "", "c.yaml", b"", b"", {}, (), {})
    text = reproduce_markdown(task)
    assert "locked code hash)\n\n```bash\n" in text
    assert "uv sync --frozen\nuv run refute verify" in text
    assert "prepare-inputs" not in text
    with_empty = reproduce_markdown(
        TargetTask(
            "tess",
            {},
            "TIC-1",
            {},
            {**context, "reproduction_inputs": []},
            "",
            "",
            "c.yaml",
            b"",
            b"",
            {},
            (),
            {},
        )  # fmt: skip
    )
    assert with_empty == text
