"""CLI: write a record into the thread store.

Reads the payload from stdin or ``--file`` and dispatches the write
through the ``thread_store`` facade. The facade resolves the active
backend via ``SPX_VET_BACKEND``; this CLI performs no direct
filesystem effects.

Exit codes: 0 on success, non-zero on argument or backend error.
"""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import sys
from types import ModuleType


def _load_thread_store() -> ModuleType:
    """Load the ``thread_store`` facade via ``importlib``.

    The script can be invoked via ``python3 path/to/write_record.py``
    in any working directory; locating the facade through ``__file__``
    keeps the import independent of ``sys.path[0]``.
    """
    cached = sys.modules.get("thread_store")
    if cached is not None:
        return cached
    path = pathlib.Path(__file__).resolve().parent / "thread_store.py"
    spec = importlib.util.spec_from_file_location("thread_store", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load thread_store from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["thread_store"] = module
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Write a record to the thread store.")
    parser.add_argument("--slug", required=True, help="thread slug")
    parser.add_argument("--name", required=True, help="record name")
    parser.add_argument(
        "--file",
        type=pathlib.Path,
        default=None,
        help="path to payload file; when omitted, payload is read from stdin",
    )
    args = parser.parse_args(argv)

    if args.file is not None:
        payload = args.file.read_bytes()
    else:
        payload = sys.stdin.buffer.read()

    thread_store = _load_thread_store()
    try:
        thread_store.write(args.slug, args.name, payload)
    except thread_store.ThreadStoreError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
