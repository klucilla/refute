"""The claim file of 2305.19518 (LRA-diffusion) in the main sample of v0.3: the three drawn
claims (claim_draw.json, round 6563834), written from the frozen inventory, with the engine's
own schema checking the result (load_claim). Each fact comes from a recorded source: the
inventory and its approval, the paper read on arXiv (READ), the repository at the pinned
commit, the CIFAR archives Refute downloaded and the CLIP weights' records
(calibration/v0.3/main/sources/2305.19518-data-sources.md).

The maintainer's decision 4 of 2026-10-18: the two CLIP claims need the CLIP ViT-L/14 weights,
which version 1 does not fetch: they name them and are not run (INCONCLUSIVE by an unsupported
capability, wp3-declared-weights-acceptance.md); the SimCLR claim runs normally (expected
INCONCLUSIVE by the budget: 6.8 to 7.7 CPU-hours per epoch measured, about 1,400 CPU-hours for
200 epochs, and the memory limit reached at the start of epoch 1).

Usage (from the repository's root, the project's environment):
  .venv/Scripts/python.exe calibration/v0.3/main/claims/2305.19518/make_claim.py \\
      --out <folder> --approved-utc <UTC> --approved-commit <40 hex> [--draft]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import yaml

from refute.core.canonical import canonical_bytes
from refute.core.claim import load_claim
from refute.packs.ml import seeds
from refute.packs.ml.schema import ENGINE_BASE_IMAGE
from refute.selection import inventory as inv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import transcription_time as tt  # noqa: E402 - the shared correction of the approval time

ROOT = Path(__file__).resolve().parents[5]
ARXIV, VERSION = "2305.19518", 2
REPO = "https://github.com/puar-playground/lra-diffusion"
COMMIT = "231e587f3569ce413d40d96b9cce5a3c08ee361f"  # main_walk_batch_01.json, position 1
READ = "2026-10-19T02:16:21Z"  # https://arxiv.org/html/2305.19518v2, Table 1, read by the agent
INVENTORY = ROOT / "calibration/v0.3/main/inventories/2305.19518.json"
DRAW = ROOT / "calibration/v0.3/main/claim_draw.json"
PLACEHOLDER = "pending: the maintainer's approval of the claims package (draft only)"
LICENCE = "none stated; the CIFAR page asks users to cite the tech report (Krizhevsky 2009)"
REFERENCE = "Krizhevsky 2009, Learning Multiple Layers of Features from Tiny Images"
CIFAR = {
    10: ("https://www.cs.toronto.edu/~kriz/cifar-10-python.tar.gz",
         "6d958be074577803d12ecdefd02955f39262c83c16fe9348329d7fe0b5c001ce", 170498071,
         "2026-10-18T22:02:26Z",
         "cifar-10-batches-py/data_batch_1+cifar-10-batches-py/data_batch_2+"
         "cifar-10-batches-py/data_batch_3+cifar-10-batches-py/data_batch_4+"
         "cifar-10-batches-py/data_batch_5", "cifar-10-batches-py/test_batch"),
    100: ("https://www.cs.toronto.edu/~kriz/cifar-100-python.tar.gz",
          "85cd44d02ba6437773c5bbd22e183051d648de2e7d6b014e1ef29b855ba677a7", 169001437,
          "2026-10-18T22:54:44Z", "cifar-100-python/train", "cifar-100-python/test"),
}  # fmt: skip
CLIP = {
    "name": "CLIP ViT-L/14",
    "url": "https://openaipublic.azureedge.net/clip/models/"
    "b8cca3fd41ae0c99ba7e8951adf17d267cdb84cd88be6f7c2e0eca1737a03836/ViT-L-14.pt",
    "reference": "Radford et al. 2021, Learning Transferable Visual Models From Natural "
    "Language Supervision (openai/CLIP)",
    "version": "ViT-L/14",
    "license": "MIT (the openai/CLIP repository)",
    "retrieved_utc": "2026-10-18T12:54:21Z",
    "sha256": "b8cca3fd41ae0c99ba7e8951adf17d267cdb84cd88be6f7c2e0eca1737a03836",
    "size_bytes": 932768134,
    "local_copy_allowed": True,
}
# the identifiers the frozen inventory gives the datasets, by candidate
CANDIDATES = {
    "T1/CIFAR-10/35% PMD/LRA-diffusion (CLIP)>LRA-diffusion (SimCLR)": 10,
    "T1/CIFAR-100/LRA-diffusion (SimCLR)/35% PMD": 100,
    "T1/CIFAR-10/LRA-diffusion (CLIP)/35% PMD + 60% U": 10,
}
# train_CIFAR.py line 107 prints the test accuracy each time the validation accuracy
# improves; the reported value is the last such line (inventory): the regular expression
# matches only the line that no other such line follows
LAST_TEST_ACC = (
    r"(?s)Model saved, update best accuracy at Epoch [0-9]+, val acc: [0-9.]+, test acc: "
    r"([0-9.]+)\n(?!.*Model saved, update best accuracy)"
)


def cite(file: str, first: int, last: int, role: str) -> dict:
    return {"file": file, "lines": [first, last], "role": role}


def candidates() -> dict:
    return {c["candidate_id"]: c for c in json.loads(INVENTORY.read_bytes())["candidates"]}


def dataset_entry(name: str, classes: int) -> dict:
    url, digest, size, retrieved, train, test = CIFAR[classes]
    return {
        "name": name,
        "url": url,
        "reference": REFERENCE,
        "version": f"CIFAR-{classes}, python version",
        "license": LICENCE,
        "retrieved_utc": retrieved,
        "sha256": digest,
        "size_bytes": size,
        "local_copy_allowed": True,
        "splits": {
            "train": {"expected_examples": 50000,
                      "source": f"reader:container:cifar_python:{train}"},
            "test": {"expected_examples": 10000,
                     "source": f"reader:container:cifar_python:{test}"},
        },
    }  # fmt: skip


def plan(run_seed: str) -> dict:
    stage = {"active_time_limit_hours": 24, "no_progress_hours": 2, "retries": 0}
    names = {cid: candidates()[cid]["dataset"] for cid in CANDIDATES}
    entries, seen = [], set()
    for cid, classes in CANDIDATES.items():
        if names[cid] not in seen:
            seen.add(names[cid])
            entries.append(dataset_entry(names[cid], classes))
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
            # torch==1.7.1 (requirements.txt): wheels up to Python 3.9, the version the budget
            # measurement built with (budget-measurements/lra2-build.json)
            "python_ladder": ["3.9"],
            "exclude_newer": "2025-09-28",  # the date of the pinned commit
            "base_image": ENGINE_BASE_IMAGE,
            "allowed_patches": [],
        },
        "datasets": entries,
        "weights": [dict(CLIP)],
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
    return [
        {"name": "seeds", "applies": False, "reason": "the script fixes its seeds (lines 20-23: "
         "123) and takes no seed argument"},
        {"name": "data_split", "applies": False, "reason": "the split is fixed in the code "
         "(train[:45000], validation train[45000:], the test set), with no argument"},
        {"name": "ablation", "applies": False, "reason": "the claim names no component to "
         "disable"},
        {"name": "holdout", "applies": False, "reason": "the test set is the archive's own, "
         "with no argument to hold examples out"},
        {"name": "leakage", "applies": True, "params": {"max_overlap_fraction": 0.01},
         "reason": "the CIFAR train and test sets are files of the archive: exact duplicates "
         "between them can be counted"},
        {"name": "trivial_baseline", "applies": True, "reason": "a classification accuracy "
         "can be compared with a random guess over the classes",
         "params": {"kind": "random", "labels": None,
                    "task": "single_label_classification"}},
    ]  # fmt: skip


def uncertainty(value: float, half: float, location: str, quote: str) -> dict:
    # the paper does not state what the deviation is nor over how many runs (inventory):
    # an interval of unknown construction, reported but not convertible (wp3-acceptance.md)
    return {
        "kind": "ci",
        "lower": round(value - half, 6),
        "upper": round(value + half, 6),
        "method": "other_or_unknown",
        "unit": "percent",
        "location": location,
        "quote": quote,
    }


def run_of(command: str) -> dict:
    return {
        "argv": json.loads(command),
        "workdir": ".",
        "seed_argument": None,
        "metric_extraction": {
            "from": "log",
            "regex": {"pattern": LAST_TEST_ACC, "group": 1},
            "unit": "percent",
        },
    }


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
                "link": [cite("train_CIFAR.py", 111, 130, "test() counts the test examples "
                              "(all_cnt) but prints only the accuracy, so this declared route "
                              "finds none: metric_extracted is INCONCLUSIVE by coverage")],
            }
        ],
    }  # fmt: skip


def labelled(attacks_list: list, classes: int) -> list:
    out = []
    for a in attacks_list:
        if a["name"] == "trivial_baseline":
            a = {**a, "params": {**a["params"], "labels": list(range(classes))}}
        out.append(a)
    return out


def target(cid: str, position: int, approvals: dict) -> dict:
    c = candidates()[cid]
    t = dict(c["transcription"])
    classes = CANDIDATES[cid]
    clip = "(CLIP)" in cid.split(">")[0]
    base = {
        "key": f"arXiv-{ARXIV}v{VERSION}-C{position}",
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
        "dataset": c["dataset"],
        "scope": "full_training",
        "run": run_of(t["command"]),
        "seeds": {"base": [123], "base_cap": 1, "base_source": "documented"},
        "attacks": labelled(attacks(), classes),
        "metric_recompute": {
            "applies": False,
            "reason": "the script saves the model, not the per-example predictions",
        },
        "approvals": approvals,
    }
    if clip:
        base["weights"] = CLIP["name"]  # the frozen CLIP encoder the training loads
    if c["type"] == "comparison":
        reference = json.loads(t["command"])
        reference[reference.index("CLIP")] = "SimCLR"
        loc = t["location"]
        return {
            **base,
            "type": "comparison",
            "statement": "On CIFAR-10 with 35% PMD noise, LRA-diffusion with the CLIP encoder "
            "reaches a higher test accuracy than with the SimCLR encoder (96.54% against "
            "88.76%).",
            "metric": {
                "name": "accuracy",
                "split": "test",
                "unit": "percent",
                "higher_is_better": True,
                "reported_n_seeds": None,
                "n_examples": 10000,
            },  # fmt: skip
            "comparison_mode": "direction",
            "comparison": {
                "method": "LRA-diffusion (CLIP)",
                "reference": "LRA-diffusion (SimCLR)",
                "orientation": "method_minus_reference",
                "reported_method": 96.54,
                "reported_reference": 88.76,
                "uncertainty_method": uncertainty(96.54, 0.13, loc, "96.54 ± 0.13"),
                "uncertainty_reference": uncertainty(88.76, 0.24, loc, "88.76 ± 0.24"),
                "paired_uncertainty": {"kind": "none"},
                "reference_run": run_of(json.dumps(reference)),
            },
            "coverage_evidence": {"method": no_count_route(), "reference": no_count_route()},
        }
    value = float(t["value"])
    half = 0.15 if classes == 100 else 0.71
    method = "SimCLR" if "SimCLR" in cid else "CLIP"
    noise = "35% PMD noise" if classes == 100 else "35% PMD and 60% uniform noise"
    return {
        **base,
        "type": "value",
        "statement": f"On CIFAR-{classes} with {noise}, LRA-diffusion with the {method} encoder "
        f"reaches a test accuracy of {t['value']}%.",
        "metric": {
            "name": "accuracy",
            "split": "test",
            "unit": "percent",
            "higher_is_better": True,
            "reported": value,
            "reported_uncertainty": uncertainty(
                value, half, t["location"], c["approved_text"]["value"]
            ),  # fmt: skip
            "n_examples": 10000,
        },
        "comparison_mode": "two_sided",
        "coverage_evidence": {"method": no_count_route()},
    }


def write(out: Path, name: str, data: bytes) -> dict:
    (out / name).write_bytes(data)
    return {"path": name, "sha256": hashlib.sha256(data).hexdigest()}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--approved-utc", default="")
    p.add_argument("--approved-commit", default="")
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

    attachments = [
        {**write(out, "inventory.json", INVENTORY.read_bytes()), "role": "claim-inventory"},
        {**write(out, "draw.json", canonical_bytes(record)), "role": "claim-draw"},
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
            "approved_utc": tt.approved_utc(approval),  # the definition, the decision of 10-19
            "approved_commit": approval["approved_commit"],
            "inventory_sha256": inv.inventory_sha256(inventory),
        },
        "claim": claim_approval,
    }
    claim = {
        "id": f"v0.3-main-{ARXIV}",
        "kind": "replicate",
        "pack": "ml",
        "title": "Label-Retrieval-Augmented Diffusion Models for Learning from Noisy Labels "
        "(arXiv 2305.19518v2), the three drawn claims",
        "hypothesis": "The drawn claims of Table 1 (CIFAR) reproduce from the repository at the "
        "pinned commit.",
        "created": READ[:10],
        "authors": ["refute"],
        "definitions": {"transcription_approval_time": tt.DEFINITION},
        "attachments": attachments,
        "test_plan": plan(seeds.run_seed(claim_seed, ARXIV)),
        "targets": [target(cid, i, approvals) for i, cid in enumerate(draw.drawn, start=1)],
    }
    path = out / "claim.yaml"
    path.write_text(yaml.safe_dump(claim, sort_keys=False, allow_unicode=True), encoding="utf-8")
    loaded = load_claim(path)
    print("claim.yaml", loaded.sha256(), "draft" if a.draft else "final")
    return 0


if __name__ == "__main__":
    sys.exit(main())
