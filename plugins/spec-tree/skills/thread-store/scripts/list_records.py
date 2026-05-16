"""CLI: list records in a thread.

Writes record names to stdout, one per line, in the order the backend
returns them. Dispatches through the ``thread_store`` facade.

Exit codes: 0 on success (including an empty thread), non-zero on
backend error.
"""

from __future__ import annotations

import argparse
import importlib.util
import pathlib
import sys
from types import ModuleType


def _load_thread_store() -> ModuleType:
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
    parser = argparse.ArgumentParser(description="List records in a thread.")
    parser.add_argument("--slug", required=True, help="thread slug")
    args = parser.parse_args(argv)

    thread_store = _load_thread_store()
    try:
        names = thread_store.list(args.slug)
    except thread_store.ThreadStoreError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    for name in names:
        sys.stdout.write(name + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
