"""The provenance of a paper's dossier (docs/validation/v0.3/wp3-dossier-provenance-acceptance.md):
the reads recorded and kept at the read, the host's profile records, the logs manifest with
lossless compression, the sources, the built environment, the Refute checkout, the unit,
and the order of finalization ending with MANIFEST.sha256. Offline, synthetic files only."""

from __future__ import annotations

import gzip
import hashlib
import json
import subprocess
from types import SimpleNamespace

import pytest

from refute.core.dossier import verify_manifest
from refute.packs.ml import extract as ex
from refute.packs.ml import production as pd
from refute.packs.ml import readers as rd
from refute.packs.ml.docker_backend import Limits
from refute.packs.ml.sandbox import TimingMaxima

LIMITS = Limits(cpus=22, period_us=100_000, memory_bytes=12 << 30, pids=4096)
TIMING = TimingMaxima(0.000346, 0.207)
EXECUTION = "0123456789abcdef0123456789abcdef"
CLAIM_SHA = "c" * 64


def h(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ---- the reads, recorded and kept at the read ------------------------------------------------


def test_a_read_is_recorded_once_and_kept_in_the_store(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "metrics.json").write_bytes(b'{"acc": 0.5}')
    store = tmp_path / "store"
    with ex.record_reads(store) as recorded:
        for _ in range(2):  # two read sessions: one entry
            with ex.read_session():
                ex.read_output_bytes(run, "metrics.json", None)
    assert recorded["reads"] == [
        {"workdir": str(run.resolve()), "path": "metrics.json", "sha256": h(b'{"acc": 0.5}'),
         "size": 12, "stored": True}
    ]  # fmt: skip
    assert (store / h(b'{"acc": 0.5}')).read_bytes() == b'{"acc": 0.5}'


def test_bytes_read_stay_recorded_when_the_parsing_fails(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "metrics.json").write_bytes(b"not json")
    extraction = {"from": "file", "file": "metrics.json", "json_path": "$.acc"}
    with ex.record_reads(tmp_path / "store") as recorded:
        with pytest.raises(ex.ExtractionError):
            ex.extract(extraction, run, "", None)
    assert [r["sha256"] for r in recorded["reads"]] == [h(b"not json")]


def test_a_failed_read_is_not_recorded(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    with ex.record_reads(tmp_path / "store") as recorded:
        with pytest.raises(ex.ExtractionError):
            ex.read_output_bytes(run, "absent.json", None)
    assert recorded["reads"] == []


def test_two_versions_of_one_path_are_both_recorded_and_kept(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    store = tmp_path / "store"
    with ex.record_reads(store) as recorded:
        (run / "m.json").write_bytes(b"1")
        ex.read_output_bytes(run, "m.json", None)
        (run / "m.json").write_bytes(b"2")
        ex.read_output_bytes(run, "m.json", None)
    assert [r["sha256"] for r in recorded["reads"]] == [h(b"1"), h(b"2")]
    assert (store / h(b"1")).exists() and (store / h(b"2")).exists()


def test_a_log_read_and_a_container_readers_answer_are_recorded(tmp_path):
    log = tmp_path / "a.log"
    log.write_bytes(b"line\n")
    reader = tmp_path / "reader"
    (reader / "out").mkdir(parents=True)
    (reader / "out" / "counts.json").write_bytes(b'{"test": 3}')
    with ex.record_reads(tmp_path / "store") as recorded:
        assert ex.read_log(log) == "line\n"
        assert rd.read_answer(reader / rd.ANSWER, {"test"}, reader) == {"test": 3}
    assert recorded["logs"] == [{"path": str(log.resolve()), "sha256": h(b"line\n"), "size": 5}]
    assert recorded["reads"][0]["path"] == "out/counts.json"


def test_no_recorder_records_nothing_and_two_cannot_open(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    (run / "m.json").write_bytes(b"1")
    ex.read_output_bytes(run, "m.json", None)  # no recorder: nothing to record, no error
    with ex.record_reads() as recorded:
        with pytest.raises(RuntimeError, match="already open"):
            with ex.record_reads():
                pass
        ex.read_output_bytes(run, "m.json", None)
    assert recorded["reads"][0]["stored"] is False


# ---- the host's profile records ----------------------------------------------------------------


def profile(**changes) -> dict:
    record = {
        "format": pd.PROFILE_FORMAT,
        "execution_id": EXECUTION,
        "paper": "p1",
        "claim_sha256": CLAIM_SHA,
        "phase": "run",
        "profile": "pull",
        "read_utc": "2026-10-18T12:00:00Z",
        "checks": {"adapter_on_configured_switch": True, "entries_of_the_profile": True},
        "script_sha256": "a" * 64,
    }
    record.update(changes)
    return record


def read(record, phase="run", consumed="2026-10-18T12:01:00Z", not_before=None):
    data = record if isinstance(record, bytes) else json.dumps(record).encode()
    return pd.read_profile(
        data, execution_id=EXECUTION, paper="p1", claim_sha256=CLAIM_SHA, phase=phase,
        consumed_utc=consumed, not_before=not_before,
    )  # fmt: skip


def test_a_profile_record_of_this_execution_is_accepted_and_kept_as_read():
    got = read(profile(), not_before="2026-10-18T11:59:00Z")
    assert got["record"]["profile"] == "pull" and got["sha256"] == h(json.dumps(profile()).encode())
    assert "bytes" not in got  # the caller keeps the bytes as a file of the dossier
    assert read(profile(phase="build", profile="build"), phase="build")["record"]["phase"]


@pytest.mark.parametrize(
    ("record", "match"),
    [
        (profile(profile="build"), "the profile of run"),
        (profile(execution_id="f" * 32), "this execution"),
        (profile(paper="p2"), "this paper"),
        (profile(claim_sha256="d" * 64), "this claim"),
        (profile(phase="build"), "the phase"),
        (
            profile(checks={"adapter_on_configured_switch": False, "entries_of_the_profile": True}),
            "each true",
        ),  # fmt: skip
        (profile(checks={}), "each true"),
        (profile(checks={"x": 1}), "each true"),
        (profile(checks={"anything": True}), "each true"),
        (
            profile(
                checks={
                    "adapter_on_configured_switch": True,
                    "entries_of_the_profile": True,
                    "more": True,
                }
            ),
            "each true",
        ),  # fmt: skip
        (b'{"profile": "build", "profile": "pull"}', "twice"),
        (json.dumps(profile(paper="p\u00e9")).encode("utf-8"), "not ASCII"),
        (json.dumps(profile(checks={"adapter\u0301": True})).encode(), "not ASCII"),
        (profile(script_sha256="x"), "script_sha256"),
        (profile(format="other"), "format"),
        (profile(extra=1), "exactly the fields"),
        ({k: v for k, v in profile().items() if k != "checks"}, "exactly the fields"),
        (profile(read_utc="2026-10-18 12:00:00"), "read_utc"),
        (profile(read_utc="2026-10-18T12:06:01Z"), "after its consumption"),
        (b"", "not JSON"),
        (b"{", "not JSON"),
        (b" " * 5000, "larger than"),
    ],
)
def test_a_profile_record_that_does_not_bind_is_refused(record, match):
    with pytest.raises(pd.ProductionError, match=match):
        read(record)


def test_a_run_record_read_before_the_setup_ended_is_refused():
    read(profile(read_utc="2026-10-18T11:55:00Z"), not_before="2026-10-18T12:00:00Z")  # skew
    with pytest.raises(pd.ProductionError, match="read before"):
        read(profile(read_utc="2026-10-18T11:54:59Z"), not_before="2026-10-18T12:00:00Z")


def test_the_run_phase_flag_is_checked_when_it_appears(tmp_path):
    flag = tmp_path / "run-phase-approved"
    seen = []
    flag.write_bytes(b"{}")
    pd.wait_for_run_phase(flag, timeout_s=10, check=lambda data, ended: seen.append(data))()
    assert seen == [b"{}"]

    def refuse(data, ended):
        raise pd.ProductionError("refused")

    with pytest.raises(pd.ProductionError, match="refused"):
        pd.wait_for_run_phase(flag, timeout_s=10, check=refuse)()


def test_the_profile_records_need_the_execution_id(tmp_path):
    claim = tmp_path / "claim.json"
    claim.write_text("{}")
    with pytest.raises(pd.ProductionError, match="execution-id"):
        pd.main(["--claim", str(claim), "--paper", "p1", "--root", str(tmp_path / "r"),
                 "--out", str(tmp_path / "o"), "--cache", str(tmp_path / "c"),
                 "--run-phase-flag", str(tmp_path / "flag")])  # fmt: skip
    with pytest.raises(pd.ProductionError, match="32 lowercase hex"):
        pd.main(["--claim", str(claim), "--paper", "p1", "--root", str(tmp_path / "r"),
                 "--out", str(tmp_path / "o"), "--cache", str(tmp_path / "c"),
                 "--execution-id", "XYZ"])  # fmt: skip


# ---- the logs, losslessly compressed above the limit ------------------------------------------


def test_logs_at_the_limit_are_stored_as_written_and_above_it_compressed(tmp_path, monkeypatch):
    monkeypatch.setattr(pd, "LOG_STORE_LIMIT", 10)
    logs = tmp_path / "logs"
    (logs / "k1").mkdir(parents=True)
    (logs / "k1" / "at.log").write_bytes(b"x" * 10)
    (logs / "k1" / "above.log").write_bytes(b"y" * 11)
    manifest = pd.copy_logs(logs, tmp_path / "out" / "logs")
    by_path = {e["path"]: e for e in manifest}
    assert "stored" not in by_path["logs/k1/at.log"]
    assert (tmp_path / "out" / "logs" / "k1" / "at.log").read_bytes() == b"x" * 10
    above = by_path["logs/k1/above.log"]
    assert above["sha256"] == h(b"y" * 11) and above["size"] == 11
    stored = tmp_path / "out" / above["stored"]["path"]
    assert not (tmp_path / "out" / "logs" / "k1" / "above.log").exists()
    assert gzip.decompress(stored.read_bytes()) == b"y" * 11
    assert above["stored"]["sha256"] == h(stored.read_bytes())


# ---- the sources and the built environment -----------------------------------------------------


def test_the_sources_are_copied_from_the_store_and_checked(tmp_path):
    store = tmp_path / "store"
    store.mkdir()
    (store / h(b"1")).write_bytes(b"1")
    folder = tmp_path / "ws" / "k1"
    reads = [
        {"workdir": str(folder), "path": "m.json", "sha256": h(b"1"), "size": 1, "stored": True},
        {"workdir": str(folder), "path": "m.json", "sha256": h(b"2"), "size": 1, "stored": False},
    ]
    folder.mkdir(parents=True)
    reads[0]["workdir"] = reads[1]["workdir"] = str(folder.resolve())
    out = pd.copy_sources(reads, {"k1/base/s0": folder}, store, tmp_path / "out" / "sources")
    assert out[0]["source"] == f"sources/{h(b'1')}" and out[0]["divergent"] is True
    assert out[0]["container"] == "k1/base/s0"
    assert out[1]["source"] is None and out[1]["reason"] == "not kept at the read"
    (store / h(b"1")).write_bytes(b"changed")
    with pytest.raises(pd.ProductionError, match="differ from the read"):
        pd.copy_sources(reads[:1], {}, store, tmp_path / "other")


def _setup(tmp_path):
    return pd.PaperSetup("p1", tmp_path / "run", tmp_path / "repo", {}, {}, LIMITS, TIMING)


def _outcome(rung):
    return SimpleNamespace(ladder=SimpleNamespace(built_with=rung))


def test_the_environment_of_each_rung(tmp_path):
    setup = _setup(tmp_path)
    built = setup.root / "ws" / "setup_build_requirements_compiled" / ".refute"
    built.mkdir(parents=True)
    (built / "requirements.lock").write_bytes(b"lock")
    (built / "pyvenv.cfg").write_bytes(b"cfg")
    dest = tmp_path / "d1"
    dest.mkdir()
    env = pd.built_environment(setup, _outcome("requirements_compiled"), dest, "sha256:1")
    assert env["requirements.lock"] == h(b"lock") and env["pyvenv.cfg"] == h(b"cfg")
    assert (dest / "pyvenv.cfg").read_bytes() == b"cfg" and env["image_id"] == "sha256:1"
    own = pd.built_environment(setup, _outcome("own_environment"), dest, "sha256:2")
    assert own["requirements.lock"] is None and "own_environment" in own["pyvenv.cfg reason"]
    assert env["complete"] is True and own["complete"] is True
    (built / "pyvenv.cfg").unlink()
    dest2 = tmp_path / "d2"
    dest2.mkdir()
    partial = pd.built_environment(setup, _outcome("requirements_compiled"), dest2, None)
    assert partial["complete"] is False and partial["incomplete"]
    none = pd.built_environment(setup, _outcome(None), dest, "sha256:3")
    assert none["rung"] is None and none["image_id"] is None and none["reason"]


# ---- the checkout and the unit -----------------------------------------------------------------


def test_the_refute_checkout_of_this_repository():
    record, _ = pd.refute_checkout()
    assert len(record["commit"]) == 40


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def test_a_changed_checkout_is_recorded_with_its_diff(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    (repo / "a.py").write_text("a = 1\n")
    _git(repo, "add", "a.py")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "a")
    clean, diff = pd.refute_checkout(repo)
    assert clean["tracked_files_unchanged"] is True and diff is None
    (repo / "a.py").write_text("a = 2\n")
    changed, diff = pd.refute_checkout(repo)
    assert changed["changed"] == ["a.py"] and changed["diff_sha256"] == h(diff)
    assert b"a = 2" in diff
    missing, _ = pd.refute_checkout(tmp_path / "nothing")
    assert missing["commit"] is None and missing["reason"]


def test_the_systemd_unit_from_the_cgroup():
    cgroup = "0::/system.slice/refute-p1.service\n"
    assert pd.systemd_unit(cgroup, {"INVOCATION_ID": "abc"}) == {
        "name": "refute-p1.service",
        "invocation_id": "abc",
    }
    assert pd.systemd_unit("0::/user.slice/session-1.scope\n", {}) is None


# ---- the dossier, in the order of finalization -------------------------------------------------


def test_the_dossier_carries_the_provenance_and_an_intact_manifest(tmp_path):
    setup = _setup(tmp_path)
    (setup.root / "logs").mkdir(parents=True)
    log = setup.root / "logs" / "k1.log"
    log.write_bytes(b"value 1\n")
    folder = setup.root / "ws" / "k1"
    folder.mkdir(parents=True)
    (folder / "m.json").write_bytes(b"1")
    store = setup.root / pd.READ_STORE
    with ex.record_reads(store) as recorded:
        ex.read_log(log)
        ex.read_output_bytes(folder, "m.json", None)
    provenance = {
        "times": {"engine_started_utc": "t0"}, "refute_diff": b"diff", "image_id": None,
        "claim_input": b'{"test_plan": {}}\n', "profile_bytes": {"run": b"{}"},
    }  # fmt: skip
    out = pd.write_dossier(
        tmp_path / "dossier", setup, {"test_plan": {}}, _outcome(None), {"base": "x"},
        provenance, recorded, {"k1/base/s0": folder},
    )  # fmt: skip
    record = json.loads((out / "dossier.json").read_text())
    prov = record["provenance"]
    assert record["format"] == "refute-ml-dossier-2"
    assert prov["logs"] == [{"path": "logs/k1.log", "sha256": h(b"value 1\n"), "size": 8}]
    assert prov["logs_read"] == [
        {"log": "logs/k1.log", "container": None, "sha256": h(b"value 1\n"), "size": 8,
         "bound": True}
    ]  # fmt: skip
    assert (out / "claim_input.json").read_bytes() == b'{"test_plan": {}}\n'
    assert prov["claim_input"]["sha256"] == h(b'{"test_plan": {}}\n')
    assert (out / "profiles" / "run.json").read_bytes() == b"{}"
    assert prov["profiles"]["run file"]["sha256"] == h(b"{}")
    assert prov["reads"][0]["source"] == f"sources/{h(b'1')}"
    assert prov["reads"][0]["container"] == "k1/base/s0"
    assert (out / "sources" / h(b"1")).read_bytes() == b"1"
    assert (out / "refute.diff").read_bytes() == b"diff" and "refute_diff" not in prov
    assert prov["environment"]["rung"] is None and prov["times"]["dossier_written_utc"]
    assert verify_manifest(out) == []
    (out / "logs" / "k1.log").write_bytes(b"altered\n")
    assert verify_manifest(out) != []
    with pytest.raises(FileExistsError):
        pd.write_dossier(tmp_path / "dossier", setup, {}, _outcome(None), {})


def test_a_log_read_gives_the_text_read_text_gave(tmp_path):
    log = tmp_path / "a.log"
    log.write_bytes(b"value=1\r\nother\rlast\n\xff")
    text = ex.read_log(log)
    assert text == log.read_text(encoding="utf-8", errors="replace")
    regex = {"pattern": "(?m)^value=(\\d+)$", "group": 1}
    assert ex.extract({"from": "log", "regex": regex}, tmp_path, text, None).token == "1"


def test_a_log_read_that_differs_from_its_copy_is_unbound(tmp_path):
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "k1_base_s0.log").write_bytes(b"copied")
    manifest = [{"path": "logs/k1_base_s0.log", "sha256": h(b"copied"), "size": 6}]
    reads = [
        {"path": str((logs / "k1_base_s0.log").resolve()), "sha256": h(b"read"), "size": 4},
        {"path": str((logs / "other.log").resolve()), "sha256": h(b"x"), "size": 1},
    ]
    out = pd.bind_logs_read(reads, manifest, logs, {"k1/base/s0": tmp_path})
    assert out[0]["container"] == "k1/base/s0" and out[0]["bound"] is False
    assert out[1]["log"] is None and out[1]["bound"] is False and out[1]["reason"]
