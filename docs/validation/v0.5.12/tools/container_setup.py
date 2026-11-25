"""Prepare v0.5.12's offline AppContainer (charter, step 0; #218 comment 7173638284, item 3).

    bootstrap-v0512 payload: {python} -I -B docs/validation/v0.5.12/tools/container_setup.py

It does, and records in ``docs/validation/v0.5.12/container.json``:
1. **The profile** ``refute.v0512.offline``, with no capability: the one change outside the project
   (an HKCU registry mapping and a folder under the local application-data ``Packages``), authorized
   by the maintainer. Its removal is the maintainer's (v0.5.10's ``delete_profile.py`` pattern); the
   session never removes it.
2. **Local copies inside the project,** because an AppContainer reads only files whose ACL grants
   it, and the installs outside the project do not (no ACL is changed outside the project):
   - the base CPython 3.13.16 that ``.venv`` uses, copied to ``.cache/v0512/cpy``, every file's
     SHA-256 checked against its source; a ``.pth`` file in its ``site-packages`` adds the project's
     ``.venv`` site-packages (the same packages, the same ``refute`` editable install), and
     ``ruff.exe`` is copied from ``.venv/Scripts`` into its ``Scripts``;
   - Git's ``mingw64/bin`` (git.exe and its libraries), copied to ``.cache/v0512/git``;
   - a private git configuration (user name and email, ``core.autocrlf``, the repository as a safe
     directory), read from the current effective configuration.

   These are copies of programs already in use, from the local disk: nothing is downloaded.
3. **The grants,** inside the project only, to the container's SID: read and execute on the
   project folder (inherited), and modify on ``.git``, ``.cache/v0512`` and ``.ruff_cache``.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import jobrun  # noqa: E402

ROOT = HERE.parents[3]
WORK = ROOT / ".cache" / "v0512"
NAME = "refute.v0512.offline"
BASE_SRC = Path("C:/uv/python/cpython-3.13.16-windows-x86_64-none")
GIT_SRC = Path("C:/Program Files/Git/mingw64/bin")
OUT = HERE.parent / "container.json"


def sha(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def inside(p: Path) -> Path:
    p = p.resolve()
    if p != ROOT and ROOT not in p.parents:
        raise SystemExit(f"refused: {p} is outside the project")
    return p


def copy_checked(src: Path, dst: Path) -> dict:
    dst = inside(dst)
    if dst.exists():
        raise SystemExit(f"refused: {dst} exists already")
    shutil.copytree(src, dst)
    n = size = 0
    for f in src.rglob("*"):
        if f.is_file():
            g = dst / f.relative_to(src)
            if sha(f) != sha(g):
                raise SystemExit(f"refused: the copy of {f.name} does not match")
            n += 1
            size += f.stat().st_size
    return {"files": n, "bytes": size, "all_match": True}


def git_config(key: str) -> str | None:
    out = subprocess.run(["git", "config", "--get", key], cwd=ROOT, capture_output=True, text=True)
    return out.stdout.strip() or None


def icacls(path: Path, sid: str, right: str) -> None:
    subprocess.run(
        ["icacls", str(inside(path)), "/grant", f"*{sid}:{right}", "/C", "/Q"],
        check=True,
        capture_output=True,
    )


def main() -> int:
    t0 = time.time()
    profile = jobrun.ensure_profile(
        NAME,
        "Refute v0.5.12 offline units",
        "Refute v0.5.12: units with no network capability (charter, step 0)",
    )
    _, sid = jobrun.container_sid(NAME)
    WORK.mkdir(parents=True, exist_ok=True)
    cpy = WORK / "cpy"
    base = copy_checked(BASE_SRC, cpy)
    site = cpy / "Lib" / "site-packages"
    site.mkdir(parents=True, exist_ok=True)
    venv_site = ROOT / ".venv" / "Lib" / "site-packages"
    (site / "_refute_venv.pth").write_text(
        f"import site; site.addsitedir({str(venv_site)!r})\n", encoding="utf-8"
    )
    (cpy / "Scripts").mkdir(exist_ok=True)
    shutil.copyfile(ROOT / ".venv" / "Scripts" / "ruff.exe", cpy / "Scripts" / "ruff.exe")
    git_copy = copy_checked(GIT_SRC, WORK / "git" / "mingw64" / "bin")
    cfg = {
        "user.name": git_config("user.name"),
        "user.email": git_config("user.email"),
        "core.autocrlf": git_config("core.autocrlf"),
    }
    lines = []
    for key, value in cfg.items():
        if value is not None:
            section, name = key.split(".")
            lines.append(f"[{section}]\n\t{name} = {value}\n")
    lines.append(f"[safe]\n\tdirectory = {ROOT.as_posix()}\n")
    (WORK / "gitconfig").write_text("".join(lines), encoding="utf-8")
    t1 = time.time()
    icacls(ROOT, sid, "(OI)(CI)(RX)")
    for rel in (".git", ".cache/v0512", ".ruff_cache"):
        (ROOT / rel).mkdir(exist_ok=True)
        icacls(ROOT / rel, sid, "(OI)(CI)(M)")
    doc = {
        "schema": "refute-v0512-container-1",
        "decision": "#218 comment 7173638284, item 3",
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "appcontainer": {
            "name": NAME,
            "sid": sid,
            "capabilities": [],
            "profile": profile,
            "created_outside_the_project": [
                "HKCU registry key: Software/Classes/Local Settings/Software/Microsoft/Windows/"
                "CurrentVersion/AppContainer/Mappings/" + sid,
                "folder: <local application-data folder>/Packages/" + NAME,
            ],
            "removal": "the maintainer's (v0.5.10's delete_profile.py pattern); the session never "
            "removes it",
        },
        "copies": {
            ".cache/v0512/cpy": {"source": "the base CPython 3.13.16 of .venv", **base},
            ".cache/v0512/git/mingw64/bin": {"source": "Git for Windows, mingw64/bin", **git_copy},
            "python_exe_sha256": sha(cpy / "python.exe"),
            "ruff_exe_sha256": sha(cpy / "Scripts" / "ruff.exe"),
        },
        "git_config_keys": [k for k, v in cfg.items() if v is not None],
        "grants": {
            "read_execute_inherited": ["."],
            "modify_inherited": [".git", ".cache/v0512", ".ruff_cache"],
        },
        "seconds": {"copies": round(t1 - t0, 1), "grants": round(time.time() - t1, 1)},
    }
    OUT.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"profile": profile, "sid": sid, "seconds": doc["seconds"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
