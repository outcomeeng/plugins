#!/usr/bin/env python3
"""Capture pre-computed tool output into a results directory.

The orchestrator runs tools (linters, type-checkers, test runners, the
project's ``spx validation``) once, captures each tool's verbatim output,
and writes it into a results directory using this script. The dispatched
audit skills receive the directory path and read the files instead of
re-running the tools.

Two subcommands:

- ``mkdir``       — create a fresh results directory. Prints its path on
                    stdout. Uses ``tempfile.mkdtemp`` with prefix
                    ``audit-results-`` so the directory is unique per
                    invocation and survives until the caller removes it.
                    **The caller owns cleanup**: this script does not
                    register an atexit handler or remove the directory
                    on completion. In long-lived environments with
                    persistent ``/tmp`` (CI runners reused across jobs,
                    developer machines), the orchestrator should remove
                    the directory after the audit emits its verdict.
- ``add``         — write verbatim content to a file inside an existing
                    results directory, named after the command that
                    produced it. Reads content from stdin (default) or
                    ``--file``. Prints the resulting file path on stdout.

Filename derivation (``add``): spaces in the command are replaced with
underscores; everything else is preserved verbatim. On collision (same
sanitized name already present in the directory), a numeric suffix
``.1``, ``.2``, … is appended.

Portability: stdlib only.
"""

from __future__ import annotations

import argparse
import sys
import tempfile
from pathlib import Path

EXIT_OK = 0
EXIT_IO_ERROR = 2
EXIT_USAGE = 64

RESULTS_DIR_PREFIX = "audit-results-"
MAX_COLLISION_SUFFIX = 999


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    if args.subcommand == "mkdir":
        return _cmd_mkdir(args)
    if args.subcommand == "add":
        return _cmd_add(args)
    parser.print_help(sys.stderr)
    return EXIT_USAGE


def _cmd_mkdir(args: argparse.Namespace) -> int:
    parent = Path(args.parent) if args.parent else None
    try:
        path = mkdir(parent=parent)
    except OSError as exc:
        print(f"pass_results: cannot create directory: {exc}", file=sys.stderr)
        return EXIT_IO_ERROR
    sys.stdout.write(str(path) + "\n")
    return EXIT_OK


def _cmd_add(args: argparse.Namespace) -> int:
    directory = Path(args.directory)
    if not directory.is_dir():
        print(
            f"pass_results: results directory {args.directory!r} does not exist",
            file=sys.stderr,
        )
        return EXIT_IO_ERROR
    try:
        content = _read_content(args.file)
    except OSError as exc:
        print(f"pass_results: cannot read input: {exc}", file=sys.stderr)
        return EXIT_IO_ERROR
    try:
        path = add(directory=directory, command=args.command, content=content)
    except OSError as exc:
        print(f"pass_results: cannot write file: {exc}", file=sys.stderr)
        return EXIT_IO_ERROR
    sys.stdout.write(str(path) + "\n")
    return EXIT_OK


def mkdir(*, parent: Path | None = None) -> Path:
    """Create a fresh results directory and return its path.

    Uses ``tempfile.mkdtemp`` with prefix ``audit-results-``. If
    ``parent`` is provided, the directory is created inside ``parent``;
    otherwise the system temp root is used.

    Caller-owned cleanup: this function does not register an atexit
    handler or remove the directory itself. The orchestrator should
    remove the returned path (e.g., via ``shutil.rmtree``) after the
    audit verdict is emitted, otherwise the directories accumulate in
    persistent-``/tmp`` environments.
    """
    return Path(tempfile.mkdtemp(prefix=RESULTS_DIR_PREFIX, dir=parent))


def add(*, directory: Path, command: str, content: str) -> Path:
    """Write ``content`` to a uniquely named file in ``directory``.

    The filename is the sanitized ``command`` (see ``filename_for_command``).
    On collision, appends ``.1``, ``.2``, … up to ``MAX_COLLISION_SUFFIX``
    until a free name is found. Beyond that, raises ``OSError`` — the
    bounded retry keeps the contract explicit and prevents a runaway
    loop in pathological cases (e.g., a results directory shared across
    many parallel callers).
    Returns the path of the written file.
    """
    base_name = filename_for_command(command)
    # Generate the candidate sequence eagerly so every candidate up to
    # ``MAX_COLLISION_SUFFIX`` is actually checked. An in-place "assign
    # next target at end of loop body" pattern is off-by-one: the final
    # ``.N`` is set but never tested before the loop exits.
    candidates = [directory / base_name]
    candidates.extend(
        directory / f"{base_name}.{suffix}"
        for suffix in range(1, MAX_COLLISION_SUFFIX + 1)
    )
    for target in candidates:
        if not target.exists():
            target.write_text(content, encoding="utf-8")
            return target
    raise OSError(
        f"too many collisions for {base_name!r} in {directory} "
        f"(exceeded MAX_COLLISION_SUFFIX={MAX_COLLISION_SUFFIX})"
    )


def filename_for_command(command: str) -> str:
    """Derive a single filename component from a command line.

    Replaces every character that participates in path resolution —
    ASCII space, POSIX path separator ``/``, Windows path separator
    ``\\``, and the ``:`` byte (NTFS alternate-data-stream separator,
    macOS HFS path separator) — with underscores. Preserves everything
    else (flags, ``=``, ``-``, dots, etc.) verbatim.

    The result is a single filename component, never a path. The
    contract is deliberately narrow so callers can ``directory / name``
    without surprise: a command containing ``/path/to/check.py`` does
    not produce a nested subdirectory or escape the results directory.

    Windows-specific reserved characters (``*``, ``?``, ``"``, ``<``,
    ``>``, ``|``) are left through verbatim. The marketplace targets
    macOS and Linux; extend the replacement set if Windows support is
    ever in scope.
    """
    out = command
    for character in (" ", "/", "\\", ":"):
        out = out.replace(character, "_")
    return out


def _read_content(path: str | None) -> str:
    if path is None or path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pass_results",
        description=(
            "Capture pre-computed tool output into a results directory. The "
            "orchestrator runs tools once and writes their output here; "
            "dispatched skills read the files instead of re-running the tools."
        ),
    )
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    mkdir_parser = subparsers.add_parser(
        "mkdir",
        help="Create a fresh results directory and print its path.",
    )
    mkdir_parser.add_argument(
        "--parent",
        default=None,
        help="Parent directory for the new results directory. Defaults to the system temp root.",
    )

    add_parser = subparsers.add_parser(
        "add",
        help="Write verbatim content to a command-named file inside a results directory.",
    )
    add_parser.add_argument(
        "directory",
        help="Path to an existing results directory.",
    )
    add_parser.add_argument(
        "command",
        help="The command line whose output is being captured. Used to derive the filename.",
    )
    add_parser.add_argument(
        "--file",
        default=None,
        help="File to read content from. Use '-' or omit to read from stdin.",
    )

    return parser


if __name__ == "__main__":
    sys.exit(main())
