"""For exit criterion 2: list the test_host_readers_count cases of both JUnit files (v0.4.0 and
end) whose parameter ID holds zip bytes, with outcomes, to see whether the two 'missing' IDs
are the same cases under an ID that changes between runs."""

import xml.etree.ElementTree as ET

for label, path in (
    ("v040", ".cache/v05/crit2/junit-v040.xml"),
    ("end", ".cache/v05/crit2/junit-end.xml"),
):
    cases = []
    for case in ET.parse(path).getroot().iter("testcase"):
        name = case.get("name", "")
        if name.startswith("test_host_readers_count[") and "PK" in name:
            outcome = (
                "failed"
                if {c.tag for c in case} & {"failure", "error"}
                else ("skipped" if any(c.tag == "skipped" for c in case) else "passed")
            )
            tail = name[name.rfind("-reader:") :]
            cases.append((tail, outcome, ascii(name[24:60])))
    print(label, len(cases))
    for c in sorted(cases):
        print("  ", c)
