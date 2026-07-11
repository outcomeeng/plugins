"""Harness for audit verification-run contract evidence."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Mapping
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from typing import Final

from outcomeeng.validation.spx_version import (
    REQUIRED_SPX_VERSION,
    is_satisfied,
    read_pinned_version,
)


MINIMUM_VERIFICATION_RUN_SPX_VERSION: Final = "0.6.13"
AUDIT_SUBJECT_PATH: Final = "file.txt"
WORKFLOW_PATH: Final = Path(".github/workflows/check.yml")
PLUGIN_SURFACES: Final = (
    Path("src/plugins"),
    Path("dist/claude"),
    Path("dist/codex"),
)
AUDIT_SKILL_SCRIPT_DIRS: Final = tuple(
    surface / "spec-tree" / "skills" / "audit-implementation" / "scripts"
    for surface in PLUGIN_SURFACES
)
SPEC_TREE_AGENT_DIRS: Final = tuple(
    surface / "spec-tree" / "agents" for surface in PLUGIN_SURFACES
)
RETIRED_IMPLEMENTATION_AUDITOR_PATHS: Final = (
    "auditor.md",
    "audit-orchestrator.md",
)
RETIRED_AUDIT_SKILL_TOKENS: Final = (
    "verdict.py",
    "aggregate_verdicts.py",
    "pass_results.py",
    "journal_emit.py",
    "audit_orchestrator.py",
)
IMPLEMENTATION_AUDIT_INPUT: Final = {
    "schema_version": 1,
    "request": {"kind": "implementation-audit-contract"},
}
IMPLEMENTATION_AUDIT_SCOPE_UNIT: Final = {
    "unitId": "unit-python-code",
    "auditClass": "implementation",
    "auditKind": "code",
    "subject": AUDIT_SUBJECT_PATH,
    "coverageRequirement": "required",
    "coverageStatus": "audited",
    "priorContext": {
        "changedFilePartition": AUDIT_SUBJECT_PATH,
        "concernPartition": "code",
        "languagePartition": "python",
    },
    "expectedProducer": {
        "producerKind": "skill",
        "agentName": "implementation-auditor",
        "agentOwningPluginName": "spec-tree",
        "skillName": "audit-python-code",
        "skillOwningPluginName": "python",
        "invocationRole": "leaf-skill",
    },
    "recordedByRunDriver": {
        "producerKind": "agent",
        "agentName": "implementation-auditor",
        "agentOwningPluginName": "spec-tree",
        "skillName": "audit-implementation",
        "skillOwningPluginName": "spec-tree",
        "invocationRole": "run-driver",
    },
}
IMPLEMENTATION_AUDIT_FINDING: Final = {
    "unitId": "unit-python-code",
    "producerIdentity": {
        "producerKind": "skill",
        "agentName": "implementation-auditor",
        "agentOwningPluginName": "spec-tree",
        "skillName": "audit-python-code",
        "skillOwningPluginName": "python",
        "invocationRole": "leaf-skill",
    },
    "rule": "example-rule",
    "severity": "blocking",
    "location": f"{AUDIT_SUBJECT_PATH}:1",
    "message": "example finding",
    "evidence": {"observed": "problem", "expected": "clean"},
}


def spx_floor_provides_verification_run_lifecycle() -> bool:
    workflow_pin = read_pinned_version(WORKFLOW_PATH.read_text(encoding="utf-8"))
    return (
        is_satisfied(REQUIRED_SPX_VERSION, MINIMUM_VERIFICATION_RUN_SPX_VERSION)
        and workflow_pin is not None
        and is_satisfied(workflow_pin, MINIMUM_VERIFICATION_RUN_SPX_VERSION)
    )


def audit_skill_ships_no_verdict_toolchain_scripts() -> bool:
    return all(
        not (script_dir / retired_name).exists()
        for script_dir in AUDIT_SKILL_SCRIPT_DIRS
        for retired_name in RETIRED_AUDIT_SKILL_TOKENS
    )


def implementation_auditor_is_the_only_implementation_wrapper() -> bool:
    return all(
        (agent_dir / "implementation-auditor.md").is_file()
        for agent_dir in SPEC_TREE_AGENT_DIRS
    ) and not any(
        (agent_dir / retired_name).exists()
        for agent_dir in SPEC_TREE_AGENT_DIRS
        for retired_name in RETIRED_IMPLEMENTATION_AUDITOR_PATHS
    )


def language_concern_skill_trios_exist() -> bool:
    return all(
        _surface_language_concern_skill_trios_exist(surface)
        for surface in PLUGIN_SURFACES
    )


def spx_audit_verification_run_lifecycle_accepts_implementation_payloads() -> bool:
    with TemporaryDirectory() as tmp_dir:
        repo = Path(tmp_dir)
        _initialize_changeset_repo(repo)
        scope = _changeset_scope(repo)
        start_report = _run_spx_json(
            repo,
            (
                "verification",
                "run",
                "start",
                "--verification-type",
                "audit",
                "--scope-type",
                "changeset",
                "--scope",
                scope,
                "--input",
                "stdin",
            ),
            IMPLEMENTATION_AUDIT_INPUT,
        )
        run_token = _required_string(start_report, "runToken")

        scope_report = _run_spx_json(
            repo,
            (
                "verification",
                "run",
                "scope",
                "add",
                "--verification-type",
                "audit",
                "--scope-type",
                "changeset",
                "--scope",
                scope,
                "--run",
                run_token,
                "--payload",
                "stdin",
                "--idempotency-key",
                "unit-python-code",
            ),
            _with_producer_provenance(IMPLEMENTATION_AUDIT_SCOPE_UNIT),
        )
        finding_report = _run_spx_json(
            repo,
            (
                "verification",
                "run",
                "finding",
                "add",
                "--verification-type",
                "audit",
                "--scope-type",
                "changeset",
                "--scope",
                scope,
                "--run",
                run_token,
                "--payload",
                "stdin",
                "--idempotency-key",
                "finding-example",
            ),
            _with_producer_provenance(IMPLEMENTATION_AUDIT_FINDING),
        )
        finish_report = _run_spx_json(
            repo,
            (
                "verification",
                "run",
                "finish",
                "--verification-type",
                "audit",
                "--scope-type",
                "changeset",
                "--scope",
                scope,
                "--run",
                run_token,
                "--terminal-status",
                "rejected",
            ),
        )
        render_report = _run_spx_json(
            repo,
            (
                "verification",
                "run",
                "render",
                "--verification-type",
                "audit",
                "--scope-type",
                "changeset",
                "--scope",
                scope,
                "--run",
                run_token,
            ),
        )

    return (
        scope_report.get("sequence") == 1
        and finding_report.get("sequence") == 2
        and finish_report.get("terminalStatus") == "rejected"
        and finish_report.get("sealed") is True
        and render_report.get("runToken") == run_token
        and render_report.get("findingCount") == 1
        and render_report.get("sealed") is True
        and render_report.get("terminalStatus") == "rejected"
    )


def _surface_language_concern_skill_trios_exist(surface: Path) -> bool:
    language_plugins = tuple(
        plugin_dir
        for plugin_dir in surface.iterdir()
        if (plugin_dir / "skills" / f"code-{plugin_dir.name}" / "SKILL.md").is_file()
    )
    return all(
        all(
            (
                plugin_dir
                / "skills"
                / f"audit-{plugin_dir.name}-{concern}"
                / "SKILL.md"
            ).is_file()
            for concern in ("code", "tests", "architecture")
        )
        and not (plugin_dir / "skills" / f"audit-{plugin_dir.name}").exists()
        for plugin_dir in language_plugins
    )


def _initialize_changeset_repo(repo: Path) -> None:
    _run(repo, ("git", "init", "-q"))
    _run(repo, ("git", "config", "user.email", "test@example.com"))
    _run(repo, ("git", "config", "user.name", "Test User"))
    (repo / "file.txt").write_text("before\n", encoding="utf-8")
    _run(repo, ("git", "add", "file.txt"))
    _run(repo, ("git", "commit", "-q", "-m", "initial"))
    (repo / "file.txt").write_text("after\n", encoding="utf-8")
    _run(repo, ("git", "add", "file.txt"))
    _run(repo, ("git", "commit", "-q", "-m", "change"))


def _changeset_scope(repo: Path) -> str:
    head = _run(repo, ("git", "rev-parse", "HEAD")).stdout.strip()
    base = _run(repo, ("git", "rev-parse", "HEAD~1")).stdout.strip()
    return f"{base}..{head}"


def _run_spx_json(
    repo: Path,
    args: tuple[str, ...],
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    stdin = None if payload is None else f"{json.dumps(payload)}\n"
    completed = _run(repo, ("spx", *args), input_text=stdin)
    parsed = json.loads(completed.stdout)
    if not isinstance(parsed, dict):
        raise TypeError("spx command did not return a JSON object")
    return parsed


def _with_producer_provenance(payload: Mapping[str, Any]) -> dict[str, Any]:
    result = dict(payload)
    result["producerProvenance"] = {
        "agentOwningPluginVersion": _plugin_version("spec-tree"),
        "skillOwningPluginVersion": _plugin_version("python"),
        "toolVersion": MINIMUM_VERIFICATION_RUN_SPX_VERSION,
    }
    return result


def _plugin_version(plugin_name: str) -> str:
    manifest_path = (
        Path("src") / "plugins" / plugin_name / ".claude-plugin" / "plugin.json"
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise TypeError(f"plugin manifest is not a JSON object: {manifest_path}")
    version = manifest.get("version")
    if not isinstance(version, str):
        raise TypeError(f"plugin manifest lacks string version: {manifest_path}")
    return version


def _run(
    repo: Path,
    args: tuple[str, ...],
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=repo,
        input=input_text,
        text=True,
        check=True,
        capture_output=True,
    )


def _required_string(payload: Mapping[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise TypeError(f"missing string field: {key}")
    return value
