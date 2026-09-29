"""Authored configuration text derived from the profile owners.

The assignment domain crosses every native configuration field with every value
its owning configuration type admits, in every serialization ``ProfileSyntax``
names. Each serialization's grammar is checked against that format's own parser,
so a syntax the owner adds without a grammar here fails at generation rather
than silently shrinking the domain.

A token document places generated lines one per line and records which model
literals and native fields each line carries, so evidence compares a scanner's
report with the placement rather than with hand-written coordinates.
"""

from __future__ import annotations

import json
import tomllib
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, fields
from types import MappingProxyType
from typing import Final, get_type_hints

import yaml

from outcomeeng.distribution.contracts import (
    PROFILE_CONFIG_GLOBAL,
    PROFILE_DESCRIPTION_GLOBAL,
    format_template_call,
)
from outcomeeng.distribution.profiles import (
    NATIVE_CONFIGURATION_TYPES,
    PROFILE_FIELD,
    ProfileSyntax,
)
from outcomeeng.models import CLAUDE_MODEL_FAMILIES, MODEL_IDENTIFIERS, AgentProfile


class AssignmentGrammarError(ValueError):
    """A generated assignment does not parse back to the field and value it names."""


def _json_assignment(field: str, value: str) -> str:
    return json.dumps({field: value})


def _separated_assignment(
    separator: str, load: Callable[[str], object]
) -> Callable[[str, str], str]:
    """Join a key to a JSON-encoded value, which both TOML and YAML accept verbatim."""

    def serialize(field: str, value: str) -> str:
        text = f"{field}{separator}{json.dumps(value)}"
        if load(text) != {field: value}:
            msg = f"{text!r} does not parse back to {field!r}"
            raise AssignmentGrammarError(msg)
        return text

    return serialize


_ASSIGNMENT_GRAMMARS: Final[Mapping[ProfileSyntax, Callable[[str, str], str]]] = (
    MappingProxyType(
        {
            ProfileSyntax.JSON: _json_assignment,
            ProfileSyntax.TOML: _separated_assignment(" = ", tomllib.loads),
            ProfileSyntax.YAML: _separated_assignment(": ", yaml.safe_load),
        }
    )
)


def assignment_text(syntax: ProfileSyntax, field: str, value: str) -> str:
    """Return one line assigning ``value`` to ``field`` in ``syntax``."""
    return _ASSIGNMENT_GRAMMARS[syntax](field, value)


def model_literals() -> tuple[str, ...]:
    """Return every model identifier and bare family name the model owner declares."""
    return tuple(sorted(MODEL_IDENTIFIERS | CLAUDE_MODEL_FAMILIES))


@dataclass(frozen=True)
class NativeAssignment:
    """One native field assigned one admitted value in one serialization."""

    field: str
    value: str
    syntax: ProfileSyntax
    text: str
    tokens: tuple[str, ...]


def _native_field_values() -> dict[str, tuple[str, ...]]:
    values: dict[str, set[str]] = {}
    for configuration_type in NATIVE_CONFIGURATION_TYPES.values():
        annotations = get_type_hints(configuration_type)
        for field in fields(configuration_type):
            values.setdefault(field.name, set()).update(
                str(member) for member in annotations[field.name]
            )
    return {field: tuple(sorted(admitted)) for field, admitted in values.items()}


def native_field_assignments() -> tuple[NativeAssignment, ...]:
    """Return every native field with every admitted value in every syntax.

    Each assignment's tokens are the model literals its value places followed by
    the field it assigns.
    """
    literals = frozenset(model_literals())
    return tuple(
        NativeAssignment(
            field=field,
            value=value,
            syntax=syntax,
            text=assignment_text(syntax, field, value),
            tokens=(*((value,) if value in literals else ()), field),
        )
        for field, admitted in sorted(_native_field_values().items())
        for value in admitted
        for syntax in ProfileSyntax
    )


def native_prose_values() -> tuple[str, ...]:
    """Return every admitted native value that is not a model literal."""
    literals = frozenset(model_literals())
    return tuple(
        sorted(
            {
                value
                for admitted in _native_field_values().values()
                for value in admitted
                if value not in literals
            }
        )
    )


def native_value_prose() -> tuple[str, ...]:
    """Return sentences naming each native field beside each non-model native value.

    The field is a word of the sentence, never the key of an assignment.
    """
    return tuple(
        f"Choose the {field} that reads {value} for this run."
        for field in sorted(_native_field_values())
        for value in native_prose_values()
    )


def profile_selection_texts() -> tuple[str, ...]:
    """Return every profile selection in every syntax, and every profile request."""
    return (
        *(
            format_template_call(template_global, profile)
            for template_global in (PROFILE_CONFIG_GLOBAL, PROFILE_DESCRIPTION_GLOBAL)
            for profile in AgentProfile
        ),
        *(
            assignment_text(syntax, PROFILE_FIELD, profile)
            for profile in AgentProfile
            for syntax in ProfileSyntax
        ),
    )


@dataclass(frozen=True)
class PlacedToken:
    """One token a document carries, and the one-based line it sits on."""

    line: int
    token: str


@dataclass(frozen=True)
class TokenDocument:
    """Text with one generated line per entry and the tokens each line carries."""

    text: str
    placed: tuple[PlacedToken, ...]


def token_document(entries: Iterable[tuple[str, Iterable[str]]]) -> TokenDocument:
    """Place each entry's line in order and record the tokens it carries."""
    lines = tuple((line, tuple(tokens)) for line, tokens in entries)
    return TokenDocument(
        text="".join(f"{line}\n" for line, _ in lines),
        placed=tuple(
            PlacedToken(line=number, token=token)
            for number, (_, tokens) in enumerate(lines, start=1)
            for token in tokens
        ),
    )
