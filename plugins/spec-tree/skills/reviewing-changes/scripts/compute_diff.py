"""CLI: compute the working diff against the PR's base ref.

Reads ``pr.json`` from the thread store under the given slug, extracts
``baseRefName``, runs ``git diff <base_ref>..HEAD`` via ``subprocess``,
and emits the diff to stdout. Every filesystem effect against the
thread-store backend routes through the ``thread_store`` facade; the
git invocation is the only ``subprocess.run`` call this script makes.

Exit codes:

- ``0`` — the diff was produced (possibly empty).
- non-zero — the slug has no ``pr.json``, the document is malformed,
  ``baseRefName`` is missing, or git itself fails.

Stdlib-only.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import subprocess
import sys
from types import ModuleType

PR_RECORD_NAME = "pr.json"


def _load_thread_store() -> ModuleType:
    """Load the ``thread_store`` facade via ``importlib``.

    The facade lives at
    ``plugins/spec-tree/skills/thread-store/scripts/thread_store.py``.
    Resolving it via ``__file__`` keeps the import independent of
    ``sys.path[0]`` and of the consumer's working directory.
    """
    cached = sys.modules.get("thread_store")
    if cached is not None:
        return cached
    path = (
        pathlib.Path(__file__).resolve().parent.parent.parent
        / "thread-store"
        / "scripts"
        / "thread_store.py"
    )
    spec = importlib.util.spec_from_file_location("thread_store", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load thread_store from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["thread_store"] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compute git diff against the PR's base ref."
    )
    parser.add_argument("--slug", required=True, help="thread slug")
    args = parser.parse_args(argv)

    thread_store = _load_thread_store()
    try:
        payload = thread_store.read(args.slug, PR_RECORD_NAME)
    except thread_store.NotFound as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    except thread_store.ThreadStoreError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1

    try:
        pr = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        sys.stderr.write(f"{PR_RECORD_NAME} is not valid JSON: {exc}\n")
        return 1
    if not isinstance(pr, dict):
        sys.stderr.write(f"{PR_RECORD_NAME} must be a JSON object\n")
        return 1

    base_ref = pr.get("baseRefName")
    if not isinstance(base_ref, str) or not base_ref:
        sys.stderr.write(
            f"{PR_RECORD_NAME} missing 'baseRefName' or it is not a non-empty string\n"
        )
        return 1

    completed = subprocess.run(  # noqa: S603 — args derived from validated pr.json field
        ["git", "diff", f"{base_ref}..HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        sys.stderr.write(completed.stderr)
        return completed.returncode
    sys.stdout.write(completed.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
