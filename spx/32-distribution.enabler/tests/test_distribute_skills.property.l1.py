"""Level 1 property tests for scripts/distribute_skills.py."""

from __future__ import annotations

import tempfile
from pathlib import Path

from hypothesis import given, settings
from hypothesis import strategies as st

from outcomeeng.scripts import distribute_skills

FRONTMATTER_MINIMAL = """\
---
name: my-skill
description: A simple skill
---

Content here.
"""


def _create_skill(
    plugins_dir: Path,
    plugin_name: str,
    skill_name: str,
    *,
    frontmatter: str = FRONTMATTER_MINIMAL,
) -> Path:
    skill_dir = plugins_dir / plugin_name / "skills" / skill_name
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(frontmatter)
    return skill_dir


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
def test_collect_skills_returns_union(plugin_skills: dict[str, list[str]]) -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        plugins_dir = tmp_path / "plugins"

        expected_dirs: set[str] = set()
        for plugin_name, skill_names in plugin_skills.items():
            for skill_name in skill_names:
                _create_skill(plugins_dir, plugin_name, skill_name)
                expected_dirs.add(skill_name)

        original = distribute_skills.MONOREPO_ROOT
        distribute_skills.MONOREPO_ROOT = tmp_path
        try:
            result = distribute_skills.collect_skills(list(plugin_skills.keys()))
        finally:
            distribute_skills.MONOREPO_ROOT = original

        result_dirs = {skill["dir_name"] for skill in result}
        assert result_dirs == expected_dirs
