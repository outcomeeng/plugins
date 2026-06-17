"""Plugin-portability compliance tests.

Covers the Compliance clauses in ``../manage-thread-store.md`` and
``../21-backend-abstraction.adr.md`` that constrain the imports and
module shape of thread-store scripts and the cross-skill rules that
keep backend selection routed through the facade:

- Every script under ``plugins/spec-tree/skills/manage-thread-store/scripts/``
  imports only the standard library and other thread-store scripts.
  No third-party packages, no ``outcomeeng_*`` modules.
- No verification skill (any plugin under ``plugins/spec-tree/skills/`` other
  than ``manage-thread-store`` itself, plus future language-verification skills)
  imports a concrete backend module directly. Verification skill code reaches
  persistence only through the ``thread_store`` facade.
- No backend module redefines the ``branch_slug`` function. Slug
  derivation lives in the canonical helper and is re-exported, never
  re-implemented.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys


# parents[5] = repo root (this file lives 5 levels deep: spx/21-spec-tree.enabler/
# 16-verification.enabler/21-thread-store.enabler/tests/<file>).
# Tree surgery that changes the enabler's depth must update this index.
REPO_ROOT = pathlib.Path(__file__).resolve().parents[5]
THREAD_STORE_SCRIPTS_DIR = (
    REPO_ROOT / "src" / "plugins" / "spec-tree" / "skills" / "manage-thread-store" / "scripts"
)
SPEC_TREE_SKILLS_DIR = REPO_ROOT / "src" / "plugins" / "spec-tree" / "skills"
SPEC_TREE_AGENTS_DIR = REPO_ROOT / "src" / "plugins" / "spec-tree" / "agents"

# Names of modules that ship alongside ``thread_store.py`` and are
# imported by sibling scripts via bare names (sys.path[0] resolution).
LOCAL_THREAD_STORE_MODULES = frozenset(
    {
        "thread_store",
        "backend",
        "fs_backend",
        "branch_slug",
        "errors",
    }
)

# Concrete backend module names a verification skill MUST NOT import directly. The
# facade dispatches; the verification skill never names a backend.
CONCRETE_BACKEND_MODULES = frozenset({"fs_backend"})


def _iter_script_files(directory: pathlib.Path) -> list[pathlib.Path]:
    """Return every ``.py`` file under ``directory``, excluding ``__pycache__``."""
    if not directory.is_dir():
        return []
    return [p for p in sorted(directory.rglob("*.py")) if "__pycache__" not in p.parts]


def _top_level_name(module: str) -> str:
    """Return the top-level package portion of an import name."""
    return module.split(".", 1)[0]


def _imported_modules(source: str) -> list[str]:
    """Return the top-level module names imported by ``source``.

    Walks every ``ast.Import`` and ``ast.ImportFrom`` node and returns
    the top-level module portion. Relative imports (``from . import``)
    are returned as the empty string and filtered out by callers.
    """
    tree = ast.parse(source)
    modules: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.append(_top_level_name(alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.level > 0:
                # Relative import — local to the package.
                continue
            if node.module is None:
                continue
            modules.append(_top_level_name(node.module))
    return modules


class TestThreadStoreScriptsImportOnlyStdlib:
    """Every thread-store script imports only stdlib + sibling modules."""

    def test_no_third_party_or_outcomeeng_imports(self) -> None:
        violations: list[str] = []
        stdlib = set(sys.stdlib_module_names)
        for script in _iter_script_files(THREAD_STORE_SCRIPTS_DIR):
            source = script.read_text(encoding="utf-8")
            for module in _imported_modules(source):
                if module in stdlib:
                    continue
                if module in LOCAL_THREAD_STORE_MODULES:
                    continue
                violations.append(f"{script.relative_to(REPO_ROOT)}: import '{module}'")
        assert not violations, (
            "thread-store scripts import non-stdlib, non-local modules:\n"
            + "\n".join(violations)
        )

    def test_no_outcomeeng_imports(self) -> None:
        violations: list[str] = []
        for script in _iter_script_files(THREAD_STORE_SCRIPTS_DIR):
            source = script.read_text(encoding="utf-8")
            for module in _imported_modules(source):
                if module.startswith("outcomeeng_") or module == "outcomeeng":
                    violations.append(
                        f"{script.relative_to(REPO_ROOT)}: import '{module}'"
                    )
        assert not violations, (
            "thread-store scripts import outcomeeng_* modules (forbidden by "
            "Plugin Portability Constraints):\n" + "\n".join(violations)
        )


class TestVerificationSkillsDoNotImportBackendsDirectly:
    """Every verification skill under ``plugins/spec-tree/skills/`` (other than
    thread-store itself) reaches persistence through the
    ``thread_store`` facade, never by importing ``fs_backend`` (or any
    other concrete backend module) directly.

    The current marketplace has no verification skills yet — reviewing-changes
    is declared but not implemented. The test passes trivially on an
    empty input and fails the moment a verification skill adds a forbidden import.
    """

    def test_no_verification_skill_imports_concrete_backend(self) -> None:
        violations: list[str] = []
        for skill_dir in sorted(SPEC_TREE_SKILLS_DIR.iterdir()):
            if not skill_dir.is_dir():
                continue
            if skill_dir.name == "manage-thread-store":
                # The thread-store skill is the implementation home for the
                # facade; its own scripts legitimately reference the
                # concrete backend modules.
                continue
            scripts_dir = skill_dir / "scripts"
            for script in _iter_script_files(scripts_dir):
                source = script.read_text(encoding="utf-8")
                for module in _imported_modules(source):
                    if module in CONCRETE_BACKEND_MODULES:
                        violations.append(
                            f"{script.relative_to(REPO_ROOT)}: import '{module}'"
                        )
        assert not violations, (
            "verification skills import a concrete backend module directly "
            "(forbidden — route through thread_store facade):\n" + "\n".join(violations)
        )


class TestAgentsDoNotReferenceConcreteBackends:
    """Wrapper-agent prose must not name a concrete backend module.

    Spec line 37 names "verification skill or wrapper agent" as joint subject.
    Agents are markdown files; their prose "imports" a backend by
    naming the module in instructions to the model. The check scans
    every agent file under ``plugins/spec-tree/agents/`` for the
    presence of any concrete backend module name as a whole word.

    A future ``changes-reviewer`` agent that referenced ``fs_backend``
    in its body would fail this test; the rule directs agents to reach
    persistence only through the CRUD CLIs exposed by ``manage-thread-store``.
    """

    def test_no_agent_names_concrete_backend(self) -> None:
        violations: list[str] = []
        if not SPEC_TREE_AGENTS_DIR.is_dir():
            # No agents directory yet; the rule has no input to violate.
            return
        for agent_file in sorted(SPEC_TREE_AGENTS_DIR.glob("*.md")):
            content = agent_file.read_text(encoding="utf-8")
            for module_name in CONCRETE_BACKEND_MODULES:
                # Match the module name as a whole word to avoid false
                # hits on substrings inside unrelated identifiers.
                if re.search(rf"\b{re.escape(module_name)}\b", content):
                    violations.append(
                        f"{agent_file.relative_to(REPO_ROOT)}: contains '{module_name}'"
                    )
        assert not violations, (
            "agent prose names a concrete backend module (forbidden — "
            "agents reach persistence only through thread-store CRUD CLIs):\n"
            + "\n".join(violations)
        )


class TestBackendModulesDoNotRedefineBranchSlug:
    """The slug rule lives in one function. Backend modules re-use, never re-implement."""

    def test_no_backend_module_defines_branch_slug(self) -> None:
        violations: list[str] = []
        for script in _iter_script_files(THREAD_STORE_SCRIPTS_DIR):
            # Backend modules are recognised by filename suffix.
            if not script.name.endswith("_backend.py") and script.name not in {
                "backend.py"
            }:
                continue
            source = script.read_text(encoding="utf-8")
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if (
                    isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                    and node.name == "branch_slug"
                ):
                    violations.append(
                        f"{script.relative_to(REPO_ROOT)}:{node.lineno} "
                        "defines branch_slug()"
                    )
        assert not violations, (
            "backend modules redefine branch_slug (forbidden — re-export "
            "from audit_orchestrator.py):\n" + "\n".join(violations)
        )
