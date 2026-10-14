"""Resource lifecycle and observations for skill-reference validation evidence.

The harness lays out a marketplace checkout in a caller-supplied directory and
runs the validator against it.  It returns observations; the linked tests own
every expectation and verdict.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping, Sequence
from contextlib import redirect_stdout
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

from outcomeeng.distribution.contracts import SKILL_FILENAME
from outcomeeng.validation.skill_reference import main

CATALOG_PATH = Path(".claude-plugin") / "marketplace.json"
PLUGIN_SOURCE_ROOT = Path("src") / "plugins"
SKILLS_DIRECTORY = "skills"
ROOT_FLAG = "--root"


@dataclass(frozen=True)
class ValidatorRun:
    """The observable result of one validator invocation."""

    exit_code: int
    lines: tuple[str, ...]


def build_marketplace(
    root: Path,
    shipped: Mapping[str, Sequence[str]],
    catalog_plugins: Iterable[str] | None = None,
) -> Path:
    """Lay out plugin skill directories and a marketplace catalog under ``root``.

    ``shipped`` maps each plugin name to the skill directory names it ships.
    ``catalog_plugins`` names the plugins the catalog lists; it defaults to
    every key of ``shipped``.
    """
    for plugin, skills in shipped.items():
        for skill in skills:
            skill_file = (
                root
                / PLUGIN_SOURCE_ROOT
                / plugin
                / SKILLS_DIRECTORY
                / skill
                / SKILL_FILENAME
            )
            skill_file.parent.mkdir(parents=True, exist_ok=True)
            skill_file.write_text(f"---\nname: {skill}\n---\n", encoding="utf-8")
    listed = list(shipped) if catalog_plugins is None else list(catalog_plugins)
    catalog = root / CATALOG_PATH
    catalog.parent.mkdir(parents=True, exist_ok=True)
    catalog.write_text(
        json.dumps(
            {"name": "marketplace", "plugins": [{"name": name} for name in listed]}
        ),
        encoding="utf-8",
    )
    return root


def write_file(root: Path, relative_path: str, text: str) -> Path:
    """Write ``text`` at ``relative_path`` under ``root`` and return the path."""
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def run_validator(root: Path, paths: Sequence[Path] = ()) -> ValidatorRun:
    """Run the validator for the checkout at ``root``.

    With no ``paths`` the validator scans its declared scan roots; with
    ``paths`` it scans exactly those files.
    """
    output = StringIO()
    with redirect_stdout(output):
        exit_code = main([ROOT_FLAG, str(root), *(str(path) for path in paths)])
    return ValidatorRun(
        exit_code=exit_code, lines=tuple(output.getvalue().splitlines())
    )


def repository_root() -> Path:
    """Return the root of the checkout that holds this toolchain package."""
    return Path(__file__).resolve().parents[2]
