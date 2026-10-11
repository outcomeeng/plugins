"""Authored-source fixtures for native configuration rejection."""

from pathlib import Path
import json

from outcomeeng.distribution.contracts import (
    FRONTMATTER_DELIMITER,
    Target,
    format_target_conditional,
)
from outcomeeng.distribution.profiles import NATIVE_CONFIGURATION_FIELDS
from outcomeeng_testing.generators.profile_binding import PROFILE_DESCRIPTION_TOKEN
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

_AUTHORED_SOURCE_DIRECTORIES = (
    Path("src/_shared"),
    Path("src/plugins"),
    Path("src/templates"),
)


def write_configuration_overrides(root: Path) -> tuple[Path, ...]:
    """Place native overrides inside every harness conditional and skill frontmatter."""
    paths: list[Path] = []
    for directory in _AUTHORED_SOURCE_DIRECTORIES:
        for target in Target:
            for field in sorted(NATIVE_CONFIGURATION_FIELDS):
                path = root / directory / target.value / field / "SKILL.md"
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(
                    f"{FRONTMATTER_DELIMITER}\n"
                    + f"{field}: {json.dumps(PROFILE_DESCRIPTION_TOKEN)}\n"
                    + f"{FRONTMATTER_DELIMITER}\n"
                    + format_target_conditional(target, f'{field} = "value"')
                    + "\n",
                    encoding="utf-8",
                )
                paths.append(path)
    return tuple(paths)


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
    existing = dist_root / "claude" / "sentinel.txt"
    existing.parent.mkdir(parents=True, exist_ok=True)
    existing.write_text("Existing generated output.\n", encoding="utf-8")
    return builder.src_root, dist_root
