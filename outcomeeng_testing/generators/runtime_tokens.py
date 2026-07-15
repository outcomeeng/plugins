"""Source-derived domains for runtime-token validation evidence."""

from __future__ import annotations

from dataclasses import dataclass

from outcomeeng.distribution.build import RUNTIME_TOKEN_REGISTRY, RuntimeTokenKind
from outcomeeng.distribution.contracts import (
    Target,
    format_target_branches,
    format_target_conditional,
)


@dataclass(frozen=True)
class RuntimeNameCase:
    """One runtime-divergent name and its source registry coordinates."""

    kind: str
    capability: str
    runtime: str
    name: str


@dataclass(frozen=True)
class RuntimeConditionalCase:
    """Generated valid and invalid conditional sources for one raw name."""

    name: str
    matching_sources: tuple[str, ...]
    mismatching_sources: tuple[str, ...]


@dataclass(frozen=True)
class RuntimeRegistryProbe:
    """A controlled registry whose enforcement differs from the live registry."""

    registry: dict[str, RuntimeTokenKind]
    enforced_names: tuple[str, ...]
    excluded_names: tuple[str, ...]


def lint_enforced_runtime_names() -> tuple[RuntimeNameCase, ...]:
    """Return every name owned by a guard-enforced registry kind."""
    return _runtime_names(lint_enforced=True)


def review_only_runtime_names() -> tuple[RuntimeNameCase, ...]:
    """Return names owned exclusively by review-only registry kinds."""
    enforced_names = frozenset(case.name for case in _runtime_names(lint_enforced=True))
    return tuple(
        case
        for case in _runtime_names(lint_enforced=False)
        if case.name not in enforced_names
    )


def runtime_conditional_cases() -> tuple[RuntimeConditionalCase, ...]:
    """Return conditional sources derived from every enforced registry name."""
    targets_by_name: dict[str, set[Target]] = {}
    for case in lint_enforced_runtime_names():
        targets_by_name.setdefault(case.name, set()).add(Target(case.runtime))

    all_targets = tuple(Target)
    return tuple(
        RuntimeConditionalCase(
            name=name,
            matching_sources=tuple(
                format_target_conditional(target, name) for target in native_targets
            )
            + (
                format_target_branches(
                    tuple(
                        (target, name if target in native_targets else "")
                        for target in all_targets
                    )
                ),
            )
            + tuple(
                format_target_conditional(
                    target,
                    format_target_conditional(target, name),
                )
                for target in native_targets
            ),
            mismatching_sources=tuple(
                format_target_conditional(target, name)
                for target in all_targets
                if target not in native_targets
            ),
        )
        for name, target_set in sorted(targets_by_name.items())
        for native_targets in (
            tuple(sorted(target_set, key=lambda target: target.value)),
        )
    )


def inverted_enforcement_registry_probe() -> RuntimeRegistryProbe:
    """Invert live kind enforcement so scanner injection is falsifiable."""
    registry = {
        kind: RuntimeTokenKind(
            lint_enforced=not entry.lint_enforced,
            names=entry.names,
        )
        for kind, entry in RUNTIME_TOKEN_REGISTRY.items()
    }
    enforced_names = _names_for_lint_enforcement(lint_enforced=False)
    excluded_names = tuple(
        name
        for name in _names_for_lint_enforcement(lint_enforced=True)
        if name not in frozenset(enforced_names)
    )
    return RuntimeRegistryProbe(
        registry=registry,
        enforced_names=enforced_names,
        excluded_names=excluded_names,
    )


def empty_enforcement_registry() -> dict[str, RuntimeTokenKind]:
    """Return the live registry shape with every kind excluded from linting."""
    return {
        kind: RuntimeTokenKind(lint_enforced=False, names=entry.names)
        for kind, entry in RUNTIME_TOKEN_REGISTRY.items()
    }


def _runtime_names(*, lint_enforced: bool) -> tuple[RuntimeNameCase, ...]:
    return tuple(
        RuntimeNameCase(
            kind=kind,
            capability=capability,
            runtime=runtime,
            name=name,
        )
        for kind, entry in RUNTIME_TOKEN_REGISTRY.items()
        if entry.lint_enforced is lint_enforced
        for capability, runtime_names in entry.names.items()
        for runtime, name in runtime_names.items()
    )


def _names_for_lint_enforcement(*, lint_enforced: bool) -> tuple[str, ...]:
    return tuple(
        sorted({case.name for case in _runtime_names(lint_enforced=lint_enforced)})
    )
