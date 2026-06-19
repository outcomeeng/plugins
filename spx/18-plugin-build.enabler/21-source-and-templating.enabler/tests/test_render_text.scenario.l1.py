"""Scenario evidence for render_text's conditional rendering behaviors.

The verbatim-inlining property (test_render_text.property.l1.py) is deliberately
scoped to directive-free, variable-delimiter-free bodies. These scenarios cover
the behaviors that scope excludes — each a build-relied-upon path through
render_text:

- Recursive expansion: a directive inside an included body is itself expanded,
  so includes and require_skill directives resolve at any nesting depth.
- Cycle detection: includes that form a reference cycle raise CyclicIncludeError
  instead of recursing without end.
- Variable pass: a template carrying the variable delimiter triggers a Jinja
  pass that substitutes bound variables — the source references the build target
  by name.

Directive and delimiter text is built from source-owned constructors
(format_directive) and constants so the cases track the production contract.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.build import (
    IMPLEMENTED,
    SHARED_FRAGMENT_FILENAME,
    VARIABLE_DELIMITER_END,
    VARIABLE_DELIMITER_START,
    CyclicIncludeError,
    IncludeDirective,
    RequireSkillDirective,
    expand_require_skill,
    format_directive,
    render_text,
)
from outcomeeng_testing.harnesses.src_tree import SrcTreeBuilder

SCOPE = "samplescope"
INNER_TOPIC = "inner-topic"
OUTER_TOPIC = "outer-topic"
SKILL_TOPIC = "skill-topic"
CYCLE_TOPIC_A = "cycle-topic-a"
CYCLE_TOPIC_B = "cycle-topic-b"

INNER_BODY = "Inner fragment body.\nSecond line.\n"
SKILL_REF = "develop:skill-standards"


def _fragment_path(topic: str) -> str:
    return f"{SCOPE}/{topic}/{SHARED_FRAGMENT_FILENAME}"


def _include_text(topic: str) -> str:
    return format_directive(IncludeDirective(path=_fragment_path(topic)))


@pytest.fixture(autouse=True)
def _require_module_implemented() -> None:
    if not IMPLEMENTED:
        pytest.fail(
            "outcomeeng.distribution.build is a stub; implement it before "
            "running this test, or filter via `spx test passing` "
            "(node is listed in spx/EXCLUDE)"
        )


class TestRecursiveIncludeExpansion:
    """render_text re-processes an inlined body, expanding nested directives."""

    def test_include_nested_in_included_body_is_expanded(self, tmp_path: Path) -> None:
        builder = SrcTreeBuilder(tmp_path)
        builder.add_shared_topic(SCOPE, INNER_TOPIC, INNER_BODY)
        builder.add_shared_topic(SCOPE, OUTER_TOPIC, _include_text(INNER_TOPIC))

        result = render_text(
            _include_text(OUTER_TOPIC), shared_root=builder.shared_root
        )

        # The outer include resolves to a body that is itself an include; the
        # nested include must also resolve, surfacing the innermost body.
        assert result == INNER_BODY

    def test_require_skill_nested_in_included_body_is_expanded(
        self, tmp_path: Path
    ) -> None:
        builder = SrcTreeBuilder(tmp_path)
        require_directive = format_directive(RequireSkillDirective(SKILL_REF))
        builder.add_shared_topic(SCOPE, SKILL_TOPIC, require_directive)

        result = render_text(
            _include_text(SKILL_TOPIC), shared_root=builder.shared_root
        )

        assert result == expand_require_skill(RequireSkillDirective(SKILL_REF))
        assert require_directive not in result


class TestCyclicIncludeDetection:
    """render_text raises CyclicIncludeError when includes form a cycle."""

    def test_mutually_referential_includes_raise_cyclic_include_error(
        self, tmp_path: Path
    ) -> None:
        builder = SrcTreeBuilder(tmp_path)
        builder.add_shared_topic(SCOPE, CYCLE_TOPIC_A, _include_text(CYCLE_TOPIC_B))
        builder.add_shared_topic(SCOPE, CYCLE_TOPIC_B, _include_text(CYCLE_TOPIC_A))

        with pytest.raises(CyclicIncludeError):
            render_text(_include_text(CYCLE_TOPIC_A), shared_root=builder.shared_root)


class TestVariableDelimiterJinjaPass:
    """A template carrying the variable delimiter triggers a Jinja pass."""

    def test_bound_variable_is_substituted(self) -> None:
        template = (
            f"target is {VARIABLE_DELIMITER_START} target {VARIABLE_DELIMITER_END}"
        )

        rendered_claude = render_text(
            template, variables={"target": Target.CLAUDE.value}
        )
        rendered_codex = render_text(template, variables={"target": Target.CODEX.value})

        # The same template substitutes the bound value — the source references
        # the build target by name, the binding emit supplies per target. The
        # bindings are the build's own target values.
        assert rendered_claude == f"target is {Target.CLAUDE.value}"
        assert rendered_codex == f"target is {Target.CODEX.value}"
