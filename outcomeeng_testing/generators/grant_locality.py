"""Generated grant categories for grant-locality evidence.

The skill-directory variable names come from the validator, because they are the
values the spec tree declares and the validator complies with. What each grant
line is composed into — the field declaration, the surrounding tool list, the
body mention — is this module's own construction.
"""

from __future__ import annotations

from dataclasses import dataclass

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
            # The shell reads `$VAR/x` and `${VAR}/x` identically, so the
            # unbraced spelling reaches the same sibling file.
            _declaration(f"Bash(python3 ${variable}/{sibling}:*)")
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
    # The unbraced spelling of a path that stays inside the directory: widening
    # the pattern to read it must not turn a supported spelling into a finding.
    unbraced = tuple(
        _declaration(f"Bash(python3 ${variable}/scripts/{scenario.skill}.py:*)")
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
    return (
        *own_entrypoint,
        *returning_descent,
        *split_quotes,
        *unbraced,
        *pathless,
        *listed,
    )


def _escaping_grant() -> str:
    """One escaping grant, as every body and file category writes it."""
    scenario = source_scenarios()[0]
    return f'Bash(python3 "${{{SKILL_DIR_VARIABLES[0]}}}/../{scenario.plugin}/scripts/x.py":*)'


def body_mentions() -> tuple[str, ...]:
    """Escaping grants written outside an `allowed-tools` field declaration.

    A standard documenting the prohibited shape, a table row rejecting it, an
    indented quotation, and the column-zero spelling a fenced example carries.
    The last one is indistinguishable from a declaration line by itself, so it
    is what makes the frontmatter boundary the thing under test rather than the
    leading whitespace.
    """
    escaping = _escaping_grant()
    return (
        f"Never write {escaping} in frontmatter.",
        f"| {escaping} | rejected |",
        f"  {ALLOWED_TOOLS_FIELD}: {escaping}",
        f"{ALLOWED_TOOLS_FIELD}: {escaping}",
    )


def skill_files_whose_body_mentions_an_escaping_grant() -> tuple[str, ...]:
    """One whole skill file per body spelling of a prohibited grant.

    Each file's frontmatter declares only local grants and its body carries one
    `body_mentions` category, so scanning the whole file rather than the
    frontmatter turns each of them into a violation the skill does not commit.
    """
    local = local_grant_declarations()[0]
    return tuple(
        f"---\nname: standards\n{local}\n---\n\n<constraints>\n\n{mention}\n\n</constraints>\n"
        for mention in body_mentions()
    )


def skill_files_whose_grants_are_local() -> tuple[str, ...]:
    """Whole skill files declaring only local grants, however the body reads.

    The second file writes the prohibited declaration in its body at column
    zero, inside a fence, which is how a standard shows the shape it rejects.
    Its frontmatter grants are local, so the file complies — a rule reading past
    the frontmatter fails the very skill that documents the rule.
    """
    local = local_grant_declarations()[0]
    escaping = _escaping_grant()
    compliant = (
        f"---\nname: example\n{local}\n---\n\n<objective>\nOne output.\n</objective>\n"
    )
    documenting = (
        f"---\nname: standards\n{local}\n---\n\n<constraints>\n\n"
        f"NEVER write this declaration:\n\n"
        f"```yaml\n{ALLOWED_TOOLS_FIELD}: {escaping}\n```\n\n</constraints>\n"
    )
    return (compliant, documenting)


@dataclass(frozen=True)
class EscapingSkillFile:
    """A skill file whose frontmatter escapes, with what its diagnostic must say.

    `declaration_line` is counted from this module's own composition, and
    `variable` and `parent_segment` are the tokens it wrote into the grant. None
    of the three is read back from the validator, so a diagnostic that disagrees
    with them fails rather than agreeing with a defect twice.
    """

    content: str
    declaration_line: int
    variable: str
    parent_segment: str


def skill_file_whose_grant_escapes() -> EscapingSkillFile:
    """One whole skill file whose frontmatter declares an escaping grant."""
    variable = SKILL_DIR_VARIABLES[0]
    scenario = source_scenarios()[0]
    grant = f'Bash(python3 "${{{variable}}}/../{scenario.plugin}/scripts/x.py":*)'
    preamble = ("---", "name: example")
    body = ("---", "", "<objective>", "One output.", "</objective>", "")
    return EscapingSkillFile(
        content="\n".join((*preamble, _declaration(grant), *body)),
        declaration_line=len(preamble) + 1,
        variable=variable,
        parent_segment="..",
    )
