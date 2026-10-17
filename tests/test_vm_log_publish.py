"""The publishable copy of the endpoint's operation log (#59, item 5), offline.

The records are synthetic, in the shape ``RefuteVm.psm1`` writes; the host and account
names are invented.
"""

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location(
    "publish_operation_log", ROOT / "scripts" / "vm" / "publish_operation_log.py"
)
pub = importlib.util.module_from_spec(spec)
sys.modules["publish_operation_log"] = pub
spec.loader.exec_module(pub)

HOST = "LABHOST7"
USER = "opsuser"
PLAN_SHA = "3976d96a09c23d1a6ca1cd858a16087810c4ecb814af3384a219b6041cffd304"
OP_ID = "6f1c2d3e-4b5a-4c6d-8e7f-0a1b2c3d4e5f"


def caller(va):
    return {
        "ConnectedUser": f"{HOST}\\{USER}",
        "RunAsUser": f"WinRM Virtual Users\\WinRM VA_{va}_{HOST}_{USER}",
    }


def plan(refusal=None, adapter_switch=""):
    return {
        "Operation": "SetMemory",
        "Argument": None,
        "ConfigSha256": "fa27a08622297aa2615cf48d09d584fed6b4ab25b1862ce2f5d0d91c728208ff",
        "Target": {"VmName": "refute-vm", "VmId": "f77c8269-f6d7-4955-a37b-42a503ffe2f1"},
        "Preconditions": {
            "Host": {
                "VirtualMachinePath": "C:\\Hyper-V",
                "VirtualHardDiskPath": "C:\\Hyper-V\\Virtual Hard Disks",
                "EnableEnhancedSessionMode": False,
            },
            "Files": {"BaseDisk": {"Exists": True, "Format": "VHDX", "SizeBytes": 107374182400}},
            "RecordedVmId": "f77c8269-f6d7-4955-a37b-42a503ffe2f1",
            "TargetVm": {
                "Name": "refute-vm",
                "NetworkAdapters": [{"Name": "Network Adapter", "SwitchName": adapter_switch}],
                "HardDisks": [],
            },
        },
        "Changes": [{"Item": "Vm.MemoryStartup", "Before": 51539607552, "After": 25769803776}],
        "AlreadyDone": False,
        "Refusal": refusal,
    }


def records():
    return [
        {
            "Utc": "2026-10-17T13:20:34.188Z",
            "OperationId": OP_ID,
            "Operation": "SetMemory",
            "Mode": "simulated",
            "PlanSha256": PLAN_SHA,
            "Plan": plan(),
            "Caller": caller(31),
            "Module": {"RefuteVm.Core.ps1": "5b717a33" + "0" * 56},
        },
        {
            "Utc": "2026-10-17T13:21:00.000Z",
            "OperationId": OP_ID,
            "Operation": "SetMemory",
            "Mode": "refused",
            "PlanSha256": PLAN_SHA,
            "Plan": plan(
                refusal=f"network adapter 'Network Adapter' is connected to '{HOST} switch'",
                adapter_switch=f"{HOST} switch",
            ),
            "Caller": caller(32),
            "Reason": f"network adapter 'Network Adapter' is connected to '{HOST} switch'",
        },
        {
            "Utc": "2026-10-17T13:22:00.000Z",
            "OperationId": OP_ID,
            "Operation": "SetMemory",
            "Mode": "result",
            "PlanSha256": PLAN_SHA,
            "Outcome": "failed",
            "Error": "UnauthorizedAccessException (HRESULT 0x80070005)",
            "Caller": {"ConnectedUser": "", "RunAsUser": f"{HOST}\\{USER}"},
        },
    ]


def jsonl(recs):
    return pub.dump(recs)


def write_source(tmp_path, recs):
    source = tmp_path / "operations.jsonl"
    source.write_bytes(jsonl(recs))
    return source


# ---- the copy -----------------------------------------------------------------------------


def test_the_copy_replaces_accounts_and_host_names_and_keeps_everything_else(tmp_path):
    source = write_source(tmp_path, records())
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    output = tmp_path / "published.jsonl"
    result = pub.publish(source, output, set())
    # the local log stays whole
    assert hashlib.sha256(source.read_bytes()).hexdigest() == before == result["source_sha256"]
    published = pub.read_records(output.read_bytes())
    assert result["records"] == 3 and len(published) == 3
    assert result["copy_sha256"] == hashlib.sha256(output.read_bytes()).hexdigest()
    first, refused, failed = published
    assert first["Caller"] == {
        "ConnectedUser": "<operator-account>",
        "RunAsUser": "<virtual-account> VA 31",
    }
    assert refused["Caller"]["RunAsUser"] == "<virtual-account> VA 32"
    # a call outside a remote session
    assert failed["Caller"] == {"ConnectedUser": "", "RunAsUser": "<account>"}
    assert refused["Reason"] == (
        "network adapter 'Network Adapter' is connected to '<host-identifier> switch'"
    )
    assert refused["Plan"]["Preconditions"]["TargetVm"]["NetworkAdapters"][0]["SwitchName"] == (
        "<host-identifier> switch"
    )
    # everything else as in the source, the plan hash included
    source_records = records()
    for key in ("Utc", "OperationId", "Operation", "Mode", "PlanSha256", "Module"):
        assert first.get(key) == source_records[0].get(key)
    assert first["Plan"] == source_records[0]["Plan"]
    assert failed["Error"] == source_records[2]["Error"]
    text = output.read_text(encoding="utf-8").casefold()
    assert HOST.casefold() not in text and USER.casefold() not in text


def test_the_names_are_learned_from_the_whole_log_not_only_the_window(tmp_path):
    recs = records()
    recs[1]["Caller"] = {"ConnectedUser": "", "RunAsUser": ""}
    recs[1]["Reason"] = "the switch 'otherhost-sw' is refused"
    recs.append(
        {
            "Utc": "2026-10-18T00:00:00.000Z",
            "OperationId": OP_ID,
            "Operation": "Status",
            "Mode": "simulated",
            "Caller": {"ConnectedUser": "OTHERHOST\\someone", "RunAsUser": ""},
        }
    )
    source = write_source(tmp_path, recs)
    output = tmp_path / "published.jsonl"
    pub.publish(source, output, set(), "2026-10-17T13:21:00.000Z", "2026-10-17T13:21:00.000Z")
    (only,) = pub.read_records(output.read_bytes())
    assert only["Reason"] == "the switch '<host-identifier>-sw' is refused"


def test_a_name_inside_a_hash_guid_or_time_is_left_alone():
    recs = records()
    recs[0]["Caller"] = {"ConnectedUser": "dead\\beef", "RunAsUser": ""}
    recs[0]["PlanSha256"] = "dead" + "0" * 56 + "beef"
    out = pub.anonymize(recs[:1], {"dead", "beef"})
    assert out[0]["PlanSha256"] == recs[0]["PlanSha256"]
    assert pub.check(recs[:1], out, {"dead", "beef"}) == []


# ---- the checker --------------------------------------------------------------------------


def _good():
    recs = records()
    return recs, pub.anonymize(recs, pub.caller_identifiers(recs))


def _names():
    return pub.caller_identifiers(records())


def test_the_copy_of_the_tool_passes_the_checker():
    recs, out = _good()
    assert pub.check(recs, out, _names()) == []


@pytest.mark.parametrize(
    "change, reason",
    [
        (lambda c: c.pop(), "the copy has 2 records"),
        (lambda c: c[0].update(PlanSha256="0" * 64), ".PlanSha256: differs from the source"),
        (lambda c: c[0]["Plan"]["Changes"][0].update(After=1), "differs from the source"),
        (lambda c: c[0]["Plan"].update(AlreadyDone=True), "differs from the source"),
        (lambda c: c[0].update(Extra="x"), "not the same object as the source"),
        (lambda c: c[2].update(Error="another text"), ".Error: differs from the source"),
        (
            lambda c: c[0]["Caller"].update(ConnectedUser="someone"),
            "ConnectedUser: not a placeholder",
        ),
        (
            lambda c: c[0]["Caller"].update(RunAsUser="<virtual-account>"),
            "RunAsUser: not a placeholder",
        ),
        (lambda c: c[1].update(Reason=f"connected to '{HOST} switch'"), "holds a host identifier"),
        (
            lambda c: c[1].update(Reason=f"<host-identifier> {USER.upper()}"),
            "holds a host identifier",
        ),
        (lambda c: c[2].update(Error="at 192.168.1.20 <host-identifier>"), "holds an IPv4 address"),
        (lambda c: c[2].update(Error="fe80::1 <host-identifier>"), "holds an IPv6 address"),
        (
            lambda c: c[2].update(Error="2001:db8:0:0:1:0:0:1 <host-identifier>"),
            "holds an IPv6 address",
        ),
        (lambda c: c[2].update(Error="00-15-5D-01-02-03 <host-identifier>"), "holds a MAC address"),
        (
            lambda c: c[2].update(Error="C:\\Users\\<host-identifier>\\x"),
            "holds a user profile path",
        ),
        (lambda c: c[2].update(Error="\\\\server\\share <host-identifier>"), "holds a UNC path"),
        (
            lambda c: c[2].update(Error="ops@example.org <host-identifier>"),
            "holds an e-mail address",
        ),
        (
            lambda c: c[2].update(
                Error="S-1-5-21-1004336348-1177238915-682003330 <host-identifier>"
            ),
            "holds an account SID",
        ),
        # Codex review of #154: a SID of another authority, a local host name, a path
        # outside the allowed roots, a module map that is not one
        (
            lambda c: c[2].update(Error="S-1-12-1-100-200-300-400 <host-identifier>"),
            "holds an account SID",
        ),
        (
            lambda c: c[2].update(Error="remotehost.internal <host-identifier>"),
            "holds a local host name",
        ),
        (
            lambda c: c[2].update(Error="C:\\Temp\\<host-identifier>.log"),
            "holds a path outside the allowed roots",
        ),
        (
            lambda c: c[0]["Module"].update({"../other.ps1": "0" * 64}),
            ".Module: not file names of the module",
        ),
    ],
)
def test_the_checker_refuses_a_copy_that_differs_or_leaks(change, reason):
    recs, out = _good()
    bad = copy.deepcopy(out)
    change(bad)
    problems = pub.check(recs, bad, _names())
    assert any(reason in p for p in problems), problems


def test_a_text_changed_beyond_the_replaced_names_is_refused():
    """Codex review of #154: a copy that rewrites a text and leaves a placeholder in it is
    not a copy; each placeholder must stand where the source held a known name."""
    recs, out = _good()
    out[2]["Error"] = "everything succeeded <host-identifier>"
    problems = pub.check(recs, out, _names())
    assert any(".Error: differs from the source beyond the replaced names" in p for p in problems)
    # a placeholder where the source held another text than a known name
    recs, out = _good()
    out[1]["Reason"] = out[1]["Reason"].replace("Network Adapter", "<host-identifier>")
    assert any("beyond the replaced names" in p for p in pub.check(recs, out, _names()))


def test_a_known_name_shaped_as_a_hash_in_free_text_is_refused_not_kept():
    """Codex review of #154: a host name made of hex digits, in a free text or a key, is not
    a hash; the copy leaves a text of hash shape alone, and the checker refuses it."""
    name = "deadbeef" * 4
    recs = records()
    recs[2]["Error"] = name
    recs[2]["Extra"] = {name: 1}
    names = _names() | {name}
    problems = pub.check(recs, pub.anonymize(recs, names), names)
    assert any(".Error: holds a host identifier" in p for p in problems), problems
    assert any(f".Extra.{name} (key): holds a host identifier" in p for p in problems), problems


def test_the_host_part_of_a_virtual_account_is_learned():
    """Codex review of #154: with a domain account, the virtual account's name holds the
    connecting host, not the domain; it is learned alone, and replaced."""
    recs = records()
    recs[0]["Caller"] = {
        "ConnectedUser": "CORP\\opsuser",
        "RunAsUser": "WinRM Virtual Users\\WinRM VA_31_machinehost_opsuser",
    }
    recs[1]["Reason"] = "the switch 'machinehost-sw' is refused"
    names = pub.caller_identifiers(recs)
    assert {"CORP", "opsuser", "machinehost_opsuser", "machinehost"} <= names
    out = pub.anonymize(recs, names)
    assert out[1]["Reason"] == "the switch '<host-identifier>-sw' is refused"
    assert pub.check(recs, out, names) == []


def test_a_name_inside_a_placeholder_is_not_a_leak():
    """Codex review of #154: an identifier such as "host" is inside "<host-identifier>"; the
    placeholders are masked before the scan, and the copy replaces in one pass, so a
    placeholder is never replaced again."""
    recs = records()
    names = _names() | {"host"}
    out = pub.anonymize(recs, names)
    assert pub.check(recs, out, names) == []
    assert "<<host-identifier>" not in json.dumps(out)
    # the key "Host" of the preconditions was replaced, and accepted as a replacement
    assert "<host-identifier>" in out[0]["Plan"]["Preconditions"]


def test_times_hashes_and_paths_of_the_configuration_are_not_leaks():
    recs, out = _good()
    assert not any("address" in p for p in pub.check(recs, out, _names()))
    assert out[0]["Plan"]["Preconditions"]["Host"]["VirtualHardDiskPath"] == (
        "C:\\Hyper-V\\Virtual Hard Disks"
    )


def test_a_leak_in_the_source_refuses_the_publication(tmp_path):
    recs = records()
    recs[2]["Error"] = "connect to 10.0.0.5 failed"
    source = write_source(tmp_path, recs)
    output = tmp_path / "published.jsonl"
    with pytest.raises(pub.LogError, match="holds an IPv4 address"):
        pub.publish(source, output, set())
    assert not output.exists()


# ---- the command --------------------------------------------------------------------------


def test_the_copy_never_overwrites_and_is_never_the_source(tmp_path):
    source = write_source(tmp_path, records())
    before = source.read_bytes()
    existing = tmp_path / "published.jsonl"
    existing.write_bytes(b"kept")
    with pytest.raises(pub.LogError, match="never overwrites"):
        pub.publish(source, existing, set())
    assert existing.read_bytes() == b"kept"
    with pytest.raises(pub.LogError, match="never overwrites"):
        pub.publish(source, source, set())
    assert source.read_bytes() == before


def test_a_short_identifier_is_refused_not_skipped(tmp_path):
    source = write_source(tmp_path, records())
    with pytest.raises(pub.LogError, match="shorter than 3"):
        pub.publish(source, tmp_path / "published.jsonl", {"ab"})


@pytest.mark.parametrize(
    "data, reason",
    [
        (b"\xff\xfe", "not UTF-8"),
        (b"{not json}\n", "line 1 is not JSON"),
        (b"[1]\n", "not a JSON object"),
        (b'{"Utc": "2026-10-17 13:20"}\n', "no Utc time"),
    ],
)
def test_a_source_that_is_not_an_operation_log_is_refused(data, reason):
    with pytest.raises(pub.LogError, match=reason):
        pub.read_records(data)


def test_a_window_bound_of_another_format_is_refused():
    with pytest.raises(pub.LogError, match="not a time"):
        pub.select(records(), "2026-10-17")


def test_main_reports_the_hashes_and_refuses_with_exit_1(tmp_path, capsys, monkeypatch):
    for name in ("COMPUTERNAME", "USERNAME", "USERDOMAIN", "HOSTNAME", "USER"):
        monkeypatch.delenv(name, raising=False)
    source = write_source(tmp_path, records())
    output = tmp_path / "published.jsonl"
    assert pub.main(["--source", str(source), "--output", str(output)]) == 0
    printed = capsys.readouterr().out
    assert f"source SHA-256 {hashlib.sha256(source.read_bytes()).hexdigest()}" in printed
    assert "records 3" in printed
    assert pub.main(["--source", str(source), "--output", str(output)]) == 1
    assert "refused:" in capsys.readouterr().err


def test_the_environment_names_are_identifiers():
    env = {"COMPUTERNAME": HOST, "USERNAME": USER, "USERDOMAIN": "", "PATH": "x"}
    assert pub.environment_identifiers(env) == {HOST, USER}


def test_the_dump_is_one_json_object_per_line():
    data = pub.dump(records())
    assert data.endswith(b"\n") and data.count(b"\n") == 3
    assert [json.loads(line) for line in data.decode("utf-8").splitlines()] == records()
