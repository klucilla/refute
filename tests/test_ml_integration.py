"""The WP3 integration (#46): a resolved ML claim file, run end to end on the subprocess
backend with cataloged synthetic fixtures (the WP4 trainer and the ladder build), and
every check read from the evidence. Offline: the dataset is built here, the fetch result
is given, and every run is a cataloged fixture written by this harness."""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import io
import json
import os
import re
import sys

import numpy as np

from ml_papers import dataset_bytes
from refute.core.canonical import canonical_bytes
from refute.core.paper import FailureCause, GateFailure
from refute.core.verdict import PaperVerdict, TestStatus
from refute.packs.ml import integration as ig
from refute.packs.ml import sandbox as sb
from refute.packs.ml import seeds
from refute.packs.ml import synthetic as sy
from refute.packs.ml.fetch import ArtifactSpec, FetchAttempt, FetchResult
from refute.packs.ml.schema import MlClaimSchema, MlTarget, MlTestPlan
from synthetic_harness import SOURCES, fixture

ARXIV = "2401.01234"
STAMP = "2026-10-15T00:00:00Z"
CLAIM_SEED = bytes(range(32))
SPLITS = {"train": 2000, "validation": 500, "test": 4000}
ALL_RUNGS = ("own_environment", "requirements_compiled", "requirements_compiled_next_python")
HOOK_PATCH = "patches/coverage-hook.patch"


def plan_dict(data: bytes) -> dict:
    stage = {"active_time_limit_hours": 1, "no_progress_hours": 0.5, "retries": 0}
    return {
        "paper": {
            "arxiv_id": ARXIV,
            "version": 1,
            "run_seed_sha256": seeds.run_seed(CLAIM_SEED, ARXIV),
        },
        "budget": {"profile": "development"},
        "repository": {
            "url": "https://example.org/repo",
            "commit": "a" * 40,
            "latest_commit_at_draw": "a" * 40,
            "version_basis": "latest_at_draw",
        },
        "build": {
            "python_ladder": ["3.12", "3.13"],
            "exclude_newer": "2026-01-01",
            "base_image": "python@sha256:" + "c" * 64,
            "allowed_patches": [{"attachment": HOOK_PATCH, "reason": "the coverage hook"}],
        },
        "datasets": [
            {
                "name": "synthetic",
                "url": "https://example.org/synthetic.npz",
                "reference": "WP4 synthetic dataset",
                "version": "1",
                "license": "Apache-2.0",
                "retrieved_utc": STAMP,
                "sha256": hashlib.sha256(data).hexdigest(),
                "size_bytes": len(data),
                "local_copy_allowed": True,
                "splits": {
                    name: {"expected_examples": n, "source": "the dataset builder"}
                    for name, n in SPLITS.items()
                },
            }
        ],
        "stages": {
            name: dict(stage)
            for name in ("build", "data", "base_run", "metric_recompute", "attack_run")
        },
        "absent_artifact": {"attempts": 3, "interval_minutes": 60},
        "threads": {
            "OMP_NUM_THREADS": 1,
            "MKL_NUM_THREADS": 1,
            "OPENBLAS_NUM_THREADS": 1,
            "NUMEXPR_NUM_THREADS": 1,
        },
    }


def attack_entries(applies: dict) -> list:
    params = {
        "seeds": {},
        "data_split": {
            "original_proportions": [0.8, 0.2],
            "proportions": [0.8, 0.2],
            "split_argument": "--split-seed={seed}",
        },
        "ablation": {
            "disable": {"argv": ["--no-aug"]},
            "orientation": "full_minus_ablated",
            "mode": "direction",
        },
        "holdout": {"split_argument": "--holdout-seed={seed}"},
        "leakage": {"max_overlap_fraction": 0.01},
        "trivial_baseline": {
            "kind": "random",
            "labels": [0, 1],
            "task": "single_label_classification",
        },
    }
    out = []
    for name in ("seeds", "data_split", "ablation", "holdout", "leakage", "trivial_baseline"):
        on = applies.get(name, False)
        entry = {"name": name, "applies": on, "reason": f"{name}: decided before the lock"}
        if on:
            entry["params"] = params[name]
        out.append(entry)
    return out


def _split_labels(data: bytes, split: str) -> list[int]:
    names = {"train": "train", "validation": "val", "test": "test"}
    return [int(v) for v in np.load(io.BytesIO(data), allow_pickle=False)[f"y_{names[split]}"]]


def split_sha256(split: str, data: bytes | None = None) -> str:
    """The labels hash of a split (W3.12d): the canonical JSON array of its labels."""
    return hashlib.sha256(canonical_bytes(_split_labels(data or DATA, split))).hexdigest()


def trainer_line(marker: str) -> int:
    """The line of the cataloged trainer that holds ``marker`` (exactly one)."""
    text = SOURCES["ml-paper"]["train.py"].read_text(encoding="utf-8")
    (line,) = [n for n, line in enumerate(text.splitlines(), 1) if marker in line]
    return line


def call_site_line() -> int:
    """The line of the trainer's cited call site (the hook's selected evaluation)."""
    return trainer_line("# the cited call site")


def _cite(first: str, last: str, role: str) -> dict:
    """A citation of the trainer's code from the line holding ``first`` to the one holding
    ``last`` (Codex review of #111: the links cite the code, not the docstring)."""
    return {"file": "train.py", "lines": [trainer_line(first), trainer_line(last)], "role": role}


PRINT = 'print(f"acc={printed:.2f}")'


def route(name: str) -> dict:
    """One coverage route of 1.5a, as a claim for the cataloged trainer declares it, with
    links that cite the trainer's code from the evidence to the printed value."""
    if name == "saved_predictions":
        link = [_cite('preds["t"], preds["p"] = y_eval, y_pred', PRINT, "saves, then prints")]
        return {"route": name, "link": link}
    if name == "printed_count":
        regex = {"pattern": r"evaluated=(\d+)", "group": 1}
        link = [_cite(PRINT, 'print(f"evaluated=', "prints the value, then its count")]
        return {"route": name, "count": {"from": "log", "regex": regex}, "link": link}
    if name == "sufficient_statistics":
        file = "preds/stats-{seed}.json"
        return {
            "route": name,
            "correct": {"from": "file", "file": file, "json_path": "$.correct"},
            "total": {"from": "file", "file": file, "json_path": "$.total"},
            "link": [_cite("correct = int((y_pred == y_eval).sum())", PRINT, "writes, prints")],
        }
    line = call_site_line()
    return {
        "route": "hook",
        "patch": HOOK_PATCH,
        "function": "sklearn.metrics.accuracy_score",
        "call_site": {"file": "train.py", "lines": [line, line], "role": "the test evaluation"},
        "link": [_cite("# the cited call site", PRINT, "prints the call's return")],
    }


def coverage(routes, split: str = "test") -> dict:
    """The coverage evidence of one method: the routes in their order, and the split's
    identity when a route sees labels."""
    out = {"selected_evaluation": {"kind": "final"}, "routes": [route(r) for r in routes]}
    if {"saved_predictions", "hook"} & set(routes):
        out["split_identity"] = {
            "labels_sha256": split_sha256(split),
            "other_splits": [
                {"name": s, "labels_sha256": split_sha256(s)} for s in SPLITS if s != split
            ],
            "splits_evidence": [
                _cite(
                    'x_train, y_train = data["x_train"]',
                    'x_eval, y_eval = data["x_test"]',
                    "the splits the trainer can evaluate",
                )
            ],
        }
    return out


def value_target(applies: dict, recompute: bool = True, routes=None) -> dict:
    routes = routes or (["saved_predictions"] if recompute else ["printed_count"])
    target = {
        "key": f"arXiv-{ARXIV}v1-C1",
        "type": "value",
        "statement": "The method reaches 89.2% test accuracy on the synthetic dataset.",
        "source": {
            "arxiv_id": ARXIV,
            "version": 1,
            "location": "Table 1",
            "quote": "89.2",
            "retrieved_utc": STAMP,
            "repository_url": "https://example.org/repo",
            "repository_commit": "a" * 40,
        },
        "inventory": {
            "candidate_id": "c1",
            "position": 1,
            "transcription": {
                "value": "89.2",
                "location": "Table 1",
                "metric": "accuracy",
                "split": "test",
                "command": '["python", "train.py", "--seed={seed}"]',
            },
        },
        "dataset": "synthetic",
        "metric": {
            "name": "accuracy",
            "split": "test",
            "unit": "percent",
            "higher_is_better": True,
            "reported": 89.2,
            "reported_uncertainty": {"kind": "none"},
            "reported_n_seeds": 3,
            "n_examples": SPLITS["test"],
        },
        "comparison_mode": "two_sided",
        "scope": "full_training",
        "run": {
            "argv": ["python", "train.py"],
            "workdir": ".",
            "seed_argument": "--seed={seed}",
            "metric_extraction": {
                "from": "log",
                "regex": {"pattern": r"acc=([0-9.]+)", "group": 1},
                "unit": "percent",
            },
        },
        "seeds": {"base": [1, 2, 3], "base_cap": 3, "base_source": "documented"},
        "attacks": attack_entries(applies),
        "metric_recompute": {
            "applies": True,
            "reason": "the repository saves its predictions",
            "predictions": {
                "file": "preds/{seed}.npy",
                "format": "npy",
                "fields": {"y_true": "t", "y_pred": "p"},
            },
            "convention": {"metric": "accuracy", "scale": "percent", "labels": [0, 1]},
        }
        if recompute
        else {"applies": False, "reason": "no saved predictions"},
        "coverage_evidence": {"method": coverage(routes)},
        "approvals": {
            "transcription": {
                "approved_by": "maintainer",
                "approved_utc": STAMP,
                "approved_commit": "e" * 40,
                "inventory_sha256": "0" * 64,
            },
            "claim": {
                "approved_by": "maintainer",
                "approved_utc": STAMP,
                "approved_commit": "f" * 40,
            },
        },
    }
    return target


def resolved(data: bytes, target: dict) -> dict:
    """The claim file as the schema resolves it: test_plan, and the target with every
    default and every derived value written out."""
    plan_model = MlTestPlan.model_validate(plan_dict(data))
    model = MlTarget.model_validate(target)
    out = MlClaimSchema._derive(plan_model, model, model.resolved())  # noqa: SLF001
    return {"test_plan": plan_model.model_dump(mode="json", by_alias=True), "targets": [out]}


def _arrays(data: bytes):
    return np.load(io.BytesIO(data), allow_pickle=False)


def dataset_evidence(path, data: bytes, fetch_ok: bool = True, counts=None) -> ig.DatasetEvidence:
    spec = ArtifactSpec(
        "synthetic",
        "https://example.org/synthetic.npz",
        hashlib.sha256(data).hexdigest(),
        len(data),
    )
    if fetch_ok:
        fetch = FetchResult(spec, path, True, (), None)
    else:
        attempts = tuple(FetchAttempt(i, "absent", 404, spec.url, "HTTP 404") for i in (1, 2, 3))
        fetch = FetchResult(
            spec, None, False, attempts, GateFailure(FailureCause.ARTIFACT_ABSENT, 3, 3)
        )
    arrays = _arrays(data)
    names = {"train": "train", "validation": "val", "test": "test"}
    split_counts = (
        counts if counts is not None else {s: int(len(arrays[f"y_{n}"])) for s, n in names.items()}
    )

    def labels(split):
        return [int(v) for v in arrays[f"y_{names[split]}"]]

    def hashes(split):
        x = arrays[f"x_{names[split]}"]
        return [hashlib.sha256(row.tobytes()).hexdigest() for row in x]

    return ig.DatasetEvidence(fetch, split_counts, labels, hashes)


class Paper:
    """The harness: one fresh cataloged fixture per container, a backend that runs only
    them, and the evidence of the dataset."""

    def __init__(
        self, tmp_path, claim_file, config, ladder=None, data=None, evidence=None, expect=None
    ):
        self.data = data or dataset_bytes(seed=7, n_train=2000, n_val=500, n_test=4000)
        (tmp_path / "fetched").mkdir()
        dataset_path = tmp_path / "fetched" / "synthetic.npz"
        dataset_path.write_bytes(self.data)
        ladder = ladder or {ALL_RUNGS[0]: "ok", ALL_RUNGS[1]: "ok", ALL_RUNGS[2]: "ok"}
        self.expectations = sy.BuildExpectations(
            expect or {r: ("ok" if a == "ok" else "procedure_error") for r, a in ladder.items()}
        )
        workspaces, auths = {}, []
        for cid in ig.plan_container_ids(claim_file):
            folder = tmp_path / "ws" / re.sub(r"[^A-Za-z0-9_.-]", "_", cid)
            if cid.startswith("setup/build/"):
                auth = fixture(
                    "ladder-build",
                    folder,
                    {
                        "ladder.json": json.dumps(ladder).encode(),
                        "Dockerfile": b"FROM scratch\n",
                        "requirements.txt": b"numpy\n",
                    },
                )
            else:
                settings = {"data": "data/dataset.npz", **config}
                auth = fixture(
                    "ml-paper",
                    folder,
                    {"config.json": json.dumps(settings).encode(), "data/dataset.npz": self.data},
                )
            workspaces[cid] = auth.root
            auths.append(auth)
        self.harness = ig.Harness(
            backend=sb.SubprocessBackend(auths),
            workspaces=workspaces,
            logs=tmp_path / "logs",
            command=lambda argv: (
                [sys.executable, "-I", *argv[1:]] if argv[0] == "python" else list(argv)
            ),
            datasets={"synthetic": evidence or dataset_evidence(dataset_path, self.data)},
            ladder_inputs=("Dockerfile", "requirements.txt"),
            build_command=lambda rung: [
                sys.executable,
                "-I",
                "build.py",
                rung.name,
                rung.python or "-",
            ],
            classify_build=self.classify,
            margin_usec=1_000_000,
            base_env=dict(os.environ),
        )
        self.claim_file = claim_file

    def classify(self, rung, result):
        text = result.log_path.read_text(encoding="utf-8", errors="replace")
        return sy.classify_synthetic_build(
            result.exit_code, result.stopped, text, self.expectations.by_rung[rung.name]
        )

    def run(self) -> ig.PaperOutcome:
        return ig.run_paper(self.claim_file, self.harness)


DATA = dataset_bytes(seed=7, n_train=2000, n_val=500, n_test=4000)
CONFIG = {"subsample": 1000, "aug_gain": 6}


def checks(outcome, key):
    claim = next(c for c in outcome.claims if c.key == key)
    return claim, {c.name: c for c in claim.base}


KEY = f"arXiv-{ARXIV}v1-C1"


def test_a_claim_that_holds_is_reproduced_end_to_end(tmp_path):
    applies = dict.fromkeys(
        ("seeds", "data_split", "ablation", "holdout", "leakage", "trivial_baseline"), True
    )
    paper = Paper(tmp_path, resolved(DATA, value_target(applies)), CONFIG)
    outcome = paper.run()
    claim, base = checks(outcome, KEY)
    assert outcome.run.accounting_valid
    assert {n: c.status for n, c in base.items()} == dict.fromkeys(base, TestStatus.PASS), {
        n: c.message for n, c in base.items()
    }
    assert base["metric_extracted"].coverage == SPLITS["test"]  # shown by the saved predictions
    assert base["metric_extracted"].metrics["routes_with_evidence"]["method seed=1"] == [
        "saved_predictions"
    ]
    assert base["data_present"].metrics["splits"] == SPLITS
    statuses = {a.name: a.result.status for a in claim.attacks}
    assert statuses == dict.fromkeys(applies, TestStatus.PASS), [
        a.result.message for a in claim.attacks
    ]
    assert claim.verdict.verdict is PaperVerdict.REPRODUCED, claim.verdict.reason
    assert outcome.profile.headline == "1 of 1 drawn claims: REPRODUCED"
    # identity: one container per seed and role, the ladder stopped at its first rung
    ids = [c.container_id for s in outcome.run.steps for c in s.containers]
    assert f"{KEY}/base/method/s1" in ids and "setup/build/own_environment" in ids
    assert "setup/build/requirements_compiled" not in ids


def test_two_bad_attack_seeds_make_the_claim_fragile(tmp_path):
    claim_file = resolved(DATA, value_target({"seeds": True}))
    attack_seeds = claim_file["targets"][0]["seeds"]["attack"]
    config = {**CONFIG, "bad_seeds": attack_seeds[:2], "seed_penalty": 8}
    claim, _ = checks(Paper(tmp_path, claim_file, config).run(), KEY)
    seeds_attack = claim.attacks[0]
    assert seeds_attack.result.status is TestStatus.FAIL
    assert claim.verdict.verdict is PaperVerdict.FRAGILE


def test_a_printed_value_its_predictions_do_not_give_is_not_reproduced(tmp_path):
    claim_file = resolved(DATA, value_target({}))
    claim, base = checks(Paper(tmp_path, claim_file, {**CONFIG, "print_bias": 0.5}).run(), KEY)
    assert base["metric_recompute"].status is TestStatus.FAIL
    assert claim.verdict.verdict is PaperVerdict.NOT_REPRODUCED


def test_every_rung_failing_by_its_procedure_is_not_reproducible(tmp_path):
    ladder = dict.fromkeys(ALL_RUNGS, "procedure_error")
    outcome = Paper(tmp_path, resolved(DATA, value_target({})), CONFIG, ladder=ladder).run()
    claim, base = checks(outcome, KEY)
    assert base["environment_build"].status is TestStatus.FAIL
    assert claim.failures["environment_build"] == GateFailure(FailureCause.BUILD_LADDER, 3, 3)
    assert claim.verdict.verdict is PaperVerdict.NOT_REPRODUCIBLE
    # every rung ran and was accounted; no base run happened
    ids = [c.container_id for s in outcome.run.steps for c in s.containers]
    assert [i for i in ids if i.startswith("setup/")] == [f"setup/build/{r}" for r in ALL_RUNGS]
    assert not any(i.startswith(KEY) for i in ids)


def test_a_failed_run_is_inconclusive_whatever_its_exit_code(tmp_path):
    """Item D: an exit code from 1 to 125 is not evidence of the artifact's cause."""
    outcome = Paper(tmp_path, resolved(DATA, value_target({})), {**CONFIG, "exit_code": 3}).run()
    claim, base = checks(outcome, KEY)
    assert base["run_completed"].status is TestStatus.FAIL
    assert claim.failures["run_completed"].cause is FailureCause.UNDETERMINED
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


def test_a_proven_absence_of_the_dataset_is_not_reproducible(tmp_path):
    evidence = dataset_evidence(None, DATA, fetch_ok=False)
    claim_file = resolved(DATA, value_target({}))
    claim, base = checks(Paper(tmp_path, claim_file, CONFIG, evidence=evidence).run(), KEY)
    assert base["data_present"].status is TestStatus.FAIL
    assert base["data_present"].metrics["absent_http_statuses"] == [404, 404, 404]
    assert claim.verdict.verdict is PaperVerdict.NOT_REPRODUCIBLE


def test_a_split_of_another_size_is_inconclusive(tmp_path):
    counts = {**SPLITS, "validation": 499}
    paper = Paper(tmp_path, resolved(DATA, value_target({})), CONFIG)
    path = paper.harness.datasets["synthetic"].fetch.path
    harness = dataclasses.replace(
        paper.harness, datasets={"synthetic": dataset_evidence(path, DATA, counts=counts)}
    )
    outcome = ig.run_paper(paper.claim_file, harness)
    claim, base = checks(outcome, KEY)
    assert base["data_present"].status is TestStatus.FAIL
    assert claim.failures["data_present"].cause is FailureCause.UNDETERMINED
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


def test_with_no_route_that_closes_the_chain_the_metric_shows_no_examples(tmp_path):
    """Requirement 5 and 1.5a: a printed value does not show how many examples it was
    computed on. The claim declares a printed count the run never prints, so no route
    closes the chain: metric_extracted is INCONCLUSIVE, never a raw PASS."""
    claim_file = resolved(DATA, value_target({}, recompute=False))
    claim, base = checks(Paper(tmp_path, claim_file, CONFIG).run(), KEY)
    gate = base["metric_extracted"]
    assert gate.status is TestStatus.INCONCLUSIVE and "no route shows the examples" in gate.message
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


def test_an_invalid_accounting_gives_no_verdict(tmp_path):
    paper = Paper(tmp_path, resolved(DATA, value_target({})), CONFIG)
    integration = ig.PaperIntegration(paper.claim_file, paper.harness)
    outcome = integration.run()
    assert outcome.claims[0].verdict.verdict is PaperVerdict.REPRODUCED
    broken = copy.copy(outcome.run)
    broken.accounting_valid = False
    broken.invalid_reasons = ["breach: a container used more than its reservation"]
    again = integration.evaluate(broken)
    assert again.claims[0].verdict.verdict is PaperVerdict.INCONCLUSIVE
    assert again.claims[0].computed is PaperVerdict.REPRODUCED
    assert ig.ACCOUNTING_INVALID in again.claims[0].verdict.reason


# ---- Codex review of #110 -----------------------------------------------------------------------


def test_the_unit_conversion_is_exact_whatever_the_decimal_context():
    from decimal import Decimal, localcontext

    with localcontext() as ctx:
        ctx.prec = 5  # a small context must not round the conversion
        assert ig._convert(
            Decimal("0.9000000000000000000000000000001"), "fraction", "percent"
        ) == Decimal("90.00000000000000000000000000001")
        assert ig._convert(Decimal("91.25"), "percent", "fraction") == Decimal("0.9125")


def _context(claim_file):
    return ig.ClaimContext(claim_file["targets"][0], claim_file["test_plan"])


def test_a_fetch_result_for_another_artifact_is_not_evidence(tmp_path):
    claim_file = resolved(DATA, value_target({}))
    other = DATA + b"x"
    evidence = dataset_evidence(None, other, fetch_ok=False)  # 404 x3, but another artifact
    gate, failure = ig.data_present(_context(claim_file), evidence)
    assert (
        gate.status is TestStatus.INCONCLUSIVE and "not for the declared artifact" in gate.message
    )


def test_an_absence_counts_only_against_the_attempts_the_claim_fixed(tmp_path):
    """The claim fixes 3 attempts; a fetch record of 1 attempt of 1 is incomplete."""
    claim_file = resolved(DATA, value_target({}))
    spec = ArtifactSpec(
        "synthetic",
        "https://example.org/synthetic.npz",
        hashlib.sha256(DATA).hexdigest(),
        len(DATA),
    )
    one = FetchResult(
        spec,
        None,
        False,
        (FetchAttempt(1, "absent", 404, spec.url, "HTTP 404"),),
        GateFailure(FailureCause.ARTIFACT_ABSENT, 1, 1),
    )
    evidence = ig.DatasetEvidence(one, None)
    gate, failure = ig.data_present(_context(claim_file), evidence)
    assert failure == GateFailure(FailureCause.ARTIFACT_ABSENT, 1, 3)


def test_partial_reads_of_a_split_are_never_taken_for_the_split(tmp_path):
    applies = {"leakage": True, "trivial_baseline": True}
    target = value_target(applies)
    target["attacks"][5]["params"]["kind"] = "majority"
    paper = Paper(tmp_path, resolved(DATA, target), CONFIG)
    full = paper.harness.datasets["synthetic"]
    partial = dataclasses.replace(
        full,
        labels=lambda split: list(full.labels(split))[:10],
        example_hashes=lambda split: list(full.example_hashes(split))[:10],
    )
    outcome = ig.run_paper(
        paper.claim_file, dataclasses.replace(paper.harness, datasets={"synthetic": partial})
    )
    claim = outcome.claims[0]
    assert all(a.result is None for a in claim.attacks), [a.name for a in claim.attacks]
    assert any("not every example" in n for n in claim.notes)
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


def test_an_output_present_before_the_run_stops_the_paper(tmp_path):
    """Requirement 10: a stale predictions file in a base run's folder is never read as
    that run's output; the run is refused (a Refute error) and the claim is INCONCLUSIVE."""
    paper = Paper(tmp_path, resolved(DATA, value_target({})), CONFIG)
    folder = paper.harness.workspaces[f"{KEY}/base/method/s1"]
    (folder / "preds").mkdir()
    (folder / "preds" / "1.npy").write_bytes(b"stale")
    outcome = paper.run()
    assert "outputs present before the run" in outcome.run.stopped
    assert outcome.claims[0].verdict.verdict is PaperVerdict.INCONCLUSIVE


def test_an_unexpected_success_of_a_rung_is_never_built(tmp_path):
    """Codex review of #110: each rung is classified once; a rung declared to fail by its
    procedure that exits 0 is not a success: the setup stops, nothing else runs."""
    expect = dict.fromkeys(ALL_RUNGS, "procedure_error")
    outcome = Paper(tmp_path, resolved(DATA, value_target({})), CONFIG, expect=expect).run()
    claim, base = checks(outcome, KEY)
    assert base["environment_build"].status is TestStatus.INCONCLUSIVE
    assert claim.failures["environment_build"].cause is FailureCause.UNDETERMINED
    ids = [c.container_id for s in outcome.run.steps for c in s.containers]
    assert ids == ["setup/build/own_environment"]
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


def test_a_comparison_pairs_its_methods_by_seed(tmp_path):
    """A comparison with a separate reference run (the method without its augmentation):
    each seed's difference is method minus reference of that seed."""
    target = value_target({}, recompute=False)
    target.update(
        type="comparison",
        comparison_mode="direction",
        statement="The augmentation helps.",
    )
    target["inventory"]["transcription"]["value"] = "89.2 vs 83.2"
    metric = target["metric"]
    del metric["reported"], metric["reported_uncertainty"]
    target["comparison"] = {
        "method": "Aug",
        "reference": "NoAug",
        "orientation": "method_minus_reference",
        "reported_method": 89.2,
        "reported_reference": 83.2,
        "uncertainty_method": {"kind": "none"},
        "uncertainty_reference": {"kind": "none"},
        "paired_uncertainty": {"kind": "none"},
        "reference_run": {
            "argv": ["python", "train.py", "--no-aug"],
            "workdir": ".",
            "seed_argument": "--seed={seed}",
            "metric_extraction": target["run"]["metric_extraction"],
        },
    }
    # separate runs may use the same selector on their own logs (1.5a)
    target["coverage_evidence"]["reference"] = coverage(["printed_count"])
    outcome = Paper(tmp_path, resolved(DATA, target), {**CONFIG, "print_count": True}).run()
    claim, base = checks(outcome, KEY)
    assert base["base_reproduction"].status is TestStatus.PASS
    ids = [c.container_id for s in outcome.run.steps for c in s.containers]
    assert f"{KEY}/base/reference/s1" in ids and f"{KEY}/base/method/s1" in ids
    # each method's printed count shows its examples, run by run
    gate = base["metric_extracted"]
    assert gate.status is TestStatus.PASS, gate.message
    assert gate.metrics["routes_with_evidence"]["reference seed=2"] == ["printed_count"]


def test_methods_are_paired_by_seed_not_by_position_of_completion():
    """Distinct values per seed tell a correct pairing from a swapped one: seed 1 gives
    90 - 80 = 10, seed 2 gives 91 - 85 = 6 (swapped references would give 5 and 11)."""
    from decimal import Decimal

    ctx = ig.ClaimContext(
        {"comparison": {"reference_run": {"argv": ["x"]}, "orientation": "method_minus_reference"}},
        {},
    )

    def value(role, v):
        return ig.Value(
            ig.orc.Outcome.COMPLETED, "", {role: ig.ex.Extracted(str(v), Decimal(v), "log")}
        )

    by_seed = {
        2: {"reference": value("reference", 85), "method": value("method", 91)},
        1: {"method": value("method", 90), "reference": value("reference", 80)},
    }
    assert ig._base_series(ctx, by_seed) == [Decimal(6), Decimal(10)]


# ---- the coverage routes of metric_extracted (1.5a), on both sides -----------------------------


def _metric_gate(tmp_path, routes, config, recompute=False):
    claim_file = resolved(DATA, value_target({}, recompute=recompute, routes=routes))
    claim, base = checks(Paper(tmp_path, claim_file, {**CONFIG, **config}).run(), KEY)
    return claim, base["metric_extracted"]


def test_route_c_saved_predictions_in_another_order_do_not_identify_the_split(tmp_path):
    """The declared limitation of W3.12d: the predictions saved in a shuffled order keep the
    accuracy (metric_recompute passes) but not the order of the labels, so (c) cannot
    identify the split and, alone, leaves the gate INCONCLUSIVE."""
    claim_file = resolved(DATA, value_target({}))
    claim, base = checks(Paper(tmp_path, claim_file, {**CONFIG, "shuffle_preds": True}).run(), KEY)
    assert base["metric_recompute"].status is TestStatus.PASS
    gate = base["metric_extracted"]
    assert gate.status is TestStatus.INCONCLUSIVE
    assert "not the split's, in its order" in gate.message
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


def test_route_a_a_printed_count_of_the_split_shows_its_examples(tmp_path):
    claim, gate = _metric_gate(tmp_path, ["printed_count"], {"print_count": True})
    assert gate.status is TestStatus.PASS and gate.coverage == SPLITS["test"], gate.message
    assert claim.verdict.verdict is PaperVerdict.REPRODUCED, claim.verdict.reason


def test_route_a_a_count_that_is_not_the_split_s_size_is_inconclusive(tmp_path):
    claim, gate = _metric_gate(tmp_path, ["printed_count"], {"print_count": True, "count_bias": -1})
    assert gate.status is TestStatus.INCONCLUSIVE
    assert "3999 examples, the split declares 4000" in gate.message
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


def test_route_d_sufficient_statistics_that_give_the_printed_value(tmp_path):
    claim, gate = _metric_gate(tmp_path, ["sufficient_statistics"], {"stats": True})
    assert gate.status is TestStatus.PASS and gate.coverage == SPLITS["test"], gate.message
    assert claim.verdict.verdict is PaperVerdict.REPRODUCED, claim.verdict.reason


def test_route_d_statistics_that_disagree_with_the_printed_value_are_a_conflict(tmp_path):
    """8 more correct examples in 4000 move the accuracy by 0.2 points: outside the printed
    two decimals, a conflict (all_must_agree), INCONCLUSIVE."""
    claim, gate = _metric_gate(
        tmp_path, ["sufficient_statistics"], {"stats": True, "stats_bias": 8}
    )
    assert gate.status is TestStatus.INCONCLUSIVE and "is not the printed" in gate.message
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


def test_route_b_one_hook_event_bound_to_metric_split_run_and_call_site(tmp_path):
    claim, gate = _metric_gate(tmp_path, ["hook"], {"hook": True})
    assert gate.status is TestStatus.PASS and gate.coverage == SPLITS["test"], gate.message
    assert gate.metrics["routes_with_evidence"]["method seed=3"] == ["hook"]
    assert claim.verdict.verdict is PaperVerdict.REPRODUCED, claim.verdict.reason


def test_route_b_two_events_at_the_call_site_are_inconclusive(tmp_path):
    """Exactly one event must remain (W3.12c): two calls at the cited site do not."""
    claim, gate = _metric_gate(tmp_path, ["hook"], {"hook": True, "hook_calls": 2})
    assert gate.status is TestStatus.INCONCLUSIVE
    assert "2 events bound to the metric, split and call site" in gate.message
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


def test_route_b_an_event_on_another_split_is_not_the_claim_s(tmp_path):
    claim, gate = _metric_gate(tmp_path, ["hook"], {"hook": True, "hook_split": "validation"})
    assert gate.status is TestStatus.INCONCLUSIVE
    assert "0 events bound" in gate.message
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


def test_route_b_a_hook_that_never_ran_leaves_no_evidence(tmp_path):
    claim, gate = _metric_gate(tmp_path, ["hook"], {})
    assert gate.status is TestStatus.INCONCLUSIVE and "no hook log" in gate.message


def test_route_b_a_hook_log_edited_after_the_run_is_a_failure_of_the_hook(tmp_path):
    """A log whose records no longer match its final digest: INCONCLUSIVE whatever the
    other routes show (a failure of the hook, W3.12c)."""
    claim_file = resolved(DATA, value_target({}, routes=["saved_predictions", "hook"]))
    paper = Paper(tmp_path, claim_file, {**CONFIG, "hook": True})
    integration = ig.PaperIntegration(claim_file, paper.harness)
    outcome = integration.run()
    _, base = checks(outcome, KEY)
    assert base["metric_extracted"].status is TestStatus.PASS, base["metric_extracted"].message
    log = paper.harness.workspaces[f"{KEY}/base/method/s2"] / "refute-hook" / "coverage.jsonl"
    lines = log.read_bytes().split(b"\n")
    lines[0] = lines[0].replace(b'"n_examples":4000', b'"n_examples":3999')
    log.write_bytes(b"\n".join(lines))
    again = integration.evaluate(outcome.run)
    gate = {c.name: c for c in again.claims[0].base}["metric_extracted"]
    assert gate.status is TestStatus.INCONCLUSIVE
    assert "digest different" in gate.message


def test_routes_that_disagree_on_the_count_are_a_conflict(tmp_path):
    """all_must_agree: (c) shows 4000 examples, (a) prints 4001; the agreeing route does not
    win, the gate is INCONCLUSIVE."""
    claim, gate = _metric_gate(
        tmp_path,
        ["saved_predictions", "printed_count"],
        {"print_count": True, "count_bias": 1},
        recompute=True,
    )
    assert gate.status is TestStatus.INCONCLUSIVE and "disagree on the count" in gate.message
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


def test_every_route_together_agrees(tmp_path):
    routes = ["saved_predictions", "sufficient_statistics", "printed_count", "hook"]
    config = {"print_count": True, "stats": True, "hook": True}
    claim, gate = _metric_gate(tmp_path, routes, config, recompute=True)
    assert gate.status is TestStatus.PASS, gate.message
    assert gate.metrics["routes_with_evidence"]["method seed=1"] == sorted(routes)
    assert claim.verdict.verdict is PaperVerdict.REPRODUCED, claim.verdict.reason


def test_the_same_runs_never_count_one_evidence_for_both_methods(tmp_path):
    """A comparison whose reference comes from the same runs: two different selectors that
    read the same token are one piece of evidence counted twice, INCONCLUSIVE."""
    target = value_target({}, recompute=False)
    target.update(type="comparison", comparison_mode="direction", statement="A beats B.")
    target["inventory"]["transcription"]["value"] = "89.2 vs 83.2"
    metric = target["metric"]
    del metric["reported"], metric["reported_uncertainty"]
    target["comparison"] = {
        "method": "A",
        "reference": "B",
        "orientation": "method_minus_reference",
        "reported_method": 89.2,
        "reported_reference": 83.2,
        "uncertainty_method": {"kind": "none"},
        "uncertainty_reference": {"kind": "none"},
        "paired_uncertainty": {"kind": "none"},
        "reference_run": {
            "same": True,
            "metric_extraction": {
                "from": "log",
                "regex": {"pattern": r"acc=([0-9.]+)\s", "group": 1},
                "unit": "percent",
            },
        },
    }
    other = coverage(["printed_count"])
    other["routes"][0]["count"]["regex"] = {"pattern": r"evaluated=([0-9]+)", "group": 1}
    target["coverage_evidence"]["reference"] = other
    outcome = Paper(tmp_path, resolved(DATA, target), {**CONFIG, "print_count": True}).run()
    _, base = checks(outcome, KEY)
    gate = base["metric_extracted"]
    assert gate.status is TestStatus.INCONCLUSIVE
    assert "the method and the reference count one evidence" in gate.message


# ---- Codex review of the routes (#110, round 1) -------------------------------------------------


def test_an_ambiguous_hook_is_inconclusive_even_with_another_route_that_works(tmp_path):
    """W3.12c: none or several bound events is INCONCLUSIVE; a working printed count does
    not hide it."""
    claim, gate = _metric_gate(
        tmp_path, ["printed_count", "hook"], {"print_count": True, "hook": True, "hook_calls": 2}
    )
    assert gate.status is TestStatus.INCONCLUSIVE and "2 events bound" in gate.message
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


def test_a_declared_hook_that_left_no_log_is_inconclusive_even_with_another_route(tmp_path):
    claim, gate = _metric_gate(tmp_path, ["printed_count", "hook"], {"print_count": True})
    assert gate.status is TestStatus.INCONCLUSIVE and "no hook log" in gate.message
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


def test_routes_that_disagree_on_the_value_are_a_conflict_not_a_failure(tmp_path):
    """(d) follows a tampered printed value (8 more correct of 4000, +0.2 points printed),
    (c)'s predictions keep the original: the counts agree but the values do not, so the
    gate is INCONCLUSIVE (W3.12e) and the claim never reaches NOT_REPRODUCED."""
    claim, gate = _metric_gate(
        tmp_path,
        ["saved_predictions", "sufficient_statistics"],
        {"stats": True, "stats_bias": 8, "print_bias": 0.2},
        recompute=True,
    )
    assert gate.status is TestStatus.INCONCLUSIVE and "disagree on the value" in gate.message
    assert claim.verdict.verdict is PaperVerdict.INCONCLUSIVE


def _same_runs_comparison(reference_coverage: dict) -> dict:
    target = value_target({}, recompute=False)
    target.update(type="comparison", comparison_mode="direction", statement="A beats B.")
    target["inventory"]["transcription"]["value"] = "89.2 vs 83.2"
    metric = target["metric"]
    del metric["reported"], metric["reported_uncertainty"]
    target["comparison"] = {
        "method": "A",
        "reference": "B",
        "orientation": "method_minus_reference",
        "reported_method": 89.2,
        "reported_reference": 83.2,
        "uncertainty_method": {"kind": "none"},
        "uncertainty_reference": {"kind": "none"},
        "paired_uncertainty": {"kind": "none"},
        "reference_run": {
            "same": True,
            "metric_extraction": {
                "from": "log",
                "regex": {"pattern": r"acc=([0-9.]+)\s", "group": 1},
                "unit": "percent",
            },
        },
    }
    target["coverage_evidence"]["reference"] = reference_coverage
    return target


def test_a_json_path_and_a_regex_on_one_token_are_one_evidence(tmp_path):
    """The method reads the total of the statistics file by its JSON path, the reference by
    a regular expression on the same file: two selectors, one token (Codex review)."""
    target = _same_runs_comparison(coverage(["printed_count"]))
    by_json = {"from": "file", "file": "preds/stats-{seed}.json", "json_path": "$.total"}
    by_regex = {
        "from": "file",
        "file": "preds/stats-{seed}.json",
        "regex": {"pattern": r'"total": (\d+)', "group": 1},
    }
    target["coverage_evidence"]["method"]["routes"][0]["count"] = by_json
    target["coverage_evidence"]["reference"]["routes"][0]["count"] = by_regex
    outcome = Paper(tmp_path, resolved(DATA, target), {**CONFIG, "stats": True}).run()
    _, base = checks(outcome, KEY)
    gate = base["metric_extracted"]
    assert gate.status is TestStatus.INCONCLUSIVE
    assert "the method and the reference count one evidence" in gate.message


def test_two_spellings_of_one_file_are_one_source(tmp_path):
    """Codex review (round 2): ``preds/./stats-1.json`` and ``preds/stats-1.json`` are one
    file, so a token read through each is one evidence."""
    target = _same_runs_comparison(coverage(["printed_count"]))
    plain = {"from": "file", "file": "preds/stats-{seed}.json", "json_path": "$.total"}
    dotted = {"from": "file", "file": "preds/./stats-{seed}.json", "json_path": "$.total"}
    target["coverage_evidence"]["method"]["routes"][0]["count"] = plain
    target["coverage_evidence"]["reference"]["routes"][0]["count"] = dotted
    outcome = Paper(tmp_path, resolved(DATA, target), {**CONFIG, "stats": True}).run()
    _, base = checks(outcome, KEY)
    gate = base["metric_extracted"]
    assert gate.status is TestStatus.INCONCLUSIVE
    assert "the method and the reference count one evidence" in gate.message


def test_a_hook_log_that_cannot_be_read_blocks_even_with_another_route(tmp_path, monkeypatch):
    """Codex review (round 2): a hook whose log could not be examined is a failure of the
    hook, whatever a working printed count shows."""
    claim_file = resolved(DATA, value_target({}, recompute=False, routes=["printed_count", "hook"]))
    paper = Paper(tmp_path, claim_file, {**CONFIG, "print_count": True, "hook": True})
    integration = ig.PaperIntegration(claim_file, paper.harness)
    outcome = integration.run()
    assert {c.name: c for c in outcome.claims[0].base}["metric_extracted"].status is (
        TestStatus.PASS
    )

    def unreadable(data):
        raise OSError("permission denied")

    monkeypatch.setattr(ig.ch, "read_log", unreadable)
    again = integration.evaluate(outcome.run)
    gate = {c.name: c for c in again.claims[0].base}["metric_extracted"]
    assert gate.status is TestStatus.INCONCLUSIVE and "permission denied" in gate.message


def test_values_within_a_quantum_of_each_other_must_each_print_as_the_token():
    """Codex review (round 2): with 40000 examples, (c) gives 89.1925 and (d) 89.2000. They
    are less than one quantum (0.01) apart, but (c) does not print as "89.20" (nearest:
    [89.195, 89.205]), so the routes disagree: INCONCLUSIVE."""
    from decimal import Decimal

    target = value_target({}, routes=["saved_predictions", "sufficient_statistics"])
    target["metric"]["n_examples"] = 4000
    ctx = _context(resolved(DATA, target))
    token = ig.ex.Extracted("89.20", Decimal("89.20"), "log")
    value = ig.Value(ig.orc.Outcome.COMPLETED, "", {"method": token})
    readings = {
        (1, "method"): ig.RunCoverage(
            [
                ig.RouteReading("saved_predictions", 4000, Decimal("89.1925")),
                ig.RouteReading("sufficient_statistics", 4000, Decimal("89.2000")),
            ],
            (Decimal("89.195"), Decimal("89.205")),
        )
    }
    gate, failure = ig.metric_extracted(ctx, [value], readings)
    assert gate.status is TestStatus.INCONCLUSIVE and "89.1925" in gate.message
    # the same two values, both inside the interval, agree
    readings[(1, "method")].readings[0] = ig.RouteReading(
        "saved_predictions", 4000, Decimal("89.1975")
    )
    gate, failure = ig.metric_extracted(ctx, [value], readings)
    assert gate.status is TestStatus.PASS and failure is None


def test_pieces_are_compared_by_what_they_read_not_by_their_selectors():
    text = "split,n,id\ntest,4000,t1\nval,500,v1\n"
    by_split = {"from": "log", "csv": {"column": "n", "row": {"column": "split", "equals": "test"}}}
    by_id = {"from": "log", "csv": {"column": "n", "row": {"column": "id", "equals": "t1"}}}
    other = {"from": "log", "csv": {"column": "n", "row": {"column": "id", "equals": "v1"}}}
    regex = {"from": "log", "regex": {"pattern": r"test,(\d+)", "group": 1}}
    a, b, c, d = (ig._piece(s, "log", text) for s in (by_split, by_id, other, regex))
    assert a.overlaps(b) and a.overlaps(d) and not a.overlaps(c)
    # Codex review (round 3): the csv module keeps text after a closing quote ("test"x
    # reads as testx), so both selectors read the 4000 of the first row; the locator
    # cannot follow it and abandons the span: the whole source, which overlaps
    odd = 'n,id,split\n4000,t1,"test"x\n500,t2,"testx"y\n'
    by_t1 = {"csv": {"column": "n", "row": {"column": "id", "equals": "t1"}}}
    by_testx = {"csv": {"column": "n", "row": {"column": "split", "equals": "testx"}}}
    first, second = (ig._piece(s, "file:y", odd) for s in (by_t1, by_testx))
    assert second.end is None and first.overlaps(second)
    document = '{"a": {"n": 4000}, "b": [1, {"n": 4000}]}'
    first = ig._piece({"json_path": "$.a.n"}, "file:x", document)
    second = ig._piece({"json_path": "$.b[1].n"}, "file:x", document)
    near = ig._piece({"regex": {"pattern": r'"a": \{"n": (\d+)', "group": 1}}, "file:x", document)
    assert document[first.start : first.end] == "4000" and not first.overlaps(second)
    assert first.overlaps(near) and not second.overlaps(near)
    # a span that cannot be found is the whole source, so it overlaps everything there
    assert ig._piece({"json_path": "$.missing"}, "file:x", document).overlaps(second)


def test_a_missing_reference_value_leaves_its_seed_without_a_difference():
    from decimal import Decimal

    ctx = ig.ClaimContext(
        {"comparison": {"reference_run": {"argv": ["x"]}, "orientation": "method_minus_reference"}},
        {},
    )
    ok = ig.Value(
        ig.orc.Outcome.COMPLETED, "", {"method": ig.ex.Extracted("90", Decimal(90), "log")}
    )
    ref = ig.Value(
        ig.orc.Outcome.COMPLETED, "", {"reference": ig.ex.Extracted("80", Decimal(80), "log")}
    )
    missing = ig.Value(ig.orc.Outcome.FAILED, "exit 1")
    series = ig._base_series(
        ctx, {1: {"method": ok, "reference": ref}, 2: {"method": ok, "reference": missing}}
    )
    assert series == [Decimal(10), None]
