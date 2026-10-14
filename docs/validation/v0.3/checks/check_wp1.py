"""Checks of the WP1 documents (docs/validation/v0.3/wp1-acceptance.md, section 9).

Read-only, offline. Run from the repository root with the project's Python:

    uv run --frozen python docs/validation/v0.3/checks/check_wp1.py --base <commit>

`--base` is the main commit the WP1 changes start from; `--plan-commit` is the commit
whose docs/plans/v0.3-plan.md the line numbers of wp1-acceptance.md refer to
(default 8456780). Every check prints PASS or FAIL; the exit code is 1 if any fails.

Checks:
- links: every relative Markdown link of the WP1 files resolves (G3);
- plan-lines: every "line N" / "lines N-M" of wp1-acceptance.md is inside the plan at
  --plan-commit (G1, by reference);
- plan-sections: every "plan, section X.Y" / "plan sections X and Y" reference of the
  WP1 documents names a section heading of the plan;
- verdicts-discovery: docs/verdicts.md outside "## Paper verdicts (from v0.3)" is
  identical to --base (V8);
- claim-spec-tess: docs/claim-spec.md at --base is an unchanged prefix (C7);
- reviewer-v02: docs/reviewer-protocol.md at --base is an unchanged prefix (P1);
- sandbox-status: docs/sandbox.md states "Not yet validated" (S2);
- claude-rule: the rule of #34 is in "Operating rules for agents working in this repo"
  of CLAUDE.md (L1).
"""

from __future__ import annotations

import argparse
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
LINES = re.compile(r"\blines? (\d+)(?:-(\d+))?")
SECTION = re.compile(r"\bplan, sections? ([0-9]+(?:\.[0-9]+)?)")
PAPER_SECTION = "## Paper verdicts (from v0.3)"
RULE_SECTION = "## Operating rules for agents working in this repo"
RULE_TEXT = "Every legal or license statement written to the repository"


def git_show(commit: str, path: str) -> str:
    out = subprocess.run(
        ["git", "show", f"{commit}:{path}"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    )
    return out.stdout.decode("utf-8").replace("\r\n", "\n")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8").replace("\r\n", "\n")


def drop_section(text: str, heading: str) -> str:
    start = text.find(heading + "\n")
    if start < 0:
        return text
    end = text.find("\n## ", start + len(heading))
    return text[:start] + (text[end + 1 :] if end >= 0 else "")


def section(text: str, heading: str) -> str:
    start = text.find(heading + "\n")
    if start < 0:
        return ""
    end = text.find("\n## ", start + len(heading))
    return text[start : end if end >= 0 else len(text)]


def check_links() -> list[str]:
    problems = []
    for name in WP1_FILES:
        for target in LINK.findall(read(name)):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            path = target.split("#", 1)[0]
            if path and not (ROOT / name).parent.joinpath(path).exists():
                problems.append(f"{name}: broken link {target}")
    return problems


def check_plan_lines(plan_commit: str) -> list[str]:
    total = len(git_show(plan_commit, PLAN).split("\n"))
    problems = []
    for first, last in LINES.findall(read(ACCEPTANCE)):
        a = int(first)
        b = int(last) if last else a
        if not 1 <= a <= b <= total:
            problems.append(f"lines {first}-{last or first} outside the plan (1-{total})")
    return problems


def plan_headings(plan_commit: str) -> set[str]:
    headings = set()
    for line in git_show(plan_commit, PLAN).split("\n"):
        match = re.match(r"#{2,3} ([0-9]+(?:\.[0-9]+)?)\.? ", line)
        if match:
            headings.add(match.group(1))
    return headings


def check_plan_sections(plan_commit: str) -> list[str]:
    known = plan_headings(plan_commit)
    problems = []
    for name in WP1_FILES:
        for ref in SECTION.findall(read(name)):
            if ref not in known:
                problems.append(f"{name}: plan section {ref} not found")
    return problems


def check_verdicts_discovery(base: str) -> list[str]:
    old = drop_section(git_show(base, "docs/verdicts.md"), PAPER_SECTION)
    new = drop_section(read("docs/verdicts.md"), PAPER_SECTION)
    return [] if old == new else ["docs/verdicts.md changed outside the paper section"]


def check_prefix(base: str, path: str) -> list[str]:
    old = git_show(base, path)
    return [] if read(path).startswith(old) else [f"{path}: content at base is not kept"]


def check_sandbox_status() -> list[str]:
    ok = "not yet validated" in read("docs/sandbox.md").lower()
    return [] if ok else ["docs/sandbox.md does not state 'Not yet validated'"]


def check_claude_rule() -> list[str]:
    ok = RULE_TEXT in section(read("CLAUDE.md"), RULE_SECTION)
    return [] if ok else ["the rule of #34 is not in the operating rules of CLAUDE.md"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base", required=True)
    parser.add_argument("--plan-commit", default="8456780")
    args = parser.parse_args()
    checks = {
        "links": check_links(),
        "plan-lines": check_plan_lines(args.plan_commit),
        "plan-sections": check_plan_sections(args.plan_commit),
        "verdicts-discovery": check_verdicts_discovery(args.base),
        "claim-spec-tess": check_prefix(args.base, "docs/claim-spec.md"),
        "reviewer-v02": check_prefix(args.base, "docs/reviewer-protocol.md"),
        "sandbox-status": check_sandbox_status(),
        "claude-rule": check_claude_rule(),
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
