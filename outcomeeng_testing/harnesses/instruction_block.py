"""Test harness for the instruction-block render module.

Exposes resource and execution infrastructure for generated cases:

- An importlib loader for ``instruction_block.py``. The module ships under a
  generated plugin skill directory and is not importable by package
  name; tests load it through ``importlib`` instead.
- Generator-owned templates and protocol cases derived from the production module and
  canonical template, plus harness-accessed inert whole-document fixtures for root bodies,
  shared-region examples, and line-boundary examples.
- ``canonical_router_spacing_observations``. Renders the canonical template for every
  source-owned harness and every subset of its declared languages, returning each rendering
  beside the marker that opens it; the typed mapping file reads the marker-to-body spacing off
  that rendering and owns what the spacing must be.
- ``canonical_language_presence_observations``. Renders every declared language subset beside
  the template text the source-owned presence markers wrap, so the typed mapping file judges
  whether that section belongs in a render without restating its heading.
- ``for_all_unsupported_language_overrides``. Searches unsupported language tokens with
  replayable property-run settings and passes each observation to the typed property's invariant.

Pure render and parse checks use document strings. CLI-edge checks materialize
only invocation-owned temporary repositories and clean them on exit.
"""

from __future__ import annotations

import importlib.util
import io
import itertools
import os
import pathlib
import subprocess
from collections.abc import Callable
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
import sys
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Final, cast

from hypothesis import given, seed, settings

from outcomeeng.distribution import instruction_block as distribution
from outcomeeng_testing.generators.instruction_block import (
    BootstrapThresholdRelation,
    DelegationCandidateCase,
    InstructionBlockCases,
    build_macro as generate_build_macro,
    build_template as generate_template,
    adopted_body_heading as generate_adopted_body_heading,
    delegating_root_body as generate_delegating_root_body,
    delegation_candidate_cases as generate_delegation_candidate_cases,
    harness_line as generate_harness_line,
    instruction_block_cases,
    unsupported_language_tokens,
)
from outcomeeng_testing.harnesses.property_evidence import run_replayable_property

REPO_ROOT: Final = pathlib.Path(__file__).resolve().parents[2]
INSTRUCTION_BLOCK_MODULE_PATH = distribution.GENERATOR_PATH
FIXTURES_DIR: Final = REPO_ROOT / "outcomeeng_testing/fixtures/instruction_block"

INSTRUCTION_BLOCK_PROPERTY_EXAMPLES: Final = 50
INSTRUCTION_BLOCK_PROPERTY_SEED: Final = 20260714
INSTRUCTION_BLOCK_PROPERTY_REPLAY_PATH: Final = (
    "just test spx/21-spec-tree.enabler/43-instruction-block.enabler/tests/"
    "test_instruction_block.property.l1.py"
)
LANGUAGE_OVERRIDE_PROPERTY_REPLAY_PATH: Final = (
    "just test spx/21-spec-tree.enabler/43-instruction-block.enabler/tests/"
    "test_language_override.property.l1.py"
)


def run_instruction_block_property(
    assertion: Callable[[], None],
    *,
    replay_path: str = INSTRUCTION_BLOCK_PROPERTY_REPLAY_PATH,
) -> None:
    """Run a generated property with harness-owned settings and replay diagnostics."""
    configured_assertion = seed(INSTRUCTION_BLOCK_PROPERTY_SEED)(
        settings(
            max_examples=INSTRUCTION_BLOCK_PROPERTY_EXAMPLES,
            deadline=None,
            print_blob=True,
        )(assertion)
    )
    run_replayable_property(
        configured_assertion,
        seed_value=INSTRUCTION_BLOCK_PROPERTY_SEED,
        replay_path=replay_path,
    )


def _fixture_text(name: str) -> str:
    """Read one inert whole-document instruction-block fixture."""
    return FIXTURES_DIR.joinpath(name).read_text(encoding="utf-8")


@dataclass(frozen=True)
class RootInstructionTopology:
    """Root instruction files and symlinks a consumer repository may already contain."""

    files: dict[str, str]
    symlinks: dict[str, str]


@dataclass(frozen=True)
class EvidenceRun:
    """Declared and successfully executed checks for one typed evidence file."""

    declared: tuple[str, ...]
    executed: tuple[str, ...]


@dataclass(frozen=True)
class BootstrapOutcome:
    """The seed bodies and both written root documents observed after one bootstrap write.

    ``seeds`` carries an entry only for a root instruction file the topology placed, so a
    one-file topology reports one seed and the linked test reads which side the generator
    created for itself. ``repo`` exposes the written paths, so the test can observe file kind
    as well as content.
    """

    seeds: dict[str, str]
    claude: str
    agents: str
    repo: pathlib.Path


@dataclass(frozen=True)
class RouterSpacingObservation:
    """One source-owned harness/language rendering observed by mapping evidence.

    The observation carries the opening marker the case is identified by and the rendered
    block. It carries no expected spacing: how many blank lines separate the two is the
    assertion's own claim, and recomposing it here from the separator ``render`` used would
    move the expectation whenever the separator did.
    """

    marker: str
    rendered: str


@dataclass(frozen=True)
class LanguageOverrideObservation:
    """One generated unsupported-language CLI result observed by property evidence."""

    token: str
    supported_languages: tuple[str, ...]
    returncode: int
    stderr: str


def root_instruction_topology_only_claude() -> RootInstructionTopology:
    """Return a root topology with only the Claude harness instruction file present."""
    cases = generated_cases()
    return RootInstructionTopology(
        files={cases.instruction_claude: ROOT_CLAUDE_BODY}, symlinks={}
    )


def root_instruction_topology_only_agents() -> RootInstructionTopology:
    """Return a root topology with only the Codex harness instruction file present."""
    cases = generated_cases()
    return RootInstructionTopology(
        files={cases.instruction_agents: ROOT_AGENTS_BODY}, symlinks={}
    )


def root_instruction_topology_delegating() -> RootInstructionTopology:
    """Return a root topology whose Claude file only points at the content-bearing Codex file."""
    cases = generated_cases()
    return RootInstructionTopology(
        files={
            cases.instruction_claude: generate_delegating_root_body(
                cases.instruction_agents,
                generate_adopted_body_heading(ROOT_AGENTS_BODY),
            ),
            cases.instruction_agents: ROOT_AGENTS_BODY,
        },
        symlinks={},
    )


def root_instruction_topology_reverse_delegating() -> RootInstructionTopology:
    """Return a root topology whose Codex file only points at the content-bearing Claude file.

    The mirror of ``root_instruction_topology_delegating``. Adoption is direction-agnostic, so the
    two directions are separate members of the topology domain rather than one member observed
    twice.
    """
    cases = generated_cases()
    return RootInstructionTopology(
        files={
            cases.instruction_claude: ROOT_CLAUDE_BODY,
            cases.instruction_agents: generate_delegating_root_body(
                cases.instruction_claude,
                generate_adopted_body_heading(ROOT_CLAUDE_BODY),
            ),
        },
        symlinks={},
    )


def root_instruction_topology_mutual_delegation() -> RootInstructionTopology:
    """Return a root topology whose two files point at each other and carry no content.

    Both stubs carry one identical heading, as two stubs for one product would: neither side has a
    content-bearing body to take a title from, so inventing a different title for each would make
    the fixture less like the situation it stands for, not more.
    """
    cases = generated_cases()
    shared_heading = generate_adopted_body_heading(ROOT_SHARED_BODY)
    return RootInstructionTopology(
        files={
            cases.instruction_claude: generate_delegating_root_body(
                cases.instruction_agents, shared_heading
            ),
            cases.instruction_agents: generate_delegating_root_body(
                cases.instruction_claude, shared_heading
            ),
        },
        symlinks={},
    )


def root_instruction_topology_separate() -> RootInstructionTopology:
    """Return a root topology with two independent harness instruction files."""
    cases = generated_cases()
    return RootInstructionTopology(
        files={
            cases.instruction_claude: ROOT_CLAUDE_BODY,
            cases.instruction_agents: ROOT_AGENTS_BODY,
        },
        symlinks={},
    )


def root_instruction_topology_symlinked() -> RootInstructionTopology:
    """Return a root topology matching a shared instruction file with a harness symlink."""
    cases = generated_cases()
    return RootInstructionTopology(
        files={cases.instruction_agents: ROOT_SHARED_BODY},
        symlinks={cases.instruction_claude: cases.instruction_agents},
    )


def root_instruction_topology_identical() -> RootInstructionTopology:
    """Return two identical regular instruction files with no managed block."""
    cases = generated_cases()
    return RootInstructionTopology(
        files={
            cases.instruction_claude: ROOT_SHARED_BODY,
            cases.instruction_agents: ROOT_SHARED_BODY,
        },
        symlinks={},
    )


def root_instruction_topology_legacy_managed() -> RootInstructionTopology:
    """Return identical files carrying a source-derived alternate managed block."""
    cases = generated_cases()
    return RootInstructionTopology(
        files={
            cases.instruction_claude: ROOT_LEGACY_MANAGED_BODY,
            cases.instruction_agents: ROOT_LEGACY_MANAGED_BODY,
        },
        symlinks={},
    )


def root_instruction_topology_near_identical() -> RootInstructionTopology:
    """Return differing files whose source-derived common span exceeds the threshold."""
    cases = generated_cases()
    return RootInstructionTopology(
        files={
            cases.instruction_claude: ROOT_NEAR_IDENTICAL_CLAUDE,
            cases.instruction_agents: ROOT_NEAR_IDENTICAL_CODEX,
        },
        symlinks={},
    )


def _replace_path_with_text(path: pathlib.Path, body: str) -> None:
    """Write ``body`` as a regular file, replacing a symlink or file at ``path``."""
    if path.exists() or path.is_symlink():
        path.unlink()
    path.write_text(body, encoding="utf-8")


def _seed_body(
    root: pathlib.Path, instruction_name: str, fallback: str | None
) -> str | None:
    """Read an instruction file's body, following symlinks, or return ``fallback`` when absent."""
    path = root / instruction_name
    if path.exists() or path.is_symlink():
        return path.read_text(encoding="utf-8")
    return fallback


def materialize_root_instruction_topology(
    root: pathlib.Path, topology: RootInstructionTopology
) -> dict[str, str]:
    """Create ``topology`` under ``root`` and normalize harness instruction files."""
    root.mkdir(parents=True, exist_ok=True)
    for name, body in topology.files.items():
        _replace_path_with_text(root / name, body)
    for name, target in topology.symlinks.items():
        link_path = root / name
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()
        link_path.symlink_to(target)

    cases = generated_cases()
    claude_seed = _seed_body(root, cases.instruction_claude, None)
    agents_seed = _seed_body(root, cases.instruction_agents, claude_seed)
    if claude_seed is None:
        claude_seed = agents_seed
    if claude_seed is None or agents_seed is None:
        claude_seed = agents_seed = ""

    seeds = {
        cases.instruction_claude: claude_seed,
        cases.instruction_agents: agents_seed,
    }
    for name, body in seeds.items():
        _replace_path_with_text(root / name, body)
    return seeds


def materialize_declared_root_topology(
    root: pathlib.Path, topology: RootInstructionTopology
) -> dict[str, str]:
    """Create ``topology`` under ``root`` exactly as declared and return the bodies placed.

    A root instruction file the topology omits stays absent, and a symlink stays a symlink, so
    the generator meets the topology the case names instead of a pair this harness already
    resolved on its behalf. The returned mapping carries an entry only for a file the topology
    placed; a symlinked entry carries the body reachable through the link.
    """
    root.mkdir(parents=True, exist_ok=True)
    for name, body in topology.files.items():
        _replace_path_with_text(root / name, body)
    for name, target in topology.symlinks.items():
        link_path = root / name
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()
        link_path.symlink_to(target)

    cases = generated_cases()
    placed: dict[str, str] = {}
    for instruction_name in (cases.instruction_claude, cases.instruction_agents):
        placed_body = _seed_body(root, instruction_name, None)
        if placed_body is not None:
            placed[instruction_name] = placed_body
    return placed


def symlinked_instruction_topology_materializes_as_regular_files() -> bool:
    """Check symlink normalization and source-body preservation in one owned workspace."""
    cases = generated_cases()
    with TemporaryDirectory() as directory:
        root = pathlib.Path(directory).resolve()
        materialized = materialize_root_instruction_topology(
            root, root_instruction_topology_symlinked()
        )
        claude_path = root / cases.instruction_claude
        agents_path = root / cases.instruction_agents
        return (
            claude_path.is_file()
            and agents_path.is_file()
            and not claude_path.is_symlink()
            and not agents_path.is_symlink()
            and claude_path.read_text(encoding="utf-8") == ROOT_SHARED_BODY
            and agents_path.read_text(encoding="utf-8") == ROOT_SHARED_BODY
            and materialized[cases.instruction_claude] == ROOT_SHARED_BODY
            and materialized[cases.instruction_agents] == ROOT_SHARED_BODY
        )


def root_instruction_topology_seed_mapping_is_valid() -> bool:
    """Check every source-owned root topology against its expected harness seed bodies."""
    generated = generated_cases()
    cases = (
        (
            root_instruction_topology_only_claude(),
            {
                generated.instruction_claude: ROOT_CLAUDE_BODY,
                generated.instruction_agents: ROOT_CLAUDE_BODY,
            },
        ),
        (
            root_instruction_topology_only_agents(),
            {
                generated.instruction_claude: ROOT_AGENTS_BODY,
                generated.instruction_agents: ROOT_AGENTS_BODY,
            },
        ),
        (
            root_instruction_topology_separate(),
            {
                generated.instruction_claude: ROOT_CLAUDE_BODY,
                generated.instruction_agents: ROOT_AGENTS_BODY,
            },
        ),
        (
            root_instruction_topology_symlinked(),
            {
                generated.instruction_claude: ROOT_SHARED_BODY,
                generated.instruction_agents: ROOT_SHARED_BODY,
            },
        ),
    )
    with TemporaryDirectory() as directory:
        root = pathlib.Path(directory).resolve()
        return all(
            materialize_root_instruction_topology(root / str(index), topology)
            == expected
            for index, (topology, expected) in enumerate(cases)
        )


def load_instruction_block_module() -> ModuleType:
    """Load the ``instruction_block`` module via importlib and cache it."""
    cached = sys.modules.get("instruction_block")
    if cached is not None:
        return cached
    spec = importlib.util.spec_from_file_location(
        "instruction_block", INSTRUCTION_BLOCK_MODULE_PATH
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(
            f"Cannot load instruction_block from {INSTRUCTION_BLOCK_MODULE_PATH}"
        )
    module = importlib.util.module_from_spec(spec)
    sys.modules["instruction_block"] = module
    spec.loader.exec_module(module)
    return module


def canonical_template_path(agent_harness: str | None = None) -> pathlib.Path:
    """Return one source-declared harness's rendered instruction template path."""
    harnesses = tuple(
        sorted(load_instruction_block_module().AGENT_HARNESS_INSTRUCTION_FILENAMES)
    )
    selected_harness = harnesses[0] if agent_harness is None else agent_harness
    return distribution.dist_template_path(selected_harness)


def read_canonical_template(agent_harness: str | None = None) -> str:
    """Read one rendered harness template from the generated runtime tree."""
    return canonical_template_path(agent_harness).read_text(encoding="utf-8")


def generated_cases() -> InstructionBlockCases:
    """Return source-derived carrier cases from the generator layer."""
    return instruction_block_cases(
        load_instruction_block_module(), read_canonical_template()
    )


_GENERATED_CASES = generated_cases()
INSTRUCTION_CLAUDE = _GENERATED_CASES.instruction_claude
INSTRUCTION_AGENTS = _GENERATED_CASES.instruction_agents
ROOT_CLAUDE_BODY = _fixture_text("root-claude.md")
ROOT_AGENTS_BODY = _fixture_text("root-agents.md")
ROOT_SHARED_BODY = _fixture_text("root-shared.md")
SHARED_REGION_NAME = _GENERATED_CASES.shared_region_name
SHARED_REGION_BODY = load_instruction_block_module().parse_shared_regions(
    _fixture_text("shared-region-primary.md")
)[SHARED_REGION_NAME]
SHARED_REGION_BODY_ALT = load_instruction_block_module().parse_shared_regions(
    _fixture_text("shared-region-alternate.md")
)[SHARED_REGION_NAME]
ROOT_NEAR_IDENTICAL_CLAUDE = _fixture_text("near-identical-claude.md")
ROOT_NEAR_IDENTICAL_CODEX = _fixture_text("near-identical-codex.md")
ROOT_NEAR_IDENTICAL_SHARED = _fixture_text("near-identical-shared.md")
ROOT_LEGACY_MANAGED_BODY = _fixture_text("retired-managed.md")
ROOT_STRADDLING_CLAUDE = _fixture_text("straddling-claude.md")
ROOT_STRADDLING_CODEX = _fixture_text("straddling-codex.md")
ROOT_MIDLINE_CLAUDE = _fixture_text("midline-claude.md")
ROOT_MIDLINE_CODEX = _fixture_text("midline-codex.md")
READ_ENTIRE_FILE_INSTRUCTION = _GENERATED_CASES.read_entire_file_instruction
LANG_PRIMARY = _GENERATED_CASES.lang_primary
LANG_SECONDARY = _GENERATED_CASES.lang_secondary
TEMPLATE_LANGUAGES = _GENERATED_CASES.template_languages
BASE_SECTION = _GENERATED_CASES.base_section
NEW_SECTION = _GENERATED_CASES.new_section
OLD_VERSION = _GENERATED_CASES.old_version
NEW_VERSION = _GENERATED_CASES.new_version
ILLUSTRATION_TOKEN = _GENERATED_CASES.illustration_token
BUILD_MACRO_CAPABILITY = _GENERATED_CASES.build_macro_capability
BUILD_MACRO_HARNESS = _GENERATED_CASES.build_macro_harness
HARNESS_CLAUDE = _GENERATED_CASES.harness_claude
HARNESS_CODEX = _GENERATED_CASES.harness_codex
TEMPLATE_HARNESSES = _GENERATED_CASES.template_harnesses


def property_evidence_contract() -> tuple[str, ...]:
    """Return the independent case manifest required by property evidence."""
    return (
        *(f"render-version[{agent_harness}]" for agent_harness in TEMPLATE_HARNESSES),
        "trailing-newline",
        "stale-order",
        "reconcile-identity",
        "reconcile-idempotence",
        "bootstrap-general-domain",
        *(
            f"bootstrap-threshold[{relation.value}]"
            for relation in BootstrapThresholdRelation
        ),
    )


def harness_line(harness: str) -> str:
    """Return generator-owned carrier content for one source-owned harness."""
    return generate_harness_line(harness)


def render_build_macro() -> str:
    """Return a generator-owned unresolved macro carrier."""
    return generate_build_macro(generated_cases())


def build_template(version: str, *, extra_section: bool = False) -> str:
    """Return a generator-owned template over source-declared domains."""
    return generate_template(
        load_instruction_block_module(),
        generated_cases(),
        version,
        extra_section=extra_section,
    )


def template_declared_languages(template: str) -> tuple[str, ...]:
    """Return the finite language domain declared by canonical template opening markers."""
    module = load_instruction_block_module()
    return cast(tuple[str, ...], module.template_languages(template))


def _language_subsets(languages: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    """Return every subset of a finite template-declared language domain."""
    return tuple(
        subset
        for size in range(len(languages) + 1)
        for subset in itertools.combinations(languages, size)
    )


def template_language_subsets() -> tuple[tuple[str, ...], ...]:
    """Return every enabled-language subset declared by the canonical template."""
    return _language_subsets(template_declared_languages(read_canonical_template()))


def canonical_router_spacing_observations() -> tuple[RouterSpacingObservation, ...]:
    """Observe canonical spacing for every source harness and language subset."""
    module = load_instruction_block_module()
    languages = template_declared_languages(read_canonical_template())
    observations: list[RouterSpacingObservation] = []

    for agent_harness in sorted(module.AGENT_HARNESS_INSTRUCTION_FILENAMES):
        template = read_canonical_template(agent_harness)
        version = module.parse_template_version(template)
        for enabled_languages in _language_subsets(languages):
            rendered = module.render(
                template,
                enabled_languages,
                version,
                agent_harness,
            )
            observations.append(
                RouterSpacingObservation(
                    marker=module.router_marker(version, enabled_languages),
                    rendered=rendered,
                )
            )
    return tuple(observations)


@dataclass(frozen=True)
class LanguagePresenceObservation:
    """One enabled-language subset, its rendered block, and every presence-gated section text.

    ``gated_sections`` is read out of the canonical template between the source-owned presence
    markers, so the linked test compares the render against the template's own text rather than
    against a heading restated in the test. Every gated span is carried, not the first, so the
    assertion's general wording is judged against each instance the template gates.
    """

    languages: tuple[str, ...]
    rendered: str
    gated_sections: tuple[str, ...]


def presence_gated_template_sections(agent_harness: str) -> tuple[str, ...]:
    """Return presence-gated spans that apply to one source-owned harness."""
    module = load_instruction_block_module()
    opening = (
        f"<!-- {module.LANGUAGE_PRESENCE_MARKER}:{module.LANGUAGE_PRESENCE_NAME} -->"
    )
    closing = (
        f"<!-- /{module.LANGUAGE_PRESENCE_MARKER}:{module.LANGUAGE_PRESENCE_NAME} -->"
    )
    template = read_canonical_template(agent_harness)
    harness_template = module.filter_harness(template, agent_harness)
    lines = harness_template.splitlines(keepends=True)
    sections: list[str] = []
    start: int | None = None
    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == opening:
            start = index
        elif stripped == closing and start is not None:
            sections.append("".join(lines[start + 1 : index]).strip())
            start = None
    return tuple(sections)


def canonical_language_presence_observations() -> tuple[
    LanguagePresenceObservation, ...
]:
    """Observe every harness and language subset beside its gated sections."""
    module = load_instruction_block_module()
    observations: list[LanguagePresenceObservation] = []
    for agent_harness in sorted(module.AGENT_HARNESS_INSTRUCTION_FILENAMES):
        template = read_canonical_template(agent_harness)
        version = module.parse_template_version(template)
        gated = presence_gated_template_sections(agent_harness)
        observations.extend(
            LanguagePresenceObservation(
                languages=subset,
                rendered=cast(
                    str, module.render(template, subset, version, agent_harness)
                ),
                gated_sections=gated,
            )
            for subset in _language_subsets(template_declared_languages(template))
        )
    return tuple(observations)


def canonical_router_spacing_declarations() -> tuple[str, ...]:
    """Return the finite source-owned case identities for router spacing."""
    languages = template_declared_languages(read_canonical_template())
    return tuple(
        f"{agent_harness}[{','.join(enabled_languages)}]"
        for agent_harness in sorted(
            load_instruction_block_module().AGENT_HARNESS_INSTRUCTION_FILENAMES
        )
        for enabled_languages in _language_subsets(languages)
    )


def for_all_unsupported_language_overrides(
    assertion: Callable[[LanguageOverrideObservation], None],
) -> None:
    """Bind generated unsupported tokens while the typed test owns the invariant."""
    module = load_instruction_block_module()
    supported_languages = template_declared_languages(read_canonical_template())

    @given(token=unsupported_language_tokens(supported_languages))
    def generated_assertion(token: str) -> None:
        stderr = io.StringIO()
        with TemporaryDirectory() as directory, redirect_stderr(stderr):
            result = run_generator_write(
                module,
                pathlib.Path(directory).resolve(),
                canonical_template_path(),
                languages=token,
            )
        assertion(
            LanguageOverrideObservation(
                token=token,
                supported_languages=supported_languages,
                returncode=result,
                stderr=stderr.getvalue(),
            )
        )

    run_instruction_block_property(
        generated_assertion,
        replay_path=LANGUAGE_OVERRIDE_PROPERTY_REPLAY_PATH,
    )


def extract_markdown_section(document: str, heading: str) -> str:
    """Return a markdown section by exact heading line, including the heading."""
    lines = document.splitlines()
    try:
        start = lines.index(heading)
    except ValueError as exc:
        raise RuntimeError(f"Heading not found: {heading}") from exc
    heading_level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for index, line in enumerate(lines[start + 1 :], start=start + 1):
        if line.startswith("#") and len(line) - len(line.lstrip("#")) <= heading_level:
            end = index
            break
    return "\n".join(lines[start:end])


def write_spx_tree_with_tests(
    spx_dir: pathlib.Path, extensions: tuple[str, ...]
) -> pathlib.Path:
    """Create an ``spx/`` tree carrying one node whose ``tests/`` holds the given extensions.

    Lets language-detection tests drive the CLI edge against a real on-disk tree: the
    detector globs ``spx/**/tests/`` and maps each test-file extension to its language.
    """
    tests_dir = spx_dir / "21-node.enabler" / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    for extension in extensions:
        (tests_dir / f"test_subject.scenario.l1.{extension}").write_text(
            "", encoding="utf-8"
        )
    return spx_dir


def write_template(
    directory: pathlib.Path, version: str, *, extra_section: bool = False
) -> pathlib.Path:
    """Write ``build_template(...)`` into ``directory`` and return the file path.

    Lets CLI-edge tests drive ``main([...])`` against a real template file under a
    pytest ``tmp_path``; the harness owns the on-disk setup.
    """
    path = directory / distribution.AUTHORED_TEMPLATE_PATH.name
    module = load_instruction_block_module()
    path.write_text(
        generate_template(
            module,
            generated_cases(),
            version,
            extra_section=extra_section,
        ),
        encoding="utf-8",
    )
    return path


def run_generator_write(
    module: ModuleType,
    repo_root: pathlib.Path,
    template_path: pathlib.Path,
    *,
    languages: str,
    adopt_harness: str | None = None,
) -> int:
    """Run the generator CLI's ``--write`` over ``repo_root`` and return its exit code.

    Centralizes the CLI-invocation setup the render-model tests share, since harness code —
    not test bodies — owns shared execution scaffolding. ``adopt_harness`` passes an operator
    answer through ``--adopt``; omitting it is the default run, which adopts no body. The
    dynamically loaded module types ``main`` as ``Any``; the CLI contract returns an exit code, so
    the result is cast to ``int``.
    """
    adopt_option = [] if adopt_harness is None else [f"--adopt={adopt_harness}"]
    return cast(
        int,
        module.main(
            [
                "--template",
                str(template_path),
                "--repo-root",
                str(repo_root),
                f"--languages={languages}",
                "--write",
                *adopt_option,
            ]
        ),
    )


def run_generator_write_primary(
    repo_root: pathlib.Path,
    template_path: pathlib.Path,
    adopt_harness: str | None = None,
) -> int:
    """Run the generator ``--write`` over ``repo_root`` with the harness's primary language.

    The render-model scenario tests share this exact run configuration — the loaded module and the
    single primary language — so it lives in the harness rather than a test-local wrapper.
    """
    cases = generated_cases()
    return run_generator_write(
        load_instruction_block_module(),
        repo_root,
        template_path,
        languages=cases.lang_primary,
        adopt_harness=adopt_harness,
    )


def run_generator_adopt_without_write(
    repo_root: pathlib.Path, template_path: pathlib.Path, adopt_harness: str
) -> tuple[int, str]:
    """Run the generator with an operator answer and no ``--write``; return exit code and stderr.

    Stdout is captured and discarded so a render that reaches it stays out of the test report.
    The harness owns the invocation; the linked test decides what the exit code and stderr mean.
    """
    cases = generated_cases()
    errors = io.StringIO()
    with redirect_stdout(io.StringIO()), redirect_stderr(errors):
        result = cast(
            int,
            load_instruction_block_module().main(
                [
                    "--template",
                    str(template_path),
                    "--repo-root",
                    str(repo_root),
                    f"--languages={cases.lang_primary}",
                    f"--adopt={adopt_harness}",
                ]
            ),
        )
    return result, errors.getvalue()


def seed_both_root_files(repo_root: pathlib.Path, body: str) -> pathlib.Path:
    """Create ``repo_root`` and write ``body`` as both root instruction files.

    The scenario tests that start from one identical seed share this setup, and temporary product
    scaffolding is the harness's to own rather than each test file's.
    """
    repo_root.mkdir(parents=True, exist_ok=True)
    for filename in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
        (repo_root / filename).write_text(body, encoding="utf-8")
    return repo_root


def retired_managed_block_tokens() -> tuple[str, ...]:
    """Return the source-owned markers and metadata prefixes a retired managed block carries."""
    module = load_instruction_block_module()
    return tuple(
        marker for pair in module.LEGACY_MANAGED_BLOCK_MARKERS for marker in pair
    ) + (
        module.MANAGED_TEMPLATE_VERSION_PREFIX,
        module.MANAGED_TEMPLATE_SOURCE_PREFIX,
        module.MANAGED_LANGUAGES_PREFIX,
    )


def delegation_candidate_cases() -> tuple[DelegationCandidateCase, ...]:
    """Return the generated candidate shapes over the source-owned Codex filename and size bound."""
    cases = generated_cases()
    module = load_instruction_block_module()
    return generate_delegation_candidate_cases(
        cases.instruction_agents,
        ROOT_AGENTS_BODY,
        module.DELEGATION_STUB_MAX_CHARACTERS,
    )


def observe_bootstrap_outcome(
    tmp_path: pathlib.Path,
    topology_factory: Callable[[], RootInstructionTopology],
    adopt_harness: str | None = None,
) -> BootstrapOutcome:
    """Materialize a root topology, run the real generator write, and read both root documents.

    Owns the temporary repository, the rendered template, and the generator invocation, and
    returns the seed bodies alongside the two written documents. It applies no predicate — the
    linked test decides what the observed documents mean.

    The topology reaches the generator exactly as declared, so an absent side and a symlinked
    side are resolved by the generator under test rather than by this harness.
    """
    repo = tmp_path / "repo"
    seeds = materialize_declared_root_topology(repo, topology_factory())
    template = write_template(tmp_path, NEW_VERSION)
    run_generator_write_primary(repo, template, adopt_harness)
    return BootstrapOutcome(
        seeds=seeds,
        claude=(repo / INSTRUCTION_CLAUDE).read_text(encoding="utf-8"),
        agents=(repo / INSTRUCTION_AGENTS).read_text(encoding="utf-8"),
        repo=repo,
    )


def run_generator_check(
    repo_root: pathlib.Path,
    template_path: pathlib.Path,
    *,
    languages: str | None = None,
) -> tuple[int, str]:
    """Run the real ``--check`` surface and return its exit code and report word.

    Implemented on the diagnostics runner so the CLI-invocation shape has one owner;
    this form discards the stderr diagnostics stream.
    """
    result, verdict, _diagnostics = run_generator_check_with_diagnostics(
        repo_root, template_path, languages=languages
    )
    return result, verdict


def run_generator_check_with_diagnostics(
    repo_root: pathlib.Path,
    template_path: pathlib.Path,
    *,
    languages: str | None = None,
) -> tuple[int, str, str]:
    """Run the real ``--check`` surface and return exit code, stdout verdict, and stderr.

    The verdict word stays the stdout contract; per-file diagnostics such as the budget
    report lines go to stderr, so this runner captures both streams for tests that read
    the diagnostics beside the verdict.
    """
    output = io.StringIO()
    errors = io.StringIO()
    cases = generated_cases()
    selected_languages = cases.lang_primary if languages is None else languages
    with redirect_stdout(output), redirect_stderr(errors):
        result = cast(
            int,
            load_instruction_block_module().main(
                [
                    "--template",
                    str(template_path),
                    "--repo-root",
                    str(repo_root),
                    f"--languages={selected_languages}",
                    "--check",
                ]
            ),
        )
    return result, output.getvalue().strip(), errors.getvalue()


def run_generator_reconcile(
    repo_root: pathlib.Path, template_path: pathlib.Path
) -> tuple[int, str]:
    """Run the real ``--reconcile`` surface and return its exit code and stderr report."""
    errors = io.StringIO()
    cases = generated_cases()
    with redirect_stderr(errors):
        result = cast(
            int,
            load_instruction_block_module().main(
                [
                    "--template",
                    str(template_path),
                    "--repo-root",
                    str(repo_root),
                    f"--languages={cases.lang_primary}",
                    "--reconcile",
                ]
            ),
        )
    return result, errors.getvalue()


def root_document_with_shared_region(
    module: ModuleType,
    harness: str,
    region_body: str,
    *,
    languages: tuple[str, ...],
    version: str,
    name: str | None = None,
) -> str:
    """Return a root document: the harness router block first, then one shared region.

    Mirrors a real post-bootstrap file — the router block on top of a single named shared
    region — so a file this helper produces has the three-content-kind shape a ``--reconcile``
    operates on. This root instruction-file setup policy lives in the harness, not a test body.
    """
    cases = generated_cases()
    template = generate_template(module, cases, version)
    block = module.render(template, languages, version, harness)
    region_name = name or cases.shared_region_name
    fenced = (
        f"{module.shared_open_marker(region_name)}\n\n{region_body}\n\n"
        f"{module.shared_close_marker(region_name)}"
    )
    return cast(str, module.prepend_router_block(block, fenced))


def write_both_root_files_with_shared_region(
    module: ModuleType,
    repo_root: pathlib.Path,
    *,
    languages: tuple[str, ...],
    version: str,
    claude_region: str | None = None,
    agents_region: str | None = None,
    name: str | None = None,
) -> None:
    """Write root CLAUDE.md and AGENTS.md, each a router block over one named shared region.

    The two region bodies are equal by default; passing different ``claude_region`` and
    ``agents_region`` seeds a diverged shared region for a recency-reconcile test.
    """
    cases = generated_cases()
    bodies = {
        cases.instruction_claude: (
            claude_region or SHARED_REGION_BODY,
            cases.harness_claude,
        ),
        cases.instruction_agents: (
            agents_region or SHARED_REGION_BODY,
            cases.harness_codex,
        ),
    }
    for filename, (region_body, harness) in bodies.items():
        (repo_root / filename).write_text(
            root_document_with_shared_region(
                module,
                harness,
                region_body,
                languages=languages,
                version=version,
                name=name,
            ),
            encoding="utf-8",
        )


def git_command(
    repo_root: pathlib.Path, *args: str
) -> subprocess.CompletedProcess[str]:
    """Run a git command in ``repo_root`` for tests that need real git state.

    Centralizes the git subprocess setup the drift-gate tests share, since harness code —
    not test bodies — owns shared execution scaffolding.
    """
    return subprocess.run(
        ["git", *args], cwd=repo_root, capture_output=True, check=True, text=True
    )


def init_git_identity(repo_root: pathlib.Path) -> None:
    """Initialize a git repository with a committed-safe identity for drift-gate tests.

    ``commit.gpgsign`` is forced off in local config so a committer whose global config enables GPG
    signing — the norm this repository's git-safety protocol protects — does not fail the throwaway
    ``Test User`` commits these tests make; the local setting overrides the ambient global one.
    """
    git_command(repo_root, "init")
    git_command(repo_root, "config", "user.name", "Test User")
    git_command(repo_root, "config", "user.email", "test@example.com")
    git_command(repo_root, "config", "commit.gpgsign", "false")


def git_commit_at(
    repo_root: pathlib.Path,
    timestamp: int,
    *paths: str,
    message: str = "commit",
) -> None:
    """Stage ``paths`` and commit them at a fixed epoch ``timestamp``.

    A recency-reconcile test needs two commits whose committer dates differ deterministically;
    fixing ``GIT_AUTHOR_DATE`` and ``GIT_COMMITTER_DATE`` to an explicit epoch makes the newer
    side unambiguous without depending on wall-clock time. Committing setup is harness-owned.
    """
    for path in paths:
        git_command(repo_root, "add", path)
    date = f"@{timestamp} +0000"
    env = os.environ.copy()
    env["GIT_AUTHOR_DATE"] = date
    env["GIT_COMMITTER_DATE"] = date
    subprocess.run(
        ["git", "commit", "-m", message],
        cwd=repo_root,
        capture_output=True,
        check=True,
        text=True,
        env=env,
    )


def workflow_run_block(step_name: str) -> str:
    """Return the run-command block of one refresh-workflow step, dedented for assertions.

    Reads ``.github/workflows/refresh-instruction-blocks.yml`` and extracts the ``run: |`` block
    of the named step. Workflow parsing is shared setup, so it lives in the harness rather than a
    test body.
    """
    workflow = distribution.REFRESH_WORKFLOW.path().read_text(encoding="utf-8")
    lines = workflow.splitlines()
    step_line = f"      - name: {step_name}"
    start = lines.index(step_line)
    run_line = lines.index("        run: |", start)
    block: list[str] = []
    for line in lines[run_line + 1 :]:
        if line.startswith("      - name: "):
            break
        if line.startswith("          "):
            block.append(line[10:])
        elif line:
            break
        else:
            block.append("")
    return "\n".join(block) + "\n"


def workflow_step_block(step_name: str) -> str:
    """Return the full YAML block of one refresh-workflow step, for step assertions."""
    workflow = distribution.REFRESH_WORKFLOW.path().read_text(encoding="utf-8")
    lines = workflow.splitlines()
    step_line = f"      - name: {step_name}"
    start = lines.index(step_line)
    block: list[str] = []
    for line in lines[start:]:
        if line.startswith("      - name: ") and block:
            break
        block.append(line)
    return "\n".join(block) + "\n"


def workflow_env_value(name: str) -> str:
    """Return the value of one refresh-workflow ``env`` entry, for env assertions."""
    workflow = distribution.REFRESH_WORKFLOW.path().read_text(encoding="utf-8")
    prefix = f"      {name}: "
    for line in workflow.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).split(" #", maxsplit=1)[0].strip('"')
    raise AssertionError(f"workflow env value not found: {name}")


def justfile_recipe_body(justfile: str, recipe: str) -> str:
    """Return the indented body of one justfile recipe, for recipe-binding assertions.

    A recipe header is ``<recipe>:`` at column 0; its body is the following indented lines up to
    the next unindented line. Scoping an invocation to the recipe body, rather than to the whole
    file, is what makes a recipe-body swap falsifiable.
    """
    lines = justfile.splitlines()
    start = lines.index(f"{recipe}:")
    body: list[str] = []
    for line in lines[start + 1 :]:
        if line and not line[0].isspace():
            break
        body.append(line)
    return "\n".join(body)


def write_gh_stub(bin_dir: pathlib.Path, log_path: pathlib.Path) -> None:
    """Write a fake ``gh`` CLI into ``bin_dir`` that logs its args and accepts pr list/create."""
    stub = bin_dir / "gh"
    stub.write_text(
        "\n".join(
            [
                "#!/usr/bin/env bash",
                "set -euo pipefail",
                f'printf "%s\\n" "$*" >> {str(log_path)!r}',
                'if [ "${1:-}" = "pr" ] && [ "${2:-}" = "list" ]; then',
                '  if [ -n "${REFRESH_EXISTING_PR_NUMBER:-}" ]; then',
                '    printf "%s\\n" "$REFRESH_EXISTING_PR_NUMBER"',
                "  fi",
                "  exit 0",
                "fi",
                'if [ "${1:-}" = "pr" ] && [ "${2:-}" = "create" ]; then',
                "  exit 0",
                "fi",
                'echo "unexpected gh invocation: $*" >&2',
                "exit 64",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    stub.chmod(0o755)


def run_refresh_pr_step(
    repo_root: pathlib.Path,
    gh_log: pathlib.Path,
    *,
    existing_pr_number: str | None = None,
) -> str:
    """Run the refresh workflow's PR-opening step against ``repo_root`` with a stubbed ``gh``.

    Executes the extracted step's bash block with a fake ``gh`` on PATH so the drift-driven
    commit-and-open behavior runs for real without a network call. Subprocess execution setup is
    the harness's responsibility, not a test body's.
    """
    bin_dir = repo_root.parent / f"{repo_root.name}-stub-bin"
    bin_dir.mkdir(exist_ok=True)
    write_gh_stub(bin_dir, gh_log)
    env = os.environ.copy()
    env["GH_TOKEN"] = "test-token"
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    if existing_pr_number is not None:
        env["REFRESH_EXISTING_PR_NUMBER"] = existing_pr_number
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            workflow_run_block(distribution.REFRESH_WORKFLOW.open_pr_step),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def materialize_refresh_repository(root: pathlib.Path) -> pathlib.Path:
    """Clone the committed repository head behind an invocation-owned bare remote."""
    remote = root / "remote.git"
    repo = root / "repo"
    git_command(root, "clone", "--bare", "--no-local", str(REPO_ROOT), str(remote))
    git_command(root, "clone", str(remote), str(repo))
    head = git_command(REPO_ROOT, "rev-parse", "HEAD").stdout.strip()
    git_command(
        repo, "checkout", "-B", distribution.REFRESH_WORKFLOW.default_branch, head
    )
    git_command(repo, "config", "user.name", "Test User")
    git_command(repo, "config", "user.email", "test@example.com")
    git_command(repo, "config", "commit.gpgsign", "false")
    git_command(
        repo,
        "push",
        "--force",
        "-u",
        "origin",
        distribution.REFRESH_WORKFLOW.default_branch,
    )
    return repo


def run_refresh_regeneration_step(repo_root: pathlib.Path) -> str:
    """Execute the refresh workflow's regeneration block with an owned toolchain stub."""
    bin_dir = repo_root.parent / f"{repo_root.name}-refresh-toolchain"
    bin_dir.mkdir(exist_ok=True)
    just = bin_dir / "just"
    just.write_text(
        "\n".join(
            [
                f"#!{sys.executable}",
                "from pathlib import Path",
                "import subprocess",
                "import sys",
                "from outcomeeng.distribution import build as distribution_build",
                "from outcomeeng.distribution import instruction_block as distribution_instructions",
                "",
                "repo_root = Path.cwd().resolve()",
                "for module in (distribution_build, distribution_instructions):",
                "    if not Path(module.__file__).resolve().is_relative_to(repo_root):",
                "        raise SystemExit(f'production module outside clone: {module.__file__}')",
                "",
                "def formatter_runner(args: tuple[str, ...], cwd: Path) -> subprocess.CompletedProcess[str]:",
                "    return subprocess.CompletedProcess(",
                "        args, 0, distribution_build.FORMATTER_VERSION_OUTPUT, ''",
                "    )",
                "",
                "recipe = sys.argv[1]",
                "if recipe == 'build-skills':",
                "    distribution_build.build(",
                "        Path('src'),",
                "        Path('dist'),",
                "        formatter_probe=lambda _: 'dprint',",
                "        formatter_runner=formatter_runner,",
                "    )",
                "elif recipe == 'build-instructions':",
                "    distribution_instructions.regenerate_instruction_blocks(repo_root=Path.cwd())",
                "else:",
                "    raise SystemExit(f'unexpected recipe: {recipe}')",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    just.chmod(0o755)
    env = os.environ.copy()
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
    env["PYTHONPATH"] = str(repo_root)
    result = subprocess.run(
        [
            "/bin/bash",
            "-c",
            workflow_run_block(distribution.REFRESH_WORKFLOW.regenerate_step),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout


def advance_authored_template_version(repo_root: pathlib.Path) -> tuple[str, str]:
    """Advance the real authored template version by one patch release."""
    module = distribution.load_instruction_block_module()
    path = repo_root / distribution.AUTHORED_TEMPLATE_RELATIVE_PATH
    source = path.read_text(encoding="utf-8")
    current = module.parse_template_version(source)
    assert current is not None
    parts = [int(part) for part in current.split(".")]
    parts[-1] += 1
    advanced = ".".join(str(part) for part in parts)
    current_field = f'{module.TEMPLATE_VERSION_KEY}: "{current}"'
    advanced_field = f'{module.TEMPLATE_VERSION_KEY}: "{advanced}"'
    updated = source.replace(current_field, advanced_field, 1)
    assert updated != source
    path.write_text(updated, encoding="utf-8")
    return current, advanced
