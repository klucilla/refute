"""Package 25, part A (map Amendment 25, approved by the maintainer on 2026-10-18): the identity
contract of the harness version 3. Written before the code. Each case runs
``tests/population_v3_probe.py`` in its own process (version 3 patches version 2 in place)."""

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PROBE = ROOT / "tests" / "population_v3_probe.py"
HARNESS = ROOT / "docs" / "validation" / "v0.2.1" / "population" / "population_v3.py"
CONFIGS = ROOT / "docs" / "validation" / "v0.2.1" / "population" / "m4-configurations"
CONFIG = CONFIGS / "m4-c1.json"


def _work():
    return ROOT / ".cache" / "test-population-v3" / uuid.uuid4().hex


def _env(config=CONFIG):
    env = dict(os.environ)
    env.pop("REFUTE_M4_CONFIGURATION", None)
    env.pop("REFUTE_M4_EXPECTED_IDENTITY", None)
    if config is not None:
        env["REFUTE_M4_CONFIGURATION"] = str(config)
    return env


def _probe(mode, work, config=CONFIG, extra_env=None):
    env = _env(config)
    env.update(extra_env or {})
    res = subprocess.run(
        [sys.executable, str(PROBE), mode, str(work)],
        capture_output=True,
        text=True,
        env=env,
        timeout=1200,
    )
    assert res.returncode == 0, res.stderr[-3000:]
    return json.loads(res.stdout.strip().splitlines()[-1])


# --- A2: the path (a fake checkout under the work folder) --------------------------------------


@pytest.fixture(scope="module")
def paths():
    return _probe("paths", _work())


def test_a2_a_relative_path_in_the_authorized_folder_is_accepted(paths):
    assert paths["cases"]["good"] is None
    assert paths["cases"]["env_absolute_good"] is None  # an environment value may be absolute


@pytest.mark.parametrize(
    "case", ["absolute", "backslash", "dotdot", "missing", "outside_folder", "nested"]
)
def test_a2_a_bad_declared_path_is_refused(paths, case):
    assert paths["cases"][case] is not None, case


@pytest.mark.parametrize("kind", ["dir", "file"])
def test_a2_a_path_through_a_link_is_refused(paths, kind):
    if paths["links"][kind] is not True:
        pytest.skip(f"this machine cannot create the {kind} link: {paths['links'][kind]}")
    case = "through_link" if kind == "dir" else "file_link"
    assert paths["cases"][case] is not None and "link" in paths["cases"][case]


# --- A1, A2, A3: the declaration's member --------------------------------------------------------


@pytest.fixture(scope="module")
def declarations():
    return _probe("declaration", _work())


def test_a1_the_right_member_adds_no_problem(declarations):
    assert declarations["state_ok"] is True
    assert declarations["m4_problems"]["good"] == []


@pytest.mark.parametrize(
    "variant",
    [
        "missing",
        "malformed",
        "wrong_sha256",
        "wrong_name",
        "wrong_format",
        "absolute_path",
        "dotdot_path",
        "missing_path",
        "outside_path",
    ],
)
def test_a2_each_bad_member_is_a_declaration_problem(declarations, variant):
    assert declarations["m4_problems"][variant], variant


def test_a2_identical_bytes_at_another_path_are_refused():
    # another file with the same bytes as m4-c1.json, inside the checkout but not in the folder
    work = _work()
    work.mkdir(parents=True)
    copy = work / "m4-c1.json"
    copy.write_bytes(CONFIG.read_bytes())
    out = _probe("import", work, config=copy)
    assert out["state_ok"] is False and "authorized folder" in out["problem"]


def test_a3_version_2_alone_tolerates_the_extra_member():
    out = _probe("declaration-v2", _work(), config=None)
    assert out["with"] == out["without"]


# --- A4: the workers and the main process ---------------------------------------------------------


@pytest.mark.parametrize(
    "other",
    [
        "probe-non-default.json",
        # added after the sabotage SK3 escaped (Amendment 25's record): the same block under
        # another name and file, so only the identity comparison can refuse it
        "probe-same-block.json",
    ],
)
def test_a4_a_worker_with_another_configuration_refuses_and_stops_the_dispatch(other):
    out = _probe("worker-mismatch", _work(), extra_env={"PROBE_OTHER": other})
    assert out["seen"] and "m4 identity" in out["seen"][0].get("infrastructure", "")
    assert out["record_written"] is False  # refused before the inherited analysis
    assert [e["kind"] for e in out["journal"]] == ["refusal"]


def test_a4_the_main_process_confirms_or_refuses_every_result():
    out = _probe("callback", _work())
    checked, journal = out["checked"], out["journal"]
    assert "infrastructure" not in checked["good"]
    assert "infrastructure" in checked["bare"] and "infrastructure" in checked["other"]
    assert [(e["kind"], e["case"]) for e in journal] == [
        ("confirmation", "a"),
        ("refusal", "b"),
        ("refusal", "c"),
    ]
    assert journal[0]["record_sha256"] == "1" * 64


def test_a4_a5_a_resume_accepts_only_confirmed_records():
    out = _probe("resume", _work())
    assert out["as_written"] == []
    assert out["no_confirmation"] and "confirmation" in out["no_confirmation"][0]
    assert out["refused"] and "refused" in out["refused"][0]
    assert out["record_changed"] and "confirmation" in out["record_changed"][0]
    assert out["other_block"]  # the expected identity names another block


# --- added after the Codex review of the package's implementation ---------------------------------


@pytest.fixture(scope="module")
def records():
    return _probe("records", _work())


def test_every_consumer_of_the_records_checks_the_identity(records):
    # version 2's slot_records serves compare-slots, the resume of orchestrate and metrics
    assert records["installed"] is True
    assert records["consumer_confirmed"] == []
    assert records["consumer_unconfirmed"], records


def test_an_incomplete_or_mismatched_confirmation_is_refused(records):
    assert records["no_pid"] and "no complete confirmation" in records["no_pid"][0]
    assert records["other_pid"] and "PID" in records["other_pid"][0]


def test_the_block_check_refuses_a_confirmed_record_of_another_block(records):
    problems = records["other_block_confirmed"]
    assert problems and "corrections block is not the expected one" in problems[0]


def test_a_confirmed_error_record_is_accepted_and_an_unconfirmed_one_is_not(records):
    assert records["error_confirmed"] == []
    assert records["error_unconfirmed"]


def test_a4_a_refused_result_stops_the_dispatch():
    out = _probe("stop", _work())
    assert out["stopped"] is not None or out["results"] < out["tasks"], out
    assert out["journal"] and all(e["kind"] == "refusal" for e in out["journal"])


def test_a5_the_expected_identity_comes_only_from_a_clean_opening():
    out = _probe("transport", _work())
    assert out == {
        "import_keeps": True,
        "inherited_cleared": True,
        "clean_published": True,
        "problem_unpublished": True,
    }


def test_a3_the_command_line_captures_the_configuration_once():
    assert _probe("cli-capture", _work())["reads"] == 1


def test_a4_a_worker_started_by_the_command_line_keeps_the_expected_identity():
    # added after the second Codex review of the package: the import of a spawned worker (this
    # file run as ``__mp_main__``) once cleared the inherited identity, so every worker refused
    out = _probe("cli-worker", _work())
    assert out["main_published"] is True
    worker = out["worker"]
    assert worker["module_name"] == "__mp_main__"  # the bootstrap copy is the module in use
    assert worker["executions"] == 1 and worker["installed"] is True  # one capture, one install
    assert out["env_kept"] is True
    assert worker["problem"] is None


# --- A5: the close; A6: status and the operational modes -----------------------------------------


def test_a5_a_changed_configuration_invalidates_the_close():
    out = _probe("close", _work())
    assert out["installed"] is True
    assert out["unchanged"] is True  # the first close, before the change: no lock
    assert out["changed"] is False
    assert out["calls"]["lock"] == ["the M4 configuration changed on disk during the execution"]
    assert out["calls"]["close"][-1].get("m4_configuration_changed") is True


# Version 2's command line refuses a checkout inside the user's home directory by design (its
# home_problems; the Linux runners check out under /home). One logical processor (0-0) exists on
# every runner, where 0-7 does not (CI of 158433c: SetProcessAffinityMask failed: 87).
_HOME = Path.home().resolve()
_INSIDE_HOME = ROOT == _HOME or _HOME in ROOT.parents
needs_runnable_host = pytest.mark.skipif(
    _INSIDE_HOME, reason="version 2's command line refuses a checkout inside the home directory"
)


def _harness(args, config):
    return subprocess.run(
        [sys.executable, str(HARNESS), *args, "--cpus", "0-0"],
        capture_output=True,
        text=True,
        env=_env(config),
        timeout=600,
    )


@pytest.fixture(scope="module")
def campaign_root():
    """A diagnostic root with one declaration whose member names m4-c1.json correctly."""
    work = _work()
    out = _probe("declaration", work)  # writes the variants under work/campaigns
    assert out["m4_problems"]["good"] == []
    return work / "campaigns"


@needs_runnable_host
def test_a6_status_shows_a_loading_problem_and_exits_as_version_2(campaign_root):
    res = _harness(["status", "--root", str(campaign_root), "--campaign", "probe-good"], None)
    assert res.returncode == 0, res.stderr[-2000:]
    report = json.loads(res.stdout[res.stdout.index("{") :])
    assert any("M4 configuration not loaded" in p for p in report["declaration_problems"])


@needs_runnable_host
def test_a6_status_shows_a_member_problem(campaign_root):
    res = _harness(
        ["status", "--root", str(campaign_root), "--campaign", "probe-wrong-sha256"], CONFIG
    )
    assert res.returncode == 0, res.stderr[-2000:]
    report = json.loads(res.stdout[res.stdout.index("{") :])
    assert any("m4_configuration" in p for p in report["declaration_problems"])


@needs_runnable_host
def test_a6_an_operational_mode_refuses_with_a_loading_problem(campaign_root):
    work = _work()
    args = [
        "analyze",
        "--root",
        str(campaign_root),
        "--campaign",
        "probe-good",
        "--manifest",
        str(work / "m.json"),
        "--cache",
        str(work / "cache"),
        "--out",
        str(work / "run"),
        "--point",
        "M4",
        "--lot",
        "0",
        "--slot",
        "1",
    ]
    res = _harness(args, None)
    assert res.returncode != 0
    assert "M4 configuration not loaded" in (res.stdout + res.stderr)
