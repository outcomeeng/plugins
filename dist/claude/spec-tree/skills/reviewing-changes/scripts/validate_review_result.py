"""CLI: validate a review-result JSON document.

The arbiter the wrapper agent invokes against every JSON document it
emits. Reads the document from stdin or via ``--file <path>``, pipes it
through ``review_result.parse_json``, and exits 0 on conformance.

Exit codes:

- ``0`` — the document conforms (schema, enum membership, consistency
  invariant).
- non-zero — the document violates one or more rules; the parser's
  error message is written to stderr verbatim so the agent can
  correlate the failure with the JSON it just emitted.

The CLI itself implements no schema knowledge. Every check happens
inside ``review_result.parse_json``; this script is the entry point a
subprocess can invoke and read an exit code from.

Stdlib-only.
"""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import sys
from types import ModuleType


def _load_review_result() -> ModuleType:
    """Load the sibling ``review_result`` module via ``importlib``.

    Mirrors the loader pattern in ``fs_backend.py:_errors_module``. The
    scripts directory is not a package on every consumer install, so
    the script reaches its sibling by absolute path.
    """
    cached = sys.modules.get("review_result")
    if cached is not None:
        return cached
    path = pathlib.Path(__file__).resolve().parent / "review_result.py"
    spec = importlib.util.spec_from_file_location("review_result", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load review_result from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["review_result"] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate a review-result JSON document against the canonical schema."
    )
    parser.add_argument(
        "--file",
        type=pathlib.Path,
        default=None,
        help="path to JSON payload; when omitted, payload is read from stdin",
    )
    args = parser.parse_args(argv)

    if args.file is not None:
        try:
            text = args.file.read_text(encoding="utf-8")
        except OSError as exc:
            sys.stderr.write(f"cannot read {args.file}: {exc}\n")
            return 2
    else:
        text = sys.stdin.read()

    review_result = _load_review_result()
    try:
        review_result.parse_json(text)
    except review_result.ReviewResultValidationError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
