"""Actionable Spec Tree root-instruction-block writer and drift reporter for the validation gate.

The ``just build-instructions`` recipe and the ``just instructions-check`` gate run this
module to enforce the render-model ADR's gate: regenerate the managed Spec Tree instruction
blocks in root ``CLAUDE.md`` and ``AGENTS.md`` from the rendered harness templates committed
under ``dist/``, remove retired ``spx/`` instruction files, then fail when any root
instruction file drifts from its committed content. It is the instruction-block analogue of
``dist-diff``: authored templates first become harness-specific plugin output, then the root
instruction blocks render from that output.

A root instruction file absent from the index — a first run, or a worktree where the files
were never committed — registers as drift via ``--intent-to-add``, because a plain
``git diff`` reports only tracked changes and would otherwise pass silently while
leaving the freshly written files uncommitted.
"""

from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final, Protocol, cast

from outcomeeng.distribution.contracts import (
    DIST_DIR_NAME,
    RUNTIME_TOKEN_CLOSE_AGENT_NAMES,
    RUNTIME_TOKEN_SPAWN_AGENT_NAMES,
    RUNTIME_TOKEN_WAIT_AGENT_NAMES,
    Target,
)

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
GENERATOR_RELATIVE_PATH: Final = Path(
    "src/plugins/spec-tree/skills/update-instruction-block/scripts/instruction_block.py"
)
GENERATOR_PATH: Final = REPO_ROOT / GENERATOR_RELATIVE_PATH
AUTHORED_TEMPLATE_RELATIVE_PATH: Final = Path(
    "src/plugins/spec-tree/skills/update-instruction-block/templates/instruction-block.md"
)
AUTHORED_TEMPLATE_PATH: Final = REPO_ROOT / AUTHORED_TEMPLATE_RELATIVE_PATH
DIST_TEMPLATE_RELATIVE_PATH: Final = Path(
    "spec-tree/skills/update-instruction-block/templates/instruction-block.md"
)
HEADER: Final = "root instruction blocks differ from a fresh render."
REMEDIATION: Final = "Run `just build-instructions` and commit the regenerated root CLAUDE.md and AGENTS.md."
SHARED_DRIFT_HEADER: Final = "root instruction blocks carry a shared region that diverges or is present in only one file."
SHARED_DRIFT_REMEDIATION: Final = (
    "Reconcile the shared region with `/update-instruction-block`, which takes the "
    "git-more-recent side, then commit the reconciled root CLAUDE.md and AGENTS.md."
)
FORBIDDEN_ROUTER_TOKENS: Final = (
    "Before archiving a claimed session",
    "`result`",
)
BUILD_INSTRUCTIONS_RECIPE: Final = "build-instructions"
INSTRUCTIONS_CHECK_RECIPE: Final = "instructions-check"
WRITE_FLAG: Final = "--write"
JUSTFILE_NAME: Final = "justfile"
MODULE_INVOCATION: Final = "outcomeeng.distribution.instruction_block"
LEFTHOOK_PATH: Final = Path("lefthook.yml")
PRECOMMIT_BUILD_INSTRUCTIONS_COMMAND: Final = "run: just build-instructions"
LEGACY_DIRECT_TEMPLATE_ARGUMENT: Final = "--template src/plugins"
LEGACY_DIRECT_REPO_ROOT_ARGUMENT: Final = "--repo-root ."
# Each *_POLICY_REQUIREMENTS tuple below asserts literal substrings of one authored
# template section in
# src/plugins/spec-tree/skills/update-instruction-block/templates/instruction-block.md.
# Rewording a pinned section without updating its tuple in the same change fails the
# render with a named missing requirement rather than a readable wording diff.
FOUNDATION_POLICY_HEADING: Final = "### Before product-content access -> `/understand`"
FOUNDATION_POLICY_REQUIREMENTS: Final = (
    ("live foundation marker", "live `<SPEC_TREE_FOUNDATION>` marker"),
    ("spx path trigger", "anything under `spx/`"),
    ("source and test trigger", "source or test file"),
    ("session exemption", "`spx session` operations"),
    ("session inspection exemption", "inspection"),
    ("session archive exemption", "archive"),
    ("session release exemption", "release"),
    ("worktree-status exemption", "`spx worktree status`"),
    ("diagnose exemption", "`spx diagnose`"),
    ("no-patch Git exemption", "no-patch Git status, history, and topology"),
    ("product-path follow guard", "Never follow paths from their output"),
)
AUTHORITY_HIERARCHY_POLICY_HEADING: Final = "## Authority Hierarchy"
AUTHORITY_HIERARCHY_POLICY_REQUIREMENTS: Final = (
    (
        "strong skill authority warning",
        "BELOW THE OPERATOR, SKILLS ARE THE TOP-LEVEL AUTHORITY",
    ),
    ("central skill management", "SKILLS ARE CENTRALLY MANAGED AND CURRENT"),
    ("repository staleness", "REPOSITORY CONTENT GOES STALE"),
    (
        "authority order",
        "active skills → repository decisions and specs → tests → code",
    ),
    (
        "skill conflict precedence",
        "When repository content conflicts with an active skill, the skill wins",
    ),
    (
        "higher-layer preservation",
        "NEVER** weaken a higher layer to match a lower layer",
    ),
    (
        "code reference prohibition",
        "NEVER** reference Spec Tree specs or decisions from code comments or docstrings",
    ),
    (
        "repo overlay selection",
        "active skill load the matching `spx/local/*.md` overlay when that skill declares one",
    ),
    (
        "repo overlay authority boundary",
        "below the skill in authority and cannot replace, weaken, or contradict the skill",
    ),
    (
        "nested harness guide",
        "read the active harness guide in every directory before working there when the guide exists",
    ),
    ("Claude guide filename", "`CLAUDE.md` for Claude Code"),
    ("Codex guide filename", "`AGENTS.md` for Codex"),
    (
        "dangerous-command guard stop trigger",
        "a dangerous-command guard (DCG) block terminates the attempted command family",
    ),
    (
        "dangerous-command guard retry prohibition",
        "NEVER** retry it by reformulating, splitting, rewriting, removing the flagged clause, or substituting an equivalent command to evade the guard",
    ),
    (
        "dangerous-command guard sanctioned path",
        "follow the active skills, repository instructions, and declared overlays to find a sanctioned operation",
    ),
    (
        "dangerous-command guard terminal report",
        "report the blocked command with secrets redacted",
    ),
)
WAIT_FOR_LOAD_STOP_TRIGGER: Final = (
    "🛑 **STOP TRIGGER — Before any test, eval, build, or validation command, "
    "ALWAYS invoke `/wait-for-load`.**"
)
WAIT_FOR_LOAD_POLICY_HEADING: Final = (
    "### Before tests, evals, builds, or validation -> `/wait-for-load`"
)
WAIT_FOR_LOAD_READY_REQUIREMENT: Final = (
    "**ALWAYS** wait for `ready: true`, then run the selected command unchanged."
)
WAIT_FOR_LOAD_SCOPE_REQUIREMENT: Final = "**NEVER** use host load to reduce scope, workers, limits, deadlines, or verification."
WAIT_FOR_LOAD_POLICY_REQUIREMENTS: Final = (
    ("stop trigger", WAIT_FOR_LOAD_STOP_TRIGGER),
    ("ready command", WAIT_FOR_LOAD_READY_REQUIREMENT),
    ("scope preservation", WAIT_FOR_LOAD_SCOPE_REQUIREMENT),
)


@dataclass(frozen=True)
class WaitForLoadContradiction:
    """A prohibited host-load directive and a representative router violation."""

    name: str
    pattern: re.Pattern[str]
    violating_directive: str


WAIT_FOR_LOAD_POLICY_CONTRADICTIONS: Final = (
    WaitForLoadContradiction(
        name="host-load verification reduction",
        pattern=re.compile(
            r"^(?!.*\b(?:never|do not|don't|must not|may not|should not|cannot|can't)\b)"
            r"(?=.*\b(?:(?:host|system|high)\s+load(?:\s+average)?|load\s+average)\b)"
            r"(?=.*\b(?:reduce|lower|decrease|cut|narrow|shorten|skip|omit|throttle|cap|fewer)\b)"
            r"(?=.*\b(?:scope|workers?|limits?|deadlines?|verification|tests?|evals?|builds?|validation)\b).*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        violating_directive=(
            "When host load is high, reduce test scope and use fewer workers."
        ),
    ),
)
CODEX_HARNESS: Final = "codex"
WAIT_FOR_LOAD_CODEX_POLICY_REQUIREMENTS: Final = (
    (
        "standalone waiter call",
        "Invoke `/wait-for-load` in its own top-level `functions.exec` call.",
    ),
    (
        "visible ready result",
        "top-level call visibly returns the terminal JSON with `ready: true`",
    ),
    (
        "separate selected-command call",
        "Start the selected command in a separate top-level `functions.exec` call.",
    ),
    (
        "nested waiter yield containment",
        "set a nested `exec_command` yield below the outer call's yield window",
    ),
    (
        "nested waiter collection",
        "preserve that exact id and collect the same waiter with `write_stdin`",
    ),
    (
        "collector yield containment",
        "outer yield window exceeds the nested `write_stdin` yield",
    ),
    (
        "owned process lifecycle",
        "Every nested `exec_command` that returns a `session_id` creates an owned process handle.",
    ),
    (
        "owned process reconciliation",
        "reconcile every known handle before another process sequence, an operator question, merge or publication, or turn end",
    ),
    (
        "abandoned process termination",
        "interrupt that process and collect its terminal result",
    ),
    (
        "dangling process prohibition",
        "never permits leaving its background terminal dangling",
    ),
    (
        "combined-script and nested-wait prohibition",
        "**NEVER** place the waiter and selected command in the same "
        "`functions.exec` script or use `functions.wait` as the planned collector "
        "for a nested waiter or selected command.",
    ),
)
ROUTER_POLICY_NAMES: Final = (
    "operator-question-interrupt",
    "codex-verifier-dispatch",
    "codex-deferred-agent-discovery",
    "subagent-dispatch",
)
SUBAGENT_DISPATCH_POLICY_HEADING: Final = "### Sub-agent dispatch"
SUBAGENT_DISPATCH_POLICY_REQUIREMENTS: Final = (
    ("named-role pre-authorization", "roles this router names are pre-authorized"),
    ("standing request", "treat this section as that standing request"),
    ("role-resemblance boundary", "never a role resemblance"),
    ("no confirmation prompt", "**NEVER** ask the operator to confirm dispatching one"),
    ("confirmation evasions", "not once per session"),
    (
        "structured-question evasion",
        "never as a structured-question option set",
    ),
    (
        "harness prompt ownership",
        "harness permission prompt is the operator's to answer",
    ),
    (
        "unnamed-role prohibition",
        "**NEVER** dispatch a sub-agent this router does not name",
    ),
    (
        "main-conversation verification prohibition",
        "**NEVER** run a verification skill — audit or review — in the main conversation",
    ),
    ("blocked-gate fallback", "**ALWAYS** treat the gate as blocked"),
)
OPERATOR_QUESTION_POLICY_OPEN: Final = "<operator_question_interrupt>"
OPERATOR_QUESTION_POLICY_CLOSE: Final = "</operator_question_interrupt>"
OPERATOR_QUESTION_REQUIREMENTS: Final = (
    (
        "mutation privilege revocation",
        "immediately relinquish all privileges to modify the current product or any external file, service, or resource",
    ),
    ("immediate answer", "Answer the question immediately"),
    (
        "non-verification process stop",
        "ALWAYS: stop any running non-verification process that is destructive or modifies files, external resources, or state",
    ),
    (
        "verification process preservation",
        "NEVER: stop a running verification process — including agentic verification, tests, or evals — unless the operator explicitly instructs that process to stop",
    ),
)
OPERATOR_QUESTION_CONTRADICTIONS: Final = (
    (
        "unqualified state-changing process stop",
        "ALWAYS: stop any running process that is destructive or modifies files, external resources, or state",
    ),
)
CODEX_VERIFIER_DISPATCH_POLICY_ANCHOR: Final = (
    "**Already-dispatched verifier boundary.**"
)
CODEX_VERIFIER_DISPATCH_REQUIREMENTS: Final = (
    ("boundary heading", "Already-dispatched verifier boundary"),
    ("main-conversation scope", "only in the main authoring conversation"),
    ("existing isolation", "treat the current context as the required isolation"),
    ("direct methodology", "execute the configured audit or review skill directly"),
    ("no nested verifier", "NEVER search for or spawn another verifier"),
    ("no tool discovery", "`tool_search`"),
    ("no agent CLI", "`codex exec`"),
    ("missing nested tools expected", "Missing nested-verifier tools is expected"),
)


@dataclass(frozen=True)
class VerifierDispatchContradiction:
    """A prohibited positive directive and a representative router violation."""

    name: str
    pattern: re.Pattern[str]
    violating_directive: str


CODEX_VERIFIER_DISPATCH_CONTRADICTIONS: Final = (
    VerifierDispatchContradiction(
        name="recursive verifier spawn",
        pattern=re.compile(
            r"^.*already-dispatched verifier.*\b(?:must|may|should|can)\s+"
            r"(?!(?:not|never)\b).*spawn another verifier",
            re.IGNORECASE | re.MULTILINE,
        ),
        violating_directive=(
            "Although nested tools are not obvious, an already-dispatched verifier can "
            "spawn another verifier before auditing."
        ),
    ),
    VerifierDispatchContradiction(
        name="nested tool discovery",
        pattern=re.compile(
            r"^.*running as a named verifier.*\b(?:must|may|should|can)\s+"
            r"(?!(?:not|never)\b).*tool_search",
            re.IGNORECASE | re.MULTILINE,
        ),
        violating_directive=(
            "When discovery is not documented, once running as a named verifier, it may "
            "use `tool_search` to discover another verifier."
        ),
    ),
    VerifierDispatchContradiction(
        name="nested agent CLI",
        pattern=re.compile(
            r"^.*verifier context.*\b(?:must|may|should|can)\s+"
            r"(?!(?:not|never)\b).*(?:codex exec|claude|pi)",
            re.IGNORECASE | re.MULTILINE,
        ),
        violating_directive=(
            "If isolation is not obvious, a verifier context may invoke `codex exec` to "
            "create fresh isolation."
        ),
    ),
)
DEFERRED_AGENT_DISCOVERY_POLICY_ANCHOR: Final = "**STOP TRIGGER — in the main authoring conversation, discover deferred agent tools before reporting an agent unavailable.**"
DEFERRED_AGENT_DISCOVERY_POLICY_REQUIREMENTS: Final = (
    ("stop trigger", DEFERRED_AGENT_DISCOVERY_POLICY_ANCHOR),
    ("complete registry", "complete deferred-tool registry"),
    ("top-level registry capability", "top-level `functions.exec`"),
    ("deferred registry", "inspect `ALL_TOOLS`"),
    ("nested shell distinction", "Treat `exec_command` as the nested shell tool"),
    (
        "typed spawn schema",
        f"typed `{RUNTIME_TOKEN_SPAWN_AGENT_NAMES[Target.CODEX.value]}`",
    ),
    ("available roles", "`Available roles`"),
    ("exact role authority", "exact match proves availability"),
    (
        "unavailability boundary",
        "Report unavailable only when discovery finds no typed spawn capability or omits the exact role",
    ),
    ("discovery result", "include that result"),
    (
        "insufficient surfaces",
        "Visible catalogs, initial tools, generated rosters, and local `agents/*.md` files are not availability evidence",
    ),
)
DEFERRED_AGENT_DISCOVERY_LIFECYCLE_REQUIREMENTS: Final = (
    (
        "lifecycle discovery",
        f"if `{RUNTIME_TOKEN_SPAWN_AGENT_NAMES[Target.CODEX.value]}`, "
        f"`{RUNTIME_TOKEN_WAIT_AGENT_NAMES[Target.CODEX.value]}`, or "
        f"`{RUNTIME_TOKEN_CLOSE_AGENT_NAMES[Target.CODEX.value]}` is not initially "
        "exposed, discover it through the runtime's complete deferred-tool registry",
    ),
)


@dataclass(frozen=True)
class DeferredAgentDiscoveryContradiction:
    """A prohibited availability directive and a representative router violation."""

    name: str
    pattern: re.Pattern[str]
    violating_directive: str


DEFERRED_AGENT_DISCOVERY_POLICY_CONTRADICTIONS: Final = (
    DeferredAgentDiscoveryContradiction(
        name="initial tool list as availability authority",
        pattern=re.compile(
            r"^(?!.*\b(?:never|do not|don't|must not|may not|should not|cannot|can't)\b)"
            r"(?=.*\b(?:initially visible|initial|visible)\b)"
            r"(?=.*\b(?:tool list|tool surface|catalog|roster)\b)"
            r"(?=.*\b(?:sufficient|authoritative|conclusive)\b)"
            r"(?=.*\b(?:availability|available|unavailable)\b).*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        violating_directive=(
            "The initially visible tool list is sufficient evidence that a named agent "
            "is unavailable."
        ),
    ),
    DeferredAgentDiscoveryContradiction(
        name="deferred registry bypass",
        pattern=re.compile(
            r"^(?!.*\b(?:never|do not|don't|must not|may not|should not|cannot|can't)\b)"
            r"(?=.*\breport(?:ed|ing)?\b.*\bunavailable\b)"
            r"(?=.*\bwithout\b.*\bdeferred(?:-tool)?\s+registry\b).*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        violating_directive=(
            "A named agent may be reported unavailable without checking the deferred-tool "
            "registry."
        ),
    ),
    DeferredAgentDiscoveryContradiction(
        name="local agent file as runtime authority",
        pattern=re.compile(
            r"^(?!.*\b(?:never|do not|don't|must not|may not|should not|cannot|can't)\b)"
            r".*\blocal\b.*\bagents?/\*\.md\b.{0,120}"
            r"\b(?:proves?|authoritative|conclusive)\b.{0,120}"
            r"\b(?:active|available|provisioned)\b.*$",
            re.IGNORECASE | re.MULTILINE,
        ),
        violating_directive=(
            "A local `agents/*.md` file proves that the role is active in the current "
            "runtime."
        ),
    ),
)


@dataclass(frozen=True)
class RefreshWorkflowContract:
    """Source-owned selectors and commands for instruction-block refresh workflow checks."""

    relative_path: Path
    dispatch_key: str
    checkout_step: str
    default_branch: str
    install_just_step: str
    just_checksum_env: str
    install_dprint_step: str
    dprint_version_env: str
    regenerate_step: str
    build_commands: tuple[str, ...]
    open_pr_step: str
    drift_probe: str
    automation_branch: str
    commit_subject: str

    def path(self, *, repo_root: Path = REPO_ROOT) -> Path:
        """Return the authored workflow path below ``repo_root``."""
        return repo_root / self.relative_path


REFRESH_WORKFLOW: Final = RefreshWorkflowContract(
    relative_path=Path(".github/workflows/refresh-instruction-blocks.yml"),
    dispatch_key="workflow_dispatch:",
    checkout_step="Checkout",
    default_branch="main",
    install_just_step="Install just",
    just_checksum_env="JUST_SHA256",
    install_dprint_step="Install dprint",
    dprint_version_env="DPRINT_VERSION",
    regenerate_step="Regenerate instruction blocks",
    build_commands=("just build-skills", "just build-instructions"),
    open_pr_step="Open instruction-block refresh pull request",
    drift_probe="git status --porcelain",
    automation_branch="automation/refresh-instruction-blocks",
    commit_subject="Refresh root instruction blocks",
)


class InstructionBlockRenderError(RuntimeError):
    """Base error for instruction-block rendering failures."""


class UnresolvedInstructionTemplateError(InstructionBlockRenderError):
    """Raised when a rendered harness template still contains build macros."""


class FoundationAccessPolicyError(InstructionBlockRenderError):
    """Raised when a rendered router omits part of its foundation access policy."""


class AuthorityHierarchyPolicyError(InstructionBlockRenderError):
    """Raised when a rendered router omits part of its authority hierarchy."""


class WaitForLoadPolicyError(InstructionBlockRenderError):
    """Raised when a rendered router omits or contradicts its load-wait policy."""


class OperatorQuestionPolicyError(InstructionBlockRenderError):
    """Raised when the Codex router weakens or contradicts question-interrupt policy."""


class VerifierDispatchPolicyError(InstructionBlockRenderError):
    """Raised when the Codex router weakens or contradicts verifier dispatch policy."""


class SubagentDispatchPolicyError(InstructionBlockRenderError):
    """A rendered harness router weakens the sub-agent dispatch authorization."""


class DeferredAgentDiscoveryPolicyError(InstructionBlockRenderError):
    """Raised when the Codex router omits deferred typed-agent discovery policy."""


class InstructionBlockModule(Protocol):
    """Subset of the shipped instruction-block generator reused by the product gate."""

    AGENT_HARNESS_INSTRUCTION_FILENAMES: dict[str, str]
    BOOTSTRAP_SHARED_REGION_NAME: str
    LANGUAGE_BY_EXTENSION: dict[str, str]
    OBSOLETE_SPX_INSTRUCTION_FILENAMES: tuple[str, ...]
    ROUTER_BLOCK_END: str
    ROUTER_MARKER_PREFIX: str
    TEMPLATE_VERSION_KEY: str
    UNRESOLVED_BUILD_TEMPLATE_TOKENS: tuple[str, ...]

    def router_block_bounds(self, text: str) -> tuple[int, int] | None: ...

    def parse_template_version(self, text: str) -> str | None: ...

    def assert_no_unresolved_build_macros(self, template_text: str) -> None: ...

    def detect_languages_from_tree(self, spx_dir: Path) -> tuple[str, ...]: ...

    def render(
        self,
        template_text: str,
        languages: tuple[str, ...],
        installed_version: str,
        harness: str,
    ) -> str: ...

    def write_root_instruction_files(
        self, repo_root: Path, blocks_by_harness: Mapping[str, str]
    ) -> None: ...

    def parse_shared_regions(self, text: str) -> dict[str, str]: ...

    def remove_obsolete_spx_instruction_files(self, repo_root: Path) -> None: ...

    def shared_region_drift(self, repo_root: Path) -> tuple[str, ...]: ...


def _run(
    args: Sequence[str], *, cwd: Path = REPO_ROOT
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(args), cwd=cwd, capture_output=True, text=True, check=True
    )


def load_instruction_block_module() -> InstructionBlockModule:
    """Load the shipped instruction-block generator to reuse its pure render contract."""
    cached = sys.modules.get("instruction_block")
    if cached is not None:
        return cast(InstructionBlockModule, cached)
    spec = importlib.util.spec_from_file_location("instruction_block", GENERATOR_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load instruction_block from {GENERATOR_PATH}")
    module = importlib.util.module_from_spec(spec)
    # Register before exec so dataclass type introspection can resolve the module by name.
    sys.modules["instruction_block"] = module
    spec.loader.exec_module(module)
    return cast(InstructionBlockModule, module)


def instruction_paths(module: InstructionBlockModule | None = None) -> tuple[str, ...]:
    """Derive instruction-file paths from the generator's own enumeration."""
    instruction_module = module or load_instruction_block_module()
    return (
        *root_instruction_paths(instruction_module),
        *obsolete_spx_instruction_paths(instruction_module),
    )


def root_instruction_paths(
    module: InstructionBlockModule | None = None,
) -> tuple[str, ...]:
    """Return generated root instruction-file paths."""
    instruction_module = module or load_instruction_block_module()
    return tuple(instruction_module.AGENT_HARNESS_INSTRUCTION_FILENAMES.values())


def obsolete_spx_instruction_paths(
    module: InstructionBlockModule | None = None,
) -> tuple[str, ...]:
    """Return retired spx instruction-file paths that may still be tracked."""
    instruction_module = module or load_instruction_block_module()
    return tuple(
        f"spx/{name}" for name in instruction_module.OBSOLETE_SPX_INSTRUCTION_FILENAMES
    )


def dist_template_path(harness: str, *, repo_root: Path = REPO_ROOT) -> Path:
    """Return the rendered harness template path for one instruction-block harness."""
    return repo_root / DIST_DIR_NAME / harness / DIST_TEMPLATE_RELATIVE_PATH


def load_harness_templates(
    module: InstructionBlockModule | None = None, *, repo_root: Path = REPO_ROOT
) -> dict[str, str]:
    """Read rendered harness templates from ``dist/`` for every instruction-block harness."""
    instruction_module = module or load_instruction_block_module()
    templates: dict[str, str] = {}
    for harness in instruction_module.AGENT_HARNESS_INSTRUCTION_FILENAMES:
        path = dist_template_path(harness, repo_root=repo_root)
        templates[harness] = path.read_text(encoding="utf-8")
    return templates


def assert_no_unresolved_build_macros(text: str, *, path: Path | str) -> None:
    """Reject dist templates that still contain build-time macro delimiters."""
    module = load_instruction_block_module()
    try:
        module.assert_no_unresolved_build_macros(text)
    except ValueError as exc:
        raise UnresolvedInstructionTemplateError(
            f"{path}: {exc}; run `just build-skills` before regenerating instruction blocks"
        ) from exc


def render_instruction_blocks_from_harness_templates(
    module: InstructionBlockModule,
    harness_templates: Mapping[str, str],
    languages: tuple[str, ...],
    *,
    template_paths: Mapping[str, Path | str] | None = None,
) -> dict[str, str]:
    """Render every root instruction block from its harness-specific dist template."""
    versions: dict[str, str] = {}
    for harness, template_text in harness_templates.items():
        path = (
            template_paths[harness]
            if template_paths is not None and harness in template_paths
            else harness
        )
        assert_no_unresolved_build_macros(template_text, path=path)
        version = module.parse_template_version(template_text)
        if version is None:
            raise InstructionBlockRenderError(f"{path} has no template_version")
        versions[harness] = version

    if len(set(versions.values())) != 1:
        details = ", ".join(
            f"{harness}={version}" for harness, version in sorted(versions.items())
        )
        raise InstructionBlockRenderError(
            f"harness instruction-block templates disagree on version: {details}"
        )

    return {
        harness: module.render(
            harness_templates[harness], languages, versions[harness], harness
        )
        for harness in module.AGENT_HARNESS_INSTRUCTION_FILENAMES
    }


def _markdown_section(document: str, heading: str) -> str:
    """Return the exact Markdown section beginning at ``heading``."""
    lines = document.splitlines()
    try:
        start = lines.index(heading)
    except ValueError as exc:
        raise FoundationAccessPolicyError(f"missing router section: {heading}") from exc
    heading_level = len(heading) - len(heading.lstrip("#"))
    end = len(lines)
    for index, line in enumerate(lines[start + 1 :], start=start + 1):
        if line.startswith("#") and len(line) - len(line.lstrip("#")) <= heading_level:
            end = index
            break
    return "\n".join(lines[start:end])


def managed_router_block(document: str) -> str:
    """Extract the managed router block from a complete root instruction document."""
    module = load_instruction_block_module()
    bounds = module.router_block_bounds(document)
    if bounds is None:
        raise FoundationAccessPolicyError("missing complete standalone router block")
    start, end = bounds
    return document[start:end]


def validate_foundation_access_policy(
    blocks_by_harness: Mapping[str, str],
) -> None:
    """Reject a rendered harness router that weakens the product-content gate."""
    for harness, document in blocks_by_harness.items():
        router = managed_router_block(document)
        section = _markdown_section(router, FOUNDATION_POLICY_HEADING)
        missing = [
            name
            for name, required_text in FOUNDATION_POLICY_REQUIREMENTS
            if required_text not in section
        ]
        if missing:
            details = ", ".join(missing)
            raise FoundationAccessPolicyError(
                f"{harness} router foundation policy is incomplete: {details}"
            )
        forbidden = [token for token in FORBIDDEN_ROUTER_TOKENS if token in router]
        if forbidden:
            details = ", ".join(repr(token) for token in forbidden)
            raise FoundationAccessPolicyError(
                f"{harness} router contains forbidden session-result tokens: {details}"
            )


def validate_authority_hierarchy_policy(
    blocks_by_harness: Mapping[str, str],
) -> None:
    """Reject a rendered harness router with an incomplete authority hierarchy."""
    for harness, document in blocks_by_harness.items():
        router = managed_router_block(document)
        try:
            section = _markdown_section(router, AUTHORITY_HIERARCHY_POLICY_HEADING)
        except FoundationAccessPolicyError as exc:
            raise AuthorityHierarchyPolicyError(
                f"missing router section: {AUTHORITY_HIERARCHY_POLICY_HEADING}"
            ) from exc
        missing = [
            name
            for name, required_text in AUTHORITY_HIERARCHY_POLICY_REQUIREMENTS
            if required_text not in section
        ]
        if missing:
            details = ", ".join(missing)
            raise AuthorityHierarchyPolicyError(
                f"{harness} router authority hierarchy is incomplete: {details}"
            )


def subagent_dispatch_policy_section(router: str) -> str | None:
    """Return the sub-agent dispatch section from a complete router."""
    try:
        return _markdown_section(router, SUBAGENT_DISPATCH_POLICY_HEADING)
    except FoundationAccessPolicyError:
        return None


def validate_subagent_dispatch_policy(blocks_by_harness: Mapping[str, str]) -> None:
    """Reject a rendered harness router missing the sub-agent dispatch authorization.

    Every harness router carries the section, because a harness whose router omits
    it withholds sub-agent use at every gate until the operator is asked.
    """
    for harness, document in blocks_by_harness.items():
        router = managed_router_block(document)
        try:
            section = _markdown_section(router, SUBAGENT_DISPATCH_POLICY_HEADING)
        except FoundationAccessPolicyError as exc:
            raise SubagentDispatchPolicyError(
                f"missing router section: {SUBAGENT_DISPATCH_POLICY_HEADING}"
            ) from exc
        missing = [
            name
            for name, required_text in SUBAGENT_DISPATCH_POLICY_REQUIREMENTS
            if required_text not in section
        ]
        if missing:
            details = ", ".join(missing)
            raise SubagentDispatchPolicyError(
                f"{harness} router sub-agent dispatch authorization is incomplete: {details}"
            )


def validate_wait_for_load_policy(blocks_by_harness: Mapping[str, str]) -> None:
    """Reject a rendered harness router that weakens the load-wait policy."""
    for harness, document in blocks_by_harness.items():
        router = managed_router_block(document)
        try:
            section = _markdown_section(router, WAIT_FOR_LOAD_POLICY_HEADING)
        except FoundationAccessPolicyError as exc:
            raise WaitForLoadPolicyError(
                f"missing router section: {WAIT_FOR_LOAD_POLICY_HEADING}"
            ) from exc
        requirements = list(WAIT_FOR_LOAD_POLICY_REQUIREMENTS)
        if harness == CODEX_HARNESS:
            requirements.extend(WAIT_FOR_LOAD_CODEX_POLICY_REQUIREMENTS)
        missing = [
            name for name, required_text in requirements if required_text not in section
        ]
        if missing:
            details = ", ".join(missing)
            raise WaitForLoadPolicyError(
                f"{harness} router wait-for-load policy is incomplete: {details}"
            )
        contradictions = [
            rule.name
            for rule in WAIT_FOR_LOAD_POLICY_CONTRADICTIONS
            if rule.pattern.search(router)
        ]
        if contradictions:
            details = ", ".join(contradictions)
            raise WaitForLoadPolicyError(
                f"{harness} router wait-for-load policy is contradictory: {details}"
            )


def operator_question_policy_block(router: str) -> str | None:
    """Return the operator-question policy block from a complete router."""
    start = router.find(OPERATOR_QUESTION_POLICY_OPEN)
    if start == -1:
        return None
    end = router.find(OPERATOR_QUESTION_POLICY_CLOSE, start)
    if end == -1:
        return None
    return router[start : end + len(OPERATOR_QUESTION_POLICY_CLOSE)]


def validate_operator_question_policy(
    blocks_by_harness: Mapping[str, str],
) -> None:
    """Reject a router that omits or contradicts question-interrupt policy."""
    if not blocks_by_harness:
        raise OperatorQuestionPolicyError("missing router")
    for harness, document in blocks_by_harness.items():
        router = managed_router_block(document)
        policy = operator_question_policy_block(router) or ""
        missing = [
            name
            for name, required_text in OPERATOR_QUESTION_REQUIREMENTS
            if required_text not in policy
        ]
        if missing:
            details = ", ".join(missing)
            raise OperatorQuestionPolicyError(
                f"{harness} operator-question policy is incomplete: {details}"
            )
        contradictions = [
            name
            for name, forbidden_text in OPERATOR_QUESTION_CONTRADICTIONS
            if forbidden_text in policy
        ]
        if contradictions:
            details = ", ".join(contradictions)
            raise OperatorQuestionPolicyError(
                f"{harness} operator-question policy is contradictory: {details}"
            )


def verifier_dispatch_policy_paragraph(router: str) -> str | None:
    """Return the Codex verifier-boundary paragraph from a complete router."""
    return next(
        (
            paragraph
            for paragraph in router.split("\n\n")
            if CODEX_VERIFIER_DISPATCH_POLICY_ANCHOR in paragraph
        ),
        None,
    )


def validate_verifier_dispatch_policy(
    blocks_by_harness: Mapping[str, str],
) -> None:
    """Reject a Codex router that omits or contradicts the verifier boundary."""
    document = blocks_by_harness.get(CODEX_HARNESS)
    if document is None:
        raise VerifierDispatchPolicyError("missing Codex router")
    router = managed_router_block(document)
    policy = verifier_dispatch_policy_paragraph(router) or ""
    missing = [
        name
        for name, required_text in CODEX_VERIFIER_DISPATCH_REQUIREMENTS
        if required_text not in policy
    ]
    if missing:
        details = ", ".join(missing)
        raise VerifierDispatchPolicyError(
            f"Codex verifier dispatch policy is incomplete: {details}"
        )
    contradictions = [
        rule.name
        for rule in CODEX_VERIFIER_DISPATCH_CONTRADICTIONS
        if rule.pattern.search(router)
    ]
    if contradictions:
        details = ", ".join(contradictions)
        raise VerifierDispatchPolicyError(
            f"Codex verifier dispatch policy is contradictory: {details}"
        )


def deferred_agent_discovery_policy_paragraph(router: str) -> str | None:
    """Return the Codex deferred-agent discovery heading and body."""
    paragraphs = router.split("\n\n")
    for index, paragraph in enumerate(paragraphs):
        if DEFERRED_AGENT_DISCOVERY_POLICY_ANCHOR not in paragraph:
            continue
        if index + 1 == len(paragraphs):
            return paragraph
        return "\n\n".join(paragraphs[index : index + 2])
    return None


def validate_deferred_agent_discovery_policy(
    blocks_by_harness: Mapping[str, str],
) -> None:
    """Reject a Codex router that omits or contradicts deferred agent discovery."""
    document = blocks_by_harness.get(CODEX_HARNESS)
    if document is None:
        raise DeferredAgentDiscoveryPolicyError("missing Codex router")
    router = managed_router_block(document)
    policy = deferred_agent_discovery_policy_paragraph(router) or ""
    missing_policy = [
        name
        for name, required_text in DEFERRED_AGENT_DISCOVERY_POLICY_REQUIREMENTS
        if required_text not in policy
    ]
    missing_lifecycle = [
        name
        for name, required_text in DEFERRED_AGENT_DISCOVERY_LIFECYCLE_REQUIREMENTS
        if required_text not in router
    ]
    missing = [*missing_policy, *missing_lifecycle]
    if missing:
        details = ", ".join(missing)
        raise DeferredAgentDiscoveryPolicyError(
            f"Codex deferred-agent discovery policy is incomplete: {details}"
        )
    contradictions = [
        rule.name
        for rule in DEFERRED_AGENT_DISCOVERY_POLICY_CONTRADICTIONS
        if rule.pattern.search(router)
    ]
    if contradictions:
        details = ", ".join(contradictions)
        raise DeferredAgentDiscoveryPolicyError(
            f"Codex deferred-agent discovery policy is contradictory: {details}"
        )


def regenerate_instruction_blocks(*, repo_root: Path = REPO_ROOT) -> None:
    """Render both root instruction files in place from committed harness dist templates."""
    module = load_instruction_block_module()
    spx_dir = repo_root / "spx"
    templates = load_harness_templates(module, repo_root=repo_root)
    paths = {
        harness: dist_template_path(harness, repo_root=repo_root)
        for harness in module.AGENT_HARNESS_INSTRUCTION_FILENAMES
    }
    rendered = render_instruction_blocks_from_harness_templates(
        module,
        templates,
        module.detect_languages_from_tree(spx_dir),
        template_paths=paths,
    )
    validate_foundation_access_policy(rendered)
    validate_authority_hierarchy_policy(rendered)
    validate_wait_for_load_policy(rendered)
    validate_operator_question_policy(rendered)
    validate_subagent_dispatch_policy(rendered)
    validate_verifier_dispatch_policy(rendered)
    validate_deferred_agent_discovery_policy(rendered)
    module.write_root_instruction_files(repo_root, rendered)
    module.remove_obsolete_spx_instruction_files(repo_root)


def intent_to_add_paths(
    paths: Sequence[str], *, repo_root: Path = REPO_ROOT
) -> tuple[str, ...]:
    """Return generated instruction-file paths that exist and can be marked intent-to-add."""
    return tuple(path for path in paths if (repo_root / path).exists())


def drifting_instruction_files(
    *, repo_root: Path = REPO_ROOT, module: InstructionBlockModule | None = None
) -> list[str]:
    """Return the root instruction files that drift from their committed content.

    ``--intent-to-add`` makes an absent-from-index file register as drift; a plain
    ``git diff`` reports only tracked changes and would pass silently on a first run.
    Missing root instruction files are drift directly; missing obsolete spx instruction
    files are skipped because only tracked deletion drift matters for retired paths.
    """
    instruction_module = module or load_instruction_block_module()
    root_paths = root_instruction_paths(instruction_module)
    paths = (*root_paths, *obsolete_spx_instruction_paths(instruction_module))
    missing_root_paths = [
        path for path in root_paths if not (repo_root / path).exists()
    ]
    existing_paths = intent_to_add_paths(paths, repo_root=repo_root)
    if existing_paths:
        _run(["git", "add", "--intent-to-add", *existing_paths], cwd=repo_root)
    result = _run(["git", "diff", "--name-only", "--", *paths], cwd=repo_root)
    drift = [line for line in result.stdout.splitlines() if line.strip()]
    return sorted({*missing_root_paths, *drift})


def drifting_shared_regions(
    *, repo_root: Path = REPO_ROOT, module: InstructionBlockModule | None = None
) -> tuple[str, ...]:
    """Return the shared regions that diverge or are present in only one root file.

    A shared region is kept byte-identical across the two files; a body that differs between them,
    or a region present in only one, is drift the deterministic writer leaves unresolved for the
    update skill's git-recency reconcile. Reporting it keeps the gate from passing over a region
    that carries one body for Claude Code and a different one — or none — for Codex.
    """
    instruction_module = module or load_instruction_block_module()
    return instruction_module.shared_region_drift(repo_root)


def render_report(
    drift: Sequence[str],
    shared_drift: Sequence[str] = (),
) -> str:
    """Render the actionable drift report from drifting paths and drifting shared regions."""
    sections: list[str] = []
    if drift:
        sections += [HEADER, "", *(f"  {path}" for path in drift), "", REMEDIATION]
    if shared_drift:
        if sections:
            sections.append("")
        sections += [
            SHARED_DRIFT_HEADER,
            "",
            *(f"  {name}" for name in shared_drift),
            "",
            SHARED_DRIFT_REMEDIATION,
        ]
    return "\n".join(sections)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Regenerate root instruction blocks from rendered dist templates."
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write instruction blocks without checking git drift.",
    )
    args = parser.parse_args(argv)
    try:
        regenerate_instruction_blocks()
        if args.write:
            return 0
        drift = drifting_instruction_files()
        shared_drift = drifting_shared_regions()
    except InstructionBlockRenderError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as exc:
        # Surface the failed command's own diagnostic; captured output is otherwise
        # swallowed by the default traceback, leaving the reporter unactionable.
        sys.stderr.write(exc.stderr or "")
        print(
            f"{HEADER}\n  the root instruction-block gate failed; see the error above."
        )
        return 1
    if not drift and not shared_drift:
        return 0
    print(render_report(drift, shared_drift))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
