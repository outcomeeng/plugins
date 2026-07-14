"""Source-derived domains for runtime-token validation evidence."""

from __future__ import annotations

from dataclasses import dataclass

from outcomeeng.distribution.build import RUNTIME_TOKEN_REGISTRY


@dataclass(frozen=True)
class RuntimeNameCase:
    """One runtime-divergent name and its source registry coordinates."""

    kind: str
    capability: str
    runtime: str
    name: str


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
