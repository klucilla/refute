"""Write exact, applicable patches for a proposed change that is NOT applied (v0.5.13, amendment 2,
item D1b of #218 comment 7207651312: "prepare the EXACT diff, without commit").

    unit make-patch:  {python} -I -B docs/validation/v0.5.13/tools/make_patch.py <mode> ...

- ``file <repo path> <proposed file> <output patch>``: a git-style unified diff from the
  committed file at HEAD (``/dev/null`` if it does not exist) to the proposed file, with headers
  ``a/<repo path>`` and ``b/<repo path>``, so that ``git apply`` applies it at the repository root.
- ``lock <output patch>``: the dependency proposal. It copies HEAD's ``pyproject.toml`` and
  ``uv.lock`` into ``.cache/v0513/d1b2/lockcopy/``, inserts the runtime extra
  ``[project.optional-dependencies] blas-pin = ["threadpoolctl==3.7.0"]`` after the
  ``dependencies`` block, runs ``uv lock --offline`` there, and writes the patch of both files.
  Nothing in the repository's own files changes.
It prints each patch's SHA-256 and line counts.
"""

from __future__ import annotations

import difflib
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EXTRA = '\n[project.optional-dependencies]\nblas-pin = ["threadpoolctl==3.7.0"]\n'


def head_text(rel: str) -> str | None:
    p = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True)
    return p.stdout.decode("utf-8") if p.returncode == 0 else None


def file_patch(rel: str, old: str | None, new: str) -> str:
    a = (old or "").splitlines(True)
    b = new.splitlines(True)
    src = f"a/{rel}" if old is not None else "/dev/null"
    lines = list(difflib.unified_diff(a, b, src, f"b/{rel}"))
    if not lines:
        return ""
    head = f"diff --git a/{rel} b/{rel}\n"
    if old is None:
        head += "new file mode 100644\n"
    return head + "".join(lines)


def write(out: Path, text: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(text.encode("utf-8"))
    print(f"{out.relative_to(ROOT).as_posix()}: {text.count(chr(10))} lines, "
          f"sha256 {hashlib.sha256(text.encode('utf-8')).hexdigest()}")  # fmt: skip


def main() -> int:
    mode = sys.argv[1]
    if mode == "file":
        rel, proposed, out = sys.argv[2], ROOT / sys.argv[3], ROOT / sys.argv[4]
        write(out, file_patch(rel, head_text(rel), proposed.read_text(encoding="utf-8")))
        return 0
    if mode == "lock":
        out = ROOT / sys.argv[2]
        work = ROOT / ".cache" / "v0513" / "d1b2" / "lockcopy"
        if work.exists():
            shutil.rmtree(work)
        work.mkdir(parents=True)
        py_old, lock_old = head_text("pyproject.toml"), head_text("uv.lock")
        marker = '  "pydantic>=2.6",\n]\n'
        if marker not in py_old:
            raise SystemExit("the dependencies block was not found")
        py_new = py_old.replace(marker, marker + EXTRA, 1)
        (work / "pyproject.toml").write_text(py_new, encoding="utf-8", newline="\n")
        (work / "uv.lock").write_text(lock_old, encoding="utf-8", newline="\n")
        p = subprocess.run(["uv", "lock", "--offline", "--directory", str(work)],
                           capture_output=True, text=True)  # fmt: skip
        print(p.stderr.strip())
        if p.returncode != 0:
            return p.returncode
        lock_new = (work / "uv.lock").read_text(encoding="utf-8")
        text = file_patch("pyproject.toml", py_old, py_new) + file_patch(
            "uv.lock", lock_old, lock_new
        )
        write(out, text)
        return 0
    raise SystemExit("mode must be file or lock")


if __name__ == "__main__":
    raise SystemExit(main())
