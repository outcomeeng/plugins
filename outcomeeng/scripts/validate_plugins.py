"""Discover and validate all marketplace and plugin manifests.

Finds the marketplace root (.claude-plugin/marketplace.json) and all plugin
directories (plugins/*/.claude-plugin/plugin.json), then runs
``claude plugin validate`` on each.

Usage::

    uv run python -m outcomeeng.scripts.validate_plugins [root_dir]

Exit codes:
    0 - All validations passed
    1 - One or more validations failed or no targets found
"""

from __future__ import annotations

import subprocess
import sys
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def discover_targets(root: Path) -> list[Path]:
    """Discover marketplace root and plugin directories to validate.

    Returns a sorted list of directories that contain
    .claude-plugin/marketplace.json or .claude-plugin/plugin.json.
    """
    targets: list[Path] = []

    # Marketplace root
    if (root / ".claude-plugin" / "marketplace.json").is_file():
        targets.append(root)

    # Plugin directories
    plugins_dir = root / "plugins"
    if plugins_dir.is_dir():
        for child in sorted(plugins_dir.iterdir()):
            if child.is_dir() and (child / ".claude-plugin" / "plugin.json").is_file():
                targets.append(child)

    return targets


def run_validate(cmd: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
    """Run a validation command. Thin wrapper for testability."""
    return subprocess.run(cmd, capture_output=True, text=True, **kwargs)


def main(
    argv: list[str] | None = None,
    *,
    runner: Callable[..., subprocess.CompletedProcess[str]] = run_validate,
) -> int:
    args = argv if argv is not None else sys.argv[1:]
    root = Path(args[0]) if args else Path(".")

    targets = discover_targets(root)
    if not targets:
        print(
            f"error: no marketplace or plugins found under {root}",
            file=sys.stderr,
        )
        return 1

    failures: list[tuple[Path, str]] = []

    def _validate(target: Path) -> tuple[Path, subprocess.CompletedProcess[str]]:
        cmd = ["claude", "plugin", "validate", str(target)]
        return target, runner(cmd)

    with ThreadPoolExecutor(max_workers=len(targets)) as pool:
        futures = {pool.submit(_validate, t): t for t in targets}
        for future in as_completed(futures):
            target, result = future.result()
            if result.returncode != 0:
                failures.append((target, result.stderr or result.stdout))
            else:
                print(result.stdout, end="")

    for target, output in failures:
        print(f"error: validation failed for {target}", file=sys.stderr)
        if output.strip():
            print(f"  {output.strip()}", file=sys.stderr)

    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
