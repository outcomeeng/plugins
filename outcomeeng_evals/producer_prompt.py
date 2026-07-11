"""Producer-derived prompt materialization for eval definitions."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from outcomeeng_evals.definition import EVAL_TOML_FILENAME


PROMPT_SOURCE_TABLE: Final = "prompt_source"
KIND_FIELD: Final = "kind"
PRODUCER_FIELD: Final = "producer"
SECTION_FIELD: Final = "section"
TEMPLATE_FIELD: Final = "template"
PRODUCER_SECTION_KIND: Final = "producer-section"
PRODUCER_FILE_KIND: Final = "producer-file"
PROMPT_FIELD: Final = "prompt"
MATERIALIZED_PROMPT_FILENAME: Final = "prompt.md"

_PRODUCER_PATH_PLACEHOLDER: Final = "{producer_path}"
_PRODUCER_SECTION_NAME_PLACEHOLDER: Final = "{producer_section_name}"
_PRODUCER_SECTION_PLACEHOLDER: Final = "{producer_section}"
_PRODUCER_FILE_PLACEHOLDER: Final = "{producer_file}"
_SECTION_NAME_PATTERN: Final = (
    r"""(?:^|\s)name\s*=\s*(?P<quote>["']){name}(?P=quote)(?:\s|$)"""
)
_STEP_DELIMITER_PATTERN: Final = r"<step\b(?P<attrs>[^>]*)>|</step>"


class ProducerPromptError(ValueError):
    """A producer prompt definition cannot be materialized."""


class PromptMaterializationDrift(ProducerPromptError):
    """A generated prompt differs from its source-derived rendering."""


@dataclass(frozen=True)
class ProducerPromptDefinition:
    """Resolved prompt_source contract for one eval definition."""

    eval_toml_path: Path
    prompt_path: Path
    producer_path: Path
    producer_relative_path: str
    kind: str
    section_name: str | None
    template_path: Path


def materialize_prompt(eval_toml_path: Path, *, repo_root: Path) -> Path:
    """Write ``prompt.md`` from the producer declared by ``eval.toml``."""
    definition = load_producer_prompt_definition(eval_toml_path, repo_root=repo_root)
    prompt_text = render_prompt(definition)
    resolved_root = repo_root.resolve()
    resolved_prompt = definition.prompt_path.resolve()
    if not resolved_prompt.is_relative_to(resolved_root):
        msg = f"{resolved_prompt}: generated prompt resolves outside {resolved_root}"
        raise ProducerPromptError(msg)
    resolved_prompt.write_text(prompt_text, encoding="utf-8")
    return resolved_prompt


def verify_materialized_prompt(eval_toml_path: Path, *, repo_root: Path) -> None:
    """Raise when ``prompt.md`` differs from its producer-derived rendering."""
    definition = load_producer_prompt_definition(eval_toml_path, repo_root=repo_root)
    expected = render_prompt(definition)
    try:
        actual = definition.prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        msg = f"{definition.prompt_path}: generated prompt is missing"
        raise PromptMaterializationDrift(msg) from exc
    if actual != expected:
        msg = f"{definition.prompt_path}: generated prompt differs from producer source"
        raise PromptMaterializationDrift(msg)


def materialize_prompts(
    root: Path, *, repo_root: Path, check: bool
) -> tuple[Path, ...]:
    """Materialize or check every producer-coupled eval beneath ``root``."""
    changed: list[Path] = []
    for eval_toml_path in sorted(root.rglob(EVAL_TOML_FILENAME)):
        definition = maybe_load_producer_prompt_definition(
            eval_toml_path,
            repo_root=repo_root,
        )
        if definition is None:
            continue
        if check:
            verify_materialized_prompt(eval_toml_path, repo_root=repo_root)
            changed.append(definition.prompt_path)
            continue
        prompt_text = render_prompt(definition)
        definition.prompt_path.write_text(prompt_text, encoding="utf-8")
        changed.append(definition.prompt_path)
    return tuple(changed)


def maybe_load_producer_prompt_definition(
    eval_toml_path: Path,
    *,
    repo_root: Path,
) -> ProducerPromptDefinition | None:
    """Return the prompt_source contract, or ``None`` when absent."""
    raw = _load_toml(eval_toml_path)
    prompt_source = raw.get(PROMPT_SOURCE_TABLE)
    if prompt_source is None:
        return None
    if not isinstance(prompt_source, dict):
        msg = f"{eval_toml_path}: [{PROMPT_SOURCE_TABLE}] must be a table"
        raise ProducerPromptError(msg)
    return _resolve_definition(
        eval_toml_path=eval_toml_path,
        repo_root=repo_root,
        raw=raw,
        prompt_source=prompt_source,
    )


def load_producer_prompt_definition(
    eval_toml_path: Path,
    *,
    repo_root: Path,
) -> ProducerPromptDefinition:
    """Return the required prompt_source contract for one eval."""
    definition = maybe_load_producer_prompt_definition(
        eval_toml_path,
        repo_root=repo_root,
    )
    if definition is None:
        msg = f"{eval_toml_path}: [{PROMPT_SOURCE_TABLE}] is required"
        raise ProducerPromptError(msg)
    return definition


def render_prompt(definition: ProducerPromptDefinition) -> str:
    """Render a prompt template from the declared producer source."""
    template = definition.template_path.read_text(encoding="utf-8")
    producer_text = definition.producer_path.read_text(encoding="utf-8")
    if definition.kind == PRODUCER_FILE_KIND:
        return _replace_known_placeholders_once(
            template,
            {
                _PRODUCER_PATH_PLACEHOLDER: definition.producer_relative_path,
                _PRODUCER_FILE_PLACEHOLDER: producer_text,
            },
        )
    if definition.section_name is None:
        msg = "producer-section definition requires a section name"
        raise ProducerPromptError(msg)
    producer_section = extract_named_producer_section(
        producer_text,
        section_name=definition.section_name,
        producer_path=definition.producer_path,
    )
    replacements = {
        _PRODUCER_PATH_PLACEHOLDER: definition.producer_relative_path,
        _PRODUCER_SECTION_NAME_PLACEHOLDER: definition.section_name,
        _PRODUCER_SECTION_PLACEHOLDER: producer_section,
    }
    return _replace_known_placeholders_once(template, replacements)


def extract_named_producer_section(
    producer_text: str,
    *,
    section_name: str,
    producer_path: Path,
) -> str:
    """Extract exactly one XML-like section with ``name=section_name``."""
    name_re = re.compile(
        _SECTION_NAME_PATTERN.format(name=re.escape(section_name)),
    )
    matches: list[str] = []
    open_sections: list[tuple[int, str]] = []
    for delimiter in re.finditer(_STEP_DELIMITER_PATTERN, producer_text, re.DOTALL):
        attrs = delimiter.group("attrs")
        if attrs is not None:
            open_sections.append((delimiter.start(), attrs))
            continue

        if not open_sections:
            msg = f"{producer_path}: unmatched step closing delimiter"
            raise ProducerPromptError(msg)
        section_start, open_attrs = open_sections.pop()
        section_text = producer_text[section_start : delimiter.end()]
        if name_re.search(open_attrs):
            matches.append(section_text)

    if open_sections:
        msg = f"{producer_path}: unclosed step delimiter"
        raise ProducerPromptError(msg)
    if len(matches) != 1:
        count = "no" if not matches else str(len(matches))
        msg = (
            f"{producer_path}: expected exactly one section named {section_name!r}, "
            f"found {count}"
        )
        raise ProducerPromptError(msg)
    return matches[0]


def _resolve_definition(
    *,
    eval_toml_path: Path,
    repo_root: Path,
    raw: dict[str, Any],
    prompt_source: dict[str, Any],
) -> ProducerPromptDefinition:
    kind = _required_str(prompt_source, KIND_FIELD, eval_toml_path=eval_toml_path)
    if kind not in (PRODUCER_SECTION_KIND, PRODUCER_FILE_KIND):
        msg = (
            f"{eval_toml_path}: unsupported {PROMPT_SOURCE_TABLE}.{KIND_FIELD} "
            f"{kind!r}; expected {PRODUCER_SECTION_KIND!r} or {PRODUCER_FILE_KIND!r}"
        )
        raise ProducerPromptError(msg)

    prompt_relative = _required_str(raw, PROMPT_FIELD, eval_toml_path=eval_toml_path)
    if prompt_relative != MATERIALIZED_PROMPT_FILENAME:
        msg = (
            f"{eval_toml_path}: {PROMPT_FIELD!r} must be "
            f"{MATERIALIZED_PROMPT_FILENAME!r} for producer-coupled evals"
        )
        raise ProducerPromptError(msg)
    producer_relative = _required_str(
        prompt_source,
        PRODUCER_FIELD,
        eval_toml_path=eval_toml_path,
    )
    section_name = _optional_section_name(
        prompt_source,
        kind=kind,
        eval_toml_path=eval_toml_path,
    )
    template_relative = _required_str(
        prompt_source,
        TEMPLATE_FIELD,
        eval_toml_path=eval_toml_path,
    )

    producer_path = _resolve_repo_relative_path(
        producer_relative,
        repo_root=repo_root,
        eval_toml_path=eval_toml_path,
        field_name=PRODUCER_FIELD,
    )
    template_path = _resolve_eval_relative_path(
        template_relative,
        eval_toml_path=eval_toml_path,
        field_name=TEMPLATE_FIELD,
    )
    prompt_path = eval_toml_path.parent.resolve() / MATERIALIZED_PROMPT_FILENAME

    if not producer_path.is_file():
        msg = f"{eval_toml_path}: producer file not found: {producer_path}"
        raise ProducerPromptError(msg)
    if not template_path.is_file():
        msg = f"{eval_toml_path}: prompt template file not found: {template_path}"
        raise ProducerPromptError(msg)
    if _paths_alias(template_path, prompt_path):
        msg = (
            f"{eval_toml_path}: {PROMPT_SOURCE_TABLE}.{TEMPLATE_FIELD} "
            f"must not alias {PROMPT_FIELD}"
        )
        raise ProducerPromptError(msg)

    return ProducerPromptDefinition(
        eval_toml_path=eval_toml_path,
        prompt_path=prompt_path,
        producer_path=producer_path,
        producer_relative_path=producer_relative,
        kind=kind,
        section_name=section_name,
        template_path=template_path,
    )


def _load_toml(eval_toml_path: Path) -> dict[str, Any]:
    if not eval_toml_path.is_file():
        msg = f"eval definition not found: {eval_toml_path}"
        raise FileNotFoundError(msg)
    with eval_toml_path.open("rb") as fh:
        return tomllib.load(fh)


def _paths_alias(left: Path, right: Path) -> bool:
    try:
        return left.samefile(right)
    except FileNotFoundError:
        return left.resolve(strict=False) == right.resolve(strict=False)


def _required_str(
    data: dict[str, Any],
    key: str,
    *,
    eval_toml_path: Path,
) -> str:
    if key not in data:
        msg = f"{eval_toml_path}: field {key!r} is required"
        raise ProducerPromptError(msg)
    value = data[key]
    if not isinstance(value, str) or not value:
        msg = (
            f"{eval_toml_path}: field {key!r} must be a non-empty string, "
            f"got {type(value).__name__}"
        )
        raise ProducerPromptError(msg)
    return value


def _optional_section_name(
    prompt_source: dict[str, Any],
    *,
    kind: str,
    eval_toml_path: Path,
) -> str | None:
    if kind == PRODUCER_SECTION_KIND:
        return _required_str(
            prompt_source,
            SECTION_FIELD,
            eval_toml_path=eval_toml_path,
        )
    if SECTION_FIELD in prompt_source:
        msg = (
            f"{eval_toml_path}: field {SECTION_FIELD!r} is invalid for "
            f"{PRODUCER_FILE_KIND!r}"
        )
        raise ProducerPromptError(msg)
    return None


def _resolve_repo_relative_path(
    raw_path: str,
    *,
    repo_root: Path,
    eval_toml_path: Path,
    field_name: str,
) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        msg = f"{eval_toml_path}: {field_name!r} must be repository-relative"
        raise ProducerPromptError(msg)
    if ".." in candidate.parts:
        msg = f"{eval_toml_path}: {field_name!r} must not contain parent traversal"
        raise ProducerPromptError(msg)
    return _resolve_beneath(
        (repo_root / candidate).resolve(),
        root=repo_root.resolve(),
        eval_toml_path=eval_toml_path,
        field_name=field_name,
    )


def _resolve_eval_relative_path(
    raw_path: str,
    *,
    eval_toml_path: Path,
    field_name: str,
) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        msg = f"{eval_toml_path}: {field_name!r} must be eval-directory-relative"
        raise ProducerPromptError(msg)
    eval_dir = eval_toml_path.parent.resolve()
    return _resolve_beneath(
        (eval_dir / candidate).resolve(),
        root=eval_dir,
        eval_toml_path=eval_toml_path,
        field_name=field_name,
    )


def _resolve_beneath(
    path: Path,
    *,
    root: Path,
    eval_toml_path: Path,
    field_name: str,
) -> Path:
    if path == root or root in path.parents:
        return path
    msg = f"{eval_toml_path}: {field_name!r} resolves outside {root}"
    raise ProducerPromptError(msg)


def _replace_known_placeholders_once(
    template: str,
    replacements: dict[str, str],
) -> str:
    parts: list[str] = []
    index = 0
    length = len(template)
    while index < length:
        match = next(
            (
                placeholder
                for placeholder in replacements
                if template.startswith(placeholder, index)
            ),
            None,
        )
        if match is None:
            parts.append(template[index])
            index += 1
            continue
        parts.append(replacements[match])
        index += len(match)
    return "".join(parts)
