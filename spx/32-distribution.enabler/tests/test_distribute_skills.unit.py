"""Level 1 tests for scripts/distribute_skills.py.

Tests pure computation and file I/O functions using temp directories.
Git/subprocess functions (clone_or_fetch, commit_and_push) are Level 2.
"""

from __future__ import annotations

import os
import textwrap
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from outcomeeng.scripts import distribute_skills


# =============================================================================
# Constants
# =============================================================================

FRONTMATTER_WITH_DIRECTIVE = textwrap.dedent("""\
    ---
    name: testing-python
    description: >-
      ALWAYS invoke this skill when writing Python tests.
      NEVER write tests without this skill.
    ---

    # Testing Python
""")

FRONTMATTER_MINIMAL = textwrap.dedent("""\
    ---
    name: my-skill
    description: A simple skill
    ---

    Content here.
""")

FRONTMATTER_MISSING = "# No frontmatter here\n\nJust content.\n"

DIRECTIVE_ALWAYS_NEVER = (
    "ALWAYS invoke this skill when writing Python tests. "
    "NEVER write tests without this skill."
)
DIRECTIVE_ALWAYS_ONLY = "ALWAYS invoke this skill when reviewing code."
PLAIN_DESCRIPTION = "A simple skill for testing."
EMPTY_DESCRIPTION = ""

EXPECTED_CLEAN_ALWAYS_NEVER = "writing Python tests"
EXPECTED_CLEAN_ALWAYS_ONLY = "reviewing code"


# =============================================================================
# Test parse_skill_frontmatter()
# =============================================================================


class TestParseSkillFrontmatter:
    """Test YAML frontmatter extraction from SKILL.md files."""

    def test_extracts_name_and_description(self, tmp_path: Path) -> None:
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text(FRONTMATTER_WITH_DIRECTIVE)

        result = distribute_skills.parse_skill_frontmatter(skill_md)

        assert result["name"] == "testing-python"
        assert "ALWAYS" in result["description"]

    def test_returns_empty_dict_without_frontmatter(self, tmp_path: Path) -> None:
        skill_md = tmp_path / "SKILL.md"
        skill_md.write_text(FRONTMATTER_MISSING)

        result = distribute_skills.parse_skill_frontmatter(skill_md)

        assert result == {}

    def test_falls_back_to_directory_name(self, tmp_path: Path) -> None:
        """When frontmatter has no 'name' field, uses parent dir name."""
        skill_dir = tmp_path / "my-skill-dir"
        skill_dir.mkdir()
        skill_md = skill_dir / "SKILL.md"
        skill_md.write_text("---\ndescription: something\n---\n")

        result = distribute_skills.parse_skill_frontmatter(skill_md)

        assert result["name"] == "my-skill-dir"


# =============================================================================
# Test clean_description()
# =============================================================================


class TestCleanDescription:
    """Test directive stripping from skill descriptions."""

    def test_strips_always_never_pattern(self) -> None:
        result = distribute_skills.clean_description(DIRECTIVE_ALWAYS_NEVER)

        assert result == EXPECTED_CLEAN_ALWAYS_NEVER

    def test_strips_always_only_pattern(self) -> None:
        result = distribute_skills.clean_description(DIRECTIVE_ALWAYS_ONLY)

        assert result == EXPECTED_CLEAN_ALWAYS_ONLY

    def test_returns_first_sentence_for_plain_description(self) -> None:
        result = distribute_skills.clean_description(PLAIN_DESCRIPTION)

        assert result == "A simple skill for testing"

    def test_handles_empty_description(self) -> None:
        result = distribute_skills.clean_description(EMPTY_DESCRIPTION)

        assert result == ""


# =============================================================================
# Test collect_skills()
# =============================================================================


class TestCollectSkills:
    """Test skill collection from plugin directories."""

    def _create_skill(
        self,
        plugins_dir: Path,
        plugin_name: str,
        skill_name: str,
        *,
        frontmatter: str = FRONTMATTER_MINIMAL,
    ) -> Path:
        """Helper to create a skill directory with SKILL.md."""
        skill_dir = plugins_dir / plugin_name / "skills" / skill_name
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(frontmatter)
        return skill_dir

    def test_collects_skills_from_plugin(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plugins_dir = tmp_path / "plugins"
        self._create_skill(plugins_dir, "test-plugin", "skill-a")
        self._create_skill(plugins_dir, "test-plugin", "skill-b")
        monkeypatch.setattr(distribute_skills, "MONOREPO_ROOT", tmp_path)

        result = distribute_skills.collect_skills(["test-plugin"])

        assert len(result) == 2
        names = {s["dir_name"] for s in result}
        assert names == {"skill-a", "skill-b"}

    def test_skips_plugin_without_skills_dir(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plugins_dir = tmp_path / "plugins"
        plugins_dir.mkdir(parents=True)
        monkeypatch.setattr(distribute_skills, "MONOREPO_ROOT", tmp_path)

        result = distribute_skills.collect_skills(["nonexistent-plugin"])

        assert result == []

    def test_skips_skill_without_skill_md(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plugins_dir = tmp_path / "plugins" / "test-plugin" / "skills" / "bad-skill"
        plugins_dir.mkdir(parents=True)
        monkeypatch.setattr(distribute_skills, "MONOREPO_ROOT", tmp_path)

        result = distribute_skills.collect_skills(["test-plugin"])

        assert result == []

    def test_collects_from_multiple_plugins(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        plugins_dir = tmp_path / "plugins"
        self._create_skill(plugins_dir, "plugin-a", "skill-1")
        self._create_skill(plugins_dir, "plugin-b", "skill-2")
        monkeypatch.setattr(distribute_skills, "MONOREPO_ROOT", tmp_path)

        result = distribute_skills.collect_skills(["plugin-a", "plugin-b"])

        assert len(result) == 2

    @given(
        plugin_skills=st.dictionaries(
            keys=st.from_regex(r"[a-z]{2,8}", fullmatch=True),
            values=st.lists(
                st.from_regex(r"[a-z]{2,8}", fullmatch=True),
                min_size=1,
                max_size=4,
                unique=True,
            ),
            min_size=1,
            max_size=4,
        )
    )
    @settings(max_examples=50)
    def test_collect_skills_returns_union(
        self, plugin_skills: dict[str, list[str]]
    ) -> None:
        """For any combination of plugins with skills, collect_skills returns the union."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            plugins_dir = tmp_path / "plugins"

            expected_dirs: set[str] = set()
            for plugin_name, skill_names in plugin_skills.items():
                for skill_name in skill_names:
                    self._create_skill(plugins_dir, plugin_name, skill_name)
                    expected_dirs.add(skill_name)

            original = distribute_skills.MONOREPO_ROOT
            distribute_skills.MONOREPO_ROOT = tmp_path
            try:
                result = distribute_skills.collect_skills(list(plugin_skills.keys()))
            finally:
                distribute_skills.MONOREPO_ROOT = original

            result_dirs = {s["dir_name"] for s in result}
            assert result_dirs == expected_dirs


# =============================================================================
# Test _ignore_broken_symlinks()
# =============================================================================


class TestIgnoreBrokenSymlinks:
    """Test broken symlink detection during copytree."""

    def test_ignores_broken_symlink(self, tmp_path: Path) -> None:
        broken_link = tmp_path / "broken.md"
        broken_link.symlink_to("/nonexistent/target")

        result = distribute_skills._ignore_broken_symlinks(str(tmp_path), ["broken.md"])

        assert result == {"broken.md"}

    def test_keeps_valid_symlink(self, tmp_path: Path) -> None:
        target = tmp_path / "real-file.md"
        target.write_text("content")
        link = tmp_path / "valid-link.md"
        link.symlink_to(target)

        result = distribute_skills._ignore_broken_symlinks(
            str(tmp_path), ["valid-link.md"]
        )

        assert result == set()

    def test_keeps_regular_files(self, tmp_path: Path) -> None:
        regular = tmp_path / "regular.md"
        regular.write_text("content")

        result = distribute_skills._ignore_broken_symlinks(
            str(tmp_path), ["regular.md"]
        )

        assert result == set()

    def test_handles_mixed_contents(self, tmp_path: Path) -> None:
        """Mix of regular files, valid symlinks, and broken symlinks."""
        regular = tmp_path / "regular.md"
        regular.write_text("content")

        target = tmp_path / "target.md"
        target.write_text("target content")
        valid_link = tmp_path / "valid-link.md"
        valid_link.symlink_to(target)

        broken_link = tmp_path / "broken.md"
        broken_link.symlink_to("/nonexistent")

        result = distribute_skills._ignore_broken_symlinks(
            str(tmp_path), ["regular.md", "valid-link.md", "broken.md"]
        )

        assert result == {"broken.md"}


# =============================================================================
# Test copy_skill()
# =============================================================================


class TestCopySkill:
    """Test skill directory copying with broken symlink handling."""

    def test_copies_skill_directory(self, tmp_path: Path) -> None:
        source = tmp_path / "source" / "my-skill"
        source.mkdir(parents=True)
        (source / "SKILL.md").write_text("# My Skill")
        (source / "references").mkdir()
        (source / "references" / "ref.md").write_text("reference")
        dest = tmp_path / "dest"
        dest.mkdir()

        skill = {"source": source, "dir_name": "my-skill"}
        distribute_skills.copy_skill(skill, dest)

        assert (dest / "my-skill" / "SKILL.md").read_text() == "# My Skill"
        assert (dest / "my-skill" / "references" / "ref.md").read_text() == "reference"

    def test_skips_broken_symlinks_during_copy(self, tmp_path: Path) -> None:
        source = tmp_path / "source" / "my-skill"
        refs = source / "references"
        refs.mkdir(parents=True)
        (source / "SKILL.md").write_text("# Skill")
        (refs / "good.md").write_text("good reference")
        (refs / "broken.md").symlink_to("/nonexistent/file.md")
        dest = tmp_path / "dest"
        dest.mkdir()

        skill = {"source": source, "dir_name": "my-skill"}
        distribute_skills.copy_skill(skill, dest)

        assert (dest / "my-skill" / "SKILL.md").exists()
        assert (dest / "my-skill" / "references" / "good.md").exists()
        assert not (dest / "my-skill" / "references" / "broken.md").exists()


# =============================================================================
# Test clear_repo_contents()
# =============================================================================


class TestClearRepoContents:
    """Test clearing repo contents while preserving .git."""

    def test_removes_files_and_dirs(self, tmp_path: Path) -> None:
        (tmp_path / ".git").mkdir()
        (tmp_path / "README.md").write_text("readme")
        (tmp_path / "skills").mkdir()
        (tmp_path / "skills" / "SKILL.md").write_text("skill")

        distribute_skills.clear_repo_contents(tmp_path)

        assert (tmp_path / ".git").exists()
        assert not (tmp_path / "README.md").exists()
        assert not (tmp_path / "skills").exists()

    def test_preserves_git_directory(self, tmp_path: Path) -> None:
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git config")

        distribute_skills.clear_repo_contents(tmp_path)

        assert (git_dir / "config").read_text() == "git config"


# =============================================================================
# Test generate_readme()
# =============================================================================


class TestGenerateReadme:
    """Test README generation for downstream repos."""

    REPO_NAME = "foundation"
    REPO_CONFIG: dict = {
        "description": "Foundation skills for all projects",
        "plugins": ["test"],
    }
    GITHUB_ORG = "outcomeeng"

    def test_includes_repo_name_and_description(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(distribute_skills, "README_TEMPLATE", Path("/nonexistent"))
        skills: list[dict] = [{"name": "testing", "description": "Test skill"}]

        result = distribute_skills.generate_readme(
            self.REPO_NAME, self.REPO_CONFIG, skills, self.GITHUB_ORG
        )

        assert "foundation" in result
        assert "Foundation skills for all projects" in result

    def test_includes_skill_table(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(distribute_skills, "README_TEMPLATE", Path("/nonexistent"))
        skills: list[dict] = [
            {"name": "testing", "description": "A simple test skill."},
            {"name": "writing-prose", "description": "Write prose."},
        ]

        result = distribute_skills.generate_readme(
            self.REPO_NAME, self.REPO_CONFIG, skills, self.GITHUB_ORG
        )

        assert "| `testing` |" in result
        assert "| `writing-prose` |" in result

    def test_includes_install_command(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(distribute_skills, "README_TEMPLATE", Path("/nonexistent"))
        skills: list[dict] = [{"name": "testing", "description": "desc"}]

        result = distribute_skills.generate_readme(
            self.REPO_NAME, self.REPO_CONFIG, skills, self.GITHUB_ORG
        )

        assert "npx skills add outcomeeng/foundation" in result

    def test_includes_prerequisites(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setattr(distribute_skills, "README_TEMPLATE", Path("/nonexistent"))
        config = {
            "description": "TypeScript skills",
            "plugins": ["typescript"],
            "prerequisites": ["outcomeeng/foundation (for /testing)"],
        }
        skills: list[dict] = [{"name": "testing-ts", "description": "desc"}]

        result = distribute_skills.generate_readme(
            "typescript", config, skills, self.GITHUB_ORG
        )

        assert "Prerequisites" in result
        assert "outcomeeng/foundation" in result
