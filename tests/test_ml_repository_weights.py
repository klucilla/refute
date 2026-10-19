"""Weights that are a file of the pinned commit
(docs/validation/v0.3/wp3-repository-weights-acceptance.md), offline: the schema on the
claim of test_ml_schema, the verification and the mounts of production on a local Git
repository, and the runs on the cataloged synthetic paper of test_ml_integration."""

from __future__ import annotations

import dataclasses
import hashlib

import pytest

import test_ml_schema as tsch
from conftest import git
from refute.core.claim import ClaimError
from refute.core.verdict import PaperVerdict, TestStatus
from refute.packs.ml import integration as ig
from refute.packs.ml import production as prod
from refute.packs.ml.schema import MlClaimSchema, MlTarget, MlTestPlan
from test_ml_integration import ARXIV, CONFIG, DATA, Paper, checks, plan_dict, value_target
from test_ml_production import LIMITS, TIMING, _built, _count_setup, _env_record

CKPT = b"\x80\x02a frozen predictor" * 64


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def repo_weights(commit: str, path: str = "saved/m.pth", data: bytes = CKPT, name="ckpt"):
    return {
        "name": name,
        "origin": "repository_file",
        "path": path,
        "commit": commit,
        "sha256": sha(data),
        "size_bytes": len(data),
        "license": "MIT-0 (the repository's LICENSE)",
    }


EXTERNAL = {
    "name": "w1",
    "url": "https://example.org/w1.pt",
    "reference": "a pre-trained model",
    "version": "1",
    "license": "MIT",
    "retrieved_utc": "2026-10-15T00:00:00Z",
    "sha256": "a" * 64,
    "size_bytes": 10,
    "local_copy_allowed": True,
}


# ---- the schema ------------------------------------------------------------------------------


def _with_weights(entry=None, name="ckpt"):
    def mutate(claim):
        claim["test_plan"]["weights"] = [entry or repo_weights(tsch.COMMIT)]
        tsch.target(claim, "c1")["weights"] = name

    return mutate


def test_a_repository_weights_entry_validates_and_keeps_its_fields(tmp_path):
    loaded = tsch.load(tmp_path, _with_weights())
    (entry,) = loaded.claim.test_plan["weights"]
    assert entry == repo_weights(tsch.COMMIT)


def test_a_downloaded_weights_entry_keeps_its_bytes():
    plan = tsch.test_plan()
    plan["weights"] = [dict(EXTERNAL)]
    dumped = MlTestPlan.model_validate(plan).model_dump(mode="json", by_alias=True)
    assert dumped["weights"] == [EXTERNAL]  # no origin written


@pytest.mark.parametrize(
    "path", ["/abs/m.pth", "../m.pth", "saved\\m.pth", ".refute/m.pth", "C:/m.pth", "."]
)
def test_a_weights_path_that_is_not_a_file_of_the_tree_is_refused(tmp_path, path):
    with pytest.raises(ClaimError, match="path"):
        tsch.load(tmp_path, _with_weights(repo_weights(tsch.COMMIT, path=path)))


def test_weights_of_another_commit_are_refused(tmp_path):
    with pytest.raises(ClaimError, match="repository.commit"):
        tsch.load(tmp_path, _with_weights(repo_weights("9" * 40)))


@pytest.mark.parametrize("alias", ["data/graph.bin", "data//graph.bin", "data/./graph.bin"])
def test_two_repository_files_with_one_path_are_refused(alias):
    plan = tsch.test_plan()
    plan["datasets"].append(
        {
            "name": "graph",
            "origin": "repository_file",
            "path": "data/graph.bin",
            "sha256": "b" * 64,
            "size_bytes": 5,
            "splits": {"all": {"expected_examples": 5, "source": "reader:lines:rows"}},
        }
    )
    plan["weights"] = [repo_weights(tsch.COMMIT, path=alias)]
    with pytest.raises(ValueError, match="shares its path"):
        MlTestPlan.model_validate(plan)
    # two weights entries with one path, through an alias
    plan["datasets"].pop()
    plan["weights"].append(repo_weights(tsch.COMMIT, path="data/graph.bin", name="other"))
    with pytest.raises(ValueError, match="shares its path"):
        MlTestPlan.model_validate(plan)
    # two dataset entries may still name one file (2302.12465's two names)
    plan["weights"] = []
    entry = {
        "origin": "repository_file",
        "path": "data/graph.bin",
        "sha256": "b" * 64,
        "size_bytes": 5,
        "splits": {"all": {"expected_examples": 5, "source": "reader:lines:rows"}},
    }
    plan["datasets"] += [{**entry, "name": "one"}, {**entry, "name": "two"}]
    MlTestPlan.model_validate(plan)


LISTED = [{"path": "saved/m.pth", "sha256": sha(CKPT)}]


def _counted_c1(tmp_path, monkeypatch, configuration, name="ckpt", weights=LISTED):
    """c1 measures a population counted before the lock and names the repository's
    weights; the inventory transcribes that split. ``weights`` is the record's field (absent
    when None)."""
    monkeypatch.setitem(tsch.TRANSCRIPTIONS["c1"], "split", "selected")
    record = tsch.count_record(configuration=configuration)
    if weights is not None:
        record["weights"] = weights
    count = tsch.with_count(tmp_path, record)

    def mutate(claim):
        count(claim)
        claim["test_plan"]["weights"] = [repo_weights(tsch.COMMIT)]
        c1 = tsch.target(claim, "c1")
        c1["weights"] = name
        c1["metric"]["split"] = "selected"
        c1["metric"]["n_examples"] = 77
        identity = c1["coverage_evidence"]["method"]["split_identity"]
        identity["other_splits"] = [
            {"name": "train", "labels_sha256": tsch.OTHER_LABELS_SHA256},
            {"name": "test", "labels_sha256": "c" * 64},
        ]

    return tsch.load(tmp_path, mutate)


def test_a_count_record_listing_the_weights_binds_them(tmp_path, monkeypatch):
    _counted_c1(tmp_path, monkeypatch, LISTED)


@pytest.mark.parametrize(
    "configuration",
    [
        [],
        [{"path": "saved/m.pth", "sha256": "0" * 64}],
        [{"path": "conf/c.yaml", "sha256": sha(CKPT)}],
    ],
)
def test_a_count_record_without_the_weights_is_refused(tmp_path, monkeypatch, configuration):
    with pytest.raises(ClaimError, match="does not list the weights.*configuration"):
        _counted_c1(tmp_path, monkeypatch, configuration)


@pytest.mark.parametrize(
    "weights", [None, [], [{"path": "saved/m.pth", "sha256": "0" * 64}], "saved/m.pth"]
)
def test_a_count_that_did_not_mount_the_verified_weights_is_refused(tmp_path, monkeypatch, weights):
    """A spec without weights lets the count read the tree's file: its record names no
    verified weights, and the claim does not bind (Codex review, round 2)."""
    with pytest.raises(ClaimError, match="does not list the weights.*in its weights"):
        _counted_c1(tmp_path, monkeypatch, LISTED, weights=weights)


# ---- production: verified after the checkout -------------------------------------------------


def _clone(tmp_path):
    repo = tmp_path / "clone"
    (repo / "saved").mkdir(parents=True)
    git(repo, "init", "-q")
    (repo / "saved" / "m.pth").write_bytes(CKPT)
    (repo / "train.py").write_text("print(1)\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "c")
    return repo, git(repo, "rev-parse", "HEAD").strip()


def _verify(tmp_path, repo, commit, **entry):
    plan = {"repository": {"commit": commit}, "weights": [repo_weights(commit, **entry)]}
    return prod.repository_weights(repo, plan, tmp_path / "cache")["ckpt"]


def test_repository_weights_are_copied_checked_and_kept_apart_from_the_clone(tmp_path):
    repo, commit = _clone(tmp_path)
    evidence = _verify(tmp_path, repo, commit)
    assert evidence.reason is None and evidence.rel == "saved/m.pth"
    assert evidence.copy.parent == tmp_path / "cache" / "repository-files"
    assert evidence.copy.read_bytes() == CKPT
    (repo / "saved" / "m.pth").write_bytes(b"changed by a build")
    assert evidence.copy.read_bytes() == CKPT


@pytest.mark.parametrize(
    ("case", "reason"),
    [
        ("other bytes", prod.OTHER_BYTES),
        ("missing", "missing"),
        ("untracked", "not a regular file of the commit's tree"),
        ("git", "not a regular file of the commit's tree"),
        ("folder", "not a regular file of the commit's tree"),
        ("outside", "outside the clone"),
    ],
)
def test_repository_weights_that_do_not_verify_have_no_copy(tmp_path, case, reason):
    repo, commit = _clone(tmp_path)
    entry = {}
    if case == "other bytes":
        (repo / "saved" / "m.pth").write_bytes(CKPT + b"x")
        entry = {"data": CKPT}
    elif case == "missing":
        (repo / "saved" / "m.pth").unlink()
    elif case == "untracked":
        (repo / "saved" / "u.pth").write_bytes(CKPT)
        entry = {"path": "saved/u.pth"}
    elif case == "git":
        data = (repo / ".git" / "HEAD").read_bytes()
        entry = {"path": ".git/HEAD", "data": data}
    elif case == "folder":
        entry = {"path": "saved"}
    else:
        (tmp_path / "m.pth").write_bytes(CKPT)
        entry = {"path": "../m.pth"}
    evidence = _verify(tmp_path, repo, commit, **entry)
    assert evidence.copy is None and evidence.reason == reason


def test_repository_weights_reached_through_a_link_have_no_copy(tmp_path):
    repo, commit = _clone(tmp_path)
    try:
        (repo / "linked").symlink_to(repo / "saved", target_is_directory=True)
    except OSError:
        pytest.skip("symbolic links cannot be created here")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "a link")
    commit = git(repo, "rev-parse", "HEAD").strip()
    evidence = _verify(tmp_path, repo, commit, path="linked/m.pth")
    assert evidence.copy is None and evidence.reason == "reached through a link"


def test_a_cache_reached_through_a_link_gives_no_copy(tmp_path):
    repo, commit = _clone(tmp_path)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (tmp_path / "cache").mkdir()
    try:
        (tmp_path / "cache" / "repository-files").symlink_to(elsewhere, target_is_directory=True)
    except OSError:
        pytest.skip("symbolic links cannot be created here")
    evidence = _verify(tmp_path, repo, commit)
    assert evidence.copy is None and "link" in evidence.reason


def test_a_temporary_copy_already_in_the_cache_is_never_written_through(tmp_path):
    repo, commit = _clone(tmp_path)
    folder = tmp_path / "cache" / "repository-files"
    folder.mkdir(parents=True)
    partial = folder / f".{sha(CKPT)}.partial"
    partial.write_bytes(b"left by an earlier run")
    evidence = _verify(tmp_path, repo, commit)
    assert evidence.copy is None and evidence.reason == "a partial copy is in the cache"
    assert partial.read_bytes() == b"left by an earlier run"
    partial.unlink()
    target = tmp_path / "elsewhere.bin"
    target.write_bytes(b"not to be written")
    try:
        partial.symlink_to(target)
    except OSError:
        pytest.skip("symbolic links cannot be created here")
    evidence = _verify(tmp_path, repo, commit)
    assert evidence.copy is None and evidence.reason == prod.LINKED_CACHE
    assert target.read_bytes() == b"not to be written"


def test_a_cache_below_a_linked_folder_gives_no_copy(tmp_path):
    repo, commit = _clone(tmp_path)
    real = tmp_path / "real"
    real.mkdir()
    try:
        (tmp_path / "linked").symlink_to(real, target_is_directory=True)
    except OSError:
        pytest.skip("symbolic links cannot be created here")
    plan = {"repository": {"commit": commit}, "weights": [repo_weights(commit)]}
    out = prod.repository_weights(repo, plan, tmp_path / "linked" / "cache")["ckpt"]
    assert out.copy is None and out.reason == prod.LINKED_CACHE


def test_a_cache_path_with_a_parent_component_gives_no_copy(tmp_path):
    """'..' is refused before any normalization, which would hide a link before it
    (Codex review, round 3)."""
    repo, commit = _clone(tmp_path)
    (tmp_path / "a").mkdir()
    plan = {"repository": {"commit": commit}, "weights": [repo_weights(commit)]}
    out = prod.repository_weights(repo, plan, tmp_path / "a" / ".." / "cache")["ckpt"]
    assert out.copy is None and out.reason == prod.LINKED_CACHE
    assert not (tmp_path / "cache").exists()


def test_weights_from_outside_are_not_read(tmp_path):
    plan = {"repository": {"commit": "a" * 40}, "weights": [dict(EXTERNAL)]}
    # no Git call: the folder is not a repository
    assert prod.repository_weights(tmp_path, plan, tmp_path / "cache") == {}


def test_prepare_inputs_verifies_the_weights_after_the_checkout(tmp_path, monkeypatch):
    repo, commit = _clone(tmp_path)
    monkeypatch.setattr(prod.repository, "clone", lambda url, dest: repo)
    monkeypatch.setattr(prod.repository, "checkout", lambda r, c: None)
    plan = {**plan_dict(DATA), "datasets": [], "weights": [repo_weights(commit)]}
    plan["repository"] = {**plan["repository"], "commit": commit}
    _, datasets, weights = prod.prepare_inputs({"test_plan": plan}, tmp_path, tmp_path / "cache")
    assert datasets == {} and weights["ckpt"].copy.read_bytes() == CKPT


# ---- production: the mounts --------------------------------------------------------------------


def _setup(tmp_path, repo, weights, layout=None):
    return prod.PaperSetup(
        "p1", tmp_path / "run", repo, {}, layout or {}, LIMITS, TIMING, repository_weights=weights
    )


IDS = [
    "setup/build/requirements_compiled",
    ig.READER_PREFIX + "graph",
    "k1/base/s0",
    "k1/seeds/s5",
]


def test_the_runs_mount_the_verified_weights_and_the_build_and_readers_do_not(
    tmp_path, monkeypatch
):
    repo, commit = _clone(tmp_path)
    evidence = _verify(tmp_path, repo, commit)
    setup = _setup(tmp_path, repo, {"ckpt": evidence})
    monkeypatch.setattr(ig, "plan_container_ids", lambda cf: IDS)
    ws = prod.prepare_workspaces(setup, {"test_plan": {"datasets": []}})
    for run in ("k1/base/s0", "k1/seeds/s5"):
        assert not (ws[run] / "saved" / "m.pth").exists()  # left for the mount
        assert (ws[run] / "train.py").is_file()
    build = ws["setup/build/requirements_compiled"]
    assert (build / "saved" / "m.pth").read_bytes() == CKPT  # its copy of the tree
    reader = ws[ig.READER_PREFIX + "graph"]
    assert [p.name for p in reader.rglob("*") if p.is_file()] == [prod.READER_SCRIPT]
    mount = (str(evidence.copy.resolve()), "saved/m.pth")
    assert prod.data_mounts(setup) == (mount,)
    assert prod.data_mounts(setup, weights=False) == ()
    # a build that rewrites the file in its own folder never reaches the runs' source
    (build / "saved" / "m.pth").write_bytes(b"rewritten by the build")
    assert evidence.copy.read_bytes() == CKPT


def test_unverified_weights_are_not_mounted(tmp_path, monkeypatch):
    repo, commit = _clone(tmp_path)
    evidence = ig.WeightsEvidence("saved/m.pth", sha(CKPT), None, "missing")
    setup = _setup(tmp_path, repo, {"ckpt": evidence})
    monkeypatch.setattr(ig, "plan_container_ids", lambda cf: ["k1/base/s0"])
    ws = prod.prepare_workspaces(setup, {"test_plan": {"datasets": []}})
    assert (ws["k1/base/s0"] / "saved" / "m.pth").is_file() and prod.data_mounts(setup) == ()


@pytest.mark.parametrize("alias", ["saved/m.pth", "saved//m.pth", "saved/./m.pth"])
def test_a_weights_file_that_is_also_a_data_path_is_refused(tmp_path, monkeypatch, alias):
    repo, commit = _clone(tmp_path)
    setup = _setup(tmp_path, repo, {"ckpt": _verify(tmp_path, repo, commit)}, {"d": alias})
    monkeypatch.setattr(ig, "plan_container_ids", lambda cf: ["k1/base/s0"])
    with pytest.raises(prod.ProductionError, match="also a data path"):
        prod.prepare_workspaces(setup, {"test_plan": {"datasets": []}})


def _two_names(tmp_path, data=b"1 2\n3 4\n"):
    """Two dataset entries naming one file of the repository (2302.12465's two names)."""
    repo = tmp_path / "plain"
    (repo / "data").mkdir(parents=True)
    (repo / "data" / "graph.txt").write_bytes(data)
    entry = {
        "origin": "repository_file",
        "path": "data/graph.txt",
        "sha256": sha(data),
        "size_bytes": len(data),
        "splits": {"all": {"expected_examples": 2, "source": "reader:lines:rows"}},
    }
    entries = [{**entry, "name": "one"}, {**entry, "name": "two"}]
    evidence = {e["name"]: prod.repository_file(repo, e, tmp_path / "cache") for e in entries}
    layout = {"one": "data/graph.txt", "two": "data/graph.txt"}
    setup = prod.PaperSetup("p1", tmp_path / "run", repo, evidence, layout, LIMITS, TIMING)
    return setup, {"test_plan": {"datasets": entries}}


def test_a_file_two_dataset_entries_name_is_prepared_and_mounted_once(tmp_path, monkeypatch):
    setup, claim_file = _two_names(tmp_path)
    monkeypatch.setattr(ig, "plan_container_ids", lambda cf: ["k1/base/s0"])
    ws = prod.prepare_workspaces(setup, claim_file)  # no error on the second name
    assert not (ws["k1/base/s0"] / "data" / "graph.txt").exists()
    copy = setup.datasets["one"].fetch.path
    assert prod.data_mounts(setup) == ((str(copy.resolve()), "data/graph.txt"),)


def test_two_different_files_for_one_path_are_refused(tmp_path):
    setup, _ = _two_names(tmp_path)
    other = tmp_path / "other.txt"
    other.write_bytes(b"5 6\n")
    fetch = dataclasses.replace(setup.datasets["two"].fetch, path=other)
    datasets = {**setup.datasets, "two": dataclasses.replace(setup.datasets["two"], fetch=fetch)}
    setup = dataclasses.replace(setup, datasets=datasets)
    with pytest.raises(prod.ProductionError, match="two different files are mounted"):
        prod.data_mounts(setup)


def test_no_patch_may_touch_the_weights(tmp_path, monkeypatch):
    seen = {}

    def prepare(clone, dest, patches, data_paths, entries):
        seen["data_paths"] = data_paths
        return {}

    monkeypatch.setattr(prod.repository, "ls_tree", lambda repo, commit: "")
    monkeypatch.setattr(prod.pt, "prepare", prepare)
    plan = {**plan_dict(DATA), "weights": [repo_weights("a" * 40), dict(EXTERNAL)]}
    plan["build"] = {**plan["build"], "allowed_patches": []}
    prod.patch_tree({"test_plan": plan}, tmp_path, tmp_path / "patched", {}, {})
    assert "saved/m.pth" in seen["data_paths"]


def test_the_setup_records_each_repository_weights_entry(tmp_path):
    ok = ig.WeightsEvidence("saved/m.pth", sha(CKPT), tmp_path / "copy")
    bad = ig.WeightsEvidence("saved/n.pth", "b" * 64, None, "missing")
    record = _setup(tmp_path, tmp_path, {"ok": ok, "bad": bad}).record()
    assert record["repository_weights"] == {
        "bad": {"path": "saved/n.pth", "sha256": "b" * 64, "verified": False,
                "mount_planned": False, "reason": "missing"},
        "ok": {"path": "saved/m.pth", "sha256": sha(CKPT), "verified": True,
               "mount_planned": True, "reason": None},
    }  # fmt: skip
    assert record["weights"] is None
    assert _setup(tmp_path, tmp_path, {}).record()["repository_weights"] is None


def test_a_mounted_copy_other_than_the_counts_stops_the_paper(tmp_path):
    setup = _count_setup(tmp_path)
    _built(tmp_path, "requirements_compiled")
    copy = tmp_path / "copy"
    copy.write_bytes(b"other bytes")
    evidence = ig.WeightsEvidence("conf/c.yaml", sha(b"conf"), copy)
    setup = dataclasses.replace(setup, repository_weights={"ckpt": evidence})
    with pytest.raises(prod.ProductionError, match="mounted conf/c.yaml differs"):
        prod.check_counted_environment(setup, [_env_record()])
    copy.write_bytes(b"conf")
    prod.check_counted_environment(setup, [_env_record()])


# ---- the runs ----------------------------------------------------------------------------------


def _paper(tmp_path, names, evidence):
    """One claim per entry of ``names`` (a weights name or None) on the synthetic paper,
    with a repository entry ckpt and an external entry w1 declared."""
    plan = plan_dict(DATA)
    plan["weights"] = [repo_weights(plan["repository"]["commit"]), dict(EXTERNAL)]
    plan_model = MlTestPlan.model_validate(plan)
    targets = []
    for i, name in enumerate(names, start=1):
        target = value_target({})
        target["key"] = f"arXiv-{ARXIV}v1-C{i}"
        if name is not None:
            target["weights"] = name  # full_training with a pre-trained input
        model = MlTarget.model_validate(target)
        targets.append(MlClaimSchema._derive(plan_model, model, model.resolved()))  # noqa: SLF001
    claim_file = {
        "test_plan": plan_model.model_dump(mode="json", by_alias=True),
        "targets": targets,
    }
    paper = Paper(tmp_path, claim_file, CONFIG)
    paper.harness = dataclasses.replace(paper.harness, weights=evidence)
    return paper


def _verified(tmp_path):
    copy = tmp_path / "ckpt-copy"
    copy.write_bytes(CKPT)
    return {"ckpt": ig.WeightsEvidence("saved/m.pth", sha(CKPT), copy)}


def test_a_claim_on_verified_repository_weights_runs_and_external_ones_still_do_not(tmp_path):
    outcome = _paper(tmp_path, ["ckpt", "w1"], _verified(tmp_path)).run()
    first, _ = checks(outcome, f"arXiv-{ARXIV}v1-C1")
    second, base = checks(outcome, f"arXiv-{ARXIV}v1-C2")
    assert first.verdict.verdict is PaperVerdict.REPRODUCED, first.verdict.reason
    assert base["run_completed"].message.startswith(ig.NOT_RUN_WEIGHTS)
    assert second.verdict.verdict is PaperVerdict.INCONCLUSIVE


def test_unverified_repository_weights_block_only_the_claims_that_name_them(tmp_path):
    evidence = {"ckpt": ig.WeightsEvidence("saved/m.pth", sha(CKPT), None, prod.OTHER_BYTES)}
    outcome = _paper(tmp_path, ["ckpt", None], evidence).run()
    first, base = checks(outcome, f"arXiv-{ARXIV}v1-C1")
    second, _ = checks(outcome, f"arXiv-{ARXIV}v1-C2")
    gate = base["run_completed"]
    assert gate.status is TestStatus.INCONCLUSIVE
    assert gate.message.startswith("not run: the repository's weights ckpt were not verified")
    assert prod.OTHER_BYTES in gate.message
    assert first.verdict.verdict is PaperVerdict.INCONCLUSIVE
    assert "artifact" not in str(first.verdict.reason).lower()
    steps = [s for s in outcome.run.steps if s.claim == f"arXiv-{ARXIV}v1-C1"]
    assert steps and all(not s.containers for s in steps)
    assert second.verdict.verdict is PaperVerdict.REPRODUCED, second.verdict.reason
    assert outcome.run.accounting_valid


def test_the_reason_not_to_run_reads_the_origin_and_the_evidence():
    plan = {
        "weights": [repo_weights("a" * 40), dict(EXTERNAL)],
        "datasets": [
            {"name": "d", "origin": "downloaded"},
            {"name": "g_repo", "origin": "generated", "inputs": ["ckpt"]},
            {"name": "g_out", "origin": "generated", "inputs": ["ckpt", "w1"]},
        ],
    }
    ok = {"ckpt": ig.WeightsEvidence("saved/m.pth", sha(CKPT), "copy")}
    assert ig.not_run_reason({"dataset": "d", "weights": "ckpt"}, plan, ok) is None
    assert ig.not_run_reason({"dataset": "g_repo"}, plan, ok) is None
    assert ig.not_run_reason({"dataset": "g_out"}, plan, ok) == ig.NOT_RUN_WEIGHTS
    assert ig.not_run_reason({"dataset": "d", "weights": "w1"}, plan, ok) == ig.NOT_RUN_WEIGHTS
    assert ig.not_run_reason({"dataset": "d"}, plan, ok) is None
    missing = ig.not_run_reason({"dataset": "d", "weights": "ckpt"}, plan, {})
    assert missing == "not run: the repository's weights ckpt were not verified (not read)"
    assert not ig.needs_weights({"dataset": "g_repo"}, plan)
