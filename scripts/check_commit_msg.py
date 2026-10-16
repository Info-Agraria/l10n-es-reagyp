"""Reject commit messages that carry assistant attribution."""

import re
import sys
from pathlib import Path

SCISSORS = "# ------------------------ >8 ------------------------"
TOOLS = r"(claude|anthropic|copilot|openai|chatgpt|gpt-?\d*|gemini|cursor)"
TRAILER = re.compile(rf"^\s*[\w-]+-by:.*\b{TOOLS}\b", re.IGNORECASE)
FOOTER = re.compile(rf"^\W*generated (with|by)\b.*\b{TOOLS}\b", re.IGNORECASE)


def message_lines(text: str) -> list[str]:
    lines = []
    for line in text.splitlines():
        if line.startswith(SCISSORS):
            break
        if not line.startswith("#"):
            lines.append(line)
    return lines


def main(path: str) -> int:
    for line in message_lines(Path(path).read_text()):
        if TRAILER.search(line) or FOOTER.search(line):
            print(f"assistant attribution is not allowed: {line.strip()}")
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
