#!/usr/bin/env python3
"""Resolve the registered local source for a marketplace entry from JSON stdin.

Tested with:
- Claude marketplace JSON using a Directory source -> prints path.
- Codex marketplace JSON using a local marketplaceSource -> prints path.
- Malformed JSON -> returns a clear invalid-JSON error.
- Missing local marketplace -> returns a clear target-resolution error.
- No temporary files are created.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Iterable
from typing import Any, Final

DEFAULT_MARKETPLACE_NAME: Final = "outcomeeng"
MARKETPLACES_FIELD: Final = "marketplaces"
NAME_FIELD: Final = "name"
SOURCE_FIELD: Final = "source"
PATH_FIELD: Final = "path"
ROOT_FIELD: Final = "root"
MARKETPLACE_SOURCE_FIELD: Final = "marketplaceSource"
SOURCE_TYPE_FIELD: Final = "sourceType"
CLAUDE_DIRECTORY_SOURCE: Final = "directory"
CODEX_LOCAL_SOURCE_TYPE: Final = "local"
RUNTIME_CLAUDE: Final = "claude"
RUNTIME_CODEX: Final = "codex"
EXIT_INVALID_JSON: Final = 2
EXIT_MARKETPLACE_NOT_FOUND: Final = 3


def _entries(payload: Any) -> Iterable[dict[str, Any]]:
    if isinstance(payload, list):
        for item in payload:
            if isinstance(item, dict):
                yield item
        return

    if isinstance(payload, dict):
        marketplaces = payload.get(MARKETPLACES_FIELD, [])
        if isinstance(marketplaces, list):
            for item in marketplaces:
                if isinstance(item, dict):
                    yield item


def _claude_path(entry: dict[str, Any]) -> str:
    if str(entry.get(SOURCE_FIELD, "")).lower() == CLAUDE_DIRECTORY_SOURCE:
        path = entry.get(PATH_FIELD)
        if isinstance(path, str):
            return path
    return ""


def _codex_path(entry: dict[str, Any]) -> str:
    source = entry.get(MARKETPLACE_SOURCE_FIELD, {})
    source = source if isinstance(source, dict) else {}
    source_type = source.get(SOURCE_TYPE_FIELD) or entry.get(SOURCE_TYPE_FIELD)
    if source_type != CODEX_LOCAL_SOURCE_TYPE:
        return ""

    for key_owner, key in (
        (source, SOURCE_FIELD),
        (entry, PATH_FIELD),
        (entry, ROOT_FIELD),
    ):
        value = key_owner.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _path_resolver(runtime: str) -> Callable[[dict[str, Any]], str]:
    return _codex_path if runtime == RUNTIME_CODEX else _claude_path


def _resolve(entries: list[dict[str, Any]], runtime: str, name: str) -> str:
    path_for = _path_resolver(runtime)
    for entry in entries:
        if entry.get(NAME_FIELD) == name:
            path = path_for(entry)
            if path:
                return path
    return ""


def _available_local_marketplaces(entries: list[dict[str, Any]], runtime: str) -> str:
    path_for = _path_resolver(runtime)
    names = sorted(
        str(entry[NAME_FIELD])
        for entry in entries
        if isinstance(entry.get(NAME_FIELD), str) and path_for(entry)
    )
    return ", ".join(names) if names else "none"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Print the local checkout path for a registered marketplace."
    )
    parser.add_argument(
        "--runtime", choices=(RUNTIME_CLAUDE, RUNTIME_CODEX), required=True
    )
    parser.add_argument("--name", default=DEFAULT_MARKETPLACE_NAME)
    args = parser.parse_args()

    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError as exc:
        print(f"invalid marketplace JSON: {exc}", file=sys.stderr)
        return EXIT_INVALID_JSON

    entries = list(_entries(payload))
    path = _resolve(entries, args.runtime, args.name)
    if not path:
        available = _available_local_marketplaces(entries, args.runtime)
        print(
            f"marketplace {args.name!r} is not registered as a local "
            f"{args.runtime} marketplace; available local marketplaces: {available}",
            file=sys.stderr,
        )
        return EXIT_MARKETPLACE_NOT_FOUND

    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
