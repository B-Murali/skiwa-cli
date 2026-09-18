"""Smoke test for skiwa's front-matter parsing and local scan (ponytail: one
runnable check for non-trivial logic, no framework)."""
import base64
import json
import subprocess
import tempfile
from pathlib import Path
from unittest import mock

from skiwa import gh, remote
from skiwa.cli import _matches_query
from skiwa.frontmatter import parse_front_matter, strip_front_matter
from skiwa.local import scan_installed


def test_frontmatter():
    text = (
        "---\n"
        "name: my-skill\n"
        "description: >\n"
        "  does a thing\n"
        "  across lines\n"
        "agents: [copilot, claude]\n"
        "---\n"
        "body\n"
    )
    meta = parse_front_matter(text)
    assert meta["name"] == "my-skill"
    assert meta["description"] == "does a thing across lines"
    assert meta["agents"] == ["copilot", "claude"]
    assert parse_front_matter("no front matter here") == {}


def test_scan_installed():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        skill_dir = base / "demo-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: demo-skill\ndescription: test skill\nagents: [copilot]\n---\n"
        )
        import skiwa.config as config

        original = config.AGENT_DIRS["copilot"]
        config.AGENT_DIRS["copilot"] = base
        try:
            results = scan_installed("copilot")
            assert len(results) == 1
            assert results[0].name == "demo-skill"
            assert results[0].description == "test skill"
        finally:
            config.AGENT_DIRS["copilot"] = original


def test_gh_path():
    # PATH gh wins when present.
    with mock.patch("shutil.which", return_value="/usr/local/bin/gh"):
        assert gh.gh_path() == "/usr/local/bin/gh"
    # Falls back to the bundled binary when nothing's on PATH and it exists.
    with mock.patch("shutil.which", return_value=None), mock.patch.object(
        type(gh.GH_BIN), "exists", return_value=True
    ):
        assert gh.gh_path() == str(gh.GH_BIN)
    # Neither available -> empty string, not an exception.
    with mock.patch("shutil.which", return_value=None), mock.patch.object(
        type(gh.GH_BIN), "exists", return_value=False
    ):
        assert gh.gh_path() == ""


def test_strip_front_matter():
    text = "---\nname: my-skill\n---\nbody line\n"
    assert strip_front_matter(text) == "body line"
    assert strip_front_matter("no front matter here") == "no front matter here"


def test_matches_query():
    skill = {
        "id": "drawio-skills/drawio",
        "name": "drawio",
        "description": "Generate draw.io diagrams",
        "keywords": ["diagram", "architecture"],
    }
    assert _matches_query(skill, "diagram")
    assert _matches_query(skill, "DRAWIO")
    assert _matches_query(skill, "architecture")
    assert not _matches_query(skill, "unrelated-topic")


def _fake_contents_response(payload: dict) -> mock.Mock:
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii")
    result = mock.Mock()
    result.stdout = json.dumps({"content": encoded, "encoding": "base64"})
    return result


def test_remote_fetch_index():
    index = {"schemaVersion": 1, "skills": [{"id": "a/b", "name": "b"}]}
    with mock.patch("skiwa.gh.run", return_value=_fake_contents_response(index)):
        assert remote.fetch_index() == index

    # A non-zero `gh` exit (e.g. 404) surfaces as a RemoteError, not a crash.
    def raise_err(*_a, **_k):
        raise subprocess.CalledProcessError(1, ["gh"], stderr="404 Not Found")

    with mock.patch("skiwa.gh.run", side_effect=raise_err):
        try:
            remote.fetch_index()
            raise AssertionError("expected RemoteError")
        except remote.RemoteError:
            pass


def test_agent_dirs_config():
    from skiwa import config

    # Normal load: every known agent resolves to real Path(s), home-relative.
    for agent, dirs in config.AGENT_DIRS.items():
        assert dirs, f"{agent} should have resolved dirs"
        dirs_list = dirs if isinstance(dirs, list) else [dirs]
        assert all(isinstance(p, Path) for p in dirs_list)

    # A missing/unreadable agent_dirs.json falls back to built-in defaults
    # instead of crashing.
    with mock.patch.object(Path, "read_text", side_effect=OSError("gone")):
        data = config._load_agent_dirs_data()
        assert data == config._FALLBACK_AGENT_DIRS_DATA

    # Malformed JSON also falls back cleanly.
    with mock.patch.object(Path, "read_text", return_value="{ not json"):
        data = config._load_agent_dirs_data()
        assert data == config._FALLBACK_AGENT_DIRS_DATA

    # A missing 'agents' key falls back cleanly too.
    with mock.patch.object(Path, "read_text", return_value=json.dumps({"shared_alias": []})):
        data = config._load_agent_dirs_data()
        assert data == config._FALLBACK_AGENT_DIRS_DATA


if __name__ == "__main__":
    test_frontmatter()
    test_scan_installed()
    test_gh_path()
    test_strip_front_matter()
    test_matches_query()
    test_remote_fetch_index()
    test_agent_dirs_config()
    print("ok")
