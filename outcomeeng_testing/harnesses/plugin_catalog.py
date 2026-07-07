"""Harnesses for plugin catalog evidence tests."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.catalog.plugin_catalog import (
    BEGIN_SENTINEL,
    END_SENTINEL,
    SOURCE_PLUGINS_ROOT,
    collect_plugins,
    collect_skills,
    main,
    render_catalog,
    shorten_purpose,
)

PLUGIN_NAME = "example"
SECOND_PLUGIN_NAME = "sample"
SKILL_NAME = "create-example"
SECOND_SKILL_NAME = "audit-example"


def generated_catalog_is_deterministic() -> bool:
    with TemporaryDirectory() as tmp:
        repo_root = Path(tmp)
        _write_manifest(repo_root)
        _write_skill(
            repo_root / SOURCE_PLUGINS_ROOT / PLUGIN_NAME / "skills" / SKILL_NAME
        )
        _write_skill(
            repo_root
            / SOURCE_PLUGINS_ROOT
            / SECOND_PLUGIN_NAME
            / "skills"
            / SECOND_SKILL_NAME,
            skill_name=SECOND_SKILL_NAME,
        )

        return render_catalog(collect_plugins(repo_root)) == render_catalog(
            collect_plugins(repo_root)
        )


def generated_catalog_uses_declared_sentinels() -> bool:
    catalog = render_catalog([])
    return catalog.startswith(f"{BEGIN_SENTINEL}\n\n") and catalog.endswith(
        f"{END_SENTINEL}\n",
    )


def check_mode_fails_when_readme_catalog_drifts() -> bool:
    with TemporaryDirectory() as tmp:
        repo_root = Path(tmp)
        _write_manifest(repo_root)
        _write_drifted_readme(repo_root)

        return main(["--root", str(repo_root), "--check"]) == 1


def runtime_divergent_skill_descriptions_name_each_target() -> bool:
    with TemporaryDirectory() as tmp:
        plugin_dir = Path(tmp) / "plugin"
        skill_dir = plugin_dir / "skills" / SKILL_NAME
        _write_skill(skill_dir)

        (entry,) = collect_skills(plugin_dir)
        return entry.purpose == (
            "Claude: Creating subagents; Codex: Creating custom agents"
        )


def purpose_shortening_preserves_untrimmed_em_dash() -> bool:
    return shorten_purpose("Build — ships runtime output") == (
        "Build — ships runtime output"
    )


def _write_manifest(repo_root: Path) -> None:
    manifest_path = repo_root / ".claude-plugin" / "marketplace.json"
    manifest_path.parent.mkdir()
    manifest_path.write_text(
        (
            '{"plugins": ['
            '{"name": "sample", "description": "Sample plugin."},'
            '{"name": "example", "description": "Example plugin."}'
            "]}\n"
        ),
        encoding="utf-8",
    )


def _write_skill(skill_dir: Path, *, skill_name: str = SKILL_NAME) -> None:
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text(
        f"""---
name: {skill_name}
description: >-
  ALWAYS invoke this skill when creating {{{{! term('configured_agents') !}}}}.
---

<objective>
Example output.
</objective>
""",
        encoding="utf-8",
    )


def _write_drifted_readme(repo_root: Path) -> None:
    (repo_root / "README.md").write_text(
        f"# README\n\n{BEGIN_SENTINEL}\n\nstale\n{END_SENTINEL}\n",
        encoding="utf-8",
    )
