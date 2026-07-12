"""Compliance evidence for runtime-token parameterization."""

from __future__ import annotations

from outcomeeng_testing.harnesses.runtime_parameterization import (
    build_fails_on_unknown_kind_capability_or_runtime,
    conditional_renders_absent_capability_only_where_present,
    field_kind_renders_live_registry_name_per_target,
    file_kind_renders_guide_filename_per_target,
    registry_is_keyed_by_kind_with_explicit_guard_enforcement,
    registry_token_renders_each_target_name,
    runtime_explicit_token_renders_named_runtime_on_every_target,
    term_kind_renders_live_registry_name_per_target,
)


def test_registry_token_renders_each_target_name() -> None:
    assert registry_token_renders_each_target_name()


def test_file_kind_renders_guide_filename_per_target() -> None:
    assert file_kind_renders_guide_filename_per_target()


def test_field_kind_renders_live_registry_name_per_target() -> None:
    assert field_kind_renders_live_registry_name_per_target()


def test_term_kind_renders_live_registry_name_per_target() -> None:
    assert term_kind_renders_live_registry_name_per_target()


def test_runtime_explicit_token_renders_named_runtime_on_every_target() -> None:
    assert runtime_explicit_token_renders_named_runtime_on_every_target()


def test_build_fails_on_unknown_kind_capability_or_runtime() -> None:
    assert build_fails_on_unknown_kind_capability_or_runtime()


def test_conditional_renders_absent_capability_only_where_present() -> None:
    assert conditional_renders_absent_capability_only_where_present()


def test_registry_keyed_by_kind_with_explicit_guard_enforcement() -> None:
    assert registry_is_keyed_by_kind_with_explicit_guard_enforcement()
