"""Generated domains for build directive and delimiter evidence."""

from __future__ import annotations

from hypothesis import strategies as st
from hypothesis.strategies import SearchStrategy

from outcomeeng.distribution.build import (
    BLOCK_DELIMITER_END,
    BLOCK_DELIMITER_START,
    Directive,
    IncludeDirective,
    RequireSkillDirective,
    VARIABLE_DELIMITER_END,
    VARIABLE_DELIMITER_START,
)
from outcomeeng.distribution.contracts import (
    STANDARD_JINJA_BLOCK_DELIMITER_END,
    STANDARD_JINJA_BLOCK_DELIMITER_START,
    STANDARD_JINJA_VARIABLE_DELIMITER_END,
    STANDARD_JINJA_VARIABLE_DELIMITER_START,
)

MAX_STANDARD_JINJA_BODY_LENGTH = 64


def directives() -> SearchStrategy[Directive]:
    """Generate every directive variant over arbitrary string payloads."""
    arguments = st.text()
    return st.one_of(
        st.builds(IncludeDirective, path=arguments),
        st.builds(RequireSkillDirective, skill_ref=arguments),
    )


def standard_jinja_syntax() -> SearchStrategy[str]:
    """Generate standard-Jinja forms that contain no custom build delimiter."""
    custom_delimiter_characters = "".join(
        {
            *BLOCK_DELIMITER_START,
            *BLOCK_DELIMITER_END,
            *VARIABLE_DELIMITER_START,
            *VARIABLE_DELIMITER_END,
        }
    )
    body = st.text(
        alphabet=st.characters(blacklist_characters=custom_delimiter_characters),
        max_size=MAX_STANDARD_JINJA_BODY_LENGTH,
    )
    return st.one_of(
        body.map(
            lambda value: (
                f"{STANDARD_JINJA_BLOCK_DELIMITER_START}{value}"
                f"{STANDARD_JINJA_BLOCK_DELIMITER_END}"
            )
        ),
        body.map(
            lambda value: (
                f"{STANDARD_JINJA_VARIABLE_DELIMITER_START}{value}"
                f"{STANDARD_JINJA_VARIABLE_DELIMITER_END}"
            )
        ),
    )
