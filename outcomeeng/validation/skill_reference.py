"""Validate that every skill reference names a skill a marketplace plugin ships.

A skill reference is written in one of three forms:

* a plugin-qualified name, ``<plugin>:<skill>``;
* a slash invocation, ``/<skill>``, standing as its own token rather than as a
  path segment;
* either form with a brace alternation (``{code|tests}``) or a placeholder
  (``{type}``) in the skill name.

The shipped skill set derives from the skill directories under
``src/plugins/<plugin>/skills/`` of each plugin the committed marketplace
catalog lists.  A brace alternation expands over each member; a placeholder
passes when at least one shipped skill name matches the template with the
placeholder standing for one or more name characters.

Usage::

    uv run python -m outcomeeng.validation.skill_reference [--root DIR] [FILE ...]

Exit codes:
    0 - Every scanned reference names a shipped skill
    1 - One or more references name no shipped skill
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from outcomeeng.distribution.contracts import (
    AGENTS_SUBDIR_NAME,
    CLAUDE_PLUGIN_SUBDIR_NAME,
    PLUGINS_DIR_NAME,
    SKILL_FILENAME,
    SKILLS_SUBDIR_NAME,
    SOURCE_ROOT_NAME,
)

CATALOG_PATH: Final = Path(CLAUDE_PLUGIN_SUBDIR_NAME) / "marketplace.json"
CATALOG_PLUGINS_FIELD: Final = "plugins"
CATALOG_PLUGIN_NAME_FIELD: Final = "name"
PLUGIN_SOURCE_ROOT: Final = Path(SOURCE_ROOT_NAME) / PLUGINS_DIR_NAME
TEMPLATE_SOURCE_ROOT: Final = Path(SOURCE_ROOT_NAME) / "templates"
MARKDOWN_SUFFIX: Final = ".md"
SCAN_ROOTS: Final = (
    PLUGIN_SOURCE_ROOT,
    Path(SOURCE_ROOT_NAME) / "_shared",
    TEMPLATE_SOURCE_ROOT,
    Path("outcomeeng"),
    Path("outcomeeng_testing"),
)
CHANGELOG_FILENAME: Final = "CHANGELOG.md"
INERT_FIXTURE_ROOT: Final = Path("outcomeeng_testing") / "fixtures"
EXCLUDED_DIRECTORY_NAMES: Final = frozenset(
    {"__pycache__", ".venv", "node_modules", ".git", ".mypy_cache", ".ruff_cache"}
)
# Slash invocations of harness commands, which no marketplace plugin ships.
HARNESS_COMMANDS: Final = frozenset(
    {
        "clear",
        "compact",
        "config",
        "exit",
        "help",
        "init",
        "loop",
        "model",
        "permissions",
        "plugin",
        "quit",
        "resume",
        "session",
        "status",
    }
)
# Each exempted reference to a skill no marketplace plugin ships yet, mapped to
# the Change that ships the skill and removes the exemption.
EXEMPTED_REFERENCES: Final[Mapping[str, str]] = {
    "/probe": "outcomeeng/changes#363",
    "spec-tree:probe": "outcomeeng/changes#363",
    "/eval": "outcomeeng/changes#514",
    "spec-tree:eval": "outcomeeng/changes#514",
}
# Top-level filesystem directories, which a slash-prefixed token names as a path.
FILESYSTEM_ROOTS: Final = frozenset(
    {
        "bin",
        "dev",
        "etc",
        "home",
        "opt",
        "private",
        "proc",
        "tmp",
        "tmpfs",
        "usr",
        "var",
    }
)
PLACEHOLDER_STAND_IN: Final = "[a-z0-9-]+"
ALTERNATION_SEPARATOR: Final = "|"
ROOT_FLAG: Final = "--root"

_NAME: Final = r"(?=[a-z{])(?:[a-z0-9]|\{[^{}\s]*\}|-(?=[a-z0-9{]))+"
_SLASH_REFERENCE: Final = re.compile(rf"/(?P<name>{_NAME})(?![\w/:\\]|\.\w|-)")
_OPENING_PRECEDERS: Final = frozenset(" \t([*,;")
_QUOTES: Final = frozenset("\"'")
_BACKTICK: Final = "`"
_ASSIGNMENT_ENDINGS: Final = (":", "=")
_NOT_BEFORE_OPENING_QUOTE: Final = re.compile(r"[\w>)\]}\"']")
_GROUP: Final = re.compile(r"\{([^{}]*)\}")


@dataclass(frozen=True)
class Violation:
    """One skill reference that names no shipped skill."""

    path: Path
    line: int
    reference: str
    unmatched: tuple[str, ...]


@dataclass(frozen=True)
class ShippedSkills:
    """The marketplace's shipped skill names, by plugin."""

    by_plugin: Mapping[str, frozenset[str]]
    agents_by_plugin: Mapping[str, frozenset[str]]
    known_plugins: frozenset[str]

    @property
    def all_names(self) -> frozenset[str]:
        return frozenset(itertools.chain.from_iterable(self.by_plugin.values()))


def load_shipped_skills(root: Path) -> ShippedSkills:
    """Derive the shipped skills from the catalog and the skill directories."""
    catalog = json.loads((root / CATALOG_PATH).read_text(encoding="utf-8"))
    cataloged = [
        entry[CATALOG_PLUGIN_NAME_FIELD] for entry in catalog[CATALOG_PLUGINS_FIELD]
    ]
    plugin_root = root / PLUGIN_SOURCE_ROOT
    on_disk = (
        [entry.name for entry in plugin_root.iterdir() if entry.is_dir()]
        if plugin_root.is_dir()
        else []
    )
    template_root = root / TEMPLATE_SOURCE_ROOT
    templates = (
        [entry.name for entry in template_root.iterdir() if entry.is_dir()]
        if template_root.is_dir()
        else []
    )
    by_plugin = {
        plugin: frozenset(
            [
                skill_file.parent.name
                for skill_file in (plugin_root / plugin / SKILLS_SUBDIR_NAME).glob(
                    f"*/{SKILL_FILENAME}"
                )
            ]
            + [f"{plugin}-{template}" for template in templates]
        )
        for plugin in cataloged
    }
    agents_by_plugin = {
        plugin: frozenset(
            agent_file.stem
            for agent_file in (plugin_root / plugin / AGENTS_SUBDIR_NAME).glob(
                f"*{MARKDOWN_SUFFIX}"
            )
        )
        for plugin in cataloged
    }
    return ShippedSkills(
        by_plugin=by_plugin,
        agents_by_plugin=agents_by_plugin,
        known_plugins=frozenset([*cataloged, *on_disk]),
    )


def expand_alternations(name: str) -> list[str]:
    """Expand each ``{a|b}`` group of ``name`` over its members."""
    for group in _GROUP.finditer(name):
        if ALTERNATION_SEPARATOR not in group.group(1):
            continue
        return [
            expansion
            for member in group.group(1).split(ALTERNATION_SEPARATOR)
            for expansion in expand_alternations(
                name[: group.start()] + member + name[group.end() :]
            )
        ]
    return [name]


def _matches_a_shipped_name(template: str, shipped: Iterable[str]) -> bool:
    pattern = PLACEHOLDER_STAND_IN.join(
        re.escape(part) for part in _GROUP.split(template)[::2]
    )
    compiled = re.compile(pattern)
    return any(compiled.fullmatch(name) for name in shipped)


def unmatched_expansions(name: str, shipped: frozenset[str]) -> tuple[str, ...]:
    """Return each expansion of ``name`` that no shipped skill name matches."""
    return tuple(
        expansion
        for expansion in expand_alternations(name)
        if not _matches_a_shipped_name(expansion, shipped)
    )


def _qualified_pattern(plugins: Iterable[str]) -> re.Pattern[str] | None:
    names = sorted(plugins, key=len, reverse=True)
    if not names:
        return None
    alternation = "|".join(re.escape(name) for name in names)
    return re.compile(
        rf"(?<![\w.-])(?<!//)(?P<plugin>{alternation}):(?P<name>{_NAME})(?![\w/:\\]|\.\w|-)"
    )


def stands_alone(line: str, start: int, quotes_open: bool) -> bool:
    """Return whether the slash at ``start`` begins a token rather than a path.

    A slash after whitespace or an opening bracket begins a token; after a
    backtick only when that backtick opens a code span; after a quote only when
    ``quotes_open`` holds and the quote itself opens.
    """
    if start == 0:
        return True
    preceder = line[start - 1]
    if preceder in _OPENING_PRECEDERS:
        return True
    if preceder == _BACKTICK:
        return line[: start - 1].count(_BACKTICK) % 2 == 0
    if preceder in _QUOTES and quotes_open:
        before = line[: start - 1].rstrip()
        return not before.endswith(_ASSIGNMENT_ENDINGS) and (
            start < 2 or not _NOT_BEFORE_OPENING_QUOTE.match(line[start - 2])
        )
    return False


def find_violations(
    text: str,
    path: Path,
    skills: ShippedSkills,
    exemptions: Mapping[str, str] = EXEMPTED_REFERENCES,
) -> list[Violation]:
    """Return one violation per unshipped skill reference in ``text``.

    A reference that is a key of ``exemptions`` is not a violation.
    """
    quotes_open = path.suffix == MARKDOWN_SUFFIX
    qualified = _qualified_pattern(skills.known_plugins)
    all_names = skills.all_names
    violations: list[Violation] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        found: list[tuple[int, str, tuple[str, ...]]] = []
        if qualified is not None:
            for match in qualified.finditer(line):
                plugin = match.group("plugin")
                shipped = skills.by_plugin.get(
                    plugin, frozenset()
                ) | skills.agents_by_plugin.get(plugin, frozenset())
                unmatched = unmatched_expansions(match.group("name"), shipped)
                if unmatched and match.group(0) not in exemptions:
                    found.append((match.start(), match.group(0), unmatched))
        for match in _SLASH_REFERENCE.finditer(line):
            name = match.group("name")
            if name in HARNESS_COMMANDS or name in FILESYSTEM_ROOTS:
                continue
            if not stands_alone(line, match.start(), quotes_open):
                continue
            unmatched = unmatched_expansions(name, all_names)
            if unmatched and match.group(0) not in exemptions:
                found.append((match.start(), match.group(0), unmatched))
        violations.extend(
            Violation(path=path, line=lineno, reference=reference, unmatched=unmatched)
            for _, reference, unmatched in sorted(found)
        )
    return violations


def in_scope(root: Path, path: Path) -> bool:
    """Return whether ``path`` is a file the validator scans."""
    try:
        relative = path.relative_to(root)
    except ValueError:
        return False
    if not any(relative.is_relative_to(scan_root) for scan_root in SCAN_ROOTS):
        return False
    if relative.is_relative_to(INERT_FIXTURE_ROOT):
        return False
    if EXCLUDED_DIRECTORY_NAMES.intersection(relative.parts):
        return False
    return not (
        relative.name == CHANGELOG_FILENAME
        and relative.is_relative_to(PLUGIN_SOURCE_ROOT)
    )


def scan_files(root: Path, paths: Sequence[Path]) -> list[Path]:
    """Return the files to scan: ``paths`` when given, else every scan root."""
    candidates = (
        list(paths)
        if paths
        else sorted(
            candidate
            for scan_root in SCAN_ROOTS
            for candidate in (root / scan_root).rglob("*")
            if candidate.is_file()
        )
    )
    return [path for path in candidates if path.is_file() and in_scope(root, path)]


def scan_file(
    path: Path,
    skills: ShippedSkills,
    exemptions: Mapping[str, str] = EXEMPTED_REFERENCES,
) -> list[Violation]:
    """Return the violations in ``path``; a non-text file has none."""
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return []
    return find_violations(text, path, skills, exemptions)


def format_violation(violation: Violation) -> str:
    """Return the stable diagnostic for one unshipped skill reference."""
    return (
        f"{violation.path}:{violation.line}: skill reference "
        f"'{violation.reference}' names no shipped skill; "
        f"unmatched expansion: {', '.join(violation.unmatched)}"
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(ROOT_FLAG, type=Path, default=Path.cwd())
    parser.add_argument("paths", nargs="*", type=Path)
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    root: Path = args.root
    skills = load_shipped_skills(root)
    violations = [
        violation
        for path in scan_files(root, args.paths)
        for violation in scan_file(path, skills)
    ]
    for violation in violations:
        print(format_violation(violation))
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
