"""Reject independently authored native profile settings throughout source text.

The guard reads every authored file under ``src/`` and every eval definition
under the spec tree together with the prompt templates that definition
declares, so no authored template names a model or sets a native model or
reasoning field in place of selecting a profile.
"""

import os
import re
import tomllib
from collections.abc import Iterator
from pathlib import Path
from typing import Final

from outcomeeng.distribution.profiles import NATIVE_CONFIGURATION_FIELDS
from outcomeeng.models import MODEL_IDENTIFIER_PATTERN
from outcomeeng_evals.definition import EVAL_TOML_FILENAME
from outcomeeng_evals.producer_prompt import (
    PROMPT_FIELD,
    PROMPT_SOURCE_TABLE,
    TEMPLATE_FIELD,
)

# Command-line marker: every file argument after it receives the configuration
# guard alone, without the authored-source checks that apply only under src/.
CONFIGURATION_ONLY_OPTION: Final = "--configuration-only"

_ASSIGNMENT: Final = re.compile(
    r"(?:^|[\s{,])['\"]?(?P<field>"
    + "|".join(re.escape(field) for field in sorted(NATIVE_CONFIGURATION_FIELDS))
    + r")[\"']?[ \t]*[:=][ \t]*(?=\S)"
)


def find_profile_literals(text: str) -> list[tuple[int, str]]:
    """Report native assignments and model literals without conditional exemptions."""
    violations: list[tuple[int, str]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        violations.extend(
            (line_number, match.group(0))
            for match in MODEL_IDENTIFIER_PATTERN.finditer(line)
        )
        violations.extend(
            (line_number, match.group("field")) for match in _ASSIGNMENT.finditer(line)
        )
    return violations


def eval_configuration_files(spec_root: Path) -> tuple[Path, ...]:
    """Return every eval definition under ``spec_root`` and each prompt template it declares.

    A definition declares its prompt through the top-level ``prompt`` path and,
    for a producer-coupled eval, its authored template through
    ``prompt_source.template``; both resolve relative to the definition's
    directory. A declared path that names no file selects nothing, and a
    definition that does not parse still selects itself, so its own text is
    guarded while the eval harness reports the malformed declaration.
    """
    selected: set[Path] = set()
    for definition in spec_root.rglob(EVAL_TOML_FILENAME):
        if not definition.is_file():
            continue
        selected.add(definition)
        selected.update(_declared_prompt_templates(definition))
    return tuple(sorted(selected))


def _declared_prompt_templates(definition: Path) -> Iterator[Path]:
    try:
        declaration = tomllib.loads(definition.read_text(encoding="utf-8"))
    except (tomllib.TOMLDecodeError, UnicodeDecodeError):
        return
    prompt_source = declaration.get(PROMPT_SOURCE_TABLE)
    declared = (
        declaration.get(PROMPT_FIELD),
        prompt_source.get(TEMPLATE_FIELD) if isinstance(prompt_source, dict) else None,
    )
    for relative in declared:
        if not isinstance(relative, str):
            continue
        path = Path(os.path.normpath(definition.parent / relative))
        if path.is_file():
            yield path
