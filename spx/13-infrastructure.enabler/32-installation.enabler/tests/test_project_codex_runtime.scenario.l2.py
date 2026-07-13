"""Level 2 evidence for project-scoped Codex runtime resolution."""

from collections import Counter

from outcomeeng_testing.harnesses.codex_project_runtime import (
    observe_project_codex_runtime,
)


def test_project_codex_runtime_resolves_worktree_artifacts() -> None:
    assert observe_project_codex_runtime().skills.errors == ()
    assert Counter(observe_project_codex_runtime().skills.expected_digests) <= Counter(
        observe_project_codex_runtime().skills.resolved_digests
    )
    assert observe_project_codex_runtime().agents.project_layer_names == ()
    assert (
        observe_project_codex_runtime().agents.configured_names
        == observe_project_codex_runtime().agents.expected_names
    )
    assert (
        observe_project_codex_runtime().agents.parsed_names
        == observe_project_codex_runtime().agents.expected_names
    )
    assert Counter(observe_project_codex_runtime().agents.expected_digests) == Counter(
        observe_project_codex_runtime().agents.resolved_digests
    )
    assert (
        observe_project_codex_runtime().user_state_after
        == observe_project_codex_runtime().user_state_before
    )
    assert (
        observe_project_codex_runtime().generated_plugin_version
        != observe_project_codex_runtime().seeded_user_plugin_version
    )
