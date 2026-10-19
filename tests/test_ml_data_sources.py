"""Data sources, evaluated populations and host readers of the ML pack
(docs/validation/v0.3/wp3-data-sources-acceptance.md, sections 1 to 4.1 and the cases of
section 6), offline: schema cases on the claim of test_ml_schema, run cases on the cataloged
synthetic paper of test_ml_integration."""

from __future__ import annotations

import dataclasses
import hashlib
import io
import json
import os
import pickle
import subprocess
import sys
import tarfile
import zipfile

import pytest

from refute.core.claim import ClaimError
from refute.core.paper import FailureCause
from refute.core.verdict import PaperVerdict, TestStatus
from refute.packs.ml import integration as ig
from refute.packs.ml import production as prod
from refute.packs.ml import readers as rd
from refute.packs.ml import sandbox as sb
from refute.packs.ml.schema import MlClaimSchema, MlTarget, MlTestPlan, verify_derived
from synthetic_harness import fixture
from test_ml_integration import (
    CONFIG,
    DATA,
    KEY,
    SPLITS,
    Paper,
    _cite,
    checks,
    dataset_evidence,
    plan_dict,
    value_target,
)
from test_ml_schema import load

GEN_CITE = {"file": "src/gen.py", "lines": [1, 20], "role": "generates the data"}
DERIVED_CITE = {"file": "src/data.py", "lines": [5, 9], "role": "cuts the population"}
EXEMPT = {"data_present": "generated_by_repository_code"}


def generated(name="cifar10", sizes=(("train", 50000), ("test", 10000)), inputs=()):
    return {
        "name": name,
        "origin": "generated",
        "generator": [dict(GEN_CITE)],
        "configuration": "configs/gen.yaml, --n 60000",
        "inputs": list(inputs),
        "splits": {
            s: {"expected_examples": n, "unit": "sample", "source": "paper, section 4"}
            for s, n in sizes
        },
    }


def with_datasets(*datasets):
    def mutate(claim):
        claim["test_plan"]["datasets"] = list(datasets)

    return mutate


def chain(*mutations):
    def mutate(claim):
        for m in mutations:
            m(claim)

    return mutate


# ---- schema: origins (section 1) -------------------------------------------------------------


def test_an_existing_claim_writes_no_new_field(tmp_path):
    claim = load(tmp_path).canonical()
    (dataset,) = claim["test_plan"]["datasets"]
    assert "origin" not in dataset and "derived_splits" not in dataset
    assert all("not_applicable" not in t for t in claim["targets"])
    assert all("data_present" in t["coverage_minimum"] for t in claim["targets"])


def test_generated_data_resolve_with_the_exemption_written_by_the_resolution(tmp_path):
    claim = load(tmp_path, with_datasets(generated())).canonical()
    for t in claim["targets"]:
        assert t["not_applicable"] == EXEMPT
        assert "data_present" not in t["coverage_minimum"]
        assert "environment_build" in t["coverage_minimum"]
    verify_derived(claim)


def test_the_exemption_written_by_hand_is_refused(tmp_path):
    def hand(claim):
        claim["targets"][0]["not_applicable"] = dict(EXEMPT)

    with pytest.raises(ClaimError, match="never by hand"):
        load(tmp_path, chain(with_datasets(generated()), hand))


def test_the_exemption_written_by_hand_on_downloaded_data_is_refused(tmp_path):
    def hand(claim):
        claim["targets"][0]["not_applicable"] = dict(EXEMPT)

    with pytest.raises(ClaimError, match="never by hand"):
        load(tmp_path, hand)


def test_a_minimum_of_data_present_given_for_generated_data_is_refused(tmp_path):
    def minimum(claim):
        claim["targets"][0]["coverage_minimum"] = {"data_present": {"positive": 2, "negative": 1}}

    with pytest.raises(ClaimError, match="minimum coverage of data_present"):
        load(tmp_path, chain(with_datasets(generated()), minimum))


def test_a_minimum_equal_to_the_default_given_by_hand_is_refused_too(tmp_path):
    def minimum(claim):
        claim["targets"][0]["coverage_minimum"] = {"data_present": {"positive": 1, "negative": 1}}

    with pytest.raises(ClaimError, match="minimum coverage of data_present"):
        load(tmp_path, chain(with_datasets(generated()), minimum))


def test_verify_derived_refuses_an_exemption_that_does_not_match_the_origin(tmp_path):
    claim = load(tmp_path, with_datasets(generated())).canonical()
    broken = {**claim, "targets": [dict(t) for t in claim["targets"]]}
    del broken["targets"][0]["not_applicable"]
    with pytest.raises(ValueError, match="not_applicable"):
        verify_derived(broken)
    broken = {**claim, "targets": [dict(t) for t in claim["targets"]]}
    broken["targets"][0]["coverage_minimum"] = {
        **broken["targets"][0]["coverage_minimum"],
        "data_present": {"positive": 1, "negative": 1},
    }
    with pytest.raises(ValueError, match="coverage_minimum.data_present"):
        verify_derived(broken)
    plain = load(tmp_path).canonical()  # downloaded data, written again in the same folder
    plain["targets"][0]["not_applicable"] = dict(EXEMPT)
    with pytest.raises(ValueError, match="not_applicable"):
        verify_derived(plain)


@pytest.mark.parametrize(
    "change, message",
    [
        (lambda d: d.update(url="https://example.org/x"), "url"),
        (lambda d: d.update(sha256="d" * 64), "sha256"),
        (lambda d: d.update(generator=[]), "generator"),
        (lambda d: d.update(inputs=["teacher"]), "not weights"),
        (lambda d: d.update(inputs=["t", "t"]), "twice"),
        (lambda d: d.update(configuration="  "), "configuration"),
        (lambda d: d.update(derived_splits={}), "derived_splits"),
        (lambda d: d["splits"]["test"].update(unit=""), "unit"),
    ],
)
def test_invalid_generated_entries_are_refused(tmp_path, change, message):
    entry = generated()
    change(entry)
    with pytest.raises(ClaimError, match=message):
        load(tmp_path, with_datasets(entry))


def test_generated_inputs_name_weights_entries(tmp_path):
    weights = {
        "name": "teacher",
        "url": "https://example.org/teacher.pt",
        "reference": "teacher models",
        "version": "1",
        "license": "Apache-2.0",
        "retrieved_utc": "2026-10-15T00:00:00Z",
        "sha256": "e" * 64,
        "size_bytes": 10,
        "local_copy_allowed": False,
    }

    def add_weights(claim):
        claim["test_plan"]["weights"] = [weights]

    claim = load(tmp_path, chain(with_datasets(generated(inputs=["teacher"])), add_weights))
    assert claim.canonical()["test_plan"]["datasets"][0]["inputs"] == ["teacher"]


def repository_file(path="data/graph.bin"):
    return {
        "name": "cifar10",
        "origin": "repository_file",
        "path": path,
        "sha256": "d" * 64,
        "size_bytes": 1000,
        "splits": {
            "train": {"expected_examples": 50000, "source": "reader:npy"},
            "test": {"expected_examples": 10000, "source": "reader:npy"},
        },
    }


def test_a_repository_file_resolves_and_keeps_the_gate(tmp_path):
    claim = load(tmp_path, with_datasets(repository_file())).canonical()
    assert claim["test_plan"]["datasets"][0]["origin"] == "repository_file"
    assert all("not_applicable" not in t for t in claim["targets"])


@pytest.mark.parametrize("path", ["/etc/graph.bin", "../graph.bin", "data\\graph.bin", "c:graph"])
def test_a_repository_file_path_must_stay_in_the_repository(tmp_path, path):
    with pytest.raises(ClaimError, match="path"):
        load(tmp_path, with_datasets(repository_file(path)))


def test_dataset_names_are_unique_across_origins(tmp_path):
    with pytest.raises(ClaimError, match="share a name"):
        load(tmp_path, with_datasets(repository_file(), generated()))


# ---- schema: derived splits (section 2) ------------------------------------------------------


def derived(name="ood", n=10000, sources=("test",)):
    def mutate(claim):
        claim["test_plan"]["datasets"][0]["derived_splits"] = {
            name: {
                "expected_examples": n,
                "derived_from": list(sources),
                "rule": "the outer quartiles of the first principal component",
                "code": [dict(DERIVED_CITE)],
            }
        }

    return mutate


def test_a_claim_may_evaluate_a_derived_split():
    claim_file = claim_file_with(_downloaded_with_derived(), _derived_target())
    (t,) = claim_file["targets"]
    assert t["metric"]["split"] == "heldout" and t["metric"]["n_examples"] == SPLITS["test"]
    assert claim_file["test_plan"]["datasets"][0]["derived_splits"]["heldout"]["derived_from"] == [
        "test"
    ]


@pytest.mark.parametrize(
    "mutation, message",
    [
        (derived(sources=("test", "test")), "twice"),
        (derived(sources=("nope",)), "undeclared"),
        (derived(name="test"), "repeats a split name"),
        (derived(sources=()), "derived_from"),
    ],
)
def test_invalid_derived_splits_are_refused(tmp_path, mutation, message):
    with pytest.raises(ClaimError, match=message):
        load(tmp_path, mutation)


def test_a_derived_split_of_another_size_than_the_metric_is_refused(tmp_path):
    plan = MlTestPlan.model_validate({**plan_dict(DATA), "datasets": [_downloaded_with_derived()]})
    model = MlTarget.model_validate(_derived_target(n=3999))
    with pytest.raises(ValueError, match="n_examples"):
        MlClaimSchema._check_target(plan, model)  # noqa: SLF001


def test_other_splits_must_list_the_derived_splits_too(tmp_path):
    plan = MlTestPlan.model_validate(
        {**plan_dict(DATA), "datasets": [_downloaded_with_derived(extra="sibling")]}
    )
    t = _derived_target(routes=["saved_predictions"])
    identity = t["coverage_evidence"]["method"]["split_identity"]
    # every file split listed, the sibling derived split left out
    identity["other_splits"] = [
        {"name": s, "labels_sha256": f"{i}" * 64} for i, s in enumerate(SPLITS, start=1)
    ]
    model = MlTarget.model_validate(t)
    with pytest.raises(ValueError, match="sibling"):
        MlClaimSchema._check_target(plan, model)  # noqa: SLF001
    identity["other_splits"].append({"name": "sibling", "labels_sha256": "9" * 64})
    MlClaimSchema._check_target(plan, MlTarget.model_validate(t))  # noqa: SLF001


# ---- run: the exemption and the derived splits (sections 2 and 3) ----------------------------


def _downloaded_with_derived(sources=("test",), n=SPLITS["test"], extra=None):
    entry = plan_dict(DATA)["datasets"][0]
    entry["derived_splits"] = {
        "heldout": {
            "expected_examples": n,
            "derived_from": list(sources),
            "rule": "the test rows the trainer evaluates",
            "code": [dict(DERIVED_CITE)],
        }
    }
    if extra:
        entry["derived_splits"][extra] = {
            "expected_examples": 10,
            "derived_from": ["train"],
            "rule": "another population",
            "code": [dict(DERIVED_CITE)],
        }
    return entry


def _derived_target(n=SPLITS["test"], routes=("printed_count",)):
    recompute = "saved_predictions" in routes
    t = value_target({}, recompute=recompute, routes=list(routes))
    t["metric"]["split"] = "heldout"
    t["metric"]["n_examples"] = n
    t["inventory"]["transcription"]["split"] = "heldout"
    return t


def _generated_entry():
    return {
        "name": "synthetic",
        "origin": "generated",
        "generator": [_cite("x_train, y_train = data", "x_eval, y_eval = data", "the data")],
        "configuration": "config.json",
        "inputs": [],
        "splits": {
            s: {"expected_examples": n, "unit": "example", "source": "the dataset builder"}
            for s, n in SPLITS.items()
        },
    }


def claim_file_with(dataset: dict, target: dict) -> dict:
    plan = MlTestPlan.model_validate({**plan_dict(DATA), "datasets": [dataset]})
    model = MlTarget.model_validate(target)
    MlClaimSchema._check_target(plan, model)  # noqa: SLF001
    out = MlClaimSchema._derive(plan, model, model.resolved())  # noqa: SLF001
    return {"test_plan": plan.model_dump(mode="json", by_alias=True), "targets": [out]}


def test_generated_data_reproduce_with_a_printed_count_and_no_data_present(tmp_path):
    claim_file = claim_file_with(_generated_entry(), value_target({}, recompute=False))
    assert claim_file["targets"][0]["not_applicable"] == EXEMPT
    outcome = Paper(tmp_path, claim_file, {**CONFIG, "print_count": True}).run()
    claim, base = checks(outcome, KEY)
    assert "data_present" not in base
    assert base["metric_extracted"].coverage == SPLITS["test"]
    assert claim.verdict.verdict is PaperVerdict.REPRODUCED, claim.verdict.reason
    assert claim.verdict.gates_not_applicable == EXEMPT


def test_generated_data_without_an_observed_count_are_inconclusive(tmp_path):
    claim_file = claim_file_with(_generated_entry(), value_target({}, recompute=False))
    claim, base = checks(Paper(tmp_path, claim_file, CONFIG).run(), KEY)
    assert base["metric_extracted"].status is TestStatus.INCONCLUSIVE
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE
    assert claim.verdict.gates_not_applicable == EXEMPT


def test_an_exemption_that_does_not_match_the_origin_stops_the_evaluation(tmp_path):
    claim_file = claim_file_with(_generated_entry(), value_target({}, recompute=False))
    claim_file["targets"][0].pop("not_applicable")
    with pytest.raises(ValueError, match="does not match the dataset's origin"):
        ig.ClaimContext(claim_file["targets"][0], claim_file["test_plan"]).not_applicable()
    plain = claim_file_with(plan_dict(DATA)["datasets"][0], value_target({}, recompute=False))
    plain["targets"][0]["not_applicable"] = dict(EXEMPT)
    with pytest.raises(ValueError, match="does not match the dataset's origin"):
        ig.ClaimContext(plain["targets"][0], plain["test_plan"]).not_applicable()


def test_a_derived_split_takes_the_coverage_of_its_sources(tmp_path):
    claim_file = claim_file_with(_downloaded_with_derived(), _derived_target())
    outcome = Paper(tmp_path, claim_file, {**CONFIG, "print_count": True}).run()
    claim, base = checks(outcome, KEY)
    assert base["data_present"].status is TestStatus.PASS
    assert base["data_present"].coverage == SPLITS["test"]
    assert claim.verdict.verdict is PaperVerdict.REPRODUCED, claim.verdict.reason


def test_a_derived_split_of_two_sources_sums_them(tmp_path):
    entry = _downloaded_with_derived(sources=("validation", "test"))
    claim_file = claim_file_with(entry, _derived_target())
    claim, base = checks(Paper(tmp_path, claim_file, {**CONFIG, "print_count": True}).run(), KEY)
    assert base["data_present"].coverage == SPLITS["validation"] + SPLITS["test"]


def test_a_wrong_file_split_fails_the_gate_whatever_the_derived_split(tmp_path):
    claim_file = claim_file_with(_downloaded_with_derived(), _derived_target())
    paper = Paper(tmp_path, claim_file, {**CONFIG, "print_count": True})
    path = paper.harness.datasets["synthetic"].fetch.path
    wrong = {**SPLITS, "train": SPLITS["train"] - 1}  # outside derived_from
    harness = dataclasses.replace(
        paper.harness, datasets={"synthetic": dataset_evidence(path, DATA, counts=wrong)}
    )
    claim, base = checks(ig.run_paper(claim_file, harness), KEY)
    assert base["data_present"].status is TestStatus.FAIL
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


# ---- container readers (section 4.2) ---------------------------------------------------------

CIFAR_SOURCE = "reader:container:cifar_python:batches/test_batch"
HOST_COUNTS = {"train": SPLITS["train"], "validation": SPLITS["validation"]}


def cifar_archive(n_labels=SPLITS["test"], twice=False, key=b"labels") -> bytes:
    """A CIFAR-like tar.gz: one pickled batch in the real format, a label list and the
    images as a NumPy uint8 array (unpickling it imports numpy: the maintainer's check of
    2026-10-18 on the reader under -I -S)."""
    import numpy as np

    buffer = io.BytesIO()
    images = np.zeros((n_labels, 3072), dtype=np.uint8)
    batch = pickle.dumps({key: [0] * n_labels, b"data": images, b"batch_label": b"test"}, 2)
    with tarfile.open(fileobj=buffer, mode="w:gz") as archive:
        for _ in range(2 if twice else 1):
            info = tarfile.TarInfo("batches/test_batch")
            info.size = len(batch)
            archive.addfile(info, io.BytesIO(batch))
    return buffer.getvalue()


def _reader_entry(source=CIFAR_SOURCE):
    entry = plan_dict(DATA)["datasets"][0]
    entry["splits"]["test"]["source"] = source
    return entry


PLANTED = b'open("out/planted", "w").close()\n'


def run_with_reader(tmp_path, archive, command=True, host=None, stale=False, planted=False):
    claim_file = claim_file_with(_reader_entry(), value_target({}, recompute=False))
    paper = Paper(tmp_path, claim_file, {**CONFIG, "print_count": True})
    data = {"data/archive.tar.gz": archive}
    if planted:  # modules named like the reader's imports, in its working folder
        data.update({name: PLANTED for name in ("json.py", "tarfile.py", "sitecustomize.py")})
    reader = fixture("data-reader", tmp_path / "reader", data)
    if stale:  # a well-formed answer left before the reader runs
        (reader.root / "out").mkdir()
        (reader.root / rd.ANSWER).write_bytes(b'{"test": 4000}')
    authorized = paper.harness.backend._authorized  # noqa: SLF001 - the test's own backend
    path = paper.harness.datasets["synthetic"].fetch.path
    harness = dataclasses.replace(
        paper.harness,
        backend=sb.SubprocessBackend([*authorized.values(), reader]),
        workspaces={**paper.harness.workspaces, "setup/data/synthetic": reader.root},
        datasets={"synthetic": dataset_evidence(path, DATA, counts=host or dict(HOST_COUNTS))},
        reader_command=(
            lambda rung, request, env: [sys.executable, "-I", "-S", "reader.py", request]
        )
        if command
        else None,
        data_paths={"synthetic": "data/archive.tar.gz"},
    )
    outcome = ig.run_paper(claim_file, harness)
    return outcome, *checks(outcome, KEY)


def test_a_container_reader_counts_its_split_after_the_build(tmp_path):
    outcome, claim, base = run_with_reader(tmp_path, cifar_archive())
    assert base["data_present"].status is TestStatus.PASS, base["data_present"].message
    assert base["data_present"].metrics["splits"] == SPLITS
    assert claim.verdict.verdict is PaperVerdict.REPRODUCED, claim.verdict.reason
    ids = [c.container_id for s in outcome.run.steps for c in s.containers]
    assert ids.index("setup/data/synthetic") > ids.index("setup/build/own_environment")
    assert ids.index("setup/data/synthetic") < ids.index(f"{KEY}/base/method/s1")


def test_a_container_count_of_another_size_fails_the_gate(tmp_path):
    _, claim, base = run_with_reader(tmp_path, cifar_archive(n_labels=SPLITS["test"] - 1))
    assert base["data_present"].status is TestStatus.FAIL
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


def test_with_no_reader_command_the_split_has_no_count(tmp_path):
    outcome, claim, base = run_with_reader(tmp_path, cifar_archive(), command=False)
    assert base["data_present"].status is TestStatus.INCONCLUSIVE
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE
    ids = [c.container_id for s in outcome.run.steps for c in s.containers]
    assert "setup/data/synthetic" not in ids


@pytest.mark.parametrize("case", ["two_members", "no_labels"])
def test_a_reader_that_fails_gives_no_count_and_does_not_stop_the_runs(tmp_path, case):
    archive = cifar_archive(twice=True) if case == "two_members" else cifar_archive(key=b"other")
    outcome, claim, base = run_with_reader(tmp_path, archive)
    assert base["data_present"].status is TestStatus.INCONCLUSIVE
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE
    ids = [c.container_id for s in outcome.run.steps for c in s.containers]
    assert f"{KEY}/base/method/s1" in ids  # the base runs still ran


def test_an_answer_present_before_the_reader_runs_is_never_read(tmp_path):
    outcome, claim, base = run_with_reader(tmp_path, cifar_archive(), stale=True)
    assert outcome.run.stopped  # a Refute error: the reader's folder was not fresh
    assert base["data_present"].status is not TestStatus.PASS
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


def _answer(tmp_path, text: bytes):
    path = tmp_path / "counts.json"
    path.write_bytes(text)
    return rd.read_answer(path, {"test", "train"})


def test_a_well_formed_answer_is_read(tmp_path):
    assert _answer(tmp_path, b'{"test": 4000, "train": 0}') == {"test": 4000, "train": 0}


@pytest.mark.parametrize(
    "case",
    [
        "boolean",
        "duplicate",
        "float",
        "negative",
        "missing",
        "extra",
        "trailing",
        "nan",
        "truncated",
        "list",
        "too_large",
    ],
)
def test_an_answer_of_any_other_form_gives_no_count(tmp_path, case):
    text = {
        "boolean": b'{"test": true, "train": 1}',
        "duplicate": b'{"test": 1, "test": 2, "train": 1}',
        "float": b'{"test": 1.0, "train": 1}',
        "negative": b'{"test": -1, "train": 1}',
        "missing": b'{"test": 1}',
        "extra": b'{"test": 1, "train": 1, "other": 1}',
        "trailing": b'{"test": 1, "train": 1} []',
        "nan": b'{"test": 1, "train": NaN}',
        "truncated": b'{"test": 1, "train": 1',
        "list": b"[1, 2]",
        # well formed, but above the size limit
        "too_large": b'{"test": 1, "train": 1' + b" " * (64 * 1024) + b"}",
    }[case]
    assert _answer(tmp_path, text) is None


def test_an_answer_that_is_a_link_gives_no_count(tmp_path):
    target = tmp_path / "real.json"
    target.write_bytes(b'{"test": 1, "train": 1}')
    link = tmp_path / "counts.json"
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symbolic links cannot be created here")
    assert rd.read_answer(link, {"test", "train"}) is None


@pytest.mark.parametrize(
    "source",
    [
        "reader:container:pickle:x",  # not in the closed list
        "reader:container:cifar_python:",  # no member
        "reader:container:cifar_python:a+",  # an empty member
        "reader:container:cifar_python:a#x",  # an argument it does not take
        "reader:container:cifar_python:../a",  # a member that climbs
        "reader:container:excel:table.xlsx",  # no sheet
        "reader:container:dgl:graph.bin#a,b,c",  # dgl takes no member
        "reader:container:dgl:#a,b",  # not a canonical edge type
    ],
)
def test_container_selectors_are_checked_before_the_lock(tmp_path, source):
    with pytest.raises(ValueError):
        rd.container_place(source)
    entry = _reader_entry(source)
    with pytest.raises(ValueError):
        MlTestPlan.model_validate({**plan_dict(DATA), "datasets": [entry]})


def test_container_requests_name_each_split_s_reader():
    splits = {
        "a": {"source": "reader:container:excel:Concrete.xls#0"},
        "b": {"source": "reader:container:dgl:#user,buys,item"},
        "c": {"source": "reader:npy"},
    }
    request = json.loads(rd.container_request("data/f", splits))
    assert request == {
        "path": "data/f",
        "splits": {
            "a": {"reader": "excel", "member": "Concrete.xls", "arg": "0"},
            "b": {"reader": "dgl", "member": "", "arg": "user,buys,item"},
        },
    }
    assert rd.container_request("data/f", {"c": splits["c"]}) is None


# ---- production inputs ---------------------------------------------------------------------


def _offline_inputs(monkeypatch, tmp_path, dataset):
    fetched = []
    monkeypatch.setattr(prod.repository, "clone", lambda url, dest: dest)
    monkeypatch.setattr(prod.repository, "checkout", lambda repo, commit: None)
    monkeypatch.setattr(prod, "fetch_artifact", lambda spec, *a, **k: fetched.append(spec))
    claim_file = {"test_plan": {**plan_dict(DATA), "datasets": [dataset]}}
    return fetched, lambda: prod.prepare_inputs(claim_file, tmp_path, tmp_path / "cache")


def test_generated_data_are_neither_fetched_nor_counted(monkeypatch, tmp_path):
    fetched, prepare = _offline_inputs(monkeypatch, tmp_path, _generated_entry())
    _, datasets, weights = prepare()
    assert datasets == {} and fetched == [] and weights == {}


def test_declared_weights_are_not_fetched_and_the_paper_goes_on(monkeypatch, tmp_path):
    """Weights (inputs of generated data, checkpoints, pre-trained inputs) are not
    fetched by version 1: the paper goes on, and the claims that need them are not run
    (wp3-declared-weights-acceptance.md; the integration tests show the claims)."""
    weights = {
        "name": "teacher",
        "url": "https://example.org/teacher.pt",
        "reference": "teacher models",
        "version": "1",
        "license": "Apache-2.0",
        "retrieved_utc": "2026-10-15T00:00:00Z",
        "sha256": "e" * 64,
        "size_bytes": 10,
        "local_copy_allowed": False,
    }
    cloned = []
    monkeypatch.setattr(prod.repository, "clone", lambda url, dest: cloned.append(dest) or dest)
    monkeypatch.setattr(prod.repository, "checkout", lambda repo, commit: None)

    def no_fetch(*args, **kwargs):
        raise AssertionError("declared weights are never fetched by version 1")

    monkeypatch.setattr(prod, "fetch_artifact", no_fetch)
    plan = {**plan_dict(DATA), "datasets": [_generated_entry()], "weights": [weights]}
    repo, datasets, read = prod.prepare_inputs({"test_plan": plan}, tmp_path, tmp_path / "cache")
    # a weights entry from outside the repository is not read at all
    assert cloned == [tmp_path / "source"] and datasets == {} and read == {}


GRAPH = b"\n".join(b"%d %d" % (i, i + 1) for i in range(50)) + b"\n"


def _repo_entry(path="data/graph.txt", content=GRAPH):
    return {
        "name": "graph",
        "origin": "repository_file",
        "path": path,
        "sha256": hashlib.sha256(content).hexdigest(),
        "size_bytes": len(content),
        "splits": {"all": {"expected_examples": 50, "source": "reader:lines:rows"}},
    }


def _clone(tmp_path, content=GRAPH):
    repo = tmp_path / "clone"
    (repo / "data").mkdir(parents=True)
    (repo / "data" / "graph.txt").write_bytes(content)
    return repo


def test_a_repository_file_is_copied_checked_and_counted_before_any_build(tmp_path):
    repo = _clone(tmp_path)
    evidence = prod.repository_file(repo, _repo_entry(), tmp_path / "cache")
    assert evidence.fetch.ok and evidence.split_counts == {"all": 50}
    assert evidence.fetch.spec.url == "repository:data/graph.txt"
    copy = evidence.fetch.path
    assert copy.parent == tmp_path / "cache" / "repository-files"
    assert copy.read_bytes() == GRAPH
    # the clone's file changing afterwards (a build, a run) does not touch the copy
    (repo / "data" / "graph.txt").write_bytes(b"changed\n")
    assert copy.read_bytes() == GRAPH


def test_other_bytes_in_a_repository_file_fail_with_no_cause_of_the_artifact(tmp_path):
    repo = _clone(tmp_path)
    (repo / "data" / "graph.txt").write_bytes(GRAPH + b"1 2\n")
    evidence = prod.repository_file(repo, _repo_entry(), tmp_path / "cache")
    assert not evidence.fetch.ok and evidence.fetch.path is None
    assert evidence.fetch.failure.cause is FailureCause.UNDETERMINED


@pytest.mark.parametrize("case", ["missing", "outside", "folder"])
def test_a_repository_file_that_is_not_there_gives_no_evidence(tmp_path, case):
    repo = _clone(tmp_path)
    if case == "missing":
        entry = _repo_entry(path="data/none.txt")
    elif case == "outside":
        (tmp_path / "graph.txt").write_bytes(GRAPH)
        entry = _repo_entry(path="../graph.txt")
    else:
        entry = _repo_entry(path="data")
    assert prod.repository_file(repo, entry, tmp_path / "cache") is None


def test_a_repository_file_reached_through_a_link_gives_no_evidence(tmp_path):
    repo = _clone(tmp_path)
    try:
        (repo / "linked").symlink_to(repo / "data", target_is_directory=True)
    except OSError:
        pytest.skip("symbolic links cannot be created here")
    entry = _repo_entry(path="linked/graph.txt")
    assert prod.repository_file(repo, entry, tmp_path / "cache") is None


def test_with_no_verified_copy_the_workspaces_are_prepared_and_nothing_is_mounted(
    tmp_path, monkeypatch
):
    repo = _clone(tmp_path)
    (repo / "data" / "graph.txt").unlink()  # the declared file is missing
    limits = prod.Limits(cpus=1.0, period_us=100_000, memory_bytes=1 << 30, pids=256)
    setup = prod.PaperSetup(
        "p1", tmp_path / "run", repo, {}, {"graph": "data/graph.txt"}, limits, prod.V22_MAXIMA
    )
    monkeypatch.setattr(ig, "plan_container_ids", lambda cf: ["k1/base/s0"])
    claim_file = {"test_plan": {"datasets": [_repo_entry()]}}
    ws = prod.prepare_workspaces(setup, claim_file)  # no ProductionError
    assert "k1/base/s0" in ws and prod.data_mounts(setup) == ()


def _production_setup(tmp_path, layout):
    repo = _clone(tmp_path)
    (repo / "train.py").write_text("print(1)\n", encoding="utf-8")
    evidence = prod.repository_file(repo, _repo_entry(), tmp_path / "cache")
    limits = prod.Limits(cpus=1.0, period_us=100_000, memory_bytes=1 << 30, pids=256)
    setup = prod.PaperSetup(
        "p1", tmp_path / "run", repo, {"graph": evidence}, layout, limits, prod.V22_MAXIMA
    )
    entry = _repo_entry()
    entry["splits"]["all"]["source"] = "reader:container:dgl:#a,b,c"
    claim_file = {"test_plan": {"datasets": [entry]}, "targets": []}
    return setup, claim_file, evidence


def test_the_runs_mount_the_verified_copy_in_place_of_the_clone_s_file(tmp_path, monkeypatch):
    setup, claim_file, evidence = _production_setup(tmp_path, {"graph": "data/graph.txt"})
    ids = ["setup/build/requirements_compiled", "setup/data/graph", "k1/base/s0"]
    monkeypatch.setattr(ig, "plan_container_ids", lambda cf: ids)
    ws = prod.prepare_workspaces(setup, claim_file)
    run = ws["k1/base/s0"]
    assert (run / "train.py").is_file()
    assert not (run / "data" / "graph.txt").exists()  # left for the mount
    assert prod.data_mounts(setup) == ((str(evidence.fetch.path.resolve()), "data/graph.txt"),)
    # the build sees the clone as it is
    assert (ws["setup/build/requirements_compiled"] / "data" / "graph.txt").is_file()
    # the reader's folder holds Refute's script only, never the clone
    reader = ws["setup/data/graph"]
    files = sorted(p.relative_to(reader).as_posix() for p in reader.rglob("*") if p.is_file())
    assert files == [prod.READER_SCRIPT]
    assert (reader / prod.READER_SCRIPT).read_bytes() == prod.READER_SOURCE.read_bytes()


def test_a_repository_file_must_be_mounted_at_its_own_path(tmp_path, monkeypatch):
    setup, claim_file, _ = _production_setup(tmp_path, {"graph": "elsewhere/graph.txt"})
    monkeypatch.setattr(ig, "plan_container_ids", lambda cf: ["k1/base/s0"])
    with pytest.raises(prod.ProductionError, match="must be that path"):
        prod.prepare_workspaces(setup, claim_file)


@pytest.mark.parametrize(
    "rung, python",
    [
        ("own_environment", "/opt/conda/envs/env/bin/python"),
        ("requirements_compiled", "/opt/venv/bin/python"),
        ("requirements_compiled_next_python", "/opt/venv/bin/python"),
    ],
)
def test_the_reader_command_starts_the_built_interpreter_isolated(rung, python):
    env = {"OMP_NUM_THREADS": "2", "MKL_NUM_THREADS": "2"}
    assert prod.reader_argv(rung, '{"x":1}', env) == [
        "/usr/bin/env",
        "-i",
        "MKL_NUM_THREADS=2",
        "OMP_NUM_THREADS=2",
        python,
        "-I",
        "-S",
        "reader.py",
        '{"x":1}',
    ]


def test_planted_modules_in_the_reader_s_folder_never_run(tmp_path):
    _, claim, base = run_with_reader(tmp_path, cifar_archive(), planted=True)
    assert base["data_present"].status is TestStatus.PASS, base["data_present"].message
    assert not (tmp_path / "reader" / "out" / "planted").exists()


def test_the_reader_finds_the_venv_s_libraries_without_site_processing(tmp_path):
    """Python 3.12 and 3.13 keep sys.prefix at the base installation under -S: the reader
    finds the venv's site-packages from the interpreter's path (Codex review)."""
    pytest.importorskip("pandas")
    script = tmp_path / "probe.py"
    script.write_text(
        "import sys\n"
        f"sys.argv = ['reader.py']\n"
        f"exec(open({str(prod.READER_SOURCE)!r}, encoding='utf-8').read().split('READERS =')[0])\n"
        "_library_paths()\n"
        "import pandas\n"
        "print(pandas.__file__)\n",
        encoding="utf-8",
    )
    out = subprocess.run(
        [sys.executable, "-I", "-S", str(script)], capture_output=True, text=True, check=True
    )
    venv = os.path.dirname(os.path.dirname(os.path.abspath(sys.executable)))
    assert out.stdout.strip().lower().startswith(venv.lower()), (venv, out.stdout)


# ---- host readers (section 4.1) ----------------------------------------------------------------


def _zip(member: str, data: bytes) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr(member, data)
    return buffer.getvalue()


ARFF = b"""% a comment
@relation kin8nm
@attribute a numeric
@ATTRIBUTE y numeric
@DATA
% another comment
0.1,0.2

0.3,0.4
0.5,0.6
"""


@pytest.mark.parametrize(
    "content, source, expected",
    [
        (b"1 2 3\n4 5 6\n\n7 8 9\n", "reader:lines:rows", 3),
        (b"a b\n1 2\n3 4\n", "reader:lines:rows-1", 2),
        (b"", "reader:lines:rows-1", 0),
        (ARFF, "reader:arff:rows", 3),
        (_zip("d/yacht.data", b"1 2\n3 4\n"), "reader:zip:d/yacht.data!lines:rows", 2),
        (_zip("k.arff", ARFF), "reader:zip:k.arff!arff:rows", 3),
    ],
)
def test_host_readers_count(tmp_path, content, source, expected):
    path = tmp_path / "file"
    path.write_bytes(content)
    assert rd.count_split(path, source) == expected


@pytest.mark.parametrize(
    "content, source",
    [
        (b"@relation x\n1,2\n", "reader:arff:rows"),  # no @data line
        (b"1 2\n", "reader:lines:cells"),
        (ARFF, "reader:arff:cells"),
    ],
)
def test_host_readers_give_no_count_rather_than_a_guess(tmp_path, content, source):
    path = tmp_path / "file"
    path.write_bytes(content)
    assert rd.count_split(path, source) is None


def test_with_declared_weights_a_downloaded_dataset_is_still_fetched(monkeypatch, tmp_path):
    monkeypatch.setattr(prod.repository, "clone", lambda url, dest: dest)
    monkeypatch.setattr(prod.repository, "checkout", lambda repo, commit: None)
    fetched = []

    def fetch(spec, cache, **kwargs):
        fetched.append(spec.url)
        return prod.FetchResult(spec, None, False, (), None)

    monkeypatch.setattr(prod, "fetch_artifact", fetch)
    weights = {"name": "w", "url": "https://example.org/w.pt", "reference": "r", "version": "1",
               "license": "MIT", "retrieved_utc": "2026-10-15T00:00:00Z", "sha256": "e" * 64,
               "size_bytes": 10, "local_copy_allowed": False}  # fmt: skip
    plan = {**plan_dict(DATA), "weights": [weights]}
    prod.prepare_inputs({"test_plan": plan}, tmp_path, tmp_path / "cache")
    assert fetched == [d["url"] for d in plan["datasets"]]
    assert "https://example.org/w.pt" not in fetched


def test_the_setup_record_states_the_weights_not_fetched(tmp_path):
    from refute.packs.ml.docker_backend import Limits
    from refute.packs.ml.sandbox import TimingMaxima

    setup = prod.PaperSetup(
        "p1", tmp_path, tmp_path, {}, {}, Limits(cpus=1, period_us=100_000,
        memory_bytes=1 << 30, pids=64), TimingMaxima(0.1, 0.1), weights=("w1",),
    )  # fmt: skip
    record = setup.record()["weights"]
    assert record["declared"] == ["w1"] and record["fetched"] is False
    assert record["mounted"] is False and "version 1" in record["reason"]
