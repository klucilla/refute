"""A2 (#218, comment 7203695669): move three domain blocks of CLAUDE.md literally to
docs/agents/, each replaced in CLAUDE.md by a trigger. No other line changes."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
src = (ROOT / "CLAUDE.md").read_text(encoding="utf-8").splitlines()


def block(first: int, last: int, starts: str, ends: str) -> list[str]:
    lines = src[first - 1 : last]
    assert lines[0].startswith(starts), lines[0]
    assert lines[-1].endswith(ends), lines[-1]
    return lines


data_pub = block(221, 228, "- Raw outputs larger than 5 MB", "(the maintainer publishes).")
ci = block(289, 326, "   **CI in two levels**", "`head_sha` is checked.")
vm = block(345, 357, "   Since 2026-10-17", "   with the agent.")
assert src[287] == "" and src[326].startswith("2. **Codex**"), (src[287], src[326])
assert src[343] == "" and src[357] == "", (src[343], src[357])

HEADER = (
    "Moved literally from `CLAUDE.md` on 2026-11-26 by the maintainer's decision (#218, comment",
    "7203695669, item A2), from commit `02b6ddf`, with no line changed (indentation included).",
    "No rule changed: the text below binds exactly as it did in `CLAUDE.md`, which cites this file",
    "with the trigger quoted here. Relative links are written for the repository root, as they",
    "were in `CLAUDE.md`.",
)


def agent_file(title: str, trigger: str, where: str, body: list[str]) -> str:
    lines = [
        f"# {title}",
        "",
        *HEADER,
        "",
        f"**Trigger in `CLAUDE.md`** ({where}): {trigger}",
        "",
        "---",
        "",
        *body,
        "",
    ]
    return "\n".join(lines)


T_DATA = (
    "Before committing, archiving or publishing any raw output larger than 5 MB, or preparing a "
    "Zenodo record, read [docs/agents/data-publication.md](docs/agents/data-publication.md)."
)
T_CI = (
    "Before a push, a pull request, a wait on CI, or any step gated on CI (a lock, a tag, a "
    "release, an acceptance or a dependency change), read "
    "[docs/agents/ci-two-level.md](docs/agents/ci-two-level.md): CI in two levels."
)
T_VM = (
    "Before any step on a VM, through the JEA endpoint or by SSH to a VM, read "
    "[docs/agents/vm-jea.md](docs/agents/vm-jea.md): which of those steps the agent runs itself."
)

new = [
    *src[:220],
    "- **Raw outputs and data publication.** " + T_DATA,
    *src[228:288],
    "   " + T_CI,
    *src[326:344],
    "   " + T_VM,
    *src[357:],
    "",
]

agents = ROOT / "docs" / "agents"
agents.mkdir(exist_ok=True)
files = {
    "data-publication.md": agent_file(
        "Raw outputs and data publication", T_DATA, "Operating rules for agents", data_pub
    ),
    "ci-two-level.md": agent_file(
        "CI in two levels", T_CI, "GitHub operations, Working mode (v0.3), item 1", ci
    ),
    "vm-jea.md": agent_file(
        "VMs and the JEA endpoint", T_VM, "GitHub operations, Working mode (v0.3), item 3", vm
    ),
}
for name, text in files.items():
    (agents / name).write_text(text, encoding="utf-8", newline="\n")
(ROOT / "CLAUDE.md").write_text("\n".join(new), encoding="utf-8", newline="\n")
print("CLAUDE.md", len(new) - 1, "lines")
