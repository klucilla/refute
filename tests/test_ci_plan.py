"""The two-level CI plan (scripts/ci_plan.py), its test evidence (scripts/ci_evidence.py) and their
use in .github/workflows/ci.yml."""

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


ci_plan = _load("ci_plan")
ci_evidence = _load("ci_evidence")
Change = ci_plan.Change

A = "a" * 40
B = "b" * 40
ZERO = "0" * 40
WORKFLOW = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
PROOF = "seed of the draw\n\nCI: order-proof\n"


def run(event, change=None, message="", before=A, ref_type="branch", error=False):
    def read(a, b, merge_base):
        if error:
            raise RuntimeError("git failed")
        return change or Change(("tests/test_x.py",))

    return ci_plan.plan(event, ref_type, B, before, A, B, message, read)


# --- the levels, with a stubbed change


@pytest.mark.parametrize(
    "path",
    [
        "src/refute/core/verdict.py",
        "pyproject.toml",
        "uv.lock",
        "calibration/v0.5/claim.yaml",
        ".github/workflows/ci.yml",
    ],
)
def test_a_full_path_gives_the_full_matrix(path):
    assert run("push", Change(("docs/x.md", path))).level == "full"
    assert run("pull_request", Change((path,))).level == "full"


def test_other_paths_give_the_fast_matrix_with_the_recorded_values_elsewhere():
    p = run("push", Change(("docs/validation/x.json", "scripts/ci_shard.py", "tests/t.py")))
    assert p.level == "fast"
    assert p.pairs == [
        {"os": "ubuntu-24.04", "python": "3.12.15"},
        {"os": "windows-2025", "python": "3.13.16"},
    ]
    assert p.extra_pairs == [
        {"os": "ubuntu-24.04", "python": "3.13.16"},
        {"os": "windows-2025", "python": "3.12.15"},
    ]
    assert run("pull_request", Change(("tests/t.py",))).level == "fast"


def test_the_four_pairs_are_covered_on_every_test_run():
    p = run("push", Change(("tests/t.py",)))
    assert {tuple(x.values()) for x in p.pairs + p.extra_pairs} == set(ci_plan.FULL_PAIRS)
    full = run("schedule")
    assert len(full.pairs) == 4 and full.extra_pairs == []


def test_lookalike_paths_are_not_full():
    assert run("push", Change(("docs/src/x.md", "srcx/a.txt", "a/pyproject.toml"))).level == "fast"


def test_documentation_only_runs_no_test_but_readme_and_data_files_do():
    assert run("push", Change(("ROADMAP.md", "docs/plans/x.md", "docs/assets/a.png"))).level == (
        "docs"
    )
    for path in ("README.md", "docs/validation/x.json", "docs/x.py", "LICENSE"):
        assert run("push", Change(("ROADMAP.md", path))).level == "fast"


@pytest.mark.parametrize("event", ["schedule", "workflow_dispatch"])
def test_nightly_and_manual_runs_are_full(event):
    assert run(event).level == "full"


def test_a_tag_creation_is_full_and_a_branch_creation_runs_no_test():
    assert run("create", ref_type="tag").level == "full"
    p = run("create", ref_type="branch")
    assert (p.level, p.pairs, p.extra_pairs) == ("none", [], [])


def test_the_order_proof_trailer_records_without_tests():
    p = run("push", Change(("docs/plans/x-seed.json",)), message=PROOF)
    assert (p.level, p.pairs, p.extra_pairs) == ("record-only", [], [])


def test_the_trailer_is_ignored_unless_exact_single_and_outside_code():
    seed = Change(("docs/plans/x-seed.json",))
    assert run("push", seed, message="seed CI: order-proof").level == "fast"  # not a line
    assert run("push", Change(("src/refute/a.py",)), message=PROOF).level == "full"
    assert run("push", Change(("calibration/v0.6/seed.json",)), message=PROOF).level == "full"
    for path in ("tests/t.py", "scripts/s.py", "docs/x.py", ".python-version"):
        assert run("push", Change((path,)), message=PROOF).level == "fast"
    two = Change(("docs/plans/x.json",), commits=2)
    assert run("push", two, message=PROOF).level == "fast"
    merge = Change(("docs/plans/x.json",), head_is_merge=True)
    assert run("push", merge, message=PROOF).level == "fast"
    assert run("pull_request", seed, message=PROOF).level == "fast"


def test_unknown_history_rollback_or_git_errors_give_full():
    assert run("push", before=ZERO).level == "full"
    assert run("push", before="").level == "full"
    assert run("push", Change((), fast_forward=False)).level == "full"
    assert run("push", error=True).level == "full"
    assert run("pull_request", error=True).level == "full"
    assert run("something_else").level == "full"


def test_github_skip_tokens_are_not_the_trailer():
    for token in ("[skip ci]", "[ci skip]", "[no ci]", "[skip actions]", "[actions skip]"):
        assert token not in ci_plan.ORDER_PROOF


def test_main_writes_the_outputs(tmp_path, monkeypatch):
    out = tmp_path / "out.txt"
    monkeypatch.setenv("GITHUB_OUTPUT", str(out))
    monkeypatch.setenv("EVENT", "schedule")
    ci_plan.main()
    text = out.read_text(encoding="utf-8")
    assert "level=full" in text
    pairs = json.loads(next(x for x in text.splitlines() if x.startswith("pairs="))[6:])
    assert len(pairs) == 4
    assert "extra_pairs=[]" in text


# --- real git histories


def _git(repo, *args):
    cmd = ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args]
    return subprocess.run(cmd, cwd=repo, capture_output=True, check=True, text=True).stdout


def _commit(repo, files, msg="c"):
    for name, text in files.items():
        p = repo / name
        p.parent.mkdir(parents=True, exist_ok=True)
        if text is None:
            p.unlink()
        else:
            p.write_text(text, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", msg)
    return _git(repo, "rev-parse", "HEAD").strip()


@pytest.fixture
def repo(tmp_path):
    _git(tmp_path, "init", "-q", "-b", "main")
    return tmp_path


def _plan_git(repo, before, sha, message="c", event="push"):
    def read(a, b, merge_base):
        return ci_plan.git_change(a, b, merge_base, cwd=str(repo))

    base, head = (before, sha)
    return ci_plan.plan(event, "branch", sha, before, base, head, message, read)


def test_git_a_rollback_is_not_a_fast_forward(repo):
    c1 = _commit(repo, {"uv.lock": "1\n"})
    c2 = _commit(repo, {"uv.lock": "2\n"})
    assert _plan_git(repo, c2, c1).level == "full"


def test_git_a_change_reverted_within_the_batch_still_counts(repo):
    c0 = _commit(repo, {"README.md": "r\n", "src/a.py": "x = 1\n"})
    _commit(repo, {"src/a.py": "x = 2\n"})
    c2 = _commit(repo, {"src/a.py": "x = 1\n"})
    assert _git(repo, "diff", "--name-only", c0, c2) == ""
    assert _plan_git(repo, c0, c2).level == "full"


def test_git_a_merge_brings_its_branch_paths(repo):
    c0 = _commit(repo, {"README.md": "r\n"})
    _git(repo, "checkout", "-q", "-b", "side")
    _commit(repo, {"calibration/x.yaml": "a: 1\n"})
    _git(repo, "checkout", "-q", "main")
    _commit(repo, {"docs/n.md": "n\n"})
    _git(repo, "-c", "user.name=t", "merge", "-q", "--no-ff", "-m", "merge", "side")
    head = _git(repo, "rev-parse", "HEAD").strip()
    assert _plan_git(repo, c0, head).level == "full"


def test_git_a_non_ascii_path_under_src_is_read(repo):
    c0 = _commit(repo, {"README.md": "r\n"})
    c1 = _commit(repo, {"src/ação.py": "x = 1\n"})
    assert _plan_git(repo, c0, c1).level == "full"


def test_git_documentation_and_order_proof(repo):
    c0 = _commit(repo, {"README.md": "r\n"})
    c1 = _commit(repo, {"ROADMAP.md": "x\n"})
    assert _plan_git(repo, c0, c1).level == "docs"
    c2 = _commit(repo, {"docs/plans/seed.json": "{}\n"}, PROOF)
    assert _plan_git(repo, c1, c2, PROOF).level == "record-only"
    c3 = _commit(repo, {"docs/plans/a.json": "{}\n"})
    c4 = _commit(repo, {"docs/plans/b.json": "{}\n"}, PROOF)
    assert _plan_git(repo, c2, c4, PROOF).level == "fast"
    assert c3


def test_git_a_pull_request_compares_with_the_merge_base(repo):
    _commit(repo, {"README.md": "r\n"})
    _git(repo, "checkout", "-q", "-b", "pr")
    head = _commit(repo, {"tests/t.py": "x = 1\n"})
    _git(repo, "checkout", "-q", "main")
    base = _commit(repo, {"src/a.py": "y = 1\n"})
    # main's own src change is not the pull request's
    assert _plan_git(repo, base, head, event="pull_request").level == "fast"


# --- the workflow


def test_the_workflow_uses_the_plan_and_has_no_path_filter():
    assert "python3 scripts/ci_plan.py" in WORKFLOW
    assert "pair: ${{ fromJSON(needs.plan.outputs.pairs) }}" in WORKFLOW
    assert "pair: ${{ fromJSON(needs.plan.outputs.extra_pairs) }}" in WORKFLOW
    assert "if: needs.plan.outputs.pairs != '[]'" in WORKFLOW
    assert "if: needs.plan.outputs.extra_pairs != '[]'" in WORKFLOW
    for event in ("  create:", "  schedule:", "  workflow_dispatch:"):
        assert event in WORKFLOW
    on = WORKFLOW.split("\non:\n", 1)[1].split("\npermissions:", 1)[0]
    assert "paths-ignore" not in on and "paths:" not in on
    push = on.split("  push:", 1)[1].split("  pull_request:", 1)[0]
    assert "tags" not in push
    assert "matrix.os" not in WORKFLOW and "matrix.python" not in WORKFLOW


def test_the_recorded_value_job_runs_exactly_the_recorded_value_tests():
    job = WORKFLOW.split("  recorded-values:", 1)[1]
    line = next(x for x in job.splitlines() if "uv run pytest" in x)
    assert line.split("junit.xml", 1)[1].split() == list(ci_plan.RECORDED_VALUE_TESTS)
    for f in ci_plan.RECORDED_VALUE_TESTS:
        assert (ROOT / f).is_file()


def test_the_workflow_allowlist_holds_the_four_pairs():
    for os_, py in ci_plan.FULL_PAIRS:
        assert f"{os_}/{py}" in WORKFLOW
    assert WORKFLOW.count("Check the pair against the workflow's allowlist") == 2


# --- the evidence


def _jobs(names, conclusion="success"):
    return [{"name": n, "conclusion": conclusion} for n in names]


def test_evidence_needs_every_expected_job_on_the_exact_sha():
    sha = "c" * 40
    full = ci_evidence.expected_jobs("full")
    fast = ci_evidence.expected_jobs("fast")
    # eight shards since 2026-11-27 (heavy-g, #218 item I4): 4 pairs x 8 in full, and 2 x 8 plus
    # the 2 recorded-value jobs in fast
    assert len(full) == 32 and len(fast) == 18
    run_ = {"id": 1, "head_sha": sha, "path": ".github/workflows/ci.yml", "status": "completed"}
    assert ci_evidence.evaluate(sha, [run_], lambda i: _jobs(full), "full")[0]
    assert ci_evidence.evaluate(sha, [run_], lambda i: _jobs(fast), "fast")[0]
    # a fast run is no full evidence; a plan-only run is no evidence; a failure is none
    assert not ci_evidence.evaluate(sha, [run_], lambda i: _jobs(fast), "full")[0]
    assert not ci_evidence.evaluate(sha, [run_], lambda i: [{"name": "plan"}], "fast")[0]
    bad = _jobs(full)
    bad[0]["conclusion"] = "failure"
    assert not ci_evidence.evaluate(sha, [run_], lambda i: bad, "full")[0]
    other = dict(run_, head_sha="d" * 40)
    assert not ci_evidence.evaluate(sha, [other], lambda i: _jobs(full), "full")[0]
    pending = dict(run_, status="in_progress")
    assert not ci_evidence.evaluate(sha, [pending], lambda i: _jobs(full), "full")[0]
