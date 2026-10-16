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

from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    SKILL_FILENAME,
    SKILLS_SUBDIR_NAME,
)
from outcomeeng.validation.skill_reference import (
    CATALOG_PATH,
    CATALOG_PLUGIN_NAME_FIELD,
    CATALOG_PLUGINS_FIELD,
    INERT_FIXTURE_ROOT,
    MARKDOWN_SUFFIX,
    PLUGIN_SOURCE_ROOT,
    ROOT_FLAG,
    find_violations,
    load_shipped_skills,
    main,
    scan_file,
    scan_files,
)

FIXTURE_ROOT = (
    Path(__file__).resolve().parents[2] / INERT_FIXTURE_ROOT / "skill_reference"
)
UNSHIPPED_REFERENCES_FIXTURE = "unshipped_references" + MARKDOWN_SUFFIX
INCIDENTAL_FILE_STEM = "incidental"
OUTSIDE_SCAN_ROOTS_DIRECTORY = Path("unscanned")
PAYLOAD_PATH = Path("payload" + MARKDOWN_SUFFIX)
EXEMPTION_CHANGE = "outcomeeng/changes#1"


@dataclass(frozen=True)
class ValidatorRun:
    """The observable result of one validator invocation."""

    exit_code: int
    lines: tuple[str, ...]


def build_marketplace(
    root: Path,
    shipped: Mapping[str, Sequence[str]],
    catalog_plugins: Iterable[str] | None = None,
    agents: Mapping[str, Sequence[str]] | None = None,
) -> Path:
    """Lay out plugin skill directories and a marketplace catalog under ``root``.

    ``shipped`` maps each plugin name to the skill directory names it ships.
    ``catalog_plugins`` names the plugins the catalog lists; it defaults to
    every key of ``shipped``.  ``agents`` maps each plugin name to the subagent
    definition names it ships under its agents directory; it defaults to none.
    """
    for plugin, names in (agents or {}).items():
        for name in names:
            _write_named(
                root
                / PLUGIN_SOURCE_ROOT
                / plugin
                / AGENTS_SUBDIR_NAME
                / f"{name}{MARKDOWN_SUFFIX}",
                f"---\nname: {name}\n---\n",
            )
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
                CATALOG_PLUGINS_FIELD: [
                    {CATALOG_PLUGIN_NAME_FIELD: name} for name in listed
                ],
            }
        ),
        encoding="utf-8",
    )
    return root


def write_file(root: Path, directory: Path, text: str) -> Path:
    """Write ``text`` as a newly named markdown file in ``directory`` under ``root``.

    The harness chooses the file name; the name is unique within ``directory``.
    """
    target = root / directory
    target.mkdir(parents=True, exist_ok=True)
    return _write_named(
        target
        / f"{INCIDENTAL_FILE_STEM}-{len(list(target.iterdir()))}{MARKDOWN_SUFFIX}",
        text,
    )


def write_outside_scan_roots(root: Path, text: str) -> Path:
    """Write ``text`` as a markdown file in a directory no scan root contains."""
    return write_file(root, OUTSIDE_SCAN_ROOTS_DIRECTORY, text)


def write_plugin_file(
    root: Path, plugin: str, text: str, filename: str | None = None
) -> Path:
    """Write ``text`` in plugin ``plugin``'s source directory and return the path.

    The directory is the one ``build_marketplace`` lays plugin skills under, so
    the file lies beneath the validator's plugin source root.  With no
    ``filename`` the harness names the file.
    """
    directory = PLUGIN_SOURCE_ROOT / plugin
    if filename is None:
        return write_file(root, directory, text)
    return _write_named(root / directory / filename, text)


def _write_named(path: Path, text: str) -> Path:
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


def exemption_change() -> str:
    """Return a Change identity for an exemption mapping a test passes to a scan."""
    return EXEMPTION_CHANGE


def unshipped_references_fixture() -> Path:
    """Return the path of the inert fixture that names unshipped references."""
    return FIXTURE_ROOT / UNSHIPPED_REFERENCES_FIXTURE


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
        for violation in find_violations(text, PAYLOAD_PATH, skills, exemptions)
    )


def repository_root() -> Path:
    """Return the root of the checkout that holds this toolchain package."""
    return Path(__file__).resolve().parents[2]
