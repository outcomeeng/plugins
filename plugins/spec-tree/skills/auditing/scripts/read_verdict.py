#!/usr/bin/env python3
"""Extract an audit-verdict JSON document from any surface form.

The inverse of ``emit_verdict.py``. Accepts text in any of three forms:

- ``json-only``      — the input *is* the JSON document.
- ``markdown+json``  — markdown with an HTML-comment-delimited JSON block;
                       the block content is the JSON document.
- ``markdown`` alone — fails: markdown without an embedded JSON block has
                       no machine-readable verdict.

Validates the extracted JSON against the canonical schema in ``verdict.py``
and writes a normalized JSON document to stdout (or ``--output``).

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
from verdict import VerdictValidationError

JSON_BLOCK_BEGIN = "<!-- AUDIT_VERDICT_JSON_BEGIN -->"
JSON_BLOCK_END = "<!-- AUDIT_VERDICT_JSON_END -->"

EXIT_OK = 0
EXIT_VALIDATION_ERROR = 1
EXIT_IO_ERROR = 2
EXIT_NOT_FOUND = 3


class ExtractError(ValueError):
    """Raised when the input contains no extractable verdict."""


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    try:
        text = _read_input(args.file)
    except OSError as exc:
        print(f"read_verdict: cannot read input: {exc}", file=sys.stderr)
        return EXIT_IO_ERROR
    try:
        payload = extract_json(text)
    except ExtractError as exc:
        print(f"read_verdict: {exc}", file=sys.stderr)
        return EXIT_NOT_FOUND
    try:
        parsed = verdict.parse_json(payload)
    except VerdictValidationError as exc:
        print(f"read_verdict: invalid verdict: {exc}", file=sys.stderr)
        return EXIT_VALIDATION_ERROR
    normalized = verdict.dump_json(parsed)
    try:
        _write_output(args.output, normalized + "\n")
    except OSError as exc:
        print(f"read_verdict: cannot write output: {exc}", file=sys.stderr)
        return EXIT_IO_ERROR
    return EXIT_OK


def extract_json(text: str) -> str:
    """Return the JSON payload string extracted from any surface form.

    Detection rules, evaluated in order. Delimiters take precedence over
    the ``startswith({)`` heuristic so a markdown+json document whose
    prose section happens to start with an open brace still routes to
    the delimited block.

    1. If the input contains both ``JSON_BLOCK_BEGIN`` and
       ``JSON_BLOCK_END`` delimiters (in that order), return the text
       between them, trimmed.
    2. Else, if the stripped input begins with ``{``, treat the whole
       input as a JSON-only verdict and return the stripped text.
    3. Else, raise ``ExtractError``.

    The function does not validate the schema — it only locates the JSON
    document. Schema validation is the caller's responsibility (via
    ``verdict.parse_json``). A malformed JSON document that begins with
    ``{`` therefore surfaces downstream as ``"invalid verdict: invalid
    JSON: …"`` rather than as ``ExtractError("no JSON payload found")``;
    the heuristic cannot distinguish "starts with brace but is broken"
    from "is a valid JSON-only verdict" without parsing.
    """
    begin = text.find(JSON_BLOCK_BEGIN)
    end = text.find(JSON_BLOCK_END)
    if begin != -1 and end != -1 and begin < end:
        payload = text[begin + len(JSON_BLOCK_BEGIN) : end]
        return payload.strip()
    stripped = text.strip()
    if stripped.startswith("{"):
        return stripped
    raise ExtractError(
        "no JSON payload found; expected json-only input or "
        f"an HTML-comment-delimited block ({JSON_BLOCK_BEGIN} ... {JSON_BLOCK_END})"
    )


def _read_input(path: str | None) -> str:
    if path is None or path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def _write_output(path: str | None, content: str) -> None:
    if path is None or path == "-":
        sys.stdout.write(content)
        return
    Path(path).write_text(content, encoding="utf-8")


def _parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="read_verdict",
        description=(
            "Extract an audit-verdict JSON document from any surface form "
            "(json-only or markdown+json) and write the normalized JSON to "
            "stdout."
        ),
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Input file path. Use '-' or omit to read from stdin.",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Output file path. Use '-' or omit to write to stdout.",
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
