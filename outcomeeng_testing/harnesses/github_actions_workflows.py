"""Harnesses for asserting repository GitHub Actions workflow policy."""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Final

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

from outcomeeng_testing.harnesses.ci_gate import workflow_paths

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR: Final = REPO_ROOT / ".github" / "workflows"
RENOVATE_CONFIG: Final = REPO_ROOT / "renovate.json"
SONAR_PROPERTIES: Final = REPO_ROOT / ".sonarcloud.properties"
FULL_SHA_RE: Final = re.compile(r"^[0-9a-f]{40}$")
OUTCOMEENG_GH_ACTIONS_PREFIX: Final = "outcomeeng/gh-actions/"
OUTCOMEENG_GH_ACTIONS_DEP_NAME: Final = "outcomeeng/gh-actions"
BETA_TESTER_MARKER: Final = "# BETA TESTER:"
RENOVATE_ENABLED: Final = "enabled"
RENOVATE_MATCH_DEP_NAMES: Final = "matchDepNames"
RENOVATE_MATCH_FILE_NAMES: Final = "matchFileNames"
RENOVATE_MATCH_MANAGERS: Final = "matchManagers"
RENOVATE_PACKAGE_RULES: Final = "packageRules"
RENOVATE_GITHUB_ACTIONS_MANAGER: Final = "github-actions"
SONAR_EXCLUSIONS: Final = "sonar.exclusions"
UNPINNED_QUOTED_USES_VALUE: Final = "actions/checkout@v4"
QUOTED_USES_KEY_WORKFLOW: Final = f"""
jobs:
  scan:
    steps:
      - "uses": {UNPINNED_QUOTED_USES_VALUE}
"""
BLOCK_SCALAR_USES_TEXT_WORKFLOW: Final = """
jobs:
  scan:
    steps:
      - run: |
          uses: actions/checkout@v4
"""
GENERIC_CLAUDE_WORKFLOW_NAMES: Final = frozenset(
    {
        "claude.yml",
        "claude.yaml",
        "claude-code-review.yml",
        "claude-code-review.yaml",
    }
)


@dataclass(frozen=True)
class ExternalWorkflowUse:
    workflow: Path
    value: str
    ref: str
    marked_beta: bool


@dataclass(frozen=True)
class WorkflowUse:
    value: str
    line_number: int


def active_generic_claude_callers() -> tuple[str, ...]:
    """Return generic Claude caller workflows active in this repository."""
    return tuple(
        workflow.name
        for workflow in _workflow_paths()
        if workflow.name in GENERIC_CLAUDE_WORKFLOW_NAMES
    )


def external_workflow_pin_violations() -> tuple[str, ...]:
    """Return external `uses:` refs that violate the workflow pin policy."""
    return tuple(
        external_use.value
        for external_use in _external_workflow_uses()
        if not _allowed_external_workflow_use(external_use)
    )


def quoted_uses_key_pin_violations() -> tuple[str, ...]:
    """Return pin violations from a workflow with a quoted `uses` key."""
    return _external_workflow_pin_violations_from_text(
        workflow=Path(".github/workflows/quoted-uses.yml"),
        text=QUOTED_USES_KEY_WORKFLOW,
    )


def block_scalar_uses_text_pin_violations() -> tuple[str, ...]:
    """Return pin violations from `uses:` text inside a block scalar."""
    return _external_workflow_pin_violations_from_text(
        workflow=Path(".github/workflows/block-scalar.yml"),
        text=BLOCK_SCALAR_USES_TEXT_WORKFLOW,
    )


def sonar_beta_main_exclusion_violations() -> tuple[str, ...]:
    """Return mismatches between Sonar exclusions and beta `@main` callers."""
    expected = set(_beta_main_workflow_resource_keys())
    actual = _sonar_workflow_exclusion_resource_keys()

    missing = tuple(
        sorted(f"missing:{resource_key}" for resource_key in expected - actual)
    )
    unexpected = tuple(
        sorted(f"unexpected:{resource_key}" for resource_key in actual - expected)
    )
    return (*missing, *unexpected)


def renovate_beta_main_exemption_violations() -> tuple[str, ...]:
    """Return mismatches between Renovate exemptions and beta `@main` callers."""
    expected = set(_beta_main_workflow_resource_keys())
    actual, broad_rules = _renovate_beta_main_exemption_resource_keys()

    broad = tuple(sorted(f"broad:{rule}" for rule in broad_rules))
    missing = tuple(
        sorted(f"missing:{resource_key}" for resource_key in expected - actual)
    )
    unexpected = tuple(
        sorted(f"unexpected:{resource_key}" for resource_key in actual - expected)
    )
    return (*broad, *missing, *unexpected)


def _allowed_external_workflow_use(external_use: ExternalWorkflowUse) -> bool:
    if FULL_SHA_RE.fullmatch(external_use.ref):
        return True

    return (
        external_use.value.startswith(OUTCOMEENG_GH_ACTIONS_PREFIX)
        and external_use.ref == "main"
        and external_use.marked_beta
    )


def _beta_main_workflow_resource_keys() -> Iterator[str]:
    for external_use in _external_workflow_uses():
        if (
            external_use.value.startswith(OUTCOMEENG_GH_ACTIONS_PREFIX)
            and external_use.ref == "main"
            and external_use.marked_beta
        ):
            yield external_use.workflow.relative_to(REPO_ROOT).as_posix()


def _sonar_workflow_exclusion_resource_keys() -> set[str]:
    properties = _read_sonar_properties()
    return {
        resource_key
        for resource_key in _split_sonar_list(properties.get(SONAR_EXCLUSIONS, ""))
        if resource_key.startswith(".github/workflows/")
    }


def _split_sonar_list(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _renovate_beta_main_exemption_resource_keys() -> tuple[set[str], tuple[str, ...]]:
    if not RENOVATE_CONFIG.exists():
        return set(), ()

    config = json.loads(RENOVATE_CONFIG.read_text())
    resource_keys: set[str] = set()
    broad_rules: list[str] = []
    for rule in config.get(RENOVATE_PACKAGE_RULES, []):
        if not _renovate_rule_disables_outcomeeng_gh_actions(rule):
            continue
        file_names = tuple(rule.get(RENOVATE_MATCH_FILE_NAMES, []))
        if not file_names:
            broad_rules.append(rule.get("description", "<unnamed>"))
            continue
        resource_keys.update(file_names)
    return resource_keys, tuple(broad_rules)


def _renovate_rule_disables_outcomeeng_gh_actions(rule: object) -> bool:
    if not isinstance(rule, dict):
        return False

    return (
        rule.get(RENOVATE_ENABLED) is False
        and RENOVATE_GITHUB_ACTIONS_MANAGER in rule.get(RENOVATE_MATCH_MANAGERS, [])
        and OUTCOMEENG_GH_ACTIONS_DEP_NAME in rule.get(RENOVATE_MATCH_DEP_NAMES, [])
    )


def _read_sonar_properties() -> dict[str, str]:
    if not SONAR_PROPERTIES.exists():
        return {}

    properties: dict[str, str] = {}
    logical_lines = SONAR_PROPERTIES.read_text().replace("\\\n", "").splitlines()
    for raw_line in logical_lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", maxsplit=1)
        properties[key.strip()] = value.strip()
    return properties


def _external_workflow_uses() -> Iterator[ExternalWorkflowUse]:
    for workflow in _workflow_paths():
        yield from _external_workflow_uses_from_text(workflow, workflow.read_text())


def _external_workflow_pin_violations_from_text(
    *, workflow: Path, text: str
) -> tuple[str, ...]:
    return tuple(
        external_use.value
        for external_use in _external_workflow_uses_from_text(workflow, text)
        if not _allowed_external_workflow_use(external_use)
    )


def _external_workflow_uses_from_text(
    workflow: Path, text: str
) -> Iterator[ExternalWorkflowUse]:
    lines = text.splitlines()
    for workflow_use in _workflow_uses_from_text(text):
        uses = workflow_use.value.strip().strip("'\"")
        if uses.startswith("./"):
            continue

        _, _, ref = uses.partition("@")
        yield ExternalWorkflowUse(
            workflow=workflow,
            value=uses,
            ref=ref,
            marked_beta=_marked_beta(lines, workflow_use.line_number),
        )


def _workflow_uses_from_text(text: str) -> Iterator[WorkflowUse]:
    root = yaml.compose(text, Loader=yaml.BaseLoader)
    if root is None:
        return

    yield from _workflow_uses_from_node(root)


def _workflow_uses_from_node(node: Node) -> Iterator[WorkflowUse]:
    if isinstance(node, MappingNode):
        for key_node, value_node in node.value:
            if (
                isinstance(key_node, ScalarNode)
                and key_node.value == "uses"
                and isinstance(value_node, ScalarNode)
            ):
                yield WorkflowUse(
                    value=value_node.value,
                    line_number=value_node.start_mark.line,
                )
            yield from _workflow_uses_from_node(value_node)
    elif isinstance(node, SequenceNode):
        for item_node in node.value:
            yield from _workflow_uses_from_node(item_node)


def _marked_beta(lines: list[str], line_number: int) -> bool:
    if BETA_TESTER_MARKER in lines[line_number]:
        return True

    for comment_line in reversed(lines[:line_number]):
        stripped = comment_line.strip()
        if not stripped.startswith("#"):
            return False
        if BETA_TESTER_MARKER in stripped:
            return True
    return False


def _workflow_paths() -> tuple[Path, ...]:
    return workflow_paths(WORKFLOWS_DIR)
