"""Own disposable installation, authentication, and native auditor-dispatch evidence."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.installation import (
    InstallationFailure,
    build_isolated_installation_plan,
    execute_installation,
)
from outcomeeng.distribution.native_auditor_dispatch import (
    NativeAuditorDispatchObservation,
    NativeAuditorRow,
    materialize_native_auditor,
    native_auditor_rows,
    record_native_auditor_failure,
    run_native_auditor_row,
)
from outcomeeng_testing.harnesses.discovery_auth import (
    CredentialRedactor,
    DiscoveryAuthentication,
    DiscoveryAuthenticationError,
    ProbeRunner,
    select_authentication,
)
from outcomeeng_testing.harnesses.installation import mirror_installation_inputs
from outcomeeng_testing.harnesses.native_profile_execution import (
    CLAUDE_CREDENTIAL_VARIABLES,
    NativeProfileInterval,
    isolated_environment,
    run_profile_process,
)


def _execute_row(
    row: NativeAuditorRow,
    checkout: Path,
    environment: Mapping[str, str],
    interval: NativeProfileInterval,
) -> NativeAuditorDispatchObservation:
    if row.target is Target.CODEX:
        interval.authentication = DiscoveryAuthentication(
            select_authentication(environment), interval.runner
        )
    plan = build_isolated_installation_plan(
        checkout, row.state_root, isolated_environment(environment)
    )
    execute_installation(plan, interval.install)
    child_environment = dict(plan.commands[0].environment)
    if interval.authentication is not None:
        with interval.authentication.authenticated_home(
            plan.roots.codex_home, cwd=checkout, env=child_environment
        ):
            return run_native_auditor_row(
                row,
                checkout=checkout,
                environment=child_environment,
                parent=interval.parent,
                sanitize=interval.sanitize,
            )
    selected = tuple(
        name for name in CLAUDE_CREDENTIAL_VARIABLES if environment.get(name)
    )
    if len(selected) != 1:
        raise DiscoveryAuthenticationError(
            "Claude auditor dispatch requires exactly one selected native credential."
        )
    name = selected[0]
    interval.redactor.add(environment[name])
    child_environment[name] = environment[name]
    return run_native_auditor_row(
        row,
        checkout=checkout,
        environment=child_environment,
        parent=interval.parent,
        sanitize=interval.sanitize,
    )


def run_native_auditor_dispatch(
    artifact_root: Path,
    *,
    checkout: Path,
    environment: Mapping[str, str],
    runner: ProbeRunner = run_profile_process,
    target: Target | None = None,
) -> tuple[NativeAuditorDispatchObservation, ...]:
    """Retain every row's observations while removing its disposable state."""
    artifact_root.mkdir(parents=True, exist_ok=False)
    observations: list[NativeAuditorDispatchObservation] = []
    with TemporaryDirectory() as temporary_checkout:
        mirror = Path(temporary_checkout) / "checkout"
        mirror_installation_inputs(checkout, mirror)
        for index in range(len(native_auditor_rows(checkout))):
            with TemporaryDirectory() as temporary_state:
                row = native_auditor_rows(
                    checkout, artifact_root, Path(temporary_state)
                )[index]
                if target is not None and row.target is not target:
                    continue
                interval = NativeProfileInterval(runner, redactor=CredentialRedactor())
                try:
                    materialize_native_auditor(row)
                    observation = _execute_row(row, mirror, environment, interval)
                except (
                    OSError,
                    ValueError,
                    InstallationFailure,
                    DiscoveryAuthenticationError,
                    subprocess.TimeoutExpired,
                ) as error:
                    observation = record_native_auditor_failure(
                        row,
                        interval.sanitize(str(error)),
                        install_exit_code=(
                            error.result.exit_code
                            if isinstance(error, InstallationFailure)
                            else None
                        ),
                    )
                observations.append(observation)
    return tuple(observations)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the native auditor-dispatch harness through its public recipe."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact_directory", type=Path)
    parser.add_argument("--target", type=Target, choices=tuple(Target))
    arguments = parser.parse_args(argv)
    observations = run_native_auditor_dispatch(
        arguments.artifact_directory.resolve(),
        checkout=Path.cwd(),
        environment=os.environ,
        target=arguments.target,
    )
    print(
        json.dumps(
            [
                {
                    "identifier": item.row.identifier,
                    "configuration": str(item.row.configuration_path),
                    "loading": str(item.row.loading_path),
                    "result": str(item.row.result_path),
                    "terminal_condition": item.terminal_condition,
                }
                for item in observations
            ],
            sort_keys=True,
        )
    )
    return int(any(item.terminal_condition is not None for item in observations))


if __name__ == "__main__":
    raise SystemExit(main())
