"""Fixed configuration. The target repo is intentionally hardcoded, not a
flag or env override — the CLI always points at one skills repo.
"""
import json
import sys
from pathlib import Path

REPO = "AAInternal/skiwa-skills"
REPO_SKILLS_PATH = "skills/"
REPO_INDEX_PATH = "index.json"
# TODO: set to the real template repo before wiring up create-skill.
TEMPLATE_REPO = ""

# Package root: PyInstaller onefile extracts to sys._MEIPASS at runtime;
# in a normal install/dev checkout it's just this file's parent.
_PKG = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent)) / "skiwa"
ASSETS = _PKG / "assets"
GH_BIN = ASSETS / "gh" / ("gh.exe" if sys.platform == "win32" else "gh")
AGENT_DIRS_FILE = ASSETS / "agent_dirs.json"

# Known-good fallback if AGENT_DIRS_FILE is ever missing, unreadable, or
# malformed — so a bad hand-edit degrades gracefully instead of crashing.
_FALLBACK_AGENT_DIRS_DATA = {
    "shared_alias": [".agents/skills"],
    "agents": {
        "copilot": [".copilot/skills"],
        "claude": [".claude/skills"],
        "gemini": [".gemini/skills"],
        "cursor": [".cursor/skills"],
    },
}


def _load_agent_dirs_data() -> dict:
    """Read AGENT_DIRS_FILE, falling back to defaults if it's missing/invalid."""
    try:
        data = json.loads(AGENT_DIRS_FILE.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"warning: could not read {AGENT_DIRS_FILE} ({exc}); using built-in defaults",
            file=sys.stderr,
        )
        return _FALLBACK_AGENT_DIRS_DATA
    if not isinstance(data.get("agents"), dict):
        print(
            f"warning: {AGENT_DIRS_FILE} is missing an 'agents' object; using built-in defaults",
            file=sys.stderr,
        )
        return _FALLBACK_AGENT_DIRS_DATA
    return data


def _build_agent_dirs() -> dict:
    """Resolve the loaded (or fallback) agent-dirs data into real Paths.

    Per-agent directories can be a single Path or a list of Paths (checked
    in order; first match wins on name collisions). `None` = not confirmed
    yet, so `list`/`install` skip it rather than guessing.
    """
    data = _load_agent_dirs_data()
    home = Path.home()
    shared = [home / rel for rel in data.get("shared_alias", []) if isinstance(rel, str)]

    result: dict = {}
    for agent, rels in data.get("agents", {}).items():
        if not isinstance(rels, list) or not all(isinstance(r, str) for r in rels):
            print(
                f"warning: {AGENT_DIRS_FILE} has an invalid entry for '{agent}'; skipping it",
                file=sys.stderr,
            )
            result[agent] = None
            continue
        result[agent] = [home / rel for rel in rels] + shared
    return result


# Per-agent local skill install directories, loaded from AGENT_DIRS_FILE
# (`skiwa/assets/agent_dirs.json`) — edit that file to add/change an agent
# or its paths without touching this module.
AGENT_DIRS = _build_agent_dirs()

