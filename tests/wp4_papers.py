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

The detailed expectations (``expected_counts``, ``interrupted``, ``interrupted_steps``,
``flags``, ``incomplete``, ``not_applicable``) were added after the first runs, asked by the
Codex review of #111. They restate what each case's text already fixed in the first commit
of this file (for example "2 of 5 seeds") or what the WP2 core gives for that case; no
expected verdict changed. One of them, the flags of ``failed-run``, was wrong as first
written and was corrected after its first check (0cdf05d): an expectation erratum, accepted
as such by the maintainer on 2026-10-16, which is not an approval of the original
expectation.

``no-seed-option`` is the claim's declaration: the claim has no seed argument and records
the ``seeds`` attack as not applicable, with its reason. The cataloged trainer itself still
accepts ``--seed``; the runs simply never receive it.

**The coverage routes of ``metric_extracted``** (wp3-acceptance.md 1.5a, implemented in
#110): the papers ``route-*`` and ``routes-*`` put each route on both sides, the side where
it shows the examples (the claim reproduces) and the side where it does not close the
chain or finds a conflict (``metric_extracted`` is INCONCLUSIVE, so the claim is). Their
expectations are fixed here, in their own commit, before the runner supports them. A paper
declares its routes (``routes``) and whether ``metric_recompute`` applies (``recompute``);
every other paper keeps the saved predictions route with ``metric_recompute``.
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
    # one run of the seeds attack -> config, named by the claim's seed list ("attack[2]")
    seed_config: dict = field(default_factory=dict)
    ladder: dict = field(default_factory=lambda: dict(LADDER_OK))
    stages: dict = field(default_factory=dict)  # stage name -> limits in hours
    reported: float = 89.2
    seed_argument: bool = True
    leak: int = 0  # test examples copied into train
    expected_checks: dict = field(default_factory=dict)  # check or attack name -> status
    expected_failures: dict = field(default_factory=dict)  # gate -> failure cause
    # attack -> (valid runs, valid failures) of the attack's own result
    expected_counts: dict = field(default_factory=dict)
    # runs of the seeds attack a guard must stop, named by the claim's seed list ("attack[2]")
    interrupted: tuple[str, ...] = ()
    # attack steps every run of which a guard must stop (the step ends as operational_guard)
    interrupted_steps: tuple[str, ...] = ()
    # the claim's status flags (W4.4): (basic reproduction obtained, incomplete coverage)
    flags: tuple[bool, bool] = (True, False)
    # attacks recorded as incomplete (a result below the attack's expected coverage)
    incomplete: tuple[str, ...] = ()
    # attack -> the reason the claim records for it not applying
    not_applicable: dict = field(default_factory=dict)
    # the coverage routes the claim declares (1.5a), and whether metric_recompute applies
    routes: tuple[str, ...] = ("saved_predictions",)
    recompute: bool = True


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
        expected_counts={"seeds": (5, 2)},
    ),
    SyntheticPaper(
        "split-fragile",
        "W4.3: split-fragile (the predicate fails on 1 of 3 re-splits)",
        FRAGILE,
        attacks=("data_split",),
        config={"bad_split_seeds": "data_split[:1]", "split_penalty": 7},
        expected_checks={"data_split": "FAIL"},
        expected_counts={"data_split": (3, 1)},
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
        flags=(False, False),
    ),
    SyntheticPaper(
        "not-reproducible",
        "W4.3: the controlled NOT_REPRODUCIBLE (every rung fails by its procedure)",
        NOT_REPRODUCIBLE,
        ladder={r: "procedure_error" for r in RUNGS},
        expected_checks={"environment_build": "FAIL"},
        expected_failures={"environment_build": "artifact_build_ladder"},
        flags=(False, False),
    ),
    SyntheticPaper(
        "not-reproducible-twin",
        "W4.3: its twin, interrupted on Refute's side (a guard stops a rung)",
        INCONCLUSIVE,
        ladder={RUNGS[0]: "procedure_error", RUNGS[1]: "busy", RUNGS[2]: "procedure_error"},
        stages={"build": {"active_time_limit_hours": 0.001, "no_progress_hours": 0.0008}},
        expected_checks={"environment_build": "INCONCLUSIVE"},
        expected_failures={"environment_build": "operational_guard"},
        flags=(False, True),
    ),
    SyntheticPaper(
        "failed-run",
        "W4.3: INCONCLUSIVE, a run that fails (item D of 2026-10-16)",
        INCONCLUSIVE,
        config={"exit_code": 3},
        expected_checks={"run_completed": "FAIL"},
        expected_failures={"run_completed": "undetermined"},
        # EXPECTATION ERRATUM (commit 0cdf05d, accepted as such by the maintainer on
        # 2026-10-16; not an approval of the original expectation): set to (False, False)
        # in a389d0c and corrected after its first check. No run completed, so the failed
        # gate has zero coverage and the coverage rule makes it INCONCLUSIVE, an incomplete
        # coverage. The expected verdict (INCONCLUSIVE) is unchanged.
        flags=(False, True),
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
        expected_counts={"seeds": (5, 2)},
        interrupted_steps=("data_split",),
        flags=(True, True),
    ),
    SyntheticPaper(
        "seeds-interrupted-established",
        "W4.3 (Codex review of #110): inside one attack, two valid failures and an interrupted "
        "run: the failure stays established",
        FRAGILE,
        attacks=("seeds",),
        config={"bad_seeds": "attack[:2]", "seed_penalty": 8},
        seed_config={"attack[2]": {"sleep_s": 60}},
        stages={"attack_run": {"active_time_limit_hours": 0.01, "no_progress_hours": 0.001}},
        expected_checks={"seeds": "FAIL"},
        expected_counts={"seeds": (4, 2)},
        interrupted=("attack[2]",),
        flags=(True, True),
        incomplete=("seeds",),
    ),
    SyntheticPaper(
        "seeds-interrupted-insufficient",
        "W4.3 (Codex review of #110): inside one attack, an interrupted run and no valid "
        "failure: never a PASS",
        INCONCLUSIVE,
        attacks=("seeds",),
        seed_config={"attack[2]": {"sleep_s": 60}},
        stages={"attack_run": {"active_time_limit_hours": 0.01, "no_progress_hours": 0.001}},
        expected_checks={"seeds": "INCONCLUSIVE"},
        expected_counts={"seeds": (4, 0)},
        interrupted=("attack[2]",),
        flags=(True, True),
        incomplete=("seeds",),
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
        not_applicable={"seeds": "the repository has no seed option"},
    ),
    SyntheticPaper(
        "no-attack",
        "W4.3: n_attack = 0 (no applicable attack)",
        REPRODUCED,
    ),
    # ---- the coverage routes of metric_extracted (1.5a), on both sides ----
    SyntheticPaper(
        "route-c-shown",
        "1.5a (c): the saved predictions show the split's examples, in its order",
        REPRODUCED,
        expected_checks={"metric_extracted": "PASS", "metric_recompute": "PASS"},
    ),
    SyntheticPaper(
        "route-c-other-order",
        "1.5a (c), W3.12d limitation: the predictions saved in another order keep the "
        "accuracy but do not identify the split",
        INCONCLUSIVE,
        config={"shuffle_preds": True},
        expected_checks={"metric_extracted": "INCONCLUSIVE"},
        expected_failures={"metric_extracted": "undetermined"},
        flags=(False, True),
    ),
    SyntheticPaper(
        "route-d-shown",
        "1.5a (d): correct and total give the printed value",
        REPRODUCED,
        config={"stats": True},
        routes=("sufficient_statistics",),
        recompute=False,
        expected_checks={"metric_extracted": "PASS"},
    ),
    SyntheticPaper(
        "route-d-conflict",
        "1.5a (d): correct and total that do not give the printed value (a conflict)",
        INCONCLUSIVE,
        config={"stats": True, "stats_bias": 8},
        routes=("sufficient_statistics",),
        recompute=False,
        expected_checks={"metric_extracted": "INCONCLUSIVE"},
        expected_failures={"metric_extracted": "undetermined"},
        flags=(False, True),
    ),
    SyntheticPaper(
        "route-a-shown",
        "1.5a (a): the printed count is the split's size",
        REPRODUCED,
        config={"print_count": True},
        routes=("printed_count",),
        recompute=False,
        expected_checks={"metric_extracted": "PASS"},
    ),
    SyntheticPaper(
        "route-a-other-count",
        "1.5a (a): a printed count that is not the split's declared size",
        INCONCLUSIVE,
        config={"print_count": True, "count_bias": -1},
        routes=("printed_count",),
        recompute=False,
        expected_checks={"metric_extracted": "INCONCLUSIVE"},
        expected_failures={"metric_extracted": "undetermined"},
        flags=(False, True),
    ),
    SyntheticPaper(
        "route-a-absent",
        "1.5a: no route closes the chain (the declared count is never printed)",
        INCONCLUSIVE,
        routes=("printed_count",),
        recompute=False,
        expected_checks={"metric_extracted": "INCONCLUSIVE"},
        expected_failures={"metric_extracted": "undetermined"},
        flags=(False, True),
    ),
    SyntheticPaper(
        "route-b-shown",
        "1.5a (b): one hook event bound to the metric, the split, the run and the call site",
        REPRODUCED,
        config={"hook": True},
        routes=("hook",),
        recompute=False,
        expected_checks={"metric_extracted": "PASS"},
    ),
    SyntheticPaper(
        "route-b-two-events",
        "1.5a (b), W3.12c: two events at the cited call site (not exactly one)",
        INCONCLUSIVE,
        config={"hook": True, "hook_calls": 2},
        routes=("hook",),
        recompute=False,
        expected_checks={"metric_extracted": "INCONCLUSIVE"},
        expected_failures={"metric_extracted": "undetermined"},
        flags=(False, True),
    ),
    SyntheticPaper(
        "route-b-other-split",
        "1.5a (b): the cited call evaluates another split (its labels are not the split's)",
        INCONCLUSIVE,
        config={"hook": True, "hook_split": "validation"},
        routes=("hook",),
        recompute=False,
        expected_checks={"metric_extracted": "INCONCLUSIVE"},
        expected_failures={"metric_extracted": "undetermined"},
        flags=(False, True),
    ),
    SyntheticPaper(
        "routes-disagree",
        "1.5a W3.12e: (c) shows 4000 examples, (a) prints 4001; all_must_agree, no route wins",
        INCONCLUSIVE,
        config={"print_count": True, "count_bias": 1},
        routes=("saved_predictions", "printed_count"),
        expected_checks={"metric_extracted": "INCONCLUSIVE"},
        expected_failures={"metric_extracted": "undetermined"},
        flags=(False, True),
    ),
    SyntheticPaper(
        "routes-value-conflict",
        "1.5a W3.12e (Codex review of #110): (d) follows a tampered printed value, (c)'s "
        "predictions keep the original; the counts agree, the values do not: a conflict, "
        "never NOT_REPRODUCED",
        INCONCLUSIVE,
        config={"stats": True, "stats_bias": 8, "print_bias": 0.2},
        routes=("saved_predictions", "sufficient_statistics"),
        expected_checks={"metric_extracted": "INCONCLUSIVE"},
        expected_failures={"metric_extracted": "undetermined"},
        flags=(False, True),
    ),
    SyntheticPaper(
        "route-b-ambiguous-next-to-a-count",
        "1.5a W3.12c (Codex review of #110): two bound hook events next to a printed count "
        "that works; the ambiguity is not hidden",
        INCONCLUSIVE,
        config={"print_count": True, "hook": True, "hook_calls": 2},
        routes=("printed_count", "hook"),
        recompute=False,
        expected_checks={"metric_extracted": "INCONCLUSIVE"},
        expected_failures={"metric_extracted": "undetermined"},
        flags=(False, True),
    ),
    SyntheticPaper(
        "routes-all-agree",
        "1.5a: every route together, all agreeing",
        REPRODUCED,
        config={"print_count": True, "stats": True, "hook": True},
        routes=("saved_predictions", "sufficient_statistics", "printed_count", "hook"),
        expected_checks={"metric_extracted": "PASS", "metric_recompute": "PASS"},
    ),
]

# a claim file with three claims, for the execution in phases (W4.3a, WP3 D-S4)
PHASES = {"claims": 3, "attacks": ("seeds",), "expected": [REPRODUCED, REPRODUCED, REPRODUCED]}
