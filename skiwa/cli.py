"""skiwa CLI entry point."""
from __future__ import annotations

import argparse
import re
import sys

from .config import AGENT_DIRS
from .local import scan_installed
from .ui import print_banner


def _short_description(text: str, limit: int = 90) -> str:
    """First sentence, or a hard truncation, whichever is shorter."""
    if not text:
        return ""
    first_sentence = re.split(r"(?<=[.!?])\s", text, maxsplit=1)[0]
    short = first_sentence if len(first_sentence) <= limit else text[:limit].rstrip() + "…"
    return short


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
    sub = parser.add_subparsers(dest="command")

    p_list = sub.add_parser("list", help="List locally installed skills.")
    p_list.add_argument("--agent", choices=sorted(AGENT_DIRS), help="Only list skills for this agent.")
    p_list.set_defaults(func=cmd_list)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        print_banner()
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
