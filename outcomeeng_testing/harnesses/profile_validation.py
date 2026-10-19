"""Authored-source fixtures for native configuration rejection."""

from dataclasses import dataclass
from pathlib import Path
import json

from outcomeeng.distribution.build import SHARED_DIR_NAME, TEMPLATES_DIR_NAME
from outcomeeng.distribution.contracts import (
    FRONTMATTER_DELIMITER,
    PLUGINS_DIR_NAME,
    SKILL_FILENAME,
    SOURCE_ROOT_NAME,
    Target,
    format_target_conditional,
)
from outcomeeng.distribution.profiles import (
    MODEL_IDENTIFIERS,
    NATIVE_CONFIGURATION_FIELDS,
)
from outcomeeng_testing.generators.profile_binding import (
    LITERAL_BINDING,
    PROFILE_DESCRIPTION_TOKEN,
)
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

_AUTHORED_SOURCE_DIRECTORIES = tuple(
    Path(SOURCE_ROOT_NAME) / name
    for name in (SHARED_DIR_NAME, PLUGINS_DIR_NAME, TEMPLATES_DIR_NAME)
)
_LITERAL_DIRECTORY = "literal"
_MODEL_FILE_DIRECTORY = "model-identifiers"


@dataclass(frozen=True)
class WrittenLiteral:
    """One literal the guard reports: the file and 1-based line the harness wrote."""

    path: Path
    line: int


def write_configuration_overrides(root: Path) -> tuple[Path, ...]:
    """Place native overrides inside every harness conditional and skill frontmatter."""
    paths: list[Path] = []
    for directory in _AUTHORED_SOURCE_DIRECTORIES:
        for target in Target:
            for field in sorted(NATIVE_CONFIGURATION_FIELDS):
                path = root / directory / target.value / field / SKILL_FILENAME
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    f"{FRONTMATTER_DELIMITER}\n"
                    + f"{field}: {json.dumps(PROFILE_DESCRIPTION_TOKEN)}\n"
                    + f"{FRONTMATTER_DELIMITER}\n"
                    + format_target_conditional(target, f"{field} = {LITERAL_BINDING}")
                    + "\n",
                    encoding="utf-8",
                )
                paths.append(path)
    return tuple(paths)


def write_literal_overrides(root: Path) -> tuple[WrittenLiteral, ...]:
    """Write literal frontmatter overrides and literal model identifiers under src.

    Return the path and line of every literal the harness wrote, in layout order.
    """
    base = root / SOURCE_ROOT_NAME / PLUGINS_DIR_NAME
    written: list[WrittenLiteral] = []
    for field in sorted(NATIVE_CONFIGURATION_FIELDS):
        path = base / _LITERAL_DIRECTORY / field / SKILL_FILENAME
        path.parent.mkdir(parents=True, exist_ok=True)
        lines = [
            FRONTMATTER_DELIMITER,
            f"{field}: {LITERAL_BINDING}",
            FRONTMATTER_DELIMITER,
        ]
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(
            WrittenLiteral(path, lines.index(f"{field}: {LITERAL_BINDING}") + 1)
        )
    model_path = base / _MODEL_FILE_DIRECTORY / SKILL_FILENAME
    model_path.parent.mkdir(parents=True, exist_ok=True)
    identifiers = sorted(MODEL_IDENTIFIERS)
    model_path.write_text(
        "\n".join(f"Select {identifier} here." for identifier in identifiers) + "\n",
        encoding="utf-8",
    )
    written.extend(
        WrittenLiteral(model_path, number) for number in range(1, len(identifiers) + 1)
    )
    return tuple(written)


def prepare_profile_build(
    root: Path, field: str, value: str, *, skill: bool = False
) -> tuple[Path, Path]:
    """Materialize one invalid authoring input beside existing generated state."""
    encoded_value = json.dumps(value).replace("{", "\\u007b")
    content = (
        "---\nname: reviewer\ndescription: Review.\n"
        + f"{field}: {encoded_value}\n---\nReview.\n"
    )
    builder = SrcTreeBuilder(root)
    builder.add_plugin(
        "sample",
        skills={"reviewer": content} if skill else None,
        agents=None if skill else {"reviewer": content},
    )
    dist_root = root / "dist"
    existing = dist_root / Target.CLAUDE.value / "sentinel.txt"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("Existing generated output.\n", encoding="utf-8")
    return builder.src_root, dist_root
