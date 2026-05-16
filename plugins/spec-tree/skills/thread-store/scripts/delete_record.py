"""CLI: delete a record from the thread store.

Dispatches through the ``thread_store`` facade; performs no direct
filesystem effects against the persistence store.

Exit codes: 0 on success, non-zero on missing record or backend error.
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
    parser = argparse.ArgumentParser(
        description="Delete a record from the thread store."
    )
    parser.add_argument("--slug", required=True, help="thread slug")
    parser.add_argument("--name", required=True, help="record name")
    args = parser.parse_args(argv)

    thread_store = _load_thread_store()
    try:
        thread_store.delete(args.slug, args.name)
    except thread_store.NotFound as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    except thread_store.ThreadStoreError as exc:
        sys.stderr.write(f"{exc}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
