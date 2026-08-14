"""Generated grant categories for grant-locality evidence.

The skill-directory variable names come from the validator, because they are the
values the spec tree declares and the validator complies with. What each grant
line is composed into — the field declaration, the surrounding tool list, the
body mention — is this module's own construction.
"""

from __future__ import annotations

from outcomeeng.validation.grant_locality import (
    ALLOWED_TOOLS_FIELD,
    SKILL_DIR_VARIABLES,
)
from outcomeeng_testing.generators.source_and_templating import source_scenarios


def _declaration(*grants: str) -> str:
    """Compose one `allowed-tools` field declaration carrying `grants`."""
    return f"{ALLOWED_TOOLS_FIELD}: Read, {', '.join(grants)}"


def escaping_grant_declarations() -> tuple[str, ...]:
    """One field declaration per way a grant escapes the skill directory.

    Every target spelling of the skill-directory variable appears, because the
    build renders one authored token into each generated tree and a rule reading
    a single spelling misses every skill in the other.
    """
    scenario = source_scenarios()[0]
    sibling = f"../{scenario.plugin}-standards/scripts/{scenario.skill}.py"
    return (
        tuple(
            _declaration(f'Bash(python3 "${{{variable}}}/{sibling}":*)')
            for variable in SKILL_DIR_VARIABLES
        )
        + tuple(
            # A bare parent reference with no trailing path still leaves the
            # directory, so the escape does not depend on what follows it.
            _declaration(f'Bash(cat "${{{variable}}}/..":*)')
            for variable in SKILL_DIR_VARIABLES
        )
        + tuple(
            # The parent reference need not lead: descending first and then rising
            # twice still lands above the skill directory.
            _declaration(
                f'Bash(python3 "${{{variable}}}/scripts/../../{scenario.plugin}/x.py":*)'
            )
            for variable in SKILL_DIR_VARIABLES
        )
        + tuple(
            # The shell concatenates adjacent quoted and unquoted pieces, so
            # closing the quote right after the variable reaches the same sibling
            # file as quoting the whole path. Both spellings are one path.
            _declaration(f'Bash(python3 "${{{variable}}}"/{sibling}:*)')
            for variable in SKILL_DIR_VARIABLES
        )
        + tuple(
            # The same concatenation with the trailing piece quoted separately,
            # which is the spelling a copied command line most often carries.
            _declaration(f'Bash(python3 "${{{variable}}}"/"{sibling}":*)')
            for variable in SKILL_DIR_VARIABLES
        )
        + tuple(
            # The YAML list form of the same field, which carries each grant on its
            # own indented line rather than in the declaration's scalar.
            "\n".join(
                (
                    f"{ALLOWED_TOOLS_FIELD}:",
                    "  - Read",
                    f'  - Bash(python3 "${{{variable}}}/{sibling}":*)',
                )
            )
            for variable in SKILL_DIR_VARIABLES
        )
    )


def local_grant_declarations() -> tuple[str, ...]:
    """One field declaration per grant that stays inside the skill directory."""
    scenario = source_scenarios()[0]
    own_entrypoint = tuple(
        _declaration(f'Bash(python3 "${{{variable}}}/scripts/{scenario.skill}.py":*)')
        for variable in SKILL_DIR_VARIABLES
    )
    # A descent that returns to the skill directory resolves inside it and names
    # no sibling, so it is not an escape.
    returning_descent = tuple(
        _declaration(f'Bash(python3 "${{{variable}}}/scripts/../scripts/run.py":*)')
        for variable in SKILL_DIR_VARIABLES
    )
    # The quote-split spelling of a path that stays inside the directory: the
    # widened parse reads the concatenation, so it must accept this too.
    split_quotes = tuple(
        _declaration(f'Bash(python3 "${{{variable}}}"/scripts/{scenario.skill}.py:*)')
        for variable in SKILL_DIR_VARIABLES
    )
    # Grants that carry no path at all, and a reference file read.
    pathless = (
        _declaration("Bash(git status:*)", "Glob", "Skill"),
        _declaration(f'Read("${{{SKILL_DIR_VARIABLES[0]}}}/references/notes.md")'),
    )
    # The YAML list form carrying only local grants: the widened parse must not
    # turn a supported spelling into a false positive.
    listed = tuple(
        "\n".join(
            (
                f"{ALLOWED_TOOLS_FIELD}:",
                "  - Read",
                f'  - Bash(python3 "${{{variable}}}/scripts/run.py":*)',
            )
        )
        for variable in SKILL_DIR_VARIABLES
    )
    return (*own_entrypoint, *returning_descent, *split_quotes, *pathless, *listed)


def body_mentions() -> tuple[str, ...]:
    """Escaping grants written outside an `allowed-tools` field declaration.

    A standard documenting the prohibited shape, and a skill body quoting one,
    both carry the text without declaring the grant.
    """
    scenario = source_scenarios()[0]
    escaping = f'Bash(python3 "${{{SKILL_DIR_VARIABLES[0]}}}/../{scenario.plugin}/scripts/x.py":*)'
    return (
        f"Never write {escaping} in frontmatter.",
        f"| {escaping} | rejected |",
        f"  {ALLOWED_TOOLS_FIELD}: {escaping}",
    )
