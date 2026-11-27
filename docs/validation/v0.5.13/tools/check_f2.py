"""The deterministic checks of the maintainer's decision F2 (#218 comment 7218843893), run before
the commit of the index README.

    unit check-f2:  {python} -I -B docs/validation/v0.5.13/tools/check_f2.py <new> <reference>

(``<new>`` and ``<reference>`` are wheel files.)

1. ``readme_unchanged``: README.md in the working tree has the SHA-256 of README.md at ``HEAD``
   (the tip of ``main``).
2. ``links_only``: README-pypi.md differs from README.md only in link targets. Every target that
   ``scripts/md_links.py`` recognizes (Markdown ``](...)`` and HTML ``src``/``href``/``srcset``) is
   masked in both texts, and the masked texts must be equal. Each pair of targets must then be
   equal, or the README.md target must be relative and the README-pypi.md target must be
   ``make_pypi_readme.absolute`` of it.
3. ``up_to_date``: README-pypi.md is what ``make_pypi_readme.render()`` writes.
4. ``wheel_diff``: the new wheel and the reference wheel (0.5.12 as published on TestPyPI) have
   the same entry names. Their entries' bytes differ only in ``*.dist-info/METADATA`` and
   ``*.dist-info/RECORD``.
It writes ``out/check-f2.json`` and exits 0 only if all four hold.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
import make_pypi_readme  # noqa: E402
import md_links  # noqa: E402

MASK = "\x00TARGET\x00"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def masked(text: str) -> tuple[str, list[str]]:
    found: list[str] = []
    fenced = False
    lines = []
    for line in text.split("\n"):
        if md_links._FENCE.match(line):
            fenced = not fenced
            lines.append(line)
            continue
        if fenced:
            lines.append(line)
            continue

        def md(m):
            found.append(m.group(2))
            return m.group(1) + MASK + m.group(3)

        def html(m):
            found.append(m.group(3))
            return m.group(1) + m.group(2) + MASK + m.group(4)

        lines.append(md_links._HTML.sub(html, md_links._MD.sub(md, line)))
    return "\n".join(lines), found


def main() -> int:
    new_whl, ref_whl = Path(sys.argv[1]), Path(sys.argv[2])
    readme = (ROOT / "README.md").read_bytes()
    head = subprocess.run(["git", "show", "HEAD:README.md"], cwd=ROOT, capture_output=True,
                          check=True).stdout  # fmt: skip
    pypi_text = (ROOT / "README-pypi.md").read_text(encoding="utf-8")
    readme_text = readme.decode("utf-8")
    a, ta = masked(readme_text)
    b, tb = masked(pypi_text)
    pairs_ok = len(ta) == len(tb) and all(
        y == x or (md_links.is_relative(x) and y == make_pypi_readme.absolute(x))
        for x, y in zip(ta, tb, strict=False)
    )
    changed = [(x, y) for x, y in zip(ta, tb, strict=False) if x != y]
    with zipfile.ZipFile(new_whl) as zn, zipfile.ZipFile(ref_whl) as zr:
        names_n, names_r = sorted(zn.namelist()), sorted(zr.namelist())
        differing = [n for n in names_n if n in names_r and zn.read(n) != zr.read(n)]
    allowed = [n for n in differing if n.endswith((".dist-info/METADATA", ".dist-info/RECORD"))]
    result = {
        "readme_unchanged": {
            "ok": sha(readme) == sha(head),
            "readme_sha256": sha(readme),
            "head_sha256": sha(head),
        },
        "links_only": {
            "ok": a == b and pairs_ok,
            "masked_texts_equal": a == b,
            "targets": len(ta),
            "changed_targets": len(changed),
            "changed": changed,
        },
        "up_to_date": {"ok": pypi_text == make_pypi_readme.render()},
        "wheel_diff": {
            "ok": names_n == names_r and differing == allowed and len(allowed) == 2,
            "new": {"file": new_whl.name, "sha256": sha(new_whl.read_bytes())},
            "reference": {"file": ref_whl.name, "sha256": sha(ref_whl.read_bytes())},
            "same_entry_names": names_n == names_r,
            "entries": len(names_n),
            "differing_entries": differing,
        },
    }
    result["all_ok"] = all(v["ok"] for v in result.values() if isinstance(v, dict))
    out = Path(os.environ.get("REFUTE_RUN_OUT", "."))
    text = json.dumps(result, indent=1) + "\n"
    (out / "check-f2.json").write_text(text, encoding="utf-8", newline="\n")
    print(json.dumps({k: (v["ok"] if isinstance(v, dict) else v) for k, v in result.items()}))
    return 0 if result["all_ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
