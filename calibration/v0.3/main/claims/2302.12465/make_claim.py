"""The claim file of 2302.12465 (PaGE-Link) in the main sample of v0.3: the three drawn
claims (claim_draw.json, round 6563834), written from the frozen inventory and its approved
errata, with the engine's own schema checking the result (load_claim). Everything a claim
states comes from a recorded source: the inventory and its approvals, the errata, the paper
read on arXiv (READ below), the repository at the pinned commit, the population counted
before the lock (population_count.py and its record) and the count of the dataset's edges by
the engine's dgl reader.

Usage (from the repository's root, the project's environment):
  .venv/Scripts/python.exe calibration/v0.3/main/claims/2302.12465/make_claim.py \\
      --out <folder> --likes-edges <N> --count-record <record.json> \\
      --approved-utc <UTC> --approved-commit <40 hex> [--draft]
writes claim.yaml and its attachments into <folder> and loads it with the engine's schema.
With --draft the claim approval is a labelled placeholder (never a valid approval): a draft
is written only under .cache, for the maintainer's review of the claims package.
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
HERE = Path(__file__).resolve().parent
ARXIV, VERSION = "2302.12465", 3
REPO = "https://github.com/amazon-science/page-link-path-based-gnn-explanation"
COMMIT = "cdb7160f9a2fd90bded8cefa8f591f9a0e47ee6c"  # main_walk_batch_13.json, position 325
# https://arxiv.org/html/2302.12465v3, Table 4 and section 6.3, read by the agent
READ = "2026-10-19T01:38:45Z"
INVENTORY = ROOT / "calibration/v0.3/main/inventories/2302.12465.json"
# errata 2 carries both corrections (the engine corrects a candidate once) and replaces
# errata 1 in the claim file: GNNExp-Link's entry is errata 1's; PGExp-Link's adds
# --train_pgexplainer (the maintainer's decision of 2026-10-19; issue #158 comment 6267417453)
ERRATA = ROOT / "calibration/v0.3/main/inventories/2302.12465-errata-2.json"
DRAW = ROOT / "calibration/v0.3/main/claim_draw.json"
PATCHES = {
    # README "Requirements": PyTorch = 1.12.1 and DGL = 0.9.1, which requirements.txt omits
    "2302-torch-dgl.patch": "4d8563a7ffbafd74acb12e19eba4eff0a3143ac55329472e667e723057c097f8",
    # W3.12f: prints len(mask_auc_list) after the mean (wp3-population-count-acceptance.md)
    "2302-population-size.patch": (
        "9741191e660dfcef11c975c5971c13aedeb7adaf10986faac3fc734d7a469151"
    ),
}
COUNT_SCRIPT = "population_count.py"
COUNT_SCRIPT_SHA256 = "edae1ced3336732c2173554019c5219c2aa7dfa46b9f7beefb2d16e824d44ee6"
# the frozen inventory names the dataset in two ways: the value candidates and the
# comparison candidates; a claim uses its candidate's identifier, so the same file is
# declared twice, each entry with its own derived split and its own count pair (an
# attachment serves one counted population only)
DATASETS = {
    "value": {
        "name": "UserItemAttr (synthetic, datasets/synthetic)",
        "script": COUNT_SCRIPT,
        "record": "population_count_record.json",
    },
    "comparison": {
        "name": "UserItemAttr",
        "script": "population_count_comparison.py",
        "record": "population_count_record_comparison.json",
    },
}
# the split as transcribed in the frozen inventory: the test links the evaluator keeps
FILE_SPLIT, SPLIT = "likes_edges", "test_links"
DATASET_SHA256 = "a368d8f68a6bbfd7ea5cf844fe217872c79ac1f3c160f4f46823bbbb7798df9f"
DATASET_SIZE = 93724
NAMES = {  # the candidate, its explainer name in eval_explanations.py, its method
    "T4/UserItemAttr/PaGE-Link": "pagelink",
    "T4/UserItemAttr/GNNExp-Link": "gnnexp",
    "T4/UserItemAttr/PGExp-Link": "pgexp",
}
PLACEHOLDER = "pending: the maintainer's approval of the claims package (draft only)"
# the repository's trained link predictor, a file of the pinned commit, which every
# explainer and the evaluator load and keep frozen (wp3-repository-weights-acceptance.md);
# its bytes read with git from the commit's tree (blob cc6c067a67d6194867660c2793928b9b62c09c6b)
WEIGHTS = {
    "name": "synthetic_model",
    "origin": "repository_file",
    "path": "saved_models/synthetic_model.pth",
    "commit": COMMIT,
    "sha256": "a9446dca4857d6c43f7e95d2641541bf24b94600e1f2a3d83e98b0bfd1b442c2",
    "size_bytes": 272468,
    "license": "MIT-0 (MIT No Attribution), the repository's LICENSE at the pinned commit; "
    "the repository states no other licence for saved_models/ "
    "(calibration/v0.3/main/sources/2302.12465-data-sources.md)",
}
PREDICTOR = (
    "with the repository's trained link predictor (saved_models/synthetic_model.pth of the "
    "pinned commit, loaded frozen; the run does not train it)"
)
DEFINITIONS = {
    "scope": "Every claim is full_training (plan section 5: full training, or evaluation of "
    "a released checkpoint): each run optimizes the explainer's masks from the start "
    "(pagelink.py, baselines/gnnexplainer_link.py or baselines/pgexplainer_link.py) and "
    "eval_explanations.py scores those masks. The repository's trained link predictor, "
    "saved_models/synthetic_model.pth of the pinned commit, is a pre-trained input loaded "
    "frozen, declared as weights that are a file of the repository; it is never trained by "
    "the run, and these claims do not test its training (wp3-repository-weights-acceptance.md, "
    "reviewed by Codex on 2026-10-19).",
    "verdict_paths": "No attack applies to these claims (the seed and the split are fixed in "
    "the code, with no argument), so the verdict of each claim rests on its base reproduction "
    "alone: when the base run completes it is REPRODUCED or NOT_REPRODUCED, never FRAGILE; "
    "NOT_REPRODUCIBLE or INCONCLUSIVE remain possible when the base reproduction cannot be "
    "obtained (the maintainer's decision of 2026-10-19).",
    "transcription_approval_time": tt.DEFINITION,
    "reference_pgexp_link": "The comparison's reference, PGExp-Link, runs errata 2's "
    "command: errata 1's with --train_pgexplainer added, the repository's own training "
    "parameters, none tuned. Without that option baselines/pgexplainer_link.py never trains "
    "the PGExplainer's mask generator (lines 55 and 117-125). This is a reproduction with an "
    "explicit correction of the documented procedure: neither the repository nor the paper "
    "shows that this command produced the published 0.578 (the maintainer's decision of "
    "2026-10-19; https://github.com/klucilla/refute/issues/158#issuecomment-6267417453).",
}


def cite(file: str, first: int, last: int, role: str) -> dict:
    return {"file": file, "lines": [first, last], "role": role}


def auc_extraction(explainer: str) -> dict:
    # eval_explanations.py line 145 prints f'Average Mask-AUC: {avg_auc : .4f}' once per
    # explainer named; each run names one explainer
    del explainer
    return {
        "from": "log",
        "regex": {"pattern": r"(?m)^Average Mask-AUC: +(-?[0-9]+\.[0-9]+)$", "group": 1},
        "unit": "fraction",
    }


def population_route(explainer: str) -> dict:
    return {
        "selected_evaluation": {"kind": "final"},
        "routes": [
            {
                "route": "printed_count",
                "count": {
                    "from": "log",
                    "regex": {
                        "pattern": rf"(?m)^refute-population-size {explainer} ([0-9]+)$",
                        "group": 1,
                    },
                },
                "link": [
                    cite("eval_explanations.py", 94, 109, "the test links kept when pred > 0.5, "
                         "keyed by the pair as comp_graphs: the population"),
                    cite("eval_explanations.py", 133, 139, "one mask AUC per pair of "
                         "comp_graphs, appended to mask_auc_list"),
                    cite("eval_explanations.py", 141, 145, "the mean over mask_auc_list, "
                         "printed; the allowed patch 2302-population-size.patch prints "
                         "len(mask_auc_list) on the next line, named by the explainer"),
                ],
            }
        ],
    }  # fmt: skip


def inventory_bytes() -> bytes:
    return INVENTORY.read_bytes()


def candidates() -> dict:
    return {c["candidate_id"]: c for c in json.loads(inventory_bytes())["candidates"]}


def corrected() -> dict:
    errata = json.loads(ERRATA.read_bytes())
    return {e["candidate_id"]: e["new"] for e in errata["entries"] if e["field"] == "command"}


def transcription(candidate_id: str) -> dict:
    out = dict(candidates()[candidate_id]["transcription"])
    if candidate_id in corrected():
        out["command"] = corrected()[candidate_id]
    return out


def run_of(candidate_id: str) -> dict:
    return {
        "argv": json.loads(transcription(candidate_id)["command"]),
        "workdir": ".",
        # set_seed(0) is called by each script, with no argument (pagelink.py line 91,
        # baselines/gnnexplainer_link.py line 88, baselines/pgexplainer_link.py line 97)
        "seed_argument": None,
        "metric_extraction": auc_extraction(NAMES[candidate_id]),
    }


def dataset_entry(kind: str, likes_edges: int, k: int) -> dict:
    ds = DATASETS[kind]
    return {
        "name": ds["name"],
        "origin": "repository_file",
        "path": "datasets/synthetic",
        "sha256": DATASET_SHA256,
        "size_bytes": DATASET_SIZE,
        "splits": {
            FILE_SPLIT: {
                "expected_examples": likes_edges,
                "source": "reader:container:dgl:#user,likes,item",
            }
        },
        "derived_splits": {
            SPLIT: {
                "expected_examples": k,
                "derived_from": [FILE_SPLIT],
                "rule": "the test links of eids_split (validation 0.1, test 0.2, seed 0) that "
                "the repository's saved model predicts as positive (sigmoid of the score > 0.5 "
                "on the 2-hop subgraph of the pair), counted once per pair",
                "code": [
                    cite("data_processing.py", 7, 101, "process_data: the split of the "
                         "'likes' edges and the test graph"),
                    cite("data_processing.py", 104, 147, "load_dataset: the graph read from "
                         "datasets/synthetic, then process_data"),
                    cite("utils.py", 41, 89, "idx_split and eids_split, seed 0"),
                    cite("eval_explanations.py", 87, 109, "the test links, the prediction and "
                         "the selection pred > 0.5, keyed by the pair"),
                ],
                "counted_before_lock": {"script": ds["script"], "record": ds["record"]},
            }
        },
    }  # fmt: skip


def plan(run_seed: str, likes_edges: int, k: int) -> dict:
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
            # torch==1.12.1 (README "Requirements"): wheels for Python 3.7 to 3.10 only
            "python_ladder": ["3.10"],
            "exclude_newer": "2023-07-25",  # the date of the pinned commit
            "base_image": ENGINE_BASE_IMAGE,
            "allowed_patches": [
                {
                    "attachment": "2302-torch-dgl.patch",
                    "reason": "the dependencies the README "
                    "declares (PyTorch = 1.12.1, DGL = 0.9.1) and requirements.txt omits",
                },
                {
                    "attachment": "2302-population-size.patch",
                    "reason": "instrumentation "
                    "(W3.12f): prints len(mask_auc_list) after the mean is printed, with no "
                    "change to the computation",
                },
            ],
        },  # fmt: skip
        "datasets": [dataset_entry(kind, likes_edges, k) for kind in ("value", "comparison")],
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
        "seeds": "each script calls set_seed(0) with no argument: no seed can be changed "
        "without editing the code",
        "data_split": "the split is eids_split with seed 0 fixed in the code, with no argument",
        "ablation": "the claim names no component to disable",
        "holdout": "the test links are fixed by the code's split, with no argument",
        "leakage": "the metric scores explanation masks against ground-truth paths on one "
        "graph; there are no train and test examples of the explainer to compare",
        "trivial_baseline": "the metric is a ROC-AUC of edge masks per pair, not a "
        "single-label classification",
    }
    return [{"name": n, "applies": False, "reason": r} for n, r in reasons.items()]


def source(location: str, quote: str) -> dict:
    return {
        "arxiv_id": ARXIV,
        "version": VERSION,
        "location": location,
        "quote": quote,
        "retrieved_utc": READ,
        "repository_url": REPO,
        "repository_commit": COMMIT,
    }


def metric(k: int, reported: float | None) -> dict:
    out = {
        "name": "auroc",
        "split": SPLIT,
        "unit": "fraction",
        "higher_is_better": True,
        "n_examples": k,
    }
    if reported is not None:
        out["reported"] = reported
        # Table 4 reports one value per cell, no deviation and no seeds (inventory)
        out["reported_uncertainty"] = {"kind": "none"}
    return out


NO_RECOMPUTE = {
    "applies": False,
    "reason": "the explainers save their masks as pickled tensors and no file holds the "
    "per-pair AUCs; the recomputer does not average an AUC per pair",
}


def value_target(candidate_id: str, position: int, reported: float, statement: str, k: int,
                 approvals: dict) -> dict:  # fmt: skip
    t = transcription(candidate_id)
    return {
        "key": f"arXiv-{ARXIV}v{VERSION}-C{position}",
        "type": "value",
        "statement": statement,
        "source": source(t["location"], t["value"]),
        "inventory": {"candidate_id": candidate_id, "position": position, "transcription": t},
        "dataset": DATASETS["value"]["name"],
        "metric": metric(k, reported),
        "comparison_mode": "two_sided",
        # the explainer runs on the repository's own checkpoint (inventory decisions of
        # 2026-10-18: follow the README literally; the checkpoint is a file of the commit),
        # declared as weights of the repository (DEFINITIONS["scope"])
        "scope": "full_training",
        "weights": WEIGHTS["name"],
        "run": run_of(candidate_id),
        "seeds": {"base": [0], "base_cap": 1, "base_source": "documented"},
        "attacks": attacks(),
        "metric_recompute": dict(NO_RECOMPUTE),
        "coverage_evidence": {"method": population_route(NAMES[candidate_id])},
        "approvals": approvals,
    }


def comparison_target(position: int, k: int, approvals: dict) -> dict:
    cid = "T4/UserItemAttr/PaGE-Link>PGExp-Link"
    t = transcription(cid)
    return {
        "key": f"arXiv-{ARXIV}v{VERSION}-C{position}",
        "type": "comparison",
        "statement": f"On UserItemAttr, {PREDICTOR}, the explanations of PaGE-Link have a "
        "higher ROC-AUC against the ground-truth paths than those of PGExp-Link (0.954 "
        "against 0.578); PGExp-Link runs with its mask generator trained, an explicit "
        "correction of the documented command (errata 2, definitions).",
        "source": source(t["location"], "PaGE-Link outperforms both baseline explainers"),
        "inventory": {"candidate_id": cid, "position": position, "transcription": t},
        "dataset": DATASETS["comparison"]["name"],
        "metric": metric(k, None),
        "comparison_mode": "direction",
        "comparison": {
            "method": "PaGE-Link",
            "reference": "PGExp-Link",
            "orientation": "method_minus_reference",
            "reported_method": 0.954,
            "reported_reference": 0.578,
            "uncertainty_method": {"kind": "none"},
            "uncertainty_reference": {"kind": "none"},
            "paired_uncertainty": {"kind": "none"},
            "reference_run": run_of("T4/UserItemAttr/PGExp-Link"),
        },
        "scope": "full_training",
        "weights": WEIGHTS["name"],
        "run": run_of("T4/UserItemAttr/PaGE-Link"),
        "seeds": {"base": [0], "base_cap": 1, "base_source": "documented"},
        "attacks": attacks(),
        "metric_recompute": dict(NO_RECOMPUTE),
        "coverage_evidence": {
            "method": population_route("pagelink"),
            "reference": population_route("pgexp"),
        },
        "approvals": approvals,
    }


def write(out: Path, name: str, data: bytes) -> dict:
    (out / name).write_bytes(data)
    return {"path": name, "sha256": hashlib.sha256(data).hexdigest()}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--likes-edges", type=int, required=True)
    p.add_argument("--count-record", type=Path, required=True, help="the value entry's")
    p.add_argument("--count-record-comparison", type=Path, required=True)
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
    inventory = json.loads(inventory_bytes())
    draw = inv.draw_claims(inventory, claim_seed)
    record = inv.draw_record(draw)
    published = next(d for d in draw_file["draws"] if d["arxiv_id"] == ARXIV)
    if canonical_bytes(record) != canonical_bytes(published):
        raise SystemExit("the draw recomputed differs from claim_draw.json")
    records = {
        "value": a.count_record.read_bytes(),
        "comparison": a.count_record_comparison.read_bytes(),
    }
    counts = {kind: json.loads(data)["count"] for kind, data in records.items()}
    if len(set(counts.values())) != 1:
        raise SystemExit(f"the two count records disagree: {counts}")
    k = counts["value"]

    attachments = [
        {**write(out, "inventory.json", inventory_bytes()), "role": "claim-inventory"},
        {**write(out, "draw.json", canonical_bytes(record)), "role": "claim-draw"},
        {**write(out, ERRATA.name, ERRATA.read_bytes()), "role": "inventory-errata"},
    ]
    for name, digest in PATCHES.items():
        data = (a.patch_dir / name).read_bytes()
        if hashlib.sha256(data).hexdigest() != digest:
            raise SystemExit(f"{name}: SHA-256 differs")
        attachments.append({**write(out, name, data), "role": "allowed-patch"})
    script = (HERE / COUNT_SCRIPT).read_bytes()
    if hashlib.sha256(script).hexdigest() != COUNT_SCRIPT_SHA256:
        raise SystemExit("the count script differs from the one Codex checked")
    for kind, ds in DATASETS.items():
        # the same script bytes under each entry's own name
        attachments.append({**write(out, ds["script"], script), "role": "population-count"})
        attachments.append(
            {**write(out, ds["record"], records[kind]), "role": "population-count-record"}
        )

    approval = json.loads(inventory_bytes())["approval"]
    if a.draft:
        claim_approval = {"approved_by": PLACEHOLDER, "approved_utc": "2000-01-01T00:00:00Z",
                          "approved_commit": "0" * 40}  # fmt: skip
    else:
        claim_approval = {"approved_by": "maintainer", "approved_utc": a.approved_utc,
                          "approved_commit": a.approved_commit}  # fmt: skip
    approvals = {
        "transcription": {
            "approved_by": approval["approved_by"],
            "approved_utc": tt.approved_utc(approval),  # DEFINITIONS, the decision of 10-19
            "approved_commit": approval["approved_commit"],
            "inventory_sha256": inv.inventory_sha256(inventory),
        },
        "claim": claim_approval,
    }
    builders = {
        "T4/UserItemAttr/PaGE-Link": lambda pos: value_target(
            "T4/UserItemAttr/PaGE-Link", pos, 0.954,
            f"On UserItemAttr, {PREDICTOR}, the explanations of PaGE-Link reach a ROC-AUC of "
            "0.954 against the ground-truth paths.", k, approvals),
        "T4/UserItemAttr/GNNExp-Link": lambda pos: value_target(
            "T4/UserItemAttr/GNNExp-Link", pos, 0.608,
            f"On UserItemAttr, {PREDICTOR}, the explanations of GNNExp-Link reach a ROC-AUC of "
            "0.608 against the ground-truth paths.", k, approvals),
        "T4/UserItemAttr/PaGE-Link>PGExp-Link": lambda pos: comparison_target(pos, k, approvals),
    }  # fmt: skip
    targets = [builders[cid](i) for i, cid in enumerate(draw.drawn, start=1)]
    claim = {
        "id": f"v0.3-main-{ARXIV}",
        "kind": "replicate",
        "pack": "ml",
        "title": "PaGE-Link: Path-based Graph Neural Network Explanation for Heterogeneous "
        "Link Prediction (arXiv 2302.12465v3), the three drawn claims",
        "hypothesis": "The drawn claims of Table 4 (UserItemAttr) reproduce from the "
        "repository at the pinned commit, with its saved link predictor.",
        "created": READ[:10],
        "authors": ["refute"],
        "definitions": dict(DEFINITIONS),
        "attachments": attachments,
        "test_plan": plan(seeds.run_seed(claim_seed, ARXIV), a.likes_edges, k),
        "targets": targets,
    }
    path = out / "claim.yaml"
    path.write_text(yaml.safe_dump(claim, sort_keys=False, allow_unicode=False), encoding="utf-8")
    loaded = load_claim(path)
    print("claim.yaml", loaded.sha256(), "draft" if a.draft else "final")
    return 0


if __name__ == "__main__":
    sys.exit(main())
