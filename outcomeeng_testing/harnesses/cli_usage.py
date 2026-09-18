"""Read a captured CLI usage text into the grammar contract it declares.

A usage text is the CLI's own declaration of its command path, positionals,
options, and separators. This module reads that captured payload into an
observation record and reads an argument vector against it; every predicate
stays in the linked test.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

USAGE_PREFIX: Final = "Usage:"
OPTIONS_HEADING: Final = "Options:"
ARGUMENTS_HEADING: Final = "Arguments:"
OPTIONS_PLACEHOLDER: Final = "[OPTIONS]"
SEPARATOR: Final = "--"
# Joins an option to a value carried in the same token.
ATTACHED_VALUE_SEPARATOR: Final = "="
REPEAT_MARKER: Final = "repeat"
_OPTION_LINE: Final = re.compile(
    r"^\s*(?:-[A-Za-z],\s*)?(?P<long>--[a-z][a-z0-9-]*)(?:,\s*-[A-Za-z])?"
    r"(?P<value>\s+<[^>]+>)?"
)


@dataclass(frozen=True)
class UsageContract:
    """The grammar one usage text declares for one command."""

    command_path: tuple[str, ...]
    required_positionals: tuple[str, ...]
    optional_positionals: tuple[str, ...]
    variadic_positional: bool
    required_options: frozenset[str]
    options: dict[str, bool] = field(default_factory=dict)
    repeatable_options: frozenset[str] = frozenset()
    trailing_separator: bool = False


@dataclass(frozen=True)
class ArgvReading:
    """What one argument vector carries, read against a usage contract."""

    command_path: tuple[str, ...]
    options_seen: dict[str, int]
    unknown_options: tuple[str, ...]
    positionals: tuple[str, ...]
    trailing: tuple[str, ...]


def usage_contract(usage_text: str) -> UsageContract:
    """Read the first usage line and the options section of a captured help text."""
    lines = usage_text.splitlines()
    usage_line = next(line for line in lines if line.strip().startswith(USAGE_PREFIX))
    tokens = usage_line.strip()[len(USAGE_PREFIX) :].split()
    command_path: list[str] = []
    required_positionals: list[str] = []
    optional_positionals: list[str] = []
    variadic = False
    required_options: set[str] = set()
    trailing_separator = False
    index = 1  # the tool name opens the usage line
    while index < len(tokens):
        token = tokens[index]
        if token.startswith("--"):
            required_options.add(token)
            index += (
                2
                if index + 1 < len(tokens) and tokens[index + 1].startswith("<")
                else 1
            )
            continue
        if token.startswith("<"):
            name = token.strip("<>.")
            if token.endswith("..."):
                variadic = True
            required_positionals.append(name)
        elif token.startswith("["):
            if token == OPTIONS_PLACEHOLDER:
                pass
            elif token.startswith("[--"):
                trailing_separator = True
                break
            else:
                optional_positionals.append(token.strip("[]."))
        elif not required_positionals and not optional_positionals:
            command_path.append(token)
        index += 1
    options: dict[str, bool] = {}
    repeatable: set[str] = set()
    in_options = False
    current: str | None = None
    for line in lines:
        stripped = line.strip()
        if stripped == OPTIONS_HEADING:
            in_options = True
            continue
        if not in_options:
            continue
        if stripped and not line.startswith((" ", "\t")):
            break
        match = _OPTION_LINE.match(line)
        if match and line.lstrip().startswith("-"):
            long_option = match.group("long")
            if not isinstance(long_option, str):
                raise RuntimeError(f"Option line without a long option: {line!r}")
            current = long_option
            options[current] = match.group("value") is not None
            description = line[match.end() :]
        else:
            description = line
        if current is not None and REPEAT_MARKER in description.lower():
            repeatable.add(current)
    for required in required_options:
        options.setdefault(required, True)
    return UsageContract(
        command_path=tuple(command_path),
        required_positionals=tuple(required_positionals),
        optional_positionals=tuple(optional_positionals),
        variadic_positional=variadic,
        required_options=frozenset(required_options),
        options=options,
        repeatable_options=frozenset(repeatable),
        trailing_separator=trailing_separator,
    )


def usage_contract_from_path(path: Path) -> UsageContract:
    return usage_contract(path.read_text(encoding="utf-8"))


def read_argv(contract: UsageContract, argv: tuple[str, ...]) -> ArgvReading:
    """Read an argument vector the way the contract's command would consume it."""
    path_length = len(contract.command_path) + 1  # the tool name opens the vector
    command_path = argv[:path_length]
    options_seen: dict[str, int] = {}
    unknown: list[str] = []
    positionals: list[str] = []
    trailing: list[str] = []
    index = path_length
    while index < len(argv):
        token = argv[index]
        if token == SEPARATOR and contract.trailing_separator:
            trailing.extend(argv[index + 1 :])
            break
        if token.startswith("--"):
            # `--option=value` carries its value in the same token, the form a
            # value that begins with `-` must take.
            option, attached, _ = token.partition(ATTACHED_VALUE_SEPARATOR)
            options_seen[option] = options_seen.get(option, 0) + 1
            if option not in contract.options:
                unknown.append(option)
                index += 1
                continue
            index += 2 if contract.options[option] and not attached else 1
            continue
        positionals.append(token)
        index += 1
    return ArgvReading(
        command_path=command_path,
        options_seen=options_seen,
        unknown_options=tuple(unknown),
        positionals=tuple(positionals),
        trailing=tuple(trailing),
    )
