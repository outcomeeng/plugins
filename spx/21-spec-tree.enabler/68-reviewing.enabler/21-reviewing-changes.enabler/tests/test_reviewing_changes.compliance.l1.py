"""Compliance tests for cross-cutting review-changes rules.

Covers the Compliance clauses in ``../reviewing-changes.md`` that are
universal rules across the skill's files rather than per-case scenarios:

- Every script under ``plugins/spec-tree/skills/review-changes/scripts/``
  performs filesystem effects only through ``thread_store`` — no script
  calls ``open()``, ``Path.write_*``, ``os.remove``, ``os.unlink``,
  ``shutil.rmtree``, or any other direct filesystem-write primitive.
- The swappable prompt template lives at
  ``plugins/spec-tree/skills/review-changes/references/review-prompt.md``
  and the skill prose loads it via ``${CLAUDE_SKILL_DIR}/references/
  review-prompt.md``.
- The wrapper agent at ``plugins/spec-tree/agents/changes-reviewer.md``
  declares ``model: sonnet``, ``tools: Bash, Read, Skill``, and ``skills:``
  listing ``spec-tree:review-changes`` — tolerated absent during the
  slice authoring phase, asserted shape when present.
- The per-section render templates live under
  ``plugins/spec-tree/skills/review-changes/references/render/`` and
  ``render_review.py`` loads them via stdlib ``string.Template`` —
  rendered shape is data the script substitutes, not f-string
  concatenation in code.
- No script under the skill's ``scripts/`` directory imports a third-party
  package, depends on ``uv`` at runtime, or imports any ``outcomeeng_*``
  module.
- The judgment-style review prompt is NEVER embedded inside ``SKILL.md``
  or any ``.py`` file — the prompt is one standalone markdown file.
- The render templates are NEVER embedded inside ``render_review.py`` as
  f-string literals — the templates are standalone markdown files under
  ``references/render/``.
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
    RENDER_TEMPLATES_DIR,
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
# subprocess's stdout and reads the optional ``changes.json`` override via
# ``thread_store``.
FORBIDDEN_NAME_CALLS = {"open"}
FORBIDDEN_ATTR_CALLS = {
    ("os", "remove"),
    ("os", "unlink"),
    ("shutil", "rmtree"),
}
FORBIDDEN_METHOD_NAMES = {"write_text", "write_bytes", "unlink"}

# Names of modules that ship under the review-changes scripts/ directory
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

# Phrases that mark judgment-style review prompt content — they only
# appear in a prompt body, never in orchestration prose or code. If any
# of these show up in SKILL.md or a .py file, the prompt body has leaked
# from the reference file into a place it should not live.
#
# Schema vocabulary (``blocking``, ``request_changes``, ``acknowledgements``)
# is excluded because those tokens legitimately appear in rendering code
# (e.g., to switch on severity) and in skill-prose orchestration
# (referring to the schema the agent emits).
PROMPT_FINGERPRINT_PHRASES = (
    "Review a labeled diff bundle",
    "Inspect every section",
)


def _script_files() -> list[pathlib.Path]:
    """Return every ``.py`` file under the review-changes ``scripts/`` dir."""
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
            "review-changes scripts import non-stdlib, non-local modules:\n"
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
            "review-changes scripts import outcomeeng_* modules "
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
        """Prompt fingerprint phrases live only in ``references/review-prompt.md``.

        Prompt-specific phrases such as "Review a labeled diff bundle" or
        "Apply each of the eight concerns" only make sense in prompt
        content. They must not leak into orchestration prose (SKILL.md) or
        code (``*.py``). Schema vocabulary tokens like ``must_fix`` are
        excluded from this check because they legitimately appear in
        renderers and in skill prose that names the schema vocabulary the
        reviewer emits.

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
            "Prompt fingerprint phrases leaked outside "
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
            "alternate schema representation found in review-changes "
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
        # Skills field must list spec-tree:review-changes.
        assert "spec-tree:review-changes" in frontmatter, (
            f"{WRAPPER_AGENT_PATH.name} 'skills:' must list spec-tree:review-changes"
        )


class TestComputeDiffSlugIsOptional:
    """``compute_diff.py --slug`` is optional — the script derives the slug.

    Guards against an accidental regression where ``--slug`` is made
    required again. The agent never names a slug in its prose; the script
    falls back to ``thread_store.current_slug()`` when ``--slug`` is
    omitted. Inspecting the argparse parser directly is faster than
    fixturing a git repo + running subprocess.
    """

    def test_compute_diff_slug_argument_is_optional(self) -> None:
        if not COMPUTE_DIFF_SCRIPT.is_file():
            pytest.skip("compute_diff.py not yet present")
        # Source-level check: argparse declares --slug with required=False
        # (the default) or omits required=True from add_argument.
        source = COMPUTE_DIFF_SCRIPT.read_text(encoding="utf-8")
        # Look for the add_argument call for --slug and confirm
        # required=True is NOT set on it.
        slug_arg_match = re.search(
            r"add_argument\(\s*['\"]--slug['\"][^)]*\)", source, re.DOTALL
        )
        assert slug_arg_match is not None, (
            "compute_diff.py must declare a --slug argparse argument "
            "(even if optional) so callers can override slug derivation"
        )
        assert "required=True" not in slug_arg_match.group(0), (
            "compute_diff.py --slug must NOT be required=True — the script "
            "derives the slug via thread_store.current_slug() when omitted"
        )


REQUIRED_RENDER_TEMPLATES = (
    "document.md",
    "finding-blocking.md",
    "finding-debt.md",
    "none-blocking.md",
    "none-debt.md",
    "acknowledgements.md",
)


class TestRenderTemplatesAreDataFiles:
    """Render templates live under ``references/render/`` as standalone files.

    The rendered ``review.md`` shape (two-severity headings,
    per-severity ``none`` census markers, finding body shape) is the externally
    observable verdict format. Two surfaces consume it (the local verification skill
    and the GH ``spec-tree-review`` workflow); both must read from the
    same source.
    These tests guard the file enumeration, the template-loading
    discipline of ``render_review.py``, and the absence of embedded
    f-string render literals.
    """

    @pytest.mark.parametrize("template_name", REQUIRED_RENDER_TEMPLATES)
    def test_template_file_exists(self, template_name: str) -> None:
        path = RENDER_TEMPLATES_DIR / template_name
        assert path.is_file(), (
            f"required render template {template_name!r} missing at {path}"
        )

    def test_render_review_loads_templates_via_string_template(self) -> None:
        if not RENDER_REVIEW_SCRIPT.is_file():
            pytest.skip("render_review.py not yet present")
        source = RENDER_REVIEW_SCRIPT.read_text(encoding="utf-8")
        # Source-level checks: the script imports `string` and uses
        # `string.Template` for substitution. Both are required for the
        # render-shape-as-data invariant.
        assert re.search(r"^import\s+string\b", source, re.MULTILINE), (
            "render_review.py must import the stdlib `string` module to "
            "use string.Template for render substitution"
        )
        assert "string.Template(" in source, (
            "render_review.py must instantiate string.Template — required "
            "by the render-templates-as-data invariant"
        )

    def test_render_review_does_not_embed_template_headings(self) -> None:
        if not RENDER_REVIEW_SCRIPT.is_file():
            pytest.skip("render_review.py not yet present")
        source = RENDER_REVIEW_SCRIPT.read_text(encoding="utf-8")
        # Render-class heading prefixes must NOT appear as literal
        # strings in the script — they belong in the template files.
        forbidden_in_script = (
            "### BLOCKING",
            "### DEBT",
            "### FOLLOW-UP",
            "### NEEDS-ANSWER",
        )
        for needle in forbidden_in_script:
            assert needle not in source, (
                f"render_review.py must not embed the render-template "
                f"literal {needle!r} — move it to references/render/"
            )


class TestPromptTeachesRuleCitation:
    """The review prompt instructs the model to populate ``Finding.rule`` as a citation.

    The arbiter enforces structural form; the prompt enforces the semantic
    that ``rule`` cites an existing rule in the spec-tree or skill
    ecosystem. The prompt must contain a Rule citation section that names
    the accepted path forms and forbids text/action/location populations.
    """

    def test_prompt_contains_rule_citation_section(self) -> None:
        prompt_source = REVIEW_PROMPT_PATH.read_text(encoding="utf-8")
        assert "## Rule citation" in prompt_source, (
            "review-prompt.md must include a 'Rule citation' section "
            "that defines what Finding.rule should contain"
        )

    def test_prompt_names_accepted_rule_path_forms(self) -> None:
        prompt_source = REVIEW_PROMPT_PATH.read_text(encoding="utf-8")
        # Each accepted form's distinguishing prefix must appear in the
        # prompt so the model can pattern-match its citations.
        for prefix in ("spx/", "plugins/", "SKILL.md", "AGENTS.md", "CLAUDE.md"):
            assert prefix in prompt_source, (
                f"review-prompt.md must mention the {prefix!r} citation form "
                "so the model populates Finding.rule with the correct shape"
            )

    def test_prompt_forbids_text_action_or_location_in_rule(self) -> None:
        prompt_source = REVIEW_PROMPT_PATH.read_text(encoding="utf-8")
        # The prompt must explicitly state that rule is a citation, not
        # text/action/location. The "Never populate it with" anchor
        # makes the prohibition findable for review and stable for tests.
        assert "Never populate it with" in prompt_source, (
            "review-prompt.md must include an explicit 'Never populate it "
            "with' clause forbidding prose/action/location text in Finding.rule"
        )
