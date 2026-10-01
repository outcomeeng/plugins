from outcomeeng_testing.harnesses.distribution import (
    observe_distribution_workflow_paths,
    observe_distribution_workflow_python,
)


def test_distribution_workflow_uses_runtime_and_source_paths() -> None:
    observed = observe_distribution_workflow_paths()

    assert observed.committed_result
    assert observed.violating_results
    assert not any(observed.violating_results)


def test_distribution_workflow_uses_project_python() -> None:
    observed = observe_distribution_workflow_python()

    assert observed.committed_result
    assert observed.violating_results
    assert not any(observed.violating_results)
