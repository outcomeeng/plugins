"""Test harness for the instruction-block render module.

Exposes:

- An importlib loader for ``instruction_block.py``. The module ships under a
  generated plugin skill directory and is not importable by package
  name; tests load it through ``importlib`` instead.
- ``build_template``. Constructs a synthetic instruction-block.md-shaped template with a
  brace-delimited illustration token, a language-conditional block per language in
  ``TEMPLATE_LANGUAGES``, and (optionally) a section that exists only in a newer
  template — for exercising new-section propagation on update. The lang-block
  marker syntax mirrors the module's ``<!-- lang:NAME -->`` conditional-block contract
  (parsed by ``_filter_languages``); a synthetic template that drifts from it fails to
  render, which is the intended input-fixture coupling.

The render and parse functions take document strings, so the harness builds
documents as strings; no filesystem is involved.
"""

from __future__ import annotations

import importlib.util
import json
import os
import pathlib
import subprocess
from dataclasses import dataclass
import sys
from tempfile import TemporaryDirectory
from types import ModuleType
from typing import Final, cast

REPO_ROOT: Final = pathlib.Path(__file__).resolve().parents[2]
# Coupled to the update-instruction-block skill directory name; a rename there must update
# this path or load_instruction_block_module raises RuntimeError at import time.
INSTRUCTION_BLOCK_MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "update-instruction-block"
    / "scripts"
    / "instruction_block.py"
)
CANONICAL_TEMPLATE_PATH = (
    REPO_ROOT
    / "src"
    / "plugins"
    / "spec-tree"
    / "skills"
    / "understand"
    / "templates"
    / "instruction-block.md"
)

INSTRUCTION_CLAUDE: Final = "CLAUDE.md"
INSTRUCTION_AGENTS: Final = "AGENTS.md"
ROOT_TOPOLOGY_FIXTURES_DIR: Final = (
    REPO_ROOT / "outcomeeng_testing" / "fixtures" / "instruction_block"
)
TOPOLOGY_ONLY_CLAUDE: Final = "only-claude.json"
TOPOLOGY_ONLY_AGENTS: Final = "only-agents.json"
TOPOLOGY_SEPARATE: Final = "separate.json"
TOPOLOGY_SYMLINKED: Final = "symlinked.json"

# Invented shared-region body payloads the harness owns, for shared-region preservation and
# recency-reconcile tests. Their byte-identity (or, for the ALT, their divergence) across the two
# root files is what the tests assert; the strings carry no domain vocabulary.
SHARED_REGION_NAME: Final = "root"
SHARED_REGION_BODY: Final = "Build: `product build --all`"
SHARED_REGION_BODY_ALT: Final = "Build: `product build --changed`"

# Two near-identical root-file bodies for the bootstrap line-boundary guard: more than 80%
# identical but diverging mid-line on a harness-specific word, so the longest contiguous common
# span ends mid-line. The bootstrap must snap to line boundaries rather than split the divergent
# line across the shared-region fence.
_NEAR_IDENTICAL_COMMON: Final = (
    "\n".join(
        f"Common line {index} with plenty of words to be substantial here."
        for index in range(30)
    )
    + "\n"
)
ROOT_NEAR_IDENTICAL_CLAUDE: Final = (
    _NEAR_IDENTICAL_COMMON + "Shared opening words then CLAUDE specific tail here.\n"
)
ROOT_NEAR_IDENTICAL_CODEX: Final = (
    _NEAR_IDENTICAL_COMMON + "Shared opening words then CODEX specific tail here.\n"
)

# A pair for the bootstrap span-maximality guard: a whole-line-identical block plus a longer
# near-duplicate single line diverging mid-line. The byte-level-longest match is that long line,
# which snaps away to nothing at a line boundary — so the biggest whole-line span is the block
# elsewhere, and the wrap must find it rather than under-detect from the single longest byte match.
_STRADDLING_BLOCK: Final = (
    "\n".join(
        f"Common whole line number {index} shared across both files."
        for index in range(6)
    )
    + "\n"
)
# The long prefix and the diverging tail form ONE line (no newline between them), so the
# byte-longest match is that line's shared prefix — which straddles the line and snaps away.
_STRADDLING_LONG_PREFIX: Final = "x" * 480
ROOT_STRADDLING_CLAUDE: Final = (
    _STRADDLING_BLOCK + _STRADDLING_LONG_PREFIX + "AAAAA claude-specific tail here.\n"
)
ROOT_STRADDLING_CODEX: Final = (
    _STRADDLING_BLOCK + _STRADDLING_LONG_PREFIX + "BBBBB codex-specific tail here.\n"
)

# A pair whose shared content starts at a line boundary in one file but mid-line in the other: the
# second file carries a harness-specific prefix on the otherwise-shared first line. The bootstrap
# must snap the span to line boundaries in BOTH files, never splitting the prefixed line.
_MIDLINE_COMMON: Final = "".join(
    f"identical line {index} here with plenty of content to dominate.\n"
    for index in range(20)
)
ROOT_MIDLINE_CLAUDE: Final = "shared prose here\n" + _MIDLINE_COMMON
ROOT_MIDLINE_CODEX: Final = "harness-prefix shared prose here\n" + _MIDLINE_COMMON

# The retired session-result tokens the shipped instruction block must never teach. No
# production module owns a removed token, so the regression guard declares the forbidden
# strings here and asserts they are absent from the real rendered output.
SESSION_MANAGEMENT_HEADING = "## Session Management"
SESSION_ARCHIVE_RESULT_INSTRUCTION = "Before archiving a claimed session"
SESSION_RESULT_FRONTMATTER_FIELD = "`result`"

# The required read-the-whole-file directive the router must carry so a reading agent reaches the
# product's own commands below the router. Declared here as the required-content vocabulary the
# compliance guard asserts is present in the rendered router.
READ_ENTIRE_FILE_INSTRUCTION = "Read this entire file"

# Invented scenario payload owned by the harness.
LANG_PRIMARY = "python"
LANG_SECONDARY = "typescript"
TEMPLATE_LANGUAGES = (LANG_PRIMARY, LANG_SECONDARY)
BASE_SECTION = "Test Naming"
NEW_SECTION = "Process Hygiene"
# Invented scenario version payload owned by the harness: NEW_VERSION is the installed (current)
# template version, OLD_VERSION a version numerically below it. The values carry no domain
# meaning; the dotted-numeric ordering NEW_VERSION > OLD_VERSION is what the staleness and
# upgrade scenarios rely on.
OLD_VERSION: Final = "0.17.0"
NEW_VERSION: Final = "0.18.0"
# A brace-delimited illustration token the render must pass through unchanged.
ILLUSTRATION_TOKEN = "{product-slug}"
BUILD_MACRO_CAPABILITY = "ask_user"
BUILD_MACRO_HARNESS = "codex"

# Harness payload: the template carries a per-harness block for each agent harness,
# rendered only into that harness's instruction file. The marker syntax mirrors the module's
# ``<!-- harness:NAME -->`` conditional-block contract (parsed by ``_filter_harness``); a
# synthetic template that drifts from it fails to render.
HARNESS_CLAUDE = "claude"
HARNESS_CODEX = "codex"
TEMPLATE_HARNESSES = (HARNESS_CLAUDE, HARNESS_CODEX)


@dataclass(frozen=True)
class RootInstructionTopology:
    """Root instruction files and symlinks a consumer repository may already contain."""

    files: dict[str, str]
    symlinks: dict[str, str]


def _load_root_instruction_topology(fixture_name: str) -> RootInstructionTopology:
    """Load one inert whole-topology fixture from disk."""
    payload = json.loads(
        (ROOT_TOPOLOGY_FIXTURES_DIR / fixture_name).read_text(encoding="utf-8")
    )
    return RootInstructionTopology(
        files=cast(dict[str, str], payload["files"]),
        symlinks=cast(dict[str, str], payload["symlinks"]),
    )


def root_instruction_topology_only_claude() -> RootInstructionTopology:
    """Return a root topology with only the Claude harness instruction file present."""
    return _load_root_instruction_topology(TOPOLOGY_ONLY_CLAUDE)


def root_instruction_topology_only_agents() -> RootInstructionTopology:
    """Return a root topology with only the Codex harness instruction file present."""
    return _load_root_instruction_topology(TOPOLOGY_ONLY_AGENTS)


def root_instruction_topology_separate() -> RootInstructionTopology:
    """Return a root topology with two independent harness instruction files."""
    return _load_root_instruction_topology(TOPOLOGY_SEPARATE)


def root_instruction_topology_symlinked() -> RootInstructionTopology:
    """Return a root topology matching a shared instruction file with a harness symlink."""
    return _load_root_instruction_topology(TOPOLOGY_SYMLINKED)


ROOT_CLAUDE_BODY: Final = root_instruction_topology_only_claude().files[
    INSTRUCTION_CLAUDE
]
ROOT_AGENTS_BODY: Final = root_instruction_topology_only_agents().files[
    INSTRUCTION_AGENTS
]
ROOT_SHARED_BODY: Final = root_instruction_topology_symlinked().files[
    INSTRUCTION_AGENTS
]


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

    claude_seed = _seed_body(root, INSTRUCTION_CLAUDE, None)
    agents_seed = _seed_body(root, INSTRUCTION_AGENTS, claude_seed)
    if claude_seed is None:
        claude_seed = agents_seed
    if claude_seed is None or agents_seed is None:
        claude_seed = agents_seed = ""

    seeds = {INSTRUCTION_CLAUDE: claude_seed, INSTRUCTION_AGENTS: agents_seed}
    for name, body in seeds.items():
        _replace_path_with_text(root / name, body)
    return seeds


def _assert_root_instruction_topology_mapping(
    topology: RootInstructionTopology, expected: dict[str, str]
) -> None:
    """Materialize one topology and assert its source-owned seed mapping."""
    with TemporaryDirectory() as directory:
        assert (
            materialize_root_instruction_topology(pathlib.Path(directory), topology)
            == expected
        )


def assert_only_claude_topology_maps_to_both_harnesses() -> None:
    """Assert a lone Claude instruction file seeds both harness paths."""
    topology = root_instruction_topology_only_claude()
    body = topology.files[INSTRUCTION_CLAUDE]
    _assert_root_instruction_topology_mapping(
        topology,
        {INSTRUCTION_CLAUDE: body, INSTRUCTION_AGENTS: body},
    )


def assert_only_agents_topology_maps_to_both_harnesses() -> None:
    """Assert a lone Agents instruction file seeds both harness paths."""
    topology = root_instruction_topology_only_agents()
    body = topology.files[INSTRUCTION_AGENTS]
    _assert_root_instruction_topology_mapping(
        topology,
        {INSTRUCTION_CLAUDE: body, INSTRUCTION_AGENTS: body},
    )


def assert_separate_topology_maps_each_harness_body() -> None:
    """Assert separate instruction files retain their matching bodies."""
    topology = root_instruction_topology_separate()
    _assert_root_instruction_topology_mapping(
        topology,
        dict(topology.files),
    )


def assert_symlinked_topology_maps_shared_body() -> None:
    """Assert a symlinked topology seeds both harness paths from the target."""
    topology = root_instruction_topology_symlinked()
    body = topology.files[INSTRUCTION_AGENTS]
    _assert_root_instruction_topology_mapping(
        topology,
        {INSTRUCTION_CLAUDE: body, INSTRUCTION_AGENTS: body},
    )


def assert_symlinked_topology_materializes_regular_files() -> None:
    """Assert symlink normalization preserves bodies in regular files."""
    topology = root_instruction_topology_symlinked()
    body = topology.files[INSTRUCTION_AGENTS]
    with TemporaryDirectory() as directory:
        root = pathlib.Path(directory)
        materialized = materialize_root_instruction_topology(root, topology)
        claude_path = root / INSTRUCTION_CLAUDE
        agents_path = root / INSTRUCTION_AGENTS

        assert claude_path.is_file()
        assert agents_path.is_file()
        assert not claude_path.is_symlink()
        assert not agents_path.is_symlink()
        assert claude_path.read_text(encoding="utf-8") == body
        assert agents_path.read_text(encoding="utf-8") == body
        assert materialized[INSTRUCTION_CLAUDE] == body
        assert materialized[INSTRUCTION_AGENTS] == body


def harness_line(harness: str) -> str:
    """The body the harness emits inside a harness block — what render keeps or drops."""
    return f"{harness.upper()} runs the audit as a subagent."


def render_build_macro() -> str:
    """Build an unresolved macro-shaped token owned by the render harness."""
    return f"\n{{{{! tool('{BUILD_MACRO_CAPABILITY}', '{BUILD_MACRO_HARNESS}') !}}}}\n"


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


def _language_heading(language: str) -> str:
    """The H3 heading the harness emits inside a language block — what render keeps or drops."""
    return f"### {language.capitalize()}"


def build_template(version: str, *, extra_section: bool = False) -> str:
    """Build a synthetic template at ``version`` with a block per template language.

    With ``extra_section`` the template also carries ``NEW_SECTION`` — a section a
    newer template introduces, absent from an older one.
    """
    module = load_instruction_block_module()
    delimiter = module.FRONTMATTER_DELIMITER
    frontmatter = (
        f"{delimiter}\n"
        f'{module.TEMPLATE_VERSION_KEY}: "{version}"\n'
        f"{module.TEMPLATE_SOURCE_KEY}: {module.DEFAULT_TEMPLATE_SOURCE}\n"
        f"{delimiter}\n"
    )
    parts = [
        "",
        "# Spec Tree Instructions",
        "",
        f"The root spec is `{ILLUSTRATION_TOKEN}.product.md`.",
        "",
        f"## {BASE_SECTION}",
        "",
    ]
    for language in TEMPLATE_LANGUAGES:
        parts += [
            f"<!-- lang:{language} -->",
            "",
            _language_heading(language),
            f"{language} naming rules",
            "",
            f"<!-- /lang:{language} -->",
        ]
    for harness in TEMPLATE_HARNESSES:
        parts += [
            f"<!-- harness:{harness} -->",
            "",
            harness_line(harness),
            "",
            f"<!-- /harness:{harness} -->",
        ]
    if extra_section:
        parts += ["", f"## {NEW_SECTION}", "", "new methodology guidance"]
    return frontmatter + "\n".join(parts) + "\n"


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
    path.write_text(
        build_template(version, extra_section=extra_section), encoding="utf-8"
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
                "--languages",
                languages,
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
    return run_generator_write(
        load_instruction_block_module(),
        repo_root,
        template_path,
        languages=LANG_PRIMARY,
    )


def root_document_with_shared_region(
    module: ModuleType,
    harness: str,
    region_body: str,
    *,
    languages: tuple[str, ...],
    version: str,
    name: str = SHARED_REGION_NAME,
) -> str:
    """Return a root document: the harness router block first, then one shared region.

    Mirrors a real post-bootstrap file — the router block on top of a single named shared
    region — so a file this helper produces has the three-content-kind shape a ``--reconcile``
    operates on. This root instruction-file setup policy lives in the harness, not a test body.
    """
    template = build_template(version)
    block = module.render(template, languages, version, harness)
    fenced = (
        f"{module.shared_open_marker(name)}\n\n{region_body}\n\n"
        f"{module.shared_close_marker(name)}"
    )
    return cast(str, module.prepend_router_block(block, fenced))


def write_both_root_files_with_shared_region(
    module: ModuleType,
    repo_root: pathlib.Path,
    *,
    languages: tuple[str, ...],
    version: str,
    claude_region: str = SHARED_REGION_BODY,
    agents_region: str = SHARED_REGION_BODY,
    name: str = SHARED_REGION_NAME,
) -> None:
    """Write root CLAUDE.md and AGENTS.md, each a router block over one named shared region.

    The two region bodies are equal by default; passing different ``claude_region`` and
    ``agents_region`` seeds a diverged shared region for a recency-reconcile test.
    """
    bodies = {
        module.AGENT_HARNESS_INSTRUCTION_FILENAMES["claude"]: (claude_region, "claude"),
        module.AGENT_HARNESS_INSTRUCTION_FILENAMES["codex"]: (agents_region, "codex"),
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
    workflow = REPO_ROOT.joinpath(
        ".github", "workflows", "refresh-instruction-blocks.yml"
    ).read_text(encoding="utf-8")
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
    workflow = REPO_ROOT.joinpath(
        ".github", "workflows", "refresh-instruction-blocks.yml"
    ).read_text(encoding="utf-8")
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
    workflow = REPO_ROOT.joinpath(
        ".github", "workflows", "refresh-instruction-blocks.yml"
    ).read_text(encoding="utf-8")
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
            workflow_run_block("Open instruction-block refresh pull request"),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout
