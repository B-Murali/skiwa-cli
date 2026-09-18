"""Locate and invoke `gh`: the user's own install wins (keeps their existing
auth/config); the bundled copy (PyInstaller onefile builds only) is the
fallback so the CLI still works with zero prerequisites.
"""
from __future__ import annotations

import shutil
import subprocess

from .config import GH_BIN


def gh_path() -> str:
    """Return a runnable `gh` path, or "" if none is available."""
    found = shutil.which("gh")
    if found:
        return found
    return str(GH_BIN) if GH_BIN.exists() else ""


def run(*args: str) -> subprocess.CompletedProcess:
    """Run `gh` with args, raising a clear error if no `gh` is available."""
    gh = gh_path()
    if not gh:
        raise FileNotFoundError(
            "gh not found on PATH and no bundled copy present. "
            "Install gh: https://cli.github.com"
        )
    return subprocess.run([gh, *args], capture_output=True, text=True, check=True)
