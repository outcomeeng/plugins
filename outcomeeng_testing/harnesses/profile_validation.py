"""Authored-source fixtures for native configuration rejection."""

from pathlib import Path
import json

from outcomeeng.distribution.contracts import BUILD_TARGET_VARIABLE, Target
from outcomeeng.distribution.profiles import AgentProfile, NATIVE_CONFIGURATION_FIELDS
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
                    "---\n"
                    + f"{field}: \"{{{{! profile_description('{AgentProfile.STANDARD}') !}}}}\"\n"
                    + "---\n"
                    + f"{{!% if {BUILD_TARGET_VARIABLE} == '{target.value}' %!}}\n"
                    + f'{field} = "value"\n'
                    + "{!% endif %!}\n",
                    encoding="utf-8",
                )
                paths.append(path)
    return tuple(paths)


def prepare_profile_build(
    root: Path, field: str, value: str, *, skill: bool = False
) -> tuple[Path, Path]:
    """Materialize one invalid authoring input beside existing generated state."""
    content = (
        "---\nname: reviewer\ndescription: Review.\n"
        + f"{field}: {json.dumps(value)}\n---\nReview.\n"
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
