"""ShellCheck gate over tracked shell scripts."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Final


_REPO_ROOT: Final = Path(__file__).resolve().parents[2]
_SHELL_GLOBS: Final = ("*.sh", "*.bash", "*.zsh")


def tracked_shell_files(root: Path = _REPO_ROOT) -> tuple[str, ...]:
    """Return tracked shell files that ShellCheck should inspect."""
    completed = subprocess.run(
        ("git", "ls-files", "-z", *_SHELL_GLOBS),
        cwd=root,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return tuple(path for path in completed.stdout.decode().split("\0") if path)


def main() -> int:
    """Run ShellCheck over tracked shell scripts, or no-op when none exist."""
    files = tracked_shell_files()
    if not files:
        return 0
    completed = subprocess.run(
        ("shellcheck", "--severity=warning", *files),
        cwd=_REPO_ROOT,
        check=False,
    )
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
