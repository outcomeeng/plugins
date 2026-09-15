"""Load complete placement fixtures and own their disposable filesystem."""

from __future__ import annotations

import json
from collections.abc import Iterator
from contextlib import contextmanager, redirect_stdout
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import TypedDict, cast

from outcomeeng.distribution.installation import AgentDefinition
from outcomeeng_testing.harnesses.installation import (
    PluginLifecycleHarness,
    PluginLifecycleRun,
    racing_digest_reader,
    repository_root,
)


class DefinitionPayload(TypedDict):
    path: str
    name: str
    content: str
    digest: str
    plugin: str


class FilePayload(TypedDict):
    path: str
    content: str


class SymlinkPayload(TypedDict):
    path: str
    target: str


class LifecyclePayload(TypedDict):
    plugin: str
    definitions: list[DefinitionPayload]
    foreign: DefinitionPayload
    shipped: list[str]
    files: list[FilePayload]
    directories: list[str]
    symlinks: list[SymlinkPayload]
    scope_paths: list[str]
    race_target: str | None


@dataclass(frozen=True)
class LifecycleResources:
    """Resource handles and original artifacts; no behavioral verdicts."""

    harness: PluginLifecycleHarness
    definitions: tuple[AgentDefinition, ...]
    foreign: AgentDefinition
    scope_paths: tuple[Path, ...]
    race_target: Path | None

    @property
    def current(self) -> AgentDefinition:
        return self.definitions[0]

    @property
    def retired(self) -> AgentDefinition:
        return self.definitions[1]

    @property
    def destination(self) -> Path:
        return self.harness.home_agents / self.current.source.name

    @property
    def foreign_destination(self) -> Path:
        return self.harness.home_agents / self.foreign.source.name

    @property
    def external(self) -> Path:
        return self.harness.root / self.foreign.source.name

    def run(self, *, check: bool = False) -> PluginLifecycleRun:
        target = self.race_target
        if target is None:
            return self.harness.run(check=check)
        module = self.harness.load_module()

        def write_foreign_content() -> None:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(self.foreign.content)

        output = StringIO()
        with redirect_stdout(output):
            code = module.main(
                [
                    "--home",
                    str(self.harness.home),
                    "--checkout",
                    str(self.harness.checkout),
                ],
                current_digest=racing_digest_reader(
                    target, write_foreign_content, module._current_digest
                ),
            )
        return PluginLifecycleRun(
            exit_code=code,
            stdout=output.getvalue(),
            stderr="",
            home_snapshot=self.harness.snapshot(self.harness.home),
            checkout_snapshot=self.harness.snapshot(self.harness.checkout),
        )


def lifecycle_fixture(filename: str) -> Path:
    """Resolve an inert complete filesystem fixture without loading its data."""
    return (
        repository_root()
        / "outcomeeng_testing"
        / "fixtures"
        / "plugin_lifecycle"
        / filename
    )


def _definition(
    payload: DefinitionPayload, harness: PluginLifecycleHarness
) -> AgentDefinition:
    return AgentDefinition(
        plugin=payload["plugin"],
        source=Path(payload["path"]),
        destination=harness.home_agents / payload["name"],
        digest=payload["digest"],
        content=payload["content"].encode("utf-8"),
    )


@contextmanager
def lifecycle_case(fixture: Path) -> Iterator[LifecycleResources]:
    """Materialize an inert filesystem payload and execute the current script."""
    payload = cast(LifecyclePayload, json.loads(fixture.read_text(encoding="utf-8")))
    with TemporaryDirectory(prefix="plugin-placement-") as temporary:
        root = Path(temporary).resolve()
        harness = PluginLifecycleHarness.create(root, plugin_name=payload["plugin"])
        definitions = tuple(
            _definition(value, harness) for value in payload["definitions"]
        )
        for definition in definitions:
            if definition.source.name in payload["shipped"]:
                harness.write_shipped(definition.source.name, definition.content)
        for directory in payload["directories"]:
            (root / directory).mkdir(parents=True, exist_ok=True)
        for file in payload["files"]:
            path = root / file["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(file["content"], encoding="utf-8")
        for link in payload["symlinks"]:
            path = root / link["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(link["target"])
        race_target = payload["race_target"]
        yield LifecycleResources(
            harness=harness,
            definitions=definitions,
            foreign=_definition(payload["foreign"], harness),
            scope_paths=tuple(root / path for path in payload["scope_paths"]),
            race_target=root / race_target if race_target is not None else None,
        )
