"""Reconcile one plugin's generated agents into the selected Codex home.

Tested with: missing/current/stale owned definitions, foreign and modified
collisions, malformed ownership records, scope splits, check-only runs,
write and prune destinations changed between preflight and mutation (through
the injected digest reader), adoption of identical unrecorded destinations an
interrupted run left behind, and atomic ownership updates with no temporary
files left behind.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Any

PLUGIN = "spec-tree"
SHIPPED = Path(__file__).resolve().parent.parent / "agents"
OWNERSHIP = ".outcomeeng-marketplace-ownership.json"


def _digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}."
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _load_ownership(path: Path) -> list[dict[str, str]]:
    if not path.exists() and not path.is_symlink():
        return []
    if path.is_symlink():
        raise ValueError(f"agent ownership record {path} must be a regular file")
    try:
        document: Any = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid agent ownership record {path}: {error}") from error
    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise ValueError(f"agent ownership record {path} must use schema_version 1")
    values = document.get("entries")
    if not isinstance(values, list):
        raise ValueError(f"agent ownership record {path} must contain an entries array")
    entries: list[dict[str, str]] = []
    seen: set[str] = set()
    for index, value in enumerate(values):
        if not isinstance(value, dict):
            raise ValueError(
                f"agent ownership record {path} entry {index} must be an object"
            )
        destination, plugin, digest = (
            value.get(key) for key in ("destination", "plugin", "digest")
        )
        for key, item in (
            ("destination", destination),
            ("plugin", plugin),
            ("digest", digest),
        ):
            if not isinstance(item, str):
                raise ValueError(
                    f"agent ownership record {path} entry {index} field {key!r} "
                    f"is not a string: {item!r}"
                )
        relative = Path(destination)
        if (
            relative.is_absolute()
            or len(relative.parts) != 2
            or relative.parts[0] != "agents"
            or relative.suffix != ".toml"
        ):
            raise ValueError(
                f"agent ownership record {path} entry {index} destination "
                f"{destination!r} is not agents/<name>.toml"
            )
        if not plugin:
            raise ValueError(
                f"agent ownership record {path} entry {index} plugin is empty"
            )
        if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
            raise ValueError(
                f"agent ownership record {path} entry {index} digest {digest!r} "
                "is not a lowercase sha256 hex string"
            )
        if destination in seen:
            raise ValueError(f"agent ownership record {path} repeats {destination}")
        seen.add(destination)
        entries.append({"destination": destination, "plugin": plugin, "digest": digest})
    return entries


def _print_each(messages: list[str]) -> None:
    for message in messages:
        print(message)


def _current_digest(path: Path) -> str | None:
    if path.is_file() and not path.is_symlink():
        return _digest(path.read_bytes())
    return None


def _collision_cause(
    path: Path, recorded: dict[str, str] | None, current: str | None, desired: str
) -> str | None:
    """Name why a present destination is not this plugin's to replace.

    A destination no entry records whose bytes already equal the desired
    shipped content is the artifact of a run interrupted before the ownership
    record was written; it is adopted, not a collision.
    """
    if path.is_symlink():
        return "symlink"
    if recorded is None:
        return None if current == desired else "unrecorded"
    if recorded["plugin"] != PLUGIN:
        return f"owned by {recorded['plugin']}"
    if current is None:
        return "not a regular file"
    if current != recorded["digest"]:
        return "digest mismatch"
    return None


def _mentions_plugin(path: Path, content: bytes) -> bool:
    """Whether a checkout definition claims this plugin by name or by skill.

    A filename carrying the plugin prefix and a definition enabling one of this
    plugin's skills are both plugin-owned shapes; the second catches a renamed
    copy the prefix check would let shadow the selected home.
    """
    if path.stem.startswith((f"{PLUGIN}_", f"{PLUGIN}-")):
        return True
    try:
        document = tomllib.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return False
    skills = document.get("skills")
    config = skills.get("config") if isinstance(skills, dict) else None
    if not isinstance(config, list):
        return False
    return any(
        isinstance(entry, dict)
        and isinstance(name := entry.get("name"), str)
        and name.partition(":")[0] == PLUGIN
        for entry in config
    )


def _scope_splits(checkout: Path, shipped: dict[str, bytes]) -> list[str]:
    found: list[str] = []
    for path in sorted((checkout / ".codex" / "agents").glob("*.toml")):
        if path.is_symlink():
            found.append(f"scope-split collision: {path}")
            continue
        content = path.read_bytes()
        if content in shipped.values():
            found.append(f"scope-split directed-removal: {path}")
        elif _mentions_plugin(path, content):
            found.append(f"scope-split collision: {path}")
    return found


def main(
    argv: list[str] | None = None,
    *,
    current_digest: Callable[[Path], str | None] = _current_digest,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=os.environ.get("CODEX_HOME"))
    parser.add_argument("--checkout", type=Path, default=Path.cwd())
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.home is None:
        parser.error("set CODEX_HOME or pass --home <absolute selected CODEX_HOME>")
    if not args.home.is_absolute():
        parser.error(f"CODEX_HOME/--home resolved to a relative path: {args.home}")
    home = args.home.resolve()
    agents = home / "agents"
    shipped = {path.name: path.read_bytes() for path in sorted(SHIPPED.glob("*.toml"))}
    splits = _scope_splits(args.checkout.resolve(), shipped)
    if agents.is_symlink():
        _print_each(splits)
        print(f"collision: selected agent directory {agents} must not be a symlink")
        return 2
    ownership_path = agents / OWNERSHIP
    ownership_before = (
        ownership_path.read_bytes()
        if ownership_path.is_file() and not ownership_path.is_symlink()
        else None
    )
    try:
        entries = _load_ownership(ownership_path)
    except ValueError as error:
        _print_each(splits)
        print(f"collision: {error}")
        return 2
    by_destination = {entry["destination"]: entry for entry in entries}
    desired = {f"agents/{name}": content for name, content in shipped.items()}
    writes: list[tuple[Path, bytes, str | None]] = []
    prunes: list[tuple[Path, str]] = []
    collisions: list[str] = []
    next_entries = [entry for entry in entries if entry["plugin"] != PLUGIN]
    for relative, content in desired.items():
        path, recorded = home / relative, by_destination.get(relative)
        present = path.exists() or path.is_symlink()
        current = current_digest(path)
        digest = _digest(content)
        if present:
            cause = _collision_cause(path, recorded, current, digest)
            if cause is not None:
                collisions.append(f"collision: {path} ({cause})")
                continue
        if current != digest:
            writes.append((path, content, current))
        next_entries.append(
            {"destination": relative, "plugin": PLUGIN, "digest": digest}
        )
    for entry in entries:
        if entry["plugin"] != PLUGIN or entry["destination"] in desired:
            continue
        path = home / entry["destination"]
        present = path.exists() or path.is_symlink()
        current = current_digest(path)
        if present and path.is_symlink():
            collisions.append(f"collision: {path} (symlink)")
        elif present and current != entry["digest"]:
            collisions.append(f"collision: {path} (digest mismatch)")
        elif present:
            prunes.append((path, entry["digest"]))
    _print_each([*splits, *collisions])
    for path, _, _ in writes:
        print(f"write: {path}")
    for path, _ in prunes:
        print(f"prune: {path}")
    if splits or collisions:
        return 2
    if args.check:
        return 1 if writes or prunes else 0
    current_ownership = (
        ownership_path.read_bytes()
        if ownership_path.is_file() and not ownership_path.is_symlink()
        else None
    )
    if current_ownership != ownership_before:
        print(f"collision: {ownership_path} (changed after preflight)")
        return 2
    drifted = [
        path for path, _, expected in writes if current_digest(path) != expected
    ] + [path for path, expected in prunes if current_digest(path) != expected]
    if drifted:
        for path in drifted:
            print(f"collision: {path} (changed after preflight)")
        return 2
    for path, content, _ in writes:
        _atomic_write(path, content)
    for path, _ in prunes:
        path.unlink()
    ownership = {
        "schema_version": 1,
        "entries": sorted(next_entries, key=lambda entry: entry["destination"]),
    }
    ownership_content = (
        json.dumps(ownership, indent=2, sort_keys=True) + "\n"
    ).encode()
    if current_ownership != ownership_content:
        _atomic_write(ownership_path, ownership_content)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
