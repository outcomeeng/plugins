"""Synthetic repositories and source sets for static import-index evidence.

The harness writes real files into a temporary repository — a
test-infrastructure package, executed tests under spec nodes, a conftest —
and returns the repository-relative paths it wrote. For generated import
chains it composes the same layout as in-memory source text, so the property
exercises transitive closure over parsed import edges without filesystem
wiring per generated case. The linked test builds the index and owns every
predicate over it.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from hypothesis import given, seed, settings

from outcomeeng import validation as validation_pkg
from outcomeeng.validation.infrastructure_index import (
    CONFTEST_FILENAME,
    PACKAGE_INIT_FILENAME,
    PYTHON_SUFFIX,
    SPEC_TREE_ROOT,
    TEST_INFRASTRUCTURE_PACKAGE,
    TESTS_DIRECTORY_NAME,
    InfrastructureIndex,
    InfrastructureReach,
    index_test_infrastructure,
)
from outcomeeng_testing.generators.infrastructure_index import import_chains
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

HARNESSES_SUBPACKAGE: Final = "harnesses"
GENERATORS_SUBPACKAGE: Final = "generators"
FIXTURES_DIRECTORY: Final = "fixtures"
FIRST_NODE: Final = f"{SPEC_TREE_ROOT}/21-first.enabler"
SECOND_NODE: Final = f"{SPEC_TREE_ROOT}/32-second.enabler"
SIDE_EFFECT_MARKER_NAME: Final = "imported.marker"


@dataclass(frozen=True)
class SyntheticRepository:
    """A temporary repository holding a test-infrastructure package and tests."""

    root: Path
    package: str

    def write_module(self, module: str, source: str) -> str:
        """Write a module under the package; return its repository-relative path."""

        relative = Path(*module.split(".")).with_suffix(PYTHON_SUFFIX)
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        for ancestor in relative.parents:
            if ancestor == Path():
                continue
            init = self.root / ancestor / PACKAGE_INIT_FILENAME
            if not init.exists():
                init.write_text("", encoding="utf-8")
        target.write_text(source, encoding="utf-8")
        return relative.as_posix()

    def write_test(self, node: str, name: str, source: str) -> str:
        """Write an executed test under ``node``; return its repository-relative path."""

        relative = executed_test_path(node, name)
        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source, encoding="utf-8")
        return relative

    def write_conftest(self, source: str) -> str:
        """Write the repository-root conftest; return its repository-relative path."""

        (self.root / CONFTEST_FILENAME).write_text(source, encoding="utf-8")
        return CONFTEST_FILENAME

    def write_artifact(self, relative: str, content: str) -> str:
        """Write a non-Python artifact; return its repository-relative path."""

        target = self.root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return relative

    def index(self) -> InfrastructureIndex:
        """Build the static import index over the repository."""

        return index_test_infrastructure(self.root, package=self.package)


def executed_test_path(node: str, name: str) -> str:
    """Return the repository-relative path of executed test ``name`` under ``node``."""

    return (
        Path(node) / TESTS_DIRECTORY_NAME / f"test_{name}.scenario.l1.py"
    ).as_posix()


@contextmanager
def synthetic_repository(
    package: str = TEST_INFRASTRUCTURE_PACKAGE,
) -> Iterator[SyntheticRepository]:
    """Yield a temporary repository whose package root exists and is empty."""

    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / package).mkdir()
        (root / package / PACKAGE_INIT_FILENAME).write_text("", encoding="utf-8")
        yield SyntheticRepository(root=root, package=package)


@dataclass(frozen=True)
class ReachLayout:
    """One changed path and the executed tests the layout wrote to reach it."""

    changed_path: str
    tests: tuple[str, ...]
    index: InfrastructureIndex


def reach_layout(kind: InfrastructureReach, repo: SyntheticRepository) -> ReachLayout:
    """Write the layout that gives one changed path the reach ``kind``."""

    harness = f"{repo.package}.{HARNESSES_SUBPACKAGE}.{kind.name.lower()}"
    import_line = (
        f"from {repo.package}.{HARNESSES_SUBPACKAGE} import {kind.name.lower()}\n"
    )
    tests: tuple[str, ...]
    if kind is InfrastructureReach.NODE_LOCAL:
        changed = repo.write_module(harness, "")
        tests = (
            repo.write_test(FIRST_NODE, "one", import_line),
            repo.write_test(FIRST_NODE, "two", import_line),
        )
    elif kind is InfrastructureReach.SHARED:
        changed = repo.write_module(harness, "")
        tests = (
            repo.write_test(FIRST_NODE, "one", import_line),
            repo.write_test(SECOND_NODE, "other", import_line),
        )
    elif kind is InfrastructureReach.UNTRACEABLE:
        changed = repo.write_artifact(
            f"{repo.package}/{FIXTURES_DIRECTORY}/sample.json", "{}\n"
        )
        tests = ()
    else:
        changed = repo.write_module(harness, "")
        other = f"{repo.package}.{HARNESSES_SUBPACKAGE}.other"
        repo.write_module(other, "")
        repo.write_test(FIRST_NODE, "one", f"import {other}\n")
        tests = ()
    return ReachLayout(changed_path=changed, tests=tests, index=repo.index())


def conftest_reach_layout(repo: SyntheticRepository) -> ReachLayout:
    """Write a module reached by one node's test and by the root conftest."""

    harness = f"{repo.package}.{HARNESSES_SUBPACKAGE}.discovery"
    import_line = f"from {repo.package}.{HARNESSES_SUBPACKAGE} import discovery\n"
    changed = repo.write_module(harness, "")
    tests = (repo.write_test(FIRST_NODE, "one", import_line),)
    repo.write_conftest(import_line)
    return ReachLayout(changed_path=changed, tests=tests, index=repo.index())


@dataclass(frozen=True)
class TransitiveLayout:
    """A generator reached only through a harness that imports it."""

    generator: str
    harness: str
    test: str
    index: InfrastructureIndex


def transitive_layout(repo: SyntheticRepository) -> TransitiveLayout:
    """Write generator <- harness <- test and index the result."""

    generator = f"{repo.package}.{GENERATORS_SUBPACKAGE}.domain"
    harness = f"{repo.package}.{HARNESSES_SUBPACKAGE}.driver"
    repo.write_module(generator, "")
    repo.write_module(
        harness, f"from {repo.package}.{GENERATORS_SUBPACKAGE} import domain\n"
    )
    test = repo.write_test(
        FIRST_NODE,
        "driver",
        f"from {repo.package}.{HARNESSES_SUBPACKAGE} import driver\n",
    )
    return TransitiveLayout(
        generator=generator, harness=harness, test=test, index=repo.index()
    )


@dataclass(frozen=True)
class SideEffectLayout:
    """A module whose import writes a marker file, and a test importing it."""

    module: str
    marker: Path
    test: str


def side_effect_layout(repo: SyntheticRepository) -> SideEffectLayout:
    """Write a module that records its own import; return where it would record."""

    module = f"{repo.package}.{HARNESSES_SUBPACKAGE}.effectful"
    marker = repo.root / SIDE_EFFECT_MARKER_NAME
    repo.write_module(
        module,
        "from pathlib import Path\n"
        f"Path({str(marker)!r}).write_text('imported', encoding='utf-8')\n",
    )
    test = repo.write_test(
        FIRST_NODE,
        "effectful",
        f"from {repo.package}.{HARNESSES_SUBPACKAGE} import effectful\n",
    )
    return SideEffectLayout(module=module, marker=marker, test=test)


INDEX_PROPERTY_SEED: Final = 20260830
INDEX_PROPERTY_REPLAY_PATH: Final = (
    "spx/15-validation.enabler/65-gate.enabler/21-selected-gate.enabler/tests/"
    "test_infrastructure_index.property.l1.py::"
    "test_every_module_in_an_import_chain_reaches_the_test"
)
INDEX_PROPERTY_EXAMPLES: Final = 40


@dataclass(frozen=True)
class ChainSources:
    """An import chain as in-memory source text, and the test importing its first module."""

    package: str
    modules: tuple[str, ...]
    test: str
    module_sources: Mapping[str, str]
    test_sources: Mapping[str, str]


def chain_sources(
    chain: tuple[str, ...], package: str = TEST_INFRASTRUCTURE_PACKAGE
) -> ChainSources:
    """Compose modules where each imports the next and a test importing the first."""

    harnesses = f"{package}.{HARNESSES_SUBPACKAGE}"
    modules = tuple(f"{harnesses}.{name}" for name in chain)
    module_sources = {package: "", harnesses: ""}
    for position, module in enumerate(modules):
        following = chain[position + 1 :]
        module_sources[module] = (
            f"from {harnesses} import {following[0]}\n" if following else ""
        )
    test = executed_test_path(FIRST_NODE, "chain")
    return ChainSources(
        package=package,
        modules=modules,
        test=test,
        module_sources=module_sources,
        test_sources={test: f"from {harnesses} import {chain[0]}\n"},
    )


def index_property(test_func: Callable[..., None]) -> Callable[[], None]:
    """Bind the chain domain and run configuration to a property test."""

    configured = seed(INDEX_PROPERTY_SEED)(
        settings(max_examples=INDEX_PROPERTY_EXAMPLES, deadline=None, print_blob=True)(
            given(chain=import_chains())(test_func)
        )
    )

    def wrapper() -> None:
        run_replayable_property(
            configured,
            seed_value=INDEX_PROPERTY_SEED,
            replay_path=INDEX_PROPERTY_REPLAY_PATH,
        )

    return wrapper


@dataclass(frozen=True)
class MixedLayout:
    """A node-local module beside a changed test that does not import it."""

    changed_path: str
    reached_tests: tuple[str, ...]
    changed_test: str
    index: InfrastructureIndex


def mixed_reach_layout(repo: SyntheticRepository) -> MixedLayout:
    """Write a node-local harness, its importing tests, and one unrelated test."""

    harness = f"{repo.package}.{HARNESSES_SUBPACKAGE}.local"
    import_line = f"from {repo.package}.{HARNESSES_SUBPACKAGE} import local\n"
    changed = repo.write_module(harness, "")
    reached = (repo.write_test(FIRST_NODE, "one", import_line),)
    unrelated = repo.write_test(FIRST_NODE, "unrelated", "")
    return MixedLayout(
        changed_path=changed,
        reached_tests=reached,
        changed_test=unrelated,
        index=repo.index(),
    )


REPOSITORY_ROOT: Final = Path(validation_pkg.__file__).resolve().parents[2]


@dataclass(frozen=True)
class RepositoryReach:
    """A real repository module's path beside the index built over the checkout."""

    path: str
    index: InfrastructureIndex


def repository_reach(module_file: str) -> RepositoryReach:
    """Index this checkout and return the repository-relative path of ``module_file``."""

    path = Path(module_file).resolve().relative_to(REPOSITORY_ROOT).as_posix()
    return RepositoryReach(path=path, index=index_test_infrastructure(REPOSITORY_ROOT))
