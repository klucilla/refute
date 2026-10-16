"""The synthetic catalog and the subprocess backend's refusals (WP3 W3.8; item E of the
maintainer's review of 2026-10-16, design A'; closes the gap of #87), and the build ladder
played by a cataloged fixture under the subprocess backend, end to end through the WP2
core. Offline."""

import hashlib
import json
import os
import sys

import pytest

from refute.core.paper import FailureCause, aggregate_claim
from refute.core.verdict import PaperVerdict, TestStatus
from refute.packs.ml import ladder as ld
from refute.packs.ml import sandbox as sb
from refute.packs.ml import synthetic as sy
from refute.packs.ml.orchestrate import Outcome
from synthetic_harness import SOURCES, fixture


def spec(root, argv, **kw):
    values = dict(
        argv=argv,
        workdir=root,
        env=dict(os.environ),
        log_path=root.parent / "logs" / "run.log",
        threshold_usec=None,
        active_time_limit_s=60.0,
        no_progress_s=30.0,
        poll_s=0.05,
    )
    values.update(kw)
    return sb.RunSpec(**values)


PROBE = [sys.executable, "-I", "probe.py", "exit", "0"]


# ---- the catalog ------------------------------------------------------------------------------


def test_the_catalog_pins_the_bytes_of_every_fixture_source():
    """Changing a fixture's code means changing the catalog, in a reviewed commit."""
    assert set(sy.CATALOG) == set(SOURCES)
    for name, files in SOURCES.items():
        for path, source in files.items():
            digest = hashlib.sha256(source.read_bytes()).hexdigest()
            assert sy.CATALOG[name].code[path] == digest, (name, path)


def test_materialize_refuses_anything_outside_the_catalog(tmp_path):
    code = {"probe.py": SOURCES["sandbox-probe"]["probe.py"].read_bytes()}
    with pytest.raises(sy.SyntheticRefusedError, match="not a fixture"):
        sy.materialize("real-paper", tmp_path / "a", code)
    with pytest.raises(sy.SyntheticRefusedError, match="cataloged bytes"):
        sy.materialize("sandbox-probe", tmp_path / "b", {"probe.py": code["probe.py"] + b"\n"})
    with pytest.raises(sy.SyntheticRefusedError, match="code files"):
        sy.materialize("sandbox-probe", tmp_path / "c", {**code, "extra.py": b"print(1)\n"})
    with pytest.raises(sy.SyntheticRefusedError, match="code files"):
        sy.materialize("sandbox-probe", tmp_path / "d", {})
    with pytest.raises(sy.SyntheticRefusedError, match="data files not allowed"):
        sy.materialize("sandbox-probe", tmp_path / "e", code, {"sitecustomize.py": b""})
    (tmp_path / "f").mkdir()
    (tmp_path / "f" / "x.txt").write_text("x")
    with pytest.raises(sy.SyntheticRefusedError, match="new or empty"):
        sy.materialize("sandbox-probe", tmp_path / "f", code)


def test_an_authorization_is_created_only_by_materialize(tmp_path):
    with pytest.raises(sy.SyntheticRefusedError, match="only by materialize"):
        sy.Authorization(sy.CATALOG["sandbox-probe"], tmp_path, {}, object())
    with pytest.raises(sy.SyntheticRefusedError, match="not an authorization"):
        sb.SubprocessBackend(["not an authorization"])


# ---- the backend refuses everything that is not a synthetic fixture (the gap of #87) ----------


def test_a_backend_with_no_authorization_runs_nothing(tmp_path):
    """A real repository's command is refused before any process starts."""
    repo = tmp_path / "repo"
    repo.mkdir()
    marker = repo / "ran.txt"
    (repo / "train.py").write_text(f"open({str(marker)!r}, 'w').write('x')\n")
    with pytest.raises(sy.SyntheticRefusedError, match="runs nothing else"):
        sb.SubprocessBackend().run(spec(repo, [sys.executable, "-I", "train.py"]))
    assert not marker.exists()


def test_an_unauthorized_folder_is_refused_even_with_a_cataloged_script(tmp_path):
    auth = fixture("sandbox-probe", tmp_path / "fixture")
    copy = fixture("sandbox-probe", tmp_path / "copy")  # authorized, but not given
    backend = sb.SubprocessBackend([auth])
    with pytest.raises(sy.SyntheticRefusedError, match="runs nothing else"):
        backend.run(spec(copy.root, PROBE))


@pytest.mark.parametrize(
    "argv",
    [
        ["python", "-I", "probe.py", "exit", "0"],  # not this interpreter
        [sys.executable, "probe.py", "exit", "0"],  # not isolated
        [sys.executable, "-c", "print(1)"],  # inline code
        [sys.executable, "-I", "-c", "print(1)"],
        [sys.executable, "-I", "other.py"],  # not a code file of the fixture
        [sys.executable, "-I", "../probe.py"],  # outside the fixture
    ],
)
def test_a_command_that_is_not_a_fixture_code_file_is_refused(tmp_path, argv):
    auth = fixture("sandbox-probe", tmp_path / "fixture")
    with pytest.raises(sy.SyntheticRefusedError):
        sb.SubprocessBackend([auth]).run(spec(auth.root, argv))


def test_a_changed_or_added_file_is_refused(tmp_path):
    auth = fixture("sandbox-probe", tmp_path / "fixture")
    backend = sb.SubprocessBackend([auth])
    assert backend.run(spec(auth.root, PROBE)).exit_code == 0
    (auth.root / "out").mkdir()
    (auth.root / "out" / "result.txt").write_text("an output is allowed")
    assert backend.run(spec(auth.root, PROBE)).exit_code == 0
    shadow = auth.root / "json.py"  # would shadow a module: the script's folder is on sys.path
    shadow.write_text("raise SystemExit(9)\n")
    with pytest.raises(sy.SyntheticRefusedError, match="does not hold: json.py"):
        backend.run(spec(auth.root, PROBE))
    shadow.unlink()
    probe = auth.root / "probe.py"
    probe.write_bytes(probe.read_bytes() + b"# changed\n")
    with pytest.raises(sy.SyntheticRefusedError, match="changed since"):
        backend.run(spec(auth.root, PROBE))


def test_a_missing_file_is_refused(tmp_path):
    data = {"ladder.json": b"{}"}
    auth = fixture("ladder-build", tmp_path / "fixture", data)
    (auth.root / "ladder.json").unlink()
    argv = [sys.executable, "-I", "build.py", "own_environment", "-"]
    with pytest.raises(sy.SyntheticRefusedError, match="missing"):
        sb.SubprocessBackend([auth]).run(spec(auth.root, argv))


def test_a_link_in_the_fixture_is_refused(tmp_path):
    auth = fixture("sandbox-probe", tmp_path / "fixture")
    target = tmp_path / "elsewhere"
    target.mkdir()
    try:
        (auth.root / "out").symlink_to(target, target_is_directory=True)
    except OSError:
        pytest.skip("this system does not let the test create a symbolic link")
    with pytest.raises(sy.SyntheticRefusedError, match="a link"):
        sb.SubprocessBackend([auth]).run(spec(auth.root, PROBE))


# ---- the build ladder played by the cataloged fixture (A') ------------------------------------


def ladder_fixture(tmp_path, plan):
    data = {
        "ladder.json": json.dumps(plan).encode(),
        "Dockerfile": b"FROM scratch\n",
        "requirements.txt": b"numpy\n",
    }
    return fixture("ladder-build", tmp_path / "fixture", data)


def synthetic_build(auth, expected, threshold_usec=None):
    """The build of one rung: the cataloged build.py under the subprocess backend, its
    result classified from what the harness declared before the run (``expected``)."""
    backend = sb.SubprocessBackend([auth])

    def build(rung):
        log = auth.root.parent / "logs" / f"{rung.name}.log"
        argv = [sys.executable, "-I", "build.py", rung.name, rung.python or "-"]
        result = backend.run(spec(auth.root, argv, log_path=log, threshold_usec=threshold_usec))
        text = result.log_path.read_text(encoding="utf-8", errors="replace")
        return sy.classify_synthetic_build(
            result.exit_code, result.stopped, text, expected[rung.name]
        )

    return build


def rungs():
    return ld.ladder_rungs("Dockerfile", "requirements.txt", ["3.12", "3.13"])


def verdict(result):
    return aggregate_claim(
        [result.gate],
        [],
        [],
        metric_recompute_applies=False,
        failures={ld.GATE: result.failure} if result.failure else None,
    ).verdict


ALL = ("own_environment", "requirements_compiled", "requirements_compiled_next_python")


def test_the_controlled_not_reproducible_runs_end_to_end(tmp_path):
    """Every rung fails with the deliberate, declared procedure error: the controlled
    NOT_REPRODUCIBLE of WP4 W4.3, through the real backend and the WP2 core."""
    auth = ladder_fixture(tmp_path, dict.fromkeys(ALL, "procedure_error"))
    expected = dict.fromkeys(ALL, "procedure_error")
    result = ld.run_ladder(rungs(), synthetic_build(auth, expected))
    assert result.gate.status is TestStatus.FAIL
    assert result.failure == ld.GateFailure(FailureCause.BUILD_LADDER, 3, 3)
    assert verdict(result) is PaperVerdict.NOT_REPRODUCIBLE


def test_the_first_rung_that_builds_is_used(tmp_path):
    plan = {ALL[0]: "procedure_error", ALL[1]: "ok", ALL[2]: "ok"}
    auth = ladder_fixture(tmp_path, plan)
    result = ld.run_ladder(rungs(), synthetic_build(auth, dict(plan)))
    assert result.built_with == "requirements_compiled"
    assert (auth.root / "out" / "built-requirements_compiled.txt").exists()
    assert verdict(result) is not PaperVerdict.NOT_REPRODUCIBLE


@pytest.mark.parametrize(
    ("action", "why"),
    [
        ("crash", "an unexpected exception"),
        ("exit86", "the deliberate exit code without its line"),
        ("ok", "an unexpected success"),
    ],
)
def test_an_unexpected_outcome_is_never_an_error_of_the_procedure(tmp_path, action, why):
    """Only the declared deliberate failure counts (Codex review of the preview): any other
    outcome is undetermined, so the ladder stops and the gate is INCONCLUSIVE."""
    plan = {ALL[0]: "procedure_error", ALL[1]: action, ALL[2]: "procedure_error"}
    auth = ladder_fixture(tmp_path, plan)
    expected = dict.fromkeys(ALL, "procedure_error")
    result = ld.run_ladder(rungs(), synthetic_build(auth, expected))
    assert result.failure.cause is FailureCause.UNDETERMINED, why
    assert result.gate.metrics["attempts"][2]["reached"] is False
    assert verdict(result) is PaperVerdict.INCONCLUSIVE


def test_the_twin_on_refutes_side_keeps_its_own_cause(tmp_path):
    """The same failures, then a rung stopped by its threshold: budget_exhausted,
    INCONCLUSIVE, never NOT_REPRODUCIBLE (WP4 W4.3)."""
    plan = {ALL[0]: "procedure_error", ALL[1]: "busy", ALL[2]: "procedure_error"}
    auth = ladder_fixture(tmp_path, plan)
    expected = dict.fromkeys(ALL, "procedure_error")
    result = ld.run_ladder(rungs(), synthetic_build(auth, expected, threshold_usec=300_000))
    assert result.failure.cause is FailureCause.BUDGET_EXHAUSTED
    assert verdict(result) is PaperVerdict.INCONCLUSIVE


def test_the_classification_reads_only_the_declared_expectation():
    deliberate = sy.DELIBERATE_BUILD_LINE + "\n"
    ok = sy.classify_synthetic_build(0, None, "", "ok")
    assert ok.outcome is Outcome.COMPLETED
    failed = sy.classify_synthetic_build(86, None, deliberate, "procedure_error")
    assert (failed.outcome, failed.cause) == (Outcome.FAILED, FailureCause.BUILD_LADDER)
    for code, text, expected in ((86, deliberate, "ok"), (1, deliberate, "procedure_error")):
        other = sy.classify_synthetic_build(code, None, text, expected)
        assert other.cause is FailureCause.UNDETERMINED
    guard = sy.classify_synthetic_build(None, sb.STOP_NO_PROGRESS, "", "ok")
    assert guard.outcome is Outcome.OPERATIONAL_GUARD
    with pytest.raises(ValueError, match="expected"):
        sy.classify_synthetic_build(0, None, "", "anything")
