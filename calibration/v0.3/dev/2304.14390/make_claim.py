"""The resolved claim file of the development run of 2304.14390 (DSMCS), written by the ML
schema's own models (MlTestPlan, MlTarget, the resolution and the derivation), so the
engine's rules apply to it as to any claim. A development paper's verdict is computed and
recorded but does not count (plan 4.5; the maintainer's terms of 2026-10-18). See NOTES.md
for the extraction rule and the seed.

Usage: .venv/Scripts/python.exe calibration/v0.3/dev/2304.14390/make_claim.py <approved commit>
writes claim.json and inventory.json next to this file.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from refute.core.canonical import canonical_bytes
from refute.packs.ml.schema import MlClaimSchema, MlTarget, MlTestPlan

HERE = Path(__file__).resolve().parent
ARXIV, VERSION = "2304.14390", 1
REPO = "https://github.com/jzenn/DSMCS"
COMMIT = "72f9ebe5fb652b376c96c031a5a95808e07e86e9"  # main_walk_batch_14.json, position 335
READ = "2026-10-18T13:39:35Z"  # https://arxiv.org/html/2304.14390 (v1), read by the agent
# no drand round reserves the claims of a development paper: a fixed, labelled stand-in
RUN_SEED = hashlib.sha256(b"refute/v0.3/development/2304.14390").hexdigest()
NOT_APPROVED = "not approved: development paper, verdict not counted (maintainer, 2026-10-18)"
ARGV = [
    "python", "train_static_target.py", "--path", "runs", "--log_interval", "100",
    "--lrate", "0.01", "--batch-size", "64", "--epochs", "500",
    "--max_iterations_per_epoch", "10", "--zdim", "50", "--n_particles", "32",
    "--n_transitions", "32", "--deltas_nn_output_scale", "0.25",
    "--variational_augmentation", "UHA",
]  # fmt: skip
LOCATION = "Table 3, block 'DAIS', row delta-hat 0.25 / K 32, column N 32"
TRANSCRIPTION = {
    "value": "-5.35",
    "location": LOCATION,
    "metric": "elbo",
    "split": "test",
    "command": json.dumps(ARGV),
}


def cite(file: str, first: int, last: int, role: str) -> dict:
    return {"file": file, "lines": [first, last], "role": role}


def inventory() -> dict:
    return {
        "format": "refute-ml-inventory-2",
        "paper": {"arxiv_id": ARXIV, "version": VERSION},
        "candidates": [
            {
                "candidate_id": "T3/DAIS/0.25/32/32",
                "reading_order": 1,
                "type": "value",
                "method": "DAIS (UHA, the Hamiltonian kernel)",
                "dataset": "the static toy target the code generates (a Gaussian mixture)",
                "conditions": "the README's DAIS command (learning rate 0.01 of the paper's grid)",
                "transcription": dict(TRANSCRIPTION),
            }
        ],
        # no approval block: a development paper's inventory is not approved by the
        # maintainer and is not checked by refute.selection.inventory (NOTES.md)
    }


def plan() -> dict:
    stage = {"active_time_limit_hours": 24, "no_progress_hours": 2, "retries": 0}
    return {
        "paper": {"arxiv_id": ARXIV, "version": VERSION, "run_seed_sha256": RUN_SEED},
        "budget": {"profile": "development"},
        "repository": {
            "url": REPO,
            "commit": COMMIT,
            "latest_commit_at_draw": COMMIT,
            "version_basis": "latest_at_draw",
        },
        "build": {
            "python_ladder": ["3.10"],  # torch==1.13.1 of requirements.txt: Python <= 3.10
            "exclude_newer": "2024-05-21",  # the date of the pinned commit
            "base_image": "python@sha256:"
            "6ff506466f8b1e981719b468cc0023b8ef000b983cdec0eafe119d01f379e31d",
            "allowed_patches": [],
        },
        "datasets": [
            {
                "name": "toy_targets",
                "origin": "generated",
                "generator": [
                    cite("src/toy/distributions.py", 8, 46, "the target: a Gaussian mixture"),
                    cite("src/toy/distributions.py", 47, 81, "the initial variational samples"),
                    cite("train_static_target.py", 26, 32, "the target and the model built"),
                ],
                "configuration": "the README's DAIS command: " + " ".join(ARGV[1:]),
                "inputs": [],
                "splits": {
                    "test": {
                        "expected_examples": 640,
                        "unit": "batch element (10 test iterations of 64)",
                        "source": "train_static_target.py lines 50-53: the test loader holds "
                        "max_iterations_per_epoch (10) entries; --batch-size 64",
                    }
                },
            }
        ],
        "stages": {
            name: dict(stage)
            for name in ("build", "data", "base_run", "metric_recompute", "attack_run")
        },
        "absent_artifact": {"attempts": 3, "interval_minutes": 60},
        "threads": {
            "OMP_NUM_THREADS": 22,
            "MKL_NUM_THREADS": 22,
            "OPENBLAS_NUM_THREADS": 22,
            "NUMEXPR_NUM_THREADS": 22,
        },
    }


def attacks() -> list:
    reasons = {
        "seeds": "the seed argument is parsed but never applied (set_seed is not called): "
        "no seed can be set without editing the code (NOTES.md)",
        "data_split": "the data are generated, there is no split to redraw",
        "ablation": "the claim names no component to disable",
        "holdout": "the data are generated, there is no file to hold out",
        "leakage": "the data are generated, there are no two populations to compare",
        "trivial_baseline": "the metric is a likelihood bound, not a classification score",
    }
    return [{"name": n, "applies": False, "reason": r} for n, r in reasons.items()]


def target(inventory_sha256: str, approved_commit: str) -> dict:
    approval = {
        "approved_by": NOT_APPROVED,
        "approved_utc": READ,
        "approved_commit": approved_commit,
    }
    return {
        "key": f"arXiv-{ARXIV}v{VERSION}-C1",
        "type": "value",
        "statement": "DAIS with the Hamiltonian kernel (UHA), 32 particles, 32 transitions and "
        "a step scale of 0.25 reaches a log-likelihood bound of -5.35 on the static toy target.",
        "source": {
            "arxiv_id": ARXIV,
            "version": VERSION,
            "location": LOCATION,
            "quote": "-5.35±0.77",
            "retrieved_utc": READ,
            "repository_url": REPO,
            "repository_commit": COMMIT,
        },
        "inventory": {
            "candidate_id": "T3/DAIS/0.25/32/32",
            "position": 1,
            "transcription": dict(TRANSCRIPTION),
        },
        "dataset": "toy_targets",
        "metric": {
            "name": "elbo",
            "split": "test",
            "unit": "native",
            "higher_is_better": True,
            "reported": -5.35,
            "reported_uncertainty": {
                "kind": "sd",
                "value": 0.77,
                "unit": "native",
                "location": LOCATION,
                "quote": "-5.35±0.77",
            },
            "reported_n_seeds": 3,
            "n_examples": 640,
        },
        "comparison_mode": "two_sided",
        "scope": "full_training",
        "run": {
            "argv": ARGV,
            "workdir": ".",
            "seed_argument": None,
            "metric_extraction": {
                "from": "file",
                # W3.11a: the one folder the run names by its date and time (NOTES.md, a)
                "file": "runs/results/static_target/local-mbp/*/models/test_loss_stats.txt",
                "json_path": "$.elbo",
                "unit": "native",
            },
        },
        "seeds": {"base": [2023], "base_cap": 1, "base_source": "documented"},
        "tolerance": {
            "rel_tol": 0.02,
            "k_sd": 2.0,
            "abs_floor": 0.1,
            "override_reason": "native unit (a likelihood bound in nats) has no default floor; "
            "0.1 is written for this development run only and tunes nothing",
        },
        "attacks": attacks(),
        "metric_recompute": {
            "applies": False,
            "reason": "the repository saves no per-example values, only the means of the test "
            "iterations",
        },
        "coverage_evidence": {
            "method": {
                "selected_evaluation": {"kind": "final"},
                "routes": [
                    {
                        "route": "printed_count",
                        "count": {
                            "from": "log",
                            "regex": {"pattern": r"test examples evaluated=(\d+)", "group": 1},
                        },
                        "link": [
                            cite(
                                "src/trainer/trainer.py",
                                76,
                                106,
                                "the test loop: it prints no count of what it evaluated, so this "
                                "declared route finds none (NOTES.md, coverage)",
                            )
                        ],
                    }
                ],
            }
        },
        "approvals": {
            "transcription": {**approval, "inventory_sha256": inventory_sha256},
            "claim": dict(approval),
        },
    }


def main() -> int:
    approved_commit = sys.argv[1]
    inv = inventory()
    inv_bytes = canonical_bytes(inv)
    digest = hashlib.sha256(inv_bytes).hexdigest()
    plan_model = MlTestPlan.model_validate(plan())
    model = MlTarget.model_validate(target(digest, approved_commit))
    MlClaimSchema._check_target(plan_model, model)  # noqa: SLF001 - the schema's own check
    resolved = MlClaimSchema._derive(plan_model, model, model.resolved())  # noqa: SLF001
    claim = {"test_plan": plan_model.model_dump(mode="json", by_alias=True), "targets": [resolved]}
    (HERE / "inventory.json").write_bytes(inv_bytes)
    (HERE / "claim.json").write_bytes(canonical_bytes(claim))
    print("claim.json", hashlib.sha256(canonical_bytes(claim)).hexdigest())
    return 0


if __name__ == "__main__":
    sys.exit(main())
