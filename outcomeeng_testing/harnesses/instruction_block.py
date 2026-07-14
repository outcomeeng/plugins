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

import os
import pathlib
import re
import subprocess
import tempfile
from dataclasses import dataclass
from types import ModuleType
from typing import Final, cast

import pytest

from outcomeeng.distribution import instruction_block as dist

REPO_ROOT: Final = pathlib.Path(__file__).resolve().parents[2]
FIXTURES_DIR: Final = REPO_ROOT / "outcomeeng_testing/fixtures/instruction_block"
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


def _fixture_text(name: str) -> str:
    """Read one inert whole-document instruction-block fixture."""
    return FIXTURES_DIR.joinpath(name).read_text(encoding="utf-8")


_SOURCE_MODULE = dist.load_instruction_block_module()
TEMPLATE_HARNESSES = tuple(_SOURCE_MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES)
HARNESS_CLAUDE, HARNESS_CODEX = TEMPLATE_HARNESSES
INSTRUCTION_CLAUDE = _SOURCE_MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES[HARNESS_CLAUDE]
INSTRUCTION_AGENTS = _SOURCE_MODULE.AGENT_HARNESS_INSTRUCTION_FILENAMES[HARNESS_CODEX]
ROOT_CLAUDE_BODY: Final = _fixture_text("root-claude.md")
ROOT_AGENTS_BODY: Final = _fixture_text("root-agents.md")
ROOT_SHARED_BODY: Final = _fixture_text("root-shared.md")

# Invented shared-region body payloads the harness owns, for shared-region preservation and
# recency-reconcile tests. Their byte-identity (or, for the ALT, their divergence) across the two
# root files is what the tests assert; the strings carry no domain vocabulary.
SHARED_REGION_NAME: Final = _SOURCE_MODULE.BOOTSTRAP_SHARED_REGION_NAME
SHARED_REGION_BODY: Final = _SOURCE_MODULE.parse_shared_regions(
    _fixture_text("shared-region-primary.md")
)[SHARED_REGION_NAME]
SHARED_REGION_BODY_ALT: Final = _SOURCE_MODULE.parse_shared_regions(
    _fixture_text("shared-region-alternate.md")
)[SHARED_REGION_NAME]

# Two near-identical root-file bodies for the bootstrap line-boundary guard: more than 80%
# identical but diverging mid-line on a harness-specific word, so the longest contiguous common
# span ends mid-line. The bootstrap must snap to line boundaries rather than split the divergent
# line across the shared-region fence.
ROOT_NEAR_IDENTICAL_CLAUDE: Final = _fixture_text("near-identical-claude.md")
ROOT_NEAR_IDENTICAL_CODEX: Final = _fixture_text("near-identical-codex.md")

# A pair for the bootstrap span-maximality guard: a whole-line-identical block plus a longer
# near-duplicate single line diverging mid-line. The byte-level-longest match is that long line,
# which snaps away to nothing at a line boundary — so the biggest whole-line span is the block
# elsewhere, and the wrap must find it rather than under-detect from the single longest byte match.
ROOT_STRADDLING_CLAUDE: Final = _fixture_text("straddling-claude.md")
ROOT_STRADDLING_CODEX: Final = _fixture_text("straddling-codex.md")

# A pair whose shared content starts at a line boundary in one file but mid-line in the other: the
# second file carries a harness-specific prefix on the otherwise-shared first line. The bootstrap
# must snap the span to line boundaries in BOTH files, never splitting the prefixed line.
ROOT_MIDLINE_CLAUDE: Final = _fixture_text("midline-claude.md")
ROOT_MIDLINE_CODEX: Final = _fixture_text("midline-codex.md")

# The retired session-result tokens the shipped instruction block must never teach. No
# production module owns a removed token, so the regression guard declares the forbidden
# strings here and asserts they are absent from the real rendered output.
SESSION_ARCHIVE_RESULT_INSTRUCTION, SESSION_RESULT_FRONTMATTER_FIELD = (
    dist.FORBIDDEN_ROUTER_TOKENS
)

# Invented scenario payload owned by the harness.
TEMPLATE_LANGUAGES = tuple(dict.fromkeys(_SOURCE_MODULE.LANGUAGE_BY_EXTENSION.values()))
LANG_PRIMARY, LANG_SECONDARY, *_ = TEMPLATE_LANGUAGES
_BASE_TEMPLATE = _fixture_text("template-base.md")
_EXTENDED_TEMPLATE = _fixture_text("template-extended.md")
_BASE_HEADINGS = tuple(
    line.removeprefix("## ")
    for line in _BASE_TEMPLATE.splitlines()
    if line.startswith("## ")
)
_EXTENDED_HEADINGS = tuple(
    line.removeprefix("## ")
    for line in _EXTENDED_TEMPLATE.splitlines()
    if line.startswith("## ")
)
BASE_SECTION = _BASE_HEADINGS[0]
NEW_SECTION = next(
    heading for heading in _EXTENDED_HEADINGS if heading not in _BASE_HEADINGS
)
# Invented scenario version payload owned by the harness: NEW_VERSION is the installed (current)
# template version, OLD_VERSION a version numerically below it. The values carry no domain
# meaning; the dotted-numeric ordering NEW_VERSION > OLD_VERSION is what the staleness and
# upgrade scenarios rely on.
_CURRENT_TEMPLATE_VERSION = _SOURCE_MODULE.parse_template_version(_BASE_TEMPLATE)
if _CURRENT_TEMPLATE_VERSION is None:
    raise RuntimeError(
        "instruction-block base template fixture has no template version"
    )
NEW_VERSION: Final[str] = _CURRENT_TEMPLATE_VERSION
_VERSION_PARTS = [int(part) for part in NEW_VERSION.split(".")]
_PREVIOUS_PART = next(
    index for index in range(len(_VERSION_PARTS) - 1, -1, -1) if _VERSION_PARTS[index]
)
_VERSION_PARTS[_PREVIOUS_PART] -= 1
for _index in range(_PREVIOUS_PART + 1, len(_VERSION_PARTS)):
    _VERSION_PARTS[_index] = 0
OLD_VERSION: Final = ".".join(str(part) for part in _VERSION_PARTS)
# A brace-delimited illustration token the render must pass through unchanged.
ILLUSTRATION_TOKEN = next(
    token
    for token in re.findall(r"\{[^{}\n]+\}", _BASE_TEMPLATE)
    if token not in dist.UNRESOLVED_BUILD_TEMPLATE_TOKENS
)

# Harness payload: the template carries a per-harness block for each agent harness,
# rendered only into that harness's instruction file. The marker syntax mirrors the module's
# ``<!-- harness:NAME -->`` conditional-block contract (parsed by ``_filter_harness``); a
# synthetic template that drifts from it fails to render.


@dataclass(frozen=True)
class RootInstructionTopology:
    """Root instruction files and symlinks a consumer repository may already contain."""

    files: dict[str, str]
    symlinks: dict[str, str]


def root_instruction_topology_only_claude() -> RootInstructionTopology:
    """Return a root topology with only the Claude harness instruction file present."""
    return RootInstructionTopology(
        files={INSTRUCTION_CLAUDE: ROOT_CLAUDE_BODY}, symlinks={}
    )


def root_instruction_topology_only_agents() -> RootInstructionTopology:
    """Return a root topology with only the Codex harness instruction file present."""
    return RootInstructionTopology(
        files={INSTRUCTION_AGENTS: ROOT_AGENTS_BODY}, symlinks={}
    )


def root_instruction_topology_separate() -> RootInstructionTopology:
    """Return a root topology with two independent harness instruction files."""
    return RootInstructionTopology(
        files={
            INSTRUCTION_CLAUDE: ROOT_CLAUDE_BODY,
            INSTRUCTION_AGENTS: ROOT_AGENTS_BODY,
        },
        symlinks={},
    )


def root_instruction_topology_symlinked() -> RootInstructionTopology:
    """Return a root topology matching a shared instruction file with a harness symlink."""
    return RootInstructionTopology(
        files={INSTRUCTION_AGENTS: ROOT_SHARED_BODY},
        symlinks={INSTRUCTION_CLAUDE: INSTRUCTION_AGENTS},
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


def harness_line(harness: str) -> str:
    """The body the harness emits inside a harness block — what render keeps or drops."""
    return f"{harness.upper()} runs the audit as a subagent."


def render_build_macro() -> str:
    """Return a source-owned unresolved build delimiter as template content."""
    return f"\n{dist.UNRESOLVED_BUILD_TEMPLATE_TOKENS[0]}\n"


def load_instruction_block_module() -> ModuleType:
    """Return the distribution module's loaded instruction-block implementation."""
    return cast(ModuleType, dist.load_instruction_block_module())


def read_canonical_template() -> str:
    """Read the canonical template both instruction files render from."""
    return CANONICAL_TEMPLATE_PATH.read_text(encoding="utf-8")


def _language_heading(language: str) -> str:
    """The H3 heading the harness emits inside a language block — what render keeps or drops."""
    return f"### {language.capitalize()}"


def build_template(version: str, *, extra_section: bool = False) -> str:
    """Read a whole-template fixture and replace only its source-owned version value."""
    template = _EXTENDED_TEMPLATE if extra_section else _BASE_TEMPLATE
    current = load_instruction_block_module().parse_template_version(template)
    if current is None:
        raise RuntimeError("instruction-block template fixture has no template version")
    return template.replace(
        f'template_version: "{current}"', f'template_version: "{version}"', 1
    )


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


def write_current_template(directory: pathlib.Path) -> pathlib.Path:
    """Write the harness's current synthetic template into ``directory``."""
    return write_template(directory, NEW_VERSION)


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


def copy_shipped_dist_templates(repo_root: pathlib.Path) -> None:
    """Copy each shipped instruction-block template into an isolated repository."""
    module = load_instruction_block_module()
    for agent_harness in module.AGENT_HARNESS_INSTRUCTION_FILENAMES:
        source = dist.dist_template_path(agent_harness)
        target = dist.dist_template_path(agent_harness, repo_root=repo_root)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def render_shipped_dist_with_generation_entrypoint() -> dict[str, str]:
    """Run production generation against copied shipped templates and return both outputs."""
    with tempfile.TemporaryDirectory() as directory:
        repo_root = pathlib.Path(directory).resolve() / "repo"
        repo_root.mkdir()
        copy_shipped_dist_templates(repo_root)
        dist.regenerate_instruction_blocks(repo_root=repo_root)
        module = load_instruction_block_module()
        return {
            agent_harness: repo_root.joinpath(filename).read_text(encoding="utf-8")
            for agent_harness, filename in module.AGENT_HARNESS_INSTRUCTION_FILENAMES.items()
        }


def assert_generation_writes_both_root_files() -> None:
    """Assert one generation writes both runtime root instruction files."""
    with tempfile.TemporaryDirectory() as directory:
        tmp_path = pathlib.Path(directory).resolve()
        repo = tmp_path / "repo"
        repo.mkdir()
        run_generator_write_primary(repo, write_current_template(tmp_path))
        assert (repo / INSTRUCTION_CLAUDE).is_file()
        assert (repo / INSTRUCTION_AGENTS).is_file()


def assert_router_is_first() -> None:
    """Assert production generation places the shipped router first in each output."""
    module = load_instruction_block_module()
    for document in render_shipped_dist_with_generation_entrypoint().values():
        assert document.startswith(module.ROUTER_MARKER_PREFIX)


def assert_generation_reads_dist_templates() -> None:
    """Assert production generation requires each runtime's shipped dist template."""
    module = load_instruction_block_module()
    for agent_harness in module.AGENT_HARNESS_INSTRUCTION_FILENAMES:
        with tempfile.TemporaryDirectory() as directory:
            repo_root = pathlib.Path(directory).resolve() / "repo"
            repo_root.mkdir()
            copy_shipped_dist_templates(repo_root)
            missing = dist.dist_template_path(agent_harness, repo_root=repo_root)
            missing.unlink()
            with pytest.raises(FileNotFoundError, match=str(missing)):
                dist.regenerate_instruction_blocks(repo_root=repo_root)


def assert_justfile_binds_instruction_recipes() -> None:
    """Assert repository recipes bind generation and drift checking."""
    justfile = dist.REPO_ROOT.joinpath(dist.JUSTFILE_NAME).read_text(encoding="utf-8")
    build_body = justfile_recipe_body(justfile, dist.BUILD_INSTRUCTIONS_RECIPE)
    check_body = justfile_recipe_body(justfile, dist.INSTRUCTIONS_CHECK_RECIPE)
    assert f"{dist.MODULE_INVOCATION} {dist.WRITE_FLAG}" in build_body
    assert dist.MODULE_INVOCATION in check_body
    assert dist.WRITE_FLAG not in check_body


def assert_lefthook_regenerates_through_build_instructions() -> None:
    """Assert pre-commit regeneration uses the repository recipe."""
    lefthook = dist.REPO_ROOT.joinpath(dist.LEFTHOOK_PATH).read_text(encoding="utf-8")
    assert dist.PRECOMMIT_BUILD_INSTRUCTIONS_COMMAND in lefthook
    assert dist.LEGACY_DIRECT_TEMPLATE_ARGUMENT not in lefthook
    assert dist.LEGACY_DIRECT_REPO_ROOT_ARGUMENT not in lefthook


def assert_drift_gate_reports_missing_root_instruction_file() -> None:
    """Assert a deleted generated root file registers as drift."""
    with tempfile.TemporaryDirectory() as directory:
        tmp_path = pathlib.Path(directory).resolve()
        module = load_instruction_block_module()
        repo = tmp_path / "repo"
        repo.mkdir()
        init_git_identity(repo)
        write_both_root_files_with_shared_region(
            module, repo, languages=(LANG_PRIMARY,), version=NEW_VERSION
        )
        git_commit_at(repo, 1000, INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS)
        (repo / INSTRUCTION_CLAUDE).unlink()
        drift = dist.drifting_instruction_files(repo_root=repo, module=module)
        assert INSTRUCTION_CLAUDE in drift


def assert_drift_gate_marks_untracked_root_files() -> None:
    """Assert never-committed root files register as intent-to-add drift."""
    with tempfile.TemporaryDirectory() as directory:
        tmp_path = pathlib.Path(directory).resolve()
        module = load_instruction_block_module()
        repo = tmp_path / "repo"
        repo.mkdir()
        init_git_identity(repo)
        write_both_root_files_with_shared_region(
            module, repo, languages=(LANG_PRIMARY,), version=NEW_VERSION
        )
        drift = dist.drifting_instruction_files(repo_root=repo, module=module)
        assert INSTRUCTION_CLAUDE in drift
        assert INSTRUCTION_AGENTS in drift


def assert_drift_gate_skips_missing_obsolete_spx_file() -> None:
    """Assert absent untracked legacy instruction paths do not create drift."""
    with tempfile.TemporaryDirectory() as directory:
        tmp_path = pathlib.Path(directory).resolve()
        module = load_instruction_block_module()
        repo = tmp_path / "repo"
        repo.mkdir()
        init_git_identity(repo)
        write_both_root_files_with_shared_region(
            module, repo, languages=(LANG_PRIMARY,), version=NEW_VERSION
        )
        git_commit_at(repo, 1000, INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS)
        drift = dist.drifting_instruction_files(repo_root=repo, module=module)
        assert drift == []
        assert "spx/CLAUDE.md" not in drift
        assert "spx/AGENTS.md" not in drift


def assert_refresh_pr_step_exits_cleanly_without_drift() -> None:
    """Assert refresh automation leaves GitHub untouched when output is current."""
    with tempfile.TemporaryDirectory() as directory:
        tmp_path = pathlib.Path(directory).resolve()
        gh_log = tmp_path / "gh.log"
        repo = tmp_path / "repo"
        repo.mkdir()
        init_git_identity(repo)
        git_command(repo, "config", "commit.gpgsign", "false")
        (repo / INSTRUCTION_CLAUDE).write_text("current\n", encoding="utf-8")
        (repo / INSTRUCTION_AGENTS).write_text("current\n", encoding="utf-8")
        git_command(repo, "add", ".")
        git_command(repo, "commit", "-m", "seed instruction files")
        output = run_refresh_pr_step(repo, gh_log)
        assert output == "Root instruction blocks are current.\n"
        assert not gh_log.exists()


def assert_refresh_pr_step_stages_obsolete_deletions() -> None:
    """Assert refresh automation commits retired nested instruction deletions."""
    with tempfile.TemporaryDirectory() as directory:
        tmp_path = pathlib.Path(directory).resolve()
        remote = tmp_path / "remote.git"
        repo = tmp_path / "repo"
        gh_log = tmp_path / "gh.log"
        git_command(tmp_path, "init", "--bare", str(remote))
        git_command(tmp_path, "clone", str(remote), str(repo))
        git_command(repo, "config", "user.name", "Test User")
        git_command(repo, "config", "user.email", "test@example.com")
        git_command(repo, "config", "commit.gpgsign", "false")
        spx_dir = repo / "spx"
        spx_dir.mkdir()
        for path in (
            repo / INSTRUCTION_CLAUDE,
            repo / INSTRUCTION_AGENTS,
            spx_dir / INSTRUCTION_CLAUDE,
            spx_dir / INSTRUCTION_AGENTS,
        ):
            path.write_text(f"{path.name}\n", encoding="utf-8")
        git_command(repo, "add", ".")
        git_command(repo, "commit", "-m", "seed instruction files")
        git_command(repo, "branch", "-M", "main")
        git_command(repo, "push", "-u", "origin", "main")
        (repo / INSTRUCTION_CLAUDE).write_text("updated\n", encoding="utf-8")
        (repo / INSTRUCTION_AGENTS).write_text("updated\n", encoding="utf-8")
        (spx_dir / INSTRUCTION_CLAUDE).unlink()
        (spx_dir / INSTRUCTION_AGENTS).unlink()
        run_refresh_pr_step(repo, gh_log)
        committed = git_command(
            repo,
            "show",
            "--name-status",
            "--format=%s",
            "automation/refresh-instruction-blocks",
        ).stdout
        assert "Refresh root instruction blocks" in committed
        assert f"M\t{INSTRUCTION_CLAUDE}" in committed
        assert f"M\t{INSTRUCTION_AGENTS}" in committed
        assert f"D\tspx/{INSTRUCTION_CLAUDE}" in committed
        assert f"D\tspx/{INSTRUCTION_AGENTS}" in committed
        gh_calls = gh_log.read_text(encoding="utf-8")
        assert "pr list" in gh_calls
        assert "pr create" in gh_calls


def assert_regenerate_overwrites_router_drift() -> None:
    """Assert regeneration overwrites a stale router version."""
    with tempfile.TemporaryDirectory() as directory:
        tmp_path = pathlib.Path(directory).resolve()
        module = load_instruction_block_module()
        repo = tmp_path / "repo"
        repo.mkdir()
        template = write_current_template(tmp_path)
        run_generator_write_primary(repo, template)
        claude = repo / INSTRUCTION_CLAUDE
        claude.write_text(
            claude.read_text(encoding="utf-8").replace(f"v{NEW_VERSION}", "v0.0.1"),
            encoding="utf-8",
        )
        run_generator_write_primary(repo, template)
        assert module.parse_instruction_version(claude.read_text(encoding="utf-8")) == (
            NEW_VERSION
        )


def assert_refresh_workflow_regenerates_and_opens_pr() -> None:
    """Assert refresh workflow dispatch regenerates before opening a drift PR."""
    workflow = dist.REPO_ROOT.joinpath(dist.REFRESH_WORKFLOW_PATH).read_text(
        encoding="utf-8"
    )
    assert dist.WORKFLOW_DISPATCH_TRIGGER in workflow
    assert dist.WORKFLOW_BUILD_INSTRUCTIONS_COMMAND in workflow_run_block(
        dist.WORKFLOW_REGENERATE_STEP
    )
    assert dist.WORKFLOW_DRIFT_COMMAND in workflow_step_block(
        dist.WORKFLOW_OPEN_PR_STEP
    )


def assert_refresh_workflow_checks_out_main() -> None:
    """Assert refresh automation starts from the default branch."""
    assert dist.DEFAULT_BRANCH in workflow_step_block(dist.WORKFLOW_CHECKOUT_STEP)


def assert_refresh_workflow_verifies_just_download() -> None:
    """Assert refresh automation verifies its pinned just download."""
    install = workflow_run_block(dist.WORKFLOW_INSTALL_JUST_STEP)
    just_sha256 = workflow_env_value(dist.WORKFLOW_JUST_CHECKSUM_ENV)
    assert len(just_sha256) == 64
    assert dist.WORKFLOW_JUST_CHECKSUM_REFERENCE in install
    assert "mktemp -d" in install
    assert "trap " in install
    assert "rm -rf" in install
    assert install.index("sha256sum -c") < install.index("install -m 0755")
    assert "-o just.tar.gz" not in install
    assert "tar -xzf just.tar.gz" not in install


def assert_refresh_workflow_installs_dprint() -> None:
    """Assert refresh automation installs and verifies its pinned formatter."""
    install = workflow_run_block(dist.WORKFLOW_INSTALL_DPRINT_STEP)
    dprint_version = workflow_env_value(dist.WORKFLOW_DPRINT_VERSION_ENV)
    assert dprint_version
    assert dist.WORKFLOW_DPRINT_INSTALL_COMMAND in install
    assert dist.WORKFLOW_DPRINT_VERSION_COMMAND in install


def assert_render_preserves_brace_token() -> None:
    """Assert rendering preserves ordinary brace-delimited illustrations."""
    module = load_instruction_block_module()
    rendered = module.render(
        build_template(NEW_VERSION),
        (LANG_PRIMARY,),
        NEW_VERSION,
        HARNESS_CLAUDE,
    )
    assert ILLUSTRATION_TOKEN in rendered


def assert_former_command_slot_fence_is_ordinary_content() -> None:
    """Assert retired command-slot fences remain unmanaged root content."""
    with tempfile.TemporaryDirectory() as directory:
        tmp_path = pathlib.Path(directory).resolve()
        module = load_instruction_block_module()
        repo = tmp_path / "repo"
        repo.mkdir()
        slot_fence = (
            "<!-- SPEC-TREE:author -->\n\nproduct author command\n\n"
            "<!-- /SPEC-TREE:author -->\n"
        )
        for name in (INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS):
            (repo / name).write_text(slot_fence, encoding="utf-8")
        run_generator_write_primary(repo, write_current_template(tmp_path))
        result = (repo / INSTRUCTION_CLAUDE).read_text(encoding="utf-8")
        assert "product author command" in result
        assert set(module.parse_shared_regions(result)) == {SHARED_REGION_NAME}


def assert_reconcile_replaces_losing_region_whole() -> None:
    """Assert shared-region reconciliation takes one complete side."""
    module = load_instruction_block_module()
    open_marker = module.shared_open_marker(SHARED_REGION_NAME)
    close_marker = module.shared_close_marker(SHARED_REGION_NAME)
    doc_a = f"{open_marker}\n\n{SHARED_REGION_BODY}\n\n{close_marker}\n"
    doc_b = f"{open_marker}\n\n{SHARED_REGION_BODY_ALT}\n\n{close_marker}\n"
    _, new_b = module.reconcile_shared_regions(doc_a, doc_b, "a")
    reconciled = module.parse_shared_regions(new_b)[SHARED_REGION_NAME]
    assert reconciled == SHARED_REGION_BODY
    assert SHARED_REGION_BODY_ALT not in reconciled


def assert_rendered_router_omits_retired_session_tokens() -> None:
    """Assert legacy session result fields never render into the router."""
    for document in render_shipped_dist_with_generation_entrypoint().values():
        assert SESSION_ARCHIVE_RESULT_INSTRUCTION not in document
        assert SESSION_RESULT_FRONTMATTER_FIELD not in document


def assert_unresolved_build_macro_is_rejected() -> None:
    """Assert production rendering rejects an unresolved build macro."""
    module = load_instruction_block_module()
    harness_templates = {
        agent_harness: build_template(NEW_VERSION)
        for agent_harness in module.AGENT_HARNESS_INSTRUCTION_FILENAMES
    }
    harness_templates[HARNESS_CODEX] += render_build_macro()
    with pytest.raises(dist.UnresolvedInstructionTemplateError):
        dist.render_instruction_blocks_from_harness_templates(
            module, harness_templates, (LANG_PRIMARY,)
        )


def assert_obsolete_spx_instruction_files_are_removed() -> None:
    """Assert generation removes retired nested instruction files."""
    with tempfile.TemporaryDirectory() as directory:
        tmp_path = pathlib.Path(directory).resolve()
        repo = tmp_path / "repo"
        repo.mkdir()
        spx_dir = repo / "spx"
        spx_dir.mkdir()
        for name in INSTRUCTION_CLAUDE, INSTRUCTION_AGENTS:
            (spx_dir / name).write_text(
                "retired spx instruction file\n", encoding="utf-8"
            )
        run_generator_write_primary(repo, write_current_template(tmp_path))
        assert not (spx_dir / INSTRUCTION_CLAUDE).exists()
        assert not (spx_dir / INSTRUCTION_AGENTS).exists()


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
    workflow = REPO_ROOT.joinpath(dist.REFRESH_WORKFLOW_PATH).read_text(
        encoding="utf-8"
    )
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
    workflow = REPO_ROOT.joinpath(dist.REFRESH_WORKFLOW_PATH).read_text(
        encoding="utf-8"
    )
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
    workflow = REPO_ROOT.joinpath(dist.REFRESH_WORKFLOW_PATH).read_text(
        encoding="utf-8"
    )
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
            workflow_run_block(dist.WORKFLOW_OPEN_PR_STEP),
        ],
        cwd=repo_root,
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout
