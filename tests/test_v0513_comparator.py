"""The comparator of v0.5.13's amendment 2, section 3.1 (revision 8), on synthetic tokens only.

It opens no golden file: every input here is written by the test.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "v0513_comparator", ROOT / "docs/validation/v0.5.13/tools/comparator.py"
)
comp = importlib.util.module_from_spec(spec)
sys.modules["v0513_comparator"] = comp
spec.loader.exec_module(comp)

SCHEMA = {
    "exact_keys": ["snr_min"],
    "json": {
        "verdict": {
            "measurement": ["candidate.**", "tests[*].metrics.**"],
            "exact": ["tests[*].thresholds.**"],
        },
        "chain": {"measurement": ["candidate.**"]},
    },
    "report": [
        {
            "name": "snr-row",
            "regex": r"\| SNR \| (?P<found>\S+) \| \|",
            "groups": {"found": "measurement"},
        },
        {
            "name": "rel-error",
            "regex": r"- Relative period error: (?P<rel>\S+) \(tolerance (?P<tol>\S+)\)",
            "groups": {"rel": "measurement", "tol": "exact"},
        },
    ],
}


def verdict(period: str, snr_min: str = "7.0", thr: str = "7.1", count: str = "3") -> str:
    template = (
        '{\n  "candidate": {\n    "period": PERIOD\n  },\n  "tests": [\n    {\n'
        '      "metrics": {\n        "n": COUNT,\n        "snr_min": SNRMIN\n      },\n'
        '      "thresholds": {\n        "snr": THR\n      }\n    }\n  ]\n}\n'
    )
    for name, value in (("PERIOD", period), ("COUNT", count), ("SNRMIN", snr_min), ("THR", thr)):
        template = template.replace(name, value)
    return template


def jcmp(a: str, b: str) -> list[str]:
    return comp.compare_json(a, b, "verdict", SCHEMA)


def test_identical_json_passes():
    assert jcmp(verdict("1.5"), verdict("1.5")) == []


def test_measurement_within_budget_passes_and_beyond_fails():
    assert jcmp(verdict("1.0000000"), verdict("1.0000005")) == []
    assert jcmp(verdict("1.0"), verdict("1.000002"))


def test_budget_is_relative_and_zero_equals_only_zero():
    assert comp.within_budget("0.0", "0.0")
    assert not comp.within_budget("0.0", "1e-300")
    assert comp.within_budget("1000000.0", "1000001.0")
    assert not comp.within_budget("1000000.0", "1000002.0")


def test_integer_token_compares_exactly():
    assert jcmp(verdict("1.5", count="3"), verdict("1.5", count="4"))


def test_threshold_path_and_exact_key_compare_exactly():
    assert jcmp(verdict("1.5", thr="7.1"), verdict("1.5", thr="7.1000001"))
    assert jcmp(verdict("1.5", snr_min="7.0"), verdict("1.5", snr_min="7.0000001"))


def test_last_key_skips_list_indices():
    assert comp.last_key("tests[0].thresholds.snr_min[1]") == "snr_min"
    assert comp.last_key("a.b[2][0]") == "b"
    assert comp.last_key("candidate.period") == "period"


def test_list_under_an_exact_key_compares_exactly():
    a = '{\n  "candidate": {\n    "snr_min": [\n      1.0\n    ]\n  }\n}\n'
    assert jcmp(a, a.replace("1.0", "1.0000001"))


def test_exact_subtree_key_covers_its_whole_subtree():
    a = '{\n  "candidate": {\n    "thresholds_m4": {\n      "x": 1.0\n    }\n  }\n}\n'
    b = a.replace("1.0", "1.0000001")
    assert jcmp(a, b) == []
    schema = {**SCHEMA, "exact_subtree_keys": ["thresholds_m4"]}
    assert comp.compare_json(a, b, "verdict", schema)


def test_null_against_number_fails():
    assert jcmp(verdict("1.5"), verdict("null"))
    assert jcmp(verdict("null"), verdict("null")) == []


def test_whitespace_and_structure_compare_exactly():
    a = verdict("1.5")
    assert jcmp(a, a.replace("\n", "\r\n"))
    assert jcmp(a, a.replace('"period"', '"periods"'))


def test_mixed_forms_compare_by_value_only_on_measurement_paths():
    # Codex's round 2, item 3: "2.0" and "2" on a measurement path are the same value; on an
    # integer count (both integer form) or an exact path a difference still fails
    assert jcmp(verdict("2.0"), verdict("2")) == []
    assert jcmp(verdict("1.5", count="3"), verdict("1.5", count="4"))
    assert jcmp(verdict("1.5", thr="7"), verdict("1.5", thr="7.0"))  # an exact path


def test_report_templates():
    rep = comp.compare_report
    assert rep("| SNR | 12.3456 | |", "| SNR | 12.3456 | |", SCHEMA) == []
    assert rep("| SNR | 1.0000000 | |", "| SNR | 1.0000001 | |", SCHEMA) == []
    assert rep("| SNR | 12.35 | |", "| SNR | 12.34 | |", SCHEMA)
    # decision S1, item 4: a valid change of printed form is compared by value
    assert rep("| SNR | 1.2e+05 | |", "| SNR | 120000.0 | |", SCHEMA) == []
    assert rep("| SNR | 99999.9999 | |", "| SNR | 1.0000e+05 | |", SCHEMA) == []
    assert rep("| SNR | n/a | |", "| SNR | 1.0 | |", SCHEMA)
    assert rep("a\nb", "a", SCHEMA)
    assert rep("free text 1.0", "free text 1.0000001", SCHEMA)
    line = "- Relative period error: {} (tolerance {})"
    assert rep(line.format("0.5", "0.01"), line.format("0.5000001", "0.01"), SCHEMA) == []
    assert rep(line.format("0.5", "0.01"), line.format("0.5", "0.0100001"), SCHEMA)


def test_ambiguous_template_fails():
    schema = dict(SCHEMA)
    schema["report"] = SCHEMA["report"] + [
        {"name": "dup", "regex": r"\| SNR \| (?P<x>\S+) \| \|", "groups": {"x": "measurement"}}
    ]
    assert comp.compare_report("| SNR | 1.0 | |", "| SNR | 1.0000001 | |", schema)


def test_files_by_kind():
    v = verdict("1.5") + comp.SEPARATOR + "| SNR | 1.0 | |"
    w = verdict("1.5000001") + comp.SEPARATOR + "| SNR | 1.0000001 | |"
    assert comp.compare_file("verdict-v1.txt", v.encode(), w.encode(), SCHEMA) == []
    assert comp.compare_file("plan-v1.json", b'{"a": 1.0}', b'{"a": 1.0000001}', SCHEMA)
    assert comp.compare_file("error-v1.json", b"x", b"y", SCHEMA)
    assert comp.compare_file("verdict-v1.txt", b"ERROR a", b"ERROR b", SCHEMA)
    assert comp.compare_file("verdict-v1.txt", verdict("1.5").encode(), b"{}", SCHEMA)
    assert comp.compare_file("chain-v1.json", b'{"candidate": {"p": 1.0}}',
                             b'{"candidate": {"p": 1.0000001}}', SCHEMA) == []  # fmt: skip
    assert comp.compare_file("chain-v1.json", b"{", b"{}", SCHEMA)


def _record(folder: Path, files: dict[str, bytes]) -> dict:
    folder.mkdir()
    for name, data in files.items():
        (folder / name).write_bytes(data)
    digests = {n: hashlib.sha256(d).hexdigest() for n, d in files.items()}
    return {"payload": {"files_sha256": digests, "error_outputs": []}}


def test_setting_inventory_and_hashes(tmp_path):
    files = {"plan-v1.json": b"{}\n", "chain-v1.json": b'{"candidate": {"p": 1.0}}\n'}
    ref = _record(tmp_path / "ref", files)
    alt = _record(tmp_path / "alt", files)
    assert (
        comp.compare_setting(SCHEMA, ref, tmp_path / "ref", alt, tmp_path / "alt")["result"]
        == "PASS"
    )
    (tmp_path / "alt" / "extra.txt").write_bytes(b"x")
    assert (
        comp.compare_setting(SCHEMA, ref, tmp_path / "ref", alt, tmp_path / "alt")["result"]
        == "FAIL"
    )
    (tmp_path / "alt" / "extra.txt").unlink()
    (tmp_path / "alt" / "plan-v1.json").write_bytes(b"{} \n")
    assert (
        comp.compare_setting(SCHEMA, ref, tmp_path / "ref", alt, tmp_path / "alt")["result"]
        == "FAIL"
    )


EXAMPLES = {
    "period-row": "| Period (d) | 3.1234567 | n/a |",
    "epoch-row": "| Epoch (BJD_TDB) | 2459001.2345678 | n/a |",
    "duration-row": "| Duration (h) | 2.500 | n/a |",
    "depth-row": "| Depth (ppm) | 1200.0 | n/a |",
    "snr-row": "| SNR | 25.3 | |",
    "relative-period-error": (
        "- Relative period error: n/a (tolerance n/a, within: n/a, alias: none)"
    ),
    "sde-line": (
        "- SDE: the largest SDE over sectors. SDE of the kept peak (largest over sectors): 12.34."
    ),
    "parameters-line": (
        "- Period 3.1234 d (error 1e-05) and epoch 2459001.2 BJD_TDB (error 0.0002), from: fit."
    ),
    "cadence-row": "| 1 | 18000 | 19000 | 0.947 |",
    "holdout-row": "| 2019 | PASS | 4 | 12.1 | 0.3 |",
    "holdout-v05-row": "| 2019 | yes | 0.85 |",
    "gauntlet-row": "| odd_even | INCONCLUSIVE (out_of_domain) | fatal | depths 12.3, 11.9 |",
}


def test_draft_schema_templates_compile_and_match_once():
    import re

    parts = json.loads(
        (ROOT / "docs/validation/v0.5.13/l4/comparator-schema-parts.json").read_text("utf-8")
    )
    names = [t["name"] for t in parts["report"]]
    assert sorted(names) == sorted(EXAMPLES)
    for name, line in EXAMPLES.items():
        matched = [t["name"] for t in parts["report"] if re.fullmatch(t["regex"], line)]
        assert matched == [name], (name, matched)
    for t in parts["report"]:
        assert set(re.compile(t["regex"]).groupindex) == set(t["groups"])
    for kind in ("verdict", "chain"):
        for p in parts["json"][kind]["measurement"] + parts["json"][kind]["exact"]:
            comp._pattern(p)


def test_frozen_schema_loads_and_compiles():
    import re

    import pytest

    path = ROOT / "docs/validation/v0.5.13/l4/comparator-schema.json"
    if not path.is_file():
        pytest.skip("the schema is committed by the freeze commit, after this test")
    schema = json.loads(path.read_text("utf-8"))
    assert schema["exact_keys"] and "thresholds" in schema["exact_subtree_keys"]
    for t in schema["report"]:
        assert set(re.compile(t["regex"]).groupindex) == set(t["groups"])
    for kind in ("verdict", "chain"):
        for p in schema["json"][kind]["measurement"] + schema["json"][kind]["exact"]:
            comp._pattern(p)
    v = verdict("1.5") + comp.SEPARATOR + "| SNR | 1.0 | |"
    assert comp.compare_file("verdict-v1.txt", v.encode(), v.encode(), schema) == []


H1, H2 = "a" * 64, "b" * 64
EXC = {"d.yaml": "ERROR ClaimError: x"}


def rec(claims: dict) -> str:
    return json.dumps({"payload": {"claims": claims}}, indent=1)


def test_claims():
    a = rec({"c.yaml": H1, "d.yaml": "ERROR ClaimError: x"})
    assert comp.compare_claims(a, a, EXC) == []
    assert comp.compare_claims(a, rec({"c.yaml": H2, "d.yaml": "ERROR ClaimError: x"}), EXC)
    assert comp.compare_claims(a, rec({"c.yaml": H1}), EXC)


def test_claims_reject_shared_gaps_and_bad_values():
    # the same malformed value, or the same missing exception, in both records still fails
    bad = rec({"c.yaml": "ab", "d.yaml": "ERROR ClaimError: x"})
    assert comp.compare_claims(bad, bad, EXC)
    gap = rec({"c.yaml": H1})
    assert comp.compare_claims(gap, gap, EXC)
    other = rec({"c.yaml": H1, "d.yaml": "ERROR ClaimError: y"})
    assert comp.compare_claims(other, other, EXC)
    number = '{"payload": {"claims": {"c.yaml": 1, "d.yaml": "ERROR ClaimError: x"}}}'
    assert comp.compare_claims(number, number, EXC)


def test_claim_exception_is_compared_by_its_bytes():
    # decision S1, item 5: "ERROR" decodes to "ERROR" but is not the same serialized value
    a = rec({"c.yaml": H1, "d.yaml": "ERROR ClaimError: x"})
    b = a.replace('"ERROR ClaimError', '"\\u0045RROR ClaimError')
    assert json.loads(a) == json.loads(b)
    assert comp.compare_claims(a, b, EXC) == ["claim d.yaml: serialized entry differs"]


def test_no_shortcut_on_equal_bytes():
    assert comp.compare_file("chain-v1.json", b"{", b"{", SCHEMA)
    assert comp.compare_file("chain-v1.json", b'{"a": 1, "a": 1}', b'{"a": 1, "a": 1}', SCHEMA)
    assert comp.compare_file("plan-v1.json", b'{"a": 1, "a": 2}', b'{"a": 1, "a": 2}', SCHEMA)
    v = verdict("1.5").encode()
    assert comp.compare_file("verdict-v1.txt", v, v, SCHEMA)  # no report separator
    assert comp.compare_file("plan-v1.json", b'{"a": 1}', b'{"a": 1}', SCHEMA) == []


def test_ambiguous_template_fails_on_equal_lines():
    schema = dict(SCHEMA)
    schema["report"] = SCHEMA["report"] + [
        {"name": "dup", "regex": r"\| SNR \| (?P<x>\S+) \| \|", "groups": {"x": "measurement"}}
    ]
    assert comp.compare_report("| SNR | 1.0 | |", "| SNR | 1.0 | |", schema)


NAMES = {
    **SCHEMA,
    "exact_keys": ["snr_min", "period_err_days"],
    "exact_key_regex": "^(required_|min_|max_)|(_threshold|_limit)$",
    "computed_keys_despite_name": {"max_event_snr": "s", "max_timing_sigma_days": "s"},
    "exact_key_exempt_paths": ["v05.parameters.period_err_days"],
    "json": {
        "verdict": {
            "measurement": ["candidate.**", "v05.**", "tests[*].**", "search_diagnostics.**"],
            "exact": [
                "search_diagnostics.refined[*].factor",
                "tests[*].metrics.near_systematic_periods_days[*]",
            ],
        }
    },
    "exact_by_sibling": [
        {
            "pattern": "tests[*].sensitivity.*.alternative",
            "sibling": "effect",
            "values": ["SAP relative depth difference"],
        }
    ],
}


def nudged(doc: str, old: str = "1.0", new: str = "1.0000001") -> list[str]:
    return comp.compare_json(doc, doc.replace(old, new), "verdict", NAMES)


def test_threshold_names_and_computed_measurements():
    doc = '{\n  "candidate": {\n    "KEY": 1.0\n  }\n}\n'
    cases = (
        ("required_probability", True),
        ("min_train_snr", True),
        ("max_event_snr", False),  # decision S1, item 1: a computed measurement
        ("max_timing_sigma_days", False),
        ("x", False),
    )
    for key, fails in cases:
        assert bool(nudged(doc.replace("KEY", key))) is fails, key


def test_the_fit_error_exemption_is_one_path():
    fit = '{\n  "v05": {\n    "parameters": {\n      "period_err_days": 1.0\n    }\n  }\n}\n'
    assert nudged(fit) == []
    other = fit.replace('"parameters"', '"other"')
    assert nudged(other)  # the plan field elsewhere under v05 stays exact
    cand = '{\n  "candidate": {\n    "period_err_days": 1.0\n  }\n}\n'
    assert nudged(cand)


def test_configuration_under_broad_patterns_is_exact():
    refined = '{"search_diagnostics": {"refined": [{"factor": 1.0, "period": 1.0}]}}'
    assert nudged(refined, '"factor": 1.0', '"factor": 1.0000001')
    assert nudged(refined, '"period": 1.0', '"period": 1.0000001') == []
    near = '{"tests": [{"metrics": {"near_systematic_periods_days": [1.0]}}]}'
    assert nudged(near)


def test_alternative_exact_when_the_plan_sets_it():
    block = '{"tests": [{"sensitivity": {"sap": {"effect": "EFFECT", "alternative": 1.0}}}]}'
    assert nudged(block.replace("EFFECT", "SAP relative depth difference"))
    assert nudged(block.replace("EFFECT", "odd/even depth difference")) == []


def test_gauntlet_message_lines_are_exact():
    # decision S2: a message line is compared byte for byte, even when only a number changes
    parts = json.loads(
        (ROOT / "docs/validation/v0.5.13/l4/comparator-schema-parts.json").read_text("utf-8")
    )
    schema = {**SCHEMA, "report": parts["report"]}
    line = "| snr | PASS | fatal | SNR 12.3456 >= 7.0 |"
    assert comp.compare_report(line, line, schema) == []
    assert comp.compare_report(line, line.replace("12.3456", "12.3456001"), schema)
    assert "message" in parts["message_lines"]["decision"]


def test_malformed_measurement_groups_fail_even_when_equal():
    rep = comp.compare_report
    assert rep("| SNR | bogus | |", "| SNR | bogus | |", SCHEMA)
    assert rep("| SNR | n/a | |", "| SNR | n/a | |", SCHEMA) == []
    assert rep("| SNR | inf | |", "| SNR | inf | |", SCHEMA) == []
    assert rep("| SNR | inf | |", "| SNR | 1.0 | |", SCHEMA)


def test_non_standard_json_constants_are_malformed():
    assert comp.compare_file("plan-v1.json", b'{"a": NaN}', b'{"a": NaN}', SCHEMA)
    assert comp.compare_file("chain-v1.json", b'{"a": Infinity}', b'{"a": Infinity}', SCHEMA)


def test_coverage_counts_json_and_report_pairs():
    # decision R2: numeric pairs compared and differing, and the largest relative difference
    cov = comp.Coverage()
    v = verdict("1.5") + comp.SEPARATOR + "| SNR | 2.0 | |\nfree text 9.0"
    w = verdict("1.5000003") + comp.SEPARATOR + "| SNR | 2.0000002 | |\nfree text 9.0"
    assert comp.compare_file("verdict-v1.txt", v.encode(), w.encode(), SCHEMA, cov) == []
    # JSON: period, n, snr_min, thr (4 pairs); report: one templated group (free text: none)
    d = cov.as_dict()
    assert d["numeric_tokens_compared"] == 5
    assert d["numeric_tokens_differing"] == 2
    # 0.0000003 / 1.5000003 (1.9999996e-7) is the larger of the two; 6 significant digits
    assert d["largest_relative_difference"] == "2.00000e-7"


def test_coverage_of_equal_and_exact_files():
    cov = comp.Coverage()
    assert comp.compare_file("plan-v1.json", b'{"a": 1.0}', b'{"a": 1.0}', SCHEMA, cov) == []
    assert cov.as_dict() == {
        "numeric_tokens_compared": 0,
        "numeric_tokens_differing": 0,
        "largest_relative_difference": "0",
    }
    a = b'{"candidate": {"p": 1.0, "q": 0.0}}'
    assert comp.compare_file("chain-v1.json", a, a, SCHEMA, cov) == []
    assert cov.as_dict()["numeric_tokens_compared"] == 2
    assert cov.as_dict()["numeric_tokens_differing"] == 0


def test_setting_reports_coverage_and_zero_coverage_is_inconclusive(tmp_path):
    files = {"plan-v1.json": b"{}\n", "chain-v1.json": b'{"candidate": {"p": 1.0}}\n'}
    ref = _record(tmp_path / "ref", files)
    alt = _record(tmp_path / "alt", files)
    out = comp.compare_setting(SCHEMA, ref, tmp_path / "ref", alt, tmp_path / "alt")
    assert out["result"] == "PASS"
    assert out["coverage"] == {
        "files_compared": 2,
        "numeric_tokens_compared": 1,
        "numeric_tokens_differing": 0,
        "largest_relative_difference": "0",
    }
    assert sorted(out["coverage_by_file"]) == ["chain-v1.json", "plan-v1.json"]
    empty_ref = _record(tmp_path / "e1", {})
    empty_alt = _record(tmp_path / "e2", {})
    out = comp.compare_setting(SCHEMA, empty_ref, tmp_path / "e1", empty_alt, tmp_path / "e2")
    assert out["result"] == "INCONCLUSIVE"
    assert out["coverage"]["files_compared"] == 0


def _write(root: Path, rel: str, text: str) -> str:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return hashlib.sha256(text.encode()).hexdigest()


def _freeze(root: Path) -> dict:
    """A synthetic freeze list: the reference, one frozen setting, the NR-A2 entry."""
    digest = {
        "schema": _write(root, "s/schema.json", json.dumps(SCHEMA)),
        "ref": _write(root, "s/ref.json", '{"payload": {}}'),
        "ref_c": _write(root, "s/ref-c.json", '{"payload": {}}'),
        "t1": _write(root, "s/t1.json", '{"payload": {}}'),
        "t1_c": _write(root, "s/t1-c.json", '{"payload": {}}'),
        "manifest": _write(root, "m/nr-a2.json", '{"manifest": "NR-A2"}'),
    }
    return {
        "schema": {"path": "s/schema.json", "sha256": digest["schema"]},
        "settings": {
            "id-before": {"record": "s/ref.json", "record_sha256": digest["ref"],
                          "claim_record": "s/ref-c.json", "claim_record_sha256": digest["ref_c"]},
            "nr-a1-t1": {"record": "s/t1.json", "record_sha256": digest["t1"],
                         "claim_record": "s/t1-c.json", "claim_record_sha256": digest["t1_c"]},
        },
        "prospective": {
            "nr-a2-t2": {
                "manifest": {"path": "m/nr-a2.json", "sha256": digest["manifest"]},
                "record": "s/a2.json",
                "claim_record": "s/a2-c.json",
                "script": "t/identity_v2.py",
                "script_sha256": "f" * 64,
                "thread_env": {"OMP_NUM_THREADS": "2"},
                "threads": 2,
                "journal": "log.jsonl",
                "units": {
                    "golden": {"unit": "g", "spec": "u/g.json", "spec_sha256": "1" * 64,
                               "output": "s/a2.json"},
                    "claims": {"unit": "c", "spec": "u/c.json", "spec_sha256": "2" * 64,
                               "output": "s/a2-c.json"},
                },
                "fixture_code": "tests/f.py",
                "authorized_code_commit": "auth",
                "code_digest": dict(DIGEST),
            }
        },
    }  # fmt: skip


DIGEST = {"src_tree": "tree", "fixture_code_sha256": "3" * 64, "pyproject_sha256": "4" * 64,
          "uv_lock_sha256": "5" * 64, "script_sha256": "f" * 64}  # fmt: skip
FREEZE_REL = "f/freeze.json"
# the synthetic order: the manifest's push run at 20:50, the runs 21:00-21:10, records at 21:20
PUSHED, START, END, RECORDED = (
    "2026-11-27T20:50:00Z",
    "2026-11-27T21:00:00Z",
    "2026-11-27T21:10:00Z",
    "2026-11-27T21:20:00+00:00",
)
COMMITS = {"f/": "F", "m/": "M", "r/": "R", "s/": "C"}


def _journal(root: Path, freeze: dict, **change) -> list[dict]:
    """A synthetic journal: one successful run of each NR-A2 unit, as the launcher writes it."""
    entry = freeze["prospective"]["nr-a2-t2"]
    out = []
    for i, key in enumerate(("golden", "claims")):
        unit = entry["units"][key]
        before = {
            "event": "before", "unit": unit["unit"], "attempt_id": f"a{i}", "head": "h",
            "utc": START,
            "identity_sha256": {unit["spec"]: unit["spec_sha256"],
                                entry["script"]: entry["script_sha256"]},
            "env": dict(entry["thread_env"]),
            "order_proof": {"manifest": entry["manifest"]["path"],
                            "manifest_sha256": entry["manifest"]["sha256"]},
        }  # fmt: skip
        data = (root / unit["output"]).read_bytes()
        after = {
            "event": "after", "unit": unit["unit"], "attempt_id": f"a{i}", "status": "ok",
            "exit_code": 0, "utc": END,
            "outputs_sha256": {unit["output"]: hashlib.sha256(data).hexdigest()},
        }  # fmt: skip
        for k, v in change.items():
            target = after if k.startswith("after_") else before
            target[k.removeprefix("after_")] = v
        out += [before, after]
    return out


def _check(**change) -> dict:
    check = {"head": "h", "authorized_commit": "auth", "same_code_as_authorized": True,
             "porcelain": "", "digest": dict(DIGEST)}  # fmt: skip
    check.update(change)
    return check


def _nr_a2_records(
    root: Path, label="nr-a2-t2", script="f" * 64, threads=2, env="2", code_check=None
) -> None:
    code = code_check if code_check is not None else {"before": _check(), "after": _check()}
    prov = {
        "head": "h",
        "script_sha256": script,
        "blas": {"thread_env": {"OMP_NUM_THREADS": env}},
        "code_check": code,
    }
    golden = {"label": label, "payload": {}, "provenance": {**prov}}
    golden["provenance"]["blas"] = {
        "thread_env": {"OMP_NUM_THREADS": env},
        "child_threadpool_info": [{"num_threads": threads}, {"num_threads": threads}],
    }
    _write(root, "s/a2.json", json.dumps(golden))
    _write(root, "s/a2-c.json", json.dumps({"label": label, "payload": {}, "provenance": prov}))


def _git_ok(
    monkeypatch,
    root: Path,
    freeze: dict,
    not_ancestor=(),
    receipt=True,
    committed=True,
    journal=None,
    digest=None,
    same=True,
    recorded=RECORDED,
):
    receipt_doc = {"ci_run_created_at": PUSHED, "receipt_rel": "r/receipt.json"}
    monkeypatch.setattr(comp, "ROOT", root)
    monkeypatch.setattr(comp, "committed", lambda rel, data: committed)
    monkeypatch.setattr(comp, "receipt_ok", lambda rel, s, files: receipt_doc if receipt else None)
    monkeypatch.setattr(comp, "last_commit", lambda rel: COMMITS[rel[:2]])
    monkeypatch.setattr(comp, "is_ancestor", lambda a, b: (a, b) not in not_ancestor)
    monkeypatch.setattr(comp, "commit_facts", lambda c: (1, True, recorded))
    monkeypatch.setattr(comp, "code_digest", lambda head, entry: digest or dict(DIGEST))
    monkeypatch.setattr(comp, "same_code", lambda a, b: same)
    monkeypatch.setattr(
        comp,
        "journal_entries",
        lambda rel: journal if journal is not None else _journal(root, freeze),
    )


def _bind(freeze: dict, label: str = "nr-a2-t2") -> list[str]:
    return comp.bind(freeze, label, FREEZE_REL)[1]


def test_frozen_settings_are_bound_by_hash(tmp_path, monkeypatch):
    freeze = _freeze(tmp_path)
    _git_ok(monkeypatch, tmp_path, freeze)
    parsed, problems = comp.bind(freeze, "nr-a1-t1", FREEZE_REL)
    assert problems == [] and "raw" in parsed
    (tmp_path / "s/t1-c.json").write_text('{"payload": {"x": 1}}', encoding="utf-8")
    assert _bind(freeze, "nr-a1-t1") == ["alt_claims: SHA-256 is not the frozen one"]


def test_no_unbound_path(tmp_path, monkeypatch):
    # decision S3: a label that is neither frozen nor the frozen prospective one is refused
    freeze = _freeze(tmp_path)
    _git_ok(monkeypatch, tmp_path, freeze)
    problems = _bind(freeze, "nr-a2-t3")
    assert problems and "neither" in problems[0]
    assert _bind(freeze, "id-before")  # the reference is never an alternate


def test_nr_a2_is_bound_to_its_manifest_and_setting(tmp_path, monkeypatch):
    freeze = _freeze(tmp_path)
    _nr_a2_records(tmp_path)
    _git_ok(monkeypatch, tmp_path, freeze)
    assert _bind(freeze) == []
    for kwargs, expected in (
        ({"label": "nr-a1-t1"}, "labelled"),
        ({"script": "e" * 64}, "identity script"),
        ({"threads": 4}, "thread count"),
        ({"env": "4"}, "thread variables"),
    ):
        _nr_a2_records(tmp_path, **kwargs)
        problems = _bind(freeze)
        assert any(expected in p for p in problems), (kwargs, problems)
    _nr_a2_records(tmp_path)
    for kwargs, expected in (
        ({"not_ancestor": {("M", "C")}}, "after the NR-A2 manifest"),
        ({"receipt": False}, "order-proof receipt"),
        ({"committed": False}, "not committed"),
    ):
        _git_ok(monkeypatch, tmp_path, freeze, **kwargs)
        problems = _bind(freeze)
        assert any(expected in p for p in problems), (kwargs, problems)
    _git_ok(monkeypatch, tmp_path, freeze)
    (tmp_path / "m/nr-a2.json").write_text('{"manifest": "changed"}', encoding="utf-8")
    assert any("not the frozen one" in p for p in _bind(freeze))


def test_nr_a2_records_need_their_journal_runs(tmp_path, monkeypatch):
    # Codex's round 2, item 5: copies of other payloads, committed after the manifest with the
    # right provenance fields, are refused without the journal's runs of the authorized units
    freeze = _freeze(tmp_path)
    _nr_a2_records(tmp_path)
    for change, expected in (
        ({"env": {"OMP_NUM_THREADS": "4"}}, "thread variables"),
        ({"after_status": "failed"}, "did not end successfully"),
        ({"after_outputs_sha256": {}}, "output SHA-256"),
        ({"identity_sha256": {}}, "unit spec"),
        ({"order_proof": {}}, "order proof"),
    ):
        _git_ok(monkeypatch, tmp_path, freeze, journal=_journal(tmp_path, freeze, **change))
        problems = _bind(freeze)
        assert any(expected in p for p in problems), (change, problems)
    _git_ok(monkeypatch, tmp_path, freeze, journal=[])
    assert any("exactly one run" in p for p in _bind(freeze))
    twice = _journal(tmp_path, freeze)
    _git_ok(monkeypatch, tmp_path, freeze, journal=twice + twice)
    assert any("exactly one run" in p for p in _bind(freeze))


# --- decision T2: one test per attack of Codex's round 3 (s5/codex/answer-r3.md) -------------


def test_t2_1_counts_ids_and_versions_are_exact():
    # attack 1: candidate.n_transits 100 -> 100.00001 and v05.discovery_version 4 -> 4.0
    schema = {
        **SCHEMA,
        "exact_integer_keys": {"n_transits": ["types.py:256"], "discovery_version": ["p:863"]},
        "json": {"verdict": {"measurement": ["candidate.**", "v05.**"], "exact": []}},
    }

    def cmp(a: str, b: str) -> list[str]:
        return comp.compare_json(a, b, "verdict", schema)

    count = '{"candidate": {"n_transits": VALUE, "period": 1.5}}'
    assert cmp(count.replace("VALUE", "100"), count.replace("VALUE", "100.00001"))
    version = '{"v05": {"discovery_version": VALUE}}'
    assert cmp(version.replace("VALUE", "4"), version.replace("VALUE", "4.0"))
    # a change of notation is compared by value only on a measurement path
    period = '{"candidate": {"n_transits": 3, "period": VALUE}}'
    assert cmp(period.replace("VALUE", "1"), period.replace("VALUE", "1e0")) == []


def test_t2_1_empty_or_non_numeric_cells_fail():
    # attack 1: equal cadence rows with an empty or n/a fraction, or a bogus count, passed
    parts = json.loads(
        (ROOT / "docs/validation/v0.5.13/l4/comparator-schema-parts.json").read_text("utf-8")
    )
    schema = {**SCHEMA, "report": parts["report"]}
    for line in (
        "| 1 | 18000 | 19000 |  |",
        "| 1 | 18000 | 19000 | n/a |",
        "| 1 | bogus | 19000 | 0.947 |",
        "| 1 |  | 19000 | 0.947 |",
        "| SNR |  | |",
        "| Period (d) |  | n/a |",
        "| 2019 | PASS | bogus | 12.1 | 0.3 |",
    ):
        assert comp.compare_report(line, line, schema), line
    good = "| 1 | 18000 | 19000 | 0.947 |"
    assert comp.compare_report(good, good, schema) == []
    assert comp.compare_report(good, good.replace("18000", "18001"), schema)  # a count, exact
    holdout = "| 2019 | PASS | n/a | 12.1 | 0.3 |"
    assert comp.compare_report(holdout, holdout, schema) == []


def test_t2_2_claim_line_is_compared_whole():
    # attack 2: spaces around the separator changed, and passed
    a = rec({"c.yaml": H1, "d.yaml": "ERROR ClaimError: x"})
    for b in (a.replace('"c.yaml": ', '"c.yaml":  '), a.replace('"c.yaml": ', '"c.yaml" : ')):
        assert json.loads(a) == json.loads(b)
        assert comp.compare_claims(a, b, EXC) == ["claim c.yaml: serialized entry differs"]
    assert comp.compare_claims(a, a, EXC) == []


def test_t2_3_order_pieces_missing_or_out_of_order_fail(tmp_path, monkeypatch):
    # attack 3: a run not proven to follow the freeze, the manifest and the receipt's commit
    freeze = _freeze(tmp_path)
    _nr_a2_records(tmp_path)
    cases = (
        ({"not_ancestor": {("F", "M")}}, "freeze commit is not an ancestor"),
        ({"receipt": False}, "order-proof receipt"),
        ({"not_ancestor": {("R", "h")}}, "does not hold the manifest and its receipt"),
        ({"not_ancestor": {("M", "h")}}, "does not hold the manifest and its receipt"),
        ({"journal": _journal(tmp_path, freeze, utc="2026-11-27T20:40:00Z")}, "push run"),
        ({"journal": _journal(tmp_path, freeze, after_utc="2026-11-27T20:59:00Z")}, "end is"),
        ({"journal": _journal(tmp_path, freeze, after_unit="other")}, "another unit"),
        ({"journal": _journal(tmp_path, freeze, utc=None)}, "time is missing"),
        ({"recorded": "2026-11-27T21:05:00+00:00"}, "before the run's end"),
    )
    for kwargs, expected in cases:
        _git_ok(monkeypatch, tmp_path, freeze, **kwargs)
        problems = _bind(freeze)
        assert any(expected in p for p in problems), (kwargs, problems)


def test_t2_4_code_records_missing_or_divergent_fail(tmp_path, monkeypatch):
    # attack 4: a run with local changes, or at another head, or without the code records
    freeze = _freeze(tmp_path)
    cases = (
        ({"code_check": {}}, {}, "no code check before"),
        ({"code_check": {"before": _check(), "after": _check(head="x")}}, {}, "run's head"),
        ({"code_check": {"before": _check(porcelain=" M src/a.py\n"), "after": _check()}}, {},
         "not clean"),
        ({"code_check": {"before": _check(digest={}), "after": _check()}}, {}, "digest before"),
        ({"code_check": {"before": _check(authorized_commit="x"), "after": _check()}}, {},
         "another authorized commit"),
        ({"code_check": {"before": _check(same_code_as_authorized=False), "after": _check()}},
         {}, "not the authorized code"),
        ({}, {"same": False}, "run head is not the authorized code"),
        ({}, {"digest": {"src_tree": "other"}}, "run head is not the frozen digest"),
    )  # fmt: skip
    for record_kw, git_kw, expected in cases:
        _nr_a2_records(tmp_path, **record_kw)
        _git_ok(monkeypatch, tmp_path, freeze, **git_kw)
        problems = _bind(freeze)
        assert any(expected in p for p in problems), (record_kw, git_kw, problems)


def test_t2_4_the_executor_refuses_other_code():
    spec = importlib.util.spec_from_file_location(
        "v0513_identity_v2", ROOT / "docs/validation/v0.5.13/tools/identity_v2.py"
    )
    ident = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ident)
    ok = {"same_code_as_authorized": True, "porcelain": "", "digest": dict(DIGEST)}
    ident.require(ok, dict(DIGEST), "before")
    import pytest

    for bad in ({"same_code_as_authorized": False}, {"porcelain": "?? x"}, {"digest": {}}):
        with pytest.raises(SystemExit):
            ident.require({**ok, **bad}, dict(DIGEST), "before")


def test_round_2_report_and_json_forms():
    rep = comp.compare_report
    parts = json.loads(
        (ROOT / "docs/validation/v0.5.13/l4/comparator-schema-parts.json").read_text("utf-8")
    )
    schema = {**SCHEMA, "report": parts["report"]}
    # a malformed cell in a row recognized by its structure fails, even when equal
    assert rep("| 1 | 18000 | 19000 | bogus |", "| 1 | 18000 | 19000 | bogus |", schema)
    assert rep("| 1 | 18000 | 19000 | 0.947 |", "| 1 | 18000 | 19000 | 0.947 |", schema) == []
    # None only in the error groups the writer may leave absent
    ok = "- Period 3.1234 d (error None) and epoch 2459001.2 BJD_TDB (error None), from: BLS."
    assert rep(ok, ok, schema) == []
    bad = "- Period None d (error None) and epoch 2459001.2 BJD_TDB (error None), from: BLS."
    assert rep(bad, bad, schema)
    # two integer-form tokens are a count (exact); a mixed pair is compared by value
    doc = '{"candidate": {"p": VALUE}}'
    assert jcmp(doc.replace("VALUE", "1"), doc.replace("VALUE", "1e0")) == []
    assert jcmp(doc.replace("VALUE", "1"), doc.replace("VALUE", "2"))


def test_claim_key_escape_is_a_difference():
    a = rec({"c.yaml": H1, "d.yaml": "ERROR ClaimError: x"})
    b = a.replace('"c.yaml"', '"\\u0063.yaml"')
    assert json.loads(a) == json.loads(b)
    assert comp.compare_claims(a, b, EXC) == ["claim c.yaml: serialized entry differs"]


def test_compared_bytes_are_the_checked_bytes(tmp_path):
    # read_folder keeps only bytes whose SHA-256 it checked
    files = {"plan-v1.json": b"{}\n"}
    rec = _record(tmp_path / "f", files)
    data, problems = comp.read_folder(tmp_path / "f", rec["payload"]["files_sha256"])
    assert problems == [] and data == files
    (tmp_path / "f" / "plan-v1.json").write_bytes(b"{} \n")
    data, problems = comp.read_folder(tmp_path / "f", rec["payload"]["files_sha256"])
    assert problems and data == {}
