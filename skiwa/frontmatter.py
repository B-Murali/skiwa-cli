"""Minimal YAML front-matter parser for SKILL.md files.

Handles the restricted subset our skill metadata actually uses: scalar
`key: value` pairs, `>` folded multi-line strings, and simple inline lists
(`[a, b]`). Not a general YAML parser — pulling in PyYAML for this would be
one dependency for what a few lines already cover.
"""
from __future__ import annotations

import re

_FENCE = re.compile(r"^---\s*$")
# Bounded, non-overlapping character classes only (no `\s*` next to `.*`),
# so matching is linear instead of risking catastrophic backtracking.
_KEY = re.compile(r"^\w[\w-]*$")


def _split_key_value(line: str) -> tuple[str, str] | None:
    """Split a `key: value` line. Returns None if `line` isn't one."""
    k, sep, v = line.partition(":")
    k = k.strip()
    if not sep or not _KEY.match(k):
        return None
    return k, v.strip()


def _parse_scalar(v: str):
    """Parse a front-matter scalar: inline list, quoted string, or plain text."""
    if v.startswith("[") and v.endswith("]"):
        return [item.strip() for item in v[1:-1].split(",") if item.strip()]
    if len(v) >= 2 and v[0] == v[-1] == '"':
        return v[1:-1].replace('\\"', '"')
    return v


class _Parser:
    """Incremental state machine for the front-matter block's body lines."""

    def __init__(self) -> None:
        self.data: dict = {}
        self.key: str | None = None
        self.folded: list[str] = []

    def _flush_fold(self) -> None:
        if self.key:
            self.data[self.key] = " ".join(self.folded).strip()
            self.key = None
            self.folded = []

    def feed(self, line: str) -> None:
        """Process one line of the front-matter block."""
        if self.key and (line.startswith("  ") or line.strip() == ""):
            self.folded.append(line.strip())
            return
        self._flush_fold()

        parsed = _split_key_value(line)
        if not parsed:
            return
        k, v = parsed
        if v[:1] in (">", "|"):
            self.key = k
            self.folded = []
        else:
            self.data[k] = _parse_scalar(v)

    def result(self) -> dict:
        self._flush_fold()
        return self.data


def parse_front_matter(text: str) -> dict:
    """Return the front-matter dict from a SKILL.md's leading `---` block.

    Returns {} if there's no front matter.
    """
    lines = text.splitlines()
    if not lines or not _FENCE.match(lines[0]):
        return {}
    try:
        end = next(i for i in range(1, len(lines)) if _FENCE.match(lines[i]))
    except StopIteration:
        return {}

    parser = _Parser()
    for line in lines[1:end]:
        parser.feed(line)
    return parser.result()
