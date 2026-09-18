"""Fixed configuration. The target repo is intentionally hardcoded, not a
flag or env override — the CLI always points at one skills repo.
"""
import sys
from pathlib import Path

# TODO: set to the real skills repo before wiring up search/install/create-skill.
REPO = "owner/skills-repo"
REPO_SKILLS_PATH = "skills/"
TEMPLATE_REPO = ""

# Package root: PyInstaller onefile extracts to sys._MEIPASS at runtime;
# in a normal install/dev checkout it's just this file's parent.
_PKG = Path(getattr(sys, "_MEIPASS", Path(__file__).parent.parent)) / "skiwa"
ASSETS = _PKG / "assets"
GH_BIN = ASSETS / "gh" / ("gh.exe" if sys.platform == "win32" else "gh")

# Per-agent local skill install directories. `None` = not confirmed yet, so
# `list`/`install` skip it rather than guessing.
AGENT_DIRS = {
    "copilot": Path.home() / ".agents" / "skills",
    "claude": Path.home() / ".claude" / "skills",
    "gemini": None,
    "cursor": None,
}
