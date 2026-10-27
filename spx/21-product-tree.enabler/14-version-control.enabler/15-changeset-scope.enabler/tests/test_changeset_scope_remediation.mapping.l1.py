"""Mapping evidence: each changeset-scope failure maps to its error and remedy.

Covers the Mapping assertions in ``../changeset-scope.md``. The failure-to-remedy
domain is the generator-owned table of the governing sentences; the harness arms
the real repository state for each row.
"""

from __future__ import annotations

import subprocess

import pytest

from outcomeeng_testing.generators.changeset_scope import remediation_cases
from outcomeeng_testing.harnesses.changeset_scope import (
    CHANGESET_SCOPE,
    remediation_scenario,
)


@pytest.mark.parametrize("case", remediation_cases(), ids=lambda case: case.failure)
def test_failure_maps_to_its_error_class_and_remedy(case) -> None:
    with remediation_scenario(case) as armed:
        with pytest.raises(getattr(CHANGESET_SCOPE, case.error_name)) as raised:
            armed.invoke()
        cause = raised.value.__cause__
        observed = (
            {
                "command": " ".join(map(str, cause.cmd)),
                "status": str(cause.returncode),
            }
            if isinstance(cause, subprocess.CalledProcessError)
            else {}
        )
        message = str(raised.value)
        for fragment in case.fragments:
            assert fragment.format(**armed.placeholders, **observed) in message
