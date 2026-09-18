"""Smoke test for skiwa's front-matter parsing and local scan (ponytail: one
runnable check for non-trivial logic, no framework)."""
import tempfile
from pathlib import Path
from unittest import mock

from skiwa import gh
from skiwa.frontmatter import parse_front_matter
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

        config.AGENT_DIRS["copilot"] = base
        results = scan_installed("copilot")
        assert len(results) == 1
        assert results[0].name == "demo-skill"
        assert results[0].description == "test skill"


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


if __name__ == "__main__":
    test_frontmatter()
    test_scan_installed()
    test_gh_path()
    print("ok")
