"""Capture one authenticated Codex skill-composition probe observation."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Final

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.installation import (
    CODEX_HOME_AGENTS_PATH,
    CODEX_EXEC_SUBCOMMAND,
    CODEX_EXECUTABLE,
    InstallationFailure,
    build_isolated_installation_plan,
    execute_installation,
    report_document,
)
from outcomeeng.distribution.native_thread_evidence import (
    NativeChildEvidence,
    collect_native_child_evidence,
)
from outcomeeng.distribution.profiles import (
    AGENT_PROFILES,
    AgentProfile,
    CodexConfiguration,
)
from outcomeeng_testing.harnesses.discovery_auth import (
    DiscoveryAuthentication,
    DiscoveryAuthenticationError,
    ProbeRunner,
    credential_free_environment,
    select_authentication,
)
from outcomeeng_testing.harnesses.native_profile_execution import (
    NativeProfileInterval,
    run_profile_process,
)

IMPLEMENTATION_AUDITOR_ROLE: Final = "spec-tree_implementation-auditor"
IMPLEMENTATION_AUDITOR_DEFINITION: Final = f"{IMPLEMENTATION_AUDITOR_ROLE}.toml"
PROBE_SANDBOX_MODE: Final = "danger-full-access"
PARENT_PROMPT: Final = (
    f"Launch {IMPLEMENTATION_AUDITOR_ROLE} exactly once with target HEAD. "
    'Return its terminal result. Explicitly set fork_turns to "none".'
)
INSTALLER_REPORT_FILENAME: Final = "installer-report.json"
INSTALLED_DEFINITION_FILENAME: Final = "installed-definition.toml"
PARENT_STREAM_FILENAME: Final = "parent.jsonl"
PARENT_STDERR_FILENAME: Final = "parent.stderr.txt"
CHILD_RECORD_FILENAME: Final = "child.json"
TERMINAL_RESULT_FILENAME: Final = "terminal.txt"
SUMMARY_FILENAME: Final = "summary.json"


@dataclass(frozen=True)
class CodexSkillCompositionObservation:
    """Retained paths and terminal conditions from one probe execution."""

    artifact_root: Path
    parent_exit_code: int | None
    parent_thread_id: str | None
    child_terminal_condition: str | None
    failure: str | None


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _write_json(path: Path, document: Mapping[str, object]) -> None:
    _write_text(path, json.dumps(document, indent=2, sort_keys=True) + "\n")


def _standard_codex_configuration() -> CodexConfiguration:
    configuration = AGENT_PROFILES[Target.CODEX][AgentProfile.STANDARD]
    if not isinstance(configuration, CodexConfiguration):
        raise TypeError("the standard Codex profile has an incompatible configuration")
    return configuration


def _parent_command(checkout: Path, terminal_path: Path) -> tuple[str, ...]:
    return (
        CODEX_EXECUTABLE,
        CODEX_EXEC_SUBCOMMAND,
        "--json",
        "--strict-config",
        "--skip-git-repo-check",
        "--sandbox",
        PROBE_SANDBOX_MODE,
        "-C",
        str(checkout),
        "--output-last-message",
        str(terminal_path),
        PARENT_PROMPT,
    )


def _retain_child_record(artifact_root: Path, evidence: NativeChildEvidence) -> None:
    if evidence.thread_read is None:
        return
    _write_text(artifact_root / CHILD_RECORD_FILENAME, evidence.thread_read.stdout)


def run_codex_skill_composition_probe(
    artifact_root: Path,
    *,
    checkout: Path,
    environment: Mapping[str, str],
    runner: ProbeRunner = run_profile_process,
) -> CodexSkillCompositionObservation:
    """Install, authenticate, launch, and retain one composition observation."""
    resolved_artifacts = artifact_root.resolve()
    resolved_artifacts.mkdir(parents=True, exist_ok=False)
    resolved_checkout = checkout.resolve(strict=True)
    authentication = DiscoveryAuthentication(select_authentication(environment), runner)
    interval = NativeProfileInterval(runner, authentication=authentication)
    parent_exit_code: int | None = None
    parent_thread_id: str | None = None
    child_terminal_condition: str | None = None
    failure: str | None = None

    try:
        with TemporaryDirectory() as temporary_state:
            state_root = Path(temporary_state).resolve()
            plan = build_isolated_installation_plan(
                resolved_checkout,
                state_root,
                credential_free_environment(environment),
            )
            report = execute_installation(plan, interval.install)
            _write_json(
                resolved_artifacts / INSTALLER_REPORT_FILENAME,
                report_document(report),
            )
            codex_home = plan.roots.codex_home
            shutil.copyfile(
                codex_home / CODEX_HOME_AGENTS_PATH / IMPLEMENTATION_AUDITOR_DEFINITION,
                resolved_artifacts / INSTALLED_DEFINITION_FILENAME,
            )
            child_environment = dict(plan.commands[0].environment)
            terminal_path = resolved_artifacts / TERMINAL_RESULT_FILENAME
            with authentication.authenticated_home(
                codex_home,
                cwd=resolved_checkout,
                env=child_environment,
            ):
                parent = interval.parent(
                    _parent_command(resolved_checkout, terminal_path),
                    resolved_checkout,
                    child_environment,
                )
                parent_exit_code = parent.returncode
                _write_text(
                    resolved_artifacts / PARENT_STREAM_FILENAME,
                    parent.stdout,
                )
                _write_text(
                    resolved_artifacts / PARENT_STDERR_FILENAME,
                    parent.stderr,
                )
                if terminal_path.exists():
                    _write_text(
                        terminal_path,
                        interval.sanitize(terminal_path.read_text(encoding="utf-8")),
                    )
                if parent.returncode != 0:
                    failure = f"native parent session exited {parent.returncode}"
                else:
                    evidence = collect_native_child_evidence(
                        parent.stdout,
                        IMPLEMENTATION_AUDITOR_ROLE,
                        _standard_codex_configuration(),
                        reader=interval.thread,
                        cwd=resolved_checkout,
                        environment=child_environment,
                    )
                    parent_thread_id = evidence.parent_id
                    child_terminal_condition = evidence.terminal_condition
                    _retain_child_record(resolved_artifacts, evidence)
                    if evidence.terminal_condition is not None:
                        failure = evidence.terminal_condition
    except (
        OSError,
        ValueError,
        TypeError,
        InstallationFailure,
        DiscoveryAuthenticationError,
        subprocess.TimeoutExpired,
    ) as error:
        failure = interval.sanitize(str(error))

    observation = CodexSkillCompositionObservation(
        artifact_root=resolved_artifacts,
        parent_exit_code=parent_exit_code,
        parent_thread_id=parent_thread_id,
        child_terminal_condition=child_terminal_condition,
        failure=failure,
    )
    _write_json(
        resolved_artifacts / SUMMARY_FILENAME,
        {
            "artifact_root": str(observation.artifact_root),
            "parent_exit_code": observation.parent_exit_code,
            "parent_thread_id": observation.parent_thread_id,
            "child_terminal_condition": observation.child_terminal_condition,
            "failure": observation.failure,
        },
    )
    return observation


def main(argv: Sequence[str] | None = None) -> int:
    """Run one probe and print the retained observation summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_directory", type=Path)
    parser.add_argument("--checkout", type=Path, default=Path.cwd())
    arguments = parser.parse_args(argv)
    observation = run_codex_skill_composition_probe(
        arguments.artifact_directory,
        checkout=arguments.checkout,
        environment=os.environ,
    )
    print(
        json.dumps(
            {
                "artifact_root": str(observation.artifact_root),
                "parent_exit_code": observation.parent_exit_code,
                "parent_thread_id": observation.parent_thread_id,
                "child_terminal_condition": observation.child_terminal_condition,
                "failure": observation.failure,
            },
            sort_keys=True,
        )
    )
    return int(observation.failure is not None)


if __name__ == "__main__":
    raise SystemExit(main())
