#!/usr/bin/env python3
"""Enforce the commit policy for changes that touch documents.

Conventional Commits validates the shape of the header. It says nothing about
which type a given change must use, and it makes the body optional. This hook
adds the two rules in `.claude/rules/commits.md`: a commit touching any Markdown file is
typed `docs`, and it carries a body with an inventory of what changed and why.

Runs at the commit-msg stage. Set CHECK_DOCS_COMMIT_REV to validate an existing
commit instead of the staged tree, which is how CI checks a pull request.
"""

import os
import re
import subprocess
import sys
from pathlib import Path

HEADER = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^()]+)\))?!?: .+")
SCISSORS = "# ------------------------ >8"
SKIP_PREFIXES = ("merge ", "revert ", "fixup!", "squash!", "amend!")


def changed_markdown() -> list[str]:
    rev = os.environ.get("CHECK_DOCS_COMMIT_REV")
    if rev:
        cmd = ["git", "show", "--name-only", "--format=", rev]
    else:
        cmd = ["git", "diff", "--cached", "--name-only"]
    out = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout
    return sorted({p for p in out.splitlines() if p.endswith(".md")})


def message_lines(path: Path) -> list[str]:
    lines: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith(SCISSORS):
            break
        if line.startswith("#"):
            continue
        lines.append(line.rstrip())
    while lines and not lines[-1]:
        lines.pop()
    return lines


def section(lines: list[str], label: str) -> list[str] | None:
    """Return the non-empty lines under `label:`, or None if it is absent."""
    for i, line in enumerate(lines):
        if line.strip().lower() == f"{label}:":
            rest: list[str] = []
            for candidate in lines[i + 1 :]:
                if candidate.strip().lower().endswith(":") and not candidate.startswith(
                    (" ", "-", "*")
                ):
                    break
                if candidate.strip():
                    rest.append(candidate)
            return rest
    return None


def fail(documents: list[str], problems: list[str]) -> int:
    print("[Docs commit policy] This commit touches documents:")
    for document in documents:
        print(f"  - {document}")
    print()
    for problem in problems:
        print(f"  - {problem}")
    print(
        "\nDocuments are always the most recent copy, so the commit body is the"
        "\nonly trace of what changed and why. See `.claude/rules/commits.md`."
        "\n\nExpected shape:\n"
        "\n    docs(scope): subject"
        "\n"
        "\n    Inventory:"
        "\n    - path/to/doc.md: the concrete change."
        "\n"
        "\n    Why:"
        "\n    What prompted it.\n"
    )
    return 1


def main() -> int:
    lines = message_lines(Path(sys.argv[1]))
    if not lines:
        return 0
    header = lines[0]
    if header.lower().startswith(SKIP_PREFIXES):
        return 0
    match = HEADER.match(header)
    if not match:
        # Malformed header: conventional-pre-commit reports it with detail.
        return 0

    documents = changed_markdown()
    if not documents:
        return 0

    problems: list[str] = []
    if match.group("type") != "docs":
        problems.append(
            f"the type is `{match.group('type')}`, but any commit touching a "
            "Markdown file is typed `docs`."
        )

    body = lines[2:] if len(lines) > 2 and not lines[1] else []
    if not body:
        problems.append("the body is missing. It is mandatory on a docs commit.")
    else:
        inventory = section(body, "inventory")
        why = section(body, "why")
        if inventory is None:
            problems.append("the body has no `Inventory:` section.")
        elif not any(line.lstrip().startswith(("-", "*")) for line in inventory):
            problems.append(
                "`Inventory:` has no bullets. List one per document touched."
            )
        if why is None:
            problems.append("the body has no `Why:` section.")
        elif not why:
            problems.append("`Why:` is empty.")

    if problems:
        return fail(documents, problems)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
