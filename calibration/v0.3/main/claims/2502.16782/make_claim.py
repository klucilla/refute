"""The claim file of 2502.16782 (CipherPrune) in the main sample of v0.3: the three drawn
claims (claim_draw.json, round 6563834), written from the frozen inventory, with the engine's
own schema checking the result (load_claim). Each fact comes from a recorded source: the
inventory and its approval, the paper read on arXiv (READ), the repository at the pinned
commit and the BOLT weights' records (calibration/v0.3/main/sources/2502.16782-data-sources.md).

Option 1 of the maintainer (2026-10-18): the paper stays and every drawn claim is
INCONCLUSIVE by an unsupported capability. Two of Refute's limits apply, each enough alone:
the repository holds a Dockerfile at its root, which version 1 does not build (the ladder
stops at its first rung, PROTOCOL.md "Recorded in the triage"), and each claim evaluates the
declared BOLT weights, which version 1 does not fetch (wp3-declared-weights-acceptance.md).
The README gives no single command (per-layer tests of SCI/build/bin, server and client,
summed, plus BOLT's linear part): the inventory's command field says so, and the claim keeps
it as the transcription; nothing runs. The claims are written in full all the same.

Usage (from the repository's root, the project's environment):
  .venv/Scripts/python.exe calibration/v0.3/main/claims/2502.16782/make_claim.py \\
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

ROOT = Path(__file__).resolve().parents[5]
ARXIV, VERSION = "2502.16782", 2
REPO = "https://github.com/ucf-lou-lab-pet/cipher-prune-inference"
COMMIT = "69a0f972cd1b5e26a140a88d3749cb5788fceef8"  # main_walk_batch_05.json, position 112
READ = "2026-10-19T02:24:52Z"  # https://arxiv.org/html/2502.16782v2, Table 1, read by the agent
INVENTORY = ROOT / "calibration/v0.3/main/inventories/2502.16782.json"
DRAW = ROOT / "calibration/v0.3/main/claim_draw.json"
PLACEHOLDER = "pending: the maintainer's approval of the claims package (draft only)"
WEIGHTS = {
    "name": "bolt_word_elimination.zip",
    "url": "https://drive.usercontent.google.com/download?id=1cqh29kv9Cw-AabcVXoo97WQUF5z7AI5E"
    "&export=download&confirm=t",
    "reference": "Pang et al. 2024, BOLT (the fine-tuned BERT models with word elimination)",
    "version": "the bundle of the BOLT Google Drive folder, file id "
    "1cqh29kv9Cw-AabcVXoo97WQUF5z7AI5E",
    "license": "none stated for the weights; the BOLT code (cmu-cryptosystems/BOLT) is MIT",
    "retrieved_utc": "2026-10-19T02:06:58Z",
    "sha256": "66408e4898ed52d9c3f768ee34bdfaf1b4072b0fac7dbafb179d096d2ea61356",
    "size_bytes": 817634523,
    "local_copy_allowed": True,
}
# each candidate: the layers' tokens of the README (lines 103-105), the published value
CANDIDATES = {
    "T1/CipherPrune/BERT Medium/Comm.": ("BERT Medium", 6.7),
    "T1/CipherPrune/BERT Base/Comm.": ("BERT Base", 9.7),
    "T1/CipherPrune/BERT Large/Comm.": ("BERT Large", 18.4),
}


def cite(file: str, first: int, last: int, role: str) -> dict:
    return {"file": file, "lines": [first, last], "role": role}


def candidates() -> dict:
    return {c["candidate_id"]: c for c in json.loads(INVENTORY.read_bytes())["candidates"]}


def dataset_entry(name: str) -> dict:
    return {
        "name": name,
        "origin": "generated",
        "generator": [
            cite("README.md", 99, 105, "the input of 128 tokens and the tokens kept in each "
                 "layer of BERT-medium, BERT-base and BERT-large"),
            cite("README.md", 110, 125, "CipherPrune's communication: the per-layer tests of "
                 "SCI/build/bin, server and client, plus BOLT's linear part"),
        ],
        "configuration": "one private inference of one input of 128 tokens, as the README "
        "describes; no data file",
        "inputs": [WEIGHTS["name"]],
        "splits": {
            "one_input": {
                "expected_examples": 1,
                "unit": "private inference",
                "source": "README.md lines 99-105: one input of 128 tokens",
            }
        },
    }  # fmt: skip


def plan(run_seed: str) -> dict:
    stage = {"active_time_limit_hours": 24, "no_progress_hours": 2, "retries": 0}
    names = []
    for cid in CANDIDATES:
        name = candidates()[cid]["dataset"]
        if name not in names:
            names.append(name)
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
            # no requirements file at the root: the rungs that use a Python version do not
            # apply; the engine's image's Python is named
            "python_ladder": ["3.12"],
            "exclude_newer": "2024-11-08",  # the date of the pinned commit
            "base_image": ENGINE_BASE_IMAGE,
            "allowed_patches": [],
        },
        "datasets": [dataset_entry(n) for n in names],
        "weights": [dict(WEIGHTS)],
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
        "seeds": "no command takes a seed: the claim has no single command",
        "data_split": "the input is one inference, with no split",
        "ablation": "the claim names no component to disable",
        "holdout": "the input is one inference, with nothing to hold out",
        "leakage": "the input is one inference, with no train and test sets",
        "trivial_baseline": "the metric is a communication volume, not a classification",
    }
    return [{"name": n, "applies": False, "reason": r} for n, r in reasons.items()]


def target(cid: str, position: int, approvals: dict) -> dict:
    c = candidates()[cid]
    t = dict(c["transcription"])
    model, value = CANDIDATES[cid]
    return {
        "key": f"arXiv-{ARXIV}v{VERSION}-C{position}",
        "type": "value",
        "statement": f"CipherPrune runs one private inference of {model} on 128 input tokens "
        f"with {value} GB of communication.",
        "source": {
            "arxiv_id": ARXIV,
            "version": VERSION,
            "location": t["location"],
            "quote": t["value"],
            "retrieved_utc": READ,
            "repository_url": REPO,
            "repository_commit": COMMIT,
        },
        "inventory": {"candidate_id": cid, "position": position, "transcription": t},
        "dataset": c["dataset"],
        "metric": {
            "name": t["metric"],
            "split": t["split"],
            "unit": "native",
            "higher_is_better": False,
            "reported": value,
            # Table 1 prints one value per cell for the communication, with no deviation
            "reported_uncertainty": {"kind": "none"},
            "n_examples": 1,
        },
        "comparison_mode": "two_sided",
        "scope": "checkpoint_evaluation",
        "weights": WEIGHTS["name"],
        "run": {
            # the inventory's command: the README gives no single command; nothing runs
            "argv": json.loads(t["command"]),
            "workdir": ".",
            "seed_argument": None,
            "metric_extraction": {
                "from": "log",
                "regex": {"pattern": r"(?m)^total communication \(GB\): ([0-9.]+)$", "group": 1},
                "unit": "native",
            },
        },
        "seeds": {"base": [0], "base_cap": 1, "base_source": "documented"},
        "tolerance": {
            "rel_tol": 0.02,
            "k_sd": 2.0,
            "abs_floor": 0.1,
            "override_reason": "native unit (GB) has no default floor; 0.1 GB is the last "
            "digit Table 1 prints; nothing runs in version 1 (no command, a Dockerfile, "
            "declared weights)",
        },
        "attacks": attacks(),
        "metric_recompute": {
            "applies": False,
            "reason": "there is no run and no per-example output",
        },
        "coverage_evidence": {
            "method": {
                "selected_evaluation": {"kind": "final"},
                "routes": [
                    {
                        "route": "printed_count",
                        "count": {
                            "from": "log",
                            "regex": {"pattern": r"(?m)^inferences=([0-9]+)$", "group": 1},
                        },
                        "link": [
                            cite(
                                "README.md",
                                110,
                                125,
                                "the per-layer tests print their "
                                "own communication; no command prints the inference "
                                "count, so this declared route finds none",
                            )
                        ],
                    }
                ],
            }
        },  # fmt: skip
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
        "title": "CipherPrune: Efficient and Scalable Private Transformer Inference "
        "(arXiv 2502.16782v2), the three drawn claims",
        "hypothesis": "The drawn claims of Table 1 (communication) reproduce from the "
        "repository at the pinned commit.",
        "created": READ[:10],
        "authors": ["refute"],
        "attachments": attachments,
        "test_plan": plan(seeds.run_seed(claim_seed, ARXIV)),
        "targets": [target(cid, i, approvals) for i, cid in enumerate(draw.drawn, start=1)],
    }
    path = out / "claim.yaml"
    path.write_text(yaml.safe_dump(claim, sort_keys=False, allow_unicode=False), encoding="utf-8")
    loaded = load_claim(path)
    print("claim.yaml", loaded.sha256(), "draft" if a.draft else "final")
    return 0


if __name__ == "__main__":
    sys.exit(main())
