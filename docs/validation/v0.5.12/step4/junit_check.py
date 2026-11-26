"""v0.5.12: the checker of the decisive JUnit file of the src/ change (the charter, section 5 (e)
and criterion 2; Codex's review of all the phase's commits, "before sealing").

    launch_v3 unit junit-check: {python} -I -B docs/validation/v0.5.12/step4/junit_check.py

- ``step4/junit-after-src.xml``: the three suites (#223's, correction 2's and
  ``test_v0511_screen.py``) on the working tree whose diff was the approved patch, committed at
  ``6f83a91``.
- ``step2/junit-suites-before-src.xml``: the two new suites on the approval code (10 strict xfails).

The check: the after file has 0 failures, 0 errors, 0 skipped (no xfail), every test case passed,
and every test ID of the before file is present in it and passed. It writes
``junit-after-src-summary.json`` (the files' SHA-256, the counts and the IDs), copied to
``step4/``, and exits 1 otherwise.
"""

from __future__ import annotations

import hashlib
import json
import os
import xml.etree.ElementTree as ET
from pathlib import Path

HERE = Path(__file__).resolve().parent
AFTER = HERE / "junit-after-src.xml"
BEFORE = HERE.parent / "step2" / "junit-suites-before-src.xml"


def cases(path: Path) -> dict[str, str]:
    root = ET.parse(path).getroot()
    out = {}
    for tc in root.iter("testcase"):
        key = f"{tc.get('classname')}::{tc.get('name')}"
        kids = [c.tag for c in tc]
        out[key] = next((k for k in ("failure", "error", "skipped") if k in kids), "passed")
    return out


def main() -> int:
    root = ET.parse(AFTER).getroot()
    suite = root if root.tag == "testsuite" else root.find("testsuite")
    counts = {k: int(suite.get(k)) for k in ("tests", "failures", "errors", "skipped")}
    after, before = cases(AFTER), cases(BEFORE)
    missing = sorted(set(before) - set(after))
    not_passed = sorted(k for k, v in after.items() if v != "passed")
    ok = (
        counts["failures"] == counts["errors"] == counts["skipped"] == 0
        and counts["tests"] == len(after)
        and not missing
        and not not_passed
    )
    doc = {
        "schema": "refute-v0512-junit-check-1",
        "after": {"path": "step4/junit-after-src.xml", "sha256": _sha(AFTER), "counts": counts},
        "before": {"path": "step2/junit-suites-before-src.xml", "sha256": _sha(BEFORE)},
        "before_ids_present_and_passed": not missing,
        "missing_before_ids": missing,
        "not_passed": not_passed,
        "ids": sorted(after),
        "passed": ok,
    }
    out = Path(os.environ["REFUTE_RUN_OUT"]) / "junit-after-src-summary.json"
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"passed": ok, "counts": counts, "before_ids": len(before)}))
    return 0 if ok else 1


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == "__main__":
    raise SystemExit(main())
