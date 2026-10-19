"""The claim file of 2309.15704 (MaxWEnt) in the main sample of v0.3: the three drawn claims
(claim_draw.json, round 6563834), written from the frozen inventory, with the engine's own
schema checking the result (load_claim). Each fact comes from a recorded source: the
inventory and its approval, the paper read on arXiv (READ), the repository at the pinned
commit, the datasets Refute downloaded (.cache/data/uci/records.json) and their licences and
sizes (calibration/v0.3/main/sources/2309.15704-data-sources.md).

The repository's command runs the whole configs/uci_all.yml grid (16 settings x 11 methods,
measured at about 154 CPU-hours per run, above the reserve of a claim): the claims are
expected to end INCONCLUSIVE by the budget (the maintainer's decision of 2026-10-18), and
are written in full all the same.

Usage (from the repository's root, the project's environment):
  .venv/Scripts/python.exe calibration/v0.3/main/claims/2309.15704/make_claim.py \\
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
ARXIV, VERSION = "2309.15704", 2
REPO = "https://github.com/antoinedemathelin/maxwent-expe"
COMMIT = "c67aa620a64e139d8599613e24cc57b34af5b67f"  # main_walk_batch_13.json, position 309
# https://arxiv.org/html/2309.15704v2, Table 2, read by the agent between 01:51:45 and this time
READ = "2026-10-19T01:53:17Z"
INVENTORY = ROOT / "calibration/v0.3/main/inventories/2309.15704.json"
DRAW = ROOT / "calibration/v0.3/main/claim_draw.json"
PATCH = ("2309-uci-files.patch",
         "05413b6a4bd65cf26cc79c69dc0a9c1f5e7e5d0d4ee8a0d028f8e4c6e30c4a8f")  # fmt: skip
PLACEHOLDER = "pending: the maintainer's approval of the claims package (draft only)"
UCI = "Dua and Graff, UCI Machine Learning Repository"
KIN8NM_LICENCE = (
    "OpenML licence field 'Public' (data 189); the original source, DELVE (University of "
    "Toronto), permits use and copying for non-commercial purposes only"
)
# (name in the claim, url, sha256, size, retrieved, licence, version, splits)
DATASETS = [
    ("UCI energy (downloaded by uci_datasets.py from archive.ics.uci.edu, CC BY 4.0)",
     "https://archive.ics.uci.edu/static/public/242/energy+efficiency.zip",
     "499441eee27929a4b00417f58fd8c63c9cc14b8a71520cd0dd27fcb626738351", 76321,
     "2026-10-18T21:25:14Z", "CC BY 4.0", "UCI dataset 242",
     {"rows": (768, "reader:container:excel:ENB2012_data.xlsx#0")}),
    ("UCI wine (downloaded by uci_datasets.py from archive.ics.uci.edu, CC BY 4.0)",
     "https://archive.ics.uci.edu/static/public/186/wine+quality.zip",
     "3ed56667f4b828242bd732d7d1dd7f2861e54432239d7fa63877014cbb0304d4", 91353,
     "2026-10-18T21:25:16Z", "CC BY 4.0", "UCI dataset 186 (the red wine file)",
     {"rows": (1599, "reader:zip:winequality-red.csv!lines:rows-1")}),
    ("UCI naval (downloaded by uci_datasets.py from a GitHub copy (trewaite/Naval-Vessel-"
     "Maintenance at 15bb3ed, 'UCI CBM Dataset/data.txt'); original source UCI dataset 316, "
     "CC BY 4.0)",
     "https://raw.githubusercontent.com/trewaite/Naval-Vessel-Maintenance/"
     "15bb3ed4ba49c9b82e6648e73218232cbe1138a8/UCI%20CBM%20Dataset/data.txt",
     "de0ea69da1efaab8b9655ffed828547d10dd68c1fb8c6e0163e6a988def393a6", 3448926,
     "2026-10-18T21:25:20Z", "CC BY 4.0 (the original source, UCI dataset 316)",
     "the copy at 15bb3ed of trewaite/Naval-Vessel-Maintenance",
     {"rows": (11934, "reader:lines:rows")}),
    ("UCI yacht", "https://archive.ics.uci.edu/static/public/243/yacht+hydrodynamics.zip",
     "aa52b68f88c4bb552187a53ef4c5753fa178f6a36035a3771c5bc04e078487ac", 11633,
     "2026-10-18T21:25:13Z", "CC BY 4.0", "UCI dataset 243",
     {"rows": (308, "reader:zip:yacht_hydrodynamics.data!lines:rows")}),
    ("UCI concrete",
     "https://archive.ics.uci.edu/static/public/165/concrete+compressive+strength.zip",
     "dad85d14de8aee4e07479daa774e6b569a313715b71a3b92c95a07cf91c2c9a7", 34444,
     "2026-10-18T21:25:14Z", "CC BY 4.0", "UCI dataset 165",
     {"rows": (1030, "reader:container:excel:Concrete_Data.xls#0")}),
    ("UCI power", "https://archive.ics.uci.edu/static/public/294/combined+cycle+power+plant.zip",
     "cc7b2a4977c0a44e8221c91d9a7e5746b3c68186cff7e5c61c70af6432b98c7a", 3674852,
     "2026-10-18T21:25:18Z", "CC BY 4.0", "UCI dataset 294",
     {"rows": (9568, "reader:container:excel:CCPP/Folds5x2_pp.xlsx#0")}),
    ("UCI protein",
     "https://archive.ics.uci.edu/static/public/265/"
     "physicochemical+properties+of+protein+tertiary+structure.zip",
     "ee6536c8cc415dc50d66bd247af7c9bc95c187ab8a4ea0f1f546b127206c1100", 3528824,
     "2026-10-18T21:25:20Z", "CC BY 4.0", "UCI dataset 265",
     {"rows": (45730, "reader:zip:CASP.csv!lines:rows-1")}),
    ("OpenML kin8nm", "https://www.openml.org/data/download/3626/dataset_2175_kin8nm.arff",
     "698fb5297abde73c001b07f8fb2fe31626366cf179678aed0990737cc0689c79", 1131204,
     "2026-10-18T21:25:23Z", KIN8NM_LICENCE,
     "OpenML data 189, file 3626", {"rows": (8192, "reader:arff:rows")}),
]  # fmt: skip
# the interpolation population auc_ood is computed on (the in-distribution test set and the
# OOD set; utils.py lines 177-234): sizes from the rows and uci_interpol's cut (datasets.py
# lines 208-232; sklearn train_test_split: n_train = floor(0.9 n), n_test the rest)
INTERPOLATION = {"energy": 423, "wine": 880, "naval": 6564}
CANDIDATES = {
    "T2/Interpolation/energy/Ensemble/AN": ("energy", "AnchoredNetwork", 98.7,
                                            "Anchored-Networks (an ensemble)"),
    "T2/Interpolation/wine/Bayesian Ensemble/BN": ("wine", "BNN5", 33.9, "a BNN ensemble (x5)"),
    "T2/Interpolation/naval/Bayesian Ensemble/BN": ("naval", "BNN5", 46.9, "a BNN ensemble (x5)"),
}  # fmt: skip


def cite(file: str, first: int, last: int, role: str) -> dict:
    return {"file": file, "lines": [first, last], "role": role}


def candidates() -> dict:
    return {c["candidate_id"]: c for c in json.loads(INVENTORY.read_bytes())["candidates"]}


def dataset_name(short: str) -> str:
    return next(d[0] for d in DATASETS if d[0].startswith(f"UCI {short} "))


def dataset_entry(row: tuple) -> dict:
    name, url, digest, size, retrieved, licence, version, splits = row
    out = {
        "name": name,
        "url": url,
        "reference": UCI if "UCI" in name else "Vanschoren et al., OpenML",
        "version": version,
        "license": licence,
        "retrieved_utc": retrieved,
        "sha256": digest,
        "size_bytes": size,
        "local_copy_allowed": True,
        "splits": {k: {"expected_examples": n, "source": s} for k, (n, s) in splits.items()},
    }
    short = next((k for k in INTERPOLATION if name.startswith(f"UCI {k} ")), None)
    if short is not None:
        out["derived_splits"] = {
            "interpolation": {
                "expected_examples": INTERPOLATION[short],
                "derived_from": ["rows"],
                "rule": "the in-distribution test set and the OOD set of uci_interpol: the rows "
                "sorted along the first principal component of the standardized features; OOD "
                "the middle 50% (indices int(0.25 n) to int(0.75 n)), in-distribution the rest, "
                "of which train_test_split with train_size 0.9 (seed: state 0) keeps the test "
                "part; auc_ood scores the test set against the OOD set",
                "code": [
                    cite("datasets.py", 208, 232, "uci_interpol: the cut and the splits"),
                    cite("utils.py", 177, 234, "results_regression: auc_ood on xtest "
                         "against xood"),
                    cite("utils.py", 238, 243, "auroc_score: one label per scored example"),
                ],
            }
        }  # fmt: skip
    return out


def plan(run_seed: str) -> dict:
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
            # tensorflow==2.12 (requirements.txt): wheels up to Python 3.11, the version
            # the budget measurement built with (budget-measurements/mwe-build.json)
            "python_ladder": ["3.11"],
            "exclude_newer": "2025-02-12",  # the date of the pinned commit
            "base_image": ENGINE_BASE_IMAGE,
            "allowed_patches": [
                {
                    "attachment": PATCH[0],
                    "reason": "the origin of the bytes: the URLs of "
                    "uci_datasets.py read the files Refute downloaded, verified and mounted in "
                    "the run's folder (data/uci/), with no other change (Codex, line by line)",
                },
            ],
        },  # fmt: skip
        "datasets": [dataset_entry(row) for row in DATASETS],
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
        "seeds": "run.py takes no seed: the grid runs state 0 (n_runs 1 in configs/uci_all.yml)",
        "data_split": "the split is uci_interpol's cut with the state of the run, with no "
        "argument of its own",
        "ablation": "the claim names no component to disable",
        "holdout": "the in-distribution and OOD sets are cut by the code, with no argument",
        "leakage": "the populations are cut from one file by the code; the claim's split is "
        "derived, with no train and test files to compare",
        "trivial_baseline": "the metric is an AUROC of OOD detection from predicted "
        "uncertainty, not a single-label classification",
    }
    return [{"name": n, "applies": False, "reason": r} for n, r in reasons.items()]


def target(cid: str, position: int, approvals: dict) -> dict:
    short, method_key, reported, method_text = CANDIDATES[cid]
    t = dict(candidates()[cid]["transcription"])
    return {
        "key": f"arXiv-{ARXIV}v{VERSION}-C{position}",
        "type": "value",
        "statement": f"In the interpolation setting of the UCI {short} dataset, {method_text} "
        f"detects out-of-distribution inputs with an AUROC of {reported}%.",
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
        "dataset": dataset_name(short),
        "metric": {
            "name": "auroc",
            "split": "interpolation",
            "unit": "percent",
            "higher_is_better": True,
            "reported": reported,
            # "Each experiment is performed only once" (section 7.2.2): no uncertainty
            "reported_uncertainty": {"kind": "none"},
            "reported_n_seeds": 1,
            "n_examples": INTERPOLATION[short],
        },
        "comparison_mode": "two_sided",
        "scope": "full_training",
        "run": {
            "argv": json.loads(t["command"]),
            "workdir": ".",
            "seed_argument": None,
            "metric_extraction": {
                "from": "file",
                # train.py line 291: pd.Series(config).to_csv(logs/<save_path>.csv), the
                # header row ",0", one row per key; save_path results/uci/<setting>_<run>_<state>
                "file": f"logs/results/uci/{short}_interpol_{method_key}_0.csv",
                "csv": {"column": "0", "row": {"column": "", "equals": "auc_ood"}},
                "unit": "fraction",
            },
        },
        "seeds": {"base": [0], "base_cap": 1, "base_source": "documented"},
        "attacks": attacks(),
        "metric_recompute": {
            "applies": False,
            "reason": "the repository saves the scores of the run, not the per-example "
            "uncertainties auc_ood is computed from",
        },
        "coverage_evidence": {
            "method": {
                "selected_evaluation": {"kind": "final"},
                "routes": [
                    {
                        "route": "printed_count",
                        "count": {
                            "from": "log",
                            "regex": {"pattern": r"(?m)^ood examples scored=([0-9]+)$", "group": 1},
                        },
                        "link": [
                            cite(
                                "utils.py",
                                177,
                                234,
                                "results_regression scores xtest "
                                "and xood and prints no count of the examples it "
                                "scores, so this declared route finds none: "
                                "metric_extracted is then INCONCLUSIVE by coverage",
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
        "title": "Deep Out-of-Distribution Uncertainty Quantification via Weight Entropy "
        "Maximization (arXiv 2309.15704v2), the three drawn claims",
        "hypothesis": "The drawn claims of Table 2 (UCI, interpolation) reproduce from the "
        "repository at the pinned commit.",
        "created": READ[:10],
        "authors": ["refute"],
        "definitions": {"transcription_approval_time": tt.DEFINITION},
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
