from outcomeeng_testing.harnesses.distribution import (
    distribution_workflow_uses_project_python,
    distribution_workflow_uses_runtime_and_source_paths,
)


def test_distribution_workflow_uses_runtime_and_source_paths() -> None:
    assert distribution_workflow_uses_runtime_and_source_paths()


def test_distribution_workflow_uses_project_python() -> None:
    assert distribution_workflow_uses_project_python()
