"""Compliance tests for cross-cutting reviewing-changes rules.

Covers the Compliance clauses in ``../reviewing-changes.md`` that are
universal rules across the skill's files rather than per-case scenarios:

- Every script under ``plugins/spec-tree/skills/reviewing-changes/scripts/``
  performs filesystem effects only through ``thread_store`` — no script
  calls ``open()``, ``Path.write_*``, ``os.remove``, ``os.unlink``,
  ``shutil.rmtree``, or any other direct filesystem-write primitive.
- The swappable prompt template lives at
  ``plugins/spec-tree/skills/reviewing-changes/references/review-prompt.md``
  and the skill prose loads it via ``${CLAUDE_SKILL_DIR}/references/
  review-prompt.md``.
- The wrapper agent at ``plugins/spec-tree/agents/changes-reviewer.md``
  declares ``model: sonnet``, ``tools: Bash, Read, Skill``, and ``skills:``
  listing ``spec-tree:reviewing-changes`` — tolerated absent during the
  slice authoring phase, asserted shape when present.
- No script under the skill's ``scripts/`` directory imports a third-party
  package, depends on ``uv`` at runtime, or imports any ``outcomeeng_*``
  module.
- The judgment-style review prompt is NEVER embedded inside ``SKILL.md``
  or any ``.py`` file — the prompt is one standalone markdown file.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys

import pytest

from outcomeeng_testing.harnesses.reviewing_changes import (
    COMPUTE_DIFF_SCRIPT,
    RENDER_REVIEW_SCRIPT,
    REVIEW_PROMPT_PATH,
    REVIEW_RESULT_MODULE_PATH,
    SCRIPTS_DIR,
    SKILL_DIR,
    SKILL_FILE,
    VALIDATE_REVIEW_RESULT_SCRIPT,
    WRAPPER_AGENT_PATH,
)


# Filesystem-write primitives the scripts MUST NOT use directly. Read
# primitives (``open(..., 'rb')``, ``Path.read_bytes``, ``Path.read_text``)
# are permitted because ``compute_diff.py`` legitimately reads the diff
# subprocess's stdout and reads pr.json via ``thread_store``.
FORBIDDEN_NAME_CALLS = {"open"}
FORBIDDEN_ATTR_CALLS = {
    ("os", "remove"),
    ("os", "unlink"),
    ("shutil", "rmtree"),
}
FORBIDDEN_METHOD_NAMES = {"write_text", "write_bytes", "unlink"}

# Names of modules that ship under the reviewing-changes scripts/ directory
# (sibling-imported via bare names) — these are not "third-party" or
# "outcomeeng_*" violations.
LOCAL_REVIEWING_CHANGES_MODULES = frozenset(
    {
        "review_result",
        "validate_review_result",
        "compute_diff",
        "render_review",
        "thread_store",
    }
)

# Phrases that are vocative LLM-facing instructions — they only appear in
# a prompt body, never in orchestration prose or code. If any of these
# show up in SKILL.md or a .py file, the prompt body has leaked from the
# reference file into a place it should not live.
#
# Schema vocabulary (``must_fix``, ``request_changes``, ``acknowledgements``)
# is excluded because those tokens legitimately appear in rendering code
# (e.g., to switch on severity) and in skill-prose orchestration
# (referring to the schema the agent emits).
PROMPT_FINGERPRINT_PHRASES = (
    "You are reviewing",
    "Apply each of the eight concerns",
)


def _script_files() -> list[pathlib.Path]:
    """Return every ``.py`` file under the reviewing-changes ``scripts/`` dir."""
    if not SCRIPTS_DIR.is_dir():
        return []
    return [
        p for p in sorted(SCRIPTS_DIR.rglob("*.py")) if "__pycache__" not in p.parts
    ]


def _top_level_name(module: str) -> str:
    return module.split(".", 1)[0]


def _imported_modules(source: str) -> list[str]:
    tree = ast.parse(source)
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(_top_level_name(alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                continue
            if node.module is None:
                continue
            modules.append(_top_level_name(node.module))
    return modules


class TestScriptsRouteThroughThreadStore:
    """Every script delegates filesystem effects to the ``thread_store`` facade."""

    @pytest.mark.parametrize(
        "script_path",
        [
            REVIEW_RESULT_MODULE_PATH,
            VALIDATE_REVIEW_RESULT_SCRIPT,
            COMPUTE_DIFF_SCRIPT,
            RENDER_REVIEW_SCRIPT,
        ],
    )
    def test_script_uses_no_direct_write_primitives(
        self, script_path: pathlib.Path
    ) -> None:
        source = script_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        violations: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name) and func.id in FORBIDDEN_NAME_CALLS:
                violations.append(f"call to {func.id}() at line {node.lineno}")
            elif isinstance(func, ast.Attribute):
                if func.attr in FORBIDDEN_METHOD_NAMES:
                    violations.append(f".{func.attr}() at line {node.lineno}")
                value = func.value
                if (
                    isinstance(value, ast.Name)
                    and (value.id, func.attr) in FORBIDDEN_ATTR_CALLS
                ):
                    violations.append(f"{value.id}.{func.attr}() at line {node.lineno}")
        assert not violations, (
            f"{script_path.name} uses forbidden direct-write filesystem "
            f"primitives: {'; '.join(violations)}"
        )


class TestScriptsAreStdlibOnly:
    """No script imports a third-party package or any ``outcomeeng_*`` module."""

    def test_no_third_party_or_outcomeeng_imports(self) -> None:
        violations: list[str] = []
        stdlib = set(sys.stdlib_module_names)
        for script in _script_files():
            source = script.read_text(encoding="utf-8")
            for module in _imported_modules(source):
                if module in stdlib:
                    continue
                if module in LOCAL_REVIEWING_CHANGES_MODULES:
                    continue
                violations.append(f"{script.name}: import '{module}'")
        assert not violations, (
            "reviewing-changes scripts import non-stdlib, non-local modules:\n"
            + "\n".join(violations)
        )

    def test_no_outcomeeng_imports(self) -> None:
        violations: list[str] = []
        for script in _script_files():
            source = script.read_text(encoding="utf-8")
            for module in _imported_modules(source):
                if module.startswith("outcomeeng_") or module == "outcomeeng":
                    violations.append(f"{script.name}: import '{module}'")
        assert not violations, (
            "reviewing-changes scripts import outcomeeng_* modules "
            "(forbidden by Plugin Portability Constraints):\n" + "\n".join(violations)
        )


class TestSwappablePromptIsAStandaloneFile:
    """The judgment-style review prompt lives only at the reference path."""

    def test_review_prompt_file_exists(self) -> None:
        assert REVIEW_PROMPT_PATH.is_file(), (
            f"review-prompt.md must exist at {REVIEW_PROMPT_PATH}"
        )

    def test_skill_md_loads_prompt_via_claude_skill_dir(self) -> None:
        """SKILL.md must reference the prompt path via ``${CLAUDE_SKILL_DIR}``."""
        skill_source = SKILL_FILE.read_text(encoding="utf-8")
        assert "${CLAUDE_SKILL_DIR}/references/review-prompt.md" in skill_source, (
            "SKILL.md must load the swappable prompt via "
            "${CLAUDE_SKILL_DIR}/references/review-prompt.md"
        )

    def test_prompt_fingerprint_phrases_appear_only_in_reference_file(self) -> None:
        """LLM-vocative prompt phrases live only in ``references/review-prompt.md``.

        Vocative phrases like "You are reviewing" or "Apply each of the
        eight concerns" address the model directly and only make sense in
        prompt content. They must not leak into orchestration prose
        (SKILL.md) or code (``*.py``). Schema vocabulary tokens like
        ``must_fix`` are excluded from this check because they
        legitimately appear in renderers and in skill prose that names
        the schema vocabulary the agent emits.

        The reference file itself must contain every fingerprint phrase —
        otherwise the phrases stopped being valid LLM-prompt markers and
        the leak check no longer falsifies anything.
        """
        prompt_source = REVIEW_PROMPT_PATH.read_text(encoding="utf-8")
        for phrase in PROMPT_FINGERPRINT_PHRASES:
            assert phrase in prompt_source, (
                f"prompt fingerprint phrase {phrase!r} no longer appears in "
                f"{REVIEW_PROMPT_PATH.name} — update the test or restore "
                f"the prompt phrasing"
            )

        leaked: list[str] = []
        skill_source = SKILL_FILE.read_text(encoding="utf-8")
        for phrase in PROMPT_FINGERPRINT_PHRASES:
            if phrase in skill_source:
                leaked.append(f"{SKILL_FILE.name}: contains '{phrase}'")
        for script in _script_files():
            source = script.read_text(encoding="utf-8")
            for phrase in PROMPT_FINGERPRINT_PHRASES:
                if phrase in source:
                    leaked.append(f"{script.name}: contains '{phrase}'")
        assert not leaked, (
            "LLM-vocative prompt phrases leaked outside "
            f"{REVIEW_PROMPT_PATH.name}:\n" + "\n".join(leaked)
        )


class TestNoSecondSchemaRepresentation:
    """The schema lives in one Python module. Alternate representations forbidden.

    ADR clause: ``review_result.py`` is the canonical schema; a JSON
    Schema document, OpenAPI fragment, or duplicate dataclass set would
    invite drift between representations. The check globs the skill
    directory for the artifact shapes a second representation would
    take.
    """

    def test_no_alternate_schema_file_exists(self) -> None:
        forbidden_globs = ("*.schema.json", "*.xsd", "openapi.*", "schema.*")
        violations: list[str] = []
        for pattern in forbidden_globs:
            for match in SKILL_DIR.rglob(pattern):
                if "__pycache__" in match.parts:
                    continue
                violations.append(str(match.relative_to(SKILL_DIR)))
        assert not violations, (
            "alternate schema representation found in reviewing-changes "
            f"skill directory (forbidden — the canonical schema lives in "
            f"review_result.py): {violations}"
        )


class TestWrapperAgentFrontmatter:
    """The wrapper agent (when present) has the spec-mandated shape.

    The agent file is authored in a later step of the slice. Tests
    tolerate its absence here so the suite passes during the implementation
    phase; the moment the file lands, the frontmatter is asserted.
    """

    def test_agent_when_present_has_required_frontmatter(self) -> None:
        if not WRAPPER_AGENT_PATH.is_file():
            pytest.skip(
                f"wrapper agent {WRAPPER_AGENT_PATH.name} not yet authored — "
                "frontmatter assertion deferred"
            )
        content = WRAPPER_AGENT_PATH.read_text(encoding="utf-8")
        # The frontmatter is a YAML block bounded by ``---`` lines.
        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        assert match is not None, (
            f"{WRAPPER_AGENT_PATH.name} must begin with a YAML frontmatter "
            "block delimited by '---' lines"
        )
        frontmatter = match.group(1)
        assert re.search(r"^model:\s*sonnet\b", frontmatter, re.MULTILINE), (
            f"{WRAPPER_AGENT_PATH.name} frontmatter must declare 'model: sonnet'"
        )
        # Tools field must include Bash, Read, and Skill in any order.
        tools_match = re.search(r"^tools:\s*(.+)$", frontmatter, re.MULTILINE)
        assert tools_match is not None, (
            f"{WRAPPER_AGENT_PATH.name} frontmatter must declare 'tools:'"
        )
        tools_value = tools_match.group(1)
        for tool in ("Bash", "Read", "Skill"):
            assert tool in tools_value, (
                f"{WRAPPER_AGENT_PATH.name} 'tools:' must include {tool!r}; "
                f"got: {tools_value!r}"
            )
        # Skills field must list spec-tree:reviewing-changes.
        assert "spec-tree:reviewing-changes" in frontmatter, (
            f"{WRAPPER_AGENT_PATH.name} 'skills:' must list spec-tree:reviewing-changes"
        )
