"""The synthetic papers of WP4 (docs/validation/v0.3/wp4-acceptance.md, W4.1 to W4.3a), a
first set: value claims on the cataloged WP4 trainer (tests/fixtures/ml_papers/trainer.py)
and the cataloged ladder build, run end to end by the WP3 integration (#46) on the
subprocess backend.

Each paper is fixed here with its expected verdict **before its first run** (W4.1): this
file is committed on its own, before the tests that run the papers.

A paper is: the claim's attacks (by name), the trainer's configuration (the injected
effect), optional per-step configuration overrides (an effect on one attack's runs only),
the ladder plan (what each rung's build does), optional stage limits, and the expected
claim verdict with the expected status of the checks that decide it.

Not in this first set (listed in the pull request): the comparison papers (they need
predictions saved per method), the coverage papers of #15 that need other datasets, the
holdout and uncertainty papers of W4.3b and W4.3c, the reply draft, the seal and the
dossier verification of W4.4.
"""

from __future__ import annotations

from dataclasses import dataclass, field

REPRODUCED = "REPRODUCED"
FRAGILE = "FRAGILE"
NOT_REPRODUCED = "NOT_REPRODUCED"
NOT_REPRODUCIBLE = "NOT_REPRODUCIBLE"
INCONCLUSIVE = "INCONCLUSIVE"

ALL_ATTACKS = ("seeds", "data_split", "ablation", "holdout", "leakage", "trivial_baseline")
RUNGS = ("own_environment", "requirements_compiled", "requirements_compiled_next_python")
LADDER_OK = {RUNGS[0]: "ok", RUNGS[1]: "ok", RUNGS[2]: "ok"}
BASE_CONFIG = {"subsample": 1000, "aug_gain": 6}


@dataclass(frozen=True)
class SyntheticPaper:
    name: str
    case: str  # the case of wp4-acceptance.md it covers
    expected: str  # the expected claim verdict
    attacks: tuple[str, ...] = ()
    config: dict = field(default_factory=dict)  # added to BASE_CONFIG
    step_config: dict = field(default_factory=dict)  # step name -> config for its runs
    ladder: dict = field(default_factory=lambda: dict(LADDER_OK))
    stages: dict = field(default_factory=dict)  # stage name -> limits in hours
    reported: float = 89.2
    seed_argument: bool = True
    leak: int = 0  # test examples copied into train
    expected_checks: dict = field(default_factory=dict)  # check or attack name -> status
    expected_failures: dict = field(default_factory=dict)  # gate -> failure cause


PAPERS = [
    SyntheticPaper(
        "reproduced",
        "W4.3: REPRODUCED, with every attack",
        REPRODUCED,
        attacks=ALL_ATTACKS,
        expected_checks=dict.fromkeys(ALL_ATTACKS, "PASS"),
    ),
    SyntheticPaper(
        "seed-fragile",
        "W4.3: seed-fragile (the predicate fails on 2 of 5 seeds)",
        FRAGILE,
        attacks=("seeds",),
        config={"bad_seeds": "attack[:2]", "seed_penalty": 8},
        expected_checks={"seeds": "FAIL"},
    ),
    SyntheticPaper(
        "split-fragile",
        "W4.3: split-fragile (the predicate fails on 1 of 3 re-splits)",
        FRAGILE,
        attacks=("data_split",),
        config={"bad_split_seeds": "data_split[:1]", "split_penalty": 7},
        expected_checks={"data_split": "FAIL"},
    ),
    SyntheticPaper(
        "leaky",
        "W4.3: leaky (duplicates between train and test above the fixed fraction)",
        FRAGILE,
        attacks=("leakage",),
        leak=200,
        expected_checks={"leakage": "FAIL"},
    ),
    SyntheticPaper(
        "metric-bug",
        "W4.3 and W4.3a: metric bug, metric_recompute fatal path",
        NOT_REPRODUCED,
        config={"print_bias": 0.5},
        expected_checks={"metric_recompute": "FAIL"},
    ),
    SyntheticPaper(
        "not-reproducible",
        "W4.3: the controlled NOT_REPRODUCIBLE (every rung fails by its procedure)",
        NOT_REPRODUCIBLE,
        ladder={r: "procedure_error" for r in RUNGS},
        expected_checks={"environment_build": "FAIL"},
        expected_failures={"environment_build": "artifact_build_ladder"},
    ),
    SyntheticPaper(
        "not-reproducible-twin",
        "W4.3: its twin, interrupted on Refute's side (a guard stops a rung)",
        INCONCLUSIVE,
        ladder={RUNGS[0]: "procedure_error", RUNGS[1]: "busy", RUNGS[2]: "procedure_error"},
        stages={"build": {"active_time_limit_hours": 0.001, "no_progress_hours": 0.0008}},
        expected_checks={"environment_build": "INCONCLUSIVE"},
        expected_failures={"environment_build": "operational_guard"},
    ),
    SyntheticPaper(
        "failed-run",
        "W4.3: INCONCLUSIVE, a run that fails (item D of 2026-10-16)",
        INCONCLUSIVE,
        config={"exit_code": 3},
        expected_checks={"run_completed": "FAIL"},
        expected_failures={"run_completed": "undetermined"},
    ),
    SyntheticPaper(
        "interrupted-attack",
        "W4.3: an interrupted attack next to a valid failure (must stay FRAGILE)",
        FRAGILE,
        attacks=("seeds", "data_split"),
        config={"bad_seeds": "attack[:2]", "seed_penalty": 8},
        step_config={"data_split": {"sleep_s": 60}},
        stages={"attack_run": {"active_time_limit_hours": 0.01, "no_progress_hours": 0.001}},
        expected_checks={"seeds": "FAIL", "data_split": "INCONCLUSIVE"},
    ),
    SyntheticPaper(
        "ablation-fragile",
        "W4.3a: ablation (the switched-off component makes no difference)",
        FRAGILE,
        attacks=("ablation",),
        config={"aug_gain": 0},
        expected_checks={"ablation": "FAIL"},
    ),
    SyntheticPaper(
        "holdout-fragile",
        "W4.3a and W4.3b: holdout, a model fitted to its evaluation split",
        FRAGILE,
        attacks=("holdout",),
        config={"memorize_test": True},
        reported=100.0,
        expected_checks={"holdout": "FAIL"},
    ),
    SyntheticPaper(
        "no-seed-option",
        "W4.3a: a repository with no seed option (one base run; seeds not applicable)",
        REPRODUCED,
        seed_argument=False,
    ),
    SyntheticPaper(
        "no-attack",
        "W4.3: n_attack = 0 (no applicable attack)",
        REPRODUCED,
    ),
]

# a claim file with three claims, for the execution in phases (W4.3a, WP3 D-S4)
PHASES = {"claims": 3, "attacks": ("seeds",), "expected": [REPRODUCED, REPRODUCED, REPRODUCED]}
