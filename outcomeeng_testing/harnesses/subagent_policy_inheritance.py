"""Harness for subagent execution-policy inheritance evidence.

The harness renders each authored agent definition's frontmatter once per
target and reports which fields each rendering declares. It returns
observations and the spec-declared names only; the linked test owns every
classification and verdict.
"""

from __future__ import annotations

import re
import shutil
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Final, cast

import yaml

from outcomeeng.distribution.agents import AGENT_TOOLS_FIELD, NATIVE_PERMISSION_FIELDS
from outcomeeng.distribution.build import _render_variables, render_text
from outcomeeng.distribution.contracts import FRONTMATTER_DELIMITER, Target
from outcomeeng_testing.harnesses.agent_conversion import (
    PRODUCT_TREE_AGENT_SOURCE_DIR,
)
from outcomeeng_testing.harnesses.distribution import REPOSITORY_ROOT

AUTHORED_AGENT_DEFINITIONS_DIRECTORY: Final = PRODUCT_TREE_AGENT_SOURCE_DIR
INHERITANCE_SPEC_PATH: Final = (
    REPOSITORY_ROOT / "spx" / "21-product-tree.enabler" / "product-tree.md"
)
INHERITANCE_ASSERTION_ANCHOR: Final = (
    "inherits the invoking session's execution policy in that rendering"
)
FIXTURES_DIRECTORY: Final = (
    Path(__file__).resolve().parents[1] / "fixtures" / "subagent_policy_inheritance"
)
CONFORMING_FIXTURE_NAME: Final = "inheriting-conforming"
UNDECLARED_INHERITING_FIXTURE_NAME: Final = "inheriting-undeclared"
NATIVE_FIELD_FIXTURE_NAME: Final = "native-field-declared"
NO_ALLOWLIST_FIXTURE_NAME: Final = "no-tools-allowlist"
FIXTURE_NAMES: Final = (
    CONFORMING_FIXTURE_NAME,
    UNDECLARED_INHERITING_FIXTURE_NAME,
    NATIVE_FIELD_FIXTURE_NAME,
    NO_ALLOWLIST_FIXTURE_NAME,
)
DEFINITION_SUFFIX: Final = ".md"
_BACKTICKED_NAME: Final = re.compile(r"`([a-z][a-z0-9-]*)`")


@dataclass(frozen=True)
class RenderingObservation:
    """The fields one target's rendering of a definition declares."""

    declares_tools_allowlist: bool
    declares_native_permission_field: bool


@dataclass(frozen=True)
class DefinitionObservation:
    """One authored definition observed in every target's rendering."""

    name: str
    renderings: Mapping[Target, RenderingObservation]


def observe_definitions(directory: Path) -> tuple[DefinitionObservation, ...]:
    """Observe every definition file under ``directory`` in each rendering."""
    return tuple(
        DefinitionObservation(
            name=path.stem,
            renderings={
                target: _observe_rendering(path.read_text(encoding="utf-8"), target)
                for target in Target
            },
        )
        for path in sorted(directory.glob(f"*{DEFINITION_SUFFIX}"))
    )


def declared_inheriting_names(
    spec_path: Path = INHERITANCE_SPEC_PATH,
) -> frozenset[str]:
    """Read the definition names the owning spec's inheritance assertion lists."""
    assertions = [
        line
        for line in spec_path.read_text(encoding="utf-8").splitlines()
        if INHERITANCE_ASSERTION_ANCHOR in line
    ]
    if len(assertions) != 1:
        raise ValueError(
            f"{spec_path}: expected one inheritance assertion, found {len(assertions)}"
        )
    declaration = assertions[0].partition(INHERITANCE_ASSERTION_ANCHOR)[0]
    return frozenset(_BACKTICKED_NAME.findall(declaration))


def copy_fixture_definitions(destination: Path, names: tuple[str, ...]) -> Path:
    """Copy the named inert fixture definitions into ``destination``."""
    destination.mkdir(parents=True, exist_ok=True)
    for name in names:
        shutil.copyfile(
            FIXTURES_DIRECTORY / f"{name}{DEFINITION_SUFFIX}",
            destination / f"{name}{DEFINITION_SUFFIX}",
        )
    return destination


def _observe_rendering(text: str, target: Target) -> RenderingObservation:
    frontmatter = _rendered_frontmatter(text, target)
    return RenderingObservation(
        declares_tools_allowlist=AGENT_TOOLS_FIELD in frontmatter,
        declares_native_permission_field=NATIVE_PERMISSION_FIELDS[target]
        in frontmatter,
    )


def _rendered_frontmatter(text: str, target: Target) -> Mapping[str, object]:
    opener = f"{FRONTMATTER_DELIMITER}\n"
    closer = f"\n{FRONTMATTER_DELIMITER}"
    if not text.startswith(opener) or closer not in text:
        raise ValueError("expected YAML frontmatter delimiters")
    block = text[: text.index(closer, len(opener)) + len(closer)]
    rendered = render_text(block, variables=_render_variables(target))
    loaded = yaml.safe_load(rendered.removeprefix(opener).removesuffix(closer))
    if not isinstance(loaded, Mapping):
        raise ValueError("expected a YAML mapping in the frontmatter")
    return cast("Mapping[str, object]", loaded)
