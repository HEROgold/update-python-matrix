"""Keep a workflow's Python version matrix in step with endoflife.date.

The matrix is a block list under a key (default `python-version`). Its lowest
version is the project's floor: the list becomes every Python release that is
not past end of life and is at or above that floor.

    python update_matrix.py .github/workflows/test.yml [--key python-version]

Writes `changed` and `versions` to `$GITHUB_OUTPUT` when that is set.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request
from datetime import date
from pathlib import Path

ENDOFLIFE_URL = "https://endoflife.date/api/python.json"
ITEM = re.compile(
    r"""^(?P<indent>[ \t]*)-[ \t]*(?P<quote>["']?)(?P<version>\d+\.\d+)(?P=quote)[ \t]*$"""
)


class MatrixNotFoundError(ValueError):
    """The workflow has no block list of versions under the matrix key."""


def update_matrix(
    workflow: str, cycles: list[dict], today: date, key: str = "python-version"
) -> tuple[str, list[str]]:
    """Return the workflow with its matrix updated, and the new list of versions."""
    lines = workflow.splitlines(keepends=True)
    start, items = _find_list(lines, key)
    end = start + len(items)
    current = [item["version"] for item in items]
    floor = min(current, key=_version_key)

    versions = sorted(
        (v for v in _supported(cycles, today) if _version_key(v) >= _version_key(floor)),
        key=_version_key,
    )
    if versions == sorted(current, key=_version_key):
        return workflow, versions

    first = items[0]
    newline = "\r\n" if lines[start].endswith("\r\n") else "\n"
    quote = first["quote"]
    new_items = [f"{first['indent']}- {quote}{v}{quote}{newline}" for v in versions]
    return "".join([*lines[:start], *new_items, *lines[end:]]), versions


def _find_list(lines: list[str], key: str) -> tuple[int, list[re.Match[str]]]:
    """Return the first line of the version list under `key:`, and its items."""
    heading = re.compile(rf"^[ \t]*{re.escape(key)}:[ \t]*$")
    for index, line in enumerate(lines):
        if not heading.match(line.rstrip("\r\n")):
            continue
        items = []
        for item_line in lines[index + 1 :]:
            item = ITEM.match(item_line.rstrip("\r\n"))
            if item is None:
                break
            items.append(item)
        if items:
            return index + 1, items
    msg = f"no block list of versions under `{key}:`"
    raise MatrixNotFoundError(msg)


def _supported(cycles: list[dict], today: date) -> list[str]:
    """Return the release cycles not past their end of life."""
    supported = []
    for cycle in cycles:
        eol = cycle.get("eol")
        if eol is False or (isinstance(eol, str) and date.fromisoformat(eol) >= today):
            supported.append(cycle["cycle"])
    return supported


def _version_key(version: str) -> tuple[int, ...]:
    return tuple(int(part) for part in version.split("."))


def main() -> int:
    """Update the workflow file in place and report the result."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("workflow", type=Path)
    parser.add_argument("--key", default="python-version")
    args = parser.parse_args()

    with urllib.request.urlopen(ENDOFLIFE_URL, timeout=10) as response:
        cycles = json.load(response)

    with args.workflow.open(encoding="utf-8", newline="") as file:
        text = file.read()
    updated, versions = update_matrix(text, cycles, date.today(), key=args.key)  # noqa: DTZ011 - EOL dates are dates
    changed = updated != text
    if changed:
        with args.workflow.open("w", encoding="utf-8", newline="") as file:
            file.write(updated)

    if output := os.environ.get("GITHUB_OUTPUT"):
        with Path(output).open("a", encoding="utf-8") as file:
            file.write(f"changed={'true' if changed else 'false'}\n")
            file.write(f"versions={json.dumps(versions)}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
