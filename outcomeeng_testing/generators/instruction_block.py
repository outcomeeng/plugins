"""Generated input domains for instruction-block evidence.

The instruction-block harness owns filesystems, fixtures, subprocesses, and
cleanup. This module owns variable input domains and source-derived protocol
cases from the production module's harness, filename, marker, and template
contracts.
"""

from __future__ import annotations

import string
from dataclasses import dataclass
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


def free_root_contents() -> SearchStrategy[str]:
    """Generate root content with line variation and no fence-forming characters."""
    return st.text(
        alphabet=st.characters(
            whitelist_categories=("L", "N"), whitelist_characters=" -_`\n"
        ),
        max_size=200,
    )


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
