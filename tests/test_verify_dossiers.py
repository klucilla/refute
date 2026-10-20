"""The dossier verification of the main sample of v0.3
(docs/validation/v0.3/dossier-verification-acceptance.md, section 4). The five published
dossiers are in the repository, so no case needs the network; every must-fail case changes a
copy in a temporary folder."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MAIN = ROOT / "calibration/v0.3/main"
SAMPLE = ("2302.12465", "2305.19518", "2309.15704", "2407.11735", "2502.16782")

_spec = importlib.util.spec_from_file_location(
    "verify_dossiers", ROOT / "calibration/v0.3/verify_dossiers.py"
)
vd = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vd)


def _copy(tmp_path: Path, arxiv: str, name: str = "dossier") -> Path:
    target = tmp_path / arxiv / name
    shutil.copytree(MAIN / "dossiers" / arxiv / "dossier", target)
    return target


def _verify(arxiv: str, dossier: Path) -> dict:
    return vd.verify(arxiv, dossier=dossier, claim_dir=MAIN / "claims" / arxiv / "claim")


def _edit_record(dossier: Path, change) -> None:
    path = dossier / "dossier.json"
    record = json.loads(path.read_bytes())
    change(record)
    path.write_text(json.dumps(record), encoding="utf-8")


def _has(report: dict, prefix: str) -> bool:
    return any(f.startswith(prefix) for f in report["findings"])


# ---- must pass ------------------------------------------------------------------------------


@pytest.mark.parametrize("arxiv", SAMPLE)
def test_published_dossier_is_verified(arxiv):
    report = vd.verify(arxiv)
    assert report["result"] == "VERIFIED", report["findings"]
    assert report["findings"] == []
    assert len(report["claims"]) == 3


def test_a_copy_under_another_folder_name_is_verified(tmp_path):
    report = _verify("2302.12465", _copy(tmp_path, "2302.12465", "renamed"))
    assert report["result"] == "VERIFIED", report["findings"]


# ---- must fail: V1 --------------------------------------------------------------------------


def test_changed_manifest_line_fails(tmp_path):
    d = _copy(tmp_path, "2302.12465")
    manifest = d / "MANIFEST.sha256"
    lines = manifest.read_text(encoding="utf-8").splitlines()
    lines[0] = "0" * 64 + lines[0][64:]
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report = _verify("2302.12465", d)
    assert report["result"] == "NOT VERIFIED"
    assert _has(report, "V1")


def test_changed_claim_input_with_manifest_updated_fails_on_the_lock(tmp_path):
    d = _copy(tmp_path, "2309.15704")
    data = (d / "claim_input.json").read_bytes().replace(b'"98.7"', b'"98.8"', 1)
    assert data != (d / "claim_input.json").read_bytes()
    for name in ("claim_input.json", "claim_file.json"):
        (d / name).write_bytes(data)
    digest = hashlib.sha256(data).hexdigest()
    manifest = d / "MANIFEST.sha256"
    lines = []
    for line in manifest.read_text(encoding="utf-8").splitlines():
        if line.endswith(("claim_input.json", "claim_file.json")):
            line = digest + line[64:]
        lines.append(line)
    manifest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    report = _verify("2309.15704", d)
    assert _has(report, "V1 lock")


# ---- must fail: V2, V3 ----------------------------------------------------------------------


def test_changed_verdict_fails(tmp_path):
    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, lambda r: r["outcome"]["claims"][0]["verdict"].update(verdict="FRAGILE"))
    report = _verify("2302.12465", d)
    assert _has(report, "V2 arXiv-2302.12465v3-C1: expected verdict")


def test_changed_computed_fails(tmp_path):
    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, lambda r: r["outcome"]["claims"][1].update(computed="NOT_REPRODUCED"))
    report = _verify("2302.12465", d)
    assert _has(report, "V2 arXiv-2302.12465v3-C2: recomputed REPRODUCED")


def test_invalid_accounting_with_verdicts_unchanged_fails(tmp_path):
    def change(r):
        r["outcome"]["run"]["accounting_valid"] = False
        r["outcome"]["run"]["invalid_reasons"] = ["a synthetic reason"]

    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, change)
    report = _verify("2302.12465", d)
    assert _has(report, "V2 arXiv-2302.12465v3-C1: expected verdict")


def test_changed_profile_fails(tmp_path):
    d = _copy(tmp_path, "2302.12465")
    _edit_record(
        d, lambda r: r["outcome"]["profile"].update(headline="Mixed results: see the claims")
    )
    assert _has(_verify("2302.12465", d), "V3 profile")
    d2 = _copy(tmp_path / "b", "2302.12465")
    _edit_record(d2, lambda r: r["outcome"]["profile"]["counts"].update(REPRODUCED=2))
    assert _has(_verify("2302.12465", d2), "V3 profile")


# ---- must fail: V4, V5 ----------------------------------------------------------------------


def _step(record, phase, claim_suffix, name):
    return next(
        s
        for s in record["outcome"]["run"]["steps"]
        if s["phase"] == phase and (s["claim"] or "").endswith(claim_suffix) and s["step"] == name
    )


def test_failed_base_step_recorded_as_completed_fails(tmp_path):
    def change(r):
        s = _step(r, "base", "C1", "base")
        s["outcome"], s["reason"] = "completed", ""

    d = _copy(tmp_path, "2309.15704")
    _edit_record(d, change)
    report = _verify("2309.15704", d)
    assert _has(report, "V4 base arXiv-2309.15704v2-C1 base: recorded completed")


def test_removed_duplicated_and_extra_steps_fail(tmp_path):
    d = _copy(tmp_path, "2407.11735")
    _edit_record(d, lambda r: r["outcome"]["run"]["steps"].pop())
    assert _has(_verify("2407.11735", d), "V4 steps: missing")

    d2 = _copy(tmp_path / "b", "2407.11735")
    _edit_record(
        d2, lambda r: r["outcome"]["run"]["steps"].append(r["outcome"]["run"]["steps"][-1])
    )
    assert _has(_verify("2407.11735", d2), "V4 steps: a step is recorded twice")

    def extra(r):
        s = dict(r["outcome"]["run"]["steps"][-1])
        s["step"] = "holdout"
        r["outcome"]["run"]["steps"].append(s)

    d3 = _copy(tmp_path / "c", "2407.11735")
    _edit_record(d3, extra)
    assert _has(_verify("2407.11735", d3), "V4 steps: not in the plan")


def test_empty_reason_of_a_not_executed_step_fails(tmp_path):
    d = _copy(tmp_path, "2407.11735")
    _edit_record(d, lambda r: _step(r, "base", "C2", "base").update(reason=""))
    report = _verify("2407.11735", d)
    assert _has(report, "V4 base arXiv-2407.11735v2-C2 base: not_executed with no reason")


def test_a_reason_the_runner_never_gives_fails(tmp_path):
    d = _copy(tmp_path, "2305.19518")
    _edit_record(
        d, lambda r: _step(r, "base", "C1", "base").update(reason="skipped for lack of time")
    )
    report = _verify("2305.19518", d)
    assert _has(report, "V4 base arXiv-2305.19518v2-C1 base: not executed: a reason the runner")


def test_base_obtained_for_a_failed_base_fails(tmp_path):
    def change(r):
        key = r["outcome"]["claims"][0]["key"]
        r["outcome"]["run"]["base_obtained"][key] = True

    d = _copy(tmp_path, "2309.15704")
    _edit_record(d, change)
    report = _verify("2309.15704", d)
    assert _has(report, "V4 run: base_obtained true")


def test_built_with_a_rung_that_did_not_complete_fails(tmp_path):
    d = _copy(tmp_path, "2407.11735")
    _edit_record(d, lambda r: r["outcome"]["ladder"].update(built_with="own_environment"))
    report = _verify("2407.11735", d)
    assert _has(report, "V5 ladder: built_with")


def test_malformed_record_is_a_finding_not_a_crash(tmp_path):
    d = _copy(tmp_path, "2302.12465")
    (d / "dossier.json").write_text("not json", encoding="utf-8")
    report = _verify("2302.12465", d)
    assert report["result"] == "NOT VERIFIED"
    assert _has(report, "the dossier cannot be read")

    d2 = _copy(tmp_path / "b", "2302.12465")
    _edit_record(d2, lambda r: r["outcome"].pop("claims"))
    report2 = _verify("2302.12465", d2)
    assert _has(
        report2, "the dossier cannot be read as recorded: RecordError: outcome has no claims"
    )


# ---- section 4a: the false accepts of the Codex review of 420c844 -------------------------


def test_failed_build_with_an_exit_zero_last_container_fails(tmp_path):
    def change(r):
        s = _step(r, "setup", "", "build")
        s["outcome"], s["reason"] = "failed", "setup/build/requirements_compiled: exit code 1"
        r["outcome"]["ladder"]["built_with"] = None

    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, change)
    assert _has(_verify("2302.12465", d), "V4 setup build: recorded failed")


def test_invented_refute_error_on_a_failed_base_fails(tmp_path):
    def change(r):
        s = _step(r, "base", "C1", "base")
        s["outcome"] = "refute_error"
        s["reason"] += "; the accounting was invented"

    d = _copy(tmp_path, "2309.15704")
    _edit_record(d, change)
    report = _verify("2309.15704", d)
    assert _has(report, "V4 base arXiv-2309.15704v2-C1 base: recorded refute_error")
    assert _has(report, "V4 run: stopped ''")


def test_unknown_stop_cause_fails(tmp_path):
    def change(r):
        _step(r, "base", "C1", "base")["containers"][0]["result"]["stopped"] = "mystery"

    d = _copy(tmp_path, "2309.15704")
    _edit_record(d, change)
    assert _has(_verify("2309.15704", d), "V4 base arXiv-2309.15704v2-C1 base: container")


@pytest.mark.parametrize(
    ("arxiv", "phase", "claim", "step", "reason", "expected"),
    [
        ("2305.19518", "base", "C1", "base", "the setup did not complete", "the setup completed"),
        ("2407.11735", "attacks", "C1", "seeds", "the paper stopped: invented", "a stop not"),
        ("2407.11735", "base", "C1", "base", "step base did not complete (not_executed)", "no ear"),
        ("2407.11735", "base", "C2", "base", "not reached", "'not reached' in a run"),
    ],
)
def test_not_executed_reasons_are_checked_by_cause(
    tmp_path, arxiv, phase, claim, step, reason, expected
):
    d = _copy(tmp_path, arxiv)
    _edit_record(d, lambda r: _step(r, phase, claim, step).update(reason=reason))
    report = _verify(arxiv, d)
    assert any(f.startswith(f"V4 {phase} ") and expected in f for f in report["findings"])


def test_an_invented_not_run_reason_copied_into_the_notes_fails(tmp_path):
    def change(r):
        text = "not run: an invented reason"
        _step(r, "base", "C1", "base")["reason"] = text
        r["outcome"]["claims"][0]["notes"] = [text]

    d = _copy(tmp_path, "2305.19518")
    _edit_record(d, change)
    assert _has(_verify("2305.19518", d), "V4 base arXiv-2305.19518v2-C1 base: not executed")


def test_setup_exhausted_with_the_wrong_reasons_fails(tmp_path):
    d = _copy(tmp_path, "2305.19518")
    _edit_record(d, lambda r: r["outcome"]["run"].update(setup_exhausted=True))
    report = _verify("2305.19518", d)
    assert _has(report, "V4 base arXiv-2305.19518v2-C2 base: ran although")
    assert _has(report, "V4 base arXiv-2305.19518v2-C1 base: reason")


def test_a_stop_with_no_refute_error_step_fails(tmp_path):
    def change(r):
        r["outcome"]["run"].update(stopped="invented", accounting_valid=False)
        r["outcome"]["run"]["invalid_reasons"] = ["invented"]

    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, change)
    assert _has(_verify("2302.12465", d), "V4 run: stopped 'invented' with no Refute error step")


def test_no_run_with_an_empty_ladder_or_a_passed_build_fails(tmp_path):
    def empty(r):
        r["outcome"]["run"] = None
        r["outcome"]["ladder"]["attempts"] = []

    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, empty)
    assert _has(_verify("2302.12465", d), "the dossier cannot be read as recorded: RecordError")

    d2 = _copy(tmp_path / "b", "2302.12465")
    _edit_record(d2, lambda r: r["outcome"].update(run=None))
    report = _verify("2302.12465", d2)
    assert _has(report, "V4 run: no run recorded although a rung")
    assert _has(report, "V4 run: no run, yet arXiv-2302.12465v3-C1's environment_build passed")


def test_accounting_valid_as_a_string_fails(tmp_path):
    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, lambda r: r["outcome"]["run"].update(accounting_valid="false"))
    assert _has(_verify("2302.12465", d), "the dossier cannot be read as recorded: RecordError")


def test_a_ladder_that_is_not_an_object_is_a_finding_not_a_crash(tmp_path):
    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, lambda r: r["outcome"].update(ladder=[]))
    assert _has(_verify("2302.12465", d), "the dossier cannot be read as recorded")


def test_steps_out_of_the_plans_order_fail(tmp_path):
    def change(r):
        steps = r["outcome"]["run"]["steps"]
        i = next(n for n, s in enumerate(steps) if s["phase"] == "base")
        steps[i], steps[i + 1] = steps[i + 1], steps[i]

    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, change)
    assert _has(_verify("2302.12465", d), "V4 order")


def test_the_accounting_rule_with_its_verdicts_and_profile_passes_v2_to_v5(tmp_path):
    def change(r):
        run = r["outcome"]["run"]
        run["accounting_valid"], run["invalid_reasons"] = False, ["a synthetic reason"]
        for c in r["outcome"]["claims"]:
            verdict = vd.ClaimVerdict(
                vd.PaperVerdict.INCONCLUSIVE, f"{vd.ig.ACCOUNTING_INVALID}: a synthetic reason"
            )
            c["verdict"] = vd._plain(verdict)
        keys = [(c["key"], "INCONCLUSIVE") for c in r["outcome"]["claims"]]
        r["outcome"]["profile"] = vd._plain(vd.paper_profile(keys))

    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, change)
    report = _verify("2302.12465", d)
    assert not [f for f in report["findings"] if f[:2] in ("V2", "V3", "V4", "V5")]
    assert _has(report, "V1")  # the copy no longer matches its manifest and seal


def test_a_missing_field_has_its_own_finding(tmp_path):
    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, lambda r: r["outcome"]["claims"][0].pop("computed"))
    assert _has(_verify("2302.12465", d), "the dossier cannot be read as recorded: RecordError")


def test_a_seal_or_annexes_unlike_the_committed_records_fail(tmp_path, monkeypatch):
    monkeypatch.setattr(vd, "seal_record", lambda: {"2302.12465": "0" * 64})
    assert _has(_verify("2302.12465", _copy(tmp_path, "2302.12465")), "V1 seal: core")
    monkeypatch.undo()
    d = _copy(tmp_path / "b", "2302.12465")
    shutil.rmtree(d / "annexes")
    assert _has(_verify("2302.12465", d), "V1 annexes")


def test_attack_records_round_trip_through_the_plain_record():
    def check(name, status, coverage):
        return vd.TestResult(
            name, status, vd.Severity.GATE, "m", metrics={"expected_coverage": 3}, coverage=coverage
        )

    attack = vd.Attack(
        "seeds",
        check("seeds:run", vd.TestStatus.PASS, 3),
        check("seeds:metric", vd.TestStatus.PASS, 3),
        check("seeds", vd.TestStatus.FAIL, 3),
    )
    rebuilt = vd._attack(json.loads(json.dumps(vd._plain(attack))))
    assert vd._plain(rebuilt) == vd._plain(attack)
    empty = vd._attack(json.loads(json.dumps(vd._plain(vd.Attack("holdout")))))
    assert empty.run is None and empty.metric is None and empty.result is None


# ---- section 4b: paths of the frozen runner that must be accepted -------------------------


def _step_findings(report: dict, where: str) -> list[str]:
    return [f for f in report["findings"] if f.startswith(f"V4 {where}:")]


def test_a_threshold_stop_without_an_exit_code_is_accepted(tmp_path):
    def change(r):
        s = _step(r, "base", "C1", "base")
        cid = s["containers"][0]["container_id"]
        s["containers"][0]["result"].update(exit_code=None, stopped=vd.orc.STOP_THRESHOLD)
        s["outcome"], s["reason"] = "budget_exhausted", f"threshold reached: {cid}"

    d = _copy(tmp_path, "2309.15704")
    _edit_record(d, change)
    report = _verify("2309.15704", d)
    assert not _has(report, "the dossier cannot be read")
    assert _step_findings(report, "base arXiv-2309.15704v2-C1 base") == []


def _two_rungs(r):
    for a in r["outcome"]["ladder"]["attempts"]:
        if a["rung"] == "requirements_compiled_next_python":
            a["applicable"] = True
    s = _step(r, "setup", "", "build")
    s["containers"][0]["result"]["exit_code"] = 1
    r["outcome"]["ladder"]["built_with"] = None
    return s


def test_a_grant_refused_between_rungs_is_accepted(tmp_path):
    def change(r):
        s = _two_rungs(r)
        s["outcome"], s["reason"] = "budget_exhausted", "budget_exhausted (setup)"

    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, change)
    assert _step_findings(_verify("2302.12465", d), "setup build") == []


def test_a_classifier_failure_is_accepted(tmp_path):
    def change(r):
        s = _step(r, "setup", "", "build")
        s["outcome"], s["reason"] = "refute_error", "the fallback failed: OSError: unreadable log"
        r["outcome"]["ladder"]["built_with"] = None

    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, change)
    report = _verify("2302.12465", d)
    assert _step_findings(report, "setup build") == []
    # its consequences are still required: the stop is not recorded in this copy
    assert _has(report, "V4 run: stopped ''")


# ---- section 4c: refusal reasons and prerequisites -----------------------------------------


def test_an_invented_refusal_between_rungs_fails(tmp_path):
    def change(r):
        s = _two_rungs(r)
        s["outcome"], s["reason"] = "refute_error", "skipped for lack of time"

    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, change)
    assert _has(_verify("2302.12465", d), "V4 setup build: recorded refute_error")


def test_base_steps_that_ran_after_a_failed_build_fail(tmp_path):
    def change(r):
        s = _step(r, "setup", "", "build")
        cid = s["containers"][0]["container_id"]
        s["containers"][0]["result"]["exit_code"] = 1
        s["outcome"], s["reason"] = "failed", f"{cid}: exit code 1"
        r["outcome"]["ladder"]["built_with"] = None

    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, change)
    report = _verify("2302.12465", d)
    assert _has(report, "V4 base arXiv-2302.12465v3-C1 base: ran although the setup did not")
    assert _has(report, "V4 setup data/UserItemAttr: ran after an earlier setup step")


def test_base_steps_that_ran_after_a_setup_refute_error_fail(tmp_path):
    def change(r):
        s = _step(r, "setup", "", "build")
        s["outcome"], s["reason"] = "refute_error", "the fallback failed: OSError: x"
        r["outcome"]["ladder"]["built_with"] = None
        run = r["outcome"]["run"]
        run["stopped"] = "setup build: the fallback failed: OSError: x"
        run["accounting_valid"], run["invalid_reasons"] = False, [run["stopped"]]

    d = _copy(tmp_path, "2302.12465")
    _edit_record(d, change)
    report = _verify("2302.12465", d)
    assert _has(report, "V4 base arXiv-2302.12465v3-C1 base: ran after the paper stopped")
