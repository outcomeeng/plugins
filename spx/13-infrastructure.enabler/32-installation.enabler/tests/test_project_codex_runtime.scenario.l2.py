"""Level 2 evidence for project-scoped Codex runtime resolution."""

from collections import Counter

from outcomeeng_testing.harnesses.codex_project_runtime import (
    observe_project_codex_runtime,
)


def test_project_codex_runtime_resolves_worktree_artifacts() -> None:
    observation = observe_project_codex_runtime()

    assert observation.skills.errors == ()
    assert Counter(observation.skills.expected_digests) <= Counter(
        observation.skills.resolved_digests
    )
    assert observation.agents.project_layer_names == ()
    assert observation.agents.configured_names == observation.agents.expected_names
    assert observation.agents.parsed_names == observation.agents.expected_names
    assert observation.user_state_after == observation.user_state_before
    assert (
        observation.generated_plugin_version
        != observation.seeded_user_plugin_version
    )
