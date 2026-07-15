"""Test harness for the instruction-block render module.

Exposes resource and execution infrastructure for generated cases:

- An importlib loader for ``instruction_block.py``. The module ships under a
  generated plugin skill directory and is not importable by package
  name; tests load it through ``importlib`` instead.
- Generator-owned templates and protocol cases derived from the production module and
  canonical template, plus harness-accessed inert whole-document fixtures for root bodies,
  shared-region examples, and line-boundary examples.
- ``canonical_router_spacing_is_valid_for_all_mappings``. Renders the canonical template for
  every source-owned harness and every subset of its declared languages, then checks the
  marker-to-body separator without placing setup or iteration policy in a test file.
- ``unsupported_language_overrides_are_rejected``. Searches unsupported language tokens with
  replayable property-run settings derived from the canonical template's declared languages.

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
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
import sys
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Final, cast

from hypothesis import given, seed, settings

from outcomeeng.distribution import instruction_block as distribution
from outcomeeng_testing.generators.instruction_block import (
    InstructionBlockCases,
    build_macro as generate_build_macro,
    build_template as generate_template,
    harness_line as generate_harness_line,
    instruction_block_cases,
    unsupported_language_tokens,
)

REPO_ROOT: Final = pathlib.Path(__file__).resolve().parents[2]
INSTRUCTION_BLOCK_MODULE_PATH = distribution.GENERATOR_PATH
CANONICAL_TEMPLATE_PATH = distribution.AUTHORED_TEMPLATE_PATH
FIXTURES_DIR: Final = REPO_ROOT / "outcomeeng_testing/fixtures/instruction_block"

LANGUAGE_OVERRIDE_PROPERTY_SEED = 20260714
LANGUAGE_OVERRIDE_PROPERTY_EXAMPLES = 50


def _fixture_text(name: str) -> str:
    """Read one inert whole-document instruction-block fixture."""
    return FIXTURES_DIR.joinpath(name).read_text(encoding="utf-8")


@dataclass(frozen=True)
class RootInstructionTopology:
    """Root instruction files and symlinks a consumer repository may already contain."""

    files: dict[str, str]
    symlinks: dict[str, str]


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


def read_canonical_template() -> str:
    """Read the canonical template both instruction files render from."""
    return CANONICAL_TEMPLATE_PATH.read_text(encoding="utf-8")


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


def canonical_router_spacing_is_valid_for_all_mappings() -> bool:
    """Check canonical spacing for every source harness and declared-language subset."""
    module = load_instruction_block_module()
    template = read_canonical_template()
    languages = template_declared_languages(template)
    version = module.parse_template_version(template)

    for agent_harness in sorted(module.AGENT_HARNESS_INSTRUCTION_FILENAMES):
        for enabled_languages in _language_subsets(languages):
            marker = module.router_marker(version, enabled_languages)
            separator = f"{marker}{module.ROUTER_BODY_SEPARATOR}"
            rendered = module.render(
                template,
                enabled_languages,
                version,
                agent_harness,
            )
            body = rendered.removeprefix(separator)
            if body == rendered or body.startswith("\n"):
                return False
    return True


def unsupported_language_overrides_are_rejected() -> bool:
    """Check generated unsupported tokens against the canonical template language contract."""
    module = load_instruction_block_module()
    supported_languages = template_declared_languages(read_canonical_template())

    @seed(LANGUAGE_OVERRIDE_PROPERTY_SEED)
    @settings(max_examples=LANGUAGE_OVERRIDE_PROPERTY_EXAMPLES, deadline=None)
    @given(token=unsupported_language_tokens(supported_languages))
    def assertion(token: str) -> None:
        stderr = io.StringIO()
        with TemporaryDirectory() as directory, redirect_stderr(stderr):
            result = run_generator_write(
                module,
                pathlib.Path(directory).resolve(),
                CANONICAL_TEMPLATE_PATH,
                languages=token,
            )

        message = stderr.getvalue()
        assert result == 2
        assert token in message
        assert all(language in message for language in supported_languages)

    assertion()
    return True


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
    path = directory / "instruction-block.md"
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
) -> int:
    """Run the generator CLI's ``--write`` over ``repo_root`` and return its exit code.

    Centralizes the CLI-invocation setup the render-model tests share, since harness code —
    not test bodies — owns shared execution scaffolding. The dynamically loaded module types
    ``main`` as ``Any``; the CLI contract returns an exit code, so the result is cast to ``int``.
    """
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
            ]
        ),
    )


def run_generator_write_primary(
    repo_root: pathlib.Path, template_path: pathlib.Path
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
    )


def run_generator_check(
    repo_root: pathlib.Path,
    template_path: pathlib.Path,
    *,
    languages: str | None = None,
) -> tuple[int, str]:
    """Run the real ``--check`` surface and return its exit code and report word."""
    output = io.StringIO()
    cases = generated_cases()
    selected_languages = cases.lang_primary if languages is None else languages
    with redirect_stdout(output):
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
    return result, output.getvalue().strip()


def scenario_evidence_is_valid() -> bool:
    """Run all scenario cases behind one zero-argument harness entrypoint."""
    from outcomeeng_testing.harnesses import instruction_block_scenario_evidence

    return instruction_block_scenario_evidence.scenario_evidence_is_valid()


def mapping_evidence_is_valid() -> bool:
    """Run all mapping cases behind one zero-argument harness entrypoint."""
    from outcomeeng_testing.harnesses import instruction_block_mapping_evidence

    return instruction_block_mapping_evidence.mapping_evidence_is_valid()


def property_evidence_is_valid() -> bool:
    """Run all property cases behind one zero-argument harness entrypoint."""
    from outcomeeng_testing.harnesses import instruction_block_property_evidence

    return instruction_block_property_evidence.property_evidence_is_valid()


def compliance_evidence_is_valid() -> bool:
    """Run all compliance cases behind one zero-argument harness entrypoint."""
    from outcomeeng_testing.harnesses import instruction_block_compliance_evidence

    return instruction_block_compliance_evidence.compliance_evidence_is_valid()


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


def run_refresh_pr_step(repo_root: pathlib.Path, gh_log: pathlib.Path) -> str:
    """Run the refresh workflow's PR-opening step against ``repo_root`` with a stubbed ``gh``.

    Executes the extracted step's bash block with a fake ``gh`` on PATH so the drift-driven
    commit-and-open behavior runs for real without a network call. Subprocess execution setup is
    the harness's responsibility, not a test body's.
    """
    bin_dir = repo_root.parent / f"{repo_root.name}-stub-bin"
    bin_dir.mkdir()
    write_gh_stub(bin_dir, gh_log)
    env = os.environ.copy()
    env["GH_TOKEN"] = "test-token"
    env["PATH"] = f"{bin_dir}{os.pathsep}{env['PATH']}"
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
