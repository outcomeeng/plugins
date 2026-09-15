"""Real artifact and filesystem arrangements for shipped plugin placement."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager, redirect_stdout
from dataclasses import dataclass
from enum import StrEnum, auto
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory

from outcomeeng.distribution.installation import (
    AGENT_OWNERSHIP_DESTINATION_FIELD,
    AGENT_OWNERSHIP_DIGEST_FIELD,
    AGENT_OWNERSHIP_ENTRIES_FIELD,
    AGENT_OWNERSHIP_PLUGIN_FIELD,
    AGENT_OWNERSHIP_SCHEMA_FIELD,
    AGENT_OWNERSHIP_SCHEMA_VERSION,
    AgentDefinition,
    generated_codex_agent_definitions,
)
from outcomeeng_testing.harnesses.installation import (
    PluginLifecycleHarness,
    PluginLifecycleRun,
    committed_catalog_plugin_names,
    racing_digest_reader,
    repository_root,
)


class LifecycleCase(StrEnum):
    """Filesystem violations and transitions declared by placement ownership."""

    EMPTY = auto()
    RETIRED = auto()
    UNRECORDED = auto()
    INVALID_DIGEST = auto()
    SYMLINK = auto()
    SCOPE_SPLIT = auto()
    IDENTICAL = auto()
    WRITE_RACE = auto()
    PRUNE_RACE = auto()
    INVALID_DIGEST_AND_SCOPE = auto()
    DIRECTORY = auto()
    SYMLINK_ROOT_AND_SCOPE = auto()


@dataclass
class LifecycleResources:
    """Resource handles and original artifacts; no behavioral verdicts."""

    harness: PluginLifecycleHarness
    definitions: tuple[AgentDefinition, ...]
    foreign: AgentDefinition
    case: LifecycleCase
    scope_paths: tuple[Path, ...] = ()

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

    def ownership_document(self) -> dict[str, object]:
        return {
            AGENT_OWNERSHIP_SCHEMA_FIELD: AGENT_OWNERSHIP_SCHEMA_VERSION,
            AGENT_OWNERSHIP_ENTRIES_FIELD: [
                {
                    AGENT_OWNERSHIP_DESTINATION_FIELD: (
                        self.harness.home_agents / definition.source.name
                    )
                    .relative_to(self.harness.home)
                    .as_posix(),
                    AGENT_OWNERSHIP_PLUGIN_FIELD: definition.plugin,
                    AGENT_OWNERSHIP_DIGEST_FIELD: hashlib.sha256(
                        definition.content
                    ).hexdigest(),
                }
                for definition in self.definitions
            ],
        }

    def run(self, *, check: bool = False) -> PluginLifecycleRun:
        if self.case not in {LifecycleCase.WRITE_RACE, LifecycleCase.PRUNE_RACE}:
            return self.harness.run(check=check)
        module = self.harness.load_module()
        target = (
            self.destination
            if self.case is LifecycleCase.WRITE_RACE
            else self.harness.home_agents / self.retired.source.name
        )

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


def _scope_split(resources: LifecycleResources) -> None:
    harness = resources.harness
    resources.scope_paths = (
        harness.write_checkout(
            resources.current.source.name, resources.current.content
        ),
        harness.write_checkout(
            resources.retired.source.name, resources.foreign.content
        ),
        harness.write_checkout(
            resources.foreign.source.name, resources.current.content + b"\n"
        ),
    )


def _arrange(resources: LifecycleResources) -> None:
    harness = resources.harness
    case = resources.case
    if case in {LifecycleCase.RETIRED, LifecycleCase.PRUNE_RACE}:
        harness.write_home(resources.foreign.source.name, resources.foreign.content)
        installed = harness.run()
        if installed.exit_code:
            raise RuntimeError(
                f"cannot prepare installed definitions: {installed.stdout}"
            )
        (harness.shipped_agents / resources.retired.source.name).unlink()
    if case is LifecycleCase.UNRECORDED:
        harness.write_home(resources.current.source.name, resources.foreign.content)
    if case is LifecycleCase.IDENTICAL:
        harness.write_home(resources.current.source.name, resources.current.content)
    if case is LifecycleCase.SYMLINK:
        resources.external.write_bytes(resources.foreign.content)
        harness.home_agents.mkdir(parents=True)
        resources.destination.symlink_to(resources.external)
    if case in {LifecycleCase.INVALID_DIGEST, LifecycleCase.INVALID_DIGEST_AND_SCOPE}:
        document = resources.ownership_document()
        entries = document[AGENT_OWNERSHIP_ENTRIES_FIELD]
        if not isinstance(entries, list):
            raise TypeError("ownership entries must be a list")
        for entry in entries:
            digest = entry[AGENT_OWNERSHIP_DIGEST_FIELD]
            upper = digest.upper()
            if upper == digest:
                raise ValueError(
                    "artifact digest has no hexadecimal letter to uppercase"
                )
            entry[AGENT_OWNERSHIP_DIGEST_FIELD] = upper
        harness.write_ownership(document)
    if case is LifecycleCase.DIRECTORY:
        resources.destination.mkdir(parents=True)
        harness.write_ownership(resources.ownership_document())
    if case is LifecycleCase.SYMLINK_ROOT_AND_SCOPE:
        resources.external.mkdir()
        harness.home.mkdir(parents=True)
        harness.home_agents.symlink_to(resources.external)
    if case in {
        LifecycleCase.SCOPE_SPLIT,
        LifecycleCase.INVALID_DIGEST_AND_SCOPE,
        LifecycleCase.SYMLINK_ROOT_AND_SCOPE,
    }:
        _scope_split(resources)


@contextmanager
def lifecycle_case(case: LifecycleCase) -> Iterator[LifecycleResources]:
    """Copy complete committed agent artifacts and apply one ownership transition."""
    with TemporaryDirectory(prefix="plugin-placement-") as temporary:
        root = Path(temporary).resolve()
        definitions = generated_codex_agent_definitions(
            repository_root(),
            root,
            sorted(committed_catalog_plugin_names()),
        )
        by_plugin: dict[str, list[AgentDefinition]] = defaultdict(list)
        for definition in definitions:
            by_plugin[definition.plugin].append(definition)
        plugin, selected = next(
            (plugin, values) for plugin, values in by_plugin.items() if len(values) >= 2
        )
        foreign = next(value for value in definitions if value.plugin != plugin)
        harness = PluginLifecycleHarness.create(root, plugin_name=plugin)
        for definition in selected:
            harness.write_shipped(definition.source.name, definition.content)
        resources = LifecycleResources(harness, tuple(selected), foreign, case)
        _arrange(resources)
        yield resources
