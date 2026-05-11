#!/usr/bin/env python3
"""
Ensure every HTML template under templates/ loads i18n for {% trans %} / {% blocktrans %}.

- Replaces `{% load static %}` with `{% load i18n static %}` when i18n not already present.
- Inserts `{% load i18n %}` after the first `{% extends ... %}` line when the file has no i18n load.
"""
from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"


def process_file(path: pathlib.Path) -> bool:
    raw = path.read_text(encoding="utf-8")
    if "{% load i18n" in raw or "{%load i18n" in raw:
        return False
    lines = raw.splitlines(keepends=True)
    if not lines:
        return False
    out: list[str] = []
    i = 0
    inserted = False
    while i < len(lines):
        line = lines[i]
        if (
            not inserted
            and line.strip().startswith("{% load static %}")
            and "i18n" not in line
        ):
            out.append(line.replace("{% load static %}", "{% load i18n static %}", 1))
            inserted = True
            i += 1
            continue
        if not inserted and line.strip().startswith("{% extends"):
            out.append(line)
            i += 1
            if i < len(lines) and lines[i].strip().startswith("{% load ") and "i18n" not in lines[i]:
                parts = lines[i].strip().split()
                if len(parts) >= 3 and parts[1] == "load":
                    rest = lines[i].replace("{% load ", "").replace("%}", "").strip()
                    out.append(f"{{% load i18n {rest} %}}\n")
                    inserted = True
                    i += 1
                    continue
            if not inserted:
                out.append("{% load i18n %}\n")
                inserted = True
            continue
        out.append(line)
        i += 1
    new = "".join(out)
    if new != raw:
        path.write_text(new, encoding="utf-8")
        return True
    return False


def main() -> int:
    changed = 0
    for path in sorted(TEMPLATES.rglob("*.html")):
        if path.name == "base.html":
            continue
        if process_file(path):
            changed += 1
            print("updated", path.relative_to(ROOT))
    print(f"Done. {changed} file(s) updated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
