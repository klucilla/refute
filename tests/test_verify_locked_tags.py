"""scripts/verify_locked_tags.py: the separate list of the v0.3 locks (direct PASS at the frozen
code, never projected), one output file per claim, and a joint result that needs every claim
(the maintainer's decision of 2026-10-20, items 3 and 4). No network: verify and uv are faked."""

from __future__ import annotations

import importlib.util
import json
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLAIM = "calibration/v0.3/main/claims/2302.12465/claim/claim.yaml"


def load_script():
    spec = importlib.util.spec_from_file_location(
        "verify_locked_tags_v03", ROOT / "scripts" / "verify_locked_tags.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git(cwd, *args):
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.invalid", *args],
        cwd=cwd,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


@pytest.fixture
def v03_repo(tmp_path):
    """A small git repository holding a copy of one v0.3 claim folder (claim, lock, history,
    attachments) at its repository path."""
    repo = tmp_path / "repo"
    source = ROOT / Path(CLAIM).parent
    shutil.copytree(source, repo / Path(CLAIM).parent)
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "snapshot")
    return repo, git(repo, "rev-parse", "HEAD")


def entry_for(script, claim=CLAIM):
    return next(d for d in script.DIRECT_LOCKS if d.claim == claim)


# The list ------------------------------------------------------------------------------------


def test_the_five_v03_locks_are_a_separate_list_never_in_the_projection_table():
    script = load_script()
    from refute.core.lock_compat import HISTORICAL_LOCKS

    assert len(script.DIRECT_LOCKS) == 5
    assert {d.tag for d in script.DIRECT_LOCKS} == {"v0.3.0-main-lock"}
    assert {d.commit for d in script.DIRECT_LOCKS} == {"b6f5346cbf2d6c5398b3da2ec37d91a6ae1c87bc"}
    projected = [dict(e.identity) for e in HISTORICAL_LOCKS]
    for direct in script.DIRECT_LOCKS:
        assert dict(direct.identity) not in projected
        assert direct.identity["claim_path_in_repo"] == direct.claim
    assert {t for t, _ in script.LOCKED_TAGS} == {"v0.1.0", "v0.2.0-calibration-lock"}


def test_each_expected_identity_is_the_identity_of_its_committed_lock():
    script = load_script()
    from refute.core.lock_compat import lock_identity

    for direct in script.DIRECT_LOCKS:
        lock_file = ROOT / Path(direct.claim).with_suffix(".lock.json")
        lock = json.loads(lock_file.read_text(encoding="utf-8"))
        assert lock_identity(lock) == dict(direct.identity)


def test_every_check_writes_its_own_file():
    script = load_script()
    checks = script.expected_checks()
    names = [script.output_name(c.tag, c.claim) for c in checks]
    assert len(checks) == 7
    assert len(set(names)) == len(names)
    assert all(
        n.startswith(c.tag + "__") and n.endswith(".json")
        for c, n in zip(checks, names, strict=True)
    )
    assert "summary.json" not in names


# The worktree of a direct lock ----------------------------------------------------------------


def test_a_clean_worktree_at_the_commit_with_the_expected_identity_is_trusted(v03_repo):
    repo, head = v03_repo
    script = load_script()
    identity = entry_for(script).identity
    assert script.direct_worktree_problems(repo, CLAIM, head, identity) == []


def test_a_changed_tracked_file_or_an_untracked_file_is_refused(v03_repo):
    repo, head = v03_repo
    script = load_script()
    identity = entry_for(script).identity
    stray = repo / "src" / "refute" / "extra.py"
    stray.parent.mkdir(parents=True)
    stray.write_text("x = 1\n", encoding="utf-8")
    problems = script.direct_worktree_problems(repo, CLAIM, head, identity)
    assert any("not clean" in p for p in problems)
    stray.unlink()
    claim = repo / CLAIM
    claim.write_text(claim.read_text(encoding="utf-8") + "\n# edited\n", encoding="utf-8")
    problems = script.direct_worktree_problems(repo, CLAIM, head, identity)
    assert any("not clean" in p for p in problems)


def test_another_commit_or_another_identity_is_refused(v03_repo):
    repo, head = v03_repo
    script = load_script()
    identity = entry_for(script).identity
    assert any(
        "expected" in p for p in script.direct_worktree_problems(repo, CLAIM, "0" * 40, identity)
    )
    other = dict(identity, locked_at_utc="2026-10-19T00:00:00Z")
    problems = script.direct_worktree_problems(repo, CLAIM, head, other)
    assert any("expected identity: locked_at_utc" in p for p in problems)


# The joint result -----------------------------------------------------------------------------


def passing(script, check):
    identity = check.identity or {}
    return {
        "status": "PASS",
        "claim_projection": None,
        "locked_claim_sha256": identity.get("claim_sha256"),
        "current_claim_sha256": identity.get("claim_sha256"),
        "locked_code_sha256": identity.get("code_sha256"),
        "current_code_sha256": identity.get("code_sha256"),
    }


def test_the_joint_result_needs_every_expected_check():
    script = load_script()
    checks = script.expected_checks()
    good = {c.key: {"status": "PASS", "problems": []} for c in checks}
    assert script.summarize(checks, good)["joint"] == "PASS"
    missing = dict(good)
    missing.pop(checks[-1].key)
    assert script.summarize(checks, missing)["joint"] == "FAIL"
    one_bad = dict(good, **{checks[3].key: {"status": "TAMPERED", "problems": ["verify"]}})
    summary = script.summarize(checks, one_bad)
    assert summary["joint"] == "FAIL"
    assert summary["passed"] == len(checks) - 1
    extra = dict(good, **{"x::y": {"status": "PASS", "problems": []}})
    assert script.summarize(checks, extra)["joint"] == "FAIL"
    assert script.summarize([], {})["joint"] == "FAIL"


def test_a_direct_lock_passes_only_by_a_direct_pass_with_its_own_hashes():
    script = load_script()
    check = next(c for c in script.expected_checks() if c.kind == "direct")
    assert script.result_problems(check, passing(script, check), 0) == []
    assert script.result_problems(check, passing(script, check), 2)
    projected = dict(passing(script, check), claim_projection="tess-calibration-v0.2@e176ac3")
    assert any("projection" in p for p in script.result_problems(check, projected, 0))
    other_code = dict(passing(script, check), current_code_sha256="0" * 64)
    assert any("current code" in p for p in script.result_problems(check, other_code, 0))
    tampered = dict(passing(script, check), status="TAMPERED")
    assert script.result_problems(check, tampered, 2)
    assert script.result_problems(check, None, None) == ["no verify result"]


def run_with(script, tmp_path, monkeypatch, verdict_for):
    """run_checks with a faked worktree, trust check and verify; ``verdict_for(check)`` gives
    the verify result (a dict, dumped as JSON, or a str, the raw output) and the exit code of
    each claim."""
    monkeypatch.setattr(script, "worktree_problems", lambda *a: [])
    monkeypatch.setattr(script, "direct_worktree_problems", lambda *a: [])
    checks = script.expected_checks()
    by_claim = {c.claim: c for c in checks}

    def prepare(tag, commit):
        return script.Prepared(tmp_path, "present", commit or "c" * 40)

    def verify(worktree, claim):
        result, code = verdict_for(by_claim[claim])
        return (result if isinstance(result, str) else json.dumps(result)), code

    out = tmp_path / "out"
    return script.run_checks(checks, out, prepare, verify), out


def test_one_failing_claim_makes_the_joint_verification_fail(tmp_path, monkeypatch):
    script = load_script()
    bad = "calibration/v0.3/main/claims/2407.11735/claim/claim.yaml"

    def verdict(check):
        if check.claim == bad:
            return dict(passing(script, check), status="TAMPERED"), 2
        return passing(script, check), 0

    summary, out = run_with(script, tmp_path, monkeypatch, verdict)
    assert summary["joint"] == "FAIL"
    assert [r["claim"] for r in summary["checks"] if not r["pass"]] == [bad]
    written = sorted(p.name for p in out.iterdir())
    assert len(written) == 8 and "summary.json" in written
    saved = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert saved["joint"] == "FAIL"


def test_every_claim_passing_gives_a_joint_pass(tmp_path, monkeypatch):
    script = load_script()
    summary, out = run_with(script, tmp_path, monkeypatch, lambda c: (passing(script, c), 0))
    assert summary["joint"] == "PASS"
    assert summary["passed"] == 7
    assert summary["tags_absent"] == []


CLAIMS = [c.claim for c in load_script().expected_checks()]


@pytest.mark.parametrize("bad", CLAIMS)
def test_each_claim_failing_alone_fails_the_joint_verification(bad, tmp_path, monkeypatch):
    script = load_script()

    def verdict(check):
        if check.claim == bad:
            return dict(passing(script, check), status="FAIL"), 1
        return passing(script, check), 0

    summary, _ = run_with(script, tmp_path, monkeypatch, verdict)
    assert summary["joint"] == "FAIL"
    assert [r["claim"] for r in summary["checks"] if not r["pass"]] == [bad]


@pytest.mark.parametrize("raw", ["null", "[]", "7", '"PASS"', "", "{not json"])
def test_an_output_that_is_not_a_json_object_never_passes(raw, tmp_path, monkeypatch):
    """Codex review of d1ad932, finding 1: `null` with exit 27 gave a joint PASS; finding 2:
    `[]` raised before the summary was written."""
    script = load_script()
    bad = "calibration/v0.3/main/claims/2309.15704/claim/claim.yaml"

    def verdict(check):
        if check.claim == bad:
            return raw, 27
        return passing(script, check), 0

    summary, out = run_with(script, tmp_path, monkeypatch, verdict)
    assert summary["joint"] == "FAIL"
    row = next(r for r in summary["checks"] if r["claim"] == bad)
    assert not row["pass"] and row["status"] is None
    assert json.loads((out / "summary.json").read_text(encoding="utf-8"))["joint"] == "FAIL"


def test_a_pass_with_a_failing_exit_code_never_passes(tmp_path, monkeypatch):
    script = load_script()
    summary, _ = run_with(
        script,
        tmp_path,
        monkeypatch,
        lambda c: (passing(script, c), 27 if c.kind == "direct" else 0),
    )
    assert summary["joint"] == "FAIL" and summary["passed"] == 2


def test_a_verify_that_raises_is_a_recorded_failure(tmp_path, monkeypatch):
    script = load_script()

    def verdict(check):
        if check.kind == "historical":
            raise OSError("uv not found")
        return passing(script, check), 0

    summary, out = run_with(script, tmp_path, monkeypatch, verdict)
    assert summary["joint"] == "FAIL" and summary["passed"] == 5
    assert (out / "summary.json").is_file()


def test_a_row_without_a_pass_status_never_passes_even_with_no_problems():
    script = load_script()
    checks = script.expected_checks()
    good = {c.key: {"status": "PASS", "problems": []} for c in checks}
    good[checks[0].key] = {"status": None, "problems": []}
    assert script.summarize(checks, good)["joint"] == "FAIL"


def test_an_output_folder_of_an_earlier_run_is_refused(tmp_path, monkeypatch):
    """Codex review of d1ad932, finding 2: an earlier summary must never be read as current."""
    script = load_script()
    out = tmp_path / "out"
    out.mkdir()
    (out / "summary.json").write_text('{"joint": "PASS"}\n', encoding="utf-8")
    with pytest.raises(SystemExit, match="not empty"):
        run_with(script, tmp_path, monkeypatch, lambda c: (passing(script, c), 0))
    assert sorted(p.name for p in out.iterdir()) == ["summary.json"]


def test_a_tag_that_cannot_be_prepared_fails_each_of_its_claims(tmp_path, monkeypatch):
    script = load_script()
    checks = script.expected_checks()

    def prepare(tag, commit):
        if tag == "v0.3.0-main-lock":
            return script.Prepared(None, "absent", commit or "", ("tag does not exist",))
        return script.Prepared(tmp_path, "present", "c" * 40)

    monkeypatch.setattr(script, "worktree_problems", lambda *a: [])
    summary = script.run_checks(
        checks, tmp_path / "out", prepare, lambda w, c: (json.dumps({"status": "PASS"}), 0)
    )
    assert summary["joint"] == "FAIL"
    assert summary["passed"] == 2


# The tag --------------------------------------------------------------------------------------


@pytest.fixture
def tagged(v03_repo, monkeypatch, tmp_path):
    repo, head = v03_repo
    script = load_script()
    monkeypatch.setattr(script, "ROOT", repo)
    monkeypatch.setattr(script, "WORK", repo / ".cache" / "lock-compat")
    real_run = script.run

    def run(args, cwd):  # uv is never run by the tests
        if args[0] == "uv":
            return subprocess.CompletedProcess(args, 0, "", "")
        return real_run(args, cwd)

    monkeypatch.setattr(script, "run", run)
    return script, repo, head


def test_a_missing_tag_fails_unless_allowed_then_the_commit_is_checked(tagged):
    script, repo, head = tagged
    refused = script.make_prepare([], allow_missing_tags=False)("v0.3.0-main-lock", head)
    assert refused.worktree is None and "does not exist" in refused.problems[0]
    allowed = script.make_prepare([], allow_missing_tags=True)("v0.3.0-main-lock", head)
    assert allowed.problems == () and allowed.tag_state.startswith("absent")
    assert git(allowed.worktree, "rev-parse", "HEAD") == head
    git(repo, "worktree", "remove", "--force", str(allowed.worktree))


def test_a_tag_on_another_commit_is_refused_even_when_missing_tags_are_allowed(tagged):
    script, repo, head = tagged
    (repo / "note.txt").write_text("later\n", encoding="utf-8")
    git(repo, "add", "note.txt")
    git(repo, "commit", "-q", "-m", "later")
    git(repo, "tag", "-a", "v0.3.0-main-lock", "-m", "t")  # on the later commit
    prepared = script.make_prepare([], allow_missing_tags=True)("v0.3.0-main-lock", head)
    assert prepared.worktree is None
    assert "points to" in prepared.problems[0]


def test_a_branch_of_the_same_name_is_not_the_tag(tagged):
    """Codex review of d1ad932, finding 3: only refs/tags/<tag> counts."""
    script, repo, head = tagged
    git(repo, "branch", "v0.3.0-main-lock", head)
    refused = script.make_prepare([], allow_missing_tags=False)("v0.3.0-main-lock", head)
    assert refused.worktree is None and "does not exist" in refused.problems[0]
    allowed = script.make_prepare([], allow_missing_tags=True)("v0.3.0-main-lock", head)
    assert allowed.tag_state.startswith("absent")
    git(repo, "worktree", "remove", "--force", str(allowed.worktree))


def test_a_tag_on_its_commit_is_used(tagged):
    script, repo, head = tagged
    git(repo, "tag", "-a", "v0.3.0-main-lock", "-m", "t", head)
    prepared = script.make_prepare([], allow_missing_tags=False)("v0.3.0-main-lock", head)
    assert prepared.problems == () and prepared.tag_state == "present"
    assert prepared.commit == head
    git(repo, "worktree", "remove", "--force", str(prepared.worktree))
