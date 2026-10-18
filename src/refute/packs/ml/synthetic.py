"""Synthetic fixtures: the only code the ``subprocess`` backend runs (WP3 W3.8; item E of
the maintainer's review of 2026-10-16, design A'; closes the gap of #87).

The ``subprocess`` backend is not an isolation boundary, so it must never run the code of
a real paper. No mark inside a repository can show that it is synthetic: a folder name, a
sentinel file or a manifest can be copied. The authorization therefore comes from the
harness, never from a claim, a repository or a path:

- ``CATALOG``: a closed, read-only catalog of fixtures, in Refute's code. Each fixture
  names its code files with their SHA-256, the data files the harness may add (by exact
  path) and the folders its runs may write to. A claim or a repository can neither choose
  an entry nor extend the list; changing a fixture means changing this file, in a
  reviewed commit.
- ``materialize``: the harness writes one fixture into a new, empty folder: every code
  file with exactly the bytes of the catalog, and only the data files the catalog names.
  It returns an ``Authorization`` bound to that folder and to the SHA-256 of every file
  written, and records it as issued. Only this function issues one.
- ``check_run``: before a run starts, the backend requires an issued authorization for the
  run's folder, given exactly (no alias), and checks again that every written file is
  unchanged (code files also against the catalog) and has a single link, that nothing
  else is in the folder except under its output folders, that no entry is a symbolic link
  or a junction, that the log is outside the folder, and that the command is this
  interpreter, in isolated mode (``-I``), running a code file of the fixture named by its
  path in the catalog. It returns the command to launch: this interpreter's absolute path
  and the code file's absolute path, never the words given, with an environment built
  from an allowlist (``LAUNCH_ENV_KEYS``), so no variable such as ``LD_PRELOAD`` can load
  code before Python starts. Anything else is refused before any process starts.

**Trust boundary.** The harness and every module of Refute run in one trusted Python
process: code already in it could replace any of these objects, and nothing here defends
against it. What this module guarantees is that nothing a claim or a repository can write
(a YAML field, a file, a path, a command) makes the backend run anything but cataloged
code.

**Limit.** The check runs just before the start; a change made to the folder by another
process between the check and the start is not seen. The fixtures are written and run by
the test harness only, in folders it creates, and no other process writes there.

**The build ladder under this backend (A').** CI cannot build images, so the ladder fixture
plays the build of each rung (``tests/fixtures/ladder/build.py``). Its result counts as an
error of the procedure (``artifact_build_ladder``) only for the deliberate failure the
harness declared before the run (``BuildExpectations``), recognised by its exit code and
its exact line in the log (``classify_synthetic_build``); a stop by the threshold or a
guard keeps its own cause, and any other outcome, including an unexpected success, is
``undetermined`` (``INCONCLUSIVE``). This tests the existing rules of the ladder; it
creates no general rule that blames an artifact. Docker, the resolution of dependencies
and a real change of the Python version are not shown by this emulation.
"""

from __future__ import annotations

import hashlib
import os
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from types import MappingProxyType

from refute.core.paper import FailureCause

DELIBERATE_BUILD_EXIT = 86
DELIBERATE_BUILD_LINE = "synthetic build: deliberate procedure error"
BUILD_EXPECTATIONS = ("ok", "procedure_error")


class SyntheticRefusedError(ValueError):
    """A fixture or a run that the synthetic catalog does not authorize."""


@dataclass(frozen=True)
class Fixture:
    name: str
    code: Mapping[str, str]  # relative POSIX path -> SHA-256 of its exact bytes
    data: frozenset[str] = frozenset()  # relative POSIX paths the harness may add
    outputs: tuple[str, ...] = ()  # folders (relative) the runs may write to

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", MappingProxyType(dict(self.code)))


CATALOG: Mapping[str, Fixture] = MappingProxyType(
    {
        f.name: f
        for f in (
            Fixture(
                "sandbox-probe",
                {"probe.py": "875835e6371220ea5d3fcfed58662225a23df43c22aa278fa6c788db57779425"},
                outputs=("out",),
            ),
            Fixture(
                "ml-paper",
                {
                    "train.py": "5ab4ab5dfed408e1e1f0d03bcec929911320feb513b00c0b1c3d3d7b8bc9a084",
                    # the coverage hook, as an allowed patch would install it (1.5a, route
                    # (b)): the bytes of src/refute/packs/ml/coverage_hook.py
                    "coverage_hook.py": (
                        "a6223fb44452c55e552badbb5e9951bf29037a87ee185844bb9107011efcc69a"
                    ),
                },
                data=frozenset({"config.json", "data/dataset.npz"}),
                outputs=("preds", "refute-hook"),
            ),
            Fixture(
                "ladder-build",
                {"build.py": "f686c16e19e70a85fc63bf17515c2d947382dd8b65c3d22f2fd28d29120bdb1a"},
                data=frozenset({"ladder.json", "Dockerfile", "requirements.txt"}),
                outputs=("out",),
            ),
            Fixture(
                # the container reader (wp3-data-sources-acceptance.md, section 4.2): the
                # bytes of src/refute/packs/ml/container_reader.py, on a test's own file
                "data-reader",
                {"reader.py": "4b64c5edda6bd940aa392d02a193a0e0547f8b4ddc30f5bb96bf879ad41cb733"},
                # a test may also plant modules named like those the reader imports, in its
                # working folder; none of them may run (section 6)
                data=frozenset(
                    {
                        "data/archive.tar.gz",
                        "data/table.xlsx",
                        "data/graph.bin",
                        "json.py",
                        "tarfile.py",
                        "sitecustomize.py",
                    }
                ),
                outputs=("out",),
            ),
        )
    }
)

_TOKEN = object()
_ISSUED: dict[int, Authorization] = {}  # by id: the authorizations materialize issued


@dataclass(frozen=True)
class Authorization:
    """A fixture written by ``materialize``: its folder and the SHA-256 of every file."""

    fixture: Fixture
    root: Path
    manifest: Mapping[str, str]
    _token: object = field(repr=False, compare=False)

    def __post_init__(self) -> None:
        if self._token is not _TOKEN:
            raise SyntheticRefusedError("an authorization is created only by materialize")
        if CATALOG.get(self.fixture.name) is not self.fixture:
            raise SyntheticRefusedError("an authorization names a fixture of the catalog")
        manifest = dict(self.manifest)
        if any(manifest.get(path) != digest for path, digest in self.fixture.code.items()):
            raise SyntheticRefusedError("an authorization holds the cataloged code")
        object.__setattr__(self, "manifest", MappingProxyType(manifest))


def issued(auth: object) -> bool:
    """True for an authorization that ``materialize`` issued (not a copy or a rebuild)."""
    return isinstance(auth, Authorization) and _ISSUED.get(id(auth)) is auth


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _relative(path: str) -> PurePosixPath:
    rel = PurePosixPath(path)
    if rel.is_absolute() or not rel.parts or any(p in ("", ".", "..") for p in rel.parts):
        raise SyntheticRefusedError(f"not a plain relative path: {path!r}")
    if "\\" in path or ":" in path:
        raise SyntheticRefusedError(f"not a plain relative path: {path!r}")
    return rel


def materialize(
    name: str, root: Path, code: Mapping[str, bytes], data: Mapping[str, bytes] | None = None
) -> Authorization:
    """Writes the fixture ``name`` of the catalog into ``root`` (new or empty) and returns
    its authorization. ``code`` must hold exactly the fixture's code files with their
    cataloged bytes; ``data`` only paths the fixture names."""
    fixture = CATALOG.get(name)
    if fixture is None:
        raise SyntheticRefusedError(f"{name!r} is not a fixture of the synthetic catalog")
    data = dict(data or {})
    if set(code) != set(fixture.code):
        raise SyntheticRefusedError(
            f"fixture {name!r} has the code files {sorted(fixture.code)}, given {sorted(code)}"
        )
    for path, content in code.items():
        if _sha256(content) != fixture.code[path]:
            raise SyntheticRefusedError(f"{path} differs from the cataloged bytes of {name!r}")
    extra = sorted(set(data) - fixture.data)
    if extra:
        raise SyntheticRefusedError(f"data files not allowed in {name!r}: {extra}")
    root = Path(root)
    if root.exists() and (not root.is_dir() or any(root.iterdir())):
        raise SyntheticRefusedError(f"{root} is not a new or empty folder")
    root.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for path, content in sorted({**code, **data}.items()):
        target = root.joinpath(*_relative(path).parts)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
        manifest[path] = _sha256(content)
    auth = Authorization(fixture, root.resolve(), manifest, _TOKEN)
    _ISSUED[id(auth)] = auth
    return auth


def _is_link(path: Path) -> bool:
    return path.is_symlink() or (hasattr(path, "is_junction") and path.is_junction())


def verify_tree(auth: Authorization) -> None:
    """Every written file unchanged (code files also against the catalog) and with a single
    link; no other file except under the output folders; no symbolic link or junction
    anywhere in the folder."""
    root = auth.root
    if _is_link(root) or not root.is_dir():
        raise SyntheticRefusedError(f"{root} is not the fixture's folder")
    seen = set()
    for current, dirs, files in os.walk(root, followlinks=False):
        here = Path(current)
        for name in dirs + files:
            if _is_link(here / name):
                raise SyntheticRefusedError(f"a link in the fixture: {here / name}")
        for name in files:
            path = here / name
            rel = path.relative_to(root).as_posix()
            if rel in auth.manifest:
                seen.add(rel)
                if os.stat(path).st_nlink != 1:
                    raise SyntheticRefusedError(f"{rel} has another link to its data")
                digest = _sha256(path.read_bytes())
                if digest != auth.manifest[rel] or digest != auth.fixture.code.get(rel, digest):
                    raise SyntheticRefusedError(f"{rel} changed since the fixture was written")
            elif not any(rel.startswith(out + "/") for out in auth.fixture.outputs):
                raise SyntheticRefusedError(f"a file the fixture does not hold: {rel}")
    missing = sorted(set(auth.manifest) - seen)
    if missing:
        raise SyntheticRefusedError(f"fixture files missing: {missing}")


def _same_file(a: str, b: str) -> bool:
    try:
        return os.path.samefile(a, b)
    except OSError:
        return False


# The only environment variables a synthetic run receives (Codex review of #109): the
# thread counts of the claim, what Python needs to start on each system, and the
# temporary and home folders. Anything else is dropped, so no variable can select code
# outside the catalog (LD_PRELOAD, LD_LIBRARY_PATH, DYLD_*, PYTHON*, PATH, ...).
LAUNCH_ENV_KEYS = frozenset(
    {
        "OMP_NUM_THREADS",
        "MKL_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "NUMEXPR_NUM_THREADS",
        "SYSTEMROOT",
        "SystemRoot",
        "WINDIR",
        "TEMP",
        "TMP",
        "TMPDIR",
        "HOME",
        "USERPROFILE",
        "LANG",
        "LC_ALL",
    }
)


def launch_env(env: Mapping[str, str]) -> dict[str, str]:
    """The environment a synthetic run is launched with: only ``LAUNCH_ENV_KEYS``."""
    return {k: v for k, v in env.items() if k in LAUNCH_ENV_KEYS}


@dataclass(frozen=True)
class Launch:
    argv: list[str]
    env: dict[str, str]


def check_run(
    argv: Sequence[str],
    workdir: Path,
    env: Mapping[str, str],
    log_paths: Sequence[Path],
    authorizations: Mapping[Path, Authorization],
) -> Launch:
    """The command and environment to launch for a run, or ``SyntheticRefusedError``
    before anything starts. ``argv`` must be ``[<this interpreter>, '-I', <code file as
    cataloged>, *arguments]``, or the same with ``'-S'`` after ``'-I'`` (the container
    reader); the returned command uses this interpreter's absolute path
    and the code file's absolute path, so what was checked is what runs, and the returned
    environment holds only ``LAUNCH_ENV_KEYS``."""
    workdir = Path(workdir)
    if not workdir.is_absolute() or workdir.resolve() != workdir:
        raise SyntheticRefusedError(f"{workdir} must be the fixture's own absolute folder")
    auth = authorizations.get(workdir)
    if auth is None or not issued(auth):
        raise SyntheticRefusedError(
            f"{workdir} is not a synthetic fixture written by the harness: the subprocess "
            "backend runs nothing else"
        )
    for log in log_paths:
        log = Path(log).resolve()
        if log == auth.root or auth.root in log.parents:
            raise SyntheticRefusedError(f"the log {log} must be outside the fixture's folder")
    # isolated mode, and optionally no site processing (the container reader's -I -S,
    # wp3-data-sources-acceptance.md 4.2): no other flag is accepted
    flags = ["-I", "-S"] if list(argv[1:3]) == ["-I", "-S"] else ["-I"]
    n = 1 + len(flags)
    if len(argv) <= n or not _same_file(argv[0], sys.executable) or argv[1] != "-I":
        raise SyntheticRefusedError(
            "a synthetic run is this interpreter in isolated mode running a fixture's code "
            f"file: [{sys.executable!r}, '-I', ('-S',) <file>, ...], got {list(argv[:4])!r}"
        )
    if argv[n] not in auth.fixture.code:
        raise SyntheticRefusedError(
            f"{argv[n]!r} is not a code file of {auth.fixture.name!r} "
            f"({sorted(auth.fixture.code)}, named as in the catalog)"
        )
    verify_tree(auth)
    script = auth.root.joinpath(*_relative(argv[n]).parts)
    return Launch([sys.executable, *flags, str(script), *argv[n + 1 :]], launch_env(env))


# ---- the build ladder under the subprocess backend (A') --------------------------------------


@dataclass(frozen=True)
class BuildExpectations:
    """What the harness declares, before the ladder runs, for each rung of a synthetic
    build: ``ok`` or ``procedure_error`` (the deliberate failure). Read-only."""

    by_rung: Mapping[str, str]

    def __post_init__(self) -> None:
        values = dict(self.by_rung)
        bad = sorted(r for r, v in values.items() if v not in BUILD_EXPECTATIONS)
        if bad:
            raise ValueError(f"expectations are one of {BUILD_EXPECTATIONS}: {bad}")
        object.__setattr__(self, "by_rung", MappingProxyType(values))


def classify_synthetic_build(exit_code, stopped, log_text: str, expected: str):
    """The ``RungResult`` of one synthetic build, from what the harness declared before the
    run (``expected``: ``ok`` or ``procedure_error``) and what the run did. Only the declared
    deliberate failure, with its exit code and its exact line, is an error of the
    procedure."""
    from refute.packs.ml.ladder import RungResult  # the ladder imports orchestrate
    from refute.packs.ml.orchestrate import Outcome
    from refute.packs.ml.sandbox import STOP_ACTIVE_TIME, STOP_NO_PROGRESS, STOP_THRESHOLD

    if expected not in BUILD_EXPECTATIONS:
        raise ValueError(f"expected is one of {BUILD_EXPECTATIONS}")
    if stopped == STOP_THRESHOLD:
        return RungResult(Outcome.BUDGET_EXHAUSTED, None, "threshold reached")
    if stopped in (STOP_ACTIVE_TIME, STOP_NO_PROGRESS):
        return RungResult(Outcome.OPERATIONAL_GUARD, None, stopped)
    if stopped is not None or exit_code is None:
        return RungResult(Outcome.REFUTE_ERROR, None, f"unknown stop: {stopped!r}")
    lines = [line.rstrip("\r") for line in log_text.split("\n")]
    deliberate = exit_code == DELIBERATE_BUILD_EXIT and DELIBERATE_BUILD_LINE in lines
    if expected == "ok" and exit_code == 0:
        return RungResult(Outcome.COMPLETED)
    if expected == "procedure_error" and deliberate:
        return RungResult(Outcome.FAILED, FailureCause.BUILD_LADDER, DELIBERATE_BUILD_LINE)
    return RungResult(
        Outcome.FAILED,
        FailureCause.UNDETERMINED,
        f"unexpected outcome of the synthetic build (exit {exit_code}, expected {expected})",
    )
