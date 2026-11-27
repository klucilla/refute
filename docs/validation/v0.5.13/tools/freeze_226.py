"""The freeze commit of amendment 2, revision 8, section 4, for #226 (the maintainer's decision
R3(a), #218 comment 7226818333). From source and records only: it opens no golden file and runs
no comparator.

    unit freeze-226:  {python} -I -B docs/validation/v0.5.13/tools/freeze_226.py <out folder> \
        <NR-A2 manifest draft>

**Under decision S3** (#218 comment 7227283917) the freeze list also holds ``prospective``: the
entry that binds NR-A2, which runs after the freeze. It names the path where NR-A2's manifest will
be committed (alone, with its order proof) and the SHA-256 of the draft given as the second
argument, which that commit must carry byte for byte; the paths of NR-A2's two records; the
SHA-256 of ``tools/identity_v2.py``, which must write them; and the two-thread setting.

Under revision 8, section 4 (blind review 3, item 1), the freeze of versions 1 to 4 holds: the
fixture list, the source commits and code digests, the resolved plans, the SHA-256 of each golden
file of ID-BEFORE and of NR-A1's three settings, and the comparator with its schema and span
mapping. There is no margin manifest for versions 1 to 4.

It reads the records of ID-BEFORE and NR-A1 (``step0/golden-before.json``,
``step1/golden-nr-a1-*.json``) and their claim-hash records, ``l4/comparator-schema-parts.json``
(the json patterns, the report templates and the fields of decision P2) and ``l4/schema-keys.json``
(the exact keys and exact subtree keys). It writes:

- ``comparator-schema.json``: the comparator's schema and span mapping, built from those two files
  in the same way as the schema of the freeze made under revision 6 (``tools/manifest.py``);
- ``freeze.json``, each item with its SHA-256:
  - the fixture list, from ID-BEFORE's recorded inventory;
  - for each setting: its golden record and claim-hash record; the source commit its golden record
    names (``provenance.head``); the git tree of ``src`` and the SHA-256 of
    ``tests/baseline_code_v0511.py`` at that commit (the code digests); the recorded SHA-256 of
    every golden file, taken from the record, never by reading the files; the resolved plans (the
    ``plan-*`` files among them); the recorded error outputs;
  - the comparator (``tools/comparator.py``), the schema and the files it is built from;
  - revision 8 itself.
It fails if the four settings do not record the same inventory.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
V = "docs/validation/v0.5.13"
L4 = f"{V}/l4"
RECORDS = {
    "id-before": f"{V}/step0/golden-before.json",
    "nr-a1-default": f"{V}/step1/golden-nr-a1-default.json",
    "nr-a1-t1": f"{V}/step1/golden-nr-a1-t1.json",
    "nr-a1-t4": f"{V}/step1/golden-nr-a1-t4.json",
}
CLAIM_RECORDS = {
    "id-before": f"{V}/step0/claim-hashes-before.json",
    "nr-a1-default": f"{V}/step1/claim-hashes-nr-a1-default.json",
    "nr-a1-t1": f"{V}/step1/claim-hashes-nr-a1-t1.json",
    "nr-a1-t4": f"{V}/step1/claim-hashes-nr-a1-t4.json",
}
COMPARATOR = f"{V}/tools/comparator.py"
FIXTURE_CODE = "tests/baseline_code_v0511.py"
REVISION = "docs/plans/v0.5.13-charter-amendment-2-rev8.md"
LABELS = ["exploratory", "method_status: not_validated"]
NR_A2_MANIFEST = f"{V}/manifests/nr-a2.json"
IDENTITY_V2 = f"{V}/tools/identity_v2.py"
THREAD_VARS = ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS")


def load(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(*args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True).stdout


def file_item(rel: str) -> dict:
    return {"path": rel, "sha256": sha((ROOT / rel).read_bytes())}


def main() -> int:
    out_rel = Path(sys.argv[1]).as_posix()
    out = ROOT / out_rel
    keys = load(f"{L4}/schema-keys.json")
    parts = load(f"{L4}/comparator-schema-parts.json")
    schema = {
        "labels": LABELS,
        "json": parts["json"],
        "report": parts["report"],
        "exact_keys": keys["exact_keys"],
        "exact_subtree_keys": keys["exact_subtree_keys"],
        "exact_key_regex": parts.get("exact_key_regex"),
        "computed_keys_despite_name": parts.get("computed_keys_despite_name", {}),
        "exact_key_exempt_paths": parts.get("exact_key_exempt_paths", []),
        "exact_by_sibling": parts.get("exact_by_sibling", []),
        "message_lines": parts.get("message_lines", {}),
        "claim_exceptions": parts.get("claim_exceptions", {}),
    }
    schema_text = json.dumps(schema, indent=1) + "\n"

    settings, inventories = {}, set()
    for label, rel in RECORDS.items():
        rec = load(rel)
        head = rec["provenance"]["head"]
        files = rec["payload"]["files_sha256"]
        inventories.add(tuple(sorted(files)))
        settings[label] = {
            "record": rel,
            "record_sha256": sha((ROOT / rel).read_bytes()),
            "claim_record": CLAIM_RECORDS[label],
            "claim_record_sha256": sha((ROOT / CLAIM_RECORDS[label]).read_bytes()),
            "source_commit": head,
            "src_tree": git("rev-parse", f"{head}:src").decode().strip(),
            "fixture_code_sha256": sha(git("show", f"{head}:{FIXTURE_CODE}")),
            "files_sha256": files,
            "resolved_plans_sha256": {n: d for n, d in files.items() if n.startswith("plan-")},
            "error_outputs": rec["payload"]["error_outputs"],
        }
    if len(inventories) != 1:
        print(json.dumps({"result": "FAIL", "problem": "the recorded inventories differ"}))
        return 1
    names = sorted(next(iter(inventories)))
    versions = sorted(n[len("plan-") : -len(".json")] for n in names if n.startswith("plan-"))
    fixtures = sorted(versions + [f"chain-{v}" for v in versions])

    freeze = {
        "labels": LABELS,
        "rule": "amendment 2, revision 8, section 4 (blind review 3, item 1): the freeze commit of "
        "section 4; for versions 1 to 4 there is no margin manifest and no margin check",
        "revision": file_item(REVISION),
        "fixtures": fixtures,
        "golden_files": names,
        "settings": settings,
        "fixture_code": FIXTURE_CODE,
        "comparator": file_item(COMPARATOR),
        "schema": {"path": f"{out_rel}/comparator-schema.json",
                   "sha256": sha(schema_text.encode("utf-8")),
                   "span_mapping": "the schema's json measurement and exact patterns, exact keys, "
                   "exact subtree keys, exact key regex, computed keys despite their name, "
                   "exact-key exempt paths, exact by sibling, message lines, and report "
                   "templates",
                   "built_from": [file_item(f"{L4}/comparator-schema-parts.json"),
                                  file_item(f"{L4}/schema-keys.json")]},
        "margin_manifest": None,
        # decision S3: NR-A2 runs after this freeze; its records are bound to this entry
        "prospective": {
            "nr-a2-t2": {
                "manifest": {"path": NR_A2_MANIFEST,
                             "sha256": sha((ROOT / sys.argv[2]).read_bytes()),
                             "draft": Path(sys.argv[2]).as_posix()},
                "record": f"{V}/step1/golden-nr-a2-t2.json",
                "claim_record": f"{V}/step1/claim-hashes-nr-a2-t2.json",
                "script": IDENTITY_V2,
                "script_sha256": sha((ROOT / IDENTITY_V2).read_bytes()),
                "thread_env": {v: "2" for v in THREAD_VARS},
                "threads": 2,
            }
        },
    }  # fmt: skip
    out.mkdir(parents=True, exist_ok=True)
    (out / "comparator-schema.json").write_text(schema_text, encoding="utf-8", newline="\n")
    freeze_text = json.dumps(freeze, indent=1) + "\n"
    (out / "freeze.json").write_text(freeze_text, encoding="utf-8", newline="\n")
    print(json.dumps({
        "result": "PASS",
        "fixtures": fixtures,
        "golden_files": len(names),
        "settings": sorted(settings),
        "freeze_sha256": sha(freeze_text.encode("utf-8")),
        "schema_sha256": freeze["schema"]["sha256"],
        "comparator_sha256": freeze["comparator"]["sha256"],
        "revision_sha256": freeze["revision"]["sha256"],
        "nr_a2_manifest_sha256": freeze["prospective"]["nr-a2-t2"]["manifest"]["sha256"],
        "identity_v2_sha256": freeze["prospective"]["nr-a2-t2"]["script_sha256"],
        "report_templates": len(schema["report"]),
    }, indent=1))  # fmt: skip
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
