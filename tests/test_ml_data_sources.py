"""Data sources, evaluated populations and host readers of the ML pack
(docs/validation/v0.3/wp3-data-sources-acceptance.md, sections 1 to 4.1 and the cases of
section 6), offline: schema cases on the claim of test_ml_schema, run cases on the cataloged
synthetic paper of test_ml_integration."""

from __future__ import annotations

import dataclasses
import io
import zipfile

import pytest

from refute.core.claim import ClaimError
from refute.core.verdict import PaperVerdict, TestStatus
from refute.packs.ml import integration as ig
from refute.packs.ml import production as prod
from refute.packs.ml import readers as rd
from refute.packs.ml.schema import MlClaimSchema, MlTarget, MlTestPlan, verify_derived
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


def test_a_minimum_equal_to_the_default_cannot_be_told_apart_and_is_not_written(tmp_path):
    def minimum(claim):
        claim["targets"][0]["coverage_minimum"] = {"data_present": {"positive": 1, "negative": 1}}

    claim = load(tmp_path, chain(with_datasets(generated()), minimum)).canonical()
    assert all("data_present" not in t["coverage_minimum"] for t in claim["targets"])


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
    _, datasets = prepare()
    assert datasets == {} and fetched == []


def test_a_repository_file_is_refused_before_the_runs_until_it_is_supported(monkeypatch, tmp_path):
    entry = {**repository_file(), "name": "synthetic"}
    _, prepare = _offline_inputs(monkeypatch, tmp_path, entry)
    with pytest.raises(prod.ProductionError, match="not supported yet"):
        prepare()


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
