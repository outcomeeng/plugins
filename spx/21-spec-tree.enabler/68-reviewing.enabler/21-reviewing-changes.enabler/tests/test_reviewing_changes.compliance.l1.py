"""Compliance tests for cross-cutting review-changes rules.

Covers the Compliance clauses in ``../reviewing-changes.md`` that are
universal rules across the skill's files rather than per-case scenarios:

- Every script under ``plugins/spec-tree/skills/review-changes/scripts/``
  writes no durable review state. ``compute_diff.py`` may write only the
  caller-owned scratch review-input bundle files; the remaining scripts use no
  direct write primitives.
- The swappable prompt template lives at
  ``plugins/spec-tree/skills/review-changes/references/review-prompt.md``
  and the skill prose loads it via ``${CLAUDE_SKILL_DIR}/references/
  review-prompt.md``.
- The wrapper agent at ``plugins/spec-tree/agents/changes-reviewer.md``
  declares ``model: sonnet``, ``tools: Bash, Read, Skill``, and ``skills:``
  listing ``spec-tree:review-changes`` — tolerated absent during the
  slice authoring phase, asserted shape when present.
- The scripts/ directory holds the audit-parity set — the policy module
  plus ``compute_diff.py`` and ``journal_emit.py`` — with no parallel
  validation or renderer script, so the human surface comes only from the
  sealed journal prefix.
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
    JOURNAL_EMIT_SCRIPT,
    REVIEW_PROMPT_PATH,
    REVIEW_RESULT_MODULE_PATH,
    SCRIPTS_DIR,
    SKILL_DIR,
    SKILL_FILE,
    WRAPPER_AGENT_PATH,
)

# Filesystem-write primitives the scripts MUST NOT use directly. Read
# primitives (``open(..., 'rb')``, ``Path.read_bytes``, ``Path.read_text``)
# are permitted because ``compute_diff.py`` legitimately reads the diff
# subprocess's stdout and read user-provided payload/template files.
FORBIDDEN_NAME_CALLS = {"open"}
FORBIDDEN_ATTR_CALLS = {
    ("os", "remove"),
    ("os", "unlink"),
    ("shutil", "rmtree"),
}
FORBIDDEN_METHOD_NAMES = {"write_text", "write_bytes", "unlink", "mkdir"}
COMPUTE_DIFF_ALLOWED_WRITE_CALLS = {
    ("bundle_dir", "mkdir"),
    ("diff_path", "write_text"),
    ("manifest_path", "write_text"),
}

# Names of modules that ship under the review-changes scripts/ directory
# (sibling-imported via bare names) — these are not "third-party" or
# "outcomeeng_*" violations.
LOCAL_REVIEWING_CHANGES_MODULES = frozenset(
    {
        "review_result",
        "compute_diff",
        "journal_emit",
    }
)

# Phrases that mark judgment-style review prompt content — they only
# appear in a prompt body, never in orchestration prose or code. If any
# of these show up in SKILL.md or a .py file, the prompt body has leaked
# from the reference file into a place it should not live.
#
# Schema vocabulary (``blocking``, ``debt``, ``concern``) is excluded
# because those tokens legitimately appear in the adapter (switching on
# severity) and in skill-prose orchestration (naming the schema the agent
# emits).
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


class TestScriptsDoNotWriteStorageDirectly:
    """Review scripts write no durable review state directly."""

    @pytest.mark.parametrize(
        "script_path",
        [
            REVIEW_RESULT_MODULE_PATH,
            COMPUTE_DIFF_SCRIPT,
            JOURNAL_EMIT_SCRIPT,
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
                value = func.value
                if script_path == COMPUTE_DIFF_SCRIPT and isinstance(value, ast.Name):
                    if (value.id, func.attr) in COMPUTE_DIFF_ALLOWED_WRITE_CALLS:
                        continue
                if func.attr in FORBIDDEN_METHOD_NAMES:
                    violations.append(f".{func.attr}() at line {node.lineno}")
                if (
                    isinstance(value, ast.Name)
                    and (value.id, func.attr) in FORBIDDEN_ATTR_CALLS
                ):
                    violations.append(f"{value.id}.{func.attr}() at line {node.lineno}")
        assert not violations, (
            f"{script_path.name} uses forbidden direct-write filesystem "
            f"primitives outside the caller-owned review-input bundle exception: "
            f"{'; '.join(violations)}"
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

    def test_agent_when_present_exports_branch_identity_for_explicit_scope(
        self,
    ) -> None:
        if not WRAPPER_AGENT_PATH.is_file():
            pytest.skip(
                f"wrapper agent {WRAPPER_AGENT_PATH.name} not yet authored — "
                "branch export assertion deferred"
            )
        content = WRAPPER_AGENT_PATH.read_text(encoding="utf-8")
        assert "SPX_VERIFY_BRANCH=<branch_name>" in content, (
            f"{WRAPPER_AGENT_PATH.name} must export SPX_VERIFY_BRANCH with "
            "non-empty review scopes so detached CI checkouts can record "
            "branch run identity"
        )


class TestComputeDiffHasNoThreadAddressing:
    """``compute_diff.py`` does not accept thread-addressing arguments."""

    def test_compute_diff_has_no_slug_argument(self) -> None:
        if not COMPUTE_DIFF_SCRIPT.is_file():
            pytest.skip("compute_diff.py not yet present")
        source = COMPUTE_DIFF_SCRIPT.read_text(encoding="utf-8")
        assert "--slug" not in source
        assert "thread_store" not in source


# The audit-parity script set: the policy module plus the two CLI scripts.
# No parallel validation script (`validate_review_result.py`) and no parallel
# renderer (`render_review.py`) — validity is the `journal_emit finding-reported`
# per-finding parse, and the human surface is rendered only from the sealed
# journal prefix.
EXPECTED_SCRIPT_NAMES = frozenset(
    {"__init__.py", "review_result.py", "compute_diff.py", "journal_emit.py"}
)


class TestNoParallelReviewResultRenderer:
    """The human surface is rendered only from the sealed journal prefix.

    ``reviewing-changes.md`` NEVER clause: no script renders a parallel
    surface from the review-result JSON payload — the journal is the
    review's sole source of truth. The deleted ``render_review.py`` was
    exactly that parallel renderer; its absence, and the absence of a
    render-templates directory it consumed, is the falsifiable evidence.
    """

    def test_script_set_is_the_audit_parity_set(self) -> None:
        present = {p.name for p in _script_files()}
        unexpected = present - EXPECTED_SCRIPT_NAMES
        assert not unexpected, (
            "review-changes scripts/ carries unexpected scripts "
            f"(audit parity is {sorted(EXPECTED_SCRIPT_NAMES)}): {sorted(unexpected)}"
        )
        assert "render_review.py" not in present, (
            "render_review.py renders a parallel surface from the review-result "
            "JSON — the surface is rendered only from the sealed journal prefix"
        )
        assert "validate_review_result.py" not in present, (
            "validate_review_result.py is the removed parallel validation script "
            "— validity is the journal_emit finding-reported per-finding parse, "
            "matching the audit kind"
        )

    def test_no_render_templates_directory(self) -> None:
        render_dir = REVIEW_PROMPT_PATH.parent / "render"
        assert not render_dir.exists(), (
            f"{render_dir} holds render templates for the removed parallel "
            "renderer — the surface comes from the shared journal projection"
        )


class TestPromptTeachesRuleCitation:
    """The review prompt instructs the model to populate ``Finding.rule`` as a citation.

    The ``journal_emit finding-reported`` parse enforces structural form; the
    prompt enforces the semantic that ``rule`` cites an existing rule in the
    spec-tree or skill ecosystem. The prompt must contain a Rule citation
    section that names the accepted path forms and forbids text/action/
    location populations.
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

    def test_prompt_requires_rule_citations_from_loaded_repo_context(self) -> None:
        prompt_source = REVIEW_PROMPT_PATH.read_text(encoding="utf-8")
        required_phrases = (
            "Locate and read the cited text in a file that exists in the "
            "repository under review",
            "loaded skill file that governs that repository",
            "Treat rules recalled from system prompts, user/global instructions "
            "outside the repository, prior sessions, or training as invalid "
            "review citations",
            "Drop the finding when the candidate rule cannot be located",
            "comment length or docstring length",
        )
        for phrase in required_phrases:
            assert phrase in prompt_source, (
                "review-prompt.md must require standards findings to cite "
                f"loaded repository-governed rule text; missing {phrase!r}"
            )
