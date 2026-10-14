"""Checks of the WP1 documents (docs/validation/v0.3/wp1-acceptance.md, section 9).

Read-only, offline. Every file is read from git objects, never from the working tree,
so the checks apply to a commit exactly as it is stored. Run from the repository root
with the project's Python:

    uv run --frozen python docs/validation/v0.3/checks/check_wp1.py --base <commit> \
        [--commit <commit>] [--plan-commit <commit>]

`--base` is the main commit the WP1 changes start from; `--commit` is the commit
checked (default HEAD); `--plan-commit` is the commit whose docs/plans/v0.3-plan.md
the line numbers refer to (default 8456780). Every check prints PASS or FAIL; the
exit code is 1 if any fails.

Checks:
- links: every relative Markdown link of the WP1 files resolves to a path that exists
  in the tree of --commit (G3);
- plan-lines: every "line N" / "lines N-M" in the WP1 files is inside the plan at
  --plan-commit (G1, by reference);
- plan-sections: every number of every "plan, section(s) ..." reference in the WP1
  files names a section heading of the plan (case-insensitive);
- verdicts-discovery: the bytes of docs/verdicts.md outside
  "## Paper verdicts (from v0.3)" are identical at --base and --commit (V8);
- claim-spec-tess: the bytes of docs/claim-spec.md at --base are an unchanged prefix
  at --commit (C7);
- reviewer-v02: the bytes of docs/reviewer-protocol.md at --base are an unchanged
  prefix at --commit (P1);
- sandbox-status: docs/sandbox.md states "Not yet validated" (S2);
- claude-rule: the rule of #34 is in "Operating rules for agents working in this repo"
  of CLAUDE.md (L1).
"""

from __future__ import annotations

import argparse
import posixpath
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PLAN = "docs/plans/v0.3-plan.md"
ACCEPTANCE = "docs/validation/v0.3/wp1-acceptance.md"
WP1_FILES = [
    "docs/verdicts.md",
    "docs/claim-spec.md",
    "docs/sandbox.md",
    "docs/right-of-reply.md",
    "docs/reviewer-protocol.md",
    "CLAUDE.md",
    ACCEPTANCE,
]
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")
LINES = re.compile(r"\blines? (\d+)(?:-(\d+))?\b", re.IGNORECASE)
NUMBER = r"\d+(?:\.\d+)?"
SECTION = re.compile(
    rf"\bplan,? sections? ({NUMBER}(?:(?:,\s+and\s+|,\s+|\s+and\s+){NUMBER})*)",
    re.IGNORECASE,
)
PAPER_SECTION = b"## Paper verdicts (from v0.3)"
RULE_SECTION = "## Operating rules for agents working in this repo"
RULE_TEXT = "Every legal or license statement written to the repository"


def git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, check=False)


def blob(commit: str, path: str) -> bytes:
    out = git("show", f"{commit}:{path}")
    if out.returncode != 0:
        raise SystemExit(f"cannot read {path} at {commit}: {out.stderr.decode().strip()}")
    return out.stdout


def text(commit: str, path: str) -> str:
    return blob(commit, path).decode("utf-8")


def exists(commit: str, path: str) -> bool:
    return git("cat-file", "-e", f"{commit}:{path}").returncode == 0


def drop_section(data: bytes, heading: bytes) -> bytes:
    start = data.find(heading + b"\n")
    if start < 0:
        start = data.find(heading + b"\r\n")
    if start < 0:
        return data
    end = data.find(b"\n## ", start + len(heading))
    return data[:start] + (data[end + 1 :] if end >= 0 else b"")


def section(content: str, heading: str) -> str:
    start = content.find(heading)
    if start < 0:
        return ""
    end = content.find("\n## ", start + len(heading))
    return content[start : end if end >= 0 else len(content)]


def check_links(commit: str) -> list[str]:
    problems = []
    for name in WP1_FILES:
        for target in LINK.findall(text(commit, name)):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#", 1)[0]
            if not path:
                continue
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(name), path))
            if resolved.startswith("..") or resolved.startswith(".git/"):
                problems.append(f"{name}: link outside the tree: {target}")
            elif not exists(commit, resolved):
                problems.append(f"{name}: broken link {target} (not in {commit})")
    return problems


def check_plan_lines(commit: str, plan_commit: str) -> list[str]:
    total = len(text(plan_commit, PLAN).split("\n"))
    problems = []
    for name in WP1_FILES:
        for first, last in LINES.findall(text(commit, name)):
            a = int(first)
            b = int(last) if last else a
            if not 1 <= a <= b <= total:
                problems.append(f"{name}: lines {first}-{last or first} outside 1-{total}")
    return problems


def plan_headings(plan_commit: str) -> set[str]:
    headings = set()
    for line in text(plan_commit, PLAN).split("\n"):
        match = re.match(r"#{2,3} (\d+(?:\.\d+)?)\.? ", line)
        if match:
            headings.add(match.group(1))
    return headings


def check_plan_sections(commit: str, plan_commit: str) -> list[str]:
    known = plan_headings(plan_commit)
    problems = []
    for name in WP1_FILES:
        for group in SECTION.findall(text(commit, name)):
            for ref in re.findall(NUMBER, group):
                if ref not in known:
                    problems.append(f"{name}: plan section {ref} not found")
    return problems


def check_verdicts_discovery(base: str, commit: str) -> list[str]:
    old = drop_section(blob(base, "docs/verdicts.md"), PAPER_SECTION)
    new = drop_section(blob(commit, "docs/verdicts.md"), PAPER_SECTION)
    return [] if old == new else ["docs/verdicts.md bytes changed outside the paper section"]


def check_prefix(base: str, commit: str, path: str) -> list[str]:
    ok = blob(commit, path).startswith(blob(base, path))
    return [] if ok else [f"{path}: bytes at base are not kept as a prefix"]


def check_sandbox_status(commit: str) -> list[str]:
    ok = "not yet validated" in text(commit, "docs/sandbox.md").lower()
    return [] if ok else ["docs/sandbox.md does not state 'Not yet validated'"]


def check_claude_rule(commit: str) -> list[str]:
    ok = RULE_TEXT in section(text(commit, "CLAUDE.md"), RULE_SECTION)
    return [] if ok else ["the rule of #34 is not in the operating rules of CLAUDE.md"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", required=True)
    parser.add_argument("--commit", default="HEAD")
    parser.add_argument("--plan-commit", default="8456780")
    args = parser.parse_args()
    checks = {
        "links": check_links(args.commit),
        "plan-lines": check_plan_lines(args.commit, args.plan_commit),
        "plan-sections": check_plan_sections(args.commit, args.plan_commit),
        "verdicts-discovery": check_verdicts_discovery(args.base, args.commit),
        "claim-spec-tess": check_prefix(args.base, args.commit, "docs/claim-spec.md"),
        "reviewer-v02": check_prefix(args.base, args.commit, "docs/reviewer-protocol.md"),
        "sandbox-status": check_sandbox_status(args.commit),
        "claude-rule": check_claude_rule(args.commit),
    }
    failed = False
    for name, problems in checks.items():
        print(f"{'PASS' if not problems else 'FAIL'} {name}")
        for problem in problems:
            print(f"     {problem}")
        failed = failed or bool(problems)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
