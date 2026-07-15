"""Generated input domains for instruction-block evidence.

The instruction-block harness owns filesystems, subprocesses, and cleanup. This
module owns variable input domains and source-derived carrier cases. Carrier
text is derived from the production module's harness, filename, marker, and
template contracts so the harness never becomes a second source of product
vocabulary.
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
    root_claude_body: str
    root_agents_body: str
    root_shared_body: str
    shared_region_name: str
    shared_region_body: str
    shared_region_body_alt: str
    root_near_identical_claude: str
    root_near_identical_codex: str
    root_near_identical_shared: str
    root_legacy_managed_body: str
    root_straddling_claude: str
    root_straddling_codex: str
    root_midline_claude: str
    root_midline_codex: str
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


def _carrier_body(filename: str, harness: str) -> str:
    """Build a root-file payload from source-owned filename and harness values."""
    return f"# {filename}\n\n{harness} repository instructions.\n"


def _boundary_pairs(
    harness_claude: str,
    harness_codex: str,
) -> tuple[tuple[str, str, str], tuple[str, str], tuple[str, str]]:
    """Generate meaningful bootstrap line-boundary carrier pairs."""
    near_common = "".join(
        f"shared line {index} for {harness_claude} and {harness_codex}\n"
        for index in range(30)
    )
    near = (
        near_common + f"shared opening then {harness_claude} tail\n",
        near_common + f"shared opening then {harness_codex} tail\n",
        near_common,
    )
    whole_lines = "".join(
        f"whole shared line {index} for both harnesses\n" for index in range(6)
    )
    long_prefix = "x" * 480
    straddling = (
        whole_lines + long_prefix + f" {harness_claude} tail\n",
        whole_lines + long_prefix + f" {harness_codex} tail\n",
    )
    midline_common = "".join(
        f"identical generated line {index} for both harnesses\n" for index in range(20)
    )
    midline = (
        "shared prose here\n" + midline_common,
        f"{harness_codex} prefix shared prose here\n" + midline_common,
    )
    return near, straddling, midline


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
    near, straddling, midline = _boundary_pairs(harness_claude, harness_codex)
    shared_name = module.BOOTSTRAP_SHARED_REGION_NAME
    shared_body = module.router_marker(version, languages)
    shared_body_alt = module.router_marker(_prior_dotted_version(version), languages)
    legacy_open, legacy_close = module.LEGACY_MANAGED_BLOCK_MARKERS[0]
    root_shared_body = _carrier_body(shared_name, module.DEFAULT_TEMPLATE_SOURCE)
    legacy_metadata = (
        f"{module.MANAGED_TEMPLATE_VERSION_PREFIX} {version} -->\n"
        f"{module.MANAGED_TEMPLATE_SOURCE_PREFIX} "
        f"{module.DEFAULT_TEMPLATE_SOURCE} -->\n"
        f"{module.MANAGED_LANGUAGES_PREFIX} {','.join(languages)} -->\n"
    )
    root_legacy_managed_body = (
        f"{legacy_open}\n{legacy_metadata}{module.DEFAULT_TEMPLATE_SOURCE}\n"
        f"{legacy_close}\n\n{root_shared_body}"
    )
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
        root_claude_body=_carrier_body(instruction_claude, harness_claude),
        root_agents_body=_carrier_body(instruction_agents, harness_codex),
        root_shared_body=root_shared_body,
        shared_region_name=shared_name,
        shared_region_body=shared_body,
        shared_region_body_alt=shared_body_alt,
        root_near_identical_claude=near[0],
        root_near_identical_codex=near[1],
        root_near_identical_shared=near[2],
        root_legacy_managed_body=root_legacy_managed_body,
        root_straddling_claude=straddling[0],
        root_straddling_codex=straddling[1],
        root_midline_claude=midline[0],
        root_midline_codex=midline[1],
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
