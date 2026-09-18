"""Scan per-agent local skill directories for installed skills."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .config import AGENT_DIRS
from .frontmatter import parse_front_matter


@dataclass
class InstalledSkill:
    agent: str
    name: str
    path: Path
    description: str
    agents: list[str]


def _load_skill(agent: str, skill_dir: Path, filter_agent: str | None) -> InstalledSkill | None:
    """Build an InstalledSkill from `skill_dir`, or None if it's filtered out.

    A skill's own `agents:` field can further narrow an agent-filtered scan
    (e.g. installed under copilot's dir but only declared for claude).
    """
    skill_md = skill_dir / "SKILL.md"
    meta = parse_front_matter(skill_md.read_text()) if skill_md.exists() else {}
    declared_agents = meta.get("agents", [])
    if isinstance(declared_agents, str):
        declared_agents = [declared_agents]
    if filter_agent and declared_agents and filter_agent not in declared_agents:
        return None
    return InstalledSkill(
        agent=agent,
        name=meta.get("name", skill_dir.name),
        path=skill_dir,
        description=meta.get("description", ""),
        agents=declared_agents,
    )


def _iter_agent_skill_dirs(agents: list[str]):
    """Yield (agent, skill_dir) for every skill dir under each agent's base dir.

    Agents whose base dir isn't set or doesn't exist yield nothing.
    """
    for a in agents:
        base = AGENT_DIRS.get(a)
        if not base or not base.is_dir():
            continue
        for skill_dir in sorted(p for p in base.iterdir() if p.is_dir()):
            yield a, skill_dir


def scan_installed(agent: str | None = None) -> list[InstalledSkill]:
    """Scan known agent dirs (or just one) for installed skills.

    Directories that don't exist or aren't confirmed yet (`None` in
    AGENT_DIRS) are silently skipped.
    """
    agents = [agent] if agent else list(AGENT_DIRS)
    found: list[InstalledSkill] = []
    for a, skill_dir in _iter_agent_skill_dirs(agents):
        skill = _load_skill(a, skill_dir, agent)
        if skill:
            found.append(skill)
    return found
