"""Static import index deciding how far a test-infrastructure change reaches.

The index records which test-infrastructure modules each executed test and
each other test-infrastructure module imports, derived from ``ast`` over the
source text. It never imports or executes the modules it indexes. The planner
receives the index as a value; only the command edge builds one from a
repository root.
"""

from __future__ import annotations

import ast
from collections.abc import Collection, Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

TEST_INFRASTRUCTURE_PACKAGE: Final = "outcomeeng_testing"
SPEC_TREE_ROOT: Final = "spx"
TESTS_DIRECTORY_NAME: Final = "tests"
CONFTEST_FILENAME: Final = "conftest.py"
PACKAGE_INIT_FILENAME: Final = "__init__.py"
PYTHON_SUFFIX: Final = ".py"
EXECUTED_TEST_PREFIX: Final = "test_"


class InfrastructureReach(StrEnum):
    """How far a changed test-infrastructure path reaches into executed tests."""

    NODE_LOCAL = "node-local"
    SHARED = "shared"
    UNTRACEABLE = "untraceable"
    UNREACHED = "unreached"


@dataclass(frozen=True)
class ReachReport:
    """The reach of one changed test-infrastructure path."""

    path: str
    kind: InfrastructureReach
    tests: tuple[str, ...]
    nodes: tuple[str, ...]


@dataclass(frozen=True)
class InfrastructureIndex:
    """Import dependencies of executed tests and test-infrastructure modules.

    ``module_dependencies`` maps each test-infrastructure module to the
    test-infrastructure modules it imports. ``test_dependencies`` maps each
    executed test path to the test-infrastructure modules it imports.
    ``conftest_dependencies`` holds the modules any ``conftest.py`` imports.
    """

    package: str
    modules: frozenset[str]
    module_dependencies: Mapping[str, frozenset[str]]
    test_dependencies: Mapping[str, frozenset[str]]
    conftest_dependencies: frozenset[str]

    def module_for_path(self, path: str) -> str | None:
        """Return the module name a repository-relative path denotes, or None."""

        return module_name_for_path(path, package=self.package)

    def dependents(self, module: str) -> frozenset[str]:
        """Return ``module`` plus every test-infrastructure module reaching it."""

        closure = {module}
        frontier = [module]
        while frontier:
            current = frontier.pop()
            for candidate, dependencies in self.module_dependencies.items():
                if current in dependencies and candidate not in closure:
                    closure.add(candidate)
                    frontier.append(candidate)
        return frozenset(closure)

    def reaching_tests(self, module: str) -> tuple[str, ...]:
        """Return the executed tests that import ``module`` directly or transitively."""

        closure = self.dependents(module)
        return tuple(
            sorted(
                path
                for path, dependencies in self.test_dependencies.items()
                if dependencies & closure
            )
        )

    def reaches_conftest(self, module: str) -> bool:
        """Return whether any ``conftest.py`` imports ``module`` directly or transitively."""

        return bool(self.conftest_dependencies & self.dependents(module))

    def reach(self, path: str) -> ReachReport:
        """Classify how far a changed path under the package reaches."""

        module = self.module_for_path(path)
        if module is None:
            return ReachReport(
                path=path, kind=InfrastructureReach.UNTRACEABLE, tests=(), nodes=()
            )
        tests = self.reaching_tests(module)
        nodes = tuple(sorted({node_for_test_path(test) for test in tests}))
        if self.reaches_conftest(module) or len(nodes) > 1:
            kind = InfrastructureReach.SHARED
        elif tests:
            kind = InfrastructureReach.NODE_LOCAL
        else:
            kind = InfrastructureReach.UNREACHED
        return ReachReport(path=path, kind=kind, tests=tests, nodes=nodes)


def module_name_for_path(path: str, *, package: str) -> str | None:
    """Return the dotted module name for a Python path under ``package``."""

    if path != package and not path.startswith(f"{package}/"):
        return None
    if not path.endswith(PYTHON_SUFFIX):
        return None
    parts = path[: -len(PYTHON_SUFFIX)].split("/")
    if parts[-1] == PACKAGE_INIT_FILENAME[: -len(PYTHON_SUFFIX)]:
        parts = parts[:-1]
    return ".".join(parts)


def node_for_test_path(path: str) -> str:
    """Return the spec node directory that owns an executed test path."""

    return path.rsplit(f"/{TESTS_DIRECTORY_NAME}/", 1)[0]


def importing_package_for_module(module: str, *, modules: Collection[str]) -> str:
    """Return the package that relative imports in ``module`` resolve against."""

    if module in modules and module_is_package(module, modules=modules):
        return module
    return module.rsplit(".", 1)[0] if "." in module else module


def module_is_package(module: str, *, modules: Collection[str]) -> bool:
    """Return whether ``module`` has submodules in ``modules``."""

    prefix = f"{module}."
    return any(candidate.startswith(prefix) for candidate in modules)


def import_dependencies(
    source: str,
    *,
    importing_package: str | None,
    package: str,
    modules: Collection[str],
) -> frozenset[str]:
    """Return the test-infrastructure modules ``source`` imports.

    Every import records the named module and every package on its dotted
    path inside ``package``. A ``from`` import also records the imported name
    as a submodule when ``modules`` contains it. Relative imports resolve
    against ``importing_package``; a source outside the package passes
    ``None`` and its relative imports record nothing.
    """

    dependencies: set[str] = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            for alias in node.names:
                dependencies.update(_within_package(alias.name, package=package))
        elif isinstance(node, ast.ImportFrom):
            base = _resolve_import_from_base(node, importing_package=importing_package)
            if base is None:
                continue
            dependencies.update(_within_package(base, package=package))
            for alias in node.names:
                candidate = f"{base}.{alias.name}"
                if candidate in modules:
                    dependencies.update(_within_package(candidate, package=package))
    return frozenset(dependencies)


def index_test_infrastructure(
    repo: Path,
    *,
    package: str = TEST_INFRASTRUCTURE_PACKAGE,
    spec_root: str = SPEC_TREE_ROOT,
) -> InfrastructureIndex:
    """Build the index from the repository's source text without importing it."""

    package_root = repo / package
    modules = frozenset(
        _module_name(path.relative_to(repo).as_posix(), package=package)
        for path in _python_files(package_root)
    )
    module_dependencies: dict[str, frozenset[str]] = {}
    for path in _python_files(package_root):
        module = _module_name(path.relative_to(repo).as_posix(), package=package)
        module_dependencies[module] = import_dependencies(
            path.read_text(encoding="utf-8"),
            importing_package=importing_package_for_module(module, modules=modules),
            package=package,
            modules=modules,
        )
    test_dependencies: dict[str, frozenset[str]] = {}
    conftest_dependencies: set[str] = set()
    for path in _executed_test_files(repo / spec_root):
        test_dependencies[path.relative_to(repo).as_posix()] = import_dependencies(
            path.read_text(encoding="utf-8"),
            importing_package=None,
            package=package,
            modules=modules,
        )
    for path in _conftest_files(repo, spec_root=spec_root):
        conftest_dependencies.update(
            import_dependencies(
                path.read_text(encoding="utf-8"),
                importing_package=None,
                package=package,
                modules=modules,
            )
        )
    return InfrastructureIndex(
        package=package,
        modules=modules,
        module_dependencies=module_dependencies,
        test_dependencies=test_dependencies,
        conftest_dependencies=frozenset(conftest_dependencies),
    )


def _module_name(path: str, *, package: str) -> str:
    module = module_name_for_path(path, package=package)
    if module is None:
        raise ValueError(f"{path} is not a Python module under {package}")
    return module


def _within_package(module: str, *, package: str) -> tuple[str, ...]:
    if module != package and not module.startswith(f"{package}."):
        return ()
    parts = module.split(".")
    return tuple(".".join(parts[: index + 1]) for index in range(len(parts)))


def _resolve_import_from_base(
    node: ast.ImportFrom, *, importing_package: str | None
) -> str | None:
    if node.level == 0:
        return node.module
    if importing_package is None:
        return None
    base_parts = importing_package.split(".")
    ascend = node.level - 1
    if ascend >= len(base_parts):
        return None
    base_parts = base_parts[: len(base_parts) - ascend] if ascend else base_parts
    if node.module:
        base_parts = [*base_parts, *node.module.split(".")]
    return ".".join(base_parts)


def _python_files(root: Path) -> Iterator[Path]:
    if not root.is_dir():
        return
    yield from sorted(root.rglob(f"*{PYTHON_SUFFIX}"))


def _executed_test_files(root: Path) -> Iterator[Path]:
    if not root.is_dir():
        return
    for path in sorted(root.rglob(f"{EXECUTED_TEST_PREFIX}*{PYTHON_SUFFIX}")):
        if path.parent.name == TESTS_DIRECTORY_NAME:
            yield path


def _conftest_files(repo: Path, *, spec_root: str) -> Iterator[Path]:
    root_conftest = repo / CONFTEST_FILENAME
    if root_conftest.is_file():
        yield root_conftest
    spec_dir = repo / spec_root
    if spec_dir.is_dir():
        yield from sorted(spec_dir.rglob(CONFTEST_FILENAME))
