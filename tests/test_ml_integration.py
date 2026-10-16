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
from refute.core.paper import FailureCause, GateFailure
from refute.core.verdict import PaperVerdict, TestStatus
from refute.packs.ml import integration as ig
from refute.packs.ml import sandbox as sb
from refute.packs.ml import seeds
from refute.packs.ml import synthetic as sy
from refute.packs.ml.fetch import ArtifactSpec, FetchAttempt, FetchResult
from refute.packs.ml.schema import MlClaimSchema, MlTarget, MlTestPlan
from synthetic_harness import fixture

ARXIV = "2401.01234"
STAMP = "2026-10-15T00:00:00Z"
CLAIM_SEED = bytes(range(32))
SPLITS = {"train": 2000, "validation": 500, "test": 4000}
ALL_RUNGS = ("own_environment", "requirements_compiled", "requirements_compiled_next_python")


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
            "allowed_patches": [],
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


def value_target(applies: dict, recompute: bool = True) -> dict:
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

    def __init__(self, tmp_path, claim_file, config, ladder=None, data=None, evidence=None):
        self.data = data or dataset_bytes(seed=7, n_train=2000, n_val=500, n_test=4000)
        (tmp_path / "fetched").mkdir()
        dataset_path = tmp_path / "fetched" / "synthetic.npz"
        dataset_path.write_bytes(self.data)
        ladder = ladder or {ALL_RUNGS[0]: "ok", ALL_RUNGS[1]: "ok", ALL_RUNGS[2]: "ok"}
        self.expectations = sy.BuildExpectations(
            {r: ("ok" if a == "ok" else "procedure_error") for r, a in ladder.items()}
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


def test_without_saved_predictions_the_metric_shows_no_examples(tmp_path):
    """Requirement 5: a printed number does not show how many examples it was computed on;
    without that evidence metric_extracted cannot pass, so the claim is INCONCLUSIVE."""
    claim_file = resolved(DATA, value_target({}, recompute=False))
    claim, base = checks(Paper(tmp_path, claim_file, CONFIG).run(), KEY)
    assert base["metric_extracted"].coverage is None
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
