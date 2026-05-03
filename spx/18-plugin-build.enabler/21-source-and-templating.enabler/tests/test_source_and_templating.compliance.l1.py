"""Compliance tests for source-and-templating enabler.

Each test class verifies one ALWAYS/NEVER assertion from
spx/18-plugin-build.enabler/21-source-and-templating.enabler/source-and-templating.md.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_build_plugins = pytest.importorskip(
    "outcomeeng.scripts.build_plugins",
    reason="18-plugin-build.enabler is in spx/EXCLUDE pending implementation",
)

make_environment = _build_plugins.make_environment
render_text = _build_plugins.render_text

REPO_ROOT = Path(__file__).resolve().parents[4]
SRC_ROOT = REPO_ROOT / "src"
SRC_PLUGINS = SRC_ROOT / "plugins"
SRC_SHARED = SRC_ROOT / "_shared"

EXPECTED_PLUGIN_SUBDIRS = frozenset({"skills", "commands", "agents"})
SHARED_FRAGMENT_FILENAME = "fragment.md"

CUSTOM_BLOCK_START = "{!%"
CUSTOM_BLOCK_END = "%!}"
CUSTOM_VARIABLE_START = "{{!"
CUSTOM_VARIABLE_END = "!}}"

INCLUDE_FRAGMENT_BODY = "# Inlined heading\n\nFragment body text."
INCLUDE_TEMPLATE_PREFIX = "Before include."
INCLUDE_TEMPLATE_SUFFIX = "After include."

REQUIRE_SKILL_NAME = "develop:standardizing-skills"

STANDARD_BLOCK_SAMPLE = "Code example: {% if user %} renders a block."
STANDARD_VARIABLE_SAMPLE = "Variable example: {{ user.name }} interpolates."
TEMPLATING_DOC_SAMPLE = (
    "When teaching templating, code blocks may contain {% if user %} "
    "or {{ user.name }} — such content passes through unchanged."
)


class TestSourceTreeStructure:
    """ALWAYS: src/ contains src/plugins/<plugin>/{skills,commands,agents}/ and src/_shared/<scope>/<topic>/."""

    def test_src_root_exists(self) -> None:
        assert SRC_ROOT.is_dir()

    def test_src_plugins_dir_exists(self) -> None:
        assert SRC_PLUGINS.is_dir()

    def test_src_shared_dir_exists(self) -> None:
        assert SRC_SHARED.is_dir()

    def test_each_plugin_uses_canonical_subdirs_only(self) -> None:
        plugins = [p for p in SRC_PLUGINS.iterdir() if p.is_dir()]
        assert plugins, "src/plugins/ contains at least one plugin"
        for plugin_dir in plugins:
            subdirs = {
                p.name
                for p in plugin_dir.iterdir()
                if p.is_dir() and not p.name.startswith(".")
            }
            non_canonical = subdirs - EXPECTED_PLUGIN_SUBDIRS
            assert not non_canonical, (
                f"plugin {plugin_dir.name} contains non-canonical subdirs: "
                f"{sorted(non_canonical)}"
            )


class TestSharedContentShape:
    """ALWAYS: src/_shared/<scope>/<topic>/ contains a fragment.md and reference subtrees."""

    def test_at_least_one_shared_topic_exists(self) -> None:
        topics = [
            t
            for t in SRC_SHARED.rglob("*")
            if t.is_dir() and (t / SHARED_FRAGMENT_FILENAME).is_file()
        ]
        assert topics, (
            f"src/_shared/ contains at least one topic dir with {SHARED_FRAGMENT_FILENAME}"
        )

    def test_each_shared_topic_has_fragment_file(self) -> None:
        topics = [
            t
            for t in SRC_SHARED.rglob("*")
            if t.is_dir() and (t / SHARED_FRAGMENT_FILENAME).is_file()
        ]
        for topic_dir in topics:
            fragment = topic_dir / SHARED_FRAGMENT_FILENAME
            assert fragment.is_file()
            assert fragment.read_text().strip(), (
                f"{fragment} fragment body is non-empty"
            )


class TestCustomDelimiters:
    """ALWAYS: Jinja2 environment uses custom delimiters {!% %!} and {{! !}}."""

    def test_environment_uses_custom_block_start(self) -> None:
        env = make_environment()
        assert env.block_start_string == CUSTOM_BLOCK_START

    def test_environment_uses_custom_block_end(self) -> None:
        env = make_environment()
        assert env.block_end_string == CUSTOM_BLOCK_END

    def test_environment_uses_custom_variable_start(self) -> None:
        env = make_environment()
        assert env.variable_start_string == CUSTOM_VARIABLE_START

    def test_environment_uses_custom_variable_end(self) -> None:
        env = make_environment()
        assert env.variable_end_string == CUSTOM_VARIABLE_END


class TestIncludeDirective:
    """ALWAYS: {!% include 'path/to/file.md' %!} inlines the named file's body verbatim."""

    def test_include_inlines_fragment_body(self, tmp_path: Path) -> None:
        topic_dir = tmp_path / "test-topic"
        topic_dir.mkdir()
        fragment = topic_dir / SHARED_FRAGMENT_FILENAME
        fragment.write_text(INCLUDE_FRAGMENT_BODY)

        template = (
            f"{INCLUDE_TEMPLATE_PREFIX}\n\n"
            f"{CUSTOM_BLOCK_START} include 'test-topic/fragment.md' {CUSTOM_BLOCK_END}\n\n"
            f"{INCLUDE_TEMPLATE_SUFFIX}"
        )

        rendered = render_text(template, shared_root=tmp_path)

        assert INCLUDE_FRAGMENT_BODY in rendered
        assert INCLUDE_TEMPLATE_PREFIX in rendered
        assert INCLUDE_TEMPLATE_SUFFIX in rendered


class TestRequireSkillDirective:
    """ALWAYS: {!% require_skill 'plugin:skill' %!} expands to agent-runtime-neutral invocation text."""

    def test_require_skill_expansion_names_the_skill(self, tmp_path: Path) -> None:
        template = (
            f"{CUSTOM_BLOCK_START} require_skill '{REQUIRE_SKILL_NAME}' "
            f"{CUSTOM_BLOCK_END}"
        )
        rendered = render_text(template, shared_root=tmp_path)
        assert REQUIRE_SKILL_NAME in rendered

    def test_require_skill_expansion_replaces_directive(self, tmp_path: Path) -> None:
        template = (
            f"{CUSTOM_BLOCK_START} require_skill '{REQUIRE_SKILL_NAME}' "
            f"{CUSTOM_BLOCK_END}"
        )
        rendered = render_text(template, shared_root=tmp_path)
        assert CUSTOM_BLOCK_START not in rendered
        assert CUSTOM_BLOCK_END not in rendered

    def test_require_skill_expansion_directs_invocation(self, tmp_path: Path) -> None:
        template = (
            f"{CUSTOM_BLOCK_START} require_skill '{REQUIRE_SKILL_NAME}' "
            f"{CUSTOM_BLOCK_END}"
        )
        rendered = render_text(template, shared_root=tmp_path)
        assert "invoke" in rendered.lower()


class TestStandardJinjaPassthrough:
    """NEVER: standard Jinja2 delimiters {% %} or {{ }} in source content trigger template parsing."""

    def test_standard_block_delimiters_pass_through(self, tmp_path: Path) -> None:
        rendered = render_text(STANDARD_BLOCK_SAMPLE, shared_root=tmp_path)
        assert rendered == STANDARD_BLOCK_SAMPLE

    def test_standard_variable_delimiters_pass_through(self, tmp_path: Path) -> None:
        rendered = render_text(STANDARD_VARIABLE_SAMPLE, shared_root=tmp_path)
        assert rendered == STANDARD_VARIABLE_SAMPLE

    def test_documentation_sample_with_standard_syntax_unchanged(
        self, tmp_path: Path
    ) -> None:
        rendered = render_text(TEMPLATING_DOC_SAMPLE, shared_root=tmp_path)
        assert rendered == TEMPLATING_DOC_SAMPLE
