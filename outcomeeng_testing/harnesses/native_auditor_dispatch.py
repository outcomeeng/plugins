"""Own disposable installation, authentication, and native auditor-dispatch evidence."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Mapping, Sequence
from pathlib import Path

from outcomeeng.distribution.contracts import Target
from outcomeeng.distribution.native_auditor_dispatch import (
    NativeAuditorDispatchObservation,
    NativeAuditorRow,
    materialize_native_auditor,
    native_auditor_rows,
    record_native_auditor_failure,
    run_native_auditor_row,
)
from outcomeeng_testing.harnesses.discovery_auth import ProbeRunner
from outcomeeng_testing.harnesses.native_profile_execution import (
    NativeProfileInterval,
    execute_native_row,
    run_native_rows,
    run_profile_process,
)


def run_native_auditor_dispatch(
    artifact_root: Path,
    *,
    checkout: Path,
    environment: Mapping[str, str],
    runner: ProbeRunner = run_profile_process,
    target: Target | None = None,
) -> tuple[NativeAuditorDispatchObservation, ...]:
    """Retain every auditor row's observations while removing its disposable state."""

    def plan(state_root: Path) -> tuple[NativeAuditorRow, ...]:
        return native_auditor_rows(checkout, artifact_root, state_root)

    def execute(
        row: NativeAuditorRow, mirror: Path, interval: NativeProfileInterval
    ) -> NativeAuditorDispatchObservation:
        def run(
            auditor_row: NativeAuditorRow, child_environment: Mapping[str, str]
        ) -> NativeAuditorDispatchObservation:
            return run_native_auditor_row(
                auditor_row,
                checkout=mirror,
                environment=child_environment,
                parent=interval.parent,
                sanitize=interval.sanitize,
            )

        return execute_native_row(
            row, mirror, environment, interval, subject="auditor dispatch", run=run
        )

    return run_native_rows(
        artifact_root,
        checkout=checkout,
        plan=plan,
        materialize=materialize_native_auditor,
        execute=execute,
        record_failure=record_native_auditor_failure,
        runner=runner,
        target=target,
    )


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
