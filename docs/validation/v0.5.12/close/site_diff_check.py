"""The deterministic check of the approved site change (#218 comment 7202817195, item 2).

    launch_v4.py docs/validation/v0.5.12/units/inspect.json -- \
        docs/validation/v0.5.12/close/site_diff_check.py <new commit>

It passes only if the diff between the draft commit 50d2e53 and the new commit of
klucilla/refute-site touches exactly two lines:
- one line of ``src/i18n/en.ts``, where the old sentence is replaced by the new one;
- one line of ``src/i18n/pt-br.ts``, likewise;

and both lines belong to the ``v0_5_12`` entry's purpose. It prints a JSON result and exits 0
(passed) or 1 (failed). It only reads.
"""

import json
import subprocess
import sys

SITE = "C:/Projetos/refute-site"
BASE = "50d2e53"
CHANGES = {
    "src/i18n/en.ts": (
        "No earlier test, threshold or verdict changed.",
        "No test, threshold or verdict of the earlier battery versions changed.",
        "Check whether the core of the fifth version of the battery",
    ),
    "src/i18n/pt-br.ts": (
        "Nenhum teste, limiar ou veredito anterior mudou.",
        "Nenhum teste, limiar ou veredito das versões anteriores da bateria mudou.",
        "Verificar se o núcleo da quinta versão da bateria",
    ),
}


def main() -> int:
    new = sys.argv[1]
    out = subprocess.run(
        ["git", "-C", SITE, "diff", "-U0", "--no-color", BASE, new],
        capture_output=True, check=True, encoding="utf-8",
    ).stdout  # fmt: skip
    files: dict[str, dict[str, list[str]]] = {}
    current = None
    for line in out.splitlines():
        if line.startswith("diff --git "):
            current = line.split(" b/", 1)[1]
            files[current] = {"-": [], "+": []}
        elif line.startswith(("---", "+++", "@@", "index ")) or current is None:
            continue
        elif line[:1] in "-+":
            files[current][line[0]].append(line[1:])
    problems = []
    if set(files) != set(CHANGES):
        problems.append(f"files touched: {sorted(files)}")
    for path, (old, new_text, anchor) in CHANGES.items():
        d = files.get(path, {"-": [], "+": []})
        if len(d["-"]) != 1 or len(d["+"]) != 1:
            problems.append(f"{path}: {len(d['-'])} removed and {len(d['+'])} added lines")
            continue
        before, after = d["-"][0], d["+"][0]
        if before.count(old) != 1 or anchor not in before:
            problems.append(f"{path}: removed line is not the v0_5_12 purpose with the old text")
        elif before.replace(old, new_text) != after:
            problems.append(f"{path}: added line is not the removed line with only the change")
    result = {"base": BASE, "new": new, "files": sorted(files), "passed": not problems,
              "problems": problems}  # fmt: skip
    print(json.dumps(result, indent=1, ensure_ascii=False))
    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
