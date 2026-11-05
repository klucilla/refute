"""The S5 draw of the C3 dossiers for independent review (the maintainer's decision of
2026-11-05, #199; calibration/v0.5/reviews/RULE.md).

Strata, from the committed C3 run (``calibration/v0.5/runs/c3/report.json``, the final
assignment, and ``records.jsonl``): in each class (planet, eb-fp), the final 8 controls split by
their v0.5 verdict without the catalog test (the variant the targets read):
``<class>-inconclusive`` (verdict INCONCLUSIVE) and ``<class>-other`` (any other verdict). One
dossier is drawn from each of the four strata.

Authentication (before any network access): the rule commit given must be the one commit that
added ``RULE.md``; the bytes of ``RULE.md``, this script and the C3 run files read here must be
those of that commit; the executed code (``refute.drand``, ``discover.pilot``) must be the
frozen code, imported from this tree's ``src/`` (``check_executed_code``); the interpreter must
be CPython 3.13.16 (the project's environment), since
``random.shuffle`` is not guaranteed across Python versions.

Randomness: the first drand round published at least 1 hour after the ``created_at`` of the CI
push run (workflow ci.yml, event push, ``head_sha`` the rule commit, run_attempt 1) of the rule
commit (``discover.pilot.push_run_created_at``, which refuses zero or several such runs;
``refute.drand.round_after``); its BLS signature verified (``refute.drand.drand_seed``). Per
stratum: seed = ``int(sha256((randomness_hex + "|v0.5|s5|" + stratum).encode("utf-8"))
.hexdigest(), 16)``; the stratum's controls sorted by TIC ID as an integer, then shuffled
(``refute.drand.shuffled``); the first is drawn.

Attempts: every attempt is written to ``draw-attempts/attempt-NN.json`` (created exclusively);
the first is also ``draw.json``. A later attempt must reproduce the same round and draw, or the
script stops; nothing is overwritten.

Usage, from the repository root:
- ``.venv/Scripts/python.exe calibration/v0.5/reviews/draw.py strata`` (no network);
- ``.venv/Scripts/python.exe calibration/v0.5/reviews/draw.py draw --rule-commit <sha>``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

RUNS = Path("calibration/v0.5/runs")
HERE = Path("calibration/v0.5/reviews")
OUT = HERE / "draw.json"
ATTEMPTS = HERE / "draw-attempts"
DOSSIERS = ".cache/v05/c3/dossiers/c3-dossiers"
CLASSES = {"planet": "planet", "false_positive": "eb-fp"}
LABEL = "|v0.5|s5|"
INTERPRETER = ("CPython", (3, 13, 16))
BOUND = (
    HERE / "RULE.md",
    HERE / "draw.py",
    RUNS / "c3/report.json",
    RUNS / "c3/records.jsonl",
)


class DrawError(RuntimeError):
    pass


def git(root: Path, *args: str) -> bytes:
    return subprocess.run(["git", *args], cwd=root, check=True, capture_output=True).stdout


def strata(root: Path) -> dict[str, list[str]]:
    report = json.loads((root / RUNS / "c3/report.json").read_text(encoding="utf-8"))
    records = {}
    with open(root / RUNS / "c3/records.jsonl", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                record = json.loads(line)
                records[record["target_key"]] = record
    out: dict[str, list[str]] = {}
    for group, name in CLASSES.items():
        final = report["assignment"][group]["final"]
        if len(final) != 8 or len(set(final)) != 8:
            raise DrawError(f"{group}: the final assignment is not 8 distinct controls")
        out[f"{name}-inconclusive"] = []
        out[f"{name}-other"] = []
        for key in final:
            record = records[key]
            if record["status"] != "OK" or record["kind"] != group:
                raise DrawError(f"{key}: not a valid {group} record")
            verdict = record["without_catalog"]["v05"]["verdict"]
            stratum = "inconclusive" if verdict == "INCONCLUSIVE" else "other"
            out[f"{name}-{stratum}"].append(key)
    for stratum, keys in out.items():
        if not keys:
            raise DrawError(f"stratum {stratum} is empty")
    return out


def seed_for(randomness_hex: str, stratum: str) -> int:
    message = (randomness_hex + LABEL + stratum).encode("utf-8")
    return int(hashlib.sha256(message).hexdigest(), 16)


def tic(key: str) -> int:
    return int(key.removeprefix("TIC-"))


def choose(groups: dict[str, list[str]], randomness_hex: str) -> dict[str, Any]:
    from refute.drand import shuffled

    if len(randomness_hex) != 64 or any(c not in "0123456789abcdef" for c in randomness_hex):
        raise DrawError("the randomness must be 64 lowercase hex characters")
    out = {}
    for stratum, keys in sorted(groups.items()):
        order = shuffled(keys, seed_for(randomness_hex, stratum), key=tic)
        out[stratum] = {"order": order, "drawn": order[0], "dossier": f"{DOSSIERS}/{order[0]}"}
    return out


def check_interpreter() -> None:
    found = (platform.python_implementation(), tuple(sys.version_info[:3]))
    if found != INTERPRETER:
        raise DrawError(f"interpreter {found}; the rule requires {INTERPRETER}")


def authenticate(root: Path, rule_commit: str) -> None:
    """The rule commit is the one commit that added RULE.md, and the files read here are its
    bytes."""
    full = git(root, "rev-parse", "--verify", f"{rule_commit}^{{commit}}").decode().strip()
    if full != rule_commit:
        raise DrawError("give the rule commit as its full 40-character SHA")
    added = (
        git(root, "log", "--diff-filter=A", "--format=%H", "--", (HERE / "RULE.md").as_posix())
        .decode()
        .split()
    )
    if added != [rule_commit]:
        raise DrawError(f"the commits that added RULE.md are {added}, not [{rule_commit}]")
    on_main = subprocess.run(
        ["git", "merge-base", "--is-ancestor", rule_commit, "origin/main"], cwd=root
    )
    if on_main.returncode != 0:
        raise DrawError("the rule commit is not on origin/main")
    for path in BOUND:
        committed = git(root, "show", f"{rule_commit}:{path.as_posix()}")
        if (root / path).read_bytes() != committed:
            raise DrawError(f"{path} differs from its bytes at the rule commit")
    check_executed_code(root)


def check_executed_code(root: Path) -> None:
    """The code the draw executes (``refute.drand``, ``discover.pilot`` and what they import) is
    the frozen code: imported from this tree's ``src/``, and the tree's code hash the one frozen
    in ``inputs.json`` with every bound path intact (``calib05.steps.frozen_code``)."""
    import refute.drand
    from refute.packs.tess.calib05 import steps
    from refute.packs.tess.discover import pilot

    src = (root / "src").resolve()
    for module in (refute.drand, pilot, steps):
        if not Path(module.__file__).resolve().is_relative_to(src):
            raise DrawError(f"{module.__name__} is not imported from {src}")
    try:
        steps.frozen_code(root)
    except ValueError as exc:
        raise DrawError(f"the executed code is not the frozen code: {exc}") from exc


def _attempt_path(root: Path) -> Path:
    folder = root / ATTEMPTS
    folder.mkdir(parents=True, exist_ok=True)
    n = 1
    while (folder / f"attempt-{n:02d}.json").exists():
        n += 1
    return folder / f"attempt-{n:02d}.json"


def write_once(path: Path, data: dict[str, Any]) -> None:
    with open(path, "x", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(data, indent=2) + "\n")


def draw(root: Path, rule_commit: str) -> dict[str, Any]:
    from refute.drand import drand_seed, interpreter_record, round_after
    from refute.packs.tess.discover import pilot

    check_interpreter()
    authenticate(root, rule_commit)
    groups = strata(root)
    created = pilot.push_run_created_at(rule_commit)
    number = round_after(created)
    _seed, beacon = drand_seed(number)
    result = {
        "rule": (HERE / "RULE.md").as_posix(),
        "rule_commit": rule_commit,
        "push_run_created_at": created,
        "round": number,
        "beacon": beacon,
        "interpreter": interpreter_record(),
        "strata": groups,
        "draw": choose(groups, beacon["randomness"]),
    }
    attempt = _attempt_path(root)
    write_once(attempt, result)
    first = root / OUT
    if first.exists():
        before = json.loads(first.read_text(encoding="utf-8"))
        if (before["round"], before["draw"]) != (result["round"], result["draw"]):
            raise DrawError(f"{attempt.name} does not reproduce draw.json")
    else:
        write_once(first, result)
    return result


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="step", required=True)
    sub.add_parser("strata")
    d = sub.add_parser("draw")
    d.add_argument("--rule-commit", required=True)
    args = parser.parse_args(argv)
    root = Path.cwd()
    result = strata(root) if args.step == "strata" else draw(root, args.rule_commit)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
