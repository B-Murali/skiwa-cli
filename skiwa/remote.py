"""Remote skill catalog access: fetch `index.json` and `SKILL.md` files from
the hardcoded skills repo (see `config.REPO`), via `gh api` — no direct HTTP
client, no token handling; `gh`'s own auth is reused as-is.
"""
from __future__ import annotations

import base64
import json
import subprocess

from . import gh
from .config import REPO, REPO_INDEX_PATH


class RemoteError(RuntimeError):
    """Raised when the remote catalog can't be fetched or parsed."""


def _fetch_contents(path: str) -> str:
    """Fetch and decode one file from REPO via the GitHub contents API."""
    try:
        result = gh.run("api", f"repos/{REPO}/contents/{path}")
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        detail = f": {stderr}" if stderr else ""
        raise RemoteError(f"Could not fetch '{path}' from {REPO}{detail}") from exc

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RemoteError(f"Unexpected response fetching '{path}' from {REPO}") from exc

    encoding = data.get("encoding")
    content = data.get("content", "")
    if encoding != "base64":
        raise RemoteError(f"Unsupported response encoding fetching '{path}' from {REPO}")
    try:
        return base64.b64decode(content).decode("utf-8")
    except ValueError as exc:
        raise RemoteError(f"Could not decode '{path}' from {REPO}") from exc


def fetch_index() -> dict:
    """Fetch and parse `index.json`, the generated global skill catalog."""
    text = _fetch_contents(REPO_INDEX_PATH)
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise RemoteError(f"'{REPO_INDEX_PATH}' in {REPO} is not valid JSON") from exc


def fetch_skill_manifest(path: str) -> str:
    """Fetch the raw SKILL.md content at `path` (a catalog `manifestPath`)."""
    return _fetch_contents(path)
