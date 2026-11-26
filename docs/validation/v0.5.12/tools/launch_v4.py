"""The metered launcher of v0.5.12, version 4: the ledger's stale ``downloads_rule`` text corrected.

    .venv/Scripts/python.exe -I -B docs/validation/v0.5.12/tools/launch_v4.py <unit spec>
        [--label L] [--approval URL] [-- extra arguments]

Asked by the maintainer's decision recorded in #218, comment 7202383280, item 2 (the gate's finding
10 and Codex's minor). It runs ``launch_v3.py`` unchanged (rule (c): a new file, not a revision),
with two changes, neither of which touches how a unit runs or how it is metered:
- after ``launch_v1.write_ledger`` writes ``caps-ledger.json``, its ``downloads_rule`` text is
  replaced by :data:`DOWNLOADS_RULE`, which says how units ran since charter amendment 1;
- every ``before`` entry also names this launcher and carries its SHA-256.
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent

DOWNLOADS_RULE = (
    "until charter amendment 1, every offline unit ran in the AppContainer with no capability; "
    "from amendment 1 (bb6292c, approved in #218 comment 7193450494; launch_v3.py) every unit "
    "without network runs outside the AppContainer, in the launcher's job object, with no network "
    "block across its process tree (a declared limit of exit criterion 6); only units declaring "
    "GitHub or review traffic are meant to use the network, with their operations journaled; "
    "downloads are declared, not blocked"
)


def _load(name: str):
    spec = importlib.util.spec_from_file_location(name, _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


v3 = _load("launch_v3")
v1 = v3.v1


def main() -> int:
    me = Path(__file__).resolve().relative_to(v1.ROOT).as_posix()
    my_sha = v1.committed_sha256(me)
    original_write = v1.write_ledger

    def write_ledger(entries: list[dict]) -> None:
        original_write(entries)
        doc = json.loads(v1.LEDGER.read_text(encoding="utf-8"))
        doc["downloads_rule"] = DOWNLOADS_RULE
        v1.LEDGER.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")

    v1.write_ledger = write_ledger
    inner = v1.append_log

    def tagged(entry: dict) -> None:
        if entry.get("event") == "before":
            entry = dict(entry)
            entry["launcher"] = "launch_v4.py"
            entry["identity_sha256"] = {me: my_sha, **entry.get("identity_sha256", {})}
        inner(entry)

    v1.append_log = tagged
    return v3.main()


if __name__ == "__main__":
    sys.exit(main())
