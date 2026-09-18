"""skiwa CLI entry point."""
from __future__ import annotations

import argparse
import re
import sys

from . import remote
from . import __version__
from .config import AGENT_DIRS
from .frontmatter import strip_front_matter
from .local import scan_installed
from .ui import print_banner


def _short_description(text: str, limit: int = 90) -> str:
    """First sentence, or a hard truncation, whichever is shorter."""
    if not text:
        return ""
    first_sentence = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
    short = first_sentence if len(first_sentence) <= limit else text[:limit].rstrip() + "…"
    return short


def _skill_label(skill: dict) -> str:
    """The identifier to print/match: catalog `id` (repo/name), else `name`."""
    return skill.get("id") or skill.get("name", "")


def _matches_query(skill: dict, query: str) -> bool:
    """Case-insensitive substring match over name/id/description/keywords."""
    query = query.lower()
    keywords = skill.get("keywords") or []
    haystack = " ".join(
        [skill.get("name", ""), skill.get("id", ""), skill.get("description", ""), *keywords]
    ).lower()
    return query in haystack


def _fetch_catalog() -> tuple[list[dict] | None, int]:
    """Fetch the remote catalog's skill list, or (None, error_code) on failure."""
    try:
        index = remote.fetch_index()
    except (FileNotFoundError, remote.RemoteError) as exc:
        print(str(exc), file=sys.stderr)
        return None, 1
    return index.get("skills", []), 0


def cmd_search(args: argparse.Namespace) -> int:
    skills, err = _fetch_catalog()
    if skills is None:
        return err

    if args.query:
        skills = [s for s in skills if _matches_query(s, args.query)]

    if not skills:
        scope = f"matching '{args.query}'" if args.query else "in the catalog"
        print(f"No skills found {scope}.")
        return 0

    for i, s in enumerate(skills, start=1):
        version = f" v{s['version']}" if s.get("version") else ""
        desc = f" — {_short_description(s.get('description', ''))}" if s.get("description") else ""
        print(f"{i}. {_skill_label(s)}{version}{desc}")
    return 0


def _find_skill(skills: list[dict], identifier: str) -> dict | None:
    """Find a catalog skill by `id` or `name`."""
    return next((s for s in skills if s.get("id") == identifier or s.get("name") == identifier), None)


def _print_skill_metadata(match: dict) -> None:
    """Print a matched skill's metadata fields (version, owner, keywords, ...)."""
    print(_skill_label(match))
    for label, key in (
        ("version", "version"),
        ("owner", "owner"),
        ("squad", "squadId"),
        ("visibility", "visibility"),
    ):
        if match.get(key):
            print(f"  {label}: {match[key]}")
    if match.get("keywords"):
        print(f"  keywords: {', '.join(match['keywords'])}")
    if match.get("allowedTools"):
        print(f"  allowed-tools: {', '.join(match['allowedTools'])}")
    if match.get("deprecated"):
        print("  deprecated: yes")

    print()
    print(match.get("description") or "(no description)")


def _print_skill_body(match: dict, full: bool = False, snippet_lines: int = 6) -> None:
    """Fetch and print a matched skill's SKILL.md body, if it has one.

    By default only the first `snippet_lines` lines are shown; pass
    `full=True` to print the entire body.
    """
    manifest_path = match.get("manifestPath")
    if not manifest_path:
        return
    try:
        manifest_text = remote.fetch_skill_manifest(manifest_path)
    except (FileNotFoundError, remote.RemoteError) as exc:
        print(f"\n(Could not fetch SKILL.md body: {exc})", file=sys.stderr)
        return
    body = strip_front_matter(manifest_text).strip()
    if not body:
        return

    print()
    if full:
        print(body)
        return

    lines = body.splitlines()
    print("\n".join(lines[:snippet_lines]))
    if len(lines) > snippet_lines:
        print("…")
        print(f"(showing first {snippet_lines} lines — use --full to see the complete guide)")


def cmd_describe(args: argparse.Namespace) -> int:
    skills, err = _fetch_catalog()
    if skills is None:
        return err

    match = _find_skill(skills, args.skill)
    if not match:
        print(f"No skill named '{args.skill}' found in the catalog.", file=sys.stderr)
        return 1

    _print_skill_metadata(match)
    _print_skill_body(match, full=args.full)
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    if args.agent and args.agent not in AGENT_DIRS:
        print(f"Unknown agent '{args.agent}'. Known: {', '.join(AGENT_DIRS)}", file=sys.stderr)
        return 1
    if args.agent and AGENT_DIRS[args.agent] is None:
        print(f"No confirmed local skill directory for '{args.agent}' yet.", file=sys.stderr)
        return 1

    skills = scan_installed(args.agent)
    if not skills:
        scope = f"agent '{args.agent}'" if args.agent else "any known agent"
        print(f"No skills installed for {scope}.")
        return 0

    for i, s in enumerate(skills, start=1):
        desc = f" — {_short_description(s.description)}" if s.description else ""
        print(f"{i}. {s.name} ({s.agent}){desc}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="skiwa", description="Browse and manage agent skills.")
    parser.add_argument(
        "-v", "--version", action="version", version=f"skiwa {__version__}"
    )
    sub = parser.add_subparsers(dest="command")

    p_search = sub.add_parser("search", help="Search the remote skill catalog.")
    p_search.add_argument(
        "query", nargs="?", help="Filter by name, id, description, or keyword."
    )
    p_search.set_defaults(func=cmd_search)

    p_describe = sub.add_parser(
        "describe", help="Show full details for one skill from the remote catalog."
    )
    p_describe.add_argument("skill", help="Skill id (repo/name) or name.")
    p_describe.add_argument(
        "--full", action="store_true", help="Print the entire SKILL.md body instead of a short snippet."
    )
    p_describe.set_defaults(func=cmd_describe)

    p_list = sub.add_parser("list", help="List locally installed skills.")
    p_list.add_argument("--agent", choices=sorted(AGENT_DIRS), help="Only list skills for this agent.")
    p_list.set_defaults(func=cmd_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    # Legacy Windows consoles default stdout/stderr to a non-UTF-8 codepage
    # (e.g. cp437/cp1252); skill names/descriptions from the remote catalog
    # can contain arbitrary Unicode, so force UTF-8 out to avoid a crash on
    # the first emoji or accented character. No-op where already UTF-8.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        print_banner()
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
