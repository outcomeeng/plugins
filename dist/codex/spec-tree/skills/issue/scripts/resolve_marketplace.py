#!/usr/bin/env python3
"""Resolve the registered local source for a marketplace entry from JSON stdin.

A Codex entry carries the materialized checkout at top-level `root` and, when the
marketplace was registered from a local directory, the same path at
`marketplaceSource.source` with `marketplaceSource.sourceType` of `local`. Both
fields are resolved, `source` first; no other Codex field carries the path, and
`sourceType` appears only inside `marketplaceSource`.

A Claude entry carries the checkout at top-level `path` when its `source` is
exactly the `directory` token; the token is a fixed literal, so a source
differing in case is a different source and resolves nothing.

Tested with:
- The complete per-runtime field domain, over the registered source, the
  materialized root, and the source type each present, empty, or absent ->
  resolves the path the rule above names, or names none as available. An
  empty value falls through wherever an absent one would.
- A Claude source differing from the `directory` token in case -> resolves
  nothing, so the exact-match rule is exercised rather than assumed.
- Every one of those cases repeated carrying the other runtime's fields as
  decoys -> the resolved path is unchanged, so a resolver reading a field
  outside its own runtime's set fails the case.
- Two entries sharing the name -> resolves the first with a path.
- An omitted --name -> resolves the default marketplace.
- Generated JSON naming no matching marketplace -> target-resolution error.
- Generated text that is not a JSON document -> invalid-JSON error.
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
NO_LOCAL_MARKETPLACES: Final = "none"
EXIT_INVALID_JSON: Final = 2
EXIT_MARKETPLACE_NOT_FOUND: Final = 3
INVALID_JSON_MESSAGE: Final = "invalid marketplace JSON: {error}"
NOT_FOUND_MESSAGE: Final = (
    "marketplace {name!r} is not registered as a local {runtime} marketplace; "
    "available local marketplaces: {available}"
)


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
    if entry.get(SOURCE_FIELD) == CLAUDE_DIRECTORY_SOURCE:
        path = entry.get(PATH_FIELD)
        if isinstance(path, str):
            return path
    return ""


def _codex_path(entry: dict[str, Any]) -> str:
    source = entry.get(MARKETPLACE_SOURCE_FIELD, {})
    source = source if isinstance(source, dict) else {}
    if source.get(SOURCE_TYPE_FIELD) != CODEX_LOCAL_SOURCE_TYPE:
        return ""

    for key_owner, key in (
        (source, SOURCE_FIELD),
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
    return ", ".join(names) if names else NO_LOCAL_MARKETPLACES


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
        print(INVALID_JSON_MESSAGE.format(error=exc), file=sys.stderr)
        return EXIT_INVALID_JSON

    entries = list(_entries(payload))
    path = _resolve(entries, args.runtime, args.name)
    if not path:
        print(
            NOT_FOUND_MESSAGE.format(
                name=args.name,
                runtime=args.runtime,
                available=_available_local_marketplaces(entries, args.runtime),
            ),
            file=sys.stderr,
        )
        return EXIT_MARKETPLACE_NOT_FOUND

    print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
