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

from outcomeeng.distribution.contracts import SKILL_FILENAME, SKILLS_SUBDIR_NAME
from outcomeeng.validation.skill_reference import (
    CATALOG_PATH,
    CATALOG_PLUGIN_NAME_FIELD,
    CATALOG_PLUGINS_FIELD,
    PLUGIN_SOURCE_ROOT,
    ROOT_FLAG,
    find_violations,
    load_shipped_skills,
    main,
    scan_file,
    scan_files,
)

FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures" / "skill_reference"


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
                / SKILLS_SUBDIR_NAME
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
            {
                "name": "marketplace",
                CATALOG_PLUGINS_FIELD: [
                    {CATALOG_PLUGIN_NAME_FIELD: name} for name in listed
                ],
            }
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


def fixture_path(name: str) -> Path:
    """Return the path of the inert skill-reference fixture ``name``."""
    return FIXTURE_ROOT / name


def scan_references(
    root: Path,
    paths: Sequence[Path],
    exemptions: Mapping[str, str],
) -> tuple[str, ...]:
    """Return the reference of each violation in ``paths`` under ``exemptions``.

    The shipped skill set derives from the marketplace checkout at ``root``;
    ``paths`` are scanned as given, and the exemption mapping is passed to the
    scan unchanged.
    """
    skills = load_shipped_skills(root)
    return tuple(
        violation.reference
        for path in paths
        for violation in scan_file(path, skills, exemptions)
    )


def scan_repository_references(
    root: Path, exemptions: Mapping[str, str]
) -> tuple[str, ...]:
    """Return the reference of each violation across every scanned file of ``root``."""
    return scan_references(root, scan_files(root, ()), exemptions)


def scan_text_references(
    root: Path, text: str, exemptions: Mapping[str, str]
) -> tuple[str, ...]:
    """Return the reference of each violation in ``text`` under ``exemptions``."""
    skills = load_shipped_skills(root)
    return tuple(
        violation.reference
        for violation in find_violations(text, Path("payload.md"), skills, exemptions)
    )


def repository_root() -> Path:
    """Return the root of the checkout that holds this toolchain package."""
    return Path(__file__).resolve().parents[2]
