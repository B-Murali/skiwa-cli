# skiwa — CLI Plan

Skill wrangler: browse, install, and scaffold agent skills from a single
GitHub repo, using `gh` under the hood. Ponytail-guided: stdlib first,
minimal deps, no speculative abstraction.

## Fixed anchor: one repo

The CLI always targets **one** GitHub repo, hardcoded as a constant in
`skiwa/config.py` (not a flag, not an env override users can casually
change — that's the whole point of "no matter what"). Needed from you:

- `repo` — `owner/repo`
- `repo_skills_path` — subfolder holding skill folders (default `skills/`)
- `template_repo` — repo/path `create-skill` copies from (can stub later)

## Dependencies (equivalents chosen, all real PyPI packages)

| JS package | Python equivalent | Why |
|---|---|---|
| `figlet` | `pyfiglet` | direct port, banner ASCII art |
| `gradient-string` | `rich` (`Text` with per-char styled color interpolation) | no PyPI `gradient-string` port exists; `rich` already does color blending and is a normal, maintained dep — not hand-rolled ANSI math |
| `inquirer` | `questionary` | closest UX match (select/confirm/checkbox prompts), simpler API than InquirerPy |

`gh` CLI is invoked via `subprocess` (already installed & authenticated in
this env) — no GitHub API client library needed.

## Layout

```
skiwa/
  __init__.py
  config.py      # REPO, SKILLS_PATH, TEMPLATE_REPO, AGENT_DIRS constants
  gh.py          # thin subprocess wrapper around `gh api` / `gh repo clone`
  skills.py      # parse skill metadata (SKILL.md front matter), remote listing, fuzzy find
  local.py       # scan/install into per-agent skill dirs
  ui.py          # banner (pyfiglet+rich), tables, questionary prompts
  cli.py         # argparse subcommands, entry point
pyproject.toml   # console_scripts: skiwa = skiwa.cli:main
test_smoke.py    # one runnable check per ponytail (asserts, no framework)
```

Argparse over `click`/`typer`: stdlib, and the command surface is flat
enough that subparsers are all we need.

## Skill metadata convention

Each skill = a folder with a `SKILL.md` whose YAML front matter declares:
```yaml
name: my-skill
description: one-liner shown in list/find/describe
agents: [copilot, claude]
language: [py]        # or [md], [sh, js], etc.
```
This mirrors what's already in this env (`~/.agents/skills/<name>/SKILL.md`).

## Local install directories (per agent)

Each agent also discovers skills from `~/.agents/skills/<name>/` — the
cross-tool "agentskills.io" alias directory that Copilot, Claude, Gemini CLI,
and Cursor all additionally scan alongside their own dedicated directory.

| agent | install dir(s) |
|---|---|
| copilot | `~/.copilot/skills/<name>/`, `~/.agents/skills/<name>/` |
| claude | `~/.claude/skills/<name>/`, `~/.agents/skills/<name>/` |
| gemini | `~/.gemini/skills/<name>/`, `~/.agents/skills/<name>/` |
| cursor | `~/.cursor/skills/<name>/`, `~/.agents/skills/<name>/` |

All four known agents now have confirmed directories; `list`/`install --agent`
would only skip an agent if a future one is added without a confirmed dir.

## Commands

1. `skiwa search [query]` — `gh api repos/{repo}/contents/{skills_path}`, print name+description table; with `query`, filter to skills whose name/description match (stdlib `difflib.get_close_matches` or substring match), same fuzzy logic as `find`.
2. `skiwa list [--agent X]` — scan local dirs (all known agents, or just X), print what's installed + where.
3. `skiwa list --agent copilot` — same command, agent filter narrows both remote metadata (`agents:` field) and local dir scanned.
4. `skiwa find <query>` — fetch remote listing (or use short-lived cache), fuzzy-match name+description with stdlib `difflib.get_close_matches`. No new dependency.
5. `skiwa describe <skill>` — fetch that skill's `SKILL.md`, print name/description/agents/language.
6. `skiwa install <skill> [--agent X]` — no `--agent` → `questionary.select` over the known-agent list; `gh api` download the skill folder into that agent's dir.
7. `skiwa create-skill <name>` — `questionary.checkbox` to pick language(s) (md/py/sh/js, multi-select = hybrid); clone `template_repo`, copy only the matching language stub(s) into `./<name>/`.

## Explicitly out of scope (ponytail: skip, add if asked)

- No response caching layer beyond maybe a single in-memory fetch per run — skip persistent cache until repo size makes `search` slow.
- No plugin system for arbitrary agents — fixed list, extend the table when a new agent is confirmed.
- No auth/token handling — delegate entirely to `gh`'s existing auth.

## Open items before coding starts

Still need from you: `template_repo` (or "stub for now"). `repo`/`repo_skills_path`
and all four agents' install dirs (copilot/claude/gemini/cursor) are now confirmed
and wired in.
