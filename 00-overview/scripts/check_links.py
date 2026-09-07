"""Verify every relative markdown link resolves, flag em-dashes, and flag unescaped pipes inside code spans in table rows (ClickUp rejects those).

Usage (from the xms repo root). Skips the seeded skills under .claude and .cursor and the application folders:

    python 00-overview/scripts/check_links.py

Exit code 1 when a link is broken or an em-dash is found in a .md file.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[2]
LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")


def _pipe_in_code(line: str) -> bool:
    """True when a table row has an unescaped | inside a backtick span."""
    in_code = False
    for i, ch in enumerate(line):
        if ch == "`":
            in_code = not in_code
        elif ch == "|" and in_code and (i == 0 or line[i - 1] != "\\"):
            return True
    return False


def main() -> int:
    broken: list[str] = []
    dashes: list[str] = []
    pipes: list[str] = []
    skip = {".claude", ".cursor", ".agents", "frontend", "backend", "infra", "node_modules"}
    files = sorted(md for md in ROOT.rglob("*.md") if not (set(md.relative_to(ROOT).parts[:-1]) & skip))
    for md in files:
        text = md.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), 1):
            if "—" in line:
                dashes.append(f"{md.relative_to(ROOT)}:{line_no}")
            if line.startswith("|") and _pipe_in_code(line):
                pipes.append(f"{md.relative_to(ROOT)}:{line_no}")
        for match in LINK.finditer(text):
            target = match.group(1)
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if re.match(r"^[A-Za-z]:/", target):
                # Absolute Windows path (AIX Docs links); check existence directly.
                path = Path(unquote(target.split("#", 1)[0]))
            else:
                path = (md.parent / unquote(target.split("#", 1)[0])).resolve()
            if not path.exists():
                broken.append(f"{md.relative_to(ROOT)} -> {target}")
    print(f"{len(files)} markdown files checked")
    if broken:
        print("BROKEN LINKS:")
        for b in broken:
            print("  ", b)
    if dashes:
        print("EM-DASHES:")
        for d in dashes:
            print("  ", d)
    if pipes:
        print("UNESCAPED PIPE IN TABLE CODE SPAN (ClickUp rejects these):")
        for p in pipes:
            print("  ", p)
    return 1 if (broken or dashes or pipes) else 0


if __name__ == "__main__":
    sys.exit(main())
