"""Process boundary for the implementation audit's shipped scope entrypoint."""

import pathlib
import runpy
import subprocess
import sys
from typing import cast

SCRIPT_PATH = (
    pathlib.Path(__file__)
    .resolve()
    .parents[2]
    .joinpath(
        "src",
        "plugins",
        "spec-tree",
        "skills",
        "audit-implementation",
        "scripts",
        "resolve_scope.py",
    )
)
ERROR_PREFIX = cast(str, runpy.run_path(str(SCRIPT_PATH))["ERROR_PREFIX"])


def run_implementation_scope(
    repo: pathlib.Path,
    selector: str,
    *,
    repo_override: pathlib.Path | None = None,
    audit_input: str | None = None,
) -> subprocess.CompletedProcess[str]:
    """Capture the real CLI result while keeping cwd separate from --repo."""
    audit_input_argv = () if audit_input is None else ("--audit-input", audit_input)
    return subprocess.run(
        (
            sys.executable,
            str(SCRIPT_PATH),
            selector,
            "--repo",
            str(repo if repo_override is None else repo_override),
            *audit_input_argv,
        ),
        cwd=repo,
        text=True,
        capture_output=True,
        check=False,
    )
