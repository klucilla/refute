"""ML claim schema (WP3, docs/validation/v0.3/wp3-acceptance.md, section 1.0 and the
schema cases of section 2), offline."""

import copy
import json
import math
from decimal import Decimal

import pytest
import yaml

from refute.core.canonical import canonical_bytes
from refute.core.claim import ClaimError, load_claim
from refute.core.hashing import sha256_bytes
from refute.core.pack import DomainPack
from refute.packs.ml import rules, seeds
from refute.packs.ml.schema import MlClaimSchema
from refute.packs.ml.uncertainty import Uncertainty, resolve_uncertainty
from refute.selection import inventory as inv

PACK = DomainPack(
    name="ml",
    version="test",
    description="ML schema under test",
    schema=MlClaimSchema(),
    adapter=None,
    search=None,
    gauntlet=None,
    holdout=None,
    exporter=None,
    analyzer=None,
    calibrator=None,
)
CLAIM_SEED = bytes(range(32))
ARXIV = "2401.01234"
REPO = "https://github.com/example/repo"
COMMIT = "a" * 40
STAMP = "2026-10-15T00:00:00Z"
LABELS = list(range(10))
# synthetic SHA-256 hashes of the labels of the claim's split and of the other split (1.5a;
# the run compares them, the schema cannot)
LABELS_SHA256 = "b" * 64
OTHER_LABELS_SHA256 = "c" * 64
CITE = {"file": "src/eval.py", "lines": [40, 52], "role": "counts the evaluated examples"}
FINAL = {"kind": "final"}


def hook_evidence(function):
    """(b) alone, for one method: the patch is not declared in test_plan by default."""
    return {
        "selected_evaluation": dict(FINAL),
        "routes": [
            {
                "route": "hook",
                "patch": "hook.patch",
                "function": function,
                "call_site": dict(CITE),
                "link": [dict(CITE)],
            }
        ],
        "split_identity": split_identity(),
    }


def split_identity():
    return {
        "labels_sha256": LABELS_SHA256,
        "other_splits": [{"name": "train", "labels_sha256": OTHER_LABELS_SHA256}],
        "splits_evidence": [
            {"file": "src/data.py", "lines": [10, 18], "role": "the splits the code can load"}
        ],
    }


def printed_count(pattern=r"evaluated=(\d+)"):
    """(a): a count the run prints, with the cited code from the counter to the output."""
    return {
        "route": "printed_count",
        "count": {"from": "log", "regex": {"pattern": pattern, "group": 1}},
        "link": [dict(CITE)],
    }


TRANSCRIPTIONS = {
    "c1": {
        "value": "91.2",
        "location": "Table 2, row Ours, column CIFAR-10",
        "metric": "accuracy",
        "split": "test",
        "command": '["python", "train.py", "--seed={seed}"]',
    },
    "c2": {
        "value": "91.2 vs 89.0",
        "location": "Table 2, rows Ours and ResNet, column CIFAR-10",
        "metric": "accuracy",
        "split": "test",
        "command": '["python", "train.py", "--seed={seed}"]',
    },
}


def inventory():
    return {
        "format": inv.FORMAT,
        "paper": {"arxiv_id": ARXIV, "version": 2},
        "candidates": [
            {
                "candidate_id": "c1",
                "reading_order": 1,
                "type": "value",
                "transcription": dict(TRANSCRIPTIONS["c1"]),
                "method": "Ours",
                "dataset": "CIFAR-10",
                "conditions": "the repository's training script, 3 seeds",
            },
            {
                "candidate_id": "c2",
                "reading_order": 2,
                "type": "comparison",
                "transcription": dict(TRANSCRIPTIONS["c2"]),
                "method": "Ours",
                "dataset": "CIFAR-10",
                "conditions": "the repository's training script, 3 seeds",
                "reference": "ResNet",
                "eligible_comparison": True,
            },
        ],
        "approval": {
            "approved_by": "maintainer",
            "approved_utc": STAMP,
            "approved_commit": "e" * 40,
            "approval_record": "https://github.com/example/repo/issues/2#issuecomment-3",
        },
    }


def stage():
    return {"active_time_limit_hours": 10, "retries": 1}


def test_plan():
    return {
        "paper": {
            "arxiv_id": ARXIV,
            "version": 2,
            "run_seed_sha256": seeds.run_seed(CLAIM_SEED, ARXIV),
        },
        "budget": {"profile": "main"},
        "repository": {
            "url": REPO,
            "commit": COMMIT,
            "latest_commit_at_draw": "b" * 40,
            "version_basis": "latest_at_draw",
        },
        "build": {
            "python_ladder": ["3.10", "3.11"],
            "exclude_newer": "2024-01-15",
            "base_image": "python@sha256:" + "c" * 64,
            "allowed_patches": [],
        },
        "datasets": [
            {
                "name": "cifar10",
                "url": "https://example.org/cifar10",
                "reference": "Krizhevsky 2009",
                "version": "1",
                "license": "MIT",
                "retrieved_utc": STAMP,
                "sha256": "d" * 64,
                "size_bytes": 1000,
                "local_copy_allowed": True,
                "splits": {
                    "train": {"expected_examples": 50000, "source": "paper, section 4"},
                    "test": {"expected_examples": 10000, "source": "paper, section 4"},
                },
            }
        ],
        "stages": {
            name: stage()
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


def attacks(**applies):
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
            "labels": LABELS,
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


def approvals(inventory_hash):
    return {
        "transcription": {
            "approved_by": "maintainer",
            "approved_utc": STAMP,
            "approved_commit": "e" * 40,
            "inventory_sha256": inventory_hash,
        },
        "claim": {"approved_by": "maintainer", "approved_utc": STAMP, "approved_commit": "f" * 40},
    }


def source(location):
    return {
        "arxiv_id": ARXIV,
        "version": 2,
        "location": location,
        "quote": "91.2",
        "retrieved_utc": STAMP,
        "repository_url": REPO,
        "repository_commit": COMMIT,
    }


def run_block():
    return {
        "argv": ["python", "train.py"],
        "workdir": ".",
        "seed_argument": "--seed={seed}",
        "metric_extraction": {
            "from": "log",
            "regex": {"pattern": r"acc=([0-9.]+)", "group": 1},
            "unit": "percent",
        },
    }


def value_claim(inventory_hash, position):
    return {
        "key": f"arXiv-{ARXIV}v2-C1",
        "type": "value",
        "statement": "The method reaches 91.2% test accuracy on CIFAR-10.",
        "source": source(TRANSCRIPTIONS["c1"]["location"]),
        "inventory": {
            "candidate_id": "c1",
            "position": position,
            "transcription": dict(TRANSCRIPTIONS["c1"]),
        },
        "dataset": "cifar10",
        "metric": {
            "name": "accuracy",
            "split": "test",
            "unit": "percent",
            "higher_is_better": True,
            "reported": 91.2,
            "reported_uncertainty": {
                "kind": "sd",
                "value": 0.3,
                "unit": "percent",
                "location": "Table 2",
                "quote": "91.2 ± 0.3",
            },
            "reported_n_seeds": 3,
            "n_examples": 10000,
        },
        "comparison_mode": "two_sided",
        "scope": "full_training",
        "run": run_block(),
        "seeds": {"base": [1, 2, 3], "base_cap": 3, "base_source": "documented"},
        "attacks": attacks(seeds=True, holdout=True, leakage=True, trivial_baseline=True),
        "metric_recompute": {
            "applies": True,
            "reason": "the repository saves its predictions",
            "predictions": {
                "file": "preds/{seed}.npy",
                "format": "npy",
                "fields": {"y_true": "t", "y_pred": "p"},
            },
            "convention": {"metric": "accuracy", "scale": "percent", "labels": LABELS},
        },
        "coverage_evidence": {
            "method": {
                "selected_evaluation": dict(FINAL),
                "routes": [
                    {
                        "route": "saved_predictions",
                        "link": [dict(CITE, role="writes the test predictions it prints from")],
                    },
                    printed_count(),
                ],
                "split_identity": split_identity(),
            }
        },
        "approvals": approvals(inventory_hash),
    }


def comparison_claim(inventory_hash, position):
    return {
        "key": f"arXiv-{ARXIV}v2-C2",
        "type": "comparison",
        "statement": "The method beats ResNet by 2.2 points on CIFAR-10.",
        "source": source(TRANSCRIPTIONS["c2"]["location"]),
        "inventory": {
            "candidate_id": "c2",
            "position": position,
            "transcription": dict(TRANSCRIPTIONS["c2"]),
        },
        "dataset": "cifar10",
        "metric": {
            "name": "accuracy",
            "split": "test",
            "unit": "percent",
            "higher_is_better": True,
            "reported_n_seeds": 3,
            "n_examples": 10000,
        },
        "comparison_mode": "margin",
        "comparison": {
            "method": "Ours",
            "reference": "ResNet",
            "orientation": "method_minus_reference",
            "reported_method": 91.2,
            "reported_reference": 89.0,
            "uncertainty_method": {"kind": "none"},
            "uncertainty_reference": {"kind": "none"},
            "g_pub": 2.2,
            "paired_uncertainty": {"kind": "none"},
            "reference_run": {
                "same": True,
                "metric_extraction": {
                    "from": "log",
                    "regex": {"pattern": r"ref_acc=([0-9.]+)", "group": 1},
                    "unit": "percent",
                },
            },
        },
        "scope": "full_training",
        "run": run_block(),
        "seeds": {"base": [1, 2, 3], "base_cap": 3, "base_source": "documented"},
        "attacks": attacks(seeds=True, holdout=True),
        "metric_recompute": {
            "applies": False,
            "reason": "the repository saves the predictions of one method only",
        },
        "coverage_evidence": {
            "method": {"selected_evaluation": dict(FINAL), "routes": [printed_count()]},
            "reference": {
                "selected_evaluation": dict(FINAL),
                "routes": [printed_count(r"ref_evaluated=(\d+)")],
            },
        },
        "approvals": approvals(inventory_hash),
    }


def build_claim(tmp_path, mutate=None, files=None):
    """Writes a valid claim (two drawn claims), applies ``mutate`` to the claim dict, and
    returns its path. ``files`` may replace the inventory or draw records."""
    files = files or {}
    inventory_record = files.get("inventory", inventory())
    digest = inv.inventory_sha256(inventory())
    draw = inv.draw_claims(inventory(), CLAIM_SEED)
    draw_record = files.get("draw", inv.draw_record(draw))
    attachments = []
    for role, name, record in (
        ("claim-inventory", "inventory.json", inventory_record),
        ("claim-draw", "draw.json", draw_record),
    ):
        data = record if isinstance(record, bytes) else canonical_bytes(record)
        (tmp_path / name).write_bytes(data)
        attachments.append({"path": name, "role": role, "sha256": sha256_bytes(data)})
    builders = {"c1": value_claim, "c2": comparison_claim}
    targets = [builders[cid](digest, i) for i, cid in enumerate(draw.drawn, start=1)]
    claim = {
        "id": "ml-test",
        "kind": "replicate",
        "pack": "ml",
        "title": "ML schema test",
        "hypothesis": "The drawn claims of the paper reproduce.",
        "created": "2026-10-15",
        "authors": ["refute"],
        "attachments": attachments,
        "test_plan": test_plan(),
        "targets": targets,
    }
    if mutate is not None:
        mutate(claim)
    path = tmp_path / "claim.yaml"
    path.write_text(yaml.safe_dump(claim, sort_keys=False), encoding="utf-8")
    return path


def load(tmp_path, mutate=None, files=None):
    return load_claim(build_claim(tmp_path, mutate, files), pack=PACK)


def target(claim, cid):
    return next(t for t in claim["targets"] if t["inventory"]["candidate_id"] == cid)


def attack(t, name):
    return next(a for a in t["attacks"] if a["name"] == name)


# ---- must pass ----------------------------------------------------------------------------


def test_a_valid_claim_resolves_with_every_default_written_out(tmp_path):
    loaded = load(tmp_path)
    claim = loaded.canonical()
    plan = claim["test_plan"]
    assert plan["build"]["ladder"] == [
        "own_environment",
        "requirements_compiled",
        "requirements_compiled_next_python",
    ]
    assert plan["budget"] == {
        "profile": "main",
        "paper_cpu_hours": 384.0,
        "base_cpu_hours": 192.0,
        "attacks_cpu_hours": 192.0,
    }
    assert plan["stages"]["build"] == {
        "active_time_limit_hours": 10.0,
        "no_progress_hours": 2.0,
        "progress_signal": "cpu_or_output",
        "retries": 1,
    }
    value = target(claim, "c1")
    assert value["tolerance"] == {
        "rel_tol": 0.02,
        "k_sd": 2.0,
        "abs_floor": 0.5,
        "override_reason": None,
    }
    assert value["metric_recompute"]["printed_rounding"] == "nearest"
    assert value["metric"]["reported_uncertainty"]["status"] == "converted"
    assert value["metric"]["reported_uncertainty"]["sd"] == pytest.approx(0.3)
    names = list(value["coverage_minimum"])
    assert names == [
        "environment_build",
        "data_present",
        "run_completed",
        "metric_extracted",
        "base_reproduction",
        "metric_recompute",
        "seeds",
        "seeds:run",
        "seeds:metric",
        "holdout",
        "holdout:run",
        "holdout:metric",
        "leakage",
        "leakage:run",
        "leakage:metric",
        "trivial_baseline",
        "trivial_baseline:run",
        "trivial_baseline:metric",
    ]
    assert value["coverage_minimum"]["base_reproduction"] == {"positive": 3, "negative": 3}
    assert value["coverage_minimum"]["metric_recompute"] == {"positive": 3, "negative": 1}
    assert value["coverage_minimum"]["seeds"] == {"positive": 1, "negative": 1}
    # derived seeds (1.0.4) and the holdout rule (1.0.10) are written out
    run_seed = plan["paper"]["run_seed_sha256"]
    assert value["seeds"]["attack"] == seeds.derived_seeds(run_seed, "seeds", 5, [1, 2, 3])
    assert len(value["seeds"]["data_split"]) == 3 and len(value["seeds"]["holdout"]) == 1
    holdout = attack(value, "holdout")["params"]
    assert holdout["fraction"] == 0.1 and holdout["m"] == 5000
    assert holdout["factor"] == pytest.approx(math.sqrt(10000 / 5000))
    comparison = target(claim, "c2")
    assert comparison["comparison"]["paired_uncertainty"]["status"] == "none"
    assert "metric_recompute" not in comparison["coverage_minimum"]


def test_resolution_is_deterministic(tmp_path):
    a = load(tmp_path).sha256()
    b = load(tmp_path).sha256()
    assert a == b


def test_derived_seed_lists_may_be_given_when_they_equal_the_derivation(tmp_path):
    run_seed = seeds.run_seed(CLAIM_SEED, ARXIV)

    def give(claim):
        for t in claim["targets"]:
            t["seeds"]["attack"] = seeds.derived_seeds(run_seed, "seeds", 5, [1, 2, 3])

    load(tmp_path, give)


def test_derived_base_seeds(tmp_path):
    run_seed = seeds.run_seed(CLAIM_SEED, ARXIV)

    def derived(claim):
        for t in claim["targets"]:
            t["seeds"] = {
                "base": seeds.derived_seeds(run_seed, "base", 3),
                "base_cap": 3,
                "base_source": "derived",
            }

    load(tmp_path, derived)


def test_allowed_patch_attachment(tmp_path):
    def patch(claim):
        (tmp_path / "fix.patch").write_text("--- a\n+++ b\n")
        claim["attachments"].append({"path": "fix.patch", "role": "allowed-patch"})
        claim["test_plan"]["build"]["allowed_patches"] = [
            {"attachment": "fix.patch", "reason": "pins a removed URL"}
        ]

    load(tmp_path, patch)


def test_the_coverage_evidence_is_written_out_with_its_default_rule(tmp_path):
    """1.5a: the routes of each method are kept in their order, and the rule for
    conflicting evidence is written out (all_must_agree, the only rule of v0.3)."""
    claim = load(tmp_path).canonical()
    value = target(claim, "c1")["coverage_evidence"]
    assert [r["route"] for r in value["method"]["routes"]] == ["saved_predictions", "printed_count"]
    assert value["method"]["conflict_rule"] == "all_must_agree"
    assert value["method"]["split_identity"]["labels_sha256"] == LABELS_SHA256
    assert value["method"]["selected_evaluation"] == {"kind": "final", "value": None}
    assert value["method"]["complementary"] == []
    assert value["reference"] is None
    comparison = target(claim, "c2")["coverage_evidence"]
    assert comparison["reference"]["routes"][0]["count"]["regex"]["pattern"] == (
        r"ref_evaluated=(\d+)"
    )


def test_every_route_in_its_order_with_complementary_evidence(tmp_path):
    """The four routes together, in the fixed order (c), (d), (a), (b): the hook names an
    allowed patch, the observed function of its metric and the call that is the selected
    evaluation; a dataset read trace is complementary evidence."""

    def every_route(claim):
        (tmp_path / "hook.patch").write_text("--- a\n+++ b\n")
        claim["attachments"].append({"path": "hook.patch", "role": "allowed-patch"})
        claim["test_plan"]["build"]["allowed_patches"] = [
            {"attachment": "hook.patch", "reason": "observes accuracy_score in the container"}
        ]
        stats_file = "out/stats_{seed}.json"
        target(claim, "c1")["coverage_evidence"]["method"] = {
            "selected_evaluation": {"kind": "checkpoint", "value": "ckpt/best_{seed}.pt"},
            "routes": [
                {"route": "saved_predictions", "link": [dict(CITE)]},
                {
                    "route": "sufficient_statistics",
                    "correct": {"from": "file", "file": stats_file, "json_path": "$.correct"},
                    "total": {"from": "file", "file": stats_file, "json_path": "$.total"},
                    "link": [dict(CITE, role="writes correct and total of the test evaluation")],
                },
                printed_count(),
                {
                    "route": "hook",
                    "patch": "hook.patch",
                    "function": "sklearn.metrics.accuracy_score",
                    "call_site": dict(CITE, lines=[48, 48], role="the test evaluation call"),
                    "link": [dict(CITE, lines=[48, 52], role="prints the call's return")],
                },
            ],
            "split_identity": split_identity(),
            "complementary": ["dataset_read_trace"],
        }

    claim = load(tmp_path, every_route).canonical()
    routes = target(claim, "c1")["coverage_evidence"]["method"]["routes"]
    assert [r["route"] for r in routes] == [
        "saved_predictions",
        "sufficient_statistics",
        "printed_count",
        "hook",
    ]


def test_a_claim_without_seed_option_runs_once(tmp_path, monkeypatch):
    monkeypatch.setitem(TRANSCRIPTIONS["c1"], "command", '["python", "train.py"]')

    def no_seed(claim):
        t = target(claim, "c1")
        t["run"]["seed_argument"] = None
        t["seeds"]["base"] = [1]
        t["seeds"]["base_cap"] = 1
        attack(t, "seeds").update(applies=False)
        attack(t, "seeds").pop("params")
        t["metric_recompute"]["predictions"]["file"] = "preds/p.npy"

    loaded = load(tmp_path, no_seed)
    value = target(loaded.canonical(), "c1")
    assert value["coverage_minimum"]["base_reproduction"] == {"positive": 1, "negative": 1}


# ---- seeds (1.0.2, 1.0.4): recorded values ----------------------------------------------------

# Recorded on 2026-10-15 from the formula of 1.0.2 (regression values: a change of the
# formula, the domain string or the byte layout changes them).
RECORDED_RUN_SEED = "ea5f422fd077eef68d2cdf48528610d5b1c057658341c55eea8f5673e8cc78cd"


def test_run_seed_is_recorded_and_differs_from_the_draw_seed():
    value = seeds.run_seed(CLAIM_SEED, ARXIV)
    assert value == RECORDED_RUN_SEED
    # the formula, written out independently: sha256(seed || "refute/v0.3/runs" || id)
    import hashlib

    assert value == hashlib.sha256(CLAIM_SEED + b"refute/v0.3/runs" + b"2401.01234").hexdigest()
    draw_seed = inv.draw_seed(CLAIM_SEED, ARXIV)
    assert int(value, 16) != draw_seed


RECORDED_DERIVED = {
    "base": [1682078425, 1086819446, 1485235142],
    "seeds": [227762419, 1707632574, 1477631509, 537010992, 184707613],
    "data_split": [1974123531, 76345666, 1822092505],
    "holdout": [414533134],
}


def test_derived_seed_lists_are_recorded():
    run_seed = seeds.run_seed(CLAIM_SEED, ARXIV)
    got = {
        "base": seeds.derived_seeds(run_seed, "base", 3),
        "seeds": seeds.derived_seeds(run_seed, "seeds", 5, [1, 2, 3]),
        "data_split": seeds.derived_seeds(run_seed, "data_split", 3, [1, 2, 3]),
        "holdout": seeds.derived_seeds(run_seed, "holdout", 1, [1, 2, 3]),
    }
    assert got == RECORDED_DERIVED


def test_derived_seeds_skip_the_excluded_values():
    run_seed = seeds.run_seed(CLAIM_SEED, ARXIV)
    first = seeds.derived_seeds(run_seed, "seeds", 1)
    assert first[0] not in seeds.derived_seeds(run_seed, "seeds", 3, first)


# ---- uncertainty (1.0.9): recorded conversions -------------------------------------------------


def unc(**kw):
    base = {"location": "Table 2", "quote": "as printed", "unit": "percent"}
    base.update(kw)
    return Uncertainty.model_validate(base)


def test_uncertainty_conversions():
    assert resolve_uncertainty(unc(kind="sd", value=0.3), "percent", 91.2)["sd"] == pytest.approx(
        0.3
    )
    se = resolve_uncertainty(unc(kind="se", value=0.2, n=4), "percent", 91.2)
    assert se["status"] == "converted" and se["sd"] == pytest.approx(0.4)
    # 95% t interval, n = 5: t(0.975, 4) = 2.776 (NIST e-Handbook, table of t)
    ci = resolve_uncertainty(
        unc(kind="ci", lower=90.0, upper=92.0, level=0.95, method="t", n=5), "percent", 91.0
    )
    assert ci["quantile"] == pytest.approx(2.776, abs=5e-4)
    assert ci["sd"] == pytest.approx(2.0 / (2 * ci["quantile"]) * math.sqrt(5))
    # 90% t interval: t(0.95, 4) = 2.132
    ci90 = resolve_uncertainty(
        unc(kind="ci", lower=90.0, upper=92.0, level=0.90, method="t", n=5), "percent", 91.0
    )
    assert ci90["quantile"] == pytest.approx(2.132, abs=5e-4)
    # 95% normal interval: z(0.975) = 1.960
    z = resolve_uncertainty(
        unc(kind="ci", lower=90.0, upper=92.0, level=0.95, method="normal", n=30), "percent", 91.0
    )
    assert z["quantile"] == pytest.approx(1.960, abs=5e-4)
    # printed in fraction for a claim in percent
    frac = resolve_uncertainty(unc(kind="sd", value=0.003, unit="fraction"), "percent", 91.2)
    assert frac["sd"] == pytest.approx(0.3)


@pytest.mark.parametrize(
    "record",
    [
        dict(kind="se", value=2.0),  # no n
        dict(kind="ci", lower=90.0, upper=92.0, level=0.95, method="other_or_unknown", n=5),
        dict(kind="ci", lower=89.0, upper=92.0, level=0.95, method="t", n=5),  # asymmetric
    ],
)
def test_reported_but_not_convertible(record):
    out = resolve_uncertainty(unc(**record), "percent", 91.0)
    assert out["status"] == "not_convertible" and out["sd"] is None


def test_none_means_no_uncertainty():
    out = resolve_uncertainty(Uncertainty(kind="none"), "percent", 91.0)
    assert out["status"] == "none"


@pytest.mark.parametrize("field", ["unit", "location", "quote"])
def test_a_none_record_has_nothing_to_locate_or_quote(field):
    """'none' means the paper publishes no uncertainty for the value (not an unknown one):
    an uncertainty unit, location or quote is refused (1.0.9, the maintainer, 2026-10-16)."""
    value = "percent" if field == "unit" else "Table 2"
    with pytest.raises(ValueError, match=f"takes no {field}"):
        Uncertainty.model_validate({"kind": "none", field: value})


@pytest.mark.parametrize(
    "record",
    [
        dict(kind="var", value=1.0),
        dict(kind="ci", lower=90.0, upper=92.0, level=0.95, method="bootstrap", n=5),
        dict(kind="se", value=1.0, n=1),
        dict(kind="ci", lower=92.0, upper=90.0, level=0.95, method="t", n=5),
        dict(kind="ci", lower=90.0, upper=92.0, level=1.0, method="t", n=5),
        dict(kind="sd", value=-0.1),
        dict(kind="se", value=-0.1, n=5),
        dict(kind="sd", value=0.3, location=None),
        dict(kind="sd", value=0.3, quote=None),
        dict(kind="sd", value=0.3, sd=0.3),  # derived fields are never given
    ],
)
def test_invalid_uncertainty_records(record):
    with pytest.raises(ValueError):
        unc(**record)


# ---- holdout and baseline rules ----------------------------------------------------------------


def test_holdout_rule():
    assert rules.holdout_size(50000) == 5000
    assert rules.holdout_factor(10000, 5000) == pytest.approx(math.sqrt(2))
    assert rules.holdout_size(1500) == 150
    assert rules.holdout_factor(10000, 150) == pytest.approx(math.sqrt(10000 / 150))
    assert rules.holdout_factor(100, 5000) == 1.0  # m >= n_examples
    assert rules.holdout_size(999) == 99
    for m in (0, 99):
        with pytest.raises(ValueError):
            rules.holdout_factor(10000, m)


@pytest.mark.parametrize(
    ("n_examples", "m", "expected_hex"),
    [
        (50, 100, "0x1.0000000000000p+0"),  # n_examples < m: the factor is 1
        (100, 100, "0x1.0000000000000p+0"),
        (400, 100, "0x1.0000000000000p+1"),
        (4000, 199, "0x1.1eef580e6f51bp+2"),
        (10000, 1000, "0x1.94c583ada5b53p+1"),
        # the two roundings differ from the correctly rounded root of the exact ratio,
        # which would be 0x1.0a0b02501c799p+0, 0x1.94df6df17465dp+0, 0x1.09f20785dfe40p+0
        # and 0x1.04f8a99a17335p+0
        (108, 100, "0x1.0a0b02501c79ap+0"),
        (5000, 1999, "0x1.94df6df17465ep+0"),
        (109, 101, "0x1.09f20785dfe41p+0"),
        (106, 102, "0x1.04f8a99a17336p+0"),
    ],
)
def test_holdout_factor_reference_values(n_examples, m, expected_hex):
    """The normative definition of 1.0.11, in IEEE-754 binary64 with two roundings:
    q = fl(float(n) / float(m)), then f = max(1, fl(sqrt(q))). The expected values were
    checked with exact rational arithmetic (each step the nearest binary64); this test
    checks them on every CI platform, which is all the definition promises."""
    assert rules.holdout_factor(n_examples, m).hex() == expected_hex


def test_a_claim_may_raise_a_coverage_minimum(tmp_path):
    """1.0.7: the defaults are floors; a value above them is written as given."""
    raised = {
        "base_reproduction": {"positive": 3, "negative": 3},
        "seeds": {"positive": 5, "negative": 2},
    }
    claim = load(tmp_path, _set(["c1", "coverage_minimum"], raised)).canonical()
    written = target(claim, "c1")["coverage_minimum"]
    assert written["seeds"] == {"positive": 5, "negative": 2}
    assert written["base_reproduction"] == {"positive": 3, "negative": 3}


@pytest.mark.parametrize("k", [2, 3, 10])
def test_random_baseline(k):
    assert rules.random_baseline("accuracy", k) == pytest.approx(1 / k)
    assert rules.random_baseline("error_rate", k) == pytest.approx(1 - 1 / k)


# ---- must fail at validation ----------------------------------------------------------------


def _set(path, value):
    """A mutation that sets claim[path...] = value (path through dicts and lists; a
    string 'c1'/'c2' selects that target; 'attack:<name>' an attack entry)."""

    def mutate(claim):
        node = claim
        for key in path[:-1]:
            node = _step(node, key)
        node[path[-1]] = value

    return mutate


def _drop(path):
    def mutate(claim):
        node = claim
        for key in path[:-1]:
            node = _step(node, key)
        del node[path[-1]]

    return mutate


def _step(node, key):
    if key in ("c1", "c2"):
        return target(node, key)
    if isinstance(key, str) and key.startswith("attack:"):
        return attack(node, key.split(":", 1)[1])
    return node[key]


def _apply(*mutations):
    def mutate(claim):
        for m in mutations:
            m(claim)

    return mutate


FAILS = {
    # placement
    "ml field at top level": _set(["metric"], {"name": "accuracy"}),
    "pass_criteria set": _set(["pass_criteria"], {"x": 1}),
    # identity
    "source other paper": _apply(
        _set(["c1", "source", "arxiv_id"], "2401.09999"),
        _set(["c1", "key"], "arXiv-2401.09999v2-C1"),
    ),
    "source other repository": _set(["c1", "source", "repository_commit"], "9" * 40),
    "key does not match source": _set(["c1", "key"], f"arXiv-{ARXIV}v3-C1"),
    "duplicate key": _set(["c2", "key"], f"arXiv-{ARXIV}v2-C1"),
    "position differs from order": _set(["c1", "inventory", "position"], 7),
    "candidate not in inventory": _set(["c1", "inventory", "candidate_id"], "c9"),
    "transcription differs": _set(["c1", "inventory", "transcription", "value"], "91.3"),
    "transcribed location differs from source": _set(["c1", "source", "location"], "Table 3"),
    "approval names another inventory": _set(
        ["c1", "approvals", "transcription", "inventory_sha256"], "0" * 64
    ),
    "two inventory attachments": lambda c: c["attachments"].append(
        dict(c["attachments"][0], path="inventory2.json")
    ),
    "no draw attachment": lambda c: c["attachments"].pop(1),
    "attachment without sha256": _drop(["attachments", 0, "sha256"]),
    # paper level
    "budget differs from profile": _set(["test_plan", "budget", "base_cpu_hours"], 200),
    "ladder given": _set(["test_plan", "build", "ladder"], ["own_environment"]),
    "python ladder unsorted": _set(["test_plan", "build", "python_ladder"], ["3.11", "3.10"]),
    "python ladder repeated": _set(["test_plan", "build", "python_ladder"], ["3.10", "3.10"]),
    "named_in_paper without named_ref": _set(
        ["test_plan", "repository", "version_basis"], "named_in_paper"
    ),
    "allowed_patches missing": _drop(["test_plan", "build", "allowed_patches"]),
    "allowed patch not an attachment": _set(
        ["test_plan", "build", "allowed_patches"], [{"attachment": "x.patch", "reason": "r"}]
    ),
    "stage missing": _drop(["test_plan", "stages", "data"]),
    "absent_artifact missing": _drop(["test_plan", "absent_artifact"]),
    "thread value missing": _drop(["test_plan", "threads", "MKL_NUM_THREADS"]),
    "no_progress above active limit": _set(
        ["test_plan", "stages", "build", "no_progress_hours"], 11
    ),
    # one claim
    "dataset not declared": _set(["c1", "dataset"], "imagenet"),
    "split not declared": _apply(
        _set(["c1", "metric", "split"], "validation"),
        _set(["c1", "inventory", "transcription", "split"], "validation"),
    ),
    "n_examples differs from split": _set(["c1", "metric", "n_examples"], 9999),
    "comparison on a value claim": lambda c: target(c, "c1").update(
        comparison=copy.deepcopy(target(c, "c2")["comparison"])
    ),
    "comparison missing": _drop(["c2", "comparison"]),
    "no comparison_mode": _drop(["c1", "comparison_mode"]),
    "value claim with comparison mode": _set(["c1", "comparison_mode"], "margin"),
    "comparison claim with value mode": _set(["c2", "comparison_mode"], "two_sided"),
    "margin without g_pub": _drop(["c2", "comparison", "g_pub"]),
    "magnitude without d_pub": _apply(
        _set(["c2", "comparison_mode"], "magnitude"), _drop(["c2", "comparison", "g_pub"])
    ),
    "d_pub outside magnitude": _set(["c2", "comparison", "d_pub"], 2.2),
    "override without reason": _set(["c1", "tolerance"], {"rel_tol": 0.05}),
    "native without reason": _apply(
        _set(["c1", "metric", "unit"], "native"),
        _set(["c1", "run", "metric_extraction", "unit"], "native"),
        _set(["c1", "tolerance"], {"abs_floor": 0.1}),
    ),
    "negative rel_tol with reason": _set(
        ["c1", "tolerance"], {"rel_tol": -0.01, "override_reason": "r"}
    ),
    "non-finite k_sd with reason": _set(
        ["c1", "tolerance"], {"k_sd": float("inf"), "override_reason": "r"}
    ),
    "extraction without unit": _drop(["c1", "run", "metric_extraction", "unit"]),
    "native extraction for percent metric": _set(
        ["c1", "run", "metric_extraction", "unit"], "native"
    ),
    "checkpoint without weights": _set(["c1", "scope"], "checkpoint_evaluation"),
    "argv as one string": _set(["c1", "run", "argv"], "python train.py"),
    "workdir with ..": _set(["c1", "run", "workdir"], "../x"),
    "workdir absolute": _set(["c1", "run", "workdir"], "/abs"),
    "extraction file with ..": _set(
        ["c1", "run", "metric_extraction"],
        {"from": "file", "file": "../out.json", "json_path": "$.acc", "unit": "percent"},
    ),
    "seed_argument without {seed}": _set(["c1", "run", "seed_argument"], "--seed=1"),
    "seed_argument with two {seed}": _set(["c1", "run", "seed_argument"], "{seed}{seed}"),
    # seeds
    "repeated base seeds": _set(["c1", "seeds", "base"], [1, 1, 2]),
    "base longer than base_cap": _apply(
        _set(["c1", "seeds", "base_cap"], 2), _set(["c1", "seeds", "base"], [1, 2, 3])
    ),
    "base longer than reported_n_seeds": _set(["c1", "metric", "reported_n_seeds"], 2),
    "no seed argument with n_base > 1": _set(["c1", "run", "seed_argument"], None),
    "derived list differs": _set(["c1", "seeds", "attack"], [5, 6, 7, 8, 9]),
    "derived list overlaps base": _set(["c1", "seeds", "holdout"], [1]),
    "derived base differs": _set(["c1", "seeds", "base_source"], "derived"),
    # attacks
    "attack missing": lambda c: target(c, "c1")["attacks"].pop(),
    "attack repeated": lambda c: target(c, "c1")["attacks"].append(
        copy.deepcopy(target(c, "c1")["attacks"][0])
    ),
    "attack unknown": _set(["c1", "attack:leakage", "name"], "dropout"),
    "applies without params": _drop(["c1", "attack:leakage", "params"]),
    "not applying with params": _set(["c1", "attack:ablation", "params"], {}),
    "split proportions do not sum to 1": _apply(
        _set(["c1", "attack:data_split", "applies"], True),
        _set(
            ["c1", "attack:data_split", "params"],
            {
                "original_proportions": [0.8, 0.3],
                "proportions": [0.8, 0.3],
                "split_argument": "--s",
            },
        ),
    ),
    "split proportions differ from original": _apply(
        _set(["c1", "attack:data_split", "applies"], True),
        _set(
            ["c1", "attack:data_split", "params"],
            {
                "original_proportions": [0.8, 0.2],
                "proportions": [0.7, 0.3],
                "split_argument": "--s",
            },
        ),
    ),
    "holdout for a metric outside the list": _apply(
        _set(["c1", "metric", "name"], "f1"),
        _set(["c1", "inventory", "transcription", "metric"], "f1"),
    ),
    "holdout without train split": lambda c: c["test_plan"]["datasets"][0]["splits"].pop("train"),
    "holdout with m below 100": _set(
        ["test_plan", "datasets", 0, "splits", "train", "expected_examples"], 999
    ),
    "holdout factor by hand": _set(["c1", "attack:holdout", "params", "factor"], 1.0),
    "holdout fraction by hand": _set(["c1", "attack:holdout", "params", "fraction"], 0.2),
    "holdout on a direction claim": _apply(
        _set(["c2", "comparison_mode"], "direction"), _drop(["c2", "comparison", "g_pub"])
    ),
    "ablation without orientation": _apply(
        _set(["c1", "attack:ablation", "applies"], True),
        _set(
            ["c1", "attack:ablation", "params"], {"disable": {"argv": ["--x"]}, "mode": "direction"}
        ),
    ),
    "ablation margin without published values": _apply(
        _set(["c1", "attack:ablation", "applies"], True),
        _set(
            ["c1", "attack:ablation", "params"],
            {"disable": {"argv": ["--x"]}, "orientation": "full_minus_ablated", "mode": "margin"},
        ),
    ),
    "ablation g_abl not the oriented difference": _apply(
        _set(["c1", "attack:ablation", "applies"], True),
        _set(
            ["c1", "attack:ablation", "params"],
            {
                "disable": {"argv": ["--x"]},
                "orientation": "full_minus_ablated",
                "mode": "margin",
                "reported_full": 91.2,
                "reported_ablated": 90.0,
                "g_abl": -1.2,
            },
        ),
    ),
    "leakage fraction 1": _set(["c1", "attack:leakage", "params", "max_overlap_fraction"], 1.0),
    "trivial baseline for another metric": _apply(
        _set(["c1", "attack:holdout", "applies"], False),
        _drop(["c1", "attack:holdout", "params"]),
        _set(["c1", "metric", "name"], "f1"),
        _set(["c1", "inventory", "transcription", "metric"], "f1"),
    ),
    "trivial baseline for another task": _set(
        ["c1", "attack:trivial_baseline", "params", "task"], "multi_label_classification"
    ),
    "trivial baseline with one label": _set(
        ["c1", "attack:trivial_baseline", "params", "labels"], [0]
    ),
    # uncertainty in a claim
    "uncertainty without location": _drop(["c1", "metric", "reported_uncertainty", "location"]),
    "uncertainty unknown kind": _set(["c1", "metric", "reported_uncertainty", "kind"], "iqr"),
    # coverage
    "coverage name WP2 refuses": _set(
        ["c1", "coverage_minimum"], {"data_split": {"positive": 1, "negative": 1}}
    ),
    # 1.0.7, the maintainer (2026-10-16): a claim may raise a minimum, never lower it
    "base_reproduction minimum below n_base": _set(
        ["c1", "coverage_minimum"], {"base_reproduction": {"positive": 2, "negative": 3}}
    ),
    "metric_recompute minimum below its default": _set(
        ["c1", "coverage_minimum"], {"metric_recompute": {"positive": 1, "negative": 1}}
    ),
    # 1.0.9, the maintainer (2026-10-16): 'none' is no published uncertainty, nothing to quote
    "uncertainty none with a location": _set(
        ["c1", "metric", "reported_uncertainty"], {"kind": "none", "location": "Table 2"}
    ),
    # metric_recompute
    "recompute for an unsupported metric": _apply(
        _set(["c1", "metric_recompute", "convention", "metric"], "top5"),
    ),
    "recompute with sample weights": _set(
        ["c1", "metric_recompute", "convention", "sample_weight"], "w"
    ),
    "recompute with an unsupported format": _set(
        ["c1", "metric_recompute", "predictions", "format"], "parquet"
    ),
    "recompute scale differs from unit": _set(
        ["c1", "metric_recompute", "convention", "scale"], "fraction"
    ),
    "recompute file without {seed} for several runs": _set(
        ["c1", "metric_recompute", "predictions", "file"], "preds/p.npy"
    ),
    # coverage of metric_extracted (1.5a)
    "coverage evidence missing": _drop(["c1", "coverage_evidence"]),
    "coverage without a route": _set(["c1", "coverage_evidence", "method", "routes"], []),
    "coverage route (e) out of v0.3": _set(
        ["c1", "coverage_evidence", "method", "routes"], [{"route": "evaluator_observer"}]
    ),
    "coverage route (f) decides": _set(
        ["c1", "coverage_evidence", "method", "routes"], [{"route": "dataset_read_trace"}]
    ),
    "coverage complementary other than (f)": _set(
        ["c1", "coverage_evidence", "method", "complementary"], ["printed_count"]
    ),
    "coverage routes out of order": _set(
        ["c1", "coverage_evidence", "method", "routes"],
        [printed_count(), {"route": "saved_predictions", "link": [dict(CITE)]}],
    ),
    "coverage route twice": _set(
        ["c1", "coverage_evidence", "method", "routes"], [printed_count(), printed_count()]
    ),
    "coverage conflict rule other than all_must_agree": _set(
        ["c1", "coverage_evidence", "method", "conflict_rule"], "first_route_wins"
    ),
    "coverage split identity missing for saved predictions": _drop(
        ["c1", "coverage_evidence", "method", "split_identity"]
    ),
    "coverage split identity without a route that sees labels": _set(
        ["c2", "coverage_evidence", "method", "split_identity"], split_identity()
    ),
    "coverage split labels equal another split's": _set(
        ["c1", "coverage_evidence", "method", "split_identity", "other_splits"],
        [
            {"name": "train", "labels_sha256": OTHER_LABELS_SHA256},
            {"name": "val", "labels_sha256": LABELS_SHA256},
        ],
    ),
    "coverage split identity without its evidence": _set(
        ["c1", "coverage_evidence", "method", "split_identity", "splits_evidence"], []
    ),
    "coverage split identity leaves out a declared split": _set(
        ["c1", "coverage_evidence", "method", "split_identity", "other_splits"], []
    ),
    "coverage split identity names the claim's own split": _set(
        ["c1", "coverage_evidence", "method", "split_identity", "other_splits"],
        [
            {"name": "train", "labels_sha256": OTHER_LABELS_SHA256},
            {"name": "test", "labels_sha256": "d" * 64},
        ],
    ),
    "coverage hook alike for both methods with other roles": _apply(
        _set(
            ["c2", "coverage_evidence", "method"], hook_evidence("sklearn.metrics.accuracy_score")
        ),
        _set(
            ["c2", "coverage_evidence", "reference"],
            hook_evidence("sklearn.metrics.accuracy_score"),
        ),
        _set(
            ["c2", "coverage_evidence", "reference", "routes", 0, "call_site", "role"],
            "the reference's evaluation call",
        ),
    ),
    "coverage count json_path with an empty step": _set(
        ["c2", "coverage_evidence", "method", "routes", 0, "count"],
        {"from": "log", "json_path": "$."},
    ),
    "coverage count json_path with a bare bracket": _set(
        ["c2", "coverage_evidence", "method", "routes", 0, "count"],
        {"from": "log", "json_path": "$]"},
    ),
    "metric_extraction json_path outside the grammar": _set(
        ["c1", "run", "metric_extraction"],
        {"from": "file", "file": "out/{seed}.json", "json_path": "$..acc", "unit": "percent"},
    ),
    "coverage saved predictions without metric_recompute": _apply(
        _set(
            ["c2", "coverage_evidence", "method", "routes"],
            [{"route": "saved_predictions", "link": [dict(CITE)]}],
        ),
        _set(["c2", "coverage_evidence", "method", "split_identity"], split_identity()),
    ),
    "coverage saved predictions without link": _drop(
        ["c1", "coverage_evidence", "method", "routes", 0, "link"]
    ),
    "coverage selected evaluation missing": _drop(
        ["c1", "coverage_evidence", "method", "selected_evaluation"]
    ),
    "coverage selected evaluation final with a value": _set(
        ["c1", "coverage_evidence", "method", "selected_evaluation"], {"kind": "final", "value": 3}
    ),
    "coverage selected epoch without its number": _set(
        ["c1", "coverage_evidence", "method", "selected_evaluation"], {"kind": "epoch"}
    ),
    "coverage selected checkpoint outside the repository": _set(
        ["c1", "coverage_evidence", "method", "selected_evaluation"],
        {"kind": "checkpoint", "value": "../best.pt"},
    ),
    "coverage count json_path without a member": _set(
        ["c2", "coverage_evidence", "method", "routes", 0, "count"],
        {"from": "log", "json_path": "$"},
    ),
    "coverage count regex without its group": _set(
        ["c2", "coverage_evidence", "method", "routes", 0, "count"],
        {"from": "log", "regex": {"pattern": "evaluated=10000", "group": 9}},
    ),
    "coverage count regex without its named group": _set(
        ["c2", "coverage_evidence", "method", "routes", 0, "count"],
        {"from": "log", "regex": {"pattern": r"evaluated=(?P<n>\d+)", "group": "count"}},
    ),
    "coverage same evidence for both methods": _set(
        ["c2", "coverage_evidence", "reference", "routes"], [printed_count()]
    ),
    "coverage printed count without link": _drop(
        ["c2", "coverage_evidence", "method", "routes", 0, "link"]
    ),
    "coverage printed count with an empty link": _set(
        ["c2", "coverage_evidence", "method", "routes", 0, "link"], []
    ),
    "coverage printed count with a hook field": _set(
        ["c2", "coverage_evidence", "method", "routes", 0, "patch"], "hook.patch"
    ),
    "coverage citation lines reversed": _set(
        ["c2", "coverage_evidence", "method", "routes", 0, "link", 0, "lines"], [52, 40]
    ),
    "coverage citation outside the repository": _set(
        ["c2", "coverage_evidence", "method", "routes", 0, "link", 0, "file"], "../eval.py"
    ),
    "coverage count file without {seed} for several runs": _set(
        ["c2", "coverage_evidence", "method", "routes", 0, "count"],
        {"from": "file", "file": "out/count.json", "json_path": "$.n"},
    ),
    "coverage statistics for a metric outside the list": _apply(
        _set(["c1", "attack:holdout", "applies"], False),
        _drop(["c1", "attack:holdout", "params"]),
        _set(["c1", "attack:trivial_baseline", "applies"], False),
        _drop(["c1", "attack:trivial_baseline", "params"]),
        _set(["c1", "metric", "name"], "f1"),
        _set(["c1", "inventory", "transcription", "metric"], "f1"),
        _set(["c1", "metric_recompute"], {"applies": False, "reason": "not saved"}),
        _set(
            ["c1", "coverage_evidence", "method"],
            {
                "selected_evaluation": dict(FINAL),
                "routes": [
                    {
                        "route": "sufficient_statistics",
                        "correct": {"from": "log", "regex": {"pattern": r"c=(\d+)", "group": 1}},
                        "total": {"from": "log", "regex": {"pattern": r"n=(\d+)", "group": 1}},
                        "link": [dict(CITE)],
                    }
                ],
            },
        ),
    ),
    "coverage hook for another function": _set(
        ["c2", "coverage_evidence", "method"],
        hook_evidence("sklearn.metrics.f1_score"),
    ),
    "coverage hook not an allowed patch": _set(
        ["c2", "coverage_evidence", "method"],
        hook_evidence("sklearn.metrics.accuracy_score"),
    ),
    "coverage hook without link": _apply(
        _set(
            ["c2", "coverage_evidence", "method"], hook_evidence("sklearn.metrics.accuracy_score")
        ),
        _drop(["c2", "coverage_evidence", "method", "routes", 0, "link"]),
    ),
    "coverage reference missing for a comparison": _drop(["c2", "coverage_evidence", "reference"]),
    "coverage reference on a value claim": _set(
        ["c1", "coverage_evidence", "reference"],
        {"selected_evaluation": dict(FINAL), "routes": [printed_count(r"other=(\d+)")]},
    ),
}


# The reason each case must fail for: a case that fails for another reason proves
# nothing about its own rule.
REASONS = {
    "ablation g_abl not the oriented difference": "oriented difference",
    "ablation margin without published values": "needs reported_full",
    "ablation without orientation": "orientation: Field required",
    "absent_artifact missing": "absent_artifact: Field required",
    "allowed patch not an attachment": "is not an attachment with role 'allowed-patch'",
    "allowed_patches missing": "allowed_patches: Field required",
    "applies without params": "applies and needs params",
    "approval names another inventory": "approval names another inventory",
    "argv as one string": "run.argv: Input should be a valid list",
    "attachment without sha256": "attachment needs its sha256",
    "attack missing": "exactly once",
    "attack repeated": "exactly once",
    "attack unknown": "name: Input should be",
    "base longer than base_cap": "n_base = 2",
    "base_reproduction minimum below n_base": "base_reproduction: positive below the 1.0.7",
    "base longer than reported_n_seeds": "n_base = 2",
    "budget differs from profile": "no other value is accepted",
    "candidate not in inventory": "is not in the inventory",
    "checkpoint without weights": "weights is required for checkpoint_evaluation",
    "comparison claim with value mode": "a comparison claim takes comparison_mode",
    "comparison missing": "needs its comparison block",
    "comparison on a value claim": "a value claim has no comparison block",
    "coverage citation lines reversed": "first <= last",
    "coverage citation outside the repository": "citation file must be relative",
    "coverage complementary other than (f)": "Input should be 'dataset_read_trace'",
    "coverage conflict rule other than all_must_agree": "Input should be 'all_must_agree'",
    "coverage count file without {seed} for several runs": "a count file names {seed}",
    "coverage evidence missing": "coverage_evidence: Field required",
    "coverage count json_path with a bare bracket": "unsupported step at 1",
    "coverage count json_path with an empty step": "unsupported step at 1",
    "coverage count json_path without a member": "names the whole document",
    "coverage hook alike for both methods with other roles": "read the same evidence",
    "coverage count regex without its group": "regex has no group 9",
    "coverage count regex without its named group": "regex has no group named 'count'",
    "coverage hook for another function": "no other function",
    "coverage hook not an allowed patch": "is not in test_plan.build.allowed_patches",
    "coverage hook without link": "takes exactly",
    "coverage same evidence for both methods": "read the same evidence of the same runs",
    "coverage saved predictions without link": "takes exactly",
    "coverage selected checkpoint outside the repository": "checkpoint must be relative",
    "coverage selected epoch without its number": "an epoch number",
    "coverage selected evaluation final with a value": "'final' takes no value",
    "coverage selected evaluation missing": "selected_evaluation: Field required",
    "coverage split identity missing for saved predictions": "split_identity is required",
    "coverage split identity without a route that sees labels": "split_identity is required",
    "coverage split identity leaves out a declared split": "leaves out the declared splits",
    "coverage split identity names the claim's own split": "names the claim's own split",
    "coverage split identity without its evidence": "List should have at least 1 item",
    "coverage split labels equal another split's": "cannot identify it",
    "metric_extraction json_path outside the grammar": "unsupported step at 1",
    "coverage printed count with a hook field": "takes exactly",
    "coverage printed count with an empty link": "cites at least one place",
    "coverage printed count without link": "takes exactly",
    "coverage reference missing for a comparison": "coverage_evidence.reference is required",
    "coverage reference on a value claim": "coverage_evidence.reference is required",
    "coverage route (e) out of v0.3": "route: Input should be",
    "coverage route (f) decides": "route: Input should be",
    "coverage route twice": "listed twice",
    "coverage routes out of order": "listed in the order",
    "coverage saved predictions without metric_recompute": "which must apply",
    "coverage statistics for a metric outside the list": "sufficient_statistics applies only to",
    "coverage without a route": "routes: List should have at least 1 item",
    "coverage name WP2 refuses": "WP2 refuses",
    "d_pub outside magnitude": "d_pub is required in magnitude mode",
    "dataset not declared": "dataset imagenet is not declared",
    "derived base differs": "seeds.base differs from the derivation",
    "derived list differs": "seeds.attack differs from the derivation",
    "derived list overlaps base": "overlaps the base seeds",
    "duplicate key": "two claims share a key",
    "extraction file with ..": "metric_extraction.file must be relative",
    "extraction without unit": "metric_extraction.unit: Field required",
    "holdout factor by hand": "never by hand",
    "holdout for a metric outside the list": "holdout applies only to",
    "holdout fraction by hand": "never by hand",
    "holdout on a direction claim": "holdout does not apply to a direction claim",
    "holdout with m below 100": "below 100",
    "holdout without train split": "needs a declared train split",
    "key does not match source": "matching its source",
    "ladder given": "build.ladder is fixed",
    "leakage fraction 1": "max_overlap_fraction: Input should be less than 1",
    "magnitude without d_pub": "d_pub is required in magnitude mode",
    "metric_recompute minimum below its default": "metric_recompute: positive below the 1.0.7",
    "margin without g_pub": "g_pub is required in margin mode",
    "ml field at top level": "metric: Extra inputs are not permitted",
    "n_examples differs from split": "n_examples differs",
    "named_in_paper without named_ref": "named_ref must be non-empty",
    "native extraction for percent metric": "cannot be converted to metric.unit",
    "native without reason": "needs a reason",
    "negative rel_tol with reason": "tolerance.rel_tol must be finite",
    "no comparison_mode": "comparison_mode: Field required",
    "no draw attachment": "role 'claim-draw'",
    "no seed argument with n_base > 1": "n_base must be 1",
    "no_progress above active limit": "no_progress_hours cannot exceed",
    "non-finite k_sd with reason": "tolerance.k_sd must be finite",
    "not applying with params": "does not apply and takes no params",
    "override without reason": "needs a reason",
    "pass_criteria set": "no pass_criteria",
    "position differs from order": "its place in the draw",
    "python ladder repeated": "distinct versions",
    "python ladder unsorted": "distinct versions",
    "recompute file without {seed} for several runs": "names {seed}",
    "recompute for an unsupported metric": "unsupported metric",
    "recompute scale differs from unit": "scale must equal metric.unit",
    "recompute with an unsupported format": "format: Input should be",
    "recompute with sample weights": "unknown fields ['sample_weight']",
    "repeated base seeds": "seeds.base repeats a seed",
    "seed_argument with two {seed}": "exactly one {seed}",
    "seed_argument without {seed}": "exactly one {seed}",
    "source other paper": "another paper",
    "source other repository": "another repository",
    "split not declared": "split validation is not declared",
    "split proportions differ from original": "must equal original_proportions",
    "split proportions do not sum to 1": "must sum to 1",
    "stage missing": "stages.data: Field required",
    "thread value missing": "MKL_NUM_THREADS: Field required",
    "transcribed location differs from source": "transcribed location differs",
    "transcription differs": "transcription differs from the inventory",
    "trivial baseline for another metric": "trivial_baseline applies only to",
    "trivial baseline for another task": "task: Input should be 'single_label_classification'",
    "trivial baseline with one label": "labels: List should have at least 2 items",
    "two inventory attachments": "role 'claim-inventory'",
    "uncertainty none with a location": "uncertainty 'none' takes no location",
    "uncertainty unknown kind": "kind: Input should be",
    "uncertainty without location": "needs its location and quote",
    "value claim with comparison mode": "a value claim takes comparison_mode",
    "workdir absolute": "run.workdir must be relative",
    "workdir with ..": "run.workdir must be relative",
}


def test_every_failing_case_names_its_reason():
    assert sorted(REASONS) == sorted(FAILS)


@pytest.mark.parametrize("case", sorted(FAILS))
def test_invalid_claims_are_refused(tmp_path, case):
    with pytest.raises(ClaimError) as error:
        load(tmp_path, FAILS[case])
    assert REASONS[case] in str(error.value), str(error.value)


def test_the_inventory_must_be_stored_in_canonical_json(tmp_path):
    pretty = json.dumps(inventory(), indent=2).encode("utf-8")
    with pytest.raises(ClaimError, match="canonical"):
        load(tmp_path, files={"inventory": pretty})


def test_the_draw_must_list_the_targets_in_order(tmp_path):
    draw = inv.draw_record(inv.draw_claims(inventory(), CLAIM_SEED))
    draw["drawn"] = list(reversed(draw["drawn"]))
    with pytest.raises(ClaimError, match="drawn order"):
        load(tmp_path, files={"draw": draw})


def test_the_draw_must_use_the_same_inventory(tmp_path):
    draw = inv.draw_record(inv.draw_claims(inventory(), CLAIM_SEED))
    draw["inventory_sha256"] = "0" * 64
    with pytest.raises(ClaimError, match="another inventory"):
        load(tmp_path, files={"draw": draw})


@pytest.mark.parametrize(
    ("change", "reason"),
    [
        (lambda d: d.update(arxiv_id="2401.09999"), "another paper"),
        (lambda d: d.update(comparison_required=False), "comparison requirement"),
        (lambda d: d["shuffled"].append("c9"), "drawable candidates"),
    ],
)
def test_the_draw_must_agree_with_its_inventory(tmp_path, change, reason):
    draw = inv.draw_record(inv.draw_claims(inventory(), CLAIM_SEED))
    change(draw)
    with pytest.raises(ClaimError, match=reason):
        load(tmp_path, files={"draw": draw})


def test_a_separate_reference_run_has_the_same_seed_control(tmp_path):
    def separate(claim):
        reference = run_block()
        reference["argv"] = ["python", "baseline.py"]
        reference["seed_argument"] = None
        target(claim, "c2")["comparison"]["reference_run"] = reference

    with pytest.raises(ClaimError, match="same seeds"):
        load(tmp_path, separate)

    def controlled(claim):
        reference = run_block()
        reference["argv"] = ["python", "baseline.py"]
        target(claim, "c2")["comparison"]["reference_run"] = reference

    load(tmp_path, controlled)


def test_separate_reference_runs_may_read_their_own_logs_with_the_same_selector(tmp_path):
    """1.5a, Codex review of #120: with a separate reference run, the method and the
    reference read different logs, so the same selector is two pieces of evidence; with
    the same runs it is one, and it is refused (case 'coverage same evidence for both
    methods')."""

    def separate(claim):
        reference = run_block()
        reference["argv"] = ["python", "baseline.py"]
        t = target(claim, "c2")
        t["comparison"]["reference_run"] = reference
        t["coverage_evidence"]["reference"]["routes"] = [printed_count()]

    load(tmp_path, separate)


def test_the_same_hook_call_may_serve_two_selected_evaluations(tmp_path):
    """Codex review of #120, round 3: with the same runs, one evaluation helper may compute
    the method's and the reference's values from two different checkpoints; the hook
    declarations differ by their selected evaluation, so the schema accepts them and the
    gate checks that the events are distinct."""

    def two_checkpoints(claim):
        (tmp_path / "hook.patch").write_text("--- a\n+++ b\n")
        claim["attachments"].append({"path": "hook.patch", "role": "allowed-patch"})
        claim["test_plan"]["build"]["allowed_patches"] = [
            {"attachment": "hook.patch", "reason": "observes accuracy_score in the container"}
        ]
        cov = target(claim, "c2")["coverage_evidence"]
        cov["method"] = hook_evidence("sklearn.metrics.accuracy_score")
        cov["reference"] = hook_evidence("sklearn.metrics.accuracy_score")
        cov["method"]["selected_evaluation"] = {"kind": "checkpoint", "value": "ours_{seed}.pt"}
        cov["reference"]["selected_evaluation"] = {
            "kind": "checkpoint",
            "value": "baseline_{seed}.pt",
        }

    load(tmp_path, two_checkpoints)


def test_selectors_accept_the_grammar_and_groups_they_can_read(tmp_path):
    """Positive limits of the selector checks: a json_path with name and index steps, a
    regular expression's group 0 and an existing named group, in metric_extraction and in
    a coverage count."""

    def selectors(claim):
        t = target(claim, "c2")
        t["run"]["metric_extraction"] = {
            "from": "file",
            "file": "out/metrics_{seed}.json",
            "json_path": "$.runs[0].test-acc",
            "unit": "percent",
        }
        t["coverage_evidence"]["method"]["routes"][0]["count"] = {
            "from": "log",
            "regex": {"pattern": r"evaluated=(?P<n>\d+)", "group": "n"},
        }
        t["coverage_evidence"]["reference"]["routes"][0]["count"] = {
            "from": "log",
            "regex": {"pattern": r"\d+", "group": 0},
        }

    load(tmp_path, selectors)


@pytest.mark.parametrize("metric", ["mae", "r2", "bleu", "top5_accuracy"])
def test_a_metric_outside_the_bounded_rates_is_native(tmp_path, metric):
    def mae_in_percent(claim):
        t = target(claim, "c1")
        t["metric"]["name"] = metric
        t["inventory"]["transcription"]["metric"] = metric
        for name in ("holdout", "trivial_baseline"):
            attack(t, name).update(applies=False)
            attack(t, name).pop("params")
        t["metric_recompute"] = {"applies": False, "reason": "not saved"}

    with pytest.raises(ClaimError, match="not a bounded rate"):
        load(tmp_path, mae_in_percent)


# ---- trivial_baseline and the claim's unit (#59; the maintainer's approval, 2026-10-17) ------


def _metric_in(metric, unit, baseline):
    """c1 as a claim on ``metric`` in ``unit``, with trivial_baseline applying or not. The
    reported value and its transcription follow the unit; the uncertainty and
    metric_recompute are set aside, so only the unit and the attack differ."""

    def mutate(claim):
        t = target(claim, "c1")
        value = {"percent": "91.2", "fraction": "0.912", "native": "0.912"}[unit]
        t["metric"]["name"] = metric
        t["metric"]["unit"] = unit
        t["metric"]["higher_is_better"] = metric == "accuracy"
        t["metric"]["reported"] = float(value)
        t["metric"]["reported_uncertainty"] = {"kind": "none"}
        t["run"]["metric_extraction"]["unit"] = unit
        t["metric_recompute"] = {"applies": False, "reason": "set aside in this test"}
        # the saved_predictions route needs metric_recompute: the printed count stays
        t["coverage_evidence"]["method"]["routes"] = [printed_count()]
        t["coverage_evidence"]["method"].pop("split_identity")
        if unit == "native":
            t["tolerance"] = {"abs_floor": 0.005, "override_reason": "a native unit"}
        if not baseline:
            attack(t, "trivial_baseline").update(applies=False)
            attack(t, "trivial_baseline").pop("params")

    return mutate


def _transcribe(monkeypatch, metric, unit):
    """The inventory's transcription of c1 for ``metric`` in ``unit``: the claim's own
    transcription, the inventory attachment and its hash all follow it."""
    value = {"percent": "91.2", "fraction": "0.912", "native": "0.912"}[unit]
    monkeypatch.setitem(
        TRANSCRIPTIONS, "c1", dict(TRANSCRIPTIONS["c1"], metric=metric, value=value)
    )


@pytest.mark.parametrize("unit", ["percent", "fraction"])
@pytest.mark.parametrize("metric", ["accuracy", "error_rate"])
def test_trivial_baseline_in_percent_or_fraction_resolves_and_runs(
    tmp_path, monkeypatch, metric, unit
):
    """From the schema to trivial_baseline_value: a claim the schema accepts with the attack
    applying gives a baseline in its own unit (the attack can run)."""
    from refute.packs.ml.attacks import trivial_baseline_value

    _transcribe(monkeypatch, metric, unit)
    claim = load(tmp_path, _metric_in(metric, unit, baseline=True)).canonical()
    t = target(claim, "c1")
    params = attack(t, "trivial_baseline")["params"]
    baseline = trivial_baseline_value(
        params["kind"], params["labels"], t["metric"]["name"], t["metric"]["unit"]
    )
    expected = {"accuracy": 0.1, "error_rate": 0.9}[metric] * (100 if unit == "percent" else 1)
    assert float(baseline.strongest) == pytest.approx(expected)


@pytest.mark.parametrize("metric", ["accuracy", "error_rate"])
def test_trivial_baseline_with_a_native_unit_is_refused(tmp_path, monkeypatch, metric):
    """Before this check, the schema accepted the combination and the attack raised at run
    time ("trivial_baseline needs a claim in percent or fraction")."""
    _transcribe(monkeypatch, metric, "native")
    with pytest.raises(ClaimError, match="trivial_baseline needs a claim in percent or fraction"):
        load(tmp_path, _metric_in(metric, "native", baseline=True))


@pytest.mark.parametrize("metric", ["accuracy", "error_rate"])
def test_a_native_unit_without_the_baseline_attack_is_valid(tmp_path, monkeypatch, metric):
    _transcribe(monkeypatch, metric, "native")
    claim = load(tmp_path, _metric_in(metric, "native", baseline=False)).canonical()
    t = target(claim, "c1")
    assert t["metric"]["unit"] == "native"
    assert attack(t, "trivial_baseline")["applies"] is False


def test_a_reason_may_accompany_the_default_tolerance(tmp_path):
    load(tmp_path, _set(["c1", "tolerance"], {"override_reason": "defaults kept on purpose"}))


# ---- transcribed value and command (maintainer's decision 1, 2026-10-15) ----------------------


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (_set(["c1", "metric", "reported"], 91.3), "transcribed value differs"),
        (_set(["c2", "comparison", "reported_reference"], 88.0), "transcribed value differs"),
        (_set(["c1", "run", "argv"], ["python", "train2.py"]), "transcribed command differs"),
        (_set(["c1", "run", "seed_argument"], "--seed {seed}"), "transcribed command differs"),
    ],
)
def test_the_transcribed_value_and_command_are_the_claims(tmp_path, mutate, reason):
    with pytest.raises(ClaimError, match=reason):
        load(tmp_path, mutate)


def test_values_are_compared_as_written_decimals_never_through_a_float(tmp_path):
    # 91.20000000000000001 is the float 91.2, but not the decimal 91.2 transcribed
    path = build_claim(tmp_path)
    text = path.read_text(encoding="utf-8")
    assert text.count("reported: 91.2\n") == 1
    path.write_text(text.replace("reported: 91.2\n", "reported: 91.20000000000000001\n"))
    with pytest.raises(ClaimError, match="transcribed value differs"):
        load_claim(path, pack=PACK)
    # trailing zeros are the same decimal
    path.write_text(text.replace("reported: 91.2\n", "reported: 91.20\n"))
    load_claim(path, pack=PACK)


def test_commands_are_compared_as_argument_lists(tmp_path, monkeypatch):
    # "train.py --seed={seed}" as one argument is not two arguments
    monkeypatch.setitem(TRANSCRIPTIONS["c1"], "command", '["python", "train.py --seed={seed}"]')
    with pytest.raises(ClaimError, match="transcribed command differs"):
        load(tmp_path)


@pytest.mark.parametrize(
    ("cid", "field", "text", "reason"),
    [
        ("c1", "command", "python train.py --seed={seed}", "JSON array"),
        ("c1", "value", "91.2%", "decimal number as printed"),
        ("c2", "value", "91.2 / 89.0", "<method> vs <reference>"),
    ],
)
def test_transcription_formats(tmp_path, monkeypatch, cid, field, text, reason):
    monkeypatch.setitem(TRANSCRIPTIONS[cid], field, text)
    with pytest.raises(ClaimError, match=reason):
        load(tmp_path)


# ---- derived values (maintainer's condition on item e, 2026-10-15) -----------------------------


def _ci_value_claim(claim):
    target(claim, "c1")["metric"]["reported_uncertainty"] = {
        "kind": "ci",
        "lower": 90.9,
        "upper": 91.5,
        "level": 0.95,
        "method": "t",
        "n": 3,
        "unit": "percent",
        "location": "Table 2",
        "quote": "91.2 [90.9, 91.5]",
    }


def _tamper(path, value):
    def apply(claim):
        node = claim
        for key in path[:-1]:
            node = _step(node, key)
        node[path[-1]] = value

    return apply


DERIVED = {
    "ladder": (["test_plan", "build", "ladder"], ["own_environment"]),
    "budget": (["test_plan", "budget", "base_cpu_hours"], 191.0),
    "seeds.attack": (["c1", "seeds", "attack"], [11, 12, 13, 14, 15]),
    "seeds.data_split": (["c1", "seeds", "data_split"], [11, 12, 13]),
    "seeds.holdout": (["c1", "seeds", "holdout"], [11]),
    "holdout.fraction": (["c1", "attack:holdout", "params", "fraction"], 0.2),
    "holdout.m": (["c1", "attack:holdout", "params", "m"], 4999),
    "holdout.factor": (["c1", "attack:holdout", "params", "factor"], 1.0),
    "uncertainty.status": (["c1", "metric", "reported_uncertainty", "status"], "none"),
    "uncertainty.sd": (["c1", "metric", "reported_uncertainty", "sd"], 0.31),
    "uncertainty.quantile": (["c1", "metric", "reported_uncertainty", "quantile"], 2.0),
    "paired.status": (["c2", "comparison", "paired_uncertainty", "status"], "converted"),
}


def test_the_written_derived_values_pass_their_own_check(tmp_path):
    from refute.packs.ml.schema import verify_derived

    verify_derived(load(tmp_path, _ci_value_claim).canonical())


@pytest.mark.parametrize("name", sorted(DERIVED))
def test_each_altered_derived_value_is_refused(tmp_path, name):
    from refute.packs.ml.schema import verify_derived

    claim = copy.deepcopy(load(tmp_path, _ci_value_claim).canonical())
    path, value = DERIVED[name]
    _tamper(path, value)(claim)
    with pytest.raises(ValueError, match="derived value differs"):
        verify_derived(claim)


MISSING = {
    "seeds.attack": ["c1", "seeds", "attack"],
    "holdout.factor": ["c1", "attack:holdout", "params", "factor"],
    "ladder": ["test_plan", "build", "ladder"],
    "budget": ["test_plan", "budget", "paper_cpu_hours"],
    # expected None: a missing key is still refused (Codex review)
    "sd record quantile": ["c1", "metric", "reported_uncertainty", "quantile"],
    "none record sd": ["c2", "comparison", "uncertainty_method", "sd"],
    "none record quantile": ["c2", "comparison", "paired_uncertainty", "quantile"],
}


@pytest.mark.parametrize("name", sorted(MISSING))
def test_a_missing_derived_value_is_refused(tmp_path, name):
    from refute.packs.ml.schema import verify_derived

    claim = copy.deepcopy(load(tmp_path).canonical())
    path = MISSING[name]
    node = claim
    for key in path[:-1]:
        node = _step(node, key)
    del node[path[-1]]
    with pytest.raises(ValueError, match="derived value differs"):
        verify_derived(claim)


def test_a_truncated_derived_base_is_refused(tmp_path):
    """Codex review: n_base comes from reported_n_seeds and base_cap, never from the
    written list, so a prefix of the derived base does not pass."""
    from refute.packs.ml.schema import verify_derived

    run_seed = seeds.run_seed(CLAIM_SEED, ARXIV)

    def derived(claim):
        for t in claim["targets"]:
            t["seeds"] = {
                "base": seeds.derived_seeds(run_seed, "base", 3),
                "base_cap": 3,
                "base_source": "derived",
            }

    claim = copy.deepcopy(load(tmp_path, derived).canonical())
    t = target(claim, "c1")
    t["seeds"]["base"] = t["seeds"]["base"][:2]
    with pytest.raises(ValueError, match="derived value differs"):
        verify_derived(claim)


def test_recorded_derived_values_are_exact(tmp_path):
    """The written derived values of the CI fixture, recorded on 2026-10-15; every CI job
    (Python 3.12 and 3.13, Ubuntu and Windows) must give exactly these."""
    value = target(load(tmp_path, _ci_value_claim).canonical(), "c1")
    record = value["metric"]["reported_uncertainty"]
    assert (record["status"], record["quantile"], record["sd"]) == (
        "converted",
        4.30265272975,  # t(0.975, 2) = 4.303 in the NIST table
        0.120766251638,
    )
    assert attack(value, "holdout")["params"] == {
        "split_argument": "--holdout-seed={seed}",
        "fraction": 0.1,
        "m": 5000,
        "factor": 1.4142135623730951,
    }


@pytest.mark.parametrize("precision", [5, 28, 100])
def test_base_60_is_exact_whatever_the_decimal_context(tmp_path, monkeypatch, precision):
    """Codex review: 1:30.000000000000000000000000001 is 90 + 1e-27, not 90, whatever
    the decimal context of the caller."""
    import decimal

    from refute.packs.ml import schema

    text = "x: 1:30.000000000000000000000000001"
    with decimal.localcontext() as ctx:
        ctx.prec = precision
        value = yaml.load(text, Loader=schema._DecimalLoader)["x"]
    assert value == Decimal("90.000000000000000000000000001")
    # in a claim, the transcription "90" does not match it
    monkeypatch.setitem(TRANSCRIPTIONS["c1"], "value", "90")
    path = build_claim(tmp_path)
    content = path.read_text(encoding="utf-8")
    path.write_text(
        content.replace("reported: 91.2\n", "reported: 1:30.000000000000000000000000001\n")
    )
    with decimal.localcontext() as ctx:
        ctx.prec = precision
        with pytest.raises(ClaimError, match="transcribed value differs"):
            load_claim(path, pack=PACK)


def test_numbers_the_yaml_reads_are_compared_without_a_float(tmp_path):
    """Codex review: the second reading accepts every number form the claim accepts."""
    path = build_claim(tmp_path)
    text = path.read_text(encoding="utf-8")
    # YAML 1.1 reads 9.12e1 as a string; the schema's float field accepts it
    path.write_text(text.replace("reported: 91.2\n", "reported: 9.12e1\n"))
    load_claim(path, pack=PACK)
    # a base-60 float elsewhere in the file (1:30.0 = 90.0) does not break the reading
    marker = "active_time_limit_hours: 10\n"
    assert marker in text
    path.write_text(text.replace(marker, "active_time_limit_hours: 1:30.0\n", 1))
    load_claim(path, pack=PACK)


@pytest.mark.parametrize(
    ("written", "transcribed", "accepted"),
    [
        ("1e3", "1000", True),  # YAML 1.1 reads 1e3 as a string; exact decimal 1000
        ("1e3", "1000.00000000000001", False),  # the same float as 1000, another decimal
        ("1:30.5", "90.5", True),  # base 60
        ("1:30.5", "90.500000000000001", False),  # the same float as 90.5
    ],
)
def test_published_value_forms_against_the_transcription(
    tmp_path, monkeypatch, written, transcribed, accepted
):
    """Maintainer's decision 1.0.11: decimals preserved, never through a float, including
    1e3 and base-60 numbers. The refused transcriptions are the same float as the
    published value, so only a decimal comparison can refuse them (Codex review)."""
    if not accepted:
        published = 1000.0 if written == "1e3" else 90.5
        assert float(transcribed) == published  # a float comparison would accept it
    monkeypatch.setitem(TRANSCRIPTIONS["c1"], "value", transcribed)
    path = build_claim(tmp_path)
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("reported: 91.2\n", f"reported: {written}\n"))
    if accepted:
        load_claim(path, pack=PACK)
    else:
        with pytest.raises(ClaimError, match="transcribed value differs"):
            load_claim(path, pack=PACK)


@pytest.mark.parametrize(
    "named",
    [
        {"named_ref": "v1.0"},
        {"named_ref_location": "README, line 3"},
        {"named_ref": "v1.0", "named_ref_location": "README, line 3"},
    ],
)
def test_named_ref_is_refused_with_latest_at_draw(tmp_path, named):
    """Maintainer's decision 1.0.11: the explicit refusal is kept."""

    def mutate(claim):
        claim["test_plan"]["repository"].update(named)

    with pytest.raises(ClaimError, match="latest_at_draw takes no named_ref"):
        load(tmp_path, mutate)


@pytest.mark.parametrize(
    ("reference_run", "reason"),
    [
        ({"same": True}, "metric_extraction"),
        ("same", "reference_run"),
        (
            {
                "same": False,
                "metric_extraction": {
                    "from": "log",
                    "regex": {"pattern": "r=([0-9.]+)", "group": 1},
                    "unit": "percent",
                },
            },
            "reference_run",
        ),
    ],
)
def test_a_same_run_reference_needs_its_own_extraction(tmp_path, reference_run, reason):
    """Maintainer's decision 1.0.11: reference_run may use the same runs, with its own
    extraction."""
    with pytest.raises(ClaimError, match=reason):
        load(tmp_path, _set(["c2", "comparison", "reference_run"], reference_run))


def test_resolution_does_not_depend_on_key_order(tmp_path):
    path = build_claim(tmp_path)
    a = load_claim(path, pack=PACK).sha256()
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    path.write_text(yaml.safe_dump(data, sort_keys=True), encoding="utf-8")
    b = load_claim(path, pack=PACK).sha256()
    assert a == b


def test_converted_values_are_rounded_to_12_significant_digits():
    out = resolve_uncertainty(
        unc(kind="ci", lower=90.0, upper=92.0, level=0.95, method="t", n=5), "percent", 91.0
    )
    assert out["quantile"] == float(f"{out['quantile']:.12g}")
    assert out["sd"] == float(f"{out['sd']:.12g}")
    frac = resolve_uncertainty(unc(kind="sd", value=0.003, unit="fraction"), "percent", 91.2)
    assert frac["sd"] == 0.3  # not 0.30000000000000004


def test_draw_record_round_trip():
    draw = inv.draw_claims(inventory(), CLAIM_SEED)
    assert inv.read_draw_record(inv.draw_record(draw)) == draw
    bad = inv.draw_record(draw)
    bad["format"] = "other"
    with pytest.raises(inv.InventoryError):
        inv.read_draw_record(bad)
