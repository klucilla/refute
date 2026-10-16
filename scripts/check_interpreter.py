"""Check the interpreter that runs this script: CPython, its exact version, and a base
installation inside the uv Python install directory (a uv-managed build; WP0,
docs/validation/v0.3/wp0-acceptance.md, sections 3.4 and 3.5).

Usage: python scripts/check_interpreter.py <expected version> [<uv python install dir>]

The install directory defaults to the UV_PYTHON_INSTALL_DIR environment variable (set by
setup-uv in CI). The script prints the implementation, the version, ``sys.executable``,
``sys.base_prefix`` and the install directory, and exits 1 when the implementation is not
CPython, the version is not exactly the expected one, or the base installation is not
inside the install directory.

What it shows, and what it does not: the location of the base installation (symlinks
and junctions resolved) and the version the process reports. It does not authenticate the
build: any CPython of the same version placed under that directory passes. Which build uv
installs is fixed by the pinned uv version (section 3.5).
"""

from __future__ import annotations

import os
import platform
import sys


def _norm(path: str) -> str:
    return os.path.normcase(os.path.realpath(path))


def problems(
    version: str,
    base_prefix: str,
    install_dir: str,
    expected: str,
    implementation: str = "CPython",
) -> list[str]:
    """What is wrong with this interpreter, empty when it is the expected uv-managed one."""
    out = []
    if implementation != "CPython":
        out.append(f"implementation {implementation}, expected CPython")
    if version != expected:
        out.append(f"version {version}, expected exactly {expected}")
    if not install_dir:
        out.append("no uv Python install directory given (UV_PYTHON_INSTALL_DIR)")
        return out
    base, root = _norm(base_prefix), _norm(install_dir)
    try:
        inside = base != root and os.path.commonpath([base, root]) == root
    except ValueError:  # different drives on Windows
        inside = False
    if not inside:
        out.append(f"base installation {base_prefix} is not inside {install_dir}")
    return out


def main(argv: list[str]) -> int:
    if len(argv) not in (1, 2):
        print(__doc__)
        return 2
    expected = argv[0]
    install_dir = argv[1] if len(argv) == 2 else os.environ.get("UV_PYTHON_INSTALL_DIR", "")
    implementation = platform.python_implementation()
    version = platform.python_version()
    print(f"implementation={implementation}")
    print(f"version={version}")
    print(f"executable={sys.executable}")
    print(f"base_prefix={sys.base_prefix}")
    print(f"uv_python_install_dir={install_dir}")
    found = problems(version, sys.base_prefix, install_dir, expected, implementation)
    for p in found:
        print(f"FAIL: {p}")
    if not found:
        print(f"OK: CPython {expected}, base installation inside the uv Python install directory")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
