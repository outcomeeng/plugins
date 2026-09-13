"""Real template renders around isolated catalog and role changes."""

from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from hypothesis import given

from outcomeeng.distribution.build import SHARED_DIR_NAME, render_text
from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    PLUGINS_DIR_NAME,
    SOURCE_ROOT_NAME,
    Target,
)
from outcomeeng.distribution.installation import (
    CATALOG_PLUGIN_NAME_FIELD,
    CATALOG_PLUGINS_FIELD,
    CLAUDE_CATALOG_PATH,
    CODEX_CATALOG_PATH,
)
from outcomeeng.distribution.instruction_block import (
    AUTHORED_TEMPLATE_PATH,
    AUTHORIZED_PLUGIN_LIST_PREFIX,
    load_instruction_block_module,
)
from outcomeeng_testing.generators.plugin_authorization import (
    PluginAuthorizationCase,
    plugin_authorization_cases,
)
from outcomeeng_testing.harnesses.instruction_block import (
    run_instruction_block_property,
)


@dataclass(frozen=True)
class PluginAuthorizationObservation:
    catalog: tuple[str, ...]
    additional_plugin: str
    initial_document: str
    role_added_document: str
    plugin_added_document: str
    initial_plugins: tuple[str, ...]
    updated_plugins: tuple[str, ...]


def _write_catalog(path: Path, names: tuple[str, ...]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                CATALOG_PLUGINS_FIELD: [
                    {CATALOG_PLUGIN_NAME_FIELD: name} for name in names
                ]
            }
        ),
        encoding="utf-8",
    )


def _listed_plugins(document: str) -> tuple[str, ...]:
    return tuple(
        name
        for line in document.splitlines()
        if line.startswith(AUTHORIZED_PLUGIN_LIST_PREFIX)
        for name in line.removeprefix(AUTHORIZED_PLUGIN_LIST_PREFIX)
        .strip()
        .removesuffix(".")
        .split(", ")
    )


def for_all_plugin_authorization_changes(
    assertion: Callable[[PluginAuthorizationObservation], None],
) -> None:
    module = load_instruction_block_module()
    authored = AUTHORED_TEMPLATE_PATH.read_text(encoding="utf-8")
    catalog_paths = {
        Target.CLAUDE: CLAUDE_CATALOG_PATH,
        Target.CODEX: CODEX_CATALOG_PATH,
    }

    @given(case=plugin_authorization_cases())
    def generated_assertion(case: PluginAuthorizationCase) -> None:
        with TemporaryDirectory() as directory:
            checkout = Path(directory)
            source_root = checkout / SOURCE_ROOT_NAME
            shared_root = source_root / SHARED_DIR_NAME
            shared_root.mkdir(parents=True)
            for target, names in case.catalogs.items():
                _write_catalog(checkout / catalog_paths[target], names)

            def render(target: Target) -> str:
                rendered = render_text(
                    authored,
                    shared_root=shared_root,
                    variables={"target": target.value},
                )
                version = module.parse_template_version(rendered)
                if version is None:
                    raise ValueError("authorization template has no version")
                return module.render(rendered, (), version, target.value)

            initial = {target: render(target) for target in Target}
            for names in case.catalogs.values():
                agents = source_root / PLUGINS_DIR_NAME / names[0] / AGENTS_SUBDIR_NAME
                agents.mkdir(parents=True, exist_ok=True)
                (agents / f"{case.additional_role}.md").write_text(
                    f"---\nname: {case.additional_role}\ndescription: Inspect the requested artifact.\n---\n",
                    encoding="utf-8",
                )
            role_added = {target: render(target) for target in Target}
            for target, names in case.catalogs.items():
                _write_catalog(
                    checkout / catalog_paths[target], (*names, case.additional_plugin)
                )
            for target, names in case.catalogs.items():
                plugin_added = render(target)
                assertion(
                    PluginAuthorizationObservation(
                        catalog=names,
                        additional_plugin=case.additional_plugin,
                        initial_document=initial[target],
                        role_added_document=role_added[target],
                        plugin_added_document=plugin_added,
                        initial_plugins=_listed_plugins(initial[target]),
                        updated_plugins=_listed_plugins(plugin_added),
                    )
                )

    run_instruction_block_property(
        generated_assertion,
        replay_path="just test spx/21-spec-tree.enabler/43-instruction-block.enabler/tests/test_plugin_authorization.property.l1.py",
    )
