"""The container virtual environment's check, after the .pth copy (v0.5.12, step 0; the
maintainer's decision of #218 comment 7176253382, item 2). Run once in the AppContainer with the
cvenv's interpreter (launch_v2).

It passes only if ``sys.prefix`` differs from ``sys.base_prefix``, ``numpy`` and ``ruff``
resolve, and ``refute`` imports from ``C:/Projetos/refute/src``. If ``refute`` fails to import, it
records whether the cause is a denied read inside ``src`` (``src_read_denied``), the one cause
for which the decision pre-approves a grant. The record is ``cvenv-check.json`` in the run's out
folder; the launcher copies it to ``step0/`` on success.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
from pathlib import Path

SRC = Path("C:/Projetos/refute/src").resolve()


def main() -> int:
    doc = {
        "schema": "refute-v0512-cvenv-check-1",
        "decision": "#218 comment 7176253382, item 2",
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "executable": Path(sys.executable).name,
        "prefix_differs": sys.prefix != sys.base_prefix,
        "numpy": importlib.util.find_spec("numpy") is not None,
        "ruff": importlib.util.find_spec("ruff") is not None,
    }
    cause = None
    try:
        import refute

        where = Path(refute.__file__).resolve()
        doc["refute_from_src"] = SRC in where.parents
        shown = where.relative_to(SRC.parent).as_posix() if doc["refute_from_src"] else str(where)
        doc["refute_file"] = shown
    except PermissionError as exc:
        doc["refute_from_src"] = False
        inside = exc.filename and SRC in Path(exc.filename).resolve().parents
        cause = "src_read_denied" if inside else f"PermissionError: {exc.filename}"
    except Exception as exc:  # noqa: BLE001
        doc["refute_from_src"] = False
        cause = f"{type(exc).__name__}: {exc}"
    doc["refute_failure"] = cause
    doc["passed"] = all(doc[k] for k in ("prefix_differs", "numpy", "ruff", "refute_from_src"))
    out = Path(os.environ["REFUTE_RUN_OUT"]) / "cvenv-check.json"
    out.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc))
    return 0 if doc["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
