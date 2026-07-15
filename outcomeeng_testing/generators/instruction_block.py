"""Generated input domains for instruction-block evidence.

The instruction-block harness owns filesystems, fixtures, subprocesses, and
cleanup. This module owns variable input domains and source-derived protocol
cases from the production module's harness, filename, marker, and template
contracts.
"""

from __future__ import annotations

import string
from dataclasses import dataclass
from enum import StrEnum
from fractions import Fraction
from types import ModuleType

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

_LANGUAGE_TOKEN_CHARACTERS = string.ascii_letters + string.digits + "-_"


@dataclass(frozen=True)
class InstructionBlockCases:
    """Source-derived carrier values used across instruction-block evidence."""

    instruction_claude: str
    instruction_agents: str
    shared_region_name: str
    read_entire_file_instruction: str
    lang_primary: str
    lang_secondary: str
    template_languages: tuple[str, ...]
    base_section: str
    new_section: str
    old_version: str
    new_version: str
    illustration_token: str
    build_macro_capability: str
    build_macro_harness: str
    harness_claude: str
    harness_codex: str
    template_harnesses: tuple[str, ...]


class BootstrapThresholdRelation(StrEnum):
    """Generated positions around the source-owned bootstrap threshold."""

    ABOVE = "above"
    AT = "at"
    BELOW = "below"


@dataclass(frozen=True)
class BootstrapWrapCase:
    """A root-content pair with one controlled biggest whole-line shared span."""

    content_a: str
    content_b: str
    shared_body: str
    relation: BootstrapThresholdRelation


def _prior_dotted_version(version: str) -> str:
    """Return a dotted-numeric version strictly below ``version``."""
    parts = [int(part) for part in version.split(".")]
    for index in range(len(parts) - 1, -1, -1):
        if parts[index] > 0:
            parts[index] -= 1
            return ".".join(str(part) for part in parts)
    raise ValueError(f"version has no lower non-negative value: {version}")


def instruction_block_cases(
    module: ModuleType,
    canonical_template: str,
) -> InstructionBlockCases:
    """Derive deterministic carrier cases from production and template contracts."""
    harnesses = tuple(sorted(module.AGENT_HARNESS_INSTRUCTION_FILENAMES))
    harness_claude = next(
        harness
        for harness, filename in module.AGENT_HARNESS_INSTRUCTION_FILENAMES.items()
        if filename.casefold().startswith("claude")
    )
    harness_codex = next(
        harness
        for harness, filename in module.AGENT_HARNESS_INSTRUCTION_FILENAMES.items()
        if filename.casefold().startswith("agents")
    )
    instruction_claude = module.AGENT_HARNESS_INSTRUCTION_FILENAMES[harness_claude]
    instruction_agents = module.AGENT_HARNESS_INSTRUCTION_FILENAMES[harness_codex]
    languages = module.template_languages(canonical_template)
    version = module.parse_template_version(canonical_template)
    if version is None:
        raise ValueError("canonical instruction-block template has no version")
    shared_name = module.BOOTSTRAP_SHARED_REGION_NAME
    first_section = next(
        line.removeprefix("## ")
        for line in canonical_template.splitlines()
        if line.startswith("## ")
    )
    read_directive = next(
        line
        for line in canonical_template.splitlines()
        if "Read this entire file" in line
    )
    return InstructionBlockCases(
        instruction_claude=instruction_claude,
        instruction_agents=instruction_agents,
        shared_region_name=shared_name,
        read_entire_file_instruction=read_directive,
        lang_primary=languages[0],
        lang_secondary=languages[-1],
        template_languages=languages,
        base_section=first_section,
        new_section=f"{module.DEFAULT_TEMPLATE_SOURCE.title()} Extension",
        old_version=_prior_dotted_version(version),
        new_version=version,
        illustration_token=f"{{{module.DEFAULT_TEMPLATE_SOURCE}-slug}}",
        build_macro_capability=module.TEMPLATE_VERSION_KEY,
        build_macro_harness=harness_codex,
        harness_claude=harness_claude,
        harness_codex=harness_codex,
        template_harnesses=harnesses,
    )


def harness_line(harness: str) -> str:
    """Generate distinct body content for one source-owned harness value."""
    return f"{harness.upper()} runs the audit as a subagent."


def build_macro(cases: InstructionBlockCases) -> str:
    """Generate one unresolved build-macro carrier from source-derived vocabulary."""
    return (
        f"\n{{{{! tool('{cases.build_macro_capability}', "
        f"'{cases.build_macro_harness}') !}}}}\n"
    )


def build_template(
    module: ModuleType,
    cases: InstructionBlockCases,
    version: str,
    *,
    extra_section: bool = False,
) -> str:
    """Generate a valid template over every source-declared language and harness."""
    delimiter = module.FRONTMATTER_DELIMITER
    frontmatter = (
        f"{delimiter}\n"
        f'{module.TEMPLATE_VERSION_KEY}: "{version}"\n'
        f"{module.TEMPLATE_SOURCE_KEY}: {module.DEFAULT_TEMPLATE_SOURCE}\n"
        f"{delimiter}\n"
    )
    parts = [
        "",
        "# Spec Tree Instructions",
        "",
        f"The root spec is `{cases.illustration_token}.product.md`.",
        "",
        f"## {cases.base_section}",
        "",
    ]
    for language in cases.template_languages:
        parts.extend(
            (
                f"<!-- lang:{language} -->",
                "",
                f"### {language.capitalize()}",
                f"{language} naming rules",
                "",
                f"<!-- /lang:{language} -->",
            )
        )
    for harness in cases.template_harnesses:
        parts.extend(
            (
                f"<!-- harness:{harness} -->",
                "",
                harness_line(harness),
                "",
                f"<!-- /harness:{harness} -->",
            )
        )
    if extra_section:
        parts.extend(("", f"## {cases.new_section}", "", harness_line("extension")))
    return frontmatter + "\n".join(parts) + "\n"


def version_triples() -> SearchStrategy[tuple[int, int, int]]:
    """Generate dotted-version components across the supported numeric domain."""
    part = st.integers(min_value=0, max_value=999)
    return st.tuples(part, part, part)


def dotted_version(parts: tuple[int, int, int]) -> str:
    """Render generated numeric components as a dotted version."""
    return ".".join(str(part) for part in parts)


def shared_region_bodies() -> SearchStrategy[str]:
    """Generate non-empty bodies that cannot form shared-region fences."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N"), whitelist_characters=" -_`"
        ),
        min_size=1,
    ).filter(lambda body: body.strip() != "")


@st.composite
def _bootstrap_wrap_cases(
    draw: st.DrawFn,
    threshold: float,
    relation: BootstrapThresholdRelation,
) -> BootstrapWrapCase:
    """Generate one exact threshold relation with no accidental common whole line."""
    threshold_fraction = Fraction(str(threshold)).limit_denominator()
    if not 0 < threshold_fraction < 1:
        raise ValueError(
            f"bootstrap threshold must be between zero and one: {threshold}"
        )

    scale = draw(st.integers(min_value=1, max_value=8))
    common_line_count = threshold_fraction.numerator * scale
    equal_divergent_count = (
        threshold_fraction.denominator - threshold_fraction.numerator
    ) * scale
    if relation is BootstrapThresholdRelation.ABOVE:
        largest_divergent_count = draw(
            st.integers(min_value=0, max_value=equal_divergent_count - 1)
        )
    elif relation is BootstrapThresholdRelation.AT:
        largest_divergent_count = equal_divergent_count
    else:
        largest_divergent_count = draw(
            st.integers(
                min_value=equal_divergent_count + 1,
                max_value=equal_divergent_count + common_line_count,
            )
        )

    smaller_divergent_count = draw(
        st.integers(min_value=0, max_value=largest_divergent_count)
    )
    if draw(st.booleans()):
        divergent_a, divergent_b = (
            largest_divergent_count,
            smaller_divergent_count,
        )
    else:
        divergent_a, divergent_b = (
            smaller_divergent_count,
            largest_divergent_count,
        )
    before_a = draw(st.integers(min_value=0, max_value=divergent_a))
    before_b = draw(st.integers(min_value=0, max_value=divergent_b))
    line_width = draw(st.integers(min_value=1, max_value=20))
    common_character, character_a, character_b = draw(
        st.lists(
            st.sampled_from(tuple(string.ascii_letters + string.digits)),
            min_size=3,
            max_size=3,
            unique=True,
        )
    )

    def lines(character: str, count: int) -> str:
        return f"{character * line_width}\n" * count

    shared = lines(common_character, common_line_count)
    content_a = (
        lines(character_a, before_a)
        + shared
        + lines(character_a, divergent_a - before_a)
    )
    content_b = (
        lines(character_b, before_b)
        + shared
        + lines(character_b, divergent_b - before_b)
    )
    return BootstrapWrapCase(
        content_a=content_a,
        content_b=content_b,
        shared_body=shared.rstrip("\n"),
        relation=relation,
    )


def bootstrap_wrap_cases(
    threshold: float,
    relation: BootstrapThresholdRelation,
) -> SearchStrategy[BootstrapWrapCase]:
    """Generate root pairs above, at, or below the supplied source threshold."""
    return _bootstrap_wrap_cases(threshold, relation)


def shared_document(module: ModuleType, name: str, body: str) -> str:
    """Render generated body text inside source-owned shared-region markers."""
    return (
        f"{module.shared_open_marker(name)}\n\n{body}\n\n"
        f"{module.shared_close_marker(name)}\n"
    )


def unsupported_language_tokens(
    supported_languages: tuple[str, ...],
) -> SearchStrategy[str]:
    """Generate one CLI language token outside the template-declared language set."""
    return st.text(alphabet=_LANGUAGE_TOKEN_CHARACTERS, min_size=1).filter(
        lambda token: token not in supported_languages
    )
