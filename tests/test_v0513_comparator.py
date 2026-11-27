"""The comparator of v0.5.13's amendment 2, revision 6, section 3.1, on synthetic tokens only.

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


def test_float_form_and_integer_form_do_not_mix():
    assert jcmp(verdict("2.0"), verdict("2"))


def test_report_templates():
    rep = comp.compare_report
    assert rep("| SNR | 12.3456 | |", "| SNR | 12.3456 | |", SCHEMA) == []
    assert rep("| SNR | 1.0000000 | |", "| SNR | 1.0000001 | |", SCHEMA) == []
    assert rep("| SNR | 12.35 | |", "| SNR | 12.34 | |", SCHEMA)
    assert rep("| SNR | 1.2e+05 | |", "| SNR | 120000.0 | |", SCHEMA)
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


def test_claims():
    a = {"payload": {"claims": {"c.yaml": "ab", "d.yaml": "ERROR ClaimError: x"}}}
    assert comp.compare_claims(a, json.loads(json.dumps(a))) == []
    b = {"payload": {"claims": {"c.yaml": "ab", "d.yaml": "ERROR ClaimError: y"}}}
    assert comp.compare_claims(a, b)
    assert comp.compare_claims(a, {"payload": {"claims": {"c.yaml": "ab"}}})
