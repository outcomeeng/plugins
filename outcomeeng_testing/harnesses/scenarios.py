"""Named scenario fixtures for build tests.

Each scenario is a frozen dataclass that documents one shape of src/ tree
plus the queries tests run against it. Scenarios are reusable across many
tests, so adding a new test for an established shape is a one-liner.

Scenarios call the harness immediately when applied; they do not stage
state. The IncludeScenario.apply() method, for example, calls
SrcTreeBuilder.add_shared_topic() and returns the builder for chaining.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from outcomeeng.scripts.build_plugins import (
    BLOCK_DELIMITER_END,
    BLOCK_DELIMITER_START,
    IncludeDirective,
    SHARED_FRAGMENT_FILENAME,
)
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder


@dataclass(frozen=True)
class IncludeScenario:
    """A shared topic that exists at src/_shared/<scope>/<topic>/fragment.md.

    Tests apply the scenario to a SrcTreeBuilder, then construct templates
    that reference the fragment via the directive() property.
    """

    scope: str
    topic: str
    fragment_body: str

    @property
    def fragment_path(self) -> str:
        """Relative path under shared_root to the fragment file."""
        return f"{self.scope}/{self.topic}/{SHARED_FRAGMENT_FILENAME}"

    @property
    def directive(self) -> IncludeDirective:
        """The include directive that resolves to this scenario's fragment."""
        return IncludeDirective(path=self.fragment_path)

    @property
    def directive_text(self) -> str:
        """The source-text form of the include directive."""
        return (
            f"{BLOCK_DELIMITER_START} include '{self.fragment_path}' "
            f"{BLOCK_DELIMITER_END}"
        )

    def apply(self, builder: SrcTreeBuilder) -> SrcTreeBuilder:
        """Materialize the scenario's shared topic on the given builder."""
        return builder.add_shared_topic(self.scope, self.topic, self.fragment_body)


# A single shared topic with a small fragment body. The simplest case for
# verifying the include directive's behavior end-to-end.
SCENARIO_SIMPLE_INCLUDE: Final = IncludeScenario(
    scope="samplelang",
    topic="code-standards",
    fragment_body="# Code Standards\n\nUse named constants for all literals.",
)


# A shared topic whose fragment body spans multiple paragraphs and contains
# both prose and a small markdown structure. Verifies the include directive
# preserves complex content verbatim.
SCENARIO_MULTILINE_INCLUDE: Final = IncludeScenario(
    scope="samplelang",
    topic="test-standards",
    fragment_body=(
        "# Test Standards\n"
        "\n"
        "## Naming\n"
        "\n"
        "- `test_<subject>.<evidence>.<level>.py` for Python.\n"
        "- `<subject>.<evidence>.<level>.test.ts` for TypeScript.\n"
        "\n"
        "## Coverage\n"
        "\n"
        "Every assertion links to at least one test file.\n"
    ),
)
