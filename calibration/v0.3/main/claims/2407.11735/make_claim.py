"""The claim file of 2407.11735 (ProSub) in the main sample of v0.3: the three drawn claims
(claim_draw.json, round 6563834), written from the frozen inventory, with the engine's own
schema checking the result (load_claim). Each fact comes from a recorded source: the
inventory and its approval, the paper read on arXiv (READ), the repository at the pinned
commit, the CIFAR MATLAB archives Refute downloaded and the CIFAR page
(calibration/v0.3/main/sources/2407.11735-data-sources.md).

Expected path: the repository holds a Dockerfile at its root, so the ladder's first rung
(own_environment) applies and version 1 of the docker backend does not build a Dockerfile
(PROTOCOL.md, "Recorded in the triage"; wp3-acceptance.md W3.10b): the build ends as a
Refute error and the ladder stops there (ladder.py: a rung that ends for a reason on
Refute's side is not replaced by the next), so the claims are INCONCLUSIVE on Refute's
side before the budget (about 524,288 training steps, of the order of 10^3 to 10^4
CPU-hours) and the coverage (no printed count) come into play. The claims are written in
full all the same.

Usage (from the repository's root, the project's environment):
  .venv/Scripts/python.exe calibration/v0.3/main/claims/2407.11735/make_claim.py \\
      --out <folder> --approved-utc <UTC> --approved-commit <40 hex> [--draft]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

from refute.core.canonical import canonical_bytes
from refute.core.claim import load_claim
from refute.packs.ml import seeds
from refute.packs.ml.schema import ENGINE_BASE_IMAGE
from refute.selection import inventory as inv

ROOT = Path(__file__).resolve().parents[5]
ARXIV, VERSION = "2407.11735", 2
REPO = "https://github.com/walline/prosub"
COMMIT = "8a28cf3d2cb54250f75a3f6a542f93745d1928ce"  # main_walk_batch_10.json, position 230
# https://arxiv.org/html/2407.11735v2: Table 1 read at this time; the score (the angle to
# the subspace) at 01:58:27Z and the meaning of the deviation at 02:02:36Z
READ = "2026-10-19T01:58:15Z"
INVENTORY = ROOT / "calibration/v0.3/main/inventories/2407.11735.json"
DRAW = ROOT / "calibration/v0.3/main/claim_draw.json"
PATCH = ("2407-cifar-matlab-files.patch",
         "42c124af63e532ae8f816e2d00d2954b40d5d7c001b70749dbce9697be869a71")  # fmt: skip
PLACEHOLDER = "pending: the maintainer's approval of the claims package (draft only)"
LICENCE = (
    "none stated; the CIFAR page asks users to cite the tech report (Krizhevsky 2009, "
    "'Learning Multiple Layers of Features from Tiny Images')"
)
REFERENCE = "Krizhevsky 2009, Learning Multiple Layers of Features from Tiny Images"
CIFAR10 = {
    "url": "https://www.cs.toronto.edu/~kriz/cifar-10-matlab.tar.gz",
    "sha256": "7b4bd3b9c8a3592049c10ccede7e45e827b789198cf071eeb17fbfaf3246a804",
    "size": 183434414,
    "retrieved": "2026-10-19T01:48:27Z",
}
CIFAR100_URL = "https://www.cs.toronto.edu/~kriz/cifar-100-matlab.tar.gz"
NOT_READ = (
    "not read by Refute: the MATLAB version of the archive, which no reader of the engine's "
    "catalogue reads; {n} images by the CIFAR page"
)
# the names the frozen inventory gives the dataset, by its labelled-set size
NAMES = {
    4000: "ID CIFAR10 with OOD CIFAR100 (CIFAR from www.cs.toronto.edu, downloaded by "
    "scripts/create_datasets.py), 4000 labeled examples",
    1000: "ID CIFAR10 with OOD CIFAR100 (CIFAR from www.cs.toronto.edu, downloaded by "
    "scripts/create_datasets.py), 1000 labeled examples",
}
CIFAR100_NAME = "CIFAR-100 (the OOD and unseen sets of the runs, MATLAB version)"
# prosub_ossl.py line 638 and base.py lines 12 and 23-24: train/<datasets.name>/
# <experiment_name>/summaries, datasets.name = "cifar10.<seed>@<nlabeled>+cifar100"
# (data.py line 135), the experiment name from the sorted keyword arguments
EXPERIMENT = (
    "ProSub_archWRN-28-2_batch64_lr0.03_momentum0.9_nclass10_wd0.0005_wpl1.0_ws10.0_wsub1.0"
)


def cite(file: str, first: int, last: int, role: str) -> dict:
    return {"file": file, "lines": [first, last], "role": role}


def candidates() -> dict:
    return {c["candidate_id"]: c for c in json.loads(INVENTORY.read_bytes())["candidates"]}


def cifar100() -> dict:
    record = ROOT / ".cache/data/cifar100-matlab/record.txt"
    if not record.is_file():
        return {}
    line = record.read_text(encoding="utf-8").split()
    out = {"retrieved": line[0], "size": int(line[1])}
    out["sha256"] = re.fullmatch(r"sha256=([0-9a-f]{64})", line[2]).group(1)
    md5 = re.fullmatch(r"md5=([0-9a-f]{32})", line[3]).group(1)
    if md5 != "6a4bfa1dcd5c9453dda6bb54194911f4":  # the CIFAR page's MD5 (sources/)
        raise SystemExit("the CIFAR-100 MATLAB archive's MD5 differs from the CIFAR page's")
    return out


def cifar10_entry(labelled: int) -> dict:
    return {
        "name": NAMES[labelled],
        "url": CIFAR10["url"],
        "reference": REFERENCE,
        "version": "the MATLAB version (cifar-10-matlab.tar.gz)",
        "license": LICENCE,
        "retrieved_utc": CIFAR10["retrieved"],
        "sha256": CIFAR10["sha256"],
        "size_bytes": CIFAR10["size"],
        "local_copy_allowed": True,
        "splits": {
            "train": {"expected_examples": 50000, "source": NOT_READ.format(n=50000)},
            "test": {"expected_examples": 10000, "source": NOT_READ.format(n=10000)},
        },
        "derived_splits": {
            "test_id_and_ood": {
                "expected_examples": 20000,
                "derived_from": ["test"],
                "rule": "the CIFAR-10 test set (ID) and the CIFAR-100 test set (OOD, the "
                "entry " + CIFAR100_NAME + "): auroc_rank_calculation scores the ID test "
                "set against the OOD test set, 10,000 images each",
                "code": [
                    cite("data.py", 147, 158, "the ID test set and the OOD test set read"),
                    cite("prosub_ossl.py", 457, 477, "the EMA scores of both test sets"),
                    cite("prosub_ossl.py", 507, 517, "the AUROC of each score, written as "
                         "ood/auroc_<score>"),
                ],
            }
        },
    }  # fmt: skip


def cifar100_entry(draft: bool) -> dict:
    found = cifar100()
    if not found and not draft:
        raise SystemExit("the CIFAR-100 MATLAB archive has no record yet")
    return {
        "name": CIFAR100_NAME,
        "url": CIFAR100_URL,
        "reference": REFERENCE,
        "version": "the MATLAB version (cifar-100-matlab.tar.gz)",
        "license": LICENCE,
        "retrieved_utc": found.get("retrieved", "2000-01-01T00:00:00Z"),
        "sha256": found.get("sha256", "0" * 64),  # a draft before the download ends
        "size_bytes": found.get("size", 1),
        "local_copy_allowed": True,
        "splits": {
            "train": {"expected_examples": 50000, "source": NOT_READ.format(n=50000)},
            "test": {"expected_examples": 10000, "source": NOT_READ.format(n=10000)},
        },
    }


def plan(run_seed: str, draft: bool) -> dict:
    stage = {"active_time_limit_hours": 24, "no_progress_hours": 2, "retries": 0}
    return {
        "paper": {"arxiv_id": ARXIV, "version": VERSION, "run_seed_sha256": run_seed},
        "budget": {"profile": "main"},
        "repository": {
            "url": REPO,
            "commit": COMMIT,
            "latest_commit_at_draw": COMMIT,
            "version_basis": "latest_at_draw",
        },
        "build": {
            # tensorflow==2.14.0 (requirements.txt): wheels for Python 3.9 to 3.11
            "python_ladder": ["3.11"],
            "exclude_newer": "2024-09-26",  # the date of the pinned commit
            "base_image": ENGINE_BASE_IMAGE,
            "allowed_patches": [
                {
                    "attachment": PATCH[0],
                    "reason": "the origin of the bytes: the two MATLAB "
                    "CIFAR URLs of scripts/create_datasets.py read the archives Refute "
                    "downloaded, verified and mounted in the run's folder (data/cifar/), with "
                    "no other change (the maintainer's decision D3 of 2026-10-18)",
                },
            ],
        },  # fmt: skip
        "datasets": [cifar10_entry(4000), cifar10_entry(1000), cifar100_entry(draft)],
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


def attacks(accuracy: bool) -> list:
    out = [
        {"name": "seeds", "applies": True, "params": {}, "reason": "the run takes --seed (the "
         "labeled subset of create_split.py and prosub_ossl.py): other seeds can be run"},
        {"name": "data_split", "applies": False, "reason": "--seed selects the labeled subset; "
         "there is no other argument for the split"},
        {"name": "ablation", "applies": False, "reason": "the claim names no component to "
         "disable"},
        {"name": "holdout", "applies": False, "reason": "the test sets are the archives' own, "
         "with no argument to hold examples out"},
        {"name": "leakage", "applies": True, "params": {"max_overlap_fraction": 0.01},
         "reason": "the CIFAR-10 train and test sets are files of the archive: exact "
         "duplicates between them can be counted (the MATLAB files are not read by the "
         "engine's readers, so the attack has no data and is INCONCLUSIVE)"},
    ]  # fmt: skip
    if accuracy:
        out.append({"name": "trivial_baseline", "applies": True, "reason": "a closed-set "
                    "accuracy over 10 classes can be compared with a random guess",
                    "params": {"kind": "random", "labels": list(range(10)),
                               "task": "single_label_classification"}})  # fmt: skip
    else:
        out.append(
            {
                "name": "trivial_baseline",
                "applies": False,
                "reason": "the metric is "
                "an AUROC of OOD detection, not a single-label classification",
            }
        )
    return out


def no_count_route() -> dict:
    return {
        "selected_evaluation": {"kind": "final"},
        "routes": [
            {
                "route": "printed_count",
                "count": {
                    "from": "log",
                    "regex": {"pattern": r"(?m)^test examples evaluated=([0-9]+)$", "group": 1},
                },
                "link": [cite("prosub_ossl.py", 423, 528, "the final evaluation writes its "
                              "results as TensorBoard scalars and prints the EMA accuracy, but "
                              "no count of the examples it evaluates, so this declared route "
                              "finds none: metric_extracted is INCONCLUSIVE by coverage")],
            }
        ],
    }  # fmt: skip


def target(cid: str, position: int, approvals: dict, run_seed: str) -> dict:
    c = candidates()[cid]
    t = dict(c["transcription"])
    labelled = 4000 if "4,000 lab." in cid else 1000
    accuracy = t["metric"] == "accuracy"
    argv = json.loads(t["command"])
    assert argv[-1] == "{seed}"
    tag = "test/accuracy_ema" if accuracy else "ood/auroc_subspacescore"
    file = f"train/cifar10.{{seed}}@{labelled}+cifar100/{EXPERIMENT}/summaries/*"
    reported = float(t["value"])
    sd = 0.05 if accuracy else 0.0
    if accuracy:
        statement = (f"ProSub reaches a closed-set accuracy of {t['value']}% on the CIFAR-10 "
                     f"test set with {labelled:,} labels and CIFAR-100 as OOD data.")  # fmt: skip
    else:
        statement = (f"ProSub separates the CIFAR-10 test set (ID) from the CIFAR-100 test "
                     f"set (OOD) with an AUROC of {t['value']}, trained with {labelled:,} "
                     "labels.")  # fmt: skip
    return {
        "key": f"arXiv-{ARXIV}v{VERSION}-C{position}",
        "type": "value",
        "statement": statement,
        "source": {
            "arxiv_id": ARXIV,
            "version": VERSION,
            "location": t["location"],
            "quote": c["approved_text"]["value"],
            "retrieved_utc": READ,
            "repository_url": REPO,
            "repository_commit": COMMIT,
        },
        "inventory": {"candidate_id": cid, "position": position, "transcription": t},
        "dataset": NAMES[labelled],
        "metric": {
            "name": t["metric"],
            "split": t["split"],
            "unit": "percent" if accuracy else "fraction",
            "higher_is_better": True,
            "reported": reported,
            # the paper: "reported as mean and std over three runs" (read at 02:02:36Z)
            "reported_uncertainty": {
                "kind": "sd",
                "value": sd,
                "unit": "percent" if accuracy else "fraction",
                "location": t["location"],
                "quote": c["approved_text"]["value"],
            },
            "reported_n_seeds": 3,
            "n_examples": 10000 if accuracy else 20000,
        },
        "comparison_mode": "two_sided",
        "scope": "full_training",
        "run": {
            "argv": argv[:-1],
            "workdir": ".",
            "seed_argument": "{seed}",
            "metric_extraction": {
                "from": "file",
                "file": file,
                "tensorboard": {"tag": tag, "step": "last"},
                "unit": "fraction",
            },
        },
        # the seeds of the three runs are not stated (inventory): derived from the run seed
        "seeds": {
            "base": seeds.derived_seeds(run_seed, "base", 3),
            "base_cap": 3,
            "base_source": "derived",
        },
        "attacks": attacks(accuracy),
        "metric_recompute": {
            "applies": False,
            "reason": "the repository saves no per-example predictions or scores (the "
            "--savestats option is off in the README's command)",
        },
        "coverage_evidence": {"method": no_count_route()},
        "approvals": approvals,
    }


def write(out: Path, name: str, data: bytes) -> dict:
    (out / name).write_bytes(data)
    return {"path": name, "sha256": hashlib.sha256(data).hexdigest()}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--approved-utc", default="")
    p.add_argument("--approved-commit", default="")
    p.add_argument("--patch-dir", type=Path, default=ROOT / ".cache/tb")
    p.add_argument("--draft", action="store_true")
    a = p.parse_args()
    out = a.out.resolve()
    if a.draft and ROOT / ".cache" not in out.parents:
        raise SystemExit("a draft is written only under .cache")
    out.mkdir(parents=True, exist_ok=True)

    draw_file = json.loads(DRAW.read_bytes())
    claim_seed = int(draw_file["seed"]).to_bytes(32, "big")
    inventory = json.loads(INVENTORY.read_bytes())
    draw = inv.draw_claims(inventory, claim_seed)
    record = inv.draw_record(draw)
    published = next(d for d in draw_file["draws"] if d["arxiv_id"] == ARXIV)
    if canonical_bytes(record) != canonical_bytes(published):
        raise SystemExit("the draw recomputed differs from claim_draw.json")
    run_seed = seeds.run_seed(claim_seed, ARXIV)

    patch = (a.patch_dir / PATCH[0]).read_bytes()
    if hashlib.sha256(patch).hexdigest() != PATCH[1]:
        raise SystemExit(f"{PATCH[0]}: SHA-256 differs")
    attachments = [
        {**write(out, "inventory.json", INVENTORY.read_bytes()), "role": "claim-inventory"},
        {**write(out, "draw.json", canonical_bytes(record)), "role": "claim-draw"},
        {**write(out, PATCH[0], patch), "role": "allowed-patch"},
    ]
    approval = inventory["approval"]
    if a.draft:
        claim_approval = {"approved_by": PLACEHOLDER, "approved_utc": "2000-01-01T00:00:00Z",
                          "approved_commit": "0" * 40}  # fmt: skip
    else:
        claim_approval = {"approved_by": "maintainer", "approved_utc": a.approved_utc,
                          "approved_commit": a.approved_commit}  # fmt: skip
    approvals = {
        "transcription": {
            "approved_by": approval["approved_by"],
            "approved_utc": approval["approved_utc"],
            "approved_commit": approval["approved_commit"],
            "inventory_sha256": inv.inventory_sha256(inventory),
        },
        "claim": claim_approval,
    }
    claim = {
        "id": f"v0.3-main-{ARXIV}",
        "kind": "replicate",
        "pack": "ml",
        "title": "ProSub: Probabilistic Open-Set Semi-Supervised Learning with Subspace-Based "
        "Out-of-Distribution Detection (arXiv 2407.11735v2), the three drawn claims",
        "hypothesis": "The drawn claims of Table 1 (ID CIFAR-10, OOD CIFAR-100) reproduce from "
        "the repository at the pinned commit.",
        "created": READ[:10],
        "authors": ["refute"],
        "attachments": attachments,
        "test_plan": plan(run_seed, a.draft),
        "targets": [
            target(cid, i, approvals, run_seed) for i, cid in enumerate(draw.drawn, start=1)
        ],
    }
    path = out / "claim.yaml"
    path.write_text(yaml.safe_dump(claim, sort_keys=False, allow_unicode=False), encoding="utf-8")
    loaded = load_claim(path)
    print("claim.yaml", loaded.sha256(), "draft" if a.draft else "final")
    return 0


if __name__ == "__main__":
    sys.exit(main())
