#!/usr/bin/env python3
"""Aggregate multiple child verdicts into one wrapper verdict.

Reads N child verdict JSON documents (either as a list of file paths or
as a directory of ``*.json`` files), validates each against the canonical
schema, and emits one wrapper verdict whose ``children`` array holds the
parsed children and whose ``overall`` is derived from the children's
overalls via ``verdict.roll_up``.

The wrapper's ``skill``, ``target``, and ``metadata`` come from CLI flags
or default values; the orchestrator typically sets ``skill="auditing"``
and ``target`` to the spec node under audit.

Portability: stdlib only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Bare ``import verdict`` resolves because this file is invoked as a script
# (Python prepends the script's directory to ``sys.path``). Tests exercise
# this script through ``subprocess`` calls, not via ``importlib`` loading.
import verdict
from verdict import Verdict, VerdictValidationError

EXIT_OK = 0
EXIT_VALIDATION_ERROR = 1
EXIT_IO_ERROR = 2

DEFAULT_SKILL = "auditing"
DEFAULT_TARGET = ""


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        paths = _resolve_paths(args.inputs, args.directory)
    except OSError as exc:
        print(f"aggregate_verdicts: cannot enumerate inputs: {exc}", file=sys.stderr)
        return EXIT_IO_ERROR
    if not paths:
        print(
            "aggregate_verdicts: no input verdicts (use positional paths or --directory)",
            file=sys.stderr,
        )
        return EXIT_IO_ERROR
    try:
        children = [_load_verdict(p) for p in paths]
    except OSError as exc:
        print(f"aggregate_verdicts: cannot read input: {exc}", file=sys.stderr)
        return EXIT_IO_ERROR
    except VerdictValidationError as exc:
        print(f"aggregate_verdicts: invalid child verdict: {exc}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR
    try:
        metadata = _parse_metadata(args.metadata)
    except ValueError as exc:
        print(f"aggregate_verdicts: {exc}", file=sys.stderr)
        return EXIT_IO_ERROR
    wrapper = aggregate(
        children=tuple(children),
        skill=args.skill,
        target=args.target,
        metadata=metadata,
    )
    try:
        _write_output(args.output, verdict.dump_json(wrapper) + "\n")
    except OSError as exc:
        print(f"aggregate_verdicts: cannot write output: {exc}", file=sys.stderr)
        return EXIT_IO_ERROR
    return EXIT_OK


def aggregate(
    *,
    children: tuple[Verdict, ...],
    skill: str,
    target: str,
    metadata: dict[str, str],
) -> Verdict:
    """Build a wrapper ``Verdict`` over the given children.

    The wrapper's ``overall`` is derived via ``verdict.roll_up`` over the
    children's overalls. Wrapper ``rows`` are empty — the orchestrator
    expresses per-language results through children, not through its own
    rows.
    """
    overall = verdict.roll_up([child.overall for child in children])
    return Verdict(
        schema_version=verdict.SCHEMA_VERSION,
        skill=skill,
        target=target,
        overall=overall,
        rows=(),
        children=children,
        metadata=dict(metadata),
    )


def _resolve_paths(positional: list[str], directory: str | None) -> list[Path]:
    paths: list[Path] = [Path(p) for p in positional]
    if directory is not None:
        dir_path = Path(directory)
        if not dir_path.is_dir():
            raise OSError(f"--directory {directory} is not a directory")
        paths.extend(sorted(dir_path.glob("*.json")))
    # Deduplicate by resolved path so a file passed both positionally and
    # discovered via --directory contributes one child to the wrapper,
    # not two. Without this, a duplicated FAIL child would count twice in
    # the rollup. Map resolved -> original so error reporting preserves
    # the caller-supplied (possibly relative) path. Hard-linked files
    # remain undetected: ``Path.resolve`` follows symlinks but does not
    # canonicalize to an inode; callers passing two hard-link aliases to
    # the same file will see both as distinct children.
    seen: dict[Path, Path] = {}
    for path in paths:
        seen.setdefault(path.resolve(), path)
    return list(seen.values())


def _load_verdict(path: Path) -> Verdict:
    text = path.read_text(encoding="utf-8")
    return verdict.parse_json(text)


def _parse_metadata(items: list[str]) -> dict[str, str]:
    """Parse ``--metadata key=value`` items into a dict.

    Each item must contain exactly one ``=``; the key is the substring
    before the first ``=``, the value is everything after it (values
    may themselves contain ``=``).
    """
    metadata: dict[str, str] = {}
    for item in items:
        if "=" not in item:
            raise ValueError(
                f"malformed --metadata entry {item!r} (expected key=value)"
            )
        key, value = item.split("=", 1)
        metadata[key] = value
    return metadata


def _write_output(path: str | None, content: str) -> None:
    if path is None or path == "-":
        sys.stdout.write(content)
        return
    Path(path).write_text(content, encoding="utf-8")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="aggregate_verdicts",
        description=(
            "Aggregate multiple child verdict JSON files into one wrapper "
            "verdict. The wrapper's overall is derived from the children's "
            "overalls per the canonical rollup rule."
        ),
    )
    parser.add_argument(
        "inputs",
        nargs="*",
        help="Paths to child verdict JSON files.",
    )
    parser.add_argument(
        "--directory",
        default=None,
        help=(
            "Directory containing child verdict JSON files. All *.json files "
            "in the directory (lexicographic order) are included alongside "
            "any positional paths."
        ),
    )
    parser.add_argument(
        "--skill",
        default=DEFAULT_SKILL,
        help=f"Wrapper verdict's 'skill' field. Default: {DEFAULT_SKILL!r}.",
    )
    parser.add_argument(
        "--target",
        default=DEFAULT_TARGET,
        help="Wrapper verdict's 'target' field. Default: empty string.",
    )
    parser.add_argument(
        "--metadata",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help=(
            "Metadata entry for the wrapper. May be repeated. Each entry "
            "is split on the first '=': key, value."
        ),
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path. Use '-' or omit to write to stdout.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
