"""Resource lifecycle and observations for plugin catalog evidence."""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

import yaml  # type: ignore[import-untyped]

from outcomeeng.catalog.plugin_catalog import (
    BEGIN_SENTINEL,
    CATALOG_AGENT_KIND,
    CATALOG_SKILL_KIND,
    END_SENTINEL,
    MARKETPLACE_CATALOG_RELATIVE,
    MARKETPLACE_PLUGINS_FIELD,
    SOURCE_PLUGINS_ROOT,
    STRIP_PREFIXES,
    collect_plugins,
    collect_skills,
    main,
    render_catalog,
    render_target_values,
    shorten_purpose,
)
from outcomeeng.distribution.build import (
    SHARED_DIR_NAME,
    IncludeDirective,
    RuntimeTokenResolverCase,
    format_directive,
    resolve_runtime_token,
    runtime_token_resolver_cases,
)
from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    FRONTMATTER_DELIMITER,
    MARKDOWN_FILE_SUFFIX,
    SENTENCE_TERMINATOR,
    SKILL_DESCRIPTION_FIELD,
    SKILL_FILENAME,
    SKILL_NAME_FIELD,
    SKILLS_SUBDIR_NAME,
    Target,
    format_runtime_token,
)
from outcomeeng_testing.generators.source_and_templating import source_scenarios


def generated_catalog_is_deterministic() -> bool:
    first, second = source_scenarios()[:2]
    with TemporaryDirectory() as temporary_directory:
        repo_root = Path(temporary_directory)
        _write_manifest(repo_root, first.plugin, second.plugin)
        first_plugin = repo_root / SOURCE_PLUGINS_ROOT / first.plugin
        _write_skill(first_plugin / SKILLS_SUBDIR_NAME / first.skill)
        _write_agent(first_plugin / AGENTS_SUBDIR_NAME / second.skill)
        second_plugin = repo_root / SOURCE_PLUGINS_ROOT / second.plugin
        _write_skill(second_plugin / SKILLS_SUBDIR_NAME / second.skill)

        first_catalog = collect_plugins(repo_root)
        second_catalog = collect_plugins(repo_root)
        entry_kinds = {
            entry.kind for plugin in first_catalog for entry in plugin.entries
        }
        return render_catalog(first_catalog) == render_catalog(
            second_catalog
        ) and entry_kinds == {CATALOG_SKILL_KIND, CATALOG_AGENT_KIND}


def generated_catalog_uses_declared_sentinels() -> bool:
    catalog = render_catalog([])
    return catalog.startswith(f"{BEGIN_SENTINEL}\n\n") and catalog.endswith(
        f"{END_SENTINEL}\n",
    )


def check_mode_fails_when_readme_catalog_drifts() -> bool:
    first, second = source_scenarios()[:2]
    with TemporaryDirectory() as temporary_directory:
        repo_root = Path(temporary_directory)
        _write_manifest(repo_root, first.plugin, second.plugin)
        _write_drifted_readme(repo_root, first.fragment_body)
        return main(["--root", str(repo_root), "--check"]) == 1


def runtime_divergent_skill_descriptions_name_each_target() -> bool:
    with TemporaryDirectory() as temporary_directory:
        root = Path(temporary_directory)
        scenario = source_scenarios()[0]
        plugin_dir = root / scenario.plugin
        skill_dir = plugin_dir / SKILLS_SUBDIR_NAME / scenario.skill
        coordinate = _divergent_runtime_coordinate()
        _write_skill(skill_dir, coordinate=coordinate)

        (entry,) = collect_skills(plugin_dir)
        expected = render_target_values(
            {
                target: shorten_purpose(
                    f"{STRIP_PREFIXES[0]}"
                    f"{resolve_runtime_token(coordinate.kind, coordinate.capability, target.value)}"
                    f"{SENTENCE_TERMINATOR}"
                )
                for target in Target
            }
        )
        return entry.purpose == expected


def catalog_frontmatter_includes_use_shared_root() -> bool:
    with TemporaryDirectory() as temporary_directory:
        repo_root = Path(temporary_directory)
        scenario = source_scenarios()[0]
        coordinate = _divergent_runtime_coordinate()
        shared_relative = (
            Path(scenario.plugin) / f"{scenario.skill}{MARKDOWN_FILE_SUFFIX}"
        )
        shared_file = (
            repo_root / SOURCE_PLUGINS_ROOT.parent / SHARED_DIR_NAME / shared_relative
        )
        shared_file.parent.mkdir(parents=True)
        shared_file.write_text(
            _directive_description(coordinate),
            encoding="utf-8",
        )
        plugin_dir = repo_root / SOURCE_PLUGINS_ROOT / scenario.plugin
        _write_skill_with_description_include(
            plugin_dir / SKILLS_SUBDIR_NAME / scenario.skill,
            shared_relative,
        )

        (entry,) = collect_skills(plugin_dir)
        expected = render_target_values(
            {
                target: shorten_purpose(
                    f"{STRIP_PREFIXES[0]}"
                    f"{resolve_runtime_token(coordinate.kind, coordinate.capability, target.value)}"
                    f"{SENTENCE_TERMINATOR}"
                )
                for target in Target
            }
        )
        return entry.purpose == expected


def purpose_shortening_preserves_untrimmed_em_dash() -> bool:
    scenario = source_scenarios()[0]
    purpose = f"{scenario.skill} — {scenario.fragment_body.strip()}"
    return shorten_purpose(purpose) == purpose


def _write_manifest(repo_root: Path, first_plugin: str, second_plugin: str) -> None:
    manifest_path = repo_root / MARKETPLACE_CATALOG_RELATIVE
    manifest_path.parent.mkdir()
    manifest_path.write_text(
        json.dumps(
            {
                MARKETPLACE_PLUGINS_FIELD: [
                    {
                        SKILL_NAME_FIELD: second_plugin,
                        SKILL_DESCRIPTION_FIELD: second_plugin,
                    },
                    {
                        SKILL_NAME_FIELD: first_plugin,
                        SKILL_DESCRIPTION_FIELD: first_plugin,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )


def _write_skill(
    skill_dir: Path,
    *,
    coordinate: RuntimeTokenResolverCase | None = None,
) -> None:
    skill_dir.mkdir(parents=True)
    selected = coordinate or _divergent_runtime_coordinate()
    (skill_dir / SKILL_FILENAME).write_text(
        _frontmatter_document(
            skill_dir.name,
            _directive_description(selected),
        ),
        encoding="utf-8",
    )


def _write_agent(agent_path: Path) -> None:
    agent_path.parent.mkdir(parents=True)
    agent_path.with_suffix(MARKDOWN_FILE_SUFFIX).write_text(
        _frontmatter_document(
            agent_path.name,
            _directive_description(_divergent_runtime_coordinate()),
        ),
        encoding="utf-8",
    )


def _write_skill_with_description_include(
    skill_dir: Path,
    shared_relative: Path,
) -> None:
    skill_dir.mkdir(parents=True)
    directive = format_directive(IncludeDirective(path=str(shared_relative)))
    (skill_dir / SKILL_FILENAME).write_text(
        (
            f"{FRONTMATTER_DELIMITER}\n"
            f"{SKILL_NAME_FIELD}: {skill_dir.name}\n"
            f"{SKILL_DESCRIPTION_FIELD}: >-\n"
            f"  {directive}\n"
            f"{FRONTMATTER_DELIMITER}\n"
        ),
        encoding="utf-8",
    )


def _write_drifted_readme(repo_root: Path, drift: str) -> None:
    (repo_root / "README.md").write_text(
        f"{BEGIN_SENTINEL}\n{drift}{END_SENTINEL}\n",
        encoding="utf-8",
    )


def _frontmatter_document(name: str, description: str) -> str:
    frontmatter = yaml.safe_dump(
        {
            SKILL_NAME_FIELD: name,
            SKILL_DESCRIPTION_FIELD: description,
        },
        sort_keys=True,
    )
    return f"{FRONTMATTER_DELIMITER}\n{frontmatter}{FRONTMATTER_DELIMITER}\n"


def _directive_description(coordinate: RuntimeTokenResolverCase) -> str:
    kind = coordinate.kind
    capability = coordinate.capability
    return (
        f"{STRIP_PREFIXES[0]}{format_runtime_token(kind, capability)}"
        f"{SENTENCE_TERMINATOR}"
    )


def _divergent_runtime_coordinate() -> RuntimeTokenResolverCase:
    grouped: dict[tuple[str, str], set[str]] = {}
    for coordinate in runtime_token_resolver_cases():
        grouped.setdefault((coordinate.kind, coordinate.capability), set()).add(
            coordinate.runtime
        )
    kind, capability = next(
        key
        for key, runtimes in grouped.items()
        if runtimes == {target.value for target in Target}
        and len(
            {resolve_runtime_token(key[0], key[1], target.value) for target in Target}
        )
        == len(Target)
    )
    return next(
        coordinate
        for coordinate in runtime_token_resolver_cases()
        if coordinate.kind == kind and coordinate.capability == capability
    )
